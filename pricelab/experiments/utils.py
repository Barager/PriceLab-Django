import os
import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine, text

# df = pd.read_sql(sql_query, conn_str)

def query_db(sql_query, params=None):
    # user = os.getenv("SNOWFLAKE_USER")
    # password = os.getenv("SNOWFLAKE_PASSWORD")
    user = 'UVA_ABEUGER'
    password = 'T2yVc4C8Oa'
    conn_str = f"snowflake://{user}:{password}@rd02543.europe-west4.gcp/FELYX_UVA/MART?warehouse=COMPUTE_WAREHOUSE_MULTICLUSTER&role=FELYX_UVA"

    engine = create_engine(conn_str)
    with engine.connect() as connection:
        result = connection.execute(text(sql_query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df