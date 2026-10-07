import math
import re
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal, Optional


class Cell(BaseModel):
    line_no: Optional[int] = Field(
        description="Printed line number of the row")
    value_as_printed: Optional[str] = Field(
        description=
        "Number exactly as printed in the cell (keep commas and decimals); null if the cell has no number"
    )
    cell_status: Literal["VALUE", "BLANK", "NOT_REPORTED", "FLAG_ONLY",
                         "ILLEGIBLE"] = Field(
                             description="What the cell contains")
    footnote_flags: list[str] = Field(
        description="Footnote flags printed in or next to the cell.")


class TransmissionBin(Cell):
    diam_bin_label: str = Field(
        description="Inside diameter label exactly as printed.")


class Company(BaseModel):
    col_index: int = Field(
        description="Position of the company column on the page.")
    company_name_raw: str = Field(
        description="Company name exactly as printed in the column header")
    company_footnote_flags: list[str] = Field(
        description="Footnote flags printed next to the company name")
    field: Cell = Field(description="Field pipelines entry")
    transmission_bins: list[TransmissionBin] = Field(
        description="Transmission pipelines entries by diameter, top to bottom"
    )
    total_transmission: Cell = Field(
        description="Total Transmission pipelines entry")


class Footnote(BaseModel):
    flag: str = Field(description="Footnote flag as printed")
    text: str = Field(description="Footnote text")


class FPCPage(BaseModel):
    printed_page_number: Optional[str] = Field(
        description="Printed page number.")
    report_year: Optional[int] = Field(description="Year in the page header.")
    companies: list[Company] = Field(
        description="Every company column on the page, left to right")
    footnotes: list[Footnote] = Field(
        description="Every footnote printed at the bottom of the page")


def _parse_miles(value_as_printed):
    """Returns the printed value as a float, or None if it is missing or not a plain number."""
    if value_as_printed is None:
        return None
    try:
        return float(value_as_printed.replace(",", "").strip())
    except ValueError:
        return None


def _parse_diam_bin(diam_bin_label):
    """
    Splits a transmission diameter label into lower and upper bounds in inches.

    Args:
        * diam_bin_label (str): diameter label as printed.

    Returns:
        * tuple: (lower, upper) as floats, math.inf for open upper bounds, or None if the label cannot be parsed.
    """
    if diam_bin_label is None:
        return None, None
    label = diam_bin_label.lower()
    bounds = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", label)]
    is_open_top = re.search(r"over|above|more than|\+", label) is not None
    is_open_bottom = re.search(r"under|up to|less than", label) is not None

    if len(bounds) == 2 and not (is_open_top or is_open_bottom):
        return bounds[0], bounds[1]
    if len(bounds) == 1 and is_open_top:
        return bounds[0], math.inf
    if len(bounds) == 1 and is_open_bottom:
        return 0.0, bounds[0]
    return None, None


def page_to_dataframe(page: FPCPage, data_year=None, source_file=None):
    """
    Converts an FPCPage into a long dataframe with one row per company per mileage row.

    Args:
        * page (FPCPage): parsed page.
        * data_year (int): data year of the input file.
        * source_file (str): name of the input PDF.
    """
    data = []
    for company in page.companies:
        # format: segment_type, diam_bin_label, cell
        rows = [("FIELD", None, company.field)]
        rows += [("TRANSMISSION", b.diam_bin_label, b)
                 for b in company.transmission_bins]
        rows += [("TOTAL_TRANSMISSION", None, company.total_transmission)]
        for segment_type, diam_bin_label, cell in rows:
            diam_min, diam_max = _parse_diam_bin(diam_bin_label)
            data.append({
                "Data.Year": data_year,
                "Report.Year": page.report_year,
                "Source.File": source_file,
                "Printed.Page": page.printed_page_number,
                "Col.Index": company.col_index,
                "Company.Name.Raw": company.company_name_raw,
                "Company.Flags": ";".join(company.company_footnote_flags),
                "Line.No": cell.line_no,
                "Segment.Type": segment_type,
                "Diam.Bin.Label": diam_bin_label,
                "Diam.Min.In": diam_min,
                "Diam.Max.In": diam_max,
                "Miles.As.Printed": cell.value_as_printed,
                "Miles": _parse_miles(cell.value_as_printed),
                "Cell.Status": cell.cell_status,
                "Footnote.Flags": ";".join(cell.footnote_flags),
            })

    return pd.DataFrame(data)


def page_to_footnotes_dataframe(page: FPCPage,
                                data_year=None,
                                source_file=None):
    """Returns the page's footnotes as a dataframe with one row per footnote."""
    data = [{
        "Data.Year": data_year,
        "Source.File": source_file,
        "Printed.Page": page.printed_page_number,
        "Flag": fn.flag,
        "Footnote.Text": fn.text,
    } for fn in page.footnotes]

    return pd.DataFrame(data)
