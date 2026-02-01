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

@users_bp.route("/add", methods=["GET", "POST"])
@require_role(["owner"])
def add_user():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO users (email, password, role, status)
            VALUES (%s, %s, %s, 'pending')
        """, (email, password, role))

        db.commit()

        flash("User added successfully and is now pending approval.", "success")
        return redirect(url_for("users.manage_users"))

    return render_template("users/add_user.html")

@users_bp.route("/approvals", methods=["GET", "POST"])
@require_role(["owner"])
def approvals():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        request_id = request.form.get("request_id")
        decision = request.form.get("decision")
        cursor.execute(
            "UPDATE user_approvals SET status = %s WHERE id = %s",
            (decision, request_id),
        )
        db.commit()

    cursor.execute("""
        SELECT ua.id, u.email, u.role, ua.status
        FROM user_approvals ua
        JOIN users u ON ua.user_id = u.id
        WHERE ua.status = 'pending'
    """)
    pending = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("users/approvals.html", approvals=pending)

@users_bp.route("/dashboard")
@require_role(["owner", "middleman", "provider", "client", "viewer"])
def dashboard():
    role = session.get("role")
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # ---------- OWNER-SPECIFIC METRICS ----------
    total_users = None
    pending_approvals = None

    if role == "owner":
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS pending FROM user_approvals WHERE status='pending'")
        pending_approvals = cursor.fetchone()["pending"]

    # ---------- ANALYTICS FOR ALL ROLES ----------
    cursor.execute("SELECT COUNT(*) AS total FROM service_requests")
    total_requests = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT status, COUNT(*) AS count
        FROM service_requests
        GROUP BY status
    """)
    status_counts = cursor.fetchall()

    cursor.execute("""
        SELECT st.name AS type, COUNT(*) AS count
        FROM service_requests sr
        JOIN service_types st ON sr.service_type_id = st.id
        GROUP BY st.name
    """)
    type_counts = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        role=role,
        total_users=total_users,
        pending_approvals=pending_approvals,
        total_requests=total_requests,
        status_counts=status_counts,
        type_counts=type_counts
    )



@users_bp.route("/profile")
@require_role(["owner", "middleman", "provider", "client", "viewer"])
def profile():
    user_id = session.get("user_id")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, email, role, status FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    return render_template("users/profile.html", user=user)

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