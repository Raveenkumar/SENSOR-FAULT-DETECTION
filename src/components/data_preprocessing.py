import pandas  as pd
import sys,os
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import PowerTransformer
from sklearn.impute import KNNImputer
from src.exception import SensorFaultException
from src.logger import logger
from src.entity.config_entity import PreprocessorConfig
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from src.utilities.utils import create_folder_using_file_path,save_obj,find_final_path
from src.entity.artifact_entity import PreprocessorArtifacts



class Preprocessor:
    def __init__(self,config:PreprocessorConfig, input_file:pd.DataFrame) -> None:
        self.input_input_file = input_file
        self.config = config
        
    def drop_unwanted_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """drop_unwanted_columns :Used for drop unwanted columns

        Args:
            df (pd.DataFrame): Input Dataframe

        Raises:
            error_message: Custom Exception

        Returns:
            pd.DataFrame: clean dataframe
        """
        try:
            dropped_columns = self.config.unwanted_columns_list
            df.drop(columns=dropped_columns, inplace=True)
            logger.info(f'Dropped columns :: Status: Success :: dropped_columns:{dropped_columns}')
            return df
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"Dropped columns :: Status: Failed :: dropped_columns:{dropped_columns} :: Error:{error_message}")
            raise error_message
        
    def drop_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """drop_duplicate_rows :Used for drop duplicate data in dataframe

        Args:
            df (pd.DataFrame): Input Dataframe

        Raises:
            error_message: Custom Exception

        Returns:
            pd.DataFrame: clean dataframe
        """
        try:
            before_shape = df.shape
            df.drop_duplicates(inplace=True)
            after_shape = df.shape
            no_of_dropped_rows = before_shape[0]-after_shape[0]
            logger.info(f'Dropped Duplicate rows :: Status: Success :: no_of_rows_dropped:{no_of_dropped_rows}')
            return df
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.error(msg=f"Dropped Duplicate rows :: Status: Failed :: Error:{error_message}")
            raise error_message
    
    class HandleZeroStdColumns(BaseEstimator, TransformerMixin):
        def __init__(self,config: PreprocessorConfig) -> None:
            """__init__ :Custom Transformer used for handle zero standard deviation columns
            """
            self.zero_std_columns =[]
            self.config = config

        def fit(self,X,y=None):
            try:
                self.zero_std_columns = [column for column in X.columns if X[column].std() == 0]
                if self.config.target_feature in self.zero_std_columns:
                    self.zero_std_columns.remove(self.config.target_feature)
                logger.info("DropZeroStdColumns  fitted successfully.")  

            except Exception as e:
                logger.error(f"An error occurred during fitting: {e}")
                raise e

            return self


        def transform(self, X, y=None):
            try:
                X = X.drop(columns=self.zero_std_columns)
                logger.info("DropZeroStdColumns columns transform successfully.")

            except Exception as e:
                logger.error(f"An error occurred during Transform: {e}")
                raise e
            
            return X 


        def fit_transform(self, X, y=None):
            try:
                # Fit and transform in one step
                transformed_data = self.fit(X, y).transform(X, y)
                logger.info("DropZeroStdColumns Fit and transform completed successfully.")
            
            except Exception as e:
                logger.error(f"An error occurred during fit_transform: {e}")
                raise e
            
            return transformed_data
        
    class HandleHighSkewColumns(BaseEstimator, TransformerMixin):
        """HandleHighSkewColumns :It is custom transformer used for handle high skew columns 
        """
        def __init__(self,config: PreprocessorConfig):
            self.skewed_columns =[]
            self.power_transformation = PowerTransformer()    
            self.config = config

        def fit(self,X,y=None):
            try:
                high_skew_columns = X.columns[(X.skew() < -1) | (X.skew() > 1)]
                self.skewed_columns = list(high_skew_columns)
                if self.config.target_feature in self.skewed_columns:
                    self.skewed_columns.remove(self.config.target_feature) 
                logger.info(f"Getting high skew columns : {self.skewed_columns}")

                self.power_transformation.fit(X[self.skewed_columns])
                logger.info("HandleHighSkewColumns PowerTransformer  fitted successfully.")  

            except Exception as e:
                logger.error(f"An error occurred during fitting: {e}")
                raise e

            return self


        def transform(self, X, y=None):
            try:
                X[self.skewed_columns] = self.power_transformation.transform(X[self.skewed_columns])
                logger.info("Handle high skew columns transform successfully")

            except Exception as e:
                logger.error(f"An error occurred during Transform: {e}")
                raise e
            
            return X 


        def fit_transform(self, X, y=None):
            try:
                # Fit and transform in one step
                transformed_data = self.fit(X, y).transform(X, y)
                logger.info("Handle high skew columns Fit and transform completed successfully.")
            
            except Exception as e:
                logger.error(f"An error occurred during fit_transform: {e}")
                raise e
            
            return transformed_data        
    
    class HandleNaNValues(BaseEstimator, TransformerMixin):
        """HandleNaNValues:It is custom Transformer used for handle nan values
        """
        def __init__(self):
            self.columns_to_drop = []
            self.knn_imputer = KNNImputer(n_neighbors=5, weights='uniform')

        def fit(self, X, y=None):
            try:
                # Determine which columns to drop based on training data
                self.columns_to_drop = X.columns[X.isnull().mean() * 100 > 50].tolist()
                logger.info(f"Columns to drop due to high NaN percentage: {self.columns_to_drop}")
                
                # Prepare data for imputation by dropping the columns
                X_to_impute = X.drop(columns=self.columns_to_drop, errors='ignore')
                
                # Fit the KNN imputer on the remaining data
                self.knn_imputer.fit(X_to_impute)
                logger.info("handle nan values KNN Imputer fitted successfully.")
            
            except Exception as e:
                logger.error(f"An error occurred during fitting: {e}")
                raise e
            
            return self

        def transform(self, X, y=None):
            try:
                # Drop columns that were determined during fit
                X = X.drop(columns=self.columns_to_drop, errors='ignore')
                # logger.info(f"handle nan values Applied column dropping. Remaining columns: {X.columns.tolist()}")
                
                # Apply KNN imputation using the fitted imputer
                imputed_data = self.knn_imputer.transform(X)
                result_df = pd.DataFrame(imputed_data, columns=X.columns)
                logger.info("handle nan values Data transformed using KNN Imputer.")
            
            except Exception as e:
                logger.error(f"An error occurred during transformation: {e}")
                raise e
            
            return result_df

        def fit_transform(self, X, y=None):
            try:
                # Fit and transform in one step
                transformed_data = self.fit(X, y).transform(X, y)
                logger.info("handle nan values Fit and transform completed successfully.")
            
            except Exception as e:
                logger.error(f"An error occurred during fit_transform handle nan values: {e}")
                raise e
            
            return transformed_data

    class OutlierHandler(BaseEstimator, TransformerMixin):
        """OutlierHandler :It is custom transformer handle outliers
        """
        def __init__(self,config: PreprocessorConfig):
            self.lower_limits = {}
            self.upper_limits = {}
            self.config = config
        
        def fit(self, X, y=None):
            # Calculate the lower and upper limits based on the training data
            try:
                for column in X.columns:
                    if column != self.config.target_feature:
                        lower_bound = X[column].quantile(self.config.lower_percentile)
                        upper_bound = X[column].quantile(self.config.upper_percentile)
                        IQR = upper_bound - lower_bound
                        self.lower_limits[column] = lower_bound - (IQR * self.config.iqr_multiplier)
                        self.upper_limits[column] = upper_bound + (IQR * self.config.iqr_multiplier)
                        

                logger.info(f"OutlierHandler Fitted successfully ")
                logger.info(f"Lower_limits:{self.lower_limits}")
                logger.info(f"Upper_limits:{self.upper_limits}")

            except Exception as e:
                logger.error(f"An error occurred during fitting: {e}")
                raise e
                        
            return self

        def transform(self, X, y=None):
            try:
                # Clip the values based on the calculated limits instead of removing rows
                for column in X.columns:
                    if column != PreprocessorConfig.target_feature:
                        X[column] = X[column].clip(lower=self.lower_limits[column], upper=self.upper_limits[column])


                logger.info(f"OutlierHandler Transformed successfully ")
                        
                        
            except Exception as e:
                logger.error(f"An error occurred during transform: {e}")
                raise e
            
            return X

        def fit_transform(self, X, y=None):
            try:
                # Fit and transform in one step
                transformed_data = self.fit(X, y).transform(X, y)
                logger.info("OutlierHandler Fit and transform completed successfully.")
            
            except Exception as e:
                logger.error(f"An error occurred during fit_transform: {e}")
                raise e
            
            return transformed_data
    
    def initialize_preprocessing(self):
        try:
            logger.info("started the initialize_preprocessing process!")
            # Define the FunctionTransformer for each function
            drop_unwanted_columns_ = FunctionTransformer(func=self.drop_unwanted_columns)
            drop_duplicate_rows_ = FunctionTransformer(func=self.drop_duplicate_rows)

            preprocessing_pipeline = Pipeline(
                [
                    ("drop_unwanted_columns", drop_unwanted_columns_),
                    ("drop_duplicate_rows", drop_duplicate_rows_),
                    ("drop_zero_std_columns", Preprocessor.HandleZeroStdColumns(config=self.config)),  
                    ("handle_nan_values", Preprocessor.HandleNaNValues()),           
                    ("handle_high_skew_columns", Preprocessor.HandleHighSkewColumns(config=self.config)),
                    ("handle_outlier", Preprocessor.OutlierHandler(config=self.config))
                ]
            )
            
            preprocessed_data = preprocessing_pipeline.fit_transform(self.input_input_file)
            
            # storing the preprocessing object
            # final_preprocessor_object_path = find_final_path(self.config.experiment_preprocessor_object_path,self.config.stable_preprocessor_object_path)
            final_preprocessor_object_path = self.config.preprocessor_object_path
            create_folder_using_file_path(file_path=final_preprocessor_object_path)
            save_obj(file_path=final_preprocessor_object_path,obj=preprocessing_pipeline)   
                
            
            result = PreprocessorArtifacts(preprocessed_data=preprocessed_data,preprocessed_object_path=final_preprocessor_object_path)   # type: ignore
            logger.info("Ended the initialize_preprocessing process!")
            return result
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"started the initialize_preprocessing Failed!:: Error:{error_message}")
            raise error_message