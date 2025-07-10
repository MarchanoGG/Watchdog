#!/bin/bash
cd /opt/watchdog
source .venv/bin/activate
python3 main.py "$@"