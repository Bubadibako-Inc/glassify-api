from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity 
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users = db["users"]

# Create a Blueprint for users
auth_bp = Blueprint('auth', __name__)

# Initialize JWT Manager
jwt = JWTManager()
bcrypt = Bcrypt()

# Set up a set to store blacklisted tokens
blacklist = set()

def format_user(user):
    try:
        # Create a new dictionary to store the formatted data
        formatted_user = {
            "_id": str(user["_id"]),  # Convert ObjectId to string
            "name": user.get("name", ""),  # Use default empty string if "name" doesn't exist
            "email": user.get("email", ""),
            "role": user.get("role", "user"),  # Default role if not found
            "photo_profile": user.get("photo_profile", None)  # Default empty string if no photo_profile
        }
        
        return formatted_user

    except Exception as e:
        print(f"Error formatting user: {str(e)}")
        return None  # Return None or handle the error as needed


# Create new user
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not all(field in data for field in ("name", "email", "password")):
        return jsonify({"message": "Nama, email, dan password harus diisi"}), 400
    
    name = data["name"]
    email = data["email"]
    role = data.get("role", "user")
    password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')

    if users.find_one({"email": email}):
        return jsonify({"message": "Email sudah terdaftar"}), 409

    user_id = users.insert_one({
        "name": name,
        "email": email,
        "role": role,
        "password": password
    }).inserted_id
    
    access_token = create_access_token(identity=str(user_id))
    
    user = users.find_one({"email": email})

    return jsonify({"message": "Berhasil register", "access_token": access_token, "user": format_user(user)}), 201

# Login and create JWT token
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not all(field in data for field in ("email", "password")):
        return jsonify({"message": "Email dan password harus diisi"}), 400
    
    email = data["email"]
    password = data["password"]

    user = users.find_one({"email": email})

    if user and bcrypt.check_password_hash(user["password"],password):
        access_token = create_access_token(identity=str(user["_id"]))

        return jsonify({"message": "Berhasil login", "access_token": access_token, "user": format_user(user)}), 200
    else:
        return jsonify({"message": "Email atau password salah"}), 401

# Logout
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt_identity()
    blacklist.add(jti)
    
    return jsonify({"message": "Berhasil log out"}), 200