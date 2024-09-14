from fastapi import FastAPI, File, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
import pandas as pd
from uvicorn import run as app_run
from src.constants import APP_HOST, APP_PORT
from src.entity.config_entity import PredictionRawDataValidationConfig,BaseArtifactConfig,S3Config
from src.entity.artifact_entity import RawDataTransformationArtifacts
from src.logger import logger
from src.pipeline.train_models import  get_training_results
from src.pipeline.training_pipeline import TrainingPipeline
from src.utilities.utils import clear_artifact_folder,read_json
import asyncio

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    # Set the upload directory path using absolute paths
    upload_dir = os.path.abspath(PredictionRawDataValidationConfig.prediction_raw_data_folder_path)  
    logger.info(f"Upload directory set to: {upload_dir}")

    try:
        # Create the directory along with all intermediate directories if they don't exist
        os.makedirs(upload_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create upload directory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create upload directory")

    # Handle each uploaded file
    logger.info(f"Saving file to: {files}")
    for file in files:
        try:
            file_name = file.filename.split("/")[1] # type: ignore
            logger.info(f"Saving file to: {file}")
            logger.info(f"Saving file to: {file.filename}")
            # Use os.path.join to construct the full file path properly
            file_path = os.path.join(upload_dir, file_name) # type: ignore
            logger.info(f"Saving file to: {file_path}")
 
            # Read the file content asynchronously
            content = await file.read()
            
            # Check if content is empty
            if not content:
                logger.warning(f"File {file_name} is empty. Skipping.")
                raise HTTPException(status_code=400, detail=f"File {file_name} is empty")

            # Save the file content to the specified path
            with open(file_path, "wb") as buffer:
                buffer.write(content)
                logger.info(f"File {file_name} saved successfully at {file_path}")

        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}. Reason: {str(e)}")

    return JSONResponse({"message": "Files uploaded successfully"})

## training related----start here----
# Training status and pipeline objects
training_status = {"completed": False}
upload_status = {"completed": False}
training_pipeline = TrainingPipeline()

async def train_model():
    await asyncio.sleep(0)  # Yield control to the event loop
    training_pipeline.initialize_pipeline()
    training_status["completed"] = True
    
async def upload_data_to_s3():
    if not upload_status["completed"]:
        # Only upload if it hasn't been completed before
        try:
            local_artifact_folder_path = BaseArtifactConfig.artifact_dir
            s3_bucket = training_pipeline.s3_bucket_obj
            training_pipeline.s3.upload_folder_to_s3(bucket_obj=s3_bucket, local_folder_path=local_artifact_folder_path)
            
            local_training_files_path = training_pipeline.rawdata_transformation_config.merge_file_path
            s3_training_files_path = training_pipeline.s3_config.training_files_path
            training_pipeline.s3.upload_files_to_s3(bucket_obj=s3_bucket, 
                                                    local_folder_path=local_training_files_path, 
                                                    s3_subfolder_path=s3_training_files_path)
            
            training_pipeline.s3.store_prediction_models()
            clear_artifact_folder()
            
            upload_status["completed"] = True  # Mark upload as completed
            
        except Exception as e:
            print(f"Upload failed: {e}")
        
@app.get("/train")
async def train_route(request: Request, background_tasks: BackgroundTasks):
    # Start the training in the background
    background_tasks.add_task(train_model)
    return templates.TemplateResponse("training.html", {"request": request})

