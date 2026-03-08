#!/usr/bin/env bash
# setup.sh — Bootstrap ai-doc-gen on Linux / macOS
set -euo pipefail

VENV_DIR=".venv"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║    🔧  ai-doc-gen Setup (Unix)       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "▶  Creating virtual environment…"
    python3 -m venv "$VENV_DIR"
    echo "✔  venv created at ./$VENV_DIR"
else
    echo "✔  venv already exists — skipping"
fi

# 2. Activate & install dependencies
echo "▶  Installing dependencies…"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✔  Dependencies installed"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       ✅  Setup complete!            ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Activate venv :  source .venv/bin/activate"
echo "  Run            :  python main.py /path/to/project"
echo "  Options        :  python main.py --help"
echo ""
