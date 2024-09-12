from box import ConfigBox
from pathlib import Path
import json
import zipfile
import shutil,dill
import os,sys
from typing import Any
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from datetime import datetime
from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV
from sklearn.base import BaseEstimator
from src.logger import logger
from mypy_boto3_s3.service_resource import Bucket,S3ServiceResource 
from src.exception import SensorFaultException
from src.entity.config_entity import BaseArtifactConfig,ModelTrainerConfig,ModelTunerConfig
from src.entity.artifact_entity import ModelTunerArtifacts


def create_folder_using_folder_path(folder_path:Path):
    """create_folder_using_folder_path :Used for create a folder using folder path

    Args:
        folder_path (Path): folder_path to create

    Raises:
        error_message: CustomException
    """
    try:
        os.makedirs(folder_path,exist_ok=True)
        logger.info(f"create folder using folder path :: Status:Successful :: folder_path:{folder_path}")
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"create folder using folder path :: Status:Failed :: folder_path:{folder_path} :: Error:{error_message}")
        raise error_message

def create_folder_using_file_path(file_path:Path):
    """create_folder_using_file_path :Used for create a folder using file path

    Args:
        file_path (Path): file path we  can get folder name

    Raises:
        error_message: CustomException
    """
    try:
        folder_name,_ = os.path.split(file_path)
        os.makedirs(folder_name,exist_ok=True)
        logger.info(f"create folder using file path :: Status:Successful :: folder_path:{file_path}")
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"create folder using file path :: Status:Failed :: folder_path:{file_path} :: Error:{error_message}")
        raise error_message

def read_json(file_path:Path) -> ConfigBox:
    """read_json: used for reading json file 

    Args:
        file_path (Path): file_path

    Returns:
        ConfigBox: Provide ConfigBox (contains json data)
    """
    try:
        #check file path exist or not
        if os.path.exists(file_path):
            with open(file_path,mode='r') as file:
                json_data = json.load(file)
            logger.info(f"read json data :: file_path:{file_path} :: Status:Successful")    
        return ConfigBox(json_data)    
    
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"read json data :: file_path:{file_path} :: Status:Failed :: Error:{error_message}")
        raise error_message  

def save_json(file_path:Path, file_obj:object):
    try:
        #check file path exist or not
        with open(file_path, 'w') as json_file:
            json.dump(file_obj, json_file, indent=4)
        logger.info(f"save dict data into json :: file_path:{file_path} :: Status:Successful")    
       
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f" save dict data into json :: file_path:{file_path} :: Status:Failed :: Error:{error_message}")
        raise error_message     

def read_csv_file(file_path:Path) -> pd.DataFrame:
    """read_csv_file :: Used for read the csv file using pandas

    Args:
        file_path (Path): File path of the file

    Raises:
        SensorFaultException: Custom Exception

    Returns:
        pd.DataFrame: dataframe
    """
    try:
        #check file path exist or not
        if os.path.exists(file_path):
            dataframe = pd.read_csv(file_path)
            logger.info(f"read csv file : file_path: {file_path} : Status: Successful")    
        return dataframe    
    
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"read csv data :: file_path:{file_path} :: Status:Failed :: Error:{error_message}")
        raise error_message

def style_excel(excel_filename):
    """style_excel : Used for style the append_log_to_excel method

    Args:
        excel_filename (_type_): Excel file name
    """
    
    # Load the workbook and select the active worksheet
    wb = load_workbook(excel_filename)
    ws = wb.active

    # Define border style
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Define header fill color and font style
    header_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')  # Yellow color
    header_font = Font(bold=True, color='000000')  # Black color for text

    # Apply styles to the header row
    for cell in ws[1]: # type: ignore
        cell.fill = header_fill
        cell.font = header_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Apply border to all data cells and adjust column widths
    for row in ws.iter_rows(min_row=2, min_col=1, max_col=ws.max_column, max_row=ws.max_row):# type: ignore
        for cell in row:
            cell.border = thin_border

    # Adjust column widths based on the maximum length of the data in each column
    for column in ws.columns:# type: ignore
        max_length = 0
        column_letter = column[0].column_letter  # Get the column letter (e.g., 'A', 'B')
        for cell in column:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = max_length + 2  # Add some padding
        ws.column_dimensions[column_letter].width = adjusted_width# type: ignore

    # Save the styled workbook
    wb.save(excel_filename)

