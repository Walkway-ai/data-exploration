from google.cloud import bigquery
import re
from collections import OrderedDict
from tqdm import tqdm

def split_bigquery_table_into_chunks(dataset_id, table_id, chunk_size=1000):
    
    client = bigquery.Client()

    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)
    total_rows = client.query(f"SELECT COUNT(*) FROM `{table.project}.{dataset_id}.{table_id}`").to_dataframe().iloc[0, 0]
    num_chunks = (total_rows + chunk_size - 1) // chunk_size

    for chunk_index in tqdm(range(num_chunks)):
        
        offset = chunk_index * chunk_size
        chunk_table_name = f"{table_id}_chunk_{chunk_index + 1}"

        query = f"""
            CREATE OR REPLACE TABLE `chunked.{chunk_table_name}` AS
            SELECT *
            FROM `{dataset_id}.{table_id}`
            LIMIT {chunk_size}
            OFFSET {offset}
        """

        client.query(query).result()

def aggregate(df, agg_field):

    columns_to_aggregate = [col for col in df.columns if col != agg_field]
    agg_dict = {col: list for col in columns_to_aggregate}
    df = df.groupby(agg_field).agg(agg_dict).reset_index()

    return df

def get_ordered_set_dict(df, field):

    df[field] = [list(OrderedDict.fromkeys(el).keys()) for el in list(df[field])]

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

    return df

def list_bigquery_tables(dataset_id):

    client = bigquery.Client()

    dataset_ref = client.dataset(dataset_id)
    
    tables = list(client.list_tables(dataset_ref))
    
    table_names = [table.table_id for table in tables]
    
    return table_names