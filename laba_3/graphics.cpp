#include "graphics.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <queue>
#include <stdexcept>
#include <utility>

namespace {
constexpr double maxCoordinate = 1'000'000.0;
constexpr int maxThickness = 10'000;

void validatePoint(Point point) {
    if (!std::isfinite(point.x) || !std::isfinite(point.y) ||
        std::abs(point.x) > maxCoordinate || std::abs(point.y) > maxCoordinate) {
        throw std::invalid_argument("Координаты должны быть конечными числами от -1000000 до 1000000.");
    }
}

void validateThickness(int thickness) {
    if (thickness < 1 || thickness > maxThickness) {
        throw std::invalid_argument("Толщина должна быть в диапазоне 1..10000.");
    }
}

bool clipLine(Point& start, Point& end, double left, double top, double right, double bottom) {
    const double dx = end.x - start.x;
    const double dy = end.y - start.y;
    const double p[] = {-dx, dx, -dy, dy};
    const double q[] = {start.x - left, right - start.x, start.y - top, bottom - start.y};
    double first = 0.0;
    double last = 1.0;
    for (int i = 0; i < 4; ++i) {
        if (p[i] == 0.0) {
            if (q[i] < 0.0) return false;
            continue;
        }
        const double t = q[i] / p[i];
        if (p[i] < 0.0) first = std::max(first, t);
        else last = std::min(last, t);
        if (first > last) return false;
    }
    end = {start.x + last * dx, start.y + last * dy};
    start = {start.x + first * dx, start.y + first * dy};
    return true;
}

double fraction(double value) { return value - std::floor(value); }
double inverseFraction(double value) { return 1.0 - fraction(value); }
}

Canvas::Canvas(Image& image) : image_(image) {}
Image& Canvas::image() { return image_; }
void Canvas::setPen(Color color) { pen_ = color; }

void Canvas::plot(int x, int y, float coverage) {
    if (x < 0 || y < 0 || x >= image_.width() || y >= image_.height()) return;
    Color source = pen_;
    source.a *= std::clamp(coverage, 0.0f, 1.0f);
    image_.at(x, y) = image_.at(x, y).blend(source);
}

void Canvas::lineWu(Point start, Point end) {
    validatePoint(start);
    validatePoint(end);
    if (!clipLine(start, end, -1.0, -1.0, image_.width(), image_.height())) return;
    if (start.x == end.x && start.y == end.y) {
        plot(static_cast<int>(std::lround(start.x)), static_cast<int>(std::lround(start.y)));
        return;
    }

    const bool steep = std::abs(end.y - start.y) > std::abs(end.x - start.x);
    if (steep) {
        std::swap(start.x, start.y);
        std::swap(end.x, end.y);
    }
    if (start.x > end.x) std::swap(start, end);
    const double gradient = (end.y - start.y) / (end.x - start.x);
    auto draw = [&](int x, int y, double coverage) {
        if (steep) plot(y, x, static_cast<float>(coverage));
        else plot(x, y, static_cast<float>(coverage));
    };

    if (std::round(start.x) == std::round(end.x)) {
        const int x = static_cast<int>(std::round(start.x));
        const double middleY = (start.y + end.y) / 2.0;
        const int y = static_cast<int>(std::floor(middleY));
        const double coverage = end.x - start.x;
        draw(x, y, inverseFraction(middleY) * coverage);
        draw(x, y + 1, fraction(middleY) * coverage);
        return;
    }

    double xEnd = std::round(start.x);
    double yEnd = start.y + gradient * (xEnd - start.x);
    double gap = inverseFraction(start.x + 0.5);
    const int firstX = static_cast<int>(xEnd);
    const int firstY = static_cast<int>(std::floor(yEnd));
    draw(firstX, firstY, inverseFraction(yEnd) * gap);
    draw(firstX, firstY + 1, fraction(yEnd) * gap);
    double intersection = yEnd + gradient;

    xEnd = std::round(end.x);
    yEnd = end.y + gradient * (xEnd - end.x);
    gap = fraction(end.x + 0.5);
    const int lastX = static_cast<int>(xEnd);
    const int lastY = static_cast<int>(std::floor(yEnd));
    for (int x = firstX + 1; x < lastX; ++x) {
        const int y = static_cast<int>(std::floor(intersection));
        draw(x, y, inverseFraction(intersection));
        draw(x, y + 1, fraction(intersection));
        intersection += gradient;
    }
    draw(lastX, lastY, inverseFraction(yEnd) * gap);
    draw(lastX, lastY + 1, fraction(yEnd) * gap);
}

