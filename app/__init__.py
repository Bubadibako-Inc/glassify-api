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

    # Load JWT secret key from .env file
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")

    if not jwt_secret_key:
        raise EnvironmentError("JWT_SECRET_KEY environment variable not set correctly in .env file.")

    # Apply configurations
    app.config['JWT_SECRET_KEY'] = jwt_secret_key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

    # Initialize extensions with the app
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Register Blueprints
    from .auth import auth_bp
    from .cart import cart_bp
    from .model import model_bp
    from .product import products_bp
    from .review import reviews_bp
    from .transaction import transactions_bp
    from .user import user_bp
    from .wishlist import wishlist_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(model_bp, url_prefix='/model')
    app.register_blueprint(products_bp, url_prefix='/product')
    app.register_blueprint(reviews_bp, url_prefix='/review')
    app.register_blueprint(transactions_bp, url_prefix='/transaction')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(wishlist_bp, url_prefix='/wishlist')

    return app
