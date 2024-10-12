from datetime import datetime




# general constants
ARTIFACT_FOLDER_NAME:str = "artifacts"
DATA_FOLDER_NAME:str = 'data'
MODEL_DATA_FOLDER_NAME: str = "model_data"
DASHBOARD_DATA_FOLDER_NAME: str = "dashboard_data"


#logs constants
LOG_FOLDER_NAME:str = "logs"
LOG_FILE_NAME:str = f"{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.log"


#data ingestion constants
FINAL_FILE_TWO_NAME:str = 'final_file_prediction.csv'

# validation constants
REGEX_PATTERN :str = "wafer_(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])\d{4}_(0[0-9]|1[0-9]|2[0-3])([0-5][0-9]){2}\.csv"   # type: ignore
TRAINING_BATCH_FILES_PATH: str = "artifacts/Client_DB_Data/training_batch_files"
PREDICTION_BATCH_FILES_PATH: str = "artifacts/Client_DB_Data/prediction_batch_files"
TRAINING_DATA_FOLDER_NAME: str = "training_data"
PREDICTION_DATA_FOLDER_NAME: str = 'prediction_data'
PREDICTION_BATCH_DATA: str = "prediction_batch_files"
GOOD_RAW_DATA_FOLDER_NAME: str = "good_raw_data"
BAD_RAW_DATA_FOLDER_NAME: str = "bad_raw_data"
EVALUATION_DATA_FOLDER_NAME: str  = "evaluation_data"
TRAINING_VALIDATION_LOG_FILE: str = "training_validation_logs.xlsx"
PREDICTION_VALIDATION_LOG_FILE: str = "prediction_validation_logs.xlsx"
BAD_RAW_ZIP_FILE_NAME:str = "bad_raw_data.zip"
BAD_FILE_NAMES_FILE_NAME:str = "bad_file_names.json"

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
PREPROCESSOR_FOLDER_NAME:str = "preprocessor_stage_one"
PREPROCESSOR_OBJECT_NAME:str = "preprocessor_obj.dill"
PREPROCESSOR_JSON_FILE_NAME:str = "preprocessing_report.json"
NON_DUPLICATE_DF_NAME :str = "final_non_duplicate_df.csv"

# cluster constants
CLUSTER_COLUMN_NAME:str = "Cluster"
CLUSTER_FOLDER_NAME:str = "cluster"
CLUSTER_OBJECT_NAME:str = "cluster_obj.dill"

## model tuner constants
# kfold n splits
KFOLD_N_SPLITS:int = 5

#pca n_components
PCA_N_COMPONENTS: int | float | str | None = 0.99

# model hyperparameters
GAUSSIANNB_PARAM_GRID = {
        'var_smoothing': [1e-9, 1e-8, 1e-7, 1e-6, 1e-5]  # Tuning var_smoothing for GaussianNB
    }

SVC_PARAM_GRID: dict = {
    'C': [0.001, 0.01, 0.1, 1, 10, 100],
    'kernel': ['rbf', 'linear', 'poly'],
    'gamma': [0.0001, 0.001, 0.01, 0.1, 'scale', 'auto']
    }

RANDOM_FOREST_PARAM_GRID: dict = {
    'n_estimators': [100, 200, 300, 400, 500],
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['sqrt', 'log2'],
    'bootstrap': [True, False],
    'criterion': ['gini', 'entropy']
}

XGB_CLASSIFIER_PARAM_GRID: dict= {
    'n_estimators': [50, 100, 200, 500],
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'max_depth': [3, 4, 5, 6, 8, 10],
    'min_child_weight': [1, 3, 5, 7],
    'gamma': [0, 0.1, 0.2, 0.3, 0.4, 0.5],
    'subsample': [0.5, 0.6, 0.7, 0.8, 0.9, 1],
    'colsample_bytree': [0.5, 0.6, 0.7, 0.8, 0.9, 1],
    'reg_alpha': [0, 0.1, 0.5, 1, 5, 10],
    'reg_lambda': [0, 0.1, 0.5, 1, 5, 10]
}
# model trainer and tuner constants
AUC_SCORE_THRESHOLD_VALUE :float = 0.95
MODEL_OBJS_FOLDER_NAME:str ="model_objs"
BEST_MODEL_OBJ_FOLDER_NAME:str ="bestmodel_obj"
PREPROCESSOR_FOLDER_STAGE_TWO_NAME:str = "preprocessor_stage_two"
STANDARD_SCALAR_OBJECT_NAME:str = 'standard_scalar.dill'
HANDLE_IMBALANCE_SMOTE_OBJECT_NAME : str = "handle_imbalance_smote.dill"
PCA_OBJECT_NAME: str = "pca.dill"
EXCEL_FILES_FOLDER_NAME : str = "excel_files"
JSON_FILES_FOLDER_NAME : str = "json_files"
ALL_MODELS_RESULTS_DATA_EXCEL_FILE_NAME: str = "all_models_result.xlsx"
BEST_MODEL_RESULT_DATA_EXCEL_FILE_NAME: str = "best_model_result.xlsx"
ALL_MODELS_RESULTS_DATA_JSON_FILE_NAME: str = "all_models_result.json"
BEST_MODEL_RESULT_DATA_JSON_FILE_NAME: str = "best_model_result.json"
EXCEL_AND_JSON_FILES_FOLDER_NAME: str = "excel_and_json_files"
BEST_MODEL_NAME: str = "model.pkl"

#s3 constants
BUCKET_NAME:str = 'wafersensorsdata'
S3_TRAINING_DATA_FOLDER_NAME: str = "training_data"
S3_RETRAINING_DATA_FOLDER_NAME: str = "retraining_data"
S3_CLIENT_DB_FOLDER_NAME: str = "client_db_data"
S3_PREDICTION_DATA_FOLDERNAME: str = "predicted_files"
DEFAULT_TRAINING_BATCH_FILES:str = "training_batch_files"
LOCAL_PREDICTION_MODELS_FOLDER_NAME: str = "prediction_models"

# model evolution constants
DAGSHUB_REPO_OWNER_NAME:str = 'Raveenkumar'
DAGSHUB_REPO_NAME:str = 'SENSOR-FAULT-DETECTION'
CONFUSION_MATRIX_FOLDER_NAME:str = "confusion_matrix_images"

# datadrift constants
DATA_DRIFT_FILE_NAME:str = 'data_drift.html'
DATA_DRIFT_THRESHOLD_VALUE:float = 0.30

# prediction constants
PREDICTION_DATA_FILE_NAME: str = "predictions.xlsx"
FINAL_PREDICTION_FILE_NAME: str = "final_prediction_file.csv"
FINAL_OUTPUT_COLUMN_NAME: str = 'Final_Output'
FEEDBACK_COLUMN_NAME:str = "Feedback"
CONFIDENCE_COLUMN_NAME:str = "Confidence"
TARGET_FEATURE_ZERO_MAP:str = 'Working'
TARGET_FEATURE_ONE_MAP:str = 'NotWorking'



#api_constants
APP_HOST:str = "0.0.0.0"
APP_PORT:int = 8080
