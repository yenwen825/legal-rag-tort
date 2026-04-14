from flask import Blueprint, jsonify, request
from services.analyze_service import analyze
from models.schemas import AnalysisRequest, AnalysisResponse, ErrorResponse
from pydantic import ValidationError
import time
import logging

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analyze', methods=['POST'])
def analyze_endpoint():
    try:
        request_data = AnalysisRequest.model_validate(request.get_json())
        start_time = time.time()
        summary = analyze(query=request_data.query, result_ids=request_data.result_ids)
        elapsed_ms = int((time.time() - start_time) * 1000)
        response = AnalysisResponse(
            summary=summary,
            analysis_time_ms=elapsed_ms
        )
        return jsonify(response.model_dump())
    except ValidationError as e:
        return jsonify(ErrorResponse(error="invalid request data", detail=e.errors()).model_dump()), 400
    except Exception as e:
        logging.error(f"Error in analyze_endpoint: {e}")
        return jsonify(ErrorResponse(error=str(e), detail=None).model_dump()), 500