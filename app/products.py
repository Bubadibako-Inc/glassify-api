from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from functools import wraps
from dotenv import load_dotenv
import os
import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)
db = client.glassify
users = db["users"]
products = db["products"]

# Create a Blueprint for products
products_bp = Blueprint('products', __name__)

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

# Helper function to format product data
def format_product(product):
    product["_id"] = str(product["_id"])

    for review in product.get("review", []):
        review["user_id"] = str(review["user_id"])

    return product

# Create new user (only admin)
@products_bp.route("/", methods=["POST"])
@role_required("admin")
def create_product():
    data = request.get_json()

    if not data or not all(field in data for field in ("name", "shape", "material", "color", "price", "description", "stock", "face_shape", "images")):
        return jsonify({"error": "Missing fields"}), 400
    
    name = data["name"]
    shape = data["shape"]
    material = data["material"]
    color = data["color"]
    price = data["price"]
    sold = data.get("sold", 0)
    description = data["description"]
    stock = data["stock"]
    face_shape = data["face_shape"]
    images = data["images"]
    reviews = data.get("review", [])
    rating = 0

    product_id = products.insert_one({
        "name": name,
        "shape": shape,
        "material": material,
        "color": color,
        "price": price,
        "sold": sold,
        "description": description,
        "stock": stock,
        "face_shape": face_shape,
        "images": images,
        "reviews": reviews,
        "rating": rating
    }).inserted_id

    return jsonify({"message": "Product created", "_id": str(product_id)}), 201

# Get all products
@products_bp.route("/", methods=["GET"])
def get_all_produtcs():
    products_list = [format_product(product) for product in products.find()]

    return jsonify(products_list), 200

# Get product by ID
@products_bp.route("/<id>", methods=["GET"])
def get_user(id):
    try:
        product = products.find_one({"_id": ObjectId(id)})
        if product:
            return jsonify(format_product(product)), 200
        else:
            return jsonify({"error": "Product not found"}), 404

    except errors.InvalidId:
        return jsonify({"error": "Invalid ID format"}), 400

# Update product (only admin)
@products_bp.route("/<id>", methods=["PUT"])
@role_required("admin")
def update_product(id):
    data = request.get_json()
    update_fields = {}

    if "name" in data:
        update_fields["name"] = data["name"]
    if "shape" in data:
        update_fields["shape"] = data["shape"]
    if "material" in data:
        update_fields["material"] = data["material"]
    if "color" in data:
        update_fields["color"] = data["color"]
    if "price" in data:
        update_fields["price"] = data["price"]
    if "description" in data:
        update_fields["description"] = data["description"]
    if "stock" in data:
        update_fields["stock"] = data["stock"]
    if "face_shape" in data:
        update_fields["face_shape"] = data["face_shape"]
    if "images" in data:
        update_fields["images"] = data["images"]
        

    if update_fields:
        result = products.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_fields}
        )

        if result.modified_count > 0:
            return jsonify({"message": "Product updated"}), 200
        else:
            return jsonify({"message": "No changes made or product not found"}), 404
    else:
        return jsonify({"error": "No valid fields provided for update"}), 400
    
# Delete product by ID
@products_bp.route("/<id>", methods=["DELETE"])
@role_required("admin")
def delete_product(id):
    result = products.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Product deleted"}), 200
    else:
        return jsonify({"error": "Product not found"}), 404