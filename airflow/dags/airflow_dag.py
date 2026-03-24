from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'data_eng',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
}

# Assumes AIRFLOW_HOME is set in .env or defaults to docker /opt/airflow
project_root = os.getenv('AIRFLOW_HOME', '/Users/vybhavswaroop/Desktop/untitled folder 3')

with DAG(
    'ecommerce_pipeline',
    default_args=default_args,
    description='End-to-End E-Commerce Data Pipeline',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['ecommerce'],
) as dag:

    generate_data = BashOperator(
        task_id='generate_data',
        bash_command=f'cd "{project_root}" && python3 generators/generate_orders.py',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f'cd "{project_root}/dbt_project" && dbt run',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=f'cd "{project_root}/dbt_project" && dbt test',
    )

    data_quality = BashOperator(
        task_id='data_quality',
        bash_command=f'cd "{project_root}" && python3 tests/data_quality.py',
    )

    dashboard_readiness = DummyOperator(
        task_id='dashboard_readiness'
    )

    generate_data >> dbt_run >> dbt_test >> data_quality >> dashboard_readiness
