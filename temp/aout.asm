[BITS 64]

section .data
section .bss
section .rodata
str0: db "Program Name: ", 0
str1: db "", 10, 13, "Starting Loop:", 10, 13, 0
str2: db "Looped!", 0
section .text
global __arris__compilerinjected__main
__arris__compilerinjected__main:
	mov rax, [rsp]
	lea rbx, [rsp + 8]
	call kmain
	mov rdi, rax
	mov rax, 60
	syscall
__arris__compilerinjected__strlen:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	mov rbx, rax
	mov rax, 0
.__arris__compilerinjected__strlen_loop:
	mov cl, byte [rbx + rax]
	cmp cl, 0
	je .__arris__compilerinjected__strlen_done
	inc rax
	jmp .__arris__compilerinjected__strlen_loop
.__arris__compilerinjected__strlen_done:
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
__arris_syscall:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 96
	mov [rbp - 0], rax
	mov [rbp - 16], rbx
	mov [rbp - 32], rcx
	mov [rbp - 48], rdx
	mov [rbp - 64], rdi
	mov [rbp - 80], rsi
; ASM Runlang
	mov rax, [rbp - 0]
	mov rdi, [rbp - 16]
	mov rsi, [rbp - 32]
	mov rdx, [rbp - 48]
	mov r10, [rbp - 64]
	mov r8, [rbp - 80]
	syscall
; Runlang-End
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
__arris_exit:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 16
	mov [rbp - 0], rax
	mov rax, 60
	mov rbx, [rbp - 0]
	mov rcx, 0
	mov rdx, 0
	mov rdi, 0
	mov rsi, 0
	call __arris_syscall
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
itos:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 16
	mov [rbp - 0], rax
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
print_raw:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 48
	mov [rbp - 0], rax
	mov [rbp - 16], rbx
	mov [rbp - 32], rcx
	mov rax, 1
	mov rbx, [rbp - 16]
	mov rcx, [rbp - 0]
	mov rdx, [rbp - 32]
	call __arris_syscall
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
strlen:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 16
	mov [rbp - 0], rax
	mov rax, [rbp - 0]
	call __arris__compilerinjected__strlen
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
emits:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 48
	mov [rbp - 0], rax
	mov [rbp - 16], rbx
	mov rax, [rbp - 0]
	call strlen
	mov [rbp - 32], rax
	mov rax, [rbp - 0]
	call strlen
	mov [rbp - 32], rax
	mov rax, [rbp - 0]
	mov rbx, [rbp - 16]
	mov rcx, [rbp - 32]
	call print_raw
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
print:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 16
	mov [rbp - 0], rax
	mov rax, [rbp - 0]
	mov rbx, 0
	call emits
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret
kmain:
	push rbp
	sub rsp, 8
	mov rbp, rsp
	sub rsp, 48
	mov [rbp - 0], rax
	mov [rbp - 16], rbx
	mov rax, [rbp - 16]
	mov rax, [rax]
	mov [rbp - 32], rax
	mov rax, [rbp - 16]
	mov rax, [rax]
	mov [rbp - 32], rax
	lea rax, [str0]
	call print
	mov rax, [rbp - 32]
	call print
	lea rax, [str1]
	call print
	mov rax, 0
	mov [rbp - 40], rax
	mov rax, 0
	mov [rbp - 40], rax
.for_kmain_0:
	mov rax, [rbp - 40]
	push rax
	mov rax, 5
	mov rbx, rax
	pop rcx
	cmp rcx, rbx
	jl .cmp_true_kmain_0
	jmp .cmp_false_kmain_0
.cmp_true_kmain_0:
	mov rax, 1
	jmp .cmp_end_kmain_0
.cmp_false_kmain_0:
	mov rax, 0
	jmp .cmp_end_kmain_0
.cmp_end_kmain_0:
	cmp rax, 0
	je .for_end_kmain_1
	lea rax, [str2]
	call print
	inc qword [rbp - 40]
	mov rax, qword [rbp - 40]
jmp .for_kmain_0
.for_end_kmain_1:
	mov rax, 0
	mov rsp, rbp
	add rsp, 8
	pop rbp
	ret