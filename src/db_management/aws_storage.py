import json
import shutil
import os,sys
from src.logger import logger
from src.exception import SensorFaultException
from src.configuration.aws_connection import S3Client
from src.entity.config_entity import S3Config
from mypy_boto3_s3.service_resource import Bucket 
from src.utilities.utils import format_as_s3_path,models_auc_threshold_satisfied,create_folder_using_file_path,remove_file
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
        
    def upload_folder_to_s3(self,bucket_obj:Bucket, local_folder_path:Path, s3_folder_path:str):
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
                    logger.info(self.config.local_artifact_dir)
                    logger.info(s3_folder_path)
                    s3_path = local_file_path.replace(self.config.local_artifact_dir,s3_folder_path)
                    s3_path = s3_path.replace("\\","/")
                    self.upload_file_to_s3(bucket_obj=bucket_obj,
                                           local_file_path=local_file_path,
                                           s3_filepath_path=s3_path)
            logger.info(msg=f"upload_folder_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_folder_path:{local_folder_path} :: s3_folder_path:{s3_folder_path}")
                    
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
                    s3_key = os.path.join(s3_subfolder_path, filename).replace("\\", "/")  # 
                
                    # Upload the file to S3
                    self.upload_file_to_s3(bucket_obj=bucket_obj,local_file_path=local_file_path,s3_filepath_path=s3_key)
                    
            logger.info(msg=f"upload_files_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_folder_path:{local_folder_path_} :: s3_file_path:{s3_key} ")
                    
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"upload_files_to_s3 execution failed :: Error:{error_message}")
            raise error_message       
    
    def upload_file_to_s3(self, bucket_obj:Bucket, local_file_path:str, s3_filepath_path:str) -> None:
        """upload_file_to_s3 :Used for upload the file from the local folder into s3 subfolder
        
        Args:
            bucket_obj (Bucket): bucket object
            local_file_path (Path): local file path
            s3_file_path (str): s3 bucket file path
            
        Raises:
            error_message: Custom Exception
        """
        try:
            bucket_obj.upload_file(Filename=local_file_path,Key=s3_filepath_path)
            logger.info(msg=f"upload_file_to_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: local_file_path:{local_file_path} :: s3_file_path:{s3_filepath_path} ")

        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"upload_file_to_s3 execution failed :: Error:{error_message}")
            raise error_message    
    
    def list_files_in_s3_folder(self,bucket_obj:Bucket, s3_folder_path:str) -> list[str]: 
        """
        list_files_in_s3_folder: Lists all files in a specified S3 folder.

        Args:
            bucket_obj (Bucket): The S3 bucket object.
            s3_folder_path (str): The S3 folder path.

        Returns:
            list[str]: A list of file paths within the specified S3 folder.

        Raises:
            SensorFaultException: Custom exception if listing files fails.
        """
        try:
            files_obj = bucket_obj.objects.filter(Prefix=s3_folder_path)
            files_path = [file_path.key for file_path in files_obj if not file_path.key.endswith("/")]
            logger.info(msg=f"list_files_in_s3_folder :: Status: Successful :: Bucket_Obj:{bucket_obj} :: s3_file_path:{s3_folder_path} :: files_path:{files_path} ")

            return files_path
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"list_files_in_s3_folder execution failed :: Error:{error_message}")
            raise error_message
    
    def download_files_from_s3(self, bucket_obj:Bucket, local_folder_path:Path, s3_subfolder_path:str) -> None:
        """
        download_files_from_s3: Downloads all files from a specified S3 subfolder to a local folder.

        Args:
            bucket_obj (Bucket): The S3 bucket object containing the files.
            local_folder_path (Path): The local directory where files will be downloaded.
            s3_subfolder_path (str): The S3 subfolder path containing the files to download.

        Raises:
            SensorFaultException: Custom exception if the download process fails.
        """
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
    
    def download_file_from_s3(self, bucket_obj:Bucket, local_file_path:str, s3_file_path:str) -> None:
        """
        download_file_from_s3: Downloads a single file from S3 to a local path.

        Args:
            bucket_obj (Bucket): The S3 bucket object from which the file will be downloaded.
            local_file_path (str): The local file path where the downloaded file will be saved.
            s3_file_path (str): The S3 path of the file to be downloaded.

        Raises:
            SensorFaultException: Custom exception if the download process fails.
        """
        try:
            bucket_obj.download_file(Key=s3_file_path,Filename=local_file_path)
            logger.info(msg=f"download_file_from_s3 :: Status: Successful :: Bucket_Obj:{bucket_obj} :: s3_file_path:{s3_file_path} :: local file path:{local_file_path} ")
                
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"download_file_from_s3 execution :: Status:failed :: Error:{error_message}")
            raise error_message    
    
    def check_s3_folder_empty(self,bucket_object:Bucket,s3_folder_path:str) -> bool:
        """
        check_s3_folder_empty: Checks if a specified S3 folder is empty.

        Args:
            bucket_object (Bucket): The S3 bucket object to check.
            s3_folder_path (str): The S3 folder path to check for emptiness.

        Returns:
            bool: True if the folder is empty, False otherwise.

        Raises:
            SensorFaultException: Custom exception if the folder check process fails.
        """
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
    
    def store_prediction_models(self,local_models_source_path) -> None:
        """
        store_prediction_models: Stores prediction models from a local source path to an S3 bucket.

        Args:
            local_models_source_path (str): The local path where prediction models are stored.

        Raises:
            SensorFaultException: Custom exception if the model storage process fails.
        """
        try:
            bucket_obj = self.get_bucket(bucket_name=self.config.bucket_name)
            if self.check_s3_folder_empty(bucket_object=bucket_obj,s3_folder_path=self.config.champion_folder_path):
                target_folder_path = self.config.champion_folder_path   
            else:
                if models_auc_threshold_satisfied():
                    target_folder_path = self.config.champion_folder_path
                else:
                    target_folder_path = self.config.challenger_folder
            logger.info(f'Copy the models data from:{local_models_source_path} to:{target_folder_path}')        
            # check source path exist or not
            if self.check_s3_subfolder_exists(bucket_obj,local_models_source_path):
                for obj in bucket_obj.objects.filter(Prefix=local_models_source_path):
                    source_path = obj.key
                    destination_path = source_path.replace(local_models_source_path,target_folder_path,1)
                    self.s3_resource.Object(self.config.bucket_name, destination_path).copy_from(CopySource={'Bucket': self.config.bucket_name, 'Key': source_path})
                    logger.info(f"models_data copied from :{source_path}--->to:{destination_path}") 
                logger.info(f"store_prediction_models execution :: Status:Success :: source_path:{local_models_source_path} :: destination_path:{target_folder_path}" )    
            else:    
                logger.info(f"store_prediction_models execution :: Status:Failed :: source_path:{local_models_source_path} :: destination_path:{target_folder_path}" )
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"store_prediction_models execution :: Status:failed :: Error:{error_message}")
            raise error_message
    
    
    def get_s3_folder_state(self,bucket_obj:Bucket, prefix: str) -> dict:
        """Generate a dictionary of S3 file paths and their MD5 (ETag) hashes for a given S3 folder.

        Args:
            bucket: The S3 bucket object.
            prefix (str): The S3 folder path to scan.

        Returns:
            dict: A dictionary with S3 file keys as paths and ETag hashes.
        """
        try:
            folder_state = {}
            for obj in bucket_obj.objects.filter(Prefix=prefix):
                if not obj.key.endswith('/'):  # Skip folders, only get files
                    # Use the S3 object's ETag as an MD5-like hash
                    folder_state[obj.key] = obj.e_tag.strip('"')
            logger.info(f"get_s3_folder_state :: Status:Success :: folder_state:{folder_state}")        
            return folder_state
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_s3_folder_state  :: Status:failed :: Error:{error_message}")
            raise error_message
    
    def detect_s3_folder_changes(self,bucket_obj:Bucket, prefix: str, state_file: Path) -> bool:
        """Detect changes in the S3 folder content based on a stored state file.

        Args:
            bucket_obj: The S3 bucket object.
            prefix (str): The S3 folder path to monitor.
            state_file (Path): The path to the JSON file storing the previous state.

        Returns:
            bool: True if there are changes, False otherwise.
        """
        try:
            # Calculate current state
            current_state = self.get_s3_folder_state(bucket_obj, prefix)
            
            # Load previous state if exists
            if state_file.exists():
                with open(state_file, "r") as f:
                    previous_state = json.load(f)
            else:
                previous_state = {}

            # Check for any changes in the folder state
            if current_state != previous_state:
                # Save the current state as the new baseline
                with open(state_file, "w") as f:
                    json.dump(current_state, f, indent=4)
                logger.info(f"detect_s3_folder_changes  :: Status:Change in s3 models data folder")    
                return True  # Changes detected
            logger.info(f"detect_s3_folder_changes  :: Status: No change in s3 models data folder") 
            return False  # No changes detected
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"detect_s3_folder_changes  :: Status:failed :: Error:{error_message}")
            raise error_message
    
    def get_prediction_models(self,bucket_object:Bucket) -> None:
        """
        get_prediction_models: Downloads the prediction models from S3 if the local MD5 hash does not match the S3 ETag.

        Args:
            bucket_object (Bucket): The S3 bucket object used to access S3 resources.

        Raises:
            SensorFaultException: Custom exception if there is an error during the model download process.
        
        Notes:
            - The function compares the MD5 hash of a local file against the ETag of the S3 object.
            - If the hashes do not match, it downloads the model files (with .pkl or .dill extensions) from the specified S3 paths.
            - The function handles downloading for model objects, cluster objects, and preprocessor objects.
        """
        try: 
            if self.detect_s3_folder_changes(bucket_obj=bucket_object,prefix=self.config.s3_prediction_model_path,state_file=self.config.etag_data_json_file_path):
                model_objects = bucket_object.objects.filter(Prefix=self.config.s3_prediction_model_path)
                cluster_object = bucket_object.objects.filter(Prefix=self.config.s3_prediction_cluster_path)
                preprocessing_stage_one_object = bucket_object.objects.filter(Prefix=self.config.s3_prediction_preprocessor_one_path)
                preprocessing_stage_two_objects = bucket_object.objects.filter(Prefix=self.config.s3_prediction_preprocessor_two_path)
                
                
                s3_best_model_path = self.config.champion_folder_path.removesuffix('/')
                s3_cluster_path = self.config.s3_prediction_cluster_path.removesuffix('/')
                s3_preprocessor_stage_one_path= self.config.s3_prediction_preprocessor_one_path.removesuffix('/')
                s3_preprocessor_stage_two_path= self.config.s3_prediction_preprocessor_two_path.removesuffix('/')
                
                # drop old models
                shutil.rmtree(self.config.local_prediction_models_path)
                logger.info(f'Remove old models from local directory: {self.config.local_prediction_models_path}')
                
                # download model objects
                for obj in model_objects:
                    if obj.key.endswith(".pkl") or obj.key.endswith(".dill") or obj.key.endswith(".xgb"):
                        s3_key = obj.key
                        local_file_path = s3_key.replace(s3_best_model_path,str(self.config.local_prediction_models_path),1)
                        create_folder_using_file_path(Path(local_file_path))
                        self.download_file_from_s3(bucket_obj=bucket_object,local_file_path=local_file_path,s3_file_path=s3_key) 
                
                for obj in cluster_object:
                    if obj.key.endswith(".pkl") or obj.key.endswith(".dill"):
                        s3_key = obj.key
                        local_file_path = s3_key.replace(s3_cluster_path,str(self.config.local_prediction_models_path),1)
                        create_folder_using_file_path(Path(local_file_path))
                        self.download_file_from_s3(bucket_obj=bucket_object,local_file_path=local_file_path,s3_file_path=s3_key)    
                
                for obj in preprocessing_stage_one_object:
                    if obj.key.endswith(".pkl") or obj.key.endswith(".dill"):
                        s3_key = obj.key
                        local_file_path = s3_key.replace(s3_preprocessor_stage_one_path,str(self.config.local_prediction_models_path),1)
                        create_folder_using_file_path(Path(local_file_path))
                        self.download_file_from_s3(bucket_obj=bucket_object,local_file_path=local_file_path,s3_file_path=s3_key) 
                        
                for obj in preprocessing_stage_two_objects:
                    if obj.key.endswith(".pkl") or obj.key.endswith(".dill") :
                        if not obj.key.endswith("handle_imbalance_smote.dill"):
                            s3_key = obj.key
                            local_file_path = s3_key.replace(s3_preprocessor_stage_two_path,str(self.config.local_prediction_models_path),1)
                            create_folder_using_file_path(Path(local_file_path))
                            self.download_file_from_s3(bucket_obj=bucket_object,local_file_path=local_file_path,s3_file_path=s3_key)         
                            
                logger.info("get_prediction_models :: Status:Downloaded the new prediction models")
            
            else:
                logger.info("get_prediction_models :: Status: Local models are updated models can't download again!")    
                             
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_prediction_models execution :: Status:failed :: Error:{error_message}")
            raise error_message
        
    def clear_bucket(self,bucket_object:Bucket):
        """
        clear_bucket: Deletes all versions of objects in the specified S3 bucket.

        Args:
            bucket_object (Bucket): The S3 bucket object from which to delete all object versions.

        Raises:
            SensorFaultException: Custom exception if there is an error during the bucket clearing process.

        Notes:
            - This method deletes all object versions in the specified bucket, effectively clearing the bucket.
            - It handles any exceptions that occur during the deletion process and logs an error message.
        """
        try:
            bucket_object.object_versions.delete()
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"clear_bucket  :: Status:failed :: Error:{error_message}")
            raise error_message
    
    def clear_deleted_versions_data(self,bucket_object:Bucket):
        """
        clear_deleted_versions_data: Permanently deletes all but the latest versions of objects in the specified S3 bucket.

        Args:
            bucket_object (Bucket): The S3 bucket object from which to delete old object versions.

        Raises:
            SensorFaultException: Custom exception if there is an error during the deletion of old versions.
        """
        try:
            # Iterate through all object versions
            for version in bucket_object.object_versions.all():
                if version.is_latest:
                    continue  # Skip the latest version of the object
                # Permanently delete old versions and delete markers
                if version.version_id :
                    print(f"Deleting version {version.version_id} for object {version.object_key}")
                    version.delete()
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"clear_old_version_data  :: Status:failed :: Error:{error_message}")
            raise error_message
    
    def s3_url_generation(self,object_key:str):
        """
        s3_url_generation: Generates a pre-signed URL for accessing an object in S3.

        Args:
            object_key (str): The key of the S3 object for which to generate the pre-signed URL.

        Returns:
            str: A pre-signed URL that allows access to the specified S3 object.

        Raises:
            SensorFaultException: Custom exception if there is an error during URL generation.

        Notes:
            - The pre-signed URL generated is valid for one week (604,799) seconds.
            - This URL can be shared with users to provide temporary access to the specified S3 object without needing AWS credentials.
        """
        try:
            # Generate a pre-signed URL for the file, valid for 15 days
            s3_object = self.s3_resource.Object(self.config.bucket_name, object_key)
            url = s3_object.meta.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': object_key},
                ExpiresIn=604799  # URL valid for one week
            )

            logger.info("s3_url_generation ::: URL Generated:Successfully : object_key: {object_key}")
            logger.info(f"Your pre-signed URL is: {url}")
            return url
        
        except Exception as e:
                error_message = SensorFaultException(error_message=str(e),error_detail=sys)
                logger.error(msg=f"url_generation :: Status:Failed :: error_message:{error_message}")
                raise error_message    