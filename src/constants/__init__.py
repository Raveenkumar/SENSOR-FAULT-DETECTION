# general constants



# validation constants
REGEX_PATTERN :str = "wafer_(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])\d{4}_(0[0-9]|1[0-9]|2[0-3])([0-5][0-9]){2}\.csv"   # type: ignore
TRAINING_BATCH_FILES_PATH: str = "artifacts/Client_DB_Data/training_batch_files"
PREDICTION_BATCH_FILES_PATH: str = "artifacts/Client_DB_Data/prediction_batch_files"
TRAINING_DATA_FOLDER_NAME: str = "training_data"
PREDICTION_DATA_FOLDER_NAME: str = 'prediction_data'
PREDICTION_RAW_DATA: str = "prediction_raw_data"
GOOD_RAW_DATA_FOLDER_NAME: str = "good_raw_data"
BAD_RAW_DATA_FOLDER_NAME: str = "bad_raw_data"




#api_constants
APP_HOST = "0.0.0.0"
APP_PORT = 8080
