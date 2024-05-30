#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import torch
import yaml
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import AutoModel

# Load configuration from yaml file.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

# Run garbage collection to free up memory.
gc.collect()


def get_embeddings(df, text_field):
    """
    Generate embeddings for a specified text field in the DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the text data.
    text_field (str): The column name of the text data to embed.

    Saves:
    Torch tensor file containing the embeddings for the specified text field.
    """
    # Load the appropriate embedding model.
    if embedding_model == "jinaai/jina-embeddings-v2-base-en":
        model = AutoModel.from_pretrained(embedding_model, trust_remote_code=True)
    elif embedding_model == "thenlper/gte-large":
        model = SentenceTransformer(embedding_model)
    else:
        raise ValueError("Unsupported embedding model")

    embeddings = []

    # Generate embeddings for each text entry in the specified column.
    for text in tqdm(df[text_field].tolist(), desc=f"Embedding {text_field}"):
        embedding = model.encode([text])
        embeddings.append(embedding[0])

    # Convert embeddings to a torch tensor and save to file.
    embeddings = torch.tensor(embeddings)
    torch.save(embeddings, f"tmp/embeddings_{text_field}_{model_name}.pt")


def main():
    """
    Main function to generate embeddings for product text fields.

    Steps:
    1. Load the summarized product textual data from a pickle file.
    2. Generate embeddings for the 'pdt_inclexcl_ENG_CONTENT' field.
    3. Generate embeddings for the 'pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED' field.
    """
    # Load the summarized product textual data from a pickle file.
    df = pd.read_pickle("tmp/product_textual_lang_summarized.pickle")

    # Generate embeddings for the specified text fields.
    get_embeddings(df=df, text_field="pdt_inclexcl_ENG_CONTENT")
    get_embeddings(df=df, text_field="pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED")


if __name__ == "__main__":
    main()
