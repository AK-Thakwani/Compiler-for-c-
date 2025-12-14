# parser.py
from my_ast import *
  # make sure your AST module is named ast.py (not my_ast)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -----------------------------
    # Utility (safe peek/advance/previous)
    # -----------------------------
    def peek(self):
        if self.pos >= len(self.tokens):
            return ("EOF", "EOF")
        return self.tokens[self.pos]

    def advance(self):
        # move forward and return current token (safe)
        self.pos += 1
        return self.peek()

    def previous(self):
        if self.pos - 1 < 0:
            return ("EOF", "EOF")
        return self.tokens[self.pos - 1]

    def match(self, kind, value=None):
        tok = self.peek()
        if tok[0] != kind:
            return False
        if value is not None and tok[1] != value:
            return False
        # consume
        self.advance()
        return True

    def expect(self, kind, value=None):
        tok = self.peek()
        if tok[0] != kind:
            raise SyntaxError(f"Expected token type {kind}, found {tok}")
        if value is not None and tok[1] != value:
            raise SyntaxError(f"Expected token value '{value}', found '{tok[1]}'")
        self.advance()
        return self.previous()  # return the consumed token

    # -----------------------------
    # Program
    # -----------------------------
    def parse(self):
        stmts = []
        while self.peek()[0] != "EOF":
            stmts.append(self.statement())
        return Program(stmts)

    # -----------------------------
    # Statements
    # -----------------------------
    def statement(self):
        tok = self.peek()

        if tok[0] == "VAR":
            return self.var_decl()

        if tok[0] == "OUTPUT":
            return self.output_stmt()

        if tok[0] == "ID":
            # could be assignment or function call (we only support assignment)
            return self.assign_stmt()

        if tok[0] == "IF":
            return self.if_stmt()

        if tok[0] == "WHILE":
            return self.while_stmt()

        if tok[0] == "PUNC" and tok[1] == "{":
            return self.block()

        raise SyntaxError(f"Unexpected token in statement: {tok}")

    # VAR <type> <name> (= expr)? ;
    def var_decl(self):
        self.expect("VAR")
        # Types (INT/FLOAT/...) are tokenized as ID (unless you add them as keywords).
        type_tok = self.expect("ID")
        var_type = type_tok[1]

        name_tok = self.expect("ID")
        name = name_tok[1]

        value = None
        if self.match("OP", "="):
            value = self.expr()

        self.expect("PUNC", ";")
        return VarDecl(var_type, name, value)

    # assignment: ID = expr ;
    def assign_stmt(self):
        name_tok = self.expect("ID")
        name = name_tok[1]

        self.expect("OP", "=")
        expr = self.expr()
        self.expect("PUNC", ";")
        return AssignStmt(name, expr)

    # OUTPUT(expr);
    def output_stmt(self):
        self.expect("OUTPUT")
        self.expect("PUNC", "(")
        expr = self.expr()
        self.expect("PUNC", ")")
        self.expect("PUNC", ";")
        return OutputStmt(expr)

    # IF (cond) block (ELSE block)?
    def if_stmt(self):
        self.expect("IF")
        self.expect("PUNC", "(")
        condition = self.expr()
        self.expect("PUNC", ")")
        true_block = self.block()

        false_block = None
        # match can take either ELSE (keyword) — ensure lexer uses token "ELSE"
        if self.match("ELSE"):
            false_block = self.block()

        return IfStmt(condition, true_block, false_block)

    # WHILE (cond) block
    def while_stmt(self):
        self.expect("WHILE")
        self.expect("PUNC", "(")
        condition = self.expr()
        self.expect("PUNC", ")")
        body = self.block()
        return WhileStmt(condition, body)

    # { stmt* }
    def block(self):
        self.expect("PUNC", "{")
        stmts = []
        # keep parsing statements until we find the closing '}'
        while not (self.peek()[0] == "PUNC" and self.peek()[1] == "}"):
            # safety: if EOF encountered before '}', raise error
            if self.peek()[0] == "EOF":
                raise SyntaxError("Unexpected EOF inside block; '}' expected")
            stmts.append(self.statement())
        # consume '}'
        self.expect("PUNC", "}")
        return Block(stmts)

    # -----------------------------
    # Expression Grammar (precedence)
    # expr -> equality
    # equality -> comparison ( (== | !=) comparison )*
    # comparison -> term ( (< | > | <= | >=) term )*
    # term -> factor ( (+ | -) factor )*
    # factor -> unary ( (* | /) unary )*
    # unary -> ( + | - ) unary | primary
    # primary -> INT | ID | ( expr )
    # -----------------------------
    def expr(self):
        return self.equality()

    def equality(self):
        node = self.comparison()
        while True:
            if self.match("OP", "==") or self.match("OP", "!="):
                op = self.previous()[1]
                right = self.comparison()
                node = BinOp(node, op, right)
            else:
                break
        return node

    def comparison(self):
        node = self.term()
        while True:
            if (self.match("OP", "<") or self.match("OP", ">") or
                self.match("OP", "<=") or self.match("OP", ">=")):
                op = self.previous()[1]
                right = self.term()
                node = BinOp(node, op, right)
            else:
                break
        return node

    def term(self):
        node = self.factor()
        while True:
            if self.match("OP", "+") or self.match("OP", "-"):
                op = self.previous()[1]
                right = self.factor()
                node = BinOp(node, op, right)
            else:
                break
        return node

    def factor(self):
        node = self.unary()
        while True:
            if self.match("OP", "*") or self.match("OP", "/"):
                op = self.previous()[1]
                right = self.unary()
                node = BinOp(node, op, right)
            else:
                break
        return node

    def unary(self):
        # support unary + / - (optional; useful)
        if self.match("OP", "-"):
            op = self.previous()[1]
            right = self.unary()
            return BinOp(Literal("0"), op, right)  # represent -x as 0 - x
        if self.match("OP", "+"):
            return self.unary()
        return self.primary()

    def primary(self):
        # Use previous() after match to get the consumed token's value
        if self.match("INT"):
            val = self.previous()[1]
            return Literal(val)
        if self.match("ID"):
            val = self.previous()[1]
            return Identifier(val)
        if self.match("PUNC", "("):
            node = self.expr()
            self.expect("PUNC", ")")
            return node

        tok = self.peek()
        raise SyntaxError(f"Unexpected token in primary(): {tok}")
