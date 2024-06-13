import argparse
import ast
import gc

import pandas as pd
import yaml

pd.set_option("display.max_columns", None)
import subprocess
from collections import defaultdict

from openai import OpenAI

from mongodb_lib import *

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Load OpenAI key from yaml file
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
apikey = config["openai_key"]

# Run garbage collection to free up memory.
gc.collect()

system_role = "You are an expert in online bookings and product matching in the tourism and entertainment industry. Your expertise includes comparing product descriptions to identify highly similar products."


def query_gpt(df, df_product):

    df = df.astype(str)
    df_product = df_product.astype(str)

    product_features = "\n".join(
        [f"{col}: {list(df_product[col])[0]}" for col in list(df_product.columns)]
    )

    candidates_str = ""

    for _, row in df.iterrows():

        df_now = pd.DataFrame(row).T

        candidates_str_now = "\n".join(
            [f"{col}: {list(df_now[col])[0]}" for col in list(df_now.columns)]
        )

        candidates_str += "\n \n" + candidates_str_now

    prompt = f"Given the following REFERENCE PRODUCT, identify the PRODUCTCODEs of any POSSIBILITY PRODUCTS that are extremely similar to it. Similarity should be determined based on the content of pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED. \nREFERENCE PRODUCT: \n \n{product_features} \n \nPOSSIBILITY PRODUCTS: {candidates_str} \n \nYour answer should contain ONLY a Python list of the PRODUCTCODEs of the similar products (e.g., ['18745FBP', 'H73TOUR2']). If there are no similar products, return an empty list ([])."

    # client = secretmanager.SecretManagerServiceClient()
    # secret_name = "projects/725559607119/secrets/OPENAI_APIKEY_PRODUCTSIMILARITY/versions/1"
    # response = client.access_secret_version(request={"name": secret_name})
    # apikey = response.payload.data.decode("UTF-8")

    client = OpenAI(api_key=apikey)

    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt},
        ],
    )

    return result

def range_to_tuple(range_str):
    if not range_str:
        return (float('-inf'), float('-inf'))
    parts = range_str.strip('()[]').split(',')
    return (float(parts[0]), float(parts[1]))

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
        "-rating", type=str, required=True, help="Tour average rating."
    )
    parser.add_argument(
        "-start_year", type=str, required=True, help="Star year of products."
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
    rating = args.rating
    embedding_model = args.embedding_model

    object_name = f"product_similarities_{embedding_model}"
    existing_file = fs.find_one({"filename": object_name})

    if existing_file:

        city_feature = "pdt_product_detail_VIDESTINATIONCITY"
        supplier_code_feature = "pdt_product_level_SUPPLIERCODE"
        avg_rating_feature = "pdt_product_level_TOTALAVGRATING"

        similarity_dict = read_object(fs, object_name)
        similar_products = similarity_dict[product_id]
        id_score = defaultdict(lambda: 0)
        id_score.update({key: value for key, value in similar_products})

        all_products = list(id_score.keys())
        all_products.append(product_id)

        df_raw = read_object(fs, "product_tabular")
        df_raw = pd.DataFrame(df_raw)
        avg_rating_possible_values = list(set(df_raw[avg_rating_feature]))
        avg_rating_possible_values = sorted(avg_rating_possible_values, key=range_to_tuple)
        df_raw = df_raw[df_raw["PRODUCTCODE"].isin(all_products)]

        df_text = read_object(fs, "product_textual_lang_summarized")
        df_text = pd.DataFrame(df_text)
        df_text = df_text[df_text["PRODUCTCODE"].isin(all_products)]

        df = pd.merge(df_raw, df_text, on="PRODUCTCODE", how="outer")

        del df["pdt_product_detail_PRODUCTDESCRIPTION_translated"]

        # Product features
        df_product = df[df["PRODUCTCODE"] == product_id]
        df = df[df["PRODUCTCODE"] != product_id]

        if city_name == "same":

            df = df[df[city_feature] == str(list(df_product[city_feature])[0])]

        if city_name == "different":

            df = df[df[city_feature] != str(list(df_product[city_feature])[0])]

        if supplier_code == "same":

            df = df[
                df[supplier_code_feature]
                == str(list(df_product[supplier_code_feature])[0])
            ]

        if supplier_code == "different":

            df = df[
                df[supplier_code_feature]
                != str(list(df_product[supplier_code_feature])[0])
            ]

        product_avg_rating = str(list(df_product[avg_rating_feature])[0])
        avg_rating_index = avg_rating_possible_values.index(product_avg_rating)

        if rating == "similar":

            possible_values = avg_rating_possible_values[avg_rating_index-2:avg_rating_index+2]

            df = df[
                df[avg_rating_feature].isin(possible_values)
            ]

        if rating == "different":

            possible_values = avg_rating_possible_values[:avg_rating_index-2] + avg_rating_possible_values[avg_rating_index+2:]

            product_avg_rating[:avg_rating_index-2:avg_rating_index+2]

            df = df[
                df[avg_rating_feature].isin(possible_values)
            ]

        # Only retrieve products from start_year

        print(df)

        import sys
        sys.exit()

        df["score"] = [id_score[p_id] for p_id in list(df["PRODUCTCODE"])]

        df = df.sort_values(by="score", ascending=False)

        del df["score"]

        df_product = df_product[
            ["PRODUCTCODE", "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"]
        ]
        df = df[["PRODUCTCODE", "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"]]

        # Take top k
        df = df[:20]

        result = query_gpt(df, df_product)

        subprocess.run(["clear"])

        print(50 * "-")
        print("")
        print("EXPERIMENT WITH PARAMETERS:")
        print(f"City: {city_name}")
        print(f"Supplier code: {supplier_code}")
        print(f"Embedding model: {embedding_model}")

        product_features = "\n".join(
            [f"{col}: {list(df_product[col])[0]}" for col in list(df_product.columns)]
        )
        product_features = product_features.replace(
            "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED", "Summarized description"
        )

        print(product_features)

        print(50 * "-")
        print("")
        print("RESULTS WITHOUT OPENAI:")
        print("")

        df_raw = df[:3]

        for _, row in df_raw.iterrows():

            df_now = pd.DataFrame(row).T

            result_features = "\n".join(
                [f"{col}: {list(df_now[col])[0]}" for col in list(df_now.columns)]
            )
            result_features = result_features.replace(
                "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED",
                "Summarized description",
            )

            print(result_features)
            print("")

        print(50 * "-")
        print("")
        print("RESULTS WITH OPENAI:")
        print("")

        try:

            result = ast.literal_eval(result.choices[0].message.content)

            if len(result) > 0:

                result = result[:3]

                df_openai = df[df["PRODUCTCODE"].isin(result)]

                for _, row in df_openai.iterrows():

                    df_now = pd.DataFrame(row).T

                    result_features = "\n".join(
                        [
                            f"{col}: {list(df_now[col])[0]}"
                            for col in list(df_now.columns)
                        ]
                    )
                    result_features = result_features.replace(
                        "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED",
                        "Summarized description",
                    )

                    print(result_features)
                    print("\n")

            else:

                print("No products were found for the combination.")

        except Exception as e:

            print("No products were found for the combination.")


if __name__ == "__main__":
    main()
