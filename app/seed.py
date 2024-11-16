from faker import Faker
from pymongo import MongoClient
from bson import ObjectId
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users_collection = db["users"]
products_collection = db["products"]
transactions_collection = db["transactions"]

faker = Faker()

# Seed Products Collection
def seed_products(count=10):
    products = []

    for _ in range(count):
        product = {
            "name": faker.word().capitalize() + " Glasses",
            "shape": random.choice([
                "Round", "Square", "Oval", "Rectangle", "Cat-Eye", "Aviator", "Browline", "Oversized", "Geometric", "Butterfly", "Goggle", "Pilot"
            ]),
            "material": random.sample(["Plastic", "Metal", "Titanium", "Aluminum", "Carbon", "Wooden"], random.randint(1, 2)),
            "color": faker.color_name(),
            "price": random.randint(100000, 1000000),
            "sold": random.randint(0, 50),
            "description": faker.sentence(),
            "stock": random.randint(10, 100),
            "face_shape": random.sample(["Oval", "Square", "Heart", "Round", "Diamond", "Rectangle"], random.randint(1, 3)),
            "images": [faker.file_name(extension="jpg") for _ in range(2)],
            "reviews": [],
            "rating": 0
        }
        products.append(product)
    
    result = products_collection.insert_many(products)
    print(f"{count} products inserted.")
    return result.inserted_ids

# Seed Users Collection
def seed_users(count=10):
    users = []

    for _ in range(count):
        user = {
            "name": faker.first_name(),
            "email": faker.email(),
            "role": random.choice(["admin", "user"]),
            "password": faker.password(),  # Use bcrypt for secure passwords if needed
            "face_photo": faker.file_name(extension="jpg"),
            "photo_profile": faker.file_name(extension="png"),
            "wishlist": [],
            "cart": []
        }
        users.append(user)
    
    result = users_collection.insert_many(users)
    print(f"{count} users inserted.")
    return result.inserted_ids

# Seed Transactions Collection
def seed_transactions(user_ids, product_ids, count=10):
    transactions = []

    for _ in range(count):
        user_id = random.choice(user_ids)
        items = [
            {
                "product_id": random.choice(product_ids),
                "quantity": random.randint(1, 5),
                "price": random.randint(100000, 500000)
            }
            for _ in range(random.randint(1, 3))
        ]
        transaction = {
            "user_id": user_id,
            "items": items,
            "total_amount": sum(item["quantity"] * item["price"] for item in items),
            "date": faker.iso8601()
        }
        transactions.append(transaction)
    
    transactions_collection.insert_many(transactions)
    print(f"{count} transactions inserted.")

# Update Users Collection with Cart
def update_cart_for_users(user_ids, product_ids):
    for user_id in user_ids:
        cart = [
            {
                "product_id": random.choice(product_ids),  # Reference a real product ID
                "quantity": random.randint(1, 5)
            }
            for _ in range(random.randint(1, 3))
        ]
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {"cart": cart}}
        )
    print("Cart updated for users.")

# Update Users Collection with Wishlist
def update_wishlist_for_users(user_ids, product_ids):
    for user_id in user_ids:
        wishlist = [
            {
                "product_id": random.choice(product_ids)  # Reference a real product ID
            }
            for _ in range(random.randint(1, 5))
        ]
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {"wishlist": wishlist}}
        )
    print("Wishlist updated for users.")

# Add Reviews to Products
def add_reviews_to_products(user_ids, product_ids):
    for product_id in product_ids:
        reviews = [
            {
                "user_id": random.choice(user_ids),
                "rating": random.randint(1, 5),
                "comment": faker.sentence(),
                "date": faker.iso8601()
            }
            for _ in range(random.randint(1, 5))
        ]
        average_rating = round(
            sum(review["rating"] for review in reviews) / len(reviews), 1
        )
        products_collection.update_one(
            {"_id": product_id},
            {"$set": {"reviews": reviews, "rating": average_rating}}
        )
    print("Reviews and ratings added to products.")

# Main Seeding Function
if __name__ == "__main__":
    product_ids = seed_products(10)  # Step 1: Seed Products
    user_ids = seed_users(5)         # Step 2: Seed Users
    seed_transactions(user_ids, product_ids, 5)  # Step 3: Seed Transactions
    update_cart_for_users(user_ids, product_ids)  # Step 4: Update Cart
    update_wishlist_for_users(user_ids, product_ids)  # Step 5: Update Wishlist
    add_reviews_to_products(user_ids, product_ids)  # Step 6: Add Reviews
