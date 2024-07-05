import argparse
import ast
import gc
import re
from collections import defaultdict

import gspread
import numpy as np
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
    del df["reviews"]
    # df["title"] = [mapping_title[x] for x in df[product_field]]
    df_product = df_product.astype(str)
    # df_product["title"] = [mapping_title[x] for x in df_product[product_field]]

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
        temperature=0.1,
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
        "-start_year", type=str, required=True, help="Star year of products."
    )
    parser.add_argument(
        "-landmarks", type=str, required=True, help="Landmarks of the product."
    )
    parser.add_argument(
        "-prices", type=str, required=True, help="Price ranges of the product."
    )
    parser.add_argument(
        "-is_private",
        type=str,
        required=True,
        help="Whether the activity is private or not.",
    )
    parser.add_argument(
        "-categories",
        type=str,
        required=True,
        help="Categories of Walkway AI's taxonomy.",
    )
    parser.add_argument(
        "-embedding_fields", type=str, required=True, help="Embedding fields."
    )
    parser.add_argument("-apikey", type=str, required=True, help="OpenAI API key.")
    parser.add_argument("-experiment_id", type=str, required=True, help="Experiment ID")

    args = parser.parse_args()

    # Access the arguments
    product_id = args.product_id

    object_name = f"product_similarities_mean_{args.embedding_fields}"
    existing_file = fs.find_one({"filename": object_name})

    if existing_file:

        city_feature = "pdt_product_detail_VIDESTINATIONCITY"
        supplier_code_feature = "pdt_product_level_SUPPLIERCODE"
        avg_rating_feature = "pdt_product_level_TOTALAVGRATING"
        time_feature = "bookings_MOSTRECENTORDERDATE"
        private_feature = "pdt_product_level_ISPRIVATETOUR"
        text_field = "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"
        product_field = "PRODUCTCODE"

        similarity_dict = read_object(fs, object_name)
        similar_products = similarity_dict[args.product_id]
        id_score = defaultdict(lambda: 0)
        id_score.update({key: value for key, value in similar_products})

        all_products = list(id_score.keys())
        all_products.append(args.product_id)

        df_raw = read_object(fs, "product_tabular")
        df_raw = pd.DataFrame(df_raw)

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
                time_feature,
                private_feature,
            ]
        ]

        # Product features
        df_product = df[df[product_field] == args.product_id]

        # Candidate features
        df = df[df[product_field] != args.product_id]

        # Sort by scores
        df["score"] = [id_score[p_id] for p_id in list(df[product_field])]
        df = df.sort_values(by="score", ascending=False)
        del df["score"]

        print(f"Number of initial candidates: {df.shape[0]}")

        ## CITY FILTER

        if args.city_name == "same":

            df = df[df[city_feature] == str(list(df_product[city_feature])[0])]

        print(f"Number of candidates after the city filter: {df.shape[0]}")

        ## SUPPLIER CODE FILTER

        if args.supplier_code == "different":

            df = df[
                df[supplier_code_feature]
                != str(list(df_product[supplier_code_feature])[0])
            ]

        print(f"Number of candidates after the supplier code filter: {df.shape[0]}")

        ## AVERAGE RATING FILTER

        if args.average_rating == "similar":

            try:
                product_avg_rating = float(list(df_product[avg_rating_feature])[0])
            except:
                product_avg_rating = np.nan

            print(list(df_product[avg_rating_feature])[0])
            print(product_avg_rating)
            
            if product_avg_rating:

                tolerance = 0.3 * product_avg_rating
                print(tolerance)
                avg_bool = [abs(product_avg_rating - x) <= tolerance for x in list(df[avg_rating_feature])]
                df = df[avg_bool]

        print(f"Number of candidates after the average rating filter: {df.shape[0]}")

        print(list(df_product[text_field]))
        print(list(df[text_field])[:5])

        import sys
        sys.exit()

        ## START YEAR FILTER

        if args.start_year != "any":

            df["year"] = pd.to_datetime(df[time_feature], unit="ms")
            df["year"] = df["year"].dt.year

            df = df[df["year"] >= int(args.start_year)]
            del df["year"]

        print(f"Number of candidates after the year filter: {df.shape[0]}")

        ## LANDMARKS FILTER

        d_landmarks = {}

        one_hot_encoding = read_object(fs, "one_hot_encoding_landmarks")
        name_landmarks = read_object(fs, "name_landmarks")
        list_products = list(df_raw[product_field])

        idx_product = list_products.index(args.product_id)
        which_landmarks = one_hot_encoding[idx_product]
        which_landmarks = [bool(x) for x in which_landmarks]
        names_landmarks_product = [
            elem for elem, flag in zip(name_landmarks, which_landmarks) if flag
        ]

        if names_landmarks_product:

            d_landmarks[args.product_id] = names_landmarks_product

            if args.landmarks == "same":

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

        if args.is_private == "same":

            df = df[df[private_feature] == str(list(df_product[private_feature])[0])]

        print(f"Number of candidates after the private filter: {df.shape[0]}")

        ## CATEGORY FILTER

        annotated_data = read_object(
            fs, "product_textual_lang_summarized_subcategories_categories_walkway"
        )
        annotated_data = pd.DataFrame(annotated_data)

        annotated_data = annotated_data[[product_field, "categories-walkway"]]

        annotated_data = annotated_data.set_index(product_field)[
            "categories-walkway"
        ].to_dict()

        if args.categories != "any":

            product_categories = annotated_data[args.product_id]

            if product_categories:

                l_pd = list()

                for prd_ in list(df[product_field]):

                    if args.categories == "same":

                        if set(product_categories).issubset(set(annotated_data[prd_])):

                            l_pd.append(prd_)

                    if args.categories == "one":

                        if any(ct in annotated_data[prd_] for ct in product_categories):

                            l_pd.append(prd_)

                df = df[df[product_field].isin(l_pd)]

        print(f"Number of candidates after the category filter: {df.shape[0]}")

        ## PRICES FILTER

        if args.prices != "any":

            price_ranges = read_object(fs, "price_categories_per_product")
            price_ranges = pd.DataFrame(price_ranges)

            price_product_id = price_ranges[price_ranges[product_field] == args.product_id]
            price_product_id = price_product_id[price_product_id["CATEGORY"] == args.prices]
            values_to_be_compared_against = list(price_product_id["ADULTRETAILPRICE"])

            if values_to_be_compared_against:

                final_candidates = list()

                for prd in list(df[product_field]):

                    sbs = price_ranges[price_ranges[product_field] == prd]
                    sbs = sbs[sbs["CATEGORY"] == args.prices]
                    values_candidate = list(sbs["ADULTRETAILPRICE"])

                    for vo in values_to_be_compared_against:
                        for vc in values_candidate:

                            tolerance = 0.3 * vo
                            is_close = abs(vo - vc) <= tolerance

                            if is_close:

                                final_candidates.append(prd)

                df = df[df[product_field].isin(final_candidates)]

        print(f"Number of candidates after the price filter: {df.shape[0]}")

        ## REVIEWS FILTER (sorted)

        product_table = read_object(fs, "product_tables")
        product_table = pd.DataFrame(product_table)

        product_table["pdt_product_level_TOTALREVIEWCOUNT"] = product_table[
            "pdt_product_level_TOTALREVIEWCOUNT"
        ].apply(lambda x: x if x is not None else [])
        product_table["pdt_product_level_TOTALREVIEWCOUNT"] = [
            max([el for el in x if el is not None])
            if len([el for el in x if el is not None]) > 0
            else 0
            for x in product_table["pdt_product_level_TOTALREVIEWCOUNT"]
        ]

        mapping = dict(
            zip(
                product_table[product_field],
                product_table["pdt_product_level_TOTALREVIEWCOUNT"],
            )
        )

        df["reviews"] = [mapping[el] for el in df[product_field]]
        df = df[df["reviews"] != ""]
        df = df[df["reviews"] != 0]
        df = df[df["reviews"] > np.percentile(list(df["reviews"]), 75)]

        print(f"Number of candidates after the reviews filter: {df.shape[0]}")

        # Create dict for product title

        product_table["pdt_product_detail_PRODUCTTITLE"] = product_table[
            "pdt_product_detail_PRODUCTTITLE"
        ].apply(lambda x: x if x is not None else [])
        product_table["pdt_product_detail_PRODUCTTITLE"] = [
            [el for el in x if el is not None][0]
            if len([el for el in x if el is not None]) > 0
            else ""
            for x in product_table["pdt_product_detail_PRODUCTTITLE"]
        ]

        mapping_title = dict(
            zip(
                product_table[product_field],
                product_table["pdt_product_detail_PRODUCTTITLE"],
            )
        )

        del df[city_feature]
        del df[supplier_code_feature]
        del df[avg_rating_feature]
        del df[time_feature]
        del df[private_feature]

        del df_product[city_feature]
        del df_product[supplier_code_feature]
        del df_product[avg_rating_feature]
        del df_product[time_feature]
        del df_product[private_feature]

        output_product_categories = list(set(annotated_data[args.product_id]))
        title = str(mapping_title[args.product_id])
        n_reviews = str(mapping[args.product_id])

        product_features = "\n".join(
            [f"{col}: {list(df_product[col])[0]}" for col in list(df_product.columns)]
        )
        product_features = product_features.replace(
            text_field, "Summarized description"
        )

        product_features = (
            product_features
            + "\n reviews: "
            + str(n_reviews)
            + "\n Category: "
            + str(output_product_categories)
            + "\n Title: "
            + str(title)
        )

        # RAW RESULTS
        df = df[:30]
        df = df.sort_values(by="reviews", ascending=False)

        df_no_openai = df

        result_features_wo_openai = list()

        for _, row in df_no_openai.iterrows():

            df_now = pd.DataFrame(row).T

            product_id = list(df_now[product_field])[0]
            no_openai_product_categories = list(set(annotated_data[product_id]))
            title = str(mapping_title[product_id])

            result_features = "\n".join(
                [f"{col}: {list(df_now[col])[0]}" for col in list(df_now.columns)]
            )
            result_features = result_features.replace(
                text_field,
                "Summarized description",
            )

            result_features = (
                result_features
                + "\n Category: "
                + str(no_openai_product_categories)
                + "\n Title: "
                + str(title)
            )

            result_features_wo_openai.append(result_features.split("\n"))

        result_features_w_openai = list()

        try:

            df_openai = df
            result = query_gpt(args.apikey, text_field, df_openai, df_product)
            result = re.findall(r"\[.*?\]", result.choices[0].message.content)[0]
            result = ast.literal_eval(result)

            if len(result) > 0:

                result = result[:10]

                df_openai = df_openai[df_openai[product_field].isin(result)]

                for _, row in df_openai.iterrows():

                    df_now = pd.DataFrame(row).T

                    product_id = list(df_now[product_field])[0]
                    openai_product_categories = list(set(annotated_data[product_id]))
                    title = str(mapping_title[product_id])

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

                    result_features = (
                        result_features
                        + "\n Category: "
                        + str(openai_product_categories)
                        + "\n Title: "
                        + str(title)
                    )

                    result_features_w_openai.append(result_features.split("\n"))

        except Exception as e:

            print(e)

            print("No products were found for the combination.")

        columns = [
            "Experiment ID",
            "City",
            "Supplier Code",
            "Average Rating",
            "Start Year",
            "Landmarks",
            "Price",
            "Private",
            "Categories",
            "Embedding Model",
        ]

        results_out = [
            args.experiment_id,
            args.city_name,
            args.supplier_code,
            args.average_rating,
            args.start_year,
            args.landmarks,
            args.prices,
            args.is_private,
            args.categories,
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
