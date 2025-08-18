mem = bytearray(512)
FUNCS:dict = {}

def setMem(mem_:bytearray) -> None:
    global mem
    mem = mem_

def getMem() -> bytearray:
    global mem
    return mem

def mov(currentOffset:int) -> int:
    """Move 1 byte forward"""
    currentOffset += 1
    return currentOffset

def movn(currentOffset:int, n:int) -> int:
    """Move n bytes forward"""
    currentOffset += n
    return currentOffset

def movb(currentOffset:int) -> int:
    """Move 1 byte backwards"""
    currentOffset -= 1
    return currentOffset

def movbn(currentOffset:int, n:int) -> int:
    """Move n bytes backwards"""
    currentOffset -= n
    return currentOffset

def set(currentOffset:int, val:int) -> int:
    """Set Current offset to a value"""
    currentOffset = val
    return val

def clr(currentOffset:int) -> None:
    """Clears current cell"""
    memory = getMem()

    memory[currentOffset] = int(0).to_bytes(1, "little")

def run(lang:str, code:str) -> None:
    """Runs code of another language"""
    if lang == "python" or lang == "py":
        exec(code)
    else:
        return

def include(code:str, file:str) -> None:
    """Includes another file"""
    with open(file, "r") as f:
        code += "\n" + f.read()
    
def addFunc(funcType:str, funcName:str, funcParams:list[tuple]) -> None:
    pass