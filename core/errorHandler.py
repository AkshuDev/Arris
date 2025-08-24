def error(msg:str, code:int=2) -> None: # 1 is used by main.py
    print("[Error]\n\t"+msg+"\n\tExiting...")
    exit(code)

def printBacktrace(bt:list) -> None:
    for v in bt:
        print("At:", v)

def compilerError(msg:str, code:int=2) -> None:
    out = f"[Error during compiling]:\n\t{msg}\nExiting..."
    print(out)
    exit(code)

def assemblerError(msg:str, code:int=3) -> None:
    out = f"[Error during Assembling]:\n\t{msg}\nExiting..."
    print(out)
    exit(code)