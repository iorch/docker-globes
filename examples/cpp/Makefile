# Makefile for CEvNS C++ Examples

# Compiler and flags
CXX = g++
CXXFLAGS = -O2 -Wall -std=c++11
LIBS = -lglobes -lgsl -lgslcblas -lm

# Targets
TARGETS = basic_rate_calculator mc_event_generator

# Default target: build all
all: $(TARGETS)

# Build basic_rate_calculator
basic_rate_calculator: basic_rate_calculator.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)
	@echo "Built: basic_rate_calculator"

# Build mc_event_generator
mc_event_generator: mc_event_generator.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)
	@echo "Built: mc_event_generator"

# Clean build artifacts
clean:
	rm -f $(TARGETS) *.o
	@echo "Cleaned build artifacts"

# Help target
help:
	@echo "CEvNS C++ Examples Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all                      - Build all examples (default)"
	@echo "  basic_rate_calculator    - Build rate calculator only"
	@echo "  mc_event_generator       - Build MC event generator only"
	@echo "  clean                    - Remove build artifacts"
	@echo "  help                     - Show this help message"
	@echo ""
	@echo "Usage:"
	@echo "  make                     # Build everything"
	@echo "  make clean               # Clean"
	@echo "  make basic_rate_calculator  # Build specific target"

.PHONY: all clean help
