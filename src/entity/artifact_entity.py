from dataclasses import dataclass
import os
from typing import Optional
from datetime import datetime
from src.constants import *
from pathlib import Path
from pandas import DataFrame

# raw data validation artifacts
@dataclass
class RawDataValidationArtifacts:
    good_raw_data_folder:Path
    bad_raw_data_folder:Path
    validation_log_file_path:Path
    
# raw data transformation artifacts
@dataclass
class RawDataTransformationArtifacts:
    final_file_path:Path    

@dataclass
class DataIngestionArtifacts:
    input_dataframe:DataFrame
    
@dataclass
class PreprocessorArtifacts:
    preprocessed_data:DataFrame
    preprocessed_object_path:Path   
    
@dataclass
class ClusterArtifact:
    final_file : DataFrame    
    silhouette_score_ : Optional[float]
   

