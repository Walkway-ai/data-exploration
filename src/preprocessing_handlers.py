
#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np

def detect_and_treat_outliers(df, column, method='zscore', threshold=3, replace_with='nan'):
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

    if method == 'zscore':
        z_scores = np.abs((values - values.mean()) / values.std())
        outliers_mask = z_scores > threshold
    elif method == 'iqr':
        Q1 = values.quantile(0.05)
        Q3 = values.quantile(0.95)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers_mask = (values < lower_bound) | (values > upper_bound)
    else:
        raise ValueError("Invalid method. Choose 'zscore' or 'iqr'.")

    print(f"outliers for {column}:")
    print(list(df[column][outliers_mask]))

    if replace_with == 'nan':
        df.loc[outliers_mask, column] = np.nan
    elif replace_with == 'mean':
        df.loc[outliers_mask, column] = values.mean()
    elif replace_with == 'median':
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

    print(column_name, num_bins)
    
    # Create intervals using pd.qcut
    df[column_name] = pd.qcut(df[column_name], q=num_bins, duplicates='drop')
    
    return df