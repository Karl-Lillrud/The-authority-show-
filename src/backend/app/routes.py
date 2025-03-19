except Exception as e:
    # Ensure the error response is JSON-serializable
    return jsonify({"error": str(e)}), 500