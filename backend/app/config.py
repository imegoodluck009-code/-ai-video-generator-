from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Video Generator"
    debug: bool = False
    
    # Pexels
    pexels_api_key: str = ""
    
    # ElevenLabs
    elevenlabs_api_key: str = ""
    
    # Replicate
    replicate_api_token: str = ""
    
    # Railway / general
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Settings()
