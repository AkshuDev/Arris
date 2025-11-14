import sys
# Specially designed for lsp
def error(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    raise RuntimeError(f"Error in file:<{file if file else "unknown"}> at line:<{line if line else 0}> char: <{col if col else 0}>:\n\t{" ".join(args)}")

def parser_error(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    raise RuntimeError(f"Parser Error in file:<{file if file else "unknown"}> at line:<{line if line else 0}> char: <{col if col else 0}>:\n\t{" ".join(args)}")


def printBacktrace(bt:list) -> None:
    for v in bt:
        print("At:", v)

def compilerError(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    raise RuntimeError(f"Compiler Error in file:<{file if file else "unknown"}> at line:<{line if line else 0}> char: <{col if col else 0}>:\n\t{" ".join(args)}")


def assemblerError(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    raise RuntimeError(f"Assembler Error in file:<{file if file else "unknown"}> at line:<{line if line else 0}> char: <{col if col else 0}>:\n\t{" ".join(args)}")