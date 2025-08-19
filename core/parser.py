import os

from lexer import *
import errorHandler

FUNCS:dict[str, dict] = {}

class Parser():
    def __init__(self, memory:bytearray, memorysize:int, tokens:list[tuple[str, str]], basedir:str) -> None:
        self.tokens = tokens
        self.mem = memory
        self.memoffset = 0
        self.memsize = memorysize
        self.basedir = basedir

    def include(self, file:str, offset:int) -> int:
        code = ""
        with open(os.path.join(self.basedir, file), "r") as f:
            f.seek(0)
            code = f.read()
        
        lex = Lexer(code)
        newTokens = lex.tokenize()

        newTokens.pop(len(newTokens) - 1) # Remove EOF
        for i, v in enumerate(newTokens):
            self.tokens.insert(i + (offset + 1), v)

        self.tokens.pop(offset)

        return offset - 1

    def run(self, lang:str, code:str):
        if lang == "python" or lang == "py":
            exec(code)
            return

    def parse(self) -> None:
        skip = 0
        i = -1
        
        while True:
            i += 1
            v = self.tokens[i]
            typ = v[0]
            val = v[1]

            if skip > 0:
                skip -= 1
                continue
            
            if typ == TOK_EOF:
                break

            if typ == TOK_INC:
                i = self.include(val, i)
            elif typ == TOK_RUNLANG:
                skip = 1
                self.run(val, self.tokens[i + 1][1])
            elif typ == TOK_FUNC:
                
            else:
                pass