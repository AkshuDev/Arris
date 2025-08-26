import struct
import os
import sys
from typing import List, Tuple, Dict, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from instructionSet import *
from phardwareitk.Memory.Memory import Memory as PHWMemory

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import errorHandler

# Asm error alias
def asm_error(*args):
    errorHandler.assemblerError("".join(args))

# Token IDs
TK_ADD = 0
TK_SUB = 1
TK_MUL = 2
TK_DIV = 3
TK_REG = 5
TK_MOV = 6
TK_PUSH = 7
TK_POP = 8
TK_PLUS = 9
TK_MINUS = 10
TK_FSLASH = 11
TK_BSLASH = 12
TK_ASTERIK = 13
TK_COMMA = 14
TK_LABEL = 15
TK_GLOBAL = 16
TK_SECTION = 17
TK_IDENTIFIER = 18
TK_DB = 19
TK_DW = 20
TK_DD = 21
TK_DQ = 22
TK_DT = 23
TK_RESB = 24
TK_IMUL = 25
TK_LBRACKET = 26
TK_RBRACKET = 27
TK_LPAR = 28
TK_RPAR = 29
TK_CQO = 30
TK_IDIV = 31
TK_XCHG = 32
TK_LEA = 33
TK_INC = 34
TK_DEC = 35
TK_NEG = 36
TK_AND = 37
TK_OR = 38
TK_XOR = 39
TK_NOT = 40
TK_SHL = 41
TK_SHR = 42
TK_ROL = 43
TK_ROR = 44
TK_JMP = 45
TK_CALL = 46
TK_RET = 47
TK_JE = 48
TK_JNE = 49
TK_JG = 50
TK_JL = 51
TK_LOOP = 52
TK_MOVS = 53
TK_CMPS = 54
TK_SCAS = 55
TK_LODS = 56
TK_STOS = 57
TK_BT = 58
TK_BTS = 59
TK_BTR = 60
TK_BTC = 61
TK_BSF = 62
TK_BSR = 63
TK_INT = 64
TK_SYSCALL = 65
TK_HLT = 66
TK_NOP = 67
TK_IRET = 68
TK_CPUID = 69
TK_RDTSC = 70
TK_RESW = 71
TK_RESD = 72
TK_RESQ = 73
TK_EXTERN = 74
TK_COMMENT = 75
TK_SPECIAL = 76
TK_CMP = 77

# Constants
AVEF_MAGIC = b"AVEF"
AVEF_VERSION = 0x0100    # 16-bit
ARCH_ID_PVCPU = 0xA0A0   # 16-bit

# AVEF Header:
# Magic
# Version
# Architecture
# Entry Point
# Section Table offset
# Number of Sections
# Flags
# Memory Size
# Reserved

# AVEF Section Table Entry:
# Virtual Address
# File Offset
# Size
# Flags
# Align

HEADER_FMT = "<4sHHQQIQQ20s"   # 64 bytes
HEADER_SIZE = struct.calcsize(HEADER_FMT)

SECTION_FMT = "<32sQQQII"         # 64 bytes
SECTION_SIZE = struct.calcsize(SECTION_FMT)

# Section flags
SEC_R = 1 << 0
SEC_W = 1 << 1
SEC_X = 1 << 2
SEC_D = 1 << 3

DEFAULT_SECTIONS = {
    ".text":  {"vaddr": 0x1000, "flags": SEC_R | SEC_X,           "align": 0x10},
    ".rodata":{"vaddr": 0x1800, "flags": SEC_R,                   "align": 0x10},
    ".data":  {"vaddr": 0x2000, "flags": SEC_R | SEC_W | SEC_D,   "align": 0x08},
    ".bss":   {"vaddr": 0x2800, "flags": SEC_R | SEC_W | SEC_D,   "align": 0x08},  # zero-filled
}

