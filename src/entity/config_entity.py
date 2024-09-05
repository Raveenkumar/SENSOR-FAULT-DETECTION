from dataclasses import dataclass,field
import os
from datetime import datetime
from src.constants import *
from pathlib import Path


TIMESTAMP: str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")


@dataclass
class BaseArtifactConfig:
    timestamp: str = TIMESTAMP
    artifact_base_dir = Path(ARTIFACT_FOLDER_NAME)
    artifact_dir:Path = artifact_base_dir / timestamp

@dataclass    
class LogValidationConfig:
    log_folder_path:Path = Path(LOG_FOLDER_NAME)
    log_file_path:Path = log_folder_path / LOG_FILE_NAME

@dataclass
class TrainingRawDataValidationConfig:
    purpose = "Training"
    raw_file_name_regex_format = REGEX_PATTERN
    good_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,TRAINING_DATA_FOLDER_NAME,GOOD_RAW_DATA_FOLDER_NAME))
    bad_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,TRAINING_DATA_FOLDER_NAME,BAD_RAW_DATA_FOLDER_NAME))
    validation_report_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,TRAINING_DATA_FOLDER_NAME,EVALUATION_DATA_FOLDER_NAME,TRAINING_VALIDATION_LOG_FILE))
    schema_file_path = Path('config') / 'training_schema.json'

@dataclass
class PredictionRawDataValidationConfig:
    purpose = "Prediction"
    raw_file_name_regex_format = REGEX_PATTERN
    prediction_batch_files_path = PREDICTION_BATCH_FILES_PATH
    prediction_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,PREDICTION_RAW_DATA))
    good_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,GOOD_RAW_DATA_FOLDER_NAME))
    bad_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,BAD_RAW_DATA_FOLDER_NAME))
    schema_file_path = Path('config') / 'training_schema.json'
    validation_report_file_path =  Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,EVALUATION_DATA_FOLDER_NAME,PREDICTION_VALIDATION_LOG_FILE))
    
@dataclass
class TrainingRawDataTransformationConfig(TrainingRawDataValidationConfig):
    old_wafer_column_name = OLD_WAFER_COLUMN_NAME
    old_output_column_name = OLD_OUTPUT_COLUMN_NAME
    new_wafer_column_name = NEW_WAFER_COLUMN_NAME
    new_output_column_name = NEW_OUTPUT_COLUMN_NAME
    merge_file_path =  Path(os.path.join(BaseArtifactConfig.artifact_dir,TRAINING_DATA_FOLDER_NAME,FINAL_TRAINING_FILE_FOLDER_NAME,FINAL_FILE_NAME))
    
    
@dataclass
class PredictionRawDataTransformationConfig(PredictionRawDataValidationConfig):
    old_wafer_column_name = OLD_WAFER_COLUMN_NAME
    old_output_column_name = OLD_OUTPUT_COLUMN_NAME
    new_wafer_column_name = NEW_WAFER_COLUMN_NAME
    new_output_column_name = NEW_OUTPUT_COLUMN_NAME
    merge_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,FINAL_PREDICTION_FILE_FOLDER_NAME,FINAL_FILE_NAME))
        
@dataclass
class AppConfig:
    training_folder_path  = Path(r"C:\Users\RAVEEN\Downloads\testing_data\batch3")     