from google.cloud import bigquery
import re
from collections import OrderedDict
import pandas as pd

def retrieve_most_recent_pdt_capacity(dataset_id, table_id):
    """
    Retrieve the most recent records for each product from the specified BigQuery table
    and create or replace a new table with these records.

    Parameters:
    dataset_id (str): The dataset ID in BigQuery.
    table_id (str): The table ID in BigQuery.
    """

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
    """
    Aggregate and deduplicate values in each column of the DataFrame based on the key field.

    Parameters:
    df (pd.DataFrame): The DataFrame to aggregate.
    key_field (str): The column name to group by.

    Returns:
    pd.DataFrame: The aggregated DataFrame with unique lists of values for each column.
    """

    columns_to_aggregate = [col for col in df.columns if col != key_field]
    agg_dict = {col: list for col in columns_to_aggregate}
    df = df.groupby(key_field).agg(agg_dict).reset_index()

    for column in columns_to_aggregate:

        df[column] = [list(OrderedDict.fromkeys(el).keys()) for el in list(df[column])]

    return df

def read_bigquery_table(dataset_id, table_id, key_field):
    """
    Read a BigQuery table into a DataFrame and aggregate its values.

    Parameters:
    dataset_id (str): The dataset ID in BigQuery.
    table_id (str): The table ID in BigQuery.
    key_field (str): The column name to group by.

    Returns:
    pd.DataFrame: The aggregated DataFrame with cleaned column names.
    """

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

def upload_bigquery_table(df, dataset_id, table_id):
    """
    Upload a DataFrame to a specified BigQuery table.

    Parameters:
    df (pd.DataFrame): The DataFrame to upload.
    dataset_id (str): The dataset ID in BigQuery.
    table_id (str): The table ID in BigQuery.
    """

    client = bigquery.Client()

    table_ref = client.dataset(dataset_id).table(table_id)

    job = client.load_table_from_dataframe(df, table_ref)

    job.result()

    print(f"Loaded {job.output_rows} rows into {dataset_id}:{table_id}.")

def merge_dfs(left, right):
    """
    Merge two DataFrames on the 'PRODUCTCODE' column with an outer join.

    Parameters:
    left (pd.DataFrame): The left DataFrame to merge.
    right (pd.DataFrame): The right DataFrame to merge.

    Returns:
    pd.DataFrame: The merged DataFrame.
    """

    return pd.merge(left, right, on='PRODUCTCODE', how='outer')