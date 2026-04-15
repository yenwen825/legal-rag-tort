from flask import Blueprint, jsonify
from models.database import get_db_stats
from models.schemas import HealthCheckResponse
from services.vector_service import get_vector_cache
from services.redis_client import get_redis_client
from datetime import datetime

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    try:
        db_stats = get_db_stats()
        ids, _ = get_vector_cache()
        try:
            redis_client = get_redis_client()
            if redis_client is not None and redis_client.ping():
                redis = "ok"
            else:
                redis = "down"
        except Exception:
            redis = "down"
        return jsonify(
            HealthCheckResponse(
                status="ok",
                database=db_stats,
                vector_cache_status="loaded",
                vector_cache_count=len(ids),
                redis=redis,
                version="1.0.0",
                timestamp=datetime.now().isoformat(),
            ).model_dump()
        ), 200
    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ), 503
