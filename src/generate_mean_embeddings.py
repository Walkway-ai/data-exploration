#!/usr/bin/env python
# coding: utf-8

import argparse
import gc

import numpy as np
import yaml
from sklearn.decomposition import PCA

from mongodb_lib import *

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()


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

    args = parser.parse_args()

    embedding_models = args.embedding_models
    embedding_models = embedding_models.split(",")

    object_name = f"final_embeddings_mean"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file or args.overwrite:

        # Load the combined embeddings from MongoDB.

        l = list()

        for em in embedding_models:

            model_name = em.split("/")[-1]

            em_ = read_object(fs, f"final_embeddings_{model_name}")

            em_ = np.array(em_)
            l.append(em_)

        # Concatenate the arrays along the feature axis (axis=1)
        concatenated_array = np.concatenate(l, axis=1)

        # Reduce dimensions to the target dimension
        reduced_array = reduce_dimension(concatenated_array=concatenated_array)

        # Save the mean concatenated embeddings as a pickle file.
        remove_object(fs=fs, object_name=object_name)
        save_object(fs=fs, object=reduced_array, object_name=object_name)

    else:
        print("Skipping generation of mean embeddings.")


if __name__ == "__main__":
    main()
