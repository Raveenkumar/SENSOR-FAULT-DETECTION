from src.components.rawdata_validation import RawDataValidation
from src.entity.config_entity import TrainingRawDataValidationConfig
from pathlib import Path
import os
from src.pipeline.training_pipeline import TrainingPipeline


training_folder_path  = Path(r"E:\data science\Projects\SENSOR-FAULT-DETECTION\cluster_data.csv")

training_pipeline = TrainingPipeline(training_folder_path)
training_pipeline.initialize_pipeline()
