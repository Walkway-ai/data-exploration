import argparse
import ast
import gc
import re
from collections import defaultdict

import gspread
import pandas as pd
import yaml
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI

from mongodb_lib import *

# Load configuration from yaml file for MongoDB connection.
config = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config)

# Run garbage collection to free up memory.
gc.collect()

system_role = "You are an expert in online bookings and product matching in the tourism and entertainment industry. Your expertise includes comparing product descriptions to identify highly similar products."


def append_to_google_sheets(credentials_file, results_out):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet
    sheet = client.open("WalkwayAI - Product Similarity").sheet1

    # Append data

    for line in results_out:

        if line:

            if isinstance(line[0], list):

                for l_ in line:

                    sheet.append_row(l_)

            else:

                sheet.append_row(line)


def query_gpt(apikey, text_field, df, df_product):

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

    prompt = f"Given the following REFERENCE PRODUCT, identify the PRODUCTCODEs of any POSSIBILITY PRODUCTS that are extremely similar to it. Similarity should be determined based on the content of {text_field}, and similar products include the same activities (e.g. a tour in the same place, or the same activity). \nREFERENCE PRODUCT: \n \n{product_features} \n \nPOSSIBILITY PRODUCTS: {candidates_str} \n \nYour answer should contain ONLY a Python list of the PRODUCTCODEs of the similar products (e.g., ['18745FBP', 'H73TOUR2']). If there are no similar products, return an empty list ([])."

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
        return (float("-inf"), float("-inf"))
    parts = range_str.strip("()[]").split(",")
    return (float(parts[0]), float(parts[1]))


def landmarks_are_the_same(list1, list2):

    return list(sorted(list1)) == list(sorted(list2))