# Lexer for the Assembler
class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.i = 0
        self.n = len(code)
        self.tokens: List[Tuple[int, str]] = []

    def _peek(self) -> str:
        return self.code[self.i + 1] if self.i + 1 < self.n else ""

    def _get(self) -> str:
        return self.code[self.i] if self.i < self.n else ""

    def _advance(self) -> str:
        self.i += 1
        return self._get()

    def _get_line_tail(self) -> str:
        start = self.i
        while self.i < self.n and self.code[self.i] != "\n":
            self.i += 1
        return self.code[start:self.i]

    def _string_literal(self) -> str:
        # assumes current char == '"'
        self.i += 1
        out = []
        while self.i < self.n:
            c = self.code[self.i]
            if c == '"':
                self.i += 1
                break
            out.append(c)
            self.i += 1
        return "".join(out)

    def _int_literal(self) -> str:
        start = self.i
        # support 0x..., 0b..., decimal
        if self.code.startswith("0x", self.i) or self.code.startswith("0X", self.i):
            self.i += 2
            start = self.i
            while self.i < self.n and self.code[self.i].lower() in "0123456789abcdef":
                self.i += 1
            return "0x" + self.code[start:self.i]
        if self.code.startswith("0b", self.i) or self.code.startswith("0B", self.i):
            self.i += 2
            start = self.i
            while self.i < self.n and self.code[self.i] in "01":
                self.i += 1
            return "0b" + self.code[start:self.i]
        while self.i < self.n and self.code[self.i].isdigit():
            self.i += 1
        return self.code[start:self.i]

    def _emit(self, typ: int, val: str):
        self.tokens.append((typ, val))

    def _handle_word(self):
        start = self.i
        while self.i < self.n and self.code[self.i] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._@":
            self.i += 1
        s = self.code[start:self.i]
        s_low = s.lower()
        match s_low:
            case "global":  self._emit(TK_GLOBAL, s)
            case "extern":  self._emit(TK_EXTERN, s)
            case "section": self._emit(TK_SECTION, s)
            case "push":    self._emit(TK_PUSH, s)
            case "pop":     self._emit(TK_POP, s)
            case "mov":     self._emit(TK_MOV, s)
            case "movs":    self._emit(TK_MOVS, s)
            case "stos":    self._emit(TK_STOS, s)
            case "lods":    self._emit(TK_LODS, s)
            case "add":     self._emit(TK_ADD, s)
            case "sub":     self._emit(TK_SUB, s)
            case "mul":     self._emit(TK_MUL, s)
            case "imul":    self._emit(TK_IMUL, s)
            case "div":     self._emit(TK_DIV, s)
            case "idiv":    self._emit(TK_IDIV, s)
            case "and":     self._emit(TK_AND, s)
            case "or":      self._emit(TK_OR, s)
            case "xor":     self._emit(TK_XOR, s)
            case "shl":     self._emit(TK_SHL, s)
            case "shr":     self._emit(TK_SHR, s)
            case "not":     self._emit(TK_NOT, s)
            case "rol":     self._emit(TK_ROL, s)
            case "ror":     self._emit(TK_ROR, s)
            case "cmp":     self._emit(TK_CMP, s)
            case "cmps":    self._emit(TK_CMPS, s)
            case "jmp":     self._emit(TK_JMP, s)
            case "je":      self._emit(TK_JE, s)
            case "jne":     self._emit(TK_JNE, s)
            case "jg":      self._emit(TK_JG, s)
            case "jl":      self._emit(TK_JL, s)
            case "int":     self._emit(TK_INT, s)
            case "syscall": self._emit(TK_SYSCALL, s)
            case "hlt":     self._emit(TK_HLT, s)
            case "nop":     self._emit(TK_NOP, s)
            case "db":      self._emit(TK_DB, s)
            case "dw":      self._emit(TK_DW, s)
            case "dd":      self._emit(TK_DD, s)
            case "dq":      self._emit(TK_DQ, s)
            case "resb":    self._emit(TK_RESB, s)
            case "resw":    self._emit(TK_RESW, s)
            case "resd":    self._emit(TK_RESD, s)
            case "resq":    self._emit(TK_RESQ, s)
            case "cqo":     self._emit(TK_CQO, s)
            case _:
                self._emit(TK_IDENTIFIER, s)

    def tokenize(self) -> List[Tuple[int, str]]:
        while self.i < self.n:
            c = self._get()

            if c in " \t\r":
                self.i += 1
                continue
            if c == "\n":
                self.i += 1
                continue

            if c == ";" and self._peek() == ";":  # ;;special (e.g., runlang)
                tail = self._get_line_tail()
                # strip leading ';;'
                tail = tail[2:] if tail.startswith(";;") else tail
                self._emit(TK_SPECIAL, tail.strip())
                continue
            if c == ";":  # normal comment: consume to end-of-line
                self._get_line_tail()
                continue

            if c == "+":
                self._emit(TK_PLUS, c); self.i += 1; continue
            if c == "-":
                self._emit(TK_MINUS, c); self.i += 1; continue
            if c == "*":
                self._emit(TK_ASTERIK, c); self.i += 1; continue
            if c == "/":
                self._emit(TK_FSLASH, c); self.i += 1; continue
            if c == "\\":
                self._emit(TK_BSLASH, c); self.i += 1; continue
            if c == ",":
                self._emit(TK_COMMA, c); self.i += 1; continue
            if c == "[":
                self._emit(TK_LBRACKET, c); self.i += 1; continue
            if c == "]":
                self._emit(TK_RBRACKET, c); self.i += 1; continue
            if c == "(":
                self._emit(TK_LPAR, c); self.i += 1; continue
            if c == ")":
                self._emit(TK_RPAR, c); self.i += 1; continue
            if c == ":":
                self._emit(TK_LABEL, c); self.i += 1; continue
            if c == '"':
                s = self._string_literal()
                # We’ll emit as TK_IDENTIFIER with quotes kept out—handled by data directives
                self._emit(TK_IDENTIFIER, f'"{s}"')
                continue
            if c.isdigit():
                s = self._int_literal()
                self._emit(TK_IDENTIFIER, s)
                continue
            if c.isalpha() or c in "._@":
                self._handle_word()
                continue

            asm_error(f"Unknown character '{c}' at {self.i}")
        return self.tokens

