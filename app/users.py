from dotenv import load_dotenv
import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity 
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client.glassify
users_collection = db["users"]

# Create a Blueprint for users
users_bp = Blueprint('users', __name__)

# Initialize JWT Manager
jwt = JWTManager()

# Set up a set to store blacklisted tokens
blacklist = set()

# Helper function to format user data
def format_user(user):
    user["_id"] = str(user["_id"])
    user.pop("password", None)  # Remove password field for security
    return user

# Check user role
def role_required(role):
    def wrapper(fn):
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()
            user_data = users_collection.find_one({"_id": ObjectId(current_user)})

            if user_data and user_data.get("role") != role:
                return jsonify({"error": "Access forbidden: Insufficient permissions"}), 403
            
            return fn(*args, **kwargs)
        return decorated_function
    return wrapper

# Get all users (only accessible to admin)
@users_bp.route("/", methods=["GET"])
@role_required("admin")
def get_all_users():
    users = [format_user(user) for user in users_collection.find()]
    return jsonify(users=users), 200

# Create new user
@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "email", "password")):
        return jsonify({"error": "Missing fields"}), 400
    
    name = data["name"]
    email = data["email"]
    role = data.get("role", "user")
    password = generate_password_hash(data["password"])

    # Check if user already exists
    if users_collection.find_one({"email": email}):
        return jsonify({"message": "Email already registered"}), 409

    # Insert user
    user_id = users_collection.insert_one({
        "name": name,
        "email": email,
        "role": role,
        "password": password
    }).inserted_id

    return jsonify({
        "message": "User created",
        "_id": str(user_id)
    }), 201

# Get user by ID
@users_bp.route("/<id>", methods=["GET"])
@jwt_required()
def get_user(id):
    try:
        user = users_collection.find_one({"_id": ObjectId(id)})
        if user:
            return jsonify(user=format_user(user)), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except errors.InvalidId:
        return jsonify({"error": "Invalid ID format"}), 400

# Update user by ID
@users_bp.route("/<id>", methods=["PUT"])
@jwt_required()
def update_user(id):
    data = request.get_json()
    update_fields = {}

    if "name" in data:
        update_fields["name"] = data["name"]
    if "email" in data:
        update_fields["email"] = data["email"]
    if "password" in data:
        update_fields["password"] = generate_password_hash(data["password"])

    if update_fields:
        result = users_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_fields}
        )
        if result.modified_count > 0:
            return jsonify({"message": "User updated"}), 200
        else:
            return jsonify({"message": "No changes made or user not found"}), 404
    else:
        return jsonify({"error": "No valid fields provided for update"}), 400

# Delete user by ID
@users_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    result = users_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({"message": "User deleted"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Login and create JWT token
@users_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ("email", "password")):
        return jsonify({"error": "Missing email or password"}), 400

    email = data["email"]
    password = data["password"]

    user = users_collection.find_one({"email": email})
    if user and check_password_hash(user["password"], password):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": format_user(user)
        }), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

# Add token to blacklist when user logout
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist

# Logout
@users_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt_identity()  # Mengambil JWT ID (jti) dari token
    blacklist.add(jti)  # Tambahkan ke daftar blacklist
    
    return jsonify({"message": "Successfully logged out"}), 200
