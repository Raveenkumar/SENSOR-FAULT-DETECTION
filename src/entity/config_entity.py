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
class PreprocessorConfig:
    unwanted_columns_list = [NEW_WAFER_COLUMN_NAME]
    target_feature = NEW_OUTPUT_COLUMN_NAME
    lower_percentile = LOWER_PERCENTILE
    upper_percentile = UPPER_PERCENTILE
    iqr_multiplier = IQR_MULTIPLIER
    experiment_preprocessor_object_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_NAME,
                                                            PREPROCESSOR_OBJECT_NAME))
    stable_preprocessor_object_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        STABLE_FOLDER_NAME,
                                                        PREPROCESSOR_FOLDER_NAME,
                                                        PREPROCESSOR_OBJECT_NAME))

@dataclass
class ClusterConfig:
    cluster_column_name = CLUSTER_COLUMN_NAME
    experiment_cluster_object_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            CLUSTER_FOLDER_NAME,
                                                            CLUSTER_OBJECT_NAME))
    
    stable_cluster_object_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        STABLE_FOLDER_NAME,
                                                        CLUSTER_FOLDER_NAME,
                                                        CLUSTER_OBJECT_NAME))
    

@dataclass
class ModelTunerConfig:
    kfold_n_splits = KFOLD_N_SPLITS
    pca_n_components = PCA_N_COMPONENTS
    gaussiannb_param_grid = GAUSSIANNB_PARAM_GRID
    svc_param_grid = SVC_PARAM_GRID
    randomforest_param_grid = RANDOM_FOREST_PARAM_GRID 
    xgbclassifier_param_grid = XGB_CLASSIFIER_PARAM_GRID
    auc_score_threshold_value = AUC_SCORE_THRESHOLD_VALUE


@dataclass
class ModelTrainerConfig:
    experiment_all_model_objects_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            MODEL_OBJS_FOLDER_NAME))
    
    experiment_best_model_object_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            BEST_MODEL_OBJ_FOLDER_NAME))
    
    stable_all_model_objects_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        STABLE_FOLDER_NAME,
                                                        MODEL_OBJS_FOLDER_NAME))

    stable_best_model_object_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        STABLE_FOLDER_NAME,
                                                        BEST_MODEL_OBJ_FOLDER_NAME))
    
    excel_and_json_files_folder_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME))
    
    all_model_results_excel_file_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        EXCEL_FILES_FOLDER_NAME,
                                                        ALL_MODELS_RESULTS_DATA_EXCEL_FILE_NAME))
    
    best_model_results_excel_file_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                    MODEL_DATA_FOLDER_NAME,
                                                    EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                    EXCEL_FILES_FOLDER_NAME,
                                                    BEST_MODEL_RESULT_DATA_EXCEL_FILE_NAME))
    
    
    all_model_results_json_file_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        JSON_FILES_FOLDER_NAME,
                                                        ALL_MODELS_RESULTS_DATA_JSON_FILE_NAME))
    
   
    
    best_model_results_json_file_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        JSON_FILES_FOLDER_NAME,
                                                        BEST_MODEL_RESULT_DATA_JSON_FILE_NAME))
    
    experiment_standard_scalar_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
                                                            STANDARD_SCALAR_OBJECT_NAME))
                                           
    experiment_smote_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
                                                            HANDLE_IMBALANCE_SMOTE_OBJECT_NAME))
                    
    experiment_pca_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            EXPERIMENT_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
                                                            PCA_OBJECT_NAME))
    
    
    stable_standard_scalar_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            STABLE_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
                                                            STANDARD_SCALAR_OBJECT_NAME))
                                           
    stable_smote_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            STABLE_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
                                                            HANDLE_IMBALANCE_SMOTE_OBJECT_NAME))
                    
    stable_pca_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            STABLE_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
                                                            PCA_OBJECT_NAME))
    
    
    all_model_result_json_file_name = ALL_MODELS_RESULTS_DATA_JSON_FILE_NAME
    all_model_result_excel_file_name = ALL_MODELS_RESULTS_DATA_EXCEL_FILE_NAME
    best_model_json_file_name = BEST_MODEL_RESULT_DATA_JSON_FILE_NAME
    best_model_excel_file_name = BEST_MODEL_RESULT_DATA_EXCEL_FILE_NAME

@dataclass
class AppConfig:
    training_folder_path  = Path(r"C:\Users\RAVEEN\Downloads\testing_data\batch3")     