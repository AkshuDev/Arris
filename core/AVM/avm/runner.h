#pragma once

#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <instset.h>
#include <avef.h>

#define REG_NUM 62
#define QSP_REG 60
#define QSF_REG 61
#define QG0_REG 43
#define QG1_REG 44
#define QG2_REG 45
#define QG3_REG 46

#define SEC_R (1 << 0)
#define SEC_W (1 << 1)
#define SEC_X (1 << 2)
#define SEC_D (1 << 3)
#define SEC_META (1 << 4)
#define SEC_ALLOC (1 << 5)

#define REGREG 1
#define MEMREG 2
#define MEMDIR 3
#define REGDIR 4
#define MEMONLY 5
#define IMMONLY 6
#define NULL_ 0

struct AVEF_State;
typedef void (*IntHandler) (struct AVEF_State* state, uint16_t int_no, AVEF_Instruction* inst);

typedef struct AVEF_State {
    int running; // 0 = False, 1 = True
    uint8_t* memory;
    size_t mem_size;
    uint64_t REGS[REG_NUM];
    size_t pc; // Program counter
    IntHandler int_handlers[256]; // INT vector table
} AVEF_State;

static inline uint64_t read_u64(AVEF_State* vm, uint64_t addr) {
    if (addr + 8 > vm->mem_size) {
        printf("Error: Address for reading is greater than memory size!\n");
        vm->running = 0;
        return -1;
    }
    return *(uint64_t*)(vm->memory + addr);
}

static inline int write_u64(AVEF_State* vm, uint64_t addr, uint64_t val) {
    if (addr + 8 > vm->mem_size) {
        printf("Error: Address for writing is greater than memory size!\n");
        vm->running = 0;
        return 1;
    }
    *(uint64_t*)(vm->memory + addr) = val;
    return 0;
}

static inline char* get_string(AVEF_State* vm, uint64_t addr) {
    if (addr >= vm->mem_size) {
        printf("Error: Trying to access string outside memory range!\n");
        vm->running = 0;
        return NULL;
    }

    // Scan until '\0' or end of memory
    uint64_t i = addr;
    while (i < vm->mem_size && vm->memory[i] != '\0') {
        i++;
    }

    if (i == vm->mem_size) {
        printf("Error: Unterminated string in memory!\n");
        vm->running = 0;
        return NULL;
    }

    return (const char*)(vm->memory + addr);
}

static inline int raise_int(AVEF_State* vm, uint16_t int_no, const AVEF_Instruction* inst) {
    if (int_no > 256) {
        printf("Interrupt value too great! 0x%02X\n", int_no);
        vm->running = 0;
        return 1;
    }

    IntHandler h = vm->int_handlers[int_no];
    if (h) {h(vm, int_no, inst);}
    else {
        printf("Unhandled Interrupt 0x%02X\n", int_no);
        vm->running = 0;
        return 1;
    }

    return 0;
}

static inline int idiv128(AVEF_State* vm, int64_t divisor, int64_t* q_out, int64_t* r_out) {
    if (divisor == 0) return -1;

    // build 128-bit signed dividend from RDX:RAX
    __int128 hi = ( __int128)( (int64_t)vm->REGS[QG3_REG] ); // sign-preserved
    __int128 lo = (unsigned __int128)vm->REGS[QG0_REG];
    __int128 dividend = (hi << 64) | lo;

    __int128 q = dividend / ( __int128)divisor;
    __int128 r = dividend % ( __int128)divisor;

    // overflow if quotient doesn't fit in signed 64
    if (q > INT64_MAX || q < INT64_MIN) return -2;

    *q_out = (int64_t)q;
    *r_out = (int64_t)r;
    return 0;
}

int parse_inst(AVEF_State* vm, AVEF_Instruction inst);
void run_vm(const unsigned char* buf, size_t buf_size, AVEF_State* state, AVEF_Header* header);
