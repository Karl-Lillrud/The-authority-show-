# backend/middleware/authorization.py

import json
import jwt
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    token = None
    if 'authorizationToken' in event and event['authorizationToken']:
        auth_header = event['authorizationToken']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

    if not token:
        return generate_policy('Deny', event['methodArn'])

    try:
        secret = get_jwt_secret()
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        user_id = decoded.get('userId')
        role = decoded.get('role')

        if not user_id or not role:
            return generate_policy('Deny', event['methodArn'])

        # Allow access
        return generate_policy('Allow', event['methodArn'])

    except jwt.ExpiredSignatureError:
        return generate_policy('Deny', event['methodArn'])
    except jwt.InvalidTokenError:
        return generate_policy('Deny', event['methodArn'])
    except ClientError:
        return generate_policy('Deny', event['methodArn'])

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

def generate_policy(effect, resource):
    auth_response = {}
    auth_response['principalId'] = 'user'  # Can be set to user_id if available
    if effect and resource:
        policy_document = {}
        policy_document['Version'] = '2012-10-17'
        policy_document['Statement'] = []
        statement = {}
        statement['Action'] = 'execute-api:Invoke'
        statement['Effect'] = effect
        statement['Resource'] = resource
        policy_document['Statement'].append(statement)
        auth_response['policyDocument'] = policy_document
    return auth_response

