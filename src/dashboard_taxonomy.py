#!/usr/bin/env python
# coding: utf-8
import gc

import pandas as pd
import plotly.express as px
import yaml
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from mongodb_lib import *

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()

df = read_object(fs, "product_textual_lang_summarized_subcategories")
df = pd.DataFrame(df)
df = df[["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED", "sub_categories_gpt4o"]]
df = df.explode("sub_categories_gpt4o")

# Ensure the sub_categories_gpt4o column is of type string
df["sub_categories_gpt4o"] = df["sub_categories_gpt4o"].astype(str)

# Get unique subcategories
unique_categories = df["sub_categories_gpt4o"].unique()

# Create dropdown options
dropdown_options = [{"label": cat, "value": cat} for cat in unique_categories]

# Debug output to ensure options are formatted correctly
print("Dropdown options:", dropdown_options)

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div(
    [
        html.H1("Sub Categories Distribution and Descriptions"),
        html.Div(
            [
                dcc.Dropdown(
                    id="category-filter",
                    options=dropdown_options,  # Use the validated dropdown options
                    placeholder="Select a Sub Category",
                ),
                html.Div(id="description-examples"),
            ]
        ),
        dcc.Graph(id="category-distribution"),
    ]
)

# Callback to update the category distribution graph
@app.callback(
    Output("category-distribution", "figure"), Input("category-filter", "value")
)
def update_graph(selected_category):
    category_counts = df["sub_categories_gpt4o"].value_counts().reset_index()
    category_counts.columns = ["Sub Category", "Count"]
    category_counts = category_counts[category_counts["Count"]>50]
    category_counts = category_counts[category_counts["Sub Category"]!="nan"]
    fig = px.bar(
        category_counts,
        x="Sub Category",  # Ensure this is set to your categorical variable
        y="Count",         # Ensure this is set to the count of occurrences
        title="Distribution of Sub Categories",
        orientation='v'    # Explicitly set the orientation to 'v' for vertical
    )
    return fig

# Callback to update the description examples based on selected category
@app.callback(
    Output("description-examples", "children"), Input("category-filter", "value")
)
def update_descriptions(selected_category):
    if selected_category is None:
        return html.Div()

    filtered_df = df[df["sub_categories_gpt4o"] == selected_category]
    examples = filtered_df["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"].tolist()

    return html.Ul([html.Li(example) for example in examples])

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8065)
