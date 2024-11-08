from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize extensions globally
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    # Load configuration from .env or any other config file
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret_key:
        raise EnvironmentError("JWT_SECRET_KEY environment variable not set.")

    app.config['JWT_SECRET_KEY'] = jwt_secret_key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

    # Initialize extensions with the app
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Register Blueprints
    from .users import users_bp
    from .products import products_bp
    from .transactions import transactions_bp

    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')

    return app
