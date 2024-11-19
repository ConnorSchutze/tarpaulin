from flask import Blueprint, request, jsonify
from app.utility import verify_jwt

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/login', methods=['POST'])
def login():
    """
    Issues JWTs.\n
    Protection: Pre-created Auth0 users
    """
    pass

@bp.route('', methods=['GET'])
def get_users():
    """
    Summary of all users. No info about avatar or courses.\n
    Protection: Admin only
    """
    # Get all users implementation
    pass

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Detailed summary about the user, including avatar and courses.\n
    Protection: Admin or JWT matching id
    """
    # Get a specific user implementation
    pass