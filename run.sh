#!/bin/bash

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

mkdir tmp reports

#python3 src/retrieve_bigquery_data.py
#python3 src/generate_product_data.py
#python3 src/categorize_tabular_data.py
python3 src/embed_textual_data.py