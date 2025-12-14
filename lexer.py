# lexer.py
import re

class Lexer:
    def __init__(self, code):
        self.code = code

    token_spec = [
        ("WHILE", r"\bWHILE\b"),
        ("IF", r"\bIF\b"),
        ("ELSE", r"\bELSE\b"),
        ("OUTPUT", r"\bOUTPUT\b"),
        ("VAR", r"\bVAR\b"),

        # MULTI-CHAR OPERATORS
        ("OP_EQ", r"=="),
        ("OP_NE", r"!="),
        ("OP_LE", r"<="),
        ("OP_GE", r">="),

        # SINGLE-CHAR OPERATORS
        ("OP", r"[+\-*/=<>]"),

        # NUMBERS
        ("INT", r"\b\d+\b"),

        # IDENTIFIER
        ("ID", r"\b[A-Za-z_][A-Za-z0-9_]*\b"),

        # PUNCTUATION
        ("PUNC", r"[(){};]"),

        # SPACES / NEWLINES
        ("NEWLINE", r"\n"),
        ("SKIP", r"[ \t]+"),

        ("MISMATCH", r"."),
    ]

    def tokenize(self):
        tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.token_spec)
        tokens = []

        for m in re.finditer(tok_regex, self.code):
            kind = m.lastgroup
            value = m.group()

            if kind in ("SKIP", "NEWLINE"):
                continue

            if kind == "MISMATCH":
                raise RuntimeError(f"Unexpected character: {value}")

            # Normalize multi-ops to ("OP", actual)
            if kind == "OP_EQ": tokens.append(("OP", "==")); continue
            if kind == "OP_NE": tokens.append(("OP", "!=")); continue
            if kind == "OP_LE": tokens.append(("OP", "<=")); continue
            if kind == "OP_GE": tokens.append(("OP", ">=")); continue

            tokens.append((kind, value))

        tokens.append(("EOF", "EOF"))
        return tokens
