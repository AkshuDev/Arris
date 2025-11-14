import os
from . import parser
from . import lexer
from typing import Optional

from .syscalls import *

from . import errorHandler

# Macros
NULL = "0" # in string for easy use
_START = "__arris__compilerinjected__main" # entry label

def type_bits(type_node: parser.Expr, ptr_size: int = 64, src: Optional[str]=None) -> int:
    """
    Return bit-width for a given type node (using parser ast).
    """
    if isinstance(type_node, parser.Param):
        type_node = type_node.var_type
    
    if isinstance(type_node, parser.Signed) or isinstance(type_node, parser.Unsigned):
        type_node = type_node.value

    if isinstance(type_node, parser.Pointer):
        return ptr_size

    if isinstance(type_node, parser.Char) or (isinstance(type_node, parser.Byte) or (isinstance(type_node, parser.Bool) or isinstance(type_node, parser.Bit))):
        return 8
    if isinstance(type_node, parser.Word):
        return 16
    if isinstance(type_node, parser.Int) or isinstance(type_node, parser.Dword):
        return 32
    if isinstance(type_node, parser.Long) or isinstance(type_node, parser.Qword):
        return 64
    if isinstance(type_node, parser.Void):
        return 0
    
    # own -> error
    errorHandler.compilerError(f"Unknown Data type!", line=type_node.line, col=type_node.col, src=src)
    return 0

def mask_for_bits(bits: int) -> int:
    if bits >= 64:
        return (1 << 64) - 1
    return (1 << bits) - 1

def bits_to_bytes(bits: int) -> int:
    if bits <= 0:
        return 0
    return (bits + 7) // 8

