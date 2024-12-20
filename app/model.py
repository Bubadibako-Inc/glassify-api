from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from PIL import Image
import numpy as np
import os
import dlib
import cv2
import time
import shutil
import joblib

# Load environment variables from .env file
load_dotenv()

UPLOAD_FOLDER = "uploads/predict"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
users = db["users"]
products = db["products"]

# Create a Blueprint for model
model_bp = Blueprint('model', __name__)

predictor_path = 'shape_predictor_68_face_landmarks.dat'
scaler_path = 'models/scaler.pkl'
model_path = 'models/model.pkl'

scaler = joblib.load(scaler_path)
model = joblib.load(model_path)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

def detect_facial_landmarks(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    if len(faces) == 0:
        return None

    face = faces[0]
    landmarks = predictor(gray, face)
    landmark_points = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(68)]
    return np.array(landmark_points)

def extract_features_from_landmarks(landmarks):
    features = []

    # Rasio jarak antar landmark (fitur awal)
    features.append(np.linalg.norm(landmarks[9] - landmarks[18]) / np.linalg.norm(landmarks[1] - landmarks[17]))
    features.append(np.linalg.norm(landmarks[5] - landmarks[13]) / np.linalg.norm(landmarks[1] - landmarks[17]))
    features.append(np.linalg.norm(landmarks[9] - landmarks[19]) / np.linalg.norm(landmarks[5] - landmarks[13]))

    # Sudut landmark terhadap dagu
    for i in range(4, 12):
        x1, y1 = landmarks[i - 3]
        x2, y2 = landmarks[9]
        features.append(np.arctan2(x1 - x2, y1 - y2))

    for i in range(12, 20):
        x1, y1 = landmarks[i - 2]
        x2, y2 = landmarks[9]
        features.append(np.arctan2(x1 - x2, y1 - y2))

    # Fitur tambahan awal
    features.append(np.linalg.norm(landmarks[36] - landmarks[45]))  # Jarak antara mata
    features.append(np.linalg.norm(landmarks[48] - landmarks[54]))  # Lebar mulut
    features.append(np.linalg.norm(landmarks[27] - landmarks[8]))  # Tinggi dahi ke dagu

    # Proporsi area segitiga (mata kanan, mata kiri, dan dagu)
    triangle_area = 0.5 * np.abs(
        landmarks[36][0] * (landmarks[45][1] - landmarks[8][1]) +
        landmarks[45][0] * (landmarks[8][1] - landmarks[36][1]) +
        landmarks[8][0] * (landmarks[36][1] - landmarks[45][1])
    )
    features.append(triangle_area)

    # Proporsi lebar wajah terhadap tinggi wajah
    width = np.linalg.norm(landmarks[1] - landmarks[17])  # Lebar wajah
    height = np.linalg.norm(landmarks[27] - landmarks[8])  # Tinggi wajah
    features.append(width / height)

    # Simetri wajah (rata-rata jarak landmark kiri-kanan)
    left_points = [36, 37, 38, 39, 40, 41]  # Mata kiri
    right_points = [42, 43, 44, 45, 46, 47]  # Mata kanan
    symmetry = np.mean([
        np.abs(np.linalg.norm(landmarks[left_points[i]] - landmarks[27]) -
               np.linalg.norm(landmarks[right_points[i]] - landmarks[27]))
        for i in range(len(left_points))
    ])
    features.append(symmetry)

    # Rasio lebar mulut terhadap tinggi mulut
    mouth_width = np.linalg.norm(landmarks[48] - landmarks[54])  # Lebar mulut
    mouth_height = np.linalg.norm(landmarks[51] - landmarks[57])  # Tinggi mulut
    features.append(mouth_width / mouth_height)

    # Sudut antara kedua mata dan hidung
    eye_center = (landmarks[36] + landmarks[45]) / 2  # Titik tengah antara mata
    nose_tip = landmarks[33]  # Ujung hidung
    eye_to_nose_angle = np.arctan2(nose_tip[1] - eye_center[1], nose_tip[0] - eye_center[0])
    features.append(eye_to_nose_angle)

    return features

@model_bp.route("/predict", methods=["POST"])
def predict():
    # Check if the image file is provided in the request
    if 'picture' not in request.files:
        return jsonify({"message": "Tidak ada gambar yang diupload"}), 400

    # Extract the image file and format
    image_file = request.files['picture']
    image_format = image_file.filename.split('.')[-1].upper()
    
    if image_format == 'JPG':
        image_format = 'JPEG'

    # Generate a unique folder name based on the current epoch time
    epoch_time = int(time.time())
    folder_name = os.path.join(UPLOAD_FOLDER, str(epoch_time))
    os.makedirs(folder_name, exist_ok=True)

    # Save the image to the folder
    image = Image.open(image_file)
    filename = f"{epoch_time}.{image_format.lower()}"
    image_path = os.path.join(folder_name, filename)
    image.save(image_path, format=image_format.upper())

    # Read the image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        try:
            shutil.rmtree(folder_name)
        except Exception as e:
            print(f"Error: {e}")
        return jsonify({"message": "Gambar tidak dapat dibaca"}), 400

    # Detect facial landmarks in the image
    landmarks = detect_facial_landmarks(img)
    if landmarks is None:
        try:
            shutil.rmtree(folder_name)
        except Exception as e:
            print(f"Error: {e}")
        return jsonify({"message": "Tidak ada wajah yang terdeksi"}), 400

    # Extract features from the landmarks and scale them
    features = extract_features_from_landmarks(landmarks)
    features_scaled = scaler.transform([features])

    # Make the prediction using the model
    prediction = model.predict(features_scaled)
    confidence = None
    if hasattr(model, "predict_proba"):
        probas = model.predict_proba(features_scaled)
        confidence = probas.max()  # Get the maximum probability

    # Ensure the prediction and confidence are serializable
    prediction = prediction.item() if isinstance(prediction, np.ndarray) else prediction
    confidence = confidence.item() if isinstance(confidence, np.ndarray) else confidence
    
    confidence = round(confidence, 2)
    
    try:
        shutil.rmtree(folder_name)
    except Exception as e:
        print(f"Error: {e}")
    
    return jsonify({
        "message": "Image uploaded successfully",
        "prediction": prediction,
        "confidence": confidence if confidence is not None else None
    }), 200
