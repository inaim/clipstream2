#!/bin/bash

# ClipStream Backend Startup Script
# This script starts the ClipStream backend server

set -e

echo "🚀 Starting ClipStream Backend..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env file not found"
    echo "📝 Creating from .env.example..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Created backend/.env - Please update with your credentials"
    else
        echo "❌ Error: backend/.env.example not found"
        exit 1
    fi
fi

# Change to backend directory
cd backend

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Error: Python not found. Please install Python 3.8+"
    exit 1
fi

echo "🐍 Using Python: $PYTHON"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if PORT is set, otherwise use default
PORT=${PORT:-8080}

echo ""
echo "✅ Backend ready!"
echo "🌐 Starting server on http://0.0.0.0:$PORT"
echo "📚 API docs available at http://localhost:$PORT/docs"
echo "🏥 Health check at http://localhost:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
$PYTHON main.py

