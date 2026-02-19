#!/bin/bash
# MDViewer wrapper script

PROJECT_DIR="/home/anderson/Documentos/Coding/mdviewer"

# Save current directory
CURRENT_DIR=$(pwd)

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Run mdviewer from current directory
cd "$PROJECT_DIR"
python mdv "$CURRENT_DIR" "$@"
