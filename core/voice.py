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

# Comprehensive Voice Catalog (All ElevenLabs entries use verified Free-Tier Premade Multilingual IDs)
VOICE_CATALOG = {
    "elevenlabs": [
        # --- Marathi (Multilingual Free-Tier Verified) ---
        {"id": "elevenlabs:pNInz6obpgDQGcFmaJgB|mr", "name": "Adam (Marathi)", "gender": "male", "lang": "marathi", "accent": "Marathi / IN", "tag": "Marathi Tech Authority", "label": "🇮🇳 Adam — Marathi Tech Authority (Male)"},
        {"id": "elevenlabs:JBFqnCBsd6RMkjVDRZzb|mr", "name": "George (Marathi)", "gender": "male", "lang": "marathi", "accent": "Marathi / IN", "tag": "Warm Marathi Storyteller", "label": "🇮🇳 George — Marathi Storyteller (Male)"},
        {"id": "elevenlabs:TX3LPaxmHKxFdv7VOQHJ|mr", "name": "Liam (Marathi)", "gender": "male", "lang": "marathi", "accent": "Marathi / IN", "tag": "Marathi High-Energy Creator", "label": "🇮🇳 Liam — Marathi High-Energy Creator (Male)"},
        {"id": "elevenlabs:EXAVITQu4vr4xnSDxMaL|mr", "name": "Sarah (Marathi)", "gender": "female", "lang": "marathi", "accent": "Marathi / IN", "tag": "Marathi Confident Narrator", "label": "🇮🇳 Sarah — Marathi Confident Narrator (Female)"},
        {"id": "elevenlabs:Xb7hH8MSUJpSbSDYk0k2|mr", "name": "Alice (Marathi)", "gender": "female", "lang": "marathi", "accent": "Marathi / IN", "tag": "Marathi Clear Educator", "label": "🇮🇳 Alice — Marathi Clear Educator (Female)"},
        # --- Hindi / Hinglish (Multilingual Free-Tier Verified) ---
        {"id": "elevenlabs:pNInz6obpgDQGcFmaJgB|hi", "name": "Adam (Hindi)", "gender": "male", "lang": "hindi", "accent": "Hindi / IN", "tag": "Hindi / Hinglish Tech Authority", "label": "🇮🇳 Adam — Hindi / Hinglish Tech Authority (Male)"},
        {"id": "elevenlabs:IKne3meq5aSn9XLyUdCD|hi", "name": "Charlie (Hindi)", "gender": "male", "lang": "hindi", "accent": "Hindi / IN", "tag": "Hindi Energetic Creator", "label": "🇮🇳 Charlie — Hindi Energetic Creator (Male)"},
        {"id": "elevenlabs:nPczCjzI2devNBz1zQrb|hi", "name": "Brian (Hindi)", "gender": "male", "lang": "hindi", "accent": "Hindi / IN", "tag": "Hindi Deep & Reassuring", "label": "🇮🇳 Brian — Hindi Deep & Reassuring (Male)"},
        {"id": "elevenlabs:EXAVITQu4vr4xnSDxMaL|hi", "name": "Sarah (Hindi)", "gender": "female", "lang": "hindi", "accent": "Hindi / IN", "tag": "Hindi Confident Narrator", "label": "🇮🇳 Sarah — Hindi Confident Tech (Female)"},
        {"id": "elevenlabs:XrExE9yKIg1WjnnlVkGX|hi", "name": "Matilda (Hindi)", "gender": "female", "lang": "hindi", "accent": "Hindi / IN", "tag": "Hindi Knowledgeable Educator", "label": "🇮🇳 Matilda — Hindi Tech Educator (Female)"},
        {"id": "elevenlabs:cgSgspJ2msm6clMCkdW9|hi", "name": "Jessica (Hindi)", "gender": "female", "lang": "hindi", "accent": "Hindi / IN", "tag": "Hindi Bright & Expressive", "label": "🇮🇳 Jessica — Hindi Bright & Expressive (Female)"},
        # --- English Male (Premade) ---
        {"id": "elevenlabs:pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "lang": "english", "accent": "American", "tag": "Dominant, Firm Tech Authority", "label": "🇺🇸 Adam (Dominant Tech Authority - Male) [Recommended]"},
        {"id": "elevenlabs:JBFqnCBsd6RMkjVDRZzb", "name": "George", "gender": "male", "lang": "english", "accent": "British", "tag": "Warm, Captivating Storyteller", "label": "🇬🇧 George (Warm Storyteller - UK Male)"},
        {"id": "elevenlabs:IKne3meq5aSn9XLyUdCD", "name": "Charlie", "gender": "male", "lang": "english", "accent": "Australian", "tag": "Deep, Confident & Energetic", "label": "🇦🇺 Charlie (Deep & Energetic - AU Male)"},
        {"id": "elevenlabs:TX3LPaxmHKxFdv7VOQHJ", "name": "Liam", "gender": "male", "lang": "english", "accent": "American", "tag": "High-Energy Social Media Creator", "label": "🇺🇸 Liam (High-Energy Creator - US Male)"},
        {"id": "elevenlabs:nPczCjzI2devNBz1zQrb", "name": "Brian", "gender": "male", "lang": "english", "accent": "American", "tag": "Deep, Resonant & Reassuring", "label": "🇺🇸 Brian (Deep & Comforting - US Male)"},
        {"id": "elevenlabs:N2lVS1w4EtoT3dr4eOWO", "name": "Callum", "gender": "male", "lang": "english", "accent": "American", "tag": "Husky, Dramatic Narrative", "label": "🇺🇸 Callum (Husky Dramatic - US Male)"},
        {"id": "elevenlabs:CwhRBWXzGAHq8TQ4Fs17", "name": "Roger", "gender": "male", "lang": "english", "accent": "American", "tag": "Laid-Back, Casual, Resonant", "label": "🇺🇸 Roger (Laid-Back & Casual - US Male)"},
        {"id": "elevenlabs:onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "gender": "male", "lang": "english", "accent": "British", "tag": "Steady Broadcaster", "label": "🇬🇧 Daniel (Steady Broadcaster - UK Male)"},
        {"id": "elevenlabs:cjVigY5qzO86Huf0OWal", "name": "Eric", "gender": "male", "lang": "english", "accent": "American", "tag": "Smooth, Trustworthy Engineer", "label": "🇺🇸 Eric (Smooth & Trustworthy - US Male)"},
        {"id": "elevenlabs:pqHfZKP75CvOlQylNhV4", "name": "Bill", "gender": "male", "lang": "english", "accent": "American", "tag": "Wise, Mature & Balanced", "label": "🇺🇸 Bill (Wise & Mature - US Male)"},
        {"id": "elevenlabs:iP95p4xoKVk53GoZ742B", "name": "Chris", "gender": "male", "lang": "english", "accent": "American", "tag": "Charming, Down-to-Earth", "label": "🇺🇸 Chris (Casual Engineer - US Male)"},
        {"id": "elevenlabs:bIHbv24MWmeRgasZH58o", "name": "Will", "gender": "male", "lang": "english", "accent": "American", "tag": "Relaxed Optimist", "label": "🇺🇸 Will (Relaxed Optimist - US Male)"},
        {"id": "elevenlabs:SOYHLrjzK2X1ezoPC6cr", "name": "Harry", "gender": "male", "lang": "english", "accent": "American", "tag": "Fierce, High-Intensity Dramatic", "label": "🇺🇸 Harry (High-Intensity Dramatic - US Male)"},
        # --- English Female (Premade) ---
        {"id": "elevenlabs:EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "gender": "female", "lang": "english", "accent": "American", "tag": "Mature, Reassuring, Confident", "label": "🇺🇸 Sarah (Mature & Confident - US Female) [Recommended]"},
        {"id": "elevenlabs:FGY2WhTYpPnrIDTdsKH5", "name": "Laura", "gender": "female", "lang": "english", "accent": "American", "tag": "Enthusiast, Quirky Tech Attitude", "label": "🇺🇸 Laura (Quirky Attitude - US Female)"},
        {"id": "elevenlabs:cgSgspJ2msm6clMCkdW9", "name": "Jessica", "gender": "female", "lang": "english", "accent": "American", "tag": "Playful, Bright & Warm", "label": "🇺🇸 Jessica (Playful & Bright - US Female)"},
        {"id": "elevenlabs:Xb7hH8MSUJpSbSDYk0k2", "name": "Alice", "gender": "female", "lang": "english", "accent": "British", "tag": "Clear, Engaging Educator", "label": "🇬🇧 Alice (Clear Educator - UK Female)"},
        {"id": "elevenlabs:pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "gender": "female", "lang": "english", "accent": "British", "tag": "Velvety, Emotionally Rich Actress", "label": "🇬🇧 Lily (Velvety Dramatic - UK Female)"},
        {"id": "elevenlabs:XrExE9yKIg1WjnnlVkGX", "name": "Matilda", "gender": "female", "lang": "english", "accent": "American", "tag": "Knowledgeable & Professional", "label": "🇺🇸 Matilda (Knowledgeable - US Female)"},
        {"id": "elevenlabs:hpp4J3VqNfWAUOO0d1Us", "name": "Bella", "gender": "female", "lang": "english", "accent": "American", "tag": "Bright, Professional & Warm", "label": "🇺🇸 Bella (Bright & Warm - US Female)"},
        # --- Neutral ---
        {"id": "elevenlabs:SAz9YHcvj6GT2YYXdXww", "name": "River", "gender": "neutral", "lang": "english", "accent": "American", "tag": "Relaxed, Neutral & Informative", "label": "🇺🇸 River (Relaxed & Neutral - US)"}
    ],
    "edge_tts": [
        # Hindi & Hinglish Male (Verified Live Synthesis)
        {"id": "hi-IN-MadhurNeural", "name": "Madhur", "gender": "male", "lang": "hindi", "accent": "Indian", "tag": "Native Hindi / Hinglish Tech", "label": "🇮🇳 Madhur — Native Hindi / Hinglish Tech (Male)"},
        {"id": "en-US-AndrewMultilingualNeural|hi", "name": "Andrew Multilingual (Hindi/EN)", "gender": "male", "lang": "hindi", "accent": "Multilingual", "tag": "Warm Confident Hindi/Hinglish", "label": "🎙️ Andrew — Warm Mentor Multilingual Hindi/EN (Male)"},
        {"id": "en-US-BrianMultilingualNeural|hi", "name": "Brian Multilingual (Hindi/EN)", "gender": "male", "lang": "hindi", "accent": "Multilingual", "tag": "Friendly Storyteller Hindi/EN", "label": "🎙️ Brian — Friendly Storyteller Multilingual Hindi/EN (Male)"},
        {"id": "en-IN-PrabhatNeural|hinglish", "name": "Prabhat (Indian Hinglish)", "gender": "male", "lang": "hindi", "accent": "Indian", "tag": "Indian Accent Hinglish", "label": "🇮🇳 Prabhat — Indian Accent Hinglish (Male)"},
        {"id": "fr-FR-RemyMultilingualNeural|hi", "name": "Remy Multilingual (Hindi/EN)", "gender": "male", "lang": "hindi", "accent": "Multilingual", "tag": "Expressive Multilingual Hindi/EN", "label": "🎙️ Remy — Expressive Multilingual Hindi/EN (Male)"},
        # Hindi & Hinglish Female (Verified Live Synthesis)
        {"id": "hi-IN-SwaraNeural", "name": "Swara", "gender": "female", "lang": "hindi", "accent": "Indian", "tag": "Native Hindi / Hinglish", "label": "🇮🇳 Swara — Native Hindi / Hinglish Conversational (Female)"},
        {"id": "en-US-AvaMultilingualNeural|hi", "name": "Ava Multilingual (Hindi/EN)", "gender": "female", "lang": "hindi", "accent": "Multilingual", "tag": "Caring Expressive Hindi/EN", "label": "🎙️ Ava — Caring Expressive Multilingual Hindi/EN (Female)"},
        {"id": "en-US-EmmaMultilingualNeural|hi", "name": "Emma Multilingual (Hindi/EN)", "gender": "female", "lang": "hindi", "accent": "Multilingual", "tag": "Cheerful Conversational Hindi/EN", "label": "🎙️ Emma — Cheerful Clear Multilingual Hindi/EN (Female)"},
        {"id": "en-IN-NeerjaExpressiveNeural|hinglish", "name": "Neerja Expressive (Indian Hinglish)", "gender": "female", "lang": "hindi", "accent": "Indian", "tag": "Expressive Indian Hinglish", "label": "🇮🇳 Neerja Expressive — Expressive Indian Hinglish (Female)"},
        {"id": "en-IN-NeerjaNeural|hinglish", "name": "Neerja (Indian Hinglish)", "gender": "female", "lang": "hindi", "accent": "Indian", "tag": "Crisp Educator Hinglish", "label": "🇮🇳 Neerja — Crisp Educator Indian Hinglish (Female)"},
        {"id": "fr-FR-VivienneMultilingualNeural|hi", "name": "Vivienne Multilingual (Hindi/EN)", "gender": "female", "lang": "hindi", "accent": "Multilingual", "tag": "Bright Multilingual Hindi/EN", "label": "🎙️ Vivienne — Bright Multilingual Hindi/EN (Female)"},
        # Marathi Male & Female
        {"id": "mr-IN-ManoharNeural", "name": "Manohar", "gender": "male", "lang": "marathi", "accent": "Indian", "tag": "Marathi Tech Authority", "label": "🇮🇳 Manohar (Marathi Tech - Male)"},
        {"id": "mr-IN-AarohiNeural", "name": "Aarohi", "gender": "female", "lang": "marathi", "accent": "Indian", "tag": "Marathi Conversational", "label": "🇮🇳 Aarohi (Marathi - Female)"},
        # English Male & Female
        {"id": "en-IN-PrabhatNeural", "name": "Prabhat", "gender": "male", "lang": "english", "accent": "Indian", "tag": "Crisp Indian Tech English", "label": "🇮🇳 Prabhat (Indian Tech English - Male)"},
        {"id": "en-US-ChristopherNeural", "name": "Christopher", "gender": "male", "lang": "english", "accent": "American", "tag": "Calm Tech Authority", "label": "🇺🇸 Christopher (Calm Tech - US Male)"},
        {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male", "lang": "english", "accent": "American", "tag": "Conversational American", "label": "🇺🇸 Guy (Conversational - US Male)"},
        {"id": "en-GB-RyanNeural", "name": "Ryan", "gender": "male", "lang": "english", "accent": "British", "tag": "Crisp British Tech", "label": "🇬🇧 Ryan (Crisp British - UK Male)"},
        {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female", "lang": "english", "accent": "American", "tag": "Engaging Female Tech", "label": "🇺🇸 Jenny (Engaging Female - US Female)"}
    ]
}

# Dynamic Voice Parameters tailored to chosen Delivery Tone (ElevenLabs + Edge-TTS Prosody)
TONE_VOICE_SETTINGS = {
    "mentor_storyteller": {
        "stability": 0.34,
        "similarity_boost": 0.80,
        "style": 0.48,
        "use_speaker_boost": True
    },
    "dramatic_performance": {
        "stability": 0.32,
        "similarity_boost": 0.82,
        "style": 0.42,
        "use_speaker_boost": True
    },
    "fireship_octane": {
        "stability": 0.42,
        "similarity_boost": 0.75,
        "style": 0.25,
        "use_speaker_boost": True
    },
    "staff_engineer": {
        "stability": 0.72,
        "similarity_boost": 0.85,
        "style": 0.06,
        "use_speaker_boost": True
    },
    "conversational_casual": {
        "stability": 0.55,
        "similarity_boost": 0.75,
        "style": 0.12,
        "use_speaker_boost": True
    },
    "interview_prep": {
        "stability": 0.58,
        "similarity_boost": 0.80,
        "style": 0.18,
        "use_speaker_boost": True
    }
}

EDGE_TTS_PROSODY = {
    "mentor_storyteller": {"rate": "+7%", "pitch": "+2Hz"},
    "fireship_octane": {"rate": "+16%", "pitch": "+2Hz"},
    "dramatic_performance": {"rate": "-4%", "pitch": "-4Hz"},
    "staff_engineer": {"rate": "+4%", "pitch": "-2Hz"},
    "conversational_casual": {"rate": "+8%", "pitch": "+0Hz"},
    "interview_prep": {"rate": "+12%", "pitch": "+1Hz"},
}

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

def _clean_tts_text(text: str, preserve_pauses: bool = False) -> str:
    """Cleans script text for natural speech synthesis and handles explicit pause tokens."""
    if preserve_pauses:
        cleaned = re.sub(r'\[pause\]', ' ... ', text, flags=re.IGNORECASE)
    else:
        cleaned = re.sub(r'\[pause\]', ', ', text, flags=re.IGNORECASE)
        cleaned = cleaned.replace("...", ", ")
    cleaned = cleaned.replace("`", "").replace("*", "").replace("#", "")
    # Replace technical underscores with spaces (e.g. DENSE_RANK -> DENSE RANK)
    cleaned = re.sub(r'(?<=\w)_(?=\w)', ' ', cleaned)
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _split_pause_beats(text: str, max_beats: int = 4) -> List[str]:
    """Splits narration along explicit pause cues ('...' or '[pause]') for natural breathing cadence."""
    normalized = re.sub(r'\[pause\]', ' ... ', text, flags=re.IGNORECASE)
    raw_parts = [p.strip() for p in re.split(r'\s*\.{3,}\s*', normalized) if p and any(ch.isalnum() for ch in p)]
    if len(raw_parts) <= 1:
        return [re.sub(r'\s+', ' ', normalized).strip()]
    if len(raw_parts) > max_beats:
        merged = raw_parts[:max_beats - 1]
        merged.append(", ".join(raw_parts[max_beats - 1:]))
        return merged
    return raw_parts

def _get_cache_path(text: str, voice: str, model_id: str, tone: str = "conversational_casual") -> Path:
    """Generates a unique deterministic cache file path based on text, voice, model, and tone."""
    key = f"{voice}|{model_id}|{tone}|{text}".encode("utf-8")
    hash_str = hashlib.sha256(key).hexdigest()[:24]
    return VOICE_CACHE_DIR / f"tts_{hash_str}.mp3"

def _synthesize_elevenlabs_sync(
    text: str,
    output_path: Path,
    voice_id: str,
    model_id: str,
    tone: str = "conversational_casual",
    lang_code: str = ""
) -> bool:
    """
    Synthesizes speech using ElevenLabs REST API with credit-conservation caching,
    tone-calibrated voice settings, and optional Hindi language hint ('hi').
    Returns True on success, False on failure.
    """
    if not ELEVENLABS_API_KEY:
        print("[Voice] ElevenLabs API key missing, skipping ElevenLabs.")
        return False

    cleaned_text = _clean_tts_text(text, preserve_pauses=(tone in ("mentor_storyteller", "dramatic_performance")))
    if not cleaned_text:
        return False

    # 1. Check Cache First (Saves 100% of credits on re-runs)
    cache_path = _get_cache_path(cleaned_text, f"{voice_id}:{lang_code}", model_id, tone)
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        try:
            shutil.copyfile(cache_path, output_path)
            print(f"[Voice] ⚡ Reused cached ElevenLabs audio (Saved {len(cleaned_text)} credits)")
            return True
        except Exception:
            pass

    # 2. Tone-tailored voice settings
    voice_settings = TONE_VOICE_SETTINGS.get(tone, {
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.10,
        "use_speaker_boost": True
    })

    # 3. Call ElevenLabs API
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": cleaned_text,
        "model_id": model_id,
        "voice_settings": voice_settings
    }
    if lang_code == "hi" and model_id in ["eleven_flash_v2_5", "eleven_turbo_v2_5"]:
        payload["language_code"] = "hi"

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=25)
        if res.status_code == 200 and len(res.content) > 1000:
            output_path.write_bytes(res.content)
            # Save to cache
            try:
                cache_path.write_bytes(res.content)
            except Exception:
                pass
            print(f"[Voice] ✅ ElevenLabs synthesized scene ({model_id}, tone: {tone}, {len(cleaned_text)} chars)")
            return True
        else:
            print(f"[Voice] ElevenLabs returned {res.status_code}: {res.text[:120]}")
            return False
    except Exception as e:
        print(f"[Voice] ElevenLabs request failed ({e})")
        return False

async def _synthesize_edge_tts_scene(text: str, output_path: Path, voice: str, tone: str = "conversational_casual") -> bool:
    """
    Synthesizes speech using Microsoft Edge-TTS with tone-matched rate & pitch prosody.
    When explicit pause beats ('...' / '[pause]') exist or tone is 'mentor_storyteller',
    splits along pause cues, applies per-phrase curiosity/excitement inflection, and inserts
    genuine 300ms breathing silence between phrases via FFmpeg.
    """
    preserve = (tone == "mentor_storyteller") or bool(re.search(r'(\[pause\]|\.{3,})', text, re.IGNORECASE))
    cleaned_text = _clean_tts_text(text, preserve_pauses=preserve)
    if not cleaned_text:
        return False

    prosody = EDGE_TTS_PROSODY.get(tone, {"rate": "+8%", "pitch": "+0Hz"})
    rate = prosody["rate"]
    pitch = prosody["pitch"]

    beats = _split_pause_beats(cleaned_text, max_beats=4) if preserve else [cleaned_text]
    if len(beats) > 1:
        beat_files: List[Path] = []
        try:
            for bi, beat_txt in enumerate(beats):
                if tone == "mentor_storyteller":
                    if beat_txt.endswith("?"):
                        b_rate, b_pitch = "+6%", "+3Hz"
                    elif "!" in beat_txt or any(kw in beat_txt.lower() for kw in ("boom", "magic", "secret", "finally", "exactly")):
                        b_rate, b_pitch = "+11%", "+4Hz"
                    elif len(beat_txt) <= 38:
                        b_rate, b_pitch = "+4%", "+2Hz"
                    else:
                        b_rate, b_pitch = rate, pitch
                else:
                    b_rate, b_pitch = rate, pitch

                bp = output_path.parent / f"{output_path.stem}_beat{bi}.mp3"
                ok = False
                for _ in range(2):
                    try:
                        comm = edge_tts.Communicate(beat_txt, voice, rate=b_rate, pitch=b_pitch)
                        await comm.save(str(bp))
                        if bp.exists() and bp.stat().st_size > 400:
                            ok = True
                            break
                    except Exception:
                        await asyncio.sleep(0.3)
                if not ok:
                    beat_files = []
                    break
                beat_files.append(bp)

            if len(beat_files) > 1:
                cmd = [str(FFMPEG_EXE), "-y"]
                for bp in beat_files:
                    cmd.extend(["-i", str(bp.resolve())])
                cmd.extend(["-f", "lavfi", "-t", "0.30", "-i", "anullsrc=r=44100:cl=stereo"])
                sil_idx = len(beat_files)
                parts = []
                seq = []
                for idx in range(len(beat_files)):
                    parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo[b{idx}]")
                    seq.append(f"[b{idx}]")
                    if idx < len(beat_files) - 1:
                        parts.append(f"[{sil_idx}:a]atrim=0:0.30[p{idx}]")
                        seq.append(f"[p{idx}]")
                filt = ";".join(parts) + ";" + "".join(seq) + f"concat=n={len(seq)}:v=0:a=1[outa]"
                cmd.extend(["-filter_complex", filt, "-map", "[outa]", "-c:a", "libmp3lame", "-b:a", "192k", str(output_path.resolve())])
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                    return True
        except Exception as e:
            print(f"[Voice] Multi-beat pause stitch notice ({e}), falling back cleanly...")
        finally:
            for bp in beat_files:
                try:
                    if bp.exists():
                        bp.unlink()
                except Exception:
                    pass

    plain_text = _clean_tts_text(text, preserve_pauses=False)
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(plain_text, voice, rate=rate, pitch=pitch)
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
    elevenlabs_model: str = DEFAULT_ELEVENLABS_MODEL,
    tone: str = "conversational_casual",
    allow_elevenlabs: bool = True
) -> None:
    """
    Synthesizes speech for a single scene:
    - Only calls ElevenLabs API if allow_elevenlabs=True AND voice starts with 'elevenlabs:'.
    - Otherwise strictly uses Microsoft Edge-TTS (0 ElevenLabs credits consumed), with tone-matched prosody.
    """
    is_elevenlabs = allow_elevenlabs and voice.startswith("elevenlabs:")
    
    if is_elevenlabs:
        raw_vid = voice.split("elevenlabs:", 1)[1].strip()
        lang_code = ""
        if "|" in raw_vid:
            voice_id, lang_code = raw_vid.split("|", 1)
            voice_id, lang_code = voice_id.strip(), lang_code.strip().lower()
        else:
            voice_id = raw_vid
        success = _synthesize_elevenlabs_sync(text, output_path, voice_id, elevenlabs_model, tone=tone, lang_code=lang_code)
        if success:
            return
        print("[Voice] Falling back to high-fidelity Edge-TTS for this scene...")
        fallback_voice = "mr-IN-ManoharNeural" if lang_code == "mr" else ("hi-IN-MadhurNeural" if lang_code == "hi" else "en-US-ChristopherNeural")
        asyncio.run(_synthesize_edge_tts_scene(text, output_path, fallback_voice, tone=tone))
        return

    # Standard Edge-TTS path (never consumes ElevenLabs credits)
    clean_voice = voice.replace("edge:", "").split("|", 1)[0].strip()
    if clean_voice.startswith("elevenlabs:"):
        clean_voice = "en-US-ChristopherNeural"
    asyncio.run(_synthesize_edge_tts_scene(text, output_path, clean_voice, tone=tone))

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
    elevenlabs_model: str = DEFAULT_ELEVENLABS_MODEL,
    tone: str = "conversational_casual",
    allow_elevenlabs: bool = True
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

    # 1. Synthesize all scene voiceovers (dynamic per-scene tone when tone == "auto_dynamic")
    for i, (sc, text, p) in enumerate(zip(scenes, scene_texts, scene_audio_paths)):
        sc_tone = (sc.get("scene_tone") or "conversational_casual") if tone == "auto_dynamic" else tone
        _synthesize_single_scene(text, p, voice=voice, elevenlabs_model=elevenlabs_model, tone=sc_tone, allow_elevenlabs=allow_elevenlabs)
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
    # Pass original script excerpt as prompt hint so Hinglish/English tech spellings (RAG, JSON, SQL, Fine-Tuning) stay exact
    combined_prompt = re.sub(r'\[pause\]', ' ', " ".join(scene_texts), flags=re.IGNORECASE)[:750]
    word_timestamps = []
    try:
        word_timestamps = _extract_word_timestamps(final_audio_path, prompt_hint=combined_prompt)
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

def _extract_word_timestamps(audio_path: Path, prompt_hint: str = "") -> List[Dict[str, Any]]:
    """Calls Groq Whisper Large v3 to get microsecond word-level timestamps with script vocabulary hint."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required for word timestamp alignment.")
    
    client = Groq(api_key=GROQ_API_KEY)
    with open(audio_path, "rb") as file:
        req_kwargs = {
            "file": (audio_path.name, file.read()),
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
            "timestamp_granularities": ["word"],
        }
        if prompt_hint.strip():
            req_kwargs["prompt"] = prompt_hint.strip()
        transcription = client.audio.transcriptions.create(**req_kwargs)
    
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
        narration = re.sub(r'\[pause\]', ' ', sc.get("narration", ""), flags=re.IGNORECASE).strip()
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
