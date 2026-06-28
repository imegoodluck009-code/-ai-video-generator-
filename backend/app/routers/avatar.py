from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.avatar_generator import AvatarGenerator
from app.services.voice_generator import VoiceGenerator
from app.services.pexels import PexelsService
import uuid

router = APIRouter(prefix="/api/avatar", tags=["avatar"])

# In-memory job store
jobs = {}


@router.post("/generate")
async def generate_avatar(
    image_url: str,
    script: str,
    background_video_query: str = "office",
    background_opacity: float = 0.3,
    background_tasks: BackgroundTasks = None
):
    """
    Generate a talking avatar video.
    
    - image_url: URL to a portrait photo
    - script: Text to speak
    - background_video_query: Pexels search query for background
    - background_opacity: How visible the background is (0-1)
    """
    job_id = str(uuid.uuid4())[:8]
    
    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "message": "Job queued"
    }
    
    if background_tasks:
        background_tasks.add_task(
            process_avatar_job,
            job_id, image_url, script, background_video_query, background_opacity
        )
    
    return {"id": job_id, "status": "queued"}


@router.get("/{job_id}")
async def get_avatar_status(job_id: str):
    """Check avatar generation status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


async def process_avatar_job(
    job_id: str,
    image_url: str,
    script: str,
    background_video_query: str,
    background_opacity: float
):
    """Background task: generate voice, then create talking avatar."""
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["message"] = "Generating voiceover..."
    
    try:
        # 1. Generate voice with ElevenLabs
        voice = VoiceGenerator()
        voice_path = f"temp/{job_id}_voice.mp3"
        await voice.generate_voice(text=script, output_path=voice_path)
        
        # 2. Upload voice to a temporary URL (or use base64)
        # For now, we need the audio accessible via URL for Replicate
        # We'll use the voice file path and handle it in the avatar generator
        
        jobs[job_id]["message"] = "Creating talking avatar with Replicate..."
        
        # 3. Generate avatar video with Replicate
        # Note: Replicate needs public URLs for image and audio
        # For testing, we'll use the image_url directly and need to host the audio
        avatar = AvatarGenerator()
        
        # For now, return a placeholder since we need public URLs
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Avatar generation requires public URLs for image and audio. Use a service like imgur for images and a file host for audio."
        jobs[job_id]["download_url"] = None
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)
