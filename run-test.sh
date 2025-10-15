#!/bin/bash

# ClipStream Backend Test Runner
# This script runs the backend connection test

set -e

echo "🧪 ClipStream Backend Connection Test"
echo ""

# Check if we're in the right directory
if [ ! -f "test/test_backend_connection.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

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
echo ""

# Check if virtual environment exists
if [ -d "backend/venv" ]; then
    echo "🔧 Activating virtual environment..."
    source backend/venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found"
    echo "   Consider creating one: python3 -m venv backend/venv"
fi

# Run the test
echo "🚀 Running connection test..."
echo ""

$PYTHON test/test_backend_connection.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Tests completed successfully!"
else
    echo ""
    echo "❌ Tests failed with exit code: $exit_code"
fi

exit $exit_code

