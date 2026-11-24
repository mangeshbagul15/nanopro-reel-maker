import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import requests
import edge_tts
from groq import Groq
from core.config import GROQ_API_KEY, ELEVENLABS_API_KEY, OUTPUT_DIR, FFMPEG_EXE

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_ELEVENLABS_MODEL = "eleven_flash_v2_5"

# ElevenLabs Supported Models
ELEVENLABS_MODELS = {
    "eleven_flash_v2_5": {
        "id": "eleven_flash_v2_5",
        "name": "⚡ Eleven Flash v2.5",
        "desc": "Our fastest and most emotive, human-like model (50% fewer credits - Saves Free Tier)",
        "cost_multiplier": 0.5
    },
    "eleven_multilingual_v2": {
        "id": "eleven_multilingual_v2",
        "name": "🎭 Eleven Multilingual v2",
        "desc": "Emotionally rich delivery for dramatic performances",
        "cost_multiplier": 1.0
    },
    "eleven_turbo_v2_5": {
        "id": "eleven_turbo_v2_5",
        "name": "🚀 Eleven Turbo v2.5",
        "desc": "Our best model for real-time and agents",
        "cost_multiplier": 0.5
    }
}

# Voice Cache Directory to prevent wasting the 10,000 monthly credits
VOICE_CACHE_DIR = OUTPUT_DIR / "voice_cache"
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_elevenlabs_usage() -> Dict[str, Any]:
    """Fetches real-time character credit consumption and limits from ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        return {
            "tier": "none",
            "character_count": 0,
            "character_limit": 10000,
            "remaining": 10000,
            "percent_used": 0.0
        }
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=5
        )
        if r.status_code == 200:
            sub = r.json().get("subscription", {})
            used = sub.get("character_count", 0)
            limit = sub.get("character_limit", 10000)
            remaining = max(0, limit - used)
            pct = round((used / max(1, limit)) * 100, 1)
            return {
                "tier": sub.get("tier", "free"),
                "character_count": used,
                "character_limit": limit,
                "remaining": remaining,
                "percent_used": pct
            }
    except Exception as e:
        print(f"[Voice] ElevenLabs subscription fetch warning: {e}")
        
    return {
        "tier": "free",
        "character_count": 0,
        "character_limit": 10000,
        "remaining": 10000,
        "percent_used": 0.0
    }

def get_audio_duration(file_path: Path) -> float:
    """Extracts exact duration of an audio file using FFmpeg."""
    try:
        cmd = [str(FFMPEG_EXE), "-i", str(file_path.resolve())]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        print(f"[Voice] Error getting audio duration for {file_path}: {e}")
    return 0.0

def _clean_tts_text(text: str) -> str:
    """Cleans script text for natural speech synthesis and removes technical clutter."""
    cleaned = text.replace("...", ", ")
    cleaned = cleaned.replace("`", "").replace("*", "").replace("#", "")
    # Replace technical underscores with spaces (e.g. DENSE_RANK -> DENSE RANK)
    cleaned = re.sub(r'(?<=\w)_(?=\w)', ' ', cleaned)
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def _get_cache_path(text: str, voice: str, model_id: str) -> Path:
    """Generates a unique deterministic cache file path based on text, voice, and model."""
    key = f"{voice}|{model_id}|{text}".encode("utf-8")
    hash_str = hashlib.sha256(key).hexdigest()[:24]
    return VOICE_CACHE_DIR / f"tts_{hash_str}.mp3"

def _synthesize_elevenlabs_sync(text: str, output_path: Path, voice_id: str, model_id: str) -> bool:
    """
    Synthesizes speech using ElevenLabs REST API with credit-conservation caching.
    Returns True on success, False on failure.
    """
    if not ELEVENLABS_API_KEY:
        print("[Voice] ElevenLabs API key missing, skipping ElevenLabs.")
        return False

    cleaned_text = _clean_tts_text(text)
    if not cleaned_text:
        return False

    # 1. Check Cache First (Saves 100% of credits on re-runs)
    cache_path = _get_cache_path(cleaned_text, voice_id, model_id)
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        try:
            shutil.copyfile(cache_path, output_path)
            print(f"[Voice] ⚡ Reused cached ElevenLabs audio (Saved {len(cleaned_text)} credits)")
            return True
        except Exception:
            pass

    # 2. Call ElevenLabs API
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": cleaned_text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "use_speaker_boost": True
        }
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=25)
        if res.status_code == 200 and len(res.content) > 1000:
            output_path.write_bytes(res.content)
            # Save to cache
            try:
                cache_path.write_bytes(res.content)
            except Exception:
                pass
            print(f"[Voice] ✅ ElevenLabs synthesized scene with model '{model_id}' ({len(cleaned_text)} chars)")
            return True
        else:
            print(f"[Voice] ElevenLabs returned {res.status_code}: {res.text[:120]}")
            return False
    except Exception as e:
        print(f"[Voice] ElevenLabs request failed ({e})")
        return False

async def _synthesize_edge_tts_scene(text: str, output_path: Path, voice: str) -> bool:
    """Synthesizes speech using Microsoft Edge-TTS with automatic retries."""
    cleaned_text = _clean_tts_text(text)
    if not cleaned_text:
        return False

    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(cleaned_text, voice, rate="+6%", pitch="+0Hz")
            await communicate.save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 1000:
                return True
        except Exception as e:
            print(f"[Voice] Edge-TTS attempt {attempt + 1} warning: {e}")
            await asyncio.sleep(0.5)

    return False

def _synthesize_single_scene(
    text: str,
    output_path: Path,
    voice: str,
    elevenlabs_model: str = DEFAULT_ELEVENLABS_MODEL
) -> None:
    """
    Synthesizes speech for a single scene:
    - If voice starts with 'elevenlabs:', uses ElevenLabs API.
    - If ElevenLabs fails (e.g. quota limit reached), falls back to Edge-TTS.
    - If voice is standard Edge-TTS, uses Edge-TTS.
    """
    is_elevenlabs = voice.startswith("elevenlabs:")
    
    if is_elevenlabs:
        voice_id = voice.split("elevenlabs:", 1)[1].strip()
        success = _synthesize_elevenlabs_sync(text, output_path, voice_id, elevenlabs_model)
        if success:
            return
        print("[Voice] Falling back to high-fidelity Edge-TTS for this scene...")
        # Fallback voice
        fallback_voice = "en-US-ChristopherNeural"
        asyncio.run(_synthesize_edge_tts_scene(text, output_path, fallback_voice))
        return

    # Standard Edge-TTS path
    clean_voice = voice.replace("edge:", "")
    asyncio.run(_synthesize_edge_tts_scene(text, output_path, clean_voice))

def _ensure_valid_audio(path: Path) -> None:
    """Generates a 2-second silent audio if an audio synthesis failed, guaranteeing FFmpeg never crashes."""
    if not path.exists() or path.stat().st_size < 100:
        print(f"[Voice] Generating fallback audio for {path.name}...")
        cmd = [
            str(FFMPEG_EXE), "-y",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "2.0",
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(path.resolve())
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def generate_voiceover(
    scenes: List[Dict[str, Any]],
    voice: str = DEFAULT_VOICE,
    elevenlabs_model: str = DEFAULT_ELEVENLABS_MODEL
) -> Tuple[Path, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Synthesizes each scene's voiceover individually to guarantee 100% exact timing
    match between spoken narration and on-screen visuals.
    Supports both ElevenLabs AI Voices and Microsoft Edge-TTS with caching.
    
    Returns:
        (audio_file_path, word_timestamps, scenes_with_exact_timestamps)
    """
    scene_audio_paths = []
    scene_texts = []
    
    for i, sc in enumerate(scenes):
        sc_text = sc.get("narration", "").strip()
        if not sc_text:
            sc_text = sc.get("visual_data", {}).get("title", f"Scene {i + 1}")
        scene_texts.append(sc_text)
        sc_path = OUTPUT_DIR / f"scene_{i + 1:02d}_voice.mp3"
        scene_audio_paths.append(sc_path)

    # 1. Synthesize all scene voiceovers
    for i, (text, p) in enumerate(zip(scene_texts, scene_audio_paths)):
        _synthesize_single_scene(text, p, voice=voice, elevenlabs_model=elevenlabs_model)
        _ensure_valid_audio(p)

    # 2. Measure exact duration of each scene's audio
    scene_durations = [max(1.5, get_audio_duration(p)) for p in scene_audio_paths]

    # 3. Concatenate scene audios into full reel voiceover via FFmpeg
    final_audio_path = OUTPUT_DIR / "reel_voiceover.mp3"
    concat_cmd = [str(FFMPEG_EXE), "-y"]
    for p in scene_audio_paths:
        concat_cmd.extend(["-i", str(p.resolve())])
    filter_expr = "".join(f"[{i}:a]" for i in range(len(scene_audio_paths))) + f"concat=n={len(scene_audio_paths)}:v=0:a=1[a]"
    concat_cmd.extend(["-filter_complex", filter_expr, "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(final_audio_path.resolve())])
    
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    total_audio_duration = get_audio_duration(final_audio_path)
    if total_audio_duration <= 0:
        total_audio_duration = sum(scene_durations)

    # 4. Compute exact scene timestamps
    scenes_with_timestamps = []
    cur_time = 0.0
    for i, sc in enumerate(scenes):
        dur = scene_durations[i]
        s_start = cur_time
        s_end = cur_time + dur
        
        # Ensure the last scene aligns exactly with total audio
        if i == len(scenes) - 1:
            s_end = max(s_end, total_audio_duration)
            dur = s_end - s_start
            
        s_copy = dict(sc)
        s_copy["start_time"] = round(s_start, 3)
        s_copy["end_time"] = round(s_end, 3)
        s_copy["duration"] = round(dur, 3)
        scenes_with_timestamps.append(s_copy)
        cur_time = s_end

    # 5. Extract Word Timestamps via Groq Whisper for karaoke subtitles
    word_timestamps = []
    try:
        word_timestamps = _extract_word_timestamps(final_audio_path)
    except Exception as e:
        print(f"[Voice] Groq Whisper extraction notice ({e}), generating robust fallback timestamps...")
        word_timestamps = _generate_fallback_word_timestamps(scenes_with_timestamps)

    # Cleanup individual scene MP3 files
    for p in scene_audio_paths:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    return final_audio_path, word_timestamps, scenes_with_timestamps

def _extract_word_timestamps(audio_path: Path) -> List[Dict[str, Any]]:
    """Calls Groq Whisper Large v3 to get microsecond word-level timestamps."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required for word timestamp alignment.")
    
    client = Groq(api_key=GROQ_API_KEY)
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path.name, file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    
    words = []
    if hasattr(transcription, "words") and transcription.words:
        for w in transcription.words:
            if isinstance(w, dict):
                words.append({
                    "word": str(w.get("word", "")).strip(),
                    "start": round(float(w.get("start", 0)), 3),
                    "end": round(float(w.get("end", 0)), 3)
                })
            else:
                words.append({
                    "word": str(getattr(w, "word", "")).strip(),
                    "start": round(float(getattr(w, "start", 0)), 3),
                    "end": round(float(getattr(w, "end", 0)), 3)
                })
    return [w for w in words if w["word"]]

def _generate_fallback_word_timestamps(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fallback word timing generator that guarantees words match their exact scene
    boundaries if Groq API is temporarily unreachable.
    """
    all_words = []
    for sc in scenes:
        narration = sc.get("narration", "").strip()
        words = narration.split()
        if not words:
            continue
        sc_start = sc.get("start_time", 0.0)
        sc_dur = sc.get("duration", 5.0)
        time_per_word = sc_dur / max(1, len(words))
        
        for idx, w in enumerate(words):
            w_start = sc_start + (idx * time_per_word)
            w_end = w_start + (time_per_word * 0.95)
            all_words.append({
                "word": w.strip(),
                "start": round(w_start, 3),
                "end": round(w_end, 3)
            })
    return all_words
