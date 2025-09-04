#include <instset.h>
#include <avef.h>
#include <runner.h>

static char* avef_code = NULL;
static long avef_size = 0;
static FILE* avef_fd = NULL;

void load_file(const char* file) {
    avef_fd = fopen(file, "rb");
    if (!avef_fd) {
        perror("Could not open AVEF file!\n");
        printf("PATH: %s\n", file);
        exit(1);
    }

    fseek(avef_fd, 0, SEEK_END);

    long size = ftell(avef_fd);
    if (size < 5) {
        perror("Wrong AVEF file!\n");
        exit(2);
    }
    rewind(avef_fd);

    avef_code = malloc(size);

    fread(avef_code, size, 1, avef_fd);
    avef_size = size;
    return 0;
}

void close_file() {
    fclose(avef_fd);
}

void check_headers(AVEF_Header* header_) {
    char header[4];
    strncpy(header, avef_code, 4); // Copy header

    if (header[0] != 'A' || header[1] != 'V' || header[2] != 'E' || header[3] != 'F') {
        perror("Wrong AVEF file!\n");
        exit(4);
    }

    memcpy(header_, avef_code, sizeof(AVEF_Header));
    return;
}

void make_memory(AVEF_State* state, size_t memsize) {
    state->mem_size = memsize;
    state->memory = calloc(1, memsize);
}

int main(int argc, char** argv) {
    int debug = 0;
    int memsize = 1024*1024; // 1MB

    if (argc < 2) {
        perror("Usage: avm [FILE] [-<OPTIONS>]\n");
        exit(3);
    }

    char* file_name = NULL;

    for (int i = 1; i < argc; i++) {
        if (strncmp(argv[i], "-debug", 6) == 0) {
            debug = 1;
        } else if (strncmp(argv[i], "-memsize", 8) == 0 && argc > i + 1) {
            memsize = atoi(argv[i + 1]);
            i++;
        } else {
            file_name = argv[i];
        }
    }

    AVEF_Header header;
    AVEF_State state;

    load_file(file_name);
    close_file();
    check_headers(&header);
    make_memory(&state, memsize);

    run_vm(avef_code, avef_size, &state, &header);

    free(state.memory); // Memory allocated on heap
    free(avef_code);

    return 0;
}