# my_ast.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Node:
    pass

# Program Root
@dataclass
class Program(Node):
    statements: List[Node]

# Statements
@dataclass
class VarDecl(Node):
    var_type: str
    name: str
    value: Optional[Node] = None

@dataclass
class AssignStmt(Node):
    name: str
    expr: Node

@dataclass
class OutputStmt(Node):
    expr: Node

@dataclass
class IfStmt(Node):
    condition: Node
    true_branch: Node
    false_branch: Optional[Node] = None

@dataclass
class WhileStmt(Node):
    condition: Node
    body: Node

@dataclass
class Block(Node):
    statements: List[Node]

# Expressions
@dataclass
class BinOp(Node):
    left: Node
    op: str
    right: Node

@dataclass
class Identifier(Node):
    name: str

@dataclass
class Literal(Node):
    value: str
