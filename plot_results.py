#!/usr/bin/env python3
import csv
import math
from pathlib import Path


CSV_PATH = Path("results.csv")
PLOTS_DIR = Path("plots")
METRICS = [
    ("Time_us", "Время, мкс", "time"),
    ("Comparisons", "Сравнения", "comparisons"),
    ("Swaps", "Обмены", "swaps"),
]
DATA_TYPES = ["random", "nearly_sorted", "reversed"]
ALGORITHMS = ["bubble_flag", "shaker", "odd_even"]
COLORS = {
    "bubble_flag": "#1f77b4",
    "shaker": "#d62728",
    "odd_even": "#2ca02c",
}


def read_rows():
    with CSV_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        return [
            {
                "Size": int(row["Size"]),
                "DataType": row["DataType"],
                "Algorithm": row["Algorithm"],
                "Comparisons": int(row["Comparisons"]),
                "Swaps": int(row["Swaps"]),
                "Time_us": int(row["Time_us"]),
            }
            for row in reader
        ]


def nice_max(value):
    if value <= 0:
        return 1
    power = 10 ** math.floor(math.log10(value))
    fraction = value / power
    if fraction <= 1:
        nice = 1
    elif fraction <= 2:
        nice = 2
    elif fraction <= 5:
        nice = 5
    else:
        nice = 10
    return nice * power


def polyline(points, color):
    return (
        f'<polyline fill="none" stroke="{color}" stroke-width="2.5" '
        f'stroke-linejoin="round" stroke-linecap="round" points="{points}" />'
    )


def text(x, y, value, size=13, anchor="middle", weight="400"):
    escaped = (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="#222">{escaped}</text>'
    )


def format_number(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}k"
    return str(value)


def build_chart(rows, data_type, metric, ylabel, stem):
    width, height = 980, 560
    left, right, top, bottom = 86, 28, 58, 78
    plot_w = width - left - right
    plot_h = height - top - bottom

    subset = [row for row in rows if row["DataType"] == data_type]
    sizes = sorted({row["Size"] for row in subset})
    max_value = nice_max(max(row[metric] for row in subset))

    def sx(size):
        if len(sizes) == 1:
            return left + plot_w / 2
        index = sizes.index(size)
        return left + index * plot_w / (len(sizes) - 1)

    def sy(value):
        return top + plot_h - (value / max_value) * plot_h

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff" />',
        text(width / 2, 30, f"{ylabel} от размера массива: {data_type}", 20, "middle", "700"),
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#222" stroke-width="1.5" />',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#222" stroke-width="1.5" />',
    ]

    for tick in range(6):
        value = max_value * tick / 5
        y = sy(value)
        svg.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#e5e5e5" />')
        svg.append(text(left - 12, y + 4, format_number(round(value)), 12, "end"))

    for size in sizes:
        x = sx(size)
        svg.append(f'<line x1="{x:.2f}" y1="{top + plot_h}" x2="{x:.2f}" y2="{top + plot_h + 6}" stroke="#222" />')
        svg.append(text(x, top + plot_h + 24, size, 12))

    for algorithm in ALGORITHMS:
        series = sorted(
            [row for row in subset if row["Algorithm"] == algorithm],
            key=lambda row: row["Size"],
        )
        points = " ".join(f'{sx(row["Size"]):.2f},{sy(row[metric]):.2f}' for row in series)
        svg.append(polyline(points, COLORS[algorithm]))

        for row in series:
            svg.append(
                f'<circle cx="{sx(row["Size"]):.2f}" cy="{sy(row[metric]):.2f}" r="4" '
                f'fill="{COLORS[algorithm]}" />'
            )

    legend_x = left + 20
    legend_y = top + 18
    for index, algorithm in enumerate(ALGORITHMS):
        y = legend_y + index * 24
        svg.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 30}" y2="{y}" stroke="{COLORS[algorithm]}" stroke-width="3" />')
        svg.append(text(legend_x + 40, y + 4, algorithm, 13, "start"))

    svg.append(text(width / 2, height - 22, "Размер массива n", 14, "middle", "700"))
    svg.append(
        f'<text x="24" y="{top + plot_h / 2}" font-family="Arial, sans-serif" '
        f'font-size="14" font-weight="700" text-anchor="middle" fill="#222" '
        f'transform="rotate(-90 24 {top + plot_h / 2})">{ylabel}</text>'
    )
    svg.append("</svg>")

    output_path = PLOTS_DIR / f"{stem}_{data_type}.svg"
    output_path.write_text("\n".join(svg), encoding="utf-8")


def main():
    rows = read_rows()
    PLOTS_DIR.mkdir(exist_ok=True)

    for metric, ylabel, stem in METRICS:
        for data_type in DATA_TYPES:
            build_chart(rows, data_type, metric, ylabel, stem)

    print(f"Charts created in {PLOTS_DIR}/")


if __name__ == "__main__":
    main()
