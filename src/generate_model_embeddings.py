#!/usr/bin/env python
# coding: utf-8

import argparse
import gc

import numpy as np
import yaml

from mongodb_lib import *

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

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", action="store_true", help="Enable overwrite mode"
    )
    parser.add_argument(
        "--embedding_model", type=str, required=True, help="The embedding model."
    )

    args = parser.parse_args()

    embedding_model = args.embedding_model
    model_name = embedding_model.split("/")[-1]

    object_name = f"final_embeddings_{model_name}"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file or args.overwrite:

        embeddings1 = read_object(
            fs, f"embeddings_pdt_inclexcl_ENG_CONTENT_translated_{model_name}"
        )

        embeddings2 = read_object(
            fs,
            f"embeddings_pdt_product_detail_PRODUCTTITLE_translated_{model_name}",
        )

        embeddings3 = read_object(
            fs,
            f"embeddings_pdt_product_detail_TOURGRADEDESCRIPTION_{model_name}",
        )

        # Ensure that the embeddings have the same number of rows as the tabular data.
        if not len(embeddings1) == len(embeddings2) == len(embeddings3):
            raise ValueError("Mismatch in the number of rows between embeddings.")

        final_embeddings = np.concatenate(
            (
                np.array(embeddings1),
                np.array(embeddings2),
                np.array(embeddings3),
            ),
            axis=1,
        )

        # Save the model concatenated embeddings as a pickle file.
        remove_object(fs=fs, object_name=object_name)
        save_object(fs=fs, object=final_embeddings, object_name=object_name)

    else:
        print("Skipping generation of model embeddings.")


if __name__ == "__main__":
    main()
