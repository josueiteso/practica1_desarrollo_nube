"""
almacenamiento con s3
"""
import boto3
from config import AWS_REGION, PICTURES_BUCKET, POLAROIDS_BUCKET

s3 = boto3.client("s3", region_name=AWS_REGION)

def save_original(key: str, data: bytes) -> str:
    s3.put_object(Bucket=PICTURES_BUCKET, Key=key, Body=data, ContentType="image/jpeg")
    return key

def save_polaroid(key: str, data: bytes) -> str:
    s3.put_object(Bucket=POLAROIDS_BUCKET, Key=key, Body=data, ContentType="image/jpeg")
    return key

def read_polaroid(key: str) -> bytes:
    response = s3.get_object(Bucket=POLAROIDS_BUCKET, Key=key)
    return response["Body"].read()