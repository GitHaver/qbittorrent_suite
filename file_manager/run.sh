#!/bin/bash

# Activate the virtual environment
source /home/standarduser/standard_user_scripts/plex_server/qbittorrent_suite/venv/bin/activate

# Move to the script directory to ensure the script can find its dependencies
cd /home/standarduser/standard_user_scripts/plex_server/qbittorrent_suite

# Run the Python script with full path to Python executable to ensure the right interpreter
python3.9 file_manager/file_manager.py >> file_manager/log/"$2".log 2>&1

# Deactivate the virtual environment after the script finishes
deactivate