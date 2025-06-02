from utils.logger_utils import logger

import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

load_dotenv()


class S3Utils:
    def __init__(self, bucket_name=None):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        self.bucket = bucket_name

    def upload_fileobj_to_s3(self, fileobj, filename):
        try:
            # Upload the file
            self.s3.upload_fileobj(fileobj, self.bucket, filename)
            logger.info(f"File uploaded successfully to {self.bucket}/{filename}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                logger.error(f"The bucket '{self.bucket}' does not exist.")
            else:
                logger.error(f"An error occurred: {e}")
        except (NoCredentialsError, PartialCredentialsError):
            logger.error(
                f"AWS credentials are missing or incomplete. Make sure your credentials are properly configured."
            )

    def upload_file_to_s3(self, local_path, filename):
        try:
            # Upload the file
            self.s3.upload_file(local_path, self.bucket, filename)
            logger.info(f"File uploaded successfully to {self.bucket}/{filename}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                logger.error(f"The bucket '{self.bucket}' does not exist.")
            else:
                logger.error(f"An error occurred: {e}")
            raise ClientError
        except (NoCredentialsError, PartialCredentialsError):
            logger.error(
                f"AWS credentials are missing or incomplete. Make sure your credentials are properly configured."
            )
            raise NoCredentialsError

    def fetch_file_from_s3(self, key):
        try:
            temp_file = key.split("/")[-1]
            self.s3.download_file(self.bucket, key, temp_file)
            logger.info(f"Downloaded {key} from S3")
            return temp_file
        except ClientError as error:
            if error.response["Error"]["Code"] == "404":
                logger.error("File not found in S3: %s", key)
                raise FileNotFoundError("File not found in S3: %s", key)
            else:
                logger.error("Error reading data from S3: %s", error)
            return None
    
    def upload_images_to_s3(self, external_id):
        local_folder = f"output/{external_id}/images"
        s3_prefix = f"repository/disclosure_pdf_extract/{external_id}/images/"
        for root, dirs, files in os.walk(local_folder):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_folder)
                s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")  # For Windows compatibility

                self.upload_file_to_s3(local_path, s3_key)