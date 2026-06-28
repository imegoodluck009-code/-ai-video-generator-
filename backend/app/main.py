from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, videos, avatar
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Video Generator API — Pexels + ElevenLabs + Replicate"
)

# CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(videos.router)
app.include_router(avatar.router)


@app.get("/")
async def root():
    return {
        "message": "AI Video Generator API",
        "docs": "/docs",
        "version": "0.1.0",
        "features": ["video_generation", "voiceover", "talking_avatar"]
    }