void Canvas::lineBresenham(Point start, Point end, int thickness) {
    validatePoint(start);
    validatePoint(end);
    validateThickness(thickness);
    if (start.x > end.x || (start.x == end.x && start.y > end.y)) {
        std::swap(start, end);
    }
    const double half = thickness / 2.0;
    const double margin = half + 1.0;
    if (!clipLine(start, end, -margin, -margin,
                  image_.width() - 1.0 + margin, image_.height() - 1.0 + margin)) return;

    const double dx = end.x - start.x;
    const double dy = end.y - start.y;
    const double length = std::hypot(dx, dy);
    auto inBody = [&](int x, int y) {
        if (length == 0.0) return false;
        const double px = x - start.x;
        const double py = y - start.y;
        const double along = (px * dx + py * dy) / length;
        const double normal = (dx * py - dy * px) / length;
        return along >= 0.0 && along <= length && normal >= -half && normal < half;
    };

    if (thickness > 1 && length > 0.0) {
        const int left = static_cast<int>(std::max(0.0, std::floor(std::min(start.x, end.x) - half)));
        const int right = static_cast<int>(std::min(image_.width() - 1.0,
                                                    std::ceil(std::max(start.x, end.x) + half)));
        const int top = static_cast<int>(std::max(0.0, std::floor(std::min(start.y, end.y) - half)));
        const int bottom = static_cast<int>(std::min(image_.height() - 1.0,
                                                     std::ceil(std::max(start.y, end.y) + half)));
        for (int y = top; y <= bottom; ++y) {
            for (int x = left; x <= right; ++x) {
                if (inBody(x, y)) plot(x, y);
            }
        }
    }

    int x = static_cast<int>(std::lround(start.x));
    int y = static_cast<int>(std::lround(start.y));
    const int endX = static_cast<int>(std::lround(end.x));
    const int endY = static_cast<int>(std::lround(end.y));
    const int stepX = x < endX ? 1 : -1;
    const int stepY = y < endY ? 1 : -1;
    const int differenceX = std::abs(endX - x);
    const int differenceY = -std::abs(endY - y);
    int error = differenceX + differenceY;
    while (true) {
        if (thickness == 1 || !inBody(x, y)) plot(x, y);
        if (x == endX && y == endY) break;
        const int twiceError = 2 * error;
        if (twiceError >= differenceY) { error += differenceY; x += stepX; }
        if (twiceError <= differenceX) { error += differenceX; y += stepY; }
    }
    if (length == 0.0 && thickness > 1) {
        const int left = static_cast<int>(std::max(0.0, std::ceil(start.x - half)));
        const int right = static_cast<int>(std::min(image_.width() - 1.0, std::ceil(start.x + half) - 1));
        const int top = static_cast<int>(std::max(0.0, std::ceil(start.y - half)));
        const int bottom = static_cast<int>(std::min(image_.height() - 1.0, std::ceil(start.y + half) - 1));
        for (int py = top; py <= bottom; ++py) {
            for (int px = left; px <= right; ++px) {
                if (px != x || py != y) plot(px, py);
            }
        }
    }
}

Rectangle::Rectangle(int cx, int cy, int width, int height, Color border,
                     Color fill, int thickness, bool filled)
    : cx_(cx), cy_(cy), width_(width), height_(height), thickness_(thickness),
      border_(border), fill_(fill), filled_(filled) {
    validatePoint({static_cast<double>(cx), static_cast<double>(cy)});
    validateThickness(thickness);
    if (width < 1 || height < 1 || width > maxCoordinate || height > maxCoordinate) {
        throw std::invalid_argument("Размеры прямоугольника должны быть в диапазоне 1..1000000.");
    }
}

void Rectangle::draw(Canvas& canvas) const {
    const int left = cx_ - width_ / 2;
    const int top = cy_ - height_ / 2;
    const int right = left + width_ - 1;
    const int bottom = top + height_ - 1;
    auto drawSpan = [&](int y, int first, int last, Color color) {
        canvas.setPen(color);
        for (int x = std::max(0, first); x <= std::min(canvas.image().width() - 1, last); ++x) {
            canvas.plot(x, y);
        }
    };
    for (int y = std::max(0, top); y <= std::min(canvas.image().height() - 1, bottom); ++y) {
        if (y - top < thickness_ || bottom - y < thickness_) {
            drawSpan(y, left, right, border_);
        } else {
            const int leftEnd = std::min(right, left + thickness_ - 1);
            const int rightStart = std::max(leftEnd + 1, right - thickness_ + 1);
            drawSpan(y, left, leftEnd, border_);
            if (filled_) drawSpan(y, leftEnd + 1, rightStart - 1, fill_);
            drawSpan(y, rightStart, right, border_);
        }
    }
}

