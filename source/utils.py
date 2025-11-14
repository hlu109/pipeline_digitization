import os
from datetime import datetime
import pandas as pd

# ------------------------------------------------------------------------------


def export_clean_handcoded(handcoded_path, output_path):
    """ Wrapper for clean_handcoded to save cleaned data to output_path."""
    df_clean = clean_handcoded(handcoded_path)
    df_clean.to_csv(output_path, index=False)


def clean_handcoded(handcoded_path):
    """ Clean and standardize handcoded data for consistent formatting with LLM 
        outputs.

    Args:
        handcoded_path (str): path to handcoded data file

    Returns: 
        Dataframe containing cleaned handcoded data.
    """
    if handcoded_path.endswith(".csv"):
        df_handcoded = pd.read_csv(handcoded_path)
    elif handcoded_path.endswith((".xls", ".xlsx")):
        df_handcoded = pd.read_excel(handcoded_path)
    else:
        raise ValueError(
            "Unsupported file format. Please use .csv or .xls/.xlsx")

    # Strip all whitespace
    df_handcoded = df_handcoded.map(lambda x: x.strip()
                                    if isinstance(x, str) else x)

    # Remove trailing question marks for all entries that are strings
    df_handcoded = df_handcoded.map(
        lambda x: x.replace("?", "") if isinstance(x, str) else x)

    # Create new cleaned dataframe
    df_clean = pd.DataFrame(columns=["Data Year", "Pipeline Company",
                                     "Fuel Type", "New Construction",
                                     "Construction Complete", "Pipeline Length",
                                     "Origin State", "Terminus State",
                                     "Interstate or Intrastate"])

    df_clean["Data Year"] = df_handcoded["Data year"].copy().astype(int)
    df_clean["Pipeline Company"] = df_handcoded["Company"].copy()
    df_clean["Origin State"] = df_handcoded["Origin State"].copy()
    df_clean["Terminus State"] = df_handcoded["Terminus State"].copy()

    # Standardize fuel types
    df_clean["Fuel Type"] = df_handcoded["Fuel Type"].copy().str.upper()
    df_clean["Fuel Type"] = df_clean["Fuel Type"].str.replace(
        "PRODUCTS", "PRODUCT")

    # Extract bool for complete construction
    new_construction = df_handcoded[
        "Type of Construction Work"].str.lower() == "new"
    extension_construction = df_handcoded[
        "Type of Construction Work"].str.lower() == "extension"
    df_clean["New Construction"] = new_construction | extension_construction
    df_clean["New Construction"] = df_clean["New Construction"].astype(
        str).str.upper()
    # copy over instances where the value is "UNK" or "NA"
    df_clean.loc[
        df_handcoded["Type of Construction Work"] == "UNK", "New Construction"] = "UNK"
    df_clean.loc[
        df_handcoded["Type of Construction Work"] == "NA", "New Construction"] = "NA"

    # Extract bool for new construction (include both new construction and extension)
    df_clean["Construction Complete"] = df_handcoded[
        "Construction Completion Status"].str.lower().str.startswith("complete")
    df_clean["Construction Complete"] = df_clean["Construction Complete"].astype(
        str).str.upper()
    df_clean.loc[
        df_handcoded["Construction Completion Status"] == "UNK", "Construction Complete"] = "UNK"
    df_clean.loc[
        df_handcoded["Construction Completion Status"] == "NA", "Construction Complete"] = "NA"

    # Standardize interstate/intrastate
    df_clean["Interstate or Intrastate"] = df_handcoded["Inter/Intra-State?"].str.upper()
    df_clean["Interstate or Intrastate"] = df_clean["Interstate or Intrastate"].str.replace(
        "INTER", "INTERSTATE")
    df_clean["Interstate or Intrastate"] = df_clean["Interstate or Intrastate"].str.replace(
        "INTRA", "INTRASTATE")

    # Standardize pipeline length
    # TODO: need to handle cases with multiple mileage separated by semicolon
    df_clean["Total Pipeline Length"] = df_handcoded["Length (mi)"].copy()
    df_clean["Total Pipeline Length"] = df_clean["Total Pipeline Length"].replace(
        {"UNK": -1, "NA": -2})
    df_clean["Total Pipeline Length"] = df_clean["Total Pipeline Length"].astype(
        float)

    # Standardize parallel/loop boolean
    df_clean["Parallel or Loop"] = df_handcoded["Parallel/Loop?"].astype(
        str).str.upper()
    # convert yes/no to true/false
    df_clean["Parallel or Loop"] = df_clean["Parallel or Loop"].replace(
        {"YES": "TRUE", "NO": "FALSE"})

    # Standardize connection boolean
    df_clean["Connection"] = df_handcoded["Connection to existing line?"].astype(
        str).str.upper()
    # convert yes/no to true/false
    df_clean["Connection"] = df_clean["Connection"].replace(
        {"YES": "TRUE", "NO": "FALSE", "MAYBE": "UNK"})

    # Standardize function of pipeline
    df_clean["Function"] = df_handcoded["Pipeline Function"].astype(
        str).str.upper()
    # if it starts with the key word, convert to standard term (to eliminate other descriptors added by coder)
    df_clean["Function"] = df_clean["Function"].replace({
        r"^TRANSMISSION.*": "TRANSMISSION",
        r"^DISTRIBUTION.*": "DISTRIBUTION",
        r"^GATHERING.*": "GATHERING",
        r"^FIELDING.*": "FIELDING",
    }, regex=True)

    return df_clean


def write_log(message, log_dir, config):
    # TODO: remove config and replace with file_path arg
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_path = os.path.join(log_dir, f"log_{config.identifier}.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%H%M:%S")
        file.write(f"[{timestamp}] {message}\n\n")


def log_config(log_dir, config):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save text of gemini prompt--------
    with open(config.prompt_text_path, "r") as file:
        prompt_text = file.read()
    with open(os.path.join(log_dir, "prompt_text.txt"), "a",
              encoding="utf-8") as file:
        file.write(prompt_text)

    # Save parameter values ----------
    file_path = os.path.join(log_dir, f"log_{config.identifier}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] \n\n")
        file.write(f"CONFIG PARAMETERS\n\n")
        # file.write(f"Directory file year: {input_file_year}\n")
        file.write(f"Start page: {config.start_page}\n")
        file.write(f"End page: {config.start_page + config.n_pages - 1}\n")
        file.write(f"Page window: {config.page_window}\n")
        file.write(f"Prompt text file: {config.prompt_text_name}\n")
        file.write(f"Gemini model: {config.gemini_model_id}\n\n")
