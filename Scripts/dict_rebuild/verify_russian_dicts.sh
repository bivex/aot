#!/bin/bash

# Quick verification script to check if Russian dictionaries are properly built
# Usage: ./verify_russian_dicts.sh

set -e

# Get project root (parent of Scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DICT_DIR="${PROJECT_ROOT}/Dicts/Morph/Russian"
SOURCE_DIR="${PROJECT_ROOT}/Source/morph_dict/data/Russian"

echo "=== RML Russian Dictionary Verification ==="
echo ""

# Check if directory exists
if [[ ! -d "$DICT_DIR" ]]; then
    echo "ERROR: Dictionary directory not found: ${DICT_DIR}"
    exit 1
fi

# Check for required files
echo "[1/5] Checking required dictionary files..."
REQUIRED_FILES=(
    "morph.bases"
    "morph.annot"
    "morph.forms_autom"
    "gramtab.json"
    "morph.options"
    "lhomoweight.bin"
    "chomoweight.bin"
    "fhomoweight.bin"
    "lwordweight.bin"
    "cwordweight.bin"
    "fwordweight.bin"
    "npredict.bin"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "${DICT_DIR}/${file}" ]]; then
        echo "  ✓ ${file} ($(du -h "${DICT_DIR}/${file}" | cut -f1))"
    else
        echo "  ✗ ${file} - MISSING"
        ((MISSING++))
    fi
done

if [[ $MISSING -gt 0 ]]; then
    echo ""
    echo "ERROR: ${MISSING} required file(s) missing. Dictionaries may not be built correctly."
    exit 1
fi

echo ""
echo "[2/5] Checking source dictionary files..."
SOURCE_DIR="${PROJECT_ROOT}/Source/morph_dict/data/Russian"
for file in morphs.json gramtab.json WordData.txt; do
    if [[ -f "${SOURCE_DIR}/${file}" ]]; then
        echo "  ✓ ${file} ($(du -h "${SOURCE_DIR}/${file}" | cut -f1))"
    else
        echo "  ✗ ${file} - MISSING"
    fi
done

echo ""
echo "[3/5] Checking rebuild-related words in source..."
words=("перестроить" "отстроить" "восстановить" "реконструировать" "обновить" "отремонтировать" "реставрировать")
for word in "${words[@]}"; do
    if grep -q "^${word};INFINITIVE" "${SOURCE_DIR}/WordData.txt"; then
        echo "  ✓ ${word} found in WordData.txt"
    else
        echo "  ✗ ${word} NOT FOUND in WordData.txt"
    fi
done

echo ""
echo "[4/5] Checking morphs.json structure..."
if command -v python3 &> /dev/null; then
    if python3 -c "import json; json.load(open('${DICT_DIR}/gramtab.json'))" 2>/dev/null; then
        echo "  ✓ gramtab.json is valid JSON"
    else
        echo "  ✗ gramtab.json is invalid JSON"
    fi

    # Count lemmas
    lemma_count=$(python3 -c "import json; print(len(json.load(open('${SOURCE_DIR}/morphs.json'))['flexia_models']))" 2>/dev/null || echo "unknown")
    echo "  ℹ Source morphs.json has ${lemma_count} lemma models"
else
    echo "  ⚠ Python3 not available, skipping JSON validation"
fi

echo ""
echo "[5/5] Build timestamps:"
echo "  Source:  $(stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "${SOURCE_DIR}/morphs.json" 2>/dev/null || stat -c '%y' "${SOURCE_DIR}/morphs.json" 2>/dev/null | cut -d'.' -f1)"
echo "  Binary:  $(stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "${DICT_DIR}/morph.bases" 2>/dev/null || stat -c '%y' "${DICT_DIR}/morph.bases" 2>/dev/null | cut -d'.' -f1)"

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Dictionaries are ready. Start daemons with:"
echo "  RML=$(pwd) ./Bin/SemanDaemon --host 127.0.0.1 --port 8081"
echo "  RML=$(pwd) ./Bin/SynanDaemon --host 127.0.0.1 --port 8082"
