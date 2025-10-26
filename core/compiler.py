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

def type_bits(type_token: str, ptr: bool = False) -> int:
    """
    Return bit-width for a given type token (using lexer tokens).
    If ptr is True, return pointer size (64 by default).
    """
    if ptr:
        # pointer width is platform ptr size (64 bits in this compiler)
        return 64

    if type_token in [lexer.TOK_CHAR, lexer.TOK_BYTE]:
        return 8
    if type_token == lexer.TOK_WORD:
        return 16
    if type_token in [lexer.TOK_INT, lexer.TOK_UINT, lexer.TOK_DWORD]:
        return 32
    if type_token in [lexer.TOK_QWORD, lexer.TOK_LONG]:
        return 64
    if type_token in [lexer.TOK_BIT, lexer.TOK_BOOL]:
        return 8
    if type_token == lexer.TOK_VOID:
        return 0
    # unknown -> error
    errorHandler.compilerError(f"Unknown type token: {type_token}")
    return 0

def reg_prefix_for_bits(bits: int) -> str:
    """
    Return the register width prefix for instruction register names.
    8 -> b, 16 -> w, 32 -> d, 64 -> q
    """
    if bits == 8:
        return "b"
    if bits == 16:
        return "w"
    if bits == 32:
        return "d"
    if bits == 64:
        return "q"
    # fallback
    return "q"

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

def formatString(string:str, vars:list, local_vars:dict={}, global_vars:dict={}, curfunc:str="__main") -> str:
    i = 0
    res = ""
    bslash = False

    for c in string:
        if c == "\\":
            bslash = True
            continue

        if bslash and c == "$":
            if i >= len(vars):
                errorHandler.compilerError("Format string: not enough variables provided")
            var = vars[i]
            typ = var[0]
            val = var[1]

            if typ == lexer.TOK_LIT_CHAR or typ == lexer.TOK_LIT_STRING:
                res += val
            elif typ == lexer.TOK_LIT_INT or typ == lexer.TOK_LIT_UINT:
                res += str(val)
            elif typ == lexer.TOK_IDENTIFIER:
                if curfunc in local_vars and val in local_vars[curfunc]:
                    val_loc = local_vars[curfunc][val]
                    res += str(val_loc)
                elif val in global_vars:
                    res += str(global_vars[val])
                else:
                    errorHandler.compilerError(f"Unknown variable: {val} in {curfunc if curfunc else "global"}")
            else:
                # fallback: stringify
                res += str(val)

            i += 1
            bslash = False
            continue

        bslash = False
        res += c

    return res

def formatCode_raw(code:str, vars:list, local_vars:dict={}, global_vars:dict={}, curfunc:str="global") -> str:
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
                errorHandler.compilerError(("formatCode: no enough variables provided"))
            var = vars[used_vars]
            typ = var[0]
            val = var[1]
            used_vars += 1

            if curfunc and curfunc in local_vars and val in local_vars[curfunc]:
                offset, _len = local_vars[curfunc][val]
                buffer += f"[qSF + {offset}]"
            elif val in global_vars:
                buffer += f"[{val}]"
            else:
                errorHandler.compilerError(f"Variable: {val} was not found!")
            bslash = False
            continue

        buffer += c
        i += 1

    out_lines.append("\t" + buffer)

    return "\n".join(out_lines)

def formatCode(code:str, vars:list, local_vars:dict={}, global_vars:dict={}, curfunc:str="global") -> str:
    # This function emits VASM snippets as text lines. Keep behavior but be defensive.
    i = 0
    out_lines = []
    bslash = False

    local_vars = local_vars or {}
    global_vars = global_vars or {}

    for c in code:
        if c == "\\":
            bslash = True
            continue

        if bslash and c == "$":
            if i >= len(vars):
                errorHandler.compilerError("formatCode: not enough variables provided")
            var = vars[i]
            typ = var[0]
            val = var[1]

            # variable replacement: if local, load from [qSF + offset], else global
            if curfunc and curfunc in local_vars and val in local_vars[curfunc]:
                offset, _len = local_vars[curfunc][val]
                out_lines.append(f"\tmov qG14, [qSF + {offset}]")
                out_lines.append(f"\tpush qG14")
                i += 1
                bslash = False
                continue
            elif val in global_vars:
                out_lines.append(f"\tmov qG14, [{val}]")
                out_lines.append(f"\tpush qG14")
                i += 1
                bslash = False
                continue
            else:
                errorHandler.compilerError(f"Unknown variable: {val} in {curfunc if curfunc else 'global'}")
                # fallthrough (but normally compilerError exits)
        
        if bslash:
            # an escaped non-$ char, just emit it
            out_lines.append(f"\tpush '{c}'")
            bslash = False
            continue

        # default: push character bytes
        out_lines.append(f"\tpush '{c}'")

    out_lines.append("\tpush 0")
    return "\n".join(out_lines)


