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

    mapping_dict = {}
    categorized_df = df.copy()

    for col in df.columns:
        if col != key_field:
            categorized_df[col], uniques = pd.factorize(df[col])
            mapping_dict[col] = {
                code: category for code, category in enumerate(uniques)
            }

    categorized_df.to_pickle("tmp/product_tabular_categorized.pickle")

    with open("tmp/product_tabular_categorized_dict.pickle", "wb") as file:
        pickle.dump(mapping_dict, file)


if __name__ == "__main__":
    main()
