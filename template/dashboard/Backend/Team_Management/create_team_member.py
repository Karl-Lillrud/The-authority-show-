# backend/team_management/create_team_member.py

import json
import boto3
import uuid
import time
from botocore.exceptions import ClientError
from middleware.auth import authenticate

def lambda_handler(event, context):
    # Authenticate the user
    user_id = authenticate(event)
    if not user_id:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Unauthorized'})
        }

    # Parse the request body
    body = json.loads(event['body'])
    user_id = body.get('userId')
    role = body.get('role', 'Member')  # Default role
    name = body.get('name')

    if not user_id or not name:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing required fields'})
        }

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    team_members_table = dynamodb.Table('TeamMembers')
    users_table = dynamodb.Table('Users')

    timestamp = int(time.time())

    try:
        # Verify that the user exists
        user_response = users_table.get_item(
            Key={'userId': user_id},
            ProjectionExpression='userId, name, role'
        )
        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'User not found'})
            }

        # Create new team member
        team_member_id = str(uuid.uuid4())
        team_members_table.put_item(
            Item={
                'teamMemberId': team_member_id,
                'userId': user_id,
                'role': role,
                'name': name,
                'tasksCompleted': 0,
                'totalPoints': 0,
                'monthsWon': 0,
                'shadowGoal': '0 / 0',
                'createdAt': timestamp,
                'updatedAt': timestamp
            },
            ConditionExpression='attribute_not_exists(userId)'
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'Team member already exists'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

    return {
        'statusCode': 201,
        'body': json.dumps({'message': 'Team member created successfully', 'teamMemberId': team_member_id})
    }
