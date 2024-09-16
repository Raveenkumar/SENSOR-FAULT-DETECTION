import os,sys
from src.logger import logger
from src.exception import SensorFaultException
from src.configuration.aws_connection import S3Client
from src.entity.config_entity import S3Config
from mypy_boto3_s3.service_resource import Bucket,S3ServiceResource 
from src.utilities.utils import format_as_s3_path,models_auc_threshold_satisfied
from pathlib import Path

class SimpleStorageService:
    def __init__(self,config:S3Config):
        self.config = config
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
           bucket = self.s3_resource.Bucket(bucket_name) 
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
            # Filtering objects with the specified prefix
            objects = list(bucket_obj.objects.filter(Prefix=folder_path))
            
            # Check if there are any objects with the prefix
            if objects:
                # Verify that the object has the same prefix as the folder, not just any key with the prefix
                for obj in objects:
                    if obj.key == folder_path or obj.key.startswith(folder_path.rstrip('/') + '/'):
                        logger.info(f"Folder '{folder_path}' exists in the bucket '{bucket_obj}'.")
                        return True

            logger.info(f"Folder '{folder_path}' does not exist in the bucket '{bucket_obj}'.")
            return False
            
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
            if not self.check_s3_subfolder_exists(bucket_obj,s3_folder_path):
                bucket_obj.put_object(Key=s3_folder_path)    
                logger.info(msg=f"create_s3_subfolder :: Status: Successful :: Bucket_Obj:{bucket_obj} :: folder_path:{folder_path}")
            else:
                logger.info(msg=f"create_s3_subfolder :: Status: Already Exists :: Bucket_Obj:{bucket_obj} :: folder_path:{folder_path}")   
  
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"create_s3_subfolder execution failed :: Error:{error_message}")
            raise error_message
        
    def upload_folder_to_s3(self,bucket_obj:Bucket, local_folder_path:Path):
        """upload_folder_to_s3 :Used for upload the folder data maintain same structure in cloud also

        Args:
            bucket_obj (Bucket): s3 bucket object
            local_folder_path (Path): local folder path

        Raises:
            error_message: Custom Exception
        """
        try:
            
            for root,_,files in os.walk(local_folder_path):
                for file in files:
                    local_file_path = os.path.join(root,file)
                    s3_path = local_file_path.replace("\\","/")
                    self.upload_file_to_s3(bucket_obj=bucket_obj,
                                           local_file_path=local_file_path,
                                           s3_subfolder_path=s3_path)
            logger.info(msg=f"upload_folder_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_folder_path:{local_folder_path}")
                    
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"upload_folder_to_s3 execution :: status:Failed :: Error:{error_message}")
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
            if os.path.isfile(local_folder_path):
                local_folder_path_ = os.path.dirname(local_folder_path)
            else:
                local_folder_path_ = local_folder_path    
                
            for filename in os.listdir(local_folder_path_):
                # Construct the full local file path
                local_file_path = os.path.join(local_folder_path_, filename)

                # Check if it's a file (not a folder)
                if os.path.isfile(local_file_path):
                    s3_key = os.path.join(s3_subfolder_path, filename).replace("\\", "/") 
                
                    # Upload the file to S3
                    self.upload_file_to_s3(bucket_obj=bucket_obj,local_file_path=local_file_path,s3_subfolder_path=s3_key)
                    
            logger.info(msg=f"upload_files_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_folder_path:{local_folder_path_} :: s3_file_path:{s3_key} ")
                    
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
            files_path = [file_path.key for file_path in files_obj if not file_path.key.endswith("/")]
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
                
            # logger.info(msg=f"download_files_from_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: s3_folder_path:{s3_subfolder_path} :: local_folder_path:{local_folder_path} ")
            
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
            logger.error(msg=f"download_file_from_s3 execution :: Status:failed :: Error:{error_message}")
            raise error_message    
    
    def check_s3_folder_empty(self,bucket_object:Bucket,s3_folder_path:str) -> bool:
        try:
            files_list = [file for file in bucket_object.objects.filter(Prefix=s3_folder_path) if file.key != s3_folder_path]
            if len(files_list)==0:
                logger.info(f"check_s3_folder_empty :: Status: Folder empty :: s3_folder_path:{s3_folder_path}")
                return True
            else:
                logger.info(f"check_s3_folder_empty :: Status: Folder not empty :: s3_folder_path:{s3_folder_path}")
                return False
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"check_s3_folder_empty execution :: Status:failed :: Error:{error_message}")
            raise error_message
    
    def store_prediction_models(self):
        try:
            bucket_obj = self.get_bucket(bucket_name=self.config.bucket_name)
            if self.check_s3_folder_empty(bucket_object=bucket_obj,s3_folder_path=self.config.champion_folder_path):
                target_folder_path = self.config.champion_folder_path   
            else:
                if models_auc_threshold_satisfied():
                    target_folder_path = self.config.champion_folder_path
                else:
                    target_folder_path = self.config.challenger_folder
            logger.info(f'Copy the models data from:{self.config.models_source_path} to:{target_folder_path}')        
            # check source path exist or not
            if self.check_s3_subfolder_exists(bucket_obj,self.config.models_source_path):
                for obj in bucket_obj.objects.filter(Prefix=self.config.models_source_path):
                    source_path = obj.key
                    destination_path = source_path.replace(self.config.models_source_path,target_folder_path,1)
                    self.s3_resource.Object(self.config.bucket_name, destination_path).copy_from(CopySource={'Bucket': self.config.bucket_name, 'Key': source_path})
                    logger.info(f"models_data copied from :{source_path}--->to:{destination_path}") 
                logger.info(f"store_prediction_models execution :: Status:Success :: source_path:{self.config.models_source_path} :: destination_path:{target_folder_path}" )    
            else:    
                logger.info(f"store_prediction_models execution :: Status:Failed :: source_path:{self.config.models_source_path} :: destination_path:{target_folder_path}" )
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"store_prediction_models execution :: Status:failed :: Error:{error_message}")
            raise error_message
    
    def store_prediction_models_(self,source_path):
        try:
            bucket_obj = self.get_bucket(bucket_name=self.config.bucket_name)
            if self.check_s3_folder_empty(bucket_object=bucket_obj,s3_folder_path=self.config.champion_folder_path):
                target_folder_path = self.config.champion_folder_path   
            else:
                if models_auc_threshold_satisfied():
                    target_folder_path = self.config.champion_folder_path
                else:
                    target_folder_path = self.config.challenger_folder
                    
            # check source path exist or not
            if self.check_s3_subfolder_exists(bucket_obj,source_path):
                for obj in bucket_obj.objects.filter(Prefix=source_path):
                    source_key = obj.key
                    print(f"source key:{source_key}")
                    destination_path = source_key.replace(source_path,target_folder_path,1)
                    print(f"destination path: {destination_path}")
                    self.s3_resource.Object(self.config.bucket_name, destination_path).copy_from(CopySource={'Bucket': self.config.bucket_name, 'Key': source_key})
                    logger.info(f"models_data copied from :{source_path}--->to:{destination_path}") 
                logger.info(f"store_prediction_models execution :: Status:Success :: source_path:{source_path} :: destination_path:{target_folder_path}" )    
    
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"store_prediction_models execution :: Status:failed :: Error:{error_message}")
            raise error_message
        