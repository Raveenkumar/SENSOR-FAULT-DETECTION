from dataclasses import dataclass,field
import os
from dotenv import load_dotenv
from datetime import datetime
from src.constants import *
from pathlib import Path
load_dotenv()


TIMESTAMP: str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")


@dataclass
class BaseArtifactConfig:
    timestamp: str = TIMESTAMP
    artifact_base_dir = ARTIFACT_FOLDER_NAME
    artifact_dir:Path = Path(artifact_base_dir) / timestamp
    data_dir = Path(DATA_FOLDER_NAME)
    mlflow_experiment_name = 'training_'+timestamp
    dashboard_dir = data_dir / DASHBOARD_DATA_FOLDER_NAME 
    

@dataclass
class DataIngestionConfig:
    training_batch_files_folder_path:Path = Path(os.path.join(BaseArtifactConfig.artifact_base_dir,DEFAULT_TRAINING_BATCH_FILES))    

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
    dashboard_validation_show = BaseArtifactConfig.data_dir / DASHBOARD_DATA_FOLDER_NAME / "dashboard_validation_show.json"
    dashboard_validation_report_file_path = BaseArtifactConfig.data_dir / DASHBOARD_DATA_FOLDER_NAME / TRAINING_VALIDATION_LOG_FILE
    dashboard_bad_raw_zip_file_path = BaseArtifactConfig.data_dir / PREDICTION_DATA_FOLDER_NAME / BAD_RAW_ZIP_FILE_NAME
    
@dataclass
class PredictionRawDataValidationConfig:
    purpose = "Prediction"
    raw_file_name_regex_format = REGEX_PATTERN
    prediction_batch_files_path = PREDICTION_BATCH_FILES_PATH
    prediction_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,PREDICTION_BATCH_DATA))
    good_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,GOOD_RAW_DATA_FOLDER_NAME))
    bad_raw_data_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,BAD_RAW_DATA_FOLDER_NAME))
    schema_file_path = Path('config') / 'prediction_schema.json'
    validation_report_file_path =  Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,EVALUATION_DATA_FOLDER_NAME,PREDICTION_VALIDATION_LOG_FILE))
    dashboard_validation_show = BaseArtifactConfig.data_dir / DASHBOARD_DATA_FOLDER_NAME / "dashboard_validation_show.json" # this file used only training added here because of avoid annotation error
    dashboard_validation_report_file_path = BaseArtifactConfig.data_dir / DASHBOARD_DATA_FOLDER_NAME / PREDICTION_VALIDATION_LOG_FILE
    dashboard_bad_raw_zip_file_path = BaseArtifactConfig.data_dir / PREDICTION_DATA_FOLDER_NAME / BAD_RAW_ZIP_FILE_NAME
    dashboard_bad_file_names_json_path =  BaseArtifactConfig.data_dir / DASHBOARD_DATA_FOLDER_NAME / BAD_FILE_NAMES_FILE_NAME
    
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
    non_duplicate_data_clear_df_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,FINAL_PREDICTION_FILE_FOLDER_NAME,NON_DUPLICATE_DF_NAME))
    preprocessor_object_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            PREPROCESSOR_FOLDER_NAME,
                                                            PREPROCESSOR_OBJECT_NAME))
    preprocessor_json_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        JSON_FILES_FOLDER_NAME,
                                                        PREPROCESSOR_JSON_FILE_NAME))
    dashboard_preprocessor_json_file_path = Path(os.path.join(BaseArtifactConfig.data_dir,
                                                              DASHBOARD_DATA_FOLDER_NAME,
                                                        PREPROCESSOR_JSON_FILE_NAME))
    # stable_preprocessor_object_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                     MODEL_DATA_FOLDER_NAME,
    #                                                     STABLE_FOLDER_NAME,
    #                                                     PREPROCESSOR_FOLDER_NAME,
    #                                                     PREPROCESSOR_OBJECT_NAME))

