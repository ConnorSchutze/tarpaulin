import json
from jose import jwt
from six.moves.urllib.request import urlopen
from app import client, AuthError
from flask import jsonify, current_app

ERROR = {
    "invalid": ({"Error": "The request body is invalid"}, 400),
    "unauthorized": ({"Error": "Unauthorized"}, 401),
    "permission": ({"Error": "You don't have permission on this resource"}, 403),
    "found": ({"Error": "Not found"}, 404)
}

def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                        "description":
                        "Authorization header is missing"}, 
                        401)
    
    jsonurl = urlopen("https://"+ current_app.config['DOMAIN'] +"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                        "Invalid header. "
                        "Use an RS256 signed JWT Access Token"}, 
                        401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                        "Invalid header. "
                        "Use an RS256 signed JWT Access Token"}, 
                        401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=current_app.config['ALGORITHMS'],
                audience=current_app.config['CLIENT_ID'],
                issuer="https://"+ current_app.config['DOMAIN'] +"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)

def attribute_check(attributes, data):
    for attribute in attributes:
        if attribute not in data:
            return ERROR["invalid"]
        
    return None

def user_pass_check():
    return ERROR["unauthorized"]

def no_user():
    return ERROR["found"]

def jwt_invalid(request):
    try:
        payload = verify_jwt(request)
        sub = payload.get("sub")
        return [sub, False]
    except AuthError:
        return [ERROR["unauthorized"], True]

def permission(sub, sub2=None):
    query = client.query(kind="users")
    query.add_filter("sub", "=", sub)
    results = list(query.fetch())
    for result in results:
        if result.get("role") == "admin":
            return None
        
    if sub == sub2:
        return None
        
    return ERROR["permission"]
