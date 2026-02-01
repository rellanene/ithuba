from flask import Flask, render_template, send_from_directory
from .config import SECRET_KEY
from .auth import auth_bp
from .users import users_bp
from .services import services_bp
import os

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "docx", "xlsx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # -------------------------
    # FILE UPLOAD CONFIG
    # -------------------------
    app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

    # Create uploads folder if missing
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    # -------------------------
    # BLUEPRINTS
    # -------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(services_bp)

    # -------------------------
    # STATIC FILE SERVING
    # -------------------------
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # -------------------------
    # LANDING PAGE
    # -------------------------
    @app.route("/")
    def index():
        return render_template("landing.html")

    return app