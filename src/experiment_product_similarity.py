import argparse
import gc

import pandas as pd
import yaml
import ast
pd.set_option('display.max_columns', None)
from collections import defaultdict
from mongodb_lib import *
from openai import OpenAI

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Run garbage collection to free up memory.
gc.collect()

system_role = "You are an expert in online bookings in the tourism and entertainment industry and can find products that are the same, but with different descriptions."

def query_gpt(df, df_product):

    df = df.astype(str)
    df_product = df_product.astype(str)

    product_features = '; '.join(['{}: {}'.format(col, val) for col, val in df_product.items()])

    candidates_str = ""

    for _, row in df.iterrows():

        candidates_str_now = '; '.join(['{}_{}'.format(col, val) for col, val in row.items()])

        candidates_str += "\n" + candidates_str_now

    prompt = f"Given the following product: \n ----- \n {product_features} \n ----- \n, give me a Python list of all PRODUCTCODE of the products below that are very similar to it, if any (e.g. ['18745FBP', 'H73TOUR2']). If there are none, return an empty list ([]). You should mainly compare the pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED to make your decision. Your answer should only contain a Python list with the results. \n ----- {candidates_str}"

    #client = secretmanager.SecretManagerServiceClient()
    #secret_name = "projects/725559607119/secrets/OPENAI_APIKEY_PRODUCTSIMILARITY/versions/1"
    #response = client.access_secret_version(request={"name": secret_name})
    #apikey = response.payload.data.decode("UTF-8")
    apikey = "sk-proj-JnVgq03M094rYihMyFpeT3BlbkFJGluZobSDuqE8pFb013m7"

    client = OpenAI(api_key=apikey)

    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt},
        ],
    )

    return result

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

        df_text = read_object(fs, "product_textual_lang_summarized")
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

        result = query_gpt(df, df_product)

        try:

            result = ast.literal_eval(result.choices[0].message.content)

            print("EXPERIMENT WITH PARAMETERS:")
            print(f"City: {city_name}")
            print(f"Supplier code: {supplier_code}")
            print(f"Embedding model: {embedding_model}")
            print("")
            print("Product details:")
            
            for column_name, value in df_product.items():
                print(f"{column_name}: {value}")

            if len(result) > 0:

                df = df[df["PRODUCTCODE"].isin(result)]

                print(50 * "-")
                print("RESULTS")
                print(50 * "-")
                print("Similar product details:")
                for column_name, series in df.items():
                    print(f"{column_name}: {series.iloc[0]}")

            else:

                print("No products were found for the combination.")

        except Exception as e:

            print(e)


if __name__ == "__main__":
    main()
