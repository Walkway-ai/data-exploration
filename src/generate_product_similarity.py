import argparse
import gc

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from mongodb_lib import *

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Run garbage collection to free up memory.
gc.collect()


def find_most_similar_products(embedding, embeddings, num_similar=50):
    """
    Find the most similar products based on cosine similarity.

    Parameters:
    embedding (np.ndarray): The embedding of the given product.
    embeddings (np.ndarray): The array of embeddings for all products.
    num_similar (int): The number of similar products to find.

    Returns:
    tuple: Indices of the most similar products and their similarity scores.
    """
    # Reshape the given product embedding for cosine similarity calculation.
    embedding = embedding.reshape(1, -1)

    # Calculate cosine similarity between the given embedding and all embeddings.
    similarities = cosine_similarity(embedding, embeddings)[0]

    # Get indices of the most similar products.
    similar_indices = similarities.argsort()[-(num_similar + 1) : -1][::-1]

    # Get similarity scores of the most similar products.
    similar_scores = similarities[similar_indices]

    return similar_indices, similar_scores


def main():
    """
    Main function to find the most similar products based on embeddings.

    Steps:
    1. Check if the similarity data already exists in MongoDB.
    2. If not, load the product textual data and combined embeddings.
    3. Calculate the most similar products for each product in the dataset.
    4. Save the similarity data to MongoDB.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", action="store_true", help="Enable overwrite mode"
    )
    parser.add_argument(
        "--embedding_model", type=str, required=True, help="The embedding model."
    )

    args = parser.parse_args()

    embedding_model = args.embedding_model
    model_name = embedding_model.split("/")[-1]

    object_name = f"product_similarities_{model_name}_title_inclexcl_tgdescription"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file or args.overwrite:

        # Load the summarized product textual data from MongoDB.
        df = read_object(fs, "product_textual_lang_summarized")
        df = pd.DataFrame(df)

        # Load the combined embeddings from MongoDB.
        combined_embeddings = read_object(
            fs, f"final_embeddings_{model_name}"
        )

        combined_embeddings = np.array(combined_embeddings)

        similarity_dict = {}

        for given_product_index in tqdm(
            range(len(df["PRODUCTCODE"])), desc="Calculating similarities"
        ):
            # Get the embedding of the given product.
            given_embedding = combined_embeddings[given_product_index]

            # Find the most similar products.
            most_similar_indices, similarity_scores = find_most_similar_products(
                given_embedding, combined_embeddings, num_similar=200
            )

            similar_products = [
                df["PRODUCTCODE"].iloc[el] for el in most_similar_indices
            ]
            similarity_dict[df["PRODUCTCODE"].iloc[given_product_index]] = list(
                zip(similar_products, similarity_scores)
            )

        # Save the similarity dictionary to MongoDB.
        remove_object(fs=fs, object_name=object_name)
        save_object(fs=fs, object=similarity_dict, object_name=object_name)

    else:
        print("Skipping product similarity.")


if __name__ == "__main__":
    main()
