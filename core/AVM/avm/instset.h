#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// Core
#define HALT 0
#define MOV 71
#define LEA 72
#define MOVN 73

#define CQO 74

// Stack Data Movement
#define PUSHK 1
#define PUSHI 2
#define PUSHB 3
#define PUSHG 4
#define POPG 5
#define LOADL 6
#define STOREL 7

// Arithmetic / Logic
#define ADD 10
#define SUB 11
#define MUL 12
#define DIV 13
#define AND 14
#define NOT 15
#define OR 16
#define NOR 17
#define XOR 18
#define SHL 19
#define SHR 20

// Jumping and more
#define JMP 21
#define JMPT 22
#define JMPF 23

// Calling and more
#define CALL 30
#define RET 31

// Comparison
#define CMP_EQ 40
#define CMP_NE 41
#define CMP_LT 42
#define CMP_GT 43
#define CMP_LE 44
#define CMP_GE 45

// Host interop for RunLang
#define HOST 60
#define INT 61

#define SPECIAL_INST 70