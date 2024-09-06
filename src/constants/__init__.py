from datetime import datetime




# general constants
ARTIFACT_FOLDER_NAME:str = "artifacts"
DATA_FOLDER_NAME:str = 'data'
MODEL_DATA_FOLDER_NAME: str = "model_data"

#logs constants
LOG_FOLDER_NAME:str = "logs"
LOG_FILE_NAME:str = f"{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.log"

# validation constants
REGEX_PATTERN :str = "wafer_(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])\d{4}_(0[0-9]|1[0-9]|2[0-3])([0-5][0-9]){2}\.csv"   # type: ignore
TRAINING_BATCH_FILES_PATH: str = "artifacts/Client_DB_Data/training_batch_files"
PREDICTION_BATCH_FILES_PATH: str = "artifacts/Client_DB_Data/prediction_batch_files"
TRAINING_DATA_FOLDER_NAME: str = "training_data"
PREDICTION_DATA_FOLDER_NAME: str = 'prediction_data'
PREDICTION_RAW_DATA: str = "prediction_raw_data"
GOOD_RAW_DATA_FOLDER_NAME: str = "good_raw_data"
BAD_RAW_DATA_FOLDER_NAME: str = "bad_raw_data"
EVALUATION_DATA_FOLDER_NAME: str  = "evaluation_data"
TRAINING_VALIDATION_LOG_FILE: str = "training_validation_logs.xlsx"
PREDICTION_VALIDATION_LOG_FILE: str = "prediction_validation_logs.xlsx"


# transformation constants
OLD_WAFER_COLUMN_NAME: str = "Unnamed: 0"
OLD_OUTPUT_COLUMN_NAME: str = "Good/Bad"
NEW_WAFER_COLUMN_NAME: str = "Wafer"
NEW_OUTPUT_COLUMN_NAME: str = "Output"
FINAL_TRAINING_FILE_FOLDER_NAME: str = "training_file_data"
FINAL_PREDICTION_FILE_FOLDER_NAME: str = "prediction_file_data"
FINAL_FILE_NAME: str = "final_file.csv"

# preprocessing_constants
LOWER_PERCENTILE:float = 0.05
UPPER_PERCENTILE:float = 0.95
IQR_MULTIPLIER:float = 1.5
EXPERIMENT_FOLDER_NAME:str = "experiment_model_data"
STABLE_FOLDER_NAME:str = "stable_model_data"
PREPROCESSOR_FOLDER_NAME:str = "preprocessor"
PREPROCESSOR_OBJECT_NAME:str = "preprocessor_obj.dill"

# cluster constants
CLUSTER_COLUMN_NAME:str = "Cluster"




#s3 constants
BUCKET_NAME:str = 'wafersensorsdata'

#api_constants
APP_HOST:str = "0.0.0.0"
APP_PORT:int = 8080
