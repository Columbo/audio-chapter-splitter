#!/usr/bin/env sh

set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
FFMPEG_BIN_DIR="${FFMPEG_BIN_DIR:-}"
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_DIR="$PROJECT_DIR/venv"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python executable not found: $PYTHON_BIN" >&2
    exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"

# Activate the virtual environment for the current shell.
. "$VENV_DIR/bin/activate"

# Optionally prepend a custom FFmpeg location if it is not already on PATH.
if [ -n "$FFMPEG_BIN_DIR" ]; then
    export PATH="$FFMPEG_BIN_DIR:$PATH"
fi

python -m pip install --upgrade pip
python -m pip install -r "$PROJECT_DIR/requirements.txt"

echo "Environment is ready. You can now run the script."
