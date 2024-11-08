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
from datetime import datetime
import asyncio
from src.constants import APP_HOST, APP_PORT
from src.entity.config_entity import (TrainingRawDataTransformationConfig, 
                                      PredictionRawDataValidationConfig,
                                      BaseArtifactConfig,
                                      PreprocessorConfig,
                                      ModelTrainerConfig)
from src.logger import logger
from src.pipeline.training_pipeline import TrainingPipeline
from src.pipeline.prediction_pipeline import PredictionPipeline
from src.utilities.utils import (clear_artifact_folder,
                                 read_json,
                                 create_folder_using_file_path,
                                 get_bad_file_names,
                                 read_csv_file,
                                 send_datadrift_mail_team,
                                 send_datadrift_mail_client)


# timestamp for first time run the app.py
c_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

# dynamic way get artifact folder for clear folder 
project_root = os.path.dirname(os.path.abspath(__file__))
artifact_dir = os.path.join(project_root, 'artifacts')
os.makedirs(artifact_dir,exist_ok=True)
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
def read_root(request: Request) -> _TemplateResponse:
    """
    Handles the root endpoint ("/") and serves the main index page.

    This function is called when a GET request is made to the root URL. It generates 
    a timestamp indicating the current date and time, which can be used for generate 
    s3 artifact folder name or other purposes. The function then renders the main index 
    HTML template and returns it as a response.

    Workflow:
    1. Get the current date and time and format it as a string in the 
       "day_month_year_hour_minute_second" format.
    2. Print the formatted timestamp to the console for debugging purposes.
    3. Render the "index.html" template and return it as a response.

    Parameters:
        request (Request): The request object containing information about the incoming 
                           HTTP request.

    Returns:
        _TemplateResponse: The rendered HTML template response for the index page.

    Notes:
        - The global variable `c_time` is updated with the current timestamp each time 
          this endpoint is accessed.
    """
    global c_time
    c_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    print(f'correct time : {c_time}')
    return templates.TemplateResponse("index.html", {"request": request})

## ---- Start of Training Related Functions ----
training_pipeline = TrainingPipeline()
prediction_pipeline = PredictionPipeline()
s3_bucket = training_pipeline.s3_bucket_obj


async def train_model() -> None:
    """
    Asynchronously runs the training pipeline.

    This function initializes the training pipeline and updates the training status 
    to indicate whether the training process has been completed. It is designed to 
    be called in the background, allowing the main event loop to continue processing 
    other requests or tasks.

    Workflow:
    1. Yield control to the event loop to allow other tasks to run.
    2. Initialize the global training and upload status dictionaries to track 
       completion of the training process and data uploads.
    3. Initialize the training pipeline using the `training_pipeline` object.
    4. Once the pipeline is initialized, update the training status to indicate 
       that training has been completed.

    Notes:
        - This function does not take any parameters and does not return any values.
        - The global variables `training_status` and `upload_status` are updated to 
          manage the state of the training and upload processes.
        - This function should be called from an async context (e.g., from a FastAPI route) 
          to ensure proper asynchronous execution.
    """
    await asyncio.sleep(0)  # Yield control to the event loop
    global training_status,upload_status
    # Training status and pipeline objects
    training_status = {"completed": False} # model training status
    upload_status = {"completed": False} # model training s3 upload status
    training_pipeline.initialize_pipeline()
    training_status["completed"] = True
    
