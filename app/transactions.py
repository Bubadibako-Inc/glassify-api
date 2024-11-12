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
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users = db["users"]
products = db["products"]
transactions = db["transactions"]

# Create a Blueprint for transactions
transactions_bp = Blueprint('transactions', __name__)

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

# Helper function to format transaction data
def format_transaction(transaction):
    transaction["_id"] = str(transaction["_id"])
    transaction["user_id"] = str(transaction["user_id"])

    for item in transaction.get('items', []):
        item['product_id'] = str(item['product_id'])

    return transaction

# create new transaction
@transactions_bp.route("/", methods=["POST"])
@jwt_required()
def create_transaction():
    data = request.get_json()

    if "items" not in data or not isinstance(data["items"], list):
        return jsonify({"error": "'items' field must be provided as a list."}), 400
    
    user_id = get_jwt_identity()
    items = data["items"]
    total_amount = 0
    transaction_items = []

    for item in items:
        if not isinstance(item, dict) or "product_id" not in item or "quantity" not in item:
            return jsonify({"error": "Each item must contain 'product_id' and 'quantity'."}), 400
        
        try:
            product_id = ObjectId(item["product_id"])
        except:
            return jsonify({"error": "Invalid 'product_id' format."}), 400

        if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            return jsonify({"error": "'quantity' must be a positive integer."}), 400

        # Fetch product and calculate total price
        product = products.find_one({"_id": product_id})
        if not product:
            return jsonify({"error": f"Product with ID {item['product_id']} not found."}), 404
        
        if product["stock"] < 1:
            return jsonify({"error": "Product is out of stock"}), 400
        
        item_price = product["price"]
        total_item_price = item_price * item["quantity"]
        total_amount += total_item_price

        transaction_items.append({
            "product_id": product_id,
            "quantity": item["quantity"],
            "price": item_price
        })

        products.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {
                    "stock": -item["quantity"],
                    "sold": item["quantity"]
                }
            }
        )

    transaction_id = transactions.insert_one({
        "user_id": ObjectId(user_id),
        "items": transaction_items,
        "total_amount": round(total_amount, 2),
        "date": datetime.datetime.now().isoformat()
    }).inserted_id

    return jsonify({"message": "Transaction created", "_id": str(transaction_id)}), 201

# Get all transactions
@transactions_bp.route("/", methods=["GET"])
@role_required("admin")
def get_all_transactions():
    transactions_list = [format_transaction(transaction) for transaction in transactions.find()]
    return jsonify(transactions_list), 200

# Get transaction by ID
@transactions_bp.route("/<id>", methods=["GET"])
@jwt_required()
def get_transaction(id):
    try:
        transaction = transactions.find_one({"_id": ObjectId(id)})
        if transaction:
            return jsonify(format_transaction(transaction)), 200
        else:
            return jsonify({"error": "transactions not found"}), 404

    except errors.InvalidId:
        return jsonify({"error": "Invalid ID format"}), 400
    
# Get transaction by ID
@transactions_bp.route("/my_transactions", methods=["GET"])
@role_required("admin")
def my_transaction():
    try:
        user_id = get_jwt_identity()
        my_transaction_list = [format_transaction(transaction) for transaction in transactions.find({"user_id": ObjectId(user_id)})]
        if my_transaction_list:
            return jsonify(my_transaction_list), 200
        else:
            return jsonify({"error": "transaction not found"}), 404

    except errors.InvalidId:
        return jsonify({"error": "Invalid ID format"}), 400