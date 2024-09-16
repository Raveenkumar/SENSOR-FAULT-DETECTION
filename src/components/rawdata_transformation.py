import os,sys
from pathlib import Path
from typing import Union
import pandas as pd
import numpy as np
from src.logger import logger
from src.exception import SensorFaultException
from src.entity.artifact_entity import RawDataValidationArtifacts,RawDataTransformationArtifacts
from src.entity.config_entity import TrainingRawDataTransformationConfig,PredictionRawDataTransformationConfig
from src.utilities.utils import read_csv_file,create_folder_using_file_path



class RawDataTransformation:
    def __init__(self,config:Union[TrainingRawDataTransformationConfig,PredictionRawDataTransformationConfig],rawdata_validation_artifacts:RawDataValidationArtifacts) -> None:
        self.config = config
        self.rawdata_validation_artifacts_= rawdata_validation_artifacts
        self.raw_data_folder = self.rawdata_validation_artifacts_.good_raw_data_folder
        self.merge_file_path = self.config.merge_file_path
    
    def convert_good_raw_into_single_file(self,input_folder:Path) -> pd.DataFrame:
        """convert_good_raw_into_single_file :Used for convert good raw files into single 

        Args:
            input_folder (str): input folder path

        Raises:
            SensorFaultException: Custom Exception

        Returns:
            pd.DataFrame: merge_df
        """
        try:
            csv_list = []
            
            
            # Iterate over all files in the input directory
            for filename in os.listdir(input_folder):
                if filename.endswith(".csv"): 
                    file_path = Path(os.path.join(input_folder, filename))
                    df = read_csv_file(file_path=file_path)
                    csv_list.append(df) 

            # Concatenate all dataframes in the list into a single dataframe
            merged_df = pd.concat(csv_list, ignore_index=True)

            # # Save the merged dataframe to a new CSV file
            # merged_df.to_csv(output_file, index=False)
            logger.info(msg=f" Convert good_raw_files into single file :: Status:Success")
            return merged_df
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"Convert good_raw_files into single file :: Status:Failed :: Error:{error_message}")
            raise error_message
    
    def reformat_target_variable(self,merge_df:pd.DataFrame) -> pd.DataFrame:
        """reformat_target_variable :Used for change the values in target variable [-1,1] to [1,0] for model conventions

        Args:
            merge_df (pd.DataFrame): dataframe

        Raises:
            error_message: Custom Exception

        Returns:
            pd.DataFrame: reformated target variable dataframe
        """
        try:
            if self.config.old_output_column_name in merge_df.columns.to_list():
                target_variable = self.config.old_output_column_name
                merge_df[target_variable] = merge_df[target_variable].map({1:1,-1:0})
                logger.info(msg=f"reformat_target_variable :: Status:Success :: Target_variable:{target_variable}  reformated data:[-1,1]->[0,1]")
            return merge_df
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"reformat_target_variable :: Status:Failed :: Error:{error_message}")
            raise error_message
                
    
    def rename_column_names(self,merge_df:pd.DataFrame,output_file:Path) -> None:
        """rename_column_names :Used for rename the column 

        Args:
            merge_df (pd.DataFrame): merged_df
            output_file (Path): outfile_path store into single file

        Raises:
            error_message: Custom Exception
        """
        try:
            
            merge_file_columns = list(merge_df.columns)
            # before rename the column confirm it  transformation also used in prediction <prediction file can't contain output column>
            if self.config.old_wafer_column_name in merge_file_columns:
                columns_data = {self.config.old_wafer_column_name:self.config.new_wafer_column_name}
                merge_df.rename(columns=columns_data,inplace=True)
                logger.info(msg=f"Rename_column_names :: Status:Success :: Columns data:{columns_data}")
            
            if self.config.old_output_column_name in merge_file_columns:
                columns_data = {self.config.old_output_column_name:self.config.new_output_column_name}
                merge_df.rename(columns=columns_data,inplace=True)
                logger.info(msg=f"Rename_column_names :: Status:Success :: Columns data:{columns_data}")    
                
            
            merge_df.to_csv(output_file, index=False)
            logger.info(f"good raw data merged to single file:: Status: Success :: File_path:{output_file}")
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"Rename_column_names :: Status:Failed :: Error:{error_message}")
            logger.info(f"good raw data merged to single file:: Status: Failed")
            raise error_message
    
        
    def initialize_data_transformation_process(self) -> RawDataTransformationArtifacts:
        """initialize_data_transformation_process:Used for start the raw data transformation process

        Raises:
            error_message: Custom Exception

        Returns:
            RawDataTransformationArtifacts: Contains db_input_file <all raw files into single file?
        """
        try:
            logger.info("started the raw data transformation process!")
            # create merge_folder
            logger.info('crate folder for store transformed input file ')
            create_folder_using_file_path(self.merge_file_path)
            
            merge_df = self.convert_good_raw_into_single_file(self.raw_data_folder)
            
            merge_df = self.reformat_target_variable(merge_df=merge_df)
            
            self.rename_column_names(merge_df=merge_df,output_file=self.merge_file_path)
            
            result = RawDataTransformationArtifacts(final_file_path=self.merge_file_path)
            logger.info(f"started the raw data transformation Ended!: Artifacts:{result}")
            
            return result
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"started the raw data transformation Ended!:: Error:{error_message}")
            raise error_message