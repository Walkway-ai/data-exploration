#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import torch
import yaml
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import AutoModel

from mongodb_lib import *

# Load configuration from YAML files.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

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
    save_object(
        fs=fs, object=embeddings, object_name=f"embeddings_{text_field}_{model_name}"
    )


def main():
    """
    Main function to generate embeddings for product text fields.

    Steps:
    1. Load the summarized product textual data from a pickle file.
    2. Generate embeddings for the 'pdt_inclexcl_ENG_CONTENT' field if not already present.
    3. Generate embeddings for the 'pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED' field if not already present.
    """
    field_inclexcl = "pdt_inclexcl_ENG_CONTENT"
    embeddings_inclexcl_name = f"embeddings_{field_inclexcl}_{model_name}"
    embeddings_inclexcl_existing_file = fs.find_one(
        {"filename": embeddings_inclexcl_name}
    )

    field_description = "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
    embeddings_description_name = f"embeddings_{field_description}_{model_name}"
    remove_object(fs, embeddings_description_name)
    embeddings_description_existing_file = fs.find_one(
        {"filename": embeddings_description_name}
    )

    if (
        not embeddings_inclexcl_existing_file
        or not embeddings_description_existing_file
    ):
        # Load the summarized product textual data from a pickle file.
        df = read_object(fs, "product_textual_lang_summarized")
        df = pd.DataFrame(df)

        # Generate embeddings for the specified text fields if not already present.
        if not embeddings_inclexcl_existing_file:
            get_embeddings(df=df, text_field=field_inclexcl)
        if not embeddings_description_existing_file:
            get_embeddings(df=df, text_field=field_description)
    else:
        print(f"All required embeddings are already present in the database.")


if __name__ == "__main__":
    main()
