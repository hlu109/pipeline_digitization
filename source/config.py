import os
from datetime import datetime
from PagesLib.Page import PagePrivate, PageGov

# ------------------------------------------------------------------------------
# SET PARAMETERS ---------------------------------------------------------------
# ------------------------------------------------------------------------------

gov = False  # True for government pipelines, False for private pipelines

# Set File Paths -------------------------------------------
# Define which pdf input to use
# Give entire path to the file; expecting a .pdf
private_file_path = "inputs/pipeline_scans/1943-1951_combined_private_only.pdf"
government_file_path = "inputs/pipeline_scans/1943-1945_combined_gov_only.pdf"
INPUT_FILE_PATH = government_file_path if gov else private_file_path

# Define your output file base name (no file extension)
OUTPUT_FILE_BASE_NAME = os.path.splitext(os.path.basename(INPUT_FILE_PATH))[0]

# SET OUTPUT PATH  -------------------------------------------------------------
output_dir = "outputs"
results_dir = os.path.join(output_dir, "gemini_output")
log_dir = os.path.join(output_dir, "logs")

# SET GEMINI PROMPT ------------------------------------------------------------
# Indicate the file name for the prompt to use
prompt_text_name = "pipeline_gov_prompt.txt" if gov else "pipeline_base_prompt.txt"
# prompt_text_name = "pipeline_base_prompt.txt"
# prompt_text_name = "pipeline_gov_prompt.txt"
prompt_text_path = os.path.join("source/prompts", prompt_text_name)

# Set Page Schema -----------------------------------
page_schema = PageGov if gov else PagePrivate

# Set API Parameters -------------------------------------------
# Define the model you are going to use (flash is free with 1,500 requests per day)
# gemini_model_id = "gemini-2.0-flash"
# gemini_model_id = "gemini-2.5-pro"
gemini_model_id = "gemini-2.5-flash"

# Set the number of pages before and after page N to feed into Gemini when digitizing page N
page_window = 1
page_placement = "top"

# Define number of pages to digitize.
all_pages = True  # If True, just does all the pages in the document
start_page = 1  # The starting page number in the file
n_pages = 1  # The number of pages (total) to digitize

# Indicate whether the pages should be saved as .png instead of .pdf
# ! NOTE: .png files must be a single page, so this only works with page_window=1
png = False


# ------------------------------------------------------------------------------
# END OF SET PARAMETERS --------------------------------------------------------
# ------------------------------------------------------------------------------

# save each execution with a separate file suffix --- to ensure nothing is over-written
timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
identifier = f"{timestamp}_by{page_window}pgs"
OUTPUT_FILE_NAME = OUTPUT_FILE_BASE_NAME + "_" + identifier + ".csv"

# folder for intermediate results
intermediate_dir = os.path.join(results_dir, "intermediate_" + identifier)

# TODO: move this to utils
# Define logging function


def write_log(message, log_dir=log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_path = os.path.join(log_dir, f"log_{identifier}.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%H%M:%S")
        file.write(f"[{timestamp}] {message}\n\n")


def log_config(log_dir=log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save text of gemini prompt--------
    with open(prompt_text_path, "r") as file:
        prompt_text = file.read()
    with open(os.path.join(log_dir, "prompt_text.txt"), "a",
              encoding="utf-8") as file:
        file.write(prompt_text)

    # Save parameter values ----------
    file_path = os.path.join(log_dir, f"log_{identifier}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] \n\n")
        file.write(f"CONFIG PARAMETERS\n\n")
        # file.write(f"Directory file year: {input_file_year}\n")
        file.write(f"Start page: {start_page}\n")
        file.write(f"End page: {start_page + n_pages - 1}\n")
        file.write(f"Page window: {page_window}\n")
        file.write(f"Prompt text file: {prompt_text_name}\n")
        file.write(f"Gemini model: {gemini_model_id}\n\n")


# ------------------------------------------------------------------------------
# -----------------------------------------------------------------------------
