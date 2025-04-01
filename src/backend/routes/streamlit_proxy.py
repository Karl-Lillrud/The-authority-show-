from flask import Blueprint, request, jsonify, Response
import requests

streamlit_proxy_bp = Blueprint("streamlit_proxy", __name__)

@streamlit_proxy_bp.route("/<path:path>", methods=["GET", "POST"])
def proxy_streamlit(path):
    try:
        url = f"http://localhost:8501/{path}"
        resp = requests.request(
            method=request.method, url=url, headers=request.headers, data=request.data
        )
        return Response(resp.content, resp.status_code, resp.raw.headers.items())
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Streamlit server is not running"}), 500
