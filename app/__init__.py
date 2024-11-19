import os
from flask import Flask
from google.cloud import datastore
from authlib.integrations.flask_client import OAuth

client = datastore.Client()
oauth = OAuth()

def create_app():
    app = Flask(__name__)

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
