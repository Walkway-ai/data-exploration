#!/usr/bin/env python
# coding: utf-8

import argparse
import pickle

import numpy as np
from sklearn.decomposition import PCA

from generate_model_embeddings import read_embedding


def reduce_dimension(concatenated_array, target_dim=1000):
    """
    Reduce the dimension of the array to the target dimension using PCA.
    """
    pca = PCA(n_components=target_dim)
    reduced_array = pca.fit_transform(concatenated_array)

    return reduced_array


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", action="store_true", help="Enable overwrite mode"
    )
    parser.add_argument(
        "--embedding_models", type=str, required=True, help="The embedding model."
    )
    parser.add_argument(
        "--embedding_fields", type=str, required=True, help="Embedding fields."
    )

    args = parser.parse_args()

    embedding_models = args.embedding_models
    embedding_models = embedding_models.split(",")

    embedding_fields = args.embedding_fields

    object_name = f"model_embeddings_mean_{embedding_fields}"

    if args.overwrite:

        l = list()

        for em in embedding_models:

            model_name = em.split("/")[-1]

            em_ = read_embedding(
                f"tmp/model_embeddings_{model_name}_{embedding_fields}"
            )

            em_ = np.array(em_)
            l.append(em_)

        # Concatenate the arrays along the feature axis (axis=1)
        concatenated_array = np.concatenate(l, axis=1)

        # Reduce dimensions to the target dimension
        reduced_array = reduce_dimension(concatenated_array=concatenated_array)

        with open(f"tmp/{object_name}", "wb") as f:

            pickle.dump(reduced_array, f)

    else:
        print("Skipping generation of mean embeddings.")


if __name__ == "__main__":
    main()
