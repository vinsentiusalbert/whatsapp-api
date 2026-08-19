import requests

from wa_app.config import settings
from wa_app.repositories import save_outbound
from wa_app.utils import normalize_phone


def _response_data(response):
    try:
        return response.json()
    except ValueError:
        return {"raw_response": response.text}


def _message_id(data):
    if not isinstance(data, dict):
        return None
    return data.get("message_id") or data.get("messageId") or data.get("id")


def send_whatsapp_text(receiver: str, message: str):
    sender = normalize_phone(settings.mywhatsapp_sender)
    receiver = normalize_phone(receiver)
    validations = (
        (not settings.mywhatsapp_api_key, 500, "MYWHATSAPP_API_KEY belum diisi"),
        (not sender, 500, "MYWHATSAPP_SENDER belum diisi"),
        (not receiver, 400, "Receiver belum diisi"),
        (not message, 400, "Message tidak boleh kosong"),
    )
    for invalid, status, error in validations:
        if invalid:
            return {"success": False, "status": status, "error": error}

    url = f"{settings.mywhatsapp_base_url}/api/send-message"
    candidates = [
        {"api_key": settings.mywhatsapp_api_key, "sender": sender,
         receiver_key: receiver, "message": message}
        for receiver_key in ("number", "receiver", "to", "target")
    ]
    attempts = []
    last_status, last_response = 400, ""

    for index, payload in enumerate(candidates, start=1):
        safe_payload = {**payload, "api_key": "***HIDDEN***"}
        for request_type in ("form", "json"):
            try:
                kwargs = {"data" if request_type == "form" else "json": payload}
                response = requests.post(url, timeout=30, **kwargs)
                last_status, last_response = response.status_code, response.text
                attempts.append({"format": index, "request_type": request_type,
                                 "payload": safe_payload, "status": response.status_code,
                                 "response": response.text})
                if 200 <= response.status_code < 300:
                    data = _response_data(response)
                    save_outbound(sender, receiver, message, "SUCCESS",
                                  response.status_code, data, _message_id(data))
                    return {"success": True, "status": response.status_code,
                            "format": index, "request_type": request_type,
                            "response": data}
            except requests.exceptions.RequestException as error:
                last_status, last_response = 500, str(error)
                attempts.append({"format": index, "error": str(error)})
                # Sama seperti implementasi lama: lanjut ke candidate berikutnya.
                break

    save_outbound(sender, receiver, message, "FAILED", last_status,
                  {"last_response": last_response, "attempts": attempts})
    return {"success": False, "status": last_status,
            "error": "Semua format request gagal", "results": attempts}
