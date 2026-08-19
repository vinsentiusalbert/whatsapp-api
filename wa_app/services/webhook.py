import json

from wa_app.repositories import (
    get_myads_session,
    save_inbound,
    start_myads_session,
    update_myads_session,
)
from wa_app.services.ai_campaign import extract_campaign_draft
from wa_app.services.myads import (
    AI_FIELD_QUESTIONS,
    MYADS_FORM_MESSAGE,
    MYADS_MODE_MESSAGE,
    build_campaign_from_draft,
    format_payload_for_whatsapp,
    parse_sms_broadcast_form,
    validate_campaign_draft,
)
from wa_app.services.whatsapp import send_whatsapp_text
from wa_app.utils import normalize_phone


def find_payload_value(payload, *keys):
    if not isinstance(payload, dict):
        return None
    containers = [payload]
    for wrapper_key in ("data", "payload", "event", "messageData"):
        if isinstance(wrapped := payload.get(wrapper_key), dict):
            containers.append(wrapped)
    for container in list(containers):
        for wrapper_key in ("data", "payload", "message"):
            wrapped = container.get(wrapper_key)
            if isinstance(wrapped, dict) and wrapped not in containers:
                containers.append(wrapped)
    for container in containers:
        for key in keys:
            value = container.get(key)
            if value is not None and value != "" and not isinstance(value, (dict, list)):
                return value
    return None


def extract_inbound(payload: dict) -> dict:
    customer = find_payload_value(payload, "from", "from_number", "fromNumber", "phone",
                                  "phoneNumber", "remoteJid", "chatId")
    device = find_payload_value(payload, "sender", "sender_number", "senderNumber",
                                "device", "deviceNumber")
    return {
        "customer_phone": normalize_phone(str(customer).split("@", 1)[0]) if customer else "",
        "sender": normalize_phone(str(device).split("@", 1)[0]) if device else "",
        "sender_name": find_payload_value(payload, "pushName", "push_name", "senderName", "name"),
        "message_type": find_payload_value(payload, "messageType", "message_type", "type") or "unknown",
        "message": find_payload_value(payload, "body", "message", "text", "content", "caption"),
        "message_id": find_payload_value(payload, "message_id", "messageId", "id"),
    }


def _send_ready_campaign(customer: str, campaign: dict, source: str):
    update_myads_session(customer, status="READY", payload=campaign)
    confirmation = (
        "Campaign berhasil dilengkapi melalui mode " + source + ". "
        "JSON siap dikirim ke API MyAds "
        "/scrt/myads/api/v1/campaign/broadcast/add:\n\n"
        + format_payload_for_whatsapp(campaign)
    )
    result = send_whatsapp_text(customer, confirmation)
    return {
        "success": True,
        "action": "MYADS_JSON_READY",
        "mode": source,
        "phone": customer,
        "endpoint": "/scrt/myads/api/v1/campaign/broadcast/add",
        "campaign_payload": campaign,
        "send_result": result,
    }


