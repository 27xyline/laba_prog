#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

using namespace std;

enum class DataType {
    random,
    nearly_sorted,
    reversed,
};

struct Metrics {
    uint64_t comparisons = 0;
    uint64_t swaps = 0;
};

using SortFunction = void (*)(vector<int>&, Metrics&);

constexpr int MIN_VALUE = -32000;
constexpr int MAX_VALUE = 32000;
const vector<int> SIZES = {10, 100, 500, 1000, 2000, 5000, 10000};
const vector<DataType> DATA_TYPES = {
    DataType::random,
    DataType::nearly_sorted,
    DataType::reversed,
};

string data_type_name(DataType type) {
    switch (type) {
        case DataType::random:
            return "random";
        case DataType::nearly_sorted:
            return "nearly_sorted";
        case DataType::reversed:
            return "reversed";
    }
    return "unknown";
}

vector<int> random_array(int size, mt19937& rng) {
    uniform_int_distribution<int> dist(MIN_VALUE, MAX_VALUE);
    vector<int> values(size);

    for (int& value : values) {
        value = dist(rng);
    }

    return values;
}

vector<int> generate_array(int size, DataType type, mt19937& rng) {
    vector<int> values = random_array(size, rng);

    if (type == DataType::random) {
        return values;
    }

    sort(values.begin(), values.end());

    if (type == DataType::nearly_sorted) {
        uniform_int_distribution<int> index_dist(0, size - 1);
        const int swaps_count = size / 10;

        for (int i = 0; i < swaps_count; ++i) {
            const int first = index_dist(rng);
            const int second = index_dist(rng);
            swap(values[first], values[second]);
        }
    } else if (type == DataType::reversed) {
        reverse(values.begin(), values.end());
    }

    return values;
}

void counted_swap(int& first, int& second, Metrics& metrics) {
    swap(first, second);
    ++metrics.swaps;
}

bool greater_than(int first, int second, Metrics& metrics) {
    ++metrics.comparisons;
    return first > second;
}

void bubble_flag_sort(vector<int>& values, Metrics& metrics) {
    if (values.size() < 2) {
        return;
    }

    for (size_t unsorted_end = values.size(); unsorted_end > 1; --unsorted_end) {
        bool swapped = false;

        for (size_t i = 1; i < unsorted_end; ++i) {
            if (greater_than(values[i - 1], values[i], metrics)) {
                counted_swap(values[i - 1], values[i], metrics);
                swapped = true;
            }
        }

        if (!swapped) {
            break;
        }
    }
}

void shaker_sort(vector<int>& values, Metrics& metrics) {
    if (values.size() < 2) {
        return;
    }

    size_t left = 0;
    size_t right = values.size() - 1;
    bool swapped = true;

    while (swapped) {
        swapped = false;

        for (size_t i = left; i < right; ++i) {
            if (greater_than(values[i], values[i + 1], metrics)) {
                counted_swap(values[i], values[i + 1], metrics);
                swapped = true;
            }
        }

        if (!swapped) {
            break;
        }

        --right;
        swapped = false;

        for (size_t i = right; i > left; --i) {
            if (greater_than(values[i - 1], values[i], metrics)) {
                counted_swap(values[i - 1], values[i], metrics);
                swapped = true;
            }
        }

        ++left;
    }
}

void odd_even_sort(vector<int>& values, Metrics& metrics) {
    if (values.size() < 2) {
        return;
    }

    bool sorted = false;

    while (!sorted) {
        sorted = true;

        for (size_t i = 1; i < values.size(); i += 2) {
            if (greater_than(values[i - 1], values[i], metrics)) {
                counted_swap(values[i - 1], values[i], metrics);
                sorted = false;
            }
        }

        for (size_t i = 2; i < values.size(); i += 2) {
            if (greater_than(values[i - 1], values[i], metrics)) {
                counted_swap(values[i - 1], values[i], metrics);
                sorted = false;
            }
        }
    }
}

struct Algorithm {
    string name;
    SortFunction sort;
};

const vector<Algorithm> ALGORITHMS = {
    {"bubble_flag", bubble_flag_sort},
    {"shaker", shaker_sort},
    {"odd_even", odd_even_sort},
};

int main() {
    mt19937 rng(42);
    ofstream output("results.csv");

    if (!output) {
        cerr << "Cannot open results.csv for writing\n";
        return 1;
    }

    output << "Size;DataType;Algorithm;Comparisons;Swaps;Time_us\n";

    for (const int size : SIZES) {
        for (const DataType data_type : DATA_TYPES) {
            const vector<int> source = generate_array(size, data_type, rng);

            for (const Algorithm& algorithm : ALGORITHMS) {
                vector<int> values = source;
                Metrics metrics;

                const auto started_at = chrono::high_resolution_clock::now();
                algorithm.sort(values, metrics);
                const auto finished_at = chrono::high_resolution_clock::now();

                if (!is_sorted(values.begin(), values.end())) {
                    cerr << "Sort failed: " << algorithm.name << ", "
                              << data_type_name(data_type) << ", n=" << size << '\n';
                    return 2;
                }

                const auto time_us = chrono::duration_cast<chrono::microseconds>(
                    finished_at - started_at
                ).count();

                output << size << ';'
                       << data_type_name(data_type) << ';'
                       << algorithm.name << ';'
                       << metrics.comparisons << ';'
                       << metrics.swaps << ';'
                       << time_us << '\n';
            }
        }
    }

    cout << "results.csv created\n";
    return 0;
}
