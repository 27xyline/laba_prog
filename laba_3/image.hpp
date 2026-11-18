#pragma once

#include <cstddef>
#include <cstdint>
#include <iosfwd>
#include <vector>

struct Color {
    float r = 0.0f;
    float g = 0.0f;
    float b = 0.0f;
    float a = 1.0f;

    static Color fromBytes(int red, int green, int blue, int alpha = 255);
    std::uint8_t grayscale() const;
    Color lerp(const Color& target, float t) const;
    Color blend(const Color& source) const;
    Color operator+(const Color& other) const;
    Color operator*(float factor) const;
};

class Image {
public:
    Image(int width, int height, Color background = {});

    int width() const;
    int height() const;
    Color& at(int x, int y);
    const Color& at(int x, int y) const;
    Color* data();
    const Color* data() const;
    void clear(Color color);
    void resize(int width, int height, Color background = {});

private:
    int width_ = 0;
    int height_ = 0;
    std::vector<Color> pixels_;
};

class IPNMExporter {
public:
    virtual ~IPNMExporter() = default;
    virtual void write(const Image& image, std::ostream& output) const = 0;
};

class P2Exporter : public IPNMExporter {
public:
    void write(const Image& image, std::ostream& output) const override;
};

class P3Exporter : public IPNMExporter {
public:
    void write(const Image& image, std::ostream& output) const override;
};
