# backend/authentication/signup.py

import json
import boto3
import uuid
import time
import jwt
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Parse the request body
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')  # Ensure this is hashed on the frontend or backend
    name = body.get('name')
    role = body.get('role', 'Team Member')  # Default role

    if not email or not password or not name:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing required fields'})
        }

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

    user_id = str(uuid.uuid4())
    timestamp = int(time.time())

    try:
        # Check if user already exists
        response = table.get_item(
            Key={'userId': user_id},
            ProjectionExpression='userId'
        )
        if 'Item' in response:
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'User already exists'})
            }

        # Create new user
        table.put_item(
            Item={
                'userId': user_id,
                'email': email,
                'password': password,  # Replace with hashed password
                'name': name,
                'role': role,
                'createdAt': timestamp,
                'updatedAt': timestamp
            },
            ConditionExpression='attribute_not_exists(email)'
        )

        # Optionally, create a TeamMember entry
        team_members_table = dynamodb.Table('TeamMembers')
        team_members_table.put_item(
            Item={
                'teamMemberId': str(uuid.uuid4()),
                'userId': user_id,
                'role': role,
                'name': name,
                'tasksCompleted': 0,
                'totalPoints': 0,
                'monthsWon': 0,
                'shadowGoal': '0 / 0',
                'createdAt': timestamp,
                'updatedAt': timestamp
            }
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'User with this email already exists'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

    return {
        'statusCode': 201,
        'body': json.dumps({'message': 'User created successfully'})
    }