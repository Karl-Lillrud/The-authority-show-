from flask import Blueprint, request, jsonify
from backend.utils.translation_utils import translation_service
from backend.utils.translation_cache import translation_cache
from backend.utils.content_collector import content_collector
from functools import wraps
from flask import session

translation_bp = Blueprint('translation', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@translation_bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    """
    Translate text to target language
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    text = data.get('text')
    target_language = data.get('target_language')
    source_language = data.get('source_language')
    
    if not text or not target_language:
        return jsonify({"error": "Missing required fields: text and target_language"}), 400
    
    result = translation_service.translate_text(text, target_language, source_language)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result)

@translation_bp.route('/translate-app', methods=['POST'])
@login_required
def translate_app():
    """
    Translate all app content to target language
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    content = data.get('content')
    target_language = data.get('target_language')
    
    if not content or not target_language:
        return jsonify({"error": "Missing required fields: content and target_language"}), 400
    
    if not isinstance(content, dict):
        return jsonify({"error": "Content must be a dictionary"}), 400
    
    result = translation_service.translate_app_content(content, target_language)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify({"translated_content": result})

@translation_bp.route('/collect-and-translate', methods=['POST'])
@login_required
def collect_and_translate():
    """
    Collect all app content and translate it to target language
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    target_language = data.get('target_language')
    
    if not target_language:
        return jsonify({"error": "Missing required field: target_language"}), 400
    
    result = translation_service.collect_and_translate(target_language)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify({"translated_content": result})

@translation_bp.route('/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """
    Clear translation cache
    """
    data = request.get_json()
    language = data.get('language') if data else None
    
    translation_cache.clear_cache(language)
    
    return jsonify({"message": "Cache cleared successfully"})

@translation_bp.route('/detect-language', methods=['GET'])
@login_required
def detect_language():
    """
    Detect user's preferred language from browser
    """
    accept_language = request.headers.get('Accept-Language')
    detected_language = translation_service.detect_browser_language(accept_language)
    
    return jsonify({
        "detected_language": detected_language,
        "language_name": translation_service.supported_languages[detected_language]
    })

@translation_bp.route('/languages', methods=['GET'])
@login_required
def get_supported_languages():
    """
    Get list of supported languages
    """
    languages = translation_service.get_supported_languages()
    return jsonify({"languages": languages}) 