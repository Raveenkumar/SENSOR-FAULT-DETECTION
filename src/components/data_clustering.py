import pandas  as pd
import sys,os
from numpy import ndarray
from typing import Any
from kneed import KneeLocator
from sklearn.cluster import KMeans
from src.exception import SensorFaultException
from src.logger import logger
from src.entity.config_entity import ClusterConfig
from src.entity.artifact_entity import ClusterArtifacts
from sklearn.metrics import silhouette_score
from src.utilities.utils import save_obj,create_folder_using_file_path,find_final_path

class Clusters:
    def __init__(self,config:ClusterConfig,input_file:pd.DataFrame,target_feature_name:str) -> None:
        self.config = config
        self.input_file = input_file
        self.target_feature_name = target_feature_name
    
    def find_optimal_clusters(self,X:pd.DataFrame) -> None | Any:
        """find_optimal_clusters Used for provide optimal number clusters 

        Args:
            X (pd.DataFrame): dataframe without target variable

        Raises:
            error_message: Custom Exception

        Returns:
            None | Any: optimal_clusters
        """
        try:
            inertia = []
            for n_clusters in range(1, 11):
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                kmeans.fit(X)
                inertia.append(kmeans.inertia_)
            
            kneedlocator = KneeLocator(range(1, 11), inertia, curve='convex', direction='decreasing')
            optimal_clusters = kneedlocator.elbow    
            logger.info(f"find_optimal_clusters :: Status:Success :: optimal_clusters:{optimal_clusters}")
            return optimal_clusters
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"find_optimal_clusters :: Status:Failed ::  :: Error:{error_message}")
            raise error_message
    
    def find_cluster_labels(self, X:pd.DataFrame, optimal_clusters) :
        """find_cluster_labels:Used for find cluster labels for dataset

        Args:
            X (pd.DataFrame): dataframe without target variable
            optimal_clusters: optimal_cluster number

        Raises:
            error_message: Custom Exception

        Returns:
            ndarray[Any, Any]: 2D array of cluster labels
        """
        try:
            kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(X)
            # final_cluster_object_path = find_final_path(self.config.experiment_cluster_object_path,self.config.stable_cluster_object_path)
            final_cluster_object_path = self.config.cluster_object_path
            create_folder_using_file_path(file_path=final_cluster_object_path)
            save_obj(file_path=final_cluster_object_path,obj=kmeans)
            
            logger.info(f"n_clusters :: Status:Success ")
            return cluster_labels, final_cluster_object_path
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"n_clusters :: Status:Failed ::  :: Error:{error_message}")
            raise error_message
        
    
    def initialize_clusters(self) -> ClusterArtifacts:
        try:
            final_file = self.input_file.copy()
            logger.info("Started initialize_clusters Process!")
            X = final_file.drop(columns =[self.target_feature_name])
            
            optimal_clusters = self.find_optimal_clusters(X)
            
            cluster_labels,cluster_obj_path = self.find_cluster_labels(X, optimal_clusters=optimal_clusters)
            
            final_file[self.config.cluster_column_name] = cluster_labels
            
            silhouette_score_ = silhouette_score(X,cluster_labels)
            
            result = ClusterArtifacts(final_file=final_file,
                                     cluster_object_path = cluster_obj_path,
                                     silhouette_score_ = silhouette_score_) # type: ignore
            
            logger.info(f'Optimal clusters:{optimal_clusters} :: silhouette_score:{silhouette_score_} :: cluster_object_path:{cluster_obj_path}')
            logger.info(msg="Ended initialize_clusters Process!")
            return result
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"initialize_clusters :: Status:Failed ::  :: Error:{error_message}")
            raise error_message
            