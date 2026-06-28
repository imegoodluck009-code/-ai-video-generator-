from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import VideoRequest, VideoResponse
from app.services.pexels import PexelsService
from app.services.video_renderer import VideoRenderer
from app.services.voice_generator import VoiceGenerator
import os

router = APIRouter(prefix="/api/videos", tags=["videos"])

# In-memory job store (replace with Redis/DB in production)
jobs = {}

renderer = VideoRenderer()


@router.post("/generate", response_model=VideoResponse)
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Queue a new video generation job."""
    job_id = renderer.generate_job_id()
    
    job = {
        "id": job_id,
        "status": "queued",
        "prompt": request.prompt,
        "download_url": None,
        "message": "Job queued for processing"
    }
    jobs[job_id] = job
    
    # Queue background processing
    background_tasks.add_task(process_video_job, job_id, request)
    
    return VideoResponse(**job)


@router.get("/{job_id}", response_model=VideoResponse)
async def get_job_status(job_id: str):
    """Check status of a video generation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return VideoResponse(**jobs[job_id])


@router.get("/search/pexels")
async def search_pexels(query: str, per_page: int = 5):
    """Search Pexels for stock videos."""
    pexels = PexelsService()
    videos = await pexels.search_videos(query=query, per_page=per_page)
    
    if videos is None:
        raise HTTPException(status_code=503, detail="Pexels API unavailable or misconfigured")
    
    return {"query": query, "results": videos}


async def process_video_job(job_id: str, request: VideoRequest):
    """Background task: fetch clips, generate voice, render video."""
    jobs[job_id]["status"] = "processing"
    
    try:
        # 1. Search Pexels for relevant clips
        pexels = PexelsService()
        videos = await pexels.search_videos(
            query=request.prompt,
            per_page=3
        )
        
        if not videos:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "No suitable stock footage found"
            return
        
        # 2. Extract video URLs - pick SMALLEST MP4
        video_urls = []
        for v in videos:
            files = v.get("video_files", [])
            mp4_files = [f for f in files if f.get("file_type") == "video/mp4"]
            if mp4_files:
                smallest = min(mp4_files, key=lambda x: x.get("width", 9999) * x.get("height", 9999))
                video_urls.append(smallest["link"])
        
        if not video_urls:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "No MP4 files found in search results"
            return
        
        # 3. Generate voiceover if requested
        voiceover_path = None
        # Ensure temp directory exists
        if not os.path.exists("temp"):
            os.makedirs("temp")
            print("📁 Created temp directory")

        if request.include_voiceover and request.voice_text:
            jobs[job_id]["message"] = "Generating voiceover with ElevenLabs..."
            voice = VoiceGenerator()
            voiceover_path = f"temp/{job_id}_voice.mp3"
            try:
                await voice.generate_voice(
                    text=request.voice_text,
                    output_path=voiceover_path
                )
                jobs[job_id]["message"] = "Voiceover generated, processing video..."
            except Exception as e:
                error_msg = f"Voiceover failed: {str(e)}"
                print(f"🔴 VOICE ERROR: {error_msg}")
                jobs[job_id]["message"] = error_msg
                voiceover_path = None

        # 4. Render video with FFmpeg
        output_path = await renderer.render(
            job_id=job_id,
            video_urls=video_urls,
            voiceover_path=voiceover_path,
            duration=request.duration
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["download_url"] = f"/api/videos/{job_id}/download"
        jobs[job_id]["message"] = "Video generated successfully"
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)


@router.get("/{job_id}/download")
async def download_video(job_id: str):
    """Download generated video."""
    from fastapi.responses import FileResponse
    
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="Video not ready")
    
    output_path = f"outputs/{job_id}.mp4"
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"ai-video-{job_id}.mp4"
    )
