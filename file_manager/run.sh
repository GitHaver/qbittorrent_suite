cd ..
source venv/bin/activate
python3 file_manager.py "$1" "$2" >> log/"$2".log 2>&1