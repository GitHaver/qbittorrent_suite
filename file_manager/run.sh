#!/bin/bash

# Activate the virtual environment
source /home/standarduser/standard_user_scripts/plex_server/qbittorrent_suite/venv/bin/activate

# Move to the script directory to ensure the script can find its dependencies
cd /home/standarduser/standard_user_scripts/plex_server/qbittorrent_suite

if [ -z "$1" ]; then
  echo -n "Please enter a torrent hash (arg1):"
  read -r torrent_hash
else
  torrent_hash="$1"
fi

if [ -z "$2" ]; then
  torrent_name="Manual Run"
else
  torrent_name="$2"
fi

log_dir="file_manager/log"
if [ ! -d "$log_dir" ]; then
  mkdir -p "$log_dir"
fi

# Run the Python script with full path to Python executable to ensure the right interpreter
python3.9 file_manager/file_manager.py "$torrent_hash" "$torrent_name" >> file_manager/log/"$torrent_name".log 2>&1

# Deactivate the virtual environment after the script finishes
deactivate