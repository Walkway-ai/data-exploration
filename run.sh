#!/bin/bash

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

mkdir tmp

python3 src/bigquery_product_data_retrieval.py
python3 src/product_table_preprocessing.py