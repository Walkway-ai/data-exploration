#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import torch
import yaml
from tqdm import tqdm
from transformers import AutoModel
from sentence_transformers import SentenceTransformer

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

    return torch.tensor(embeddings)

def main():
    df = pd.read_pickle("tmp/product_textual_lang_summarized.pickle")

    embeddings1 = get_embeddings(df=df, text_field="pdt_inclexcl_ENG_CONTENT")
    embeddings2 = get_embeddings(df=df, text_field="pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED")

    combined_embeddings = torch.cat((embeddings1, embeddings2), dim=1)

    torch.save(combined_embeddings, f"tmp/embeddings_{model_name}.pt")

    print("Embeddings generated and saved successfully.")

if __name__ == "__main__":
    main()