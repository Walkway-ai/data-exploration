#!/bin/bash

python3 src/generate_product_similarity.py --overwrite --embedding_model 'mean/mean' --embedding_fields description_inclexcl
python3 src/generate_product_similarity.py --overwrite --embedding_model 'mean/mean' --embedding_fields description_title
python3 src/generate_product_similarity.py --overwrite --embedding_model 'mean/mean' --embedding_fields title_inclexcl_tgdescription
python3 src/generate_product_similarity.py --overwrite --embedding_model 'mean/mean' --embedding_fields title_inclexcl_tgdescription_description