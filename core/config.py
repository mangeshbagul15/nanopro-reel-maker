import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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

EXPORT_QUALITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "auto_hardware": {
        "label": "⚡ Auto (Local RTX GPU -> 4K 60 FPS | Cloud -> 1080p 60 FPS) [Recommended]",
    },
    "4k_60fps_ultra": {
        "label": "🚀 4K Ultra-HD (2160×3840) · 60 FPS · High Profile (Local RTX GPU)",
        "short": "4K UHD · 60 FPS",
        "fps": 60,
        "res_scale": 2.0,
        "frame_ext": "jpg",
        "nvenc_cq": "15",
        "nvenc_bv": "24M",
        "x264_crf": "15",
    },
    "4k_30fps_ultra": {
        "label": "👑 4K Ultra-HD (2160×3840) · 30 FPS · Lossless PNG + High Profile",
        "short": "4K PNG · 30 FPS",
        "fps": 30,
        "res_scale": 2.0,
        "frame_ext": "png",
        "nvenc_cq": "15",
        "nvenc_bv": "20M",
        "x264_crf": "15",
    },
    "1080p_60fps_png": {
        "label": "💎 1080p Full HD · 60 FPS · High Profile (Cloud-Safe Crisp)",
        "short": "1080p · 60 FPS",
        "fps": 60,
        "res_scale": 1.0,
        "frame_ext": "jpg",
        "nvenc_cq": "16",
        "nvenc_bv": "12M",
        "x264_crf": "16",
    },
    "1080p_60fps_lossless": {
        "label": "🖼️ 1080p Full HD · 60 FPS · Lossless PNG + High Profile",
        "short": "1080p PNG · 60 FPS",
        "fps": 60,
        "res_scale": 1.0,
        "frame_ext": "png",
        "nvenc_cq": "15",
        "nvenc_bv": "14M",
        "x264_crf": "15",
    },
    "1080p_30fps_fast": {
        "label": "⚡ 1080p Full HD · 30 FPS (Fast Draft)",
        "short": "1080p · 30 FPS",
        "fps": 30,
        "res_scale": 1.0,
        "frame_ext": "jpg",
        "nvenc_cq": "18",
        "nvenc_bv": "8M",
        "x264_crf": "18",
    },
}

EXPORT_QUALITY_OPTIONS: List[Tuple[str, str]] = [
    (k, str(v["label"])) for k, v in EXPORT_QUALITY_PROFILES.items()
]


def resolve_export_quality(choice_key: str = "auto_hardware", is_local: Optional[bool] = None) -> Dict[str, Any]:
    """Resolves Auto Hardware or manual quality preset into concrete FPS, res_scale, frame_ext & encoder specs."""
    local_flag = (sys.platform == "win32") if is_local is None else bool(is_local)
    req = str(choice_key or "auto_hardware").strip().lower()
    if req == "auto_hardware" or req not in EXPORT_QUALITY_PROFILES:
        eff_key = "4k_60fps_ultra" if local_flag else "1080p_60fps_png"
    else:
        eff_key = req
    prof = dict(EXPORT_QUALITY_PROFILES[eff_key])
    prof["key"] = eff_key
    prof["is_local"] = local_flag
    return prof


# FFmpeg Executable (prefer system ffmpeg if installed, fallback to imageio_ffmpeg)
try:
    if shutil.which("ffmpeg"):
        FFMPEG_EXE = "ffmpeg"
    else:
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"
