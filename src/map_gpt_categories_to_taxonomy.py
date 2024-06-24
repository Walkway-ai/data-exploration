#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import yaml
import gc
from mongodb_lib import *
import argparse
from openai_handlers import query_gpt_with_history
import ast

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", action="store_true", help="Enable overwrite mode"
    )
    parser.add_argument("--model_name", type=str, required=True, help="OpenAI model.")
    parser.add_argument("--apikey", type=str, required=True, help="OpenAI API key.")

    args = parser.parse_args()

    model_name = args.model_name
    apikey = args.apikey

    object_name = f"product_textual_lang_summarized_subcategories_walkway"
    existing_file = fs.find_one({"filename": object_name})

    if not existing_file or args.overwrite:

        taxonomy = pd.read_excel("Categories.xlsx")

        possible_values = list(taxonomy["Sub-category"])
        possible_values = list(set([el.split(": ")[1] for el in possible_values]))

        annotated_data = read_object(fs, "product_textual_lang_summarized_subcategories")
        annotated_data = pd.DataFrame(annotated_data)
        annotated_data = annotated_data.explode("sub_categories_gpt4o")
        gpt_fields = list(set(annotated_data["sub_categories_gpt4o"]))

        same_fields = [el for el in gpt_fields if el in possible_values]
        pctg = len(same_fields)*100/len(possible_values)
        print(f"{pctg} % of the GPT fields are present in the original taxonomy.")
        different_fields = [el for el in gpt_fields if el not in possible_values]
        different_fields = [el for el in different_fields if str(el)!="nan"]

        missing_fields = [el for el in possible_values if el not in gpt_fields]
        pctg = len(missing_fields)*100/len(possible_values)
        print(f"{pctg} % of the taxonomy fields are not present in the GPT fields.")

        conversation_history = [
            {"role": "system", "content": "Hello! How can I assist you today?"}
        ]

        initial_prompt = (
            "You are an expert in the tourism industry with a deep understanding of activity and tour taxonomy. "
            "I will provide you with two lists: one containing sub-categories from an internal taxonomy (INTERNAL) "
            "and another containing sub-categories from an external taxonomy (EXTERNAL). "
            "Your task is to map each sub-category from the INTERNAL list to one element in the EXTERNAL list. "
            "Your output should be a Python dictionary that adheres to the following criteria: "
            "1. Each key in the dictionary should be an element from the INTERNAL list. "
            "2. Each value should be the corresponding synonym from the EXTERNAL list. "
            "3. Mappings should be conservative. For example, 'Drawing Classes' can be mapped to 'Painting, Drawing & Modeling Courses' (since 'Drawing Classes' fits within this category). "
            "However, 'Classes & Workshops' should not be mapped to 'Adult Evening Classes' (as not all classes and workshops are for adults). "
            "4. If a key from the INTERNAL list has no similar element in the EXTERNAL list, do not add this key to the dictionary. "
            "5. Ensure that all keys belong to the INTERNAL list and all values belong to the EXTERNAL list. "
            "Return only a Python-formatted dictionary with no additional text. "
            "Are you ready to start?"
        )

        result = query_gpt_with_history(
            apikey, initial_prompt, model_name, conversation_history
        )
        result = result.choices[0].message.content
        conversation_history.append({"role": "user", "content": initial_prompt})
        conversation_history.append({"role": "system", "content": result})

        prompt = f"INTERNAL: {str(different_fields)} EXTERNAL: {str(possible_values)}"

        result = query_gpt_with_history(
            apikey, prompt, model_name, conversation_history
        )
        result = result.choices[0].message.content
        s = result.find("{")
        e = result.rfind("}")
        result = result[s : e + 1]
        result = ast.literal_eval(result)

        # Make sure the dictionary only contains values that exist in the original taxonomy

        gpt2taxonomy = {}

        for key in list(result.keys()):

            if result[key] in possible_values:

                gpt2taxonomy[key] = result[key]

        annotated_data["sub-categories-walkway"] = [gpt2taxonomy[el] if el in list(gpt2taxonomy.keys()) else el for el in list(annotated_data["sub_categories_gpt4o"])]
        annotated_data["sub-categories-walkway"] = [el if el in possible_values else "" for el in list(annotated_data["sub-categories-walkway"])]

        annotated_data = annotated_data[["PRODUCTCODE", "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED", "sub-categories-walkway"]]
        annotated_data = annotated_data.groupby(["PRODUCTCODE", "pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"])["sub-categories-walkway"].apply(list).reset_index()

        remove_object(fs=fs, object_name=object_name)
        save_object(fs=fs, object=annotated_data, object_name=object_name)


if __name__ == "__main__":
    main()