@dataclass
class ClusterConfig:
    cluster_column_name = CLUSTER_COLUMN_NAME
    cluster_object_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            CLUSTER_FOLDER_NAME,
                                                            CLUSTER_OBJECT_NAME))
    
    # stable_cluster_object_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                     MODEL_DATA_FOLDER_NAME,
    #                                                     STABLE_FOLDER_NAME,
    #                                                     CLUSTER_FOLDER_NAME,
    #                                                     CLUSTER_OBJECT_NAME))
    

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
    all_model_objects_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            MODEL_OBJS_FOLDER_NAME))
    
    best_model_object_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                            MODEL_DATA_FOLDER_NAME,
                                                            BEST_MODEL_OBJ_FOLDER_NAME))
    
    
    # stable_all_model_objects_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                     MODEL_DATA_FOLDER_NAME,
    #                                                     STABLE_FOLDER_NAME,
    #                                                     MODEL_OBJS_FOLDER_NAME))

    # stable_best_model_object_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                     MODEL_DATA_FOLDER_NAME,
    #                                                     STABLE_FOLDER_NAME,
    #                                                     BEST_MODEL_OBJ_FOLDER_NAME))
    
    excel_and_json_files_folder_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME))
    
    all_model_results_excel_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        EXCEL_FILES_FOLDER_NAME,
                                                        ALL_MODELS_RESULTS_DATA_EXCEL_FILE_NAME))
    
    best_model_results_excel_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                    MODEL_DATA_FOLDER_NAME,
                                                    EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                    EXCEL_FILES_FOLDER_NAME,
                                                    BEST_MODEL_RESULT_DATA_EXCEL_FILE_NAME))
    
    
    all_model_results_json_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        JSON_FILES_FOLDER_NAME,
                                                        ALL_MODELS_RESULTS_DATA_JSON_FILE_NAME))
    
   
    
    best_model_results_json_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,
                                                        MODEL_DATA_FOLDER_NAME,
                                                        EXCEL_AND_JSON_FILES_FOLDER_NAME,
                                                        JSON_FILES_FOLDER_NAME,
                                                        BEST_MODEL_RESULT_DATA_JSON_FILE_NAME))
    
    standard_scalar_obj_name = STANDARD_SCALAR_OBJECT_NAME
                                           
    smote_obj_name = HANDLE_IMBALANCE_SMOTE_OBJECT_NAME
           
    pca_obj_name = PCA_OBJECT_NAME
    
    final_best_model_results_json_file_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                                DASHBOARD_DATA_FOLDER_NAME,
                                                        BEST_MODEL_RESULT_DATA_JSON_FILE_NAME))
    
    final_all_model_results_json_file_path = Path(os.path.join(DATA_FOLDER_NAME,
                                                               DASHBOARD_DATA_FOLDER_NAME,
                                                        ALL_MODELS_RESULTS_DATA_JSON_FILE_NAME))
   
    # stable_standard_scalar_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                         MODEL_DATA_FOLDER_NAME,
    #                                                         STABLE_FOLDER_NAME,
    #                                                         PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
    #                                                         STANDARD_SCALAR_OBJECT_NAME))
                                           
    # stable_smote_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                         MODEL_DATA_FOLDER_NAME,
    #                                                         STABLE_FOLDER_NAME,
    #                                                         PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
    #                                                         HANDLE_IMBALANCE_SMOTE_OBJECT_NAME))
                    
    # stable_pca_path = Path(os.path.join(DATA_FOLDER_NAME,
    #                                                         MODEL_DATA_FOLDER_NAME,
    #                                                         STABLE_FOLDER_NAME,
    #                                                         PREPROCESSOR_FOLDER_STAGE_TWO_NAME,
    #                                                         PCA_OBJECT_NAME))
    
    
    all_model_result_json_file_name = ALL_MODELS_RESULTS_DATA_JSON_FILE_NAME
    all_model_result_excel_file_name = ALL_MODELS_RESULTS_DATA_EXCEL_FILE_NAME
    best_model_json_file_name = BEST_MODEL_RESULT_DATA_JSON_FILE_NAME
    best_model_excel_file_name = BEST_MODEL_RESULT_DATA_EXCEL_FILE_NAME
    best_model_name = BEST_MODEL_NAME



