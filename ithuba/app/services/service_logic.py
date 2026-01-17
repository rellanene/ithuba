from ..db import get_db

def get_all_requests():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT sr.*, u.email AS provider_email
        FROM service_requests sr
        JOIN users u ON sr.provider_id = u.id
        ORDER BY sr.created_at DESC
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows

def get_request_by_id(request_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT sr.*, p.email AS provider_email, c.email AS client_email
        FROM service_requests sr
        JOIN users p ON sr.provider_id = p.id
        LEFT JOIN users c ON sr.client_id = c.id
        WHERE sr.id = %s
        """,
        (request_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row