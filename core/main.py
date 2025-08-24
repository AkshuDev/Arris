# Arris
import os
import sys

import helpers
import lexer
import parser
import compiler

from phardwareitk.Memory import Memory # My Own but it has something very important MEMORY!

file_:str = None
code:str = None
debug:bool = False
compile_:bool = False
memsize:int = 512
memory:Memory.Memory = None
onlylex:bool = False
lexout:bool = False
parseout:bool = False
files:list = []
compileMode:int = 64
compileOut:str = ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: [PROGRAM] <input file> [-<OPTIONS>]")
        exit(1)
    else:
        for i, v in enumerate(sys.argv):
            if i == 0:
                continue

            if v == "-debug":
                debug = True
            elif v == "-compile":
                compile_ = True
            elif "--memory" in v and len(v.split("=")) > 1:
                memsize = helpers.ToInt(v.split("=")[1])
            elif v == "-onlylex":
                onlylex = True
            elif v == "-lexout":
                lexout = True
            elif v == "-parseout":
                parseout = True
            elif v == "--bits" and len(v.split("=")) > 1:
                compileMode = helpers.ToInt(v.split("=")[1])
            elif "--compile-out" in v and len(v.split("=")) > 1:
                compileOut = v.split("=")[1]
            else:
                file_ = v
                files.append(file_)

        if len(files) == 0:
            print("Usage: [PROGRAM] <input_files> [-<OPTIONS>]")
            exit(1)

        if onlylex:
            if debug: print("Getting Code...")
            with open(files[0], "r") as f:
                f.seek(0)
                code = f.read()
            
            if debug: print("Got Code!\nRunning lexer...")
            lex = lexer.Lexer(code)
            print("Tokens:\n", lex.tokenize())
            exit(0)

        if debug: print("Creating memory space of size:", memsize, "bytes")
        memory = Memory.Memory(memsize, 0, None, debug, 0) # No system size with no memory blocks and no process size. Just enough size for our program
        # We can use the Process class for full Virtual Process style but I would like to make this one custom.
        
        if debug: print("Getting code...")
        with open(files[0], "r") as f:
            f.seek(0)
            code = f.read()
        
        if debug: print("Got Code!\nRunning Lexer")
        lex = lexer.Lexer(code)
        tokens = lex.tokenize()
        if debug: "Lexer Finished!"

        if lexout: print(tokens, "\n")
        
        if debug: print("Running Parser...")
        parser_ = parser.Parser(tokens)
        stmts = parser_.parse()
        if debug: print("Parser Finished!")

        if (parseout): print(stmts, "\n")

        if debug: print("Running Compiler...")
        compiler_ = compiler.ArrisCompiler64(stmts)
        
        #if compileMode == 64:
            #compiler_ = compiler.ArrisCompiler64(stmts)
        #elif compileMode == 32:
            #compiler_ = compiler.ArrisCompiler32(stmts)
        #elif compileMode == 16:
            #compiler_ = compiler.ArrisCompiler16(stmts)
        #elif compileMode == 8:
            #compiler_ = compiler.ArrisCompiler8(stmts)
        
        compiled = compiler_.compile()
        if debug: print("Compiler Finished!")
        if not compileOut == "" and not compileOut == "stdout":
            with open(compileOut, "w") as f:
                f.write(compiled)
        elif not compileOut == "" and compileOut == "stdout":
            print(f"\nCompiled to Assembly:\n\n{compiled}")

        if compileOut:
            exit(0)