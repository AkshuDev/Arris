import os
import sys
import platform
import argparse
import subprocess

from . import lexer
from . import parser
from . import compiler

TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp")
DEFAULT_COMPILED = os.path.join(TEMP_DIR, "aout.asm")
DEFAULT_ASSEMBLED = os.path.join(TEMP_DIR, "aout.o")
DEFAULT_BINARY = os.path.join(TEMP_DIR, "a.out")

SUPPORTED_ARCHS = ["x86_64"]
SUPPORTED_BITS = ["64"]

def init():
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)

def read_file(path: str) -> str:
    if not os.path.exists(path):
        sys.exit(f"Error: file '{path}' not found.")
    with open(path, "r") as f:
        return f.read()


def write_file(path: str, data, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    with open(path, mode) as f:
        f.write(data)


def debug_print(debug, *args):
    if debug:
        print("[DEBUG]", *args)


def run_lexer(code: str, debug=False, file=None):
    debug_print(debug, "Running lexer...")
    lex = lexer.Lexer(code, filename=file)
    tokens = lex.tokenize()
    debug_print(debug, f"Lexing complete. Tokens: {len(tokens)}")
    return tokens


def run_parser(tokens, code, include_runlang=True, arch="x86_64", bits=64, os_="linux", debug=False, file=None):
    debug_print(debug, "Running parser...")
    p = parser.Parser(tokens, code=code, include_runlang=include_runlang, architecture=arch, bits=bits, os_=os_, file=file)
    stmts = p.parse()
    debug_print(debug, "Parsing complete.")
    return stmts


def run_compiler(stmts, arch, os_name, code, debug=False, file=None, inc_stdlib=True, entry=None):
    debug_print(debug, f"Compiling for architecture '{arch}'...")
    if arch == "x86_64":
        c = compiler.x86_64Compiler(stmts, code=code, os=os_name, file=file, add_stdlib=inc_stdlib, entry=entry)
    else:
        sys.exit(f"Unknown architecture: {arch}")
    compiled = c.compile()
    debug_print(debug, "Compilation complete.")
    return compiled


def assemble_and_link(infile, asmOut, outfile, os_name, debug=False, asm_assembler="nasm", debug_asm=False, entry=compiler._START):
    debug_print(debug, "Assembling and linking...")
    obj_file = DEFAULT_ASSEMBLED if not asmOut else asmOut

    if not shutil.which(asm_assembler):
        sys.exit(f"'{asm_assembler}' not found in the system, please install '{asm_assembler}'!")
    
    if not shutil.which("ld"):
        sys.exit("'ld' not found in the system, please install 'ld'!")

    try:
        if asm_assembler == "as":
            if not debug_asm:
                subprocess.run(["as", infile, "-o", obj_file], check=True)
            else:
                subprocess.run(["as", infile, "-o", obj_file, "-g"], check=True)
        elif asm_assembler == "nasm":
            fmt = "elf64" if os_name != "windows" else "win64"
            if not debug_asm:
                subprocess.run(["nasm", "-f", fmt, infile, "-o", obj_file], check=True)
            else:
                subprocess.run(["nasm", "-f", fmt, infile, "-o", obj_file, "-g"], check=True)
        else:
            sys.exit(f"Sorry '{asm_assembler}' is unsupported! Please assemble it manually.")

        if not debug_asm:
            subprocess.run(["ld", obj_file, "-o", outfile, "-e", entry], check=True)
        else:
            subprocess.run(["ld", obj_file, "-o", outfile, "-e", entry, "-g"], check=True)
        debug_print(debug, f"Linked binary written to {outfile}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Assembly or linking failed: {e}")
    finally:
        if os.path.exists(DEFAULT_ASSEMBLED):
            os.remove(DEFAULT_ASSEMBLED)


def main():
    parser_ = argparse.ArgumentParser(description="Arris Build & Run Tool")
    parser_.add_argument("input", help="Input source file")
    parser_.add_argument("-o", help="Output path", required=False, metavar=("--output"))
    parser_.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser_.add_argument("--compile", action="store_true", help="Compile to assembly only")
    parser_.add_argument("-b", type=int, default=64, help=f"Bit mode ({', '.join(SUPPORTED_BITS)})", metavar="--bits")
    parser_.add_argument("-cout", default="", help="Output path for compiled code", metavar=("--compiled-out"))
    parser_.add_argument("-aout", default="", help="Output path for assembled binary", metavar=("--assembled-out"))
    parser_.add_argument("-arch", default="x86_64", help=f"Target architecture ({', '.join(SUPPORTED_ARCHS)})", metavar=("--architecture"))
    parser_.add_argument("-os", default=platform.system().lower(), help="Target OS platform", metavar=("--platform"))
    parser_.add_argument("--no-runlang", action="store_true", help="Disable runlang inclusion")
    parser_.add_argument("--only-lex", action="store_true", help="Run lexer only and exit")
    parser_.add_argument("--only-parse", action="store_true", help="Run parser only and exit")
    parser_.add_argument("--exit-after-compile", action="store_true", help="Exit after compile step")
    parser_.add_argument("--exit-after-assemble", action="store_true", help="Exit after assemble step")
    parser_.add_argument("--debug-output", action="store_true", help="Export symbol table into the output file")
    parser_.add_argument("--no-inject-runtime", action="store_true", help="Do not inject runtime helpers such as __arris__compilerinjected__main")
    parser_.add_argument("-e", help="Change default entry function", default="main", metavar=("--entry"))

    args = parser_.parse_args()
    debug = args.debug
    code = read_file(args.input)

    init()

    tokens = run_lexer(code, debug, args.input)
    if args.only_lex:
        print(tokens)
        return

    stmts = run_parser(tokens, code, not args.no_runlang, args.arch, args.b, args.os, debug, args.input)
    if args.only_parse:
        print(stmts)
        return

    entry = None if not args.e else args.e

    compiled = run_compiler(stmts, args.arch, args.os, code, debug, args.input, not args.no_inject_runtime, entry)
    compile_out = args.cout or DEFAULT_COMPILED
    if args.compile or args.exit_after_compile:
        if args.cout == "stdout":
            print(compiled)
        else:
            write_file(compile_out, compiled)
            debug_print(debug, f"Compiled written to {compile_out}")
        if args.exit_after_compile:
            return

    if not args.arch in SUPPORTED_ARCHS:
        sys.exit(f"[{', '.join(SUPPORTED_ARCHS)}] architectures are supported.")

    asm_out = args.aout or DEFAULT_BINARY
    write_file(compile_out, compiled)
    if entry and args.no_inject_runtime:
        assemble_and_link(compile_out, asm_out, args.o, args.os, debug, "nasm", args.debug_output, entry)
    else:
        assemble_and_link(compile_out, asm_out, args.o, args.os, debug, "nasm", args.debug_output)
    os.chmod(asm_out, 0o755)
    debug_print(debug, "Running binary...")
    subprocess.run([args.o])


if __name__ == "__main__":
    import shutil
    main()