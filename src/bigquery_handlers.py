#!/usr/bin/env python
# coding: utf-8

import re
from collections import OrderedDict

from google.cloud import bigquery


class BigQueryDataProcessor:
    def __init__(self, config, dataset_id, table_id, table_fields, key_field):
        """
        Initialize the BigQueryDataProcessor with the given configuration file path.

        Parameters:
        config (str): The configuration file.
        dataset_id (str): The dataset ID in BigQuery.
        table_id (str): The table ID in BigQuery.
        table_fields (str): The fields to be collected.
        key_field (str): The column name to group by.
        """

        self.config = config
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.table_fields = table_fields
        self.selected_fields = ", ".join(self.table_fields)
        self.key_field = key_field

        self.client = bigquery.Client()

    def read_bigquery_table(self):
        """
        Read a BigQuery table into a DataFrame and aggregate its values.

        Returns:
        pd.DataFrame: The aggregated DataFrame with cleaned column names.
        """

        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        table = self.client.get_table(table_ref)

        query = f"SELECT {self.selected_fields} FROM `{table.project}.{table.dataset_id}.{table.table_id}`"
        query_job = self.client.query(query)
        self.df = query_job.to_dataframe()

        prefix = self.table_id + "_"
        self.df.columns = [
            prefix + re.sub(r"[^A-Za-z0-9]+", "", col.upper())
            for col in self.df.columns
        ]
        self.df.rename(columns={prefix + self.key_field: self.key_field}, inplace=True)

        self.aggregate_and_get_set()

    def aggregate_and_get_set(self):
        """
        Aggregate and deduplicate values in each column of the DataFrame based on the key field.

        Returns:
        pd.DataFrame: The aggregated DataFrame with unique lists of values for each column.
        """

        columns_to_aggregate = [col for col in self.df.columns if col != self.key_field]
        agg_dict = {col: list for col in columns_to_aggregate}
        self.df = self.df.groupby(self.key_field).agg(agg_dict).reset_index()

        for column in columns_to_aggregate:
            self.df[column] = [
                list(OrderedDict.fromkeys(el).keys()) for el in list(self.df[column])
            ]

    def retrieve_most_recent_bigquery_table(self):
        """
        Retrieve the most recent records for each product from the specified BigQuery table
        and create or replace a new table with these records.

        Parameters:
        dataset_id (str): The dataset ID in BigQuery.
        table_id (str): The table ID in BigQuery.
        """

        client = bigquery.Client()

        query = f"""
            CREATE OR REPLACE TABLE `preprocessed.{self.table_id}` AS
            WITH ranked_table AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (PARTITION BY product_code ORDER BY updated_at DESC) AS row_num
                FROM
                    `{self.dataset_id}.{self.table_id}`
            )
            SELECT
                {self.selected_fields}
            FROM
                ranked_table
            WHERE
                row_num = 1
        """

        client.query(query).result()
