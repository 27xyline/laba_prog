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


LAYOUT_SCALE = 0.7  # Scale factor to make block diagrams smaller and more compact
SCALE = 2  # Super-sampling factor for antialiasing

# Adjust font sizes proportionally
FONT = font(int(26 * LAYOUT_SCALE * SCALE))
FONT_DECISION = font(int(20 * LAYOUT_SCALE * SCALE))  # Smaller font specifically for decision blocks to prevent overflow
FONT_SMALL = font(int(18 * LAYOUT_SCALE * SCALE))


def wrapped(text, width=24):
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.extend(textwrap.wrap(paragraph, width=width))
        else:
            lines.append("")
    return "\n".join(lines)


def center(box):
    x, y, w, h = box
    return x + w / 2, y + h / 2


def side_point(box, side, kind):
    x, y, w, h = box
    if side == "top":
        return x + w / 2, y
    if side == "bottom":
        return x + w / 2, y + h
    if side == "left":
        if kind == "input_output":
            skew = 25 * SCALE * LAYOUT_SCALE
            return x + skew / 2, y + h / 2
        return x, y + h / 2
    if side == "right":
        if kind == "input_output":
            skew = 25 * SCALE * LAYOUT_SCALE
            return x + w - skew / 2, y + h / 2
        return x + w, y + h / 2
    raise ValueError(side)


def draw_arrow(draw, start, end, fill="#000000", width=2 * SCALE):
    draw.line((start, end), fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 14 * SCALE
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


def draw_arrow_path(draw, points, fill="#000000", width=2 * SCALE):
    for i in range(len(points) - 1):
        draw.line((points[i], points[i+1]), fill=fill, width=width)
    end = points[-1]
    penultimate = points[-2]
    angle = math.atan2(end[1] - penultimate[1], end[0] - penultimate[0])
    length = 14 * SCALE
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
        wrap_width = 18  # Tighter text wrapping for diamonds to prevent overflow
        points = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
        draw.polygon(points, fill="#ffffff", outline="#000000")
        draw.line(points + [points[0]], fill="#000000", width=2 * SCALE)
        f = FONT_DECISION
    elif kind == "input_output":
        wrap_width = 18
        skew = 25 * SCALE * LAYOUT_SCALE
        points = [(x + skew, y), (x + w, y), (x + w - skew, y + h), (x, y + h)]
        draw.polygon(points, fill="#ffffff", outline="#000000")
        draw.line(points + [points[0]], fill="#000000", width=2 * SCALE)
        f = FONT
    elif kind == "terminal":
        wrap_width = 20
        radius = h // 2
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill="#ffffff", outline="#000000", width=2 * SCALE)
        f = FONT
    else:  # process
        wrap_width = 30
        draw.rectangle((x, y, x + w, y + h), fill="#ffffff", outline="#000000", width=2 * SCALE)
        f = FONT

    draw.multiline_text(center(box), wrapped(text, width=wrap_width), fill="#000000", font=f, anchor="mm", align="center", spacing=4 * SCALE)


