import argparse
import gc

import pandas as pd
import yaml
from collections import defaultdict
from mongodb_lib import *
from openai import GPT, ClassificationRequest

# Initialize your ChatGPT instance
gpt = GPT(engine="text-davinci", api_key="sk-proj-oZzPbmxH9ozD9MkvLvWBT3BlbkFJGCJXmNzO5IYFmUZ68Wrm")

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Run garbage collection to free up memory.
gc.collect()

def query_gpt(df, df_product):

    df = df.astype(str)
    df_product = df_product.astype(str)

    product_features = ' '.join(['{}_{}'.format(col, val) for col, val in df_product.items()])

    for _, row in df.iterrows():

        current_features = ' '.join(['{}_{}'.format(col, val) for col, val in row.items()])
        
        similarity_score = gpt.classification([product_features, current_features])

        print(row['PRODUCTCODE'], similarity_score)

def main():

    parser = argparse.ArgumentParser(
        description="Process product similarity experiment parameters."
    )

    # Add arguments
    parser.add_argument(
        "-product_id", type=str, required=True, help="The ID of the product."
    )
    parser.add_argument(
        "-city_name", type=str, required=True, help="The name of the city."
    )
    parser.add_argument(
        "-supplier_code", type=str, required=True, help="Supplier code."
    )
    parser.add_argument(
        "-embedding_model", type=str, required=True, help="Embedding model."
    )

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    product_id = args.product_id
    city_name = args.city_name
    supplier_code = args.supplier_code
    embedding_model = args.embedding_model

    object_name = f"product_similarities_{embedding_model}"
    existing_file = fs.find_one({"filename": object_name})

    city_feature = "pdt_product_detail_VIDESTINATIONCITY"
    supplier_code_feature = "pdt_product_level_SUPPLIERCODE"

    if existing_file:

        similarity_dict = read_object(fs, object_name)
        similar_products = similarity_dict[product_id]
        id_score = defaultdict(lambda: 0)
        id_score.update({key: value for key, value in similar_products})

        all_products = list(id_score.keys())
        all_products.append(product_id)

        df_raw = read_object(fs, "product_tabular")
        df_raw = pd.DataFrame(df_raw)
        df_raw = df_raw[df_raw["PRODUCTCODE"].isin(all_products)]

        df_text = read_object(fs, "product_textual_lang_summarized_backup")
        df_text = pd.DataFrame(df_text)
        df_text = df_text[df_text["PRODUCTCODE"].isin(all_products)]

        df = pd.merge(df_raw, df_text, on="PRODUCTCODE", how="outer")

        del df["pdt_product_detail_PRODUCTDESCRIPTION_translated"]

        # Product features
        df_product = df.iloc[-1]
        df = df[:-1]

        if city_name == "same":

            df = df[
                df[city_feature] == str(df_product[city_feature])
            ]

        if city_name == "different":

            df = df[
                df[city_feature] != str(df_product[city_feature])
            ]

        if supplier_code == "same":

            df = df[
                df[supplier_code_feature] == str(df_product[supplier_code_feature])
            ]

        if supplier_code == "different":

            df = df[
                df[supplier_code_feature] != str(df_product[supplier_code_feature])
            ]

        # Take top 5
        df = df[:5]

        del df[city_feature]
        del df[supplier_code_feature]

        result = query_gpt(df, df_product)

        import sys

        sys.exit()

        print(50 * "-")
        print(50 * "-")
        print("EXPERIMENT WITH PARAMETERS:")
        print(f"City: {city_name}")
        print(f"Supplier code: {supplier_code}")
        print(f"Embedding model: {embedding_model}")
        print(f"PRODUCTCODE selected: {product_id}")
        print("Summarized description:")
        print(df_text_product)

        if len(df_result) > 0:

            print(50 * "-")
            print(50 * "-")
            print("RESULTS")
            print(50 * "-")

            for index, row in df_result.iterrows():

                print(50 * "-")
                print(f"Similar product: {row['PRODUCTCODE']}")
                print(f"Similarity score: {row['score']}")
                print("")
                print(f"Summarized description:")
                print(str(row["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"]))

        else:

            print(50 * "-")
            print("No products were found for the combination.")


if __name__ == "__main__":
    main()
