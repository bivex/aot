#!/bin/bash

# Complete rebuild and test for German dictionaries
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo " RML German Dictionary Rebuild & Test"
echo "=========================================="
echo ""

echo "Step 1: Rebuilding..."
./rebuild_german_dicts.sh --skip-build

echo ""
echo "Step 2: Verifying..."
./verify_german_dicts.sh

echo ""
echo "Step 3: Testing (if SynanDaemon available)..."

SYNAN_BIN="${PROJECT_ROOT}/Bin/SynanDaemon"
if [[ -x "$SYNAN_BIN" ]]; then
    RML="${PROJECT_ROOT}" "$SYNAN_BIN" --host 127.0.0.1 --port 8082 > /tmp/synan_ger_test.log 2>&1 &
    SYNAN_PID=$!
    sleep 2

    echo ""
    echo "Testing: 'Wir wollen das Gebäude wiederaufbauen und restaurieren.'"
    if command -v curl &> /dev/null; then
        response=$(curl -s --get --data-urlencode "action=syntax" \
            --data-urlencode "langua=German" \
            --data-urlencode "query=Wir wollen das Gebäude wiederaufbauen und restaurieren." \
            http://127.0.0.1:8082/ || echo "ERROR")
        [[ "$response" != "ERROR" ]] && { echo "$response" | head -c 500; echo ""; } || echo "ERROR: Could not connect"
    else
        echo "curl not available"
    fi

    kill "$SYNAN_PID" 2>/dev/null || true
    wait "$SYNAN_PID" 2>/dev/null || true
else
    echo "SynanDaemon not found."
fi

echo ""
echo "=========================================="
echo " Test complete!"
echo "=========================================="
