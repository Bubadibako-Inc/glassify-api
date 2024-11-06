from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import datetime

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Load configuration from .env or any other config file
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

    # Initialize JWT Manager
    jwt = JWTManager(app)

    # Register Blueprints
    from .users import users_bp
    from .items import items_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(items_bp, url_prefix='/api/items')

    return app
