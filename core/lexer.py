import errorHandler

# Special
TOK_ENDL = "ENDL"
TOK_EOF = "EOF"
TOK_ASSIGN = "ASSIGN"
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
TOK_LIT_BOOL = "BOOLLIT"
TOK_FORMAT_VAR = "FORMATVAR"
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
# Code Blocks and such
TOK_CODE_BLOCK_OPEN = "CODEBLOCKOPEN"
TOK_CODE_BLOCK_CLOSE = "CODEBLOCKCLOSE"
TOK_LPAR = "LPAR"
TOK_RPAR = "RPAR"
# More Special
TOK_SET = "SET"
TOK_LET = "LET"
TOK_INC = "INC"
TOK_FUNCDEF = "FUNCDEF"
TOK_IDENTIFIER = "IDENTIFIER"
TOK_RETURN = "RETURN"
# Data types
TOK_VOID = "VOID"
TOK_INT = "INT"
TOK_UINT = "UINT"
TOK_CHAR = "CHAR"
TOK_BOOL = "BOOL"

def toBool(val:bool) -> int:
    if val == True: return 1
    return 0

def toBoolStr(val:bool) -> str:
    if val == True: return "true"
    return "false"

def intToBool(val:int) -> bool:
    if val == 1: return True
    return 0

class Lexer():
    def __init__(self, code:str) -> None:
        self.code = code
        self.offset = 0
        self.lineno = 1
        
        self.tokens:list[tuple[str, str]] = []
    
    def peek(self) -> str:
        if len(self.code) - 1 > self.offset:
            return self.code[self.offset]
    
    def get(self) -> str:
        return self.code[self.offset]
    
    def advance(self) -> str:
        val = self.peek()
        if val:
            self.offset += 1
            return val
        else:
            self.offset += 1 # We still do it so the lexer knows it is eof
            return None
        
    def getString(self) -> str:
        c = self.get()
        if not c == "\"": return None
        self.advance()

        res = ""

        while True:
            c = self.get()

            if c == "\"":
                break

            if c == "\\":
                self.advance()
                c = self.get()

                if c == "n":
                    res += "\\n"
                    self.advance()
                    continue
                elif c == "t":
                    res += "\\t"
                    self.advance()
                    continue
                else:
                    res += c
                    self.advance()
                    continue

            res += c
            self.advance()
        return res
    
    def getInt(self) -> int:
        c = self.get()

        if not c.isdigit(): return None
        res = ""
        while c.isdigit():
            c = self.get()
            if not c.isdigit(): break
            res += c
            self.advance()
        
        return int(res)
    
    def get_last(self) -> tuple[str, str]: # Returns token
        return self.tokens[len(self.tokens) - 1]
        
    def makeToken(self, tok:str, inst:str) -> None:
        self.tokens.append((tok, inst))

    def handlemctokens(self) -> None:
        s = ""
        while True:
            c = self.get()
            if not c in "@_$:abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if c == "\n":
                    self.lineno += 1
                break

            s += c
            self.advance()

        if s == "mov":
            self.makeToken(TOK_MOV, s)
        elif s == "movb":
            self.makeToken(TOK_MOVB, s)
        elif s == "movn":
            self.makeToken(TOK_MOVN, s)
        elif s == "movbn":
            self.makeToken(TOK_MOVBN, s)
        elif s == "ret":
            self.makeToken(TOK_RETURN, s)
        elif s == "@inc":
            self.makeToken(TOK_INC, s)
        elif s == "__py__:":
            self.makeToken(TOK_RUNLANG, "python")
        elif s == "func":
            self.makeToken(TOK_FUNCDEF, s)
        elif s == "void":
            self.makeToken(TOK_VOID, s)
        elif s == "int":
            self.makeToken(TOK_INT, s)
        elif s == "uint":
            self.makeToken(TOK_UINT, s)
        elif s == "char":
            self.makeToken(TOK_CHAR, s)
        elif s.startswith("$"):
            self.makeToken(TOK_FORMAT_VAR, s)
        elif s == "let":
            self.makeToken(TOK_LET, s)
        elif s == "true":
            self.makeToken(TOK_LIT_BOOL, s)
        elif s == "false":
            self.makeToken(TOK_LIT_BOOL, s)
        else:
            self.makeToken(TOK_IDENTIFIER, s)

    def tokenize(self) -> list:
        c:str = self.get()
        i = self.offset
        comment = False

        while True:
            i = self.offset
            if len(self.code) <= i:
                self.makeToken(TOK_EOF, "")
                break

            c = self.get()

            if comment and c == "\n":
                comment = False
                self.advance()
                continue
            if comment:
                self.advance()
                continue

            if c == "\n":
                if self.get_last()[0] == TOK_ENDL:
                    self.advance()
                    self.lineno += 1 # For \n only
                    continue
                self.makeToken(TOK_ENDL, c)
                self.advance()
                self.lineno += 1
                continue
            elif c == ";":
                if self.get_last()[0] == TOK_ENDL:
                    self.advance()
                    continue
                self.makeToken(TOK_ENDL, c)
                self.advance()
                continue
            elif c in " \t":
                self.advance()
                continue
            elif c == "#":
                if self.peek() == "#":
                    comment = True
                    continue
            elif c == "+":
                self.makeToken(TOK_PLUS, c)
                self.advance()
                continue
            elif c == "-":
                self.makeToken(TOK_SUB, c)
                self.advance()
                continue
            elif c == "*":
                self.makeToken(TOK_MUL, c)
                self.advance()
                continue
            elif c == "/":
                self.makeToken(TOK_DIV, c)
                self.advance()
                continue
            elif c == "\"":
                self.makeToken(TOK_LIT_STRING, self.getString())
                self.advance() #Consume '"'
                continue
            elif c.isdigit():
                self.makeToken(TOK_LIT_INT, self.getInt())
                continue
            elif c == "{":
                self.makeToken(TOK_CODE_BLOCK_OPEN, c)
                self.advance()
                continue
            elif c == "}":
                self.makeToken(TOK_CODE_BLOCK_CLOSE, c)
                self.advance()
                continue
            elif c == "(":
                self.makeToken(TOK_LPAR, c)
                self.advance()
                continue
            elif c == ")":
                self.makeToken(TOK_RPAR, c)
                self.advance()
                continue
            elif c == "=":
                self.makeToken(TOK_ASSIGN, c)
                self.advance()
                continue
            elif c.isalnum() or (c in "@_$"):
                self.handlemctokens()
            else:
                errorHandler.error(f"Unknown Character at {self.lineno}/{self.offset}: {c}")

        return self.tokens