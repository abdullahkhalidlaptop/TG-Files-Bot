#!/usr/bin/env bash
# ============================================================
# Telegram File Store Bot — VPS install script (Ubuntu/Debian)
# This script deliberately never calls sudo — it must be run as root.
# Most fresh VPS instances give you a root shell by default; if yours
# doesn't, switch to root first (e.g. `su -`) before running this.
#
# Run this from inside the cloned project folder:
#   chmod +x install.sh && ./install.sh
# ============================================================
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "This script needs to be run as root (no sudo is used anywhere in this project)."
    echo "Switch to root first, e.g.:  su -"
    echo "...then re-run:  ./install.sh"
    exit 1
fi

echo "==> Updating package lists..."
apt update -y

echo "==> Installing Python 3, venv and pip..."
apt install -y python3 python3-venv python3-pip

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
echo "3. See README.md 'Run it 24/7' to keep it alive permanently (PM2 or systemd)"
