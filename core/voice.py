import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import requests
import edge_tts
from groq import Groq
from core.config import GROQ_API_KEY, ELEVENLABS_API_KEY, OUTPUT_DIR, FFMPEG_EXE
from core.tone_engine import (
    DEFAULT_CONCRETE_TONE,
    DEFAULT_TONE_KEY,
    DUAL_TONE_KEY,
    TONE_PROFILES,
    get_clause_prosody,
    get_tone_profile,
    is_dual_tone,
    resolve_effective_tone,
    split_text_to_dual_dialogue,
)

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
        # Dual Hinglish / Hindi / Multilingual Dialogue Pairs (Female Curious Q + Male Mentor Solver)
        {"id": "dual:hi-IN-SwaraNeural+hi-IN-MadhurNeural", "name": "Swara & Madhur (Dual Hinglish)", "gender": "dual", "lang": "hindi", "accent": "Indian", "tag": "Dual Hinglish Q&A Dialogue", "label": "🗣️🇮🇳 Dual Hinglish: Swara (Curious Q) + Madhur (Mentor A) [Recommended Dual]"},
        {"id": "dual:en-IN-NeerjaExpressiveNeural|hinglish+en-IN-PrabhatNeural|hinglish", "name": "Neerja & Prabhat (Dual Hinglish)", "gender": "dual", "lang": "hindi", "accent": "Indian", "tag": "Dual Indian Hinglish", "label": "🗣️🇮🇳 Dual Indian Hinglish: Neerja (Curious Q) + Prabhat (Mentor A)"},
        {"id": "dual:en-US-EmmaMultilingualNeural|hi+en-US-AndrewMultilingualNeural|hi", "name": "Emma & Andrew (Dual Multilingual)", "gender": "dual", "lang": "hindi", "accent": "Multilingual", "tag": "Dual Expressive Hindi/EN", "label": "🗣️🎙️ Dual Multilingual Hindi/EN: Emma (Curious Q) + Andrew (Mentor A)"},
        {"id": "dual:en-US-AvaMultilingualNeural|hi+en-US-BrianMultilingualNeural|hi", "name": "Ava & Brian (Dual Multilingual)", "gender": "dual", "lang": "hindi", "accent": "Multilingual", "tag": "Dual Caring Hindi/EN", "label": "🗣️🎙️ Dual Caring Hindi/EN: Ava (Curious Q) + Brian (Mentor A)"},
        {"id": "dual:mr-IN-AarohiNeural+mr-IN-ManoharNeural", "name": "Aarohi & Manohar (Dual Marathi)", "gender": "dual", "lang": "marathi", "accent": "Indian", "tag": "Dual Marathi Q&A Dialogue", "label": "🗣️🇮🇳 Dual Marathi: Aarohi (Curious Q) + Manohar (Mentor A)"},
        {"id": "dual:en-US-JennyNeural+en-US-ChristopherNeural", "name": "Jenny & Christopher (Dual English)", "gender": "dual", "lang": "english", "accent": "American", "tag": "Dual Tech English Q&A", "label": "🗣️🇺🇸 Dual Tech English: Jenny (Curious Q) + Christopher (Mentor A)"},
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

# Canonical 2026 Dynamic Voice Parameters & Edge-TTS Prosody (from core/tone_engine.py)
TONE_VOICE_SETTINGS: Dict[str, Dict[str, Any]] = {
    k: dict(v["elevenlabs"]) for k, v in TONE_PROFILES.items()
}

EDGE_TTS_PROSODY: Dict[str, Dict[str, str]] = {
    k: dict(v["edge_base"]) for k, v in TONE_PROFILES.items()
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

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_ORDINAL_SPECIAL = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth",
    9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
    16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth",
    30: "thirtieth", 40: "fortieth", 50: "fiftieth", 60: "sixtieth", 70: "seventieth", 80: "eightieth", 90: "ninetieth",
}

_MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}
_MONTH_ABBR = {
    "jan": "January", "feb": "February", "mar": "March", "apr": "April",
    "jun": "June", "jul": "July", "aug": "August", "sep": "September", "sept": "September",
    "oct": "October", "nov": "November", "dec": "December",
}

