# E-Commerce Data Platform

End-to-end data engineering project built with Python, DuckDB, dbt, Kafka, Airflow and Streamlit.
All data is synthetically generated — no external datasets used.

## Setup
1. `python3 -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in values
4. Run `python generators/generate_orders.py` to seed the database

## Stack
Faker · SQLite · FastAPI · Kafka · DuckDB · dbt · Airflow · Great Expectations · Streamlit
