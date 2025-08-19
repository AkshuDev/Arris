import errorHandler

# Special
TOK_ENDL = "ENDL"
TOK_EOF = "EOF"
# Array based
TOK_MOV = "MOV"
TOK_MOVN = "MOVN"
TOK_MOVB = "MOVB"
TOK_MOVBN = "MOVBN"
# Literals
TOK_LIT_CHAR = "CHARLIT"
TOK_LIT_STRING = "STRLIT"
TOK_LIT_INT = "INTLIT"
TOK_LIT_UINT = "UINTLIT"
# Data widths
TOK_BIT = "BIT"
TOK_BYTE = "BYTE"
TOK_HWORD = "HWORD"
TOK_WORD = "WORD"
TOK_QWORD = "QWORD"
# Arithemetic
TOK_PLUS = "PLUS"
TOK_SUB = "SUB"
TOK_MUL = "MUL"
TOK_DIV = "DIV"
# Special Instructions
TOK_CLR = "CLR"
TOK_RUNLANG = "RUNLANG"
TOK_RUNLANGCODE = "RUNLANGCODE"
TOK_SET = "SET"
TOK_LET = "LET"
TOK_PTR = "PTR"
TOK_INC = "INC"
TOK_FUNC = "FUNC"
TOK_FUNCDEF = "FUNCDEF"
TOK_FUNCPARAM = "FUNCPARAM"
TOK_FUNCPARAMTYPE = "FUNCPARAMTYPE"
TOK_FUNCSTART = "FUNCSTART"
TOK_FUNCEND = "FUNCEND"
TOK_FUNCRET = "FUNCRET"
TOK_IDENTIFIER = "IDENTIFIER"
TOK_RETURN = "RETURN"

class Lexer():
    def __init__(self, code:str) -> None:
        self.code = code
        self.lines = code.splitlines(False)
        self.offset = 0
        self.instructions = []

        for v in self.lines:
            split = v.split(";")
            for inst in split:
                self.instructions.append(inst)

        self.tokens:list[tuple[str, str]] = []
    
    def peek(self) -> str:
        if len(self.instructions) > self.offset + 1:
            return self.instructions[self.offset + 1]
        else:
            return TOK_EOF
        
    def advance(self) -> str:
        inst = self.peek()
        if inst == TOK_EOF:
            return inst
        
        self.offset += 1
        return inst
    
    def get(self) -> str:
        if len(self.instructions) > self.offset:
            return self.instructions[self.offset]
        else:
            return TOK_EOF

    def getString(self, line:str) -> str:
        res = ""

        if not line.startswith("\""): return None

        for char in line:
            if char == "\"":
                break
            res += char

        return res
    
    def getInt(self, line:str) -> int:
        resS = ""

        for char in line:
            if not char.isdigit():
                break
            resS += char

        if resS == "": return None
        return int(resS)
        
    def makeToken(self, tok:str, inst:str) -> None:
        self.tokens.append((tok, inst))

    def tokenize(self) -> list:
        inst = self.get().strip("\t ")
        instParts = inst.split(" ")
        end = False
        fopen = False

        while not end:
            if end == True:
                break

            if instParts[0] == TOK_EOF:
                self.makeToken(TOK_EOF, "")
                end = True
                break

            if instParts[0] == "mov":
                self.makeToken(TOK_MOV, instParts[0])
            elif instParts[0] == "movn":
                self.makeToken(TOK_MOVN, instParts[0])
                if not len(instParts) > 1:
                    self.makeToken(TOK_LIT_INT, 1)
                else:
                    if not instParts[1].isdigit():
                        errorHandler.error("[Lexer]: MOVN instruction got a non-numerical value! at instruction: " + str(self.offset + 1) + "\n\t" + inst)
                    self.makeToken(TOK_LIT_INT, int(instParts[1]))
            elif instParts[0] == "movb":
                self.makeToken(TOK_MOVB, instParts[0])
            elif instParts[0] == "movbn":
                self.makeToken(TOK_MOVBN, instParts[0])
                if not len(instParts) > 1:
                    self.makeToken(TOK_LIT_INT, 1)
                else:
                    if not instParts[1].isdigit():
                        errorHandler.error("[Lexer]: MOVBN instruction got a non-numerical value! at instruction: " + str(self.offset + 1) + "\n\t" + inst)
                    self.makeToken(TOK_LIT_INT, int(instParts[1]))
                    self.advance()
            elif instParts[0] == "\n":
                self.makeToken(TOK_ENDL, inst)
            elif instParts[0] == "__py:":
                self.makeToken(TOK_RUNLANG, "python")
                if "{" not in inst:
                    codeInst = self.advance()
                    if codeInst != "{":
                        errorHandler.error("[Lexer]: '{' expected!\n\t"+inst)
                codeInst = self.advance()
                code = ""
                while "}" not in codeInst:
                    code += codeInst + "\n"
                    codeInst = self.advance()
                    if codeInst == TOK_EOF:
                        errorHandler.error("[Lexer]: '}' expected!\n\t"+inst)
                self.makeToken(TOK_RUNLANGCODE, code)
            elif instParts[0] == "@inc":
                if len(instParts) < 2:
                    errorHandler.error("[Lexer]: Must specify an include file!\n\t"+inst)
                
                include_path = inst.split["<"][1].replace(">", "")
                self.makeToken(TOK_INC, include_path)
            elif instParts[0] == "":
                pass
            elif instParts[0] == "##":
                pass
            elif instParts[0] == "func":
                if len(instParts) < 3:
                    errorHandler.error("[Lexer]: Invalid syntax!\n\t"+inst)
                
                ret = instParts[1]
                name = ""
                paramsStr = ""

                if "(" in instParts[2]:
                    name = instParts[2].split("(")[0]
                else:
                    name = instParts[2]
                
                self.makeToken(TOK_FUNCDEF, name)
                self.makeToken(TOK_FUNCRET, ret)

                for char in inst.split("(")[1]:
                    if char == ")":
                        break
                    paramsStr += char

                if paramsStr != "":
                    params_ = paramsStr.split(",")
                    for v in params_:
                        v = v.strip(" ")

                        param_d = v.split(" ")[0]
                        param_name = v.split(" ")[1]
                        self.makeToken(TOK_FUNCPARAMTYPE, param_d)
                        self.makeToken(TOK_FUNCPARAM, param_name)
                
                if "{" in inst:
                    pass
                else:
                    inst = self.advance()
                    if inst != "{":
                        errorHandler.error("[Lexer]: Expected '{'\n\t"+inst)
                
                self.makeToken(TOK_FUNCSTART, "{")
                fopen = True
            elif instParts[0] == "}" and fopen:
                fopen = False
                self.makeToken(TOK_FUNCEND, "}")
            elif instParts[0] == "ret":
                if len(instParts) < 2:
                    self.makeToken(TOK_VOID, "void")
                else:
                    self.makeToken(TOK_RETURN, )
            else:
                if "(" in inst and ")" in inst:
                    self.makeToken(TOK_FUNC, instParts[0].replace("(", "").replace(")", ""))
                    if not "()" in inst:
                        paramsStr = ""
                        paramfull = inst.split("(")[1]
                        
                        for char in paramfull:
                            if char == ")":
                                break
                            paramsStr += char

                        for v in paramsStr.split(","):
                            self.makeToken(TOK_FUNCPARAM, v.strip(" "))
                else:
                    self.makeToken(TOK_IDENTIFIER, instParts[0])
            
            inst = self.advance().strip("\t ")
            instParts = inst.split(" ")
        
        return self.tokens