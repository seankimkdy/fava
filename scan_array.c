#include <stdio.h>
#include <stdlib.h>

#define ARRAY_SIZE_GB 2
#define PAGE_SIZE_KB 4

int main() {
    unsigned long long int array_size_bytes = ARRAY_SIZE_GB * 1024ULL * 1024ULL * 1024ULL;
    unsigned long long int page_size_bytes = PAGE_SIZE_KB * 1024ULL;

    volatile char* array = (volatile char*) malloc(array_size_bytes);

    if (array == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    for (int rep = 0; rep < 5; rep++) {
        for (size_t offset = 0; offset < array_size_bytes; offset += page_size_bytes) {
            array[offset] = 5;
        }
    }

    free((void*) array);
    return 0;
}
