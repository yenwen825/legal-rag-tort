from flask import Blueprint, jsonify
from models.schemas import JudgmentDetail, ErrorResponse
from services.judgment_service import get_judgment_by_id

judgment_bp = Blueprint('judgment', __name__)

@judgment_bp.route('/judgment/<int:id>', methods=['GET'])
def judgment(id: int):
    try:
        response: JudgmentDetail = get_judgment_by_id(id)
        return jsonify(response.model_dump()), 200
    except ValueError:
        return jsonify(ErrorResponse(
            error = 'judgment not found',
            detail = None
        ).model_dump()), 404
    except Exception:
        return jsonify(ErrorResponse(
            error = 'internal server error',
            detail = None
        ).model_dump()), 500