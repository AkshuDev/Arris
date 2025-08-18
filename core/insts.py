def mov(currentOffset:int) -> int:
    """Move 1 byte forward"""
    return currentOffset + 1

def movn(currentOffset:int, n:int) -> int:
    """Move n bytes forward"""
    return currentOffset + n

def movb(currentOffset:int) -> int:
    """Move 1 byte backwards"""
    return currentOffset - 1

def movbn(currentOffset:int, n:int) -> int:
    """Move n bytes backwards"""
    return currentOffset - n

