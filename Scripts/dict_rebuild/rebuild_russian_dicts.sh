#!/bin/bash

# Script to rebuild Russian morphological dictionaries for RML project
# Usage: ./rebuild_russian_dicts.sh [--clean] [--skip-build]

set -e

# Get absolute paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DICT_SOURCE_DIR="${PROJECT_ROOT}/Source/morph_dict/data/Russian"
DICT_OUTPUT_DIR="${PROJECT_ROOT}/Dicts/Morph/Russian"
MORPH_GEN="${BUILD_DIR}/Source/morph_dict/morph_gen/morph_gen"
STAT_DAT_BIN="${BUILD_DIR}/Source/dicts/GenFreqDict/StatDatBin"
WORD_FREQ_BIN="${BUILD_DIR}/Source/dicts/GenFreqDict/word_freq_bin"

CLEAN=false
SKIP_BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--skip-build]"
            echo ""
            echo "Options:"
            echo "  --clean       Remove build directory before building"
            echo "  --skip-build  Skip building morph_gen, only regenerate dictionaries"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check for required tools
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: Required tool '$1' not found. Please install it."
        exit 1
    fi
}

echo "=== RML Russian Dictionary Rebuild Script ==="
echo ""

# Check prerequisites
echo "[1/6] Checking prerequisites..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    check_tool brew
    check_tool cmake
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    check_tool cmake
    check_tool make
fi

# Verify RML environment variable
if [[ -z "$RML" ]]; then
    echo "WARNING: RML environment variable is not set."
    echo "Setting RML=${PROJECT_ROOT}"
    export RML="${PROJECT_ROOT}"
fi

echo "RML=${RML}"
echo ""

# Clean if requested
if [[ "$CLEAN" == true ]]; then
    echo "[2/6] Cleaning build directory..."
    rm -rf "${BUILD_DIR}"
    echo "Build directory removed"
    echo ""
fi

# Configure and build
if [[ "$SKIP_BUILD" != true ]]; then
    echo "[3/6] Configuring CMake..."
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS-specific settings
        export FLEX_TOOL="/opt/homebrew/opt/flex/bin/flex"
        export BISON_TOOL="/opt/homebrew/opt/bison/bin/bison"
        cmake .. -DCMAKE_BUILD_TYPE=Release \
            -DFLEX_EXECUTABLE="${FLEX_TOOL}" \
            -DBISON_EXECUTABLE="${BISON_TOOL}"
    else
        cmake .. -DCMAKE_BUILD_TYPE=Release
    fi

    echo ""
    echo "[4/6] Building morph_gen and related tools..."
    cmake --build . --target morph_gen -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
    echo ""
else
    echo "[3/6] Skipping build (--skip-build flag set)"
    # Verify morph_gen exists
    if [[ ! -f "$MORPH_GEN" ]]; then
        echo "ERROR: morph_gen not found at ${MORPH_GEN}"
        echo "Run without --skip-build to build it first"
        exit 1
    fi
    echo "Found morph_gen at ${MORPH_GEN}"
    echo ""
fi

# Make sure morph_gen is executable
chmod +x "$MORPH_GEN" 2>/dev/null || true

# Rebuild Russian dictionaries
echo "[5/6] Regenerating Russian morphological dictionaries..."
echo "Source: ${DICT_SOURCE_DIR}"
echo "Output: ${DICT_OUTPUT_DIR}"
echo ""

# The actual build happens through CMake custom targets
cd "${PROJECT_ROOT}"
cmake --build "${BUILD_DIR}" --target Russian_Morph -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)

echo ""
echo "[6/6] Building frequency binary files..."
# This target depends on Russian_Morph, but we ensure it completes
cmake --build "${BUILD_DIR}" --target Russian_Morph -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)

echo ""
echo "=== Rebuild Complete ==="
echo ""
echo "Generated files in ${DICT_OUTPUT_DIR}:"
ls -lh "${DICT_OUTPUT_DIR}"/*.bases "${DICT_OUTPUT_DIR}"/*.annot 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
ls -lh "${DICT_OUTPUT_DIR}"/*.forms_autom "${DICT_OUTPUT_DIR}"/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
ls -lh "${DICT_OUTPUT_DIR}"/*.bin 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "To use the rebuilt dictionaries, restart SynanDaemon/SemanDaemon if they are running."
echo ""
