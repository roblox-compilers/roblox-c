#include "src/rbx.h"

// Base class
class Shape {
   public:
    void setWidth(int w) {
        width = w;
    }
    void setHeight(int h) {
        height = h;
    }

   protected:
    int width;
    int height;
};

// Derived class
class Rectangle : public Shape {
   public:
    int getArea() {
        return (width * height);
    }
};

int main() {
    Rectangle rect;

    rect.setWidth(5);
    rect.setHeight(7);

    // Print the area of the object.
    print("Total area:", rect.getArea());

    return 0;
}