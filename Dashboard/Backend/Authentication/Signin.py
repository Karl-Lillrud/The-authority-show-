# backend/authentication/signin.py

import json
import boto3
import jwt
import time
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Parse the request body
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')

    if not email or not password:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing email or password'})
        }

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

    try:
        # Query user by email
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('email').eq(email)
        )
        items = response.get('Items', [])
        if not items:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid credentials'})
            }

        user = items[0]
        stored_password = user.get('password')

        # Verify password (assuming frontend hashes it)
        if password != stored_password:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid credentials'})
            }

        # Generate JWT token
        secret = get_jwt_secret()
        token = jwt.encode({
            'userId': user['userId'],
            'email': user['email'],
            'role': user['role'],
            'exp': time.time() + 3600  # Token expires in 1 hour
        }, secret, algorithm='HS256')

    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'token': token})
    }

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