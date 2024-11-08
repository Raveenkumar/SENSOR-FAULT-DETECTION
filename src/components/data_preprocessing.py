import pandas  as pd
import sys,os
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import PowerTransformer
from sklearn.impute import KNNImputer
from src.exception import SensorFaultException
from src.logger import logger
from src.entity.config_entity import PreprocessorConfig,BaseArtifactConfig
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from src.utilities.utils import create_folder_using_file_path,save_obj,save_json,copy_file
from src.entity.artifact_entity import PreprocessorArtifacts


preprocessing_results = {}
target_column = PreprocessorConfig.target_feature
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
            preprocessing_results["total_records"] = df.shape[0]
            preprocessing_results["total_columns"] = df.shape[1]
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
            preprocessing_results['no_of_duplicate_rows']=no_of_dropped_rows
            logger.info(f'Dropped Duplicate rows :: Status: Success :: no_of_rows_dropped:{no_of_dropped_rows}')
            create_folder_using_file_path(self.config.non_duplicate_data_clear_df_path)
            df.to_csv(self.config.non_duplicate_data_clear_df_path,index=False)
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
                preprocessing_results['zero_std_columns'] = int(len(self.zero_std_columns))
                if self.config.target_feature in self.zero_std_columns:
                    self.zero_std_columns.remove(self.config.target_feature)
                logger.info(f"DropZeroStdColumns  fitted successfully.")  

            except Exception as e:
                logger.error(f"An error occurred during fitting: {e}")
                raise e

            return self


        def transform(self, X, y=None):
            try:
                X = X.drop(columns=self.zero_std_columns)
                logger.info(f"DropZeroStdColumns columns transform successfully :: zero_std_columns:{self.zero_std_columns}")

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
                preprocessing_results['highskew_columns']= int(len(self.skewed_columns))
                if self.config.target_feature in self.skewed_columns:
                    self.skewed_columns.remove(self.config.target_feature) 
                
                self.power_transformation.fit(X[self.skewed_columns])
                logger.info("HandleHighSkewColumns PowerTransformer  fitted successfully.")  

            except Exception as e:
                logger.error(f"An error occurred during fitting: {e}")
                raise e

            return self


        def transform(self, X, y=None):
            try:
                X[self.skewed_columns] = self.power_transformation.transform(X[self.skewed_columns])
                logger.info(f"Handle high skew columns transform successfully :: total_skew_columns:{len(self.skewed_columns)} :: skew_columns:{self.skewed_columns}  ")
                
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
        def __init__(self, config: PreprocessorConfig):
            self.columns_to_drop = []
            self.knn_imputer = KNNImputer(n_neighbors=5, weights='uniform')
            self.config = config 

        def fit(self, X, y=None):
            try:
                # Determine which columns to drop based on training data
                self.columns_to_drop = X.columns[X.isnull().mean() * 100 > 50].tolist()
                self.nan_imputed_columns = X.columns[X.isnull().mean() * 100 < 50].tolist()
                preprocessing_results['hight_nan_columns_dropped'] = int(len(self.columns_to_drop))
                preprocessing_results['Nan_imputed_columns'] = int(len(self.nan_imputed_columns))
                
                
                # Prepare data for imputation by dropping the columns
                X_to_impute = X.drop(columns=self.columns_to_drop, errors='ignore')

                X_to_impute = X_to_impute.drop(columns=[self.config.target_feature])
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
                logger.info(f"Columns to drop due to high NaN percentage: {self.columns_to_drop}")
                # logger.info(f"handle nan values Applied column dropping. Remaining columns: {X.columns.tolist()}")
                if self.config.target_feature in X.columns:
                    X_to_impute = X.drop(columns=[self.config.target_feature])
                    imputed_data = self.knn_imputer.transform(X_to_impute)
                    X_imputed = pd.DataFrame(imputed_data, columns=X_to_impute.columns)
                    
                     # Concatenate the target column back to the DataFrame
                    X_imputed[self.config.target_feature] = X[self.config.target_feature].values
                else:
                    imputed_data = self.knn_imputer.transform(X)
                    X_imputed = pd.DataFrame(imputed_data, columns=X.columns)
                
                logger.info(f"handle nan values imputed using KNN Imputer. total_imputed_columns:{len(self.nan_imputed_columns)} :: columns_list:{self.nan_imputed_columns}")
            
            except Exception as e:
                logger.error(f"An error occurred during transformation: {e}")
                raise e
            
            return X_imputed

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
                # Clip the values based on the calculated limits
                count_clipped_columns = 0  # Counter for how many columns had outliers clipped
                clipped_columns = []       # List to track clipped column names

                for column in X.columns:
                    if column != self.config.target_feature:
                        original_data = X[column].copy()  # Backup original data to compare later
                        X[column] = X[column].clip(lower=self.lower_limits[column], upper=self.upper_limits[column])

                        # Check if the column had any values clipped
                        if not original_data.equals(X[column]):
                            count_clipped_columns += 1
                            clipped_columns.append(column)

                preprocessing_results["outlier_handled_columns"] = count_clipped_columns
                # preprocessing_results["clipped_columns"] = clipped_columns  # Optional: Store names of clipped columns
                
                logger.info(f"OutlierHandler transformed successfully :: total_columns_clipped: {count_clipped_columns} :: clipped columns: {clipped_columns}")

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
                    ("drop_duplicate_rows", drop_duplicate_rows_),
                    ("drop_unwanted_columns", drop_unwanted_columns_),
                    ("drop_zero_std_columns", Preprocessor.HandleZeroStdColumns(config=self.config)),  
                    ("handle_nan_values", Preprocessor.HandleNaNValues(config=self.config)),           
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
            
            # save the results into json for plotting
            logger.info('initialize_preprocessing :: create folder for preprocessing json file if not exist')
            create_folder_using_file_path(self.config.preprocessor_json_file_path)
            save_json(self.config.preprocessor_json_file_path,preprocessing_results)
            #copy file to data dir
            copy_file(src_file_path=self.config.preprocessor_json_file_path,
                      dst_folder_path=self.config.dashboard_preprocessor_json_file_path)
            
            logger.info("Ended the initialize_preprocessing process!")
            return result
        
        except Exception as e:
            error_message = SensorFaultException(error_message=str(e),error_detail=sys)
            logger.info(f"started the initialize_preprocessing Failed!:: Error:{error_message}")
            raise error_message