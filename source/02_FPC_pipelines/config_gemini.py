from datetime import datetime
from data_structs.FPCPage import FPCPage
from utils.config import CODE_DIR, DATA_ROOT_DIR, API_KEY_PATH

# ------------------------------------------------------------------------------
# SET PARAMETERS ---------------------------------------------------------------
# ------------------------------------------------------------------------------

# Optional note to log purpose of the run (default set to None)
NOTE = None

# Set API Parameters -------------------------------------------
# GEMINI_MODEL_ID = "gemini-2.0-flash"
# GEMINI_MODEL_ID = "gemini-2.5-flash"
# GEMINI_MODEL_ID = "gemini-2.5-pro"
GEMINI_MODEL_ID = "gemini-3-flash-preview"
# GEMINI_MODEL_ID = "gemini-3-pro-preview"
# note gemini 3 reads the PDF's embedded text layer alongside the page image

# Set File Paths -------------------------------------------
INPUT_DIR = DATA_ROOT_DIR / "Raw" / "Digitization Scans Clean" / "FPC Physical Quantities"

# SET GEMINI PROMPT ------------------------------------------------------------
# Indicate the file name for the prompt to use
prompt_text_name = "fpc_pipelines_prompt.txt"

# Set Page Schema -----------------------------------
page_schema = FPCPage

# Page Parameters -------------------------------------------
# Indicate whether the pages should be uploaded as .png instead of .pdf
png = False
# Gemini 3 resolution for each pdf/image
MEDIA_RESOLUTION = "MEDIA_RESOLUTION_HIGH"

# SET FILE IDENTIFIERS ---------------------------------------------------------
RUN_PREFIX = "fpc_pipelines"

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

PROMPT_TEXT_PATH = CODE_DIR / "source" / "02_FPC_pipelines" / "prompts" / prompt_text_name

OUTPUT_DIR = DATA_ROOT_DIR / "Intermediate" / "pipelines"
GEMINI_DIR = OUTPUT_DIR / "gemini_output"
LOG_DIR = OUTPUT_DIR / "gemini_logs"

RUN_DIR = GEMINI_DIR / IDENTIFIER
OUTPUT_PATH = GEMINI_DIR / f"{IDENTIFIER}.csv"
FOOTNOTES_PATH = GEMINI_DIR / f"{IDENTIFIER}_footnotes.csv"