@app.get("/training_results")
async def get_training_results_route(request: Request, background_tasks: BackgroundTasks):
    # Load Excel data for plots
    validation_data = pd.read_excel('./data/training_validation_logs.xlsx')
    preprocessing_data = pd.read_excel('./data/preprocessing_report.xlsx')
    all_model_results_data = read_json('./data/ALL_models_result.json') # type: ignore
    best_model_results_data = read_json('./data/best_model_result.json') # type: ignore

    # Determine if 'final_file.csv' is used
    file_counts = validation_data['FILENAME'].value_counts().to_dict()
    hide_validation_report = 'final_file.csv' in file_counts and file_counts['final_file.csv'] > 0

    # Process validation data for plots
    validation_summary = validation_data['STATUS'].value_counts().to_dict()
    validation_status_reasons = validation_data[validation_data['STATUS'] == 'Failed']['STATUS_REASON'].value_counts().to_dict()

    # Process Preprocessing Summary for multiple plots
    preprocessing_summary = {
        "total_columns": int(preprocessing_data['total_columns'].sum()),
        "total_records": int(preprocessing_data['total_records'].sum()),
        "no_of_duplicate_rows": int(preprocessing_data['no_of_duplicate_rows'].sum()),
        "zero_std_columns": int(preprocessing_data['zero_std_columns'].sum()),
        "nan_contains_columns": int(preprocessing_data['nan_contains_columns'].sum()),
        "highskew_columns": int(preprocessing_data['highskew_columns'].sum()),
        "outlier_columns": int(preprocessing_data['outlier_columns'].sum())
    }
    
    # all models_data_cluster_wise
    # Process all models results dynamically, remove 'best_param' and keep the necessary data
    clusters_data = {}
    for cluster_name, cluster_data in all_model_results_data.items():
        clusters_data[cluster_name] = []
        for model_name, model_data in cluster_data.items():
            model_data.pop('best_param', None)  # Remove 'best_param' from model data
            clusters_data[cluster_name].append({
                'model_name': model_name,
                'model_scores': model_data  # Assuming this includes scores like accuracy, recall, etc.
            })        
            
    best_model_clusters_data = {}
    for cluster_name, cluster_data in best_model_results_data.items():
        best_model_clusters_data[cluster_name] = []
        for model_name, model_data in cluster_data.items():
            model_data.pop('best_param', None)  # Remove 'best_param' from model data
            best_model_clusters_data[cluster_name].append({
                'model_name': model_name,
                'model_scores': model_data  # Assuming this includes scores like accuracy, recall, etc.
            })

    results = get_training_results()
    
    # Return the updated template
    return templates.TemplateResponse("training_report.html", {
        "request": request,
        "results": results,
        "validation_summary": validation_summary,
        "validation_status_reasons": validation_status_reasons,
        "preprocessing_summary": preprocessing_summary,
        "clusters_data": clusters_data,  # This contains dynamic cluster and model data
        "best_model_clusters_data": best_model_clusters_data,
        "eda_url": "/static/eda.html",
        "datadrift_url": "/static/datadrift.html",
        "hide_validation_report": hide_validation_report
    })
## training related----end here----


@app.get("/validation_summary")
def get_validation_results():
    validation_logs = pd.read_excel(PredictionRawDataValidationConfig.validation_report_file_path)
    
    summary = validation_logs['STATUS'].value_counts().to_dict()
    
    status_reasons = validation_logs[validation_logs['STATUS']=='Failed']['STATUS_REASON'].value_counts().to_dict()

    return JSONResponse({
        "validation_summary": summary,
        "status_reasons": status_reasons
    })

@app.get("/predictions")
def get_predictions():
    predictions = pd.read_csv('./data/predictions.csv')
    predictions_dict = predictions.to_dict(orient='records')

    summary = {
        "working": sum(1 for pred in predictions_dict if pred['output'] == 'Working'),
        "not_working": sum(1 for pred in predictions_dict if pred['output'] == 'Not Working')
    }

    return JSONResponse({"predictions_summary": summary})

@app.get("/bad_raw_files")
def get_bad_raw_files():
    bad_files = ['bad_file1.csv', 'bad_file2.csv']  # Example, replace with actual file list
    return JSONResponse({"bad_files": bad_files})

@app.get("/download/validation_report")
def download_validation_report():
    return FileResponse(PredictionRawDataValidationConfig.validation_report_file_path, filename='validation_logs.xlsx')

@app.get("/download/failed_files")
def download_failed_files():
    return FileResponse('./data/bad_raw_data.zip', filename='failed_files.zip')

@app.get("/download/predictions")
def download_predictions() -> FileResponse:
    return FileResponse('./data/predictions.csv', filename='predictions.csv')

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)  
