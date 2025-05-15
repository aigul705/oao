from flask import jsonify
from . import api_bp

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    }), 200 