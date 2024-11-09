# src/logger/__init__.py
import os
import sys
import logging
import time
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from src.entity.config_entity import LogValidationConfig

# Load environment variables from .env file
load_dotenv()

# Log File path
local_log_file_path = LogValidationConfig.log_file_path

# Get AWS configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
LOG_GROUP_NAME = "SensorLogGroup"    
LOG_STREAM_NAME = "SensorLogStream" 

# Set up CloudWatch client with credentials from environment variables
cloudwatch_logs = boto3.client(
    "logs",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Define a custom CloudWatch handler
class CloudWatchHandler(logging.Handler):
    def emit(self, record):
        log_event = {
            'logGroupName': LOG_GROUP_NAME,
            'logStreamName': LOG_STREAM_NAME,
            'logEvents': [
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': self.format(record)
                }
            ]
        }
        try:
            # Get the sequence token for CloudWatch
            sequence_token = self.get_sequence_token()
            if sequence_token:
                log_event['sequenceToken'] = sequence_token

            # Send log event to CloudWatch
            cloudwatch_logs.put_log_events(**log_event)
        except ClientError as e:
            print(f"Error sending logs to CloudWatch: {e}")

    def get_sequence_token(self):
        # Retrieve the sequence token for the log stream
        response = cloudwatch_logs.describe_log_streams(
            logGroupName=LOG_GROUP_NAME, logStreamNamePrefix=LOG_STREAM_NAME
        )
        streams = response.get("logStreams", [])
        if streams and "uploadSequenceToken" in streams[0]:
            return streams[0]["uploadSequenceToken"]
        return None

# Initialize logger with CloudWatch handler
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s: %(levelname)s: %(module)s: %(message)s]",
    handlers=[
        logging.StreamHandler(sys.stdout),   # Logs to console
        CloudWatchHandler(),                  # Logs to CloudWatch
        logging.FileHandler(local_log_file_path)       # Logs to a local file
    ]
)

# Logger instance
logger = logging.getLogger("sensor_fault_detection")
