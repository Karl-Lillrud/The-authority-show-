@app.route('/register-podcast', methods=['POST'])
@jwt_required()
def register_podcast():
    # Get the current logged-in user ID
    current_user_id = get_jwt_identity()

    # Get the podcast name from the request data
    data = request.get_json()
    podcast_name = data.get('name')

    if not podcast_name:
        return jsonify({"message": "Podcast name is required."}), 400

    # Retrieve the user from the database
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found."}), 404

    # Update the user's podcast name
    user.podcast_name = podcast_name
    db.session.commit()

    return jsonify({"message": "Podcast registered successfully!"}), 200