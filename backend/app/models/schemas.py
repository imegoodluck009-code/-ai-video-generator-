from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class VideoStyle(str, Enum):
    cinematic = "cinematic"
    documentary = "documentary"
    vlog = "vlog"
    minimal = "minimal"


class VideoRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=500, description="Text prompt describing the video")
    duration: int = Field(default=30, ge=10, le=120, description="Target duration in seconds")
    style: VideoStyle = Field(default=VideoStyle.cinematic)
    include_voiceover: bool = Field(default=False, description="Whether to include AI voiceover")
    voice_text: Optional[str] = Field(default=None, max_length=2000, description="Script for voiceover")


class VideoResponse(BaseModel):
    id: str
    status: str
    prompt: str
    download_url: Optional[str] = None
    message: Optional[str] = None


class PexelsVideo(BaseModel):
    id: int
    url: str
    duration: int
    width: int
    height: int
    video_files: List[dict]


class HealthCheck(BaseModel):
    status: str
    version: str = "0.1.0"
    pexels_connected: bool
