import argparse
import gc

import pandas as pd
import yaml

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

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    product_id = args.product_id
    city_name = args.city_name
    supplier_code = args.supplier_code

    object_name = f"product_similarities_{model_name}"
    existing_file = fs.find_one({"filename": object_name})

    if existing_file:

        similarity_dict = read_object(fs, object_name)
        similar_products = similarity_dict[product_id]

        df_raw = read_object(fs, "product_tabular")
        df_raw = pd.DataFrame(df_raw)
        df_raw_product = df_raw[df_raw["PRODUCTCODE"] == product_id]

        df_text = read_object(fs, "product_textual_lang_summarized")
        df_text = pd.DataFrame(df_text)
        df_text_product = str(
            list(
                df_text[df_text["PRODUCTCODE"] == product_id][
                    "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
                ]
            )[0]
        )

        str_city = str(list(df_raw_product["pdt_product_detail_VIDESTINATIONCITY"])[0])
        str_supplier_code = str(
            list(df_raw_product["pdt_product_level_SUPPLIERCODE"])[0]
        )

        df_raw_similarity = df_raw[
            df_raw["PRODUCTCODE"].isin([el[0] for el in similar_products])
        ]
        df_text_similarity = df_text[
            df_text["PRODUCTCODE"].isin([el[0] for el in similar_products])
        ]

        df_result = pd.merge(
            df_raw_similarity, df_text_similarity, on="PRODUCTCODE", how="outer"
        )

        if city_name == "same":

            df_result = df_result[
                df_result["pdt_product_detail_VIDESTINATIONCITY"] == str_city
            ]

        if city_name == "different":

            df_result = df_result[
                df_result["pdt_product_detail_VIDESTINATIONCITY"] != str_city
            ]

        if supplier_code == "same":

            df_result = df_result[
                df_result["pdt_product_level_SUPPLIERCODE"] == str_supplier_code
            ]

        if supplier_code == "different":

            df_result = df_result[
                df_result["pdt_product_level_SUPPLIERCODE"] != str_supplier_code
            ]

        df_result["score"] = [
            el[1] for el in similar_products if el[0] in list(df_result["PRODUCTCODE"])
        ]
        df_result = df_result.sort_values(by="score", ascending=False)

        print(50 * "-")
        print(50 * "-")
        print("EXPERIMENT WITH PARAMETERS:")
        print(f"City: {city_name}")
        print(f"Supplier code: {supplier_code}")
        print(f"PRODUCTCODE selected: {product_id}")
        print("Summarized description:")
        print(df_text_product)

        if len(df_result) > 0:

            for index, row in df_result.iterrows():

                print(50 * "-")
                print(f"Similar product: {row['PRODUCTCODE']}")
                print(f"Similarity score: {row['score']}")
                print("")
                print(
                    f"Summarized description:"
                )
                print(str(row['pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED']))

        else:

            print(50 * "-")
            print("No products were found for the combination.")


if __name__ == "__main__":
    main()
