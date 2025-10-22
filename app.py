from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import re

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")

# SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studenttracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ---------------------- MODELS ---------------------- #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    last_lat = db.Column(db.Float, nullable=True)
    last_lng = db.Column(db.Float, nullable=True)
    last_accuracy = db.Column(db.Float, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("locations", lazy="dynamic"))


with app.app_context():
    db.create_all()


# ---------------------- UTILITIES ---------------------- #
def format_dt(dt):
    if not dt:
        return "-"
    s = dt.strftime("%b %d, %Y %I:%M %p")
    s = re.sub(r"\b0([0-9]):", r"\1:", s)
    s = s.replace("AM", "am").replace("PM", "pm")
    return s


app.jinja_env.filters["format_dt"] = format_dt


# ---------------------- ROUTES ---------------------- #
@app.route("/")
def landing_page():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()

        if not username or not password:
            return render_template("register.html", error="Username and password required")
        if not email:
            return render_template("register.html", error="Email is required")

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already taken")
        if email and User.query.filter_by(email=email).first():
            return render_template("register.html", error="Email already registered")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        if not identifier:
            identifier = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Username/email and password required")
            return render_template("login.html", error="Username/email and password required")

        user = User.query.filter_by(username=identifier).first()
        if not user:
            user = User.query.filter_by(email=identifier).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")
        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("landing_page"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = User.query.get(session.get("user_id"))
    if not user:
        session.pop("user_id", None)
        session.pop("username", None)
        flash("Session invalid — please log in again.")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session.get("username"),
        last_lat=user.last_lat,
        last_lng=user.last_lng,
        last_accuracy=user.last_accuracy,
        last_seen=user.last_seen,
    )


@app.route("/update_location", methods=["POST"])
def update_location():
    if not session.get("user_id"):
        return jsonify({"error": "not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    try:
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
        acc = float(data.get("accuracy")) if data.get("accuracy") is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "invalid data"}), 400

    user = User.query.get(session.get("user_id"))
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Update user's last known location
    user.last_lat = lat
    user.last_lng = lng
    user.last_accuracy = acc
    user.last_seen = datetime.utcnow()

    # Reverse geocode to get city/town name
    city = None
    try:
        headers = {"User-Agent": "StudentTracker/1.0 (contact@example.com)"}
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}&zoom=10&addressdetails=1"
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.ok:
            j = resp.json()
            addr = j.get("address", {}) if isinstance(j, dict) else {}

            # Fixed: pick best available populated area (not local features)
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("municipality")
                or addr.get("hamlet")
                or addr.get("county")
                or addr.get("state")
                or "Unknown"
            )

    except Exception as e:
        app.logger.warning("Reverse geocode failed: %s", e)
        city = "Unknown"

    # Save the location in the database
    loc = Location(user_id=user.id, lat=lat, lng=lng, accuracy=acc, city=city)
    db.session.add(loc)
    db.session.commit()

    return jsonify({"success": True, "city": city}), 200


@app.route("/database")
def database():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    users = User.query.all()
    locations = Location.query.order_by(Location.created_at.desc()).limit(100).all()
    return render_template("database.html", users=users, locations=locations)


if __name__ == "__main__":
    app.run(debug=True)
