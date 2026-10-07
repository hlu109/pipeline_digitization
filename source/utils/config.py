# Shared machine-specific paths for all digitization tasks.
import getpass
import os
from pathlib import Path

# ------------------------------------------------------------------------------
# AUTO-SET BASE DIRECTORIES
# ------------------------------------------------------------------------------

_user = getpass.getuser()
if _user == "hl2266":
    DROPBOX_DIR = Path("C:/Users/hl2266/YLS Dropbox/Hannah Lu/permitting_hub/")
    # if "dropbox" in os.getcwd().lower():
    #     # code is in personal dir but use shared dropbox for data
    #     CODE_DIR = Path(
    #         "C:/Users/hl2266/YLS Dropbox/Hannah Lu/personal/predoc/Permitting project/Code/pipeline_digitization"
    #     )
    #     DATA_ROOT_DIR = DROPBOX_DIR / "Data"
    if "docker" in os.getcwd().lower():
        # code is in docker dir but use shared dropbox for data
        CODE_DIR = Path(
            "C:/Users/hl2266/project_dockers/pipelines/Code/pipeline_digitization"
        )
        DATA_ROOT_DIR = DROPBOX_DIR / "Data"
    elif "pi_zdl3" in os.getcwd().lower():
        BASE_DIR = Path("/nfs/roberts/project/pi_zdl3/shared/permitting")
        CODE_DIR = BASE_DIR / "Code" / "pipeline_digitization"
        DATA_ROOT_DIR = BASE_DIR / "Data"
    else:
        raise ValueError("Invalid location specified")
else:
    raise ValueError("Add user paths to config")

API_KEY_PATH = CODE_DIR / "secret" / "GEMINI_API_KEY.txt"
