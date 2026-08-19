import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from wa_app.services.webhook import process_inbound

router = APIRouter(tags=["webhook"])

async def _read_payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        payload = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        payload = dict(await request.form())
    else:
        raw_text = (await request.body()).decode("utf-8", errors="ignore")
        try:
            payload = json.loads(raw_text) if raw_text else {}
        except json.JSONDecodeError:
            payload = {"raw": raw_text}
    return payload if isinstance(payload, dict) else {"data": payload}

@router.post("/")
@router.post("/webhook/mywhatsapp")
async def inbound_mywhatsapp(request: Request):
    try:
        payload = await _read_payload(request)
        print("INBOUND MYWHATSAPP:", json.dumps(payload, ensure_ascii=False, default=str))
        return process_inbound(payload)
    except Exception as error:
        print("INBOUND ERROR:", str(error))
        return JSONResponse(status_code=500, content={"success": False, "error": str(error)})
