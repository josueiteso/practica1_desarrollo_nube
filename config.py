import os

# AWS
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# RDS
DB_SECRET_ARN = os.environ["DB_SECRET_ARN"]
DB_ENDPOINT = os.environ["DB_ENDPOINT"]
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "polaroiddb")

# S3
PICTURES_BUCKET = os.environ["PICTURES_BUCKET"]
POLAROIDS_BUCKET = os.environ["POLAROIDS_BUCKET"]