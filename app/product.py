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
                return jsonify({"message": "User not found"}), 404

            if user.get("role") != role:
                return jsonify({"message": "Access forbidden: Insufficient permissions"}), 403

            return fn(*args, **kwargs)
        return decorated_function
    return wrapper

# Helper function to format product data
def format_product(product):
    # Format the reviews by adding user information
    reviews = []
    for review in product.get('reviews', []):
        # Fetch the user who posted the review
        user = users.find_one({"_id": ObjectId(review['user_id'])})
        
        # If user is found, add their name and photo_profile to the review
        if user:
            review["user_id"] = str(review["user_id"])
            review['user_name'] = user.get('name')
            review['user_avatar'] = user.get('photo_profile')
        else:
            # If user not found, we can set defaults or leave empty
            review['user_name'] = 'Unknown User'
            review['user_avatar'] = None
        
        reviews.append(review)

    # Return the product with all fields and formatted reviews
    return {
        "_id": str(product["_id"]),
        "bridge": product.get("bridge"),
        "color": product.get("color"),
        "color_name": product.get("color_name"),
        "created_at": product.get("created_at"),
        "description": product.get("description"),
        "features": product.get("features", []),
        "frame_width": product.get("frame_width"),
        "images": product.get("images", []),
        "lens_height": product.get("lens_height"),
        "lens_width": product.get("lens_width"),
        "material": product.get("material", []),
        "name": product.get("name"),
        "price": product.get("price"),
        "rating": product.get("rating"),
        "reviews": reviews,  # Include formatted reviews
        "rim": product.get("rim"),
        "shape": product.get("shape"),
        "size": product.get("size"),
        "sold": product.get("sold"),
        "stock": product.get("stock"),
        "temple_length": product.get("temple_length"),
        "weight": product.get("weight")
    }

# Create new product (only admin)
@products_bp.route("/", methods=["POST"])
@role_required("admin")
def create_product():
    data = request.get_json()

    if not data or not all(field in data for field in ("name", "shape", "material", "color", "price", "description", "stock", "face_shape", "images")):
        return jsonify({"message": "Missing fields"}), 400
    
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
    reviews = data.get("reviews", [])
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
def get_all_products():
    # Get query parameters
    page = int(request.args.get("page", 1))  # Default to page 1 if not provided
    limit = int(request.args.get("limit", 10))  # Default to 10 items per page if not provided

    # MongoDB query to select only the required fields
    projection = {
        "_id": 1,
        "name": 1,
        "price": 1,
        "sold": 1,
        "review_count": {"$size": "$reviews"},  # Direct projection for review count
        "rating": 1,
        "images": 1
    }

    # Query the database with projection, skip, and limit for pagination
    cursor = products.find({}, projection).skip((page - 1) * limit).limit(limit)

    # Convert MongoDB cursor to a list of dictionaries containing only the required fields
    products_list = [
        {
            "_id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "sold": product["sold"],
            "review_count": product.get("review_count", 0),  # Ensure a valid count
            "rating": product["rating"],
            "images": product["images"][:1] if "images" in product else []
        }
        for product in cursor  # Corrected access to product within the loop
    ]

    # Check if there are more items to load
    total_count = products.count_documents({})  # Total number of documents
    has_more = (page * limit) < total_count
    next_page = page + 1 if has_more else None
    remaining_products = total_count - (page * limit) if has_more else 0

    # Return response with pagination information
    return jsonify({
        "products": products_list,
        "has_more": has_more,
        "next_page": next_page,
        "remaining_products": remaining_products
    }), 200
    
# Get Best selling product
@products_bp.route("/best-seller", methods=["GET"])
def get_best_selling_products():
    # Get query parameters
    page = int(request.args.get("page", 1))  # Default to page 1 if not provided
    limit = int(request.args.get("limit", 10))  # Default to 10 items per page if not provided

    # MongoDB query to select only the required fields
    projection = {
        "_id": 1,
        "name": 1,
        "price": 1,
        "sold": 1,
        "review_count": {"$size": "$reviews"},  # Direct projection for review count
        "rating": 1,
        "images": 1
    }

    # Sort by 'sold' in descending order to get best sellers first
    cursor = products.find({}, projection).sort("sold", -1).skip((page - 1) * limit).limit(limit)

    # Convert MongoDB cursor to a list of dictionaries containing only the required fields
    products_list = [
        {
            "_id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "sold": product["sold"],
            "review_count": product.get("review_count", 0),  # Ensure a valid count
            "rating": product["rating"],
            "images": product["images"][:1] if "images" in product else []
        }
        for product in cursor  # Corrected access to product within the loop
    ]

    # Check if there are more items to load
    total_count = products.count_documents({})  # Total number of documents
    has_more = (page * limit) < total_count
    next_page = page + 1 if has_more else None
    remaining_products = total_count - (page * limit) if has_more else 0

    # Return response with pagination information
    return jsonify({
        "products": products_list,
        "has_more": has_more,
        "next_page": next_page,
        "remaining_products": remaining_products
    }), 200
    
