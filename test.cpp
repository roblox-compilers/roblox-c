#include "src/rbx.h"
// Enums
enum Color {
    RED,
    GREEN,
    BLUE
};

// If statements
void print_color(Color color) {
    if (color == RED) {
        print("hi");
    } else if (color == GREEN) {
        print("hi");
    } else {
        print("hi");
    }
}

// Return
int add(int a, int b) {
    return a + b;
}

// Functions
void greet(const char* name) {
    print("hi");
}

// Calling functions
void call_functions() {
    greet("Alice");
    int sum = add(2, 3);
    print("hi");
}