#!/bin/bash

# ClipStream Backend Setup Script
# This script sets up the backend environment and installs dependencies

set -e

echo "🚀 ClipStream Backend Setup"
echo ""

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Error: Python not found. Please install Python 3.8+"
    exit 1
fi

echo "🐍 Using Python: $PYTHON ($($PYTHON --version))"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON -m venv backend/venv
    echo "   ✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source backend/venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt -q
    echo "   ✅ Dependencies installed from requirements.txt"
else
    echo "   ⚠️  No requirements.txt found, installing core packages..."
    pip install -q \
        fastapi \
        uvicorn \
        pydantic \
        pydantic-settings \
        surrealdb \
        python-multipart \
        python-jose[cryptography] \
        passlib[bcrypt] \
        httpx \
        python-dotenv
    echo "   ✅ Core packages installed"
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "   Please create backend/.env with your configuration"
    echo "   You can copy from backend/.env.example"
    echo ""
    if [ -f "backend/.env.example" ]; then
        echo "   Run: cp backend/.env.example backend/.env"
        echo "   Then edit backend/.env with your credentials"
    fi
else
    echo "✅ .env file exists"
fi

echo ""
echo "="*60
echo "✅ Backend setup complete!"
echo "="*60
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source backend/venv/bin/activate"
echo ""
echo "2. Configure your .env file (if not done):"
echo "   cp backend/.env.example backend/.env"
echo "   # Edit backend/.env with your credentials"
echo ""
echo "3. Run the test:"
echo "   python3 test/test_backend_connection.py"
echo ""
echo "4. Start the backend:"
echo "   python3 backend/main.py"
echo ""

