import gc
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity

gc.collect()

def find_most_similar_products(embedding, embeddings, num_similar=5):
    similarities = cosine_similarity(embedding.unsqueeze(0), embeddings)[0]
    similar_indices = similarities.argsort()[-(num_similar+1):-1][::-1]  # Indices of top num_similar excluding itself
    return similar_indices

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
    most_similar_indices = find_most_similar_products(given_embedding, combined_embeddings)

    print("Given PRODUCTCODE Description:", given_product_description)
    print(50*"-")
    print("Top 5 most similar products:")
    
    df_tabular = pd.read_pickle("tmp/product_tabular.pickle")

    for idx in most_similar_indices:
        similar_product_row = df_tabular.iloc[idx]
        text_data = df.iloc[idx]
        print(similar_product_row)
        print(text_data["pdt_inclexcl_ENG_CONTENT"])
        print(text_data["pdt_product_detail_PRODUCTDESCRIPTION"])
        print(50*"-")

if __name__ == "__main__":
    #text summarization
    #set seed pandas seed and torch seed to be the same always
    #how to handle products that are very similar
    main()