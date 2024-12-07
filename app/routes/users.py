import requests
import io
from flask import Blueprint, request, jsonify, current_app, send_file
from google.cloud import storage
from app.utility import *

AVATAR_BUCKET = "cs-tarpaulin"

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/login', methods=['POST'])
def login():
    """
    Issues JWTs.\n
    Protection: Pre-created Auth0 users
    """
    content = request.get_json()

    required_attributes = ["username", "password"]
    validation_error = attribute_check(required_attributes, content)
    if validation_error:
        return validation_error

    username = content["username"]
    password = content["password"]

    body = {
        'grant_type':'password',
        'username': username,
        'password': password,
        'client_id': current_app.config['CLIENT_ID'],
        'client_secret': current_app.config['CLIENT_SECRET']
    }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + current_app.config['DOMAIN'] + '/oauth/token'

    req = requests.post(url, json=body, headers=headers)

    if req.status_code == 200:
        token = req.json().get('id_token')
        if token:
            return jsonify({"token": token}), 200
        # error (not required)
    elif req.status_code == 403:
        return user_pass_check()
    else:
        # error (not required)
        return

@bp.route('', methods=['GET'])
def get_users():
    """
    Summary of all users. No info about avatar or courses.\n
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
    
    query = client.query(kind="users")
    results = list(query.fetch())
    response = []

    # modular design
    for result in results:
        result_data = {
            "id": result.key.id,
            "role": result.get("role"),
            "sub": result.get("sub")
        }
        response.append(result_data)
    
    return (jsonify(response), 200)

@bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    """
    Detailed summary about the user, including avatar and courses.\n
    Protection: Admin or JWT matching id
    """
    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]
    # 403 error
    else:
        sub = sub[0]
    
    # avatar
    result_data = {}

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(AVATAR_BUCKET)
    blob = bucket.blob(f"users/{id}/avatar.png")

    if blob.exists():
        result_data["avatar_url"] = f"{request.host_url}users/{id}/avatar"

    user = client.get(key=client.key("users", id))

    if user is None:
        return no_result()
    
    role = user.get("role")
    user_sub = user.get("sub")

    permission_error = permission(sub, user_sub)
    if permission_error:
        return permission_error
    
    result_data.update({
        "id": id,
        "role": role,
        "sub": user_sub
    })

    # admin & students

    if role == "admin":
        return (jsonify(result_data), 200)

    # instructors & students
    courses = []

    if role == "instructor":
        query = client.query(kind="courses")
        query.add_filter("instructor_id", "=", id)
        results = list(query.fetch())

        for r in results:
            courses.append(r.key.id)
        
        result_data.update({
            "courses": courses
        })
    elif role == "student":
        query = client.query(kind="enrollments")
        query.add_filter("student_id", "=", id)
        results = list(query.fetch())

        for r in results:
            courses.append(r.key.id)
        
        result_data.update({
            "courses": courses
        })

    return (jsonify(result_data), 200)

@bp.route('/<int:id>/avatar', methods=['POST'])
def create_avatar(id):
    """
    Create/update a user's avatar.
    Protection: User with JWT matching id
    """
    if 'file' not in request.files:
        return missing()

    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]

    sub = sub[0]

    user = client.get(key=client.key("users", id))

    if user is None:
        return no_result()
    
    user_sub = user.get("sub")

    if sub != user_sub:
        return no_id_found()
    
    file_obj = request.files['file']

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(AVATAR_BUCKET)
    blob = bucket.blob(f"users/{id}/avatar.png")
    file_obj.seek(0)
    blob.upload_from_file(file_obj)

    blob_url = f"{request.host_url}users/{id}/avatar"

    response_data = {
        "avatar_url": blob_url
    }

    return response_data, 200



@bp.route('/<int:id>/avatar', methods=['GET'])
def get_avatar(id):
    """
    Gets an avatar based on user id.
    Protection: User with JWT matching id
    """
    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]
    
    sub = sub[0]

    user = client.get(key=client.key("users", id))

    if user is None:
        return no_result()
    
    user_sub = user.get("sub")

    # 403 error
    if sub != user_sub:
        return no_id_found()
    
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(AVATAR_BUCKET)
    blob = bucket.blob(f"users/{id}/avatar.png")

    # 404 error
    if not blob.exists():
        return no_result()

    file_obj = io.BytesIO()
    blob.download_to_file(file_obj)
    file_obj.seek(0)
    
    return send_file(file_obj, mimetype='image/x-png', download_name="avatar.png")

@bp.route('/<int:id>/avatar', methods=['DELETE'])
def delete_avatar(id):
    """
    Delete an avatar based on user id.
    Protection: User with JWT matching id
    """
    sub = jwt_invalid(request)
    # 401 error
    if sub[1]:
        return sub[0]
    
    sub = sub[0]

    user = client.get(key=client.key("users", id))

    # 404 error
    if user is None:
        return no_result()
    
    user_sub = user.get("sub")

    # 403 error
    if sub != user_sub:
        return no_id_found()

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(AVATAR_BUCKET)
    blob = bucket.blob(f"users/{id}/avatar.png")

    # 404 error
    if not blob.exists():
        return no_result()

    blob.delete()

    return ("", 204)
