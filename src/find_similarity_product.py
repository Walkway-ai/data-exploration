import gc
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
import yaml
import pickle

config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
embedding_model = config["embedding-model"]
model_name = embedding_model.split("/")[-1]

gc.collect()

def find_most_similar_products(embedding, embeddings, num_similar=5):
    embedding = embedding.reshape(1, -1)
    similarities = cosine_similarity(embedding, embeddings)[0]
    similar_indices = similarities.argsort()[-(num_similar + 1): -1][::-1]
    similar_scores = similarities[similar_indices]
    return similar_indices, similar_scores

def main():
    df = pd.read_pickle("tmp/product_textual_lang_summarized.pickle")
    df = df.sample(frac=1).reset_index(drop=True)
    print(df)

    with open(f"tmp/final_embeddings_{model_name}_concated_tabular.pickle", "rb") as file:
        combined_embeddings = pickle.load(file)

    given_product_code = input("Enter the PRODUCTCODE: ")
    given_product_index = df.index[df["PRODUCTCODE"] == given_product_code].tolist()

    if not given_product_index:
        print("Given PRODUCTCODE not found.")
        return

    given_product_description = df.loc[
        df["PRODUCTCODE"] == given_product_code, "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
    ].iloc[0]

    given_embedding = combined_embeddings[given_product_index[0]]
    print(given_embedding.shape)
    most_similar_indices, similarity_scores = find_most_similar_products(
        given_embedding, combined_embeddings
    )

    print("Given PRODUCTCODE Description:", given_product_description)
    print(50 * "-")
    print("Top 5 most similar products:")

    df_tabular = pd.read_pickle("tmp/product_tabular.pickle")

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
