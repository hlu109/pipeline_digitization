import pandas as pd
from chardet.cli.chardetect import description_of  # not sure if this is used?
from pydantic import BaseModel, Field, StringConstraints
from typing import List, Dict, Optional, Union, Literal, Any, Annotated


class Entry(BaseModel):
    company: str = Field(description="Pipeline Company")
    # gov: Literal["true", "false", "UNK", "NA"] = Field(description="Government Project")
    fuel: Literal["NATURAL GAS", "GAS", "GASOLINE", "CRUDE", "PETROLEUM", "OIL",
                  "PRODUCT", "OTHER", "UNK", "NA"] = Field(description="Fuel Type")
    new_construction: Literal["TRUE", "FALSE", "UNK",
                              "NA"] = Field(description="New Construction")
    construction_complete: Literal["TRUE", "FALSE", "UNK", "NA"] = Field(
        description="Construction Complete")
    # TODO: add handling for "almost complete" (we should check if it appears in the following year's data)
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
    inter_or_intra: Literal["INTERSTATE", "INTRASTATE", "UNK", "NA"] = Field(
        description="Interstate or Intrastate")
    # parallel_or_loop: bool = Field(description="Parallel or Loop")


class EntryPrivate(Entry):
    state_heading: str = Field(description="State Heading")

    # TODO: add handling for 1943 section with random prose about barrels


class EntryGov(Entry):
    project_num: int = Field(description="Project Number")


class EntryCombined(Entry):
    state_heading: str = Field(description="State Heading")
    project_num: int = Field(description="Project Number")


class Page(BaseModel):
    pgnum: int = Field(description="Page Number")
    yr: int = Field(description="Data Year")


class PagePrivate(Page):
    entries: list[EntryPrivate] = Field(
        description="The list of entries on the page")


class PageGov(Page):
    entries: list[EntryGov] = Field(
        description="The list of entries on the page")


class PageCombined(Page):
    entries: list[EntryCombined] = Field(
        description="The list of entries on the page")


# class Directory(BaseModel):
#     p: list[Page] = Field(description="The list of pages in the pdf")


# Function to convert Directory to a DataFrame
def page_to_dataframe(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "State Heading": entry.state_heading,
            # TODO: add handling for gov/private/combined
            "Pipeline Company": entry.company,
            "Fuel Type": entry.fuel,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Pipeline Length": entry.length,
            "Origin State": entry.origin_state,
            "Terminus State": entry.terminus_state,
            "Interstate or Intrastate": entry.inter_or_intra,
        })

    df = pd.DataFrame(data)
    return df
