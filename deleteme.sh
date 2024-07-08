#!/bin/bash

python3 src/generate_model_embeddings.py --overwrite --embedding_model 'thenlper/gte-large' --embedding_fields description_inclexcl
python3 src/generate_model_embeddings.py --overwrite --embedding_model 'jinaai/jina-embeddings-v2-base-en' --embedding_fields description_inclexcl
python3 src/generate_model_embeddings.py --overwrite --embedding_model 'thenlper/gte-large' --embedding_fields description_title
python3 src/generate_model_embeddings.py --overwrite --embedding_model 'jinaai/jina-embeddings-v2-base-en' --embedding_fields description_title
python3 src/generate_model_embeddings.py --overwrite --embedding_model 'thenlper/gte-large' --embedding_fields title_inclexcl_tgdescription
python3 src/generate_model_embeddings.py --overwrite --embedding_model 'jinaai/jina-embeddings-v2-base-en' --embedding_fields title_inclexcl_tgdescription