def main():

    parser = argparse.ArgumentParser(
        description="Process product similarity experiment parameters."
    )

    # Add arguments
    parser.add_argument(
        "-credentials",
        required=True,
        help="Path to Google Sheets credentials JSON file",
    )
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
        "-average_rating", type=str, required=True, help="Tour average rating."
    )
    parser.add_argument(
        "-tour_grade_code", type=str, required=True, help="Tour grade code."
    )
    parser.add_argument(
        "-start_year", type=str, required=True, help="Star year of products."
    )
    parser.add_argument(
        "-landmarks", type=str, required=True, help="Landmarks of the product."
    )
    parser.add_argument(
        "-is_private",
        type=str,
        required=True,
        help="Whether the activity is private or not.",
    )
    parser.add_argument(
        "-subcategories",
        type=str,
        required=True,
        help="Sub-categories of Walkway AI's taxonomy.",
    )
    parser.add_argument(
        "-embedding_model", type=str, required=True, help="Embedding model."
    )
    parser.add_argument("-apikey", type=str, required=True, help="OpenAI API key.")
    parser.add_argument("-experiment_id", type=str, required=True, help="Experiment ID")

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    product_id = args.product_id
    city_name = args.city_name
    supplier_code = args.supplier_code
    average_rating = args.average_rating
    tour_grade_code = args.tour_grade_code
    start_year = args.start_year
    landmarks = args.landmarks
    is_private = args.is_private
    subcategories = args.subcategories
    embedding_model = args.embedding_model
    apikey = args.apikey
    experiment_id = args.experiment_id

    object_name = f"product_similarities_{embedding_model}"
    existing_file = fs.find_one({"filename": object_name})

    if existing_file:

        city_feature = "pdt_product_detail_VIDESTINATIONCITY"
        supplier_code_feature = "pdt_product_level_SUPPLIERCODE"
        avg_rating_feature = "pdt_product_level_TOTALAVGRATING"
        tour_grade_code_feature = "pdt_tourgrades_TOURGRADECODE"
        time_feature = "bookings_MOSTRECENTORDERDATE"
        private_feature = "pdt_product_level_ISPRIVATETOUR"
        text_field = "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
        product_field = "PRODUCTCODE"

        similarity_dict = read_object(fs, object_name)
        similar_products = similarity_dict[product_id]
        id_score = defaultdict(lambda: 0)
        id_score.update({key: value for key, value in similar_products})

        all_products = list(id_score.keys())
        all_products.append(product_id)

        df_raw = read_object(fs, "product_tabular")
        df_raw = pd.DataFrame(df_raw)

        avg_rating_possible_values = sorted(
            list(set(df_raw[avg_rating_feature])), key=range_to_tuple
        )
        df_raw_possible = df_raw[df_raw[product_field].isin(all_products)]

        df_text = read_object(fs, "product_textual_lang_summarized")
        df_text = pd.DataFrame(df_text)
        df_text_possible = df_text[df_text[product_field].isin(all_products)]

        df = pd.merge(df_raw_possible, df_text_possible, on=product_field, how="outer")

        df = df[
            [
                product_field,
                text_field,
                city_feature,
                supplier_code_feature,
                avg_rating_feature,
                tour_grade_code_feature,
                time_feature,
                private_feature,
            ]
        ]

        # Product features
        df_product = df[df[product_field] == product_id]
        df = df[df[product_field] != product_id]

        # Sort by scores
        df["score"] = [id_score[p_id] for p_id in list(df[product_field])]
        df = df.sort_values(by="score", ascending=False)
        del df["score"]

        print(f"Number of initial candidates: {df.shape[0]}")

        ## CITY FILTER

        if city_name == "same":

            df = df[df[city_feature] == str(list(df_product[city_feature])[0])]

        print(f"Number of candidates after the city filter: {df.shape[0]}")

        ## SUPPLIER CODE FILTER

        if supplier_code == "different":

            df = df[
                df[supplier_code_feature]
                != str(list(df_product[supplier_code_feature])[0])
            ]

        print(f"Number of candidates after the supplier code filter: {df.shape[0]}")

        ## AVERAGE RATING FILTER

        product_avg_rating = str(list(df_product[avg_rating_feature])[0])
        avg_rating_index = avg_rating_possible_values.index(product_avg_rating)

        if average_rating == "similar":

            possible_values = avg_rating_possible_values[
                avg_rating_index - 1 : avg_rating_index + 2
            ]

            df = df[df[avg_rating_feature].isin(possible_values)]

        print(f"Number of candidates after the average rating filter: {df.shape[0]}")

        ## TOUR GRADE CODE FILTER

        if tour_grade_code == "same":

            possible_values = list(df_product[tour_grade_code_feature])[0].split(";")

            df[tour_grade_code_feature] = [
                x.split(";") for x in df[tour_grade_code_feature]
            ]
            is_present = [
                set(x) & set(possible_values) for x in df[tour_grade_code_feature]
            ]
            bools_list = [bool(s) for s in is_present]
            df = df[bools_list]

        print(f"Number of candidates after the tour grade code filter: {df.shape[0]}")

        ## START YEAR FILTER

        if start_year != "any":

            df["year"] = pd.to_datetime(df[time_feature], unit="ms")
            df["year"] = df["year"].dt.year

            df = df[df["year"] >= int(start_year)]
            del df["year"]

        print(f"Number of candidates after the year filter: {df.shape[0]}")

        ## LANDMARKS FILTER

        d_landmarks = {}

        one_hot_encoding = read_object(fs, "one_hot_encoding_landmarks")
        name_landmarks = read_object(fs, "name_landmarks")
        list_products = list(df_raw[product_field])

        idx_product = list_products.index(product_id)
        which_landmarks = one_hot_encoding[idx_product]
        which_landmarks = [bool(x) for x in which_landmarks]
        names_landmarks_product = [
            elem for elem, flag in zip(name_landmarks, which_landmarks) if flag
        ]

        if names_landmarks_product:

            d_landmarks[product_id] = names_landmarks_product

            if landmarks == "same":

                final_candidates = list()

                for candidate in list(df[product_field]):

                    idx_candidate = list_products.index(candidate)
                    which_landmarks = one_hot_encoding[idx_candidate]
                    which_landmarks = [bool(x) for x in which_landmarks]
                    names_landmarks_candidate = [
                        elem
                        for elem, flag in zip(name_landmarks, which_landmarks)
                        if flag
                    ]
                    result = landmarks_are_the_same(
                        names_landmarks_product, names_landmarks_candidate
                    )

                    if result:

                        final_candidates.append(candidate)
                        d_landmarks[candidate] = names_landmarks_candidate

                df = df[df[product_field].isin(final_candidates)]

        print(f"Number of candidates after the landmarks filter: {df.shape[0]}")

        ## PRIVATE OPTION FILTER

        if is_private == "same":

            df = df[df[private_feature] == str(list(df_product[private_feature])[0])]

        print(f"Number of candidates after the private filter: {df.shape[0]}")

        ## SUB-CATEGORY FILTER

        print(subcategories)

        if subcategories == "same":

            annotated_data = read_object(
                fs, "product_textual_lang_summarized_subcategories_walkway"
            )
            annotated_data = pd.DataFrame(annotated_data)

            annotated_data = annotated_data.set_index("PRODUCTCODE")[
                "sub-categories-walkway"
            ].to_dict()
            product_subcategories = annotated_data[product_id]

            l_pd = list()

            for prd_ in list(df[product_field]):

                if set(product_subcategories).issubset(set(annotated_data[prd_])):

                    l_pd.append(prd_)

            df = df[df[product_field].isin(l_pd)]

        del df[city_feature]
        del df[supplier_code_feature]
        del df[avg_rating_feature]
        del df[tour_grade_code_feature]
        del df[time_feature]
        del df[private_feature]

        del df_product[city_feature]
        del df_product[supplier_code_feature]
        del df_product[avg_rating_feature]
        del df_product[tour_grade_code_feature]
        del df_product[time_feature]
        del df_product[private_feature]

        product_features = "\n".join(
            [f"{col}: {list(df_product[col])[0]}" for col in list(df_product.columns)]
        )
        product_features = product_features.replace(
            text_field, "Summarized description"
        )

        df_no_openai = df[:10]

        result_features_wo_openai = list()

        for _, row in df_no_openai.iterrows():

            df_now = pd.DataFrame(row).T

            result_features = "\n".join(
                [f"{col}: {list(df_now[col])[0]}" for col in list(df_now.columns)]
            )
            result_features = result_features.replace(
                text_field,
                "Summarized description",
            )

            result_features_wo_openai.append(result_features.split("\n"))

        try:

            df_openai = df[:30]
            result = query_gpt(apikey, text_field, df_openai, df_product)
            result = re.findall(r"\[.*?\]", result.choices[0].message.content)[0]
            result = ast.literal_eval(result)

            if len(result) > 0:

                result = result[:10]

                df_openai = df_openai[df_openai[product_field].isin(result)]

                result_features_w_openai = list()

                for _, row in df_openai.iterrows():

                    df_now = pd.DataFrame(row).T

                    result_features = "\n".join(
                        [
                            f"{col}: {list(df_now[col])[0]}"
                            for col in list(df_now.columns)
                        ]
                    )
                    result_features = result_features.replace(
                        text_field,
                        "Summarized description",
                    )

                    result_features_w_openai.append(result_features.split("\n"))

        except Exception:

            print("No products were found for the combination.")

        columns = [
            "Experiment ID",
            "City",
            "Supplier Code",
            "Average Rating",
            "Tour Grade Code",
            "Start Year",
            "Landmarks",
            "Private",
            "Embedding Model",
        ]

        results_out = [
            experiment_id,
            city_name,
            supplier_code,
            average_rating,
            tour_grade_code,
            start_year,
            landmarks,
            is_private,
            embedding_model,
        ]

        results_out = [
            columns,
            results_out,
            product_features.split("\n"),
            ["SIMILAR PRODUCTS WITHOUT OPENAI"],
            result_features_wo_openai,
            ["SIMILAR PRODUCTS WITH OPENAI"],
            result_features_w_openai,
            ["*****"],
        ]

        append_to_google_sheets(args.credentials, results_out)


if __name__ == "__main__":
    main()
