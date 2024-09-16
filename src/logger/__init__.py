import os
import sys
import logging
from src.entity.config_entity import LogValidationConfig

logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"
log_dir = LogValidationConfig.log_folder_path
log_filepath = LogValidationConfig.log_file_path
os.makedirs(log_dir, exist_ok=True)


logging.basicConfig(
    level= logging.INFO,
    format= logging_str,

    handlers=[
        logging.FileHandler(log_filepath), #  saving in folder
        logging.StreamHandler(sys.stdout)  # log can print on terminal
    ]
)

logger = logging.getLogger("sensor_fault_detection")