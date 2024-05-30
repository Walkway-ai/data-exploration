#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import yaml

# Load configuration from yaml file.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
bigquery_config = config["bigquery-to-retrieve"]
key_field = bigquery_config["key-field"]

# Run garbage collection to free up memory.
gc.collect()


def main():
    """
    Main function to categorize product data.

    Steps:
    1. Load the tabular product data from a pickle file.
    2. Create a copy of the DataFrame for categorization.
    3. Factorize each column in the DataFrame.
    4. Remove the key field and supplier code from the categorized DataFrame.
    5. Save the categorized DataFrame as a pickle file.
    """
    # Load the tabular product data from a pickle file.
    df = pd.read_pickle("tmp/product_tabular.pickle")

    # Create a copy of the DataFrame for categorization.
    categorized_df = df.copy()

    # Factorize each column in the DataFrame.
    for col in df.columns:
        categorized_df[col], _ = pd.factorize(df[col])

    # Remove the key field from the categorized DataFrame.
    del categorized_df[key_field]
    # Remove the supplier code from the categorized DataFrame.
    del categorized_df["pdt_product_level_SUPPLIERCODE"]

    # Save the categorized DataFrame as a pickle file.
    categorized_df.to_pickle("tmp/product_tabular_categorized.pickle")


if __name__ == "__main__":
    main()
