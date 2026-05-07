#!/bin/bash

# Configuration
PROJECT_ROOT="$(pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
PORT_SYNAN=8089
PORT_SEMAN=8090
LOG_DIR="${PROJECT_ROOT}/Logs"
SYNAN_LCK="${PROJECT_ROOT}/SynanDaemon.lck"

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Set RML environment variable
export RML="$PROJECT_ROOT"

stop_services() {
    echo "Stopping existing services..."
    
    # Try using lock file PID first
    if [ -f "$SYNAN_LCK" ]; then
        PID=$(cat "$SYNAN_LCK")
        if ps -p "$PID" > /dev/null; then
            echo "Killing SynanDaemon (PID $PID) from lock file..."
            kill "$PID" 2>/dev/null
        fi
    fi

    # Fallback to pkill for any remaining instances
    pkill -f SynanDaemon 2>/dev/null
    pkill -f SemanDaemon 2>/dev/null
    
    # Wait for processes to exit
    MAX_WAIT=5
    COUNT=0
    while pgrep -f "SynanDaemon|SemanDaemon" > /dev/null && [ $COUNT -lt $MAX_WAIT ]; do
        sleep 1
        ((COUNT++))
    done
    
    if pgrep -f "SynanDaemon|SemanDaemon" > /dev/null; then
        echo "Forcing shutdown..."
        pkill -9 -f SynanDaemon 2>/dev/null
        pkill -9 -f SemanDaemon 2>/dev/null
    fi
    
    # Cleanup lock files
    rm -f "$SYNAN_LCK" 2>/dev/null
    echo "Services stopped."
}

start_services() {
    echo "Starting services..."
    
    SYNAN_BIN="${BUILD_DIR}/Source/www/SynanDaemon/SynanDaemon"
    SEMAN_BIN="${BUILD_DIR}/Source/www/SemanDaemon/SemanDaemon"

    if [ ! -f "$SYNAN_BIN" ]; then
        echo "ERROR: SynanDaemon not found at $SYNAN_BIN. Please build it first."
        return 1
    fi

    echo "Starting SynanDaemon on port $PORT_SYNAN..."
    "$SYNAN_BIN" --host 0.0.0.0 --port "$PORT_SYNAN" --log-level info > "${LOG_DIR}/synan_stdout.log" 2>&1 &
    SYNAN_PID=$!
    echo "SynanDaemon PID: $SYNAN_PID"

    if [ -f "$SEMAN_BIN" ]; then
        echo "Starting SemanDaemon on port $PORT_SEMAN..."
        "$SEMAN_BIN" --host 0.0.0.0 --port "$PORT_SEMAN" --log-level info > "${LOG_DIR}/seman_stdout.log" 2>&1 &
        SEMAN_PID=$!
        echo "SemanDaemon PID: $SEMAN_PID"
    fi
    
    echo "--- Services started ---"
    echo "Use 'tail -f Logs/synan_dmn.log' to monitor."
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
        # Default to restart behavior if no arg provided
        echo "Usage: $0 {start|stop|restart}"
        echo "Defaulting to restart..."
        stop_services
        sleep 1
        start_services
        ;;
esac
