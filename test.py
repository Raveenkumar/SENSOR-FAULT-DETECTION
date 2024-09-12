from src.components.rawdata_validation import RawDataValidation
from src.entity.config_entity import TrainingRawDataValidationConfig
from pathlib import Path
import os
from src.pipeline.training_pipeline import TrainingPipeline
from src.db_management.aws_storage import SimpleStorageService
from src.constants import *

# training_folder_path  = Path(r"E:\data science\Projects\SENSOR-FAULT-DETECTION\cluster_data.csv")

# training_pipeline = TrainingPipeline(training_folder_path)
# training_pipeline.initialize_pipeline()
s3  = SimpleStorageService()

local_path = Path("Training_Batch_files")
s3_folder = 'client_db_data/training_batch_files/'
bucket_obj = s3.get_bucket(BUCKET_NAME)

s3.download_files_from_s3(bucket_obj=bucket_obj,
                          local_folder_path=local_path,
                          s3_subfolder_path=s3_folder)