def _load_draft(session: dict) -> dict:
    raw_draft = session.get("campaign_payload")
    if not raw_draft:
        return {}
    try:
        draft = json.loads(raw_draft)
        return draft if isinstance(draft, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _process_ai_answer(customer: str, session: dict, message: str):
    draft = _load_draft(session)
    expected_field, _ = validate_campaign_draft(draft)
    if expected_field is None:
        return _send_ready_campaign(customer, build_campaign_from_draft(draft), "AI")
    try:
        draft = extract_campaign_draft(message, draft, expected_field)
    except Exception as error:
        error_message = f"AI belum dapat memproses jawaban: {error}"
        update_myads_session(customer, error=error_message)
        send_whatsapp_text(customer, error_message + "\nSilakan coba lagi atau ketik MYADS MANUAL.")
        return {"success": False, "action": "MYADS_AI_ERROR", "error": str(error)}

    invalid_field, question = validate_campaign_draft(draft)
    if invalid_field:
        # Hapus nilai invalid agar jawaban berikutnya menggantikannya dengan jelas.
        if invalid_field in draft and draft[invalid_field] is not None:
            draft.pop(invalid_field)
        update_myads_session(customer, status="WAITING_AI", payload=draft, error=question)
        result = send_whatsapp_text(customer, question)
        return {
            "success": True,
            "action": "MYADS_AI_QUESTION",
            "missing_field": invalid_field,
            "draft": draft,
            "send_result": result,
        }

    return _send_ready_campaign(customer, build_campaign_from_draft(draft), "AI")


def process_inbound(payload: dict):
    inbound = extract_inbound(payload)
    customer = inbound["customer_phone"]
    save_inbound(sender=inbound["sender"], receiver=customer,
                 sender_name=inbound["sender_name"], message_id=inbound["message_id"],
                 message_type=inbound["message_type"], message=inbound["message"],
                 raw_payload=payload)
    if not customer or not isinstance(inbound["message"], str):
        return {"success": True, "message": "Inbound received and saved; no text flow executed"}

    clean_message = inbound["message"].strip()
    command = clean_message.lower()
    if command == "myads":
        start_myads_session(customer, "WAITING_MODE")
        result = send_whatsapp_text(customer, MYADS_MODE_MESSAGE)
        return {"success": bool(result.get("success")), "action": "MYADS_MODE_SENT",
                "phone": customer, "send_result": result}

    if command == "myads ai":
        start_myads_session(customer, "WAITING_AI")
        question = AI_FIELD_QUESTIONS["campaignName"]
        result = send_whatsapp_text(customer, question)
        return {"success": bool(result.get("success")), "action": "MYADS_AI_STARTED",
                "phone": customer, "send_result": result}

    if command == "myads manual":
        start_myads_session(customer, "WAITING_FORM")
        result = send_whatsapp_text(customer, MYADS_FORM_MESSAGE)
        return {"success": bool(result.get("success")), "action": "MYADS_FORM_SENT",
                "phone": customer, "send_result": result}

    session = get_myads_session(customer)
    if command == "cancel" and session:
        update_myads_session(customer, status="CANCELLED")
        send_whatsapp_text(customer, "Pembuatan campaign MyAds dibatalkan. Ketik MYADS untuk mulai lagi.")
        return {"success": True, "action": "MYADS_CANCELLED"}

    if session and session.get("status") == "WAITING_MODE":
        if command in {"1", "ai"}:
            update_myads_session(customer, status="WAITING_AI", payload={})
            question = AI_FIELD_QUESTIONS["campaignName"]
            result = send_whatsapp_text(customer, question)
            return {"success": bool(result.get("success")),
                    "action": "MYADS_AI_STARTED", "send_result": result}
        if command in {"2", "manual"}:
            update_myads_session(customer, status="WAITING_FORM", payload={})
            result = send_whatsapp_text(customer, MYADS_FORM_MESSAGE)
            return {"success": bool(result.get("success")),
                    "action": "MYADS_FORM_SENT", "send_result": result}
        result = send_whatsapp_text(customer, "Pilihan belum dikenali.\n\n" + MYADS_MODE_MESSAGE)
        return {"success": False, "action": "MYADS_MODE_INVALID", "send_result": result}

    if session and session.get("status") == "WAITING_AI":
        return _process_ai_answer(customer, session, clean_message)

    if session and session.get("status") == "WAITING_FORM":
        campaign, errors = parse_sms_broadcast_form(clean_message)
        if errors:
            error_text = "Form belum valid:\n- " + "\n- ".join(errors)
            update_myads_session(customer, error=error_text)
            send_whatsapp_text(customer, error_text + "\n\nSilakan kirim ulang form lengkap.")
            return {"success": False, "action": "MYADS_FORM_INVALID", "errors": errors}
        return _send_ready_campaign(customer, campaign, "MANUAL")

    return {"success": True, "message": "Inbound received and saved",
            "data": {"sender": inbound["sender"], "receiver": customer,
                     "sender_name": inbound["sender_name"], "message_id": inbound["message_id"],
                     "message_type": inbound["message_type"], "message": inbound["message"]}}
