# SPIRITS DATA CLEANING


import pandas as pd
import numpy as np
import json
import dateparser
import import_transformer # custom function
import export_transformer # custom function
from import_transformer import import_transformer
from export_transformer import export_transformer
import glob
import time
from datetime import datetime as dt
import re

def convert_to_kilograms(row):
    unit = row["unit"]
    value = row["quantity"]
    if unit == "Tons":
        return [value * 1000, "Kilograms"]
    
    elif unit == "Liters" or unit == "Litres" or unit == "Mixed":
        unit = "Kilograms"
        return [value, "Kilograms"]
    elif unit == "Barrels":
        return [value * 102, "Kilograms"]
    else: 
        return [value, "Kilograms"] 

def import_transformer(df):
    """
    data transformer function for imports
    take any dataframe and do the following transformation:
    - take the indication of units (Tons, Kilograms, Barrels, etc) from the column headers (examle of header : 2023-M07-Exported quantity, Kilograms)
    - create a new column based on the indication of unit and time period (example of output : 2023-M07-Exported quantity, 2023-M07-Unit)
    - drop unnecessary strings from headers
    - convert from wide to long format
    - correct some countries names (e.g Bolivia, Republic of => Bolivia)

    """
    cols = df.columns
    str = "-Imported quantity, "
    for col in cols:
        if str in col:
            year_month = col.split(str)[0] # will give "YYYY-M-Exported quantity, " with a comma after "quantity"
            unit = col.split(str)[1]
            year_month_ex_q = col.split(", ")[0] # will give "YYYY-M-Exported quantity" without the comma
            df = df.rename(columns={col: year_month_ex_q, year_month + "-Unit": unit})
            df[year_month + "-Unit"] = unit
    unit_df = df.melt(id_vars = ["Exporters", "hs_code"], 
                                var_name="m-y-units", 
                                value_name = "unit", 
                                value_vars= [col for col in df.columns if "-Unit" in col])
    
    # create unit_df that contains country, unit
    unit_df["m-y-units"] = unit_df["m-y-units"].str.replace(r"-Unit", "", regex = True)
    unit_df= unit_df.rename(columns = {"m-y-units": "time_period"})
    unit_df["time_period"] = [dateparser.parse(time) for time in unit_df["time_period"]]

    # transform from wide to long format
    value_df = df.melt(id_vars = ["Exporters", "hs_code", "reporting_country"], 
                       var_name="m-y-units",
                       value_name = "quantity",
                       value_vars= [col for col in df.columns if "quantity" in col])
    value_df["m-y-units"] = value_df["m-y-units"].str.replace(r"-Imported quantity", "", regex = True)
    value_df = value_df.rename(columns = {"m-y-units": "time_period"})
    value_df["time_period"] = [dateparser.parse(time) for time in value_df["time_period"]]

    merge_df = pd.merge(value_df, unit_df)
    
    # treating non-numeric values in the merge_df "quantity" column
    merge_df["quantity"] = pd.to_numeric(merge_df["quantity"], errors='coerce') # this will turn any values that are non-numeric into NaNs

    # create column "year" and "month" based on the "time_period" column
    merge_df["month"] = merge_df["time_period"].dt.month
    merge_df["year"] = merge_df["time_period"].dt.year
    merge_df = merge_df.drop("time_period", axis=1) # afterwards, drop the time_period column (axis=1)

    # replace country names with complicated spellings by clean country names
    # this should be in a json file
    merge_df = merge_df.replace({"No Quantity": 0, 
                    "Bolivia, Plurinational State of":"Bolivia",
                    "Congo, Democratic Republic of the" :"Congo", 
                    "Côte d'Ivoire": "Ivory Coast",
                    "Curaçao": "Curacao",
                    "Venezuela, Bolivarian Republic of":"Venezuela",
                    "Viet Nam": "Vietnam",
                    "Macedonia, North": "North Macedonia",
                    "Taipei, Chinese":"Taiwan",
                    "Tanzania, United Republic of": "Tanzania",
                    "Türkiye":"Turkey",
                    "Russian Federation": "Russia",
                    "Hong Kong, China": "Hong Kong",
                    "Korea, Republic of": "South Korea",
                    "Moldova, Republic of":"Moldova",
                    "Iran, Islamic Republic of": "Iran"
                    })

    # add a column to denote reporting country before "importers" column
    # merge_df.insert(0, "reporting_country", country)
    merge_df = merge_df.rename(columns={"Exporters": "partner"})

    # reorder the columns
    merge_df = merge_df[["reporting_country","partner",  "hs_code", "year", "month", "unit","quantity"]]

    return merge_df


spirits_hs_df = pd.read_excel("./input/hs_coding_coverage_2023.xlsx", sheet_name="MASTERLIST_SPIRITS_HS_CODES", converters={"hs_code": str})
spirits_hs_df = spirits_hs_df.drop("Column1", axis=1)
   
# drop rows where HS code is NaN or full product description is Trade of heading 2208, not elsewhere specified
idx_nan_1 = spirits_hs_df[(spirits_hs_df["full_product_description"] == "Trade of heading 2208, not elsewhere specified")].index
idx_nan_2 = spirits_hs_df[(spirits_hs_df["full_product_description"] =="Commodities not elsewhere specified")].index
spirits_hs_df = spirits_hs_df.drop(idx_nan_1)
spirits_hs_df = spirits_hs_df.drop(idx_nan_2)


SPIRITS_PATH = "./downloads/SPIRITS/"
files = []
for csv in glob.glob(SPIRITS_PATH+ "*.txt"):
    files.append(csv)


# do the first downloaded 300 files
# list of untransformed dataframes
print("The number of files to clean is", len(files))
raw_data = [pd.read_csv(textfile, sep = "\t", header=0).iloc[:,:-1] for textfile in files]
len(raw_data)
# find and remove empty dataframes in the raw_data list
def find_empty_idx(list):
    empty_df_idx = [i for i, df in enumerate(list) if df.empty]
    empty_df_idx_sorted = sorted(empty_df_idx, reverse=True)
    return empty_df_idx_sorted

empty_idx = find_empty_idx(raw_data)
print("The number of empty dataframes are", len(empty_idx))

hs_codes_lst = list(spirits_hs_df["hs_code"][:300])
countries_lst = list(spirits_hs_df["reporting_country"][:300])

for idx in empty_idx:
    if idx < len(raw_data):
        raw_data.pop(idx)
        hs_codes_lst.pop(idx)
        countries_lst.pop(idx)

for i, e in enumerate(hs_codes_lst):
    # print(i, e)
    raw_data[i]["hs_code"] = e

for i,e in enumerate(countries_lst):
    raw_data[i]["reporting_country"] = e

start = time.time()

imports_transformed_dfs = []

for df in raw_data:
    transformed_df = import_transformer(df)
    print(transformed_df.head(3))
    imports_transformed_dfs.append(transformed_df)

end = time.time()
print("Time to finish: ", end - start, "seconds", "or ", (end-start)/60, "minutes")

import_df = pd.concat(imports_transformed_dfs, ignore_index=True, axis=0)

import_df.to_csv("./output/SPIRITS_CLEAN_DATA_09-12-2024.csv")