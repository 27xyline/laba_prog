#!/usr/bin/env python3
import csv
from pathlib import Path


FLOWCHART_DIR = Path("flowcharts")
TABLE_PATH = Path("results_table.typ")
CSV_PATH = Path("results.csv")


def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def node(x, y, w, h, text, rounded=False):
    rx = 20 if rounded else 6
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="#f8fbff" stroke="#1f4e79" stroke-width="1.5" />\n'
        f'<text x="{x + w / 2}" y="{y + h / 2 + 5}" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="13" fill="#111">{esc(text)}</text>'
    )


def arrow(x1, y1, x2, y2):
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="#222" stroke-width="1.4" marker-end="url(#arrow)" />'
    )


def label(x, y, text):
    return (
        f'<text x="{x}" y="{y}" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="12" fill="#333">{esc(text)}</text>'
    )


def save_flowchart(name, title, steps):
    width = 860
    step_h = 56
    gap = 28
    top = 58
    height = top + len(steps) * step_h + (len(steps) - 1) * gap + 36
    x = 230
    w = 400

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#222" /></marker></defs>',
        '<rect width="100%" height="100%" fill="#ffffff" />',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#111">{esc(title)}</text>',
    ]

    centers = []
    for index, step in enumerate(steps):
        y = top + index * (step_h + gap)
        centers.append((x + w / 2, y + step_h / 2))
        parts.append(node(x, y, w, step_h, step, rounded=index in (0, len(steps) - 1)))
        if index > 0:
            prev_y = top + (index - 1) * (step_h + gap)
            parts.append(arrow(x + w / 2, prev_y + step_h, x + w / 2, y))

    parts.append("</svg>")
    (FLOWCHART_DIR / name).write_text("\n".join(parts), encoding="utf-8")


def make_flowcharts():
    FLOWCHART_DIR.mkdir(exist_ok=True)

    save_flowchart(
        "bubble_flag.svg",
        "Пузырек с флагом",
        [
            "Начало",
            "Задать конец неотсортированной части",
            "Выполнить проход по соседним парам",
            "Сравнить элементы и при необходимости обменять",
            "Если обменов не было, завершить сортировку",
            "Иначе уменьшить правую границу",
            "Конец",
        ],
    )
    save_flowchart(
        "shaker.svg",
        "Шейкерная сортировка",
        [
            "Начало",
            "Задать левую и правую границы",
            "Прямой проход переносит максимум вправо",
            "Если обменов не было, завершить сортировку",
            "Обратный проход переносит минимум влево",
            "Сузить границы диапазона",
            "Конец",
        ],
    )
    save_flowchart(
        "odd_even.svg",
        "Чет-нечетная сортировка",
        [
            "Начало",
            "Считать массив неотсортированным",
            "Четная фаза: сравнить пары 0-1, 2-3, ...",
            "Нечетная фаза: сравнить пары 1-2, 3-4, ...",
            "Если были обмены, повторить обе фазы",
            "Если обменов не было, завершить сортировку",
            "Конец",
        ],
    )
    save_flowchart(
        "program.svg",
        "Основная программа",
        [
            "Начало",
            "Открыть results.csv и записать заголовок",
            "Перебрать размеры и типы данных",
            "Сгенерировать исходный массив",
            "Для каждого алгоритма скопировать массив",
            "Измерить сортировку и собрать метрики",
            "Проверить сортировку и записать строку CSV",
            "Конец",
        ],
    )


def make_results_table():
    with CSV_PATH.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    lines = [
        "#table(",
        "  columns: (auto, auto, auto, auto, auto, auto),",
        "  inset: 4pt,",
        "  [*Size*], [*DataType*], [*Algorithm*], [*Comparisons*], [*Swaps*], [*Time_us*],",
    ]

    for row in rows:
        lines.append(
            f"  [{row['Size']}], [{row['DataType']}], [{row['Algorithm']}], "
            f"[{row['Comparisons']}], [{row['Swaps']}], [{row['Time_us']}],"
        )

    lines.append(")")
    TABLE_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    make_flowcharts()
    make_results_table()
    print("Report assets created")


if __name__ == "__main__":
    main()
