import sys,os,re,shutil
from typing import Union,Literal
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.entity.config_entity import (DataIngestionConfig,
                                      S3Config,
                                      TrainingRawDataValidationConfig,
                                      TrainingRawDataTransformationConfig,
                                      PreprocessorConfig,
                                      ClusterConfig,
                                      ModelTunerConfig,
                                      ModelTrainerConfig,
                                      S3Config,
                                      ModelEvaluationConfig )
from src.entity.artifact_entity import RawDataValidationArtifacts
from src.utilities.utils import read_json,read_csv_file,remove_file
from src.logger import logger
from src.exception import SensorFaultException
from src.components.rawdata_validation import RawDataValidation
from src.components.rawdata_transformation import RawDataTransformation
from src.components.data_ingestion import DataIngestion,GetTrainingData
from src.components.data_preprocessing import Preprocessor
from src.components.data_clustering import Clusters
from src.components.model_trainer import ModelTrainer
from src.db_management.aws_storage import SimpleStorageService




class TrainingPipeline:
    def __init__(self):
        self.s3_config = S3Config()
        self.s3 = SimpleStorageService(config=self.s3_config)
        self.s3_bucket_obj = self.s3.get_bucket(bucket_name=self.s3_config .bucket_name)
        self.data_ingestion_config = DataIngestionConfig()
        self.rawdata_validation_config = TrainingRawDataValidationConfig()
        self.rawdata_transformation_config = TrainingRawDataTransformationConfig()
        self.preprocessor_config = PreprocessorConfig()
        self.cluster_config = ClusterConfig()
        self.model_tuner_config = ModelTunerConfig()
        self.model_trainer_config = ModelTrainerConfig()
        # self.model_evolution_config  = ModelEvaluationConfig()
       
    
    def initialize_pipeline(self):
        try:
            self.timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            self.model_evolution_config = ModelEvaluationConfig(self.timestamp)
            logger.info(msg="---------------Started Training Pipeline---------------")
            
            get_training_data = GetTrainingData(data_ingestion_config=self.data_ingestion_config,
                                                                    s3_obj=self.s3,
                                                                    s3_config=self.s3_config,
                                                                    s3_bucket_obj=self.s3_bucket_obj)
            
            status,files_path = get_training_data.initialize_getting_training_data_process()
            logger.info(msg=f"Folder Path:{files_path}")
            
            # remove the data/training_validation_file if status is training <no need to validation>
            remove_file(self.rawdata_validation_config.dashboard_validation_show)
            
            if status=="default_training":
                raw_data_validation = RawDataValidation(self.rawdata_validation_config,folder_path=files_path)
                raw_data_validation_artifacts = raw_data_validation.initialize_rawdata_validation_process()
            else:
                raw_data_validation_artifacts = RawDataValidationArtifacts(good_raw_data_folder=files_path,
                                                                           bad_raw_data_folder=self.rawdata_validation_config.bad_raw_data_folder_path,
                                                                           validation_log_file_path=self.rawdata_validation_config.validation_report_file_path) 
            
            raw_data_transformation = RawDataTransformation(config=self.rawdata_transformation_config,
                                                            rawdata_validation_artifacts=raw_data_validation_artifacts)
            self.raw_data_transformation_artifacts = raw_data_transformation.initialize_data_transformation_process()
            
            data_ingestion = DataIngestion(input_dataset_path=self.raw_data_transformation_artifacts.final_file_path)
            data_ingestion_artifacts = data_ingestion.initialize_data_ingestion_process()
            
            input_file = data_ingestion_artifacts.input_dataframe
            data_preprocessing = Preprocessor(config=self.preprocessor_config,input_file=input_file)
            data_preprocessing_artifacts = data_preprocessing.initialize_preprocessing()
            
            input_file = data_preprocessing_artifacts.preprocessed_data
            clusters = Clusters(config=self.cluster_config,
                                input_file=input_file,
                                target_feature_name=self.preprocessor_config.target_feature)
            cluster_artifacts = clusters.initialize_clusters()
            
            input_file = cluster_artifacts.final_file
            # input_file = pd.read_csv(self.files_path)
            
            model_trainer = ModelTrainer(config=self.model_trainer_config,
                                         input_file=input_file,
                                         modeltunerconfig=self.model_tuner_config,
                                         model_evolution_config=self.model_evolution_config)
            
            model_trainer.initialize_model_trainer()
            logger.info(msg="---------------Completed Training Pipeline---------------")
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=e,error_detail=sys))
            