"""
Safe operations module to prevent type comparison errors
"""

import pandas as pd
import numpy as np

def safe_sort(values):
    """Safely sort values by converting all to strings first"""
    try:
        # Convert all values to strings, handle NaN
        str_values = []
        for val in values:
            if pd.isna(val):
                str_values.append('zzz_nan')  # Sort NaN to end
            else:
                str_values.append(str(val))
        return sorted(str_values)
    except:
        # If still fails, return as-is
        return list(values)

def safe_groupby(df, column):
    """Safely group by a column by ensuring all values are strings"""
    try:
        df_copy = df.copy()
        df_copy[column] = df_copy[column].fillna('missing').astype(str)
        return df_copy.groupby(column)
    except:
        # Fallback: return empty groupby
        return df.iloc[0:0].groupby(df.columns[0])

def safe_unique(series):
    """Safely get unique values as strings"""
    try:
        return series.fillna('missing').astype(str).unique()
    except:
        return np.array(['unknown'])

def safe_pivot(df, index, columns, values):
    """Safely pivot data"""
    try:
        df_copy = df.copy()
        df_copy[index] = df_copy[index].fillna('missing').astype(str)
        df_copy[columns] = df_copy[columns].fillna('missing').astype(str)
        return df_copy.pivot(index=index, columns=columns, values=values)
    except:
        # Return empty dataframe with expected structure
        return pd.DataFrame()
