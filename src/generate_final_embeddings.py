#!/usr/bin/env python
# coding: utf-8

import gc
import pickle
import numpy as np
import torch
import pandas as pd
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

gc.collect()


def main():
    df_tabular = pd.read_pickle("tmp/product_tabular_categorized.pickle")
    embeddings = torch.load(f"tmp/embeddings_{model_name}.pt")

    final_embeddings = np.concatenate((df_tabular.values, embeddings.numpy()), axis=1)

    with open(f"tmp/final_embeddings_{model_name}_concated_tabular.pt", "wb") as file:
        pickle.dump(final_embeddings, file)

if __name__ == "__main__":
    main()
