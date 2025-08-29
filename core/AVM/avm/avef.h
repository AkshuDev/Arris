#pragma once

#include <stdint.h>

typedef struct {
    char header[4];
    uint16_t version;
    uint16_t architecture;
    uint64_t entry_point;
    uint64_t section_table_offset;
    uint32_t number_of_sections;
    uint64_t flags;
    uint64_t memory_size;
    char reserved[20];
} AVEF_Header;

typedef struct {
    char name[32];
    uint64_t virtual_addr;
    uint64_t file_offset;
    uint64_t size;
    uint32_t flags;
    uint32_t align;
} AVEF_Section;