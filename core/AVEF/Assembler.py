import os
import sys

from instructionSet import *

from phardwareitk.Memory.Memory import *

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# This is a modified assembler of my PVCpu Project (yeah i made it from scratch instead of copying)

AVEF_MAGIC = "AVEF"
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
        self.labels = {}
        self.fixups = []

    def mk_headers(self) -> str:
        pass