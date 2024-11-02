import os
from pathlib import Path
import sys
import pandas as pd
from typing import Literal
import numpy as np
from pandas import DataFrame
from src.logger import logger
from src.exception import SensorFaultException
from src.utilities.utils import read_csv_file,create_folder_using_folder_path
from src.entity.artifact_entity import DataIngestionArtifacts
from src.entity.config_entity import S3Config, DataIngestionConfig
from mypy_boto3_s3.service_resource import Bucket
from src.db_management.aws_storage import SimpleStorageService

class DataIngestion:
    def __init__(self,input_dataset_path:Path) -> None:
        self.input_dataset_path = input_dataset_path
         
    def get_data(self) -> DataFrame:
        """get_data :Used for getting the data from input dataset path

        Raises:
            error_message: Custom Exception

        Returns:
            DataFrame: input dataframe
        """
        try:
            input_dataframe = read_csv_file(self.input_dataset_path)
            
            logger.info(f"Getting data :: Status:Successfully")
            
            return input_dataframe
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"Getting Data :: Status:Failed :: Error:{error_message}")
            raise error_message
        
        
    def initialize_data_ingestion_process(self) -> DataIngestionArtifacts:
        """initialize_data_ingestion_process :used for start the data ingestion process

        Raises:
            error_message: Custom Exception

        Returns:
            DataIngestionArtifact: provides input data from further process
        """
        try:
            logger.info("started the raw data ingestion process!")
            input_dataframe = self.get_data()
            data_ingestion_artifact = DataIngestionArtifacts(input_dataframe=input_dataframe)
            logger.info(f"started the raw data ingestion Ended!")
            return data_ingestion_artifact
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"initialize_data_ingestion_process :: Status:Failed :: Error:{error_message}")
            raise error_message
                
