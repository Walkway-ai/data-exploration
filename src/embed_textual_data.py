#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import torch
import yaml
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

gc.collect()


def get_embeddings(text_list, model, tokenizer, max_length=512):
    embeddings = []
    for text in tqdm(text_list):
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
    #df = pd.read_pickle("tmp/product_textual_lang_summarized.pickle")
    df = pd.read_pickle("tmp/product_textual_lang_summarized_intermediate.pickle")

    tokenizer = AutoTokenizer.from_pretrained(embedding_model)
    model = AutoModel.from_pretrained(embedding_model)

    text_field = "pdt_inclexcl_ENG_CONTENT"
    print(f"Generating embeddings for {text_field}...")
    embeddings1 = get_embeddings(df[text_field].tolist(), model, tokenizer)

    text_field = "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
    print(f"Generating embeddings for {text_field}...")
    embeddings2 = get_embeddings(df[text_field].tolist(), model, tokenizer)

    combined_embeddings = torch.cat((embeddings1, embeddings2), dim=1)

    torch.save(combined_embeddings, f"tmp/embeddings_{model_name}.pt")

    print("Embeddings generated and saved successfully.")


if __name__ == "__main__":
    main()
