from pathlib import Path
import sys
from pandas import DataFrame
from src.logger import logger
from src.exception import SensorFaultException
from src.utilities.utils import read_csv_file
from src.entity.artifact_entity import DataIngestionArtifact


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
        
        
    def initialize_data_ingestion_process(self) -> DataIngestionArtifact:
        """initialize_data_ingestion_process :used for start the data ingestion process

        Raises:
            error_message: Custom Exception

        Returns:
            DataIngestionArtifact: provides input data from further process
        """
        try:
            logger.info("started the raw data ingestion process!")
            input_dataframe = self.get_data()
            data_ingestion_artifact = DataIngestionArtifact(input_dataframe=input_dataframe)
            logger.info(f"started the raw data ingestion Ended!")
            return data_ingestion_artifact
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"initialize_data_ingestion_process :: Status:Failed :: Error:{error_message}")
            raise error_message
                
        