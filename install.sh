#!/usr/bin/env bash
# ============================================================
# Telegram File Store Bot — VPS install script (Ubuntu/Debian)
# Run this from inside the cloned project folder:
#   chmod +x install.sh && ./install.sh
# ============================================================
set -e

echo "==> Updating package lists..."
sudo apt update -y

echo "==> Installing Python 3, venv and pip..."
sudo apt install -y python3 python3-venv python3-pip

echo "==> Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "==> Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "!!! IMPORTANT !!!"
    echo "Edit the .env file now and fill in BOT_TOKEN and OWNER_ID:"
    echo "    nano .env"
    echo ""
else
    echo "==> .env already exists, leaving it untouched."
fi

echo "==> Install complete."
echo ""
echo "Next steps:"
echo "1. nano .env                     # fill in BOT_TOKEN and OWNER_ID"
echo "2. python3 bot.py                # test it runs (Ctrl+C to stop)"
echo "3. See README.md 'Run 24/7 with systemd' to keep it alive permanently"
