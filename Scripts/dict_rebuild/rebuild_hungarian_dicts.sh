#!/bin/bash
# Rebuild Hungarian morphological dictionaries
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="${ROOT}/build"
DICT_DIR="${ROOT}/Dicts/Morph/Hungarian"

SKIP_BUILD=false
SKIP_CONVERT=false
CLEAN=false

for arg in "$@"; do
    case $arg in
        --skip-build) SKIP_BUILD=true ;;
        --skip-convert) SKIP_CONVERT=true ;;
        --clean) CLEAN=true ;;
    esac
done

if [ "$CLEAN" = true ]; then
    echo "Cleaning Hungarian dict output..."
    rm -rf "${ROOT}/Source/morph_dict/data/Hungarian/morphs.json"
    rm -rf "${ROOT}/Source/morph_dict/data/Hungarian/gramtab.json"
    rm -rf "${DICT_DIR}/morph.bin" "${DICT_DIR}/predict.bin"
fi

if [ "$SKIP_CONVERT" = false ]; then
    echo "Converting UniMorph Hungarian data..."
    cd "${ROOT}"
    python3 dev/hun_conv/unimorph_hun_to_aot.py
fi

if [ "$SKIP_BUILD" = false ]; then
    echo "Building morph_gen..."
    cmake --build "${BUILD_DIR}" --target morph_gen -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

    echo "Generating binary dictionaries..."
    mkdir -p "${DICT_DIR}"
    "${BUILD_DIR}/Source/morph_dict/morph_gen/morph_gen" \
        --input "${ROOT}/Source/morph_dict/data/Hungarian/project.mwz" \
        --output-folder "${DICT_DIR}"
fi

echo "Hungarian dictionaries rebuilt in ${DICT_DIR}"
ls -la "${DICT_DIR}/"
