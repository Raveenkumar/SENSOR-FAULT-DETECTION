import sys
from pathlib import Path
import pandas as pd
import os
from src.logger import logger
from src.exception import SensorFaultException
from src.entity.config_entity import (PredictionRawDataValidationConfig,
                                      PredictionRawDataTransformationConfig,
                                      PredictionPipelineConfig,
                                      DataDriftConfig)
from src.components.rawdata_validation import RawDataValidation
from src.components.rawdata_transformation import RawDataTransformation
from src.components.data_ingestion import DataIngestion
from src.components.model_evaluation import DataDrift
from src.entity.artifact_entity import PredictionPipelineArtifacts
import numpy as np
from src.utilities.utils import load_obj,read_csv_file,remove_file,save_model_result_excel,save_model_result_feedback_excel

class PredictionPipeline:
    def __init__(self) -> None:
        self.config = PredictionPipelineConfig()
        self.prediction_rawdata_validation_config = PredictionRawDataValidationConfig()
        self.prediction_rawdata_transformation_config = PredictionRawDataTransformationConfig()
        self.data_drift_config = DataDriftConfig()
        self.folder_path = self.prediction_rawdata_validation_config.prediction_raw_data_folder_path
        self.data_drift = DataDrift(self.data_drift_config)
        


    def initialize_pipeline(self):
        try:
            logger.info(msg="---------------Started Prediction Pipeline---------------")
            # remove prediction.xlsx file for avoid getting previous data 
            remove_file(self.config.predictions_data_path)
            
            # raw data validation process
            raw_data_validation = RawDataValidation(config=self.prediction_rawdata_validation_config,
                                                              folder_path=self.folder_path) 
            
            raw_data_validation_artifacts = raw_data_validation.initialize_rawdata_validation_process()
            # logger.info(raw_data_validation_artifacts)
            
            raw_data_transformation = RawDataTransformation(config=self.prediction_rawdata_transformation_config,
                                                            rawdata_validation_artifacts=raw_data_validation_artifacts)
            self.raw_data_transformation_artifacts = raw_data_transformation.initialize_data_transformation_process()
            
            # data ingestion process
            input_file = self.raw_data_transformation_artifacts.final_file_path
            data_ingestion = DataIngestion(input_file)
            data_ingestion_artifact_file = data_ingestion.get_data()
            
            
            logger.info("Data Preprocessing :: Status:Started")
            # load preprocessing_stage_one_obj
            input_file = data_ingestion_artifact_file
            preprocessor_obj = load_obj(self.config.preprocessor_stage_one_obj_path)
            preprocessed_stage_one_data = preprocessor_obj.transform(input_file) # type: ignore
            
            # dataset for after duplicates in preprocessor_stage_one  need for wafers column
            preprocessing_stage_one_data_with_wafer_column = read_csv_file(self.config.preprocessor_stage_one_data_path)
            
            logger.info("Data Preprocessing :: Status:Ended")
            
            logger.info("Data Clustering Labels :: Status:Started")
            # load cluster obj
            cluster_obj = load_obj(self.config.cluster_obj_path)
            cluster_labels = cluster_obj.predict(preprocessed_stage_one_data) # type: ignore
            
            # Concatenate the cluster labels with the preprocessed data
            preprocessed_stage_one_data = pd.concat(
                [preprocessed_stage_one_data, pd.Series(cluster_labels, name=self.config.cluster_column_name)], 
                axis=1
            )            
            
            # Now you can copy the DataFrame if needed
            final_cluster_data = preprocessed_stage_one_data.copy()
            # combine wafer names final file
            final_cluster_data = pd.concat(
                [final_cluster_data, preprocessing_stage_one_data_with_wafer_column[[self.config.wafer_column_name]]],
                axis=1
            )
            logger.info("Data Clustering Labels :: Status:Ended")
            
            
            # Perform predictions cluster-wise and combine all the predictions
            logger.info("Prediction Process :: Status:Started")
            prediction_files = []
            final_predictions_with_probabilities_files =[]
            for cluster_no in range(final_cluster_data[self.config.cluster_column_name].nunique()):
                cluster_sub_folder_path = Path(os.path.join(self.config.best_models_path, f'Cluster_{cluster_no}'))
                logger.info(f"Getting the data from Cluster_{cluster_no}")
                
                # Extract the data for this cluster
                cluster_data = final_cluster_data[final_cluster_data[self.config.cluster_column_name] == cluster_no]
                prediction_data = cluster_data.drop(columns=[self.config.wafer_column_name, self.config.cluster_column_name])
                
                # Load objects
                scalar_obj_path = cluster_sub_folder_path / self.config.standard_scalar_obj_name
                pca_obj_path = cluster_sub_folder_path / self.config.pca_obj_name
                model_path = cluster_sub_folder_path / self.config.best_model_name
                
                scalar_obj = load_obj(scalar_obj_path)
                logger.info(f"Prediction Process :: Status: Loading scalar obj Success :: {scalar_obj}")
                pca_obj = load_obj(pca_obj_path)
                logger.info(f"Prediction Process :: Status: Loading pca obj Success :: {pca_obj}")
                model_obj = load_obj(model_path)
                logger.info(f"Prediction Process :: Status: Loading model_obj Success :: {model_obj}")
                
                # Transform data
                scaled_data = scalar_obj.transform(prediction_data) # type: ignore
                pca_data = pca_obj.transform(scaled_data)  # type: ignore
                predictions = model_obj.predict(pca_data)  # type: ignore
                prediction_proba = model_obj.predict_proba(pca_data).max(axis=1) # type: ignore
                predictions_probabilities = np.round(prediction_proba,2)  # type: ignore
                logger.info(f"Cluster:{cluster_no}")
                logger.info(f"prediction_probabilities :{predictions_probabilities}")
                
                
                # Ensure index alignment by resetting the index
                cluster_wafer = cluster_data[self.config.wafer_column_name].reset_index(drop=True)
                predictions_series = pd.Series(predictions, name=self.config.output_column_name).reset_index(drop=True)
                predictions_probabilities_series = pd.Series(predictions_probabilities, name=self.config.confidence_column_name).reset_index(drop=True)
                
                # Concatenate predictions with wafer data
                final_prediction = pd.concat([cluster_wafer, predictions_series], axis=1)
                final_predictions_with_probabilities = pd.concat([cluster_wafer, predictions_series,predictions_probabilities_series], axis=1)
                
                logger.info(f"Cluster {cluster_no} - Number of Wafer IDs: {len(cluster_wafer)}")
                logger.info(f"Cluster {cluster_no} - Number of Predictions: {len(predictions_series)}")
                logger.info(f"Cluster {cluster_no} - Number of Predictions: {len(predictions_probabilities_series)}")
                
                # Store the final prediction for this cluster
                prediction_files.append(final_prediction)
                final_predictions_with_probabilities_files.append(final_predictions_with_probabilities)

            # Combine all the predictions from different clusters
            final_predictions_combined = pd.concat(prediction_files, axis=0).reset_index(drop=True)
            final_predictions_with_probabilities_combined = pd.concat(final_predictions_with_probabilities_files, axis=0).reset_index(drop=True)
            
            final_prediction_file = final_predictions_combined.copy()
            final_predictions_with_probabilities_file = final_predictions_with_probabilities_combined.copy()
            
            logger.info('Prediction Process :: Status: Output column mapped success :: 0:Working & 1:NotWorking')
            final_prediction_file[self.config.output_column_name] = final_prediction_file[self.config.output_column_name].map({0:self.config.target_feature_zero_map,1:self.config.target_feature_one_map})
            final_predictions_with_probabilities_file[self.config.output_column_name] = final_predictions_with_probabilities_file[self.config.output_column_name].map({0:self.config.target_feature_zero_map,1:self.config.target_feature_one_map})
                
            save_model_result_excel(df=final_prediction_file,excel_file_path=self.config.predictions_data_path)
            logger.info(f"Prediction Process :: Status: save the prediction file Successfully :: {self.config.predictions_data_path}")
            
            save_model_result_feedback_excel(df=final_predictions_with_probabilities_file,excel_file_path=self.config.predictions_with_probabilities_data_path)
            logger.info(f"Prediction Process :: Status: save feedback file contains prediction with probabilities file Successfully :: {self.config.predictions_with_probabilities_data_path}")
            
            # prediction with raw file for retrain purpose
            prediction_with_rawdata = pd.merge(preprocessing_stage_one_data_with_wafer_column,final_predictions_combined,how='left')

            prediction_with_rawdata.to_csv(self.config.predicted_data_with_rawdata_file_path,index=False)
            logger.info(f"Prediction Process :: Status: save the prediction data with raw file Successfully :: {self.config.predicted_data_with_rawdata_file_path}")
            
            logger.info(msg="---------------Completed Prediction Pipeline-------------")
            prediction_artifacts = PredictionPipelineArtifacts(prediction_status=True)
            
            return prediction_artifacts.prediction_status
        except Exception as e:
            logger.error(msg=SensorFaultException(error_message=e,error_detail=sys))
    