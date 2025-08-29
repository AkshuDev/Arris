#include <instset.h>
#include <avef.h>

static char* avef_code = NULL;
static FILE* avef_fd = NULL;

void load_file(const char* file) {
    avef_fd = fopen(file, "rb");
    if (!avef_fd) {
        perror("Could not open AVEF file!\n");
        exit(1);
    }

    fseek(avef_fd, 0, SEEK_END);

    long size = ftell(avef_fd);
    if (size < 5) {
        perror("Wrong AVEF file!\n");
        exit(2);
    }
    rewind(avef_fd);

    fread(avef_code, size, 1, avef_fd);
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

    memcpy(header_, avef_code, sizeof(header_));
    return;
}

int main(int argc, char** argv) {
    int debug = 0;

    if (argc < 2) {
        perror("Usage: avm [FILE] [-<OPTIONS>]\n");
        exit(3);
    }

    char* file_name = NULL;

    for (int i = 1; i < argc; i++) {
        if (strncmp(argv[i], "-debug", 6) == 0) {
            debug = 1;
        } else {
            file_name = argv[i];
        }
    }

    AVEF_Header header;

    load_file(file_name);
    check_headers(&header);
    parse_header(&header);
    close_file();
    return 0;
}