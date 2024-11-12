from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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
products = db["products"]

# Create a Blueprint for wishlist
wishlist_bp = Blueprint('wishlists', __name__)

def format_user(user):
    user["_id"] = str(user["_id"])

    for product in user.get("wishlist", []):
        product["product_id"] = str(product["product_id"])

    return user

# Add wishlist to user
@wishlist_bp.route("/", methods=["POST"])
@jwt_required()
def add_wishlist():
    user_id = get_jwt_identity()
    data = request.get_json()

    if "product_id" not in data:
        return jsonify({"error": "'product_id' field is required."}), 400

    product_id = data["product_id"]

    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({"error": "Product not found."}), 404

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found."}), 404

    if any(item["product_id"] == ObjectId(product_id) for item in user.get("wishlist", [])):
        return jsonify({"message": "Product already in wishlist."}), 200

    try:
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"wishlist": {"product_id": ObjectId(product_id)}}}
        )
        return jsonify({"message": "Product added to wishlist."}), 201
    except errors.PyMongoError as e:
        return jsonify({"error": f"An error occurred while adding to wishlist: {str(e)}"}), 500

# Get user wishlist
@wishlist_bp.route("/", methods=["GET"])
@jwt_required()
def get_user_wishlist():
    user_id = get_jwt_identity()
    
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found."}), 404
    
    user_data = format_user(user)
    
    return jsonify(user_data["wishlist"]), 200

# Remove product from wishlist
@wishlist_bp.route("/<product_id>", methods=["DELETE"])
@jwt_required()
def remove_from_wishlist(product_id):
    user_id = get_jwt_identity()

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found."}), 404

    wishlist = user.get("wishlist", [])
    product_in_wishlist = next((item for item in wishlist if item["product_id"] == ObjectId(product_id)), None)

    if not product_in_wishlist:
        return jsonify({"error": "Product not found in wishlist."}), 404

    try:
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"wishlist": {"product_id": ObjectId(product_id)}}}
        )
        return jsonify({"message": "Product removed from wishlist."}), 200
    except errors.PyMongoError as e:
        return jsonify({"error": f"An error occurred while removing from wishlist: {str(e)}"}), 500
    
