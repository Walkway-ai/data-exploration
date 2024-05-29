#!/usr/bin/env python
# coding: utf-8

import gc
import os

import pandas as pd
from tqdm import tqdm
from transformers import pipeline
import yaml

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
summarization_model = config["summarization-model"]


gc.collect()


def main():
    df = pd.read_pickle("tmp/product_textual_lang.pickle")
    df.fillna("", inplace=True)

    intermediate_file = "tmp/product_textual_lang_summarized_intermediate.pickle"

    if os.path.exists(intermediate_file):
        df_intermediate = pd.read_pickle(intermediate_file)
        descriptions_summarized = df_intermediate[
            "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
        ].tolist()
        start_index = len(descriptions_summarized)
        print(f"Resuming from index {start_index}")
    else:
        descriptions_summarized = []
        start_index = 0

    summarizer = pipeline("summarization", model=summarization_model)

    save_interval = 50

    for i, desc in enumerate(
        tqdm(
            df["pdt_product_detail_PRODUCTDESCRIPTION_translated"][start_index:],
            total=len(df) - start_index,
            desc="Summarizing",
        )
    ):
        if desc:
            summarized_desc = summarizer(
                desc, max_length=100, min_length=30, do_sample=False
            )[0]["summary_text"]
            print(50 * "-" + "SUMMARIZED DESCRIPTION" + 50 * "-")
            print(summarized_desc)
        else:
            summarized_desc = ""

        descriptions_summarized.append(summarized_desc)

        if (i + 1) % save_interval == 0 or (start_index + i + 1) == len(df):
            df_intermediate = df.copy()
            df_intermediate = df_intermediate.iloc[: start_index + i + 1]
            df_intermediate[
                "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
            ] = descriptions_summarized
            df_intermediate.to_pickle(intermediate_file)
            print(f"Saved intermediate results at iteration {start_index + i + 1}")

    df["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"] = descriptions_summarized
    df.to_pickle("tmp/product_textual_lang_summarized.pickle")
    print("Saved final results")

    if os.path.exists(intermediate_file):
        os.remove(intermediate_file)


if __name__ == "__main__":
    main()