def draw_chart(filename, nodes, arrows):
    scaled_nodes = []
    for key, x, y, w, h, text, kind in nodes:
        scaled_nodes.append((
            key,
            x * LAYOUT_SCALE * SCALE,
            y * LAYOUT_SCALE * SCALE,
            w * LAYOUT_SCALE * SCALE,
            h * LAYOUT_SCALE * SCALE,
            text,
            kind
        ))

    scaled_width = int(WIDTH * LAYOUT_SCALE)
    canvas_width = int(scaled_width * SCALE)
    
    max_y = max(node[2] + node[4] for node in scaled_nodes)
    canvas_height = int(max_y + int(60 * LAYOUT_SCALE * SCALE))
    
    image = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(image)
    boxes = {}
    kinds = {}

    for key, x, y, w, h, text, kind in scaled_nodes:
        box = (x, y, w, h)
        boxes[key] = box
        kinds[key] = kind
        draw_node(draw, box, text, kind)

    for item in arrows:
        start, end = item[0], item[1]
        start_side = item[2] if len(item) > 2 else "bottom"
        end_side = item[3] if len(item) > 3 else "top"
        label = item[4] if len(item) > 4 else None
        x_override = item[5] if len(item) > 5 else None
        
        if x_override is not None:
            x_override = x_override * LAYOUT_SCALE * SCALE

        start_point = side_point(boxes[start], start_side, kinds[start])
        end_point = side_point(boxes[end], end_side, kinds[end])
        
        if x_override is not None:
            points = [
                start_point,
                (x_override, start_point[1]),
                (x_override, end_point[1]),
                end_point
            ]
            draw_arrow_path(draw, points)
        else:
            draw_arrow(draw, start_point, end_point)

        if label:
            # We want to position the label such that it NEVER touches the line.
            # We also do NOT draw a white background mask, so the flow line remains continuous and clean.
            if x_override is not None:
                # The first segment is horizontal.
                if start_side == "left":
                    lx = start_point[0] - 35 * LAYOUT_SCALE * SCALE
                    ly = start_point[1] - 8 * LAYOUT_SCALE * SCALE
                    anchor = "mb"  # Middle-Bottom
                elif start_side == "right":
                    lx = start_point[0] + 35 * LAYOUT_SCALE * SCALE
                    ly = start_point[1] - 8 * LAYOUT_SCALE * SCALE
                    anchor = "mb"  # Middle-Bottom
                else:
                    lx = start_point[0]
                    ly = start_point[1] - 15 * LAYOUT_SCALE * SCALE
                    anchor = "mb"
            else:
                # Straight line.
                dx = end_point[0] - start_point[0]
                dy = end_point[1] - start_point[1]
                if abs(dx) < 1e-3:
                    # Vertical straight line. Place label to the right of the vertical line,
                    # slightly below the starting point (the bottom of the node).
                    lx = start_point[0] + 12 * LAYOUT_SCALE * SCALE
                    ly = start_point[1] + 20 * LAYOUT_SCALE * SCALE
                    anchor = "lm"  # Left-Middle
                elif abs(dy) < 1e-3:
                    # Horizontal straight line. Place above the line, centered.
                    lx = (start_point[0] + end_point[0]) / 2
                    ly = start_point[1] - 8 * LAYOUT_SCALE * SCALE
                    anchor = "mb"  # Middle-Bottom
                else:
                    # Diagonal line (fallback).
                    lx = (start_point[0] + end_point[0]) / 2 + 12 * LAYOUT_SCALE * SCALE
                    ly = (start_point[1] + end_point[1]) / 2
                    anchor = "lm"

            draw.text((lx, ly), label, fill="#000000", font=FONT_SMALL, anchor=anchor)

    final_width = scaled_width
    final_height = canvas_height // SCALE
    image_resized = image.resize((final_width, final_height), Image.Resampling.LANCZOS)
    image_resized.save(OUT_DIR / filename)


def bubble_flagged():
    nodes = [
        ("start", 375, 40, 450, 120, "Начало", "terminal"),
        ("input", 375, 240, 450, 150, "Ввод массива A\nи размера n", "input_output"),
        ("check_n", 375, 470, 450, 150, "n < 2?", "decision"),
        ("init", 375, 700, 450, 180, "i = 0; swapped = true\ncomparisons = 0; swaps = 0", "process"),
        ("outer_loop", 375, 960, 450, 150, "i < n - 1\nи swapped = true?", "decision"),
        ("reset", 375, 1190, 450, 150, "swapped = false\nj = 0", "process"),
        ("inner_loop", 375, 1420, 450, 150, "j < n - i - 1?", "decision"),
        ("inc_comp", 375, 1650, 450, 150, "comparisons = comparisons + 1", "process"),
        ("cmp_elements", 375, 1880, 450, 150, "A[j] > A[j + 1]?", "decision"),
        ("swap_block", 375, 2110, 450, 180, "Обмен A[j] и A[j + 1]\nswaps = swaps + 1\nswapped = true", "process"),
        ("inc_j", 375, 2370, 450, 150, "j = j + 1", "process"),
        ("inc_i", 100, 1420, 200, 150, "i = i + 1", "process"),
        ("output", 375, 2620, 450, 150, "Вывод A, comparisons, swaps", "input_output"),
        ("end", 375, 2850, 450, 120, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "input"),
        ("input", "check_n"),
        ("check_n", "init", "bottom", "top", "нет"),
        ("check_n", "output", "right", "right", "да", 1100),
        ("init", "outer_loop"),
        ("outer_loop", "reset", "bottom", "top", "да"),
        ("outer_loop", "output", "right", "right", "нет", 1100),
        ("reset", "inner_loop"),
        ("inner_loop", "inc_comp", "bottom", "top", "да"),
        ("inner_loop", "inc_i", "left", "right", "нет"),
        ("inc_i", "outer_loop", "left", "left", None, 40),
        ("inc_comp", "cmp_elements"),
        ("cmp_elements", "swap_block", "bottom", "top", "да"),
        ("cmp_elements", "inc_j", "left", "left", "нет", 200),
        ("swap_block", "inc_j"),
        ("inc_j", "inner_loop", "right", "right", None, 1000),
    ]
    draw_chart("bubble_flagged_flowchart.png", nodes, arrows)


