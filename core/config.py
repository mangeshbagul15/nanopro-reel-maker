import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import imageio_ffmpeg

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
SFX_DIR = ASSETS_DIR / "sfx"
ICONS_DIR = ASSETS_DIR / "icons"
OUTPUT_DIR = BASE_DIR / "output"

for d in [ASSETS_DIR, FONTS_DIR, SFX_DIR, ICONS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def _get_env_or_secret(key: str, default: str = "") -> str:
    val = os.getenv(key, "")
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key])
        except Exception:
            pass
    return val or default

# API Keys
GEMINI_API_KEY = _get_env_or_secret("GEMINI_API_KEY")
GROQ_API_KEY = _get_env_or_secret("GROQ_API_KEY")
OPENROUTER_API_KEY = _get_env_or_secret("OPENROUTER_API_KEY")
MISTRAL_API_KEY = _get_env_or_secret("MISTRAL_API_KEY")
EDEN_AI_KEY = _get_env_or_secret("EDEN_AI_KEY")
ELEVENLABS_API_KEY = _get_env_or_secret("ELEVENLABS_API_KEY")

# Cloudflare R2
CF_ACCOUNT_ID = _get_env_or_secret("CLOUDFLARE_ACCOUNT_ID")
CF_R2_ACCESS_KEY = _get_env_or_secret("CLOUDFLARE_R2_ACCESS_KEY")
CF_R2_SECRET_KEY = _get_env_or_secret("CLOUDFLARE_R2_SECRET_KEY")
CF_R2_BUCKET = _get_env_or_secret("CLOUDFLARE_R2_BUCKET", "nanopro-reels")
CF_R2_PUBLIC_URL = _get_env_or_secret("CLOUDFLARE_R2_PUBLIC_URL", "https://pub-ba534bece9ff4d909b3a002a10a42a31.r2.dev")

# Video Specs
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
DEFAULT_WATERMARK = _get_env_or_secret("DEFAULT_WATERMARK", "@Code_With_Mangesh")

FORMAT_SPECS = {
    "9:16": {"width": 1080, "height": 1920, "label": "9:16 Vertical (Reels / Shorts / TikTok)"},
    "16:9": {"width": 1920, "height": 1080, "label": "16:9 Widescreen (YouTube / Landscape)"},
    "1:1": {"width": 1080, "height": 1080, "label": "1:1 Square (Instagram / LinkedIn)"}
}

# FFmpeg Executable (prefer system ffmpeg if installed, fallback to imageio_ffmpeg)
try:
    if shutil.which("ffmpeg"):
        FFMPEG_EXE = "ffmpeg"
    else:
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"
