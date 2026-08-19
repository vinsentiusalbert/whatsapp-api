from wa_app.database import get_db
from wa_app.utils import safe_json_dumps


MESSAGE_COLUMNS = """
    id, direction, message_id, sender, receiver, sender_name,
    message_type, message, status, http_status, created_at
"""
MESSAGE_BY_PHONE_COLUMNS = """
    id, message_id, sender, receiver, sender_name,
    message_type, message, created_at
"""


def save_outbound(sender, receiver, message, status, http_status, raw_payload=None, message_id=None):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO whatsapp_messages
                    (direction, message_id, sender, receiver, sender_name,
                     message_type, message, status, http_status, raw_payload, created_at)
                VALUES ('OUTBOUND', %s, %s, %s, NULL, 'text', %s, %s, %s, %s, NOW())
                """,
                (message_id, sender, receiver, message, status, http_status,
                 safe_json_dumps(raw_payload)),
            )
    finally:
        connection.close()


def save_inbound(sender=None, receiver=None, sender_name=None, message_id=None,
                 message_type=None, message=None, raw_payload=None):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO whatsapp_messages
                    (direction, message_id, sender, receiver, sender_name,
                     message_type, message, status, http_status, raw_payload, created_at)
                VALUES ('INBOUND', %s, %s, %s, %s, %s, %s, 'RECEIVED', 200, %s, NOW())
                """,
                (message_id, sender, receiver, sender_name, message_type, message,
                 safe_json_dumps(raw_payload)),
            )
    finally:
        connection.close()


def list_inbound(limit: int, phone: str | None = None):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            where = "WHERE direction = 'INBOUND'"
            params = []
            if phone is not None:
                where += " AND receiver = %s"
                params.append(phone)
            params.append(limit)
            columns = MESSAGE_BY_PHONE_COLUMNS if phone is not None else MESSAGE_COLUMNS
            cursor.execute(
                f"SELECT {columns} FROM whatsapp_messages "
                f"{where} ORDER BY id DESC LIMIT %s",
                tuple(params),
            )
            return cursor.fetchall()
    finally:
        connection.close()


def start_myads_session(phone: str, status: str = "WAITING_MODE"):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO myads_campaign_sessions (phone, status, campaign_payload, last_error)
                VALUES (%s, %s, NULL, NULL)
                ON DUPLICATE KEY UPDATE status = VALUES(status), campaign_payload = NULL,
                    last_error = NULL, updated_at = NOW()
                """,
                (phone, status),
            )
    finally:
        connection.close()


def get_myads_session(phone: str):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, phone, status, campaign_payload, last_error, created_at, updated_at
                   FROM myads_campaign_sessions WHERE phone = %s LIMIT 1""",
                (phone,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def update_myads_session(phone: str, *, status: str | None = None,
                         payload: dict | None = None, error: str | None = None):
    fields = ["updated_at = NOW()"]
    values = []
    if status is not None:
        fields.append("status = %s")
        values.append(status)
    if payload is not None:
        fields.append("campaign_payload = %s")
        values.append(safe_json_dumps(payload))
    if error is not None:
        fields.append("last_error = %s")
        values.append(error)
    elif payload is not None:
        fields.append("last_error = NULL")
    values.append(phone)

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE myads_campaign_sessions SET {', '.join(fields)} WHERE phone = %s",
                tuple(values),
            )
    finally:
        connection.close()
