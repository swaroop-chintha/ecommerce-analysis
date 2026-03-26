#!/bin/bash
# run_full_pipeline.sh - Executes the full ELT pipeline linearly without keeping heavy services running

echo "🔥 Starting Full Data Engineering Pipeline execution..."
export DEMO_MODE=false

if [ ! -d "venv" ]; then
    echo "Virtual environment 'venv' not found! Please run setup first."
    exit 1
fi

source venv/bin/activate

echo "1/4: Generating raw transactional data..."
python generators/generate_orders.py

echo "2/4: Transforming data via dbt star-schema models..."
(cd dbt_project && dbt run)

echo "3/4: Asserting Data Quality (Great Expectations)..."
python tests/data_quality.py

echo "4/4: Rebuilding Parquet extracts for future Demo Mode..."
python dashboard/export_demo_data.py

echo "🎉 Pipeline finished successfully. You can now run ./run_demo.sh or start Streamlit."
