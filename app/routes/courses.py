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
    # extract pagination data
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 3))

    # query courses
    query = client.query(kind="courses")
    query.order = ["subject"]
    courses_result = query.fetch(offset=offset, limit=limit)

    # generate result
    courses =[]
    for course in courses_result:
        course_data = {
            "id": course.key.id,
            "instructor_id": course["instructor_id"],
            "number": course["number"],
            "subject": course["subject"],
            "term": course["term"],
            "title": course["title"],
            "self": f"{request.host_url}courses/{course.key.id}"
        }
        courses.append(course_data)

    response = {
        "courses": courses
    }

    # determine pagination limits
    query = client.query(kind="courses")
    total_count = len(list(query.fetch()))
    next_offset = offset + limit
    next_url = None
    if next_offset < total_count:
        next_url = f"{request.host_url}courses?offset={next_offset}&limit={limit}"
    
    # create response
    if next_url:
        response.update({"next": next_url})
    
    return jsonify(response), 200

@bp.route('/<int:id>', methods=['GET'])
def get_course(id):
    """
    Gets a course based on id. Doesn't return info on course enrollment.\n
    Protection: Unprotected
    """
    course = client.get(key=client.key("courses", id))

    # 404 error
    if course is None:
        return no_result()
    
    response = {
        "id": course.key.id,
        "instructor_id": course.get("instructor_id"),
        "number": course.get("number"),
        "subject": course.get("subject"),
        "term": course.get("term"),
        "title": course.get("title"),
        "self": f"{request.host_url}courses/{course.key.id}"
    }

    return (jsonify(response), 200)

@bp.route('/<int:id>', methods=['PATCH'])
def update_course(id):
    """
    Partially updates a course.\n
    Protection: Admin only
    """
    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]
    # 403 error
    else:
        permission_error = permission(sub[0])
        if permission_error:
            return permission_error

    data = request.get_json()

    course = client.get(key=client.key("courses", id))

    # 403 error
    if course is None:
        return no_id_found()
    
    # 400 error
    if "instructor_id" in data:
        user_error = invalid_user(data["instructor_id"])
        if user_error:
            return user_error
    
    # update fields
    updatable_fields = ["subject", "number", "title", "term", "instructor_id"]
    for field in updatable_fields:
        if field in data:
            course.update({f"{field}": data[f"{field}"]})
    
    client.put(course)

    response = {
        "id": course.key.id,
        "instructor_id": course.get("instructor_id"),
        "number": course.get("number"),
        "subject": course.get("subject"),
        "term": course.get("term"),
        "title": course.get("title"),
        "self": f"{request.host_url}courses/{course.key.id}"
    }

    return (jsonify(response), 200)

@bp.route('/<int:id>', methods=['DELETE'])
def delete_course(id):
    """
    Deletes a course and enrollment info.\n
    Protection: Admin only
    """
    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]
    # 403 error
    else:
        permission_error = permission(sub[0])
        if permission_error:
            return permission_error
    
    course_key = client.key("courses", id)
    course = client.get(key=course_key)

    if course is None:
        return no_id_found()
    
    client.delete(course_key)

    return ("", 204)


@bp.route('/<int:id>/students', methods=['PATCH'])
def update_enrollment(id):
    """
    Enroll and/or disenroll students from a course.\n
    Protection: Admin or instructor of course
    """
    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]

    sub = sub[0]
    
    course_key = client.key("courses", id)
    course = client.get(key=course_key)

    if course is None:
        return no_id_found()

    # 403 error
    instructor_id = course.get("instructor_id")

    query = client.query(kind="users")
    query.add_filter("sub", "=", sub)
    results = list(query.fetch())
    for result in results:
        if result.get("role") != "admin" and result.get("id") != instructor_id:
            print(f"id: {result.get("id")} - iid: {instructor_id}")
            return no_id_found()

    data = request.get_json()

    required_attributes = ["add", "remove"]

    # 400 error (not need in api doc)
    validation_error = attribute_check(required_attributes, data)
    if validation_error:
        return validation_error

    add = data["add"]
    remove = data["remove"]

    for user_id in add:
        # 409 error - i
        if user_id in remove:
            return enrollment_invalid()
        
        user = client.get(key=client.key("users", user_id))

        # 409 error - ii
        if user is None or user.get("role") != "student":
            return enrollment_invalid()
        
        enrollment_key = client.key("enrollments", user_id)
        enrollment = client.get(key=enrollment_key)

        # don't add if already there
        if enrollment is None:
            new_enrollment = datastore.Entity(key=client.key("enrollments"))
            new_enrollment.update({
                "course_id": id,
                "student_id": user_id
            })
            client.put(new_enrollment)
    
    for user_id in remove:
        user = client.get(key=client.key("users", user_id))

        # 409 error - ii
        if user is None or user.get("role") != "student":
            return enrollment_invalid()
        
        enrollment_key = client.key("enrollments", user_id)
        enrollment = client.get(key=enrollment_key)

        # don't remove if not there
        if enrollment:
            client.delete(enrollment_key)
        
    return ("", 200)
