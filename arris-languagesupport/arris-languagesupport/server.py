from pygls.lsp.server import LanguageServer
from lsprotocol import types
import traceback

from typing import *
import logging

from lexer import *
from parser import *

FILES = {}

class ArrisLanguageServer(LanguageServer):
    CMD_NAME = "ArrisLS"
    
    def show_err(self, message: str) -> None:
        params = types.ShowMessageParams(
            type=types.MessageType.Error,
            message=message
        )
        self.window_show_message(params)

    def show_log(self, message: str) -> None:
        params = types.ShowMessageParams(
            type=types.MessageType.Log,
            message=message
        )
        self.window_show_message(params)

    def show_info(self, message: str) -> None:
        params = types.ShowMessageParams(
            type=types.MessageType.Info,
            message=message
        )
        self.window_show_message(params)

    def show_warning(self, message: str) -> None:
        params = types.ShowMessageParams(
            type=types.MessageType.Warning,
            message=message
        )
        self.window_show_message(params)

server = ArrisLanguageServer("Arris", "1.0.0")

with open("arris_language_server.log", "w") as f:
    f.write("")
logging.basicConfig(filename="arris_language_server.log", level=logging.DEBUG)

def log(msg, typ:str="debug", **kwargs):
    typ = typ.lower()
    if typ == "debug":
        logging.debug(msg)
    elif typ == "error":
        logging.error(msg)
    elif typ == "log":
        logging.log(kwargs.get("level", 1), msg)
    elif typ == "critical":
        logging.critical(msg)
    else:
        logging.error(f"Unknown Type for Log: {typ}, Defaulting to DEBUG!")
        logging.debug(msg)

def safe_handler(func):
    def wrapper(ls: ArrisLanguageServer, params):
        try:
            return func(ls, params)
        except Exception as e:
            log(e, "critical")
            log(traceback.format_exc(), "critical")
            return None
    return wrapper

def find_word_at_position(text: str, line_number: int, position: int) -> str:
    """
    Helper function to find the word at a specific position in a line of text.
    This can be used to accurately identify the word for diagnostics.
    """
    line = text.splitlines()[line_number]
    start = position
    end = position

    # Move start back to the beginning of the word
    while start > 0 and line[start - 1].isalnum():
        start -= 1

    # Move end to the end of the word
    while end < len(line) and line[end].isalnum():
        end += 1

    # Return the word
    return line[start:end]

def extract_error_details(error_msg: str):
    import re
    # Regular expression pattern to match the file, line, and column
    pattern = r"(?:Error|Parser Error|Compiler Error|Assembler Error) in file:<(?P<file>.*?)> at line:<(?P<line>\d+)> char:<(?P<col>\d+)>"
    match = re.search(pattern, error_msg)
    
    if match:
        file = match.group('file')
        line = int(match.group('line'))
        col = int(match.group('col'))
        log(f"File: {file}, Line: {line}, Col: {col}")
        return file, line, col
    else:
        return None, None, None  # Return None if pattern is not found

@server.feature(types.INITIALIZE)
@safe_handler
def on_initialize(ls: ArrisLanguageServer, params: types.InitializedParams):
    log("Arris LSP Initialized!")

