import os
import parser
import lexer

from AVM.syscalls import *

import errorHandler

# Macros
NULL = "0" # in string for easy use

# PVCpu Registers
# Format: <width (Optional)><Register>
# Widths: b (8-bit), w (16-bit), d (32-bit), q (64-bit), if none present then it defaults to the min register size (8-bit)
# Registers: g0 to g14 (General-Purpose), sp (Stack Pointer), sf (Stack Frame), NOTE: Not case-sensitive

# ABI:
# Syscalls: g0
# Arg 1-5: g1-g5
# Registers used for Arthmetic: g0, g1, g2

def formatString(string:str, vars:list, local_vars:dict=None, global_vars:dict=None, curfunc:str="__main") -> str:
    i = 0
    res = ""
    bslash = False

    for c in string:
        if c == "\\":
            bslash = True
            continue

        if bslash and c == "$":
            var = vars[i]
            typ = var[0]
            val = var[1]

            if typ == lexer.TOK_LIT_CHAR or typ == lexer.TOK_LIT_STRING:
                res += val
            elif typ == lexer.TOK_LIT_INT or typ == lexer.TOK_LIT_UINT:
                res += val
            elif typ == lexer.TOK_IDENTIFIER:
                if local_vars:
                    if curfunc in local_vars and val in local_vars[curfunc]:
                        val = local_vars[curfunc][val]
                        res += str(val)
                    elif val in global_vars:
                        val = global_vars[val]
                        res += str(val)
                    else:
                        errorHandler.compilerError(f"Unknown variable: {val}")

            i += 1
            bslash = False
            continue

        bslash = False
        res += c

    return res

def formatCode(code:str, vars:list, local_vars:dict=None, global_vars:dict=None, curfunc:str="__main") -> str:
    i = 0
    res = ""
    bslash = False
    
    for c in code:
        if c == "\\":
            bslash = True
            continue
        
        if bslash and c == "$":
            var = vars[i]
            typ = var[0]
            val = var[1]
            
            if curfunc in local_vars and val in local_vars[curfunc]:
                res += f"\tmov qG14, [qSF + {local_vars[val][0]}]\n"
                res += f"\tpush qG14\n"
                i += 1
                bslash = False
                continue
            elif val in global_vars:
                res += f"\tmov qG14, [{val}]\n"
                res += f"\tpush qG14\n"
                i += 1
                bslash = False
                continue
            else:
                errorHandler.compilerError(f"Unknown variable: {val}")
                exit(1)
        
        if bslash:
            bslash = False
        
        res += f"\tpush '{c}'\n"

    res += "\tpush 0\n"
    return res

