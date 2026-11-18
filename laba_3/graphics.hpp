#pragma once

#include "image.hpp"

#include <vector>

struct Point {
    double x;
    double y;
};

class Canvas {
public:
    explicit Canvas(Image& image);
    Image& image();
    void setPen(Color color);
    void plot(int x, int y, float coverage = 1.0f);
    void lineWu(Point start, Point end);
    void lineBresenham(Point start, Point end, int thickness);

private:
    Image& image_;
    Color pen_;
};

class IShape {
public:
    virtual ~IShape() = default;
    virtual void draw(Canvas& canvas) const = 0;
};

class Rectangle : public IShape {
public:
    Rectangle(int cx, int cy, int width, int height, Color border,
              Color fill, int thickness, bool filled);
    void draw(Canvas& canvas) const override;

private:
    int cx_, cy_, width_, height_, thickness_;
    Color border_, fill_;
    bool filled_;
};

class NestedSquares : public IShape {
public:
    NestedSquares(int cx, int cy, int size, int count, int step,
                  Color first, Color last);
    void draw(Canvas& canvas) const override;

private:
    int cx_, cy_, size_, count_, step_;
    Color first_, last_;
};

class LineSegment : public IShape {
public:
    enum class Algorithm { Wu, Bresenham };
    LineSegment(Point start, Point end, Color color, Algorithm algorithm, int thickness = 1);
    void draw(Canvas& canvas) const override;

private:
    Point start_, end_;
    Color color_;
    Algorithm algorithm_;
    int thickness_;
};

class Polygon : public IShape {
public:
    Polygon(std::vector<Point> vertices, Color color, int thickness = 1);
    void draw(Canvas& canvas) const override;

private:
    std::vector<Point> vertices_;
    Color color_;
    int thickness_;
};

class FloodFill {
public:
    static void apply(Image& image, int x, int y, Color replacement, double tolerance);
};
