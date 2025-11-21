import pandas as pd
from pydantic import BaseModel, Field, StringConstraints
from typing import List, Dict, Optional, Union, Literal, Any, Annotated


class Entry(BaseModel):
    pass


class CoreEntry(Entry):
    company: str = Field(description="Pipeline Company")
    fuel_original: Literal["NATURAL GAS", "GAS", "GASOLINE", "CRUDE",
                           "PETROLEUM", "OIL",
                           "PRODUCT", "OTHER", "UNK", "NA"] = Field(description="Fuel Type Raw")
    fuel_corrected: Literal["NATURAL GAS", "GASOLINE", "CRUDE", "PETROLEUM",
                            "OIL", "PRODUCT", "GAS (AMBIGUOUS)", "PETROLEUM (AMBIGUOUS)," "OTHER", "UNK", "NA"
                            ] = Field(description="Fuel Type Inferred")
    new_construction: Literal["TRUE", "FALSE", "UNK",
                              "NA"] = Field(description="New Construction")
    construction_complete: Literal["TRUE", "FALSE", "UNK", "NA"] = Field(
        description="Construction Complete")
    length_total: float = Field(description="Total Pipeline Length")
    origin_state: str = Field(description="Origin State")
    terminus_state: str = Field(description="Terminus State")
    inter_or_intra: Literal["INTERSTATE", "INTRASTATE", "UNK", "NA"] = Field(
        description="Interstate or Intrastate")
    fpc: bool = Field(description="FPC")


class ExtendedEntry(CoreEntry):
    diameter: str = Field(description="Pipeline Diameter")
    length_by_diameter: str = Field(description="Pipeline Length by Diameter")
    origin_city: str = Field(description="Origin City")
    terminus_city: str = Field(description="Terminus City")
    origin_county: str = Field(description="Origin County")
    terminus_county: str = Field(description="Terminus County")
    other_origin_description: str = Field(
        description="Other Origin Description")
    other_terminus_description: str = Field(
        description="Other Terminus Description")
    parallel_or_loop: Literal["TRUE", "FALSE", "UNK",
                              "NA"] = Field(description="Parallel or Loop")
    function: Literal["TRANSMISSION", "DISTRIBUTION", "GATHERING",
                      "FIELDING", "LATERAL", "OTHER", "UNK", "NA"] = Field(
                          description="Function")
    connection: Literal["TRUE", "FALSE", "UNK",
                        "NA"] = Field(description="Connection")


class CoreEntryPrivate(CoreEntry):
    state_heading: str = Field(description="State Heading")


class CoreEntryGov(CoreEntry):
    project_num: int = Field(description="Project Number")


class ExtendedEntryPrivate(ExtendedEntry):
    state_heading: str = Field(description="State Heading")


class ExtendedEntryGov(ExtendedEntry):
    project_num: int = Field(description="Project Number")


class Page(BaseModel):
    pgnum: int = Field(description="Page Number")
    yr: int = Field(description="Data Year")


class PagePrivateCore(Page):
    entries: list[CoreEntryPrivate] = Field(
        description="The list of entries on the page")


class PagePrivateExtended(Page):
    entries: list[ExtendedEntryPrivate] = Field(
        description="The list of entries on the page")


class PageGovCore(Page):
    entries: list[CoreEntryGov] = Field(
        description="The list of entries on the page")


class PageGovExtended(Page):
    entries: list[ExtendedEntryGov] = Field(
        description="The list of entries on the page")


# Function to convert Directory to a DataFrame
def page_to_dataframe(page: Page):
    if isinstance(page, PageGovCore):
        return page_to_df_gov_core(page)
    elif isinstance(page, PagePrivateCore):
        return page_to_df_private_core(page)
    elif isinstance(page, PageGovExtended):
        return page_to_df_gov_extended(page)
    elif isinstance(page, PagePrivateExtended):
        return page_to_df_private_extended(page)
    else:
        raise ValueError("Unsupported page model type")


def page_to_df_gov_core(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "Project Number": entry.project_num,
            "Pipeline Company": entry.company,
            "Fuel Type Raw": entry.fuel_original,
            "Fuel Type Inferred": entry.fuel_corrected,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Total Pipeline Length": entry.length_total,
            "Origin State": entry.origin_state,
            "Terminus State": entry.terminus_state,
            "Interstate or Intrastate": entry.inter_or_intra,
        })

    df = pd.DataFrame(data)
    return df


def page_to_df_private_core(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "State Heading": entry.state_heading,
            "Pipeline Company": entry.company,
            "Fuel Type Raw": entry.fuel_original,
            "Fuel Type Inferred": entry.fuel_corrected,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Total Pipeline Length": entry.length_total,
            "Origin State": entry.origin_state,
            "Terminus State": entry.terminus_state,
            "Interstate or Intrastate": entry.inter_or_intra,
        })

    df = pd.DataFrame(data)
    return df


def page_to_df_gov_extended(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "Project Number": entry.project_num,
            "Pipeline Company": entry.company,
            "Fuel Type Raw": entry.fuel_original,
            "Fuel Type Inferred": entry.fuel_corrected,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Total Pipeline Length": entry.length_total,
            "Pipeline Length by Diameter": entry.length_by_diameter,
            "Pipeline Diameter": entry.diameter,
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
            "FPC": entry.fpc,
        })

    df = pd.DataFrame(data)
    return df


def page_to_df_private_extended(page: Page):
    data = []

    for entry in page.entries:
        # TODO: retrieve the column name from the entry field description
        # col_names = [Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
        data.append({
            "Data Year": page.yr,
            "Page Number": page.pgnum,
            "State Heading": entry.state_heading,
            "Pipeline Company": entry.company,
            "Fuel Type Raw": entry.fuel_original,
            "Fuel Type Inferred": entry.fuel_corrected,
            "New Construction": entry.new_construction,
            "Construction Complete": entry.construction_complete,
            "Total Pipeline Length": entry.length_total,
            "Pipeline Length by Diameter": entry.length_by_diameter,
            "Pipeline Diameter": entry.diameter,
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
            "FPC": entry.fpc,
        })

    df = pd.DataFrame(data)
    return df
