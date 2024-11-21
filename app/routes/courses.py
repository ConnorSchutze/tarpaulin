from flask import Blueprint, request, jsonify
from google.cloud import datastore
from app.utility import *

bp = Blueprint('courses', __name__, url_prefix='/courses')

@bp.route('', methods=['POST'])
def create_course():
    """
    Create a course.\n
    Protection: Admin only
    """
    data = request.get_json()

    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]
    # 403 error
    else:
        permission_error = permission(sub[0])
        if permission_error:
            return permission_error
    
    # 400 error
    required_attributes = ["subject", "number", "title", "term", "instructor_id"]
    validation_error = attribute_check(required_attributes, data)
    if validation_error:
        return validation_error
    
    role_error = role_check(data["instructor_id"], "instructor")
    if role_error:
        return role_error
    
    # create new course
    new_course = datastore.Entity(key=client.key("courses"))
    new_course.update({
        "subject": data["subject"],
        "number": data["number"],
        "title": data["title"],
        "term": data["term"],
        "instructor_id": data["instructor_id"]
    })
    client.put(new_course)

    # generate self url
    course_url = f"{request.host_url}courses/{new_course.key.id}"

    # 201 response
    return jsonify({
        "id": new_course.key.id,
        "subject": data["subject"],
        "number": data["number"],
        "title": data["title"],
        "term": data["term"],
        "instructor_id": data["instructor_id"],
        "self": course_url
    }), 201


@bp.route('', methods=['GET'])
def get_courses():
    """
    Get all courses. Paginated using offset/limit. Doesn't return info on 
    course enrollment.\n
    Protection: Unprotected
    """
    pass

@bp.route('/<int:id>', methods=['GET'])
def get_course(id):
    """
    Gets a course based on id. Doesn't return info on course enrollment.\n
    Protection: Unprotected
    """
    pass

@bp.route('/<int:id>', methods=['PATCH'])
def update_course(id):
    """
    Partially updates a course.\n
    Protection: Admin only
    """
    pass

@bp.route('/<int:id>', methods=['DELETE'])
def delete_course(id):
    """
    Deletes a course and enrollment info.\n
    Protection: Admin only
    """
    pass
