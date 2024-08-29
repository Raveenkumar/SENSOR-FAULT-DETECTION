from dataclasses import dataclass
import os
from datetime import datetime
from src.constants import *
from pathlib import Path


TIMESTAMP: str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")


@dataclass
class BaseArtifactConfig:
    timestamp: str = TIMESTAMP
    artifact_dir: str = os.path.join("artifacts",timestamp)
    

@dataclass
class TrainingRawDataValidationConfig:
    purpose = "Training"
    raw_file_name_regex_format = REGEX_PATTERN
    good_raw_data_folder_path = os.path.join(BaseArtifactConfig.artifact_dir,TRAINING_DATA_FOLDER_NAME,GOOD_RAW_DATA_FOLDER_NAME)
    bad_raw_data_folder_path = os.path.join(BaseArtifactConfig.artifact_dir,TRAINING_DATA_FOLDER_NAME,BAD_RAW_DATA_FOLDER_NAME)
    validation_report_file_path = Path('data') / 'training_validation_logs.xlsx'
    schema_file_path = Path('config') / 'training_schema.json'

@dataclass
class PredictionRawDataValidationConfig:
    purpose = "Prediction"
    raw_file_name_regex_format = REGEX_PATTERN
    prediction_batch_files_path = PREDICTION_BATCH_FILES_PATH
    prediction_raw_data_folder_path = os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,PREDICTION_RAW_DATA)
    good_raw_data_folder_path = os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,GOOD_RAW_DATA_FOLDER_NAME)
    bad_raw_data_folder_path = os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,BAD_RAW_DATA_FOLDER_NAME)
    schema_file_path = Path('config') / 'training_schema.json'
    validation_report_file_path =  Path('data') / 'training_validation_logs.xlsx'