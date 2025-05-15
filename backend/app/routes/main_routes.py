from flask import jsonify, send_file
from . import api_bp
import os

@api_bp.route('/', methods=['GET'])
def serve_frontend():
    """Serves the frontend index.html file."""
    return send_file(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'frontend', 'index.html')))

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    }), 200 