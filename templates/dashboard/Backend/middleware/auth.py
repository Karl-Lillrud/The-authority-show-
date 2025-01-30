# backend/middleware/auth.py

import jwt
import boto3
import json
from botocore.exceptions import ClientError

def get_jwt_secret():
    secret_name = "TeamLeaderboardDashboard/JWTSecret"
    region_name = "eu-north-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return secret

def authenticate(event):
    token = None
    if 'headers' in event and 'Authorization' in event['headers']:
        auth_header = event['headers']['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

    if not token:
        return None

    try:
        secret = get_jwt_secret()
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        return decoded.get('userId')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except ClientError:
        return None