import pandas as pd
import sys,os
from src.exception import SensorFaultException
from src.logger import logger
from src.entity.config_entity import ModelTrainerConfig,ClusterConfig,PreprocessorConfig,ModelTunerConfig,BaseArtifactConfig
from src.components.model_tuner import ModelTuner
from src.utilities.utils import (save_models_data,proper_conversion_for_excel_file,
                                 save_model_result_excel,
                                 save_json,
                                 save_obj,
                                 copy_file,
                                 create_folder_using_file_path)

class ModelTrainer:
    def __init__(self,config:ModelTrainerConfig,input_file:pd.DataFrame,modeltunerconfig:ModelTunerConfig):
        self.config = config
        self.input_file = input_file
        self.model_tuner_config = modeltunerconfig
        self.model_tuner = ModelTuner(config=self.model_tuner_config)
        
    def initialize_model_trainer(self):
        """initialize_model_trainer :Used for initialize model trainer

        Raises:
            error_message: Custom Exception
        """
        try:
            logger.info("Start initialize model trainer process!")
            all_models_results_cluster_wise= {}
            best_models_results_cluster_wise = {}
            dataset = self.input_file.copy()
            no_of_cluster = dataset[ClusterConfig.cluster_column_name].nunique()
            for cluster in range(int(no_of_cluster)):
                logger.info(f"Start Process on Cluster : {cluster}")
                
                cluster_data = dataset[dataset[ClusterConfig.cluster_column_name]==cluster]
                
                X = cluster_data.drop(columns=[ClusterConfig.cluster_column_name,PreprocessorConfig.target_feature])
                y = cluster_data[PreprocessorConfig.target_feature]
                
                model_tuner_artifacts = self.model_tuner.initialize_model_tuner_process(X,y)
                logger.info(f"MODEL TUNER ARTIFACTS: {model_tuner_artifacts}")
                
                # exp_all_models_path = self.config.experiment_all_model_objects_path / str(cluster)
                # exp_best_models_path = self.config.experiment_best_model_object_path / str(cluster)
                # stable_all_models_path = self.config.stable_all_model_objects_path / str(cluster)
                # stable_best_model_path = self.config.stable_best_model_object_path / str(cluster)
                
                all_models_path = self.config.all_model_objects_path
                best_model_path = self.config.best_model_object_path / f"Cluster_{cluster}"
                
                save_models_data(all_model_objects_path=all_models_path,
                                 best_model_object_path=best_model_path,
                                 model_tuner_artifacts=model_tuner_artifacts)
                
                all_models_results_cluster_wise[f"Cluster:{cluster}"] = model_tuner_artifacts.all_models_data[1]
                best_models_results_cluster_wise[f"Cluster:{cluster}"] = model_tuner_artifacts.best_model_data[1]
                
            logger.info(f"initialize_model_trainer :: convert the data into df for excel data ")
            all_models_result_df =  proper_conversion_for_excel_file(all_models_results_cluster_wise)
            best_models_result_df =  proper_conversion_for_excel_file(best_models_results_cluster_wise)
            
            logger.info(f"initialize_model_trainer :: create folders for storing cluster wise models results (all_model_results,best_model_results)")
            create_folder_using_file_path(self.config.all_model_results_excel_file_path)
            create_folder_using_file_path(self.config.all_model_results_json_file_path)
            # create_folder_using_file_path(self.config.best_model_results_excel_file_path)
            # create_folder_using_file_path(self.config.best_model_results_json_file_path)
            # create_folder_using_file_path(self.config.experiment_standard_scalar_path)
            # create_folder_using_file_path(self.config.stable_standard_scalar_path)
                        
            # save the data into excel file
            logger.info(f"initialize_model_trainer :: save the all_model_results into excel")
            save_model_result_excel(all_models_result_df,self.config.all_model_results_excel_file_path)   
            logger.info(f"initialize_model_trainer :: save the all_model_results into json")
            save_json(self.config.all_model_results_json_file_path,all_models_results_cluster_wise)
            
            # save the best models data
            logger.info(f"initialize_model_trainer :: save the best_model_results into excel")
            save_model_result_excel(best_models_result_df,self.config.best_model_results_excel_file_path) 
            logger.info(f"initialize_model_trainer :: save the best_model_results into json")  
            save_json(self.config.best_model_results_json_file_path,best_models_results_cluster_wise)
            
            #save preprocessor stage two  objects(preprocessor,smote,pca)
            # final_standard_scalar_path = find_final_path(experiment_file_path=self.config.experiment_standard_scalar_path,
            #                                              stable_file_path=self.config.stable_standard_scalar_path)
            
            # final_smote_path = find_final_path(experiment_file_path=self.config.experiment_smote_path,
            #                                              stable_file_path=self.config.stable_smote_path)
            
            # final_pca_path = find_final_path(experiment_file_path=self.config.experiment_pca_path,
            #                                              stable_file_path=self.config.stable_pca_path)
            
            
            final_standard_scalar_path = self.config.standard_scalar_path
            final_smote_path = self.config.smote_path
            final_pca_path = self.config.pca_path
            
            logger.info(f"initialize_model_trainer :: create folders for storing preprocessing_stage_two objects(scalar,smote,pca)")
            create_folder_using_file_path(final_standard_scalar_path)
            create_folder_using_file_path(final_smote_path)
            create_folder_using_file_path(final_pca_path)
            
            logger.info(f"initialize_model_trainer :: storing preprocessing_stage_two objects(scalar,smote,pca)")
            save_obj(file_path=final_standard_scalar_path,obj=model_tuner_artifacts.standard_scalar_object)
            save_obj(file_path=final_smote_path,obj=model_tuner_artifacts.smote_object)
            save_obj(file_path=final_pca_path,obj=model_tuner_artifacts.pca_object)
            
            # copy files models results json files
            logger.info(f'copy files to data folder for training results')
            copy_file(self.config.all_model_results_json_file_path,BaseArtifactConfig.data_dir)
            copy_file(self.config.best_model_results_json_file_path,BaseArtifactConfig.data_dir)
            
            logger.info("Ended initialize model trainer process!")
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"initialize_model_trainer :: Status:Failed :: Error:{error_message}")
            raise error_message 