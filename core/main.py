# Arris
import os
import sys

import insts

if (len(sys.argv) < 2):
    print("Usage: [program] <file>")

def getInst(line:str, curOff:int) -> str:
    char = ""
    res = ""

    while not char == "|":
        char = line[curOff]
        if char == "|":
            break
        res += char
    
    return res

def parseInst(inst:str, nextInst:str, curMemOff:int, mem:bytearray, code:str) -> None:
    if inst == "mov":
        insts.mov(curMemOff)
    elif inst == "movn":
        insts.movn(curMemOff, int(nextInst))
    elif inst == "movb":
        insts.movb(curMemOff)
    elif inst == "movbn":
        insts.movbn(curMemOff, int(nextInst))
    elif inst == "set":
        insts.set(curMemOff, int(nextInst))
    elif inst == "clr":
        insts.clr(curMemOff, mem)
    elif inst == "__py:":
        insts.run("python", nextInst)
    elif inst == "@inc":
        insts.include(code, nextInst)
    else:
        raise ValueError("Unknown Instruction:", inst)

if __name__ == "__main__":
    data = ""
    offset = 0
    memory = bytearray(512)
    memoffset = 0

    if (len(sys.argv) > 2):
        memory = bytearray(int(sys.argv[2]))
    
    with open(sys.argv[1], "r") as f:
        data = f.read()

    lineNo = 0
    lines = data.splitlines()

    while True:
        line = lines[lineNo]
        inst = getInst(line, offset)
        Ninst = getInst(line, offset + len(inst) + 1)

        parseInst(inst, Ninst, memoffset, memory, data)