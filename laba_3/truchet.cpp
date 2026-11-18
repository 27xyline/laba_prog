#include "truchet.hpp"

#include <stdexcept>

TruchetBoard::TruchetBoard(int columns, int rows, Color first, Color second)
    : columns_(columns), rows_(rows), first_(first), second_(second) {
    if (columns < 1 || rows < 1 || columns > 16384 || rows > 16384) {
        throw std::invalid_argument("Число клеток по каждой оси должно быть в диапазоне 1..16384.");
    }
}

void TruchetBoard::draw(Canvas& canvas) const {
    Image& image = canvas.image();
    if (columns_ > image.width() || rows_ > image.height()) {
        throw std::invalid_argument("Число клеток не может превышать размер холста.");
    }
    for (int row = 0; row < rows_; ++row) {
        const int top = row * image.height() / rows_;
        const int bottom = (row + 1) * image.height() / rows_ - 1;
        for (int column = 0; column < columns_; ++column) {
            const int left = column * image.width() / columns_;
            const int right = (column + 1) * image.width() / columns_ - 1;
            const bool dark = (row + column) % 2 != 0;
            for (int y = top; y <= bottom; ++y) {
                for (int x = left; x <= right; ++x) {
                    image.at(x, y) = dark ? second_ : first_;
                }
            }
            canvas.setPen(dark ? first_ : second_);
            if ((row * column) % 2 == 0) {
                canvas.lineWu({static_cast<double>(left), static_cast<double>(top)},
                              {static_cast<double>(right), static_cast<double>(bottom)});
            } else {
                canvas.lineWu({static_cast<double>(right), static_cast<double>(top)},
                              {static_cast<double>(left), static_cast<double>(bottom)});
            }
        }
    }
}