async def sync_s3_training_data() -> None:
    """
    Synchronizes training data and model artifacts to an S3 bucket.

    This asynchronous function uploads training data and artifacts to an S3 bucket 
    if the upload process has not been completed before. It manages the uploading of 
    various components, including the local artifact folder, validated training files, 
    and prediction models.

    Workflow:
    1. Check if the upload status is marked as completed. If not, proceed with the upload.
    2. Log the start of the upload process to the cloud.
    3. Define the local artifact folder path and S3 folder path where the data will be stored.
    4. Upload the entire local artifact folder to the specified S3 folder path.
    5. Upload the validated training files to the S3 bucket.
    6. Store prediction models in the designated model source path within the S3 bucket.
    7. Clear the local artifact folder to free up space.
    8. Mark the upload status as completed to prevent future uploads.

    Notes:
        - The function uses the `training_pipeline` object to handle S3 operations.
        - Errors during the upload process are logged and printed to the console.
        - It is important to ensure that the paths provided for local and S3 storage are valid 
          and accessible.
    """
    if not upload_status["completed"]:
        # Only upload if it hasn't been upload  before (reduce duplicate upload of data) check train_model() method
        try:
            logger.info("start uploading data into cloud!")
            
            local_artifact_folder_path = BaseArtifactConfig.artifact_dir # local artifact folder
            s3_folder_path = 'artifacts/'+ c_time # s3 artifact folder
            
            # storing  local artifact folder into s3://wafersensorsdata/artifacts/
            logger.info("storing artifact data into cloud s3://wafersensorsdata/artifacts")
            training_pipeline.s3.upload_folder_to_s3(bucket_obj=s3_bucket, local_folder_path=local_artifact_folder_path,s3_folder_path=s3_folder_path)
            
            
            # storing final_file.csv into s3://wafersensorsdata/artifacts/training_files/
            logger.info("storing final_file.csv into s3://wafersensorsdata/artifacts/training_files/")
            local_training_files_path = str(training_pipeline.rawdata_transformation_config.merge_file_path)
            s3_training_files_path = training_pipeline.s3_config.training_file_path
            training_pipeline.s3.upload_file_to_s3(bucket_obj=s3_bucket, 
                                                    local_file_path=local_training_files_path, 
                                                    s3_filepath_path=s3_training_files_path)
            
            # storing local models into s3://wafersensorsdata/prediction_model_data/
            # based on champion or challenger
            logger.info("storing models into s3://wafersensorsdata/prediction_model_data/")
            local_models_source_path = s3_folder_path+"/model_data/"
            training_pipeline.s3.store_prediction_models(local_models_source_path=local_models_source_path)
            logger.info("End uploading data into cloud!")
            
            # clear the artifact folder
            clear_artifact_folder(artifact_dir=artifact_dir) 
            
            upload_status["completed"] = True  # Mark upload as completed
            
        except Exception as e:
            print(f"Upload failed: {e}")
        
@app.get("/train")
async def train_route(request: Request, background_tasks: BackgroundTasks) -> _TemplateResponse:
    """
    Initiates the training process for the machine learning model.

    This endpoint starts the model training in the background, allowing the user 
    to continue interacting with the application while training occurs.

    Args:
        request (Request): The incoming HTTP request object used for rendering the 
                           template and maintaining the request context.
        background_tasks (BackgroundTasks): A FastAPI utility to manage background tasks 
                                             that can be executed after returning the 
                                             response to the client.

    Returns:
        _TemplateResponse: A response containing the rendered HTML of the training 
                           page, indicating that the training process has started.

    Workflow:
    1. Add the `train_model` function to the background tasks to initiate the model 
       training process without blocking the request-response cycle.
    2. Return a rendered HTML response of the "training.html" template to the user, 
       indicating that training is underway.

    Notes:
        - Ensure that the `train_model` function handles all necessary components 
          for training (e.g., loading data, preprocessing, model fitting) and manages 
          any potential errors that may occur during the training process.
        - The training process should be logged appropriately to provide feedback 
          on the training status and completion to the users.
    """
    # Start the training process  in the background
    background_tasks.add_task(train_model)
    return templates.TemplateResponse("training.html", {"request": request})

