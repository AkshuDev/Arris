# Arris
import os
import sys

import helpers
import lexer
import parser
import compiler

from AVEF import Assembler, instructionSet

file_:str = ""
code:str = ""
debug:bool = False
compile_:bool = False
memsize:int = 1024 * 1024 # 1MB
onlylex:bool = False
lexout:bool = False
parseout:bool = False
exitAfterParsing:bool = False
files:list = []
compileMode:int = 64
compileOut:str = ""
exitAfterCompile:bool = False
asmOut:str = ""
exitAfterAssembling:bool = False
disassemble:bool = False
assembled_output_dir_def:str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp")
assembled_output_def:str = os.path.join(assembled_output_dir_def, "aout.avef")

better_dump = False

avm_dir_path:str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AVM")
avm_bin_path:str = os.path.join(avm_dir_path, "avm_bin")
avm_path:str = os.path.join(avm_bin_path, "avm")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: [PROGRAM] <input file> [-<OPTIONS>]")
        exit(1)
    else:
        for i, v in enumerate(sys.argv):
            if i == 0:
                continue

            if v == "--debug":
                debug = True
            elif v == "--compile":
                compile_ = True
            elif "--memory" in v and len(v.split("=")) > 1:
                memsize = helpers.ToInt(v.split("=")[1])
            elif v == "--exit-alex":
                onlylex = True
            elif v == "--lex-out":
                lexout = True
            elif v == "--parse-out":
                parseout = True
            elif v == "--bits" and len(v.split("=")) > 1:
                compileMode = helpers.ToInt(v.split("=")[1])
            elif "--compiled-out" in v and len(v.split("=")) > 1:
                compileOut = v.split("=")[1]
            elif "--assembled-out" in v and len(v.split("=")) > 1:
                asmOut = v.split("=")[1]
            elif v == "--disassemble":
                disassemble = True
            elif v == "--better-dump":
                better_dump = True
            elif v == "-dump-avef" or v == "-avef-dump":
                from AVEF import dumper
                
                d = b""
                with open(files[0], "rb") as f:
                    d = f.read()
                better = True if better_dump and disassemble else False
                dumper.dump_avef(d, better, decoder=dumper.pvcpu_avef_decoder)
                exit(0)
            elif v == "--exit-acompile": # Exit after compile
                exitAfterCompile = True
            elif v == "--exit-aassemble": # Exit after Assemble
                exitAfterAssembling = True
            elif v == "--exit-aparse": # Exit after Parse
                exitAfterParsing = True
            else:
                file_ = v
                if not os.path.exists(file_):
                    print("File [%s] does not exist!", file_)
                files.append(file_)
                
        if debug: print("MEMSIZE:", memsize, "bytes")

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
        if (exitAfterParsing): exit(0)

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
        elif compileOut == "stdout":
            print(f"\nCompiled to Assembly:\n\n{compiled}")
        
        if (exitAfterCompile): exit(0)

        if debug: print("Running Assembler (PVCpu Architecture)...")
        assembler = Assembler.PVcpuAssembler(compiled)
        assembled = assembler.assemble()
        if debug: print("Assembled Code!")
        if asmOut:
            if asmOut == "stdout":
                print(assembled.hex(" "))
            else:
                with open(asmOut, "wb") as f:
                    f.write(assembled)
        
        if (exitAfterAssembling): exit(0)
        
        if debug: print("Running AVM (Arris Virtual Machine)...")
        if not os.path.exists(avm_path):
            print("AVM doesn't exist trying, checking for Makefile...")
            if not os.path.exists(os.path.join(avm_dir_path, "Makefile")):
                print("No Makefile found, please install AVM from github repository (https://github.com/AkshuDev/Arris)")
                exit(1)
            ret = os.system(f"make -C \"{avm_dir_path}\"")
            if not ret == 0:
                print("Makefile Failed!, please install AVM from github repository (https://github.com/AkshuDev/Arris)")
                exit(1)
            if not os.path.exists(avm_path): 
                print("Failed to make AVM, please install AVM from github repository (https://github.com/AkshuDev/Arris)")
        
        memprovided = str(memsize)
        debugprovided = ""
        if debug: debugprovided = "-debug"
        
        if asmOut == "":
            os.mkdir(assembled_output_dir_def)
            with open(assembled_output_def, "wb") as f:
                f.write(assembled)
            
            if debug: print("Command:", f"{avm_path} {assembled_output_def} -memsize {memprovided} {debugprovided}")
        
            os.system(f"{avm_path} {assembled_output_def} -memsize {memprovided} {debugprovided}")
            os.remove(assembled_output_def)
            os.rmdir(assembled_output_dir_def)
        else:
            if debug: print("Command:", f"{avm_path} {asmOut} -memsize {memprovided} {debugprovided}")
            os.system(f"{avm_path} {asmOut} -memsize {memprovided} {debugprovided}")
            
        if debug: print("Finished Running AVM!")
            
        exit(0)
