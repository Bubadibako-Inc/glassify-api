from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users = db["users"]
products = db["products"]

# Create a Blueprint for cart
cart_bp = Blueprint('cart', __name__)

def format_user(user):
    user["_id"] = str(user["_id"])

    for product in user.get("cart", []):
        product["product_id"] = str(product["product_id"])

    return user

# Add cart to user
@cart_bp.route("/", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not all(field in data for field in ("product_id", "color")):
        return jsonify({"error": "Missing fields"}), 400

    product_id = data["product_id"]
    color = data["color"]

    try:
        product = products.find_one({"_id": ObjectId(product_id)})
    except errors.InvalidId:
        return jsonify({"error": "Invalid 'product_id' format."}), 400

    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({"error": "Product not found."}), 404
    
    colors = product.get("color", [])
    if color not in colors:
        return jsonify({"error": f"Invalid color. Available colors: {', '.join(colors)}"}), 400

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found."}), 404

    quantity = data.get("quantity", 1)
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "'quantity' must be a positive integer."}), 400

    cart = user.get("cart", [])
    existing_item = next((item for item in cart if item["product_id"] == ObjectId(product_id) and item["color"] == color), None)

    if existing_item:
        try:
            users.update_one(
                {"_id": ObjectId(user_id), "cart.product_id": ObjectId(product_id), "cart.color": color},
                {"$inc": {"cart.$.quantity": quantity}}
            )
            return jsonify({"message": "Product quantity updated in cart."}), 200
        except errors.PyMongoError as e:
            return jsonify({"error": f"An error occurred while updating the cart: {str(e)}"}), 500
    else:
        try:
            users.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"cart": {"product_id": ObjectId(product_id), "color": color, "quantity": quantity}}}
            )
            return jsonify({"message": "Product added to cart."}), 201
        except errors.PyMongoError as e:
            return jsonify({"error": f"An error occurred while adding to cart: {str(e)}"}), 500

# Get user cart
@cart_bp.route("/", methods=["GET"])
@jwt_required()
def get_user_cart():
    user_id = get_jwt_identity()
    
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found."}), 404
    
    user_data = format_user(user)
    
    return jsonify(user_data["cart"]), 200

# Remove product from cart
@cart_bp.route("/<product_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(product_id):
    user_id = get_jwt_identity()

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found."}), 404

    cart = user.get("cart", [])
    product_in_cart = next((item for item in cart if item["product_id"] == ObjectId(product_id)), None)

    if not product_in_cart:
        return jsonify({"error": "Product not found in cart."}), 404

    try:
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"cart": {"product_id": ObjectId(product_id)}}}
        )
        return jsonify({"message": "Product removed from cart."}), 200
    except errors.PyMongoError as e:
        return jsonify({"error": f"An error occurred while removing from cart: {str(e)}"}), 500
    