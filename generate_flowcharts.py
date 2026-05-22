from pathlib import Path
import math
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "block_diagrams"
WIDTH = 1200
HEIGHT = 1700


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT = font(30)
FONT_SMALL = font(25)


def wrapped(text, width=24):
    return "\n".join(textwrap.wrap(text, width=width))


def center(box):
    x, y, w, h = box
    return x + w / 2, y + h / 2


def side_point(box, side):
    x, y, w, h = box
    if side == "top":
        return x + w / 2, y
    if side == "bottom":
        return x + w / 2, y + h
    if side == "left":
        return x, y + h / 2
    if side == "right":
        return x + w, y + h / 2
    raise ValueError(side)


def draw_arrow(draw, start, end, fill="#333333", width=3):
    draw.line((start, end), fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 18
    spread = 0.45
    p1 = (
        end[0] - length * math.cos(angle - spread),
        end[1] - length * math.sin(angle - spread),
    )
    p2 = (
        end[0] - length * math.cos(angle + spread),
        end[1] - length * math.sin(angle + spread),
    )
    draw.polygon((end, p1, p2), fill=fill)


def draw_node(draw, box, text, kind):
    x, y, w, h = box
    if kind == "decision":
        points = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
        draw.polygon(points, fill="#fff4ce", outline="#6b5b18")
        draw.line(points + [points[0]], fill="#6b5b18", width=3)
    else:
        radius = h // 2 if kind == "terminal" else 18
        fill = "#e8f3ff" if kind == "terminal" else "#eef8ee"
        outline = "#255a8a" if kind == "terminal" else "#2d6730"
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline, width=3)

    draw.multiline_text(center(box), wrapped(text), fill="#111111", font=FONT, anchor="mm", align="center", spacing=6)


def draw_chart(filename, nodes, arrows):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    boxes = {}

    for key, x, y, w, h, text, kind in nodes:
        box = (x, y, w, h)
        boxes[key] = box
        draw_node(draw, box, text, kind)

    for item in arrows:
        start, end = item[0], item[1]
        start_side = item[2] if len(item) > 2 else "bottom"
        end_side = item[3] if len(item) > 3 else "top"
        label = item[4] if len(item) > 4 else None
        start_point = side_point(boxes[start], start_side)
        end_point = side_point(boxes[end], end_side)
        draw_arrow(draw, start_point, end_point)
        if label:
            mx = (start_point[0] + end_point[0]) / 2
            my = (start_point[1] + end_point[1]) / 2
            draw.text((mx, my - 10), label, fill="#111111", font=FONT_SMALL, anchor="mm")

    image.save(OUT_DIR / filename)


def bubble_flagged():
    nodes = [
        ("start", 390, 40, 420, 80, "Начало", "terminal"),
        ("init", 300, 180, 600, 95, "i = 0, swapped = true", "process"),
        ("outer", 330, 330, 540, 130, "i < n и swapped?", "decision"),
        ("reset", 300, 520, 600, 95, "swapped = false, j = 0", "process"),
        ("inner", 330, 670, 540, 130, "j + 1 < n - i?", "decision"),
        ("cmp", 330, 860, 540, 130, "a[j] > a[j+1]?", "decision"),
        ("swap", 300, 1050, 600, 110, "Обмен a[j] и a[j+1], swapped = true", "process"),
        ("incj", 300, 1220, 600, 90, "j = j + 1", "process"),
        ("inci", 300, 1380, 600, 90, "i = i + 1", "process"),
        ("end", 390, 1540, 420, 80, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "init"),
        ("init", "outer"),
        ("outer", "reset", "bottom", "top", "да"),
        ("reset", "inner"),
        ("inner", "cmp", "bottom", "top", "да"),
        ("cmp", "swap", "bottom", "top", "да"),
        ("swap", "incj"),
        ("incj", "inner", "left", "left"),
        ("cmp", "incj", "right", "right", "нет"),
        ("inner", "inci", "left", "left", "нет"),
        ("inci", "outer", "left", "left"),
        ("outer", "end", "right", "right", "нет"),
    ]
    draw_chart("bubble_flagged_flowchart.png", nodes, arrows)


