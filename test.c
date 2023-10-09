enum X {
    A,
    B,
    C,
};

struct Y {
    int a;
    int b;
};

union Value {
    int i;
    float f;
};


int myFunc(int a, int b) {
    a++;
    b++;
    return a + b;
}
