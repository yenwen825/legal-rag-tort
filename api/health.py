from flask import Blueprint, jsonify
from models.database import get_db_stats
from services.vector_service import get_vector_cache
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    try:
        db_stats = get_db_stats()
        ids, _ = get_vector_cache()
        return jsonify({
            'status': 'ok',
            'database': db_stats,
            'vector_cache': {
                'status': 'loaded',
                'vector_count': len(ids),
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503
