import os
from pathlib import Path

project_name = "src"

list_of_files = [
    f'{project_name}/__init__.py',
    f'{project_name}/components/__init__.py',
    f'{project_name}/components/rawdata_validation.py',
    f'{project_name}/components/rawdata_transformation.py',
    f'{project_name}/components/data_ingestion.py',
    f'{project_name}/components/data_preprocessing.py',
    f'{project_name}/components/data_clustering.py',
    f'{project_name}/components/model_trainer.py',
    f'{project_name}/components/model_evaluation.py',
    f'{project_name}/components/model_pusher.py',
    f'{project_name}/db_management/__init__.py',
    f'{project_name}/db_management/aws_storage.py',
    f'{project_name}/configuration/__init__.py',
    f'{project_name}/configuration/aws_connection.py',
    f'{project_name}/constants/__init__.py',
    f'{project_name}/entity/__init__.py',
    f'{project_name}/entity/config_entity.py',
    f'{project_name}/entity/artifact_entity.py',
    f'{project_name}/exception/__init__.py',
    f'{project_name}/logger/__init__.py',
    f'{project_name}/pipeline/training_pipeline.py',
    f'{project_name}/pipeline/prediction_pipeline.py',
    f'{project_name}/utils/utils.py',
    'app.py',
    'Dockerfile',
    'requirements.txt',
    '.dockerignore',
    'setup.py',
    'config/training_schema.json',
    'config/prediction_schema.json',
    'notebook/eda.ipynb',
    'notebook/model_build.ipynb',
    'demo.py',
    'test.py'
    
    
    
    
    
]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)
    
    # check if filedir is empty or not
    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
    
    # create file if it doesn't exist and file is empty only
    
    if (not os.path.exists(filepath)) or (os.path.getsize(filepath)==0):
        with open(filepath, 'w') as f:
            pass
        
    else:
        print(f"file is already exists: {filepath}")   
