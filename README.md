# Arris — Portable Hybrid Language & Virtual OS

Arris is a hybrid programming language, compiler toolchain, and virtual OS designed for deep systems control, cross-language embedding, and portable execution. It blends high-level expressiveness with low-level capabilities (direct memory, pointers, and live code patching) while keeping host safety via a sandboxed virtual machine.

## Project layout (recommended)
- `core/` — Python lexer, parser, ARRIS -> VASM compiler
- `core/AVEF/` — Python VASM → AVEF assembler & disassembler, AVEF dumper
- `core/AVM/` — C implementation of Arris Virtual Machine (interpreter); planned AOT/JIT backends
- `tests/` — sample `.arris`, `.vasm`, `.avef` files
- `docs/` — PVCpu ISA, VASM reference, AVEF format spec, developer guides

## What Arris does
- **Hybrid language**: high-level syntax (typed vars, expressions, control flow) + low-level primitives (explicit stack/heap access, pointers, self-modifying code).
- **Cross-language embedding**: inline blocks for other languages (e.g., `__py__`, `__c__`, `__js__`, `__aol__`) that can receive Arris variables and return values at runtime.
- **Multi-input support**: AVM toolchain accepts and integrates `.vasm`, `.asm`, `.S`, `.py`, `.c`, `.cpp`, `.cs`, `.java`, `.js`, `.aol`, and more — allowing polyglot builds and seamless interop.
- **IR & runtime**: Frontend → VASM (PVCpu virtual assembly) → Assembler → `.avef` (Arris Virtual Executable Format). AVM loads and executes `.avef`.
- **Tooling & portability**: `.avef` is portable across hosts; AVM provides host adaptors for producing native host artifacts (`.exe`, `.elf`, `.apk`, `.aosf`) via AOT or host-specific loaders.
- **Execution modes**: AVM currently interprets PVCpu bytecode (C implementation); AOT and JIT backends are planned and can be switched at runtime or during deploy.

## AVM (Arris Virtual Machine)
- Implemented in C for performance and safe memory control.
- Current mode: Interpreter of PVCpu bytecode.
- Planned: pluggable AOT compiler and JIT compiler backends so you can run interpreted, AOTed, or JIT-compiled code and switch modes.
- Runlang dispatch: AVM recognizes `Runlang` blocks embedded in AVEF and dispatches them to registered runtime handlers (Python, C, JS, etc.), with secure marshalling of values/pointers.

## File format: `.avef`
- Portable container with section table: `.text`, `.rodata`, `.data`, `.bss`, `.symbols`, and embedded runlang payloads.
- Designed for tooling: easy extraction, symbol lookup, patching, and debugging.
- Supports embedding language payloads that AVM will execute via registered handlers.

## Example
Arris source:
```arris
let dword x = 1 + 2 * 3 
let int y = (x + 4) / 2;

__py__: {
  "print(\"My var: \$: \$\")" "X" x
}
```

Vasm Compiled:
```vasm
section .data
section .bss
section .rodata
section .text
global _main
_main:
	push qSF
	mov qSF, qSP
	sub qSF, 32
	mov qG0, 1
	push qG0
	mov qG0, 2
	push qG0
	mov qG0, 3
	mov qG1, qG0
	pop qG2
	imul qG2, qG1
	mov qG0, qG2
	mov qG1, qG0
	pop qG2
	add qG2, qG1
	mov qG0, qG2
	mov [qSF + 0], dG0
	sub qSF, 32
	mov dG0, [qSF + 0]
	push qG0
	mov qG0, 4
	mov qG1, qG0
	pop qG2
	add qG2, qG1
	mov qG0, qG2
	push qG0
	mov qG0, 2
	mov qG1, qG0
	pop qG2
	mov qG0, qG2
	cqo
	idiv qG1
	mov [qSF + 32], qG0
;;@Runlang: python
;;print("My $var: X: 7")
;;@Runlang-End
	mov qSP, qSF
	pop qSF
	mov qG0, 0
	xor qG1, qG1
	syscall
```