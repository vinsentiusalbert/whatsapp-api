from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {"success": True, "service": "MyWhatsApp + MyAds Campaign Bot"}

@router.get("/health")
def health():
    return {"success": True, "status": "healthy"}
