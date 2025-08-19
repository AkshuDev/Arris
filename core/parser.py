import os
from typing import *

from lexer import *
import errorHandler

FUNCS:dict[str, dict] = {}
VARS:dict[str, dict] = {"global": {}}

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
            self.tokens.insert(i + (offset + 2), v)

        self.tokens.pop(offset)
        self.tokens.pop(offset + 1) # INC token requires 2 tokens

        return offset - 2

    def run(self, lang:str, code:str, area:str):
        if lang == "python" or lang == "py":
            exec(code)
            return
        
    def addVar(self, name:str, type:str, data:str, area:str) -> None:
        try:
            VARS[area]
        except KeyError:
            VARS[area] = {}
        
        VARS[area][name] = {"type": type, "value": data}

    def getVar(self, name:str, area:str) -> dict:
        val = VARS["global"].get(name, None)
        if val:
            return val
        else:
            if VARS.get(area, None) == None:
                return None
            return VARS[area].get(name, None)

    def addFunc(self, name:str, ret:str, params:list[str, str, str], code_tokens:list[tuple[str, str]]) -> None:
        FUNCS[name] = {"returnType": ret, "params": params, "code": code_tokens}
    
    def getFunc(self, name:str) -> dict:
        try:
            return FUNCS[name]
        except KeyError:
            return None
        
    def runFunc(self, name:str, paramsPassed:list) -> tuple[str, str]:
        func = self.getFunc(name)
        if func == None:
            errorHandler.error("[Parser]: No such function: " + name)
        
        params = func["params"]
        if params == None:
            self.parse_toks(func["code"], name)
        else:
            if len(paramsPassed) > len(params):
                errorHandler.error("[Parser]: Too many parameters passed to function "+name)
            elif len(paramsPassed) < len(params):
                errorHandler.error("[Parser]: Too less parameters passed to function "+name)
            for i, param in enumerate(params):
                self.addVar(param[1], param[0], paramsPassed[i])

        return self.parse_toks(func["code"], name)

    def parse_toks(self, tokens:list[tuple[str, str]], area:str="global") -> Optional[tuple[str, str]]:
        skip = 0
        i = -1
        
        while True:
            i += 1
            v = tokens[i]
            typ = v[0]
            val = v[1]

            if skip > 0:
                skip -= 1
                continue
            
            if typ == TOK_EOF:
                break

            if typ == TOK_INC:
                i = self.include(tokens[i + 1], i)
            elif typ == TOK_RUNLANG:
                skip = 1
                self.run(val, tokens[i + 1][1], area)
            elif typ == TOK_FUNC:
                pass
            elif typ == TOK_RETURN and not area == "global":
                if len(tokens) - 1 > i:
                    typ2 = tokens[i + 1]
                    val2 = tokens[i + 1]

                    if typ2 == TOK_IDENTIFIER:
                        data = self.getVar(val2, area)
                        return data
                    elif typ2 == TOK_LIT_CHAR:
                        return val2
                    elif typ2 == TOK_LIT_STRING:
                        return val2
                    elif typ2 == TOK_LIT_INT:
                        return val2
                    elif typ2 == TOK_LIT_UINT:
                        return val2
                    elif typ2 == TOK_FUNC:

                        return self.runFunc(val2, )

            else:
                pass

    def parse(self) -> None:
        return self.parse_toks(self.tokens)