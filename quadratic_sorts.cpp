#include <algorithm>
#include <chrono>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

using namespace std;

struct Stats {
    long long comparisons = 0;
    long long swaps = 0;
    long long time_us = 0;
};

enum class DataType {
    Random,
    NearlySorted,
    Reversed
};

enum class Algorithm {
    BubbleFlagged,
    Shaker,
    OddEven
};

string toString(DataType type) {
    switch (type) {
        case DataType::Random:
            return "random";
        case DataType::NearlySorted:
            return "nearly_sorted";
        case DataType::Reversed:
            return "reversed";
    }
    return "";
}

string toString(Algorithm algorithm) {
    switch (algorithm) {
        case Algorithm::BubbleFlagged:
            return "bubble_flagged";
        case Algorithm::Shaker:
            return "shaker";
        case Algorithm::OddEven:
            return "odd_even";
    }
    return "";
}

vector<int> generateData(size_t n, DataType type, mt19937& rng) {
    uniform_int_distribution<int> valueDist(-32000, 32000);
    vector<int> data(n);

    for (size_t i = 0; i < n; ++i) {
        data[i] = valueDist(rng);
    }

    if (type == DataType::NearlySorted || type == DataType::Reversed) {
        sort(data.begin(), data.end());
    }

    if (type == DataType::NearlySorted && n > 1) {
        uniform_int_distribution<size_t> indexDist(0, n - 1);
        const size_t swapCount = max<size_t>(1, n / 10);

        for (size_t i = 0; i < swapCount; ++i) {
            const size_t left = indexDist(rng);
            const size_t right = indexDist(rng);
            swap(data[left], data[right]);
        }
    } else if (type == DataType::Reversed) {
        reverse(data.begin(), data.end());
    }

    return data;
}

void bubbleFlagged(int* data, size_t n, Stats& stats) {
    bool swapped = true;

    for (size_t i = 0; i < n && swapped; ++i) {
        swapped = false;

        for (size_t j = 0; j + 1 < n - i; ++j) {
            ++stats.comparisons;
            if (data[j] > data[j + 1]) {
                swap(data[j], data[j + 1]);
                ++stats.swaps;
                swapped = true;
            }
        }
    }
}

void shakerSort(int* data, size_t n, Stats& stats) {
    if (n < 2) {
        return;
    }

    size_t left = 0;
    size_t right = n - 1;
    bool swapped = true;

    while (swapped && left < right) {
        swapped = false;

        for (size_t i = left; i < right; ++i) {
            ++stats.comparisons;
            if (data[i] > data[i + 1]) {
                swap(data[i], data[i + 1]);
                ++stats.swaps;
                swapped = true;
            }
        }

        if (!swapped) {
            break;
        }

        --right;
        swapped = false;

        for (size_t i = right; i > left; --i) {
            ++stats.comparisons;
            if (data[i - 1] > data[i]) {
                swap(data[i - 1], data[i]);
                ++stats.swaps;
                swapped = true;
            }
        }

        ++left;
    }
}

void oddEvenSort(int* data, size_t n, Stats& stats) {
    bool sorted = false;

    while (!sorted) {
        sorted = true;

        for (size_t i = 1; i + 1 < n; i += 2) {
            ++stats.comparisons;
            if (data[i] > data[i + 1]) {
                swap(data[i], data[i + 1]);
                ++stats.swaps;
                sorted = false;
            }
        }

        for (size_t i = 0; i + 1 < n; i += 2) {
            ++stats.comparisons;
            if (data[i] > data[i + 1]) {
                swap(data[i], data[i + 1]);
                ++stats.swaps;
                sorted = false;
            }
        }
    }
}

bool isSortedAscending(const vector<int>& data) {
    for (size_t i = 1; i < data.size(); ++i) {
        if (data[i - 1] > data[i]) {
            return false;
        }
    }
    return true;
}

Stats runSort(const vector<int>& source, Algorithm algorithm) {
    vector<int> working(source.size());
    memcpy(working.data(), source.data(), source.size() * sizeof(int));

    Stats stats;
    const auto start = chrono::high_resolution_clock::now();

    switch (algorithm) {
        case Algorithm::BubbleFlagged:
            bubbleFlagged(working.data(), working.size(), stats);
            break;
        case Algorithm::Shaker:
            shakerSort(working.data(), working.size(), stats);
            break;
        case Algorithm::OddEven:
            oddEvenSort(working.data(), working.size(), stats);
            break;
    }

    const auto finish = chrono::high_resolution_clock::now();
    stats.time_us = chrono::duration_cast<chrono::microseconds>(finish - start).count();

    if (!isSortedAscending(working)) {
        cerr << "Ошибка: массив не отсортирован алгоритмом "
             << toString(algorithm) << '\n';
    }

    return stats;
}

int main() {
    const vector<size_t> sizes = {10, 100, 500, 1000, 2000, 5000, 10000};
    const vector<DataType> dataTypes = {
        DataType::Random,
        DataType::NearlySorted,
        DataType::Reversed
    };
    const vector<Algorithm> algorithms = {
        Algorithm::BubbleFlagged,
        Algorithm::Shaker,
        Algorithm::OddEven
    };

    mt19937 rng(42);
    ofstream output("results.csv");

    if (!output) {
        cerr << "Не удалось открыть файл results.csv\n";
        return 1;
    }

    output << "Size;DataType;Algorithm;Comparisons;Swaps;Time_us\n";

    for (size_t size : sizes) {
        for (DataType dataType : dataTypes) {
            const vector<int> source = generateData(size, dataType, rng);

            for (Algorithm algorithm : algorithms) {
                const Stats stats = runSort(source, algorithm);

                output << size << ';'
                       << toString(dataType) << ';'
                       << toString(algorithm) << ';'
                       << stats.comparisons << ';'
                       << stats.swaps << ';'
                       << stats.time_us << '\n';

                cout << "n=" << size
                     << ", type=" << toString(dataType)
                     << ", algorithm=" << toString(algorithm)
                     << " done\n";
            }
        }
    }

    cout << "Готово. Результаты записаны в results.csv\n";
    return 0;
}