@dataclass
class S3Config:
    bucket_name = BUCKET_NAME
    default_training_batch_files_path:str = "/".join([S3_CLIENT_DB_FOLDER_NAME,DEFAULT_TRAINING_BATCH_FILES])+"/" 
    training_files_path:str = "/".join([ARTIFACT_FOLDER_NAME,S3_TRAINING_DATA_FOLDER_NAME])+"/"
    retraining_files_path:str = "/".join([ARTIFACT_FOLDER_NAME,S3_RETRAINING_DATA_FOLDER_NAME])+"/"
    champion_folder_path: str = "prediction_model_data/champion/"
    challenger_folder:str = "prediction_model_data/challenger/"
    models_source_path:str = "/".join([BaseArtifactConfig.artifact_base_dir,BaseArtifactConfig.timestamp,MODEL_DATA_FOLDER_NAME])+"/"
    prediction_data_path = Path(os.path.join(DATA_FOLDER_NAME, PREDICTION_DATA_FOLDER_NAME))
    local_prediction_models_path = Path(os.path.join(DATA_FOLDER_NAME, LOCAL_PREDICTION_MODELS_FOLDER_NAME))
    s3_prediction_model_path = champion_folder_path+"bestmodel_obj/"
    s3_prediction_cluster_path = champion_folder_path+"cluster/"
    s3_prediction_preprocessor_one_path = champion_folder_path+"preprocessor_stage_one/"
    s3_prediction_preprocessor_two_path = champion_folder_path+"preprocessor_stage_two/"

@dataclass
class ModelEvaluationConfig:
    mlflow_uri = os.getenv('mlflow_uri')
    mlflow_experiment_name:str = BaseArtifactConfig.mlflow_experiment_name
    dagshub_repo_owner_name = DAGSHUB_REPO_OWNER_NAME
    dagshub_repo_name = DAGSHUB_REPO_NAME    
    


@dataclass
class PredictionPipelineConfig:
    prediction_models_path = BaseArtifactConfig.data_dir / LOCAL_PREDICTION_MODELS_FOLDER_NAME
    best_models_path = prediction_models_path / "bestmodel_obj"
    preprocessor_stage_one_obj_path = prediction_models_path / PREPROCESSOR_OBJECT_NAME
    preprocessor_stage_one_data_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,FINAL_PREDICTION_FILE_FOLDER_NAME,NON_DUPLICATE_DF_NAME))
    cluster_obj_path = prediction_models_path / CLUSTER_OBJECT_NAME
    standard_scalar_obj_name = STANDARD_SCALAR_OBJECT_NAME
    pca_obj_name = PCA_OBJECT_NAME
    best_model_name = BEST_MODEL_NAME
    predictions_data_path = BaseArtifactConfig.data_dir / PREDICTION_DATA_FOLDER_NAME / PREDICTION_DATA_FILE_NAME
    prediction_with_rawdata_file_name = "prediction_data"+BaseArtifactConfig.timestamp+".csv"
    predicted_data_with_rawdata_file_path = Path(os.path.join(BaseArtifactConfig.artifact_dir,PREDICTION_DATA_FOLDER_NAME,FINAL_PREDICTION_FILE_FOLDER_NAME,prediction_with_rawdata_file_name))
    wafer_column_name = NEW_WAFER_COLUMN_NAME
    cluster_column_name = CLUSTER_COLUMN_NAME
    output_column_name = NEW_OUTPUT_COLUMN_NAME
    
@dataclass
class AppConfig:
    training_folder_path  = Path(r"C:\Users\RAVEEN\Downloads\testing_data\batch3")     