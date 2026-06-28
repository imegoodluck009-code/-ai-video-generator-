import uuid
import os
import subprocess
import httpx
from typing import Optional
from pathlib import Path


class VideoRenderer:
    """FFmpeg-based video rendering pipeline with voiceover support."""
    
    def __init__(self):
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
    
    def generate_job_id(self) -> str:
        return str(uuid.uuid4())[:8]
    
    async def download_clip(self, url: str, filename: str) -> str:
        """Download a video clip from URL with proper headers."""
        filepath = self.temp_dir / filename
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "video/mp4,video/*;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.pexels.com/",
            "Origin": "https://www.pexels.com"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=60.0, follow_redirects=True)
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(response.content)
        
        if not filepath.exists() or filepath.stat().st_size == 0:
            raise RuntimeError(f"Download failed: {filepath}")
        
        return str(filepath)
    
    def process_video(self, input_path: str, output_path: str, duration: float, voiceover_path: Optional[str] = None) -> tuple:
        """Process video: cut to duration and optionally add voiceover."""
        try:
            if voiceover_path and os.path.exists(voiceover_path):
                # Check voiceover file size
                voice_size = os.path.getsize(voiceover_path)
                print(f"Voiceover file: {voiceover_path}, size: {voice_size} bytes")
                
                # First, check if voiceover is valid audio
                probe_result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", voiceover_path],
                    capture_output=True, text=True, timeout=10
                )
                print(f"Voiceover duration: {probe_result.stdout.strip()}")
                
                # Merge video + audio using filter_complex for better control
                # - Use amix to combine audio tracks
                # - Boost audio volume
                result = subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-i", input_path,
                        "-i", voiceover_path,
                        "-t", str(duration),
                        "-filter_complex", "[1:a]volume=2.0[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
                        "-map", "0:v",
                        "-map", "[aout]",
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-threads", "1",
                        "-c:a", "aac", "-b:a", "128k",
                        "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart",
                        "-vf", "scale=640:-2",
                        "-shortest",
                        output_path
                    ],
                    capture_output=True, text=True, timeout=120
                )
            else:
                # Video only (no voiceover)
                print(f"No voiceover path provided or file doesn't exist: {voiceover_path}")
                result = subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", input_path,
                        "-t", str(duration),
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-threads", "1",
                        "-c:a", "aac", "-b:a", "96k",
                        "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart",
                        "-vf", "scale=640:-2",
                        output_path
                    ],
                    capture_output=True, text=True, timeout=120
                )
            
            print(f"FFmpeg stdout: {result.stdout[:200]}")
            print(f"FFmpeg stderr: {result.stderr[:500]}")
            
            if result.returncode != 0:
                return False, f"ffmpeg error (code {result.returncode}): {result.stderr[:300]}"
            return True, ""
        except Exception as e:
            return False, f"process_video exception: {str(e)}"
    
    async def render(
        self,
        job_id: str,
        video_urls: list,
        voiceover_path: Optional[str] = None,
        duration: int = 30
    ) -> str:
        """
        Download ONE clip and process it with optional voiceover.
        """
        output_path = self.output_dir / f"{job_id}.mp4"
        
        if not video_urls:
            raise ValueError("No video URLs provided")
        
        url = video_urls[0]
        temp_filename = f"{job_id}_clip.mp4"
        
        # Download
        try:
            downloaded = await self.download_clip(url, temp_filename)
            file_size = Path(downloaded).stat().st_size
            print(f"Clip downloaded: {file_size} bytes")
        except Exception as e:
            raise RuntimeError(f"Failed to download clip: {str(e)}")
        
        # Process (cut + merge voiceover)
        success, error = self.process_video(downloaded, str(output_path), duration, voiceover_path)
        if not success:
            raise RuntimeError(f"Failed to process video: {error}")
        
        # Verify output exists and has audio
        if not output_path.exists():
            raise RuntimeError("Output file was not created")
        
        # Check if output has audio
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(output_path)],
            capture_output=True, text=True, timeout=10
        )
        print(f"Output streams: {probe.stdout.strip()}")
        
        # Cleanup
        if os.path.exists(downloaded):
            os.remove(downloaded)
        if voiceover_path and os.path.exists(voiceover_path):
            os.remove(voiceover_path)
        
        return str(output_path)
    
    def cleanup(self, job_id: str, downloaded_clips: list = None, cut_clips: list = None, list_path: str = None):
        """Clean up temporary files for a job."""
        pass
