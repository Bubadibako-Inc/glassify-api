from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity 
from flask_bcrypt import Bcrypt
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from functools import wraps
from dotenv import load_dotenv
from PIL import Image
import io
import base64
import os

# Load environment variables from .env file
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users = db["users"]

# Directory to store images
UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed extensions for uploading image
ALLOWED_EXTENSIONS = {"jpeg", "webp", "png"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create a Blueprint for users
users_bp = Blueprint('users', __name__)

# Initialize JWT Manager
jwt = JWTManager()
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

    return user

# Create new user
@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data or not all(field in data for field in ("name", "email", "password")):
        return jsonify({"error": "Missing fields"}), 400
    
    name = data["name"]
    email = data["email"]
    role = data.get("role", "user")
    password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    face_photo = data.get("face_photo", "-")
    photo_profile = data.get("photo_profile", "-")
    wishlist = data.get("wishlist", [])
    cart = data.get("cart", [])

    if users.find_one({"email": email}):
        return jsonify({"message": "Email already registered"}), 409

    user_id = users.insert_one({
        "name": name,
        "email": email,
        "role": role,
        "password": password,
        "face_photo": face_photo,
        "photo_profile": photo_profile,
        "wishlist": wishlist,
        "cart": cart
    }).inserted_id

    return jsonify({"message": "User created", "_id": str(user_id)}), 201

# Login and create JWT token
@users_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not all(field in data for field in ("email", "password")):
        return jsonify({"error": "Missing email or password"}), 400
    
    email = data["email"]
    password = data["password"]

    user = users.find_one({"email": email})

    if user and bcrypt.check_password_hash(user["password"],password):
        access_token = create_access_token(identity=str(user["_id"]))

        return jsonify({"message": "Login successful", "access_token": access_token}), 200
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
    jti = get_jwt_identity()
    blacklist.add(jti)
    
    return jsonify({"message": "Successfully logged out"}), 200

# Get current user
@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    _id = get_jwt_identity()
    user = users.find_one({"_id": ObjectId(_id)})
    return jsonify(format_user(user)), 200

# Get all users (only accessible to admin)
@users_bp.route("/", methods=["GET"])
@role_required("admin")
def get_all_users():
    users_list = [format_user(user) for user in users.find()]

    return jsonify(users_list), 200

# Get user by ID
@users_bp.route("/<id>", methods=["GET"])
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
        update_fields["password"] = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    if "photo_profile" in data:
        update_fields["photo_profile"] = data["photo_profile"]            

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
@users_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    result = users.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "User deleted"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload face shape recognition image
@users_bp.route("/upload_image", methods=["POST"])
@jwt_required(optional=True)
def upload_image():
    _id = get_jwt_identity()
    user = None
    
    if _id:
        user = users.find_one({"_id": ObjectId(_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404

    if 'face_photo' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['face_photo']

    if not image_file.mimetype.startswith('image/'):
        return jsonify({"error": "File is not an image."}), 400

    image_format = image_file.filename.split('.')[-1].lower()
    image = Image.open(image_file)

    if image_format not in ALLOWED_EXTENSIONS:
        image = image.convert("RGB")
        image_format = "png"

    if user:
        filename = f"{user['name']}.{image_format}"
    else:
        filename = "temporary.png"

    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path, format=image_format.upper())

    if user:
        with open(image_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
            users.update_one(
                {"_id": ObjectId(_id)},
                {"$set": {"face_photo": encoded_image}}
            )

    return jsonify({"message": "Image uploaded successfully"}), 200

# Get the user's face shape recognition image
@users_bp.route("/get_image", methods=["GET"])
@jwt_required()
def get_image():
    _id = get_jwt_identity()
    user = users.find_one({"_id": ObjectId(_id)})

    if not user or "face_photo" not in user:
        return jsonify({"error": "Image not found"}), 404

    image_data = base64.b64decode(user["face_photo"])
    return send_file(io.BytesIO(image_data), mimetype='image/png')