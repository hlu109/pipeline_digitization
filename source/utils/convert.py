# write a quick script to convert a folder of csv's into xlsx

import pandas as pd
import os

from pandas.io.formats import excel


def csv_to_xlsx(input_folder):
    # Loop through all CSV files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            basename = os.path.splitext(filename)[0]
            in_path = os.path.join(input_folder, filename)
            # Read the CSV file into a DataFrame
            # read everything in as text, including numbers, and don't drop NAs, they should be text as well
            df = pd.read_csv(in_path, dtype=str, keep_default_na=False)

            # add a new column called "Notes" and have all rows be empty
            df["Notes"] = ""

            # rearrange all the columns to be in this order:
            # Data Year, State Heading/Project Number, Pipeline Company, Construction Complete, New Construction, Total Pipeline Length, Pipeline Length by Diameter, Pipeline Diameter, Fuel Type Raw, Fuel Type Inferred, Origin City, Origin County, Origin State, Other Origin Description, Terminus City, Terminus County, Terminus State, Other Terminus Description, Interstate or Intrastate, FPC, Parallel or Loop, Function, Connection, Page Number, model_id, absolute_page_n, Notes
            cols = df.columns.tolist()
            new_order = (
                ["Data Year"]
                + (["Month"] if "Month" in cols else [])
                + (["Construction Status Heading"] if "Construction Status Heading" in cols else [])
                + (["Fuel Type Heading"] if "Fuel Type Heading" in cols else [])
                + (["State Heading"] if "State Heading" in cols else [])
                + (["Project Number"] if "Project Number" in cols else [])
                + [
                    "Pipeline Company",
                    "Construction Complete",
                    "New Construction",
                    "Total Pipeline Length",
                    "Pipeline Length by Diameter",
                    "Pipeline Diameter",
                    "Fuel Type Raw",
                    "Fuel Type Inferred",
                    "Origin City",
                    "Origin County",
                    "Origin State",
                    "Other Origin Description",
                    "Terminus City",
                    "Terminus County",
                    "Terminus State",
                    "Other Terminus Description",
                    "Interstate or Intrastate",
                    "FPC",
                    "Parallel or Loop",
                    "Function",
                    "Connection",
                    "Page Number",
                    "model_id",
                    "absolute_page_n",
                    "Notes",
                ]
            )
            df = df.reindex(columns=new_order)

            # export as xlsx
            out_path = os.path.join(input_folder, basename + ".xlsx")

            # disable the default header style for Excel exports
            excel.ExcelFormatter.header_style = None

            df.to_excel(out_path, index=False)
            print(f"Converted {filename} to {basename + '.xlsx'}")


