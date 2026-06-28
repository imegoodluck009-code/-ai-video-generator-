from fastapi import APIRouter
from app.models.schemas import HealthCheck
from app.config import get_settings
from app.services.pexels import PexelsService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheck)
async def health_check():
    settings = get_settings()
    pexels = PexelsService()
    
    # Quick Pexels connectivity check
    pexels_ok = False
    if settings.pexels_api_key:
        try:
            videos = await pexels.get_popular_videos(per_page=1)
            pexels_ok = videos is not None
        except:
            pass
    
    return HealthCheck(
        status="healthy",
        pexels_connected=pexels_ok
    )