class ArrisCompiler64(): # Outputs NASM syntax but follows PVCpu registers (64-bit)
    def __init__(self, ast:list):
        self.ast:list = ast

        self.data:list = []
        self.bss:list = []
        self.rodata:list = []
        self.text:list = []
        self.cur_func:str = "__main"
        self.strings:dict = {}
        self.label_count:int = 0
        self.global_vars:dict = {}
        self.local_vars:dict = {}

        self.current_offset_from_sf:int = 0
        
        self.global_vars_value:dict = {}
        self.local_vars_value:dict = {}

        self.current_label:str = ""
    
    def new_label(self, prefix:str="L") -> str:
        self.label_count += 1
        return f"{prefix}{self.label_count}"
    
    def add_string(self, s:str) -> str:
        if s in self.strings:
            return self.strings[s]
        
        label = f"str{len(self.strings)}"
        self.strings[s] = label
        self.rodata.append(f"{label}: db {', '.join(str(b) for b in s.encode())}, 0")
        return label
    
    def compile_expr(self, e:object):
        if isinstance(e, parser.Number):
            self.text.append(f"\tmov qG0, {e.value}")
            return e.value
        elif isinstance(e, parser.Bool):
            self.text.append(f"\tmov qG0, {1 if e.value == True else 0}")
            return 1 if e.value == True else 0
        elif isinstance(e, parser.String):
            lbl = self.add_string(e.value)
            self.text.append(f"\tlea qG0, [{lbl}]")
            return lbl
        elif isinstance(e, parser.Var):
            if e.name in self.global_vars:
                type_ = "q"
                len_ = self.global_vars[e.name]

                if len_ == 8 or len_ == 1:
                    type_ = "b"
                elif len_ == 16:
                    type_ = "w"
                elif len_ == 32:
                    type_ = "d"
                elif len_ == 64:
                    pass
                else:
                    errorHandler.compilerError(f"Invalid length of variable: {e.name}")

                self.text.append(f"\tmov {type_}G0, [{e.name}]")
                return self.global_vars_value[e.name]
            else:
                if self.cur_func in self.local_vars and e.name in self.local_vars[self.cur_func]:
                    type_ = "q"
                    len_ = self.local_vars[self.cur_func][e.name][1]

                    if len_ == 8 or len_ == 1:
                        type_ = "b"
                    elif len_ == 16:
                        type_ = "w"
                    elif len_ == 32:
                        type_ = "d"
                    elif len_ == 64:
                        pass
                    else:
                        errorHandler.compilerError(f"Invalid length of variable: {e.name}")

                    self.text.append(f"\tmov {type_}G0, [qSF + {self.local_vars[self.cur_func][e.name][0]}]")
                    return self.local_vars_value[self.cur_func][e.name]
                else:
                    errorHandler.compilerError(f"Unknown variable: {e.name}")
        elif isinstance(e, parser.BinaryOp):
            left = self.compile_expr(e.left)
            self.text.append("\tpush qG0")
            right = self.compile_expr(e.right)
            res = left
            self.text.append("\tmov qG1, qG0")
            self.text.append("\tpop qG2")
            if e.op == lexer.TOK_PLUS:
                self.text.append("\tadd qG2, qG1")
                res = left + right
            elif e.op == lexer.TOK_SUB:
                self.text.append("\tsub qG2, qG1")
                res = left - right
            elif e.op == lexer.TOK_MUL:
                self.text.append("\timul qG2, qG1")
                res = left * right
            elif e.op == lexer.TOK_DIV:
                self.text.append("\tmov qG0, qG2")
                self.text.append("\tcqo")
                self.text.append("\tidiv qG1")
                return left / right
            self.text.append("\tmov qG0, qG2")
            return res
        elif isinstance(e, parser.Assignment):
            value = self.compile_expr(e.value)
            
            if e.name in self.global_vars:
                self.text.append(f"\tmov [{e.name}], qG0")
                self.global_vars_value[e.name] = value
            else:
                if self.cur_func in self.local_vars and e.name in self.local_vars[self.cur_func]:
                    type_ = "q" # 64-bits
                    len_ = self.local_vars[self.cur_func][e.name][1]

                    if len_ == 8 or len_ == 1:
                        type_ = "b"
                    elif len_ == 16:
                        type_ = "w"
                    elif len_ == 32:
                        type_ = "d"
                    elif len_ == 64:
                        type_ = "q"
                    else:
                        errorHandler.compilerError(f"Invalid size of variable: {e.name}")

                    self.text.append(f"\tmov [qSF + {self.local_vars[self.cur_func][e.name][0]}], {type_}G0")
                    self.local_vars_value[self.cur_func][e.name] = value
                else:
                    errorHandler.compilerError(f"No such variable: {e.name}", 2)
        elif isinstance(e, parser.FuncCall):
            if e.args:
                i = 1
                for arg in e.args:
                    val = self.compile_expr(arg)
                    self.text.append(f"\tmov qG{i}, {val}")
                    i += 1
            self.text.append(f"\tcall {e.name}")
            return e.name
                
    def compile_stmt(self, s):
        if isinstance(s, parser.VarDecl):
            if s.name not in self.global_vars and s.global_ == True:
                self.global_vars[s.name] = 0
                init_val = NULL
                if s.value:
                    if isinstance(s.value, parser.Number):
                        init_val = str(s.value.value)
                type_ = "dq"

                if s.len == 0:
                    errorHandler.compilerError(f"Cannot keep any variable as a void type: {s.name}")
                elif s.len == 1 or s.len == 8:
                    type_ = "db"
                else:
                    if s.len == 16:
                        type_ = "dw"
                    elif s.len == 32:
                        type_ = "dd"

                self.data.append(f"{s.name}: {type_} {init_val}")
                self.global_vars_value[s.name] = init_val
            else:
                if s.var_type == lexer.TOK_VOID and not s.ptr:
                    pass # As it means nothing
                elif (s.var_type == lexer.TOK_BIT or s.var_type == lexer.TOK_BOOL) and not s.ptr:
                    self.text.append(f"\tsub qSF, 8") # Minimum is 8 bits
                    self.local_vars[self.cur_func][s.name] = (self.current_offset_from_sf, 8)
                    self.current_offset_from_sf += 8
                else:
                    self.text.append(f"\tsub qSF, {s.len}")
                    self.local_vars[self.cur_func][s.name] = (self.current_offset_from_sf, s.len)
                    self.current_offset_from_sf += s.len

            if s.value:
                self.compile_expr(parser.Assignment(s.name, s.value))
        elif isinstance(s, parser.RunLang):
            if s.language == "python-simple":
                self.text.append(f";;@Runlang: {s.language}")
                code = formatString(s.code, s.vars, self.local_vars_value, self.global_vars_value)
                self.text.append(f";;{code}")
                self.text.append(f";;@Runlang-End")
            elif s.language == "vasm":
                self.text.append("; VASM Runlang")
                self.text.append(formatCode(s.code, s.vars, self.local_vars, self.global_vars))
            else:
                self.text.append("\tmov qG1, [qSP + 1]\n")
                self.text.append(formatCode(s.code, s.vars, self.local_vars, self.global_vars))
                self.text.append(f"\tcall runlang_{s.language}")
        elif isinstance(s, parser.FuncDecl):
            if self.cur_func:
                self.text.append("\tmov qG0, 0")
                self.text.append("\tmov qSP, qSF")
                self.text.append("\tpop qSF")
                self.text.append("\tret")
                self.current_offset_from_sf = 0
            self.text.append(s.name + ":")
            self.text.append("\tpush qSF")
            self.text.append("\tmov qSF, qSP")
            self.current_offset_from_sf = 0
            self.local_vars[s.name] = {}
            if s.params:
                i = 1
                for param in s.params:
                    self.text.append(f"\tsub qSF, {param.len}")
                    self.text.append(f"\tmov [qSF + {param.len}], qG{i}")
                    self.local_vars[param.name] = (self.current_offset_from_sf, param.len)
                    self.current_offset_from_sf += param.len
                    i += 1
            for stmt in s.body:
                self.compile_stmt(stmt)
        elif isinstance(s, parser.ReturnStmt):
            if s.value:
                self.compile_expr(s.value)
            else:
                self.text.append("\tmov qG0, 0")
            self.text.append("\tmov qSP, qSF")
            self.text.append("\tpop qSF")
            self.text.append("\tret")
            self.current_offset_from_sf = 0
            self.local_vars.pop(self.cur_func, None)
            self.cur_func = ""
        else:
            self.compile_expr(s)
    
    def compile(self):
        self.text.append("section .text")
        self.text.append("global __main") # __main is _start here
        self.text.append("__main:")
        self.text.append("\tpop qG1") # Get argc
        self.text.append("\tmov qG2, qSP") # Get memaddr of argv
        self.text.append("\tpush qSF")
        self.text.append("\tmov qSF, qSP") # Save old stack frame and make new one
        self.text.append("\tcall main")
        self.text.append("\tmov qSP, qSF")
        self.text.append("\tpop qSF") # restore stack frame
        self.text.append("\tmov qG1, qG0")
        self.text.append(f"\tmov qG0, {SYS_EXIT}")
        self.text.append("\tsyscall")
        for s in self.ast:
            self.compile_stmt(s)

        out = []
        if self.data: # Required sections
            out.append("section .data")
            out.extend(self.data)
        else:
            out.append("section .data")
        if self.bss:
            out.append("section .bss")
            out.extend(self.bss)
        else:
            out.append("section .bss")
        if self.rodata:
            out.append("section .rodata")
            out.extend(self.rodata)
        else:
            out.append("section .rodata")
        out.extend(self.text)
        return "\n".join(out)
