# [opcode:u8][a:u32][b:u32][c:u32] Instruction format

# Core
HALT = 0

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
G0 = 0
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
G14 = 14
SP = 15
SF = 16