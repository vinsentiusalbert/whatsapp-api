import json

from fastapi import APIRouter, HTTPException

from wa_app.repositories import get_myads_session
from wa_app.utils import normalize_phone

router = APIRouter(prefix="/api/myads", tags=["myads"])

@router.get("/campaign/{phone}")
def get_myads_campaign(phone: str):
    phone = normalize_phone(phone)
    session = get_myads_session(phone)
    if not session:
        raise HTTPException(status_code=404, detail="Session MyAds tidak ditemukan")
    campaign_payload = session.get("campaign_payload")
    if campaign_payload:
        try:
            campaign_payload = json.loads(campaign_payload)
        except (TypeError, json.JSONDecodeError):
            pass
    return {"success": True, "phone": phone, "status": session.get("status"),
            "campaign_payload": campaign_payload, "last_error": session.get("last_error")}
