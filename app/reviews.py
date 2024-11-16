from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
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
reviews_bp = Blueprint('reviews', __name__)

# Helper function to format product data
def format_product(product):
    product["_id"] = str(product["_id"])

    for review in product.get("review", []):
        review["user_id"] = str(review["user_id"])

    return product

# Add review by product ID
@reviews_bp.route("/<id>", methods=["POST"])
@jwt_required()
def add_review(id):
    data = request.get_json()
    
    if not data or not all(field in data for field in ("rating", "comment")):
        return jsonify({"error": "Missing fields"}), 400
    
    user_id = get_jwt_identity()
    rating = data["rating"]
    comment = data["comment"]

    if not (1 <= rating <= 5):
        return jsonify({"error": "Rating must be between 1 and 5"}), 400
    
    review = {
        "user_id": ObjectId(user_id),
        "rating": rating,
        "comment": comment,
        "date": datetime.datetime.now().isoformat()
    }

    product = products.find_one({"_id": ObjectId(id)})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    products.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"reviews": review}}
    )

    reviews = product.get("review", []) + [review]
    total_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)

    products.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"rating": total_rating}}
    )

    return jsonify({"message": "Review added successfully"}), 201

# Get all reviews from users by user ID
@reviews_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user_review():
    user_id = get_jwt_identity()

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_reviews = []
    products_with_reviews = products.find(
        {"reviews.user_id": ObjectId(user_id)},
        {"reviews": 1, "name": 1}
    )

    for product in products_with_reviews:
        product_reviews = [
            {
                "product_id": str(product["_id"]),
                "product_name": product["name"],
                "rating": review["rating"],
                "comment": review["comment"],
                "date": review["date"]
            }
            for review in product["reviews"]
            if review["user_id"] == ObjectId(user_id)
        ]
        user_reviews.extend(product_reviews)

    return jsonify(user_reviews), 200
