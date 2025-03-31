from flask import Blueprint, jsonify, render_template

listenerdashboard_bp = Blueprint("listenerdashboard_bp", __name__, url_prefix="/listener-dashboard")

@listenerdashboard_bp.route("/", methods=["GET"])
def listener_dashboard():
    """Render the Listener Intelligence Dashboard."""
    return render_template("listenerdashboard/listenerdashboard.html")

@listenerdashboard_bp.route("/api/engagement-metrics", methods=["GET"])
def get_engagement_metrics():
    # Mock data for engagement metrics
    data = {
        "dropOffPoints": [10, 20, 45],
        "relistens": 120,
        "shares": 50,
        "reviews": 30,
    }
    return jsonify(data)

@listenerdashboard_bp.route("/api/emotional-flow", methods=["GET"])
def get_emotional_flow():
    # Mock data for emotional flow
    data = {
        "episodes": [
            {"title": "Episode 1", "sentiment": [0.1, 0.5, -0.2]},
            {"title": "Episode 2", "sentiment": [0.3, 0.4, 0.2]},
        ]
    }
    return jsonify(data)

@listenerdashboard_bp.route("/api/cta-performance", methods=["GET"])
def get_cta_performance():
    # Mock data for CTA performance
    data = {
        "ctaClicks": 100,
        "conversionRate": 0.25,
    }
    return jsonify(data)

@listenerdashboard_bp.route("/api/superfan-identification", methods=["GET"])
def get_superfan_identification():
    # Mock data for superfans
    data = {
        "superfans": [
            {"name": "John Doe", "engagementScore": 95},
            {"name": "Jane Smith", "engagementScore": 90},
        ]
    }
    return jsonify(data)

@listenerdashboard_bp.route("/api/content-recommendations", methods=["GET"])
def get_content_recommendations():
    # Mock data for content recommendations
    data = {
        "recommendations": [
            {"title": "How to grow your audience", "category": "Marketing"},
            {"title": "Top 10 podcasting tools", "category": "Technology"},
        ]
    }
    return jsonify(data)