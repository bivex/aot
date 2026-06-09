#!/bin/bash

# Script to rebuild Spanish morphological dictionaries for RML project
# Usage: ./rebuild_spanish_dicts.sh [--clean] [--skip-build]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DICT_SOURCE_DIR="${PROJECT_ROOT}/Source/morph_dict/data/Spanish"
DICT_OUTPUT_DIR="${PROJECT_ROOT}/Dicts/Morph/Spanish"
MORPH_GEN="${BUILD_DIR}/Source/morph_dict/morph_gen/morph_gen"
CONVERTER="${PROJECT_ROOT}/dev/spa_conv/unimorph_spa_to_aot.py"
UNIMORPH_DATA="${PROJECT_ROOT}/Dicts/Morph/Spanish/unimorph/spa"

CLEAN=false
SKIP_BUILD=false
SKIP_CONVERT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean) CLEAN=true; shift ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        --skip-convert) SKIP_CONVERT=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--skip-build] [--skip-convert]"
            echo ""
            echo "Options:"
            echo "  --clean         Remove build directory before building"
            echo "  --skip-build    Skip building morph_gen, only regenerate dictionaries"
            echo "  --skip-convert  Skip UniMorph conversion (use existing morphs.json)"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: Required tool '$1' not found."
        exit 1
    fi
}

echo "=== RML Spanish Dictionary Rebuild Script ==="
echo ""

echo "[1/7] Checking prerequisites..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    check_tool brew; check_tool cmake
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    check_tool cmake; check_tool make
fi

if [[ -z "$RML" ]]; then
    echo "WARNING: RML not set. Setting RML=${PROJECT_ROOT}"
    export RML="${PROJECT_ROOT}"
fi

echo "RML=${RML}"
echo ""

if [[ "$SKIP_CONVERT" != true ]]; then
    echo "[2/7] Converting UniMorph Spanish data..."
    if [[ ! -f "$UNIMORPH_DATA" ]]; then
        echo "ERROR: UniMorph data not found at ${UNIMORPH_DATA}"
        echo "Run: git submodule update --init --recursive"
        exit 1
    fi
    check_tool python3
    python3 "${CONVERTER}"
    echo ""
else
    echo "[2/7] Skipping UniMorph conversion"
    if [[ ! -f "${DICT_SOURCE_DIR}/morphs.json" ]]; then
        echo "ERROR: morphs.json not found at ${DICT_SOURCE_DIR}/morphs.json"
        exit 1
    fi
    echo ""
fi

if [[ "$CLEAN" == true ]]; then
    echo "[3/7] Cleaning build directory..."
    rm -rf "${BUILD_DIR}"
    echo ""
fi

if [[ "$SKIP_BUILD" != true ]]; then
    echo "[4/7] Configuring CMake..."
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        export FLEX_TOOL="/opt/homebrew/opt/flex/bin/flex"
        export BISON_TOOL="/opt/homebrew/opt/bison/bin/bison"
        cmake .. -DCMAKE_BUILD_TYPE=Release \
            -DFLEX_EXECUTABLE="${FLEX_TOOL}" \
            -DBISON_EXECUTABLE="${BISON_TOOL}"
    else
        cmake .. -DCMAKE_BUILD_TYPE=Release
    fi
    echo ""
    echo "[5/7] Building morph_gen..."
    cmake --build . --target morph_gen -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
    echo ""
else
    echo "[4/7] Skipping build"
    if [[ ! -f "$MORPH_GEN" ]]; then
        echo "ERROR: morph_gen not found at ${MORPH_GEN}"
        exit 1
    fi
    echo ""
fi

chmod +x "$MORPH_GEN" 2>/dev/null || true

echo "[6/7] Regenerating Spanish morphological dictionaries..."
echo "Source: ${DICT_SOURCE_DIR}"
echo "Output: ${DICT_OUTPUT_DIR}"
echo ""

cd "${PROJECT_ROOT}"
cmake --build "${BUILD_DIR}" --target Spanish_Morph -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)

echo ""
echo "[7/7] Building frequency binary files..."
cmake --build "${BUILD_DIR}" --target Spanish_Morph -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)

echo ""
echo "=== Rebuild Complete ==="
echo ""
ls -lh "${DICT_OUTPUT_DIR}"/*.bases "${DICT_OUTPUT_DIR}"/*.annot 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
ls -lh "${DICT_OUTPUT_DIR}"/*.forms_autom "${DICT_OUTPUT_DIR}"/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
ls -lh "${DICT_OUTPUT_DIR}"/*.bin 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "To use the rebuilt dictionaries, restart SynanDaemon/SemanDaemon if they are running."
echo ""
