#!/bin/bash
# ===========================================
# Teams Agent Integration - Setup Script
# ===========================================

set -e

echo "=========================================="
echo "  Teams Agent Integration - Setup"
echo "=========================================="
echo

# Check Python version
echo "[1/5] Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "  [ERROR] Python 3.11+ is required (found $PYTHON_VERSION)"
    exit 1
fi
echo "  [OK] Python $PYTHON_VERSION"

# Create virtual environment
echo
echo "[2/5] Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  [OK] Virtual environment created"
else
    echo "  [OK] Virtual environment already exists"
fi

# Activate virtual environment
echo
echo "[3/5] Activating virtual environment..."
source .venv/bin/activate
echo "  [OK] Activated"

# Install dependencies
echo
echo "[4/5] Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements/base.txt
echo "  [OK] Dependencies installed"

# Create .env if not exists
echo
echo "[5/5] Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  [OK] Created .env from .env.example"
else
    echo "  [OK] .env already exists"
fi

echo
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo
echo "  Next steps:"
echo
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo
echo "  2. Start the mock servers:"
echo "     python scripts/phase0/start_mock_agent.py"
echo "     python scripts/phase0/start_mock_webhook.py"
echo
echo "  3. Run tests:"
echo "     pytest tests/phase0/"
echo
echo "  4. Try the test client:"
echo "     python scripts/phase0/test_client.py"
echo
echo "=========================================="