@app.get("/training_results")
async def get_training_results_route(request: Request, background_tasks: BackgroundTasks) -> _TemplateResponse:
    """
    Renders the training results report page.

    This endpoint retrieves and processes various training results, validation reports, 
    and preprocessing summaries, then renders the data in an HTML template for display 
    on the training report page.

    Args:
        request (Request): The incoming HTTP request object used for rendering the 
                           template and maintaining the request context.
        background_tasks (BackgroundTasks): A FastAPI utility to manage background tasks 
                                             that can be executed after returning the 
                                             response to the client.

    Returns:
        _TemplateResponse: A response containing the rendered HTML of the training report 
                           template, populated with training results and validation summaries.

    Workflow:
    1. Check if the training process is completed and if upload status is not complete; 
       if so, initiate a background task to synchronize training data with S3.
    2. Load and process the validation report data from an Excel file, summarizing the 
       status and reasons for validation failures.
    3. Read preprocessing summary data from a JSON file and prepare statistics related to 
       preprocessing actions taken during training.
    4. Load results for all models and the best performing models, removing unnecessary 
       parameters from the results.
    5. Return a rendered HTML response with all the collected data, allowing users to view 
       training outcomes, validation reports, and preprocessing summaries.

    Notes:
        - Ensure that all required files (Excel and JSON) are accessible at their specified 
          paths; otherwise, appropriate error handling should be added to manage potential 
          file access issues.
        - The rendered template ("training_report.html") should be designed to handle and 
          present the data structures passed to it for effective display of the results.
    """
    # hide validation report when runs training on final_file.csv
    hide_validation_report = False
    
    # training process is completed and upload not done the upload data into s3
    if training_status["completed"] and not upload_status["completed"]:
        background_tasks.add_task(sync_s3_training_data)

    # check dashboard validation_show.json file exist or not if exist then show validation report only
    if os.path.exists(TrainingRawDataTransformationConfig.dashboard_validation_show):    
        hide_validation_report = True
    
    # get the validation data    
    validation_data = pd.read_excel(TrainingRawDataTransformationConfig.dashboard_validation_report_file_path)
    
    # Process validation data for plots
    validation_sub_dict = validation_data['STATUS'].value_counts().to_dict()
    no_of_files = validation_data['FILENAME'].nunique()
    validation_sub_dict['Passed'] = no_of_files - validation_sub_dict['Failed'] # passed validation will count more in validation report
    validation_summary = validation_sub_dict
    validation_status_reasons = validation_data[validation_data['STATUS'] == 'Failed']['STATUS_REASON'].value_counts().to_dict()
    
    # read model result json files        
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
## ---- End of Training Related Functions ----



