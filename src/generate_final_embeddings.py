#!/usr/bin/env python
# coding: utf-8

import gc
import pickle

import numpy as np
import pandas as pd
import torch
import yaml

# Load configuration from yaml file.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

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
    # Load the categorized tabular data from a pickle file.
    df_tabular = pd.read_pickle("tmp/product_tabular_categorized.pickle")

    # Load the embeddings for 'pdt_inclexcl_ENG_CONTENT'.
    embeddings1 = torch.load(f"tmp/embeddings_pdt_inclexcl_ENG_CONTENT_{model_name}.pt")

    # Load the embeddings for 'pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED'.
    embeddings2 = torch.load(
        f"tmp/embeddings_pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED_{model_name}.pt"
    )

    # Concatenate the tabular data with the two sets of embeddings.
    final_embeddings = np.concatenate(
        (df_tabular.values, embeddings1.numpy(), embeddings2.numpy()), axis=1
    )

    # Save the final concatenated embeddings as a pickle file.
    with open(
        f"tmp/final_embeddings_{model_name}_concated_tabular.pickle", "wb"
    ) as file:
        pickle.dump(final_embeddings, file)


if __name__ == "__main__":
    main()
