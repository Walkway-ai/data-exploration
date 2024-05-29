#!/usr/bin/env python
# coding: utf-8

import gc
import os
import pandas as pd
from tqdm import tqdm
from transformers import pipeline
import yaml
import concurrent.futures

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
summarization_model = config["summarization-model"]

gc.collect()

def load_model():
    return pipeline("summarization", model=summarization_model)

def summarize_description(summarizer, desc):
    if desc:
        return summarizer(desc, max_length=100, min_length=30, do_sample=False)[0]["summary_text"]
    return ""

def save_intermediate(df, descriptions_summarized, start_index, save_interval, intermediate_file):
    df_intermediate = df.copy()
    df_intermediate = df_intermediate.iloc[: start_index + save_interval]
    df_intermediate["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"] = descriptions_summarized
    df_intermediate.to_pickle(intermediate_file)
    print(f"Saved intermediate results at iteration {start_index + save_interval}")

def main():
    df = pd.read_pickle("tmp/product_textual_lang.pickle")
    df.fillna("", inplace=True)

    intermediate_file = "tmp/product_textual_lang_summarized_intermediate.pickle"

    if os.path.exists(intermediate_file):
        df_intermediate = pd.read_pickle(intermediate_file)
        descriptions_summarized = df_intermediate["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"].tolist()
        start_index = len(descriptions_summarized)
        print(f"Resuming from index {start_index}")
    else:
        descriptions_summarized = []
        start_index = 0

    summarizer = load_model()

    save_interval = 50
    batch_size = 100

    descriptions = df["pdt_product_detail_PRODUCTDESCRIPTION_translated"][start_index:]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in tqdm(range(0, len(descriptions), batch_size), desc="Summarizing", total=len(descriptions) // batch_size):
            batch = descriptions[i:i + batch_size]
            futures = [executor.submit(summarize_description, summarizer, desc) for desc in batch]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            descriptions_summarized.extend(results)

            if (i + batch_size) % save_interval == 0 or (start_index + i + batch_size) >= len(descriptions):
                save_intermediate(df, descriptions_summarized, start_index, i + batch_size, intermediate_file)

    df["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"] = descriptions_summarized
    df.to_pickle("tmp/product_textual_lang_summarized.pickle")
    print("Saved final results")

    if os.path.exists(intermediate_file):
        os.remove(intermediate_file)

if __name__ == "__main__":
    main()