## ---- Start of Prediction Related Functions ----
@app.get("/dashboard")
def get_dashboard(request: Request) -> _TemplateResponse:
    """
    Renders the dashboard page.

    This endpoint serves the dashboard HTML template, which is part of the 
    web application's user interface. The template is rendered with the 
    given request context to support dynamic content loading and 
    proper handling of routing.

    Args:
        request (Request): The incoming HTTP request object. This object 
                           is required for rendering the template and 
                           ensuring that the correct context is passed 
                           to the template engine.

    Returns:
        _TemplateResponse: A response containing the rendered HTML of the 
                           dashboard template, which can include dynamic 
                           data and user interface elements.

    Workflow:
    - Upon receiving a GET request to the "/dashboard" endpoint, this function 
      invokes the template rendering engine to generate the HTML for the 
      dashboard page.
    - The rendered page is returned to the client as part of the HTTP response, 
      allowing users to view and interact with the dashboard.

    Note:
        Ensure that the "dashboard.html" template exists in the appropriate 
        templates directory, as specified in the application configuration. 
        The template may include various UI elements, such as charts, 
        statistics, and other information relevant to the application.

    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Upload route to handle file uploads
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)) -> JSONResponse:
    """
    Endpoint to handle the uploading of multiple files.

    This function allows users to upload files to a specified directory on the server. 
    The uploaded files are processed asynchronously, ensuring efficient handling of 
    potentially large files.

    Args:
        files (list[UploadFile]): A list of files to be uploaded. The files must be 
                                   sent as part of the request body.

    Returns:
        JSONResponse: A JSON response indicating the success of the file upload 
                       operation.

    Raises:
        HTTPException: 
            - If the upload directory cannot be created, a 500 HTTP exception is raised 
              with a message indicating the failure reason.
            - If any uploaded file is empty, a 400 HTTP exception is raised with a 
              message stating that the specific file is empty.
            - If there is an error saving any file, a 500 HTTP exception is raised with 
              details about the error.

    Workflow:
    - When the endpoint is accessed, it sets up the upload directory based on the 
      configuration.
    - It attempts to create the directory if it does not exist, logging the action.
    - Each uploaded file is read asynchronously, and its content is checked for 
      emptiness.
    - If the file is valid, it is saved to the specified directory, and a log entry 
      is created to confirm successful saving.
    - If an error occurs during any part of the upload process, appropriate 
      exceptions are raised, which provide feedback to the client.

    Note:
        This endpoint is designed for use in a web application and should be called 
        via HTTP POST requests with file uploads.
    
    """
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
    """
    Endpoint to initiate the prediction process using the specified prediction models.

    This function handles the following:
    1. Retrieves the prediction models from an S3 bucket.
    2. Initializes the prediction pipeline.
    3. Executes the prediction process, logging the outcome.
    4. If the prediction is successful, it schedules the asynchronous upload of prediction 
       data to S3 as a background task.
    
    Args:
        background_tasks (BackgroundTasks): A FastAPI utility that allows the scheduling 
                                             of background tasks.

    Returns:
        JSONResponse: A JSON response containing a message about the prediction result.

    Raises:
        HTTPException: If an error occurs during the prediction process, a 500 HTTP 
                       exception is raised with a detailed error message.

    Workflow:
    - When the endpoint is called, it attempts to fetch the necessary prediction models 
      from S3 using the `get_prediction_models` method.
    - The pipeline is then initialized, and the status of the prediction process is 
      checked.
    - Depending on the status, a success or failure message is returned. If successful, 
      the S3 synchronization task is added to run in the background, allowing the API 
      to respond immediately.

    Exception Handling:
        Any exceptions encountered during the prediction process are logged and result 
        in an HTTP 500 error response, providing the user with information about the 
        failure.

    Note:
        This endpoint is designed for use in a web application and should be called 
        via HTTP POST requests to initiate the prediction process.
    
    """
    try:
        # getting the prediction models from s3
        training_pipeline.s3.get_prediction_models(s3_bucket)
        
        # Initialize the prediction pipeline
        prediction_status = prediction_pipeline.initialize_pipeline()
        
        # Run the prediction process
        if prediction_status:
            prediction_result ="Prediction successful!"
              # Add the async S3 sync task to the background
            background_tasks.add_task(sync_s3_prediction_data)
        else:    
            prediction_result ="Prediction Process Failed!"
       
        # Return the prediction result immediately
        return JSONResponse({"message": prediction_result})
    
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in prediction. Reason: {str(e)}")

async def sync_s3_prediction_data() -> None:
    """
    Asynchronously handles the upload of prediction data to an S3 bucket by executing 
    the synchronous upload function in a separate thread.

    This function performs the following:
    1. Logs the start of the upload process.
    2. Calls the `upload_s3_prediction_data` function, which executes the actual upload 
       of prediction data and artifacts to S3.
    3. Logs the completion of the upload process.

    Returns:
        None

    Workflow:
    - Initiates the upload process to cloud storage asynchronously.
    - Utilizes `run_in_threadpool` to run the synchronous upload in a separate thread, 
      allowing the asynchronous function to maintain non-blocking behavior.
    
    Exception Handling:
        Captures and logs any exceptions that occur during the upload process, 
        printing an error message if the upload fails.
    
    Note:
        This function is designed to be called in an asynchronous context, ensuring that 
        the application remains responsive while handling potentially time-consuming 
        S3 upload operations.

    """
    try:
        logger.info("Start uploading data into the cloud!")

        # This will run your synchronous S3 upload in a separate thread
        await run_in_threadpool(upload_s3_prediction_data)

        logger.info("End uploading data into the cloud!")

    except Exception as e:
        print(f"Upload failed: {e}")

def upload_s3_prediction_data() -> None:
    """
    Handles the upload of prediction data to an S3 bucket, including data drift detection and notifications.

    This function performs the following steps:
    1. Downloads the original training data from S3 to a local path.
    2. Reads both the original training data and the reference prediction data.
    3. Calculates data drift between the original and reference datasets.
    4. Uploads the local artifact folder containing prediction results to a designated S3 path, organized by timestamp.
    5. Saves the non-duplicate predictions CSV to a specified S3 location.
    6. If data drift is detected, generates a report URL and sends notifications to the client and backend team.

    Returns:
        None

    Workflow:
    - Downloads original training data from S3 for drift comparison.
    - Checks for data drift between the training data and prediction results.
    - Uploads artifacts (e.g., prediction files) to timestamped S3 folders.
    - If data drift is detected, sends data drift report notifications to the team and client.
    
    Exception Handling:
        Captures and logs any exceptions that occur during the process, printing an error message if the upload fails.

    """
    try:
        # getting the bucket obj
        s3_bucket = training_pipeline.s3_bucket_obj 
        
        # Run Data Drift
        # getting s3 training file path
        s3_training_file_path = training_pipeline.s3_config.training_file_path
        
        # getting  local training file path
        create_folder_using_file_path(Path(training_pipeline.data_ingestion_config.training_final_file_path))
        local_training_file_path = training_pipeline.data_ingestion_config.training_final_file_path
        
        # download the s3 training file to local path
        training_pipeline.s3.download_file_from_s3(bucket_obj=s3_bucket,
                                                   local_file_path=local_training_file_path,
                                                   s3_file_path=s3_training_file_path)
        logger.info("Getting original training_df and reference_prediction_df")
        logger.info("reading original training_df and reference_prediction_df")
        original_training_df = read_csv_file(Path(local_training_file_path))
        reference_prediction_df =  read_csv_file(prediction_pipeline.config.predicted_data_with_rawdata_file_path)
        
        # Find the data drift and drift status
        drift_status = prediction_pipeline.data_drift.find_data_drift(original_data=original_training_df,
                                                       reference_data=reference_prediction_df)
        
        # upload the local artifact folder into cloud(prediction folder)
        logger.info("start uploading data into cloud!")
        local_artifact_folder_path = BaseArtifactConfig.artifact_dir # local artifact folder path
        s3_folder_path = 'artifacts/'+ c_time # need to generate timestamp based folder each prediction
        logger.info("storing artifact data into cloud s3://wafersensorsdata/artifacts")
        training_pipeline.s3.upload_folder_to_s3(bucket_obj=s3_bucket, local_folder_path=local_artifact_folder_path,s3_folder_path=s3_folder_path) # entire artifact folder
        
        # storing  non_duplicate_df+predictions.csv into s3://wafersensorsdata/artifacts/predicted_files/
        logger.info("storing predicted file into cloud s3://wafersensorsdata/artifacts/predicted_files/")
        local_predicted_file_path = str(prediction_pipeline.config.predicted_data_with_rawdata_file_path) # non_duplicate_df+predictions.csv
        s3_prediction_files_path = "artifacts/predicted_files/prediction_data"+c_time+".csv" 
        training_pipeline.s3.upload_file_to_s3(bucket_obj=s3_bucket, 
                                                local_file_path=local_predicted_file_path, 
                                                s3_filepath_path=s3_prediction_files_path)
        
        # if drift detected then start sending mails (client & backend team)
        if drift_status:
            # generate url
            url_object_path = s3_folder_path + "/prediction_data/evaluation_data/data_drift.html"
            drift_report_url = training_pipeline.s3.s3_url_generation(url_object_path)
            
            # send the mail to team
            send_datadrift_mail_team(url=drift_report_url, 
                                s3_prediction_folder_name=s3_folder_path)

            # send the mail to client
            send_datadrift_mail_client(prediction_pipeline.config.predictions_with_probabilities_data_path)

        logger.info("End uploading data into cloud!")
        
        # clear the artifact folder data
        clear_artifact_folder(artifact_dir=artifact_dir)
        
    except Exception as e:
        print(f"Upload failed: {e}")    
    
@app.get("/validation_summary")
def get_validation_results() -> JSONResponse:
    """
    Retrieves a summary of the validation results from the validation report.

    This endpoint reads the validation report from an Excel file, processes
    the validation statuses of files, and summarizes the validation results
    by counting the number of files that passed or failed. Additionally, it 
    identifies the main reasons for validation failures.

    The response includes:
    - "validation_summary": Dictionary summarizing the number of files that 
      passed or failed validation, structured as `{'Passed': int, 'Failed': int}`.
    - "status_reasons": Dictionary summarizing the reasons for validation 
      failures, structured as `{reason: count}`.

    Returns:
        JSONResponse: A JSON response containing the `validation_summary` 
                      with counts of passed and failed files, and 
                      `status_reasons` with counts for each failure reason.
    """
    # read the validation report
    validation_data = pd.read_excel(prediction_pipeline.prediction_rawdata_validation_config.dashboard_validation_report_file_path)

    # Process validation data for plots (for validation failed files report)
    validation_sub_dict = validation_data['STATUS'].value_counts().to_dict()
    no_of_files = validation_data['FILENAME'].nunique()
    validation_sub_dict['Passed'] = no_of_files - validation_sub_dict['Failed'] # passed validation will count more in validation report we need only 4 stages of validation passed files
    validation_summary = validation_sub_dict
    validation_status_reasons = validation_data[validation_data['STATUS'] == 'Failed']['STATUS_REASON'].value_counts().to_dict()

    return JSONResponse({
        "validation_summary": validation_summary,
        "status_reasons": validation_status_reasons
    })
    
@app.get("/predictions")
def get_predictions() -> JSONResponse:
    """
    Retrieves a summary of predictions from the predictions dataset.

    This endpoint reads predictions from an Excel file, converting the data 
    into a dictionary format and summarizing the count of "working" and 
    "not_working" predictions based on the specified target feature mappings 
    in the configuration.

    The response includes:
    - "working": Count of entries classified as working (based on 
      `target_feature_zero_map`).
    - "not_working": Count of entries classified as not working (based on 
      `target_feature_one_map`).

    Returns:
        JSONResponse: A JSON response containing `predictions_summary` with 
                      the counts of working and not working predictions, 
                      structured as `{"predictions_summary": {"working": int, 
                      "not_working": int}}`.
    """
    # read the predictions.xlsx 
    predictions = pd.read_excel(prediction_pipeline.config.predictions_data_path)
    predictions_dict = predictions.to_dict(orient='records')

    summary = {
        "working": sum(1 for pred in predictions_dict if pred[PreprocessorConfig.target_feature] == prediction_pipeline.config.target_feature_zero_map),
        "not_working": sum(1 for pred in predictions_dict if pred[PreprocessorConfig.target_feature] == prediction_pipeline.config.target_feature_one_map)
    }

    return JSONResponse({"predictions_summary": summary})

# getting bad files names
@app.get("/bad_raw_files")
def get_bad_raw_files() -> JSONResponse:
    """
    Fetches the list of bad raw files from the data validation process.

    This endpoint retrieves filenames that failed validation during the 
    data preprocessing stage of the prediction pipeline. These files are 
    considered "bad" due to errors or inconsistencies detected in their 
    structure or data quality.

    Returns:
        JSONResponse: A JSON response containing a list of filenames for 
                      bad raw files, structured as `{"bad_files": [...]}`.
    """
    bad_files = get_bad_file_names()  
    return JSONResponse({"bad_files": bad_files})

# download handles
@app.get("/download/validation_report")
def download_validation_report() -> FileResponse:
    """
    Downloads the validation report as an Excel file.

    This endpoint provides a download link for the validation report generated 
    during the prediction pipeline's data validation process. The report 
    is returned as an Excel file named `validation_logs.xlsx`.

    Returns:
        FileResponse: A response containing the `validation_logs.xlsx` file for download.
    """
    return FileResponse(prediction_pipeline.prediction_rawdata_validation_config.dashboard_validation_report_file_path, filename='validation_logs.xlsx')

@app.get("/download/failed_files")
def download_failed_files() -> FileResponse:
    """
    Downloads the failed files in a zip format.

    This endpoint provides a download link for the zip file containing failed files 
    that didn't pass validation during the prediction pipeline process. It returns 
    a `FileResponse` to allow the client to download `failed_files.zip`.

    Returns:
        FileResponse: A response containing the `failed_files.zip` file for download.
    """
    return FileResponse(prediction_pipeline.prediction_rawdata_validation_config.dashboard_bad_raw_zip_file_path, filename='failed_files.zip')

@app.get("/download/predictions")
async def download_predictions() -> FileResponse:
    """
    Downloads the predictions file in Excel format.

    This method provides the predictions file, `predictions.xlsx`, for download. 
    It generates a `FileResponse` to allow the client to retrieve the file directly.

    Returns:
        FileResponse: A response containing the file `predictions.xlsx` for download.
    """
    return FileResponse(prediction_pipeline.config.predictions_data_path, filename='predictions.xlsx')

## ---- End of Prediction Related Functions ----

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)  
