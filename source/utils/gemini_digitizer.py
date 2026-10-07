from pydantic import BaseModel
from PyPDF2 import PdfReader, PdfWriter
from google.genai import errors
import tempfile
import time
import json
import os
import pandas as pd
from pdf2image import convert_from_path
from utils.gemini_logging import _log_and_print


class RateLimitException(Exception):
    """Raised when 429 retries are exhausted to abort full run."""


class ClientNonRetryableException(Exception):
    """Raised when the model rejects a request with a non-retryable client error."""


def _sigterm_to_keyboard_interrupt(signum, frame):
    """Raises KeyboardInterrupt so a SIGTERM (sent by slurm scancel) is handled by the same interrupt logic as Ctrl+C."""
    raise KeyboardInterrupt()


# ==============================================================================
# Gemini
# ==============================================================================


def upload_pages_to_API(genai_client,
                        file_path: str,
                        page_n: int,
                        png=False,
                        log_dir=None,
                        identifier=None):
    """
    Uploads a single page from a PDF (or PNG if requested) to the Gemini API.

    Parameters:
        genai_client: Gemini API client.
        file_path (str): Path to the input PDF file.
        page_n (int): PDF page to upload (1-indexed).
        png (bool): If True, converts the page to PNG format.
        log_dir (str): Directory for writing Gemini error logs.
        identifier (str): Run identifier used for the Gemini log filename.

    Returns:
        object: Uploaded file object from the Gemini API.
    """
    file_name = f"{page_n}__{os.path.splitext(os.path.basename(file_path))[0]}"
    if png:
        file_name = file_name + "_png"

    # Check if file already exists in the File API
    uploaded_file = None
    max_retries = 7
    base_wait = 10
    should_check_existing = True

    # Error handling: retry server errors (5xx) and rate limits (429) with exponential backoff.
    # For all other errors, in order to keep things running, we bypass the check for existing files and upload directly.
    for attempt in range(max_retries):
        if not should_check_existing:
            break
        try:
            existing_files = genai_client.files.list()
            for f in existing_files:
                if f.display_name == file_name:
                    uploaded_file = f
                    print(
                        f"    File '{file_name}' already exists in the File API. Skipping upload."
                    )
                    break
            break
        except errors.ServerError as e:
            wait_time = base_wait * (2**attempt)
            m = f"Server error {e.code} while checking existing upload for '{file_name}' on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
            _log_and_print(m, log_dir, identifier)
            time.sleep(wait_time)
        except errors.ClientError as e:
            if e.code == 429:
                wait_time = 60 * (2**attempt)
                m = f"Rate limit (429 error) while checking existing upload for '{file_name}' on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
                _log_and_print(m, log_dir, identifier)
                time.sleep(wait_time)
            else:
                m = f"Warning: existing file check failed for '{file_name}' (client error {e.code}). Skipping check and proceeding with direct upload: {e}"
                _log_and_print(m, log_dir, identifier)
                should_check_existing = False
        except Exception as e:
            m = f"Warning: existing file check failed for '{file_name}'. Skipping check and proceeding with direct upload: {e}"
            _log_and_print(m, log_dir, identifier)
            should_check_existing = False

    if should_check_existing and not uploaded_file and attempt == max_retries - 1:
        m = f"Max retries reached while checking existing upload for '{file_name}'. Proceeding with direct upload."
        _log_and_print(m, log_dir, identifier)

    if uploaded_file:
        return uploaded_file

    # Upload file (only if it has not already been uploaded)
    # Create a temporary file with the selected page ----
    if png:
        images = convert_from_path(file_path,
                                   first_page=page_n,
                                   last_page=page_n)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_path = temp_file.name
        temp_file.close()
        images[0].save(temp_path, 'PNG')
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_path = temp_file.name
        temp_file.close()  # Close the file so PyPDF2 can write to it
        reader = PdfReader(file_path)
        writer = PdfWriter()
        writer.add_page(reader.pages[page_n -
                                     1])  # convert 1-based to 0-based index
        with open(temp_path, "wb") as output:
            writer.write(output)

    # Upload the file to the File API ---
    try:
        print(f"    Uploading file: {file_name}")
        uploaded_file = genai_client.files.upload(
            file=temp_path, config={'display_name': file_name})
    finally:
        # delete tmp file after it's uploaded
        os.remove(temp_path)

    return uploaded_file


