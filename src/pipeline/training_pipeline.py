import sys,os,re,shutil
from typing import Union,Literal
from src.entity.config_entity import TrainingRawDataValidationConfig
from pathlib import Path
from src.utilities.utils import read_json,read_csv_file 
from src.logger import logger
from src.exception import SensorFaultException
from src.components.rawdata_validation import RawDataValidation



class TrainingPipeline:
    def __init__(self,files_path):
        self.files_path :Path = files_path
        self.rawdata_validation_config = TrainingRawDataValidationConfig()
        self.raw_data_validation = RawDataValidation(self.rawdata_validation_config,folder_path=self.files_path)
        
    
    def initialize_pipeline(self):
        try:
            logger.info(msg="---------------Started Training Pipeline---------------")
            logger.info(msg=f"Folder Path:{self.files_path}")
            self.raw_data_validation.initialize_rawdata_validation_process()
        
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=e,error_detail=sys))
            