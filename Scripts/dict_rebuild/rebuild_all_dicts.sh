#!/bin/bash

# Rebuild ALL morphological dictionaries (Russian, Ukrainian, English, German)
# Usage: ./rebuild_all_dicts.sh [--clean] [--skip-build]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

echo "=========================================="
echo " RML All Languages Dictionary Rebuild"
echo "=========================================="
echo ""

LANGUAGES=("Russian" "Ukrainian" "English" "German")

# Check arguments
CLEAN=false
SKIP_BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean) CLEAN=true; shift ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--skip-build]"
            echo ""
            echo "Rebuilds all language dictionaries: Russian, Ukrainian, English, German"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Clean if requested
if [[ "$CLEAN" == true ]]; then
    echo "[*] Cleaning build directory..."
    rm -rf build
    echo ""
fi

# Build morph_gen if needed
if [[ "$SKIP_BUILD" != true ]]; then
    echo "[*] Configuring and building morph_gen..."
    mkdir -p build
    cd build

    if [[ "$OSTYPE" == "darwin"* ]]; then
        export FLEX_TOOL="/opt/homebrew/opt/flex/bin/flex"
        export BISON_TOOL="/opt/homebrew/opt/bison/bin/bison"
        cmake .. -DCMAKE_BUILD_TYPE=Release \
            -DFLEX_EXECUTABLE="${FLEX_TOOL}" \
            -DBISON_EXECUTABLE="${BISON_TOOL}"
    else
        cmake .. -DCMAKE_BUILD_TYPE=Release
    fi

    cmake --build . --target morph_gen -- -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
    cd ..
    echo ""
fi

# Rebuild each language
for lang in "${LANGUAGES[@]}"; do
    echo "=========================================="
    echo " Rebuilding ${lang} dictionaries..."
    echo "=========================================="
    echo ""

    if [[ -f "${SCRIPT_DIR}/rebuild_${lang,,}_dicts.sh" ]]; then
        "${SCRIPT_DIR}/rebuild_${lang,,}_dicts.sh" --skip-build
    else
        echo "No rebuild script found for ${lang}, skipping..."
    fi

    echo ""
done

echo "=========================================="
echo " All dictionaries rebuild complete!"
echo "=========================================="
echo ""
echo "Summary:"
for lang in "${LANGUAGES[@]}"; do
    if [[ -d "Dicts/Morph/${lang}" ]]; then
        echo "  ✓ ${lang}: Dicts/Morph/${lang}/"
    else
        echo "  ✗ ${lang}: NOT FOUND"
    fi
done
echo ""
echo "Run individual verify scripts to check each language:"
echo "  ./Scripts/dict_rebuild/verify_russian_dicts.sh"
echo "  ./Scripts/dict_rebuild/verify_ukrainian_dicts.sh"
echo ""