def extract_page_data(genai_client,
                      input_file,
                      data_struct: type[BaseModel],
                      prompt_text: str,
                      model_id: str,
                      page_n=None,
                      log_dir=None,
                      identifier=None):
    """
    Extracts structured data from a page using the Gemini API.

    Parameters:
        genai_client: Gemini API client.
        input_file: File object uploaded to the Gemini API.
        data_struct (BaseModel): Data structure for extracted content.
        prompt_text (str): Prompt text for the API.
        model_id (str): Gemini model ID.
        page_n (int): TODO: get rid of this param
        log_dir (str): Directory for writing Gemini error logs.
        identifier (str): Run identifier used for the Gemini log filename.

    Returns:
        BaseModel or None: Parsed structured data if successful, otherwise None.
    """
    # limit output size
    max_token_output = 80000
    max_retries = 7
    base_wait = 10  # this is in seconds!

    for attempt in range(max_retries):
        print(f"      Attempt {attempt + 1} to extract data...")
        log_prefix = f"page={page_n} \t\nmodel_id={model_id} \t\nextract_attempt={attempt + 1} \t\n"
        try:
            # Generate a structured response using the Gemini API ---
            response = genai_client.models.generate_content(
                model=model_id,
                contents=[prompt_text, input_file],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': data_struct,
                    'max_output_tokens': max_token_output
                })

            # print("API Response:", response)  # Debugging step
            # print(" Response Usage Metadata:", response.usage_metadata)

            # Check for token limit issues
            if hasattr(response, 'candidates') and response.candidates:
                if response.candidates[0].finish_reason.name == 'MAX_TOKENS':
                    m = (
                        f"WARNING: Response truncated due to token limit. Consider increasing max_output_tokens or splitting the page. "
                        f"Token count: {response.usage_metadata.candidates_token_count}"
                    )
                    _log_and_print(log_prefix + m, log_dir, identifier)

            if not response or not response.parsed:
                m = "ERROR: The API did not return a valid parsed response."
                _log_and_print(log_prefix + m, log_dir, identifier)
                return None

            return response.parsed

        # retry server errors with exponential backoff; retry 429s with a longer wait and kill the run if they persist
        except errors.ServerError as e:
            wait_time = base_wait * (2**attempt)
            m = f"Server error {e.code} on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
            _log_and_print(log_prefix + m, log_dir, identifier)
            time.sleep(wait_time)
        except errors.ClientError as e:
            if e.code == 429:
                # rate limits are per minute and per day; if a long wait still hits the limit we have likely exhausted the daily quota and should downgrade the model, so kill the run
                if attempt == max_retries - 1:
                    m = "Max rate limit retries reached."
                    _log_and_print(log_prefix + m, log_dir, identifier)
                    raise RateLimitException(
                        "Max rate limit retries reached. Killing rest of the full run."
                    )
                wait_time = 60 * (2**attempt)
                m = f"Rate limit (429 error) on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
                _log_and_print(log_prefix + m, log_dir, identifier)
                time.sleep(wait_time)
            else:
                # in general, Gemini documentation says not to retry on client errors like 400 or 403 as they indicate issues like invalid API keys or bad syntax
                m = f"Client error {e.code} occurred (non-retryable): {e}"
                _log_and_print(log_prefix + m, log_dir, identifier)
                raise ClientNonRetryableException(str(e))
        except Exception as e:
            m = f"Other exception occurred (non-retryable): {e}"
            _log_and_print(log_prefix + m, log_dir, identifier)
            return None

    m = "Max error retries reached. Giving up on this page."
    _log_and_print(log_prefix + m, log_dir, identifier)
    return None


# ==============================================================================
# Processing loop
# ==============================================================================


