#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
from tqdm import tqdm


def detect_and_treat_outliers(
    df, column, method="zscore", threshold=3, replace_with="mean"
):
    """
    Detects and treats outliers in a DataFrame column.

    Parameters:
    - df: DataFrame containing the data
    - column: Name of the column containing the values
    - method: Method for outlier detection ('zscore' or 'iqr')
    - threshold: Threshold value for outlier detection
    - replace_with: Value to replace outliers with ('nan', 'mean', 'median', or a specific value)

    Returns:
    - DataFrame with outliers treated according to the specified method
    """
    values = df[column]

    if method == "zscore":
        z_scores = np.abs((values - values.mean()) / values.std())
        outliers_mask = z_scores > threshold
    elif method == "iqr":
        Q1 = values.quantile(0.05)
        Q3 = values.quantile(0.95)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers_mask = (values < lower_bound) | (values > upper_bound)
    else:
        raise ValueError("Invalid method. Choose 'zscore' or 'iqr'.")

    # print(f"outliers for {column}:")
    # print(list(df[column][outliers_mask]))

    if replace_with == "nan":
        df.loc[outliers_mask, column] = np.nan
    elif replace_with == "mean":
        df.loc[outliers_mask, column] = values.mean()
    elif replace_with == "median":
        df.loc[outliers_mask, column] = values.median()
    else:
        df.loc[outliers_mask, column] = replace_with

    return df


def auto_bin_intervals(df, column_name):
    """
    Automatically creates intervals for a numerical column in a DataFrame based on Sturges' Rule.

    Parameters:
    df (pd.DataFrame): The input DataFrame.
    column_name (str): The name of the column to convert.

    Returns:
    pd.DataFrame: The DataFrame with the new interval column.
    """
    # Calculate the number of bins using Sturges' Rule
    num_bins = int(np.ceil(np.log2(len(df[column_name])) + 1))

    # Create intervals using pd.qcut
    df[column_name] = pd.qcut(df[column_name], q=num_bins, duplicates="drop")

    return df


