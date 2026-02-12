#!/bin/bash

# Quick Start Script for User Management Service

echo "🚀 Starting User Management Service..."
echo ""

# Set the Python path
PYTHON_PATH="/Users/mdevendran/python/fastapibuildingblocks/.venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found at $PYTHON_PATH"
    echo "Please ensure the virtual environment exists in the parent directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
$PYTHON_PATH -m pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""

# Run the service
echo "🎯 Starting FastAPI service..."
echo ""
echo "Service will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo ""

$PYTHON_PATH -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
