from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import logging

# Define default args
default_args = {
    'owner': 'data_eng',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Assume we run from project root, or set explicit paths to the venv python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
python_bin = os.path.join(project_root, 'venv', 'bin', 'python')
dbt_bin = os.path.join(project_root, 'venv', 'bin', 'dbt')

def on_data_quality_failure(context):
    logging.error("ALERT: Data quality checks failed for ecommerce_pipeline!")
    
with DAG(
    'ecommerce_pipeline',
    default_args=default_args,
    description='E-commerce Data Pipeline',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['ecommerce'],
) as dag:

    batch_ingest = BashOperator(
        task_id='batch_ingest',
        bash_command=f'cd {project_root} && {python_bin} ingestion/batch_ingest.py',
    )

    load_warehouse = BashOperator(
        task_id='load_warehouse',
        bash_command=f'cd {project_root} && {python_bin} storage/setup_duckdb.py',
    )

    dbt_staging = BashOperator(
        task_id='dbt_staging',
        bash_command=f'cd {os.path.join(project_root, "dbt_project")} && {dbt_bin} run --select staging.*',
    )

    dbt_marts = BashOperator(
        task_id='dbt_marts',
        bash_command=f'cd {os.path.join(project_root, "dbt_project")} && {dbt_bin} run --select marts.*',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=f'cd {os.path.join(project_root, "dbt_project")} && {dbt_bin} test',
    )

    data_quality = BashOperator(
        task_id='data_quality',
        bash_command=f'cd {project_root} && {python_bin} tests/data_quality.py',
        on_failure_callback=on_data_quality_failure
    )

    # Dependencies
    batch_ingest >> load_warehouse >> dbt_staging >> dbt_marts >> dbt_test >> data_quality
