cd ..

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    cd ..
    python3 -m venv venv
    source venv/bin/activate
    pip install -r setup/requirements.txt
fi