class GetTrainingData:
    def __init__(self,data_ingestion_config:DataIngestionConfig,s3_obj:SimpleStorageService,s3_config:S3Config,s3_bucket_obj:Bucket):
        self.config = data_ingestion_config
        self.s3_obj = s3_obj
        self.s3_config = s3_config
        self.s3_bucket_obj = s3_bucket_obj
    
    def get_file_path(self) -> tuple[str, Literal['retraining']] | tuple[str, Literal['training']] | tuple[str, Literal['default_training']]:
        """get_file_path :Used for getting the file_path for training based on retraining, training or training on default data

        Raises:
            error_message: Custom Exception

        Returns:
            tuple: file_path, status(retraining,training, default_training)
        """
        try:
            if not self.s3_obj.check_s3_folder_empty(bucket_object=self.s3_bucket_obj,s3_folder_path=self.s3_config.retraining_files_path):
                file_path = self.s3_config.retraining_files_path
                logger.info("Retraining Process started!")
                logger.info(f"get_file_path:: Status:Success :: file_path = {file_path}")
                status='retraining'
                return file_path,status
            elif not self.s3_obj.check_s3_folder_empty(bucket_object=self.s3_bucket_obj,s3_folder_path=self.s3_config.training_files_path):
                file_path = self.s3_config.training_files_path
                logger.info("training Process started on Existing Validated Data!")
                logger.info(f"get_file_path:: Status:Success :: file_path = {file_path}")
                status='training'
                return file_path,status
            else:
                file_path = self.s3_config.default_training_batch_files_path
                logger.info("training Process started on Default Data!")
                logger.info(f"get_file_path:: Status:Success :: file_path = {file_path}")
                status='default_training'
                return file_path,status 
                        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"get_file_path :: Status:Failed :: Error:{error_message}")
            raise error_message
                
            
    def files_store_in_local_path(self,s3_files_path:str) -> Path:
        """files_store_in_local_path :Used for store the cloud data into local training folder

        Args:
            s3_files_path (str): s3_files_path

        Raises:
            error_message: Custom Exception

        Returns:
            Path: Path
        """
        try:
            logger.info(f"files_store_in_local_path:: create folder for storing cloud training files into local")
            create_folder_using_folder_path(self.config.training_batch_files_folder_path)
            self.s3_obj.download_files_from_s3(bucket_obj=self.s3_bucket_obj,
                                               local_folder_path=self.config.training_batch_files_folder_path,
                                               s3_subfolder_path=s3_files_path)
            logger.info(f"files_store_in_local_path :: Status: Success")
            logger.info(f"Data stored in Local_path:{self.config.training_batch_files_folder_path} from Cloud_path:{s3_files_path}")
            
            return self.config.training_batch_files_folder_path
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"files_store_in_local_path :: Status:Failed :: Error:{error_message}")
            raise error_message
    
    def add_feedback_to_prediction_file(self,local_training_files_path: Path):
        """add_feedback_to_prediction_file :This method used for merge the prediction file and feedback file

        Args:
            local_training_files_path (Path): local training files path : artifacts/Training_batch_files

        Raises:
            error_message: _description_
        """
        try:
            prediction_file_paths = {}
            for file_name in os.listdir(local_training_files_path):
                if file_name!=self.config.final_file_name:
                    file_path = os.path.join(local_training_files_path,file_name)
                    if file_name.endswith("xlsx"):
                        prediction_file_paths['feedback_file_path'] = file_path
                    else:
                        prediction_file_paths['prediction_file_path'] = file_path    
            
            
            feedback_df = pd.read_excel(prediction_file_paths['feedback_file_path'])
            prediction_file_df = pd.read_csv(prediction_file_paths['prediction_file_path'])
                            
            # preprocess the feedback_df
            feedback_df[self.config.final_output_column_name] = np.where(pd.isna(feedback_df[self.config.feedback_column_name]),feedback_df[self.config.output_column_name],feedback_df[self.config.feedback_column_name])
            feedback_df[self.config.final_output_column_name] = feedback_df[self.config.final_output_column_name].map({self.config.target_feature_zero_map:0,
                                                                                                                       self.config.target_feature_one_map:1})
                  
            final_feedback_df = feedback_df[[self.config.wafer_column_name,self.config.final_output_column_name]]    
            
            # merge feedback into prediction data file
            merged_df = pd.merge(prediction_file_df,final_feedback_df,on=self.config.wafer_column_name,how='left')
            merged_df.drop(columns=[self.config.output_column_name],inplace=True)
            merged_df.rename(columns={self.config.final_output_column_name:self.config.output_column_name},inplace=True)
            
            final_file_prediction_path = os.path.join(local_training_files_path,self.config.final_file_name_prediction)
            merged_df.to_csv(final_file_prediction_path,index=False)
            
            # remove the preprocessed files
            os.remove(prediction_file_paths['feedback_file_path'])
            os.remove( prediction_file_paths['prediction_file_path'])
            
            logger.info(f'add_feedback_to_prediction_file :: prediction file and feedback file merged :: file_path:{final_file_prediction_path}')

        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"add_feedback_to_prediction_file :: Status:Failed :: Error:{error_message}")
            raise error_message
        
        
    
    def initialize_getting_training_data_process(self) -> tuple[Literal['retraining', 'training', 'default_training'], Path]:
        """initialize_getting_training_data_process :Used for initialize the getting training data process

        Raises:
            error_message: Custom Exception

        Returns:
            : status, path
        """
        try:
            logger.info("Start initialize_getting_training_data process!")
            s3_files_path, status = self.get_file_path()
            
            local_training_files_path = self.files_store_in_local_path(s3_files_path=s3_files_path)
            
            if status == 'retraining':
                self.add_feedback_to_prediction_file(local_training_files_path=local_training_files_path)
            
            logger.info("Ended initialize_getting_training_data process")
            
            return status, local_training_files_path
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"initialize_getting_training_data_process :: Status:Failed :: Error:{error_message}")
            raise error_message
    
    
        