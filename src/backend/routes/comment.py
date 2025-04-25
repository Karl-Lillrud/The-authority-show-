from flask import Blueprint, request, jsonify, g
from backend.repository.comment_repository import CommentRepository

# Define Blueprint
comment_bp = Blueprint("comment_bp", __name__)

# Instantiate the Comment Repository
comment_repo = CommentRepository()

@comment_bp.route("/add_comment", methods=["POST"])
def add_comment():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    
    try:
        data = request.get_json()
        print("📩 Received Comment Data:", data)
        
        response, status_code = comment_repo.add_comment(g.user_id, data)
        return jsonify(response), status_code
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add comment: {str(e)}"}), 500

@comment_bp.route("/get_comments/<podtask_id>", methods=["GET"])
def get_comments(podtask_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    response, status_code = comment_repo.get_comments_by_podtask(g.user_id, podtask_id)
    return jsonify(response), status_code

@comment_bp.route("/delete_comment/<comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    response, status_code = comment_repo.delete_comment(g.user_id, comment_id)
    return jsonify(response), status_code

@comment_bp.route("/update_comment/<comment_id>", methods=["PUT"])
def update_comment(comment_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    
    try:
        data = request.get_json()
        response, status_code = comment_repo.update_comment(g.user_id, comment_id, data)
        return jsonify(response), status_code
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update comment: {str(e)}"}), 500
