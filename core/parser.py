from lexer import *
import errorHandler

class Parser():
    def __init__(self, memory:bytearray, memorysize:int, tokens:list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.mem = memory
        self.memoffset = 0
        self.memsize = memorysize

    def include(self, file:str) -> None:
        code = ""
        with open(file, "rb") as f:
            f.seek(0)
            code = f.read()
        
        lex = Lexer(code)
        newTokens = lex.tokenize()

        newTokens.pop(len(newTokens) - 1) # Remove EOF
        for i, v in enumerate(newTokens):
            self.tokens.insert(i, v)

    def run(self, lang:str, code:str):
        if lang == "python" or lang == "py":
            exec(code)
            return

    def parse(self) -> None:
        skip = 0
        
        for i, v in enumerate(self.tokens):
            typ = v[0]
            val = v[1]

            if skip > 0:
                skip -= 1
                continue
            
            if typ == TOK_EOF:
                break

            if typ == TOK_INC:
                self.include(val)
            elif typ == TOK_RUNLANG:
                skip = 1
                self.run(val, self.tokens[i + 1][1])
            else:
                pass