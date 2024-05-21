#!/bin/bash

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

mkdir tmp reports

#python3 src/retrieve_bigquery_data.py
python3 src/generate_product_data.py