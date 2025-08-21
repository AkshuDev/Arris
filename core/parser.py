import os
from typing import *

from lexer import *
import errorHandler

FUNCS:dict[str, dict] = {}
VARS:dict[str, dict] = {"global": {}}
VARS_L:list[tuple[str, str]] = []

class Parser():
    def __init__(self, memory:bytearray, memorysize:int, tokens:list[tuple[str, str]], incDirs:list[str]) -> None:
        self.tokens = tokens
        self.mem = memory
        self.memoffset = 0
        self.memsize = memorysize
        self.incDirs = incDirs
        self.incDirs.append(os.path.dirname(os.path.dirname(__file__)))

    def include(self, file:str, area:str) -> None:
        code = ""
        path = file

        for v in self.incDirs:
            if os.path.exists(os.path.join(v, file)):
                path = os.path.join(v, file)
                break

        with open(os.path.abspath(path), "r") as f:
            f.seek(0)
            code = f.read()
        
        lex = Lexer(code)
        newTokens = lex.tokenize()

        self.parse_toks(newTokens, area)

    def run(self, lang:str, code:str):
        if lang == "python" or lang == "py":
            exec(code)
            return
        
    def addVar(self, name:str, type:str, data:str, area:str, pointer=False) -> None:
        try:
            VARS[area]
        except KeyError:
            VARS[area] = {}
        
        VARS[area][name] = {"type": type, "value": data, "ptr": pointer}

    def getVar(self, name:str, area:str) -> dict:
        val = VARS["global"].get(name, None)
        if val:
            return val
        else:
            if VARS.get(area, None) == None:
                return None
            return VARS[area].get(name, None)

    def addFunc(self, name:str, ret:str, params:list[(str, str)], code_tokens:list[tuple[str, str]]) -> None:
        FUNCS[name] = {"returnType": ret, "params": params, "code": code_tokens}
    
    def getFunc(self, name:str, area:str) -> dict:
        try:
            return FUNCS[name]
        except KeyError:
            return None
        
    def formatStr(self, tokens:list[tuple[str, str]], offset:int, area:str) -> str:
        i = offset + 1 # To get the variables
        format_l = []
        var_l = []
        
        while True:
            typ = tokens[i][0]
            val = tokens[i][1]

            if not typ in [TOK_IDENTIFIER, TOK_LIT_STRING, TOK_LIT_CHAR, TOK_LIT_INT, TOK_LIT_UINT]:
                break

            var_l.append((typ, val))
            i += 1

        coff = 0
        for char in tokens[offset][1]:
            if char == "$":
                format_l.append(coff)
            coff += 1

        if not len(var_l) == len(format_l):
            errorHandler.error("Extra or Less variables passed onto the string for formatting.")
        
        res = tokens[offset][1].replace("\"", "")
        old_len = 0
        for i, v in enumerate(format_l):
            val = ""

            if var_l[i][0] == TOK_IDENTIFIER:
                val = self.getVar(var_l[i][1], area)
                if val == None:
                    errorHandler.error("Unknown Variable: " + var_l[i][1])
                val = val["value"]
            else:
                val = var_l[i][1]

            if val == None:
                errorHandler.error("Unknown Error Occured here: " + var_l[i][1])

            res = res[:v] + val + res[v + 1:]
            if not i == len(format_l) - 1:
                format_l[i + 1] = format_l[i + 1] + old_len  + (len(val) - 1)
                old_len += (len(val) - 1)

        return res
        
    def runFunc(self, name:str, paramsPassed:list, area:str) -> tuple[str, str]:
        func = self.getFunc(name, area)
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
                self.addVar(param[1], param[0], paramsPassed[i][1], name)

        return self.parse_toks(func["code"], name)

    def parse_toks(self, tokens:list[tuple[str, str]], area:str="global") -> Optional[tuple[str, str]]:
        skip = 0
        i = -1
        
        while True:
            if i + 1 >= len(tokens):
                break # Just incase

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
                self.include(tokens[i + 1][1], area)
            elif typ == TOK_RUNLANG:
                skip = 1
                if tokens[i + 2][0] == TOK_ENDL:
                    self.run(val, self.formatStr(tokens, i + 3, area))
                else:
                    self.run(val, self.formatStr(tokens, i + 2, area))
            elif typ == TOK_IDENTIFIER:
                if tokens[i + 1][0] == TOK_LPAR:
                    # Get all params
                    pi = i + 2 # Param Index
                    skip = 2
                    params = []
                    while True:
                        ptyp = tokens[pi][0]
                        pval = tokens[pi][1]

                        if ptyp == TOK_RPAR:
                            skip += 1
                            break

                        if ptyp == TOK_IDENTIFIER:
                            pval = self.getVar(pval, area)
                            if pval == None:
                                errorHandler.error("Unknown variable: " + tokens[pi][1])
                            params.append((pval["type"], pval["value"]))
                        else:
                            params.append((ptyp, pval))
                        
                        pi += 1
                        skip += 1
                    
                    self.runFunc(val, params, area)

                elif tokens[i + 1][0] == TOK_ASSIGN:
                    data = tokens[i + 2][1]
                    details = self.getVar(val, area)

                    if details == None:
                        errorHandler.error("Unknown variable: " + val)

                    if tokens[i + 2][0] == TOK_IDENTIFIER:
                        dtype = self.getVar(data, area)
                        if dtype == None:
                            errorHandler.error("Unknown variable: " + val)
                        dtype = dtype["type"]

                        if not dtype == details["type"]:
                            errorHandler.error("Assinging Variable Type doesn't match the Assignment Variable type: " + val)
                        
                        data = self.getVar(data, area)

                    self.addVar(val, details["type"], data, area, pointer=details["ptr"])
                    skip = 2
                else:
                    pass # You not gonna do anything with just about now
            elif typ == TOK_FUNCDEF:
                code_tokens = []
                rettyp = tokens[i + 1][0]
                name = tokens[i + 2][1]
                params = []
                skip = 2

                if tokens[i + 3][0] == TOK_LPAR:
                    skip += 1
                    pi = i + 4
                    while True:
                        ptyp = tokens[pi][0]
                        pval = tokens[pi][1]

                        if ptyp == TOK_RPAR:
                            skip += 1
                            break
                        elif tokens[pi + 1][0] == TOK_RPAR:
                            skip += 1
                            pi += 1
                            break
                        
                        if tokens[pi + 1][0] == TOK_MUL:
                            pi += 1
                        params.append((ptyp, tokens[pi + 1][1]))
                        pi += 2
                        skip += 2

                    if tokens[pi + 1][0] == TOK_CODE_BLOCK_OPEN:
                        pi = pi + 2
                        while True:
                            if tokens[pi][0] == TOK_CODE_BLOCK_CLOSE:
                                skip += 1
                                break
                            code_tokens.append(tokens[pi])
                            skip += 1
                            pi += 1
                    
                    self.addFunc(name, rettyp, params, code_tokens)

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
            elif typ == TOK_LET:
                datatype = tokens[i + 1][0] # Get the type of var
                ptr = False
                
                if tokens[i + 2][0] == TOK_MUL:
                    ptr = True
                    i += 1

                name = tokens[i + 2][1]
                nametyp = tokens[i + 2][0]
                if not nametyp == TOK_IDENTIFIER:
                    errorHandler.error("Incorrect variable name usage: " + name)
                
                asn = tokens[i + 3][0]
                if not asn == TOK_ASSIGN:
                    self.addVar(name, datatype, None, area, pointer=ptr)
                else:
                    val = tokens[i + 4][1]
                    self.addVar(name, datatype, val, area, pointer=ptr)

                if ptr:
                    i -= 1
                    skip += 1
                
                skip += 4

            else:
                pass

    def parse(self) -> None:
        import platform
        import sys

        self.addVar("__OS__", TOK_LIT_STRING, platform.platform(), "global")
        self.addVar("__ARCH__", TOK_LIT_STRING, platform.machine(), "global")
        self.addVar("__LIB__", TOK_LIT_BOOL, toBoolStr(False), "global")
        return self.parse_toks(self.tokens)