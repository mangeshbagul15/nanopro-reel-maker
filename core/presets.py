"""
1-Click Creator Brand Presets & Persistent Saved Profiles (`output/creator_presets.json`).
Bundles Tone, Voice, Format, Duration, Visual Engine, BGM, Caption Style, Safe-Zone,
Audience Level, Hook Style, CTA Strategy, and Motion/SFX flags cleanly.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from core.config import OUTPUT_DIR

CREATOR_PRESETS_PATH = OUTPUT_DIR / "creator_presets.json"


BUILTIN_CREATOR_PRESETS: Dict[str, Dict[str, Any]] = {
    "custom": {
        "label": "🎛️ Custom / Manual Configuration",
        "readonly": True,
        "settings": {},
    },
    "hinglish_viral_reel": {
        "label": "🇮🇳 Hinglish / Marathi Viral Reel (Auto 2026 • IG Reels)",
        "readonly": True,
        "settings": {
            "tone_key": "auto_2026_director",
            "voice_provider": "Microsoft Edge-TTS (Free & Fast)",
            "lang_filter": "All",
            "gender_filter": "🗣️ Dual Pair",
            "edge_voice_id": "dual:hi-IN-SwaraNeural+hi-IN-MadhurNeural",
            "aspect_ratio": "9:16",
            "duration_mode": "auto",
            "visual_mode": "auto_omni",
            "bgm_style": "lofi_cyber",
            "bgm_volume_pct": 16,
            "caption_style": "karaoke_pop",
            "platform_safe_zone": "instagram_reels",
            "audience_level": "working_dev",
            "hook_style": "ai_auto",
            "cta_style": "comment_keyword",
            "cta_keyword": "NOTES",
            "enable_cam_actions": True,
            "enable_micro_sfx": True,
        },
    },
    "war_story_thriller": {
        "label": "🚨 3AM Outage War Story Short (Dark Suspense • IG Reels)",
        "readonly": True,
        "settings": {
            "tone_key": "war_story_postmortem",
            "voice_provider": "Microsoft Edge-TTS (Free & Fast)",
            "lang_filter": "🇮🇳 Hindi",
            "gender_filter": "👩 Female",
            "edge_voice_id": "en-IN-NeerjaExpressiveNeural|hinglish",
            "aspect_ratio": "9:16",
            "duration_mode": "short",
            "visual_mode": "auto_omni",
            "bgm_style": "dark_cyber_suspense",
            "bgm_volume_pct": 18,
            "caption_style": "karaoke_pop",
            "platform_safe_zone": "instagram_reels",
            "audience_level": "working_dev",
            "hook_style": "outage_3am",
            "cta_style": "save_share",
            "cta_keyword": "",
            "enable_cam_actions": True,
            "enable_micro_sfx": True,
        },
    },
    "live_ide_debug_short": {
        "label": "🧪 Live IDE Bug Catch Short (Upbeat Pulse • YT Shorts)",
        "readonly": True,
        "settings": {
            "tone_key": "live_debug_pair",
            "voice_provider": "Microsoft Edge-TTS (Free & Fast)",
            "lang_filter": "🇺🇸 English",
            "gender_filter": "👨 Male",
            "edge_voice_id": "en-US-ChristopherNeural",
            "aspect_ratio": "9:16",
            "duration_mode": "short",
            "visual_mode": "auto_omni",
            "bgm_style": "upbeat_electro_pulse",
            "bgm_volume_pct": 14,
            "caption_style": "clean_minimal",
            "platform_safe_zone": "youtube_shorts",
            "audience_level": "working_dev",
            "hook_style": "contrarian_stop",
            "cta_style": "debate_poll",
            "cta_keyword": "",
            "enable_cam_actions": True,
            "enable_micro_sfx": True,
        },
    },
    "linkedin_staff_architect": {
        "label": "🏛️ LinkedIn Clean Staff Architect (No BGM • Clean Bar)",
        "readonly": True,
        "settings": {
            "tone_key": "bigtech_reverse_engineer",
            "voice_provider": "Microsoft Edge-TTS (Free & Fast)",
            "lang_filter": "🇺🇸 English",
            "gender_filter": "👨 Male",
            "edge_voice_id": "en-IN-PrabhatNeural",
            "aspect_ratio": "1:1",
            "duration_mode": "standard",
            "visual_mode": "auto_omni",
            "bgm_style": "none",
            "bgm_volume_pct": 0,
            "caption_style": "static_bottom",
            "platform_safe_zone": "linkedin_clean",
            "audience_level": "staff_architect",
            "hook_style": "shocking_stat",
            "cta_style": "clean_zero_cta",
            "cta_keyword": "",
            "enable_cam_actions": True,
            "enable_micro_sfx": False,
        },
    },
}


def load_creator_presets() -> Dict[str, Dict[str, Any]]:
    """Returns merged dictionary of built-in + user-saved custom Creator Presets."""
    merged: Dict[str, Dict[str, Any]] = {
        k: dict(v, settings=dict(v.get("settings") or {}))
        for k, v in BUILTIN_CREATOR_PRESETS.items()
    }
    if CREATOR_PRESETS_PATH.exists():
        try:
            raw = json.loads(CREATOR_PRESETS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for pk, pv in raw.items():
                    if isinstance(pv, dict) and pk not in BUILTIN_CREATOR_PRESETS:
                        merged[pk] = {
                            "label": str(pv.get("label") or f"⭐ {pk}"),
                            "readonly": False,
                            "settings": dict(pv.get("settings") or {}),
                        }
        except Exception:
            pass
    return merged


def save_custom_creator_preset(name: str, settings: Dict[str, Any]) -> str:
    """Saves a named custom Creator Preset to `output/creator_presets.json` and returns its key."""
    clean_name = re.sub(r"\s+", " ", str(name or "").strip())[:36] or "My Creator Preset"
    slug = "user_" + (re.sub(r"[^a-z0-9]+", "_", clean_name.lower()).strip("_") or "preset")
    saved: Dict[str, Any] = {}
    if CREATOR_PRESETS_PATH.exists():
        try:
            raw = json.loads(CREATOR_PRESETS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                saved = raw
        except Exception:
            saved = {}
    saved[slug] = {
        "label": f"⭐ {clean_name}",
        "readonly": False,
        "settings": dict(settings or {}),
    }
    CREATOR_PRESETS_PATH.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return slug
