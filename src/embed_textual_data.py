#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import torch
import yaml
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import AutoModel

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

gc.collect()


def get_embeddings(df, text_field):
    if embedding_model == "jinaai/jina-embeddings-v2-base-en":
        model = AutoModel.from_pretrained(embedding_model, trust_remote_code=True)
    elif embedding_model == "thenlper/gte-large":
        model = SentenceTransformer(embedding_model)
    else:
        raise ValueError("Unsupported embedding model")

    embeddings = []

    for text in tqdm(df[text_field].tolist(), desc=f"Embedding {text_field}"):
        embedding = model.encode([text])
        embeddings.append(embedding[0])

    embeddings = torch.tensor(embeddings)
    torch.save(embeddings, f"tmp/embeddings_{text_field}_{model_name}.pt")


def main():
    df = pd.read_pickle("tmp/product_textual_lang_summarized.pickle")

    get_embeddings(df=df, text_field="pdt_inclexcl_ENG_CONTENT")
    get_embeddings(df=df, text_field="pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED")


if __name__ == "__main__":
    main()
