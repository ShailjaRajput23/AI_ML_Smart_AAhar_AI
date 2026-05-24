from flask import Flask, render_template, request, jsonify, redirect, session, flash, url_for
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Dense
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from PIL import Image
import numpy as np
import os
import re
import uuid
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# -----------------------------------
# SECRET KEY
# -----------------------------------

app.secret_key = os.getenv("SECRET_KEY", "secret123")
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "10"))
app.permanent_session_lifetime = timedelta(minutes=SESSION_TIMEOUT_MINUTES)

# -----------------------------------
# UPLOAD FOLDER
# -----------------------------------

UPLOAD_FOLDER = "uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MIN_FOOD_CONFIDENCE = float(os.getenv("MIN_FOOD_CONFIDENCE", "0.70"))

# -----------------------------------
# LOAD AI MODEL
# -----------------------------------

class DenseCompat(Dense):
    @classmethod
    def from_config(cls, config):
        config.pop("quantization_config", None)
        return super().from_config(config)


model = load_model(
    "model/gujarati_food_model.keras",
    custom_objects={"Dense": DenseCompat},
    compile=False
)
# -----------------------------------
# CLASS LABELS
# CHANGE THESE ACCORDING TO YOUR MODEL
# -----------------------------------

# IMPORTANT:
# Keep this order aligned with train_dataset.class_indices order used during training.
# For flow_from_directory, classes are sorted alphabetically by folder name.
CLASS_NAMES = [
    "bhajiya",
    "dal_dhokli",
    "dhokla",
    "fafda",
    "gathiya",
    "gulab_jambu",
    "handvo",
    "jalebi",
    "kachori",
    "samosa",
    "thepla",
]

FOOD_INFO = {
    "thepla": {
        "calories": "150 kcal",
        "protein": "5g",
        "fat": "3g",
        "benefits": "Healthy breakfast, rich in fiber",
        "suggestion": "Eat with curd or pickle",
        "healthy_alternative": "Methi Thepla with less oil",
    },
    "gulab_jambu": {
        "calories": "300 kcal",
        "protein": "4g",
        "fat": "12g",
        "benefits": "Provides quick energy",
        "suggestion": "Eat in small quantity due to high sugar",
        "healthy_alternative": "Fruit Salad or Dry Fruit Ladoo",
    },
    "jalebi": {
        "calories": "250 kcal",
        "protein": "2g",
        "fat": "10g",
        "benefits": "Instant energy source",
        "suggestion": "Avoid excess sugar intake",
        "healthy_alternative": "Dates or Honey Oats",
    },
    "fafda": {
        "calories": "320 kcal",
        "protein": "7g",
        "fat": "15g",
        "benefits": "Traditional Gujarati snack",
        "suggestion": "Eat occasionally",
        "healthy_alternative": "Roasted Khakhra",
    },
    "gathiya": {
        "calories": "350 kcal",
        "protein": "6g",
        "fat": "18g",
        "benefits": "Good energy snack",
        "suggestion": "Avoid excess oily food",
        "healthy_alternative": "Roasted Chana",
    },
    "bhajiya": {
        "calories": "280 kcal",
        "protein": "5g",
        "fat": "14g",
        "benefits": "Popular tea-time snack",
        "suggestion": "Consume less fried food",
        "healthy_alternative": "Vegetable Soup or Salad",
    },
    "samosa": {
        "calories": "260 kcal",
        "protein": "4g",
        "fat": "17g",
        "benefits": "Provides fullness",
        "suggestion": "Avoid regular consumption",
        "healthy_alternative": "Baked Samosa",
    },
    "kachori": {
        "calories": "300 kcal",
        "protein": "5g",
        "fat": "16g",
        "benefits": "Traditional snack",
        "suggestion": "Eat occasionally",
        "healthy_alternative": "Sprouts Chaat",
    },
    "dal_dhokli": {
        "calories": "220 kcal",
        "protein": "8g",
        "fat": "6g",
        "benefits": "Rich in protein and carbs",
        "suggestion": "Best served hot",
        "healthy_alternative": "Moong Dal Khichdi",
    },
    "handvo": {
        "calories": "220 kcal",
        "protein": "8g",
        "fat": "6g",
        "benefits": "High protein and healthy",
        "suggestion": "Eat with green chutney",
        "healthy_alternative": "Vegetable Handvo with less oil",
    },
    "dhokla": {
        "calories": "180 kcal",
        "protein": "6g",
        "fat": "4g",
        "benefits": "Steamed and lighter than fried snacks",
        "suggestion": "Pair with mint chutney and salad",
        "healthy_alternative": "Ragi Dhokla",
    },
}