def shaker():
    nodes = [
        ("start", 390, 55, 420, 80, "Начало", "terminal"),
        ("init", 280, 200, 640, 105, "left = 0, right = n - 1, swapped = true", "process"),
        ("outer", 330, 370, 540, 130, "swapped и left < right?", "decision"),
        ("forward", 280, 565, 640, 120, "Проход слева направо: максимум уходит в конец", "process"),
        ("any", 330, 750, 540, 130, "Были обмены?", "decision"),
        ("right", 280, 945, 640, 90, "right = right - 1", "process"),
        ("backward", 280, 1100, 640, 120, "Проход справа налево: минимум уходит в начало", "process"),
        ("left", 280, 1285, 640, 90, "left = left + 1", "process"),
        ("end", 390, 1515, 420, 80, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "init"),
        ("init", "outer"),
        ("outer", "forward", "bottom", "top", "да"),
        ("forward", "any"),
        ("any", "right", "bottom", "top", "да"),
        ("right", "backward"),
        ("backward", "left"),
        ("left", "outer", "left", "left"),
        ("outer", "end", "right", "right", "нет"),
        ("any", "end", "right", "right", "нет"),
    ]
    draw_chart("shaker_flowchart.png", nodes, arrows)


def odd_even():
    nodes = [
        ("start", 390, 40, 420, 80, "Начало", "terminal"),
        ("init", 300, 180, 600, 95, "sorted = false", "process"),
        ("outer", 330, 330, 540, 130, "sorted == false?", "decision"),
        ("set", 300, 520, 600, 90, "sorted = true", "process"),
        ("odd", 300, 680, 600, 115, "Нечётная фаза: пары (1,2), (3,4), ...", "process"),
        ("oddswap", 330, 860, 540, 130, "Есть обмены?", "decision"),
        ("even", 300, 1050, 600, 115, "Чётная фаза: пары (0,1), (2,3), ...", "process"),
        ("evenswap", 330, 1230, 540, 130, "Есть обмены?", "decision"),
        ("mark", 300, 1420, 600, 90, "Если был обмен: sorted = false", "process"),
        ("end", 390, 1570, 420, 80, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "init"),
        ("init", "outer"),
        ("outer", "set", "bottom", "top", "да"),
        ("set", "odd"),
        ("odd", "oddswap"),
        ("oddswap", "even", "bottom", "top", "нет"),
        ("oddswap", "mark", "left", "left", "да"),
        ("even", "evenswap"),
        ("evenswap", "mark", "bottom", "top", "да"),
        ("mark", "outer", "left", "left"),
        ("evenswap", "outer", "right", "right", "нет"),
        ("outer", "end", "right", "right", "нет"),
    ]
    draw_chart("odd_even_flowchart.png", nodes, arrows)


def main_program():
    nodes = [
        ("start", 390, 35, 420, 80, "Начало", "terminal"),
        ("const", 250, 170, 700, 105, "Задать размеры, типы данных, алгоритмы и диапазон значений", "process"),
        ("csv", 250, 330, 700, 95, "Открыть results.csv и записать заголовок", "process"),
        ("size", 330, 500, 540, 130, "Есть следующий размер n?", "decision"),
        ("type", 330, 690, 540, 130, "Есть следующий тип данных?", "decision"),
        ("gen", 250, 875, 700, 95, "Сгенерировать исходный массив", "process"),
        ("algo", 330, 1040, 540, 130, "Есть следующий алгоритм?", "decision"),
        ("copy", 250, 1225, 700, 95, "Скопировать массив через memcpy", "process"),
        ("measure", 250, 1370, 700, 95, "Отсортировать, измерить метрики и время", "process"),
        ("write", 250, 1515, 700, 95, "Записать строку результатов в CSV", "process"),
        ("end", 390, 1645, 420, 80, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "const"),
        ("const", "csv"),
        ("csv", "size"),
        ("size", "type", "bottom", "top", "да"),
        ("type", "gen", "bottom", "top", "да"),
        ("gen", "algo"),
        ("algo", "copy", "bottom", "top", "да"),
        ("copy", "measure"),
        ("measure", "write"),
        ("write", "algo", "left", "left"),
        ("algo", "type", "right", "right", "нет"),
        ("type", "size", "left", "left", "нет"),
        ("size", "end", "right", "right", "нет"),
    ]
    draw_chart("main_program_flowchart.png", nodes, arrows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bubble_flagged()
    shaker()
    odd_even()
    main_program()
    print("Блок-схемы построены.")


if __name__ == "__main__":
    main()
