#!/bin/bash
# run_demo.sh - Lightweight execution path for presentations

echo "🚀 Starting E-Commerce Analytics in Offline DEMO MODE..."
export DEMO_MODE=true

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run pipeline setup first."
    exit 1
fi

source venv/bin/activate
streamlit run dashboard/app.py
