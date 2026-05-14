#!/bin/bash

# Complete rebuild and test script for RML Ukrainian dictionaries
# Usage: ./rebuild_and_test.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo " RML Ukrainian Dictionary Rebuild & Test"
echo "=========================================="
echo ""

# Step 1: Rebuild
echo "Step 1: Rebuilding dictionaries..."
./rebuild_ukrainian_dicts.sh --skip-build

echo ""
echo "Step 2: Verifying rebuild..."
./verify_ukrainian_dicts.sh

echo ""
echo "Step 3: Testing with SynanDaemon (if available)..."

SYNAN_BIN="${PROJECT_ROOT}/Bin/SynanDaemon"
if [[ -x "$SYNAN_BIN" ]]; then
    echo "Found SynanDaemon at ${SYNAN_BIN}"
    echo "Starting SynanDaemon on port 8082 (will run in background)..."
    RML="${PROJECT_ROOT}" "$SYNAN_BIN" --host 127.0.0.1 --port 8082 > /tmp/synan_ukr_test.log 2>&1 &
    SYNAN_PID=$!

    sleep 2

    echo ""
    echo "Testing with sample Ukrainian sentence:"
    echo "  'Ми хочемо відбудувати будинок і відновити фасад.'"
    echo ""

    if command -v curl &> /dev/null; then
        response=$(curl -s --get --data-urlencode "action=syntax" \
            --data-urlencode "langua=Ukrainian" \
            --data-urlencode "query=Ми хочемо відбудувати будинок і відновити фасад." \
            http://127.0.0.1:8082/ || echo "ERROR")

        if [[ "$response" != "ERROR" ]]; then
            echo "Response received from SynanDaemon:"
            echo "$response" | head -c 500
            echo ""
        else
            echo "ERROR: Could not connect to SynanDaemon"
        fi
    else
        echo "curl not available, skipping API test"
    fi

    kill "$SYNAN_PID" 2>/dev/null || true
    wait "$SYNAN_PID" 2>/dev/null || true
    echo ""
    echo "SynanDaemon test completed"
else
    echo "SynanDaemon not found at ${SYNAN_BIN}"
    echo "Build it with: cmake --build build --target SynanDaemon"
fi

echo ""
echo "=========================================="
echo " Rebuild and test complete!"
echo "=========================================="
