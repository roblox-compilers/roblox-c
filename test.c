#include "src/rbx.h"

enum rbx_status {
    RBX_OK = 20,
    RBX_ERR = 30,
};

int myFunc(int n) {
    __asm__ __volatile__ (
        "movl %1, %%eax;"
        "addl $1, %%eax;"
        "movl %%eax, %0;"
    );
    return 0;
}