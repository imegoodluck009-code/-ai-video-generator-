import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
import httpx
from tts import generate_voiceover
from scene_analyzer import split_script_into_scenes, get_scene_search_query
from smart_stitcher import generate_scene_voiceovers, cut_clip_to_duration, stitch_scenes

app = FastAPI()

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
TMP_DIR = "/tmp" if os.path.exists("/tmp") else (os.environ.get("PREFIX", "/usr") + "/tmp")

async def download_pexels_clip(query: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "clip.mp4")
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1, "orientation": "landscape"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("videos"):
            raise HTTPException(status_code=404, detail="No Pexels videos found")
        video_url = data["videos"][0]["video_files"][0]["link"]
        video_resp = await client.get(video_url, timeout=60.0)
        video_resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(video_resp.content)
    return output_path

@app.post("/api/videos/generate")
async def generate_video(request: Request):
    data = await request.json()
    script = data.get("script", "")
    fallback_query = data.get("query", "nature")
    
    # Step 1: Analyze script into scenes
    scenes = split_script_into_scenes(script)
    if not scenes:
        scenes = [{"text": script, "keywords": fallback_query, "duration": 5.0}]
    
    # Step 2: Generate voiceovers for each scene
    scene_voices = await generate_scene_voiceovers(script, generate_voiceover, TMP_DIR)
    
    # Step 3: Download clips for each scene and cut to voiceover length
    scene_clips = []
    for i, sv in enumerate(scene_voices):
        query = sv["scene"]["keywords"] if sv["scene"]["keywords"] else fallback_query
        raw_clip = os.path.join(TMP_DIR, f"raw_clip_{i}.mp4")
        cut_clip = os.path.join(TMP_DIR, f"cut_clip_{i}.mp4")
        
        try:
            await download_pexels_clip(query, raw_clip)
            cut_clip_to_duration(raw_clip, cut_clip, sv["duration"])
            scene_clips.append(cut_clip)
        except Exception as e:
            print(f"Clip download failed for scene {i}: {e}")
            # Use fallback
            await download_pexels_clip(fallback_query, raw_clip)
            cut_clip_to_duration(raw_clip, cut_clip, sv["duration"])
            scene_clips.append(cut_clip)
    
    # Step 4: Stitch all scenes together
    stitched_path = os.path.join(TMP_DIR, "stitched.mp4")
    stitch_scenes(scene_clips, stitched_path)
    
    # Step 5: Mix audio (scene voiceovers concatenated)
    # For simplicity, return stitched video with first voiceover
    # Full audio mixing requires more complex FFmpeg
    final_output = os.path.join(TMP_DIR, "output.mp4")
    if scene_voices and scene_voices[0]["audio_path"]:
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-i", stitched_path,
            "-i", scene_voices[0]["audio_path"],
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            final_output
        ], check=True, capture_output=True)
    else:
        final_output = stitched_path
    
    return FileResponse(final_output, media_type="video/mp4", filename="video.mp4")

@app.get("/")
async def root():
    return {"status": "AI scene detection video generator running on Render"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
