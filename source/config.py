from pathlib import Path
from datetime import datetime
from PagesLib.Page import PagePrivateCore, PageGovCore, PagePrivateExtended, PageGovExtended, PagePrivate1951_mid1952

REPO_ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# SET PARAMETERS ---------------------------------------------------------------
# ------------------------------------------------------------------------------

# Optional note to log purpose of the run (default set to None)
NOTE = None

gov = False  # True for government pipelines, False for private pipelines
# True to use all variables, False to use only core variables
extended_variables = True

# Set API Parameters -------------------------------------------
# GEMINI_MODEL_ID = "gemini-2.0-flash"
# GEMINI_MODEL_ID = "gemini-2.5-flash"
# GEMINI_MODEL_ID = "gemini-2.5-pro"
# GEMINI_MODEL_ID = "gemini-3-flash-preview"
GEMINI_MODEL_ID = "gemini-3-pro-preview"

# Set File Paths -------------------------------------------
# Define which pdf input to use
private_file_path = REPO_ROOT / "inputs" / "pipeline_scans" / "private_1943_1951.pdf"
private_51_52_file_path = REPO_ROOT / "inputs" / "pipeline_scans" / "private_1951_mid1952.pdf"
government_file_path = REPO_ROOT / "inputs" / "pipeline_scans" / "gov_1943_1945.pdf"
# INPUT_FILE_PATH = government_file_path if gov else private_file_path
INPUT_FILE_PATH = private_51_52_file_path

# SET GEMINI PROMPT ------------------------------------------------------------
# Indicate the file name for the prompt to use
# prompt_text_name = f"pipeline_{'extended' if extended_variables else 'core'}_prompt_{"gov" if gov else "priv"}.txt"
prompt_text_name = "pipeline_extended_1951_mid1952_prompt.txt"

# Set Page Schema -----------------------------------
# if extended_variables:
#     page_schema = PageGovExtended if gov else PagePrivateExtended
# else:
#     page_schema = PageGovCore if gov else PagePrivateCore
page_schema = PagePrivate1951_mid1952

# Page Parameters -------------------------------------------
# Indicate whether the pages should be uploaded as .png instead of .pdf
png = False

# SET FILE IDENTIFIERS ---------------------------------------------------------
RUN_PREFIX = INPUT_FILE_PATH.stem + ("_extended_vars"
                                     if extended_variables else "_core_vars")

# SET RESUME PARAMETERS --------------------------------------------------------
REUSE_OLD_RESULTS = False
RESUME_RUN_IDENTIFIER = None

# ------------------------------------------------------------------------------
# END OF SET PARAMETERS --------------------------------------------------------
# ------------------------------------------------------------------------------

if REUSE_OLD_RESULTS:
    if not RESUME_RUN_IDENTIFIER:
        raise ValueError(
            "REUSE_OLD_RESULTS is True but RESUME_RUN_IDENTIFIER is not set.")
    # reuse the prior run's identifier so intermediate files, the output CSV, and the log file all resolve to the same paths as the run being resumed
    IDENTIFIER = RESUME_RUN_IDENTIFIER
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    IDENTIFIER = f"{RUN_PREFIX}_{timestamp}"

PROMPT_TEXT_PATH = REPO_ROOT / "source" / "prompts" / prompt_text_name
API_KEY_PATH = REPO_ROOT / "secret" / "GEMINI_API_KEY.txt"

OUTPUT_DIR = REPO_ROOT / "outputs"
GEMINI_DIR = OUTPUT_DIR / "gemini_output"
LOG_DIR = OUTPUT_DIR / "logs"

RUN_DIR = GEMINI_DIR / IDENTIFIER
TEMP_DIR = RUN_DIR / "temp"
OUTPUT_PATH = GEMINI_DIR / f"{IDENTIFIER}.csv"
