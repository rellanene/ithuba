from flask import render_template, request, redirect, url_for, session, flash
from . import services_bp
from .service_logic import get_all_requests, get_request_by_id
from ..db import get_db
from ..users.routes import require_role


# 3rd layer: provider posts service needed
@services_bp.route("/create", methods=["GET", "POST"])
@require_role(["provider"])
def create_request():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        provider_id = session.get("user_id")

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO service_requests (provider_id, title, description, status)
            VALUES (%s, %s, %s, 'pending_middleman')
            """,
            (provider_id, title, description),
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Service request created", "success")
        return redirect(url_for("services.list_requests"))

    return render_template("services/create_request.html")


# 3rd, 4th, 5th layer: view all requests
@services_bp.route("/list")
@require_role(["provider", "client", "viewer", "middleman", "owner"])
def list_requests():
    requests = get_all_requests()
    return render_template("services/list_requests.html", requests=requests)


# 4th layer: client accepts/declines
@services_bp.route("/<int:request_id>", methods=["GET", "POST"])
@require_role(["client"])
def request_detail(request_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        decision = request.form.get("decision")
        client_id = session.get("user_id")

        if decision == "accept":
            cursor.execute(
                """
                UPDATE service_requests
                SET status = 'accepted_by_client', client_id = %s
                WHERE id = %s
                """,
                (client_id, request_id),
            )
        elif decision == "decline":
            cursor.execute(
                "UPDATE service_requests SET status = 'declined_by_client' WHERE id = %s",
                (request_id,),
            )
        db.commit()

    cursor.close()
    db.close()

    req = get_request_by_id(request_id)
    return render_template("services/request_detail.html", req=req)


# 2nd layer: middleman approves/declines service flow
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
                (request_id,),
            )
        elif decision == "decline":
            cursor.execute(
                "UPDATE service_requests SET status = 'declined_by_middleman' WHERE id = %s",
                (request_id,),
            )
        db.commit()

    cursor.execute(
        "SELECT * FROM service_requests WHERE status IN ('pending_middleman','approved_by_middleman')"
    )
    items = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("services/list_requests.html", requests=items)