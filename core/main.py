# Arris
import os
import sys

import insts

data = ""
offset = [0]
memory = bytearray(512)
memoffset = 0

if (len(sys.argv) > 2):
    memory = bytearray(int(sys.argv[2]))

with open(sys.argv[1], "r") as f:
    data = f.read()

lineNo = 0
lines = data.splitlines(True)

insts.setMem(memory)
insts.setCode(data)

skip = 0

if (len(sys.argv) < 2):
    print("Usage: [program] <file>")

def getInst(line:str, curOff:list) -> str:
    char = ""
    res = ""

    while True:
        if (char == "|" or char == "\n") or curOff[0] >= len(line):
            break
        char = line[curOff[0]]
        res += char
        curOff[0] += 1
    
    return res[:-1]

def parseInst(inst:str, nextInst:str, curMemOff:int) -> int:
    if inst == "mov":
        insts.mov(curMemOff)
    elif inst == "movn":
        insts.movn(curMemOff, int(nextInst))
        return 1
    elif inst == "movb":
        insts.movb(curMemOff)
    elif inst == "movbn":
        insts.movbn(curMemOff, int(nextInst))
        return 1
    elif inst == "set":
        insts.set(curMemOff, int(nextInst))
        return 1
    elif inst == "clr":
        insts.clr(curMemOff)
    elif inst == "__py:":
        insts.run("python", nextInst)
        return 1
    elif inst == "@inc":
        insts.include(nextInst)
        return 1
    elif inst == "fnc":
        pass
    elif inst.startswith("##"):
        pass
    elif inst == "":
        pass
    else:
        raise ValueError("Unknown Instruction:", inst)
    
    return 0

if __name__ == "__main__":
    while True:
        line = lines[lineNo]
        inst = getInst(line, offset)
        Ninst = ""

        if offset[0] >= len(line) - 1:
            if len(lines) - 1 > lineNo:
                Ninst = getInst(lines[lineNo + 1], [0])
            else:
                break
        else:
            offset[0] = len(inst) + offset[0]
            Ninst = getInst(line, offset)

        if skip == 0:
            skip = parseInst(inst, Ninst, memoffset)
        else:
            skip -= 1

        lineNo += 1