def append_log_to_excel(filename:str, status:str, status_reason: str, remark:str, excel_filename:Path):
    """append_log_to_excel :Used for store logs of validating data

    Args:
        filename (str): validating file name
        status (str): validation status
        remark (str): any remark related to validation
        excel_filename (str, optional): validation store file name
    """
    # Get the current date for the DATE column
    current_date = datetime.now().strftime('%Y-%m-%d')
    try:
        # Load the existing data into a DataFrame if the file exists
        existing_df = pd.read_excel(excel_filename)
        
        # Define slno automatically based on the number of existing rows
        slno = len(existing_df) + 1
                
        # Create a DataFrame for the new log entry
        new_data = {
            'SLNO': [slno],
            'DATE': [current_date],
            'FILENAME': [filename],
            'STATUS': [status],
            'STATUS_REASON': [status_reason],
            'REMARK': [remark]
        }
        new_df = pd.DataFrame(new_data)
        
        # Concatenate the existing DataFrame with the new DataFrame
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Save the updated DataFrame to the Excel file
        with pd.ExcelWriter(excel_filename, engine='openpyxl', mode='w') as writer:
            updated_df.to_excel(writer, index=False)
        
        # Style the Excel file
        style_excel(excel_filename)
        # logger.info(f"File:log_file.xlsx Data added :: Status:Successful :: Data:{new_df.to_dict()}")
        logger.info("File:log_file.xlsx :: Status:Data added")
    except FileNotFoundError:
        # If the file does not exist, create a new Excel file with slno starting from 1
        new_data = {
            'SLNO': [1],
            'DATE': [current_date],
            'FILENAME': [filename],
            'STATUS': [status],
            'STATUS_REASON': [status_reason],
            'REMARK': [remark]
        }
        new_df = pd.DataFrame(new_data)
        new_df.to_excel(excel_filename, index=False, engine='openpyxl')
        
        # Style the Excel file
        style_excel(excel_filename)
        logger.info("File:log_file.xlsx  :: Status:created")
        # logger.info(f"File:log_file.xlsx Data added :: Status:Successful :: Data:{new_df.to_dict()}")
        logger.info("File:log_file.xlsx :: Status:Data added")

def format_as_s3_path(path:Path) -> str:
    """format_as_s3_path :Used for convert path to s3_path format

    Args:
        path (Path): it can be window path or other path format

    Raises:
        error_message: Custom Exception

    Returns:
        str: s3_path
    """
    try:
        # if path is file path
        if os.path.isfile(path):
            s3_path  = str(path)
            s3_path = s3_path.replace('\\','/')
        else:
            s3_path  = str(path)        
            s3_path = s3_path.replace('\\','/')+'/'
        logger.info(f'convert path:{path} to s3_path:{s3_path} successfully')
        return s3_path
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"format_as_s3_path convert path to s3_path :: file_path:{path} :: Status:Failed :: Error:{error_message}")
        raise error_message  
    
def delete_artifact_folder() -> None:
    """delete_artifact_folder :Used for drop the folder artifact after completed prediction or training process is completed

    Raises:
        error_message: Custom Exception
    """
    try:
        shutil.rmtree(BaseArtifactConfig.artifact_base_dir)
        logger.info("delete artifact folder:: Status: Successfully")
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"delete_artifact_folder  ::  Status:Failed :: Error:{error_message}")
        raise error_message

def save_obj(file_path:Path,obj: object):
    """save_obj Used: save the model to dill objects

    Args:
        file_path (Path): file path for save the object
        obj (object): model object

    Raises:
        SensorFaultException: Custom Exception
    """
    try:
        dir_name = os.path.dirname(file_path)
        os.makedirs(dir_name,exist_ok=True)
        with open(file_path,'wb') as file_obj:
            dill.dump(obj,file=file_obj) 
        logger.info(msg=f'object saved :: Status: Success :: path: {file_path}')    
        
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"save_obj  ::  Status:Failed :: Error:{error_message}")
        raise error_message
    
def load_obj(file_path:Path)-> object:
    """load_obj :Used for load dill object

    Args:
        file_path (Path): file path of object

    Raises:
        SensorFaultException: Custom Exception

    Returns:
        object: dill object
    """
    try:
        
        if os.path.exists(file_path):
            with open(file_path,mode='rb') as file_obj:
                result = dill.load(file=file_obj)
            logger.info(msg=f'object loaded :: Status: Success :: path: {file_path}') 
               
            return result     
        else:
            e = Exception(f'object file path not exist path: {file_path}')    
            logger.info(msg=e)
            raise e
    
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"load object   ::  Status:Failed :: Error:{error_message}")
        raise error_message    
     
