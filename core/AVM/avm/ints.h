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
    run_host_py(state, addr);
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
    } else {
        printf("WARNING [AVM OS]: Unknown OS Call!\n");
        return;
    }
}