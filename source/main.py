# ------------------------------------------------------------------------------
# Load libraries ---------------------------------------------------------------
# ------------------------------------------------------------------------------
from google import genai
import os
from datetime import datetime
import pandas as pd

# Load the user-defined files -----

import config
from config import write_log
from PagesLib import digitizer
from eval import eval_performance

# Note: API requires an API key, saved in GEMINI_API_KEY.txt in this directory


def main():
    # TODO: pass in config here instead of importing?
    # --------------------------------------------------------------------------
    # -- Execution -------------------------------------------------------------
    # --------------------------------------------------------------------------
    # Valid parameters check
    if (config.page_window > 1 and config.png == True):
        raise ValueError(
            f"Page window is {config.page_window} but .png files must be a single page!"
        )

    # Create output directory
    if not os.path.exists(config.results_dir):
        os.makedirs(config.results_dir)
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)
    if not os.path.exists(config.intermediate_dir):
        os.makedirs(config.intermediate_dir)

    # Log parameters used -----------------------------------------
    config.log_config()

    print(f"Using task prompt in {config.prompt_text_name}")
    print(f"Saving output in {config.results_dir}")

    # Set the input data
    filepath = config.INPUT_FILE_PATH

    # get pages to digitize
    start_page, n_pages = digitizer.check_document(filepath,
                                                   all_pages=config.all_pages,
                                                   start_page=config.start_page,
                                                   n_pages=config.n_pages)

    # Create a client -----------------------------------------

    # get API key
    with open("secret/GEMINI_API_KEY.txt", "r", encoding="utf-8") as file:
        api_key = file.read()
        print("Successfully loaded API key")

    client = genai.Client(api_key=api_key)
    print("Successfully loaded Gemini AI client with API key")

    # Read in the structured prompt
    with open(config.prompt_text_path, "r", encoding="utf-8") as file:
        task = file.read()

    # Defined .csv outfile path
    outpath = os.path.join(config.results_dir, config.OUTPUT_FILE_NAME)
    print(f"Outpath set to: {outpath}")

    # Run digitizer process ------------------------------------------
    df = digitizer.process_pages(client,
                                 filepath,
                                 model=config.page_schema,
                                 prompt_text=task,
                                 model_id=config.gemini_model_id,
                                 total_pages=n_pages,
                                 start_page=start_page,
                                 outfile_path=outpath,
                                 intermediate_dir=config.intermediate_dir,
                                 page_window=config.page_window,
                                 page_placement=config.page_placement,
                                 png=config.png)
    write_log("PROCESS COMPLETE")
    print("\n Digitizing task complete !! ")

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------


if __name__ == "__main__":
    main()