class ArrisCompiler64(): # Outputs NASM syntax but follows PVCpu registers (64-bit)
    def __init__(self, ast:list):
        self.ast:list = ast

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
        # Use db for bytes, zero terminated
        self.rodata.append(f"{label}: db {', '.join(str(b) for b in s.encode())}, 0")
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
    
    def compile_expr(self, e:object):
        # Return semantics: many nodes set qG0 and return a Python value/label where appropriate.
        if isinstance(e, parser.Number):
            self.text.append(f"\tmov qG0, {e.value}")
            return int(e.value)
        elif isinstance(e, parser.Bool):
            v = 1 if e.value == True else 0
            self.text.append(f"\tmov qG0, {v}")
            return v
        elif isinstance(e, parser.String):
            lbl = self.add_string(e.value)
            self.text.append(f"\tlea qG0, [{lbl}]")
            return lbl
        elif isinstance(e, parser.Var):
            # Load variable into qG0 and return current known value if any
            if e.name in self.global_vars:
                len_bytes = self.global_vars[e.name]
                prefix = reg_prefix_for_bits((len_bytes if len_bytes > 0 else 8) * 8)
                if prefix == "q":
                    self.text.append(f"\tmov, qG0, [{e.name}]")
                else:
                    self.text.append(f"\tmov {prefix}G0, [{e.name}]")
                    self.text.append(f"\tmov qG0, {prefix}G0")
                return self.global_vars_value.get(e.name, 0)
            else:
                if self.cur_func and self.cur_func in self.local_vars and e.name in self.local_vars[self.cur_func]:
                    offset, size_bytes = self.local_vars[self.cur_func][e.name]
                    prefix = reg_prefix_for_bits((size_bytes if size_bytes>0 else 8) * 8)
                    if prefix == "q":
                        self.text.append(f"\tmov qG0, [qSF + {offset}]")
                    else:
                        self.text.append(f"\tmov {prefix}G0, [qSF + {offset}]")
                        self.text.append(f"\tmov qG0, {prefix}G0")
                    return self.local_vars_value.get(self.cur_func, {}).get(e.name, 0)
                else:
                    errorHandler.compilerError(f"Unknown variable: {e.name} in {self.cur_func if self.cur_func else 'global'}")
                    return 0
        elif isinstance(e, parser.BinaryOp):
            # Evaluate left, push, then evaluate right.
            left_val = self.compile_expr(e.left)
            self.text.append("\tpush qG0")
            right_val = self.compile_expr(e.right)
            # qG0 currently holds right operand, popped value in stack is left operand
            self.text.append("\tmov qG1, qG0")   # right into qG1
            self.text.append("\tpop qG2")       # left into qG2
            if e.op == lexer.TOK_PLUS:
                self.text.append("\tadd qG2, qG1")
                self.text.append("\tmov qG0, qG2")
                return (left_val if isinstance(left_val, int) else 0) + (right_val if isinstance(right_val, int) else 0)
            elif e.op == lexer.TOK_SUB:
                self.text.append("\tsub qG2, qG1")
                self.text.append("\tmov qG0, qG2")
                return (left_val if isinstance(left_val, int) else 0) - (right_val if isinstance(right_val, int) else 0)
            elif e.op == lexer.TOK_MUL:
                # imul qG2, qG1  ; signed multiply
                self.text.append("\timul qG2, qG1")
                self.text.append("\tmov qG0, qG2")
                return (left_val if isinstance(left_val, int) else 0) * (right_val if isinstance(right_val, int) else 0)
            elif e.op == lexer.TOK_DIV:
                # signed division: dividend in qG2, divisor in qG1
                self.text.append("\tmov qG0, qG2")
                self.text.append("\tcqo")
                self.text.append("\tidiv qG1")
                # idiv returns quotient in qG0
                return None if right_val == 0 else (left_val // right_val if isinstance(left_val, int) and isinstance(right_val, int) else None)
            else:
                errorHandler.compilerError(f"Unsupported binary operator: {e.op}")
                return None
        elif isinstance(e, parser.Assignment):
            # Evaluate RHS, then store into variable location
            self.compile_expr(e.value)  # qG0 will hold result
            if e.name in self.global_vars:
                self.text.append(f"\tmov [{e.name}], qG0")
                # keep a python-level value if available
                self.global_vars_value[e.name] = getattr(e.value, "value", None) if isinstance(e.value, parser.Number) else None
            else:
                if self.cur_func and self.cur_func in self.local_vars and e.name in self.local_vars[self.cur_func]:
                    offset, size_bytes = self.local_vars[self.cur_func][e.name]
                    prefix = reg_prefix_for_bits((size_bytes if size_bytes>0 else 8) * 8)
                    if prefix == "q":
                        self.text.append(f"\tmov [qSF + {offset}], qG0")
                    else:
                        self.text.append(f"\tmov {prefix}G0, qG0")
                        self.text.append(f"\tmov [qSF + {offset}], {prefix}G0")
                    if self.cur_func not in self.local_vars_value:
                        self.local_vars_value[self.cur_func] = {}
                    self.local_vars_value[self.cur_func][e.name] = getattr(e.value, "value", None) if isinstance(e.value, parser.Number) else None
            return None
        elif isinstance(e, parser.FuncCall):
            # Evaluate args left-to-right and place into qG1..qG5
            if e.args:
                i = 1
                for arg in e.args:
                    self.compile_expr(arg)  # sets qG0
                    # move qG0 into qGi; use mov qG{i}, qG0
                    self.text.append(f"\tmov qG{i}, qG0")
                    i += 1
            self.text.append(f"\tcall {e.name}")
            # assume return in qG0
            return None
        elif isinstance(e, parser.Cast):
            # Compile inner expression; the value will be in qG0
            inner_val = self.compile_expr(e.expr)
            target_bits = type_bits(e.target_type, getattr(e, "ptr", False))
            # If casting to same or larger width, we keep lower bits (zero-extend)
            if target_bits >= 64:
                # nothing to do (qG0 already 64-bit)
                return inner_val
            else:
                # Truncate/mask to target bits (zero-extend semantics)
                mask = mask_for_bits(target_bits)
                # Use immediate mask via 'and' to preserve lower bits
                self.text.append(f"\tand qG0, {mask}")
                return inner_val
        else:
            errorHandler.compilerError(f"Unsupported expression node: {type(e)}")
            return None
                
    def compile_stmt(self, s):
        # top-level statement compiler
        if isinstance(s, parser.VarDecl):
            # Global variable
            if s.name not in self.global_vars and s.global_ == True:
                size_bits = s.len if hasattr(s, "len") else 8
                size_bytes = bits_to_bytes(size_bits) or 1
                init_val = NULL
                if s.value and isinstance(s.value, parser.Number):
                    init_val = str(s.value.value)
                elif s.value and isinstance(s.value, parser.String):
                    special = False
                    other_vals = []
                    buf = ""
                    for c in s.value.value:
                        if special:
                            if "n" == c:
                                other_vals.append('"' + buf + '"')
                                other_vals.append("10")
                                other_vals.append("14")
                                buf = ""
                            elif ">" == c:
                                other_vals.append('"' + buf + '"')
                                other_vals.append("10")
                                buf = ""
                            elif "<" == c:
                                other_vals.append('"' + buf + '"')
                                other_vals.append("14")
                                buf = ""
                            special = False
                            continue
                        if "\\" == c:
                            special = True
                        buf += c
                    other_vals.append('"' + buf + '"')
                    self.data.append(f"{s.name} db {", ".join(other_vals)}, 0")
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
                if s.var_type == lexer.TOK_VOID and not s.ptr:
                    # nothing to allocate
                    return
                if not s.value:
                    # BSS
                    return # placeholder
                else:
                    if not self.cur_func or self.cur_func not in self.local_vars or s.name not in self.local_vars[self.cur_func]:
                        errorHandler.compilerError(f"Internal compiler error: no slot for local variable {s.name} in {self.cur_func}")
                    off, size = self.local_vars[self.cur_func][s.name]
                    self.compile_expr(s.value) #qG0 holds init
                    prefix = reg_prefix_for_bits(size * 8 if size > 0 else 64)
                    if prefix == "q":
                        self.text.append(f"\tmov [qSF + {off}], qG0")
                    else:
                        self.text.append(f"\tmov {prefix}G0, qG0")
                        self.text.append(f"\tmov [qSF + {off}], {prefix}G0")

                    if self.cur_func not in self.local_vars_value:
                        self.local_vars_value[self.cur_func] = {}
                    self.local_vars_value[self.cur_func][s.name] = getattr(s.value, "value", None) if isinstance(s.value, parser.Number) else None


            # initializer: if present, do assignment to variable
            if s.value:
                # compile as if assignment
                self.compile_expr(parser.Assignment(s.name, s.value))

        elif isinstance(s, parser.RunLang):
            if s.language == "python-simple":
                self.text.append(f";;@Runlang: {s.language}")
                code = formatString(s.code, s.vars, self.local_vars, self.global_vars, self.cur_func)
                self.text.append(f";;{code}")
                self.text.append(f";;@Runlang-End")
            elif s.language == "vasm":
                self.text.append("; VASM Runlang")
                code = formatCode_raw(s.code, s.vars, self.local_vars, self.global_vars, self.cur_func)
                self.text.append(f"{code}")
                self.text.append(f"; Runlang-End")
            else:
                # Generic runlang call
                self.text.append("\tmov qG1, [qSP + 1]\n")
                self.text.append(formatCode(s.code, s.vars, self.local_vars, self.global_vars, self.cur_func))
                self.text.append(f"\tcall runlang_{s.language}")
        elif isinstance(s, parser.FuncDecl):
            # finalize previous function if any
            if self.cur_func:
                # generate epilogue for previous function
                self.text.append("\tmov qG0, 0")
                self.text.append("\tmov qSP, qSF")
                self.text.append("\tpop qSF")
                self.text.append("\tret")
                self.current_offset_from_sf = 0
                self.cur_func = ""
            
            self.funcs.append(s.name)
            self.cur_func = s.name
            
            self.text.append(s.name + ":")

            alloc_list = []
            if s.params:
                i = 1
                for param in s.params:
                    size_bits = getattr(param, "len", 0) or 32
                    size_bytes = bits_to_bytes(size_bits) or 1
                    size_aligned = align_up(size_bytes, 8) # align param storage to 8
                    alloc_list.append((param.name, size_aligned, "param", param))
                    i += 1

            # scan body for local var declarations
            for stmt in s.body:
                if isinstance(stmt, parser.VarDecl) and not getattr(stmt, "global_", False):
                    size_bits = getattr(stmt, "len", 0) or 32
                    size_bytes = bits_to_bytes(size_bits) or 1
                    size_aligned = align_up(size_bytes, 8)
                    alloc_list.append((stmt.name, size_aligned, "local", stmt))

            # compute offsets
            offsets = {}
            cur_off = 0
            for name, size_aligned, kind, origin in alloc_list:
                offsets[name] = (cur_off, size_aligned)
                cur_off += size_aligned

            frame_size = align_up(cur_off, 8)

            # emit prologue
            self.text.append("\tpush qSF")
            self.text.append("\tmov qSF, qSP")
            if frame_size > 0:
                self.text.append(f"\tsub qSF, {frame_size}")
            
            self.local_vars[self.cur_func] = offsets
            self.local_vars_value[self.cur_func] = {}

            if s.params:
                i = 1
                for param in s.params:
                    off, size = self.local_vars[self.cur_func][param.name]
                    prefix = reg_prefix_for_bits(size * 8 if size > 0 else 64)
                    if prefix == "q":
                        self.text.append(f"\tmov [qSF + {off}], qG{i}")
                    else:
                        self.text.append(f"\tmov {prefix}G{i}, qG{i}")
                        self.text.append(f"\tmov [qSF + {off}], {prefix}G{i}")
                    i += 1

            # compile body
            for stmt in s.body:
                self.compile_stmt(stmt)
        elif isinstance(s, parser.ReturnStmt):
            if s.value:
                self.compile_expr(s.value)
            else:
                self.text.append("\tmov qG0, 0")
            # function epilogue
            self.text.append("\tmov qSP, qSF")
            self.text.append("\tpop qSF")
            self.text.append("\tret")
            self.current_offset_from_sf = 0
            # cleanup function locals
            self.local_vars.pop(self.cur_func, None)
            self.cur_func = ""
        else:
            # expression statement
            self.compile_expr(s)
    
    def compile(self):
        # entry prelude
        self.text.append("section .text")
        self.text.append("global __arris__compilerinjected__main") # __main is _start here
        self.text.append("__arris__compilerinjected__main:")
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
        # compile top-level declarations/statements
        for s in self.ast:
            self.compile_stmt(s)

        # assemble output sections
        out = []
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
