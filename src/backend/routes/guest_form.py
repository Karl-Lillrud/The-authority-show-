from flask import Blueprint, request, jsonify, render_template

guest_form_bp = Blueprint('guest_form', __name__)

@guest_form_bp.route('/guest-form', methods=['POST', 'GET'])
def guest_form():
    if request.method == 'POST':
        data = request.get_json()
        # Process the form data here
        # For example, save it to the database or send an email
        return jsonify({"message": "Guest form submitted successfully"}), 200
    elif request.method == 'GET':
        return render_template('guest-form/guest-form.html')  # Render the HTML template