@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
@safe_handler
def validate_document(ls: ArrisLanguageServer, params: Union[types.DidOpenTextDocumentParams, types.DidChangeTextDocumentParams]):
    if isinstance(params, types.DidOpenTextDocumentParams):
        uri = params.text_document.uri
        text = params.text_document.text
        FILES[uri] = {"code": text}
    elif isinstance(params, types.DidChangeTextDocumentParams):
        uri = params.text_document.uri
        text = params.content_changes[-1].text
        if not uri in FILES:
            FILES[uri] = {"code": text}
        else:
            full_text = FILES[uri]["code"]
            lines = full_text.splitlines()
            start_line = params.content_changes[-1].range.start.line
            end_line = params.content_changes[-1].range.end.line
            start_char = params.content_changes[-1].range.start.character
            end_char = params.content_changes[-1].range.end.character
            textlines = text.splitlines()
            if text == "": # backspace
                if start_line == end_line:
                    lines[start_line] = lines[start_line][:start_char] + lines[start_line][end_char:]
                else: # multiline
                    lines = lines[:start_line] + lines[end_line + 1:]
                    lines[start_line] = lines[start_line][:start_char]
                    lines[start_line + 1] = lines[start_line + 1][end_char:]
                full_text = "\n".join(lines)
            else:
                if start_line == end_line:
                    # single line change
                    lines[start_line] = lines[start_line][:params.content_changes[-1].range.start.character] + text
                else:
                    lines[start_line] = lines[start_line][:start_char] + textlines[0]
                    for i in range(1, len(textlines) - 1):
                        lines.insert(start_line + i, textlines[i])
                    lines[end_line] = textlines[-1] + lines[end_line][end_char:]

                full_text = "\n".join(lines)

            FILES[uri]["code"] = full_text
    else:
        raise ValueError(f"Unexpected param type: {type(params)}")

    diagnostics = []

    try:
        from lexer import Lexer
        from parser import (
            Parser
        )
        toks = Lexer(text).tokenize()
        ast_nodes = Parser(toks, code=text).parse()
    except Exception as e:
        log(e, "error")
        error_msg = str(e).split(":", 1)[-1].strip() if ":" in str(e) else str(e)
        file, line, col = extract_error_details(str(e))
        
        if file is None or line is None or col is None:
            # If we cannot extract file, line, and column, default to 1, 1
            file = "unknown"
            line = 1
            col = 1

        diagnostics.append(types.Diagnostic(
            range=types.Range(
                start=types.Position(line=line - 1, character=col - 1),
                end=types.Position(line=line - 1, character=col)
            ),
            message=error_msg,
            severity=types.DiagnosticSeverity.Error,
            source="arris"
        ))

    params_diag = types.PublishDiagnosticsParams(uri, diagnostics)
    ls.text_document_publish_diagnostics(params_diag)

@server.feature(types.TEXT_DOCUMENT_COMPLETION)
@safe_handler
def completions(ls: ArrisLanguageServer, params: types.CompletionParams):
    # Add all the language constructs that we want to appear in completions.
    items = [
        types.CompletionItem(label="if", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="else", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="while", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="for", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="global", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="true", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="false", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="null", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="@inc", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="@def", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="@undef", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="@if", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="@else", kind=types.CompletionItemKind.Keyword),
        types.CompletionItem(label="@err", kind=types.CompletionItemKind.Keyword)
    ]
    return items

def convert_ast_to_type(node:Expr) -> str:
    if isinstance(node, Signed):
        return f"signed {convert_ast_to_type(node.value)}"
    elif isinstance(node, Unsigned):
        return f"unsigned {convert_ast_to_type(node.value)}"
    
    if isinstance(node, Pointer):
        return f"{convert_ast_to_type(node.target)}*"

    if isinstance(node, Bit):
        return "bit"
    elif isinstance(node, Bool):
        return "bool"
    elif isinstance(node, Byte):
        return "byte"
    elif isinstance(node, Char):
        return "char"
    elif isinstance(node, Word):
        return "word"
    elif isinstance(node, Dword):
        return "dword"
    elif isinstance(node, Int):
        return "int"
    elif isinstance(node, Qword):
        return "qword"
    elif isinstance(node, Long):
        return "long"
    elif isinstance(node, Void):
        return "void"
    else:
        return "<unknown>"

@server.feature(types.TEXT_DOCUMENT_HOVER)
@safe_handler
def hover(ls: ArrisLanguageServer, params: types.HoverParams):
    # Extract the word under the cursor
    word = ""

    text_document = params.text_document
    text: str = ""

    # Logic for extracting function definitions and comments
    hover_content = ""

    try:
        textdoc: dict = FILES.get(text_document.uri, None)
        if not textdoc:
            raise RuntimeError("Could not find current file!")
        text = textdoc.get("code", "")

        word = find_word_at_position(text, params.position.line, params.position.character)

        toks = Lexer(text).tokenize()
        ast_nodes = Parser(toks, code=text).parse()

        # Check if the word corresponds to a function or a comment
        for node in ast_nodes:
            if isinstance(node, Include):
                FILES[text_document.uri][node.filename] = node.code
                ast_nodes.extend(node.body)
            if isinstance(node, FuncDecl) and word in node.name:
                ret = convert_ast_to_type(node.ret_type)
                mk_params = []
                for param in node.params:
                    mk_params.append(f"{convert_ast_to_type(param.var_type)} {param.name}")
                hover_content = f"```arris\nfunc {ret} {node.name}({", ".join(mk_params)})\n```\n\n"

        if not hover_content:
            hover_content = "**No function or comment found under cursor.**"
    except Exception as e:
        hover_content = f"Please fix all the errors first!"

    # Return the hover content
    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=hover_content)
    )

if __name__ == "__main__":
    server.start_io()
