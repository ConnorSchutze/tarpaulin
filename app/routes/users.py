import requests
from flask import Blueprint, request, jsonify, current_app
from app.utility import *

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
    result_data = {

    }

    # admin & students
    query = client.query(kind="users")
    query.add_filter("sub", "=", sub)
    result = list(query.fetch())

    result_data.update({
        "id": result.key.id,
        "role": result.get("role"),
        "sub": result.get("sub")
    })

    roles = ["admin", "students"]

    if result.get("role") in roles:
        return (jsonify(result_data), 200)

    # instructors
    courses = []

    query = client.query(kind="courses")
    query.add_filter("instructor_id", "=", result.key.id)
    results = list(query.fetch())

    for r in results:
        courses.append(r.key.id)
