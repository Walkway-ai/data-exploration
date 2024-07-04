#!/usr/bin/env python
# coding: utf-8

import argparse
import gc

import pandas as pd
import torch
import yaml
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import AutoModel

from mongodb_lib import *

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()


def get_embeddings(texts, field_name, embedding_model, model_name):
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
    for text in tqdm(texts):
        embedding = model.encode([text])
        embeddings.append(embedding[0])

    # Convert embeddings to a torch tensor and save to file.
    embeddings = torch.tensor(embeddings)
    object_name = f"embeddings_{field_name}_{model_name}"
    remove_object(fs=fs, object_name=object_name)
    save_object(fs=fs, object=embeddings, object_name=object_name)


def main():
    """
    Main function to generate embeddings for product text fields.

    Steps:
    1. Load the summarized product textual data from a pickle file.
    2. Generate embeddings for the 'pdt_inclexcl_ENG_CONTENT' field if not already present.
    3. Generate embeddings for the 'pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED' field if not already present.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", action="store_true", help="Enable overwrite mode"
    )
    parser.add_argument(
        "--embedding_model", type=str, required=True, help="The embedding model."
    )

    args = parser.parse_args()

    embedding_model = args.embedding_model
    model_name = embedding_model.split("/")[-1]

    field_description = "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
    embeddings_description_name = f"embeddings_{field_description}_{model_name}"
    embeddings_description_file = fs.find_one(
        {"filename": embeddings_description_name}
    )

    field_inclexcl = "pdt_inclexcl_ENG_CONTENT_translated"
    embeddings_inclexcl_name = f"embeddings_{field_inclexcl}_{model_name}"
    embeddings_inclexcl_file = fs.find_one(
        {"filename": embeddings_inclexcl_name}
    )

    field_producttitle = "pdt_product_detail_PRODUCTTITLE_translated"
    embeddings_producttitle_name = f"embeddings_{field_producttitle}_{model_name}"
    embeddings_producttitle_file = fs.find_one(
        {"filename": embeddings_producttitle_name}
    )

    field_tourgradedescription = "pdt_product_detail_TOURGRADEDESCRIPTION"
    embeddings_tourgradedescription_name = f"embeddings_{field_tourgradedescription}_{model_name}"
    embeddings_tourgradedescription_file = fs.find_one(
        {"filename": embeddings_tourgradedescription_name}
    )

    if (
        not embeddings_description_file
        or not embeddings_inclexcl_file
        or not embeddings_producttitle_file
        or not embeddings_tourgradedescription_file
        or args.overwrite
    ):
        # Load the summarized product textual data from a pickle file.
        df = read_object(fs, "product_textual_lang_summarized")
        df = pd.DataFrame(df)

        df_cont = read_object(fs, "product_textual_lang")
        df_cont = pd.DataFrame(df_cont)

        get_embeddings(
            texts=list(df[field_description]),
            field_name=field_description,
            embedding_model=embedding_model,
            model_name=model_name,
        )

        get_embeddings(
            texts=list(df_cont[field_inclexcl]),
            field_name=field_inclexcl,
            embedding_model=embedding_model,
            model_name=model_name,
        )

        get_embeddings(
            texts=list(df_cont[field_producttitle]),
            field_name=field_producttitle,
            embedding_model=embedding_model,
            model_name=model_name,
        )

        # get_embeddings(
        #     texts=list(df_cont[field_tourgradedescription]),
        #     embedding_model=embedding_model,
        #     model_name=model_name,
        # )
    else:
        print("Skipping embeddings.")


if __name__ == "__main__":
    main()
