# Arris
import os
import sys

import helpers
import lexer
import parser

memory:bytearray = None
file_:str = None
code:str = None
debug:bool = False
compile_:bool = False
memsize:int = 512
onlylex:bool = False

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
            elif v == "-memory" and ((i + 1) < len(sys.argv)):
                memsize = helpers.ToInt(sys.argv[i + 1])
            elif v == "-onlylex":
                onlylex = True
            else:
                file_ = v

        if onlylex:
            if debug: print("Getting Code...")
            with open(file_, "r") as f:
                f.seek(0)
                code = f.read()
            
            if debug: print("Got Code!\nRunning lexer...")
            lex = lexer.Lexer(code)
            print("Tokens:\n", lex.tokenize())
            exit(0)

        if debug: print("Creating memory space of size:", memsize)
        memory = bytearray(memsize)
        
        if debug: print("Getting code...")
        with open(file_, "r") as f:
            f.seek(0)
            code = f.read()
        
        if debug: print("Got Code!\nRunning Lexer")
        lex = lexer.Lexer(code)
        tokens = lex.tokenize()
        
        parser_ = parser.Parser(memory, memsize, tokens, os.path.dirname(file_))
        parser_.parse()