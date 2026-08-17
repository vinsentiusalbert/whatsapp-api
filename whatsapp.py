import os
import json
import re
import requests
import pymysql

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv


# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

app = FastAPI(
    title="MyWhatsApp + MyAds Campaign Bot",
    version="2.0.0"
)


# =========================================================
# MYWHATSAPP CONFIG
# =========================================================

BASE_URL = os.getenv(
    "MYWHATSAPP_BASE_URL",
    "https://panel.mywhatsapp.my.id"
)

API_KEY = os.getenv("MYWHATSAPP_API_KEY")
DEFAULT_SENDER = os.getenv("MYWHATSAPP_SENDER")


# =========================================================
# DATABASE CONFIG
# =========================================================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "whatsapp_db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


def ensure_tables():
    """
    Table whatsapp_messages diasumsikan sudah ada dari project sebelumnya.
    Table myads_campaign_sessions dibuat otomatis untuk menyimpan state form.
    """
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_messages (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    direction ENUM('INBOUND', 'OUTBOUND') NOT NULL,
                    message_id VARCHAR(255) NULL,
                    sender VARCHAR(100) NULL,
                    receiver VARCHAR(100) NULL,
                    sender_name VARCHAR(255) NULL,
                    message_type VARCHAR(50) DEFAULT 'text',
                    message TEXT NULL,
                    status VARCHAR(50) NULL,
                    http_status INT NULL,
                    raw_payload LONGTEXT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_direction (direction),
                    KEY idx_sender (sender),
                    KEY idx_receiver (receiver),
                    KEY idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS myads_campaign_sessions (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    phone VARCHAR(30) NOT NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'WAITING_FORM',
                    campaign_payload LONGTEXT NULL,
                    last_error TEXT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_myads_campaign_phone (phone)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
    finally:
        connection.close()


@app.on_event("startup")
def startup_event():
    try:
        ensure_tables()
    except Exception as e:
        # Jangan membuat service gagal start hanya karena tabel session belum bisa dibuat.
        # Error tetap terlihat di console untuk debugging.
        print("WARNING ensure_tables:", str(e))


# =========================================================
# MODEL SEND MESSAGE
# =========================================================

class SendMessageRequest(BaseModel):
    receiver: str
    message: str


# =========================================================
# HELPERS
# =========================================================

def normalize_phone(phone: str):
    if not phone:
        return ""

    phone = (
        str(phone)
        .replace("+", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    return phone


def safe_json_dumps(data):
    return json.dumps(data, ensure_ascii=False, default=str)


def find_payload_value(payload, *keys):
    """Cari field webhook pada payload utama atau wrapper yang umum dipakai."""
    if not isinstance(payload, dict):
        return None

    containers = [payload]
    for wrapper_key in ("data", "payload", "event", "messageData"):
        wrapped = payload.get(wrapper_key)
        if isinstance(wrapped, dict):
            containers.append(wrapped)

    # Beberapa provider membungkus data pesan satu tingkat lebih dalam.
    for container in list(containers):
        for wrapper_key in ("data", "payload", "message"):
            wrapped = container.get(wrapper_key)
            if isinstance(wrapped, dict) and wrapped not in containers:
                containers.append(wrapped)

    for container in containers:
        for key in keys:
            value = container.get(key)
            if (
                value is not None
                and value != ""
                and not isinstance(value, (dict, list))
            ):
                return value

    return None


# =========================================================
# SAVE OUTBOUND / INBOUND
# =========================================================

def save_outbound(
    sender,
    receiver,
    message,
    status,
    http_status,
    raw_payload=None,
    message_id=None
):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO whatsapp_messages
                (
                    direction,
                    message_id,
                    sender,
                    receiver,
                    sender_name,
                    message_type,
                    message,
                    status,
                    http_status,
                    raw_payload,
                    created_at
                )
                VALUES
                (
                    'OUTBOUND',
                    %s,
                    %s,
                    %s,
                    NULL,
                    'text',
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
            """

            cursor.execute(
                sql,
                (
                    message_id,
                    sender,
                    receiver,
                    message,
                    status,
                    http_status,
                    safe_json_dumps(raw_payload)
                )
            )
    finally:
        connection.close()


def save_inbound(
    sender=None,
    receiver=None,
    sender_name=None,
    message_id=None,
    message_type=None,
    message=None,
    raw_payload=None
):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO whatsapp_messages
                (
                    direction,
                    message_id,
                    sender,
                    receiver,
                    sender_name,
                    message_type,
                    message,
                    status,
                    http_status,
                    raw_payload,
                    created_at
                )
                VALUES
                (
                    'INBOUND',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'RECEIVED',
                    200,
                    %s,
                    NOW()
                )
            """

            cursor.execute(
                sql,
                (
                    message_id,
                    sender,
                    receiver,
                    sender_name,
                    message_type,
                    message,
                    safe_json_dumps(raw_payload)
                )
            )
    finally:
        connection.close()


# =========================================================
# MYADS SESSION
# =========================================================

def start_myads_session(phone: str):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO myads_campaign_sessions
                    (phone, status, campaign_payload, last_error)
                VALUES
                    (%s, 'WAITING_FORM', NULL, NULL)
                ON DUPLICATE KEY UPDATE
                    status = 'WAITING_FORM',
                    campaign_payload = NULL,
                    last_error = NULL,
                    updated_at = NOW()
            """, (phone,))
    finally:
        connection.close()


def get_myads_session(phone: str):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, phone, status, campaign_payload, last_error,
                       created_at, updated_at
                FROM myads_campaign_sessions
                WHERE phone = %s
                LIMIT 1
            """, (phone,))
            return cursor.fetchone()
    finally:
        connection.close()


def save_campaign_payload(phone: str, payload: dict):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE myads_campaign_sessions
                SET status = 'READY',
                    campaign_payload = %s,
                    last_error = NULL,
                    updated_at = NOW()
                WHERE phone = %s
            """, (safe_json_dumps(payload), phone))
    finally:
        connection.close()


def save_session_error(phone: str, error_message: str):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE myads_campaign_sessions
                SET last_error = %s,
                    updated_at = NOW()
                WHERE phone = %s
            """, (error_message, phone))
    finally:
        connection.close()


# =========================================================
# MYADS SMS BROADCAST FORM
# =========================================================

MYADS_FORM_MESSAGE = """Halo, Anda masuk ke pembuatan campaign MyAds SMS Broadcast.

Silakan balas dengan format berikut dan jangan mengubah nomor field:

1. Campaign Name: Promo Agustus
2. Sender Name: MyAds
3. Message: Dapatkan promo spesial hari ini.
4. MSISDN File: <encrypted_file dari API Upload Content>
5. MSISDN File Name: Template_123.csv
6. Delivery Date: 20260818
7. Delivery Time: 0900
8. Control Numbers: 6281234567890,6281111111111

Catatan:
- Delivery Date harus YYYYMMDD
- Delivery Time harus HHMM (24 jam)
- Control Numbers boleh dikosongkan dengan tanda -
- Ketik CANCEL untuk membatalkan
"""


def extract_numbered_field(text: str, number: int):
    """
    Mendukung contoh:
      1. Campaign Name: Promo A
      1 Campaign Name: Promo A
      1: Promo A
    """
    pattern = rf"(?im)^\s*{number}\s*[\.\)\-:]?\s*(?:[^:\n]+:\s*)?(.*?)\s*$"
    match = re.search(pattern, text)
    if not match:
        return None
    return match.group(1).strip()


def parse_control_numbers(value: str):
    if value is None:
        return []

    value = value.strip()
    if not value or value in {"-", "none", "null", "kosong"}:
        return []

    numbers = []
    for item in re.split(r"[,;\n]+", value):
        phone = normalize_phone(item)
        if phone:
            numbers.append(phone)
    return numbers


def parse_sms_broadcast_form(text: str):
    campaign_name = extract_numbered_field(text, 1)
    sender_name = extract_numbered_field(text, 2)
    sms_message = extract_numbered_field(text, 3)
    msisdn_file = extract_numbered_field(text, 4)
    msisdn_file_name = extract_numbered_field(text, 5)
    delivery_date = extract_numbered_field(text, 6)
    delivery_time = extract_numbered_field(text, 7)
    control_numbers_raw = extract_numbered_field(text, 8)

    errors = []

    if not campaign_name:
        errors.append("Field 1 Campaign Name wajib diisi")
    elif len(campaign_name) > 100:
        errors.append("Campaign Name maksimal 100 karakter")

    if not sender_name:
        errors.append("Field 2 Sender Name wajib diisi")
    elif len(sender_name) > 50:
        errors.append("Sender Name maksimal 50 karakter")

    if not sms_message:
        errors.append("Field 3 Message wajib diisi")

    if not msisdn_file:
        errors.append("Field 4 MSISDN File wajib diisi")

    if not msisdn_file_name:
        errors.append("Field 5 MSISDN File Name wajib diisi")

    if not delivery_date:
        errors.append("Field 6 Delivery Date wajib diisi")
    elif not re.fullmatch(r"\d{8}", delivery_date):
        errors.append("Delivery Date harus format YYYYMMDD, contoh 20260818")

    if not delivery_time:
        errors.append("Field 7 Delivery Time wajib diisi")
    elif not re.fullmatch(r"\d{4}", delivery_time):
        errors.append("Delivery Time harus format HHMM, contoh 0900")
    else:
        hh = int(delivery_time[:2])
        mm = int(delivery_time[2:])
        if hh > 23 or mm > 59:
            errors.append("Delivery Time tidak valid")

    control_numbers = parse_control_numbers(control_numbers_raw)
    for phone in control_numbers:
        if len(phone) > 15:
            errors.append(f"Control Number terlalu panjang: {phone}")

    if errors:
        return None, errors

    payload = {
        "campaignName": campaign_name,
        "channel": "SMS",
        "senderName": sender_name,
        "message": sms_message,
        "msisdnFile": msisdn_file,
        "msisdnFileName": msisdn_file_name,
        "mmsFile": "",
        "mmsSubject": "",
        "deliveries": [
            {
                "deliveryDate": delivery_date,
                "deliveryTime": delivery_time
            }
        ],
        "controlNumbers": control_numbers
    }

    return payload, []


def format_payload_for_whatsapp(payload: dict):
    return json.dumps(payload, indent=2, ensure_ascii=False)


# =========================================================
# SEND WHATSAPP - INTERNAL FUNCTION
# =========================================================

def send_whatsapp_text(receiver: str, message: str):
    sender = normalize_phone(DEFAULT_SENDER)
    receiver = normalize_phone(receiver)

    if not API_KEY:
        return {
            "success": False,
            "status": 500,
            "error": "MYWHATSAPP_API_KEY belum diisi"
        }

    if not sender:
        return {
            "success": False,
            "status": 500,
            "error": "MYWHATSAPP_SENDER belum diisi"
        }

    if not receiver:
        return {
            "success": False,
            "status": 400,
            "error": "Receiver belum diisi"
        }

    if not message:
        return {
            "success": False,
            "status": 400,
            "error": "Message tidak boleh kosong"
        }

    url = f"{BASE_URL}/api/send-message"

    payload_candidates = [
        {
            "api_key": API_KEY,
            "sender": sender,
            "number": receiver,
            "message": message
        },
        {
            "api_key": API_KEY,
            "sender": sender,
            "receiver": receiver,
            "message": message
        },
        {
            "api_key": API_KEY,
            "sender": sender,
            "to": receiver,
            "message": message
        },
        {
            "api_key": API_KEY,
            "sender": sender,
            "target": receiver,
            "message": message
        }
    ]

    results = []
    last_status = 400
    last_response = ""

    for index, payload in enumerate(payload_candidates, start=1):
        safe_payload = payload.copy()
        safe_payload["api_key"] = "***HIDDEN***"

        try:
            response = requests.post(url, data=payload, timeout=30)
            last_status = response.status_code
            last_response = response.text

            results.append({
                "format": index,
                "request_type": "form",
                "payload": safe_payload,
                "status": response.status_code,
                "response": response.text
            })

            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"raw_response": response.text}

                message_id = None
                if isinstance(response_data, dict):
                    message_id = (
                        response_data.get("message_id")
                        or response_data.get("messageId")
                        or response_data.get("id")
                    )

                save_outbound(
                    sender=sender,
                    receiver=receiver,
                    message=message,
                    status="SUCCESS",
                    http_status=response.status_code,
                    raw_payload=response_data,
                    message_id=message_id
                )

                return {
                    "success": True,
                    "status": response.status_code,
                    "format": index,
                    "request_type": "form",
                    "response": response_data
                }

            response_json = requests.post(url, json=payload, timeout=30)
            last_status = response_json.status_code
            last_response = response_json.text

            results.append({
                "format": index,
                "request_type": "json",
                "payload": safe_payload,
                "status": response_json.status_code,
                "response": response_json.text
            })

            if 200 <= response_json.status_code < 300:
                try:
                    response_data = response_json.json()
                except Exception:
                    response_data = {"raw_response": response_json.text}

                message_id = None
                if isinstance(response_data, dict):
                    message_id = (
                        response_data.get("message_id")
                        or response_data.get("messageId")
                        or response_data.get("id")
                    )

                save_outbound(
                    sender=sender,
                    receiver=receiver,
                    message=message,
                    status="SUCCESS",
                    http_status=response_json.status_code,
                    raw_payload=response_data,
                    message_id=message_id
                )

                return {
                    "success": True,
                    "status": response_json.status_code,
                    "format": index,
                    "request_type": "json",
                    "response": response_data
                }

        except requests.exceptions.RequestException as e:
            last_status = 500
            last_response = str(e)
            results.append({
                "format": index,
                "error": str(e)
            })

    save_outbound(
        sender=sender,
        receiver=receiver,
        message=message,
        status="FAILED",
        http_status=last_status,
        raw_payload={
            "last_response": last_response,
            "attempts": results
        }
    )

    return {
        "success": False,
        "status": last_status,
        "error": "Semua format request gagal",
        "results": results
    }


# =========================================================
# HOME / HEALTH
# =========================================================

@app.get("/")
def home():
    return {
        "success": True,
        "service": "MyWhatsApp + MyAds Campaign Bot"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy"
    }


# =========================================================
# SEND WHATSAPP API
# =========================================================

@app.post("/api/send")
def send_message(data: SendMessageRequest):
    result = send_whatsapp_text(data.receiver, data.message)

    if not result.get("success"):
        return JSONResponse(
            status_code=result.get("status", 400),
            content=result
        )

    return result


# =========================================================
# INBOUND WEBHOOK + MYADS FLOW
# =========================================================

@app.post("/")
@app.post("/webhook/mywhatsapp")
async def inbound_mywhatsapp(request: Request):
    try:
        content_type = request.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            payload = await request.json()
        elif (
            "application/x-www-form-urlencoded" in content_type
            or "multipart/form-data" in content_type
        ):
            form = await request.form()
            payload = dict(form)
        else:
            raw_body = await request.body()
            raw_text = raw_body.decode("utf-8", errors="ignore")
            try:
                payload = json.loads(raw_text) if raw_text else {}
            except json.JSONDecodeError:
                payload = {"raw": raw_text}

        if not isinstance(payload, dict):
            payload = {"data": payload}

        print("\n" + "=" * 80)
        print("INBOUND MYWHATSAPP")
        print("=" * 80)
        print(json.dumps(payload, indent=4, ensure_ascii=False, default=str))
        print("=" * 80)

        # Nomor customer yang mengirim pesan
        customer_phone = find_payload_value(
            payload,
            "from",
            "from_number",
            "fromNumber",
            "phone",
            "phoneNumber",
            "remoteJid",
            "chatId"
        )

        # Nomor WhatsApp kita / device sender
        whatsapp_number = find_payload_value(
            payload,
            "sender",
            "sender_number",
            "senderNumber",
            "device",
            "deviceNumber"
        )

        sender_name = find_payload_value(
            payload, "pushName", "push_name", "senderName", "name"
        )

        message_type = (
            find_payload_value(payload, "messageType", "message_type", "type")
            or "unknown"
        )

        message = (
            find_payload_value(
                payload, "body", "message", "text", "content", "caption"
            )
        )

        message_id = (
            find_payload_value(payload, "message_id", "messageId", "id")
        )

        # JID WhatsApp lazimnya berbentuk 628xxx@s.whatsapp.net.
        if customer_phone:
            customer_phone = str(customer_phone).split("@", 1)[0]
        if whatsapp_number:
            whatsapp_number = str(whatsapp_number).split("@", 1)[0]

        if customer_phone:
            customer_phone = normalize_phone(str(customer_phone))

        if whatsapp_number:
            whatsapp_number = normalize_phone(str(whatsapp_number))

        # Struktur DB lama dipertahankan:
        # sender = nomor WA kita, receiver = nomor customer
        sender = whatsapp_number
        receiver = customer_phone

        save_inbound(
            sender=sender,
            receiver=receiver,
            sender_name=sender_name,
            message_id=message_id,
            message_type=message_type,
            message=message,
            raw_payload=payload
        )

        # Jika tidak ada text, cukup simpan inbound.
        if not customer_phone or not isinstance(message, str):
            return {
                "success": True,
                "message": "Inbound received and saved; no text flow executed"
            }

        clean_message = message.strip()
        clean_lower = clean_message.lower()

        # -----------------------------------------------------
        # 1. TRIGGER "myads"
        # -----------------------------------------------------
        if clean_lower == "myads":
            start_myads_session(customer_phone)

            send_result = send_whatsapp_text(
                customer_phone,
                MYADS_FORM_MESSAGE
            )

            return {
                "success": bool(send_result.get("success")),
                "action": "MYADS_FORM_SENT",
                "phone": customer_phone,
                "send_result": send_result
            }

        # -----------------------------------------------------
        # CANCEL
        # -----------------------------------------------------
        if clean_lower == "cancel":
            session = get_myads_session(customer_phone)
            if session:
                connection = get_db()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE myads_campaign_sessions
                            SET status = 'CANCELLED',
                                updated_at = NOW()
                            WHERE phone = %s
                        """, (customer_phone,))
                finally:
                    connection.close()

                send_whatsapp_text(
                    customer_phone,
                    "Pembuatan campaign MyAds dibatalkan. Ketik MYADS untuk mulai lagi."
                )

                return {
                    "success": True,
                    "action": "MYADS_CANCELLED"
                }

        # -----------------------------------------------------
        # 2. JIKA ADA SESSION WAITING_FORM, PARSE BALASAN FORM
        # -----------------------------------------------------
        session = get_myads_session(customer_phone)

        if session and session.get("status") == "WAITING_FORM":
            campaign_payload, errors = parse_sms_broadcast_form(clean_message)

            if errors:
                error_text = "Form belum valid:\n- " + "\n- ".join(errors)
                save_session_error(customer_phone, error_text)

                send_whatsapp_text(
                    customer_phone,
                    error_text + "\n\nSilakan kirim ulang form lengkap."
                )

                return {
                    "success": False,
                    "action": "MYADS_FORM_INVALID",
                    "errors": errors
                }

            # JSON sudah siap untuk endpoint MyAds SMS Broadcast
            save_campaign_payload(customer_phone, campaign_payload)

            json_preview = format_payload_for_whatsapp(campaign_payload)

            confirmation_message = (
                "Form berhasil diproses. JSON campaign siap dikirim ke API MyAds "
                "/scrt/myads/api/v1/campaign/broadcast/add:\n\n"
                + json_preview
            )

            send_result = send_whatsapp_text(
                customer_phone,
                confirmation_message
            )

            return {
                "success": True,
                "action": "MYADS_JSON_READY",
                "phone": customer_phone,
                "endpoint": "/scrt/myads/api/v1/campaign/broadcast/add",
                "campaign_payload": campaign_payload,
                "send_result": send_result
            }

        return {
            "success": True,
            "message": "Inbound received and saved",
            "data": {
                "sender": sender,
                "receiver": receiver,
                "sender_name": sender_name,
                "message_id": message_id,
                "message_type": message_type,
                "message": message
            }
        }

    except Exception as e:
        print("INBOUND ERROR:", str(e))

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# =========================================================
# GET CAMPAIGN JSON READY BY PHONE
# =========================================================

@app.get("/api/myads/campaign/{phone}")
def get_myads_campaign(phone: str):
    phone = normalize_phone(phone)
    session = get_myads_session(phone)

    if not session:
        raise HTTPException(status_code=404, detail="Session MyAds tidak ditemukan")

    campaign_payload = None
    if session.get("campaign_payload"):
        try:
            campaign_payload = json.loads(session["campaign_payload"])
        except Exception:
            campaign_payload = session["campaign_payload"]

    return {
        "success": True,
        "phone": phone,
        "status": session.get("status"),
        "campaign_payload": campaign_payload,
        "last_error": session.get("last_error")
    }


# =========================================================
# GET INBOUND
# =========================================================

@app.get("/api/inbound")
def get_inbound(limit: int = 100):
    if limit > 1000:
        limit = 1000
    if limit < 1:
        limit = 1

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT
                    id,
                    direction,
                    message_id,
                    sender,
                    receiver,
                    sender_name,
                    message_type,
                    message,
                    status,
                    http_status,
                    created_at
                FROM whatsapp_messages
                WHERE direction = 'INBOUND'
                ORDER BY id DESC
                LIMIT %s
            """
            cursor.execute(sql, (limit,))
            data = cursor.fetchall()

        return {
            "success": True,
            "total": len(data),
            "data": data
        }
    finally:
        connection.close()


# =========================================================
# GET INBOUND BY CUSTOMER PHONE
# =========================================================

@app.get("/api/inbound/{phone}")
def get_inbound_by_phone(phone: str, limit: int = 100):
    phone = normalize_phone(phone)

    if limit < 1:
        limit = 1
    if limit > 1000:
        limit = 1000

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            # Menggunakan whatsapp_messages agar konsisten dengan save_inbound().
            # Pada struktur existing: receiver berisi nomor customer.
            sql = """
                SELECT
                    id,
                    message_id,
                    sender,
                    receiver,
                    sender_name,
                    message_type,
                    message,
                    created_at
                FROM whatsapp_messages
                WHERE direction = 'INBOUND'
                  AND receiver = %s
                ORDER BY id DESC
                LIMIT %s
            """
            cursor.execute(sql, (phone, limit))
            data = cursor.fetchall()

        return {
            "success": True,
            "phone": phone,
            "total": len(data),
            "data": data
        }
    finally:
        connection.close()
