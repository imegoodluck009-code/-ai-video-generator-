import sys

with open('videos.py', 'r') as f:
    lines = f.readlines()

# Replace lines 88-106 (0-indexed: 87-105)
new_section = '''        # 3. Generate voiceover if requested
        voiceover_path = None
        # Ensure temp directory exists
        if not os.path.exists("temp"):
            os.makedirs("temp")
            print("📁 Created temp directory")

        if request.include_voiceover and request.voice_text:
            jobs[job_id]["message"] = "Generating voiceover with ElevenLabs..."
            voice = VoiceGenerator()
            voiceover_path = f"temp/{job_id}_voice.mp3"
            try:
                await voice.generate_voice(
                    text=request.voice_text,
                    output_path=voiceover_path
                )
                jobs[job_id]["message"] = "Voiceover generated, processing video..."
            except Exception as e:
                error_msg = f"Voiceover failed: {str(e)}"
                print(f"🔴 VOICE ERROR: {error_msg}")
                jobs[job_id]["message"] = error_msg
                voiceover_path = None

'''

new_lines = lines[:87] + [new_section] + lines[106:]

with open('videos.py', 'w') as f:
    f.writelines(new_lines)

print("Fixed!")
