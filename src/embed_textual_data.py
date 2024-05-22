#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

gc.collect()


# Function to get embeddings from the model, handling long texts by splitting into chunks
def get_embeddings(text_list, model, tokenizer, max_length=512):
    embeddings = []
    for text in text_list:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=max_length,
        )
        if len(inputs["input_ids"][0]) < max_length:
            # If the text is shorter than max_length, get the embedding directly
            with torch.no_grad():
                outputs = model(**inputs)
            # Mean pooling
            embeddings.append(outputs.last_hidden_state.mean(dim=1))
        else:
            # If the text is longer, split into chunks
            input_ids_chunks = [
                inputs["input_ids"][0][i : i + max_length]
                for i in range(0, len(inputs["input_ids"][0]), max_length)
            ]
            attention_mask_chunks = [
                inputs["attention_mask"][0][i : i + max_length]
                for i in range(0, len(inputs["attention_mask"][0]), max_length)
            ]
            chunk_embeddings = []
            for input_ids, attention_mask in zip(
                input_ids_chunks, attention_mask_chunks
            ):
                chunk_inputs = {
                    "input_ids": input_ids.unsqueeze(0),
                    "attention_mask": attention_mask.unsqueeze(0),
                }
                with torch.no_grad():
                    outputs = model(**chunk_inputs)
                chunk_embeddings.append(outputs.last_hidden_state.mean(dim=1))
            # Average the chunk embeddings
            embeddings.append(torch.mean(torch.stack(chunk_embeddings), dim=0))
    return torch.cat(embeddings)


def main():
    df = pd.read_pickle("tmp/product_textual.pickle")

    # Load the tokenizer and model from Hugging Face
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    # Fill NaNs with empty strings to avoid errors during tokenization
    df["pdt_inclexcl_ENG_CONTENT"].fillna("", inplace=True)
    df["pdt_product_detail_PRODUCTDESCRIPTION"].fillna("", inplace=True)

    # Get embeddings for each text column
    print("Generating embeddings for 'pdt_inclexcl_ENG_CONTENT'...")
    embeddings1 = get_embeddings(
        df["pdt_inclexcl_ENG_CONTENT"].tolist(), model, tokenizer
    )
    print("Generating embeddings for 'pdt_product_detail_PRODUCTDESCRIPTION'...")
    embeddings2 = get_embeddings(
        df["pdt_product_detail_PRODUCTDESCRIPTION"].tolist(), model, tokenizer
    )

    # Combine embeddings into one tensor
    combined_embeddings = torch.cat((embeddings1, embeddings2), dim=1)

    # Optionally, save embeddings for future use
    torch.save(combined_embeddings, "tmp/combined_embeddings.pt")

    print("Embeddings generated and saved successfully.")
    print(combined_embeddings)


if __name__ == "__main__":
    main()