def model_result(model:RandomizedSearchCV,X_train:pd.DataFrame,X_test:pd.DataFrame,y_train:pd.DataFrame,y_test:pd.DataFrame)-> tuple[BaseEstimator,dict[str, Any]]:
    """model_result :Used for store model result data in dict format

    Args:
        model (RandomizedSearchCV): RandomizedSearch CV object
        X_train (DataFrame): X train
        X_test (DataFrame): X_test
        y_train (DataFrame): y_train
        y_test (DataFrame): y_test

    Raises:
        error_message: Custom Exception

    Returns:
       tuple[RandomizedSearchCV,dict[str, Any]]: model,results
    """
    try: 
        y_pred = model.predict(X_test)  
        
        result_dict = {
            'best_param': model.best_params_,
            'training_score': model.score(X_train, y_train),
            'test_score': model.score(X_test, y_test), 
            'accuracy': accuracy_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'auc_score': roc_auc_score(y_test, y_pred)
        }
        
        logger.info(f"model_result: {result_dict}")
        
        return model.best_estimator_, result_dict
    
    except Exception as e:
        error_message = SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(msg=f"model_result :: Status:Failed :: Error:{error_message}")
        raise error_message

def save_model_result_excel(df:pd.DataFrame, excel_file_path) -> None:
    """save_model_result_excel :Used for store the model results in excel file 

    Args:
        model_result_data (dict): models results data
        excel_file_path (_type_): excel file path for store the excel

    Raises:
        error_message: Custom Exception
    """
    try:
        df.to_excel(excel_file_path, index=False, engine='openpyxl')
        # Style the Excel file
        style_excel(excel_file_path)
        logger.info("save_model_result_excel :: Status:created-result data added")

    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"save_model_result_excel :: Status:Failed :: Error:{error_message}")
            raise error_message

def save_models_data(all_model_objects_path:Path,
                best_model_object_path:Path,
                model_tuner_artifacts:ModelTunerArtifacts):
    """save_models_data :Used for save the model results & model objects

    Args:
        all_model_objects_path (Path): path of  files of store all models data
        best_model_object_path (Path): path of  files of store best model data
        model_tuner_artifacts (ModelTunerArtifacts): contains  all models results and best model results

    Raises:
        error_message: Custom Exception
    """
    try:
        create_folder_using_folder_path(all_model_objects_path)
        create_folder_using_folder_path(best_model_object_path)
                
        all_models_data = model_tuner_artifacts.all_models_data
        best_model_data = model_tuner_artifacts.best_model_data

        
        for model_name,model_obj in all_models_data[0].items():
            file_name = model_name+".dill"
            
            all_model_file_path = all_model_objects_path / file_name
            
            # final_file_path = find_final_path(experiment_file_path=exp_all_model_file_path,stable_file_path=stable_all_model_file_path)
            
            final_file_path = all_model_file_path
            
            #save model object
            save_obj(final_file_path,model_obj)
            
        final_path = os.path.dirname(final_file_path)
        json_file_path = Path(os.path.join(final_path,ModelTrainerConfig.all_model_result_json_file_name)) 
        save_json(json_file_path,all_models_data[1])   
            
        
        file_name = "best_model.dill"
        # exp_best_model_path = experiment_best_model_object_path / file_name
        # stable_best_file_path = stable_best_model_object_path / file_name
        
        best_model_obj_file_path = best_model_object_path / file_name
        # final_file_path = find_final_path(experiment_file_path=exp_best_model_path,stable_file_path=stable_best_file_path)
        
        final_file_path = best_model_obj_file_path
        
        #save model object
        best_model_obj = best_model_data[0]
        best_model_results = best_model_data[1]
        
        #save model object
        save_obj(final_file_path,best_model_obj)
        final_path = os.path.dirname(final_file_path)
        json_file_path = Path(os.path.join(final_path,ModelTrainerConfig.best_model_json_file_name)) 
        save_json(json_file_path,best_model_results)   
 
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"save_model_result_excel :: Status:Failed :: Error:{error_message}")
            raise error_message 

def find_final_path(experiment_file_path:Path,stable_file_path:Path) -> Path:
    """find_final_path :Used find the folder path weather we store in experiments or stable's data

    Args:
        experiment_file_path (Path): Folder path
        stable_file_path (Path): Folder path

    Raises:
        error_message: Custom Exception

    Returns:
        Path: Final path
    """
    try:
        if not os.path.exists(stable_file_path):
            return stable_file_path 
        else:    
            return experiment_file_path
                    
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"save_object_to_experiment_and_stable :: Status:Failed :: Error:{error_message}")
            raise error_message
                                             
