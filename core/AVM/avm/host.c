#include <runner.h>
#include <host.h>

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>

void run_host_py(AVEF_State* state, char* code) {
    FILE* f = fopen("tmp_host.py", "w");
    if (!f) {
        printf("WARNING [HOST]: Unable to create TEMP file!\n");
        return;
    }

    fprintf(f, "%s\n", code);
    fclose(f);
    
    system("python tmp_host.py");
    unlink("tmp_host.py");
}