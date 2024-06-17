#!/bin/bash

python3 src/generate_model_embeddings.py --overwrite --embedding_model 'thenlper/gte-large'
python3 src/generate_model_embeddings.py --overwrite --embedding_model 'jina-embeddings-v2-base-en'
python3 src/generate_mean_embeddings.py --overwrite --embedding_models 'thenlper/gte-large,jinaai/jina-embeddings-v2-base-en'
python3 src/generate_product_similarity.py --overwrite --embedding_model 'thenlper/gte-large'
python3 src/generate_product_similarity.py --overwrite --embedding_model 'jinaai/jina-embeddings-v2-base-en'
python3 src/generate_product_similarity.py --overwrite --embedding_model 'mean/mean'