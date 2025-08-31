#include <runner.h>
#include <host.h>
#include <stdio.h>
#include <stdlib.h>
#include <ints.h>

#define SEC_

int parse_inst(AVEF_State* vm, AVEF_Instruction inst) {
    uint64_t src_val = NULL_;
    uint64_t dest_val = NULL_;

    uint32_t src = inst.src;
    uint32_t dest = inst.dest;

    if (src > REG_NUM || dest > REG_NUM) {
        printf("Value in code, disguised as register, [%d]/[%d] is greater than Register count!\n", src, dest);
        return 1;
    }

    switch (inst.mode) {
        case REGREG:
            src_val = vm->REGS[src];
            break;
        case MEMREG:
            src_val = read_u64(vm, inst.imm) + vm->REGS[src];
            if (src_val == -1) return 1;
            break;
        case MEMDIR:
            src_val = read_u64(vm, inst.imm);
            if (src_val == -1) return 1;
            break;
        case REGDIR:
            src_val = inst.imm;
            break;
        case MEMONLY:
            src_val = read_u64(vm, inst.imm);
            if (src_val == -1) return 1;
            break;
        case IMMONLY:
            src_val = inst.imm;
            break;
        case NULL_:
            src_val = 0;
            break;
        default:
            printf("Unknown instruction type [%u]!\n", inst.mode);
            return 1;
    }

    // Execute
    switch(inst.instruction) {
        case MOV:
            vm->REGS[dest] = src_val;
            break;
        case STOREL:
            write_u64(vm, inst.imm, vm->REGS[src]);
            break;
        case LOADL:
            vm->REGS[dest] = src_val;
            break;
        case HALT:
            vm->running = 0; // False
            break;
        case ADD:
            vm->REGS[dest] += src_val;
            break;
        case SUB:
            vm->REGS[dest] -= src_val;
        case MUL:
            vm->REGS[dest] *= src_val;
        case CQO:
            {
                int64_t val = (int64_t)vm->REGS[QG0_REG];
                vm->REGS[QG3_REG] = (val < 0) ? ~0ULL : 0ULL; // Fill QG3 with sign
            }
            break;
        case DIV:
            int64_t q=0, r=0;
            int err = idiv128(vm, (int64_t)src_val, &q, &r);
            if (err) { raise_int(vm, 0x00, &inst); break; } // #DE
            vm->REGS[QG0_REG] = (uint64_t)q; // quotient -> RAX
            vm->REGS[QG3_REG] = (uint64_t)r; // remainder -> RDX
        case XOR:
            vm->REGS[dest] ^= src_val;
        case PUSHI:
            vm->REGS[QSP_REG] -= 8;
            write_u64(vm, vm->REGS[QSP_REG], vm->REGS[src]);
            break;
        case POPG:
            uint64_t val = read_u64(vm, vm->REGS[QSP_REG]);
            if (val == -1) return 1;
            vm->REGS[dest] = val;
            vm->REGS[QSP_REG] += 8;
            break;
        case SPECIAL_INST: // Currently assume python
            run_host_py(vm, src_val);
            break;
        case INT:
            uint16_t no_ = (uint16_t)(src_val & 0xFFFFu);
            raise_int(vm, no_, &inst);
            break;
        default:
            printf("Unknown instruction: %u\n", inst.instruction);
            return 1;
    }

    return 0;
}

void run_vm(const unsigned char* buf, size_t buf_size, AVEF_State* state, AVEF_Header* header) {
    if (!state->memory) {
        perror("Memory not present!");
        exit(5);
    }

    // Initialize the Interrupts
    state->int_handlers[0x0] = int_divide_error;
    state->int_handlers[0x1] = int_host;
    state->int_handlers[0x80] = int_os;

    // Alloc sections
    size_t section_count = header->number_of_sections;
    AVEF_Section* sections = (AVEF_Section*)(buf + header->section_table_offset); // Gets the sections via sto (section table offset)

    for (size_t i = 0; i < section_count; i++) {
        AVEF_Section* sec = &sections[i];

        if (!(sec->flags & SEC_ALLOC)) { 
            continue;
        }

        if (sec->virtual_addr + sec->size > state->mem_size) {
            printf("Section [%s] is way to big for memory allocation!\n", sec->name);
            return;
        }

        if (sec->size > 0 && sec->file_offset > 0) {
            if (sec->file_offset + sec->size <= buf_size) {
                memcpy(state->memory + sec->virtual_addr, buf + sec->file_offset, sec->size);
            } else {
                printf("Section [%s] points outside file!\n", sec->name);
                return;
            }
        } else {
            memcpy(state->memory + sec->virtual_addr, 0, sec->size);
        }
    }

    const AVEF_Section* code_sec = NULL;

    // Alloc the stack
    state->REGS[QSP_REG] = state->mem_size; // stack grows downwards
    state->REGS[QSF_REG] = NULL_;

    for (size_t i = 0; i < header->number_of_sections; i++) {
        if (sections[i].flags & SEC_X) {
            code_sec = &sections[i];
            break;
        }
    }

    if (code_sec == NULL) {
        printf("No executable section in file!\n");
        return;
    }

    size_t inst_count = code_sec->size / sizeof(AVEF_Instruction);

    state->pc = header->entry_point;
    state->running = 1;

    while (state->running && state->pc < state->mem_size + 1) {
        AVEF_Instruction* inst = (AVEF_Instruction*)(state->memory + state->pc);

        int out = parse_inst(state, *inst);
        if (out != 0) { // Some error
            printf("Fault (program dumped)\n");
            return;
        }

        state->pc += sizeof(AVEF_Instruction);
    }
}