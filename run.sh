#!/bin/bash

set -e

output_file="run.log"
sudo rm -f "$output_file"
exec > >(tee -a "$output_file") 2>&1

sudo rm -rf /root/.cache

sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove

sudo apt install python3-pip
sudo apt install virtualenv

sudo rm -rf venv
virtualenv venv
source venv/bin/activate

pip install -r requirements.txt

mkdir tmp reports

#python3 src/retrieve_bigquery_data.py
#python3 src/generate_product_data.py
#python3 src/categorize_tabular_data.py
python3 src/embed_textual_data.py

deactivate