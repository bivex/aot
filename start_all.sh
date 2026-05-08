#!/bin/bash

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
PORT_SYNAN=8089
PORT_SEMAN=8090
LOG_DIR="${PROJECT_ROOT}/Logs"
SYNAN_LCK="${PROJECT_ROOT}/SynanDaemon.lck"
SEMAN_LCK="${PROJECT_ROOT}/SemanDaemon.lck"

# Ensure we are in the project root
cd "$PROJECT_ROOT"

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Set RML environment variable
export RML="$PROJECT_ROOT"

# Ensure rml.ini is in the root (daemons look for it in the current directory)
if [ ! -f "rml.ini" ] && [ -f "Bin/rml.ini" ]; then
    echo "Creating symlink for rml.ini..."
    ln -s Bin/rml.ini rml.ini
fi

stop_services() {
    echo "Stopping existing services..."
    
    # Try using lock file PIDs first
    for LCK in "$SYNAN_LCK" "$SEMAN_LCK"; do
        if [ -f "$LCK" ]; then
            PID=$(cat "$LCK" 2>/dev/null)
            if [ -n "$PID" ] && ps -p "$PID" > /dev/null; then
                echo "Killing process (PID $PID) from lock file $LCK..."
                kill "$PID" 2>/dev/null
            fi
        fi
    done

    # Fallback to pkill for any remaining instances
    pkill -f "SynanDaemon|SemanDaemon" 2>/dev/null
    
    # Wait for processes to exit
    MAX_WAIT=10
    COUNT=0
    while pgrep -f "SynanDaemon|SemanDaemon" > /dev/null && [ $COUNT -lt $MAX_WAIT ]; do
        echo -n "."
        sleep 1
        ((COUNT++))
    done
    echo ""
    
    if pgrep -f "SynanDaemon|SemanDaemon" > /dev/null; then
        echo "Forcing shutdown..."
        pkill -9 -f "SynanDaemon|SemanDaemon" 2>/dev/null
    fi
    
    # Cleanup lock files
    rm -f "$SYNAN_LCK" "$SEMAN_LCK" 2>/dev/null
    echo "Services stopped."
}

start_services() {
    echo "Starting services in background..."
    
    SYNAN_BIN="${BUILD_DIR}/Source/www/SynanDaemon/SynanDaemon"
    SEMAN_BIN="${BUILD_DIR}/Source/www/SemanDaemon/SemanDaemon"

    if [ ! -f "$SYNAN_BIN" ]; then
        echo "ERROR: SynanDaemon not found at $SYNAN_BIN. Please build it first."
        return 1
    fi

    # Start SynanDaemon with nohup and redirect to log
    nohup "$SYNAN_BIN" --host 0.0.0.0 --port "$PORT_SYNAN" --log-level info > "${LOG_DIR}/synan_stdout.log" 2>&1 &
    SYNAN_PID=$!
    echo $SYNAN_PID > "$SYNAN_LCK"
    echo "SynanDaemon started with PID $SYNAN_PID (Port $PORT_SYNAN)"

    if [ -f "$SEMAN_BIN" ]; then
        nohup "$SEMAN_BIN" --host 0.0.0.0 --port "$PORT_SEMAN" --log-level info > "${LOG_DIR}/seman_stdout.log" 2>&1 &
        SEMAN_PID=$!
        echo $SEMAN_PID > "$SEMAN_LCK"
        echo "SemanDaemon started with PID $SEMAN_PID (Port $PORT_SEMAN)"
    fi
    
    echo ""
    echo "Initialization takes ~10-15 seconds."
    echo "Check progress: tail -f Logs/synan_dmn.log"
    echo "Check output: tail -f Logs/synan_stdout.log"
}

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 1
        start_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
