from flask import Flask, redirect, url_for
from .config import SECRET_KEY
from .auth import auth_bp
from .users import users_bp
from .services import services_bp



def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(services_bp)

    # Root route
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app