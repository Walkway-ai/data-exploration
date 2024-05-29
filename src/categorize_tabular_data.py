#!/usr/bin/env python
# coding: utf-8

import gc
import pickle

import pandas as pd
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
bigquery_config = config["bigquery-to-retrieve"]
key_field = bigquery_config["key-field"]

gc.collect()


def main():
    df = pd.read_pickle("tmp/product_tabular.pickle")

    categorized_df = df.copy()

    for col in df.columns:
        categorized_df[col], _ = pd.factorize(df[col])

    del categorized_df[key_field]
    del categorized_df["pdt_product_level_SUPPLIERCODE"]

    categorized_df.to_pickle("tmp/product_tabular_categorized.pickle")

if __name__ == "__main__":
    main()
