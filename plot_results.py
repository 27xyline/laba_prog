import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "results.csv"
GRAPHICS_DIR = ROOT / "graphics"
TABLE_PATH = ROOT / "results_table.typ"

WIDTH = 1800
HEIGHT = 1080
MARGIN_LEFT = 170
MARGIN_RIGHT = 70
MARGIN_TOP = 180
MARGIN_BOTTOM = 135

ALGORITHM_LABELS = {
    "bubble_flagged": "Пузырёк с флагом",
    "shaker": "Шейкерная",
    "odd_even": "Чёт-нечёт",
}

DATA_TYPE_LABELS = {
    "random": "случайные данные",
    "nearly_sorted": "почти отсортированные данные",
    "reversed": "обратный порядок",
}

COLORS = {
    "bubble_flagged": "#2563eb",
    "shaker": "#059669",
    "odd_even": "#dc2626",
}

DATA_TYPE_ORDER = ("random", "nearly_sorted", "reversed")
ALGORITHM_ORDER = ("bubble_flagged", "shaker", "odd_even")
BACKGROUND = "#fbfbfd"
GRID_COLOR = "#e7eaf0"
AXIS_COLOR = "#28323f"
TEXT_COLOR = "#111827"


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


FONT_TITLE = font(38, bold=True)
FONT_TEXT = font(25)
FONT_SMALL = font(21)
FONT_TINY = font(18)


