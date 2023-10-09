#include "src/rbx.h"

int (fibonacci)(int n) {
    if (n <= 1) {
        return n;
    } else {
        return fibonacci(n-1) + fibonacci(n-2);
    }
}

int main() {
    int n = 10;
    for (int i = 0; i < n; i++) {
        print((char *)fibonacci(i));
    }
    print("\n");
    return 0;
}