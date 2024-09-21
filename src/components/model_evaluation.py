import sys
from urllib.parse import urlparse
import mlflow
from mlflow.exceptions import RestException
import mlflow.sklearn
import numpy as np
from dotenv import load_dotenv
import os
import time
import requests
import os
from requests.exceptions import ConnectionError, Timeout
import dagshub
from pathlib import Path
from src.entity.config_entity import ModelEvaluationConfig
from src.exception import SensorFaultException
from src.logger import logger

load_dotenv()

# Set a higher timeout (120 seconds)
os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = "300"

class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig,mlflow_data_dict: dict):
        self.config = config
        self.mlflow_data_dict = mlflow_data_dict
        # Retry logic for Dagshub initialization
        max_retries = 3
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
                time.sleep(5)  # Wait before retrying
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
                    
                    if "xgbclassifier" in cluster_model_name:
                        mlflow.xgboost.log_model(model_data['model'], "model")
                    else:
                        mlflow.sklearn.log_model(model_data['model'], "model")
                    logger.info(f'log_into_mlflow :: Status: Data added into mlflow repo! :: model_name:{cluster_model_name}')      
                  
        except RestException:
            self.log_into_mlflow()
                
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"log_into_mlflow :: Status:Failed :: Error:{error_message}")
            raise error_message                