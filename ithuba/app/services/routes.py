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
from werkzeug.utils import secure_filename
from flask import current_app
import os


@services_bp.route("/<int:request_id>", methods=["GET", "POST"])
@require_role(["client", "provider", "middleman", "owner"])
def request_detail(request_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    user_id = session.get("user_id")

    # ---------------- HANDLE POST (message + file) ----------------
    if request.method == "POST":

        # Save message
        if "message" in request.form and request.form["message"].strip():
            msg = request.form["message"]
            cursor.execute("""
                INSERT INTO request_messages (request_id, user_id, message)
                VALUES (%s, %s, %s)
            """, (request_id, user_id, msg))
            db.commit()

        # Save file
        if "file" in request.files:
            file = request.files["file"]

            if file and file.filename.strip():
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                cursor.execute("""
                    INSERT INTO request_files (request_id, user_id, filename)
                    VALUES (%s, %s, %s)
                """, (request_id, user_id, filename))
                db.commit()

    # ---------------- LOAD REQUEST ----------------
    req = get_request_by_id(request_id)

    # ---------------- LOAD MESSAGES ----------------
    cursor.execute("""
        SELECT rm.*, u.email
        FROM request_messages rm
        JOIN users u ON rm.user_id = u.id
        WHERE rm.request_id = %s
        ORDER BY rm.created_at ASC
    """, (request_id,))
    messages = cursor.fetchall()

    # ---------------- LOAD FILES ----------------
    cursor.execute("""
        SELECT rf.*, u.email
        FROM request_files rf
        JOIN users u ON rf.user_id = u.id
        WHERE rf.request_id = %s
        ORDER BY rf.uploaded_at ASC
    """, (request_id,))
    files = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "services/request_detail.html",
        req=req,
        messages=messages,
        files=files
    )

#-----------DASHBOARD-----------
# ----------- DASHBOARD -----------
@services_bp.route("/dashboard")
@require_role(["owner", "middleman"])
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Total counts
    cursor.execute("SELECT COUNT(*) AS total FROM service_requests")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT status, COUNT(*) AS count FROM service_requests GROUP BY status")
    status_counts = cursor.fetchall()

    cursor.execute("""
        SELECT st.name, COUNT(*) AS count
        FROM service_requests sr
        JOIN service_types st ON sr.service_type_id = st.id
        GROUP BY st.name
    """)
    type_counts = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "services/dashboard.html",
        total=total,
        status_counts=status_counts,
        type_counts=type_counts
    )


# ----------- EXPORT TO CSV -----------
@services_bp.route("/export/requests/csv")
@require_role(["owner", "middleman"])
def export_requests_csv():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, client_id, provider_id, service_type_id, status, created_at
        FROM service_requests
    """)
    rows = cursor.fetchall()

    import csv
    from io import StringIO
    from flask import make_response

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Client", "Provider", "Service Type", "Status", "Created At"])

    for r in rows:
        writer.writerow([
            r["id"],
            r["client_id"],
            r["provider_id"],
            r["service_type_id"],
            r["status"],
            r["created_at"]
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=requests.csv"
    response.headers["Content-Type"] = "text/csv"

    return response
    
    

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