from phardwareitk.Extensions import Color, TextFont
from phardwareitk.Extensions.HyperOut import printH
import sys

def error(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    printH(f"\nError in <{file}>:\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))

    if src and line is not None:
        src_lines = src.splitlines()
        if 1 <= line <= len(src_lines):
            # show 1 line before and after for context
            start = max(0, line - 2)
            end = min(len(src_lines), line + 1)
            for ln in range(start, end):
                prefix = ">" if (ln + 1) == line else " "
                line_color = Color("red") if (ln + 1) == line else Color("gray")
                printH(f"{prefix} {ln + 1:4d} | {src_lines[ln]}\n", FontEnabled=True, Font=TextFont(font_color=line_color))
                if (ln + 1) == line and col is not None:
                    caret_offset = len(f"{prefix} {ln + 1:4d} | ") + col
                    printH(" " * caret_offset + "^\n", FontEnabled=True, Font=TextFont(Bold=True, font_color=Color("red")))
    printH(f"Error:\n\t{' '.join(args)}", "\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
    sys.exit(1)

def parser_error(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    printH(f"\nParser Error in <{file}>:\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))

    if src and line is not None:
        src_lines = src.splitlines()
        if 1 <= line <= len(src_lines):
            # show 1 line before and after for context
            start = max(0, line - 2)
            end = min(len(src_lines), line + 1)
            for ln in range(start, end):
                prefix = ">" if (ln + 1) == line else " "
                line_color = Color("red") if (ln + 1) == line else Color("gray")
                printH(f"{prefix} {ln + 1:4d} | {src_lines[ln]}\n", FontEnabled=True, Font=TextFont(font_color=line_color))
                if (ln + 1) == line and col is not None:
                    caret_offset = len(f"{prefix} {ln + 1:4d} | ") + col
                    printH(" " * caret_offset + "^\n", FontEnabled=True, Font=TextFont(Bold=True, font_color=Color("red")))
    printH(f"Error:\n\t{' '.join(args)}", "\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
    sys.exit(1)


def printBacktrace(bt:list) -> None:
    for v in bt:
        print("At:", v)

def compilerError(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    printH(f"\nCompiler Error in <{file}>:\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))

    if src and line is not None:
        src_lines = src.splitlines()
        if 1 <= line <= len(src_lines):
            # show 1 line before and after for context
            start = max(0, line - 2)
            end = min(len(src_lines), line + 1)
            for ln in range(start, end):
                prefix = ">" if (ln + 1) == line else " "
                line_color = Color("red") if (ln + 1) == line else Color("gray")
                printH(f"{prefix} {ln + 1:4d} | {src_lines[ln]}\n", FontEnabled=True, Font=TextFont(font_color=line_color))
                if (ln + 1) == line and col is not None:
                    caret_offset = len(f"{prefix} {ln + 1:4d} | ") + col
                    printH(" " * caret_offset + "^\n", FontEnabled=True, Font=TextFont(Bold=True, font_color=Color("red")))
    printH(f"Error:\n\t{' '.join(args)}", "\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
    sys.exit(1)


def assemblerError(*args, line=None, col=None, src=None, file=None):
    file = "unknown" if file == None else file
    printH(f"\nAssembler Error in <{file}>:\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))

    if src and line is not None:
        src_lines = src.splitlines()
        if 1 <= line <= len(src_lines):
            # show 1 line before and after for context
            start = max(0, line - 2)
            end = min(len(src_lines), line + 1)
            for ln in range(start, end):
                prefix = ">" if (ln + 1) == line else " "
                line_color = Color("red") if (ln + 1) == line else Color("gray")
                printH(f"{prefix} {ln + 1:4d} | {src_lines[ln]}\n", FontEnabled=True, Font=TextFont(font_color=line_color))
                if (ln + 1) == line and col is not None:
                    caret_offset = len(f"{prefix} {ln + 1:4d} | ") + col
                    printH(" " * caret_offset + "^\n", FontEnabled=True, Font=TextFont(Bold=True, font_color=Color("red")))
    printH(f"Error:\n\t{' '.join(args)}", "\n", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
    sys.exit(1)
