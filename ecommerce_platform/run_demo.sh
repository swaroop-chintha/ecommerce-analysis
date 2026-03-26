#!/bin/bash

# Configuration
PROJECT_ROOT=$(pwd)
export DEMO_MODE=true
export STREAMLIT_SERVER_PORT=8501

echo "🚀 Starting E-commerce Analytics in Demo Mode..."

# Stop heavy services if docker is present
if command -v docker-compose &> /dev/null; then
    echo "🛑 Stopping Docker services..."
    docker-compose down
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "🛑 Stopping Docker services (v2)..."
    docker compose down
fi

# Ensure virtual environment is activated
if [ -d "venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "❌ Error: venv directory not found! Please create it and install dependencies."
    exit 1
fi

# Check for demo data
echo "🔍 Checking for demo data..."
if [ ! -d "data/demo" ] || [ ! -f "data/demo/mart_sales_dashboard.parquet" ]; then
    echo "⚠️ Demo data missing! Running export script..."
    python dashboard/export_demo_data.py
fi

# Launch Streamlit
echo "✨ Launching Streamlit Dashboard..."
streamlit run dashboard/demo_app.py --server.headless true --server.port 8501
