#!/bin/bash

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

#bigquery_product_data_retrieval.ipynb
#product_table_preprocessing.ipynb