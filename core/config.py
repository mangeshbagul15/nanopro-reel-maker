import os
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

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
EDEN_AI_KEY = os.getenv("EDEN_AI_KEY", "")

# Cloudflare R2
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CF_R2_ACCESS_KEY = os.getenv("CLOUDFLARE_R2_ACCESS_KEY", "")
CF_R2_SECRET_KEY = os.getenv("CLOUDFLARE_R2_SECRET_KEY", "")
CF_R2_BUCKET = os.getenv("CLOUDFLARE_R2_BUCKET", "nanopro-reels")
CF_R2_PUBLIC_URL = os.getenv("CLOUDFLARE_R2_PUBLIC_URL", "https://pub-ba534bece9ff4d909b3a002a10a42a31.r2.dev")

# Video Specs (9:16 Vertical Reel)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 15

# FFmpeg Executable
try:
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"
