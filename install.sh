#!/bin/bash

set -e  # Stop on error

echo "[WatchDog] Installation started..."

# 1. Requirements
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

# 2. Create virtual environment
cd /opt/watchdog
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Create symlink (for global command)
if [ ! -f /usr/local/bin/watchdog ]; then
    sudo ln -s /opt/watchdog/watchdog.sh /usr/local/bin/watchdog
fi

echo "[WatchDog] Installation completed. Use the command: watchdog status"
