#!/bin/bash

# Friday v2 Master Launch Script

echo "======================================"
echo "    INITIALIZING FRIDAY V2 SYSTEM     "
echo "======================================"

# Function to gracefully shut down background processes on exit
cleanup() {
    echo -e "\nShutting down Friday subsystems..."
    if [ ! -z "$RUST_PID" ]; then
        kill $RUST_PID 2>/dev/null
    fi
    if [ ! -z "$PYTHON_PID" ]; then
        kill $PYTHON_PID 2>/dev/null
    fi
    echo "Friday powered down."
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM to run cleanup
trap cleanup SIGINT SIGTERM

# Source cargo and venv environments
source $HOME/.cargo/env 2>/dev/null || true
source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true

# 1. Start the Rust Core (EventBus, State Sync, Audio, Reflex)
echo "Starting Rust Realtime Core..."
cd rust-core
cargo run --release &
RUST_PID=$!
cd ..

# Wait a second to ensure Rust binds the TCP EventBus socket
sleep 2

# 2. Start the Python Cognitive Orchestrator
echo "Starting Python Cognitive Orchestrator..."
python python-core/orchestrator/main.py &
PYTHON_PID=$!

echo "======================================"
echo " Friday is fully active in background "
echo " Press Ctrl+C to shut down cleanly.   "
echo "======================================"

# Wait indefinitely for both processes
wait $RUST_PID
wait $PYTHON_PID
