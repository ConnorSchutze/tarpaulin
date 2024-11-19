from flask import Blueprint, request, jsonify
from app.utility import verify_jwt

bp = Blueprint('auth', __name__)

@bp.route('/decode', methods=['GET'])
def decode_jwt():
    """
    Decodes a JWT.
    """
    payload = verify_jwt(request)
    return jsonify(payload)
