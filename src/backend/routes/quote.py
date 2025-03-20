from flask import Blueprint, request, jsonify
from backend.services.quote_service import extract_quotes_from_transcript

# Define Blueprint
quote_bp = Blueprint("quote_bp", __name__)

@quote_bp.route("/generate_quote", methods=["POST"])
def generate_quote():
    try:
        data = request.get_json()
        text = data.get("text", "")
        num_quotes = data.get("num_quotes", 3)  # Default to 3 quotes
        
        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Extract multiple quotes
        quotes = extract_quotes_from_transcript(text, num_quotes)
        
        return jsonify({
            "quotes": quotes,
            "count": len(quotes)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@quote_bp.route("/generate_single_quote", methods=["POST"])
def generate_single_quote():
    try:
        data = request.get_json()
        text = data.get("text", "")
        
        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Extract just one quote
        quotes = extract_quotes_from_transcript(text, 1)
        quote = quotes[0] if quotes else "No meaningful quote found."
        
        return jsonify({"quote": quote}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500