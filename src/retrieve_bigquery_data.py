#!/usr/bin/env python
# coding: utf-8

import gc
from functools import reduce

import pandas as pd
import yaml
from tqdm import tqdm

from bigquery_handlers import BigQueryDataProcessor

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
bigquery_config = config["bigquery-to-retrieve"]
key_field = bigquery_config["key-field"]
tables = bigquery_config["tables"]

gc.collect()


def merge_dfs(left, right):
    """
    Merge two DataFrames on key_field with an outer join.

    Parameters:
    left (pd.DataFrame): The left DataFrame to merge.
    right (pd.DataFrame): The right DataFrame to merge.

    Returns:
    pd.DataFrame: The merged DataFrame.
    """

    return pd.merge(left, right, on=key_field, how="outer")


def main():
    """
    This script retrieves various datasets from a BigQuery database, merges them
    into a single DataFrame, and saves the resulting DataFrame as a pickle file.

    Steps:
    1. Read multiple tables from BigQuery into DataFrames.
    2. Merge the DataFrames into a single DataFrame using a common key field.
    3. Save the merged DataFrame as a pickle file.
    """

    dfs = []

    for bigquery_table in tqdm(tables):
        table_elements = tables[bigquery_table]

        bqdp = BigQueryDataProcessor(
            config=config,
            dataset_id=table_elements["dataset_id"],
            table_id=bigquery_table,
            table_fields=table_elements["fields"],
            key_field=key_field,
        )
        bqdp.read_bigquery_table()

        dfs.append(bqdp.df)

    product_df = reduce(merge_dfs, dfs)

    product_df.to_pickle("tmp/product_tables.pickle")


if __name__ == "__main__":
    main()
