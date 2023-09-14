from airflow import DAG
from airflow.operators.python import PythonOperator 
from airflow.utils.dates import days_ago
from deploy_fromFixtures import main
from datetime import datetime





dag = DAG(dag_id='deploy_fromFixtures',
          schedule="20 15 * * *",
          start_date=days_ago(1)
          )

deploy_fromFixtures = PythonOperator(python_callable=main,
                                     dag=dag,
                                     task_id='deploy_fromFixtures')

#
deploy_fromFixtures


