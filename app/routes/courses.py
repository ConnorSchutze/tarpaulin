from flask import Blueprint

bp = Blueprint('courses', __name__, url_prefix='/courses')

@bp.route('', methods=['POST'])
def create_course():
    """
    Create a course.\n
    Protection: Admin only
    """
    pass

@bp.route('', methods=['GET'])
def get_courses():
    """
    Get all courses. Paginated using offset/limit. Doesn't return info on 
    course enrollment.\n
    Protection: Unprotected
    """
    pass

@bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """
    Gets a course based on id. Doesn't return info on course enrollment.\n
    Protection: Unprotected
    """
    pass

@bp.route('/<int:course_id>', methods=['PATCH'])
def update_course():
    """
    Partially updates a course.\n
    Protection: Admin only
    """
    pass

@bp.route('/<int:course_id>', methods=['DELETE'])
def delete_course():
    """
    Deletes a course and enrollment info.\n
    Protection: Admin only
    """
    pass