@products_bp.route("/latest", methods=["GET"])
def get_newest_products():
    # Get query parameters
    page = int(request.args.get("page", 1))  # Default to page 1 if not provided
    limit = int(request.args.get("limit", 10))  # Default to 10 items per page if not provided

    # MongoDB query to select only the required fields
    projection = {
        "_id": 1,
        "name": 1,
        "price": 1,
        "sold": 1,
        "review_count": {"$size": "$reviews"},  # Direct projection for review count
        "rating": 1,
        "created_at": 1,
        "images": 1
    }

    # Sort by 'created_at' in descending order to get newest items first
    cursor = products.find({}, projection).sort("created_at", -1).skip((page - 1) * limit).limit(limit)

    # Convert MongoDB cursor to a list of dictionaries containing only the required fields
    products_list = [
        {
            "_id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "sold": product["sold"],
            "review_count": product.get("review_count", 0),  # Ensure a valid count
            "rating": product["rating"],
            "created_at": product["created_at"],
            "images": product["images"][:1] if "images" in product else []
        }
        for product in cursor  # Corrected access to product within the loop
    ]

    # Check if there are more items to load
    total_count = products.count_documents({})  # Total number of documents
    has_more = (page * limit) < total_count
    next_page = page + 1 if has_more else None
    remaining_products = total_count - (page * limit) if has_more else 0

    # Return response with pagination information
    return jsonify({
        "products": products_list,
        "has_more": has_more,
        "next_page": next_page,
        "remaining_products": remaining_products
    }), 200

@products_bp.route("/search", methods=["GET"])
def search_products():
    # Get query parameters
    query = request.args.get("query")  # Search by name
    features_query = request.args.getlist("features")  # Search by multiple features
    rating_query = request.args.get("rating")  # Filter by rating
    rim_query = request.args.get("rim")  # Filter by rim type
    size_query = request.args.get("size")  # Filter by size
    weight_query = request.args.get("weight")  # Filter by weight
    material_query = request.args.get("material")  # Filter by material
    sort_by = request.args.get("sort_by")  # Sort by price or creation date (latest or oldest)
    page = int(request.args.get("page", 1))  # Default to page 1 if not provided
    limit = int(request.args.get("limit", 10))  # Default to 10 items per page if not provided

    # MongoDB query to build
    query = {}

    if query:
        query["name"] = {"$regex": query, "$options": "i"}  # Case insensitive match for name
        query["shape"] = {"$regex": query, "$options": "i"}  # Case insensitive match for shape
    if features_query:
        query["features"] = {"$in": features_query}  # Match any of the features
    if rating_query:
        query["rating"] = float(rating_query)  # Convert to float for comparison
    if rim_query:
        query["rim"] = {"$regex": rim_query, "$options": "i"}  # Case insensitive match for rim
    if size_query:
        query["size"] = {"$regex": size_query, "$options": "i"}  # Case insensitive match for size
    if weight_query:
        query["weight"] = {"$regex": weight_query, "$options": "i"}  # Case insensitive match for weight
    if material_query:
        query["material"] = {"$regex": material_query, "$options": "i"}  # Case insensitive match for material

    # Determine the sort order
    sort_field = None
    if sort_by == "price_asc":
        sort_field = ("price", 1)  # Sort by price ascending
    elif sort_by == "price_desc":
        sort_field = ("price", -1)  # Sort by price descending
    elif sort_by == "date_asc":
        sort_field = ("created_at", 1)  # Sort by creation date oldest first
    elif sort_by == "date_desc":
        sort_field = ("created_at", -1)  # Sort by creation date latest first

    # MongoDB query with projection, skip, limit, and sorting
    projection = {
        "_id": 1,
        "name": 1,
        "price": 1,
        "sold": 1,
        "review_count": {"$size": "$reviews"},  # Direct projection for review count
        "rating": 1,
        "created_at": 1,
        "images": 1
    }

    cursor = products.find(query, projection).skip((page - 1) * limit).limit(limit)
    if sort_field:
        cursor = cursor.sort(*sort_field)

    # Convert MongoDB cursor to a list of dictionaries containing only the required fields
    products_list = [
        {
            "_id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "sold": product["sold"],
            "review_count": product.get("review_count", 0),  # Ensure a valid count
            "rating": product["rating"],
            "created_at": product["created_at"],
            "images": product["images"][:1] if "images" in product else []
        }
        for product in cursor  # Corrected access to product within the loop
    ]

    # Check if there are more items to load
    total_count = products.count_documents(query)  # Total number of documents matching the query
    has_more = (page * limit) < total_count
    next_page = page + 1 if has_more else None
    remaining_products = total_count - (page * limit) if has_more else 0

    # Return response with pagination and filtered/sorted information
    return jsonify({
        "products": products_list,
        "has_more": has_more,
        "next_page": next_page,
        "remaining_products": remaining_products
    }), 200


# Get product by ID
@products_bp.route("/<id>", methods=["GET"])
def get_product(id):
    try:
        product = products.find_one({"_id": ObjectId(id)})
        if product:
            return jsonify(format_product(product)), 200
        else:
            return jsonify({"message": "Product not found"}), 404

    except errors.InvalidId:
        return jsonify({"message": "Invalid ID format"}), 400

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
        return jsonify({"message": "No valid fields provided for update"}), 400
    
# Delete product by ID
@products_bp.route("/<id>", methods=["DELETE"])
@role_required("admin")
def delete_product(id):
    result = products.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Product deleted"}), 200
    else:
        return jsonify({"message": "Product not found"}), 404