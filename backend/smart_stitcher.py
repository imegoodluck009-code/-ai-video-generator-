import os
import subprocess
from scene_analyzer import split_script_into_scenes, get_scene_search_query

async def generate_scene_voiceovers(script: str, tts_func, tmp_dir: str) -> list:
    """
    Generate voiceover for each scene and return list of {scene, audio_path, duration}
    """
    scenes = split_script_into_scenes(script)
    results = []
    
    for i, scene in enumerate(scenes):
        audio_path = os.path.join(tmp_dir, f"voice_{i}.mp3")
        try:
            await tts_func(scene["text"], audio_path)
            # Get actual duration from file
            duration = get_audio_duration(audio_path)
            results.append({
                "scene": scene,
                "audio_path": audio_path,
                "duration": duration
            })
        except Exception as e:
            print(f"TTS failed for scene {i}: {e}")
            results.append({
                "scene": scene,
                "audio_path": None,
                "duration": scene["duration"]  # use estimate
            })
    
    return results

def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except:
        return 2.0  # fallback

def cut_clip_to_duration(input_path: str, output_path: str, duration: float):
    """Cut a video clip to exact duration."""
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-t", str(duration), "-c", "copy",
        output_path
    ], check=True, capture_output=True)

def stitch_scenes(scene_clips: list, output_path: str):
    """Stitch multiple clips together with FFmpeg concat."""
    list_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    with open(list_file, "w") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")
    
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_path
    ], check=True, capture_output=True)
