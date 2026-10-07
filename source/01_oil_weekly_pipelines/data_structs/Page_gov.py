import pandas as pd
from chardet.cli.chardetect import description_of  # not sure if this is used?
from pydantic import BaseModel, Field, StringConstraints
from typing import List, Dict, Optional, Union, Literal, Any, Annotated

# TODO: see if there's a way to constrain year to 4 digits and mileage to int or one decimal


class Entry(BaseModel):
    state_heading: str = Field(description="State Heading")
    company: str = Field(description="Pipeline Company Name")
    # gov: bool = Field(description="Government Project")
    fuel: Literal["natural gas", "gas", "gasoline", "crude", "petroleum", "oil",
                  "product", "other", "UNK", "NA"] = Field(description="Fuel Type")
    construction_complete: bool = Field(description="Construction Complete")
    length: float = Field(description="Pipeline Length")
    origin_state: str = Field(description="Origin State")
    terminus_state: str = Field(description="Terminus State")
    # origin_city: str = Field(description="Origin City")
    # terminus_city: str = Field(description="Terminus City")
    # origin_county: str = Field(description="Origin County")
    # terminus_county: str = Field(description="Terminus County")
    # other_origin_description: str = Field(
    #     description="Other Origin Description")
    # other_terminus_description: str = Field(
    #     description="Other Terminus Description")
    inter_or_intra: Literal["interstate", "intrastate", "UNK", "NA"] = Field(
        description="Interstate or Intrastate")
    # parallel_or_loop: bool = Field(description="Parallel or Loop")

# TODO: add handling for government pipeline section


class Page(BaseModel):
    pgnum: int = Field(description="page number in the pdf")
    entries: list[Entry] = Field(description="The list of entries on the page")
    yr: int = Field(description="year of data source")


class Directory(BaseModel):
    p: list[Page] = Field(description="The list of pages in the pdf")


# Function to convert Directory to a DataFrame
def page_to_dataframe(page: Page):
    data = []

    for entry in page.entries:
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "State Heading": entry.state_heading,
            "Pipeline Company": entry.company,
            "Fuel Type": entry.fuel,
            "Construction Complete": entry.construction_complete,
            "Pipeline Length (miles)": entry.length,
            "Origin State": entry.origin_state,
            "Terminus State": entry.terminus_state,
            "Interstate or Intrastate": entry.inter_or_intra
        })

    df = pd.DataFrame(data)
    return df
