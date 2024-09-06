import sys,os,re,shutil
from typing import Union,Literal
from src.entity.config_entity import (TrainingRawDataValidationConfig,
                                      TrainingRawDataTransformationConfig,
                                      PreprocessorConfig,
                                      ClusterConfig)
from pathlib import Path
from src.utilities.utils import read_json,read_csv_file 
from src.logger import logger
from src.exception import SensorFaultException
from src.components.rawdata_validation import RawDataValidation
from src.components.rawdata_transformation import RawDataTransformation
from src.components.data_ingestion import DataIngestion
from src.components.data_preprocessing import Preprocessor
from src.components.data_clustering import Clusters
import pandas as pd



class TrainingPipeline:
    def __init__(self,files_path):
        self.files_path :Path = files_path
        self.rawdata_validation_config = TrainingRawDataValidationConfig()
        self.rawdata_transformation_config = TrainingRawDataTransformationConfig()
        self.preprocessor_config = PreprocessorConfig()
        self.cluster_config = ClusterConfig()
       
    
    def initialize_pipeline(self):
        try:
            logger.info(msg="---------------Started Training Pipeline---------------")
            logger.info(msg=f"Folder Path:{self.files_path}")
            raw_data_validation = RawDataValidation(self.rawdata_validation_config,folder_path=self.files_path)
            raw_data_validation_artifacts = raw_data_validation.initialize_rawdata_validation_process()
            
            raw_data_transformation = RawDataTransformation(config=self.rawdata_transformation_config,
                                                            rawdata_validation_artifacts=raw_data_validation_artifacts)
            raw_data_transformation_artifacts = raw_data_transformation.initialize_data_transformation_process()
            
            data_ingestion = DataIngestion(input_dataset_path=raw_data_transformation_artifacts.final_file_path)
            data_ingestion_artifacts = data_ingestion.initialize_data_ingestion_process()
            
            input_file = data_ingestion_artifacts.input_dataframe
            data_preprocessing = Preprocessor(config=self.preprocessor_config,input_file=input_file)
            data_preprocessing_artifacts = data_preprocessing.initialize_preprocessing()
            
            input_file = data_preprocessing_artifacts.preprocessed_data
            clusters = Clusters(config=self.cluster_config,
                                input_file=input_file,
                                target_feature_name=self.preprocessor_config.target_feature)
            cluster_artifacts = clusters.initialize_clusters()
            cluster_artifacts.final_file.to_csv('cluster_data.csv',index=False)
            logger.info(msg="---------------Completed Training Pipeline---------------")
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=e,error_detail=sys))
            