#!/usr/bin/env python
# coding: utf-8

import gc

import yaml
from ydata_profiling import ProfileReport

from preprocessing_handlers import DataFrameProcessor

# Load configuration from yaml file.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
bigquery_config = config["bigquery-to-retrieve"]
key_field = bigquery_config["key-field"]
location_field = bigquery_config["location-field"]

# Run garbage collection to free up memory.
gc.collect()


def main():
    """
    Main function to process product data and generate profiling reports.

    Steps:
    1. Initialize a DataFrameProcessor with the product data.
    2. Preprocess the data.
    3. Save the processed tabular and textual data as pickle files.
    4. Generate and save profiling reports for both tabular and textual data.
    """
    # Initialize the DataFrameProcessor with the product data path and key fields.
    processor = DataFrameProcessor(
        data_path="tmp/product_tables.pickle",
        key_field=key_field,
        location_field=location_field,
    )

    # Preprocess the data.
    processor.preprocess()

    # Save the processed tabular data as a pickle file.
    processor.df.to_pickle("tmp/product_tabular.pickle")
    # Save the processed textual data as a pickle file.
    processor.df_text.to_pickle("tmp/product_textual.pickle")

    # Generate a profiling report for the tabular data.
    profile = ProfileReport(processor.df, title="Product Tabular Report")
    # Save the tabular profiling report to an HTML file.
    profile.to_file("reports/product-tabular-report.html")

    # Generate a profiling report for the textual data.
    profile = ProfileReport(processor.df_text, title="Product Textual Report")
    # Save the textual profiling report to an HTML file.
    profile.to_file("reports/product-textual-report.html")


if __name__ == "__main__":
    main()