# -----------------------------------
# MONGODB ATLAS CONNECTION
# -----------------------------------

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/").strip()

users_collection = None
predictions_collection = None
local_users = {}
local_predictions = []

if mongo_uri and "YOUR_MONGODB_CONNECTION_STRING" not in mongo_uri:
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        db = client["food_ai"]
        users_collection = db["users"]
        predictions_collection = db["predictions"]
        users_collection.create_index("email", unique=True)
        predictions_collection.create_index([("user", 1), ("created_at", -1)])
    except Exception:
        users_collection = None
        predictions_collection = None

# -----------------------------------
# PASSWORD HASHING
# -----------------------------------

bcrypt = Bcrypt(app)
serializer = URLSafeTimedSerializer(app.secret_key)


def normalize_email(email):
    return email.strip().lower()


def normalize_food_key(label):
    return label.strip().lower().replace(" ", "_")


def humanize_food_label(label):
    return label.replace("_", " ").title()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_registration_fields(username, email, password, confirm_password):
    errors = []
    if len(username.strip()) < 3:
        errors.append("Username must be at least 3 characters.")
    if len(username.strip()) > 30:
        errors.append("Username must be less than 30 characters.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("Please enter a valid email address.")
    errors.extend(validate_password_fields(password, confirm_password))
    return errors


def validate_password_fields(password, confirm_password):
    errors = []
    if password != confirm_password:
        errors.append("Password and confirm password do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must include a lowercase letter.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must include an uppercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must include a number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must include a special character.")
    return errors


def get_user(email):
    if users_collection is not None:
        return users_collection.find_one({"email": email})
    return local_users.get(email)


def create_user(user_doc):
    if users_collection is not None:
        users_collection.insert_one(user_doc)
    else:
        local_users[user_doc["email"]] = user_doc


def save_prediction_record(prediction_doc):
    if predictions_collection is not None:
        predictions_collection.insert_one(prediction_doc)
    else:
        local_predictions.append(prediction_doc)


def get_recent_predictions(email, limit=5):
    if predictions_collection is not None:
        return list(
            predictions_collection.find({"user": email}).sort("created_at", -1).limit(limit)
        )
    matches = [p for p in local_predictions if p["user"] == email]
    return sorted(matches, key=lambda x: x["created_at"], reverse=True)[:limit]


def send_mail(subject, recipient, body):
    mail_server = os.getenv("MAIL_SERVER", "").strip()
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME", "").strip()
    mail_password = os.getenv("MAIL_PASSWORD", "").strip()
    mail_from = os.getenv("MAIL_FROM", mail_username or "noreply@smartaahar.local")
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    if not mail_server:
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = recipient
    msg.set_content(body)
    try:
        with smtplib.SMTP(mail_server, mail_port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if mail_username and mail_password:
                server.login(mail_username, mail_password)
            server.send_message(msg)
        return True
    except Exception:
        return False


def store_reset_token(email, token):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    if users_collection is not None:
        users_collection.update_one(
            {"email": email},
            {"$set": {"reset_token": token, "reset_expires_at": expires_at}},
        )
    else:
        if email in local_users:
            local_users[email]["reset_token"] = token
            local_users[email]["reset_expires_at"] = expires_at


def clear_reset_token_and_set_password(email, new_password_hash):
    if users_collection is not None:
        users_collection.update_one(
            {"email": email},
            {
                "$set": {"password": new_password_hash},
                "$unset": {"reset_token": "", "reset_expires_at": ""},
            },
        )
    else:
        if email in local_users:
            local_users[email]["password"] = new_password_hash
            local_users[email].pop("reset_token", None)
            local_users[email].pop("reset_expires_at", None)


@app.context_processor
def inject_template_globals():
    return {
        "session_timeout_minutes": SESSION_TIMEOUT_MINUTES,
    }


@app.before_request
def enforce_inactivity_timeout():
    if request.endpoint == "static":
        return None
    if "user" not in session:
        return None

    now = datetime.now(timezone.utc)
    last_activity = session.get("last_activity_ts")
    if last_activity:
        try:
            last_activity_dt = datetime.fromisoformat(last_activity)
            if (now - last_activity_dt) > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                session.clear()
                flash("You were logged out due to 10 minutes of inactivity.", "error")
                return redirect(url_for("login"))
        except Exception:
            session["last_activity_ts"] = now.isoformat()

    session["last_activity_ts"] = now.isoformat()
    return None

# -----------------------------------
# HOME PAGE
# -----------------------------------

@app.route('/')
def home():

    return render_template("home.html")

# -----------------------------------
# REGISTER PAGE
# -----------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username', '').strip()

        email = normalize_email(request.form.get('email', ''))

        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = validate_registration_fields(username, email, password, confirm_password)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("register.html", form_data={"username": username, "email": email})

        existing_user = get_user(email)

        if existing_user:
            flash("Email is already registered.", "error")
            return render_template("register.html", form_data={"username": username, "email": email})

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')

        try:
            create_user({
                "username": username,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.now(timezone.utc)
            })
        except DuplicateKeyError:
            flash("Email is already registered.", "error")
            return render_template("register.html", form_data={"username": username, "email": email})

        send_mail(
            "Welcome to SmartAahar AI",
            email,
            f"Hello {username},\n\nYour account was created successfully. You can now login and predict Gujarati food dishes.\n",
        )

        flash("Registration successful. Please login.", "success")
        return redirect('/login')

    return render_template("register.html")

# -----------------------------------
# LOGIN PAGE
# -----------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'user' in session:
        return redirect('/dashboard')

    if request.method == 'POST':

        email = normalize_email(request.form.get('email', ''))

        password = request.form.get('password', '')

        user = get_user(email)

        if user and bcrypt.check_password_hash(
            user['password'],
            password
        ):

            session.permanent = True
            session['user'] = email
            session['username'] = user.get("username", "User")
            session['last_activity_ts'] = datetime.now(timezone.utc).isoformat()

            return redirect('/dashboard')

        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")

# -----------------------------------
# DASHBOARD
# -----------------------------------

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    recent_predictions = get_recent_predictions(session['user'])
    return render_template("index.html", recent_predictions=recent_predictions, username=session.get("username", "User"))

# -----------------------------------
# PREDICTION ROUTE
# -----------------------------------

@app.route('/predict', methods=['POST'])
def predict():

    if 'user' not in session:
        return jsonify({"error": "Please login first."}), 401

    file = request.files.get('image')
    if file is None or file.filename == "":
        return jsonify({"error": "Please upload an image file."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only png, jpg, jpeg, and webp files are allowed."}), 400

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    file.save(filepath)

    # -----------------------------------
    # IMAGE PREPROCESSING
    # -----------------------------------

    image = Image.open(filepath).convert('RGB')

    image = image.resize((224, 224))

    image_array = np.array(image) / 255.0

    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    # -----------------------------------
    # AI PREDICTION
    # -----------------------------------

    prediction = model.predict(image_array, verbose=0)
    probabilities = prediction[0]
    prediction_index = int(np.argmax(probabilities))

    class_names = CLASS_NAMES
    labels_aligned = len(class_names) == len(probabilities)
    if not labels_aligned:
        class_names = [f"class_{idx}" for idx in range(len(probabilities))]

    predicted_class_raw = class_names[prediction_index]
    predicted_key = normalize_food_key(predicted_class_raw)
    predicted_class = humanize_food_label(predicted_class_raw)
    confidence = float(np.max(probabilities))

    top_k_indices = np.argsort(probabilities)[::-1][:3]
    top_predictions = [
        {
            "label": humanize_food_label(class_names[idx]),
            "confidence": float(probabilities[idx]),
        }
        for idx in top_k_indices
    ]
    food_details = FOOD_INFO.get(predicted_key, {})
    is_food = confidence >= MIN_FOOD_CONFIDENCE

    # -----------------------------------
    # STORE RESULT IN DATABASE
    # -----------------------------------

    prediction_doc = {
        "user": session['user'],
        "image": filename,
        "prediction": predicted_class,
        "confidence": confidence,
        "prediction_key": predicted_key,
        "is_food": is_food,
        "created_at": datetime.now(timezone.utc)
    }
    save_prediction_record(prediction_doc)

    # -----------------------------------
    # RETURN RESULT
    # -----------------------------------

    return jsonify({

        "prediction": predicted_class,
        "prediction_key": predicted_key,

        "confidence": confidence,
        "is_food": is_food,
        "min_food_confidence": MIN_FOOD_CONFIDENCE,
        "top_predictions": top_predictions,
        "model_output_classes": int(len(probabilities)),
        "labels_aligned": labels_aligned,
        "food_details": food_details if is_food else {},
        "message": (
            "Image does not look like a supported Gujarati food dish. Please upload a clear single-food image."
            if not is_food
            else ""
        ),
        "suggestions": [
            (
                food_details.get("suggestion", "Use smaller portion sizes.")
                if is_food
                else "Try uploading a clear food image with one main dish."
            ),
            "Pair with salad or fiber-rich foods.",
            (
                food_details.get("healthy_alternative", "Prefer steaming or less-oil cooking methods.")
                if is_food
                else "Avoid selfies, group photos, or background-heavy photos."
            ),
        ]

    })


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = normalize_email(request.form.get('email', ''))
        user = get_user(email)
        if user:
            token = serializer.dumps(email, salt="password-reset")
            store_reset_token(email, token)
            reset_url = url_for("reset_password", token=token, _external=True)
            send_mail(
                "SmartAahar Password Reset",
                email,
                f"Click this link to reset your password (valid for 15 minutes):\n{reset_url}",
            )
        flash("If the email exists, a reset link has been sent.", "success")
        return redirect('/login')
    return render_template("forgot_password.html")


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset", max_age=900)
    except (BadSignature, SignatureExpired):
        flash("Reset link is invalid or expired.", "error")
        return redirect('/forgot-password')

    user = get_user(email)
    if not user:
        flash("Reset link is invalid or expired.", "error")
        return redirect('/forgot-password')

    stored_token = user.get("reset_token")
    stored_expiry = user.get("reset_expires_at")
    if stored_token != token:
        flash("Reset link is invalid or expired.", "error")
        return redirect('/forgot-password')
    if stored_expiry and datetime.now(timezone.utc) > stored_expiry:
        flash("Reset link has expired.", "error")
        return redirect('/forgot-password')

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        errors = validate_password_fields(password, confirm_password)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("reset_password.html")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        clear_reset_token_and_set_password(email, hashed_password)
        flash("Password reset successful. Please login.", "success")
        return redirect('/login')

    return render_template("reset_password.html")

# -----------------------------------
# LOGOUT
# -----------------------------------

@app.route('/logout')
def logout():

    session.pop('user', None)
    session.pop('username', None)

    return redirect('/login')


@app.route('/session/ping', methods=['POST'])
def session_ping():
    if 'user' not in session:
        return jsonify({"ok": False, "authenticated": False}), 401
    return jsonify({"ok": True, "authenticated": True})


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Image is too large. Max file size is 5MB."}), 413

# -----------------------------------
# RUN FLASK
# -----------------------------------

if __name__ == "__main__":

    app.run(debug=True, port=int(os.getenv("PORT", "5051")))