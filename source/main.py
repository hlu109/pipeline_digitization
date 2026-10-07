# ------------------------------------------------------------------------------
# Load libraries ---------------------------------------------------------------
# ------------------------------------------------------------------------------
from google import genai
import os
import signal
import sys
import time

# Load the user-defined files -----

import config
from PagesLib import digitizer
from PagesLib.digitizer import RateLimitException
from PagesLib.gemini_logging import write_run_boundary, log_config, _log_and_print
from PagesLib.Page import page_to_dataframe
from convert import csv_to_xlsx

# Note: API requires an API key, saved in secret/GEMINI_API_KEY.txt


def _sigterm_to_keyboard_interrupt(signum, frame):
    """Raises KeyboardInterrupt so a SIGTERM (sent by slurm scancel) is handled by the same interrupt logic as Ctrl+C."""
    raise KeyboardInterrupt()


signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)


def main():
    # --------------------------------------------------------------------------
    # Check parameters and create output directories
    # --------------------------------------------------------------------------
    if config.REUSE_OLD_RESULTS and not config.TEMP_DIR.exists():
        raise FileNotFoundError(
            f"REUSE_OLD_RESULTS is True but intermediate JSON directory does not exist: {config.TEMP_DIR}"
        )

    os.makedirs(config.GEMINI_DIR, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    os.makedirs(config.RUN_DIR, exist_ok=True)
    os.makedirs(config.TEMP_DIR, exist_ok=True)

    write_run_boundary(config.LOG_DIR, config.IDENTIFIER, "START")

    # Log parameters used -----------------------------------------
    log_config(prompt_text_path=config.PROMPT_TEXT_PATH,
               gemini_model_id=config.GEMINI_MODEL_ID,
               identifier=config.IDENTIFIER,
               log_dir=config.LOG_DIR,
               input_path=config.INPUT_FILE_PATH,
               output_path=config.OUTPUT_PATH,
               run_dir=config.RUN_DIR,
               data_struct=config.page_schema,
               png=config.png,
               reuse_old_results=config.REUSE_OLD_RESULTS,
               resume_run_identifier=config.RESUME_RUN_IDENTIFIER,
               note=config.NOTE)

    # --------------------------------------------------------------------------
    # Create Gemini client
    # --------------------------------------------------------------------------
    # get API key
    with open(config.API_KEY_PATH, "r", encoding="utf-8") as file:
        api_key = file.read().strip()
        print("Successfully loaded API key")

    client = genai.Client(api_key=api_key)
    print("Successfully loaded Gemini AI client with API key")

    # Read in the structured prompt
    with open(config.PROMPT_TEXT_PATH, "r", encoding="utf-8") as file:
        task = file.read()

    # --------------------------------------------------------------------------
    # Run digitizer process
    # --------------------------------------------------------------------------
    start_time = time.time()
    try:
        digitizer.process_pages(client,
                                config.INPUT_FILE_PATH,
                                data_struct=config.page_schema,
                                prompt_text=task,
                                model_id=config.GEMINI_MODEL_ID,
                                outfile_path=str(config.OUTPUT_PATH),
                                intermediate_dir=str(config.RUN_DIR),
                                temp_dir=str(config.TEMP_DIR),
                                to_dataframe_fn=page_to_dataframe,
                                png=config.png,
                                log_dir=config.LOG_DIR,
                                identifier=config.IDENTIFIER,
                                reuse_old_results=config.REUSE_OLD_RESULTS)
        elapsed_hrs = (time.time() - start_time) / 3600
        _log_and_print(f"PROCESS COMPLETE. Run time: {elapsed_hrs:.2f} hrs",
                       config.LOG_DIR, config.IDENTIFIER)
    except RateLimitException as e:
        _log_and_print(f"RUN ABORTED due to fatal rate limit: {e}",
                       config.LOG_DIR, config.IDENTIFIER)
        sys.exit(1)
    except KeyboardInterrupt:
        _log_and_print("RUN ABORTED.", config.LOG_DIR, config.IDENTIFIER)
        sys.exit(1)
    finally:
        write_run_boundary(config.LOG_DIR, config.IDENTIFIER, "END")


if __name__ == "__main__":
    main()
    csv_to_xlsx(config.RUN_DIR)  # make copies of all the csvs as xlsx
