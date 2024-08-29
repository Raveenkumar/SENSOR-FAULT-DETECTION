from dataclasses import dataclass
import os
from datetime import datetime
from src.constants import *
from pathlib import Path
# raw data validation artifacts
@dataclass
class RawDataValidationArtifacts:
    good_raw_data_folder:str
    bad_raw_data_folder:str
    validation_log_file_path:Path
   

