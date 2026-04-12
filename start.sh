#!/bin/bash

echo "🚀 Starting the Ad Workflow Automation Dashboard..."
echo "📁 Project organized with modular architecture"
echo "🔗 Application will start at http://127.0.0.1:5002"
echo ""

# Check Python environment
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python not found"
    exit 1
fi

# Check required packages
python -c "import flask, playwright, pymongo" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Some required packages may not be installed"
    echo "Please run: pip install -r requirements.txt"
    echo ""
fi

# Start the application
echo "✅ Starting application..."
python run.py 