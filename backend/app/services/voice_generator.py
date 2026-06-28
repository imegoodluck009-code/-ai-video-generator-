import httpx
from pathlib import Path
from app.config import get_settings


class VoiceGenerator:
    """ElevenLabs text-to-speech service."""
    
    ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    
    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, 'elevenlabs_api_key', '')
        print(f"🔑 API KEY LOADED: {self.api_key[:10]}...")
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def generate_voice(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM", output_path: str = "voiceover.mp3") -> str:
        """
        Generate voiceover from text using ElevenLabs.
        Default voice: Rachel (21m00Tcm4TlvDq8ikWAM)
        """
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not configured")
        
        url = f"{self.ELEVENLABS_URL}/{voice_id}"
        
        payload = {
            "text": text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with httpx.AsyncClient() as client:
            print(f"🔍 HEADERS: {self.headers}")
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            # Save audio file
            with open(output_path, "wb") as f:
                f.write(response.content)
        
        return output_path
