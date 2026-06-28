import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
import httpx
from tts import generate_voiceover

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

def wrap_text(text: str, max_chars: int = 30) -> str:
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current += " " + w if current else w
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return "\\\\n".join(lines)

async def assemble_video(clip_path: str, voiceover_path: str = None, 
                        output_path: str = None, subtitle_text: str = "") -> str:
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "output.mp4")
    import subprocess
    
    safe_text = subtitle_text.replace("'", "'\\\\''").replace(":", "\\\\:")
    wrapped = wrap_text(safe_text)
    
    vf = f"drawtext=text='{wrapped}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h-text_h-80:box=1:boxcolor=black@0.6:boxborderw=10:line_spacing=4"
    
    if voiceover_path and os.path.exists(voiceover_path):
        cmd = ["ffmpeg", "-y", "-i", clip_path, "-i", voiceover_path, "-vf", vf, "-c:a", "aac", "-shortest", output_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", clip_path, "-vf", vf, "-c:a", "copy", output_path]
    
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

@app.post("/api/videos/generate")
async def generate_video(request: Request):
    data = await request.json()
    script = data.get("script", "")
    query = data.get("query", "nature")
    
    clip_path = await download_pexels_clip(query)
    try:
        voiceover_path = await generate_voiceover(script)
    except Exception as e:
        voiceover_path = None
        print(f"TTS failed: {e}")
    
    output_path = await assemble_video(clip_path, voiceover_path, subtitle_text=script)
    return FileResponse(output_path, media_type="video/mp4", filename="video.mp4")

@app.get("/")
async def root():
    return {"status": "ai-video-generator with subtitles running on Render"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
