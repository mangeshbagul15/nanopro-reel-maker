import requests
import json
from pathlib import Path
from core.config import ELEVENLABS_API_KEY, OUTPUT_DIR, FFMPEG_EXE

def test_elevenlabs():
    print("=== TESTING ELEVENLABS API ===")
    assert ELEVENLABS_API_KEY, "ELEVENLABS_API_KEY is missing!"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # 1. Fetch user subscription
    user_res = requests.get("https://api.elevenlabs.io/v1/user", headers=headers, timeout=10)
    print("User info status:", user_res.status_code)
    if user_res.status_code == 200:
        sub = user_res.json().get("subscription", {})
        used = sub.get("character_count", 0)
        limit = sub.get("character_limit", 10000)
        print(f"Credits Used: {used} / {limit} (Remaining: {limit - used})")
    
    # 2. Fetch available voices
    voices_res = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=10)
    if voices_res.status_code == 200:
        voices = voices_res.json().get("voices", [])
        print(f"Total available voices: {len(voices)}")
        for v in voices[:6]:
            print(f"  - {v['name']} (ID: {v['voice_id']})")
            
    # 3. Test Synthesis with user's requested model (eleven_flash_v2_5 - saves credits!)
    test_voice_id = "pNInz6obpgDQGcFmaJgB" # Adam
    model_id = "eleven_flash_v2_5"
    text = "NanoPro Reel Maker is online."
    
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{test_voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    print(f"\nSynthesizing sample text ('{text}') with model '{model_id}'...")
    tts_res = requests.post(tts_url, json=payload, headers=headers, timeout=15)
    print("TTS Status Code:", tts_res.status_code)
    assert tts_res.status_code == 200, f"TTS synthesis failed: {tts_res.text}"
    
    out_mp3 = OUTPUT_DIR / "test_elevenlabs_sample.mp3"
    out_mp3.write_bytes(tts_res.content)
    print(f"Saved audio sample to {out_mp3} (Size: {len(tts_res.content)} bytes)")
    print("=== ELEVENLABS TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_elevenlabs()