# Utils
def parse_int(val: str) -> int:
    v = val.strip().lower()
    if v.startswith("0x"):
        return int(v, 16)
    if v.startswith("0b"):
        return int(v, 2)
    if v.startswith("'") and v.endswith("'") and len(v) == 3:
        return ord(v[1])
    if v.startswith('"') and v.endswith('"'):
        asm_error("String where integer immediate expected")
    return int(v, 10)

def strip_quotes(s: str) -> str:
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    return s

def align_up(x: int, a: int) -> int:
    if a <= 1:
        return x
    return (x + (a - 1)) // a * a

# Assembler for PVCpu Arch
class PVcpuAssembler:
    def __init__(self, asm: str):
        self.asm = asm
        self.tokens = Lexer(asm).tokenize()
        self.i = 0
        self.n = len(self.tokens)

        # sections
        self.sections: Dict[str, Dict] = {}
        for name, spec in DEFAULT_SECTIONS.items():
            self.sections[name] = {
                "name": name,
                "vaddr": spec["vaddr"],
                "flags": spec["flags"],
                "align": spec["align"],
                "bytes": bytearray(),
                "size": 0,     # for BSS
            }

        self.current_section = ".text"
        self.labels: Dict[str, Dict] = {}    # name -> {"section": str, "ofs": int, "abs": int}
        self.globals: Dict[str, Dict] = {}   # exported
        self.externs: Dict[str, None] = {}
        self.entry_label: Optional[str] = None
        self.entry_point: int = 0

        self.section_data = {".text": b"", ".data": b"", ".bss": b"", ".rodata": b""}

        self.last_vaddr = 0

        self.align: int = 0x1000

    # Token Helpers
    def _peek(self, k=0) -> Tuple[int, str]:
        j = self.i + k
        if j >= self.n:
            return (-1, "")
        return self.tokens[j]

    def _advance(self) -> Tuple[int, str]:
        t = self._peek(0)
        self.i += 1
        return t

    def _expect(self, typ: int, msg: str) -> Tuple[int, str]:
        t = self._advance()
        if t[0] != typ:
            asm_error(msg + f" (got {t})")
        return t

    def _at_eof(self) -> bool:
        return self.i >= self.n

    # Parsing helpers
    def _switch_section(self, name: str):
        if name not in self.sections:
            # create ad-hoc section with text-like defaults
            self.sections[name] = {
                "name": name,
                "vaddr": 0x3000 + 0x800 * (len(self.sections) - len(DEFAULT_SECTIONS)),
                "flags": SEC_R | SEC_W | (SEC_D if name != ".text" else SEC_X),
                "align": 0x10,
                "bytes": bytearray(),
                "size": 0,
            }
        self.current_section = name

    def _emit_bytes(self, data, width:int):
        if not len(data) > width: asm_error("Internal Error, Wrong Length specified!")

        if isinstance(data, str):
            data = data.encode("utf-8")
        elif isinstance(data, bytes):
            pass
        else:
            asm_error("Internal error, Wrong Data type provided!")

        if len(data) < width: data.ljust(width, b"\x00")

        sec = self.section_data[self.current_section]
        if self.current_section == ".bss":
            sec["size"] += len(data)  # not written into file; counts allocated bytes
        else:
            sec["bytes"].extend(data)

    def _emit_imm_le(self, value: int, width: int):
        self._emit_bytes(int(value).to_bytes(width, "little", signed=False), width)

    def _mklabel(self, name:str, section:str, global_:bool, import_:bool) -> None:
        # check if it exists
        label = self.labels.get(name, None)
        if label: asm_error(f"Label: {name} is defined previously!")

        label[name] = {
            "section": section,
            "global_": global_,
            "import_": import_
        }

    def _add_data_var(self, name:str, value:str, width:int) -> None:
        self.section_data[".data"] += name.encode("utf-8").ljust(64, b"\x00")
        w = b"\x00"
        if width == TK_DB:
            w = 0x8.to_bytes(2, "little")
        elif width == TK_DW:
            w = 0x16.to_bytes(2, "little")
        elif width == TK_DD:
            w = 0x32.to_bytes(2, "little")
        elif width == TK_DQ:
            w = 0x64.to_bytes(2, "little")
        else: asm_error("Unknown Data Width: ", width)

        self.section_data[".data"] += w
        self.section_data[".data"] += value.encode("utf-8").ljust(128, "\x00")

    def _emit_inst(self, inst:int, dest:int, src:int, imm:int) -> None:
        self._emit_imm_le(inst, 2)
        self._emit_imm_le(src, 4)
        self._emit_imm_le(dest, 4)
        self._emit_imm_le(imm, 8)

    # Assembler singlular instructions
    def assemble_inst(self, inst:tuple[int, str]) -> None:
        current_sec = ".text"
        vaddr = self.last_vaddr + 1

        typ = inst[0]
        val = inst[1]

        if typ == TK_SECTION:
            sec = self._expect(TK_IDENTIFIER, "Expected Section Name,")[1]
            current_sec = sec
            self.current_section = sec
            self.sections[sec] = {
                "vaddr": align_up(vaddr, self.align),
                "align": self.align,
                "flags": 0x0
            }
            self.last_vaddr = align_up(vaddr, self.align)
        elif typ == TK_GLOBAL:
            name = self._expect(TK_IDENTIFIER, "Expected Label name,")[1]
            self.entry_label = name
            self._mklabel(name, current_sec, True, False)
        elif typ == TK_EXTERN:
            name = self._expect(TK_IDENTIFIER, "Expected Label name,")[1]
            self._mklabel(name, current_sec, False, True)
        elif typ == TK_IDENTIFIER:
            nxt = self._advance()
            if nxt[0] == TK_LABEL:
                # Label
                self._mklabel(val, current_sec, False, False)
            elif nxt[0] in [TK_DB, TK_DW, TK_DD, TK_DQ]:
                if not current_sec == ".data":
                    asm_error("Tried to define data outside of the .data section!")
                value = self._advance()

                if not value[0] in [TK_IDENTIFIER]:
                    asm_error("Unknown Assignment value: ", value[1])

                self._add_data_var(val, value[1], nxt[0])
            else: asm_error("Unknown Instruction: ", val)
        elif typ == TK_MOV:
            reg = self._expect(TK_IDENTIFIER, "Expected register name,")
            self._advance()
            reg2 = self._expect(TK_IDENTIFIER, "Expected register name,")
            self._emit_inst(MOV, REGS[reg[1].lower()], REGS[reg2[1].lower()], 0)
        elif typ == TK_PUSH:
            reg = self._expect(TK_IDENTIFIER, "Expected register name,")
            self._emit_inst(PUSHI, 0, REGS[reg[1].lower()], 0)
        elif typ == TK_POP:
            reg = self._expect(TK_IDENTIFIER, "Expected register name,")
            self._emit_inst(POPG, REGS[reg[1].lower()], 0, 0)

    # Write AVEF
    def build_avef(self) -> bytes:
        # Assign file offsets after header + section table
        # Sections order: text, rodata, data, bss  (bss has size but no file bytes)
        ordered = [".text", ".rodata", ".data", ".bss"] + \
                  [s for s in self.sections.keys() if s not in (".text", ".rodata", ".data", ".bss")]

        sections_out: List[Tuple[int,int,int,int,int]] = []  # vaddr, file_off, size, flags, align
        blob = bytearray()

        # compute section table offset and start of data
        sec_count = len(ordered)
        sec_table_off = HEADER_SIZE
        cur_off = sec_table_off + sec_count * SECTION_SIZE

        # append each section’s bytes (except .bss)
        body_chunks: List[Tuple[int, bytes]] = []  # (pad, data)

        for name in ordered:
            sec = self.sections[name]
            vaddr = sec["vaddr"]
            flags = sec["flags"]
            align = sec["align"]

            # decide size and file offset
            if name == ".bss":
                size = sec["size"]
                file_off = 0  # no file content
                sections_out.append((name.encode("utf-8"), vaddr, file_off, size, flags, align))
                continue

            # align file offset
            pad = (-cur_off) % (align or 1)
            cur_off += pad

            data = bytes(sec["bytes"])
            size = len(data)

            file_off = cur_off
            sections_out.append((name.encode("utf-8"), vaddr, file_off, size, flags, align))
            body_chunks.append((pad, data))
            cur_off += size

        # compute mem size (round up to page)
        max_needed = 0
        for (sec, vaddr, file_off, size, flags, align) in sections_out:
            max_needed = max(max_needed, vaddr + size)
        mem_size = align_up(max_needed, 0x1000)

        # entry point
        entry = self.entry_point or self.sections[".text"]["vaddr"]

        # header
        header = struct.pack(
            HEADER_FMT,
            AVEF_MAGIC,
            AVEF_VERSION,
            ARCH_ID_PVCPU,
            entry,
            sec_table_off,
            sec_count,
            0,          # flags
            mem_size,
            b"\x00" * 20
        )

        # section table bytes
        sec_table = bytearray()
        for (name, vaddr, file_off, size, flags, align) in sections_out:
            sec_table.extend(struct.pack(SECTION_FMT, name, vaddr, file_off, size, flags, align))

        # compose final image
        out = bytearray()
        out.extend(header)
        out.extend(sec_table)

        for pad, data in body_chunks:
            if pad:
                out.extend(b"\x00" * pad)
            out.extend(data)

        return bytes(out)

    # Special Function to load .avef into memory
    def load_into_memory(self, memory_obj:PHWMemory):
        avef = self.build_avef()
        # parse header quickly
        if len(avef) < HEADER_SIZE:
            asm_error("AVEF too small")
        magic, ver, arch, entry, sec_off, sec_cnt, flags, mem_size, _ = struct.unpack(
            HEADER_FMT, avef[:HEADER_SIZE]
        )
        if magic != AVEF_MAGIC:
            asm_error("Bad AVEF magic")
        # emit sections into memory
        for i in range(sec_cnt):
            off = sec_off + i * SECTION_SIZE
            vaddr, file_off, size, sflags, align = struct.unpack(SECTION_FMT, avef[off:off+SECTION_SIZE])
            if size == 0:
                # BSS → zero-fill (skip if memory API lacks write)
                if hasattr(memory_obj, "write"):
                    memory_obj.write_ram(vaddr, b"\x00" * 0)
                continue
            chunk = avef[file_off:file_off+size]
            write_fn = getattr(memory_obj, "write", None) or getattr(memory_obj, "write_bytes", None)
            if not callable(write_fn):
                asm_error("Memory object lacks write(addr, bytes) or write_bytes(addr, bytes)")
            write_fn(vaddr, chunk)
        return entry