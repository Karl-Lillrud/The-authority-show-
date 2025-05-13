from flask import Blueprint, render_template
import logging  # Import logging

index_bp = Blueprint(
    'index_bp', 
    __name__,
    template_folder='../../frontend/templates',  # Relative path to the templates folder
    static_folder='../../frontend/static'      # Relative path to the static folder
)

logger = logging.getLogger(__name__)  # Get a logger instance

@index_bp.route('/')
@index_bp.route('/start')
def start_page():
    """
    Serves the main index page at the /start endpoint.
    """
    logger.info(f"Accessing /start route, attempting to render index/index.html")
    try:
        return render_template('index/index.html')
    except Exception as e:
        logger.error(f"Error rendering template for /start: {e}", exc_info=True)
        return "Error rendering page. Check logs.", 500

