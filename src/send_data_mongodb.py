#!/usr/bin/env python
# coding: utf-8

import gc
import yaml
from mongodb_lib import *
import pickle

config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

config_model = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config_model["embedding-model"]
model_name = embedding_model.split("/")[-1]

gc.collect()

def read_and_save_pickle(file_path):

    with open(file_path, "rb") as file:
        element = pickle.load(file)

    print(element.shape)

    save_object(fs=fs, object=element, object_name=file_path)

def main():

    read_and_save_pickle("tmp/product_tabular.pickle")
    read_and_save_pickle("tmp/product_textual_lang_summarized.pickle")
    read_and_save_pickle(f"tmp/final_embeddings_{model_name}_concated_tabular.pickle")

if __name__ == "__main__":
    main()
