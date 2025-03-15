from flask import (
    Blueprint,
    render_template,
    g,
    redirect,
    url_for,
    session,
    request,
    jsonify,
    current_app,
)
from backend.database.mongo_connection import collection
import requests
import xml.etree.ElementTree as ET
import urllib.request

podprofile_bp = Blueprint("podprofile_bp", __name__)


@podprofile_bp.route("/podprofile", methods=["GET"])
def podprofile():
    if not hasattr(g, "user_id") or not g.user_id:
        return redirect(url_for("signin"))

    # Fetch the user's email using the /get_email endpoint
    try:
        response = requests.get(
            url_for("register_bp.get_email", _external=True), cookies=request.cookies
        )
        response.raise_for_status()
        user_email = response.json().get("email")
        if not user_email:
            return redirect(url_for("signin"))
    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching email: {e}")
        return redirect(url_for("signin"))

    session["user_email"] = user_email  # Store the email in the session
    return render_template("podprofile/podprofile.html", user_email=user_email)


@podprofile_bp.route("/save_podprofile", methods=["POST"])
def save_podprofile():
    try:
        data = request.json
        user_email = session.get("user_email", "")

        # Save to User collection
        user_data = {
            "email": user_email,
            "podName": data.get("podName"),
            "podRss": data.get("podRss"),
            "imageUrl": data.get("imageUrl"),
            "description": data.get("description"),
            "socialMedia": data.get("socialMedia", []),
            "category": data.get("category"),
            "author": data.get("author"),
        }
        collection["User"].insert_one(user_data)

        # Save to Podcast collection
        podcast_data = {
            "UserID": user_email,
            "Podname": data.get("podName"),
            "RSSFeed": data.get("podRss"),
            "imageUrl": data.get("imageUrl"),
            "description": data.get("description"),
            "socialMedia": data.get("socialMedia", []),
            "category": data.get("category"),
            "author": data.get("author"),
        }
        collection["Podcast"].insert_one(podcast_data)

        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"Error saving podprofile: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@podprofile_bp.route("/post_podcast_data", methods=["POST"])
def post_podcast_data():
    try:
        data = request.json
        pod_name = data.get("podName")
        pod_rss = data.get("podRss")
        image_url = data.get("imageUrl")
        description = data.get("description")
        social_media = data.get("socialMedia", [])
        category = data.get("category")
        author = data.get("author")
        episodes = data.get("episodes", [])  # Get episodes data
        user_email = session.get("user_email", "")

        if not pod_name or not pod_rss:
            return jsonify({"error": "Missing podcast name or RSS feed"}), 400

        # Save podcast data to the database
        podcast_data = {
            "user_email": user_email,
            "podName": pod_name,
            "podRss": pod_rss,
            "imageUrl": image_url,
            "description": description,
            "socialMedia": social_media,
            "category": category,
            "author": author,
            "episodes": episodes,  # Store episodes data
        }
        collection["Podcasts"].insert_one(podcast_data)

        return jsonify({"redirectUrl": "/podprofile"}), 200
    except Exception as e:
        current_app.logger.error(f"Error posting podcast data: {e}")
        return jsonify({"error": str(e)}), 500


@podprofile_bp.route("/fetch_rss", methods=["GET"])
def fetch_rss():
    """Server-side RSS feed fetching for clients that might have CORS issues"""
    rss_url = request.args.get("url")
    if not rss_url:
        return jsonify({"error": "No RSS URL provided"}), 400

    try:
        # Fetch the RSS feed
        req = urllib.request.Request(
            rss_url, headers={"User-Agent": "Mozilla/5.0 (PodManager.ai RSS Parser)"}
        )
        with urllib.request.urlopen(req) as response:
            rss_content = response.read()

        # Parse the XML
        root = ET.fromstring(rss_content)

        # Find the channel element
        channel = root.find("channel")
        if channel is None:
            return jsonify({"error": "Invalid RSS feed format"}), 400

        # Extract basic podcast info
        title_elem = channel.find("title")
        title = title_elem.text if title_elem is not None else ""

        description_elem = channel.find("description")
        description = description_elem.text if description_elem is not None else ""

        # Find image URL
        image_url = ""
        image_elem = channel.find(".//image/url")
        if image_elem is not None:
            image_url = image_elem.text

        # Find iTunes image if regular image not found
        if not image_url:
            ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
            itunes_image = channel.find(".//itunes:image", ns)
            if itunes_image is not None:
                image_url = itunes_image.get("href", "")

        # Extract episodes
        items = channel.findall("item")
        episodes = []

        for item in items:
            episode = {}

            # Basic episode info
            title_elem = item.find("title")
            episode["title"] = title_elem.text if title_elem is not None else ""

            description_elem = item.find("description")
            episode["description"] = (
                description_elem.text if description_elem is not None else ""
            )

            pubDate_elem = item.find("pubDate")
            episode["pubDate"] = pubDate_elem.text if pubDate_elem is not None else ""

            # Find enclosure (audio file)
            enclosure = item.find("enclosure")
            if enclosure is not None:
                episode["audio"] = {
                    "url": enclosure.get("url", ""),
                    "type": enclosure.get("type", ""),
                    "length": enclosure.get("length", ""),
                }

            episodes.append(episode)

        return jsonify(
            {
                "title": title,
                "description": description,
                "imageUrl": image_url,
                "episodes": episodes[:10],  # Limit to first 10 episodes
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error fetching RSS feed: {e}")
        return jsonify({"error": f"Error fetching RSS feed: {str(e)}"}), 500