def align_up(n: int, align: int = 8) -> int:
    if align <= 0:
        return n
    return ((n + align - 1) // align) * align


class x86_64Compiler(): # Outputs NASM syntax x86_64 Assembly
    def __init__(self, ast:list, os:str, code:Optional[str]=None, file:Optional[str]=None, add_stdlib:bool=True, entry:Optional[str]=None):
        self.ast:list = ast
        self.os: str = os.lower()
        
        self.add_stdlib = add_stdlib

        self.og_code:list[Optional[str]] = []
        self.og_file:list[Optional[str]] = []
        self.code:Optional[str] = code
        self.file:Optional[str] = file

        self.entry = "" if entry is None else entry

        self.data:list = []
        self.bss:list = []
        self.rodata:list = []
        self.text:list = []
        self.cur_func:str = ""
        self.funcs:list[str] = []
        self.strings:dict = {}
        self.label_count:int = 0
        self.global_vars:dict = {}
        self.local_vars:dict = {}

        self.current_offset_from_sf:int = 0

        self.subfunc_count:int = 0
        
        self.global_vars_value:dict = {}
        self.local_vars_value:dict = {}

        self.current_label:str = ""
    
    def new_label(self, prefix:str="L") -> str:
        self.label_count += 1
        return f"{prefix}{self.label_count}"
    
    def handle_string(self, s:str) -> list[str]:
        # Use db for bytes, zero terminated
        blist = []
        buf = ""
        special = False
        
        for c in s:
            if c == "\\":
                special = True
                continue
            if special:
                if c == "n":
                    blist.append('"' + buf + '"')
                    blist.append("10")
                    blist.append("13")
                    buf = ""
                elif c == "<":
                    blist.append('"' + buf + '"')
                    blist.append("10")
                    buf = ""
                elif c == ">":
                    blist.append('"' + buf + '"')
                    blist.append("13")
                    buf = ""
                elif c == "\\":
                    buf += c
                special = False
                continue

            buf += c

        if not buf == "":
            blist.append('"' + buf + '"')
        return blist

    def add_string(self, s:str) -> str:
        if s in self.strings:
            return self.strings[s]
        
        label = f"str{len(self.strings)}"
        self.strings[s] = label
        
        blist = self.handle_string(s)

        self.rodata.append(f"{label}: db {', '.join(blist)}, 0")
        return label
    
    def add_literal_list(self, items) -> str:
        # Convert items to bytes/values
        db_values = []
        for item in items:
            if isinstance(item, parser.String):
                db_values.extend(str(b) for b in item.value.encode())
            elif isinstance(item, parser.Number):
                db_values.append(str(item.value))
            else:
                raise Exception(f"Unsupported literal: {item}")
        db_values.append("0")  # always null-terminate
        
        label = f"str{len(self.strings)}"
        self.strings[label] = label
        self.rodata.append(f"{label}: db {', '.join(db_values)}")
        return label
    
    def reg_prefix_for_bits(self, bits: int) -> str:
        """
        Return the register width prefix for instruction register names.
        8 -> byte, 16 -> word, 32 -> dword, 64 -> qword
        """
        if bits == 8:
            return "byte"
        if bits == 16:
            return "word"
        if bits == 32:
            return "dword"
        if bits == 64:
            return "qword"
        # fallback
        return "qword"

    def _get_param_reg(self, i: int) -> str:
        reg = "rax"
        if i == 2:
            reg = "rbx"
        elif i == 3:
            reg = "rcx"
        elif i == 4:
            reg = "rdx"
        elif i == 5:
            reg = "rdi"
        elif i == 6:
            reg = "rsi"
        return reg

    def formatCode_raw(self, code:str, vars:list, local_vars:dict={}, global_vars:dict={}, curfunc:str="global") -> str:
        # This func does the same as formatCode but with less defense, and better output
        i = 0
        out_lines = []
        bslash = False
        buffer = ""
        used_vars = 0

        for c in code:
            if c == "\\":
                bslash = True
                continue

            if bslash and c == "n":
                bslash = False
                out_lines.append("\t" + buffer)
                buffer = ""
                continue

            if bslash and c == "$":
                if used_vars >= len(vars):
                    errorHandler.compilerError(("Internal Compiler Error, Not enough variables provided for formatting string!"))
                var = vars[used_vars]
                typ = var[0]
                val = var[1]
                used_vars += 1

                if curfunc and curfunc in local_vars and val in local_vars[curfunc]:
                    offset, _len = local_vars[curfunc][val]
                    buffer += f"[rbp - {offset}]"
                elif val in global_vars:
                    buffer += f"[{val}]"
                else:
                    errorHandler.compilerError(f"RAW Compiler Error, Variable: '{val}' was not found!")
                bslash = False
                continue

            buffer += c
            i += 1

        out_lines.append("\t" + buffer)

        return "\n".join(out_lines)

    def opr_pointer_aware(self, left_reg, right_reg, left_type, right_type, op, target_reg):
        if op == lexer.TOK_PLUS:
            if isinstance(left_type, parser.Pointer) and isinstance(right_type, parser.Number):
                scale = bits_to_bytes(type_bits(left_type.target, ptr_size=64, src=self.code))
                self.text.append(f"\timul {right_reg}, {scale}")
            elif isinstance(right_type, parser.Pointer) and isinstance(left_type, parser.Number):
                scale = bits_to_bytes(type_bits(right_type.target, ptr_size=64, src=self.code))
                self.text.append(f"\timul {left_reg}, {scale}")
            elif isinstance(left_type, parser.Pointer) and isinstance(right_type, parser.Pointer):
                errorHandler.compilerError("Cannot add two pointers!", line=left_type.line, col=left_type.col, src=self.code, file=self.file)
        elif op == lexer.TOK_SUB:
            if isinstance(left_type, parser.Pointer) and isinstance(right_type, parser.Number):
                scale = bits_to_bytes(type_bits(left_type.target, ptr_size=64, src=self.code))
                self.text.append(f"\timul {right_reg}, {scale}")
            elif isinstance(left_type, parser.Pointer) and isinstance(right_type, parser.Pointer):
                scale = bits_to_bytes(type_bits(left_type.target, ptr_size=64, src=self.code))
                self.text.append(f"\tsub {left_reg}, {right_reg}")
                if scale > 1:
                    self.text.append(f"\tidiv {scale}")  # element difference
            elif isinstance(right_type, parser.Pointer) and isinstance(left_type, parser.Number):
                errorHandler.compilerError("Cannot subtract pointer from integer!", line=left_type.line, col=left_type.col, src=self.code, file=self.file)
        else:
            if isinstance(left_type, parser.Pointer) or isinstance(right_type, parser.Pointer):
                errorHandler.compilerError("Invalid arithmetic with pointer!", line=left_type.line, col=left_type.col, src=self.code, file=self.file)

    def compile_expr(self, e:object, target_reg:str="rax", right_reg:str="rbx", left_reg:str="rcx"):
        # Return semantics: many nodes set rax and return a Python value/label where appropriate.
        if isinstance(e, parser.Number):
            self.text.append(f"\tmov {target_reg}, {e.value}")
            return int(e.value)
        elif isinstance(e, parser.Bool):
            v = 1 if e.value == True else 0
            self.text.append(f"\tmov {target_reg}, {v}")
            return v
        elif isinstance(e, parser.String):
            lbl = self.add_string(e.value)
            self.text.append(f"\tlea {target_reg}, [{lbl}]")
            return lbl
        elif isinstance(e, parser.Char):
            value = f"'{e.value}'"
            if len(e.value) > 1:
                fchar = e.value[0]
                if not fchar == "\\" or len(e.value) > 2:
                    errorHandler.compilerError("Cannot denote a string with ('), it is meant for characters!\n\tTip: Use (\") for strings", line=e.line, col=e.col, src=self.code, file=self.file)
                schar = e.value[1]
                if schar == "0":
                    value = "0"
                elif schar == "n":
                    value = "10"
                else:
                    errorHandler.compilerError("Cannot denote a string with ('), it is meant for characters!\n\tTip: Use (\") for strings", line=e.line, col=e.col, src=self.code, file=self.file)

            self.text.append(f"\tmov {target_reg}, {value}")
            value = value.replace("'", "")
            try:
                return ord(value)
            except TypeError:
                errorHandler.compilerError(f"Multiple Bytes [{value}] defined in character!", line=e.line, col=e.col, src=self.code, file=self.file)
        elif isinstance(e, parser.Var):
            # Load variable into rax and return current known value if any
            if e.name in self.global_vars:
                len_bytes = self.global_vars[e.name]
                prefix = self.reg_prefix_for_bits((len_bytes if len_bytes > 0 else 8) * 8)
                if prefix == "qword":
                    self.text.append(f"\tmov {target_reg}, [{e.name}]")
                else:
                    self.text.append(f"\tmov {prefix} {target_reg}, [{e.name}]")
                
                return self.global_vars_value.get(e.name, 0)
            else:
                if self.cur_func and self.cur_func in self.local_vars and e.name in self.local_vars[self.cur_func]:
                    offset, size_bytes = self.local_vars[self.cur_func][e.name]
                    prefix = self.reg_prefix_for_bits((size_bytes if size_bytes>0 else 8) * 8)

                    if prefix == "qword":
                        self.text.append(f"\tmov {target_reg}, [rbp - {offset}]")
                    else:
                        self.text.append(f"\tmov {prefix} {target_reg}, [rbp - {offset}]")
                
                    return self.local_vars_value.get(self.cur_func, {}).get(e.name, 0)
                else:
                    errorHandler.compilerError(f"Unknown variable: '{e.name}' in '{self.cur_func if self.cur_func else 'global'}'", line=e.line, col=e.col, src=self.code, file=self.file)
                    return 0
        elif isinstance(e, parser.BinaryOp):
            # Evaluate left, push, then evaluate right.
            left_val = self.compile_expr(e.left, target_reg)
            self.text.append(f"\tpush {target_reg}")
            right_val = self.compile_expr(e.right, target_reg)
            
            self.text.append(f"\tmov {right_reg}, {target_reg}") # right
            self.text.append(f"\tpop {left_reg}") # left

            self.opr_pointer_aware(left_reg, right_reg, e.left, e.right, e.op, target_reg)

            if e.op == lexer.TOK_PLUS:
                self.text.append(f"\tadd {left_reg}, {right_reg}")
                self.text.append(f"\tmov {target_reg}, {left_reg}")
                return (left_val if isinstance(left_val, int) else 0) + (right_val if isinstance(right_val, int) else 0)
            elif e.op == lexer.TOK_SUB:
                self.text.append(f"\tsub {left_reg}, {right_reg}")
                self.text.append(f"\tmov {target_reg}, {left_reg}")
                return (left_val if isinstance(left_val, int) else 0) - (right_val if isinstance(right_val, int) else 0)
            elif e.op == lexer.TOK_MUL:
                # signed multiply
                self.text.append(f"\timul {left_reg}, {right_reg}")
                self.text.append(f"\tmov {target_reg}, {left_reg}")
                return (left_val if isinstance(left_val, int) else 0) * (right_val if isinstance(right_val, int) else 0)
            elif e.op == lexer.TOK_DIV:
                # signed division
                if not target_reg == "rax":
                    self.text.append(f"\tpush rax")
                self.text.append(f"\tmov rax, {left_reg}")
                self.text.append(f"\tcqo")
                self.text.append(f"\tidiv {right_reg}")
                if not target_reg == "rax":
                    self.text.append(f"\tmov {target_reg}, rax")
                    self.text.append("\tpop rax")
                # idiv returns quotient in rax
                return None if right_val == 0 else (left_val // right_val if isinstance(left_val, int) and isinstance(right_val, int) else None)
            elif e.op in [lexer.TOK_EQUALS, lexer.TOK_NE, lexer.TOK_GT, lexer.TOK_LT, lexer.TOK_GTE, lexer.TOK_LTE]:
                label_true = f".cmp_true_{self.cur_func}_{self.subfunc_count}"
                label_false = f".cmp_false_{self.cur_func}_{self.subfunc_count}"
                label_end = f".cmp_end_{self.cur_func}_{self.subfunc_count}"
                self.subfunc_count += 1
                self.text.append(f"\tcmp {left_reg}, {right_reg}")
                keyword = ""
                if e.op == lexer.TOK_EQUALS:
                    keyword = "je"
                elif e.op == lexer.TOK_NE:
                    keyword = "jne"
                elif e.op == lexer.TOK_GT:
                    keyword = "jg"
                elif e.op == lexer.TOK_LT:
                    keyword = "jl"
                elif e.op == lexer.TOK_GTE:
                    keyword = "jge"
                elif e.op == lexer.TOK_LTE:
                    keyword = "jle"
                else:
                    errorHandler.compilerError(f"Unsupported logical operator: '{e.op}'", line=e.line, col=e.col, src=self.code, file=self.file)

                self.text.append(f"\t{keyword} {label_true}")
                self.text.append(f"\tjmp {label_false}")
                self.text.append(f"{label_true}:")
                self.text.append(f"\tmov {target_reg}, 1")
                self.text.append(f"\tjmp {label_end}")
                self.text.append(f"{label_false}:")
                self.text.append(f"\tmov {target_reg}, 0")
                self.text.append(f"\tjmp {label_end}")
                self.text.append(f"{label_end}:")
                self.current_label = label_end
            else:
                errorHandler.compilerError(f"Unsupported binary operator: '{e.op}'", line=e.line, col=e.col, src=self.code, file=self.file)
                return None
        elif isinstance(e, parser.Assignment):
            # Evaluate RHS, then store into variable location
            self.compile_expr(e.value)  # rax will hold result
            if e.name in self.global_vars:
                self.text.append(f"\tmov [{e.name}], {target_reg}")
                # keep a python-level value if available
                self.global_vars_value[e.name] = getattr(e.value, "value", None) if isinstance(e.value, parser.Number) else None
            else:
                if self.cur_func and self.cur_func in self.local_vars and e.name in self.local_vars[self.cur_func]:
                    offset, size_bytes = self.local_vars[self.cur_func][e.name]
                    prefix = self.reg_prefix_for_bits((size_bytes if size_bytes>0 else 8) * 8)
                    if prefix == "qword":
                        self.text.append(f"\tmov [rbp - {offset}], {target_reg}")
                    else:
                        self.text.append(f"\tmov {prefix} [rbp - {offset}], {target_reg}")
                    if self.cur_func not in self.local_vars_value:
                        self.local_vars_value[self.cur_func] = {}
                    self.local_vars_value[self.cur_func][e.name] = getattr(e.value, "value", None) if isinstance(e.value, parser.Number) else None
            return None
        elif isinstance(e, parser.FuncCall):
            # Evaluate args left-to-right and place into rax..rsi
            if e.args:
                i = 1
                for arg in e.args:
                    reg = self._get_param_reg(i)
                    self.compile_expr(arg, reg)
                    i += 1
            self.text.append(f"\tcall {e.name}")
            # assume return in qG0
            return None
        elif isinstance(e, parser.Cast):
            if isinstance(e.target_type, parser.Pointer):
                self.compile_expr(e.expr, target_reg) if not isinstance(e.expr, parser.Pointer) else None
                return 0
            # Compile inner expression; the value will be in target_reg
            inner_val = self.compile_expr(e.expr, target_reg)
            target_bits = type_bits(e.target_type, ptr_size=64, src=self.code)

            if isinstance(e.target_type, parser.Unsigned):
                # zero-extend (mask)
                if target_bits < 64:
                    mask = mask_for_bits(target_bits)
                    self.text.append(f"\tand {target_reg}, {mask}")
            elif isinstance(e.target_type, parser.Signed):
                # sign-extend
                if target_bits == 8:
                    self.text.append(f"\tmovsxb {target_reg}, al")
                elif target_bits == 16:
                    self.text.append(f"\tmovsx {target_reg}, ax")
                elif target_bits == 32:
                    self.text.append(f"\tmovsxd {target_reg}, eax")

            return inner_val
        elif isinstance(e, parser.DerefPointer):
            self.compile_expr(e.target, target_reg)
            self.text.append(f"\tmov {target_reg}, [{target_reg}]")
        elif isinstance(e, parser.Pointer):
            self.compile_expr(e.target, target_reg, right_reg, left_reg)
            self.text.append(f"\tlea {target_reg}, [{target_reg}]")
        elif isinstance(e, parser.Increment):
            if isinstance(e.expr, parser.Var):
                var = e.expr
                if var.name in self.global_vars:
                    self.text.append(f"\tinc qword [{var.name}]")
                    self.text.append(f"\tmov {target_reg}, [{var.name}]")  # load new value into reg
                elif self.cur_func and var.name in self.local_vars.get(self.cur_func, {}):
                    offset, size_bytes = self.local_vars[self.cur_func][var.name]
                    prefix = self.reg_prefix_for_bits((size_bytes if size_bytes > 0 else 8) * 8)
                    self.text.append(f"\tinc {prefix} [rbp - {offset}]")
                    self.text.append(f"\tmov {target_reg}, {prefix} [rbp - {offset}]")
                else:
                    errorHandler.compilerError(f"Unknown variable in increment: '{var.name}'", line=e.line, col=e.col, src=self.code, file=self.file)
                return
            else:
                # Fallback: if it's not a variable, just increment value in register
                self.compile_expr(e.expr, target_reg=target_reg)
                self.text.append(f"\tinc {target_reg}")
                return
        elif isinstance(e, parser.Decrement):
            if isinstance(e.expr, parser.Var):
                var = e.expr
                if var.name in self.global_vars:
                    self.text.append(f"\tdec qword [{var.name}]")
                    self.text.append(f"\tmov {target_reg}, [{var.name}]")  # load new value into reg
                elif self.cur_func and var.name in self.local_vars.get(self.cur_func, {}):
                    offset, size_bytes = self.local_vars[self.cur_func][var.name]
                    prefix = self.reg_prefix_for_bits((size_bytes if size_bytes > 0 else 8) * 8)
                    self.text.append(f"\tdec {prefix} [rbp - {offset}]")
                    self.text.append(f"\tmov {target_reg}, {prefix} [rbp - {offset}]")
                else:
                    errorHandler.compilerError(f"Unknown variable in increment: '{var.name}'",
                                            line=e.line, col=e.col, src=self.code, file=self.file)
                return
            else:
                # Fallback: if it's not a variable, just decrement value in register
                self.compile_expr(e.expr, target_reg=target_reg)
                self.text.append(f"\tdec {target_reg}")
                return
        else:
            errorHandler.compilerError(f"Parser/Compiler Error, Unsupported expression node: '{type(e)}'")
            return None
                
    def compile_stmt(self, s):
        # top-level statement compiler
        if isinstance(s, parser.VarDecl):
            # Global variable
            if s.name not in self.global_vars and s.global_ == True:
                size_bits = type_bits(s.var_type, ptr_size=64, src=self.code)
                size_bytes = bits_to_bytes(size_bits)
                if size_bytes == 0:
                    self.global_vars[s.name] = 0
                    self.global_vars_value[s.name] = None
                    return
                init_val = NULL
                if s.value and isinstance(s.value, parser.Number):
                    init_val = str(s.value.value)
                elif s.value and isinstance(s.value, parser.String):
                    other_vals = self.handle_string(s.value.value)
                    
                    self.data.append(f"{s.name}: db {', '.join(other_vals)}, {NULL}")
                    init_val = s.value.value

                    self.global_vars[s.name] = size_bytes
                    self.global_vars_value[s.name] = init_val

                    return

                # choose directive for initialized vs uninitialized
                if s.value:
                    if size_bytes == 1:
                        directive = "db"
                        self.data.append(f"{s.name}: {directive} {init_val}")
                    elif size_bytes == 2:
                        directive = "dw"
                        self.data.append(f"{s.name}: {directive} {init_val}")
                    elif size_bytes == 4:
                        directive = "dd"
                        self.data.append(f"{s.name}: {directive} {init_val}")
                    elif size_bytes == 8:
                        directive = "dq"
                        self.data.append(f"{s.name}: {directive} {init_val}")
                    elif size_bytes == 0:
                        errorHandler.compilerError("Tried to initialize a void!", line=s.line, col=s.col, src=self.code, file=self.file)
                    else:
                        # large initialized object -> emit db bytes (simple case)
                        bytes_list = ", ".join(str(b) for b in (init_val if isinstance(init_val, str) else [0]))
                        self.data.append(f"{s.name}: db {bytes_list}")
                else:
                    # uninitialized -> bss
                    self.bss.append(f"{s.name}: resb {size_bytes}")

                # store global size in BYTES
                self.global_vars[s.name] = size_bytes
                self.global_vars_value[s.name] = init_val
                return
            else:
                # Local variable
                if isinstance(s.var_type, parser.Void):
                    # nothing to allocate
                    return
                if not s.value:
                    # BSS
                    if not self.cur_func or self.cur_func not in self.local_vars or s.name not in self.local_vars[self.cur_func]:
                        errorHandler.compilerError(f"Internal Compiler Error, No slot for local variable '{s.name}' in '{self.cur_func}'")
                    off, size = self.local_vars[self.cur_func][s.name]

                    if self.cur_func not in self.local_vars_value:
                        self.local_vars_value[self.cur_func] = {}
                    self.local_vars_value[self.cur_func][s.name] = None
                else:
                    if not self.cur_func or self.cur_func not in self.local_vars or s.name not in self.local_vars[self.cur_func]:
                        errorHandler.compilerError(f"Internal Compiler Error, No slot for local variable '{s.name}' in '{self.cur_func}'", line=s.line, col=s.col, src=self.code, file=self.file)
                    off, size = self.local_vars[self.cur_func][s.name]
                    self.compile_expr(s.value) #rax holds init
                    prefix = self.reg_prefix_for_bits(size * 8 if size > 0 else 64)
                    if prefix == "qword":
                        self.text.append(f"\tmov [rbp - {off}], rax")
                    else:
                        self.text.append(f"\tmov {prefix} [rbp - {off}], rax")

                    if self.cur_func not in self.local_vars_value:
                        self.local_vars_value[self.cur_func] = {}
                    self.local_vars_value[self.cur_func][s.name] = getattr(s.value, "value", None) if isinstance(s.value, parser.Number) else None

            # initializer: if present, do assignment to variable
            if s.value:
                # compile as if assignment
                self.compile_expr(parser.Assignment(s.name, s.value, s.line, s.col))

        elif isinstance(s, parser.Include):
            self.og_code.append(self.code)
            self.og_file.append(self.file)
            self.code = s.code
            self.file = s.filename

            for stmt in s.body:
                self.compile_stmt(stmt)
            
            self.code = self.og_code.pop()
            self.file = self.og_file.pop()
        elif isinstance(s, parser.RunLang):
            if s.language == "python-simple":
                errorHandler.compilerError("Python-Simple will not work without AVM!", line=s.line, col=s.col, src=self.code, file=self.file)
            elif s.language == "vasm":
                errorHandler.compilerError("Due to safety, implementing VASM in x86_64 is not possible!\n", line=s.line, col=s.col, src=self.code, file=self.file)
            elif s.language == "asm":
                self.text.append("; ASM Runlang")
                code = self.formatCode_raw(s.code, s.vars, self.local_vars, self.global_vars, self.cur_func)
                self.text.append(f"{code}")
                self.text.append(f"; Runlang-End")
            else:
                # Generic runlang call
                pass
        elif isinstance(s, parser.FuncDecl):
            # finalize previous function if any
            if self.cur_func:
                # generate epilogue for previous function
                self.text.append("\tmov rax, 0")
                self.text.append("\tmov rsp, rbp")
                self.text.append("\tadd rsp, 8")
                self.text.append("\tpop rbp")
                self.text.append("\tret")
                self.current_offset_from_sf = 0
                self.cur_func = ""
            
            self.funcs.append(s.name)
            self.cur_func = s.name
            self.current_label = s.name
            self.subfunc_count = 0
            
            self.text.append(s.name + ":")

            alloc_list = []
            if s.params:
                i = 1
                for param in s.params:
                    size_bits = type_bits(param, ptr_size=64, src=self.code)
                    size_bytes = bits_to_bytes(size_bits)
                    if size_bytes == 0:
                        alloc_list.append((param.name, 0, "param", param)) 
                        continue # Skip voids
                    size_aligned = align_up(size_bytes, 16) # align param storage to 16
                    alloc_list.append((param.name, size_aligned, "param", param))
                    i += 1

            # scan body for local var declarations
            for stmt in s.body:
                if getattr(stmt, "treat_as_variable", False):
                    if not getattr(stmt, "global_", False):
                        size_bits = type_bits(getattr(stmt, "var_type", None), ptr_size=64, src=self.code)
                        size_bytes = bits_to_bytes(size_bits)
                        if size_bytes == 0:
                            alloc_list.append((getattr(stmt, "name", "unknown"), 0, "local", stmt))
                            continue # Skip voids
                        size_aligned = align_up(size_bytes, 8)
                        alloc_list.append((getattr(stmt, "name", "unknown"), size_aligned, "local", stmt))
                        continue
                if isinstance(stmt, parser.VarDecl) and not getattr(stmt, "global_", False):
                    size_bits = type_bits(stmt.var_type, ptr_size=64, src=self.code)
                    size_bytes = bits_to_bytes(size_bits)
                    if size_bytes == 0:
                        alloc_list.append((stmt.name, 0, "local", stmt))
                        continue # Skip voids
                    size_aligned = align_up(size_bytes, 8)
                    alloc_list.append((stmt.name, size_aligned, "local", stmt))

            # compute offsets
            offsets = {}
            cur_off = 0
            for name, size_aligned, kind, origin in alloc_list:
                offsets[name] = (cur_off, size_aligned)
                cur_off += size_aligned

            frame_size = align_up(cur_off, 16)

            # emit prologue
            self.text.append("\tpush rbp")
            self.text.append("\tsub rsp, 8")
            self.text.append("\tmov rbp, rsp")
            if frame_size > 0:
                self.text.append(f"\tsub rsp, {frame_size}")
            
            self.local_vars[self.cur_func] = offsets
            self.local_vars_value[self.cur_func] = {}

            if s.params:
                i = 1
                for param in s.params:
                    off, size = self.local_vars[self.cur_func][param.name]
                    if size == 0: continue # Skip voids
                    reg = self._get_param_reg(i)

                    prefix = self.reg_prefix_for_bits(size * 8 if size > 0 else 64)
                    if prefix == "qword":
                        self.text.append(f"\tmov [rbp - {off}], {reg}")
                    else:
                        self.text.append(f"\tmov {prefix} [rbp - {off}], {reg}")
                    i += 1

            # compile body
            for stmt in s.body:
                self.compile_stmt(stmt)
        elif isinstance(s, parser.ReturnStmt):
            if s.value:
                self.compile_expr(s.value)
            else:
                self.text.append("\tmov rax, 0")
            # function epilogue
            self.text.append("\tmov rsp, rbp")
            self.text.append("\tadd rsp, 8")
            self.text.append("\tpop rbp")
            self.text.append("\tret")
            # cleanup function locals
            if self.cur_func == self.current_label:
                self.current_offset_from_sf = 0
                self.local_vars.pop(self.cur_func, None)
                self.cur_func = ""
        elif isinstance(s, parser.If):
            self.compile_expr(s.condition, target_reg="rax")
            new_label = f".if_{self.cur_func}_{self.subfunc_count}"
            end_label = f".endif_{self.cur_func}_{self.subfunc_count}"
            self.subfunc_count += 1
            self.text.append(f"\tcmp rax, 1")
            self.text.append(f"\tje {new_label}")
            self.text.append(f"\tjmp {end_label}")
            self.text.append(f"{new_label}:")
            self.current_label = new_label
            for stmt in s.code:
                self.compile_stmt(stmt)
            self.text.append(f"{end_label}:")
            self.current_label = self.cur_func
        elif isinstance(s, parser.While):
            while_label = f".while_{self.cur_func}_{self.subfunc_count}"
            self.text.append(f"{while_label}:")
            self.compile_expr(s.condition, target_reg="rax")
            end_label = f".while_end_{self.cur_func}_{self.subfunc_count}"
            self.subfunc_count += 1
            self.text.append(f"\tcmp rax, 0")
            self.text.append(f"\tje {end_label}")
            self.current_label = while_label
            for stmt in s.code:
                self.compile_stmt(stmt)
            self.text.append(f"\tjmp {while_label}")
            self.text.append(f"{end_label}:")
            self.current_label = self.cur_func
        elif isinstance(s, parser.For):
            for_label = f".for_{self.cur_func}_{self.subfunc_count}"
            self.compile_stmt(s.initializer)
            self.text.append(f"{for_label}:")
            self.compile_expr(s.condition, target_reg="rax")
            end_label = f".for_end_{self.cur_func}_{self.subfunc_count}"
            self.subfunc_count += 1
            self.text.append(f"\tcmp rax, 0")
            self.text.append(f"\tje {end_label}")
            self.current_label = for_label
            for stmt in s.code:
                self.compile_stmt(stmt)
            self.compile_stmt(s.increment)
            self.text.append(f"jmp {for_label}")
            self.text.append(f"{end_label}:")
            self.current_label = self.cur_func
        else:
            # expression statement
            self.compile_expr(s)
    
    def create_injections(self, entry_name:str="main"):
        # entry
        self.text.append("section .text")
        self.text.append(f"global {_START}")
        self.text.append(f"{_START}:")
        self.text.append("\tmov rax, [rsp]") # Get argc
        self.text.append("\tlea rbx, [rsp + 8]") # Get memaddr of argv
        self.text.append(f"\tcall {entry_name}")
        self.text.append("\tmov rdi, rax")
        self.text.append(f"\tmov rax, {SYS_EXIT_x86_64_LINUX}")
        self.text.append("\tsyscall")

        # strlen
        self.text.append("__arris__compilerinjected__strlen:")
        self.text.append("\tpush rbp")
        self.text.append("\tsub rsp, 8")
        self.text.append("\tmov rbp, rsp")
        self.text.append("\tmov rbx, rax") # arg 1 into rbx
        self.text.append("\tmov rax, 0")
        self.text.append(".__arris__compilerinjected__strlen_loop:")
        self.text.append("\tmov cl, byte [rbx + rax]")
        self.text.append("\tcmp cl, 0")
        self.text.append("\tje .__arris__compilerinjected__strlen_done")
        self.text.append("\tinc rax")
        self.text.append("\tjmp .__arris__compilerinjected__strlen_loop")
        self.text.append(".__arris__compilerinjected__strlen_done:")
        self.text.append("\tmov rsp, rbp")
        self.text.append("\tadd rsp, 8")
        self.text.append("\tpop rbp")
        self.text.append("\tret")

    def compile(self):
        entryname = "main" if not self.entry else self.entry
        searched_entry:bool = False
        ce = None
        for i, s in enumerate(self.ast): # find entry
            if isinstance(s, parser.CompilerEntry):
                entryname = s.func
                searched_entry = True
                ce = s
                self.ast.pop(i)
                break

        for s in self.ast: # find func
            if isinstance(s, parser.FuncDecl):
                if entryname == s.name:
                    break
        else:
            if ce is None:
                errorHandler.compilerError(f"Could not find function: {entryname} to serve as entry point!", file=self.file)
            else:
                errorHandler.compilerError(f"Could not find function: {entryname} to serve as entry point!", file=ce.filename, line=ce.line, col=ce.col, src=ce.code)

        if self.add_stdlib:
            self.create_injections(entryname)
        else:
            if not searched_entry and not self.entry:
                errorHandler.compilerError("Please specify entry point if not using runtime!", file=self.file)
            self.text.append("section .text")
            self.text.append(f"\tglobal {entryname}")
                    
        # compile top-level declarations/statements
        for s in self.ast:
            self.compile_stmt(s)

        # assemble output sections
        out = []
        out.append("[BITS 64]\n")
        # Data
        out.append("section .data")
        if self.data:
            out.extend(self.data)
        # BSS
        out.append("section .bss")
        if self.bss:
            out.extend(self.bss)
        # ROdata
        out.append("section .rodata")
        if self.rodata:
            out.extend(self.rodata)
        # Text
        out.extend(self.text)
        return "\n".join(out)
    
