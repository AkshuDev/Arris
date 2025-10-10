#pragma once

#include <avef.h>
#include <runner.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <host.h>

static inline void int_divide_error(AVEF_State* state, uint16_t n, AVEF_Instruction* i) {
    (void)n; (void)i; printf("#DE Divide Error\n"); state->running = 0;
}

static inline void int_host(AVEF_State* state, uint16_t n, AVEF_Instruction* i) {
    (void)n;
    uint64_t addr = (i->mode == IMMONLY) ? i->imm : state->REGS[i->src];
    // run_host_py(state, addr);
}

static inline void int_os(AVEF_State* state, uint16_t n, AVEF_Instruction* i) {
    (void)i;

    // This checks for OS Syscalls
    uint64_t syscall_no = state->REGS[QG0_REG];
    if (syscall_no == 0) { // Exit
        state->running = 0;
        return;
    } else if (syscall_no == 1) { 
        return;
    } else if (syscall_no == 2) {
        uint64_t len = state->REGS[QG2_REG];
        uint64_t addr = state->REGS[QG3_REG];
        char msg[len];
        memcpy(&msg, state->memory + addr, len);
        fprintf(stdout, "%s", msg);
        return;
    } else {
        printf("WARNING [AVM OS]: Unknown OS Call!\n");
        return;
    }
}
