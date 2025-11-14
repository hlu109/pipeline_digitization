import pandas as pd
from pydantic import BaseModel, Field, StringConstraints
from typing import List, Dict, Optional, Union, Literal, Any, Annotated


class Entry(BaseModel):
    company: str = Field(description="Pipeline Company")
    fuel: Literal["NATURAL GAS", "GAS", "GASOLINE", "CRUDE", "PETROLEUM", "OIL",
                  "PRODUCT", "OTHER", "UNK", "NA"] = Field(description="Fuel Type")
    new_construction: Literal["TRUE", "FALSE", "UNK",
                              "NA"] = Field(description="New Construction")
    construction_complete: Literal["TRUE", "FALSE", "UNK", "NA"] = Field(
        description="Construction Complete")
    # TODO: add handling for "almost complete" (we should check if it appears in the following year's data)
    diameter: str = Field(description="Pipeline Diameter")
    length_by_diameter: str = Field(description="Pipeline Length by Diameter")
    length_total: float = Field(description="Total Pipeline Length")
    origin_state: str = Field(description="Origin State")
    terminus_state: str = Field(description="Terminus State")
    origin_city: str = Field(description="Origin City")
    terminus_city: str = Field(description="Terminus City")
    origin_county: str = Field(description="Origin County")
    terminus_county: str = Field(description="Terminus County")
    other_origin_description: str = Field(
        description="Other Origin Description")
    other_terminus_description: str = Field(
        description="Other Terminus Description")
    inter_or_intra: Literal["INTERSTATE", "INTRASTATE", "UNK", "NA"] = Field(
        description="Interstate or Intrastate")
    parallel_or_loop: Literal["TRUE", "FALSE", "UNK",
                              "NA"] = Field(description="Parallel or Loop")
    function: Literal["TRANSMISSION", "DISTRIBUTION", "GATHERING",
                      "FIELDING", "OTHER", "UNK", "NA"] = Field(
                          description="Function")
    connection: Literal["TRUE", "FALSE", "UNK",
                        "NA"] = Field(description="Connection")


class EntryPrivate(Entry):
    state_heading: str = Field(description="State Heading")


class EntryGov(Entry):
    # TODO: add handling for 1943 section with random prose about barrels
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


# Function to convert Directory to a DataFrame
def page_to_dataframe(page: Page):
    if isinstance(page, PageGov):
        return page_to_df_gov(page)
    elif isinstance(page, PagePrivate):
        return page_to_df_private(page)
    else:
        raise ValueError("Unsupported page model type")


def page_to_df_gov(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "Project Number": entry.project_num,
            "Pipeline Company": entry.company,
            "Fuel Type": entry.fuel,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Pipeline Length by Diameter": entry.length_by_diameter,
            "Total Pipeline Length": entry.length_total,
            "Origin State": entry.origin_state,
            "Terminus State": entry.terminus_state,
            "Origin City": entry.origin_city,
            "Terminus City": entry.terminus_city,
            "Origin County": entry.origin_county,
            "Terminus County": entry.terminus_county,
            "Other Origin Description": entry.other_origin_description,
            "Other Terminus Description": entry.other_terminus_description,
            "Interstate or Intrastate": entry.inter_or_intra,
            "Parallel or Loop": entry.parallel_or_loop,
            "Function": entry.function,
            "Connection": entry.connection,
        })

    df = pd.DataFrame(data)
    return df


def page_to_df_private(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "State Heading": entry.state_heading,
            "Pipeline Company": entry.company,
            "Fuel Type": entry.fuel,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Pipeline Length by Diameter": entry.length_by_diameter,
            "Total Pipeline Length": entry.length_total,
            "Origin State": entry.origin_state,
            "Terminus State": entry.terminus_state,
            "Origin City": entry.origin_city,
            "Terminus City": entry.terminus_city,
            "Origin County": entry.origin_county,
            "Terminus County": entry.terminus_county,
            "Other Origin Description": entry.other_origin_description,
            "Other Terminus Description": entry.other_terminus_description,
            "Interstate or Intrastate": entry.inter_or_intra,
            "Parallel or Loop": entry.parallel_or_loop,
            "Function": entry.function,
            "Connection": entry.connection,
        })

    df = pd.DataFrame(data)
    return df
