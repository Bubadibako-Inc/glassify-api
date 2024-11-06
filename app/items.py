from dotenv import load_dotenv
import os
import datetime
from flask import Blueprint, request, jsonify
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client.glassify
items_collection = db["items"]
users_collection = db["users"]

# Create a Blueprint for items
items_bp = Blueprint('items', __name__)

# Helper function to format item data
def format_item(item):
    item["_id"] = str(item["_id"])  # Convert ObjectId to string
    # Format reviews and get user information
    for review in item.get("review", []):
        review["user_id"] = str(review["user_id"])  # Convert ObjectId to string for user_id
        user = users_collection.find_one({"_id": review["user_id"]})
        if user:
            review["user_name"] = user.get("name")  # Add user's name to the review

    return item

# Get all items
@items_bp.route("/", methods=["GET"])
def get_all_items():
    items = [format_item(item) for item in items_collection.find()]
    return jsonify(items=items), 200

# Create new item
@items_bp.route("/", methods=["POST"])
@jwt_required()
def create_item():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "category", "shape", "color", "material", "price", "description")):
        return jsonify({"error": "Missing fields"}), 400

    item_id = items_collection.insert_one({
        "name": data["name"],
        "category": data["category"],
        "shape": data["shape"],
        "color": data["color"],
        "material": data["material"],
        "price": data["price"],
        "sold": 0,  # Initial sold count
        "description": data["description"],
        "review": [],
        "totalRating": 0
    }).inserted_id

    return jsonify({
        "message": "Item created",
        "_id": str(item_id)
    }), 201

# Get item by ID
@items_bp.route("/<id>", methods=["GET"])
def get_item(id):
    try:
        item = items_collection.find_one({"_id": ObjectId(id)})
        if item:
            return jsonify(item=format_item(item)), 200
        else:
            return jsonify({"error": "Item not found"}), 404
    except errors.InvalidId:
        return jsonify({"error": "Invalid ID format"}), 400

# Update item by ID
@items_bp.route("/<id>", methods=["PUT"])
@jwt_required()
def update_item(id):
    data = request.get_json()
    update_fields = {}

    if "name" in data:
        update_fields["name"] = data["name"]
    if "category" in data:
        update_fields["category"] = data["category"]
    if "shape" in data:
        update_fields["shape"] = data["shape"]
    if "color" in data:
        update_fields["color"] = data["color"]
    if "material" in data:
        update_fields["material"] = data["material"]
    if "price" in data:
        update_fields["price"] = data["price"]
    if "description" in data:
        update_fields["description"] = data["description"]

    if update_fields:
        result = items_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_fields}
        )
        if result.modified_count > 0:
            return jsonify({"message": "Item updated"}), 200
        else:
            return jsonify({"message": "No changes made or item not found"}), 404
    else:
        return jsonify({"error": "No valid fields provided for update"}), 400

# Delete item by ID
@items_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_item(id):
    result = items_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({"message": "Item deleted"}), 200
    else:
        return jsonify({"error": "Item not found"}), 404

# Add review to item
@items_bp.route("/<id>/review", methods=["POST"])
@jwt_required()
def add_review(id):
    data = request.get_json()
    if not data or not all(k in data for k in ("rating", "comment")):
        return jsonify({"error": "Missing fields"}), 400
    
    rating = data["rating"]
    # Validate rating value
    if not (1 <= rating <= 5):
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    user_id = get_jwt_identity()  # Get current user ID from JWT

    # Add review to item
    review = {
        "user_id": ObjectId(user_id),
        "rating": rating,
        "comment": data["comment"],
        "date": datetime.datetime.now().isoformat()  # Current date as ISO format
    }

    # Find the item by ID
    item = items_collection.find_one({"_id": ObjectId(id)})
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Update item with new review
    items_collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"review": review}}
    )

    # Update total rating based on the number of reviews
    reviews = item.get("review", []) + [review]
    if len(reviews) == 1:
        # If there's only one review, set totalRating to that review's rating
        total_rating = data["rating"]
    else:
        # Calculate the new average rating
        total_rating = sum(r["rating"] for r in reviews) / len(reviews)

    # Update the totalRating in the item
    items_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"totalRating": total_rating}}
    )

    return jsonify({"message": "Review added successfully"}), 201
