import os,sys
from src.logger import logger
from src.exception import SensorFaultException
from src.configuration.aws_connection import S3Client
from mypy_boto3_s3.service_resource import Bucket
from src.utilities.utils import format_as_s3_path
from pathlib import Path

class SimpleStorageService:
    def __init__(self):
        s3_client = S3Client()
        self.s3_resource = s3_client.s3_resource
        self.s3_client = s3_client.s3_client
        
    def get_bucket(self,bucket_name:str)-> Bucket:
        """get_bucket :Used for getting the bucket 

        Args:
            bucket_name (str): Bucket name for getting the bucket

        Raises:
            error_message: Custom Exception

        Returns:
            Bucket: Bucket Object
        """
        try:
           bucket = self.s3_resource.Bucket(bucket_name)  # type: ignore
           logger.info(msg=f"get bucket :: Status:Successful :: Bucket Name:{bucket_name}")
           return bucket
       
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get bucket :: Status:Failed :: Bucket Name:{bucket_name}:: Error:{error_message}")
            raise error_message    
    
    def check_s3_subfolder_exists(self,bucket_obj:Bucket,folder_path:str) -> bool:
        """check_s3_subfolder_exists :Used for check sub folder path exist or not

        Args:
            bucket_obj (Bucket): Bucket object for checking sub folder
            folder_path (str): folder_path

        Raises:
            error_message: Custom Exception

        Returns:
            bool: True if subfolder exist else return False
        """
        try:
            objects = list(bucket_obj.objects.filter(Prefix=folder_path))
            if objects:
               status=True
               logger.info(msg=f"check s3 folder exist or not :: Status: Successful :: Bucket_Obj:{bucket_obj} :: folder_path:{folder_path} :: objects:{objects}")
            else:
                status=False
                logger.info(msg=f"check s3 folder exist or not :: Status: Failed :: Bucket_Obj:{bucket_obj} :: folder_path:{folder_path}")
                
            return status    
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"check_s3_folder_exists execution failed :: Error:{error_message}")
            raise error_message
    
    def create_s3_subfolder(self,bucket_obj:Bucket,folder_path:Path)  -> None:
        """create_s3_subfolder :Used for create sub folder in side s3 bucket
 
        Args:
            bucket_obj (Bucket): Bucket object for checking sub folder
            folder_path (str): folder_path

        Raises:
            error_message: Custom Exception

        """
        try:
            s3_folder_path = format_as_s3_path(path=folder_path)
            bucket_obj.put_object(Key=s3_folder_path)    
            logger.info(msg=f"create_s3_subfolder :: Status: Successful :: Bucket_Obj:{bucket_obj} :: folder_path:{folder_path}")   
  
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"create_s3_subfolder execution failed :: Error:{error_message}")
            raise error_message
    
    def upload_files_to_s3(self, bucket_obj:Bucket, local_folder_path:Path, s3_subfolder_path:str):
        """upload_files_to_s3 :Used for upload the files from the local folder into s3 subfolder
        
        Args:
            bucket_obj (Bucket): bucket object
            local_folder_path (Path): local folder path
            s3_subfolder_path (str): s3 bucket folder path
            
        Raises:
            error_message: Custom Exception
        """
        try:
            for filename in os.listdir(local_folder_path):
                # Construct the full local file path
                local_file_path = os.path.join(local_folder_path, filename)

                # Check if it's a file (not a folder)
                if os.path.isfile(local_file_path):
                    s3_key = os.path.join(s3_subfolder_path, filename).replace("\\", "/") 
                
                    # Upload the file to S3
                    self.upload_file_to_s3(bucket_obj=bucket_obj,local_file_path=local_file_path,s3_subfolder_path=s3_key)
                    
            logger.info(msg=f"upload_files_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_folder_path:{local_folder_path} :: s3_file_path:{s3_key} ")
                    
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"upload_files_to_s3 execution failed :: Error:{error_message}")
            raise error_message       
    
    def upload_file_to_s3(self, bucket_obj:Bucket, local_file_path:str, s3_subfolder_path:str):
        try:
            bucket_obj.upload_file(Filename=local_file_path,Key=s3_subfolder_path)
            logger.info(msg=f"upload_file_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_file_path:{local_file_path} :: s3_file_path:{s3_subfolder_path} ")

        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"upload_file_to_s3 execution failed :: Error:{error_message}")
            raise error_message    
    
    def list_files_in_s3_folder(self,bucket_obj:Bucket, s3_folder_path:str) -> list[str]: 
        try:
            files_obj = bucket_obj.objects.filter(Prefix=s3_folder_path)
            files_path = [file_path.key for file_path in files_obj]
            logger.info(msg=f"list_files_in_s3_folder :: Status: Successful :: Bucket_Obj:{bucket_obj} :: s3_file_path:{s3_folder_path} :: files_path:{files_path} ")

            return files_path
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"list_files_in_s3_folder execution failed :: Error:{error_message}")
            raise error_message
    
    def download_files_from_s3(self, bucket_obj:Bucket, local_folder_path:Path, s3_subfolder_path:str):
        try:
            files_path = self.list_files_in_s3_folder(bucket_obj=bucket_obj,s3_folder_path=s3_subfolder_path)
            
            for file_path in files_path:
                file_name= os.path.basename(file_path)
                local_file_path = os.path.join(local_folder_path,file_name)
                
                self.download_file_from_s3(bucket_obj=bucket_obj,local_file_path=local_file_path,s3_file_path=file_path)
                
            logger.info(msg=f"download_files_from_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: s3_folder_path:{s3_subfolder_path} :: local_folder_path:{local_folder_path} ")
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"download_files_from_s3 execution failed :: Error:{error_message}")
            raise error_message
    
    def download_file_from_s3(self, bucket_obj:Bucket, local_file_path:str, s3_file_path:str):
        try:
            bucket_obj.download_file(Key=s3_file_path,Filename=local_file_path)
            logger.info(msg=f"download_file_from_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: s3_file_path:{s3_file_path} :: local file path:{local_file_path} ")
                
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"download_file_from_s3 execution failed :: Error:{error_message}")
            raise error_message    