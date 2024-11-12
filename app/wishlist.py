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
wishlists_bp = Blueprint('wishlists', __name__)

def format_user(user):
    user["_id"] = str(user["_id"])

    for product in user.get("wishlist", []):
        product["product_id"] = str(product["product_id"])

    return user
