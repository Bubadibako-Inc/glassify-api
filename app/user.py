from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity 
from flask_bcrypt import Bcrypt
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from functools import wraps
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users = db["users"]

# Create a Blueprint for users
user_bp = Blueprint('users', __name__)

bcrypt = Bcrypt()

# Set up a set to store blacklisted tokens
blacklist = set()

# Role check decorator
def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()
            user = users.find_one({"_id": ObjectId(current_user)})
            
            if not user:
                return jsonify({"error": "User not found"}), 404

            if user.get("role") != role:
                return jsonify({"error": "Access forbidden: Insufficient permissions"}), 403

            return fn(*args, **kwargs)
        return decorated_function
    return wrapper

# Helper function to format user data
def format_user(user):
    user["_id"] = str(user["_id"])
    user.pop("password", None)

    for product in user.get("wishlist", []):
        product["product_id"] = str(product["product_id"])

    for product in user.get("cart", []):
        product["product_id"] = str(product["product_id"])

    return user

# Get all users (only accessible to admin)
@user_bp.route("/", methods=["GET"])
@role_required("admin")
def get_all_users():
    users_list = [format_user(user) for user in users.find()]

    return jsonify(users_list), 200

# Get user by ID
@user_bp.route("/<id>", methods=["GET"])
@role_required("admin")
def get_user(id):
    try:
        user = users.find_one({"_id": ObjectId(id)})
        if user:
            return jsonify(format_user(user)), 200
        else:
            return jsonify({"error": "User not found"}), 404

    except errors.InvalidId:
        return jsonify({"error": "Invalid ID format"}), 400

# Update user by ID
@user_bp.route("/<id>", methods=["PUT"])
@jwt_required()
def update_user(id):
    data = request.get_json()
    update_fields = {}

    if "name" in data:
        update_fields["name"] = data["name"]
    if "email" in data:
        update_fields["email"] = data["email"]
    if "password" in data:
        update_fields["password"] = bcrypt.generate_password_hash(data["password"]).decode('utf-8')

    if update_fields:
        result = users.update_one(
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
@user_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    result = users.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Data user berhasil dihapus"}), 200
    else:
        return jsonify({"message": "Data user tidak ditemukan"}), 404

