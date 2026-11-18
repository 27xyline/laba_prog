#include "image.hpp"

#include <algorithm>
#include <cmath>
#include <ostream>
#include <stdexcept>
#include <string>

namespace {
constexpr std::size_t maxPixels = 16'000'000;
constexpr int maxDimension = 16'384;

std::uint8_t toByte(float value) {
    return static_cast<std::uint8_t>(std::lround(std::clamp(value, 0.0f, 1.0f) * 255.0f));
}

std::size_t pixelCount(int width, int height) {
    if (width <= 0 || height <= 0 || width > maxDimension || height > maxDimension ||
        static_cast<std::size_t>(width) * static_cast<std::size_t>(height) > maxPixels) {
        throw std::invalid_argument("Недопустимый размер холста (до 16384 по каждой оси и 16000000 пикселей).");
    }
    return static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
}

class TokenWriter {
public:
    explicit TokenWriter(std::ostream& output) : output_(output) {}

    void put(int value) {
        const std::string token = std::to_string(value);
        if (length_ != 0 && length_ + 1 + token.size() > 70) {
            output_ << '\n';
            length_ = 0;
        }
        if (length_ != 0) {
            output_ << ' ';
            ++length_;
        }
        output_ << token;
        length_ += token.size();
    }

    void finish() {
        if (length_ != 0) {
            output_ << '\n';
        }
        if (!output_) {
            throw std::runtime_error("Не удалось записать изображение.");
        }
    }

private:
    std::ostream& output_;
    std::size_t length_ = 0;
};
}

Color Color::fromBytes(int red, int green, int blue, int alpha) {
    for (const int channel : {red, green, blue, alpha}) {
        if (channel < 0 || channel > 255) {
            throw std::invalid_argument("Компоненты цвета должны быть в диапазоне 0..255.");
        }
    }
    return {red / 255.0f, green / 255.0f, blue / 255.0f, alpha / 255.0f};
}

std::uint8_t Color::grayscale() const {
    return toByte(0.299f * r + 0.587f * g + 0.114f * b);
}

Color Color::lerp(const Color& target, float t) const {
    return *this * (1.0f - t) + target * t;
}

Color Color::blend(const Color& source) const {
    const float sourceAlpha = std::clamp(source.a, 0.0f, 1.0f);
    const float backgroundAlpha = std::clamp(a, 0.0f, 1.0f);
    const float resultAlpha = sourceAlpha + backgroundAlpha * (1.0f - sourceAlpha);
    if (resultAlpha == 0.0f) {
        return {0.0f, 0.0f, 0.0f, 0.0f};
    }
    const float backgroundWeight = backgroundAlpha * (1.0f - sourceAlpha);
    return {(source.r * sourceAlpha + r * backgroundWeight) / resultAlpha,
            (source.g * sourceAlpha + g * backgroundWeight) / resultAlpha,
            (source.b * sourceAlpha + b * backgroundWeight) / resultAlpha,
            resultAlpha};
}

Color Color::operator+(const Color& other) const {
    return {r + other.r, g + other.g, b + other.b, a + other.a};
}

Color Color::operator*(float factor) const {
    return {r * factor, g * factor, b * factor, a * factor};
}

Image::Image(int width, int height, Color background) {
    resize(width, height, background);
}

int Image::width() const { return width_; }
int Image::height() const { return height_; }

Color& Image::at(int x, int y) {
    if (x < 0 || y < 0 || x >= width_ || y >= height_) {
        throw std::out_of_range("Координаты пикселя находятся за пределами холста.");
    }
    return pixels_[static_cast<std::size_t>(y) * static_cast<std::size_t>(width_) +
                   static_cast<std::size_t>(x)];
}

const Color& Image::at(int x, int y) const {
    if (x < 0 || y < 0 || x >= width_ || y >= height_) {
        throw std::out_of_range("Координаты пикселя находятся за пределами холста.");
    }
    return pixels_[static_cast<std::size_t>(y) * static_cast<std::size_t>(width_) +
                   static_cast<std::size_t>(x)];
}

Color* Image::data() { return pixels_.data(); }
const Color* Image::data() const { return pixels_.data(); }

void Image::clear(Color color) {
    std::fill(pixels_.begin(), pixels_.end(), color);
}

void Image::resize(int width, int height, Color background) {
    std::vector<Color> replacement(pixelCount(width, height), background);
    pixels_.swap(replacement);
    width_ = width;
    height_ = height;
}

void P2Exporter::write(const Image& image, std::ostream& output) const {
    output << "P2\n" << image.width() << ' ' << image.height() << "\n255\n";
    TokenWriter writer(output);
    for (int y = 0; y < image.height(); ++y) {
        for (int x = 0; x < image.width(); ++x) {
            writer.put(image.at(x, y).grayscale());
        }
    }
    writer.finish();
}

void P3Exporter::write(const Image& image, std::ostream& output) const {
    output << "P3\n" << image.width() << ' ' << image.height() << "\n255\n";
    TokenWriter writer(output);
    for (int y = 0; y < image.height(); ++y) {
        for (int x = 0; x < image.width(); ++x) {
            const Color& color = image.at(x, y);
            writer.put(toByte(color.r));
            writer.put(toByte(color.g));
            writer.put(toByte(color.b));
        }
    }
    writer.finish();
}
