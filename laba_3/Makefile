CXX ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Werror -pedantic

SOURCES = image.cpp graphics.cpp truchet.cpp
HEADERS = image.hpp graphics.hpp truchet.hpp
BUILD = build

all: $(BUILD)/raster

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/raster: main.cpp $(SOURCES) $(HEADERS) | $(BUILD)
	$(CXX) $(CXXFLAGS) main.cpp $(SOURCES) -o $@

clean:
	rm -rf $(BUILD)

.PHONY: all clean
