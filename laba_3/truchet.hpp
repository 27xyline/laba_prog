#pragma once

#include "graphics.hpp"

class TruchetBoard : public IShape {
public:
    TruchetBoard(int columns, int rows, Color first, Color second);
    void draw(Canvas& canvas) const override;

private:
    int columns_, rows_;
    Color first_, second_;
};
