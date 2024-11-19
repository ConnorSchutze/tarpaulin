import os
from flask import Flask, jsonify
from google.cloud import datastore
from authlib.integrations.flask_client import OAuth

client = datastore.Client()
oauth = OAuth()

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def create_app():
    app = Flask(__name__)

    # error
    @app.errorhandler(AuthError)
    def handle_auth_error(ex):
        response = jsonify(ex.error)
        response.status_code = ex.status_code
        return response

    # configure app with environment variables
    app.config['CLIENT_ID'] = os.getenv('CLIENT_ID')
    app.config['CLIENT_SECRET'] = os.getenv('CLIENT_SECRET')
    app.config['DOMAIN'] = os.getenv('DOMAIN')
    app.config['ALGORITHMS'] = os.getenv('ALGORITHMS')

    oauth.init_app(app)

    from .routes import users, courses, auth
    app.register_blueprint(users.bp)
    app.register_blueprint(courses.bp)
    app.register_blueprint(auth.bp)

    return app
