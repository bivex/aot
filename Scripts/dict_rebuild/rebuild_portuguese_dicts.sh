#!/bin/bash
# Rebuild Portuguese morphological dictionaries
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="${ROOT}/build"
DICT_DIR="${ROOT}/Dicts/Morph/Portuguese"

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
    echo "Cleaning Portuguese dict output..."
    rm -rf "${ROOT}/Source/morph_dict/data/Portuguese/morphs.json"
    rm -rf "${ROOT}/Source/morph_dict/data/Portuguese/gramtab.json"
    rm -rf "${DICT_DIR}/morph.bin" "${DICT_DIR}/predict.bin"
fi

if [ "$SKIP_CONVERT" = false ]; then
    echo "Converting UniMorph Portuguese data..."
    cd "${ROOT}"
    python3 dev/por_conv/unimorph_por_to_aot.py
fi

if [ "$SKIP_BUILD" = false ]; then
    echo "Building morph_gen..."
    cmake --build "${BUILD_DIR}" --target morph_gen -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

    echo "Generating binary dictionaries..."
    mkdir -p "${DICT_DIR}"
    "${BUILD_DIR}/Source/morph_dict/morph_wizard/morph_gen" \
        "${ROOT}/Source/morph_dict/data/Portuguese/project.mwz" \
        "${DICT_DIR}"
fi

echo "Portuguese dictionaries rebuilt in ${DICT_DIR}"
ls -la "${DICT_DIR}/"
