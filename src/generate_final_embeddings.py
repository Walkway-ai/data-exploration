#!/usr/bin/env python
# coding: utf-8

import gc

import numpy as np
import pandas as pd
import yaml

from mongodb_lib import *

# Load configuration from YAML files.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()


def main():
    """
    Main function to concatenate tabular data with text embeddings.

    Steps:
    1. Load the categorized tabular data from a pickle file.
    2. Load the embeddings for 'pdt_inclexcl_ENG_CONTENT'.
    3. Load the embeddings for 'pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED'.
    4. Concatenate the tabular data with the two sets of embeddings.
    5. Save the final concatenated embeddings as a pickle file.
    """
    object_name = f"final_embeddings_{model_name}_concatenated_w_tabular"
    remove_object(fs, object_name)
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file:

        # Load the categorized tabular data from a pickle file.
        df_tabular = read_object(fs, "product_tabular_categorized")
        df_tabular = pd.DataFrame(df_tabular)

        # Load the embeddings for 'pdt_inclexcl_ENG_CONTENT'.
        embeddings1 = read_object(
            fs, f"embeddings_pdt_inclexcl_ENG_CONTENT_{model_name}"
        )

        # Load the embeddings for 'pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED'.
        embeddings2 = read_object(
            fs,
            f"embeddings_pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED_{model_name}",
        )

        # Ensure that the embeddings have the same number of rows as the tabular data.
        if df_tabular.shape[0] != len(embeddings1) or df_tabular.shape[0] != len(
            embeddings2
        ):
            raise ValueError(
                "Mismatch in the number of rows between tabular data and embeddings."
            )

        # Concatenate the tabular data with the two sets of embeddings.
        final_embeddings = np.concatenate(
            (df_tabular.values, np.array(embeddings1), np.array(embeddings2)), axis=1
        )

        # Save the final concatenated embeddings as a pickle file.
        save_object(fs=fs, object=final_embeddings, object_name=object_name)

    else:
        print(f"The concatenated embeddings file '{object_name}' already exists.")


if __name__ == "__main__":
    main()
