import os
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

class Param(Expr):
    def __init__(self, var_type: str, name: str, ptr: bool = False):
        self.var_type = var_type
        self.name = name
        self.ptr = ptr
        self.len = 0
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
        return f"Param(type={self.var_type}, name={self.name}, ptr={self.ptr})"

class FuncDecl(Expr):
    def __init__(self, ret_type: str, name: str, params: List[Param], body: List[Expr]):
        self.ret_type = ret_type
        self.name = name
        self.params = params
        self.body = body
    def __repr__(self):
        return f"FuncDecl(ret={self.ret_type}, name={self.name}, params={self.params}, body={self.body})"

class FuncCall(Expr):
    def __init__(self, name: str, args: List[Expr]):
        self.name = name
        self.args = args
    def __repr__(self):
        return f"FuncCall(name={self.name}, args={self.args})"

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

class Cast(Expr):
    def __init__(self, target_type: str, expr: Expr):
        self.target_type = target_type
        self.expr = expr
    def __repr__(self):
        return f"Cast({self.target_type}, {self.expr})"

# === Parser ===
class Parser:
    def __init__(self, tokens: List[Tuple[str,str]], include_runlang=True):
        self.tokens = tokens
        self.pos = 0
        if include_runlang:
            code = ""
            with open (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stdlib", "runlang.alib"), "r") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            if tokens[-1][0] == TOK_EOF:
                tokens = tokens[:-1]
            self.inject_tokens(tokens)

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
    
    def inject_tokens(self, new_tokens: List[Tuple[str, str]]) -> None:
        self.tokens = self.tokens[:self.pos] + new_tokens + self.tokens[self.pos:]

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
            elif self.peek()[0] == TOK_LPAR:
                # func call
                self.advance() # consume '('
                args = []
                if self.peek()[0] != TOK_RPAR:
                    while True:
                        arg = self.parse_expr()
                        args.append(arg)
                        if self.peek()[0] == TOK_COMMA:
                            self.advance()
                        else:
                            break
                
                self.expect(TOK_RPAR)
                return FuncCall(val, args)
            return Var(val)
        elif typ == TOK_LPAR:
            # Lookahead for type-cast: (type)expr
            next_tok = self.peek()
            if next_tok[0] in [TOK_INT, TOK_UINT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE,
                            TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                # It's a cast
                type_tok = self.advance()
                target_type = type_tok[0]
                self.expect(TOK_RPAR)
                expr = self.parse_primary()
                return Cast(target_type, expr)
            else:
                # Normal parenthesized expression
                expr = self.parse_expr()
                self.expect(TOK_RPAR)
                return expr
        else:
            errorHandler.error(f"Unexpected token in expression: {typ}:{val} at {self.pos}")

    def get_precedence(self, op: str) -> int:
        prec_table = {
            TOK_ASSIGN: 1,
            TOK_PLUS: 10, TOK_SUB: 10,
            TOK_MUL: 20, TOK_DIV: 20,
        }
        return prec_table.get(op, -1)
    
    # === Including ===
    def parse_include(self) -> None:
        self.advance() # consume "@inc"
        typ, filename = self.expect(TOK_LIT_STRING)
        code = ""
        
        # read file
        try:
            with open(filename, "r") as f:
                code = f.read()
        except FileNotFoundError:
            errorHandler.error(f"Included file is not found: {filename}")
        
        # lex included file
        included_tokens = Lexer(code).tokenize()
        
        if included_tokens and included_tokens[-1][0] == TOK_EOF:
            included_tokens = included_tokens[:-1]
        
        self.inject_tokens(included_tokens)
        return None
    
    # === Running another Language ===
    def parse_runlang(self) -> RunLang:
        _, lang = self.advance() # consume
        if self.peek()[0] == TOK_ENDL: self.advance()

        self.expect(TOK_CODE_BLOCK_OPEN)
        if self.peek()[0] == TOK_ENDL: self.advance()
        
        code_tok = self.expect(TOK_LIT_STRING)
        code = code_tok[1]
        while self.peek()[0] == TOK_LIT_STRING or self.peek()[0] == TOK_ENDL:
            typ, value = self.advance()
            if typ == TOK_LIT_STRING:
                code += value

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

    # === Functions ===
    def parse_func(self) -> FuncDecl:
        self.advance() # Consume 'func'
        # return type
        ret_type_tok = self.advance()
        if ret_type_tok[0] not in [TOK_INT, TOK_UINT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
            errorHandler.error(f"Expected return type, got {ret_type_tok[1]}")
        ret_type = ret_type_tok[0]
        
        # func name
        name = self.expect(TOK_IDENTIFIER)[1]
        # params
        self.expect(TOK_LPAR)
        params = []
        while self.peek()[0] != TOK_RPAR:
            # type
            type_tok = self.advance()
            if type_tok[0] not in [TOK_INT, TOK_UINT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                errorHandler.error(f"Expected param type, got {type_tok[1]}")
            var_type = type_tok[0]
            ptr = False
            if self.peek()[0] == TOK_MUL:
                ptr = True
                self.advance()
            
            # name
            param_name = self.expect(TOK_IDENTIFIER)[1]
            params.append(Param(var_type, param_name, ptr))
            
            if self.peek()[0] == TOK_COMMA:
                self.advance() # consume comma
        
        self.expect(TOK_RPAR)
        self.expect(TOK_CODE_BLOCK_OPEN)
        body = []
        while self.peek()[0] != TOK_CODE_BLOCK_CLOSE and self.peek()[0] != TOK_EOF:
            stmt = self.parse_stmt()
            if stmt is not None:
                body.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        self.expect(TOK_CODE_BLOCK_CLOSE)
        
        if not isinstance(body[-1], ReturnStmt):
            body.append(ReturnStmt(None))
        
        return FuncDecl(ret_type, name, params, body)

    # === Statements ===
    def parse_stmt(self) -> Expr:
        typ, val = self.peek()
        glb = False
        
        if typ == TOK_ENDL: return None
        
        if typ == TOK_IDENTIFIER and val == "@include":
            return self.parse_include()
        elif typ == TOK_INC:
            return self.parse_include()

        if typ == TOK_GLOBAL:
            glb = True
            self.advance() # consume 'global'
            typ, val = self.peek()

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

        elif typ == TOK_FUNCDEF:
            return self.parse_func()

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
            if stmt:
                stmts.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        return stmts
