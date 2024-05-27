#!/usr/bin/env python
# coding: utf-8

import gc
from transformers import pipeline
import pandas as pd
from tqdm import tqdm

gc.collect()

def main():

    df = pd.read_pickle("tmp/product_textual.pickle")
    df.fillna("", inplace=True)

    model_ckpt = "papluca/xlm-roberta-base-language-detection"
    pipe = pipeline("text-classification", model=model_ckpt)

    result = [pipe(desc, top_k=1, truncation=True) for desc in tqdm(df["pdt_product_detail_PRODUCTDESCRIPTION"], desc="Processing PRODUCTDESCRIPTION languages")]
    df["pdt_product_detail_PRODUCTDESCRIPTION_lang"] = [el[0]["label"] for el in result]

    result = [pipe(content, top_k=1, truncation=True) for content in tqdm(df["pdt_inclexcl_ENG_CONTENT"], desc="Processing ENG_CONTENT languages")]
    df["pdt_inclexcl_ENG_CONTENT_lang"] = [el[0]["label"] for el in result]

    df.to_pickle("tmp/product_textual_lang.pickle")

if __name__ == "__main__":
    main()
c