_DEVANAGARI_WORD_MAP = [
    # Months (Hindi / Marathi)
    (r"(?<![\w\u0900-\u097F])(?:जनवरी|जानेवारी)(?![\w\u0900-\u097F])", "January"),
    (r"(?<![\w\u0900-\u097F])(?:फरवरी|फेब्रुवारी)(?![\w\u0900-\u097F])", "February"),
    (r"(?<![\w\u0900-\u097F])मार्च(?![\w\u0900-\u097F])", "March"),
    (r"(?<![\w\u0900-\u097F])(?:अप्रैल|एप्रिल)(?![\w\u0900-\u097F])", "April"),
    (r"(?<![\w\u0900-\u097F])(?:मई|मे)(?![\w\u0900-\u097F])", "May"),
    (r"(?<![\w\u0900-\u097F])जून(?![\w\u0900-\u097F])", "June"),
    (r"(?<![\w\u0900-\u097F])(?:जुलाई|जुलै)(?![\w\u0900-\u097F])", "July"),
    (r"(?<![\w\u0900-\u097F])(?:अगस्त|ऑगस्ट)(?![\w\u0900-\u097F])", "August"),
    (r"(?<![\w\u0900-\u097F])(?:सितंबर|सप्टेंबर)(?![\w\u0900-\u097F])", "September"),
    (r"(?<![\w\u0900-\u097F])(?:अक्टूबर|ऑक्टोबर)(?![\w\u0900-\u097F])", "October"),
    (r"(?<![\w\u0900-\u097F])(?:नवंबर|नोव्हेंबर)(?![\w\u0900-\u097F])", "November"),
    (r"(?<![\w\u0900-\u097F])(?:दिसंबर|डिसेंबर)(?![\w\u0900-\u097F])", "December"),
    # Units / metrics / common tech transliterations
    (r"(?<![\w\u0900-\u097F])(?:प्रतिशत|टक्के)(?![\w\u0900-\u097F])", "percent"),
    (r"(?<![\w\u0900-\u097F])(?:सेकंड|सेकंद)(?![\w\u0900-\u097F])", "seconds"),
    (r"(?<![\w\u0900-\u097F])(?:मिनट|मिनिटे|मिनिट)(?![\w\u0900-\u097F])", "minutes"),
    (r"(?<![\w\u0900-\u097F])(?:घंटे|घंटा|तास)(?![\w\u0900-\u097F])", "hours"),
    (r"(?<![\w\u0900-\u097F])(?:शून्य|झिरो|ज़ीरो|जीरो)(?![\w\u0900-\u097F])", "zero"),
    (r"(?<![\w\u0900-\u097F])(?:डेटाबेस|डाटाबेस)(?![\w\u0900-\u097F])", "database"),
    (r"(?<![\w\u0900-\u097F])(?:सर्व्हर|सर्वर)(?![\w\u0900-\u097F])", "server"),
    (r"(?<![\w\u0900-\u097F])(?:इंटरव्यू|इंटरव्ह्यू)(?![\w\u0900-\u097F])", "interview"),
    (r"(?<![\w\u0900-\u097F])डाउनटाइम(?![\w\u0900-\u097F])", "downtime"),
    (r"(?<![\w\u0900-\u097F])(?:लेटेंसी|लॅटन्सी)(?![\w\u0900-\u097F])", "latency"),
    (r"(?<![\w\u0900-\u097F])(?:करोड़|कोटी)(?![\w\u0900-\u097F])", "crore"),
    (r"(?<![\w\u0900-\u097F])लाख(?![\w\u0900-\u097F])", "lakh"),
    (r"(?<![\w\u0900-\u097F])(?:हज़ार|हजार)(?![\w\u0900-\u097F])", "thousand"),
    (r"(?<![\w\u0900-\u097F])(?:शंभर|सौ)(?![\w\u0900-\u097F])", "hundred"),
    (r"(?<![\w\u0900-\u097F])(?:नब्बे|नव्वद)(?![\w\u0900-\u097F])", "ninety"),
    (r"(?<![\w\u0900-\u097F])(?:पचास|पन्नास)(?![\w\u0900-\u097F])", "fifty"),
    (r"(?<![\w\u0900-\u097F])(?:बीस|वीस)(?![\w\u0900-\u097F])", "twenty"),
    (r"(?<![\w\u0900-\u097F])(?:दस|दहा)(?![\w\u0900-\u097F])", "ten"),
    (r"(?<![\w\u0900-\u097F])(?:नौ|नऊ)(?![\w\u0900-\u097F])", "nine"),
    (r"(?<![\w\u0900-\u097F])आठ(?![\w\u0900-\u097F])", "eight"),
    (r"(?<![\w\u0900-\u097F])सात(?![\w\u0900-\u097F])", "seven"),
    (r"(?<![\w\u0900-\u097F])(?:छह|सहा)(?![\w\u0900-\u097F])", "six"),
    (r"(?<![\w\u0900-\u097F])(?:पांच|पाँच|पाच)(?![\w\u0900-\u097F])", "five"),
    (r"(?<![\w\u0900-\u097F])चार(?![\w\u0900-\u097F])", "four"),
    (r"(?<![\w\u0900-\u097F])तीन(?![\w\u0900-\u097F])", "three"),
    (r"(?<![\w\u0900-\u097F])(?:दो|दोन)(?![\w\u0900-\u097F])", "two"),
    (r"(?<![\w\u0900-\u097F])एक\s+(?=(?:second|seconds|minute|minutes|hour|hours|percent|million|billion|thousand|hundred|day|days|week|weeks|month|months|year|years|server|query|request|thread|lock|node|database|cache|api|step|user|record|ms|kb|mb|gb|tb|x)\b)", "one "),
]


