import sys
from urllib.parse import urlparse
import mlflow
from mlflow.exceptions import RestException
import mlflow.sklearn
from dotenv import load_dotenv
import os
import time
import os
from pandas import DataFrame
from requests.exceptions import ConnectionError, Timeout
import dagshub
from pathlib import Path
from src.entity.config_entity import ModelEvaluationConfig,DataDriftConfig
from src.utilities.utils import read_json
from src.exception import SensorFaultException
from src.logger import logger
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from evidently import ColumnMapping

load_dotenv()

# Set a higher timeout (120 seconds)
os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = "10000"

class  ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig,mlflow_data_dict: dict,cluster_dataset_path:str,cluster_data:DataFrame):
        self.config = config
        self.mlflow_data_dict = mlflow_data_dict
        self.cluster_dataset_path = cluster_dataset_path
        self.cluster_dataset = cluster_data
        # Retry logic for Dagshub initialization
        max_retries = 3
        retry_delay = 5  # Start with a 5-second delay
        for attempt in range(max_retries):
            try:
                self.connect_dagshub_repo = dagshub.init(                       # type: ignore
                    repo_owner=self.config.dagshub_repo_owner_name,
                    repo_name=self.config.dagshub_repo_name,
                    mlflow=True
                )  
                break  # Successfully connected
            except (ConnectionError, Timeout, OSError) as e:
                logger.error(f"Attempt {attempt + 1} to connect to Dagshub failed: {e}")
                if attempt < max_retries - 1:  # Only sleep if this isn't the last attempt
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error during Dagshub connection: {str(e)}")
                raise SensorFaultException(error_message=str(e), error_detail=sys)
        # self.connect_dagshub_repo = dagshub.init(repo_owner=self.config.dagshub_repo_owner_name, repo_name=self.config.dagshub_repo_name, mlflow=True) # type: ignore

    def log_into_mlflow(self):
        """log_into_mlflow :Used for store the models data into mlflow repo

        Raises:
            error_message: Custom Exception
        """
        try:
            logger.info(f"Log into Mlflow :: experiment_name:{self.config.mlflow_experiment_name} :: MLFLOW URI:{self.config.mlflow_uri}")
            mlflow.set_experiment(experiment_name=self.config.mlflow_experiment_name)
            mlflow.set_registry_uri(self.config.mlflow_uri)                                            # type: ignore
            dataset = mlflow.data.from_pandas(self.cluster_dataset, source=self.cluster_dataset_path)    # type: ignore
            
            for cluster_model_name, model_data in self.mlflow_data_dict.items():
                with mlflow.start_run(run_name=cluster_model_name):
                    mlflow.log_params(model_data['param'])
                    mlflow.log_metric("training_score",model_data['training_score'])
                    mlflow.log_metric("test_score",model_data['test_score'])
                    mlflow.log_metric("auc_score",model_data['auc_score'])
                    mlflow.log_metric("overall_recall_score",model_data['overall_recall_score'])
                    mlflow.log_metric("recall_1",model_data['recall_1'])
                    mlflow.log_metric("recall_0",model_data['recall_0'])
                    mlflow.log_metric("overall_precision",model_data['overall_precision'])
                    mlflow.log_metric("precision_1",model_data['precision_1'])
                    mlflow.log_metric("precision_0",model_data['precision_0'])
                    mlflow.log_input(dataset, context="training")
                    mlflow.set_tag("Dataset", self.cluster_dataset_path)
                    mlflow.log_artifact(self.cluster_dataset_path,artifact_path='dataset')
                    mlflow.log_artifact(model_data['confusion_matrix_image_path'], artifact_path='reports')
                    
                    if "xgbclassifier" in cluster_model_name:
                        mlflow.xgboost.log_model(model_data['model'], "model")
                    else:
                        mlflow.sklearn.log_model(model_data['model'], "model")
                    logger.info(f'log_into_mlflow :: Status: Data added into mlflow repo! :: model_name:{cluster_model_name}')      
                    
                    # remove the image for unnecessary duplications    
                    os.remove(model_data['confusion_matrix_image_path'])
        except RestException:
            self.log_into_mlflow()
                
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"log_into_mlflow :: Status:Failed :: Error:{error_message}")
            raise error_message                
        

class DataDrift:
    def __init__(self,config:DataDriftConfig):
        self.config = config
    
    def find_data_drift(self,original_data:DataFrame, reference_data:DataFrame):
        """find_data_drift _summary_

        Args:
            original_data (DataFrame): _description_
            reference_data (DataFrame): _description_
        """
        try:
            drift_schema = read_json(self.config.drift_schema_file_path)
            
            # Define column mapping
            column_mapping = ColumnMapping(target=drift_schema['target'],
                                           prediction=None,
                                           numerical_features=drift_schema['numerical_features'],
                                           categorical_features=None,
                                           datetime_features=None,      
                                           id=drift_schema['id'])
            
            # Create a report using DataDriftPreset
            report = Report(metrics=[DataDriftPreset()])

            # Generate the report with column mapping
            report.run(reference_data=original_data, current_data=reference_data, column_mapping=column_mapping)
            
            results = report.as_dict()
            logger.info(f'drift summary:{results['metrics'][0]['result']}')
            
            if results['metrics'][0]['result']['share_of_drifted_columns']>self.config.drift_threshold_value:
                drift_status=True
                # Save or display the report
                report.save_html(self.config.drift_report_path)
                logger.info(f'find_data_drift::: Data Drift Detected ,html file saved ::: path:{self.config.drift_report_path}')

            else:
                drift_status=False
                logger.info(f'find_data_drift::: Data Drift Not Detected')
            
            return drift_status    
                     
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"find_data_drift :: Status:Failed :: Error:{error_message}")
            raise error_message
            
            