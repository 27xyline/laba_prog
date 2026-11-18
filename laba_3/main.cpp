#include "truchet.hpp"

#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct EndOfInput {};

std::string readLine(const std::string& prompt) {
    std::cout << prompt << std::flush;
    std::string line;
    if (!std::getline(std::cin, line)) throw EndOfInput{};
    return line;
}

template<typename... Args>
void readValues(const std::string& prompt, Args&... args) {
    std::istringstream input(readLine(prompt));
    const bool valid = (... && static_cast<bool>(input >> args));
    input >> std::ws;
    if (!valid || !input.eof()) {
        throw std::invalid_argument("Введите указанное количество чисел через пробел.");
    }
}

Color readColor(const std::string& prompt) {
    int r, g, b;
    readValues(prompt, r, g, b);
    return Color::fromBytes(r, g, b);
}

Point readPoint(const std::string& prompt) {
    Point point{};
    readValues(prompt, point.x, point.y);
    return point;
}

int readChoice(const std::string& prompt, int min, int max) {
    int value;
    readValues(prompt, value);
    if (value < min || value > max) {
        throw std::invalid_argument("Выбран недопустимый пункт.");
    }
    return value;
}

std::unique_ptr<IShape> readRectangle() {
    int x, y, width, height, thickness;
    readValues("Центр (x y): ", x, y);
    readValues("Ширина и высота: ", width, height);
    const Color border = readColor("Цвет контура RGB (0..255): ");
    const bool filled = readChoice("Заливка (1 - да, 0 - нет): ", 0, 1) == 1;
    const Color fill = filled ? readColor("Цвет заливки RGB (0..255): ") : border;
    readValues("Толщина контура: ", thickness);
    return std::make_unique<Rectangle>(x, y, width, height, border, fill, thickness, filled);
}

std::unique_ptr<IShape> readSquares() {
    int x, y, size, count, step;
    readValues("Центр (x y): ", x, y);
    readValues("Начальная сторона, количество, шаг уменьшения: ", size, count, step);
    const Color first = readColor("Начальный цвет RGB (0..255): ");
    const Color last = readColor("Конечный цвет RGB (0..255): ");
    return std::make_unique<NestedSquares>(x, y, size, count, step, first, last);
}

std::unique_ptr<IShape> readSegment() {
    const Point start = readPoint("Начало отрезка (x y): ");
    const Point end = readPoint("Конец отрезка (x y): ");
    const int algorithm = readChoice("Алгоритм (1 - Ву, 2 - Брезенхем): ", 1, 2);
    int thickness = 1;
    if (algorithm == 2) readValues("Толщина линии: ", thickness);
    const Color color = readColor("Цвет линии RGB (0..255): ");
    return std::make_unique<LineSegment>(start, end, color,
        algorithm == 1 ? LineSegment::Algorithm::Wu : LineSegment::Algorithm::Bresenham, thickness);
}

std::unique_ptr<IShape> readPolygon() {
    const int count = readChoice("Число вершин (3..10000): ", 3, 10000);
    std::vector<Point> vertices;
    vertices.reserve(static_cast<std::size_t>(count));
    for (int i = 0; i < count; ++i) {
        vertices.push_back(readPoint("Вершина " + std::to_string(i + 1) + " (x y): "));
    }
    const Color color = readColor("Цвет контура RGB (0..255): ");
    int thickness;
    readValues("Толщина контура: ", thickness);
    return std::make_unique<Polygon>(std::move(vertices), color, thickness);
}

std::unique_ptr<IShape> readBoard() {
    int columns, rows;
    readValues("Количество клеток по X и Y: ", columns, rows);
    const Color first = readColor("Первый цвет RGB (0..255): ");
    const Color second = readColor("Второй цвет RGB (0..255): ");
    return std::make_unique<TruchetBoard>(columns, rows, first, second);
}

void save(const Image& image) {
    const int format = readChoice("Формат (1 - PPM P3, 2 - PGM P2): ", 1, 2);
    const std::string path = readLine("Имя файла: ");
    if (path.find_first_not_of(" \t\r\n") == std::string::npos) {
        throw std::invalid_argument("Имя файла не должно быть пустым.");
    }
    std::ofstream output(path);
    if (!output) throw std::runtime_error("Не удалось открыть файл для записи: " + path);
    std::unique_ptr<IPNMExporter> exporter;
    if (format == 1) exporter = std::make_unique<P3Exporter>();
    else exporter = std::make_unique<P2Exporter>();
    exporter->write(image, output);
    output.close();
    if (!output) throw std::runtime_error("Не удалось полностью записать файл: " + path);
    std::cout << "Сохранено: " << path << " (" << image.width() << 'x' << image.height() << ")\n";
}
}

int main() {
    Image image(512, 512, Color::fromBytes(255, 255, 255));
    Canvas canvas(image);
    while (true) {
        try {
            std::cout << "\n=== Генератор растровых изображений ===\n"
                      << "Холст: " << image.width() << 'x' << image.height() << "\n"
                      << "1. Создать новый холст\n"
                      << "2. Прямоугольник\n"
                      << "3. Вложенные квадраты\n"
                      << "4. Отрезок: Ву или Брезенхем\n"
                      << "5. Многоугольник\n"
                      << "6. Заливка области\n"
                      << "7. Вариант 2: шахматная доска и узор Трюше\n"
                      << "8. Сохранить PPM/PGM\n"
                      << "0. Выход\n";
            const int choice = readChoice("Выберите пункт: ", 0, 8);
            if (choice == 0) break;
            if (choice == 1) {
                int width, height;
                readValues("Ширина и высота холста: ", width, height);
                const Color background = readColor("Цвет фона RGB (0..255): ");
                image.resize(width, height, background);
                std::cout << "Холст создан.\n";
            } else if (choice == 6) {
                int x, y;
                double tolerance;
                readValues("Затравочная точка (x y): ", x, y);
                const Color replacement = readColor("Цвет заливки RGB (0..255): ");
                readValues("Допуск RGB (0 - точное совпадение): ", tolerance);
                FloodFill::apply(image, x, y, replacement, tolerance);
                std::cout << "Область залита.\n";
            } else if (choice == 8) {
                save(image);
            } else {
                std::unique_ptr<IShape> shape;
                if (choice == 2) shape = readRectangle();
                else if (choice == 3) shape = readSquares();
                else if (choice == 4) shape = readSegment();
                else if (choice == 5) shape = readPolygon();
                else shape = readBoard();
                shape->draw(canvas);
                std::cout << "Готово.\n";
            }
        } catch (const EndOfInput&) {
            std::cout << "\nВвод завершён.\n";
            break;
        } catch (const std::exception& error) {
            std::cerr << "Ошибка: " << error.what() << '\n';
        }
    }
    return 0;
}