NestedSquares::NestedSquares(int cx, int cy, int size, int count, int step,
                             Color first, Color last)
    : cx_(cx), cy_(cy), size_(size), count_(count), step_(step), first_(first), last_(last) {
    validatePoint({static_cast<double>(cx), static_cast<double>(cy)});
    if (size < 1 || size > maxCoordinate || count < 1 || count > 10000 ||
        step < 1 || step > maxCoordinate) {
        throw std::invalid_argument("Недопустимые параметры вложенных квадратов.");
    }
}

void NestedSquares::draw(Canvas& canvas) const {
    for (int i = 0; i < count_; ++i) {
        const long long size = static_cast<long long>(size_) - 2LL * i * step_;
        if (size <= 0) break;
        const float t = count_ > 1 ? static_cast<float>(i) / (count_ - 1) : 0.0f;
        const Color color = first_.lerp(last_, t);
        Rectangle(cx_, cy_, static_cast<int>(size), static_cast<int>(size),
                  color, color, 1, false).draw(canvas);
    }
}

LineSegment::LineSegment(Point start, Point end, Color color, Algorithm algorithm, int thickness)
    : start_(start), end_(end), color_(color), algorithm_(algorithm), thickness_(thickness) {
    validatePoint(start);
    validatePoint(end);
    validateThickness(thickness);
}

void LineSegment::draw(Canvas& canvas) const {
    canvas.setPen(color_);
    if (algorithm_ == Algorithm::Wu) canvas.lineWu(start_, end_);
    else canvas.lineBresenham(start_, end_, thickness_);
}

Polygon::Polygon(std::vector<Point> vertices, Color color, int thickness)
    : vertices_(std::move(vertices)), color_(color), thickness_(thickness) {
    if (vertices_.size() < 3 || vertices_.size() > 10000) {
        throw std::invalid_argument("Многоугольник должен содержать от 3 до 10000 вершин.");
    }
    for (Point point : vertices_) validatePoint(point);
    validateThickness(thickness);
}

void Polygon::draw(Canvas& canvas) const {
    canvas.setPen(color_);
    for (std::size_t i = 0; i < vertices_.size(); ++i) {
        canvas.lineBresenham(vertices_[i], vertices_[(i + 1) % vertices_.size()], thickness_);
    }
}

void FloodFill::apply(Image& image, int x, int y, Color replacement, double tolerance) {
    if (!std::isfinite(tolerance) || tolerance < 0.0) {
        throw std::invalid_argument("Допуск цвета должен быть неотрицательным конечным числом.");
    }
    const Color target = image.at(x, y);
    const std::size_t width = static_cast<std::size_t>(image.width());
    std::vector<unsigned char> visited(width * static_cast<std::size_t>(image.height()), 0);
    std::queue<std::pair<int, int>> pending;
    auto add = [&](int px, int py) {
        if (px < 0 || py < 0 || px >= image.width() || py >= image.height()) return;
        const std::size_t index = static_cast<std::size_t>(py) * width + static_cast<std::size_t>(px);
        if (!visited[index]) {
            visited[index] = 1;
            pending.emplace(px, py);
        }
    };
    const auto channelDifference = [](float current, float original) {
        return static_cast<double>(current * 255.0f) - original * 255.0f;
    };
    add(x, y);
    while (!pending.empty()) {
        const auto [px, py] = pending.front();
        pending.pop();
        const Color current = image.at(px, py);
        if (tolerance == 0.0) {
            if (current.r != target.r || current.g != target.g || current.b != target.b) continue;
        } else {
            const double dr = channelDifference(current.r, target.r);
            const double dg = channelDifference(current.g, target.g);
            const double db = channelDifference(current.b, target.b);
            if (std::sqrt(dr * dr + dg * dg + db * db) > tolerance) continue;
        }
        image.at(px, py) = replacement;
        add(px - 1, py);
        add(px + 1, py);
        add(px, py - 1);
        add(px, py + 1);
    }
}
