from flask import Blueprint, jsonify, request
from services.search_service import search_judgments
from models.schemas import SearchRequest, SearchResponse, ErrorResponse
from datetime import datetime
from pydantic import ValidationError

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search():
    try:
        request_data = SearchRequest.model_validate(request.get_json())
        response: SearchResponse = search_judgments(request_data.query, request_data.top_k, request_data.min_similarity)
        return jsonify(response.model_dump()), 200
    except ValidationError as e:
        return jsonify(ErrorResponse(
            error = 'invalid request data',
            detail = e.errors()
        ).model_dump()), 400
        
    except Exception as e:
        return jsonify((ErrorResponse(
            error = str(e),
            detail = None,
        ).model_dump())), 500