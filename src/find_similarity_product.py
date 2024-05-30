import gc

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics.pairwise import cosine_similarity

from mongodb_lib import *

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Load configuration from yaml file for embedding model.
config_model = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config_model["embedding-model"]
model_name = embedding_model.split("/")[-1]

# Run garbage collection to free up memory.
gc.collect()


def find_most_similar_products(embedding, embeddings, num_similar=5):
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
    Main function to find and display the most similar products.

    Steps:
    1. Load the summarized product textual data from MongoDB.
    2. Shuffle and reset the DataFrame index.
    3. Load the combined embeddings from MongoDB.
    4. Prompt the user to input a PRODUCTCODE.
    5. Find the embedding of the given product and calculate similarity scores.
    6. Display the most similar products and their details.
    """
    # Load the summarized product textual data from MongoDB.
    df = read_object(fs, "tmp/product_textual_lang_summarized.pickle")
    df = pd.DataFrame(df)

    # Shuffle and reset the DataFrame index.
    df = df.sample(frac=1).reset_index(drop=True)
    print(df)

    # Load the combined embeddings from MongoDB.
    combined_embeddings = read_object(
        fs, f"tmp/final_embeddings_{model_name}_concated_tabular.pickle"
    )
    combined_embeddings = np.array(combined_embeddings)

    # Prompt the user to input a PRODUCTCODE.
    given_product_code = input("Enter the PRODUCTCODE: ")
    given_product_index = df.index[df["PRODUCTCODE"] == given_product_code].tolist()

    # Check if the given PRODUCTCODE exists.
    if not given_product_index:
        print("Given PRODUCTCODE not found.")
        return

    # Get the description of the given product.
    given_product_description = df.loc[
        df["PRODUCTCODE"] == given_product_code,
        "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED",
    ].iloc[0]

    # Get the embedding of the given product.
    given_embedding = combined_embeddings[given_product_index[0]]

    # Find the most similar products.
    most_similar_indices, similarity_scores = find_most_similar_products(
        given_embedding, combined_embeddings
    )

    # Display the given product description.
    print("Given PRODUCTCODE Description:", given_product_description)
    print(50 * "-")
    print("Top 5 most similar products:")

    # Load the tabular product data from MongoDB.
    df_tabular = read_object(fs, "tmp/product_tabular.pickle")
    df_tabular = pd.DataFrame(df_tabular)

    # Display the details of the most similar products.
    for idx, score in zip(most_similar_indices, similarity_scores):
        similar_product_row = df_tabular.iloc[idx]
        text_data = df.iloc[idx]
        print(similar_product_row)
        print("Similarity Score:", score)
        print(text_data["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"] + "...")
        print(text_data["pdt_inclexcl_ENG_CONTENT"] + "...")
        print(50 * "-")


if __name__ == "__main__":
    main()
