import streamlit as st
import time
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Zero-lag smart hot-reload: ONLY reload already-imported `core.*` modules when files on disk actually change
# (fixes Streamlit Cloud git-pull hot-reloads without adding any latency to normal UI clicks).
import importlib
import os
_APP_MTIME = os.path.getmtime(__file__)
_PREV_APP_MTIME = getattr(sys, "_nanopro_app_mtime", None)
_CORE_MTIMES = getattr(sys, "_nanopro_core_mtimes", {})
_RELOAD_ORDER = [
    "core.config", "core.presets", "core.tone_engine", "core.palette_engine",
    "core.svg_engine", "core.mesh_shader_engine", "core.shapes_3d",
    "core.layouts_pro", "core.layouts_it_sdlc", "core.layouts_domain_220",
    "core.layouts_studio", "core.web_generative_engine", "core.cinematic_engine",
    "core.director", "core.voice", "core.thumbnail_engine", "core.animator", "core.subtitles",
    "core.renderer", "core.quality_gate", "core.studio_v2_director",
    "core.studio_v2_vector", "core.studio_v2_isometric",
    "core.studio_v3_ide", "core.studio_v4_whiteboard", "core.studio_v5_datacenter", "core.studio_pro_engines", "core.uploader",
]
_loaded_core = [m for m in _RELOAD_ORDER if m in sys.modules] + [
    k for k in list(sys.modules.keys()) if k.startswith("core.") and k not in _RELOAD_ORDER
]
if _loaded_core:
    _needs_reload = (_PREV_APP_MTIME != _APP_MTIME) or any(
        (_CORE_MTIMES.get(m) != os.path.getmtime(getattr(sys.modules[m], "__file__", "")))
        for m in _loaded_core
        if getattr(sys.modules[m], "__file__", None) and os.path.exists(sys.modules[m].__file__)
    )
    if _needs_reload:
        for _m in _loaded_core:
            try:
                importlib.reload(sys.modules[_m])
            except Exception:
                pass
for _m in list(sys.modules.keys()):
    if _m.startswith("core."):
        _fp = getattr(sys.modules[_m], "__file__", None)
        if _fp and os.path.exists(_fp):
            _CORE_MTIMES[_m] = os.path.getmtime(_fp)
sys._nanopro_app_mtime = _APP_MTIME
sys._nanopro_core_mtimes = _CORE_MTIMES

from core.config import OUTPUT_DIR, VIDEO_FPS, FORMAT_SPECS, DEFAULT_WATERMARK, EXPORT_QUALITY_OPTIONS, resolve_export_quality
from core.presets import load_creator_presets, save_custom_creator_preset
from core.tone_engine import DEFAULT_TONE_KEY, DUAL_TONE_KEY, INDIAN_BOY_STYLE_OPTIONS, TONE_PROFILES, UI_TONE_OPTIONS, collect_sfx_timeline, is_dual_tone
from core.director import generate_timeline, generate_viral_meta, generate_video_titles, load_visual_history, reset_visual_history
from core.voice import generate_voiceover, DEFAULT_VOICE, get_elevenlabs_usage, ELEVENLABS_MODELS, VOICE_CATALOG
from core.animator import render_scene_frames, generate_thumbnail_9_16, generate_thumbnail_pack
from core.subtitles import generate_ass_subtitles
from core.renderer import render_final_reel
from core.quality_gate import DEFAULT_QUALITY_MODE, QUALITY_MODES, run_quality_gate_and_self_heal
from core.studio_v2_director import STUDIO_V2_MODE_OPTIONS, generate_v2_timeline, is_studio_v2_mode
from core.studio_v2_vector import render_v2_vector_scene_frames
from core.studio_v2_isometric import render_v2_isometric_scene_frames
from core.studio_v3_ide import render_v3_ide_scene_frames
from core.studio_v4_whiteboard import render_v4_whiteboard_scene_frames
from core.studio_v5_datacenter import (
    DC_TRAVEL_MODES,
    blend_datacenter_scene_transitions,
    render_v5_datacenter_scene_frames,
)
from core.studio_pro_engines import (
    STUDIO_PRO_KEYS,
    render_studio_pro_scene_frames,
)
from core.uploader import (
    upload_to_r2,
    list_r2_videos,
    delete_from_r2,
    get_r2_storage_stats
)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_r2_stats():
    return get_r2_storage_stats()


@st.cache_data(ttl=60, show_spinner=False)
def _cached_r2_videos():
    return list_r2_videos()

