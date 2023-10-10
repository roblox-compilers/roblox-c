#include "src/rbx.h"

enum rbx_status {
    RBX_OK = 20,
    RBX_ERR = 30,
};

int myFunc(int n) {
    volatile int counter = 0;
    while (counter < 10) {
        print("Counter = ", counter);
        counter++;
    }
    return 0;
}