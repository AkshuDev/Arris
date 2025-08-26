# [opcode:u8][a:u32][b:u32][c:u32] Instruction format

# Core
HALT = 0
MOV = 71
LEA = 72
MOVN = 73

CQO = 74

# Stack Data Movement
PUSHK = 1
PUSHI = 2
PUSHB = 3
PUSHG = 4
POPG = 5
LOADL = 6
STOREL = 7

# Arithmetic / Logic
ADD = 10
SUB = 11
MUL = 12
DIV = 13

# Jumping and more
JMP = 20
JMPT = 21
JMPF = 22

# Calling and more
CALL = 30
RET = 31

# Comparison
CMP_EQ = 40
CMP_NE = 41
CMP_LT = 42
CMP_GT = 43
CMP_LE = 44
CMP_GE = 45

# Host interop for RunLang
HOST = 60

SPECIAL_INST = 70

INSTSET = [HALT, PUSHK, PUSHI, PUSHB, PUSHG, POPG, LOADL, STOREL, ADD, SUB, MUL, DIV, JMP, JMPT, JMPF, CALL, RET, CMP_EQ, CMP_NE, CMP_LT, CMP_LE, CMP_GT, CMP_GE, HOST, SPECIAL_INST]

# Registers
G0 = 62 # Cannot use 0 as it is reserved for NO VALUE
G1 = 1
G2 = 2
G3 = 3
G4 = 4
G5 = 5
G6 = 6
G7 = 7
G8 = 8
G9 = 9
G10 = 10
G12 = 12
G13 = 13
G14 = 65
WG0 = 17
WG1 = 18
WG2 = 19
WG3 = 20
WG4 = 21
WG5 = 22
WG6 = 23
WG7 = 24
WG8 = 25
WG9 = 26
WG10 = 27
WG12 = 28
WG13 = 29
WG14 = 64
DG0 = 30
DG1 = 31
DG2 = 32
DG3 = 33
DG4 = 34
DG5 = 35
DG6 = 36
DG7 = 37
DG8 = 38
DG9 = 39
DG10 = 40
DG12 = 41
DG13 = 42
DG14 = 63
QG0 = 43
QG1 = 44
QG2 = 45
QG3 = 46
QG4 = 47
QG5 = 48
QG6 = 49
QG7 = 50
QG8 = 51
QG9 = 52
QG10 = 53
QG12 = 54
QG13 = 55
QG14 = 62
SP = 15
SF = 16
WSP = 56
WSF = 57
DSP = 58
DSF = 59
QSP = 60
QSF = 61

REGS = {
    "g0": G0,
    "g1": G1,
    "g2": G2,
    "g3": G3,
    "g4": G4,
    "g5": G5,
    "g6": G6,
    "g7": G7,
    "g8": G8,
    "g9": G9,
    "g10": G10,
    "g12": G12,
    "g13": G13,
    "g14": G14,
    "sp": SP,
    "sf": SF,
    "bg0": G0,
    "bg1": G1,
    "bg2": G2,
    "bg3": G3,
    "bg4": G4,
    "bg5": G5,
    "bg6": G6,
    "bg7": G7,
    "bg8": G8,
    "bg9": G9,
    "bg10": G10,
    "bg12": G12,
    "bg13": G13,
    "bg14": G14,
    "bsp": SP,
    "bsf": SF,
    "wg0": WG0,
    "wg1": WG1,
    "wg2": WG2,
    "wg3": WG3,
    "wg4": WG4,
    "wg5": WG5,
    "wg6": WG6,
    "wg7": WG7,
    "wg8": WG8,
    "wg9": WG9,
    "wg10": WG10,
    "wg12": WG12,
    "wg13": WG13,
    "wg14": WG14,
    "wsp": WSP,
    "wsf": WSF,
    "dg0": DG0,
    "dg1": DG1,
    "dg2": DG2,
    "dg3": DG3,
    "dg4": DG4,
    "dg5": DG5,
    "dg6": DG6,
    "dg7": DG7,
    "dg8": DG8,
    "dg9": DG9,
    "dg10": DG10,
    "dg12": DG12,
    "dg13": DG13,
    "dg14": DG14,
    "dsp": DSP,
    "dsf": DSF,
    "qg0": QG0,
    "qg1": QG1,
    "qg2": QG2,
    "qg3": QG3,
    "qg4": QG4,
    "qg5": QG5,
    "qg6": QG6,
    "qg7": QG7,
    "qg8": QG8,
    "qg9": QG9,
    "qg10": QG10,
    "qg12": QG12,
    "qg13": QG13,
    "qg14": QG14,
    "qsp": QSP,
    "qsf": QSF,
}