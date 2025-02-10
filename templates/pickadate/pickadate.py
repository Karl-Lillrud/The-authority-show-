import os
import uuid
from flask import request, jsonify
from azure.cosmos import CosmosClient, PartitionKey
from werkzeug.utils import secure_filename

# Cosmos DB Configuration
COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_KEY')
DATABASE_NAME = 'PodcastDB'
CONTAINER_NAME = 'Bookings'

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(DATABASE_NAME)
container = database.create_container_if_not_exists(id=CONTAINER_NAME, partition_key=PartitionKey(path='/email'))

def book():
    try:
        guest_name = request.form.get('guestName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        social_media = request.form.get('socialMedia')
        podcast_name = request.form.get('podcastName')
        preferred_time = request.form.get('preferredTime')
        meeting_preferences = request.form.get('meetingPreferences')
        file_url = None

        if 'upload' in request.files:
            file = request.files['upload']
            if file.filename != '':
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                filepath = os.path.join('uploads/', filename)
                file.save(filepath)
                file_url = filepath

        booking_id = str(uuid.uuid4())
        item = {
            'id': booking_id,
            'guestName': guest_name,
            'email': email,
            'phone': phone,
            'socialMedia': social_media,
            'podcastName': podcast_name,
            'preferredTime': preferred_time,
            'meetingPreferences': meeting_preferences,
            'fileUrl': file_url,
            'createdAt': str(uuid.uuid1())
        }

        container.create_item(body=item)
        return jsonify({'message': 'Booking Successful', 'bookingId': booking_id}), 201
    except Exception as e:
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500

def get_bookings():
    try:
        bookings = list(container.read_all_items())
        return jsonify(bookings), 200
    except Exception as e:
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500