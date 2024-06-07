import gc

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from mongodb_lib import connect_to_mongodb, read_object, save_object

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Load configuration from yaml file for embedding model.
config_model = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config_model["embedding-model"]
model_name = embedding_model.split("/")[-1]

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
    object_name = f"product_similarities_{model_name}"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file:

        # Load the summarized product textual data from MongoDB.
        df = read_object(fs, "product_textual_lang_summarized")
        df = pd.DataFrame(df)

        # Load the combined embeddings from MongoDB.
        combined_embeddings = read_object(
            fs, f"final_embeddings_{model_name}_concatenated_w_tabular"
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
                given_embedding, combined_embeddings
            )

            similar_products = [
                df["PRODUCTCODE"].iloc[el] for el in most_similar_indices
            ]
            similarity_dict[df["PRODUCTCODE"].iloc[given_product_index]] = list(
                zip(similar_products, similarity_scores)
            )

        # Save the similarity dictionary to MongoDB.
        save_object(fs=fs, object=similarity_dict, object_name=object_name)

    else:
        print("Similarity data already exists in MongoDB. Skipping computation.")


if __name__ == "__main__":
    main()
