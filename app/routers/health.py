from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health/ready")
async def health_ready():
    return {"status": "ok"}

@router.get("/health/live")
async def health_live():
    return {"status": "ok"}