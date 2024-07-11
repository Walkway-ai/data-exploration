#!/bin/bash

# Define the arrays for each parameter's choices
city_name=("same")
supplier_code=("different")
average_rating=("any")
start_year=("any")
landmarks=("any")
is_private=("any")
categories=("any")
embedding_fields=("Product Description, Product Title")

# Credentials and other variables
GOOGLE_APPLICATION_CREDENTIALS="ww-da-ingestion-b02370b6a675.json"
OPENAI_API_KEY="sk-proj-ftn7oiSuqjPaX0dyLlhfT3BlbkFJjIh3lsGoiZHbRMvU8klU"
customBuildNumber="10428P6,104357P6,129335P2,13405P16,143594P2,15081P466,16168P1,16168P10,2140P187,252750P2,15081P240,329999P26,3763GATEWAY,47475P7,5250LIBERTYELLIS,5716GOLFWINE,6462P29,7249P9,77354P1,7812P106,7812P126,7845P10,324527P1,9511P25"
PRODUCT_ID="10428P6,104357P6,129335P2,13405P16,143594P2,15081P466,16168P1,16168P10,2140P187,252750P2,15081P240,329999P26,3763GATEWAY,47475P7,5250LIBERTYELLIS,5716GOLFWINE,6462P29,7249P9,77354P1,7812P106,7812P126,7845P10,324527P1,9511P25"

# Export credentials and other variables
export GOOGLE_APPLICATION_CREDENTIALS
export OPENAI_API_KEY

# Iterate over the arrays
for city in "${city_name[@]}"; do
  for supplier in "${supplier_code[@]}"; do
    for rating in "${average_rating[@]}"; do
      for year in "${start_year[@]}"; do
        for landmark in "${landmarks[@]}"; do
          for priv in "${is_private[@]}"; do
            for category in "${categories[@]}"; do
              for embedding in "${embedding_fields[@]}"; do
                python3 src/experiment_product_similarity.py \
                  -credentials "${GOOGLE_APPLICATION_CREDENTIALS}" \
                  -product_id "${PRODUCT_ID}" \
                  -city_name "${city}" \
                  -supplier_code "${supplier}" \
                  -average_rating "${rating}" \
                  -start_year "${year}" \
                  -landmarks "${landmark}" \
                  -is_private "${priv}" \
                  -categories "${category}" \
                  -embedding_fields "${embedding}" \
                  -apikey "${OPENAI_API_KEY}" \
                  -experiment_id "${customBuildNumber}"
              done
            done
          done
        done
      done
    done
  done
done