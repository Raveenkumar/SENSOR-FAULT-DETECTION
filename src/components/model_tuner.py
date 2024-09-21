import sys
from typing import Any
from pathlib import Path
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split ,StratifiedKFold,RandomizedSearchCV
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from sklearn.decomposition import PCA
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier
from src.logger import logger
from src.exception import SensorFaultException
from src.entity.config_entity import  ModelTunerConfig
from src.utilities.utils import model_result
from src.entity.artifact_entity import ModelTunerArtifacts
import numpy as np




class ModelTuner:
    def __init__(self,config:ModelTunerConfig) -> None:
        self.config = config
    
    def stratifiedKfold_validation(self) -> StratifiedKFold:
        """stratifiedKfold_validation :Used for cross validation in random search cv

        Returns:
            StratifiedKFold: StratifiedKFold object
        """
        return StratifiedKFold(n_splits=5)
    
    def model_build(self,model:BaseEstimator, params:dict) -> RandomizedSearchCV:
        """model_build :Used for build a model

        Args:
            model (BaseEstimator): sklearn model
            params (dict): param_grid for hyperparameter tuning

        Raises:
            error_message: Custom Exception

        Returns:
            RandomizedSearchCV: RandomizedSearchCV Object
        """
        try:
            
            random_search = RandomizedSearchCV(estimator=model,
                                               param_distributions=params,
                                               n_iter=10,
                                               cv=self.stratifiedKfold_validation(),
                                               scoring='roc_auc',
                                               error_score='raise',
                                               random_state=42,
                                               n_jobs=-1)
            # logger.info(msg=f"model_build :: Status:Success :: Model_Name: {model_name}")
            
            return random_search
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"model_build :: Status:Failed :: Error:{error_message}")
            raise error_message
    
    def get_best_svc_parameters(self,X:pd.DataFrame, y:pd.Series)-> tuple[dict[str, Any],BaseEstimator,dict[str, Any]]:
        """get_best_svc_parameters : Used for find best parameters in SVC

        Args:
            X (pd.DataFrame): X data (without label column)
            y (pd.Series): Y data (label column)

        Raises:
            error_message: Custom Exception

        Returns:
            tuple[dict[str, Any], BaseEstimator,dict[str, Any]]: mlflow_dict, model_obj,result_dict = {
                'best_param': model.best_estimator_,
                'training_score': model.score(X_train, y_train),
                'test_score': model.score(X_test, y_test), 
                'accuracy': accuracy_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_pred, zero_division=0),
                'auc_score': roc_auc_score(y_test, y_pred)
            }
        """
        try:
            logger.info(msg=f"get_best_svc_parameters :: Status:Started")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=100)
            model = self.model_build(model=SVC(),params=self.config.svc_param_grid)
            model.fit(X_train, y_train)

            logger.info(msg=f"get_best_svc_parameters :: Status:Finish") 
            
            return model_result(model=model, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_best_svc_parameters :: Status:Failed :: Error:{error_message}")
            raise error_message
    
    def get_best_gaussiannb_parameters(self,X:pd.DataFrame, y:pd.Series)-> tuple[dict[str, Any],BaseEstimator,dict[str, Any]]:
        """get_best_gaussiannb_parameters : Used for find best parameters in GaussianNB

        Args:
            X (pd.DataFrame): X data (without label column)
            y (pd.Series): Y data (label column)

        Raises:
            error_message: Custom Exception

        Returns:
            tuple[dict[str, Any],BaseEstimator,dict[str, Any]]: model_obj,result_dict = {
                'best_param': model.best_estimator_,
                'training_score': model.score(X_train, y_train),
                'test_score': model.score(X_test, y_test), 
                'accuracy': accuracy_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_pred, zero_division=0),
                'auc_score': roc_auc_score(y_test, y_pred)
            }
            }
        """
        try:
            logger.info(msg=f"get_best_gaussiannb_parameters :: Status:Started")
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=100)
            model = self.model_build(model=GaussianNB(),params=self.config.gaussiannb_param_grid)
            model.fit(X_train, y_train)

            logger.info(msg=f"get_best_gaussiannb_parameters :: Status:Finish") 
            
            return model_result(model=model, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_best_gaussiannb_parameters :: Status:Failed :: Error:{error_message}")
            raise error_message
    
    def get_best_randomforest_parameters(self,X:pd.DataFrame, y:pd.Series)-> tuple[dict[str, Any],BaseEstimator,dict[str, Any]]:
        """get_best_randomforest_parameters : Used for find best parameters in RandomForestClassifier

        Args:
            X (pd.DataFrame): X data (without label column)
            y (pd.Series): Y data (label column)

        Raises:
            error_message: Custom Exception

        Returns:
            tuple[dict[str, Any],BaseEstimator,dict[str, Any]]: mlflow_dict,model_obj,result_dict = {
                'best_param': model.best_estimator_,
                'training_score': model.score(X_train, y_train),
                'test_score': model.score(X_test, y_test), 
                'accuracy': accuracy_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_pred, zero_division=0),
                'auc_score': roc_auc_score(y_test, y_pred)
            }
            }
        """
        try:
            logger.info(msg=f"get_best_randomforest_parameters :: Status:Started")
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=100)
            model = self.model_build(model=RandomForestClassifier(),params=self.config.randomforest_param_grid)
            model.fit(X_train, y_train)

            logger.info(msg=f"get_best_randomforest_parameters :: Status:Finish") 
            return model_result(model=model, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_best_randomforest_parameters :: Status:Failed :: Error:{error_message}")
            raise error_message
                                                    
    def get_best_xgbclassifier_parameters(self,X:pd.DataFrame, y:pd.Series)-> tuple[dict[str, Any],BaseEstimator,dict[str, Any]]:
        """get_best_xgbclassifier_parameters : Used for find best parameters in XGBClassifier

        Args:
            X (pd.DataFrame): X data (without label column)
            y (pd.Series): Y data (label column)

        Raises:
            error_message: Custom Exception

        Returns:
            tuple[dict[str, Any],BaseEstimator,dict[str, Any]]: mlflow_dict ,model_obj,result_dict = {
                'best_param': model.best_estimator_,
                'training_score': model.score(X_train, y_train),
                'test_score': model.score(X_test, y_test), 
                'accuracy': accuracy_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_pred, zero_division=0),
                'auc_score': roc_auc_score(y_test, y_pred)
            }
            }
        """
        try:
            logger.info(msg=f"get_best_xgbclassifier_parameters :: Status:Started")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=100)
            model = self.model_build(model=XGBClassifier(),params=self.config.xgbclassifier_param_grid)
            model.fit(X_train, y_train)

            logger.info(msg=f"get_best_xgbclassifier_parameters :: Status:Finish") 
            
            return model_result(model=model, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"get_best_xgbclassifier_parameters :: Status:Failed :: Error:{error_message}")
            raise error_message
                                  
                                  
    def find_best_model(self,models_object_data:dict ,models_results_data:dict):# -> tuple[Any, Any] | tuple[()] | None: 
        """find_best_model :Used for find Best model

        Args:
            models_data (dict): all training models data

        Raises:
            error_message: Custom Exception

        Returns:
            tuple: best_model_obj,best_model_results
        """
        try:
            auc_scores = {model:score_['auc_score'] for model,score_ in models_results_data.items()}
            
            max_auc_score = max(auc_scores.values())
            model_results ={}
            
            if auc_scores['xgbclassifier']== max_auc_score:
                logger.info(f"find_best_model:: Status:Success :: Model_Data:'xgbclassifier'")
                model_results["xgbclassifier"]=models_results_data['xgbclassifier']
                return models_object_data['xgbclassifier'], model_results
                
            elif auc_scores['randomforest']== max_auc_score:
                logger.info(f"find_best_model:: Status:Success :: Model_Data:'randomforest'")
                model_results["randomforest"]=models_results_data['randomforest']
                return models_object_data['randomforest'], model_results

            elif auc_scores['svc']== max_auc_score:
                logger.info(f"find_best_model:: Status:Success :: Model_Data:'svc'")
                model_results["svc"]=models_results_data['svc']
                return models_object_data['svc'], model_results     
                    
            elif auc_scores['gaussiannb']== max_auc_score:
                logger.info(f"find_best_model:: Status:Success :: Model_Data:'gaussiannb'")
                model_results["gaussiannb"] = models_results_data['gaussiannb']
                return models_object_data['gaussiannb'], model_results
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"find_best_model :: Status:Failed :: Error:{error_message}")
            raise error_message
                                      
    
    def initialize_model_tuner_process(self,X:pd.DataFrame,y) -> ModelTunerArtifacts:
        """initialize_model_tuner_process :Used for initialize the model tuner process

        Raises:
            error_message: Custom Exception

        Returns:
            ModelTunerArtifacts: provide all_models_data,best_model_data
        """
        try:
            logger.info("Start initialize model tuner process!")
            scalar = StandardScaler()
            scaled_data  = scalar.fit_transform(X)
            smote = SMOTE(sampling_strategy='minority', k_neighbors=2, random_state=42)
            res_x, res_y = smote.fit_resample(scaled_data, y) # type: ignore
            res_y = pd.Series(res_y) # type: ignore
            pca = PCA(n_components=0.99) 
            pca_data = pca.fit_transform(res_x) # type: ignore
            pca_data = pd.DataFrame(pca_data)
            
            all_model_result = {}
            svc_mlflow_result_dict,svc_model_obj, all_model_result['svc'] = self.get_best_svc_parameters(pca_data, res_y)
            gaussiannb_mlflow_result_dict,gaussiannb_model_obj,all_model_result['gaussiannb'] = self.get_best_gaussiannb_parameters(pca_data, res_y)
            randomforest_mlflow_result_dict,randomforest_model_obj,all_model_result['randomforest'] = self.get_best_randomforest_parameters(pca_data, res_y)
            xgbclassifier_mlflow_result_dict,xgbclassifier_model_obj,all_model_result['xgbclassifier'] = self.get_best_xgbclassifier_parameters(pca_data, res_y)
            
            all_models_objs_data = {}
            all_models_objs_data['svc'] = svc_model_obj
            all_models_objs_data['gaussiannb'] = gaussiannb_model_obj
            all_models_objs_data['randomforest'] = randomforest_model_obj
            all_models_objs_data['xgbclassifier'] = xgbclassifier_model_obj
            
            all_models_data = (all_models_objs_data,all_model_result)
            
            best_model_obj,best_model_results  = self.find_best_model(models_object_data=all_models_objs_data,models_results_data=all_model_result) # type: ignore
            best_model_data = (best_model_obj,best_model_results)
            
            result = ModelTunerArtifacts(all_models_data=all_models_data,
                                         best_model_data=best_model_data,
                                         standard_scalar_object=scalar,
                                         smote_object=smote,
                                         pca_object=pca,
                                         svc_mlflow_dict=svc_mlflow_result_dict,
                                         gaussiannb_mlflow_dict=gaussiannb_mlflow_result_dict,
                                         randomforest_mlflow_dict=randomforest_mlflow_result_dict,
                                         xgbclassifier_mlflow_dict=xgbclassifier_mlflow_result_dict)
            
            logger.info(f"Models Artifacts: {result}")
            logger.info("Ended initialize model tuner process!")
            return result
            
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"initialize_model_tuner_process :: Status:Failed :: Error:{error_message}")
            raise error_message
                                        
                                                    