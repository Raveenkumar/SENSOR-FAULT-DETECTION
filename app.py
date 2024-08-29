from fastapi import FastAPI, File, HTTPException, UploadFile, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import pandas as pd
from uvicorn import run as app_run
from src.constants import APP_HOST, APP_PORT
from src.entity.config_entity import PredictionRawDataValidationConfig
from src.logger import logger

# Import your training pipeline module
from src.training_pipeline import train_model, get_training_results  # Assuming these functions exist

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

@app.get("/train")
async def train_route(request: Request, background_tasks: BackgroundTasks):
    # Add the training task to run in the background
    background_tasks.add_task(train_model)
    # Render a training page with animated text
    return templates.TemplateResponse("training.html", {"request": request})

@app.get("/training_results")
def get_training_results_route(request: Request):
    # Fetch training results like accuracy, scores, etc.
    results = get_training_results()  # Assuming this function retrieves the results
    return templates.TemplateResponse("training_results.html", {
        "request": request,
        "results": results,
        "eda_url": "/static/eda.html",
        "datadrift_url": "/static/datadrift.html"
    })

@app.get("/validation_summary")
def get_validation_results():
    validation_logs = pd.read_excel('./data/validation_logs.xlsx')
    
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
    return FileResponse('./data/validation_logs.xlsx', filename='validation_logs.xlsx')

@app.get("/download/failed_files")
def download_failed_files():
    return FileResponse('./data/bad_raw_data.zip', filename='failed_files.zip')

@app.get("/download/predictions")
def download_predictions():
    return FileResponse('./data/predictions.csv', filename='predictions.csv')

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)  
