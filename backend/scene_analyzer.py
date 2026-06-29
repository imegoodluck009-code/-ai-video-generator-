import re

def split_script_into_scenes(script: str) -> list:
    """
    Splits script into scenes based on sentences/phrases.
    Returns list of dicts: {text, keywords, duration_estimate}
    """
    # Split by periods, but also by commas for short phrases
    raw_scenes = re.split(r'[.!?]+', script)
    scenes = []
    
    for scene_text in raw_scenes:
        scene_text = scene_text.strip()
        if not scene_text:
            continue
        
        # Extract keywords for Pexels search (nouns/adjectives)
        words = scene_text.lower().split()
        keywords = [w for w in words if len(w) > 3][:3]  # simple keyword extraction
        if not keywords:
            keywords = ["nature"]
        
        # Estimate duration: ~0.5s per word
        word_count = len(scene_text.split())
        duration = max(2.0, word_count * 0.5)  # minimum 2 seconds
        
        scenes.append({
            "text": scene_text,
            "keywords": " ".join(keywords),
            "duration": duration
        })
    
    return scenes

def get_scene_search_query(scene: dict, fallback: str = "nature") -> str:
    """Get Pexels search query for a scene."""
    return scene.get("keywords", fallback)
