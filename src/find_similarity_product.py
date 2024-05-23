import gc
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity

gc.collect()

def find_most_similar_product(embedding, embeddings, product_codes):
    similarities = cosine_similarity(embedding.unsqueeze(0), embeddings)
    most_similar_index = similarities.argsort()[0][-2]  # Index of most similar excluding itself
    return product_codes[most_similar_index]

def main():
    df = pd.read_pickle("tmp/product_textual.pickle")
    df = df.sample(frac=1).reset_index(drop=True)
    print(df)

    combined_embeddings = torch.load("tmp/combined_embeddings.pt")

    given_product_code = input("Enter the PRODUCTCODE: ")
    given_product_index = df.index[df['PRODUCTCODE'] == given_product_code].tolist()

    if not given_product_index:
        print("Given PRODUCTCODE not found.")
        return

    given_product_description = df.loc[df['PRODUCTCODE'] == given_product_code, 'pdt_product_detail_PRODUCTDESCRIPTION'].iloc[0]
    given_embedding = combined_embeddings[given_product_index[0]]
    product_codes = df["PRODUCTCODE"].tolist()
    most_similar_product = find_most_similar_product(given_embedding, combined_embeddings, product_codes)
    most_similar_product_description = df.loc[df['PRODUCTCODE'] == most_similar_product, 'pdt_product_detail_PRODUCTDESCRIPTION'].iloc[0]
    print("Given PRODUCTCODE Description:", given_product_description)
    print(50*"-")
    print("Most similar PRODUCTCODE Description:", most_similar_product_description)

if __name__ == "__main__":
    # text summarization ?
    #9973P4
    main()