"""
lee las credenciales de RDS desde Secrets Manager.
"""
import json
import boto3
from config import AWS_REGION, DB_SECRET_ARN

credentials: dict | None = None

def get_db_credentials() -> dict:
    # devuelve las credenciales de RDS
    global credentials

    if credentials is not None:
        return credentials

    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=DB_SECRET_ARN)
    secret = json.loads(response["SecretString"])

    credentials = {
        "username": secret["username"],
        "password": secret["password"],
    }
    return credentials