def _save_partial_results(all_dataframes, outfile_path, log_dir, identifier,
                          reason):
    """
    Saves accumulated rows to CSV and returns the concatenated DataFrame.

    Parameters:
        all_dataframes (list): List of per-page DataFrames to concatenate and save.
        outfile_path (str): Output CSV path.
        log_dir (str): Logging directory.
        identifier (str): Run identifier.
        reason (str): Reason why the partial save was triggered.

    Returns:
        Concatenated DataFrame, or None.
    """
    if not all_dataframes:
        _log_and_print(f"{reason}: no partial results to save.", log_dir,
                       identifier)
        return None
    partial_df = pd.concat(all_dataframes, ignore_index=True)
    partial_df.to_csv(outfile_path, index=False)
    _log_and_print(
        f"{reason}: partial results saved to {outfile_path} ({partial_df.shape[0]} rows).",
        log_dir, identifier)
    return partial_df


def process_pages(genai_client,
                  file_path: str,
                  data_struct: type[BaseModel],
                  prompt_text: str,
                  model_id: str,
                  outfile_path: str,
                  intermediate_dir: str,
                  temp_dir: str,
                  to_dataframe_fn,
                  png=False,
                  log_dir=None,
                  identifier=None,
                  reuse_old_results: bool = False):
    """
    Extracts structured data from every page in the document and saves results.

    Parameters:
        genai_client: Gemini API client.
        file_path (str): Path to the PDF file.
        data_struct (BaseModel): Data structure for extracted content.
        prompt_text (str): Prompt text for the API.
        model_id (str): Gemini model ID.
        outfile_path (str): Path to save extracted data.
        intermediate_dir (str): Folder for per-page CSV outputs. 
        # TODO: get rid of either the csv or the jsons later
        temp_dir (str): Folder for per-page JSONs.
        to_dataframe_fn: Function converting a parsed page schema object to a DataFrame.
        png (bool): If True, converts pages to PNG before upload.
        log_dir (str): Directory for writing Gemini error logs.
        identifier (str): Run identifier used for the Gemini log filename.
        reuse_old_results (bool): If True, pages whose JSON already exists in temp_dir are loaded from disk instead of re-queried.

    Returns:
        pd.DataFrame: Aggregated structured data extracted from the document.
    """
    all_dataframes = []
    failed_pages = []
    max_retries = 5
    start_time = time.time()

    # track issues in real time
    processed_count = 0

    with open(file_path, "rb") as file:
        total_pages = len(PdfReader(file).pages)

    try:
        for N in range(1, total_pages + 1):
            print(f"\nProcessing page {N}/{total_pages}...")
            json_path = os.path.join(temp_dir, f"pg{N}.json")
            csv_path = os.path.join(intermediate_dir, f"pg{N}.csv")

            # Resume support: load intermediate JSON if it already exists rather than re-querying Gemini
            if reuse_old_results and os.path.exists(json_path):
                print(
                    f"  Page {N}/{total_pages}: intermediate JSON exists, reusing cached result."
                )
                with open(json_path, "r", encoding="utf-8") as file:
                    result_json = json.load(file)
                result = data_struct.model_validate(result_json)
                df = to_dataframe_fn(result)
                for key in ("model_id", "absolute_page_n"):
                    if key in result_json:
                        df[key] = result_json[key]
                all_dataframes.append(df)
                continue

            processed_count += 1

            retries = 0
            success = False
            df = None

            while retries < max_retries and not success:
                try:
                    print(f"\t(Attempt {retries + 1})...")

                    # get uploaded pages
                    # TODO: non-retryable upload errors (e.g. 400/403) fall through to the generic handler below and are retried; give up immediately on these instead
                    uploaded_file = upload_pages_to_API(genai_client,
                                                        file_path,
                                                        N,
                                                        png=png,
                                                        log_dir=log_dir,
                                                        identifier=identifier)

                    # submit to Gemini for extraction
                    result = extract_page_data(genai_client,
                                               uploaded_file,
                                               data_struct,
                                               prompt_text,
                                               model_id,
                                               page_n=N,
                                               log_dir=log_dir,
                                               identifier=identifier)

                    if result:
                        success = True
                        runtime_metadata = {
                            "model_id": model_id,
                            "absolute_page_n": N
                        }
                        # add metadata to the output
                        result_json = result.model_dump()
                        result_json.update(runtime_metadata)

                        # save intermediate data structure to json to handle unplanned termination and be able to resume from existing progress
                        with open(json_path, "w", encoding="utf-8") as file:
                            json.dump(result_json,
                                      file,
                                      indent=4,
                                      ensure_ascii=False)

                        df = to_dataframe_fn(result)
                        # add metadata to final dataframe
                        for key, value in runtime_metadata.items():
                            df[key] = value

                        df.to_csv(csv_path, index=False)
                        _log_and_print(
                            f"  Saved intermediate results to {csv_path}",
                            log_dir, identifier)
                        # TODO: might get rid of this later

                        # Immediately delete the uploaded file to avoid storage limits
                        try:
                            genai_client.files.delete(name=uploaded_file.name)
                            _log_and_print(
                                f"Deleted uploaded file: {uploaded_file.name}",
                                log_dir, identifier)
                        except Exception as e:
                            _log_and_print(
                                f"Warning: failed to delete uploaded file {uploaded_file.name}: {e}",
                                log_dir, identifier)

                    else:
                        m = f"FAILURE - No results retrieved for page {N}."
                        _log_and_print(
                            f"page={N} \t\nmodel_id={model_id} \t\n{m}",
                            log_dir, identifier)
                        retries += 1
                        if retries < max_retries:
                            m = f"Retrying page {N} in 5 seconds..."
                            _log_and_print(
                                f"page={N} \t\npage_attempt={retries + 1} \t\n{m}",
                                log_dir, identifier)
                            time.sleep(5)
                        else:
                            _log_and_print(
                                f"Max retries reached for page {N}. Giving up.",
                                log_dir, identifier)

                except ClientNonRetryableException as e:
                    _log_and_print(f"page={N} \t\nGiving up immediately: {e}",
                                   log_dir, identifier)
                    break

                except RateLimitException:
                    # propagate so the run stops; otherwise the generic handler below would catch it and keep retrying
                    raise

                except Exception as e:
                    m = f"Unexpected error: {e}"
                    _log_and_print(
                        f"page={N} \t\npage_attempt={retries + 1} \t\n{m}",
                        log_dir, identifier)
                    retries += 1
                    if retries < max_retries:
                        m = f"Retrying page {N} in 5 seconds..."
                        _log_and_print(
                            f"page={N} \t\npage_attempt={retries + 1} \t\n{m}",
                            log_dir, identifier)
                        time.sleep(5)
                    else:
                        _log_and_print(
                            f"Max retries reached for page {N}. Giving up.",
                            log_dir, identifier)

            # combine output
            if success and df is not None:
                all_dataframes.append(df)
            else:
                # track failed pages explicitly so we can retry later
                failed_pages.append(N)

            total_time_elapsed = time.time() - start_time
            avg_time_per_page = total_time_elapsed / processed_count if processed_count else 0

            if N % 10 == 0:
                _log_and_print(f"Progress: {N}/{total_pages}", log_dir,
                               identifier)
                _log_and_print(
                    f"Total time elapsed: {total_time_elapsed / 3600:.2f} hrs",
                    log_dir, identifier)
                _log_and_print(
                    f"Average time per Gemini query so far: {avg_time_per_page:.2f} s",
                    log_dir, identifier)
                _log_and_print(
                    f"Pages with no Gemini output so far: {len(failed_pages)}",
                    log_dir, identifier)

    except KeyboardInterrupt:
        _log_and_print("RUN INTERRUPTED by user.", log_dir, identifier)
        _save_partial_results(all_dataframes, outfile_path, log_dir,
                              identifier, "Keyboard interrupt")
        raise
    except RateLimitException as e:
        _log_and_print(f"FATAL rate limit error: {e}", log_dir, identifier)
        _save_partial_results(all_dataframes, outfile_path, log_dir,
                              identifier, "Fatal rate limit stop")
        raise

    # log failed pages so they can be rerun with REUSE_OLD_RESULTS
    m = f"Total pages with no Gemini output: {len(failed_pages)} {failed_pages}"
    _log_and_print(m, log_dir, identifier)

    if all_dataframes:
        final_dataframe = pd.concat(all_dataframes, ignore_index=True)
        _log_and_print(
            f"Generated dataframe with {final_dataframe.shape[0]} rows",
            log_dir, identifier)
        final_dataframe.to_csv(outfile_path, index=False)
        _log_and_print(f"  Saved final output to {outfile_path}", log_dir,
                       identifier)
        return final_dataframe
    else:
        return None
