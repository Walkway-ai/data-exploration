#!/usr/bin/env python
# coding: utf-8

import gc
import os

import pandas as pd
import yaml
from tqdm import tqdm
from transformers import pipeline

# Load configuration from yaml file.
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
summarization_model = config["summarization-model"]

# Run garbage collection to free up memory.
gc.collect()


def main():
    """
    Main function to summarize product descriptions.

    Steps:
    1. Load the product textual data from a pickle file.
    2. Check for intermediate results to potentially resume from.
    3. Initialize the summarization pipeline.
    4. Summarize each product description and save intermediate results.
    5. Save the final summarized descriptions as a pickle file.
    6. Clean up any intermediate files.
    """
    # Load the product textual data from a pickle file.
    df = pd.read_pickle("tmp/product_textual_lang.pickle")
    df.fillna("", inplace=True)

    # Define the intermediate file path.
    intermediate_file = "tmp/product_textual_lang_summarized_intermediate.pickle"

    # Check if an intermediate file exists to resume from.
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

    # Initialize the summarization pipeline.
    summarizer = pipeline("summarization", model=summarization_model)

    # Define the interval for saving intermediate results.
    save_interval = 50

    # Loop through each product description, starting from the last saved index.
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
        else:
            summarized_desc = ""

        descriptions_summarized.append(summarized_desc)

        # Save intermediate results at defined intervals or at the end.
        if (i + 1) % save_interval == 0 or (start_index + i + 1) == len(df):
            df_intermediate = df.copy()
            df_intermediate = df_intermediate.iloc[: start_index + i + 1]
            df_intermediate[
                "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
            ] = descriptions_summarized
            df_intermediate.to_pickle(intermediate_file)
            print(f"Saved intermediate results at iteration {start_index + i + 1}")

    # Add the summarized descriptions to the DataFrame and save the final results.
    df["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"] = descriptions_summarized
    df.to_pickle("tmp/product_textual_lang_summarized.pickle")
    print("Saved final results")

    # Remove the intermediate file if it exists.
    if os.path.exists(intermediate_file):
        os.remove(intermediate_file)


if __name__ == "__main__":
    main()
