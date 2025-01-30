# backend/guest_management/create_guest.py

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
    first_name = body.get('firstName')
    last_name = body.get('lastName')
    email = body.get('email')
    bio = body.get('bio')
    social_media = body.get('socialMedia', {})
    profile_photo = body.get('profilePhoto')
    areas_of_interest = body.get('areasOfInterest', [])
    recommended_guests = body.get('recommendedGuests', {})
    future_opportunities = body.get('futureOpportunities')
    general_notes = body.get('generalNotes')
    company = body.get('company')
    contact_preferences = body.get('contactPreferences')

    if not first_name or not last_name or not email or not bio or not profile_photo or not areas_of_interest:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing required fields'})
        }

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Guests')

    guest_id = str(uuid.uuid4())
    timestamp = int(time.time())

    try:
        # Create new guest
        table.put_item(
            Item={
                'guestId': guest_id,
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'bio': bio,
                'socialMedia': social_media,
                'episodeHistory': [],
                'contactPreferences': contact_preferences,
                'profilePhoto': profile_photo,
                'areasOfInterest': areas_of_interest,
                'recommendedGuests': recommended_guests,
                'futureOpportunities': future_opportunities,
                'generalNotes': general_notes,
                'company': company,
                'createdAt': timestamp,
                'updatedAt': timestamp
            },
            ConditionExpression='attribute_not_exists(email)'
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'Guest with this email already exists'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

    return {
        'statusCode': 201,
        'body': json.dumps({'message': 'Guest created successfully', 'guestId': guest_id})
    }