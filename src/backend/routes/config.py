from flask import Blueprint, jsonify
import os

config_bp = Blueprint("config_bp", __name__)


@config_bp.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({"API_BASE_URL": os.getenv("API_BASE_URL")})
