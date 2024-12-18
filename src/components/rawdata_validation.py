import sys,os,re,shutil
from typing import Union,Literal
from src.entity.config_entity import TrainingRawDataValidationConfig, PredictionRawDataValidationConfig
from pathlib import Path
from src.utilities.utils import (read_json,read_csv_file,
                                 append_log_to_excel,
                                 create_folder_using_file_path,
                                 create_folder_using_folder_path,copy_file,
                                 create_zip_from_folder,
                                 save_json,
                                 remove_file,
                                 save_bad_file_names)
from src.logger import logger
from src.exception import SensorFaultException
import pandas as pd
from src.entity.artifact_entity import RawDataValidationArtifacts

class RawDataValidation:
    def __init__(self,config: Union[TrainingRawDataValidationConfig, PredictionRawDataValidationConfig], folder_path: Path):
        self.data_files_path = folder_path
        self.config = config
        self.schema_file = read_json(file_path=config.schema_file_path)
        self.good_raw_data_path = self.config.good_raw_data_folder_path
        self.bad_raw_data_path = self.config.bad_raw_data_folder_path
        self.regex_file_name_format = self.config.raw_file_name_regex_format
        self.validation_report_file_path = self.config.validation_report_file_path
        self.dashboard_validation_report_file_path = self.config.dashboard_validation_report_file_path
        
    def filename_validation(self,file_name:str) -> Literal['Passed'] | Literal['Failed']:
        """filename_validation: Used for validate the file name format

        Args:
            file_name (str): filename

        Raises:
            SensorFaultException: Raise Custom Exception

        Returns:
            Literal['Passed'] | Literal['Failed']: return Passed if match the filename format else returns Failed
        """
        
        try:
            
            # check file_name match to file format  
            if re.match(pattern=self.regex_file_name_format,string=file_name):
                status = "Passed"
                logger.info(msg=f"file name validation :: Status:{status} :: File:{file_name}")
                append_log_to_excel(filename=file_name,status=status,status_reason="FILE NAME VALIDATION",remark="FILE NAME VALIDATION COMPLETED",excel_filename=self.validation_report_file_path)
                
            else:
                status = "Failed"
                logger.info(msg=f"file name validation :: Status:{status} :: File:{file_name}")
                append_log_to_excel(filename=file_name,status=status,status_reason="FILE NAME VALIDATION",remark="FILE NAME VALIDATION FAILED",excel_filename=self.validation_report_file_path)
                    
            return status
        
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=str(e),error_detail=sys))
            raise SensorFaultException(error_message=str(e),error_detail=sys)
            
    def numberofcolumns_validation(self, file_name:str, dataframe:pd.DataFrame) -> Literal['Passed'] | Literal['Failed']:
        """numberofcolumns_validation : Used for validate the number of columns in file

        Args:
            file_name (str): file_name for log
            dataframe (DataFrame): dataframe for getting number of columns

        Returns:
            -> Literal['Passed'] | Literal['Failed']: return Passed if match the number of columns else returns Failed
        """
        try:
            
           # get number of columns in file
            number_of_column_in_file = dataframe.shape[1]
           
           # check number of columns equal or not
            columns_difference = number_of_column_in_file-self.schema_file.NumberofColumns
            if columns_difference==0: 
                status = "Passed"
                logger.info(msg=f"Number of columns validation :: Status:{status} :: File:{file_name}")
                append_log_to_excel(filename=file_name ,status=status, status_reason="NUMBER OF COLUMNS VALIDATION",remark="NUMBER OF COLUMNS VALIDATION COMPLETED",excel_filename=self.validation_report_file_path)
            else:
                status = "Failed"
                logger.info(f"Number of columns validation :: Status:{status} :: File:{file_name} :: columns_difference:{columns_difference}")
                append_log_to_excel(filename=file_name ,status=status, status_reason="NUMBER OF COLUMNS VALIDATION",remark=f"COLUMN_DIFF BETWEEN DSA FILE AND PREDICTION FILE:{columns_difference}",excel_filename=self.validation_report_file_path)
            
            return status
            
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=str(e),error_detail=sys))
            raise SensorFaultException(error_message=str(e),error_detail=sys)
        
    def columnsdata_validation(self, file_name: str, dataframe: pd.DataFrame) -> Literal['Passed'] | Literal['Failed']:
        """columnsdata_validation : Used for Columns data (column name, column type, column series wise) validation
        
        Args:
            file_name (str): file_name for log
            dataframe (DataFrame): dataframe for getting data of columns
        
        Raises:
            SensorFaultException: Custom Exception

        Returns:
            Literal['Passed'] | Literal['Failed']: return Passed if match the validation of column data completed else returns Failed
        """
        try:
            mismatch_columns_data = []
            
            # get columns 
            schema_file_columns_data = self.schema_file.ColName  # Keep as a dictionary
            raw_file_columns_data = dataframe.dtypes.to_dict()   # Keep as a dictionary
            schema_file_columns = list(schema_file_columns_data.keys())
            raw_file_columns = list(raw_file_columns_data.keys())

            for slno, column in enumerate(schema_file_columns):
                column_data = {}
                # check column name validation by order wise in DSA
                if column != raw_file_columns[slno]:
                    column_data["schema_file"] = f"Column_name:{column}"
                    column_data["raw_file"] = f"Column_name:{raw_file_columns[slno]}"
                    mismatch_columns_data.append(column_data)
                    continue
                    
                # check if schema file column datatype is equal to raw file columns datatype or not
                if schema_file_columns_data[column] != raw_file_columns_data[column]:
                    column_data["schema_file"] = f"Column_name:{column}, Column_dtype:{schema_file_columns_data[column]}"
                    column_data["raw_file"] = f"Column_name:{column}, Column_dtype:{raw_file_columns_data[column]}"
                    mismatch_columns_data.append(column_data)  
                    continue
            
            # check if there are any mismatched columns
            if len(mismatch_columns_data)==0: 
                status = "Passed"
                logger.info(msg=f"Columns data (column name, column type, column series wise) validation :: Status:{status} :: File:{file_name}")
                append_log_to_excel(
                    filename=file_name,
                    status=status,
                    status_reason="COLUMN DATA VALIDATION",
                    remark="COLUMN DATA VALIDATION COMPLETED",
                    excel_filename=self.validation_report_file_path
                )
            else:
                status = "Failed"
                logger.info(msg=f"Columns data (column name, column type, column series wise) validation :: Status:Failed :: File:{file_name} :: Mismatch column list:{mismatch_columns_data}")
                append_log_to_excel(
                    filename=file_name,
                    status=status,
                    status_reason="COLUMN DATA VALIDATION",
                    remark=f"COLUMN DATA VALIDATION FAILED, MISMATCH COLUMN LIST:{mismatch_columns_data}",
                    excel_filename=self.validation_report_file_path
                )
            return status

        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=str(e), error_detail=sys))
            raise SensorFaultException(error_message=str(e), error_detail=sys)

    
    def columndata_whole_missing_validation(self,file_name:str,dataframe: pd.DataFrame) -> Literal['Passed'] | Literal['Failed']:
        """columnsdata_validation : Used for whole data of column is missing or not 
        Args:
            file_name (str): file_name for log
            dataframe (DataFrame): dataframe for getting data of columns
        
        Raises:
            SensorFaultException: Custom Exception

        Returns:
            Literal['Passed'] | Literal['Failed']: return Passed if match the whole data of column is missing data completed else returns Failed
        """
        try:
            total_columns_data= dataframe.shape[0]
            mismatch_columns_data = []
            
            for column in dataframe.columns:
                column_data = {}
                # # check entire data of column is missing or not 
                if total_columns_data-int(dataframe[column].count())==total_columns_data:
                    column_data["Sensor_Name"]= column
                    column_data["Column_Data"]=[total_columns_data,int(dataframe[column].count())]
                    mismatch_columns_data.append(column_data)
                    
            if len(mismatch_columns_data)==0: 
                status = "Passed"
                logger.info(msg=f"COLUMNDATA_WHOLE_MISSING_VALIDATION :: Status:{status} :: File:{file_name}")
                append_log_to_excel(filename=file_name,status=status, status_reason="COLUMNDATA_WHOLE_MISSING_VALIDATION",remark="COLUMN DATA WHOLE MISSING VALIDATION COMPLETED",excel_filename=self.validation_report_file_path)
            else:
                status = "Failed"
                logger.info(msg=f"COLUMNDATA_WHOLE_MISSING_VALIDATION :: Status:Failed :: File:{file_name} :: Mismatch column list:{mismatch_columns_data}")
                append_log_to_excel(filename=file_name ,status=status, status_reason="COLUMNDATA_WHOLE_MISSING_VALIDATION",remark=f"COLUMN DATA WHOLE MISSING VALIDATION FAILED, MISMATCH COLUMN LIST:{mismatch_columns_data}",excel_filename=self.validation_report_file_path)
            return status
        
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=str(e),error_detail=sys))
            raise SensorFaultException(error_message=e,error_detail=sys)
                     
    def initialize_rawdata_validation_process(self) -> RawDataValidationArtifacts:
        """initialize_rawdata_validation_process :Used for start the raw validation process

        Raises:
            SensorFaultException: Custom Exception

        Returns:
            RawDataValidationArtifacts: provides good raw folder path, bad raw folder path ,validation_logs.xlsx file path
        """
        try:
            logger.info("started the raw data validation process!")
            # create folder for needed
            logger.info(f"create folders for storing good raw data,bad raw data,validation report if not exist")
            create_folder_using_folder_path(self.good_raw_data_path)
            create_folder_using_folder_path(self.bad_raw_data_path)
            create_folder_using_file_path(self.validation_report_file_path)
            
            # remove bad_raw_zip if exists to avoid getting previous data
            remove_file(self.config.dashboard_bad_raw_zip_file_path)
            
            
            for file in os.listdir(path=self.data_files_path):
                file_path = Path(os.path.join(self.data_files_path, file))
            
                
                #read raw_data
                raw_dataframe = read_csv_file(file_path=file_path)
                if self.filename_validation(file_name=file)=="Failed":
                    shutil.copy2(src=file_path, dst=self.bad_raw_data_path)
                    os.remove(file_path)
                    continue

                # Check number of columns validation
                if self.numberofcolumns_validation(file_name=file,dataframe=raw_dataframe)=="Failed":
                    shutil.copy2(src=file_path, dst=self.bad_raw_data_path)
                    os.remove(file_path)
                    continue
                
                # Check number of columns validation
                if self.columndata_whole_missing_validation(file_name=file,dataframe=raw_dataframe)=="Failed":
                    shutil.copy2(src=file_path, dst=self.bad_raw_data_path)
                    os.remove(file_path)
                    continue
                
                # Check columns name validation
                if self.columnsdata_validation(file_name=file,dataframe=raw_dataframe)=="Failed":
                    shutil.copy2(src=file_path, dst=self.bad_raw_data_path)
                    os.remove(file_path)
                    continue

                # If all validations pass, move to good_raw_folder
                shutil.copy2(src=file_path, dst=self.good_raw_data_path)
                os.remove(file_path)
            
            #for validation report show only default training
            test_data = {"Dashboard":"show_validation_report"}
            save_json(self.config.dashboard_validation_show,test_data)
            # copy validation report file to data folder 
            logger.info(f"initialize_rawdata_validation_process :: copy the validation file into data folder for report")
            create_folder_using_file_path(self.dashboard_validation_report_file_path)
            copy_file(self.validation_report_file_path,self.dashboard_validation_report_file_path)
            
            # zip the bad raw data only prediction
            
            if self.bad_raw_data_path == PredictionRawDataValidationConfig.bad_raw_data_folder_path:
                create_folder_using_file_path(self.config.dashboard_bad_raw_zip_file_path)
                logger.info(f"initialize_rawdata_validation_process :: zip the bad data files for providing")
                create_zip_from_folder(self.bad_raw_data_path,self.config.dashboard_bad_raw_zip_file_path)
                save_bad_file_names() # save the bad file names
                
            result = RawDataValidationArtifacts(good_raw_data_folder=self.good_raw_data_path,
                                                bad_raw_data_folder=self.bad_raw_data_path,
                                                validation_log_file_path=self.validation_report_file_path)
            logger.info(msg=f"started the raw data validation Ended!: Artifacts:{result}")
            return result
                
        except Exception as e:
            # logger.error(e)
            logger.error(msg=SensorFaultException(error_message=str(e),error_detail=sys))
            raise SensorFaultException(error_message=e,error_detail=sys)
             
               