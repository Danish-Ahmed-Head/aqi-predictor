#!/bin/bash

# AQI Predictor Setup Script
# This script sets up the project environment

echo "=================================="
echo "AQI Predictor - Setup Script"
echo "=================================="

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create directories
echo ""
echo "Creating project directories..."
mkdir -p data
mkdir -p models
mkdir -p reports
mkdir -p notebooks

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.template .env
    echo "✓ .env file created"
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Create .streamlit directory and secrets file
echo ""
echo "Setting up Streamlit..."
mkdir -p .streamlit
if [ ! -f .streamlit/secrets.toml ]; then
    echo '[default]' > .streamlit/secrets.toml
    echo 'HOPSWORKS_API_KEY = "your_key_here"' >> .streamlit/secrets.toml
    echo '✓ Streamlit secrets file created'
    echo '⚠️  Please edit .streamlit/secrets.toml and add your Hopsworks API key!'
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: python src/feature_pipeline.py --backfill 7"
echo "3. Run: python src/training_pipeline.py"
echo "4. Run: streamlit run app/streamlit_app.py"
echo ""
echo "For more information, see README.md"