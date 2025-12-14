# src/codegen.py
from my_ast import Program, VarDecl, AssignStmt, OutputStmt, IfStmt, WhileStmt, Block, BinOp, Identifier, Literal

class CodeGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.code = []

    # -------------------------
    # Helpers
    # -------------------------
    def new_temp(self):
        self.temp_count += 1
        return f"_t{self.temp_count}"

    def new_label(self, base="L"):
        self.label_count += 1
        return f"{base}{self.label_count}"

    def emit(self, line):
        self.code.append(line)

    # -------------------------
    # Entry: generate TAC for a Program node
    # -------------------------
    def generate(self, program: Program):
        self.code = []
        self.temp_count = 0
        self.label_count = 0

        if not isinstance(program, Program):
            raise Exception("CodeGenerator.generate expects a Program node")

        for stmt in program.statements:
            self.visit(stmt)

        return "\n".join(self.code)

    # -------------------------
    # Dispatcher
    # -------------------------
    def visit(self, node):
        if isinstance(node, VarDecl):
            return self.visit_vardecl(node)

        if isinstance(node, AssignStmt):
            return self.visit_assign(node)

        if isinstance(node, OutputStmt):
            return self.visit_output(node)

        if isinstance(node, BinOp):
            return self.visit_binop(node)

        if isinstance(node, IfStmt):
            return self.visit_if(node)

        if isinstance(node, WhileStmt):
            return self.visit_while(node)

        if isinstance(node, Block):
            return self.visit_block(node)

        if isinstance(node, Identifier):
            return self.visit_identifier(node)

        if isinstance(node, Literal):
            return self.visit_literal(node)

        raise Exception(f"CodeGen: Unknown node type {type(node)}")

    # -------------------------
    # VarDecl: var_type, name, value
    # -------------------------
    def visit_vardecl(self, node: VarDecl):
        if node.value is None:
            # default initialize to 0
            self.emit(f"{node.name} = 0")
            return node.name
        else:
            rhs = self.visit(node.value)
            self.emit(f"{node.name} = {rhs}")
            return node.name

    # -------------------------
    # AssignStmt: name, expr
    # -------------------------
    def visit_assign(self, node: AssignStmt):
        rhs = self.visit(node.expr)
        self.emit(f"{node.name} = {rhs}")
        return node.name

    # -------------------------
    # OutputStmt: OUTPUT(expr)
    # -------------------------
    def visit_output(self, node: OutputStmt):
        operand = self.visit(node.expr)
        self.emit(f"OUTPUT {operand}")
        return None

    # -------------------------
    # BinOp: left, op, right
    # returns a temporary name (or literal/identifier string)
    # -------------------------
    def visit_binop(self, node: BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)

        # if left/right are None (shouldn't happen), guard
        if left is None:
            left = "0"
        if right is None:
            right = "0"

        # if left/right are plain numbers or identifiers, use them; otherwise they are temps
        temp = self.new_temp()
        self.emit(f"{temp} = {left} {node.op} {right}")
        return temp

    # -------------------------
    # IfStmt: condition, true_branch (Block), optional false_branch
    # -------------------------
    def visit_if(self, node: IfStmt):
        cond = self.visit(node.condition)         # cond should be an operand or temp
        else_label = self.new_label("Lelse")
        end_label = self.new_label("Lend")

        # if cond is 0 -> goto else
        self.emit(f"IFZ {cond} GOTO {else_label}")

        # true branch
        self.visit(node.true_branch)
        self.emit(f"GOTO {end_label}")

        # else branch
        self.emit(f"{else_label}:")
        if node.false_branch is not None:
            self.visit(node.false_branch)

        # end label
        self.emit(f"{end_label}:")
        return None

    # -------------------------
    # WhileStmt: condition, body (Block)
    # -------------------------
    def visit_while(self, node: WhileStmt):
        start = self.new_label("Lstart")
        end = self.new_label("Lend")

        self.emit(f"{start}:")
        cond = self.visit(node.condition)
        self.emit(f"IFZ {cond} GOTO {end}")

        # body
        self.visit(node.body)
        self.emit(f"GOTO {start}")
        self.emit(f"{end}:")
        return None

    # -------------------------
    # Block: list of statements
    # -------------------------
    def visit_block(self, node: Block):
        for s in node.statements:
            self.visit(s)
        return None

    # -------------------------
    # Identifier: return its name
    # -------------------------
    def visit_identifier(self, node: Identifier):
        return node.name

    # -------------------------
    # Literal: return literal textual representation
    # -------------------------
    def visit_literal(self, node: Literal):
        # If literal value already a string like '111', keep it
        return str(node.value)
