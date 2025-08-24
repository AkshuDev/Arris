import struct
import os
import sys

from instructionSet import *

from phardwareitk.Memory.Memory import *

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import errorHandler

# This is a modified assembler of my PVCpu Project (yeah i made it from scratch instead of copying)

AVEF_MAGIC = b"AVEF"
AVEF_VERSION = 1 # 1.0

X86_64_REG_MAP = {
    "qg0": "rax",
    "qg1": "rbx",
    "qg2": "rcx",
    "qg3": "rdx",
    "qg4": "rdi",
    "qg5": "rsi",
    "qg6": "r8",
    "qg7": "r9",
    "qg8": "r10",
    "qg9": "r11",
    "qg10": "r12",
    "qg11": "r13",
    "qg12": "r14",
    "qg13": "r15",
    "dg0": "eax",
    "dg1": "ebx",
    "dg2": "ecx",
    "dg3": "edx",
    "dg4": "edi",
    "dg5": "esi",
    "wg0": "ax",
    "wg1": "bx",
    "wg2": "cx",
    "wg3": "dx",
    "wg4": "di",
    "wg5": "si",
    "qsp": "rsp",
    "dsp": "esp",
    "wsp": "sp",
    "qsf": "rbp",
    "dsf": "ebp",
    "wsf": "bp"
}

# AVEF format -

# AVEF header
# Section Table
# Code sections
# Data sections
# BSS sections
# Reloaction Table
# Symbol Table

# AVEF Header (64 bytes)

# char magic[4]
# uint16 version
# uint16 ArchId
# uint64 EntryPoint
# uint64 SectionTableOff
# uint32 SectionCount
# uint64 Flags
# uint64 Memory size
# char Reserved[20]

# Section Table (32 bytes each)

# uint64 VirtualAddr
# uint64 FileOffset
# uint64 Size
# uint32 Flags (X=exec W=write R=read D=data)
# uint32 Align

# Required Sections -> .text .data .bss .rodata

class PVcpu():
    def __init__(self, asm:str, mem:Memory):
        self.asm = asm
        self.mem = mem
        self.ram = mem.ram
        self.code = bytearray()

        self.labels = {}
        self.fixups = []

        self.sections = {}
        self.section_count = 0
        self.section_table_offset = 65 # Starts at byte 65
        self.flags = 0x0
        self.entry_point = 0x0 # NULL

    def mk_headers(self) -> bytearray:
        header = bytearray()
        header.extend(AVEF_MAGIC)
        header.extend(struct.pack("<B", AVEF_VERSION))
        header.extend(struct.pack("<I", 0xA0A0)) # 0xA0A0 = PVCpu
        header.extend(struct.pack("<QQIQQs20", self.entry_point, self.section_table_offset, self.section_count, self.flags, self.mem.size, "\0"*20))
        return header
    
    def assemble(self) -> None:
        lines = self.asm.splitlines()
        for line in lines:
            self.assemble_line(line.strip())
        
        # Resolve fixups
        for pos, label in self.fixups:
            if label not in self.labels:
                errorHandler.assemblerError(f"Unresolved Label: {label}")
            struct.pack_into("<I", self.code, pos, self.labels[label])

        self.section_count = len(self.sections.keys())

        header = self.mk_headers()
        self.mem.write_ram(header, 0, 64)

    def assemble_line(self, line:str) -> None:
        if ";;@" in line:
            line = line.split(";;@")[0].strip()
        elif ";;" in line:
            line = line.split(";;")[0].strip()

        if not line:
            return
        
        parts = line.split()
        instr = parts[0]

        # Handle labels
        if instr.endswith(":"):
            self.labels[instr[:-1]] = len(self.code)
            return
        
        if instr not in INSTSET:
            errorHandler.assemblerError(f"Unknown Instruction: {instr}")