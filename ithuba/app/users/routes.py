from flask import render_template, redirect, url_for, session, flash, request
from . import users_bp
from ..db import get_db

def require_role(allowed_roles):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if role not in allowed_roles:
                flash("Access denied", "danger")
                return redirect(url_for("auth.login"))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

@users_bp.route("/dashboard")
@require_role(["owner", "middleman", "provider", "client", "viewer"])
def dashboard():
    role = session.get("role")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if role == "owner":
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS pending FROM user_approvals WHERE status='pending'")
        pending_approvals = cursor.fetchone()["pending"]

        cursor.execute("SELECT COUNT(*) AS requests FROM service_requests")
        total_requests = cursor.fetchone()["requests"]

        cursor.close()
        db.close()

        return render_template(
            "dashboard.html",
            role=role,
            total_users=total_users,
            pending_approvals=pending_approvals,
            total_requests=total_requests
        )

    cursor.close()
    db.close()
    return render_template("dashboard.html", role=role)

@users_bp.route("/manage", methods=["GET", "POST"])
@require_role(["owner"])
def manage_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        user_id = request.form.get("user_id")
        action = request.form.get("action")

        if action == "activate":
            cursor.execute("UPDATE users SET status = 'active' WHERE id = %s", (user_id,))
        elif action == "suspend":
            cursor.execute("UPDATE users SET status = 'suspended' WHERE id = %s", (user_id,))
        elif action == "terminate":
            cursor.execute("UPDATE users SET status = 'terminated' WHERE id = %s", (user_id,))
        else:
            flash("Invalid action", "danger")

        db.commit()

        # 🔥 Always redirect after POST to avoid None return
        return redirect(url_for("users.manage_users"))

    # GET request → show the page
    cursor.execute("SELECT * FROM users WHERE role IN ('middleman','provider','client')")
    users = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("users/manage_users.html", users=users)