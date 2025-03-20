#!/usr/bin/env bash

echo "Running in $MODE mode..."

if [ "$MODE" = "server" ]; then
    echo "Starting in server mode..."
    exec uv run server up
elif [ "$MODE" = "notebook" ]; then
    echo "Starting Jupyter Notebook..."
    # exec jupyter lab --ip=0.0.0.0 --port=8888 --allow-root
else
    echo "Unknown mode: $MODE"
    exit 1
fi
