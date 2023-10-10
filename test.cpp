#include "src/rbx.h"

class Test {
public:
    Test(int x, int y) {
        printf("Test constructor called with x = %d, y = %d\n", x, y);
    }
    ~Test() {
        printf("Test destructor called\n");
    }
private:
    int x;
    int y;
};

int main() {
    Test* t = new Test(10, 20); // call the constructor of the Test class
    delete t; // call the destructor of the Test class
    return 0;
}