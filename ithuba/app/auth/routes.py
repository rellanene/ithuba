from flask import render_template, request, redirect, url_for, session, flash
from . import auth_bp
from ..db import get_db

#----------REDIRECT----------
from flask import redirect, url_for

@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s AND status = 'active'",
            (email, password),
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Logged in successfully", "success")
            return redirect(url_for("users.dashboard"))
        else:
            flash("Invalid credentials or inactive account", "danger")

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()

        # All new accounts are CLIENTS
        cursor.execute("""
            INSERT INTO users (email, password, role, status)
            VALUES (%s, %s, 'client', 'pending')
        """, (email, password))

        db.commit()

        flash("Account created! Waiting for approval.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")




@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))