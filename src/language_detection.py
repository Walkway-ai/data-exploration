#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
import yaml
from deep_translator import GoogleTranslator
from langdetect import detect
from tqdm import tqdm

from mongodb_lib import connect_to_mongodb, read_object, save_object

# Load configuration from yaml file for MongoDB connection.
config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()


def detect_language(text):
    """
    Detect the language of a given text.

    Parameters:
    text (str): The text to detect the language of.

    Returns:
    str: The detected language code or an empty string if detection fails.
    """
    try:
        return detect(text)
    except Exception as e:
        print(f"Language detection error: {e}")
        return ""


def translate_text(text):
    """
    Translate a given text to English.

    Parameters:
    text (str): The text to translate.

    Returns:
    str: The translated text or the original text if translation fails.
    """
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def main():
    """
    Main function to process and translate product descriptions.

    Steps:
    1. Load the textual product data from MongoDB.
    2. Fill any missing values in the DataFrame.
    3. Detect the language of product descriptions.
    4. Translate non-English product descriptions to English.
    5. Filter the DataFrame to include relevant columns.
    6. Save the processed DataFrame to MongoDB.
    """

    object_name = "product_textual_lang"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file:

        # Load the textual product data from MongoDB.
        df = read_object(fs, "product_textual")
        df = pd.DataFrame(df)
        # Fill any missing values with an empty string.
        df.fillna("", inplace=True)

        # Detect the language of each product description.
        df["language"] = [
            detect_language(text)
            for text in tqdm(df["pdt_product_detail_PRODUCTDESCRIPTION"])
        ]

        # Translate non-English product descriptions to English.
        df["pdt_product_detail_PRODUCTDESCRIPTION_translated"] = df.apply(
            lambda row: translate_text(row["pdt_product_detail_PRODUCTDESCRIPTION"])
            if row["language"] != "en"
            else row["pdt_product_detail_PRODUCTDESCRIPTION"],
            axis=1,
        )

        # Filter the DataFrame to include only relevant columns.
        df = df[
            [
                "PRODUCTCODE",
                "pdt_inclexcl_ENG_CONTENT",
                "pdt_product_detail_PRODUCTDESCRIPTION_translated",
            ]
        ]

        # Save the processed DataFrame to MongoDB.
        save_object(fs=fs, object=df, object_name=object_name)

    else:
        print("Processed data already exists in MongoDB. Skipping processing.")


if __name__ == "__main__":
    main()
