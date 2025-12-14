# src/semantic.py
from my_ast import (
    Program, VarDecl, AssignStmt, OutputStmt,
    IfStmt, WhileStmt, Block, BinOp, Identifier, Literal
)

class SemanticError(Exception):
    pass

class SemanticAnalyzer:
    def __init__(self):
        # stack of scopes: each scope is a dict name -> type (e.g., "a" -> "INT")
        self.scopes = []

        # supported primitive types
        self.allowed_output_types = {"INT", "FLOAT", "STRING", "BOOL"}
        self.arithmetic_ops = {"+", "-", "*", "/"}
        self.comparison_ops = {"<", ">", "<=", ">=", "==", "!="}

    # -------------------------
    # Scope management
    # -------------------------
    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if not self.scopes:
            raise SemanticError("Internal semantic error: popping empty scope")
        self.scopes.pop()

    def current_scope(self):
        if not self.scopes:
            return None
        return self.scopes[-1]

    def find_symbol(self, name):
        # search from inner-most to outer-most
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def declare_symbol(self, name, typ):
        cur = self.current_scope()
        if cur is None:
            raise SemanticError("No active scope to declare variable")
        if name in cur:
            raise SemanticError(f"Semantic Error: Variable '{name}' already declared in this scope")
        cur[name] = typ

    # -------------------------
    # Entry point
    # -------------------------
    def analyze(self, node: Program):
        # Program-level scope
        self.push_scope()
        if not isinstance(node, Program):
            raise SemanticError("analyze() expects a Program node")
        for stmt in node.statements:
            self.visit(stmt)
        # keep top-level scope if you like, but pop for cleanliness
        self.pop_scope()

    # -------------------------
    # Visitor dispatcher
    # -------------------------
    def visit(self, node):
        if isinstance(node, VarDecl):
            return self.visit_var_decl(node)
        if isinstance(node, AssignStmt):
            return self.visit_assign(node)
        if isinstance(node, OutputStmt):
            return self.visit_output(node)
        if isinstance(node, IfStmt):
            return self.visit_if(node)
        if isinstance(node, WhileStmt):
            return self.visit_while(node)
        if isinstance(node, Block):
            return self.visit_block(node)
        if isinstance(node, BinOp):
            return self.visit_binop(node)
        if isinstance(node, Identifier):
            return self.visit_identifier(node)
        if isinstance(node, Literal):
            return self.visit_literal(node)
        # If we reach here, unknown node type
        raise SemanticError(f"Semantic Error: Unknown AST node type: {type(node)}")

    # -------------------------
    # VarDecl
    # -------------------------
    def visit_var_decl(self, node: VarDecl):
        # node.var_type is expected (e.g., 'INT'); allow only certain types or accept any string
        declared_type = node.var_type
        if declared_type not in {"INT", "FLOAT", "STRING", "BOOL", "VOID"}:
            raise SemanticError(f"Semantic Error: Unsupported type '{declared_type}' for variable '{node.name}'")

        # check duplicate in current scope
        if self.current_scope() is None:
            raise SemanticError("Semantic Error: No current scope when declaring variable")

        if node.name in self.current_scope():
            raise SemanticError(f"Semantic Error: Variable '{node.name}' already declared in this scope")

        # if has initializer, check its type
        if node.value is not None:
            expr_type = self.visit(node.value)
            if expr_type != declared_type:
                raise SemanticError(
                    f"Type Error: Cannot assign {expr_type} to {declared_type} variable '{node.name}'"
                )

        # declare in current scope
        self.declare_symbol(node.name, declared_type)
        return declared_type

    # -------------------------
    # AssignStmt
    # -------------------------
    def visit_assign(self, node: AssignStmt):
        var_type = self.find_symbol(node.name)
        if var_type is None:
            raise SemanticError(f"Semantic Error: Variable '{node.name}' used before declaration")
        expr_type = self.visit(node.expr)
        if var_type != expr_type:
            raise SemanticError(f"Type Error: Cannot assign {expr_type} to {var_type} variable '{node.name}'")
        return var_type

    # -------------------------
    # OutputStmt
    # -------------------------
    def visit_output(self, node: OutputStmt):
        expr_type = self.visit(node.expr)
        if expr_type not in self.allowed_output_types:
            raise SemanticError(f"Type Error: OUTPUT cannot print type '{expr_type}'")
        return "VOID"

    # -------------------------
    # IfStmt
    # -------------------------
    def visit_if(self, node: IfStmt):
        cond_type = self.visit(node.condition)
        if cond_type not in {"INT", "BOOL"}:
            raise SemanticError("Semantic Error: IF condition must be INT or BOOL")

        # true branch has its own scope
        self.push_scope()
        self.visit(node.true_branch)
        self.pop_scope()

        if node.false_branch:
            self.push_scope()
            self.visit(node.false_branch)
            self.pop_scope()

        return "VOID"

    # -------------------------
    # WhileStmt
    # -------------------------
    def visit_while(self, node: WhileStmt):
        cond_type = self.visit(node.condition)
        if cond_type not in {"INT", "BOOL"}:
            raise SemanticError("Semantic Error: WHILE condition must be INT or BOOL")

        self.push_scope()
        self.visit(node.body)
        self.pop_scope()
        return "VOID"

    # -------------------------
    # Block
    # -------------------------
    def visit_block(self, node: Block):
        # block creates a new nested scope already handled by callers in this design,
        # but ensure block itself checks statements in current scope (callers push/pop)
        # For safety here we will manage scope as well:
        self.push_scope()
        for s in node.statements:
            self.visit(s)
        self.pop_scope()
        return "VOID"

    # -------------------------
    # BinOp
    # -------------------------
    def visit_binop(self, node: BinOp):
        left_t = self.visit(node.left)
        right_t = self.visit(node.right)
        op = node.op

        # arithmetic operations require INT (or FLOAT if you extend)
        if op in self.arithmetic_ops:
            if left_t != right_t:
                raise SemanticError(f"Type Error: operator '{op}' operands have different types ({left_t}, {right_t})")
            if left_t not in {"INT", "FLOAT"}:
                raise SemanticError(f"Type Error: operator '{op}' not supported for type '{left_t}'")
            # result type follows operand type
            return left_t

        # comparison operators (>, <, >=, <=) → require comparable numeric types; result BOOL
        if op in {"<", ">", "<=", ">="}:
            if left_t != right_t:
                raise SemanticError(f"Type Error: comparison '{op}' operands must be same type ({left_t}, {right_t})")
            if left_t not in {"INT", "FLOAT"}:
                raise SemanticError(f"Type Error: comparison '{op}' not supported for type '{left_t}'")
            return "BOOL"

        # equality operators
        if op in {"==", "!="}:
            if left_t != right_t:
                raise SemanticError(f"Type Error: equality '{op}' operands must be same type ({left_t}, {right_t})")
            return "BOOL"

        raise SemanticError(f"Semantic Error: Unknown operator '{op}'")

    # -------------------------
    # Identifier
    # -------------------------
    def visit_identifier(self, node: Identifier):
        t = self.find_symbol(node.name)
        if t is None:
            raise SemanticError(f"Semantic Error: Variable '{node.name}' used before declaration")
        return t

    # -------------------------
    # Literal
    # -------------------------
    def visit_literal(self, node: Literal):
        # try to detect type of literal
        val = node.value
        # if someone passed numbers as strings, detect integers/floats
        if isinstance(val, str):
            s = val.strip()
            # INT
            if s.isdigit():
                return "INT"
            # FLOAT: digits with dot
            try:
                float(s)
                if "." in s:
                    return "FLOAT"
            except Exception:
                pass
            # string literal: starts and ends with quotes
            if s.startswith('"') and s.endswith('"'):
                return "STRING"
            # boolean literal words
            if s in {"true", "false", "TRUE", "FALSE"}:
                return "BOOL"
            # fallback: treat as INT if numeric-like else error
            # but to be strict, raise error:
            raise SemanticError(f"Semantic Error: Unable to infer literal type from '{val}'")
        # non-string literal handling (if you create numeric nodes differently)
        if isinstance(val, int):
            return "INT"
        if isinstance(val, float):
            return "FLOAT"
        # fallback
        raise SemanticError(f"Semantic Error: Unknown literal type for value {val}")
