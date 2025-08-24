# This file is made by AkshuDev!
# I really need to learn how to add comments
# I remade the whole Parser again because why not

from typing import List, Tuple, Optional
import errorHandler
from lexer import *

ptr_size = 64 # bits

# === Pointer ===
def set_ptr_len(len:int) -> None:
    global ptr_size
    ptr_size = len

def ptr_len() -> int:
    global ptr_size
    return ptr_size

# === AST Node Classes ===
class Expr: pass

class RunLang(Expr):
    def __init__(self, langauge: str, code: str, vars: List[str]):
        self.language = langauge
        self.code = code
        self.vars = vars
    def __repr__(self):
        return f"RunLang(lang={self.language}, code={self.code!r}), vars={self.vars})"

class Number(Expr):
    def __init__(self, value: int): self.value = int(value)
    def __repr__(self): return f"Number({self.value})"

class String(Expr):
    def __init__(self, value: str): self.value = value
    def __repr__(self): return f"String({self.value!r})"

class Bool(Expr):
    def __init__(self, value: str): self.value = (value == "true")
    def __repr__(self): return f"Bool({self.value})"

class Var(Expr):
    def __init__(self, name: str): self.name = name
    def __repr__(self): return f"Var({self.name})"

class VarDecl(Expr):
    def __init__(self, var_type: str, name: str, value: Optional[Expr], global_: bool = False, ptr: bool = False):
        self.var_type, self.name, self.value, self.global_, self.ptr = var_type, name, value, global_, ptr
        self.len = 0 # in bits

        if self.var_type == TOK_CHAR or self.var_type == TOK_BYTE:
            self.len = 8
        elif self.var_type == TOK_WORD:
            self.len = 16
        elif (self.var_type == TOK_INT or self.var_type == TOK_UINT) or self.var_type == TOK_DWORD:
            self.len = 32
        elif self.var_type == TOK_QWORD or self.var_type == TOK_LONG:
            self.len = 64
        else:
            errorHandler.error(f"Unkown variable type: {self.var_type} with value: {self.value}")

        if self.ptr:
            self.len = ptr_len()
    def __repr__(self):
        return f"VarDecl(type={self.var_type}, name={self.name}, value={self.value})"

class BinaryOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left, self.op, self.right = left, op, right
    def __repr__(self): return f"BinaryOp({self.left}, {self.op}, {self.right})"

class Assignment(Expr):
    def __init__(self, name: str, value: Expr):
        self.name, self.value = name, value
    def __repr__(self): return f"Assignment({self.name}, {self.value})"

class ReturnStmt(Expr):
    def __init__(self, value: Optional[Expr]): self.value = value
    def __repr__(self): return f"Return({self.value})"

# === Parser ===
class Parser:
    def __init__(self, tokens: List[Tuple[str,str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Tuple[str,str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (TOK_EOF, "")

    def advance(self) -> Tuple[str,str]:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, typ: str) -> Tuple[str,str]:
        tok = self.advance()
        if tok[0] != typ:
            errorHandler.error(f"Expected {typ}, got {tok}")
        return tok

    # === Expression Parsing ===
    def parse_expr(self, prec=0) -> Expr:
        left = self.parse_primary()

        while True:
            op = self.peek()[0]
            op_prec = self.get_precedence(op)
            if op_prec < prec: break
            self.advance()
            right = self.parse_expr(op_prec+1)
            left = BinaryOp(left, op, right)

        return left

    def parse_primary(self) -> Expr:
        typ, val = self.advance()
        if typ == TOK_LIT_INT:
            return Number(val)
        elif typ == TOK_LIT_STRING:
            return String(val)
        elif typ == TOK_LIT_BOOL:
            return Bool(val)
        elif typ == TOK_IDENTIFIER:
            # Could be assignment
            if self.peek()[0] == TOK_ASSIGN:
                self.advance()
                expr = self.parse_expr()
                return Assignment(val, expr)
            return Var(val)
        elif typ == TOK_LPAR:
            expr = self.parse_expr()
            self.expect(TOK_RPAR)
            return expr
        else:
            errorHandler.error(f"Unexpected token in expression: {typ}:{val}")

    def get_precedence(self, op: str) -> int:
        prec_table = {
            TOK_ASSIGN: 1,
            TOK_PLUS: 10, TOK_SUB: 10,
            TOK_MUL: 20, TOK_DIV: 20,
        }
        return prec_table.get(op, -1)
    
    # === Running another Language ===
    def parse_runlang(self) -> RunLang:
        _, lang = self.advance() # consume
        if self.peek()[0] == TOK_ENDL: self.advance()

        self.expect(TOK_CODE_BLOCK_OPEN)
        if self.peek()[0] == TOK_ENDL: self.advance()
        
        code_tok = self.expect(TOK_LIT_STRING)
        if self.peek()[0] == TOK_ENDL: self.advance()
        
        code = code_tok[1]

        # Format the string
        vars_list = []
        while self.peek()[0] not in [TOK_CODE_BLOCK_CLOSE, TOK_EOF]:
            if self.peek()[0] == TOK_LIT_STRING:
                _, val = self.advance()
                vars_list.append((TOK_LIT_STRING, val))
            elif self.peek()[0] == TOK_IDENTIFIER:
                _, name = self.advance()
                vars_list.append((TOK_IDENTIFIER, name))
            elif self.peek()[0] == TOK_LIT_CHAR:
                _, val = self.advance()
                vars_list.append((TOK_LIT_CHAR, val))
            else:
                self.advance() # Skip unknown

        self.expect(TOK_CODE_BLOCK_CLOSE)
        return RunLang(lang, code, vars_list)

    # === Statements ===
    def parse_stmt(self) -> Expr:
        typ, val = self.peek()
        glb = False

        if typ == TOK_GLOBAL:
            glb = True
            self.advance() # consume 'global'

        if typ == TOK_LET:
            self.advance()  # consume 'let'

            # expect type (int, char, uint, etc.)
            type_tok = self.advance()
            ptr = False

            if type_tok[0] not in [TOK_INT, TOK_UINT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BIT, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                errorHandler.error(f"Expected type after 'let', got {type_tok}")

            var_type = type_tok[0]

            if self.peek()[0] == TOK_MUL:
                ptr = True
                self.advance() # consume

            # now variable name
            name = self.expect(TOK_IDENTIFIER)[1]

            # optional initializer
            if self.peek()[0] == TOK_ASSIGN:
                self.advance()
                expr = self.parse_expr()
                return VarDecl(var_type, name, expr, glb, ptr)

            return VarDecl(var_type, name, None, glb, ptr)

        elif typ == TOK_RETURN:
            self.advance()
            if self.peek()[0] in [TOK_ENDL, TOK_EOF]:
                return ReturnStmt(None)
            expr = self.parse_expr()
            return ReturnStmt(expr)
        
        elif typ == TOK_RUNLANG:
            return self.parse_runlang()

        else:
            return self.parse_expr()

    def parse(self) -> List[Expr]:
        stmts = []
        while self.peek()[0] != TOK_EOF:
            stmt = self.parse_stmt()
            stmts.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        return stmts
