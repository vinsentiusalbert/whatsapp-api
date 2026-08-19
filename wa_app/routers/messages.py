from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wa_app.repositories import list_inbound
from wa_app.schemas import SendMessageRequest
from wa_app.services.whatsapp import send_whatsapp_text
from wa_app.utils import clamp_limit, normalize_phone

router = APIRouter(prefix="/api", tags=["messages"])

@router.post("/send")
def send_message(data: SendMessageRequest):
    result = send_whatsapp_text(data.receiver, data.message)
    if not result.get("success"):
        return JSONResponse(status_code=result.get("status", 400), content=result)
    return result

@router.get("/inbound")
def get_inbound(limit: int = 100):
    data = list_inbound(clamp_limit(limit))
    return {"success": True, "total": len(data), "data": data}

@router.get("/inbound/{phone}")
def get_inbound_by_phone(phone: str, limit: int = 100):
    phone = normalize_phone(phone)
    data = list_inbound(clamp_limit(limit), phone)
    return {"success": True, "phone": phone, "total": len(data), "data": data}
