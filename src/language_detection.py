#!/usr/bin/env python
# coding: utf-8

import gc

import pandas as pd
from deep_translator import GoogleTranslator
from langdetect import detect
from tqdm import tqdm

gc.collect()


def detect_language(text):
    try:
        return detect(str(text))
    except Exception:
        return ""


def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def main():
    df = pd.read_pickle("tmp/product_textual.pickle")
    df.fillna("", inplace=True)

    df["pdt_product_detail_PRODUCTDESCRIPTION_lang"] = [
        detect_language(el) for el in tqdm(df["pdt_product_detail_PRODUCTDESCRIPTION"])
    ]

    df["pdt_product_detail_PRODUCTDESCRIPTION_translated"] = [
        translate_text(el) if lang != "en" else el
        for el, lang in tqdm(
            zip(
                df["pdt_product_detail_PRODUCTDESCRIPTION"],
                df["pdt_product_detail_PRODUCTDESCRIPTION_lang"],
            )
        )
    ]

    df = df[
        [
            "PRODUCTCODE",
            "pdt_inclexcl_ENG_CONTENT",
            "pdt_product_detail_PRODUCTDESCRIPTION_translated",
        ]
    ]

    df.to_pickle("tmp/product_textual_lang.pickle")


if __name__ == "__main__":
    main()
