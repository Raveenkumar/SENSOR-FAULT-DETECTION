from box import ConfigBox
from pathlib import Path
import json
import os,sys
import pandas as pd
from src.logger import logger
from src.exception import SensorFaultException
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from datetime import datetime


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
        os.makedirs(folder_name)
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
            logger.info(f"read json data : file_path: {file_path} : Status: Successful")    
        return ConfigBox(json_data)    
    
    except Exception as e:
        error_message =  SensorFaultException(error_message=str(e),error_detail=sys)
        logger.error(f"read json data :: file_path:{file_path} :: Status:Failed :: Error:{error_message}")
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
