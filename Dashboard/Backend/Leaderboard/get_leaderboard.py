# backend/leaderboard/get_leaderboard.py
import json
import boto3
from middleware.auth import authenticate
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Authenticate the user
    user_id = authenticate(event)
    if not user_id:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Unauthorized'})
        }

    # Parse query parameters for pagination
    query_params = event.get('queryStringParameters') or {}
    limit = int(query_params.get('limit', 10))
    last_evaluated_key = query_params.get('lastKey')

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TeamMembers')

    try:
        # Scan the TeamMembers table with pagination
        scan_kwargs = {
            'Limit': limit
        }
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = json.loads(last_evaluated_key)

        response = table.scan(**scan_kwargs)
        team_members = response.get('Items', [])

        # Process data for the leaderboard
        leaderboard_data = []
        for member in team_members:
            leaderboard_data.append({
                'name': member['name'],
                'tasksCompleted': member.get('tasksCompleted', 0),
                'totalPoints': member.get('totalPoints', 0),
                'monthsWon': member.get('monthsWon', 0),
                'shadowGoal': member.get('shadowGoal', '0 / 0')
            })

        # Sort the leaderboard by totalPoints descending
        leaderboard_data.sort(key=lambda x: x['totalPoints'], reverse=True)

        # Assign medals based on ranking
        for idx, member in enumerate(leaderboard_data):
            if idx == 0:
                member['badge'] = '🥇'  # Gold medal
            elif idx == 1:
                member['badge'] = '🥈'  # Silver medal
            elif idx == 2:
                member['badge'] = '🥉'  # Bronze medal
            else:
                member['badge'] = '⚪'  # No medal

    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'leaderboard': leaderboard_data,
            'lastKey': json.dumps(response.get('LastEvaluatedKey')) if response.get('LastEvaluatedKey') else None
        })
    }

def get_badge(role):
    role = role.lower()
    if role == 'manager':
        return '🥇'
    elif role == 'coordinator':
        return '🥈'
    elif role == 'member':
        return '🥉'
    else:
        return '⚪'
    
 # backend/leaderboard/get_leaderboard.py

import json
import boto3
from middleware.auth import authenticate
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Authenticate the user
    user_id = authenticate(event)
    if not user_id:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Unauthorized'})
        }

    # Parse query parameters for pagination
    query_params = event.get('queryStringParameters') or {}
    limit = int(query_params.get('limit', 10))
    last_evaluated_key = query_params.get('lastKey')

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TeamMembers')

    try:
        # Scan the TeamMembers table with pagination
        scan_kwargs = {
            'Limit': limit
        }
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = json.loads(last_evaluated_key)

        response = table.scan(**scan_kwargs)
        team_members = response.get('Items', [])

        # Process data for the leaderboard
        leaderboard_data = []
        for member in team_members:
            leaderboard_data.append({
                'name': member['name'],
                'tasksCompleted': member.get('tasksCompleted', 0),
                'totalPoints': member.get('totalPoints', 0),
                'monthsWon': member.get('monthsWon', 0),
                'shadowGoal': member.get('shadowGoal', '0 / 0')
            })

        # Sort the leaderboard by totalPoints descending
        leaderboard_data.sort(key=lambda x: x['totalPoints'], reverse=True)

        # Assign medals based on ranking
        for idx, member in enumerate(leaderboard_data):
            if idx == 0:
                member['badge'] = '🥇'  # Gold medal
            elif idx == 1:
                member['badge'] = '🥈'  # Silver medal
            elif idx == 2:
                member['badge'] = '🥉'  # Bronze medal
            else:
                member['badge'] = '⚪'  # No medal

    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'leaderboard': leaderboard_data,
            'lastKey': json.dumps(response.get('LastEvaluatedKey')) if response.get('LastEvaluatedKey') else None
        })
    }