def _int_to_english(n: int) -> str:
    """Converts a non-negative integer into natural spoken English words."""
    if n < 0:
        return "minus " + _int_to_english(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        rem = n % 100
        return _ONES[n // 100] + " hundred" + ("" if rem == 0 else " " + _int_to_english(rem))
    for scale, name in ((10**12, "trillion"), (10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= scale:
            rem = n % scale
            return _int_to_english(n // scale) + f" {name}" + ("" if rem == 0 else " " + _int_to_english(rem))
    return str(n)


def _year_to_english(year: int) -> str:
    """Converts a 4-digit calendar year (1900-2099) into natural spoken English."""
    if 2000 <= year <= 2009:
        return "two thousand" if year == 2000 else f"two thousand {_ONES[year - 2000]}"
    if 2010 <= year <= 2099:
        return f"twenty {_int_to_english(year - 2000)}"
    if 1900 <= year <= 1999:
        hi, lo = year // 100, year % 100
        if lo == 0:
            return f"{_int_to_english(hi)} hundred"
        return f"{_int_to_english(hi)} {('oh ' + _ONES[lo]) if lo < 10 else _int_to_english(lo)}"
    return _int_to_english(year)


def _ordinal_to_english(n: int) -> str:
    """Converts day/rank integer (e.g. 1 -> first, 25 -> twenty fifth) to English ordinal words."""
    if n in _ORDINAL_SPECIAL:
        return _ORDINAL_SPECIAL[n]
    if 20 < n < 100:
        tens, ones = (n // 10) * 10, n % 10
        if ones in _ORDINAL_SPECIAL:
            return f"{_TENS[tens // 10]} {_ORDINAL_SPECIAL[ones]}"
    base = _int_to_english(n)
    return base + "th"


def _num_str_to_english(num_str: str) -> str:
    """Converts an integer or decimal numeric string (commas allowed) into spoken English."""
    clean = num_str.replace(",", "").strip()
    if not clean:
        return num_str
    if "." in clean:
        parts = clean.split(".", 1)
        int_part = _int_to_english(int(parts[0])) if parts[0].isdigit() else parts[0]
        frac_part = " ".join(_ONES[int(d)] for d in parts[1] if d.isdigit())
        return f"{int_part} point {frac_part}".strip() if frac_part else int_part
    val = int(clean)
    if 1900 <= val <= 2099 and "," not in num_str and len(clean) == 4:
        return _year_to_english(val)
    return _int_to_english(val)


def _normalize_text_for_english_tts(text: str) -> str:
    """
    Ensures ALL voices (Hindi, Marathi, Hinglish, English, ElevenLabs, Edge-TTS) pronounce
    numbers, dates, times, percentages, units, and technical words in proper human English.
    """
    s = text.translate(_DEVANAGARI_DIGITS)

    # Normalize Devanagari months, units, number words, and common transliterated tech words
    for pat, repl in _DEVANAGARI_WORD_MAP:
        s = re.sub(pat, repl, s)

    # Expand abbreviated English months ONLY when paired with a numeric day/year (avoids Hinglish 'mar'/'jan')
    s = re.sub(
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+)(Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\b",
        lambda m: f"{m.group(1)}{_MONTH_ABBR.get(m.group(2).lower(), m.group(2))}",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"\b(Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?(?=\s+\d{1,4}\b)",
        lambda m: _MONTH_ABBR.get(m.group(1).lower(), m.group(1)),
        s,
        flags=re.IGNORECASE,
    )

    # Expand K8s and common shorthand
    s = re.sub(r"\bK8s\b", "Kubernetes", s, flags=re.IGNORECASE)

    # ISO dates YYYY-MM-DD -> spoken English date
    def _iso_date_repl(m: re.Match) -> str:
        y, mo, dy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= dy <= 31:
            return f"{_ordinal_to_english(dy)} {_MONTH_NAMES[mo]} {_year_to_english(y)}"
        return m.group(0)

    s = re.sub(r"\b((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})\b", _iso_date_repl, s)

    # Numeric dates DD/MM/YYYY or DD-MM-YYYY
    def _dmy_date_repl(m: re.Match) -> str:
        dy, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= dy <= 31:
            return f"{_ordinal_to_english(dy)} {_MONTH_NAMES[mo]} {_year_to_english(y)}"
        return m.group(0)

    s = re.sub(r"\b(\d{1,2})[/-](\d{1,2})[/-]((?:19|20)\d{2})\b", _dmy_date_repl, s)

    # Ordinal numbers (1st, 2nd, 3rd, 25th)
    s = re.sub(
        r"\b(\d{1,3})(?:st|nd|rd|th)\b",
        lambda m: _ordinal_to_english(int(m.group(1))),
        s,
        flags=re.IGNORECASE,
    )

    # Timestamps HH:MM(:SS)
    def _time_repl(m: re.Match) -> str:
        h, mn = int(m.group(1)), int(m.group(2))
        if h == 0 and mn == 0:
            return "zero zero"
        h_w = _int_to_english(h)
        m_w = "o'clock" if mn == 0 else (("oh " + _ONES[mn]) if mn < 10 else _int_to_english(mn))
        return f"{h_w} {m_w}"

    s = re.sub(r"\b(\d{1,2}):(\d{2})\b", _time_repl, s)

    # Version tokens like v2.5 or v3.11 -> "version two point five"
    s = re.sub(
        r"\bv(\d+(?:\.\d+)+)\b",
        lambda m: "version " + " point ".join(_int_to_english(int(p)) if p.isdigit() else p for p in m.group(1).split(".")),
        s,
        flags=re.IGNORECASE,
    )

    # Tech units & scales attached to numbers (preserve hex literals like 0x00A1 separately)
    unit_map = {
        "ms": "milliseconds",
        "us": "microseconds",
        "µs": "microseconds",
        "ns": "nanoseconds",
        "sec": "seconds",
        "secs": "seconds",
        "s": "seconds",
        "min": "minutes",
        "mins": "minutes",
        "hr": "hours",
        "hrs": "hours",
        "gbps": "G B P S",
        "mbps": "M B P S",
        "kbps": "K B P S",
        "fps": "F P S",
        "rps": "requests per second",
        "qps": "queries per second",
        "gb": "G B",
        "mb": "M B",
        "kb": "K B",
        "tb": "T B",
        "x": "X",
        "k": "K",
        "m": "million",
        "b": "billion",
    }

    def _unit_repl(m: re.Match) -> str:
        num, unit = m.group(1), m.group(2).lower()
        return f"{_num_str_to_english(num)} {unit_map.get(unit, unit)}"

    s = re.sub(
        r"(?<![0-9a-fA-Fx])\b(\d+(?:,\d{3})*(?:\.\d+)?)\s*(ms|us|µs|ns|secs?|min|mins|hrs?|gbps|mbps|kbps|fps|rps|qps|gb|mb|kb|tb)\b",
        _unit_repl,
        s,
        flags=re.IGNORECASE,
    )
    # Single-letter scale suffixes only when directly attached (e.g. 10x, 10k, 5M, 2B — avoids "0 B" -> billion)
    s = re.sub(
        r"(?<![0-9a-fA-Fx])\b(\d+(?:,\d{3})*(?:\.\d+)?)(x|k|m|b)\b",
        _unit_repl,
        s,
        flags=re.IGNORECASE,
    )

    # Currency & Percentages
    s = re.sub(
        r"\$(\d+(?:,\d{3})*(?:\.\d+)?)",
        lambda m: f"{_num_str_to_english(m.group(1))} dollars",
        s,
    )
    s = re.sub(
        r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*%",
        lambda m: f"{_num_str_to_english(m.group(1))} percent",
        s,
    )

    # Standalone numbers (excluding hex like 0x00A1 or word-attached IDs like S3, EC2, IPv4, SHA256)
    s = re.sub(
        r"(?<![A-Za-z0-9_x.])(\d+(?:,\d{3})*(?:\.\d+)?)(?![A-Za-z0-9_])",
        lambda m: _num_str_to_english(m.group(1)),
        s,
    )
    return s


def _clean_tts_text(text: str, preserve_pauses: bool = False) -> str:
    """Cleans script text for natural speech synthesis and normalizes numbers/dates/tech terms to spoken English."""
    if preserve_pauses:
        cleaned = re.sub(r'\[pause\]', ' ... ', text, flags=re.IGNORECASE)
    else:
        cleaned = re.sub(r'\[pause\]', ', ', text, flags=re.IGNORECASE)
        cleaned = cleaned.replace("...", ", ")
    cleaned = cleaned.replace("`", "").replace("*", "").replace("#", "")
    # Replace technical underscores with spaces (e.g. DENSE_RANK -> DENSE RANK)
    cleaned = re.sub(r'(?<=\w)_(?=\w)', ' ', cleaned)
    # Force all numbers, dates, units, and tech terms into natural spoken English across ALL voices
    cleaned = _normalize_text_for_english_tts(cleaned)
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _split_pause_beats(text: str, max_beats: int = 3) -> List[str]:
    """Splits narration along explicit pause cues ('...' / '[pause]'), Indian conversational cues, or sentences."""
    normalized = re.sub(r'\[pause\]', ' ... ', text, flags=re.IGNORECASE)
    cue_split_re = r'\b(Relax|Wait|Look|Listen|Stop|Twist|Catch|Boom|Done|Think|Why|How|Samjha|Samjhe|Ruko|Suno|Dekho|Socho|Bas|Actually|Result|रुको|सोचो|सुनो|देखो|समझे)\s*([.?!।]?)\s+'
    normalized = re.sub(cue_split_re, r'\1\2 ... ', normalized, flags=re.IGNORECASE)
    raw_parts = [p.strip() for p in re.split(r'\s*\.{3,}\s*', normalized) if p and any(ch.isalnum() for ch in p)]
    if len(raw_parts) <= 1 and len(normalized) >= 56:
        sent_parts = [p.strip() for p in re.split(r'(?<=[.!?।])\s+|\s+[—-]{1,2}\s+', normalized) if p and any(ch.isalnum() for ch in p)]
        if len(sent_parts) >= 2:
            raw_parts = sent_parts
    if len(raw_parts) <= 1:
        return [re.sub(r'\s+', ' ', normalized).strip()]
    if len(raw_parts) > max_beats:
        merged = raw_parts[:max_beats - 1]
        merged.append(" ".join(raw_parts[max_beats - 1:]))
        return merged
    return raw_parts

def _get_cache_path(text: str, voice: str, model_id: str, tone: str = DEFAULT_CONCRETE_TONE) -> Path:
    """Generates a unique deterministic cache file path based on text, voice, model, and tone."""
    key = f"{voice}|{model_id}|{tone}|{text}".encode("utf-8")
    hash_str = hashlib.sha256(key).hexdigest()[:24]
    return VOICE_CACHE_DIR / f"tts_{hash_str}.mp3"

def _synthesize_elevenlabs_sync(
    text: str,
    output_path: Path,
    voice_id: str,
    model_id: str,
    tone: str = DEFAULT_CONCRETE_TONE,
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

    t_prof = get_tone_profile(tone)
    cleaned_text = _clean_tts_text(text, preserve_pauses=True)
    if not cleaned_text:
        return False

    # 1. Check Cache First (Saves 100% of credits on re-runs)
    cache_path = _get_cache_path(cleaned_text, f"{voice_id}:{lang_code}", model_id, t_prof["key"])
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        try:
            shutil.copyfile(cache_path, output_path)
            print(f"[Voice] ⚡ Reused cached ElevenLabs audio (Saved {len(cleaned_text)} credits)")
            return True
        except Exception:
            pass

    # 2. Tone-tailored voice settings
    voice_settings = dict(t_prof["elevenlabs"])

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
            tempo = str(t_prof.get("atempo") or "1.00")
            if float(tempo) > 1.01:
                fast_tmp = output_path.with_suffix(".fast.mp3")
                try:
                    t_res = subprocess.run(
                        [str(FFMPEG_EXE), "-y", "-i", str(output_path.resolve()), "-filter:a", f"atempo={tempo}", "-c:a", "libmp3lame", "-b:a", "192k", str(fast_tmp.resolve())],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
                    )
                    if t_res.returncode == 0 and fast_tmp.exists() and fast_tmp.stat().st_size > 1000:
                        shutil.move(str(fast_tmp), str(output_path))
                except Exception:
                    if fast_tmp.exists():
                        fast_tmp.unlink()
            # Save final processed audio to cache
            try:
                shutil.copyfile(output_path, cache_path)
            except Exception:
                pass
            print(f"[Voice] ✅ ElevenLabs synthesized scene ({model_id}, tone: {t_prof['key']}, {len(cleaned_text)} chars)")
            return True
        else:
            print(f"[Voice] ElevenLabs returned {res.status_code}: {res.text[:120]}")
            return False
    except Exception as e:
        print(f"[Voice] ElevenLabs request failed ({e})")
        return False

def _trim_tts_edge_silence(audio_path: Path, keep_start_sec: float = 0.03, keep_tail_sec: float = 0.14) -> None:
    """Trims Edge-TTS bloated leading/trailing digital silence while keeping a natural breath."""
    if not audio_path.exists() or audio_path.stat().st_size < 400:
        return
    tmp_trim = audio_path.with_suffix(".trim.mp3")
    try:
        filt = (
            f"aformat=sample_rates=44100:channel_layouts=stereo,"
            f"silenceremove=start_periods=1:start_silence={keep_start_sec:.2f}:start_threshold=-40dB,"
            f"areverse,"
            f"silenceremove=start_periods=1:start_silence={keep_tail_sec:.2f}:start_threshold=-40dB,"
            f"areverse"
        )
        res = subprocess.run(
            [str(FFMPEG_EXE), "-y", "-i", str(audio_path.resolve()), "-filter:a", filt, "-c:a", "libmp3lame", "-b:a", "192k", str(tmp_trim.resolve())],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
        )
        if res.returncode == 0 and tmp_trim.exists() and tmp_trim.stat().st_size > 400:
            shutil.move(str(tmp_trim), str(audio_path))
    except Exception:
        pass
    finally:
        if tmp_trim.exists():
            try:
                tmp_trim.unlink()
            except Exception:
                pass


async def _synthesize_edge_tts_scene(text: str, output_path: Path, voice: str, tone: str = DEFAULT_CONCRETE_TONE) -> bool:
    """
    Synthesizes speech using Microsoft Edge-TTS:
    - Honors natural pause cues (`...` / `[pause]` / Indian cadence beats) when `use_pause_cadence`
      or explicit pauses are present, stitching beats with clean `pause_sec` gaps and an optional
      `tail_hold_sec` comprehension breath so visuals never flash past too fast.
    """
    t_prof = get_tone_profile(tone)
    rate = str(t_prof["edge_base"]["rate"])
    pitch = str(t_prof["edge_base"]["pitch"])
    use_pauses = bool(t_prof.get("use_pause_cadence")) or ("..." in str(text)) or ("[pause]" in str(text).lower())
    gap_sec = max(0.16, min(0.42, float(t_prof.get("pause_sec") or 0.26)))
    tail_hold = max(0.0, min(0.65, float(t_prof.get("tail_hold_sec") or 0.0)))

    beats = _split_pause_beats(str(text or ""), max_beats=3) if use_pauses else [str(text or "")]
    clean_beats = [_clean_tts_text(b, preserve_pauses=False) for b in beats]
    clean_beats = [b for b in clean_beats if b]
    if not clean_beats:
        return False

    if len(clean_beats) == 1:
        plain_text = clean_beats[0]
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(plain_text, voice, rate=rate, pitch=pitch)
                await communicate.save(str(output_path))
                if output_path.exists() and output_path.stat().st_size > 1000:
                    _trim_tts_edge_silence(output_path, keep_start_sec=0.03, keep_tail_sec=max(0.14, 0.14 + tail_hold))
                    return True
            except Exception as e:
                print(f"[Voice] Edge-TTS attempt {attempt + 1} warning: {e}")
                await asyncio.sleep(0.5)
        return False

    # Multi-beat natural Hindi/Creator cadence synthesis with crisp breath pauses + visual tail hold
    seg_files: List[Path] = []
    try:
        async def _synth_beat(b_idx: int, b_txt: str):
            sp = OUTPUT_DIR / f"edge_beat_{b_idx}_{uuid.uuid4().hex[:6]}.mp3"
            b_rate, b_pitch = get_clause_prosody(tone, b_idx, len(clean_beats), b_txt)
            for attempt in range(3):
                try:
                    comm = edge_tts.Communicate(b_txt, voice, rate=b_rate, pitch=b_pitch)
                    await comm.save(str(sp))
                    if sp.exists() and sp.stat().st_size > 600:
                        _trim_tts_edge_silence(sp, keep_start_sec=0.03, keep_tail_sec=0.08)
                        return True, sp
                except Exception as e:
                    print(f"[Voice] Edge-TTS beat {b_idx + 1} attempt {attempt + 1} warning: {e}")
                    await asyncio.sleep(0.35)
            return False, sp

        results = await asyncio.gather(*(_synth_beat(bi, bt) for bi, bt in enumerate(clean_beats)))
        for ok_b, sp in results:
            if not ok_b:
                return False
            seg_files.append(sp)

        cmd = [str(FFMPEG_EXE), "-y"]
        for sp in seg_files:
            cmd.extend(["-i", str(sp.resolve())])
        max_sil = max(gap_sec, tail_hold, 0.25)
        cmd.extend(["-f", "lavfi", "-t", f"{max_sil:.2f}", "-i", "anullsrc=r=44100:cl=stereo"])
        sil_idx = len(seg_files)
        parts, seq = [], []
        for idx in range(len(seg_files)):
            parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo[b{idx}]")
            seq.append(f"[b{idx}]")
            if idx < len(seg_files) - 1:
                parts.append(f"[{sil_idx}:a]atrim=0:{gap_sec:.2f}[g{idx}]")
                seq.append(f"[g{idx}]")
        if tail_hold >= 0.12:
            parts.append(f"[{sil_idx}:a]atrim=0:{tail_hold:.2f}[tail]")
            seq.append("[tail]")
        filt = ";".join(parts) + ";" + "".join(seq) + f"concat=n={len(seq)}:v=0:a=1[outa]"
        cmd.extend(["-filter_complex", filt, "-map", "[outa]", "-c:a", "libmp3lame", "-b:a", "192k", str(output_path.resolve())])
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            return True
    except Exception as e:
        print(f"[Voice] Multi-beat Edge-TTS stitch notice: {e}")
    finally:
        for sp in seg_files:
            try:
                if sp.exists():
                    sp.unlink()
            except Exception:
                pass

    # Clean single-pass fallback if multi-beat failed
    fallback_txt = " ".join(clean_beats)
    try:
        comm = edge_tts.Communicate(fallback_txt, voice, rate=rate, pitch=pitch)
        await comm.save(str(output_path))
        if output_path.exists() and output_path.stat().st_size > 1000:
            _trim_tts_edge_silence(output_path, keep_start_sec=0.03, keep_tail_sec=0.14)
            return True
    except Exception:
        pass
    return False

def parse_dual_voice_pair(voice: str) -> Tuple[str, str]:
    """Extracts `(female_voice_id, male_voice_id)` from `dual:<fem>+<male>` strings cleanly."""
    default_pair = ("hi-IN-SwaraNeural", "hi-IN-MadhurNeural")
    raw = str(voice or "").strip()
    if not raw.startswith("dual:"):
        return default_pair
    payload = raw.split("dual:", 1)[1].strip()
    if "+" not in payload:
        return default_pair
    fem_v, male_v = payload.split("+", 1)
    fem_v = fem_v.strip() or default_pair[0]
    male_v = male_v.strip() or default_pair[1]
    return fem_v, male_v


def _normalize_edge_speaker_id(raw_voice: str, fallback: str) -> str:
    clean = str(raw_voice or "").replace("edge:", "").replace("dual:", "").split("|", 1)[0].strip()
    if not clean or clean.startswith("elevenlabs:"):
        return fallback
    return clean


async def _synthesize_dual_dialogue_scene(
    dialogue: List[Dict[str, Any]],
    output_path: Path,
    fem_voice: str = "hi-IN-SwaraNeural",
    male_voice: str = "hi-IN-MadhurNeural",
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Synthesizes alternating Female (Curious Questioner) + Male (Empathetic Mentor Solver)
    dialogue turns cleanly via Edge-TTS, stitches them with natural 0.26s conversational gaps,
    and returns `(success, dialogue_spans)` with exact `[start, end, speaker, text]` turn offsets.
    """
    clean_fem = _normalize_edge_speaker_id(fem_voice, "hi-IN-SwaraNeural")
    clean_male = _normalize_edge_speaker_id(male_voice, "hi-IN-MadhurNeural")

    turns: List[Tuple[str, str]] = []
    for item in dialogue:
        if not isinstance(item, dict):
            continue
        spk_raw = str(item.get("speaker") or "male").strip().lower()
        spk = "female" if spk_raw in ("female", "f", "she", "questioner", "curious", "girl", "student") else "male"
        raw_t = re.sub(
            r"^\s*(?:female|male|she|he|questioner|solver|mentor|dost|host)\s*:\s*",
            "",
            str(item.get("text") or "").strip(),
            flags=re.IGNORECASE,
        )
        txt = _clean_tts_text(raw_t, preserve_pauses=False)
        if txt:
            turns.append((spk, txt))

    if not turns:
        return False, []

    turn_files: List[Path] = []
    turn_metas: List[Tuple[str, str, float]] = []
    gap_sec = 0.14

    try:
        async def _run_turn(t_idx: int, spk: str, txt: str):
            tp = OUTPUT_DIR / f"dual_turn_{t_idx}_{uuid.uuid4().hex[:6]}.mp3"
            v_id = clean_fem if spk == "female" else clean_male
            t_rate = "+4%" if spk == "female" else "+3%"
            t_pitch = "+2Hz" if spk == "female" else "-1Hz"
            ok_turn = False
            for attempt in range(3):
                try:
                    comm = edge_tts.Communicate(txt, v_id, rate=t_rate, pitch=t_pitch)
                    await comm.save(str(tp))
                    if tp.exists() and tp.stat().st_size > 800:
                        _trim_tts_edge_silence(tp, keep_start_sec=0.03, keep_tail_sec=0.10)
                        ok_turn = True
                        break
                except Exception as e:
                    print(f"[Voice Dual] Turn {t_idx + 1} ({spk}) attempt {attempt + 1} warning: {e}")
                    await asyncio.sleep(0.35)
            return ok_turn, tp, spk, txt

        results = await asyncio.gather(*(_run_turn(t_idx, spk, txt) for t_idx, (spk, txt) in enumerate(turns)))
        for ok_turn, tp, spk, txt in results:
            if not ok_turn:
                return False, []
            turn_files.append(tp)
            dur = max(0.35, float(get_audio_duration(tp) or 0.8))
            turn_metas.append((spk, txt, dur))

        if len(turn_files) == 1:
            import shutil
            shutil.copy2(turn_files[0], output_path)
            spk0, txt0, dur0 = turn_metas[0]
            return True, [{"speaker": spk0, "text": txt0, "start": 0.0, "end": round(dur0, 3)}]

        cmd = [str(FFMPEG_EXE), "-y"]
        for tp in turn_files:
            cmd.extend(["-i", str(tp.resolve())])
        cmd.extend(["-f", "lavfi", "-t", f"{gap_sec:.2f}", "-i", "anullsrc=r=44100:cl=stereo"])
        sil_idx = len(turn_files)
        parts, seq = [], []
        for idx in range(len(turn_files)):
            parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo[t{idx}]")
            seq.append(f"[t{idx}]")
            if idx < len(turn_files) - 1:
                parts.append(f"[{sil_idx}:a]atrim=0:{gap_sec:.2f}[g{idx}]")
                seq.append(f"[g{idx}]")
        filt = ";".join(parts) + ";" + "".join(seq) + f"concat=n={len(seq)}:v=0:a=1[outa]"
        cmd.extend(["-filter_complex", filt, "-map", "[outa]", "-c:a", "libmp3lame", "-b:a", "192k", str(output_path.resolve())])
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        if res.returncode != 0 or not output_path.exists() or output_path.stat().st_size < 1000:
            return False, []

        spans: List[Dict[str, Any]] = []
        cursor_t = 0.0
        for idx, (spk, txt, dur) in enumerate(turn_metas):
            s_t = cursor_t
            e_t = cursor_t + dur
            spans.append({"speaker": spk, "text": txt, "start": round(s_t, 3), "end": round(e_t, 3)})
            cursor_t = e_t + (gap_sec if idx < len(turn_metas) - 1 else 0.0)
        return True, spans
    except Exception as e:
        print(f"[Voice Dual] Dialogue stitch warning: {e}")
        return False, []
    finally:
        for tp in turn_files:
            try:
                if tp.exists():
                    tp.unlink()
            except Exception:
                pass


def _synthesize_single_scene(
    text: str,
    output_path: Path,
    voice: str,
    elevenlabs_model: str = DEFAULT_ELEVENLABS_MODEL,
    tone: str = DEFAULT_CONCRETE_TONE,
    allow_elevenlabs: bool = True,
    dialogue: Optional[List[Dict[str, Any]]] = None,
    scene_idx: int = 0,
) -> List[Dict[str, Any]]:
    """
    Synthesizes speech for a single scene (single voice OR dual-speaker Female/Male dialogue):
    - Only calls ElevenLabs API if allow_elevenlabs=True AND voice starts with 'elevenlabs:'.
    - Whenever `voice` starts with `dual:` or `is_dual_tone(tone)` or `dialogue` has turns,
      synthesizes alternating Female + Male Edge-TTS clips (splitting plain text cleanly
      into alternating turns whenever explicit `dialogue` turns are absent).
    Returns `dialogue_spans` (empty list for single-speaker scenes).
    """
    has_dialogue = isinstance(dialogue, list) and len(dialogue) >= 1
    wants_dual = voice.startswith("dual:") or (has_dialogue and (is_dual_tone(tone) or len(dialogue) >= 2))
    if is_dual_tone(tone) and not wants_dual:
        wants_dual = True

    if wants_dual:
        eff_dialogue: List[Dict[str, Any]] = []
        if has_dialogue:
            eff_dialogue = [
                d for d in dialogue
                if isinstance(d, dict) and str(d.get("text") or "").strip()
            ]
        if not eff_dialogue and str(text or "").strip():
            eff_dialogue = split_text_to_dual_dialogue(text, scene_idx=scene_idx)
        elif len(eff_dialogue) == 1 and len(str(text or "").strip()) > len(str(eff_dialogue[0].get("text") or "")) + 15:
            eff_dialogue = split_text_to_dual_dialogue(text, scene_idx=scene_idx)

        if eff_dialogue:
            fem_v, male_v = parse_dual_voice_pair(voice)
            ok_dual, spans = asyncio.run(
                _synthesize_dual_dialogue_scene(eff_dialogue, output_path, fem_voice=fem_v, male_voice=male_v)
            )
            if ok_dual and spans:
                return spans
            print("[Voice Dual] Falling back to alternating single Edge-TTS voice for scene...")

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
            return []
        print("[Voice] Falling back to high-fidelity Edge-TTS for this scene...")
        fallback_voice = "mr-IN-ManoharNeural" if lang_code == "mr" else ("hi-IN-MadhurNeural" if lang_code == "hi" else "en-US-ChristopherNeural")
        asyncio.run(_synthesize_edge_tts_scene(text, output_path, fallback_voice, tone=tone))
        return []

    # Standard Edge-TTS path (never consumes ElevenLabs credits)
    if voice.startswith("dual:"):
        fem_v, male_v = parse_dual_voice_pair(voice)
        picked_v = fem_v if (scene_idx % 2 == 0) else male_v
        clean_voice = _normalize_edge_speaker_id(picked_v, "hi-IN-MadhurNeural")
    else:
        clean_voice = voice.replace("edge:", "").split("|", 1)[0].strip()
    if clean_voice.startswith("elevenlabs:"):
        clean_voice = "en-US-ChristopherNeural"
    asyncio.run(_synthesize_edge_tts_scene(text, output_path, clean_voice, tone=tone))
    return []

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
    tone: str = DEFAULT_TONE_KEY,
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

    # 1. Synthesize all scene voiceovers concurrently for 3x-4x speedup (sequential only when ElevenLabs quota requires)
    def _synth_one(idx_item):
        i, sc, text, p = idx_item
        sc_tone = resolve_effective_tone(tone, scene_tone=sc.get("scene_tone"), role=sc.get("role"), idx=i)
        spans = _synthesize_single_scene(
            text, p, voice=voice, elevenlabs_model=elevenlabs_model,
            tone=sc_tone, allow_elevenlabs=allow_elevenlabs, dialogue=sc.get("dialogue"),
            scene_idx=i,
        )
        _ensure_valid_audio(p)
        return i, (spans or [])

    use_el_serial = allow_elevenlabs and voice.startswith("elevenlabs:")
    items = list(enumerate(zip(scenes, scene_texts, scene_audio_paths)))
    packed = [(i, sc, txt, p) for i, (sc, txt, p) in items]
    scene_dialogue_spans: List[List[Dict[str, Any]]] = [[] for _ in scenes]
    if not use_el_serial and len(packed) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(4, len(packed))) as ex:
            for i, spans in ex.map(_synth_one, packed):
                scene_dialogue_spans[i] = spans
    else:
        for pk in packed:
            i, spans = _synth_one(pk)
            scene_dialogue_spans[i] = spans

    # 2. Measure exact duration of each scene's audio (never inflate short audio so subsequent scenes stay 100% synced)
    scene_durations = []
    for p in scene_audio_paths:
        d_val = get_audio_duration(p)
        scene_durations.append(d_val if d_val > 0.05 else 1.5)

    # 3. Concatenate scene audios cleanly (uniform 44.1kHz stereo format, zero single-pass loudnorm pumping)
    final_audio_path = OUTPUT_DIR / "reel_voiceover.mp3"
    concat_cmd = [str(FFMPEG_EXE), "-y"]
    norm_parts = []
    seq_labels = []
    for i, p in enumerate(scene_audio_paths):
        concat_cmd.extend(["-i", str(p.resolve())])
        norm_parts.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[s{i}]")
        seq_labels.append(f"[s{i}]")
    filter_expr = (
        ";".join(norm_parts)
        + ";"
        + "".join(seq_labels)
        + f"concat=n={len(scene_audio_paths)}:v=0:a=1[raw];[raw]highpass=f=70,alimiter=limit=0.92[a]"
    )
    concat_cmd.extend(["-filter_complex", filter_expr, "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(final_audio_path.resolve())])

    res_concat = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res_concat.returncode != 0 or not final_audio_path.exists() or final_audio_path.stat().st_size < 1000:
        fallback_cmd = [str(FFMPEG_EXE), "-y"]
        for p in scene_audio_paths:
            fallback_cmd.extend(["-i", str(p.resolve())])
        fb_expr = "".join(f"[{i}:a]" for i in range(len(scene_audio_paths))) + f"concat=n={len(scene_audio_paths)}:v=0:a=1[a]"
        fallback_cmd.extend(["-filter_complex", fb_expr, "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(final_audio_path.resolve())])
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
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
        if i < len(scene_dialogue_spans) and scene_dialogue_spans[i]:
            s_copy["dialogue_spans"] = scene_dialogue_spans[i]
        scenes_with_timestamps.append(s_copy)
        cur_time = s_end

    # 5. Extract Word Timestamps via Groq Whisper for karaoke subtitles
    # Pass Roman Hinglish/English script excerpt as prompt hint so captions stay crisp Roman Hinglish & tech spellings
    hint_texts = [
        (sc.get("narration_hinglish") or sc.get("narration") or "").strip()
        for sc in scenes_with_timestamps
    ]
    combined_prompt = re.sub(r'\[pause\]', ' ', " ".join(hint_texts), flags=re.IGNORECASE)[:750]
    word_timestamps = []
    try:
        word_timestamps = _extract_word_timestamps(final_audio_path, prompt_hint=combined_prompt)
    except Exception as e:
        print(f"[Voice] Groq Whisper extraction notice ({e}), generating robust fallback timestamps...")
        word_timestamps = []

    expected_word_cnt = sum(len(re.sub(r'\[pause\]', ' ', (sc.get("narration_hinglish") or sc.get("narration") or ""), flags=re.IGNORECASE).split()) for sc in scenes_with_timestamps)
    if len(word_timestamps) < max(3, int(expected_word_cnt * 0.72)):
        print(f"[Voice] Whisper alignment incomplete ({len(word_timestamps)}/{expected_word_cnt}), using scene-exact word alignment...")
        word_timestamps = _generate_fallback_word_timestamps(scenes_with_timestamps)
    else:
        # Per-scene completeness guard: if Whisper dropped >30% words in any specific scene, heal that scene cleanly
        healed_words: List[Dict[str, Any]] = []
        for sc in scenes_with_timestamps:
            st_t = float(sc.get("start_time", 0.0))
            en_t = float(sc.get("end_time", 0.0))
            sc_script = re.sub(r'\[pause\]', ' ', (sc.get("narration_hinglish") or sc.get("narration") or ""), flags=re.IGNORECASE).strip()
            sc_exp = len([w for w in sc_script.split() if any(ch.isalnum() for ch in w)])
            sc_ws = [w for w in word_timestamps if st_t - 0.12 <= float(w.get("start", 0.0)) < en_t - 0.02]
            if sc_exp >= 4 and len(sc_ws) < int(sc_exp * 0.68):
                healed_words.extend(_generate_fallback_word_timestamps([sc]))
            else:
                healed_words.extend(sc_ws)
        if len(healed_words) >= len(word_timestamps):
            word_timestamps = healed_words

    from core.subtitles import normalize_hinglish_subtitle_words
    word_timestamps = normalize_hinglish_subtitle_words(word_timestamps, aligned_scenes=scenes_with_timestamps)

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
    from core.subtitles import devanagari_word_to_hinglish, _extract_scene_roman_vocab
    all_words = []
    for sc in scenes:
        raw_script = sc.get("narration_hinglish") or sc.get("narration") or ""
        narration = re.sub(r'\[pause\]', ' ', raw_script, flags=re.IGNORECASE).strip()
        vocab = _extract_scene_roman_vocab(sc)
        words = [devanagari_word_to_hinglish(w, scene_vocab=vocab) for w in narration.split()]
        words = [w for w in words if w]
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
