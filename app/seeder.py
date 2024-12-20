from datetime import datetime, timedelta
from faker import Faker
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

bcrypt = Bcrypt()

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users_collection = db["users"]
products_collection = db["products"]
transactions_collection = db["transactions"]

faker = Faker()

glasses_shape = ["Square", "Cat-Eye", "Round", "Rectangle", "Aviator", "Aviator", "Browline", "Geometric", "Oval", "Heart"]
glasses_size = ["Adult XS (110-118 mm)", "Adult S (119-125 mm)", "Adult M (126-132 mm)", "Adult L (133-140 mm)", "Adult XL (141+ mm)", "Kid XS (90-106 mm)", "Kid S (107-112 mm)", "Kid M (113-118 mm)", "Kid L (119-150 mm)"]
glasses_material = ["Titanium", "Flex Titanium", "Stainless Steel", "Other Metal", "Acetate", "Recycled Plastic", "Carbon Fiber", "Other Plastic"]
glasses_rim = ["Full Rim", "Half Rim", "Rimless"]
glasses_weight =["Ultra Light (<20 grams)", "Light (21-40 grams)", "Medium (41-60 grams)", "Heavy (61-80 grams)", "Extra Heavy (81-100 grams)"]
glasses_features = ["Nose Pads", "Lightweight", "Spring Hinges", "Flexible", "Universal Fit", "Clip-Ons", "Engraving", "Protective"]
model_images = [
    "https://static.zennioptical.com/production/products/general/32/17/3217321-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/40/85/408521-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/23/43/234321-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/44/43/4443112-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/20/27/2027616-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/44/38/4438924-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/44/51/4451821-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/25/3225119-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/28/36/283621-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/78/31/7831221-modelimage-GR.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/24/3224114-eyeglasses-model-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/38/2038825-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/44/44/4444921-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/10/12/101235-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/16/3216721-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/41/90/419014-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/23/3223621-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/41/89/418912-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/20/40/2040839-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/19/3219724-eyeglasses-model-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/30/2030321-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/27/04/270421-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/12/52/125221-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/34/3234014-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/18/3218621-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/13/00/1300611-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/12/3212021-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/32/13/3213429-modelimage.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/19/11/1911221-modelimage-GR.jpg?im=FaceCrop,algorithm=dnn",
    "https://static.zennioptical.com/production/products/general/20/39/2039321-modelimage.jpg?im=FaceCrop,algorithm=dnn"
]

product_images = [
    "https://static.zennioptical.com/production/products/general/32/17/3217321-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/40/85/408521-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/23/43/234321-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/44/43/4443112-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/27/2027616-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/44/38/4438924-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/44/51/4451821-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/25/3225119-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/28/36/283621-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/78/31/7831221-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/24/3224114-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/38/2038825-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/44/44/4444921-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/10/12/101235-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/16/3216721-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/41/90/419014-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/23/3223621-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/41/89/418912-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/40/2040839-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/19/3219724-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/30/2030321-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/27/04/270421-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/12/52/125221-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/34/3234014-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/18/3218621-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/13/00/1300611-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/12/3212021-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/32/13/3213429-eyeglasses-angle-view.jpg",
    "https://static.zennioptical.com/production/products/general/19/11/1911221-eyeglasses-front-view.jpg",
    "https://static.zennioptical.com/production/products/general/20/39/2039321-eyeglasses-angle-view.jpg"
]


# Seed Products Collection
def seed_products(count=10):
    products = []
    color = random.randint(1, 5)
    
    for _ in range(count):
        
        # Randomize the creation date
        created_at = faker.date_time_between_dates(
            datetime_start=datetime.now() - timedelta(days=5*365),
            datetime_end=datetime.now()
        )
        
        random_model_image = random.choice(model_images)
        random_product_images = random.sample(product_images, random.randint(1, 4))
        
        product = {
            "name":  "Kacamata " + random.choice(glasses_shape) + " " + faker.word().capitalize(),
            "shape": random.choice(glasses_shape),
            "size": random.choice(glasses_size),
            "material": random.sample(glasses_material, random.randint(1, 2)),
            "rim": random.choice(glasses_rim),
            "weight": random.choice(glasses_weight),
            "features": random.sample(glasses_features, random.randint(1, 4)),
            "color_name": [faker.color_name() for _ in range(color)],
            "color": [faker.color() for _ in range(color)],
            "frame_width": random.randint(130, 150),
            "bridge": random.randint(19, 23),
            "lens_width": random.randint(52, 55),
            "lens_height": random.randint(46, 50),
            "temple_length": random.randint(142, 150),
            "price": random.randint(100000, 1000000),
            "sold": random.randint(0, 10000),
            "description": faker.paragraph(nb_sentences=random.randint(4,6)),
            "stock": random.randint(10, 100),
            "images": [random_model_image] + random_product_images,
            "reviews": [],
            "rating": 0,
            "created_at": created_at
        }

        products.append(product)
    
    result = products_collection.insert_many(products)
    print(f"{count} products inserted.")
    return result.inserted_ids

# Seed Users Collection
def seed_users(count=10):
    users = []

    for _ in range(count):
        # Generate a random number between 1 and 100
        random_avatar_number = random.randint(1, 100)

        # Construct the avatar URL with the random number
        avatar_url = f"https://avatar.iran.liara.run/public/{random_avatar_number}"
        
        user = {
            "name": faker.first_name() + " " + faker.last_name(),
            "email": faker.email(),
            "role": random.choice(["admin", "user"]),
            "password": bcrypt.generate_password_hash("@Verystrongpassword123").decode('utf-8'),
            "photo_profile": avatar_url,
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
            for _ in range(random.randint(1, 4))
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
        cart = []

        for _ in range(random.randint(1, 5)):
            product_id = random.choice(product_ids)
            product = products_collection.find_one({"_id": ObjectId(product_id)})

            if not product or "color" not in product or not product["color"]:
                continue

            color = random.choice(product["color"])
            quantity = random.randint(1, 2)

            cart.append({
                "product_id": product_id,
                "color": color,
                "quantity": quantity
            })

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
                "product_id": random.choice(product_ids)
            }
            for _ in range(random.randint(1, 9))
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
                "comment": faker.paragraph(nb_sentences=random.randint(3, 6)),
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
    product_ids = seed_products(2000)                     # Step 1: Seed Products
    user_ids = seed_users(120)                            # Step 2: Seed Users
    seed_transactions(user_ids, product_ids, 5)         # Step 3: Seed Transactions
    update_cart_for_users(user_ids, product_ids)        # Step 4: Update Cart
    update_wishlist_for_users(user_ids, product_ids)    # Step 5: Update Wishlist
    add_reviews_to_products(user_ids, product_ids)      # Step 6: Add Reviews