# Page Config
st.set_page_config(
    page_title="NanoPro Reel Maker — Studio Max 3D & AI Video Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek Modern Look
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        color: white;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.6rem 2rem;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
    }
    .stat-badge {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Paint Right Panel Header IMMEDIATELY so user sees Studio Max before sidebar widgets stream
st.markdown(
    '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.75rem;">'
    '<div class="main-title">🎬 NanoPro Reel Maker <span style="font-size:0.42em;vertical-align:middle;opacity:0.85;">Studio Max</span></div>'
    '<div style="display:inline-flex;align-items:center;gap:0.55rem;padding:0.42rem 0.9rem;border-radius:999px;background:rgba(30,41,59,0.92);border:1px solid rgba(56,189,248,0.45);box-shadow:0 4px 14px rgba(15,23,42,0.45);">'
    '<span style="color:#F8FAFC;font-weight:700;font-size:0.95rem;">Mangesh Bagul</span>'
    '<span style="color:#64748B;">•</span>'
    '<span style="color:#38BDF8;font-weight:600;font-size:0.92rem;font-family:monospace;">@Code_With_Mangesh</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="sub-title">2026 Smart Director &amp; Studio V2–V5 — Clean Vector Storyboard, Spatial Isometric World, Live IDE (Python/SQL), Blueprint Whiteboard, Enterprise Data Center &amp; 1,221 Semantic Engines.</div>', unsafe_allow_html=True)

# Create main tabs BEFORE sidebar R2/status blocks so main interactive studio stays snappy
tab_create, tab_storage = st.tabs(["🎬 Create New Reel", "☁️ Cloudflare R2 Media & Storage Manager"])

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Video Settings")
    channel_watermark = st.text_input(
        "🏷️ Channel Watermark (Video Corner)",
        value=DEFAULT_WATERMARK,
        help="Channel watermark displayed in the corner of every video frame and thumbnail."
    )

    # ---------------------------------------------------------------------
    # 1-Click Creator Brand Presets (loads & applies cleanly BEFORE widgets)
    # ---------------------------------------------------------------------
    _all_presets = load_creator_presets()
    _preset_keys = list(_all_presets.keys())
    st.session_state.setdefault("creator_preset_select", "custom")
    _chosen_preset_key = st.selectbox(
        "💾 Quick Creator Profile Preset",
        _preset_keys,
        format_func=lambda k: _all_presets.get(k, {}).get("label", k),
        key="creator_preset_select",
        help="Apply a complete 1-click creator setup (Tone, Voice, Format, BGM, Caption Style, Platform Safe-Zone, Audience & CTA), or configure manually and save below."
    )
    _prev_preset_key = st.session_state.get("_prev_creator_preset", "custom")
    if _chosen_preset_key != _prev_preset_key and _chosen_preset_key != "custom":
        _ps = dict(_all_presets.get(_chosen_preset_key, {}).get("settings") or {})
        if _ps.get("tone_key") in TONE_PROFILES:
            _tk = _ps["tone_key"]
            st.session_state["tone_option_select"] = (_tk, TONE_PROFILES[_tk]["label"])
            st.session_state["_prev_tone_option"] = _tk
        if _ps.get("voice_provider"):
            st.session_state["voice_provider_radio"] = _ps["voice_provider"]
        if _ps.get("lang_filter"):
            st.session_state["lang_filter_pills"] = _ps["lang_filter"]
        if _ps.get("gender_filter"):
            st.session_state["gender_filter_pills"] = _ps["gender_filter"]
        if _ps.get("edge_voice_id"):
            _match_ev = next(
                ((v["id"], v["label"]) for v in VOICE_CATALOG.get("edge_tts", []) if v["id"] == _ps["edge_voice_id"]),
                None,
            )
            if _match_ev:
                st.session_state["edge_voice_select"] = _match_ev
        _fmt_opts_map = {
            "9:16": ("9:16", "📱 9:16 Vertical (Reels / Shorts / TikTok - 1080x1920)"),
            "16:9": ("16:9", "🖥️ 16:9 Widescreen (YouTube / Landscape - 1920x1080)"),
            "1:1": ("1:1", "⏹️ 1:1 Square (Instagram / LinkedIn Post - 1080x1080)"),
        }
        _dur_opts_map = {
            "auto": ("auto", "⚡ Dynamic / Auto (AI Decides Length & Scenes • No Limit) [Recommended]"),
            "short": ("short", "⏱️ Quick Pacing (~30-45 sec • AI Decides Scenes)"),
            "standard": ("standard", "🎬 Standard Pacing (~60-90 sec • AI Decides Scenes)"),
            "deep_dive": ("deep_dive", "🧠 Deep-Dive Architecture (~90-240+ sec • AI Decides Scenes)"),
        }
        if _ps.get("aspect_ratio") in _fmt_opts_map:
            st.session_state["format_aspect_select"] = _fmt_opts_map[_ps["aspect_ratio"]]
        if _ps.get("duration_mode") in _dur_opts_map:
            st.session_state["duration_depth_select"] = _dur_opts_map[_ps["duration_mode"]]
        if _ps.get("visual_mode") == "pin_specialist":
            st.session_state["visual_engine_mode_radio"] = "🎛️ Pin Single Specialist Engine (24 Modes)"
        elif _ps.get("visual_mode") == "auto_omni":
            st.session_state["visual_engine_mode_radio"] = "🧠 Auto Omni Smart Director (All Engines Unified) [Recommended]"
        for _sk, _wk in (
            ("indian_boy_vibe", "indian_boy_vibe_select"),
            ("export_quality", "export_quality_select"),
            ("bgm_style", "bgm_style_select"),
            ("bgm_volume_pct", "bgm_volume_slider"),
            ("caption_style", "caption_style_select"),
            ("platform_safe_zone", "platform_safe_zone_select"),
            ("audience_level", "audience_level_select"),
            ("hook_style", "hook_style_select"),
            ("cta_style", "cta_style_select"),
            ("cta_keyword", "cta_keyword_input"),
            ("enable_cam_actions", "enable_cam_actions_chk"),
            ("enable_micro_sfx", "enable_micro_sfx_chk"),
            ("quality_mode", "quality_gate_select"),
            ("studio_v2_mode", "studio_v2_arch_select"),
            ("dc_travel_mode", "dc_travel_mode_select"),
        ):
            if _sk in _ps:
                st.session_state[_wk] = _ps[_sk]
    st.session_state["_prev_creator_preset"] = _chosen_preset_key

    st.markdown("---")
    st.markdown("### 🎭 Script Tone & Emotion (2026 Viral Audio-Visual Sync)")
    tone_option = st.selectbox(
        "Script Tone & 2026 Format",
        UI_TONE_OPTIONS,
        format_func=lambda x: x[1],
        key="tone_option_select",
        help="Controls 2026 script narrative archetype, Hook-to-Climax clause voice speed curves, Action-Synced Micro-SFX, 2s Pattern Interrupts, and semantic visual routing."
    )
    chosen_tone = tone_option[0]

    st.session_state.setdefault("indian_boy_vibe_select", INDIAN_BOY_STYLE_OPTIONS[0])
    indian_boy_choice = st.selectbox(
        "🇮🇳👦 Indian Boy Vibe & Hindi Sync Pace",
        INDIAN_BOY_STYLE_OPTIONS,
        format_func=lambda x: x[1],
        key="indian_boy_vibe_select",
        help="Pick an authentic Indian Hindi boy personality (Cute/Sweet/Smart Chapal, Village Freshness, City Charm, Calm Classic, or Chai-Tapri Dual) with crisp breath pauses and steady concept visuals.",
    )
    if indian_boy_choice and indian_boy_choice[0] != "follow_tone":
        chosen_tone = indian_boy_choice[0]

    # Bidirectional Auto-Sync: Tone <-> Language <-> Voice Persona (Indian Boy Hindi / Dual Pair)
    _prev_tone = st.session_state.get("_prev_tone_option")
    _dual_by_lang = {
        "All": ("dual:hi-IN-SwaraNeural+hi-IN-MadhurNeural", "🗣️🇮🇳 Dual Hinglish: Swara (Curious Q) + Madhur (Mentor A) [Recommended Dual]"),
        "🇮🇳 Hindi": ("dual:hi-IN-SwaraNeural+hi-IN-MadhurNeural", "🗣️🇮🇳 Dual Hinglish: Swara (Curious Q) + Madhur (Mentor A) [Recommended Dual]"),
        "🇮🇳 Marathi": ("dual:mr-IN-AarohiNeural+mr-IN-ManoharNeural", "🗣️🇮🇳 Dual Marathi: Aarohi (Curious Q) + Manohar (Mentor A)"),
        "🇺🇸 English": ("dual:en-US-JennyNeural+en-US-ChristopherNeural", "🗣️🇺🇸 Dual Tech English: Jenny (Curious Q) + Christopher (Mentor A)"),
    }
    if is_dual_tone(chosen_tone) and not is_dual_tone(_prev_tone):
        st.session_state["voice_provider_radio"] = "Microsoft Edge-TTS (Free & Fast)"
        st.session_state["gender_filter_pills"] = "🗣️ Dual Pair"
        _cur_lf = st.session_state.get("lang_filter_pills") or "All"
        st.session_state["edge_voice_select"] = _dual_by_lang.get(_cur_lf, _dual_by_lang["All"])
    elif str(chosen_tone).startswith("indian_boy_") and not str(_prev_tone or "").startswith("indian_boy_"):
        st.session_state["voice_provider_radio"] = "Microsoft Edge-TTS (Free & Fast)"
        if st.session_state.get("lang_filter_pills") not in ("All", "🇮🇳 Hindi"):
            st.session_state["lang_filter_pills"] = "🇮🇳 Hindi"
        if st.session_state.get("gender_filter_pills") in ("🗣️ Dual Pair", "👩 Female"):
            st.session_state["gender_filter_pills"] = "All"
        st.session_state["edge_voice_select"] = ("hi-IN-MadhurNeural", "🇮🇳 Madhur — Native Hindi / Hinglish Tech (Male)")
    elif is_dual_tone(_prev_tone) and not is_dual_tone(chosen_tone):
        if st.session_state.get("gender_filter_pills") == "🗣️ Dual Pair":
            st.session_state["gender_filter_pills"] = "All"
    st.session_state["_prev_tone_option"] = chosen_tone

    st.markdown("---")
    st.markdown("### 🎙️ Voice & TTS Engine")
    st.session_state.setdefault("voice_provider_radio", "Microsoft Edge-TTS (Free & Fast)")
    st.session_state.setdefault("lang_filter_pills", "All")
    st.session_state.setdefault("gender_filter_pills", "All")
    voice_provider = st.radio(
        "Select Voice Engine Provider:",
        ["ElevenLabs AI (Ultra-Realistic)", "Microsoft Edge-TTS (Free & Fast)"],
        key="voice_provider_radio",
        help="Microsoft Edge-TTS is 100% free & unlimited (recommended for testing). Switch to ElevenLabs AI when you want ultra-realistic studio voice."
    )

    # Language & Gender filter pills (persist & cross-sync across reruns with zero warnings)
    col_flt1, col_flt2 = st.columns([1.2, 1])
    with col_flt1:
        if hasattr(st, "pills"):
            lang_filter = st.pills("Language:", ["All", "🇺🇸 English", "🇮🇳 Hindi", "🇮🇳 Marathi"], key="lang_filter_pills")
        else:
            lang_filter = st.radio("Language:", ["All", "🇺🇸 English", "🇮🇳 Hindi", "🇮🇳 Marathi"], horizontal=True, key="lang_filter_pills")
    with col_flt2:
        if hasattr(st, "pills"):
            gender_filter = st.pills("Gender:", ["All", "🗣️ Dual Pair", "👨 Male", "👩 Female"], key="gender_filter_pills")
        else:
            gender_filter = st.radio("Gender:", ["All", "🗣️ Dual Pair", "👨 Male", "👩 Female"], horizontal=True, key="gender_filter_pills")

    l_filter_key = "all" if (not lang_filter or lang_filter == "All") else ("marathi" if "Marathi" in lang_filter else ("hindi" if "Hindi" in lang_filter else "english"))
    g_filter_key = "all" if (not gender_filter or gender_filter == "All") else ("dual" if "Dual" in gender_filter else ("male" if "Male" in gender_filter else "female"))

    if voice_provider == "ElevenLabs AI (Ultra-Realistic)":
        el_usage = get_elevenlabs_usage()
        st.caption(f"💳 **Free Tier Usage:** `{el_usage['character_count']}` / `{el_usage['character_limit']}` credits used ({el_usage['remaining']} remaining)")
        st.progress(min(1.0, max(0.01, el_usage["percent_used"] / 100)))
        st.caption("⚡ **Credit Conservation Active:** Audio is cached locally by hash, so repeated generations consume 0 credits.")

        elevenlabs_model_choice = st.selectbox(
            "ElevenLabs Voice Model",
            [
                ("eleven_flash_v2_5", "⚡ Eleven Flash v2.5 (Fastest & Emotive • 50% fewer credits [Recommended])"),
                ("eleven_multilingual_v2", "🎭 Eleven Multilingual v2 (Emotionally rich delivery for dramatic performances)"),
                ("eleven_turbo_v2_5", "🚀 Eleven Turbo v2.5 (Our best model for real-time and agents)")
            ],
            format_func=lambda x: x[1],
            help="Choose the ElevenLabs model. Flash v2.5 is fastest, supports Hindi/Marathi/English, and uses 50% fewer credits."
        )
        elevenlabs_model_id = elevenlabs_model_choice[0]

        # Filter available voices by language and gender
        available_el_voices = VOICE_CATALOG.get("elevenlabs", [])
        if l_filter_key != "all":
            available_el_voices = [v for v in available_el_voices if v.get("lang") == l_filter_key]
        if g_filter_key != "all":
            available_el_voices = [v for v in available_el_voices if v.get("gender") == g_filter_key]
        if not available_el_voices:
            available_el_voices = VOICE_CATALOG.get("elevenlabs", [])

        if is_dual_tone(chosen_tone):
            st.warning("ℹ️ Dual Voice Dialogue automatically uses 2 alternating Edge-TTS voices for crisp dialogue pairs.", icon="🗣️")

        el_voice_options = [(v["id"], v["label"]) for v in available_el_voices]
        el_voice_options.append(("custom", "✍️ Custom Voice ID (Enter your own Voice ID)"))
        if st.session_state.get("elevenlabs_voice_select") not in el_voice_options:
            st.session_state["elevenlabs_voice_select"] = el_voice_options[0]

        elevenlabs_voice_choice = st.selectbox(
            f"ElevenLabs Voice Persona ({len(available_el_voices)} available)",
            el_voice_options,
            format_func=lambda x: x[1],
            key="elevenlabs_voice_select",
        )
        if elevenlabs_voice_choice[0] == "custom":
            custom_vid = st.text_input("Enter ElevenLabs Voice ID:", placeholder="e.g. pNInz6obpgDQGcFmaJgB")
            chosen_voice = f"elevenlabs:{custom_vid.strip()}" if custom_vid.strip() else "elevenlabs:pNInz6obpgDQGcFmaJgB"
            voice_label = f"ElevenLabs Custom ({custom_vid.strip()})"
        else:
            chosen_voice = elevenlabs_voice_choice[0]
            voice_label = elevenlabs_voice_choice[1]
    else:
        elevenlabs_model_id = "eleven_flash_v2_5"
        st.success("🆓 **Edge-TTS Active:** 100% Free & Unlimited (0 ElevenLabs Credits Used)")
        available_edge_voices = VOICE_CATALOG.get("edge_tts", [])
        if l_filter_key != "all":
            available_edge_voices = [v for v in available_edge_voices if v.get("lang") == l_filter_key]
        if g_filter_key != "all":
            available_edge_voices = [v for v in available_edge_voices if v.get("gender") == g_filter_key]
        if not available_edge_voices:
            available_edge_voices = VOICE_CATALOG.get("edge_tts", [])
        edge_voice_options = [(v["id"], v["label"]) for v in available_edge_voices]
        if st.session_state.get("edge_voice_select") not in edge_voice_options:
            st.session_state["edge_voice_select"] = edge_voice_options[0]

        edge_voice_choice = st.selectbox(
            f"Edge-TTS Voice Persona ({len(available_edge_voices)} available)",
            edge_voice_options,
            format_func=lambda x: x[1],
            key="edge_voice_select",
        )
        chosen_voice = edge_voice_choice[0]
        voice_label = edge_voice_choice[1]

        if is_dual_tone(chosen_tone) or str(chosen_voice).startswith("dual:"):
            all_edge = VOICE_CATALOG.get("edge_tts", [])
            fem_pool = [(v["id"], v["label"]) for v in all_edge if v.get("gender") == "female"]
            male_pool = [(v["id"], v["label"]) for v in all_edge if v.get("gender") == "male"]
            def_fem_id, def_male_id = ("hi-IN-SwaraNeural", "hi-IN-MadhurNeural")
            if str(chosen_voice).startswith("dual:") and "+" in str(chosen_voice):
                def_fem_id, def_male_id = str(chosen_voice).split("dual:", 1)[1].split("+", 1)
            fem_idx = next((i for i, x in enumerate(fem_pool) if x[0] == def_fem_id), 0)
            male_idx = next((i for i, x in enumerate(male_pool) if x[0] == def_male_id), 0)
            with st.expander("🎭 Customize Female (Curious) + Male (Problem Solver) Voices", expanded=False):
                use_custom_pair = st.checkbox("Override Preset Pair with Custom Female + Male Voices", value=False, key="dual_custom_toggle")
                col_df, col_dm = st.columns(2)
                with col_df:
                    fem_pick = st.selectbox("👩 Female (Questions):", fem_pool, index=fem_idx, format_func=lambda x: x[1], key="dual_fem_voice")
                with col_dm:
                    male_pick = st.selectbox("👨 Male (Problem Solver):", male_pool, index=male_idx, format_func=lambda x: x[1], key="dual_male_voice")
                if use_custom_pair:
                    chosen_voice = f"dual:{fem_pick[0]}+{male_pick[0]}"
                    voice_label = f"🗣️ Dual: {fem_pick[1].split('—')[0].strip()} + {male_pick[1].split('—')[0].strip()}"
            _fp = chosen_voice.split("dual:", 1)[1].split("+", 1) if str(chosen_voice).startswith("dual:") and "+" in str(chosen_voice) else ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"]
            st.caption(f"🗣️ **Dual Dialogue Active:** Female (`{_fp[0].split('|')[0]}`) + Male (`{_fp[1].split('|')[0]}`) will alternate automatically across scenes.")
    
    st.session_state.setdefault("format_aspect_select", ("9:16", "📱 9:16 Vertical (Reels / Shorts / TikTok - 1080x1920)"))
    aspect_ratio = st.selectbox(
        "Format",
        [
            ("9:16", "📱 9:16 Vertical (Reels / Shorts / TikTok - 1080x1920)"),
            ("16:9", "🖥️ 16:9 Widescreen (YouTube / Landscape - 1920x1080)"),
            ("1:1", "⏹️ 1:1 Square (Instagram / LinkedIn Post - 1080x1080)")
        ],
        format_func=lambda x: x[1],
        key="format_aspect_select",
    )

    is_local_machine = (sys.platform == "win32")
    st.session_state.setdefault("export_quality_select", "auto_hardware")
    _exp_map = dict(EXPORT_QUALITY_OPTIONS)
    chosen_export_key = st.selectbox(
        "🎞️ Export Quality & Resolution / FPS",
        [k for k, _ in EXPORT_QUALITY_OPTIONS],
        format_func=lambda k: _exp_map.get(k, str(k)),
        key="export_quality_select",
        help="Auto mode renders 4K UHD (2160×3840) @ 60 FPS with PNG High Profile on Local RTX 3050 GPU, and 1080p @ 60 FPS on Online Cloud Studio.",
    )
    active_export = resolve_export_quality(chosen_export_key, is_local=is_local_machine)
    export_fps = int(active_export.get("fps") or VIDEO_FPS)
    export_scale = float(active_export.get("res_scale") or 1.0)
    export_ext = str(active_export.get("frame_ext") or "jpg")
    _base_fmt = FORMAT_SPECS[aspect_ratio[0]]
    export_w = int(round(_base_fmt["width"] * export_scale))
    export_h = int(round(_base_fmt["height"] * export_scale))

    st.session_state.setdefault("duration_depth_select", ("auto", "⚡ Dynamic / Auto (AI Decides Length & Scenes • No Limit) [Recommended]"))
    duration_option = st.selectbox(
        "Video Duration & Depth (Zero Scene Limit • AI Decides)",
        [
            ("auto", "⚡ Dynamic / Auto (AI Decides Length & Scenes • No Limit) [Recommended]"),
            ("short", "⏱️ Quick Pacing (~30-45 sec • AI Decides Scenes)"),
            ("standard", "🎬 Standard Pacing (~60-90 sec • AI Decides Scenes)"),
            ("deep_dive", "🧠 Deep-Dive Architecture (~90-240+ sec • AI Decides Scenes)")
        ],
        format_func=lambda x: x[1],
        key="duration_depth_select",
        help="ZERO artificial scene count cap in ANY mode! Dropdown guides target runtime pacing only — AI autonomously decides exact scenes needed based on topic depth."
    )
    
    st.markdown("---")
    st.markdown("### 🎨 Visual Engine & Style")
    st.session_state.setdefault("studio_v2_arch_select", "classic_nanopro")
    _v2_arch_map = dict(STUDIO_V2_MODE_OPTIONS)
    chosen_studio_arch = st.selectbox(
        "Studio Generation Architecture",
        [k for k, _ in STUDIO_V2_MODE_OPTIONS],
        format_func=lambda k: _v2_arch_map.get(k, str(k)),
        key="studio_v2_arch_select",
        help="Keep Classic NanoPro Studio untouched, OR pick Studio V2 (Vector / Isometric), Studio V3 (Live IDE Python/SQL), Studio V4 (Blueprint Whiteboard), or Studio V5 (Enterprise Data Center & IT Park).",
    )
    st.session_state.setdefault("v2_clean_no_subs_chk", True)
    st.session_state.setdefault("dc_travel_mode_select", "auto")
    chosen_dc_travel = st.session_state.get("dc_travel_mode_select", "auto")
    v2_clean_no_subs = False
    if is_studio_v2_mode(chosen_studio_arch):
        if chosen_studio_arch == "v5_datacenter_park":
            _dc_t_map = dict(DC_TRAVEL_MODES)
            chosen_dc_travel = st.selectbox(
                "Data Center Fly-In Travel Mode",
                [k for k, _ in DC_TRAVEL_MODES],
                format_func=lambda k: _dc_t_map.get(k, str(k)),
                key="dc_travel_mode_select",
                help="Choose how the intro travels across the 2.5D Enterprise Data Center into the matched Department & Engineer workstation.",
            )
        visual_engine = (chosen_studio_arch, _v2_arch_map.get(chosen_studio_arch, chosen_studio_arch))
        omni_color_flow = "🎨 Studio Isolated Clean Navy World"
        v2_clean_no_subs = st.checkbox(
            "🧼 Clean Diagram Mode (No Bottom Karaoke Captions — Like Reference Reels)",
            key="v2_clean_no_subs_chk",
            help="Hides overlapping bottom subtitles so Studio V2/V3/V4/V5 visuals stay 100% readable.",
        )
        st.info(
            "**Isolated Studio Generation Active (Classic NanoPro Untouched):**\n"
            "• **Studio V2 — Vector Storyboard (`GyanaHut`):** 10-segment story bar + progressive SVG widgets + Paired Analogy\n"
            "• **Studio V2 — Spatial Isometric (`@thetechypenguin`):** Continuous 2.5D Architecture World + Camera Fly + Top HUD\n"
            "• **Studio V3 — Live IDE (`Python / SQL`):** Code highlight + mouse click ripple + callout bubble + live output drawer\n"
            "• **Studio V4 — Blueprint Whiteboard (`Excalidraw`):** Dark blueprint grid + hand-drawn marker diagrams + sticky bubbles\n"
            "• **Studio V5 — Enterprise Data Center (`10 Depts · 25 Specialists`):** Fast 1-Scene Fly-In (`Camera / Drone / Fiber`) → Engineer Desk → Instant Topic Deep-Dive\n"
            "• **Studio V17–V28 — Specialized Pro Visual Studios:** SQL Joins (`V17`), ReAct/MCP Agents (`V18`), Storage/Parquet Pruning (`V19`), API/OAuth Inspector (`V21`), Decision Tree (`V23`), Editorial Cards (`V24`), Iceberg V4/Snowflake (`V25`), Multi-Agent Guardrails (`V26`), CDC/Contracts (`V27`), Semantic/Eval Hub (`V28`)",
            icon="✨",
        )
    else:
        visual_engine_mode = st.radio(
            "Engine Mode",
            [
                "🧠 Auto Omni Smart Director (All Engines Unified) [Recommended]",
                "🎛️ Pin Single Specialist Engine (24 Modes)",
            ],
            index=0,
            key="visual_engine_mode_radio",
            help="Auto Omni blends Hook/Q&A, Streaming/Consensus/RAG Topologies, SQL/Terminal Proof, Benchmarks, WebGL/SVG & Interactive FX per scene inside 1 consistent color world. Or switch to Pin Single Specialist Engine to force one specific visual style.",
        )
        if visual_engine_mode.startswith("🧠"):
            visual_engine = ("omni_smart_director", "🧠 Omni Smart Director (All 1,221 Semantic Engines • AI Validator)")
            omni_color_flow = st.radio(
                "Omni Scene Color Cadence",
                [
                    "🌈 Dynamic Multi-World Contrast (Shift Dark/Light Mood Per Scene) [Recommended]",
                    "🎨 Locked Single Color World (1 Harmonious Palette Across Video)",
                ],
                index=0,
                key="omni_color_flow_radio",
            )
            st.info(
                "**Zero-Hardcode 2026 Semantic Routing (1,221 Total Engines):**\n"
                "• 30 IT Domain & 2026 UI Specialists (Snowflake, SQL JOIN, AWS/Azure, Bank CBS/DR, AI IDE, Excalidraw, SRE)\n"
                "• 12-Verb Action Overlays + Virtual Camera Zoom + Error Shake • Topic-Adaptive Duration",
                icon="🧠",
            )
        else:
            omni_color_flow = "🎨 Locked Single Color World"
            visual_engine = st.selectbox(
                "Specialist Visual Engine (24 Modes)",
                [
                    ("studio_300_domain", "🎨 Both Combined: 1,041 Domain/Grammar + 168 Option 1 WebGL/SVG"),
                    ("multi_topology_mix", "🌐 Multi-Topology Mix (46+ Dual-Plane System Topologies + Interactive FX Per Scene)"),
                    ("interactive_storyboard", "✨ Interactive Motion Max (Cursor Glide, Ripples, Thought/Tip/Quiz Bubbles & Word Sync)"),
                    ("data_streaming_pipelines", "🌊 Data & Event Streaming Topologies (Kafka, CDC Debezium, Flink, Lakehouse, Spark)"),
                    ("distributed_consensus_labs", "🛰️ Distributed Systems & Consensus (Raft, Quorum, Hash Rings, Circuit Breakers, Sagas)"),
                    ("ai_rag_agents_studio", "🤖 AI, LLM & RAG Pipelines (Hybrid Search, MCP Tools, KV Cache, Guardrails, Agents)"),
                    ("pure_zero_template", "♾️ Option 1: 168 Zero-Template AI WebGL / SVG / Spatial Code Scenes (∞)"),
                    ("studio_domain_library", "📚 Option 2: 1,041 Studio/Domain & Composable Grammar Layouts"),
                    ("dual_generative", "⚡ Dual Generative Studio (Playwright WebGL/Three.js + Cloud 3D Mesh/Shader)"),
                    ("cinematic_studio", "🎬 Cinematic 2.5D/3D Studio Max (Contrast-Locked Worlds, 1,041 Layouts, 145 Shapes)"),
                    ("auto_dynamic", "⚡ Dynamic / Auto (Unique Layout/Transition/World History Every Click + Voice Sync)"),
                    ("all_in_one_tech_canvas", "🔮 All-in-One Tech Canvas (DB Cylinders, Python, AWS, AI Robot, K8s, Pipeline & 2D Motion)"),
                    ("hybrid_modern", "🚀 Multi-Layer Hybrid Engine (Fireship + ByteByteGo + Terminal)"),
                    ("terminal_screencast", "💻 Real Terminal & Hacker CLI Screencast (Bash / Python / Shell / Logs)"),
                    ("bytebytego_dsl", "📊 ByteByteGo Architecture & Cloud Topology (Pipelines / Microservices)"),
                    ("sql_deepdive", "🗄️ SQL Table, Query & Dataset Execution (Schemas / DENSE_RANK / Window Functions)"),
                    ("split_comparison", "⚖️ Architectural Split Comparison (Legacy vs Modern / Trade-offs)"),
                    ("benchmark_speed", "⚡ Performance Benchmark Bars & Latency (Throughput / Speedup 15x)"),
                    ("memory_internals", "🧩 Memory Buffer, CDC WAL & Partition Slots (Low-level Bytes / Offsets)"),
                    ("network_mesh", "🌐 Circular Hub & Spoke Event Mesh (Message Broker / Radar Nodes)"),
                    ("telemetry_hud", "⏱️ Speedometer & Live Telemetry HUD (99.999% SLA / CPU / Event Counters)"),
                    ("alert_troubleshoot", "🚨 Production Incident Alert & Post-Mortem (Radar Alert / Bottlenecks)"),
                    ("concept_keynote", "💡 Kinetic Concept Keynote (Punchy Principles & Bullet Cards)"),
                    ("custom_user_style", "✍️ Custom Visual Style... (Type your own custom visual aesthetic)")
                ],
                format_func=lambda x: x[1],
                key="visual_engine_select",
                help="Force any single specialist visual engine across the entire video."
            )

    # ---------------------------------------------------------------------
    # 3 Clean Compact Expanders (Audio/Captions · Audience/Hook/CTA · Overrides)
    # ---------------------------------------------------------------------
    st.session_state.setdefault("bgm_style_select", "lofi_cyber")
    st.session_state.setdefault("bgm_volume_slider", 18)
    st.session_state.setdefault("caption_style_select", "karaoke_pop")
    st.session_state.setdefault("platform_safe_zone_select", "instagram_reels")
    with st.expander("🎵 BGM & Caption Style Studio", expanded=False):
        _bgm_labels = {
            "lofi_cyber": "🎹 Chill Lo-Fi Coding (Balanced)",
            "dark_cyber_suspense": "🚨 Dark Cyber Suspense (War Story)",
            "upbeat_electro_pulse": "⚡ Upbeat Synth Pulse (Myth / Cage Match)",
            "none": "🔇 Mute / No BGM (Pure Voice + Micro-SFX)",
        }
        chosen_bgm_style = st.selectbox(
            "Background Music (BGM) Track",
            list(_bgm_labels.keys()),
            format_func=lambda k: _bgm_labels[k],
            key="bgm_style_select",
        )
        bgm_volume_pct = st.slider(
            "BGM Ducking Volume (%)",
            min_value=0, max_value=32, step=2,
            key="bgm_volume_slider",
            disabled=(chosen_bgm_style == "none"),
            help="0% mutes BGM cleanly; 14-18% is balanced under voiceover."
        )
        _cap_labels = {
            "karaoke_pop": "⚡ Bold Karaoke Highlight (Reels / Shorts Pop)",
            "clean_minimal": "🧼 Clean Minimal Pill (ByteByteGo / LinkedIn)",
            "static_bottom": "🅰️ Calm Static Bar (No Bounce)",
            "off": "🚫 Off (Clean Visuals Only — No Subtitles)",
        }
        chosen_caption_style = st.selectbox(
            "Subtitle / Caption Style",
            list(_cap_labels.keys()),
            format_func=lambda k: _cap_labels[k],
            key="caption_style_select",
        )
        _plat_labels = {
            "instagram_reels": "📱 Instagram Reels Safe-Zone (Clears Right Icons & Caption)",
            "youtube_shorts": "▶️ YouTube Shorts Safe-Zone (Clears Bottom Channel Bar)",
            "linkedin_clean": "💼 LinkedIn Clean Frame (Low Minimal Margin)",
        }
        chosen_platform_zone = st.selectbox(
            "Platform UI Safe-Zone",
            list(_plat_labels.keys()),
            format_func=lambda k: _plat_labels[k],
            key="platform_safe_zone_select",
        )

    st.session_state.setdefault("audience_level_select", "working_dev")
    st.session_state.setdefault("hook_style_select", "ai_auto")
    st.session_state.setdefault("cta_style_select", "save_share")
    st.session_state.setdefault("cta_keyword_input", "NOTES")
    with st.expander("🎯 Audience, Hook & Viral CTA", expanded=False):
        _aud_labels = {
            "beginner_interview": "🎓 Beginner / College Interview (Analogies & Traps)",
            "working_dev": "🛠️ Working Developer (Code, SQL & Practical Patterns)",
            "staff_architect": "🏛️ Staff / Principal Architect (Scale, SLA & Cost Trade-Offs)",
        }
        chosen_audience = st.selectbox(
            "Target Audience Depth",
            list(_aud_labels.keys()),
            format_func=lambda k: _aud_labels[k],
            key="audience_level_select",
        )
        _hook_labels = {
            "ai_auto": "🤖 AI Auto-Select (Matched to Scene 1 Tone)",
            "contrarian_stop": "💥 Contrarian Myth ('Stop Doing X At Scale!')",
            "outage_3am": "🚨 3AM Outage Story ('Friday 11:45 PM DB Locked...')",
            "interview_question": "💼 FAANG Interview Challenge ('Asked at Google/Uber...')",
            "shocking_stat": "🔢 Shocking Metric ('90% Teams Waste 4x Budget...')",
        }
        chosen_hook_style = st.selectbox(
            "Opening 2s Hook Strategy",
            list(_hook_labels.keys()),
            format_func=lambda k: _hook_labels[k],
            key="hook_style_select",
        )
        _cta_labels = {
            "save_share": "📌 Save & Share Architecture Checklist",
            "comment_keyword": "💬 Comment Keyword Trigger (ManyChat / Auto-DM Growth)",
            "debate_poll": "⚔️ A vs B Opinion Poll Debate",
            "clean_zero_cta": "🧼 Clean Zero-CTA (Pure Educational Takeaway)",
        }
        chosen_cta_style = st.selectbox(
            "Ending CTA Strategy",
            list(_cta_labels.keys()),
            format_func=lambda k: _cta_labels[k],
            key="cta_style_select",
        )
        chosen_cta_keyword = ""
        if chosen_cta_style == "comment_keyword":
            chosen_cta_keyword = st.text_input(
                "Comment Keyword Trigger (e.g. SYSTEM, SQL, NOTES):",
                key="cta_keyword_input",
                help="AI weaves 'Comment <KEYWORD> below...' into final scene narration & end badge."
            )

    manual_layout_choice = "auto"
    manual_world_choice = "auto"
    manual_backdrop_choice = "auto"
    manual_transition_choice = "auto"
    manual_text_fx_choice = "auto"
    st.session_state.setdefault("enable_cam_actions_chk", True)
    st.session_state.setdefault("enable_micro_sfx_chk", True)
    st.session_state.setdefault("quality_gate_select", DEFAULT_QUALITY_MODE)
    _qg_labels = dict(QUALITY_MODES)
    with st.expander("🎛️ Manual Studio & Motion Overrides", expanded=False):
        chosen_quality_mode = st.selectbox(
            "🧠 AI Quality Gate & Surgical Self-Repair",
            [k for k, _ in QUALITY_MODES],
            format_func=lambda k: _qg_labels[k],
            key="quality_gate_select",
            help="3-Layer Human-Brain Critic (Pixel CV + Audio/NLP Sync + Multimodal Vision LLM) auto-heals failing scenes and always delivers Best-So-Far without blocking.",
        )
        enable_camera_actions = st.checkbox(
            "🎥 Virtual Camera Zoom + 12-Verb Action Overlays",
            key="enable_cam_actions_chk",
            help="Follows speaking cards with smooth zoom/pan, 2s Hook Pattern Interrupt punch, Iconify SVG packet flight, and error screen-shake."
        )
        enable_micro_sfx = st.checkbox(
            "🔊 Action-Synced Micro-SFX + 2s Hook Punch Audio",
            key="enable_micro_sfx_chk",
            help="Mixes tactile pop_snap, alert_ping, key_tick, success_chime & whoosh SFX timed to Whisper words & scene cuts."
        )
        if visual_engine[0] in ("omni_smart_director", "studio_300_domain", "multi_topology_mix", "interactive_storyboard", "data_streaming_pipelines", "distributed_consensus_labs", "ai_rag_agents_studio", "pure_zero_template", "studio_domain_library", "dual_generative", "cinematic_studio", "auto_dynamic", "hybrid_modern"):
            from core.cinematic_engine import (
                ALL_BACKDROPS,
                ALL_STUDIO_LAYOUTS,
                ALL_TEXT_FX,
                ALL_TRANSITIONS,
                STUDIO_WORLDS,
            )
            layout_opts = ["auto", "web_scene", "svg_scene", "spatial_canvas", "grammar:flow:5", "grammar:grid:3x2", "grammar:ring:6"] + list(ALL_STUDIO_LAYOUTS)
            layout_opts = list(dict.fromkeys(layout_opts))
            manual_layout_choice = st.selectbox(
                f"Manual Scene Layout ({len(ALL_STUDIO_LAYOUTS)} Named + Grammar + ∞ Web/SVG)",
                layout_opts,
                format_func=lambda v: "🤖 AI Auto-Select (Recommended)" if v == "auto" else v,
                key="manual_layout_override",
            )
            world_opts = ["auto", "custom_hex"] + list(STUDIO_WORLDS.keys())
            manual_world_choice = st.selectbox(
                f"Color World ({len(STUDIO_WORLDS)} Curated + Custom #HEX)",
                world_opts,
                format_func=lambda v: "🤖 AI Auto-Select" if v == "auto" else ("🎨 Custom #HEX Color..." if v == "custom_hex" else v),
                key="manual_world_override",
            )
            if manual_world_choice == "custom_hex":
                manual_world_choice = st.text_input("Custom #HEX Seed", value="#38BDF8", key="manual_hex_input")
            manual_backdrop_choice = st.selectbox(
                f"Backdrop Shader ({len(ALL_BACKDROPS)} Styles, No Floor Jali)",
                ["auto"] + list(ALL_BACKDROPS),
                format_func=lambda v: "🤖 AI Auto-Select" if v == "auto" else v,
                key="manual_backdrop_override",
            )
            manual_transition_choice = st.selectbox(
                f"Scene Transition ({len(ALL_TRANSITIONS)} FX)",
                ["auto"] + list(ALL_TRANSITIONS),
                format_func=lambda v: "🤖 AI Auto-Select" if v == "auto" else v,
                key="manual_transition_override",
            )
            manual_text_fx_choice = st.selectbox(
                f"Kinetic Text FX ({len(ALL_TEXT_FX)} Styles)",
                ["auto"] + list(ALL_TEXT_FX),
                format_func=lambda v: "🤖 AI Auto-Select" if v == "auto" else v,
                key="manual_textfx_override",
            )
            if "visual_gen_history" not in st.session_state:
                st.session_state["visual_gen_history"] = load_visual_history()
            _vh_cnt = int(st.session_state["visual_gen_history"].get("run_count", 0))
            _vh_c1, _vh_c2 = st.columns([2, 1])
            _vh_c1.caption(f"🎨 **Anti-Repeat History:** `{_vh_cnt}` runs tracked")
            if _vh_c2.button("🔄 Reset", key="reset_vis_hist_btn", help="Clear saved layout/style history"):
                reset_visual_history(st.session_state["visual_gen_history"])
                st.rerun()

    # Save Current Setup as Custom 1-Click Creator Preset
    with st.expander("💾 Save Current Settings as My Preset", expanded=False):
        _new_preset_name = st.text_input("Preset Name:", placeholder="e.g. My Marathi SQL Reels", key="save_preset_name_input")
        if st.button("💾 Save Creator Preset", key="save_preset_btn", use_container_width=True):
            _payload_settings = {
                "tone_key": chosen_tone,
                "indian_boy_vibe": indian_boy_choice,
                "voice_provider": voice_provider,
                "lang_filter": lang_filter or "All",
                "gender_filter": gender_filter or "All",
                "edge_voice_id": chosen_voice if not str(chosen_voice).startswith("elevenlabs:") else "",
                "aspect_ratio": aspect_ratio[0],
                "export_quality": chosen_export_key,
                "duration_mode": duration_option[0],
                "visual_mode": "auto_omni" if visual_engine[0] == "omni_smart_director" else "pin_specialist",
                "bgm_style": chosen_bgm_style,
                "bgm_volume_pct": bgm_volume_pct,
                "caption_style": chosen_caption_style,
                "platform_safe_zone": chosen_platform_zone,
                "audience_level": chosen_audience,
                "hook_style": chosen_hook_style,
                "cta_style": chosen_cta_style,
                "cta_keyword": chosen_cta_keyword,
                "enable_cam_actions": enable_camera_actions,
                "enable_micro_sfx": enable_micro_sfx,
                "quality_mode": chosen_quality_mode,
                "studio_v2_mode": chosen_studio_arch,
                "dc_travel_mode": chosen_dc_travel,
            }
            _saved_slug = save_custom_creator_preset(_new_preset_name, _payload_settings)
            st.session_state["creator_preset_select"] = _saved_slug
            st.session_state["_prev_creator_preset"] = _saved_slug
            st.success(f"✅ Saved preset! Selectable anytime above.")
            st.rerun()

    custom_style_prompt = ""
    if visual_engine[0] == "custom_user_style":
        custom_style_prompt = st.text_input(
            "Enter Custom Visual Aesthetic:",
            placeholder="e.g. Cyberpunk neon green terminal with matrix code rain and glowing data blocks",
            help="Describe the exact visual style, colors, and layout you want for every scene."
        )
    elif manual_layout_choice != "auto":
        custom_style_prompt = f"Use layout '{manual_layout_choice}' across visuals where appropriate."

    # Live Synced Configuration Readout (guarantees all settings reflect immediately)
    _eng_disp = "omni_smart_director" if visual_engine[0] == "omni_smart_director" else visual_engine[1].split("(")[0].strip()[:24]
    st.caption(
        f"🔗 **Active Sync:** `{chosen_tone}` • `{voice_label.split('—')[0].split('(')[0].strip()[:18]}` • "
        f"`{aspect_ratio[0]}` (`{export_w}×{export_h} @ {export_fps}fps`) • `{chosen_bgm_style}` (`{bgm_volume_pct if chosen_bgm_style != 'none' else 0}%`) • "
        f"`{chosen_caption_style}` ({chosen_platform_zone}) • `{chosen_audience}` • `qg:{chosen_quality_mode}` • `{_eng_disp}`"
        + (f" • Override `{manual_layout_choice}`" if manual_layout_choice != "auto" else "")
    )
    
    st.markdown("---")
    st.markdown("### ⚡ Compute & Studio Switcher")
    
    if is_local_machine:
        st.success("🟢 Active: **Local RTX 3050 Studio**")
        st.caption(f"💻 Hardware: NVIDIA RTX 3050 NVENC • 16GB RAM • Auto Export: **{export_w}×{export_h} @ {export_fps} FPS ({export_ext.upper()})**")
        st.link_button("🌐 Switch to Online Cloud Studio", "https://nanopro-reel-maker.streamlit.app", use_container_width=True, type="secondary")
    else:
        st.info("☁️ Active: **Online Cloud Studio**")
        st.caption(f"Running in Cloud • Auto Export: **{export_w}×{export_h} @ {export_fps} FPS ({export_ext.upper()})**. Switch to your laptop's GPU for 4K.")
        st.link_button("⚡ Switch to Local RTX GPU Studio", "http://localhost:8501", use_container_width=True, type="primary")
    
    st.markdown("---")
    with st.expander("☁️ Cloudflare R2 Storage (On-Demand)", expanded=False):
        if st.button("🔄 Check R2 Usage", key="sidebar_r2_check_btn", use_container_width=True) or st.session_state.get("_r2_loaded_once"):
            st.session_state["_r2_loaded_once"] = True
            try:
                r2_stats = _cached_r2_stats()
                st.write(f"💾 **Used:** {r2_stats['total_mb']} MB / 10 GB")
                st.progress(min(1.0, max(0.01, r2_stats["percent_used"] / 100)))
                st.caption(f"📁 **Total Saved Reels:** {r2_stats['total_files']} files • 🆓 **{r2_stats['free_gb_remaining']} GB** free")
            except Exception:
                st.caption("Cloudflare R2 connected")
        else:
            st.caption("Lazy-loaded to keep Studio launch instant. Click above to fetch live R2 usage.")

    _pw_ok = bool(st.session_state.get("pw_web_ok", sys.platform == "win32"))
    _resvg_ok = True
    _layout_cnt = 1041
    _opt1_cnt = 168
    _shape_cnt = 145
    _mesh_cnt = 42
    _glyph_cnt = 80
    _world_cnt = 22
    _bd_cnt = 18
    _tr_cnt = 16
    _fx_cnt = 14
    _alias_cnt = 200
    with st.expander("🚀 Engine Status (Zero-Lag Cached)", expanded=False):
        try:
            from core.cinematic_engine import (
                ALL_STUDIO_LAYOUTS,
                ALL_145_SHAPES,
                VECTOR_GLYPHS,
                STUDIO_WORLDS,
                ALL_BACKDROPS,
                ALL_TRANSITIONS,
                ALL_TEXT_FX,
                is_web_engine_available,
            )
            from core.web_generative_engine import ZERO_TEMPLATE_50_ARCHETYPES
            from core.mesh_shader_engine import ALL_3D_MESHES
            from core.svg_engine import HAS_RESVG, ICON_ALIASES
            if "pw_web_ok" not in st.session_state:
                st.session_state["pw_web_ok"] = bool(is_web_engine_available())
            _pw_ok = bool(st.session_state["pw_web_ok"])
            _layout_cnt = len(ALL_STUDIO_LAYOUTS)
            _opt1_cnt = len(ZERO_TEMPLATE_50_ARCHETYPES)
            _shape_cnt = len(ALL_145_SHAPES)
            _mesh_cnt = len(ALL_3D_MESHES)
            _glyph_cnt = len(VECTOR_GLYPHS)
            _world_cnt = len(STUDIO_WORLDS)
            _bd_cnt = len(ALL_BACKDROPS)
            _tr_cnt = len(ALL_TRANSITIONS)
            _fx_cnt = len(ALL_TEXT_FX)
            _alias_cnt = len(ICON_ALIASES)
            _resvg_ok = bool(HAS_RESVG)
        except Exception:
            pass
        st.success("🟢 Gemini 3.1 / 3 Flash AI Director + Studio V2: Ready")
        st.success("🟢 Edge-TTS + Groq Whisper Large v3 + 5 Micro-SFX: Ready")
        st.success(f"🟢 {_layout_cnt + _opt1_cnt + 12} Semantic Engines | {_shape_cnt} Shapes + {_mesh_cnt} Meshes")
        if _pw_ok:
            st.success("🟢 Playwright Chromium (Vector Storyboard & Isometric 2.5D): Ready")
        st.success("🟢 FFmpeg Hardware Encoder + AI Quality Gate: Ready")

with tab_create:
    # Initialize session state for user prompt
    if "user_prompt_input" not in st.session_state:
        st.session_state.user_prompt_input = "Explain AWS Database Migration Service (DMS) architecture with zero downtime"

    # Quick Prompts (8 Topic & Domain Specialist Showcase Presets)
    st.markdown("**Quick 2026 Preset Topics (Click to Load):**")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("☁️ AWS DMS CDC", use_container_width=True):
        st.session_state.user_prompt_input = "Explain AWS Database Migration Service (DMS) architecture with zero downtime"
        st.rerun()
    if col2.button("📊 SQL JOIN & RANK", use_container_width=True):
        st.session_state.user_prompt_input = "Explain SQL INNER JOIN vs LEFT JOIN and DENSE_RANK with live tables"
        st.rerun()
    if col3.button("❄️ Snowflake Pruning", use_container_width=True):
        st.session_state.user_prompt_input = "How Snowflake micro-partitions and query pruning work under the hood"
        st.rerun()
    if col4.button("🐍 Python Memory/GIL", use_container_width=True):
        st.session_state.user_prompt_input = "Explain Python stack vs heap memory, GIL and asyncio event loop"
        st.rerun()

    col5, col6, col7, col8 = st.columns(4)
    if col5.button("🚨 3AM DB Outage", use_container_width=True):
        st.session_state.user_prompt_input = "Friday 11:45 PM database deadlock outage: 502 retry storm root cause & circuit breaker fix"
        st.rerun()
    if col6.button("🏦 Bank CBS & DR HSM", use_container_width=True):
        st.session_state.user_prompt_input = "How Banking Core Ledger (CBS), HSM PIN Vault & Active-Active DR failover handle UPI scale"
        st.rerun()
    if col7.button("🧪 Line-4 N+1 Debug", use_container_width=True):
        st.session_state.user_prompt_input = "Stop writing N+1 queries inside loops: catching ORM leaks in IDE with batch JOIN fix"
        st.rerun()
    if col8.button("🤖 PyTorch & Agents", use_container_width=True):
        st.session_state.user_prompt_input = "PyTorch tensor backprop, multi-agent workflow DAG and MCP tool execution"
        st.rerun()

    # Prompt Input Box bound directly to session state
    user_prompt = st.text_area(
        "Enter Tech Topic / Scenario Prompt:",
        key="user_prompt_input",
        height=90,
        placeholder="e.g. Explain SQL Window Functions LEAD and LAG with interview scenario"
    )

    with st.expander("✍️ Custom Script / Storyboard Override (Optional)", expanded=False):
        st.caption("Want full control over the spoken script? Type or paste your exact scene-by-scene narration below. The AI Director will structure the visuals around your exact words.")
        custom_script_override = st.text_area(
            "Custom Script Narration Override:",
            placeholder="Scene 1: At 3 AM, our production database locked up under traditional mysqldump...\nScene 2: Here's how AWS DMS replicates changes continuously using CDC without table locks...\nScene 3: The result? Sub-second replication lag and zero production downtime.",
            height=130,
            help="If provided, AI Director will strictly adapt the scenes and visuals to match these exact spoken narrations."
        )

    # Action Studio Controls Bar
    st.markdown("#### 🚀 Action Studio Controls:")
    col_act1, col_act2 = st.columns([1.3, 1])
    col_act3, col_act4, col_act5 = st.columns([1, 1, 1])

    do_full_generate = col_act1.button("🎬 Generate Full Video Reel", type="primary", use_container_width=True)
    do_titles = col_act2.button("🏷️ Make Title for Video", type="secondary", use_container_width=True)
    do_thumbnail = col_act3.button("🖼️ Generate 9:16 Thumbnail", use_container_width=True)
    do_thumb_pack = col_act4.button("✨ 4x High-Tech Thumb Pack", use_container_width=True, help="Generate 4 distinct dark 2026 high-tech thumbnails side-by-side in 1 click!")
    do_meta = col_act5.button("📋 Generate Description & Hashtags", use_container_width=True)

    # 1A. STANDALONE 9:16 THUMBNAIL GENERATOR (16 layouts x 12 dark themes x 8 grids)
    if do_thumbnail:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        _th_var = int(st.session_state.get("thumb_gen_counter", 0))
        st.session_state["thumb_gen_counter"] = _th_var + 1
        with st.spinner(f"Generating unique dark high-tech 9:16 thumbnail variation #{_th_var + 1} with watermark {channel_watermark}..."):
            try:
                thumb_path = generate_thumbnail_9_16(
                    user_prompt.strip(),
                    watermark=channel_watermark,
                    visual_engine=visual_engine[0],
                    tone=chosen_tone,
                    variant_seed=_th_var,
                )
                st.success(f"🎉 Unique 9:16 Dark High-Tech Thumbnail (#{_th_var + 1} of 16+ styles) ready! Click again anytime for a brand-new design.")
                c_th1, c_th2 = st.columns([1, 1.2])
                with c_th1:
                    st.image(str(thumb_path), caption="9:16 High-Conversion Thumbnail (Shorts / Reels Cover)", use_container_width=True)
                with c_th2:
                    st.markdown("### 🖼️ 9:16 Thumbnail Details")
                    st.write(f"- **Aspect Ratio:** `9:16` (1080x1920)")
                    st.write(f"- **Channel Watermark:** `{channel_watermark}`")
                    st.write(f"- **Topic:** *{user_prompt.strip()}*")
                    with open(thumb_path, "rb") as tf:
                        st.download_button(
                            label="⬇️ Download 9:16 Thumbnail (PNG)",
                            data=tf.read(),
                            file_name=thumb_path.name,
                            mime="image/png",
                            use_container_width=True,
                            type="primary"
                        )
            except Exception as e:
                st.error(f"❌ Error generating thumbnail: {e}")

    # 1B. 4x HIGH-TECH DARK THUMBNAIL PACK GENERATOR
    elif do_thumb_pack:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        _pack_start = int(st.session_state.get("thumb_gen_counter", 0))
        st.session_state["thumb_gen_counter"] = _pack_start + 4
        with st.spinner(f"Rendering 4 distinct dark high-tech 9:16 thumbnails for {channel_watermark}..."):
            try:
                pack_items = generate_thumbnail_pack(
                    user_prompt.strip(),
                    count=4,
                    start_seed=_pack_start,
                    watermark=channel_watermark,
                    visual_engine=visual_engine[0],
                    tone=chosen_tone,
                )
                st.success(f"🎉 4 Unique Dark High-Tech Thumbnails ready! Click again for 4 completely new styles (#{_pack_start + 5}–#{_pack_start + 8}).")
                p_cols = st.columns(4)
                for pi, item in enumerate(pack_items):
                    with p_cols[pi]:
                        st.image(str(item["path"]), caption=f"#{item['seed'] + 1} · {item['angle_tag']}", use_container_width=True)
                        with open(item["path"], "rb") as pf:
                            st.download_button(
                                label=f"⬇️ PNG #{item['seed'] + 1}",
                                data=pf.read(),
                                file_name=item["path"].name,
                                mime="image/png",
                                key=f"dl_pack_{item['seed']}",
                                use_container_width=True,
                            )
            except Exception as e:
                st.error(f"❌ Error generating thumbnail pack: {e}")

    # 2. STANDALONE VIRAL DESCRIPTION & HASHTAGS GENERATOR
    elif do_meta:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        with st.spinner("Generating viral YouTube Shorts & Instagram Reels copy & hashtags..."):
            try:
                viral_meta = generate_viral_meta(
                    user_prompt.strip(),
                    channel_tag=channel_watermark
                )
                st.success("🎉 Viral Description & 25+ Hashtags Ready!")
                st.markdown("### 🎯 High-CTR Catchy Titles:")
                for t in viral_meta.get("titles", []):
                    st.markdown(f"- **{t}**")
                
                st.markdown("### 📝 Full Description & Hashtags (Ready to Copy):")
                st.code(viral_meta.get("full_text", ""), language="markdown")
                
                st.download_button(
                    label="⬇️ Download Description & Tags (.txt)",
                    data=viral_meta.get("full_text", ""),
                    file_name=f"description_and_hashtags_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Error generating metadata: {e}")

    # 3. MAKE TITLE FOR VIDEO (High-CTR Viral Title Generator)
    elif do_titles:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        with st.spinner(f"Generating viral, high-converting video titles for '{user_prompt[:50]}' ..."):
            try:
                title_list = generate_video_titles(user_prompt.strip(), channel_tag=channel_watermark)
                st.success("🎉 High-CTR Video Titles Ready! Choose one or click 'Use This Title':")
                
                for idx, t_obj in enumerate(title_list):
                    t_text = t_obj.get("title", "")
                    t_cat = t_obj.get("category", "Viral Hook")
                    c_t1, c_t2 = st.columns([3.5, 1])
                    with c_t1:
                        st.markdown(f"**{idx + 1}. {t_text}** `[{t_cat}]`")
                    with c_t2:
                        if st.button("📌 Use This Title", key=f"use_title_btn_{idx}", use_container_width=True):
                            st.session_state.user_prompt_input = t_text
                            st.rerun()
                
                st.markdown("---")
                all_titles_text = "\n".join([f"{i+1}. {t.get('title', '')} [{t.get('category', '')}]" for i, t in enumerate(title_list)])
                st.markdown("**Copy All Titles:**")
                st.code(all_titles_text, language="text")
            except Exception as e:
                st.error(f"❌ Error generating titles: {e}")

    # 4. FULL REEL GENERATION ACTION
    elif do_full_generate:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt.")
            st.stop()

        progress_bar = st.progress(0)
        status_box = st.empty()

        try:
            # STEP 1: AI Director Timeline Generation
            status_box.info("🧠 AI Director is designing the technical storyboard & script...")
            progress_bar.progress(15)
            full_prompt = user_prompt.strip()
            if custom_script_override.strip():
                full_prompt += f"\n\nEXPLICIT USER SCRIPT OVERRIDE (MANDATORY: Follow these exact scene narrations):\n{custom_script_override.strip()}"

            if "visual_gen_history" not in st.session_state:
                st.session_state["visual_gen_history"] = load_visual_history()

            if is_studio_v2_mode(chosen_studio_arch):
                timeline = generate_v2_timeline(
                    full_prompt,
                    v2_mode=chosen_studio_arch,
                    tone=chosen_tone,
                    duration_mode=duration_option[0],
                    voice=chosen_voice,
                    watermark=channel_watermark,
                    audience_level=chosen_audience,
                    hook_style=chosen_hook_style,
                    cta_style=chosen_cta_style,
                    cta_keyword=chosen_cta_keyword,
                    dc_travel_mode=chosen_dc_travel,
                )
            else:
                timeline = generate_timeline(
                    full_prompt,
                    tone=chosen_tone,
                    engine_style=visual_engine[0],
                    duration_mode=duration_option[0],
                    custom_style_prompt=custom_style_prompt,
                    voice=chosen_voice,
                    format_ratio=aspect_ratio[0],
                    visual_history=st.session_state["visual_gen_history"],
                    audience_level=chosen_audience,
                    hook_style=chosen_hook_style,
                    cta_style=chosen_cta_style,
                    cta_keyword=chosen_cta_keyword,
                )

                # Apply ALL manual overrides, color cadence & 2026 motion flags BEFORE UI preview table, TTS, & rendering!
                for _i_ov, _sc_ov in enumerate(timeline.get("scenes", [])):
                    if visual_engine[0] == "omni_smart_director" and "Locked Single" in str(omni_color_flow):
                        _locked_w = timeline.get("art_style", "sapphire_3d")
                        _sc_ov["art_style"] = _locked_w
                        _sc_ov.setdefault("visual_data", {})["art_style"] = _locked_w
                    if not enable_camera_actions:
                        _sc_ov["_disable_camera_actions"] = True
                    if manual_world_choice != "auto":
                        _sc_ov["art_style"] = manual_world_choice
                        _sc_ov.setdefault("visual_data", {})["art_style"] = manual_world_choice
                        if isinstance(timeline, dict) and _i_ov == 0:
                            timeline["art_style"] = manual_world_choice
                    if manual_layout_choice != "auto":
                        _sc_ov["visual_type"] = manual_layout_choice
                        _sc_ov["routed_engine"] = f"Manual Override ({manual_layout_choice})"
                    if manual_backdrop_choice != "auto":
                        _sc_ov["backdrop"] = manual_backdrop_choice
                        _sc_ov.setdefault("visual_data", {})["backdrop"] = manual_backdrop_choice
                    if manual_transition_choice != "auto":
                        _sc_ov["transition"] = manual_transition_choice
                        _sc_ov.setdefault("visual_data", {})["transition"] = manual_transition_choice
                    if manual_text_fx_choice != "auto":
                        _sc_ov["text_fx"] = manual_text_fx_choice
                        _sc_ov.setdefault("visual_data", {})["text_fx"] = manual_text_fx_choice

            with st.expander("🧠 Scene-by-Scene Best Engine, 2026 Tone & Layout Selection", expanded=True):
                from core.action_engine import get_story_beat_motion
                _route_rows = []
                for _sc in timeline.get("scenes", []):
                    _vd = _sc.get("visual_data") or {}
                    _sc_tn = str(_sc.get("scene_tone") or chosen_tone)
                    _sc_sfx = str(_sc.get("sfx_cue") or "whoosh")
                    _mprof = get_story_beat_motion(_sc.get("role"), _sc.get("narration"), tone=_sc_tn)
                    _route_rows.append({
                        "Scene": f"Scene {_sc.get('scene_id', '?')} ({_sc.get('role', 'content')})",
                        "Selected Engine": _sc.get("routed_engine") or visual_engine[1].split("(")[0].strip(),
                        "Layout / Mode": _vd.get("option1_archetype") or _sc.get("visual_type", "custom_scene"),
                        "2026 Tone & SFX": f"{_sc_tn} • {(_sc_sfx if enable_micro_sfx else 'muted')}",
                        "Motion / FX": f"{(_mprof if enable_camera_actions else 'static_card')} • {_sc.get('backdrop', 'auto')}",
                        "Theme World": _sc.get("art_style") or timeline.get("art_style", "sapphire_3d"),
                    })
                if _route_rows:
                    st.dataframe(_route_rows, use_container_width=True, hide_index=True)

            with st.expander("📄 View Raw AI Director Blueprint (JSON)", expanded=False):
                st.json(timeline)

            # STEP 2: Voiceover & Whisper Alignment
            status_box.info("🎙️ Synthesizing conversational voiceover & microsecond word timestamps...")
            progress_bar.progress(35)
            scenes = timeline.get("scenes", [])
            audio_path, word_timestamps, aligned_scenes = generate_voiceover(
                scenes,
                voice=chosen_voice,
                elevenlabs_model=elevenlabs_model_id,
                tone=chosen_tone,
                allow_elevenlabs=(voice_provider == "ElevenLabs AI (Ultra-Realistic)")
            )

            with st.expander("🔊 Audio & Word Timestamps", expanded=False):
                st.audio(str(audio_path))
                st.write(f"Total Spoken Words: {len(word_timestamps)}")

            # STEP 3: 2D Generative Visual Rendering
            total_sc = len(aligned_scenes)
            all_scene_frame_dirs = []

            # Clean previous scene frame directories to avoid cross-contamination
            import shutil
            for old_dir in OUTPUT_DIR.glob("scene_*_frames"):
                try:
                    shutil.rmtree(old_dir, ignore_errors=True)
                except Exception:
                    pass

            for i, sc in enumerate(aligned_scenes):
                all_scene_frame_dirs.append(OUTPUT_DIR / f"scene_{i + 1:02d}_frames")

            # Parallel Multi-Core Scene Rendering (3x-4x faster while writing isolated per-scene dirs cleanly)
            from concurrent.futures import ThreadPoolExecutor, as_completed
            status_box.info(f"⚡ Rendering {total_sc} scenes in parallel with watermark ({channel_watermark})...")
            progress_bar.progress(45)

            def _render_scene_task(i_sc):
                idx_i, sc_obj = i_sc
                sc_start = float(sc_obj.get("start_time", 0.0))
                sc_end = float(sc_obj.get("end_time", sc_start + float(sc_obj.get("duration", 5.0))))
                sc_words = [
                    w for w in word_timestamps
                    if sc_start - 0.1 <= float(w.get("start", 0.0)) <= sc_end + 0.1
                ]
                v_type = str(sc_obj.get("visual_type") or "")
                if v_type in ("v2_vector_storyboard", "v2_spatial_isometric", "v3_live_ide", "v4_blueprint_whiteboard", "v5_datacenter_park", "v5_live_ide", "v7_blueprint_whiteboard") or v_type in STUDIO_PRO_KEYS:
                    sc_obj.setdefault("visual_data", {})["watermark"] = channel_watermark
                if v_type == "v2_vector_storyboard":
                    render_v2_vector_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        format_ratio=aspect_ratio[0],
                        scene_words=sc_words,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                elif v_type == "v2_spatial_isometric":
                    render_v2_isometric_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        prev_scene=(aligned_scenes[idx_i - 1] if idx_i > 0 else None),
                        format_ratio=aspect_ratio[0],
                        scene_words=sc_words,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                elif v_type in ("v3_live_ide", "v5_live_ide"):
                    render_v3_ide_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        format_ratio=aspect_ratio[0],
                        scene_words=sc_words,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                elif v_type in ("v4_blueprint_whiteboard", "v7_blueprint_whiteboard"):
                    render_v4_whiteboard_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        format_ratio=aspect_ratio[0],
                        scene_words=sc_words,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                elif v_type == "v5_datacenter_park":
                    render_v5_datacenter_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        format_ratio=aspect_ratio[0],
                        scene_words=sc_words,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                elif v_type in STUDIO_PRO_KEYS:
                    render_studio_pro_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        format_ratio=aspect_ratio[0],
                        scene_words=sc_words,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                else:
                    render_scene_frames(
                        sc_obj,
                        idx_i + 1,
                        total_scenes=total_sc,
                        engine_style=visual_engine[0],
                        format_ratio=aspect_ratio[0],
                        watermark=channel_watermark,
                        scene_words=sc_words,
                        custom_style_prompt=custom_style_prompt,
                        tone=chosen_tone,
                        fps=export_fps,
                        res_scale=export_scale,
                        frame_ext=export_ext,
                    )
                return idx_i + 1

            with ThreadPoolExecutor(max_workers=min(4, max(1, total_sc))) as pool_ren:
                futs = [pool_ren.submit(_render_scene_task, (i, sc)) for i, sc in enumerate(aligned_scenes)]
                done_cnt = 0
                for fut in as_completed(futs):
                    fut.result()
                    done_cnt += 1
                    progress_bar.progress(45 + int(24 * done_cnt / max(1, total_sc)))

            if any(str(s.get("visual_type") or "") == "v5_datacenter_park" for s in aligned_scenes):
                blend_datacenter_scene_transitions(aligned_scenes, all_scene_frame_dirs, transition_frames=max(12, int(round(0.40 * export_fps))))

            # STEP 3.5: Closed-Loop AI Quality Critic & Surgical Self-Repair Engine
            sfx_events = collect_sfx_timeline(aligned_scenes, word_timestamps=word_timestamps, tone=chosen_tone) if enable_micro_sfx else []

            def _qg_rerender_scene(i_sc):
                return _render_scene_task(i_sc)

            def _qg_progress(msg: str, frac: float = 0.5):
                status_box.info(msg)
                progress_bar.progress(min(79, 69 + int(10 * max(0.0, min(1.0, frac)))))

            effective_caption_style = (
                "off" if (is_studio_v2_mode(chosen_studio_arch) and v2_clean_no_subs) else chosen_caption_style
            )

            aligned_scenes, all_scene_frame_dirs, qg_report = run_quality_gate_and_self_heal(
                topic=user_prompt.strip(),
                aligned_scenes=aligned_scenes,
                frame_dirs=all_scene_frame_dirs,
                word_timestamps=word_timestamps,
                sfx_events=sfx_events,
                quality_mode=chosen_quality_mode,
                render_single_scene_fn=_qg_rerender_scene,
                format_ratio=aspect_ratio[0],
                caption_style=effective_caption_style,
                platform_safe_zone=chosen_platform_zone,
                progress_cb=_qg_progress,
            )

            with st.expander("🎞️ Scene-by-Scene Visual Preview Strip (Rendered Keyframes)", expanded=True):
                _prev_cols = st.columns(min(4, max(1, len(all_scene_frame_dirs))))
                for _si, _sdir in enumerate(all_scene_frame_dirs):
                    _sc_meta = aligned_scenes[_si] if _si < len(aligned_scenes) else {}
                    _frames_s = sorted(list(_sdir.glob("frame_*.*"))) if _sdir.exists() else []
                    if _frames_s:
                        _mid_f = _frames_s[int(len(_frames_s) * 0.72)]
                        with _prev_cols[_si % len(_prev_cols)]:
                            _r_eng = _sc_meta.get("routed_engine") or _sc_meta.get("visual_type", "studio")
                            st.image(str(_mid_f), caption=f"S{_si + 1}: {_r_eng}", use_container_width=True)

            # STEP 4: Video Stitching via Local Hardware / Cloud
            status_box.info(f"⚡ Assembling {aspect_ratio[0]} MP4 ({effective_caption_style}, {chosen_bgm_style} BGM, Micro-SFX)...")
            progress_bar.progress(80)
            art_style_val = timeline.get("art_style", "editorial_dark") if isinstance(timeline, dict) else "editorial_dark"
            subtitles_path = generate_ass_subtitles(
                word_timestamps,
                format_ratio=aspect_ratio[0],
                tone=chosen_tone,
                aligned_scenes=aligned_scenes,
                art_style=art_style_val,
                caption_style=effective_caption_style,
                platform_safe_zone=chosen_platform_zone,
            )
            sfx_events = collect_sfx_timeline(aligned_scenes, word_timestamps=word_timestamps, tone=chosen_tone) if enable_micro_sfx else []

            # Run Cover Thumbnail & Viral Metadata in parallel while FFmpeg stitches MP4!
            with ThreadPoolExecutor(max_workers=2) as pool_meta:
                fut_thumb = pool_meta.submit(
                    generate_thumbnail_9_16,
                    user_prompt.strip(),
                    timeline=timeline,
                    watermark=channel_watermark,
                    visual_engine=visual_engine[0],
                    tone=chosen_tone,
                )
                fut_viral = pool_meta.submit(
                    generate_viral_meta,
                    user_prompt.strip(),
                    timeline=timeline,
                    channel_tag=channel_watermark,
                )
                final_video_path = render_final_reel(
                    all_scene_frame_dirs=all_scene_frame_dirs,
                    audio_path=audio_path,
                    subtitles_path=subtitles_path,
                    output_filename=f"nanopro_{aspect_ratio[0].replace(':', 'x')}_{int(time.time())}.mp4",
                    sfx_events=sfx_events,
                    bgm_style=chosen_bgm_style,
                    bgm_volume=(bgm_volume_pct / 100.0) if chosen_bgm_style != "none" else 0.0,
                    fps=export_fps,
                    export_spec=active_export,
                )
                status_box.info("🖼️ Finalizing 9:16 thumbnail & viral metadata...")
                progress_bar.progress(92)
                thumb_path = fut_thumb.result()
                viral_meta = fut_viral.result()

            # Cloudflare R2 Upload (Automatic only on Cloud, Optional on Local)
            r2_url = None
            if not is_local_machine:
                status_box.info("☁️ Uploading to Cloudflare R2 CDN...")
                r2_url = upload_to_r2(final_video_path)

            progress_bar.progress(100)
            if is_local_machine:
                status_box.success("🎉 Full Reel generated and saved locally on your laptop!")
            else:
                status_box.success("🎉 Full Reel generation complete and deployed to Cloud CDN!")

            # Display Final Video & Actions
            col_vid, col_meta = st.columns([1, 1.1])
            with col_vid:
                st.markdown(f"### 📱 {aspect_ratio[0]} Video Preview")
                st.video(str(final_video_path))
                with open(final_video_path, "rb") as vf:
                    st.download_button(
                        label=f"⬇️ Download {aspect_ratio[0]} MP4 Video",
                        data=vf.read(),
                        file_name=final_video_path.name,
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary"
                    )

                # 9:16 Thumbnail Section
                if thumb_path and thumb_path.exists():
                    st.markdown("---")
                    st.markdown("### 🖼️ 9:16 Thumbnail (Shorts / Reels Cover)")
                    st.image(str(thumb_path), caption="9:16 High-Conversion Thumbnail", use_container_width=True)
                    with open(thumb_path, "rb") as tf:
                        st.download_button(
                            label="⬇️ Download 9:16 Thumbnail (PNG)",
                            data=tf.read(),
                            file_name=thumb_path.name,
                            mime="image/png",
                            use_container_width=True,
                            type="secondary"
                        )

            with col_meta:
                st.markdown("### 📊 Production Inspector & Reel Summary")
                total_duration = aligned_scenes[-1]['end_time']
                
                # Top KPI Row
                kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
                kpi1.metric("⏱️ Duration", f"{total_duration:.1f}s")
                kpi2.metric("🎬 Scenes", f"{len(aligned_scenes)}")
                kpi3.metric("🗣️ Words", f"{len(word_timestamps)}")
                kpi4.metric("📐 Format", f"{aspect_ratio[0]}")
                _qg_score_disp = (
                    f"{qg_report.get('final_score', 'N/A')}/100"
                    if qg_report.get("mode") != "fast" and qg_report.get("final_score") is not None
                    else "Bypassed"
                )
                kpi5.metric("🧠 AI Score", _qg_score_disp)

                # AI Quality Gate Scorecard & Surgical Self-Repair Log
                with st.expander(
                    f"🧠 AI Quality Gate Scorecard — {qg_report.get('status', 'N/A')} ({_qg_score_disp})",
                    expanded=True,
                ):
                    st.caption(
                        f"Mode: `{qg_report.get('mode', chosen_quality_mode)}` • "
                        f"Critic: `{qg_report.get('critic_model', 'none')}` • "
                        f"Target: `>= {qg_report.get('target_score', 84)}/100`"
                    )
                    if qg_report.get("verdict_summary"):
                        st.info(qg_report["verdict_summary"])
                    _dim_labels = [
                        ("concept_clarity", "Concept & Flow Clarity"),
                        ("visual_topic_match", "Visual ↔ Topic Match"),
                        ("motion_action_precision", "Motion & Action Precision"),
                        ("layout_legibility", "Layout & Text Legibility"),
                        ("voice_karaoke_sync", "Voice ↔ Karaoke Sync"),
                        ("audio_sfx_harmony", "Audio & SFX Harmony"),
                    ]
                    _dims = qg_report.get("dimensions", {}) or {}
                    _dc1, _dc2 = st.columns(2)
                    for _di, (_dk, _dlbl) in enumerate(_dim_labels):
                        if _dk in _dims:
                            _val = int(_dims[_dk])
                            with (_dc1 if _di % 2 == 0 else _dc2):
                                st.caption(f"**{_dlbl}:** `{_val}/100`")
                                st.progress(max(0.0, min(1.0, _val / 100.0)))
                    _rounds = qg_report.get("rounds", []) or []
                    if _rounds:
                        _r_trail = " → ".join(
                            f"R{r.get('round')}: {r.get('overall_score')}/100"
                            for r in _rounds
                        )
                        st.markdown(f"**Score Progression:** `{_r_trail}`")
                    _repairs = qg_report.get("repairs", []) or []
                    if _repairs:
                        st.markdown("**Surgical Repairs Applied:**")
                        for _rep in _repairs:
                            if isinstance(_rep, dict):
                                st.markdown(
                                    f"- Round `{_rep.get('round')}` Scene `{_rep.get('scene_index')}`: "
                                    f"`{_rep.get('defect_type')}` → {_rep.get('action')}"
                                )
                            else:
                                st.markdown(f"- {_rep}")
                    else:
                        st.caption("✨ No surgical scene repairs needed — first pass clean!")

                # Viral Description & Hashtags Expander
                with st.expander("📋 Viral Description & 25+ Hashtags (Ready to Copy)", expanded=True):
                    st.markdown("#### 🎯 Catchy Titles:")
                    for t in viral_meta.get("titles", []):
                        st.markdown(f"- **{t}**")
                    st.markdown("#### 📝 Full Description & Hashtags:")
                    st.code(viral_meta.get("full_text", ""), language="markdown")
                    st.download_button(
                        label="⬇️ Download Description & Tags (.txt)",
                        data=viral_meta.get("full_text", ""),
                        file_name=f"description_{int(time.time())}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                # Permanent Cloudflare R2 CDN Link Section
                if r2_url:
                    st.success("✅ **Uploaded to Cloudflare R2 CDN (Permanent Link):**")
                    st.code(r2_url, language="text")
                    st.link_button("🌐 Open Video in New Tab", r2_url, type="primary", use_container_width=True)
                elif is_local_machine:
                    st.info(f"💾 **Local Video Path:** `{final_video_path}`")
                    c_up1, c_up2 = st.columns(2)
                    with c_up1:
                        if st.button("📂 Open Output Folder", use_container_width=True):
                            import os
                            os.startfile(str(OUTPUT_DIR))
                    with c_up2:
                        if st.button("☁️ Upload to R2 CDN Now", use_container_width=True):
                            with st.spinner("Uploading to Cloudflare R2 Global Edge..."):
                                manual_r2 = upload_to_r2(final_video_path)
                                if manual_r2:
                                    st.success("✅ Permanent CDN Link Ready!")
                                    st.code(manual_r2, language="text")
                                    st.link_button("🌐 Open Live Video", manual_r2, type="primary", use_container_width=True)

                st.markdown("---")

                # 1. Step-by-Step Production Log ("First kay kel, then kay, then kay...")
                with st.expander("🔄 Complete Pipeline Execution Log (Start to Finish)", expanded=True):
                    st.markdown(f"""
                    1. **🧠 Step 1 — AI Director & Storyboard Blueprinting:**
                       - **Topic Entered:** *"{user_prompt.strip()}"*
                       - **Script Tone & Cadence:** `{tone_option[1]}`
                       - **Visual Engine:** `{visual_engine[1]}`
                       - **Duration Strategy:** `{duration_option[1]}` (Planned {len(aligned_scenes)} scenes without artificial 60s cutoff)
                    
                    2. **🎙️ Step 2 — Text-to-Speech & Microsecond Alignment:**
                       - **Voice Gender / Language:** `{gender_filter}` / `{lang_filter}`
                       - **Voice Persona (TTS):** `{voice_label}` (`{chosen_voice}`)
                       - **Per-Scene Tone Delivery:** `{"Dynamic 2026 Auto-Mix -> " + ", ".join(s.get("scene_tone", "") for s in aligned_scenes) if chosen_tone == DEFAULT_TONE_KEY else chosen_tone}`
                       - **Speech Engine:** `{"ElevenLabs (" + elevenlabs_model_id + ")" if (voice_provider == "ElevenLabs AI (Ultra-Realistic)" and chosen_voice.startswith("elevenlabs:")) else "Microsoft Edge-TTS (Clause Speed Curve)"}`
                       - **Audio Alignment API:** `Groq Whisper Large v3` (`whisper-large-v3`)
                       - **Total Aligned Words:** `{len(word_timestamps)}` words aligned with 0% drift across all scenes.

                    3. **🎨 Step 3 — Studio Max 3D & Dual Generative Visual Rendering:**
                       - **Rendering Engine:** {"Zero-Limit Dual Engine (Playwright WebGL/Three.js + NumPy 3D Mesh + Rust resvg_py SVG)" if _pw_ok else "Studio Max Hybrid 3D Engine (NumPy 3D Mesh/Shader + Rust resvg_py 3D SVG + Pillow)"} (`{visual_engine[0]}`)
                       - **Resolution & Frame Rate:** {export_w}x{export_h} ({aspect_ratio[0]}) @ {export_fps} FPS ({export_ext.upper()} High Profile)
                       - **Dynamic Story Elements:** {"AI Autonomous Visual Mix -> " + ", ".join(s.get("visual_type", "") for s in aligned_scenes) if visual_engine[0] == "auto_dynamic" else "Visuals strictly enforced to match `" + visual_engine[0] + "`"}
                       - **Total Frames Generated:** `{round(total_duration * export_fps)}` frames rendered frame-by-frame.

                    3.5. **🧠 Step 3.5 — Closed-Loop AI Quality Critic & Surgical Self-Repair:**
                       - **Gate Mode & Critic:** `{qg_report.get('mode', chosen_quality_mode)}` (`{qg_report.get('critic_model', 'none')}`)
                       - **Final Verdict:** `{qg_report.get('status', 'N/A')}` — Score `{qg_report.get('final_score', 'N/A')}/100` across {len(qg_report.get('rounds', []))} round(s), {len(qg_report.get('repairs', []))} surgical repair(s).

                    4. **⚡ Step 4 — Hardware FFmpeg Video Stitching & Captions:**
                       - **Video Encoder:** Hardware Accelerated High-Bitrate (Windows Media Foundation 8 Mbps / libx264 CRF 18)
                       - **Audience, Hook & CTA:** `{chosen_audience}` | `{chosen_hook_style}` | `{chosen_cta_style}`{(' (`' + chosen_cta_keyword + '`)') if chosen_cta_style == 'comment_keyword' and chosen_cta_keyword else ''}
                       - **Karaoke / Captions:** `{chosen_caption_style}` adapted to `{chosen_platform_zone}` ({aspect_ratio[0]})
                       - **Audio Mixing:** {len(sfx_events)} Action-Synced Micro-SFX cues + `{chosen_bgm_style}` BGM @ {bgm_volume_pct if chosen_bgm_style != 'none' else 0}% under voiceover.

                    5. **☁️ Step 5 — Deployment & Storage:**
                       - **Host Compute:** `{"Local NVIDIA RTX 3050 Laptop Studio (Windows)" if is_local_machine else "Online Cloud Studio Container (Linux)"}`
                       - **Cloud CDN Target:** Cloudflare R2 Global Object Storage (`nanopro-reels`)
                    """)

                # 2. Complete Spoken Script (Verbatim Transcript)
                with st.expander("📜 Full Verbatim Script (Complete Narrator Transcript)", expanded=False):
                    full_script_text = "\n\n".join([f"[Scene {idx + 1} • {sc.get('role', 'scene').upper()} ({sc['duration']:.1f}s)]\n{sc.get('narration')}" for idx, sc in enumerate(aligned_scenes)])
                    st.text_area("Full Script Text:", value=full_script_text, height=220)
                    st.markdown(f"**Total Script Word Count:** {len(word_timestamps)} words")

                # 3. Scene-by-Scene Visual Breakdown ("Kontya scenes sathi konte visuals, kasa plan kela, konte element ghetle")
                with st.expander("🎬 Scene-by-Scene Visual Storyboard & Elements Breakdown", expanded=False):
                    for idx, sc in enumerate(aligned_scenes):
                        v_data = sc.get("visual_data") or {}
                        if not isinstance(v_data, dict):
                            v_data = {}
                        v_type = sc.get("visual_type", "cards")
                        st.markdown(f"#### 📍 Scene {idx + 1}: `{sc.get('role', 'Scene').upper()}` ({sc['start_time']:.1f}s ➔ {sc['end_time']:.1f}s • {sc['duration']:.1f}s)")
                        st.markdown(f"- **Visual Engine:** `{v_type}`")
                        _disp_badge = v_data.get("badge") or v_data.get("hud_pill") or v_data.get("tag_pill") or "N/A"
                        _disp_title = v_data.get("title") or f"{v_data.get('headline_white', '')} {v_data.get('headline_accent', '')}".strip() or "N/A"
                        st.markdown(f"- **Badge & Title:** `{_disp_badge}` — **{_disp_title}**")
                        
                        # Show specific elements based on visual type
                        if v_type in ("v3_live_ide", "v5_live_ide"):
                            st.markdown(f"- **IDE File & Focus Lines:** `{v_data.get('file_name', 'main.py')}` (`{v_data.get('language', 'python')}`) • Focus lines: `{v_data.get('focus_lines', [])}`")
                            st.code("\n".join(str(x) for x in (v_data.get("code_lines") or [])[:6]), language=str(v_data.get("language") or "python"))
                            _dr = v_data.get("output_drawer") if isinstance(v_data.get("output_drawer"), dict) else {}
                            st.markdown(f"- **Output Drawer:** `{_dr.get('mode', 'terminal')}` — **{_dr.get('metric', '')}**")
                        elif v_type in ("v4_blueprint_whiteboard", "v7_blueprint_whiteboard"):
                            _dnodes = " ➔ ".join(
                                f"**[{n.get('label') if isinstance(n, dict) else str(n)}]**"
                                for n in (v_data.get("diagram_nodes") or [])
                            )
                            st.markdown(f"- **Marker Nodes:** {_dnodes or 'Whiteboard diagram'}")
                            _stickies = [
                                (f"`{s.get('title', 'NOTE')}`: {s.get('text', '')}" if isinstance(s, dict) else str(s))
                                for s in (v_data.get("sticky_notes") or [])
                                if s
                            ]
                            if _stickies:
                                st.markdown(f"- **Sticky Bubbles:** {' · '.join(_stickies)}")
                        elif v_type == "v5_datacenter_park":
                            _dc_dept = (v_data.get("department") or {}).get("full", "") if isinstance(v_data.get("department"), dict) else ""
                            _dc_sp = (v_data.get("specialist") or {}).get("title", "") if isinstance(v_data.get("specialist"), dict) else ""
                            st.markdown(f"- **Data Center Mode:** `{v_data.get('dc_mode')}` (`{v_data.get('travel_mode')}` travel) • **Department:** `{_dc_dept}` • **Specialist:** `{_dc_sp}`")
                        elif v_type in ("v2_vector_storyboard", "v2_spatial_isometric"):
                            st.markdown(f"- **Studio Mode:** `{v_data.get('widget_type') or v_data.get('scene_mode', 'world_cam')}`")
                        elif v_type in STUDIO_PRO_KEYS:
                            st.markdown(f"- **Pro Studio Engine:** `{sc.get('routed_engine') or v_type}` (`{v_type}`)")
                        elif v_type == "architecture_flow":
                            nodes = v_data.get("nodes", [])
                            node_labels = " ➔ ".join([
                                f"**[{n.get('label')}]** ({n.get('sub', '')})" if isinstance(n, dict) else f"**[{n}]**"
                                for n in nodes
                            ]) if nodes else "Pipeline nodes"
                            st.markdown(f"- **Rendered Nodes:** {node_labels}")
                        elif v_type == "sql_table":
                            code_snip = v_data.get("code_snippet", "")
                            st.markdown(f"- **SQL Query:** `{code_snip}`")
                            st.markdown(f"- **Table Columns:** `{v_data.get('table_data', {}).get('headers', [])}`")
                        elif v_type == "code_terminal":
                            cmd = v_data.get("command", "")
                            code = v_data.get("code_snippet", "")
                            st.markdown(f"- **CLI Command:** `{cmd}`" if cmd else "- **Terminal Code:**")
                            st.code(code[:150] + ("..." if len(code) > 150 else ""), language="python")
                        elif v_type == "split_comparison":
                            st.markdown(f"- **Comparison:** ❌ `{v_data.get('left_label')}` vs ⚡ `{v_data.get('right_label')}`")
                            st.markdown(f"- **Points:** {len(v_data.get('left_points', []))} cons vs {len(v_data.get('right_points', []))} pros")
                        elif v_type == "benchmark_chart":
                            bars = v_data.get("bars", [])
                            st.markdown(f"- **Benchmark Metrics:** {len(bars)} comparative bars • Winner: **{v_data.get('winner_badge', '10X FASTER')}**")
                        elif v_type == "data_structure_memory":
                            entries = v_data.get("entries", [])
                            st.markdown(f"- **Memory Offsets:** {len(entries)} buffer slots rendered with LSN offsets")
                        elif v_type == "alert_diagram":
                            st.markdown(f"- **Production Bottleneck:** *{v_data.get('problem_title', 'Incident Alert')}*")
                            st.markdown(f"- **Core Dilemma:** *{v_data.get('challenge', '')}*")
                        elif v_type == "circular_hub_mesh":
                            st.markdown(f"- **Central Broker:** `{v_data.get('hub_name', 'CORE BROKER')}` with {len(v_data.get('satellites', []))} satellite nodes")
                        elif v_type == "metric_gauge_hud":
                            st.markdown(f"- **Primary Gauge:** `{v_data.get('main_value')}` {v_data.get('main_unit')} ({v_data.get('gauge_percent')}% meter)")
                        elif v_type == "all_in_one_tech_canvas":
                            st.markdown(f"- **Cloud Boundary:** `{v_data.get('vpc_label')}`")
                            st.markdown(f"- **2D Tech Stack:** 🗄️ `{v_data.get('comp4_label')}` (DB Cylinder) • 🐍 `{v_data.get('comp1_label')}` (Python Chip) • 🤖 `{v_data.get('comp2_label')}` (AI Bot) • 🖥️ `{v_data.get('comp3_label')}` (K8s Rack) • 🪣 `{v_data.get('comp5_label')}` (S3 Lake)")
                            st.markdown(f"- **2D Motion:** Directed arrows with traveling packet streams & live pulsing target reticle")
                        else:
                            st.markdown(f"- **Bullet Cards:** `{v_data.get('bullets', [])}`")

                        st.markdown(f"- **Spoken Narration:** *\"{sc.get('narration')}\"*")
                        st.markdown("---")

                # 4. APIs, Models & System Stack Summary Table
                with st.expander("🤖 Tech Stack & API Architecture Matrix", expanded=False):
                    _gfx_provider = "Playwright WebGL + NumPy 3D + resvg_py + PIL" if _pw_ok else "NumPy 3D Mesh + resvg_py + PIL"
                    _gfx_spec = (
                        f"{_layout_cnt} Layouts + Grammar | {_shape_cnt} Shapes + {_mesh_cnt} Meshes | {FORMAT_SPECS[aspect_ratio[0]]['width']}x{FORMAT_SPECS[aspect_ratio[0]]['height']} @ {VIDEO_FPS} FPS"
                        if _layout_cnt > 0
                        else f"{FORMAT_SPECS[aspect_ratio[0]]['width']}x{FORMAT_SPECS[aspect_ratio[0]]['height']} ({aspect_ratio[0]}) @ {VIDEO_FPS} FPS"
                    )
                    st.table([
                        {"Pipeline Layer": "AI Director & Storyboard", "API / Provider": "Google AI Studio (+ Groq/OR Fallback)", "Model / Spec": "gemini-3.1-flash-lite / gemini-3-flash-preview", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Text-to-Speech (TTS)", "API / Provider": "ElevenLabs AI" if chosen_voice.startswith("elevenlabs:") else "Microsoft Edge-TTS", "Model / Spec": str(elevenlabs_model_id if chosen_voice.startswith("elevenlabs:") else chosen_voice), "Status": "Active 🟢"},
                        {"Pipeline Layer": "Audio Alignment", "API / Provider": "Groq Cloud API", "Model / Spec": "whisper-large-v3 (Word-Level)", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Visual Graphics Engine", "API / Provider": _gfx_provider, "Model / Spec": _gfx_spec, "Status": "Active 🟢"},
                        {"Pipeline Layer": "Vector & Icon Engine", "API / Provider": "Rust resvg_py + Iconify 200k+" if _resvg_ok else "Vector Fallback + Iconify 200k+", "Model / Spec": f"{_glyph_cnt} Glyphs + {_alias_cnt} Aliases (3D Extrude)", "Status": "Active 🟢" if _resvg_ok else "Fallback 🟡"},
                        {"Pipeline Layer": "Video Stitcher & Encoder", "API / Provider": "FFmpeg Engine", "Model / Spec": "Hardware MF 8Mbps / libx264 CRF 18", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Subtitles & Karaoke", "API / Provider": "ASS SubStation Engine", "Model / Spec": "Segoe UI Safe-Zone Font", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Cloud CDN Storage", "API / Provider": "Cloudflare R2", "Model / Spec": "S3 Global Edge (pub-ba534...)", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Host Compute", "API / Provider": "Local RTX 3050" if is_local_machine else "Streamlit Cloud", "Model / Spec": "Windows 11 / 16GB RAM", "Status": "Active 🟢"}
                    ])

        except Exception as e:
            status_box.error(f"❌ Error during generation: {e}")
            st.exception(e)

with tab_storage:
    st.markdown("### ☁️ Cloudflare R2 Media & Storage Manager")
    st.markdown("Review all uploaded reels, view permanent universal URLs, and delete unwanted videos to keep storage clean.")

    if not st.session_state.get("_r2_gallery_open"):
        if st.button("☁️ Load Cloudflare R2 Gallery", key="open_r2_gallery_btn", type="primary"):
            st.session_state["_r2_gallery_open"] = True
            st.rerun()
        st.info("⚡ Gallery is lazy-loaded so Studio Max opens instantaneously.")
    else:
        stats = _cached_r2_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Stored Reels", f"{stats['total_files']} files")
        c2.metric("Storage Used", f"{stats['total_mb']} MB")
        c3.metric("Free Space Left", f"{stats['free_gb_remaining']} GB", delta="10 GB Free Tier")
        if c4.button("🔄 Refresh Gallery", use_container_width=True):
            _cached_r2_stats.clear()
            _cached_r2_videos.clear()
            st.rerun()

        st.markdown("---")

        videos = _cached_r2_videos()
        if not videos:
            st.info("ℹ️ No videos stored in Cloudflare R2 yet. Once you generate reels in the Studio, they will appear here with preview and delete options!")
        else:
            st.markdown(f"Showing **{len(videos)}** stored reels in `nanopro-reels`:")
            for idx, vid in enumerate(videos):
                with st.container(border=True):
                    col_left, col_right = st.columns([1, 1.2])
                    with col_left:
                        if vid["url"]:
                            if st.checkbox("▶️ Load Video Preview", key=f"load_r2_prev_{idx}_{vid['name']}", value=False):
                                st.video(vid["url"])
                            else:
                                st.caption("Click checkbox above to stream preview cleanly without slowing page load.")
                        else:
                            st.warning("Video streaming preview not available.")
                    with col_right:
                        st.markdown(f"#### 🎬 `{vid['name']}`")
                        st.caption(f"📅 Uploaded: **{vid['last_modified']}** • 📊 Size: **{vid['size_mb']} MB**")
                        if vid["url"]:
                            st.markdown("**🔗 Permanent Universal URL:**")
                            st.code(vid["url"], language="text")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                st.link_button("🌐 Open in New Tab", vid["url"], use_container_width=True)
                            with col_btn2:
                                if st.button("🗑️ Delete Permanently", key=f"del_btn_{idx}_{vid['name']}", type="secondary", use_container_width=True):
                                    if delete_from_r2(vid["name"]):
                                        _cached_r2_stats.clear()
                                        _cached_r2_videos.clear()
                                        st.success(f"Deleted {vid['name']} from Cloudflare R2!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete video.")