def read_csv(path):
    rows = []
    with open(path, encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            row["Size"] = int(row["Size"])
            row["Comparisons"] = int(row["Comparisons"])
            row["Swaps"] = int(row["Swaps"])
            row["Time_us"] = int(row["Time_us"])
            rows.append(row)
    return rows


def unique_values(rows, key):
    return sorted({row[key] for row in rows})


def nice_ticks(max_value, count=5):
    if max_value <= 0:
        return [0, 1]
    raw_step = max_value / count
    power = 10 ** (len(str(int(raw_step))) - 1)
    for factor in (1, 2, 5, 10):
        step = factor * power
        if step >= raw_step:
            break
    top = ((max_value + step - 1) // step) * step
    return [int(i * step) for i in range(int(top // step) + 1)]


def ordered_values(rows, key, preferred_order):
    values = {row[key] for row in rows}
    ordered = [value for value in preferred_order if value in values]
    ordered.extend(sorted(values - set(ordered)))
    return ordered


def format_number(value):
    return f"{int(value):,}".replace(",", " ")


def draw_text_centered(draw, xy, text, fill, font_obj):
    draw.text(xy, text, fill=fill, font=font_obj, anchor="mm")


def draw_rotated_label(image, text, center, font_obj, fill):
    bbox = font_obj.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    label = Image.new("RGBA", (text_width + 24, text_height + 24), (255, 255, 255, 0))
    label_draw = ImageDraw.Draw(label)
    label_draw.text((12 - bbox[0], 12 - bbox[1]), text, fill=fill, font=font_obj)
    rotated = label.rotate(90, expand=True)
    x = int(center[0] - rotated.width / 2)
    y = int(center[1] - rotated.height / 2)
    image.paste(rotated, (x, y), rotated)


def x_position(size, x_values, plot_left, plot_width):
    import math

    min_x = math.log10(min(x_values))
    max_x = math.log10(max(x_values))
    return plot_left + (math.log10(size) - min_x) / (max_x - min_x) * plot_width


def draw_line_chart(rows, metric, ylabel, output_name):
    x_values = [10, 100, 500, 1000, 2000, 5000, 10000]

    GRAPHICS_DIR.mkdir(exist_ok=True)

    for data_type in ordered_values(rows, "DataType", DATA_TYPE_ORDER):
        image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        draw = ImageDraw.Draw(image)

        plot_left = MARGIN_LEFT
        plot_top = MARGIN_TOP
        plot_right = WIDTH - MARGIN_RIGHT
        plot_bottom = HEIGHT - MARGIN_BOTTOM
        plot_width = plot_right - plot_left
        plot_height = plot_bottom - plot_top

        title = f"{ylabel}: {DATA_TYPE_LABELS[data_type]}"
        draw_text_centered(draw, (WIDTH // 2, 58), title, TEXT_COLOR, FONT_TITLE)

        filtered = [row for row in rows if row["DataType"] == data_type]
        max_y = max(row[metric] for row in filtered)
        ticks = nice_ticks(max_y)
        max_tick = max(ticks)

        for tick in ticks:
            y = plot_bottom - (tick / max_tick) * plot_height if max_tick else plot_bottom
            draw.line((plot_left, y, plot_right, y), fill=GRID_COLOR, width=2)

        for size in x_values:
            x = x_position(size, x_values, plot_left, plot_width)
            draw.line((x, plot_top, x, plot_bottom), fill="#f0f2f6", width=1)

        draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=AXIS_COLOR, width=3)
        draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=AXIS_COLOR, width=3)
        draw.line((plot_right, plot_top, plot_right, plot_bottom), fill="#d8dde6", width=1)
        draw.line((plot_left, plot_top, plot_right, plot_top), fill="#d8dde6", width=1)

        for tick in ticks:
            y = plot_bottom - (tick / max_tick) * plot_height if max_tick else plot_bottom
            draw.line((plot_left - 8, y, plot_left, y), fill=AXIS_COLOR, width=2)
            draw.text((plot_left - 16, y), format_number(tick), fill=TEXT_COLOR, font=FONT_SMALL, anchor="rm")

        for size in x_values:
            x = x_position(size, x_values, plot_left, plot_width)
            draw.line((x, plot_bottom, x, plot_bottom + 10), fill=AXIS_COLOR, width=2)
            draw.text((x, plot_bottom + 22), format_number(size), fill=TEXT_COLOR, font=FONT_SMALL, anchor="ma")

        draw_text_centered(draw, ((plot_left + plot_right) / 2, HEIGHT - 52), "Размер массива n", TEXT_COLOR, FONT_TEXT)
        draw_rotated_label(image, ylabel, (58, (plot_top + plot_bottom) / 2), FONT_TEXT, TEXT_COLOR)

        for algorithm in ordered_values(rows, "Algorithm", ALGORITHM_ORDER):
            points = [
                row
                for row in rows
                if row["DataType"] == data_type and row["Algorithm"] == algorithm
            ]
            points.sort(key=lambda row: row["Size"])

            coords = []
            for row in points:
                x = x_position(row["Size"], x_values, plot_left, plot_width)
                y = plot_bottom - (row[metric] / max_tick) * plot_height if max_tick else plot_bottom
                coords.append((x, y))

            color = COLORS[algorithm]
            draw.line(coords, fill=color, width=5, joint="curve")
            for x, y in coords:
                draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color, outline="white", width=3)

        legend_items = ordered_values(rows, "Algorithm", ALGORITHM_ORDER)
        legend_width = 0
        item_sizes = []
        for algorithm in legend_items:
            text = ALGORITHM_LABELS[algorithm]
            bbox = draw.textbbox((0, 0), text, font=FONT_SMALL)
            width = 52 + (bbox[2] - bbox[0]) + 38
            item_sizes.append(width)
            legend_width += width
        legend_x = (WIDTH - legend_width) / 2
        legend_y = 112
        for index, algorithm in enumerate(legend_items):
            color = COLORS[algorithm]
            x0 = legend_x + sum(item_sizes[:index])
            draw.line((x0, legend_y, x0 + 36, legend_y), fill=color, width=5)
            draw.ellipse((x0 + 14, legend_y - 7, x0 + 28, legend_y + 7), fill=color, outline="white", width=3)
            draw.text((x0 + 50, legend_y), ALGORITHM_LABELS[algorithm], fill=TEXT_COLOR, font=FONT_SMALL, anchor="lm")

        note = "Шкала размера массива логарифмическая"
        draw.text((plot_right, HEIGHT - 52), note, fill="#6b7280", font=FONT_TINY, anchor="rm")
        image.save(GRAPHICS_DIR / f"{output_name}_{data_type}.png")


def typst_cell(value):
    text = str(value).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return f"[{text}]"


def write_results_table(rows):
    lines = [
        "#table(",
        "  columns: (auto, auto, auto, auto, auto, auto),",
        "  inset: 4pt,",
        "  align: (center, left, left, right, right, right),",
        "  table.header([Размер], [Тип данных], [Алгоритм], [Сравнения], [Обмены], [Время, мкс]),",
    ]

    for row in rows:
        values = [
            row["Size"],
            row["DataType"],
            row["Algorithm"],
            row["Comparisons"],
            row["Swaps"],
            row["Time_us"],
        ]
        lines.append("  " + ", ".join(typst_cell(value) for value in values) + ",")

    lines.append(")")
    TABLE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if not CSV_PATH.exists():
        raise SystemExit("Не найден файл results.csv")

    rows = read_csv(CSV_PATH)
    draw_line_chart(rows, "Time_us", "Время работы, мкс", "time")
    draw_line_chart(rows, "Comparisons", "Количество сравнений", "comparisons")
    draw_line_chart(rows, "Swaps", "Количество обменов", "swaps")
    write_results_table(rows)
    print("Графики и таблица для Typst построены.")


if __name__ == "__main__":
    main()
