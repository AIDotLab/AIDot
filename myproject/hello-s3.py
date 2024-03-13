import os
from dotenv import load_dotenv
import boto3

load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_REGION = os.getenv("AWS_S3_BUCKET_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

def s3_connection():
    try:
        s3 = boto3.client(
            service_name='s3',
            region_name=AWS_S3_BUCKET_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
    except Exception as e:
        print(e)
        exit(ERROR_S3_CONNECTION_FAILED)
    else:
        print("s3 bucket connected!")
        return s3

if __name__ == '__main__':
    s3 = s3_connection()

    try:
        s3.upload_file("uploads/ori.jpg", AWS_S3_BUCKET_NAME, "uploads/ori.jpg")
    except Exception as e:
        print(e)

    try:
        s3.download_file(AWS_S3_BUCKET_NAME, "uploads/ori.jpg", "uploads/ori2.jpg")
    except Exception as e:
        print(e)
