import argparse
import yaml
import pandas as pd
from tqdm import tqdm
from mongodb_lib import *
import unicodedata
import re
from collections import defaultdict
import numpy as np

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
_, fs, _ = connect_to_mongodb(config_infra)

def find_mentioned_landmarks(description, candidates):

    description = remove_accents(description).lower()

    mentioned_landmarks = []

    for landmark in candidates:
        # Check if the landmark or its aliases are mentioned in the description
        if landmark in description:
            mentioned_landmarks.append(landmark)
        else:
            # Add fuzzy matching or other checks as needed for variations or typos
            pass

    return mentioned_landmarks

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

def generate_variations(keyword):
    variations = set()
    
    # Original keyword
    variations.add(keyword.lower())
    variations.add(remove_accents(keyword).lower())
    
    # Alternative names in parentheses
    match = re.match(r'(.+)\((.+)\)', keyword)

    if match:
        base_name = match.group(1).strip()
        alt_name = match.group(2).strip()
        variations.add(base_name.lower())
        variations.add(remove_accents(base_name).lower())
        variations.add(alt_name.lower())
        variations.add(remove_accents(alt_name).lower())
    
    return variations

def flatten_dict(d):

    flattened_keys = list()

    for city in d.keys():

        for name in list(d[city].values()):

            flattened_keys.append(name)

    return list(sorted(set(flattened_keys)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", help="Enable overwrite mode")
    args = parser.parse_args()

    object_name_one_hot_encoding = "one_hot_encoding_landmarks"
    existing_file_one_hot_encoding = fs.find_one({"filename": object_name_one_hot_encoding})

    object_name_landmarks = "name_landmarks"
    existing_file_name_landmarks = fs.find_one({"filename": object_name_landmarks})

    if not existing_file_one_hot_encoding or not existing_file_name_landmarks or args.overwrite:

        df = read_object(fs, "product_tabular")
        df_text_sum = read_object(fs, "product_textual_lang_summarized")

        df = pd.DataFrame(df)
        df_text_sum = pd.DataFrame(df_text_sum)

        df.fillna("", inplace=True)
        df_text_sum.fillna("", inplace=True)

        assert list(df["PRODUCTCODE"]) == list(df_text_sum["PRODUCTCODE"])

        landmarks = yaml.load(open("landmarks.yaml"), Loader=yaml.FullLoader)

        variations_dict = defaultdict(lambda: defaultdict(list))

        for city in landmarks["destinations"]:

            candidates = landmarks["destinations"].get(city, {}).get("landmarks", [])

            # Generate variations for each place and populate the dictionary
            for place in candidates:

                variations = generate_variations(place)

                for variation in variations:

                    variations_dict[city][variation] = place

        all_landmarks = flatten_dict(variations_dict)
        one_hot_encoding = []

        for city, text_summarized in tqdm(zip(list(df["pdt_product_detail_VIDESTINATIONCITY"]), list(df_text_sum["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"])), total=len(df)):

            candidates = variations_dict[city]

            mentioned_landmarks = find_mentioned_landmarks(text_summarized, candidates)
            mentioned_landmarks = list(sorted(set([candidates[el] for el in mentioned_landmarks])))

            one_hot_encoding_now = []

            for landmark in all_landmarks:
                if landmark in mentioned_landmarks:
                    one_hot_encoding_now.append(1)
                else:
                    one_hot_encoding_now.append(0)

            one_hot_encoding.append(one_hot_encoding_now)

        one_hot_encoding = np.array(one_hot_encoding)
        remove_object(fs=fs, object_name=object_name_one_hot_encoding)
        save_object(fs=fs, object=one_hot_encoding, object_name=object_name_one_hot_encoding)

        remove_object(fs=fs, object_name=object_name_landmarks)
        save_object(fs=fs, object=all_landmarks, object_name=object_name_landmarks)

if __name__ == "__main__":
    main()