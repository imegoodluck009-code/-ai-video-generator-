import edge_tts
import asyncio
import os

TMP_DIR = "/tmp" if os.path.exists("/tmp") else (os.environ.get("PREFIX", "/usr") + "/tmp")

async def generate_voiceover(text: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "voiceover.mp3")
    voice = "en-US-GuyNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path
