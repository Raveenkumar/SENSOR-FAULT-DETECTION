from fastapi import FastAPI, File, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
import os
from pathlib import Path
import pandas as pd
from starlette.templating import _TemplateResponse
from uvicorn import run as app_run
from src.constants import APP_HOST, APP_PORT
from src.entity.config_entity import (TrainingRawDataTransformationConfig, 
                                      PredictionRawDataValidationConfig,
                                      BaseArtifactConfig,
                                      PreprocessorConfig,
                                      ModelTrainerConfig)
from src.logger import logger
from src.pipeline.training_pipeline import TrainingPipeline
from src.pipeline.prediction_pipeline import PredictionPipeline
from src.utilities.utils import clear_artifact_folder,read_json,create_folder_using_file_path,get_bad_file_names
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

## training related----start here----

# Training status and pipeline objects
training_status = {"completed": False}
upload_status = {"completed": False}

training_pipeline = TrainingPipeline()
prediction_pipeline = PredictionPipeline()
s3_bucket = training_pipeline.s3_bucket_obj


async def train_model():
    await asyncio.sleep(0)  # Yield control to the event loop
    training_pipeline.initialize_pipeline()
    training_status["completed"] = True
    
async def sync_s3_training_data():
    if not upload_status["completed"]:
        # Only upload if it hasn't been completed before
        try:
            logger.info("start uploading data into cloud!")
            local_artifact_folder_path = BaseArtifactConfig.artifact_dir
            logger.info("storing artifact data into cloud")
            training_pipeline.s3.upload_folder_to_s3(bucket_obj=s3_bucket, local_folder_path=local_artifact_folder_path)
            logger.info("storing validated file into cloud")
            local_training_files_path = training_pipeline.rawdata_transformation_config.merge_file_path
            s3_training_files_path = training_pipeline.s3_config.training_files_path
            training_pipeline.s3.upload_files_to_s3(bucket_obj=s3_bucket, 
                                                    local_folder_path=local_training_files_path, 
                                                    s3_subfolder_path=s3_training_files_path)
            
            logger.info('Start the store models in prediction models')
            training_pipeline.s3.store_prediction_models()
            logger.info('Start the store models in prediction models')
            logger.info("End uploading data into cloud!")
            
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
    hide_validation_report = False
    if training_status["completed"] and not upload_status["completed"]:
        background_tasks.add_task(sync_s3_training_data)
          
    if os.path.exists(TrainingRawDataTransformationConfig.dashboard_validation_show):    
        hide_validation_report = True
        
    validation_data = pd.read_excel(TrainingRawDataTransformationConfig.dashboard_validation_report_file_path)
    # Process validation data for plots
    validation_sub_d = validation_data['STATUS'].value_counts().to_dict()
    no_of_files = validation_data['FILENAME'].nunique()
    validation_sub_d['Passed'] = no_of_files - validation_sub_d['Failed'] # passed validation will count more in validation report
    validation_summary = validation_sub_d
    validation_status_reasons = validation_data[validation_data['STATUS'] == 'Failed']['STATUS_REASON'].value_counts().to_dict()
    
            
    preprocessing_data = read_json(PreprocessorConfig.dashboard_preprocessor_json_file_path)
    all_model_results_data = read_json(ModelTrainerConfig.final_all_model_results_json_file_path) 
    best_model_results_data = read_json(ModelTrainerConfig.final_best_model_results_json_file_path) 

    

    # Process Preprocessing Summary for multiple plots
    preprocessing_summary = {
        "total_columns": preprocessing_data["total_columns"],
        "total_records":  preprocessing_data["total_records"],
        "no_of_duplicate_rows": preprocessing_data["no_of_duplicate_rows"],
        "zero_std_columns": preprocessing_data["zero_std_columns"],
        "high_nan_columns_dropped": preprocessing_data["hight_nan_columns_dropped"],
        "nan_imputed_columns": preprocessing_data["Nan_imputed_columns"],
        "highskew_columns": preprocessing_data["highskew_columns"],
        "outlier_columns": preprocessing_data["outlier_handled_columns"]
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
                'model_scores': dict(model_data)  # Assuming this includes scores like accuracy, recall, etc.
            })



    # Return the updated template
    return templates.TemplateResponse("training_report.html", {
        "request": request,
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



## prediction related start here---
 
@app.get("/dashboard")
def get_dashboard(request: Request) -> _TemplateResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Upload route to handle file uploads
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    logger.info("-------------------Getting files Started-----------------")
    # Directory path for uploaded files
    upload_dir = os.path.abspath(PredictionRawDataValidationConfig.prediction_raw_data_folder_path)
    logger.info(f"Upload directory set to: {upload_dir}")

    try:
        # Create the directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create upload directory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create upload directory")

    # Handle file uploads
    for file in files:
        print(file)
        print(file.filename)
        file_name = os.path.basename(file.filename) # type: ignore
        print(f'Modified File_name')
        file_path = Path(os.path.join(upload_dir, file_name)) # type: ignore
        try:
            # Read the file content asynchronously
            content = await file.read()

            if not content:
                logger.warning(f"File {file.filename} is empty. Skipping.")
                raise HTTPException(status_code=400, detail=f"File {file.filename} is empty")

            
            create_folder_using_file_path(file_path)
            # Save the file content to the specified path
            with open(file_path, "wb") as buffer:
                buffer.write(content)
                logger.info(f"File {file.filename} saved successfully at {file_path}")

        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}. Reason: {str(e)}")
    logger.info("-------------------Getting files Ended-----------------")
    return JSONResponse({"message": "Files uploaded successfully"})

# Prediction route
@app.post("/data_prediction")
async def run_prediction(background_tasks: BackgroundTasks) -> JSONResponse:
    try:
        # getting the prediction models from s3
        training_pipeline.s3.get_prediction_models(s3_bucket)
        
        # Initialize the prediction pipeline
        prediction_pipeline.initialize_pipeline()
        
        # Run the prediction process
        prediction_result = "Prediction successful!"
        
         # Add the async S3 sync task to the background
        background_tasks.add_task(sync_s3_prediction_data)
        
        # Return the prediction result immediately
        return JSONResponse({"message": prediction_result})
    
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in prediction. Reason: {str(e)}")


async def sync_s3_prediction_data():
    try:
        logger.info("Start uploading data into the cloud!")

        # This will run your synchronous S3 upload in a separate thread
        await run_in_threadpool(upload_s3_prediction_data)

        logger.info("End uploading data into the cloud!")

    except Exception as e:
        print(f"Upload failed: {e}")


def upload_s3_prediction_data():
    try:
        logger.info("start uploading data into cloud!")
        local_artifact_folder_path = BaseArtifactConfig.artifact_dir
        s3_bucket = training_pipeline.s3_bucket_obj
        logger.info("storing artifact data into cloud")
        training_pipeline.s3.upload_folder_to_s3(bucket_obj=s3_bucket, local_folder_path=local_artifact_folder_path)
        
        logger.info("storing predicted file into cloud")
        local_predicted_file_path = prediction_pipeline.config.predicted_data_with_rawdata_file_path
        s3_training_files_path = training_pipeline.s3_config.prediction_files_path
        training_pipeline.s3.upload_files_to_s3(bucket_obj=s3_bucket, 
                                                local_folder_path=local_predicted_file_path, 
                                                s3_subfolder_path=s3_training_files_path)
        
  
        logger.info("End uploading data into cloud!")
        
        clear_artifact_folder()
        
    except Exception as e:
        print(f"Upload failed: {e}")    
    
    
    

@app.get("/validation_summary")
def get_validation_results():
    validation_data = pd.read_excel(prediction_pipeline.prediction_rawdata_validation_config.dashboard_validation_report_file_path)

    # Process validation data for plots
    validation_sub_d = validation_data['STATUS'].value_counts().to_dict()
    no_of_files = validation_data['FILENAME'].nunique()
    validation_sub_d['Passed'] = no_of_files - validation_sub_d['Failed'] # passed validation will count more in validation report
    validation_summary = validation_sub_d
    validation_status_reasons = validation_data[validation_data['STATUS'] == 'Failed']['STATUS_REASON'].value_counts().to_dict()

    return JSONResponse({
        "validation_summary": validation_summary,
        "status_reasons": validation_status_reasons
    })
    

@app.get("/predictions")
def get_predictions():
    predictions = pd.read_excel(prediction_pipeline.config.predictions_data_path)
    predictions_dict = predictions.to_dict(orient='records')

    summary = {
        "working": sum(1 for pred in predictions_dict if pred[PreprocessorConfig.target_feature] == 'Working'),
        "not_working": sum(1 for pred in predictions_dict if pred[PreprocessorConfig.target_feature] == 'Not Working')
    }

    return JSONResponse({"predictions_summary": summary})
    
    
@app.get("/bad_raw_files")
def get_bad_raw_files():
    bad_files = get_bad_file_names()  # Example, replace with actual file list
    return JSONResponse({"bad_files": bad_files})

@app.get("/download/validation_report")
def download_validation_report():
    return FileResponse(prediction_pipeline.prediction_rawdata_validation_config.dashboard_validation_report_file_path, filename='validation_logs.xlsx')

@app.get("/download/failed_files")
def download_failed_files():
    return FileResponse(prediction_pipeline.prediction_rawdata_validation_config.dashboard_bad_raw_zip_file_path, filename='failed_files.zip')

@app.get("/download/predictions")
async def download_predictions() -> FileResponse:
    return FileResponse(prediction_pipeline.config.predictions_data_path, filename='predictions.xlsx')

## prediction related ends here ------

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)  
