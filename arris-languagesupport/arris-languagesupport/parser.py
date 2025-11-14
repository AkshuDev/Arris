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

class Unsigned(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Unsigned({self.value})"
    
class Signed(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Signed({self.value})"
    
class Int(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Int({self.value})"
    
class Bit(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Bit({self.value})"
    
class Byte(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Byte({self.value})"
    
class Word(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Word({self.value})"
    
class Dword(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Dword({self.value})"
    
class Qword(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Qword({self.value})"
    
class Long(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Long({self.value})"

class Char(Expr):
    def __init__(self, value: Expr, line: int, col: int):
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Char({self.value})"

class RunLang(Expr):
    def __init__(self, langauge: str, code: str, vars: List[str], line: int, col: int):
        self.language = langauge
        self.code = code
        self.vars = vars
        self.line = line
        self.col = col
    def __repr__(self):
        return f"RunLang(lang={self.language}, code={self.code!r}), vars={self.vars})"

class Number(Expr):
    def __init__(self, value: int, line: int, col: int): 
        self.value = int(value)
        self.line = line
        self.col = col
    def __repr__(self): return f"Number({self.value})"

class String(Expr):
    def __init__(self, value: str, line: int, col: int): 
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self): return f"String({self.value!r})"

class Bool(Expr):
    def __init__(self, value: str, line: int, col: int): 
        self.value = (value == "true")
        self.line = line
        self.col = col
    def __repr__(self): return f"Bool({self.value})"

class Var(Expr):
    def __init__(self, name: str, line: int, col: int): 
        self.name = name
        self.line = line
        self.col = col
    def __repr__(self): return f"Var({self.name})"

class VarDecl(Expr):
    def __init__(self, var_type: Expr, name: str, value: Optional[Expr], line: int, col: int, global_: bool = False, code: Optional[str]=None):
        self.var_type, self.name, self.value, self.global_ = var_type, name, value, global_
        self.len = 0 # in bits
        self.line = line
        self.col = col

        if isinstance(var_type, Bit) or (isinstance(var_type, Byte) or (isinstance(var_type, Bool) or isinstance(var_type, Char))):
            self.len = 1
        elif isinstance(var_type, Word):
            self.len = 2
        elif isinstance(var_type, Dword) or isinstance(var_type, Int):
            self.len = 4
        elif isinstance(var_type, Qword) or isinstance(var_type, Long):
            self.len = 8
        elif isinstance(var_type, Pointer):
            self.len = ptr_len()
        else:
            errorHandler.parser_error(f"Unknown variable type in variable declaration!", line=line, col=col, src=code)

    def __repr__(self):
        return f"VarDecl(type={self.var_type}, name={self.name}, value={self.value})"

class Param(Expr):
    def __init__(self, var_type: Expr, name: str, line: int, col: int, code: Optional[str]=None):
        self.var_type = var_type
        self.name = name
        self.line = line
        self.col = col
        self.len = 0
        if isinstance(var_type, Bit) or (isinstance(var_type, Byte) or (isinstance(var_type, Bool) or isinstance(var_type, Char))):
            self.len = 1
        elif isinstance(var_type, Word):
            self.len = 2
        elif isinstance(var_type, Dword) or isinstance(var_type, Int):
            self.len = 4
        elif isinstance(var_type, Qword) or isinstance(var_type, Long):
            self.len = 8
        elif isinstance(var_type, Pointer):
            self.len = ptr_len()
        else:
            errorHandler.parser_error(f"Unkown variable type in parameter!", line=line, col=col, src=code)

    def __repr__(self):
        return f"Param(type={self.var_type}, name={self.name})"

class FuncDecl(Expr):
    def __init__(self, ret_type: str, name: str, params: List[Param], body: List[Expr], line: int, col: int):
        self.ret_type = ret_type
        self.name = name
        self.params = params
        self.body = body
        self.line = line
        self.col = col
    def __repr__(self):
        return f"FuncDecl(ret={self.ret_type}, name={self.name}, params={self.params}, body={self.body})"

class FuncCall(Expr):
    def __init__(self, name: str, args: List[Expr], line: int, col: int):
        self.name = name
        self.args = args
        self.line = line
        self.col = col
    def __repr__(self):
        return f"FuncCall(name={self.name}, args={self.args})"

class BinaryOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr, line: int, col: int):
        self.left, self.op, self.right = left, op, right
        self.line = line
        self.col = col
    def __repr__(self): return f"BinaryOp({self.left}, {self.op}, {self.right})"

class Assignment(Expr):
    def __init__(self, name: str, value: Expr, line: int, col: int):
        self.name, self.value = name, value
        self.line = line
        self.col = col
    def __repr__(self): return f"Assignment({self.name}, {self.value})"

class ReturnStmt(Expr):
    def __init__(self, value: Optional[Expr], line: int, col: int): 
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self): return f"Return({self.value})"

class Cast(Expr):
    def __init__(self, target_type: Expr, expr: Expr, line: int, col: int):
        self.target_type = target_type
        self.expr = expr
        self.line = line
        self.col = col
    def __repr__(self):
        return f"Cast({self.target_type}, {self.expr})"

class Pointer(Expr):
    def __init__(self, target: Expr, line: int, col: int):
        self.target = target
        self.line = line
        self.col = col
        self.len = ptr_len()
    def __repr__(self) -> str:
        return f"Pointer({self.target})"

class DerefPointer(Expr):
    def __init__(self, target: Expr, line: int, col: int):
        self.target = target
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"DerefPointer({self.target})"

class Void(Expr):
    def __init__(self):
        pass
    def __repr__(self) -> str:
        return "Void()"

class If(Expr):
    def __init__(self, condition: Expr, code: list[Expr], line: int, col: int):
        self.condition = condition
        self.line = line
        self.col = col
        self.code = code
    def __repr__(self) -> str:
        return f"If({self.condition}, body:{self.code})"
    
class For(Expr):
    def __init__(self, initializer: Expr, condition: Expr, incrementer: Expr, code: list[Expr], line: int, col: int):
        self.condition = condition
        self.line = line
        self.col = col
        self.initializer = initializer
        self.increment = incrementer
        self.code = code
    def __repr__(self) -> str:
        return f"For({self.initializer}, {self.condition}, {self.increment}, body:{self.code})"
    
class While(Expr):
    def __init__(self, condition: Expr, code: list[Expr], line: int, col: int):
        self.condition = condition
        self.line = line
        self.col = col
        self.code = code
    def __repr__(self) -> str:
        return f"While({self.condition}, body:{self.code})"

class Increment(Expr):
    def __init__(self, expr: Expr, line: int, col: int):
        self.expr = expr
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Increment({self.expr})"
    
class Decrement(Expr):
    def __init__(self, expr: Expr, line: int, col: int):
        self.expr = expr
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Decrement({self.expr})"

class Include(Expr):
    def __init__(self, code:str, body:list[Expr], filename:str, line:int, col:int):
        self.code = code
        self.body = body
        self.filename = filename
        self.line = line
        self.col = col
    def __repr__(self) -> str:
        return f"Include({self.filename}, body: {self.body})"

class CompilerEntry(Expr):
    def __init__(self, funcname:str, line:int, col:int, code:str, filename:str):
        self.func = funcname
        self.line = line
        self.col = col
        self.code = code
        self.filename = filename
    def __repr__(self) -> str:
        return f"CompilerEntry({self.func})"

# === Parser ===
class Parser:
    def __init__(self, tokens: List[Tuple[str,str]], include_runlang=True, code:Optional[str]=None, architecture:str="x86_64", bits:int=64, os_:str="linux", file:Optional[str]=None):
        self.tokens = tokens
        self.filename = file
        self.pos = 0

        self.code = code

        self.architecture = architecture
        self.bits = bits
        self.os_ = os_

        self.last_condition = True

        self.macros = {
            "__ARRIS_ARCH": architecture,
            "__ARRIS_BITS": bits,
            "__ARRIS_OS": os_.lower()
        }

        self.stdlib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "stdlib")
        self.stmts = []

        if include_runlang:
            code = ""
            with open (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "stdlib", "runlang.alib"), "r") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            if tokens[-1][0] == TOK_EOF:
                tokens = tokens[:-1]
            self.inject_tokens(tokens)

    def peek(self) -> Tuple[str,str,int,int]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (TOK_EOF, "")

    def advance(self) -> Tuple[str,str,int,int]:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, typ: str) -> Tuple[str,str,int,int]:
        tok = self.advance()
        if tok[0] != typ:
            errorHandler.parser_error(f"Expected '{typ}', got '{tok[0]}'", line=tok[2], col=tok[3], src=self.code, file=self.filename)
        return tok
    
    def inject_tokens(self, new_tokens: List[Tuple[str, str,int,int]]) -> None:
        self.tokens = self.tokens[:self.pos] + new_tokens + self.tokens[self.pos:]

    # === Expression Parsing ===
    def parse_expr(self, prec=0) -> Expr:
        left = self.parse_primary()

        while True:
            op, _, line, col = self.peek()
            op_prec = self.get_precedence(op)
            if op_prec < prec: break
            self.advance()
            right = self.parse_expr(op_prec+1)
            left = BinaryOp(left, op, right, line, col)

        return left

    def parse_primary(self) -> Expr:
        typ, val, line, col = self.advance()
        if typ == TOK_LIT_INT:
            return Number(val, line, col)
        elif typ == TOK_LIT_STRING:
            return String(val, line, col)
        elif typ == TOK_LIT_BOOL:
            return Bool(val, line, col)
        elif typ == TOK_LIT_CHAR:
            return Char(val, line, col)
        elif typ == TOK_MUL:
            target = self.parse_primary()
            return DerefPointer(target, line, col)
        elif typ == TOK_IDENTIFIER:
            # Could be assignment
            nxt = self.peek()
            if nxt[0] == TOK_ASSIGN:
                self.advance()
                expr = self.parse_expr()
                return Assignment(val, expr, line, col)
            elif nxt[0] == TOK_LPAR:
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
                return FuncCall(val, args, line, col)
            elif nxt[0] == TOK_PLUS:
                self.advance() # consume '+'
                if self.peek()[0] == TOK_PLUS:
                    # e.g. a++; a = a + 1;
                    self.advance() # consume '+'
                    return Increment(Var(val, line, col), line, col)
            elif self.peek()[0] == TOK_SUB:
                self.advance() # consume '-'
                if self.peek()[0] == TOK_PLUS:
                    # e.g. a--; a = a - 1;
                    self.advance() # consume '-'
                    return Decrement(Var(val, line, col), line, col)

            while nxt[0] == TOK_MUL:
                val = Pointer(val, line, col)
                nxt = self.advance()

            return Var(val, line, col)
        elif typ == TOK_LPAR:
            # Lookahead for type-cast: (type)expr
            next_tok = self.peek()
            if next_tok[0] in [TOK_INT, TOK_BIT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG, TOK_UNSIGNED, TOK_SIGNED]:
                # It's a cast
                type_tok = self.advance()

                # Handle signed/unsigned prefix
                if type_tok[0] in [TOK_UNSIGNED, TOK_SIGNED]:
                    next_tok = self.advance()
                    base_type = self.tok_to_ast_type(next_tok, None)
                    if type_tok[0] == TOK_UNSIGNED:
                        target_type = Unsigned(base_type, type_tok[2], type_tok[3])
                    else:
                        target_type = Signed(base_type, type_tok[2], type_tok[3])
                else:
                    target_type = self.tok_to_ast_type(type_tok, None)

                while self.peek()[0] == TOK_MUL:
                    self.advance()
                    target_type = Pointer(target_type, line, col)

                self.expect(TOK_RPAR)
                expr = self.parse_primary()
                return Cast(target_type, expr, line, col)

            else:
                # Normal parenthesized expression
                expr = self.parse_expr()
                self.expect(TOK_RPAR)
                return expr
        elif typ == TOK_DEREF:
            target = self.parse_primary()
            return Pointer(target, line, col)
        else:
            errorHandler.parser_error(f"Unexpected code in expression: '{val}'", line=line, col=col, src=self.code, file=self.filename)

    def get_precedence(self, op: str) -> int:
        prec_table = {
            TOK_ASSIGN: 1,
            TOK_PLUS: 10, TOK_SUB: 10,
            TOK_MUL: 20, TOK_DIV: 20,
            TOK_EQUALS: 30, TOK_NE: 30, TOK_GT: 30, TOK_LT: 30, TOK_GTE: 30, TOK_LTE: 30
        }
        return prec_table.get(op, -1)
    
    # === if/while/for Parsing ===
    def parse_if(self) -> Expr:
        _, __, line, col = self.advance() # consume 'if'
        expr = self.parse_expr()

        self.expect(TOK_CODE_BLOCK_OPEN)

        body = []
        while self.peek()[0] != TOK_CODE_BLOCK_CLOSE and self.peek()[0] != TOK_EOF:
            stmt = self.parse_stmt()
            if stmt is not None:
                body.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        self.expect(TOK_CODE_BLOCK_CLOSE)

        return If(expr, body, line, col)
    
    def parse_while(self) -> Expr:
        _, __, line, col = self.advance() # consume 'while'
        expr = self.parse_expr()

        self.expect(TOK_CODE_BLOCK_OPEN)

        body = []
        while self.peek()[0] != TOK_CODE_BLOCK_CLOSE and self.peek()[0] != TOK_EOF:
            stmt = self.parse_stmt()
            if stmt is not None:
                body.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        self.expect(TOK_CODE_BLOCK_CLOSE)

        return While(expr, body, line, col)
    
    def parse_for(self) -> Expr:
        _, __, line, col = self.advance() # consume 'for'
        init = self.parse_stmt()
        conditional = self.parse_expr()
        increment = self.parse_primary()

        self.expect(TOK_CODE_BLOCK_OPEN)

        body = []
        while self.peek()[0] != TOK_CODE_BLOCK_CLOSE and self.peek()[0] != TOK_EOF:
            stmt = self.parse_stmt()
            if stmt is not None:
                body.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        self.expect(TOK_CODE_BLOCK_CLOSE)

        return For(init, conditional, increment, body, line, col)

    # === Including ===
    def parse_include(self) -> None:
        self.advance() # consume "@inc"
        typ, filename, line, col = self.expect(TOK_LIT_STRING)

        if filename.startswith("<"):
            if not filename.endswith(">"):
                errorHandler.parser_error("System Include should end with '>'!", line=line, col=col, src=self.code, file=self.filename)
            filename = filename.replace("<", "").replace(">", "")
            filename = os.path.join(self.stdlib, filename)
        elif filename.endswith(">"):
            if not filename.startswith("<"):
                errorHandler.parser_error("System Include should start with '<'!", line=line, col=col, src=self.code, file=self.filename)

        code = ""
        
        # read file
        try:
            with open(filename, "r") as f:
                code = f.read()
        except FileNotFoundError:
            errorHandler.parser_error(f"Included file is not found: {filename}", line=line, col=col, src=self.code, file=self.filename)
        
        # lex included file
        included_tokens = Lexer(code, filename=filename).tokenize()
        
        if included_tokens and included_tokens[-1][0] == TOK_EOF:
            included_tokens = included_tokens[:-1]
        
        new_ast = Parser(included_tokens, False, code, self.architecture, self.bits, self.os_, filename).parse()
        
        return Include(code, new_ast, filename, line, col)
    
    # === Running another Language ===
    def parse_runlang(self) -> RunLang:
        _, lang, ln, cl = self.advance() # consume
        if self.peek()[0] == TOK_ENDL: self.advance()

        self.expect(TOK_CODE_BLOCK_OPEN)
        if self.peek()[0] == TOK_ENDL: self.advance()
        
        code_tok = self.expect(TOK_LIT_STRING)
        code = code_tok[1]
        while self.peek()[0] == TOK_LIT_STRING or self.peek()[0] == TOK_ENDL:
            typ, value, line, col = self.advance()
            if typ == TOK_LIT_STRING:
                code += value

        # Format the string
        vars_list = []
        while self.peek()[0] not in [TOK_CODE_BLOCK_CLOSE, TOK_EOF]:
            if self.peek()[0] == TOK_LIT_STRING:
                _, val, line, col = self.advance()
                vars_list.append((TOK_LIT_STRING, val))
            elif self.peek()[0] == TOK_IDENTIFIER:
                _, name, line, col = self.advance()
                vars_list.append((TOK_IDENTIFIER, name))
            elif self.peek()[0] == TOK_LIT_CHAR:
                _, val, line, col = self.advance()
                vars_list.append((TOK_LIT_CHAR, val))
            else:
                self.advance() # Skip unknown

        self.expect(TOK_CODE_BLOCK_CLOSE)
        return RunLang(lang, code, vars_list, ln, cl)

    # === Helpers ===
    def tok_to_ast_type(self, tk: list[str, str, int, int], val: Optional[Expr]) -> Expr:
        line, col = tk[2], tk[3]
        tok = tk[0]
        if tok == TOK_BIT:
            return Bit(val, line, col)
        elif tok == TOK_BYTE:
            return Byte(val, line, col)
        elif tok == TOK_WORD:
            return Word(val, line, col)
        elif tok == TOK_DWORD:
            return Dword(val, line, col)
        elif tok == TOK_QWORD:
            return Qword(val, line, col)
        elif tok == TOK_CHAR:
            return Char(val, line, col)
        elif tok == TOK_BOOL:
            return Bool(val, line, col)
        elif tok == TOK_INT:
            return Int(val, line, col)
        elif tok == TOK_LONG:
            return Long(val, line, col)
        elif tok == TOK_VOID:
            return Void()
        else:
            errorHandler.parser_error(f"Unknown type: {tk[1]}", line=line, col=col, src=self.code, file=self.filename)

    # === Functions ===
    def parse_func(self) -> FuncDecl:
        _, __, line, col = self.advance() # Consume 'func'
        # return type
        ret_type_tok = self.advance()
        if ret_type_tok[0] not in [TOK_INT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
            errorHandler.parser_error(f"Expected return type, got '{ret_type_tok[1]}'", line=ret_type_tok[2], col=ret_type_tok[3], src=self.code, file=self.filename)

        ret_type = self.tok_to_ast_type(ret_type_tok, None)

        # handle pointer return types (e.g. func int* foo())
        while self.peek()[0] == TOK_MUL:
            self.advance()
            ret_type = Pointer(ret_type, ret_type_tok[2], ret_type_tok[3])
        
        # func name
        name = self.expect(TOK_IDENTIFIER)[1]
        # params
        self.expect(TOK_LPAR)
        params = []
        while self.peek()[0] != TOK_RPAR:
            # type
            type_tok = self.advance()
            if type_tok[0] not in [TOK_INT, TOK_BIT, TOK_UNSIGNED, TOK_SIGNED, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                errorHandler.parser_error(f"Expected param type, got '{type_tok[1]}'", line=type_tok[2], col=type_tok[3], src=self.code, file=self.filename)
            
            var_type = None
            if type_tok[0] in [TOK_UNSIGNED, TOK_SIGNED]:
                type_tk = self.advance()
                if type_tk[0] not in [TOK_INT, TOK_BIT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                    errorHandler.parser_error(f"Expected param type, got '{type_tk[1]}'", line=type_tk[2], col=type_tk[3], src=self.code, file=self.filename)

                var_tp = self.tok_to_ast_type(type_tk, None)
                if type_tok[0] == TOK_UNSIGNED:
                    var_type = Unsigned(var_tp, type_tok[2], type_tok[3])
                else:
                    var_type = Signed(var_tp, type_tok[2], type_tok[3])
            else:
                var_type = self.tok_to_ast_type(type_tok, None)

            while self.peek()[0] == TOK_MUL:
                var_type = Pointer(var_type, line, col)
                self.advance()
            
            # name
            _, param_name, param_ln, param_cl = self.expect(TOK_IDENTIFIER)
            params.append(Param(var_type, param_name, param_ln, param_cl, code=self.code))
            
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
            body.append(ReturnStmt(None, line, col))
        
        return FuncDecl(ret_type, name, params, body, line, col)

    # === Statements ===
    def parse_stmt(self) -> Expr:
        typ, val, line, col = self.peek()
        glb = False
        
        if typ == TOK_ENDL: return None
        
        if typ == TOK_INC:
            return self.parse_include()

        elif typ == TOK_PREPROCESSOR:
            return self.parse_preprocessor()

        elif typ == TOK_GLOBAL:
            glb = True
            self.advance() # consume 'global'
            typ, val, line, col = self.peek()

        elif typ == TOK_LET:
            self.advance()  # consume 'let'

            type_tok = self.advance()
            # handle signed/unsigned before type
            if type_tok[0] in [TOK_UNSIGNED, TOK_SIGNED]:
                next_tok = self.advance()
                if next_tok[0] not in [TOK_INT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BIT, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                    errorHandler.parser_error(f"Expected base type after '{type_tok[1]}', got '{next_tok[1]}'", line=next_tok[2], col=next_tok[3], src=self.code, file=self.filename)

                base_type = self.tok_to_ast_type(next_tok, None)
                if type_tok[0] == TOK_UNSIGNED:
                    var_type_ast = Unsigned(base_type, type_tok[2], type_tok[3])
                else:
                    var_type_ast = Signed(base_type, type_tok[2], type_tok[3])
            else:
                if type_tok[0] not in [TOK_INT, TOK_CHAR, TOK_BOOL, TOK_VOID, TOK_BIT, TOK_BYTE, TOK_DWORD, TOK_WORD, TOK_QWORD, TOK_LONG]:
                    errorHandler.parser_error(f"Expected type after 'let', got '{type_tok[1]}'", line=type_tok[2], col=type_tok[3], src=self.code, file=self.filename)
                var_type_ast = self.tok_to_ast_type(type_tok, None)

            # handle pointer levels (int*, char**, etc.)
            while self.peek()[0] == TOK_MUL:
                self.advance()
                var_type_ast = Pointer(var_type_ast, line, col)

            # variable name
            _, name, _, _ = self.expect(TOK_IDENTIFIER)

            expr = None
            if self.peek()[0] == TOK_ASSIGN:
                self.advance()
                expr = self.parse_expr()

            return VarDecl(var_type_ast, name, expr, line, col, glb, self.code)

        elif typ == TOK_FUNCDEF:
            return self.parse_func()

        elif typ == TOK_RETURN:
            self.advance()
            if self.peek()[0] in [TOK_ENDL, TOK_EOF]:
                return ReturnStmt(None, line, col)
            expr = self.parse_expr()
            return ReturnStmt(expr, line, col)
        
        elif typ == TOK_RUNLANG:
            return self.parse_runlang()

        elif typ == TOK_FOR:
            return self.parse_for()
        
        elif typ == TOK_WHILE:
            return self.parse_while()

        elif typ == TOK_IF:
            return self.parse_if()

        else:
            return self.parse_expr()

    # === Macros and more ===
    def convert_tk_to_corrosponding_type(self, typ: str, value: str):
        val = value
        if typ == TOK_LIT_STRING:
            val = str(value)
        elif typ == TOK_LIT_INT:
            val = int(value)
        elif typ == TOK_LIT_BOOL:
            if val == "true": 
                val = True
            else:
                val = False
        else:
            val = str(value)
        return val

    def skip_to_end(self, tok: list[str, str, int, int], line: int, col: int) -> None:
        tk = tok
        while not tk[1] == "@end":
            tk = self.advance()
            if tk[0] == TOK_EOF:
                errorHandler.parser_error("'@end' was never found!", line=line, col=col, src=self.code, file=self.filename)
            if tk[0] == TOK_PREPROCESSOR and tk[1] == "@if":
                self.skip_to_end(tk, line, col)

    def parse_preproc_define(self) -> None:
        _, name, line, col = self.expect(TOK_IDENTIFIER)
        if self.peek()[0] == TOK_ASSIGN:
            self.advance()
        typ, val, line, col = self.advance()
        if not typ in [TOK_LIT_STRING, TOK_LIT_INT, TOK_LIT_BOOL, TOK_LIT_CHAR]:
            errorHandler.parser_error(f"Unknown Type: {val}", line=line, col=col, src=self.code, file=self.filename)
        
        val = self.convert_tk_to_corrosponding_type(typ, val)
        
        self.macros[str(name)] = val

    def parse_preproc_undefine(self) -> None:
        _, name, line, col = self.expect(TOK_IDENTIFIER)
        if self.macros.get(str(name), None):
            self.macros.pop(str(name))

    def format_string(self) -> str:
        _, string, line, col = self.expect(TOK_LIT_STRING)
        string = str(string) # Gotta make sure
        if "\\$" in string and not self.peek()[0] == TOK_COMMA:
            errorHandler.parser_error("Not enough variables provided for formatting!", line=line, col=col, src=self.code, file=self.filename)
        
        if not "\\$" in string: return string

        tk = self.advance() # consume ','
        vars_ = []
        while tk[0] in [TOK_COMMA, TOK_IDENTIFIER, TOK_LIT_INT, TOK_LIT_CHAR, TOK_LIT_BOOL, TOK_LIT_STRING]:
            if tk[0] == TOK_IDENTIFIER:
                vars_.append(self.macros.get(tk[1], False))
            elif tk[0] in [TOK_LIT_BOOL, TOK_LIT_CHAR, TOK_LIT_INT, TOK_LIT_STRING]:
                vars_.append(self.convert_tk_to_corrosponding_type(tk[0], tk[1]))
            
            tk = self.advance()

        i = 0
        out_lines = []
        bslash = False
        buffer = ""
        used_vars = 0

        for c in string:
            if c == "\\":
                bslash = True
                continue

            if bslash and c == "$":
                if used_vars >= len(vars_):
                    errorHandler.parser_error("Not enough variables provided!", line=line, col=col, src=self.code, file=self.filename)
                var = vars_[used_vars]
                used_vars += 1

                buffer += str(var)

                bslash = False
                continue

            if bslash:
                bslash = False
                continue

            buffer += c
            i += 1

        return str(buffer)
    
    def parse_preproc_err(self, line: int, col: int) -> None:
        err = self.format_string()
        errorHandler.parser_error(err, line=line, col=col, src=self.code, file=self.filename)
    
    def parse_preproc_if(self, og_line: int, og_col: int) -> None:
        typ, v1, line, col = self.advance()
        if not typ in [TOK_LIT_BOOL, TOK_LIT_INT, TOK_LIT_CHAR, TOK_LIT_STRING, TOK_IDENTIFIER]:
            errorHandler.parser_error(f"Cannot preprocess such data type: {v1}", line=line, col=col, src=self.code, file=self.filename)
        
        if not typ == TOK_IDENTIFIER:
            v1 = self.convert_tk_to_corrosponding_type(typ, v1)
        else:
            v1 = self.macros.get(v1, False)

        opr, _, line, col = self.advance()
        if not opr in [TOK_GTE, TOK_LTE, TOK_LT, TOK_GT, TOK_NE, TOK_EQUALS, TOK_NOT]:
            errorHandler.parser_error(f"Cannot perform such condition: {opr}", line=line, col=col, src=self.code, file=self.filename)
        typ, v2, line, col = self.advance()
        if not typ in [TOK_LIT_BOOL, TOK_LIT_INT, TOK_LIT_CHAR, TOK_LIT_STRING, TOK_IDENTIFIER]:
            errorHandler.parser_error(f"Cannot preprocess such data type: {v2}", line=line, col=col, src=self.code, file=self.filename)

        if not typ == TOK_IDENTIFIER:
            v2 = self.convert_tk_to_corrosponding_type(typ, v2)
        else:
            v2 = self.macros.get(v2, False)

        condition = False

        try:
            if opr == TOK_EQUALS:
                if v1 == v2:
                    condition = True
            elif opr == TOK_NE:
                if not v1 == v2:
                    condition = True
            elif opr == TOK_GT:
                if v1 > v2:
                    condition = True
            elif opr == TOK_LT:
                if v1 < v2:
                    condition = True
            elif opr == TOK_GTE:
                if v1 >= v2:
                    condition = True
            elif opr == TOK_LTE:
                if v1 <= v2:
                    condition = True
            elif opr == TOK_NOT:
                if not v2:
                    condition = True
        except Exception:
            errorHandler.parser_error("Provided condition is wrong and cannot be performed!", line=line, col=col, src=self.code, file=self.filename)
        
        if condition == True:
            self.last_condition = True
            return
        
        tk = self.advance()
        self.skip_to_end(tk, og_line, og_col)

    def parse_preproc_else(self, og_line: int, og_col: int) -> None:
        if self.last_condition == False: return

        tk = self.advance()
        self.skip_to_end(tk, og_line, og_col)

    def parse_preprocessor(self) -> None:
        _, val, line, col = self.advance() # consume @<...>
        
        if val == "@def":
            self.parse_preproc_define()
        elif val == "@undef":
            self.parse_preproc_undefine()
        elif val == "@err":
            self.parse_preproc_err(line, col)
        elif val == "@if":
            self.parse_preproc_if(line, col)
        elif val == "@else":
            self.parse_preproc_else(line, col)
        elif val == "@entry":
            typ, v, line, col = self.advance()
            if not typ == TOK_IDENTIFIER:
                errorHandler.parser_error("Please Specify Function name!", line=line, col=col, src=self.code, file=self.filename)
            return CompilerEntry(v, line, col, self.code, self.filename)
        else:
            errorHandler.parser_error(f"Unknown Statement: {val}", line=line, col=col, src=self.code, file=self.filename)

    def parse(self) -> List[Expr]:
        self.stmts = []
        while self.peek()[0] != TOK_EOF:
            stmt = self.parse_stmt()
            if stmt:
                self.stmts.append(stmt)
            if self.peek()[0] == TOK_ENDL:
                self.advance()
        return self.stmts
