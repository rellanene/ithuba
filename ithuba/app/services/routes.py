from flask import render_template, request, redirect, url_for, session, flash
from . import services_bp
from .service_logic import get_all_requests, get_request_by_id
from ..db import get_db
from ..users.routes import require_role


# ---------------- CREATE SERVICE REQUEST ----------------
@services_bp.route("/create", methods=["GET", "POST"])
@require_role(["owner", "middleman", "client", "provider"])
def create_request():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Load service types for dropdown
    cursor.execute("SELECT * FROM service_types ORDER BY name ASC")
    types = cursor.fetchall()

    if request.method == "POST":
        service_type = request.form["service_type"]
        description = request.form["description"]

        cursor2 = db.cursor()
        cursor2.execute("""
            INSERT INTO service_requests (service_type_id, description, status)
            VALUES (%s, %s, 'pending')
        """, (service_type, description))

        db.commit()
        return redirect(url_for("services.list_requests"))

    return render_template("services/create_request.html", types=types)


# ---------------- LIST SERVICE REQUESTS ----------------
@services_bp.route("/list")
@require_role(["provider", "client", "viewer", "middleman", "owner"])
def list_requests():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT sr.id, st.name AS service_type, sr.description, sr.status, sr.created_at
        FROM service_requests sr
        JOIN service_types st ON sr.service_type_id = st.id
        ORDER BY sr.created_at DESC
    """)
    requests = cursor.fetchall()

    return render_template("services/list_requests.html", requests=requests)


# ---------------- ADD SERVICE TYPE ----------------
@services_bp.route("/types/add", methods=["GET", "POST"])
def add_service_type():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO service_types (name, description)
            VALUES (%s, %s)
        """, (name, description))

        db.commit()

        flash("Service type added successfully!", "success")
        return redirect(url_for("services.list_service_types"))

    return render_template("services/add_service_type.html")


# ---------------- LIST SERVICE TYPES ----------------
@services_bp.route("/types")
def list_service_types():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM service_types ORDER BY name ASC")
    types = cursor.fetchall()

    return render_template("services/list_service_types.html", types=types)


# ---------------- REQUEST DETAIL (CLIENT) ----------------
@services_bp.route("/<int:request_id>", methods=["GET", "POST"])
@require_role(["client"])
def request_detail(request_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        decision = request.form.get("decision")
        client_id = session.get("user_id")

        if decision == "accept":
            cursor.execute("""
                UPDATE service_requests
                SET status = 'accepted_by_client', client_id = %s
                WHERE id = %s
            """, (client_id, request_id))

        elif decision == "decline":
            cursor.execute(
                "UPDATE service_requests SET status = 'declined_by_client' WHERE id = %s",
                (request_id,)
            )

        db.commit()

    cursor.close()
    db.close()

    req = get_request_by_id(request_id)
    return render_template("services/request_detail.html", req=req)

@services_bp.route("/owner", methods=["GET", "POST"])
@require_role(["owner"])
def owner_panel():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        request_id = request.form.get("request_id")
        decision = request.form.get("decision")

        if decision == "approve":
            cursor.execute(
                "UPDATE service_requests SET status = 'approved_by_owner' WHERE id = %s",
                (request_id,)
            )
        elif decision == "decline":
            cursor.execute(
                "UPDATE service_requests SET status = 'declined_by_owner' WHERE id = %s",
                (request_id,)
            )

        db.commit()

    cursor.execute("""
        SELECT sr.id, st.name AS service_type, sr.description, sr.status, sr.created_at
        FROM service_requests sr
        JOIN service_types st ON sr.service_type_id = st.id
        ORDER BY sr.created_at DESC
    """)
    items = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("services/owner_panel.html", requests=items)


# ---------------- MIDDLEMAN PANEL ----------------
@services_bp.route("/middleman", methods=["GET", "POST"])
@require_role(["middleman"])
def middleman_panel():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        request_id = request.form.get("request_id")
        decision = request.form.get("decision")

        if decision == "approve":
            cursor.execute(
                "UPDATE service_requests SET status = 'approved_by_middleman' WHERE id = %s",
                (request_id,)
            )
        elif decision == "decline":
            cursor.execute(
                "UPDATE service_requests SET status = 'declined_by_middleman' WHERE id = %s",
                (request_id,)
            )

        db.commit()

    cursor.execute("""
        SELECT * FROM service_requests
        WHERE status IN ('pending_middleman', 'approved_by_middleman')
    """)
    items = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("services/list_requests.html", requests=items)