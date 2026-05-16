# Лабораторная работа, вариант 3

## Сборка и запуск

```sh
g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp -o lab_sort
./lab_sort
python3 plot_results.py
python3 make_report_assets.py
```

После запуска будут созданы:

- `results.csv` — таблица измерений;
- `plots/*.svg` — графики для отчета.
- `flowcharts/*.svg` — блок-схемы для отчета;
- `results_table.typ` — таблица результатов для Typst.

## Отчет

Отчет находится в `report.typ`. Если установлен Typst, PDF можно собрать командой:

```sh
typst compile report.typ
```