def shaker():
    nodes = [
        ("start", 375, 40, 450, 120, "Начало", "terminal"),
        ("init", 375, 240, 450, 150, "left = 0, right = n - 1, swapped = true", "process"),
        ("outer", 375, 470, 450, 150, "swapped и left < right?", "decision"),
        ("forward", 375, 700, 450, 150, "Проход слева направо: максимум уходит в конец", "process"),
        ("any", 375, 930, 450, 150, "Были обмены?", "decision"),
        ("right", 375, 1160, 450, 150, "right = right - 1", "process"),
        ("backward", 375, 1390, 450, 150, "Проход справа налево: минимум уходит в начало", "process"),
        ("left", 375, 1620, 450, 150, "left = left + 1", "process"),
        ("end", 375, 1850, 450, 120, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "init"),
        ("init", "outer"),
        ("outer", "forward", "bottom", "top", "да"),
        ("forward", "any"),
        ("any", "right", "bottom", "top", "да"),
        ("right", "backward"),
        ("backward", "left"),
        ("left", "outer", "left", "left", None, 200),
        ("outer", "end", "right", "right", "нет", 1000),
        ("any", "end", "right", "right", "нет", 1000),
    ]
    draw_chart("shaker_flowchart.png", nodes, arrows)


def odd_even():
    nodes = [
        ("start", 375, 40, 450, 120, "Начало", "terminal"),
        ("init", 375, 240, 450, 150, "sorted = false", "process"),
        ("outer", 375, 470, 450, 150, "sorted == false?", "decision"),
        ("set", 375, 700, 450, 150, "sorted = true", "process"),
        ("odd", 375, 930, 450, 180, "Нечётная фаза: сравнение и обмен пар (1,2), (3,4), ...\nПри обмене: sorted = false", "process"),
        ("even", 375, 1190, 450, 180, "Чётная фаза: сравнение и обмен пар (0,1), (2,3), ...\nПри обмене: sorted = false", "process"),
        ("end", 375, 1450, 450, 120, "Конец", "terminal"),
    ]
    arrows = [
        ("start", "init"),
        ("init", "outer"),
        ("outer", "set", "bottom", "top", "да"),
        ("set", "odd"),
        ("odd", "even"),
        ("even", "outer", "left", "left", None, 200),
        ("outer", "end", "right", "right", "нет", 1000),
    ]
    draw_chart("odd_even_flowchart.png", nodes, arrows)


def main_program():
    nodes = [
        ("start", 375, 40, 450, 120, "Начало", "terminal"),
        ("const", 375, 240, 450, 180, "Задать размеры, типы данных, алгоритмы и диапазон значений", "process"),
        ("csv", 375, 500, 450, 150, "Открыть results.csv и записать заголовок", "input_output"),
        ("size", 375, 730, 450, 150, "Есть следующий размер n?", "decision"),
        ("type", 375, 960, 450, 150, "Есть следующий тип данных?", "decision"),
        ("gen", 375, 1190, 450, 150, "Сгенерировать исходный массив", "process"),
        ("algo", 375, 1420, 450, 150, "Есть следующий алгоритм?", "decision"),
        ("copy", 375, 1650, 450, 150, "Скопировать массив через memcpy", "process"),
        ("measure", 375, 1880, 450, 150, "Отсортировать, измерить метрики и время", "process"),
        ("write", 375, 2110, 450, 150, "Записать строку результатов в CSV", "input_output"),
        ("end", 375, 2340, 450, 120, "Конец", "terminal"),
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
        ("write", "algo", "left", "left", None, 240),
        ("algo", "type", "right", "right", "нет", 960),
        ("type", "size", "left", "left", "нет", 120),
        ("size", "end", "right", "right", "нет", 1080),
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
