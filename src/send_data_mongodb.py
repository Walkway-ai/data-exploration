#!/usr/bin/env python
# coding: utf-8

import gc
import pickle

import yaml

from mongodb_lib import *

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Load configuration from yaml file for embedding model.
config_model = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config_model["embedding-model"]
model_name = embedding_model.split("/")[-1]

# Run garbage collection to free up memory.
gc.collect()


def read_and_save_pickle(file_path):
    """
    Read a pickle file and save its content to MongoDB GridFS.

    Parameters:
    file_path (str): The path to the pickle file.

    Steps:
    1. Open and load the pickle file.
    2. Save the loaded object to MongoDB GridFS.
    """
    # Open and load the pickle file.
    with open(file_path, "rb") as file:
        element = pickle.load(file)

    # Save the loaded object to MongoDB GridFS.
    save_object(fs=fs, object=element, object_name=file_path)


def main():
    """
    Main function to read and save pickle files to MongoDB.

    Steps:
    1. Read and save the 'product_tabular.pickle' file.
    2. Read and save the 'product_textual_lang_summarized.pickle' file.
    3. Read and save the 'final_embeddings_<model_name>_concated_tabular.pickle' file.
    """
    # Read and save the 'product_tabular.pickle' file.
    read_and_save_pickle("tmp/product_tabular.pickle")

    # Read and save the 'product_textual_lang_summarized.pickle' file.
    read_and_save_pickle("tmp/product_textual_lang_summarized.pickle")

    # Read and save the 'final_embeddings_<model_name>_concated_tabular.pickle' file.
    read_and_save_pickle(f"tmp/final_embeddings_{model_name}_concated_tabular.pickle")


if __name__ == "__main__":
    main()
