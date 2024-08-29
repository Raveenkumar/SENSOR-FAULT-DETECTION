import os
import sys
import logging
from datetime import datetime


LOG_FILE = f"{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.log"
logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"
log_dir = "logs"

log_filepath = os.path.join(log_dir,LOG_FILE)
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