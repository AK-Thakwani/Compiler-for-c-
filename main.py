from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer, SemanticError
from codegen import CodeGenerator
def main():
    # Read source code from test1.ss
    with open("test1.ss", "r") as f:
        source = f.read()

    print("SOURCE CODE:")
    print(source)
    print("\n--------------------------\n")

    # Step 1: Lexing
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    print("TOKENS:")
    for t in tokens:
        print(t)

    print("\n--------------------------\n")

    # Step 2: Parsing
    parser = Parser(tokens)
    ast = parser.parse()

    print("AST:")
    print(ast)

    print("\n--------------------------")
    print("SEMANTIC ANALYSIS:")

    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("✔ Semantic analysis passed with no errors.")
    except SemanticError as e:
        print("✘ Semantic Error:", e)
        exit(1)
    
# ...
    generator = CodeGenerator()
    tac_output = generator.generate(ast)
    print("\n=== 3-Address Code (TAC) ===")
    print(tac_output)
     

if __name__ == "__main__":
    main()
