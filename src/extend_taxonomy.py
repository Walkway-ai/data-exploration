#!/usr/bin/env python
# coding: utf-8

import argparse
import gc

import pandas as pd
import yaml

from mongodb_lib import *

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", action="store_true", help="Enable overwrite mode"
    )

    args = parser.parse_args()

    object_name = f"product_textual_lang_summarized_subcategories_categories_walkway"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file or args.overwrite:

        annotated_data = read_object(
            fs, "product_textual_lang_summarized_subcategories_walkway"
        )
        annotated_data = pd.DataFrame(annotated_data)

        taxonomy = pd.read_excel("Categories.xlsx")
        taxonomy = taxonomy[["Category", "Sub-category"]]
        taxonomy["Sub-category"] = [
            el.split(": ")[1] for el in taxonomy["Sub-category"]
        ]
        taxonomy["Category"] = [el.split(": ")[1] for el in taxonomy["Category"]]

        mapping = dict(zip(taxonomy["Sub-category"], taxonomy["Category"]))

        annotated_data["sub-categories-walkway"] = [
            [x for x in el if x] for el in annotated_data["sub-categories-walkway"]
        ]
        annotated_data["categories-walkway"] = [
            [mapping[x] for x in el] for el in annotated_data["sub-categories-walkway"]
        ]

        remove_object(fs=fs, object_name=object_name)
        save_object(fs=fs, object=annotated_data, object_name=object_name)


if __name__ == "__main__":
    main()
