#!/bin/bash

echo "Setting up Roxy Backend..."

if command -v conda &> /dev/null; then
    echo "Creating conda environment with Python 3.13..."
    conda create -n roxy-backend python=3.13 -y
    echo "Activating environment..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate roxy-backend
else
    echo "Conda not found, using system Python..."
fi

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Copying .env.example to .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update with your credentials."
fi

echo "Setup complete!"
echo ""
echo "To start the server:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
