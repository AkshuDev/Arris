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

def clr(currentOffset:int, memory:bytearray) -> None:
    memory[currentOffset] = int(0).to_bytes(1, "little")

def run(lang:str, code:str) -> None:
    if lang == "python" or lang == "py":
        exec(code)
    else:
        return

def include(code:str, file:str) -> None:
    with open(file, "r") as f:
        code += "\n" + f.read()
    