class DataFrameProcessor:
    def __init__(self, data_path, key_field, location_field):
        """
        Initialize the DataFrameProcessor with a path to the pickle file.

        Parameters:
        data_path (str): The path to the pickle file containing the DataFrame.
        key_field (str): The column name to group by.
        location_field (str): The column name that contains the location.
        """

        self.data_path = data_path
        self.key_field = key_field
        self.location_field = location_field

    def preprocess(self):
        self.read_data()
        self.explode_dataframe()
        self.fill_missing_values()
        self.merge_and_remove_empty_cities()
        self.fill_fixed_duration()
        self.remove_outliers()
        self.create_intervals()
        self.aggregate_tabular_fields()
        self.create_text_dataframe()
        self.preprocess_tabular_fields()
        self.preprocess_text_fields()
        self.astypestr()
        self.normalize_product_type()

    def read_data(self):
        self.df = pd.read_pickle(self.data_path)
        self.df = self.df[:-1]
        self.df_text = None

    def explode_dataframe(self):
        """Explode all columns of the DataFrame."""

        for col in tqdm(self.df.columns):

            if col != self.key_field:

                self.df = self.df.explode(col)

    def fill_missing_values(self):
        """Fill missing values in the DataFrame."""

        self.df.fillna(np.nan, inplace=True)

    def merge_and_remove_empty_cities(self):
        """Merge city values and drop rows where 'self.location_field' is NaN."""

        def fill_city(row):
            if pd.isna(row[self.location_field]):
                if not pd.isna(row["pdt_product_level_VIDESTINATIONCITY"]):
                    return row["pdt_product_level_VIDESTINATIONCITY"]
                elif not pd.isna(row["pdt_inclexcl_ENG_VIDESTINATIONCITY"]):
                    return row["pdt_inclexcl_ENG_VIDESTINATIONCITY"]
                else:
                    return np.nan
            else:
                return row[self.location_field]

        self.df[self.location_field] = self.df.apply(fill_city, axis=1)

        del self.df["pdt_product_level_VIDESTINATIONCITY"]
        del self.df["pdt_inclexcl_ENG_VIDESTINATIONCITY"]

        self.df = self.df.dropna(subset=[self.location_field])

    def fill_fixed_duration(self):
        """Compute mean of 'pdt_product_level_MINFLEXIBLEDURATION' and 'pdt_product_level_MAXFLEXIBLEDURATION' and fill 'pdt_product_level_FIXEDDURATION'."""

        def fill_duration(row):
            if np.isnan(row["pdt_product_level_FIXEDDURATION"]):
                return (
                    row["pdt_product_level_MINFLEXIBLEDURATION"]
                    + row["pdt_product_level_MAXFLEXIBLEDURATION"]
                ) / 2
            else:
                return row["pdt_product_level_FIXEDDURATION"]

        self.df["pdt_product_level_FIXEDDURATION"] = self.df.apply(
            fill_duration, axis=1
        )

        del self.df["pdt_product_level_MINFLEXIBLEDURATION"]
        del self.df["pdt_product_level_MAXFLEXIBLEDURATION"]


    def remove_outliers(self):
        """Remove outliers from the DataFrame."""

        self.df = detect_and_treat_outliers(
            self.df,
            "pdt_product_level_RETAILPRICEFROMUSD",
            method="zscore",
            threshold=3,
            replace_with="mean",
        )

    def create_intervals(self):
        """Create intervals of bins for float and int columns."""

        numerical_cols = [
            "pdt_product_level_RETAILPRICEFROMUSD",
            "pdt_product_level_FIXEDDURATION",
            "pdt_product_level_STOPSCOUNT",
            "pdt_product_level_STOPSTOTALDURATION",
            "pdt_product_level_TOTALREVIEWCOUNT",
            "pdt_product_level_TOTALAVGRATING",
        ]
        for numerical_col in tqdm(numerical_cols):
            self.df = auto_bin_intervals(self.df, numerical_col)

    def aggregate_tabular_fields(self):
        """Aggregate tabular fields in the tabular DataFrame."""

        columns_to_aggregate = [
            col for col in self.df.columns if col != self.key_field
        ]
        agg_dict = {col: list for col in columns_to_aggregate}
        self.df = self.df.groupby(self.key_field).agg(agg_dict).reset_index()

    def create_text_dataframe(self):
        """Create a separate DataFrame with descriptive content."""

        self.df_text = self.df.copy()
        descriptive_fields = [
            "pdt_inclexcl_ENG_CONTENT",
            "pdt_product_detail_PRODUCTDESCRIPTION",
        ]
        self.df_text = self.df_text[[self.key_field] + descriptive_fields]

        for del_col in descriptive_fields:
            del self.df[del_col]

    def preprocess_tabular_fields(self):
        """Preprocesses tabular fields in the text DataFrame."""

        columns_to_aggregate = [
            col for col in self.df.columns if col != self.key_field
        ]

        def get_unique_value(lst):
            unique_values = pd.unique(lst)
            unique_values = [x for x in unique_values if pd.notna(x)]
            if len(unique_values) == 1:
                return unique_values[0]
            elif len(unique_values) == 0:
                return np.nan
            else:
                raise ValueError(f"Non-unique values found: {unique_values}")

        for col in tqdm(columns_to_aggregate):

            self.df[col] = self.df[col].apply(lambda x: get_unique_value(x))

    def preprocess_text_fields(self):
        """Preprocesses text fields in the text DataFrame."""

        def unique_preserve_order(lst):
            seen = set()
            unique_list = []
            for item in lst:
                if item not in seen:
                    unique_list.append(item)
                    seen.add(item)
            return unique_list

        self.df_text["pdt_inclexcl_ENG_CONTENT"] = [
            "; ".join(unique_preserve_order(el)) if len(unique_preserve_order(el)) > 1 else unique_preserve_order(el)[0]
            for el in self.df_text["pdt_inclexcl_ENG_CONTENT"]
        ]
        self.df_text["pdt_product_detail_PRODUCTDESCRIPTION"] = [
            ". ".join(unique_preserve_order(el)) if len(unique_preserve_order(el)) > 1 else unique_preserve_order(el)[0]
            for el in self.df_text["pdt_product_detail_PRODUCTDESCRIPTION"]
        ]

    def astypestr(self):
        self.df = self.df.astype(str)
        self.df = self.df.replace("nan", "")
        self.df_text = self.df_text.astype(str)
        self.df_text = self.df_text.replace("nan", "")

    def normalize_product_type(self):
        self.df["pdt_product_level_VIPRODUCTTYPE"] = [
            "; ".join(list(sorted(el.split("; "))))
            for el in self.df["pdt_product_level_VIPRODUCTTYPE"]
        ]