def proper_conversion_for_excel_file(result_dict:dict) -> pd.DataFrame:
    """proper_conversion_for_excel_file :Used for change data into proper for format for excel file

    Args:
        result_dict (dict): result dict

    Raises:
        error_message: Custom Exception

    Returns:
        pd.DataFrame: proper data in dataframe format
    """
    try:
            data = []
            for cluster_name, models in result_dict.items():
                for model_name, metrics in models.items():
                    # Add cluster name, model name, and metrics to the list
                    data.append({
                        'cluster': cluster_name,
                        'model_name': model_name,
                        **metrics  # Unpack the metrics dictionary into separate columns
                    })

            # Convert the collected data into a DataFrame
            df = pd.DataFrame(data) 
            logger.info(msg=f"proper_conversion_for_excel_file :: Status:Success :: result_dict: {result_dict}")
            
            return df
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"proper_conversion_for_excel_file :: Status:Failed :: Error:{error_message}")
            raise error_message                              
              
def get_dir_path_from_file_path(file_path:Path) -> Path:
    """get_dir_path_from_file_path Used getting the dir path from the file path

    Args:
        file_path (Path): file_path

    Raises:
        error_message: Custom Exception

    Returns:
        Path: dir path
    """
    try:
        dir_path = os.path.dirname(file_path)    
        logger.info(msg=f"get_dir_path_from_file_path :: Status:Success :: file_path:{file_path} :: folder_path:{dir_path} ")
        return Path(dir_path)
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_dir_path_from_file_path :: Status:Failed :: file_path:{file_path} :: Error:{error_message}")
            raise error_message                              
                
def copy_file(src_file_path:Path,dst_folder_path:Path):
    """copy_file :Used for copy file from source file path to destination folder path

    Args:
        src_file_path (Path): Path of source file path
        dst_folder_path (Path): destination folder path

    Raises:
        error_message: Custom Exception
    """
    try:
        shutil.copy2(src=src_file_path,dst=dst_folder_path)
        logger.info(msg=f"copy_file :: Status:Success :: src_file_path:{src_file_path} :: dst_folder_path:{dst_folder_path} ")
        
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_dir_path_from_file_path :: Status:Failed :: Error:{error_message}")
            raise error_message    

def create_zip_from_folder(folder_path:Path, output_zip_path:Path):
    """create_zip_from_folder :Used for create zip for folder data

    Args:
        folder_path (Path): folder path
        output_zip_path (Path): zip file path

    Raises:
        error_message: Custom Exception
    """
    try:
        # Create a zip file at the specified output path
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the folder, including all subdirectories and files
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to the zip, preserving the folder structure
                    arcname = os.path.relpath(file_path, folder_path)  # Relative path inside the zip
                    zipf.write(file_path, arcname)
                    logger.info(f'Added {file_path} as {arcname}')                    
        logger.info(f"create_zip_from_folder :: Status:Success :: folder_path__path:{folder_path} :: output_zip_path:{output_zip_path}")
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"create_zip_from_folder :: Status:Failed :: folder_path__path:{folder_path} :: output_zip_path:{output_zip_path} :: Error:{error_message}")
            raise error_message
                                
def models_auc_threshold_satisfied() -> bool:
    """ models_auc_threshold_satisfied:Used for check all three models auc score are satisfied the auc threshold value or not 

    Raises:
        error_message: Custom Exception

    Returns:
        bool: return True if satisfied else return False
    """
    try:
        i=0
        best_mode_results = read_json(ModelTrainerConfig.final_best_model_results_json_file_path)
        for cluster_name, model_data in best_mode_results.items():
            for model_name, model_results in model_data.items():
                if model_results['auc_score'] >= ModelTunerConfig.auc_score_threshold_value:
                    logger.info(f"{cluster_name}:{model_name}:{model_results['auc_score']}:: Status:Satisfied")
                    i+=1
                else:
                    logger.info(f"{cluster_name}:{model_name}:{model_results['auc_score']}:: Status:Not Satisfied")
        if i==3:
            return True
        else:
            return False                
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"models_auc_threshold_satisfied :: Status:Failed :: error_message:{error_message}")
            raise error_message     

def clear_artifact_folder():
    try:
        shutil.rmtree(Path(BaseArtifactConfig.artifact_dir))
        logger.info(f"clear_artifact_folder :: Status:Success")
        
    except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"clear_artifact_folder :: Status:Failed :: error_message:{error_message}")
            raise error_message             