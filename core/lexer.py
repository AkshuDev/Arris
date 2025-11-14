from . import errorHandler
from typing import Optional

# Special
TOK_ENDL = "ENDL"
TOK_EOF = "EOF"
TOK_ASSIGN = "ASSIGN"
# conditional
TOK_EQUALS = "EQUALS"
TOK_GT = "GREATER_THAN"
TOK_LT = "LESS_THAN"
TOK_GTE = "GREATER_THAN_OR_EQUALS"
TOK_LTE = "LESS_THAN_OR_EQUALS"
TOK_NE = "NOT_EQUALS"
# Logical
TOK_AND = "AND"
TOK_NOT = "NOT"
TOK_OR = "OR"
TOK_NAND = "NAND"
TOK_NOR = "NOR"
TOK_SHL = "SHL"
TOK_SHR = "SHR"
# Conditional V2
TOK_IF = "IF"
TOK_WHILE = "WHILE"
TOK_FOR = "FOR"
# Array based
TOK_MOV = "MOV"
TOK_MOVN = "MOVN"
TOK_MOVB = "MOVB"
TOK_MOVBN = "MOVBN"
# Literals
TOK_LIT_CHAR = "CHARLIT"
TOK_LIT_STRING = "STRLIT"
TOK_LIT_INT = "INTLIT"
TOK_LIT_BOOL = "BOOLLIT"
TOK_FORMAT_VAR = "FORMATVAR"
# Data widths
TOK_BIT = "BIT"
TOK_BYTE = "BYTE"
TOK_DWORD = "DWORD"
TOK_WORD = "WORD"
TOK_QWORD = "QWORD"
# Signed/Unsigned
TOK_UNSIGNED = "UNSIGNED"
TOK_SIGNED = "SIGNED"
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
TOK_GLOBAL = "GLOBAL"
TOK_INC = "INC"
TOK_FUNCDEF = "FUNCDEF"
TOK_IDENTIFIER = "IDENTIFIER"
TOK_RETURN = "RETURN"
# Data types
TOK_VOID = "VOID"
TOK_INT = "INT"
TOK_CHAR = "CHAR"
TOK_BOOL = "BOOL"
TOK_LONG = "LONG"
# Special
TOK_COMMA = "COMMA"
# Macros and more
TOK_PREPROCESSOR = "PREPROCESSOR"
# Pointers
TOK_DEREF = "DEREF"

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
    def __init__(self, code:str, st_line:int=1, st_char:int=1, filename:Optional[str]=None) -> None:
        self.code = code
        self.offset = 0
        self.line = st_line
        self.char = st_char
        self.filename = filename
        
        self.tokens:list[tuple[str, str, int, int]] = []
    
    def peek(self) -> str:
        if len(self.code) - 1 > self.offset:
            return self.code[self.offset + 1]
    
    def get(self) -> str:
        return self.code[self.offset]
    
    def advance(self) -> str:
        val = self.peek()
        if val:
            self.offset += 1
            self.char += 1
            return val
        else:
            self.offset += 1 # We still do it so the lexer knows it is eof
            self.char += 1
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
                elif c == "$":
                    res += "\\$"
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
        
    def makeToken(self, tok:str, inst:str, line:int=None, char:int=None) -> None:
        l, c = self.line, self.char
        if line:
            l = line
        if char:
            c = char
        self.tokens.append((tok, inst, l, c))

    def handlemctokens(self) -> None:
        s = ""
        l, ch = self.line, self.char
        while True:
            c = self.get()
            if not c in "@_$:abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if c == "\n":
                    self.line += 1
                    self.char = 0
                break

            s += c
            self.advance()

        if s == "mov":
            self.makeToken(TOK_MOV, s, l, ch)
        elif s == "movb":
            self.makeToken(TOK_MOVB, s, l, ch)
        elif s == "movn":
            self.makeToken(TOK_MOVN, s, l, ch)
        elif s == "movbn":
            self.makeToken(TOK_MOVBN, s, l, ch)
        elif s == "ret":
            self.makeToken(TOK_RETURN, s, l, ch)
        elif s == "@inc":
            self.makeToken(TOK_INC, s, l, ch)
        elif s == "__py_simple__:":
            self.makeToken(TOK_RUNLANG, "python-simple", l, ch)
        elif s == "__py__:":
            self.makeToken(TOK_RUNLANG, "python", l, ch)
        elif s == "__c__":
            self.makeToken(TOK_RUNLANG, "c", l, ch)
        elif s == "__cpp__":
            self.makeToken(TOK_RUNLANG, "c++", l, ch)
        elif s == "__vasm__":
            self.makeToken(TOK_RUNLANG, "vasm", l, ch)
        elif s == "__asm__":
            self.makeToken(TOK_RUNLANG, "asm", l, ch)
        elif s == "func":
            self.makeToken(TOK_FUNCDEF, s, l, ch)
        elif s == "void":
            self.makeToken(TOK_VOID, s, l, ch)
        elif s == "bit":
            self.makeToken(TOK_BIT, s, l, ch)
        elif s == "dword":
            self.makeToken(TOK_DWORD, s, l, ch)
        elif s == "int":
            self.makeToken(TOK_INT, s, l, ch)
        elif s == "unsigned":
            self.makeToken(TOK_UNSIGNED, s, l, ch)
        elif s == "signed":
            self.makeToken(TOK_SIGNED, s, l, ch)
        elif s == "word":
            self.makeToken(TOK_WORD, s, l, ch)
        elif s == "char":
            self.makeToken(TOK_CHAR, s, l, ch)
        elif s == "byte":
            self.makeToken(TOK_BYTE, s, l, ch)
        elif s == "long":
            self.makeToken(TOK_LONG, s, l, ch)
        elif s.startswith("$"):
            self.makeToken(TOK_FORMAT_VAR, s, l, ch)
        elif s == "global":
            self.makeToken(TOK_GLOBAL, s, l, ch)
        elif s == "let":
            self.makeToken(TOK_LET, s, l, ch)
        elif s == "true":
            self.makeToken(TOK_LIT_BOOL, s, l, ch)
        elif s == "false":
            self.makeToken(TOK_LIT_BOOL, s, l, ch)
        elif s == "while":
            self.makeToken(TOK_WHILE, s, l, ch)
        elif s == "for":
            self.makeToken(TOK_FOR, s, l, ch)
        elif s == "if":
            self.makeToken(TOK_IF, s, l, ch)
        elif s.startswith("@"):
            self.makeToken(TOK_PREPROCESSOR, s, l, ch)
        else:
            self.makeToken(TOK_IDENTIFIER, s, l, ch)

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
                    self.line += 1 # For \n only
                    self.char = 0
                    continue
                self.makeToken(TOK_ENDL, c)
                self.advance()
                self.line += 1
                self.char = 0
                continue
            elif c == ";":
                if self.get_last()[0] == TOK_ENDL:
                    self.advance()
                    continue
                self.makeToken(TOK_ENDL, c)
                self.advance()
                continue
            elif c == ",":
                self.makeToken(TOK_COMMA, c)
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
                if self.peek() == "=":
                    self.makeToken(TOK_EQUALS, "==")
                    self.advance()
                    self.advance()
                    continue
                self.makeToken(TOK_ASSIGN, c)
                self.advance()
                continue
            elif c == "!":
                if self.peek() == "=":
                    self.makeToken(TOK_NE, "!=")
                    self.advance()
                    self.advance()
                    continue
                self.makeToken(TOK_NOT, c)
                self.advance()
                continue
            elif c == ">":
                if self.peek() == "=":
                    self.makeToken(TOK_GTE, ">=")
                    self.advance()
                    self.advance()
                    continue
                self.makeToken(TOK_GT, c)
                self.advance()
                continue
            elif c == "<":
                if self.peek() == "=":
                    self.makeToken(TOK_LTE, "<=")
                    self.advance()
                    self.advance()
                    continue
                self.makeToken(TOK_LT, c)
                self.advance()
                continue
            elif c == "'":
                char = self.advance()
                final_char = char

                if char == "\\":
                    # special
                    final_char += self.advance()
                    
                self.advance()
                self.makeToken(TOK_LIT_CHAR, final_char)
                self.advance() # consume '
            elif c == "&":
                self.makeToken(TOK_DEREF, c)
                self.advance()
                continue
            elif c.isalnum() or (c in "@_$"):
                self.handlemctokens()
            else:
                errorHandler.error("Unknown Character!", line=self.line, col=self.char, src=self.code, file=self.filename)

        return self.tokens