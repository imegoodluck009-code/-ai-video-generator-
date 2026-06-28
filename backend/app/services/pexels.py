import httpx
from typing import Optional, List, Dict
from app.config import get_settings


PEXELS_API_URL = "https://api.pexels.com/videos"


class PexelsService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.pexels_api_key
        self.headers = {"Authorization": self.api_key}
    
    async def search_videos(
        self,
        query: str,
        per_page: int = 10,
        orientation: str = "landscape"
    ) -> Optional[List[Dict]]:
        """Search Pexels for stock videos matching the query."""
        if not self.api_key:
            return None
        
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{PEXELS_API_URL}/search",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("videos", [])
            except Exception as e:
                print(f"Pexels API error: {e}")
                return None
    
    async def get_popular_videos(self, per_page: int = 10) -> Optional[List[Dict]]:
        """Fetch popular videos from Pexels."""
        if not self.api_key:
            return None
        
        params = {"per_page": per_page}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{PEXELS_API_URL}/popular",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("videos", [])
            except Exception as e:
                print(f"Pexels API error: {e}")
                return None
