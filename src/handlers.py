from google.cloud import bigquery
import re
from collections import OrderedDict

def retrieve_most_recent_pdt_capacity(dataset_id, table_id):

    client = bigquery.Client()

    query = f"""
        CREATE OR REPLACE TABLE `preprocessed.{table_id}` AS
        WITH ranked_table AS (
            SELECT
                *,
                ROW_NUMBER() OVER (PARTITION BY product_code ORDER BY updated_at DESC) AS row_num
            FROM
                `{dataset_id}.{table_id}`
        )
        SELECT
            product_code,
            tour_grade_code,
            availability_status,
            capacity,
            consumed_by_adult,
            consumed_by_senior,
            consumed_by_youth,
            consumed_by_child,
            consumed_by_infant,
            start_time,
            availability_date,
            booking_cutoff,
            booking_cutoff_utc,
            updated_at,
            updated_at_utc
        FROM
            ranked_table
        WHERE
            row_num = 1
    """

    client.query(query).result()

def aggregate_and_get_set(df, key_field):

    columns_to_aggregate = [col for col in df.columns if col != key_field]
    agg_dict = {col: list for col in columns_to_aggregate}
    df = df.groupby(key_field).agg(agg_dict).reset_index()

    for column in columns_to_aggregate:

        df[column] = [list(OrderedDict.fromkeys(el).keys()) for el in list(df[column])]

    return df

def read_bigquery_table(dataset_id, table_id, key_field):

    client = bigquery.Client()

    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)

    query = f"SELECT * FROM `{table.project}.{table.dataset_id}.{table.table_id}`"

    job_config = bigquery.QueryJobConfig()
    job_config.use_query_cache = False

    query_job = client.query(query, job_config=job_config)
    df = query_job.to_dataframe()

    prefix = table_id + "_"

    df.columns = [prefix + re.sub(r'[^A-Za-z0-9]+', '', col.upper()) for col in df.columns]
    df.rename(columns={prefix + key_field: key_field}, inplace=True)

    df = aggregate_and_get_set(df, key_field)

    return df

def list_bigquery_tables(dataset_id):

    client = bigquery.Client()

    dataset_ref = client.dataset(dataset_id)
    
    tables = list(client.list_tables(dataset_ref))
    
    table_names = [table.table_id for table in tables]
    
    return table_names