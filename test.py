from src.components.rawdata_validation import RawDataValidation
from src.entity.config_entity import TrainingRawDataValidationConfig
from pathlib import Path
import os
from src.pipeline.training_pipeline import TrainingPipeline

training_folder_path  = Path(r"C:\Users\RAVEEN\Downloads\testing_data\batch3")

training_pipeline = TrainingPipeline(training_folder_path)
training_pipeline.initialize_pipeline()