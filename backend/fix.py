with open('app/routers/videos.py','r') as f: c=f.read()
s='        # 3. Generate voiceover if requested\n'
e='        # 4. Render video with FFmpeg\n'
a=c.find(s); b=c.find(e)
new='        # 3. Generate voiceover if requested\n        voiceover_path = None\n        # Ensure temp directory exists\n        if not os.path.exists("temp"):\n            os.makedirs("temp")\n            print("📁 Created temp directory")\n\n        if request.include_voiceover and request.voice_text:\n            jobs[job_id]["message"] = "Generating voiceover with ElevenLabs..."\n            voice = VoiceGenerator()\n            voiceover_path = f"temp/{job_id}_voice.mp3"\n            try:\n                await voice.generate_voice(\n                    text=request.voice_text,\n                    output_path=voiceover_path\n                )\n                jobs[job_id]["message"] = "Voiceover generated, processing video..."\n            except Exception as e:\n                error_msg = f"Voiceover failed: {str(e)}"\n                print(f"🔴 VOICE ERROR: {error_msg}")\n                jobs[job_id]["message"] = error_msg\n                voiceover_path = None\n\n'
with open('app/routers/videos.py','w') as f: f.write(c[:a]+new+c[b:])
print("Fixed!")
