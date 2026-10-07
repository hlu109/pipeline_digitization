# ------------------------------------------------------------------------------
# Load libraries ---------------------------------------------------------------
# ------------------------------------------------------------------------------
from google import genai
import json
import os
import re
import signal
import sys
import time
from functools import partial
from pathlib import Path

import pandas as pd

# Add source/ to Python path to allow imports from utils
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load the user-defined files -----

import config_gemini as config
from utils import gemini_digitizer as digitizer
from utils.gemini_digitizer import RateLimitException, _sigterm_to_keyboard_interrupt
from utils.gemini_logging import write_run_boundary, log_config, _log_and_print
from data_structs.FPCPage import FPCPage, page_to_dataframe, page_to_footnotes_dataframe

# handle slurm cancellation signals
signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)


def main():
    # --------------------------------------------------------------------------
    # Check parameters and create output directories
    # --------------------------------------------------------------------------
    if config.REUSE_OLD_RESULTS and not config.RUN_DIR.exists():
        raise FileNotFoundError(
            f"REUSE_OLD_RESULTS is True but the run directory does not exist: {config.RUN_DIR}"
        )

    # map each input PDF to the data year in its file name
    input_files = {}
    for pdf_path in sorted(config.INPUT_DIR.glob("*.pdf")):
        years = re.findall(r"19\d\d", pdf_path.stem)
        if len(years) == 0:  # skip
            continue
        if len(years) > 1:
            raise ValueError(
                f"Expected exactly one year in the file name: {pdf_path.name}")
        input_files[pdf_path] = int(years[0])
    if not input_files:
        raise FileNotFoundError(
            f"No PDFs with a year in the file name found in {config.INPUT_DIR}"
        )

    os.makedirs(config.GEMINI_DIR, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    os.makedirs(config.RUN_DIR, exist_ok=True)

    write_run_boundary(config.LOG_DIR, config.IDENTIFIER, "START")

    # Log parameters used -----------------------------------------
    log_config(prompt_text_path=config.PROMPT_TEXT_PATH,
               gemini_model_id=config.GEMINI_MODEL_ID,
               identifier=config.IDENTIFIER,
               log_dir=config.LOG_DIR,
               input_path=config.INPUT_DIR,
               output_path=config.OUTPUT_PATH,
               run_dir=config.RUN_DIR,
               data_struct=config.page_schema,
               png=config.png,
               media_resolution=config.MEDIA_RESOLUTION,
               reuse_old_results=config.REUSE_OLD_RESULTS,
               resume_run_identifier=config.RESUME_RUN_IDENTIFIER,
               note=config.NOTE)
    _log_and_print(
        f"Input files: {[f'{p.name} ({yr})' for p, yr in input_files.items()]}",
        config.LOG_DIR, config.IDENTIFIER)

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
        mileage_dfs = []
        footnote_dfs = []
        for pdf_path, data_year in input_files.items():
            _log_and_print(f"Digitizing {pdf_path.name}", config.LOG_DIR,
                           config.IDENTIFIER)
            file_run_dir = config.RUN_DIR / str(data_year)
            file_temp_dir = file_run_dir / "temp"
            os.makedirs(file_temp_dir, exist_ok=True)

            df = digitizer.process_pages(
                client,
                pdf_path,
                data_struct=config.page_schema,
                prompt_text=task,
                model_id=config.GEMINI_MODEL_ID,
                outfile_path=str(file_run_dir / f"{data_year}.csv"),
                intermediate_dir=str(file_run_dir),
                temp_dir=str(file_temp_dir),
                to_dataframe_fn=partial(page_to_dataframe,
                                        data_year=data_year,
                                        source_file=pdf_path.name),
                png=config.png,
                media_resolution=config.MEDIA_RESOLUTION,
                log_dir=config.LOG_DIR,
                identifier=config.IDENTIFIER,
                reuse_old_results=config.REUSE_OLD_RESULTS)
            if df is not None:
                mileage_dfs.append(df)

            # separately build footnotes from the page-level JSONs
            for json_path in sorted(file_temp_dir.glob("pg*.json")):
                with open(json_path, "r", encoding="utf-8") as file:
                    result_json = json.load(file)
                fn_df = page_to_footnotes_dataframe(
                    FPCPage.model_validate(result_json),
                    data_year=data_year,
                    source_file=pdf_path.name)
                # copy over the run metadata
                for key in ("model_id", "absolute_page_n"):
                    fn_df[key] = result_json.get(key)
                footnote_dfs.append(fn_df)

        # combine all years
        if mileage_dfs:
            mileage = pd.concat(mileage_dfs, ignore_index=True)
            mileage.to_csv(config.OUTPUT_PATH, index=False)
            _log_and_print(
                f"Saved {mileage.shape[0]} mileage rows to {config.OUTPUT_PATH}",
                config.LOG_DIR, config.IDENTIFIER)

        if footnote_dfs:
            footnotes = pd.concat(footnote_dfs, ignore_index=True)
            footnotes.to_csv(config.FOOTNOTES_PATH, index=False)
            _log_and_print(
                f"Saved {footnotes.shape[0]} footnotes to {config.FOOTNOTES_PATH}",
                config.LOG_DIR, config.IDENTIFIER)

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
