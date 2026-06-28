import httpx
import time
import asyncio
from pathlib import Path
from app.config import get_settings


class AvatarGenerator:
    """Replicate-based talking avatar generation."""
    
    REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
    
    # Wav2Lip model - free, lightweight, good for talking heads
    WAV2LIP_MODEL = "devxpy/custom-wav2lip:6efbb89680e04ec0a2c899c5e6c8a6a519d28f4e9192b8e4b5e2a0f7b6a0b0c"
    
    def __init__(self):
        settings = get_settings()
        self.api_token = getattr(settings, 'replicate_api_token', '')
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def create_avatar_video(self, image_url: str, audio_url: str) -> str:
        """
        Create a talking avatar video from an image and audio.
        Returns the prediction ID to poll for results.
        """
        if not self.api_token:
            raise RuntimeError("REPLICATE_API_TOKEN not configured")
        
        payload = {
            "version": self.WAV2LIP_MODEL,
            "input": {
                "face": image_url,
                "audio": audio_url,
                "fps": 25,
                "pads": "0 10 0 0",
                "smooth": True,
                "resize_factor": 1
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.REPLICATE_API_URL,
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id")
    
    async def get_prediction_status(self, prediction_id: str) -> dict:
        """Check the status of a prediction."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.REPLICATE_API_URL}/{prediction_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def generate_avatar(self, image_url: str, audio_url: str, max_wait: int = 300) -> str:
        """
        Full flow: create prediction and poll for result.
        Returns the output video URL.
        """
        prediction_id = await self.create_avatar_video(image_url, audio_url)
        
        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = await self.get_prediction_status(prediction_id)
            
            if status.get("status") == "succeeded":
                output = status.get("output")
                if isinstance(output, list) and len(output) > 0:
                    return output[0]
                return output
            
            elif status.get("status") in ["failed", "canceled"]:
                error = status.get("error", "Unknown error")
                raise RuntimeError(f"Avatar generation failed: {error}")
            
            # Wait before polling again
            await asyncio.sleep(5)
        
        raise RuntimeError("Avatar generation timed out")
