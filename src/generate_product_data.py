#!/usr/bin/env python
# coding: utf-8

import gc

import yaml
from ydata_profiling import ProfileReport

from preprocessing_handlers import DataFrameProcessor

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
bigquery_config = config["bigquery-to-retrieve"]
key_field = bigquery_config["key-field"]
location_field = bigquery_config["location-field"]

gc.collect()


def main():
    """
    Main function to process product data and generate profiling reports.
    """

    processor = DataFrameProcessor(
        data_path="tmp/product_tables.pickle",
        key_field=key_field,
        location_field=location_field,
    )

    processor.preprocess()

    processor.df.to_pickle("tmp/product_tabular.pickle")
    processor.df_text.to_pickle("tmp/product_textual.pickle")

    profile = ProfileReport(processor.df, title="Product Tabular Report")
    profile.to_file("reports/product-tabular-report.html")

    profile = ProfileReport(processor.df_text, title="Product Textual Report")
    profile.to_file("reports/product-textual-report.html")


if __name__ == "__main__":
    main()
