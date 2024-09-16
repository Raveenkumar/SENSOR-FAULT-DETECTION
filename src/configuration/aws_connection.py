import boto3
import os
from dotenv import load_dotenv
from pathlib import Path
from mypy_boto3_s3 import S3ServiceResource 
load_dotenv()


class S3Client:
    s3_client = None
    s3_resource = None # type: ignore
    def __init__(self):
        if S3Client.s3_client is None or S3Client.s3_resource is None:
            __access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            __secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            _region_name = os.getenv('AWS_REGION_NAME')

            if __access_key_id is None:
                raise Exception(f"Environment variable AWS_ACCESS_KEY_ID not set")
            
            if __secret_access_key is None:
                raise Exception(f"Environment variable AWS_SECRET_ACCESS_KEY not set")
            
            S3Client.s3_client = boto3.client('s3',
                                        aws_access_key_id=__access_key_id,
                                        aws_secret_access_key=__secret_access_key,
                                        region_name=_region_name
                                        )
            
            S3Client.s3_resource:S3ServiceResource = boto3.resource('s3',
                                        aws_access_key_id=__access_key_id,
                                        aws_secret_access_key=__secret_access_key,
                                        region_name=_region_name
                                        ) # type: ignore
            
            self.s3_resource =  S3Client.s3_resource
            self.s3_client = S3Client.s3_client  

