import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, OUTPUT_DIR, FONTS_DIR, FORMAT_SPECS, DEFAULT_WATERMARK

# Premium Cyber-Tech Color Palette
COLOR_BG_DARK = (11, 15, 25)
CARD_BG = (17, 24, 39, 235)
CARD_BG_ALT = (15, 23, 42, 245)
CARD_BORDER = (51, 65, 85, 200)

NEON_CYAN = (56, 189, 248)       # #38BDF8
NEON_PURPLE = (168, 85, 247)     # #A855F7
NEON_EMERALD = (52, 211, 153)    # #34D399
NEON_AMBER = (251, 191, 36)      # #FBBF24
NEON_ROSE = (244, 63, 94)        # #F43F5E

TEXT_PRIMARY = (248, 250, 252)   # Crisp White
TEXT_MUTED = (148, 163, 184)     # Modern Slate Muted
TEXT_DIM = (100, 116, 139)       # Dim Slate

ACCENT_THEMES = {
    "cyber_cyan": {"primary": (56, 189, 248), "secondary": (168, 85, 247), "bg": (11, 15, 25)},
    "indigo_cyan": {"primary": (99, 102, 241), "secondary": (56, 189, 248), "bg": (12, 14, 30)},
    "emerald_matrix": {"primary": (52, 211, 153), "secondary": (56, 189, 248), "bg": (9, 20, 22)},
    "gold_purple": {"primary": (251, 191, 36), "secondary": (168, 85, 247), "bg": (16, 14, 26)},
    "crimson_alert": {"primary": (244, 63, 94), "secondary": (251, 191, 36), "bg": (20, 12, 20)},
}


TONE_THEME_MAP = {
    "mentor_storyteller": "emerald_matrix",
    "fireship_octane": "cyber_cyan",
    "dramatic_performance": "crimson_alert",
    "staff_engineer": "indigo_cyan",
    "conversational_casual": "emerald_matrix",
    "interview_prep": "gold_purple",
}

# Active visual palette for the current frame (supports distinct light/dark/blueprint/editorial worlds)
_ACTIVE_PAL: Dict[str, Any] = {
    "art_style": "editorial_dark",
    "is_light": False,
    "bg": (16, 17, 21),
    "card_bg": (24, 26, 32, 245),
    "card_alt": (30, 34, 42, 248),
    "card_border": (55, 65, 81, 220),
    "text": TEXT_PRIMARY,
    "muted": TEXT_MUTED,
    "dim": TEXT_DIM,
    "cyan": NEON_CYAN,
    "purple": NEON_PURPLE,
    "emerald": NEON_EMERALD,
    "amber": NEON_AMBER,
    "rose": NEON_ROSE,
    "accent": NEON_CYAN,
    "warn_bg": (38, 25, 14, 245),
    "rose_bg": (32, 16, 22, 245),
    "emerald_bg": (13, 32, 28, 245),
    "cyan_bg": (14, 30, 44, 245),
}


def _set_active_palette(art_style: str, theme_cfg: Dict[str, Tuple[int, int, int]]) -> Dict[str, Any]:
    """Sets high-contrast colors for the active visual art style."""
    style = str(art_style or "editorial_dark").lower().strip()
    accent = theme_cfg.get("primary", NEON_CYAN)
    if style == "light_whiteboard":
        _ACTIVE_PAL.update({
            "art_style": "light_whiteboard",
            "is_light": True,
            "bg": (246, 248, 252),
            "card_bg": (255, 255, 255, 248),
            "card_alt": (241, 245, 249, 250),
            "card_border": (203, 213, 225, 255),
            "text": (15, 23, 42),
            "muted": (71, 85, 105),
            "dim": (100, 116, 139),
            "cyan": (2, 132, 199),
            "purple": (126, 34, 206),
            "emerald": (5, 150, 105),
            "amber": (217, 119, 6),
            "rose": (225, 29, 72),
            "accent": (2, 132, 199),
            "warn_bg": (254, 243, 199, 250),
            "rose_bg": (255, 228, 230, 250),
            "emerald_bg": (209, 250, 229, 250),
            "cyan_bg": (224, 242, 254, 250),
        })
    elif style == "blueprint_grid":
        _ACTIVE_PAL.update({
            "art_style": "blueprint_grid",
            "is_light": False,
            "bg": (9, 21, 41),
            "card_bg": (13, 30, 56, 244),
            "card_alt": (17, 38, 68, 248),
            "card_border": (56, 189, 248, 120),
            "text": (248, 250, 252),
            "muted": (148, 163, 184),
            "dim": (100, 116, 139),
            "cyan": (56, 189, 248),
            "purple": (168, 85, 247),
            "emerald": (52, 211, 153),
            "amber": (251, 191, 36),
            "rose": (244, 63, 94),
            "accent": accent,
            "warn_bg": (36, 26, 14, 245),
            "rose_bg": (34, 16, 24, 245),
            "emerald_bg": (11, 30, 32, 245),
            "cyan_bg": (12, 34, 60, 245),
        })
    elif style == "editorial_dark":
        _ACTIVE_PAL.update({
            "art_style": "editorial_dark",
            "is_light": False,
            "bg": (16, 17, 21),
            "card_bg": (24, 26, 32, 248),
            "card_alt": (31, 34, 42, 248),
            "card_border": (63, 68, 82, 220),
            "text": (248, 250, 252),
            "muted": (161, 168, 182),
            "dim": (113, 118, 130),
            "cyan": NEON_CYAN,
            "purple": NEON_PURPLE,
            "emerald": NEON_EMERALD,
            "amber": NEON_AMBER,
            "rose": NEON_ROSE,
            "accent": accent,
            "warn_bg": (38, 26, 14, 245),
            "rose_bg": (34, 16, 22, 245),
            "emerald_bg": (13, 32, 28, 245),
            "cyan_bg": (15, 30, 44, 245),
        })
    else:  # neon_fireship
        _ACTIVE_PAL.update({
            "art_style": "neon_fireship",
            "is_light": False,
            "bg": theme_cfg.get("bg", COLOR_BG_DARK),
            "card_bg": CARD_BG,
            "card_alt": CARD_BG_ALT,
            "card_border": CARD_BORDER,
            "text": TEXT_PRIMARY,
            "muted": TEXT_MUTED,
            "dim": TEXT_DIM,
            "cyan": NEON_CYAN,
            "purple": NEON_PURPLE,
            "emerald": NEON_EMERALD,
            "amber": NEON_AMBER,
            "rose": NEON_ROSE,
            "accent": accent,
            "warn_bg": (38, 24, 12, 245),
            "rose_bg": (28, 15, 22, 245),
            "emerald_bg": (11, 28, 26, 245),
            "cyan_bg": (12, 32, 48, 245),
        })
    return _ACTIVE_PAL


def _pal_color_name(name: str, fallback: Tuple[int, int, int] = None) -> Tuple[int, int, int]:
    """Maps symbolic color names ('cyan', 'amber', 'emerald', 'purple', 'rose') or hex to active palette RGB."""
    raw = str(name or "").strip()
    if raw.startswith("#"):
        return _hex_to_rgb(raw)
    k = raw.lower()
    if k in ("cyan", "blue", "primary", "info"):
        return _ACTIVE_PAL["cyan"]
    if k in ("purple", "violet"):
        return _ACTIVE_PAL["purple"]
    if k in ("emerald", "green", "success"):
        return _ACTIVE_PAL["emerald"]
    if k in ("amber", "yellow", "gold", "warn", "warning"):
        return _ACTIVE_PAL["amber"]
    if k in ("rose", "red", "danger", "alert"):
        return _ACTIVE_PAL["rose"]
    return fallback or _ACTIVE_PAL["accent"]


def _build_themed_canvas(
    canvas_w: int,
    canvas_h: int,
    theme_name: str = "cyber_cyan",
    effective_tone: str = "conversational_casual",
    art_style: str = "editorial_dark",
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Builds a visually distinct canvas world (light_whiteboard, editorial_dark, blueprint_grid, neon_fireship)."""
    theme = dict(ACCENT_THEMES.get(str(theme_name).lower().strip(), ACCENT_THEMES["cyber_cyan"]))
    style = str(art_style or "editorial_dark").lower().strip()
    pal = _set_active_palette(style, theme)
    theme["bg"] = pal["bg"]
    p = pal["accent"]
    s = theme["secondary"]
    base = Image.new("RGB", (canvas_w, canvas_h), pal["bg"])
    gdraw = ImageDraw.Draw(base, "RGBA")

    if style == "light_whiteboard":
        # Clean Excalidraw/editorial off-white dot paper + crisp subtle top rule
        dot_col = (148, 163, 184, 70)
        for gx in range(36, canvas_w, 48):
            for gy in range(36, canvas_h, 48):
                gdraw.ellipse((gx - 1, gy - 1, gx + 1, gy + 1), fill=dot_col)
    elif style == "editorial_dark":
        # Minimal matte charcoal: clean subtle horizontal margin rules only (NO neon glow blob!)
        rule_col = (255, 255, 255, 10)
        gdraw.line((64, 345, canvas_w - 64, 345), fill=rule_col, width=1)
        gdraw.line((64, canvas_h - 110, canvas_w - 64, canvas_h - 110), fill=rule_col, width=1)
    elif style == "blueprint_grid":
        # Crisp CAD blueprint engineering grid + corner registration ticks
        grid_col = (56, 189, 248, 20)
        step = 72
        for gx in range(0, canvas_w, step):
            gdraw.line((gx, 0, gx, canvas_h), fill=grid_col, width=1)
        for gy in range(0, canvas_h, step):
            gdraw.line((0, gy, canvas_w, gy), fill=grid_col, width=1)
        tick = (56, 189, 248, 90)
        gdraw.line((36, 70, 76, 70), fill=tick, width=2)
        gdraw.line((36, 70, 36, 110), fill=tick, width=2)
        gdraw.line((canvas_w - 76, canvas_h - 70, canvas_w - 36, canvas_h - 70), fill=tick, width=2)
        gdraw.line((canvas_w - 36, canvas_h - 110, canvas_w - 36, canvas_h - 70), fill=tick, width=2)
    else:
        # neon_fireship: kinetic cyber streaks / spotlight based on tone
        if effective_tone == "fireship_octane":
            streak_col = (p[0], p[1], p[2], 18)
            for offset in range(-canvas_h, canvas_w + canvas_h, 130):
                gdraw.line((offset, 0, offset - 380, canvas_h), fill=streak_col, width=2)
        elif effective_tone == "dramatic_performance":
            gdraw.ellipse((canvas_w // 2 - 480, 120, canvas_w // 2 + 480, 950), fill=(p[0], p[1], p[2], 20))
            gdraw.ellipse((canvas_w // 2 - 360, 750, canvas_w // 2 + 360, 1550), fill=(s[0], s[1], s[2], 14))
        else:
            grid_col = (p[0], p[1], p[2], 14)
            step = 90
            for gx in range(0, canvas_w, step):
                gdraw.line((gx, 0, gx, canvas_h), fill=grid_col, width=1)
            for gy in range(0, canvas_h, step):
                gdraw.line((0, gy, canvas_w, gy), fill=grid_col, width=1)
        gdraw.ellipse((canvas_w // 2 - 360, -140, canvas_w // 2 + 360, 420), fill=(p[0], p[1], p[2], 16))
    return base, theme

def get_font(size: int = 40, bold: bool = False) -> ImageFont.ImageFont:
    """Returns a clean Truetype font across Windows (Local) and Linux (Streamlit Cloud)."""
    font_names = [
        "segoeui.ttf",
        "arial.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    if bold:
        font_names = [
            "segoeuib.ttf",
            "arialbd.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ] + font_names
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def draw_wrapped_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    max_width: int,
    fill: Tuple[int, ...],
    line_spacing: int = 8,
    align: str = "left",
    max_lines: int = 2,
    ellipsis: bool = True
) -> int:
    """Renders multi-line text strictly constrained to max_width."""
    if not text:
        return 0

    words = text.strip().split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if ellipsis and lines:
            last = lines[-1]
            while last and (font.getbbox(last + "...")[2] - font.getbbox(last + "...")[0]) > max_width:
                last = last[:-1]
            lines[-1] = last.rstrip() + "..."

    cur_y = y
    for line in lines:
        bbox = font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]

        if align == "center":
            lx = x + (max_width - lw) // 2
        elif align == "right":
            lx = x + (max_width - lw)
        else:
            lx = x

        draw.text((lx, cur_y), line, fill=fill, font=font)
        cur_y += lh + line_spacing

    return cur_y - y

def _stage_reveal(progress: float, start_p: float, end_p: float) -> float:
    """Returns smooth 0.0 -> 1.0 reveal factor for a given [start_p, end_p] window."""
    if progress <= start_p:
        return 0.0
    if progress >= end_p:
        return 1.0
    t = (progress - start_p) / max(1e-5, end_p - start_p)
    # Smooth ease-out cubic
    return 1.0 - pow(1.0 - t, 3)


def _build_choreography_anchors(
    duration: float,
    scene: Dict[str, Any],
    scene_words: List[Dict[str, Any]] = None
) -> List[Tuple[float, float]]:
    """
    Maps AI-selected choreography trigger keywords onto exact Whisper spoken word timestamps,
    returning monotonic (time_frac, stage_progress) anchor pairs for Audio-Visual Sync.
    """
    if not scene_words:
        return [(0.0, 0.0), (1.0, 1.0)]

    choreo = scene.get("choreography", {})
    triggers = choreo.get("triggers", []) if isinstance(choreo, dict) else []
    if not triggers:
        return [(0.0, 0.0), (1.0, 1.0)]

    sc_start = float(scene.get("start_time", 0.0))
    clean_words = []
    for w in scene_words:
        txt = "".join(ch for ch in str(w.get("word", "")).lower() if ch.isalnum() or "\u0900" <= ch <= "\u097f")
        clean_words.append((txt, float(w.get("start", sc_start))))

    anchors = [(0.0, 0.0)]
    target_stages = [0.08, 0.30, 0.56, 0.78]
    word_cursor = 0
    prev_t = 0.0

    for idx, trig in enumerate(triggers[:4]):
        kw = str(trig.get("keyword", "")).lower().strip()
        kw_clean = "".join(ch for ch in kw if ch.isalnum() or "\u0900" <= ch <= "\u097f")
        if not kw_clean:
            continue
        matched_t = None
        for w_idx in range(word_cursor, len(clean_words)):
            w_txt, w_start = clean_words[w_idx]
            if kw_clean in w_txt or w_txt in kw_clean:
                matched_t = (w_start - sc_start) / max(0.5, duration)
                word_cursor = w_idx + 1
                break
        if matched_t is not None:
            t_clamped = max(prev_t + 0.06, min(0.90, matched_t))
            prev_t = t_clamped
            stage_p = target_stages[idx]
            anchors.append((t_clamped, stage_p))

    anchors.append((1.0, 1.0))
    return anchors


def _compute_voice_synced_progress(
    frame_idx: int,
    total_frames: int,
    duration: float,
    scene: Dict[str, Any],
    scene_words: List[Dict[str, Any]] = None,
    anchors: List[Tuple[float, float]] = None
) -> float:
    """
    Computes frame progress (0.0 -> 1.0) anchored to Whisper word timestamps and
    AI choreography triggers for true Voice-Driven Progressive Reveal & Node-Edge Traversal.
    """
    linear_p = frame_idx / max(1, total_frames - 1)
    if not scene_words:
        return linear_p

    # Piecewise-linear interpolation along matched spoken keyword anchors
    choreo_p = linear_p
    if anchors and len(anchors) >= 3:
        for i in range(len(anchors) - 1):
            t0, p0 = anchors[i]
            t1, p1 = anchors[i + 1]
            if t0 <= linear_p <= t1:
                span = max(1e-5, t1 - t0)
                choreo_p = p0 + ((linear_p - t0) / span) * (p1 - p0)
                break

    sc_start = float(scene.get("start_time", 0.0))
    cur_time = sc_start + (linear_p * duration)
    spoken_count = sum(1 for w in scene_words if float(w.get("start", 0.0)) <= cur_time)
    word_p = spoken_count / max(1, len(scene_words))
    return min(1.0, max(0.0, 0.55 * choreo_p + 0.30 * word_p + 0.15 * linear_p))


def render_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    total_scenes: int = 4,
    engine_style: str = "hybrid_modern",
    format_ratio: str = "9:16",
    watermark: str = DEFAULT_WATERMARK,
    scene_words: List[Dict[str, Any]] = None,
    custom_style_prompt: str = "",
    tone: str = "auto_dynamic"
) -> List[Path]:
    """
    Renders high-octane 2D frames across 12+ rich motion-graphics visual engines,
    adapting layout, texture, pacing, and accents to BOTH Visual Engine & Script Tone.
    """
    duration = max(1.5, float(scene.get("duration", 5.0)))
    total_frames = max(15, round(duration * VIDEO_FPS))

    if engine_style == "cinematic_studio":
        from core.cinematic_engine import render_cinematic_scene_frames
        return render_cinematic_scene_frames(
            scene=scene,
            scene_idx=scene_idx,
            total_scenes=total_scenes,
            format_ratio=format_ratio,
            watermark=watermark,
            scene_words=scene_words,
            tone=tone,
        )

    scene_frames_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    if scene_frames_dir.exists():
        for old_f in scene_frames_dir.glob("frame_*.*"):
            try:
                old_f.unlink()
            except Exception:
                pass
    scene_frames_dir.mkdir(parents=True, exist_ok=True)
    
    visual_type = scene.get("visual_type", "concept_cards")
    visual_data = scene.get("visual_data", {})

    # Strict Visual Engine enforcement matching the user's selected dropdown choice
    if engine_style == "all_in_one_tech_canvas":
        visual_type = "all_in_one_tech_canvas"
    elif engine_style == "terminal_screencast" and visual_type != "code_terminal":
        visual_type = "code_terminal"
    elif engine_style == "sql_deepdive" and visual_type != "sql_table":
        visual_type = "sql_table"
    elif engine_style == "bytebytego_dsl" and visual_type not in ["architecture_flow", "circular_hub_mesh"]:
        visual_type = "architecture_flow"
    elif engine_style == "split_comparison" and visual_type != "split_comparison":
        visual_type = "split_comparison"
    elif engine_style == "benchmark_speed" and visual_type not in ["benchmark_chart", "metric_gauge_hud"]:
        visual_type = "benchmark_chart"
    elif engine_style == "memory_internals" and visual_type != "data_structure_memory":
        visual_type = "data_structure_memory"
    elif engine_style == "network_mesh" and visual_type != "circular_hub_mesh":
        visual_type = "circular_hub_mesh"
    elif engine_style == "telemetry_hud" and visual_type != "metric_gauge_hud":
        visual_type = "metric_gauge_hud"
    elif engine_style == "alert_troubleshoot" and visual_type != "alert_diagram":
        visual_type = "alert_diagram"
    elif engine_style == "concept_keynote" and visual_type != "concept_cards":
        visual_type = "concept_cards"

    frame_paths = []
    
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    canvas_w = spec.get("width", VIDEO_WIDTH)
    canvas_h = spec.get("height", VIDEO_HEIGHT)
    effective_tone = (scene.get("scene_tone") or "conversational_casual") if tone == "auto_dynamic" else tone
    art_style = str(visual_data.get("art_style") or scene.get("art_style") or "editorial_dark").lower().strip()
    theme_cycle = ["indigo_cyan", "cyber_cyan", "emerald_matrix", "gold_purple", "crimson_alert"]
    tone_default_theme = TONE_THEME_MAP.get(effective_tone, theme_cycle[(scene_idx - 1) % len(theme_cycle)])
    chosen_theme = visual_data.get("accent_theme") or tone_default_theme
    base_canvas, theme_cfg = _build_themed_canvas(
        canvas_w,
        canvas_h,
        chosen_theme,
        effective_tone=effective_tone,
        art_style=art_style,
    )
    accent_col = _ACTIVE_PAL["accent"]
    needs_aspect_fit = (canvas_w != VIDEO_WIDTH or canvas_h != VIDEO_HEIGHT)
    anchors = _build_choreography_anchors(duration, scene, scene_words)
    header_badge = visual_data.get("badge", "")
    header_title = visual_data.get("title", "")

    for f in range(total_frames):
        linear_p = f / max(1, total_frames - 1)
        raw_p = _compute_voice_synced_progress(f, total_frames, duration, scene, scene_words, anchors=anchors)
        # Tone-matched reveal snap: Fireship snaps faster, Dramatic eases in with suspense
        if effective_tone == "fireship_octane":
            progress = min(1.0, raw_p * 1.12)
        elif effective_tone == "dramatic_performance":
            progress = pow(raw_p, 1.08)
        else:
            progress = raw_p
        frame = base_canvas.copy()

        if needs_aspect_fit:
            # Render scene content on virtual 1080x1500 content stage, then fit cleanly onto 16:9 or 1:1
            stage = Image.new("RGBA", (VIDEO_WIDTH, 1500), (*theme_cfg["bg"], 0))
            s_draw = ImageDraw.Draw(stage, "RGBA")
            _draw_header(s_draw, header_badge, header_title, accent=accent_col, art_style=art_style)
            _dispatch_visual_renderer(s_draw, visual_type, visual_data, progress)

            # Scale stage cleanly to fit inside canvas_w x (canvas_h - 140) leaving room for top bar & subtitles
            avail_h = canvas_h - 140
            avail_w = canvas_w - 80
            scale = min(avail_w / VIDEO_WIDTH, avail_h / 1420.0)
            new_w = max(100, int(VIDEO_WIDTH * scale))
            new_h = max(100, int(1500 * scale))
            resized_stage = stage.resize((new_w, new_h), Image.Resampling.LANCZOS)
            paste_x = (canvas_w - new_w) // 2
            paste_y = 45
            frame_rgba = frame.convert("RGBA")
            frame_rgba.alpha_composite(resized_stage, (paste_x, paste_y))
            frame = frame_rgba.convert("RGB")
            draw = ImageDraw.Draw(frame, "RGBA")
        else:
            draw = ImageDraw.Draw(frame, "RGBA")
            _draw_header(draw, header_badge, header_title, accent=accent_col, art_style=art_style)
            _dispatch_visual_renderer(draw, visual_type, visual_data, progress)

        # Top Story Progress Bar & Watermark always crisp at native canvas resolution
        _draw_story_progress_bar(draw, total_scenes, scene_idx, linear_p, canvas_w=canvas_w, accent=accent_col)
        if watermark:
            _draw_watermark(draw, canvas_w, canvas_h, watermark)
            
        # Save lossless/high-fidelity crystal clear frame
        frame_file = scene_frames_dir / f"frame_{f:04d}.jpg"
        frame.convert("RGB").save(frame_file, "JPEG", quality=96, subsampling=0)
        frame_paths.append(frame_file)
        
    return frame_paths


def _dispatch_visual_renderer(draw: ImageDraw.Draw, visual_type: str, visual_data: Dict[str, Any], progress: float) -> None:
    aliases = {
        "custom": "custom_scene",
        "modular": "custom_scene",
        "dynamic_canvas": "custom_scene",
        "service_topology": "architecture_flow",
        "topology": "architecture_flow",
        "pipeline": "architecture_flow",
        "pipeline_flow": "architecture_flow",
        "data_flow": "architecture_flow",
        "memory_buffer": "data_structure_memory",
        "memory_internals": "data_structure_memory",
        "wal_log": "data_structure_memory",
        "buffer": "data_structure_memory",
        "terminal": "code_terminal",
        "cli": "code_terminal",
        "code": "code_terminal",
        "comparison": "split_comparison",
        "trade_off": "split_comparison",
        "chart": "benchmark_chart",
        "benchmark": "benchmark_chart",
        "mesh": "circular_hub_mesh",
        "hub_spoke": "circular_hub_mesh",
        "gauge": "metric_gauge_hud",
        "metrics": "metric_gauge_hud",
        "kpi": "metric_gauge_hud",
        "alert": "alert_diagram",
        "incident": "alert_diagram",
        "bottleneck": "alert_diagram",
        "sql": "sql_table",
        "question_hook": "hero_hook",
        "hook_card": "hero_hook",
        "interview_hook": "hero_hook",
        "hero": "hero_hook",
        "merge_diagram": "hybrid_merge",
        "combination_diagram": "hybrid_merge",
        "hybrid_architecture": "hybrid_merge",
        "hybrid_approach": "hybrid_merge",
        "kinetic": "kinetic_statement",
        "statement": "kinetic_statement",
        "callout": "kinetic_statement",
        "timeline": "step_timeline",
        "steps": "step_timeline",
        "step_flow": "step_timeline",
    }
    vt = aliases.get(str(visual_type).lower().strip(), visual_type)
    if vt == "custom_scene":
        _render_custom_scene(draw, visual_data, progress)
    elif vt == "hero_hook":
        _render_hero_hook(draw, visual_data, progress)
    elif vt == "hybrid_merge":
        _render_hybrid_merge(draw, visual_data, progress)
    elif vt == "kinetic_statement":
        _render_kinetic_statement(draw, visual_data, progress)
    elif vt == "step_timeline":
        _render_step_timeline(draw, visual_data, progress)
    elif vt == "split_comparison":
        _render_split_comparison(draw, visual_data, progress)
    elif vt == "benchmark_chart":
        _render_benchmark_chart(draw, visual_data, progress)
    elif vt == "circular_hub_mesh":
        _render_circular_hub_mesh(draw, visual_data, progress)
    elif vt == "metric_gauge_hud":
        _render_metric_gauge_hud(draw, visual_data, progress)
    elif vt == "data_structure_memory":
        _render_data_structure_memory(draw, visual_data, progress)
    elif vt == "sql_table":
        _render_sql_table(draw, visual_data, progress)
    elif vt == "code_terminal":
        _render_code_terminal(draw, visual_data, progress)
    elif vt == "alert_diagram":
        _render_alert_diagram(draw, visual_data, progress)
    elif vt == "architecture_flow":
        _render_architecture_flow(draw, visual_data, progress)
    elif vt == "all_in_one_tech_canvas":
        _render_all_in_one_tech_canvas(draw, visual_data, progress)
    else:
        _render_concept_cards(draw, visual_data, progress)


def _draw_story_progress_bar(draw: ImageDraw.Draw, total_scenes: int, current_scene: int, progress: float, canvas_w: int = VIDEO_WIDTH, accent: Tuple[int, int, int] = NEON_CYAN) -> None:
    """Draws a continuous sleek progress bar across the entire video matching light/dark theme."""
    global_progress = ((current_scene - 1) + progress) / max(1, total_scenes)
    bar_y = 25
    bar_h = 6
    padding = 40
    track_w = canvas_w - (padding * 2)
    fill_w = max(10, int(track_w * min(1.0, max(0.01, global_progress))))
    track_col = (15, 23, 42, 32) if _ACTIVE_PAL.get("is_light") else (255, 255, 255, 35)

    draw.rounded_rectangle((padding, bar_y, padding + track_w, bar_y + bar_h), radius=3, fill=track_col)
    draw.rounded_rectangle((padding, bar_y, padding + fill_w, bar_y + bar_h), radius=3, fill=accent)


def _draw_header(
    draw: ImageDraw.Draw,
    badge_text: str,
    title_text: str,
    accent: Tuple[int, int, int] = NEON_CYAN,
    art_style: str = "",
) -> None:
    """Draws header typography cleanly adapted to each art_style so every reel doesn't look identical."""
    style = str(art_style or _ACTIVE_PAL.get("art_style", "editorial_dark")).lower().strip()
    pal = _ACTIVE_PAL
    text_col = pal["text"]
    muted_col = pal["muted"]
    font_badge = get_font(25, bold=True)
    font_title = get_font(44, bold=True)
    badge_str = str(badge_text or "").upper().strip()

    if style in ("light_whiteboard", "editorial_dark"):
        # Left-aligned modern editorial hierarchy (accent stripe + kicker + bold title — NO neon pill capsule!)
        lx = 70
        y_cur = 104
        if badge_str:
            draw.rounded_rectangle((lx, y_cur + 4, lx + 8, y_cur + 28), radius=4, fill=accent)
            draw.text((lx + 22, y_cur), badge_str, fill=accent, font=font_badge)
            y_cur += 46
        if title_text:
            draw_wrapped_text(draw, str(title_text), font_title, lx, y_cur, 930, text_col, line_spacing=8, align="left", max_lines=2)
    elif style == "blueprint_grid":
        # Engineering bracket header [ SECTION_TAG ] + hairline + title
        lx = 68
        y_cur = 106
        if badge_str:
            tag_txt = f"[ {badge_str} ]"
            tb = font_badge.getbbox(tag_txt)
            draw.text((lx, y_cur), tag_txt, fill=accent, font=font_badge)
            rule_x = min(980, lx + (tb[2] - tb[0]) + 18)
            if rule_x < 990:
                draw.line((rule_x, y_cur + 15, VIDEO_WIDTH - 68, y_cur + 15), fill=(accent[0], accent[1], accent[2], 90), width=2)
            y_cur += 46
        if title_text:
            draw_wrapped_text(draw, str(title_text), font_title, lx, y_cur, 940, text_col, line_spacing=8, align="left", max_lines=2)
    else:
        # neon_fireship: centered glowing pill badge + centered punchy title
        by = 112
        if badge_str:
            bbox = font_badge.getbbox(badge_str)
            raw_bw = bbox[2] - bbox[0]
            bw = min(880, raw_bw + 44)
            bh = 50
            bx = (VIDEO_WIDTH - bw) // 2
            draw.rounded_rectangle((bx - 2, by - 2, bx + bw + 2, by + bh + 2), radius=26, fill=(*accent, 45))
            draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=25, fill=(15, 23, 42, 240), outline=accent, width=3)
            tx_badge = bx + (bw - raw_bw) // 2
            draw.text((tx_badge, by + 10), badge_str, fill=accent, font=font_badge)
            title_y = by + 72
        else:
            title_y = by + 18

        if title_text:
            max_title_w = 940
            start_x = (VIDEO_WIDTH - max_title_w) // 2
            draw_wrapped_text(draw, str(title_text), font_title, start_x, title_y, max_title_w, text_col, line_spacing=8, align="center", max_lines=2)


# =========================================================================
# 0. COMPOSABLE CUSTOM SCENE ENGINE (Dynamic Block Assembly — Zero Fixed Templates!)
# =========================================================================
def _synthesize_blocks_fallback(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts structured blocks from legacy visual_data keys if explicit blocks are absent."""
    blocks: List[Dict[str, Any]] = []
    q = data.get("question") or data.get("problem_title")
    if q:
        blocks.append({"block": "question_card", "text": str(q), "stage": 1})
    pills = data.get("pills")
    if isinstance(pills, list) and pills:
        blocks.append({"block": "pills", "items": [str(x) for x in pills[:4]], "mode": "vs" if data.get("show_vs") else "row", "stage": 2})
    elif data.get("left_pill") and data.get("right_pill"):
        blocks.append({"block": "pills", "items": [str(data["left_pill"]), str(data["right_pill"])], "mode": "vs" if data.get("show_vs") else "row", "stage": 2})
    nodes = data.get("nodes") or data.get("steps")
    if isinstance(nodes, list) and nodes:
        node_labels = [n.get("label") or n.get("title") or str(n) if isinstance(n, dict) else str(n) for n in nodes[:4]]
        blocks.append({"block": "flow_chain", "nodes": node_labels, "edges": data.get("edges") or [], "stage": 1 if not q else 2})
    bullets = data.get("bullets") or data.get("points")
    if isinstance(bullets, list) and bullets:
        blocks.append({"block": "list_cards", "items": [str(x) for x in bullets[:4]], "variant": "check", "stage": 1 if not blocks else 2})
    if data.get("statement"):
        blocks.append({"block": "question_card", "text": str(data["statement"]), "stage": 1})
    if data.get("stat_badge"):
        blocks.append({"block": "banner", "text": str(data["stat_badge"]), "tone": "highlight", "stage": 3})
    if data.get("warning_box"):
        blocks.append({"block": "banner", "text": str(data["warning_box"]), "tone": "warn", "stage": 3})
    if data.get("footer_cta") or data.get("cta_text"):
        blocks.append({"block": "banner", "text": str(data.get("footer_cta") or data.get("cta_text")), "tone": "cta", "stage": 4})
    if not blocks:
        title = str(data.get("title") or "Architecture Breakdown")
        blocks.append({"block": "question_card", "text": title, "stage": 1})
    return blocks[:4]


def _estimate_wrapped_lines(text: str, font: ImageFont.ImageFont, max_w: int, max_lines: int = 4) -> int:
    words = str(text or "").split()
    if not words:
        return 1
    lines = 1
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        if (font.getbbox(test)[2] - font.getbbox(test)[0]) <= max_w:
            cur.append(w)
        else:
            if cur:
                lines += 1
                cur = [w]
            else:
                cur = [w]
    return min(max_lines, max(1, lines))


def _render_custom_scene(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """
    Renders dynamically composed visual blocks (big_stat, question_card, pills,
    flow_chain, list_cards, banner, code) with automatic vertical centering and zero overlap.
    """
    pal = _ACTIVE_PAL
    raw_blocks = data.get("blocks")
    blocks = list(raw_blocks[:4]) if isinstance(raw_blocks, list) and raw_blocks else _synthesize_blocks_fallback(data)
    n_blocks = len(blocks)

    avail_top = 365
    avail_bottom = 1405
    avail_h = avail_bottom - avail_top
    only_one = (n_blocks == 1)

    font_q = get_font(38, bold=True)
    font_list = get_font(27, bold=True)
    font_banner = get_font(27, bold=True)

    # Estimate ideal height for every block
    ideal_heights: List[int] = []
    for b in blocks:
        btype = str(b.get("block", "list_cards")).lower().strip()
        if btype == "big_stat":
            ideal_heights.append(190 if only_one else 160)
        elif btype == "question_card":
            ey = str(b.get("eyebrow") or "").strip()
            n_ln = _estimate_wrapped_lines(str(b.get("text", "")), font_q, 830, max_lines=3)
            ideal_heights.append((86 if ey else 56) + n_ln * 50)
        elif btype == "pills":
            items = b.get("items") or []
            mode = str(b.get("mode", "row")).lower().strip()
            rows = math.ceil(min(4, max(1, len(items))) / 2) if (mode == "grid" or len(items) > 3) else 1
            ideal_heights.append(rows * 94 + max(0, rows - 1) * 16)
        elif btype == "flow_chain":
            nodes = b.get("nodes") or []
            cnt = min(4, max(1, len(nodes)))
            nh = 145 if only_one else (92 if cnt <= 3 else 78)
            ag = 78 if only_one else (46 if cnt <= 3 else 36)
            ideal_heights.append(cnt * nh + max(0, cnt - 1) * ag)
        elif btype == "code":
            lines = str(b.get("code", "")).splitlines()[:5]
            ideal_heights.append(72 + max(2, len(lines)) * 46)
        elif btype == "banner":
            n_ln = _estimate_wrapped_lines(str(b.get("text", "")), font_banner, 820, max_lines=2)
            ideal_heights.append(56 + n_ln * 36)
        else:  # list_cards
            items = (b.get("items") or [])[:4]
            cnt = max(1, len(items))
            rh = 155 if only_one else (112 if cnt <= 3 else 94)
            ideal_heights.append(cnt * rh + max(0, cnt - 1) * 14)

    gap = 28 if n_blocks <= 3 else 20
    total_h = sum(ideal_heights) + max(0, n_blocks - 1) * gap
    scale = 1.0
    if total_h > avail_h:
        scale = max(0.74, avail_h / max(1, total_h))
        gap = max(14, int(gap * scale))
    heights = [max(72, int(h * scale)) for h in ideal_heights]
    scaled_total = sum(heights) + max(0, n_blocks - 1) * gap

    y_cur = avail_top + max(0, min(95, (avail_h - scaled_total) // 3))
    cx = 70
    cw = VIDEO_WIDTH - 140

    for idx, (b, bh) in enumerate(zip(blocks, heights)):
        btype = str(b.get("block", "list_cards")).lower().strip()
        stage = int(b.get("stage", idx + 1)) if str(b.get("stage", "")).isdigit() else (idx + 1)
        gate = 0.0 if (idx == 0 or stage <= 1) else min(0.72, (stage - 1) * 0.21)
        if progress < gate:
            y_cur += bh + gap
            continue

        local_p = min(1.0, (progress - gate) / max(0.22, 1.0 - gate))
        col_accent = _pal_color_name(b.get("color", ""), pal["accent"])

        if btype == "big_stat":
            val_str = str(
                b.get("value")
                or b.get("val")
                or b.get("number")
                or b.get("stat")
                or b.get("metric")
                or b.get("headline")
                or b.get("text")
                or ""
            ).strip()
            lbl_str = str(b.get("label") or "").upper().strip()
            draw.rounded_rectangle((cx, y_cur, cx + cw, y_cur + bh), radius=24, fill=pal["card_bg"], outline=col_accent, width=3)
            if val_str:
                font_big = get_font(68 if len(val_str) <= 6 else (50 if len(val_str) <= 14 else 38), bold=True)
                vb = font_big.getbbox(val_str)
                vw = vb[2] - vb[0]
                if vw <= cw - 60:
                    draw.text((cx + (cw - vw) // 2, y_cur + (20 if lbl_str else max(26, (bh - 72) // 2))), val_str, fill=col_accent, font=font_big)
                else:
                    draw_wrapped_text(draw, val_str, get_font(38, bold=True), cx + 30, y_cur + 20, cw - 60, col_accent, align="center", max_lines=2)
                if lbl_str:
                    draw_wrapped_text(draw, lbl_str, get_font(23, bold=True), cx + 30, y_cur + bh - 48, cw - 60, pal["text"], align="center", max_lines=1)
            elif lbl_str:
                draw_wrapped_text(draw, lbl_str, get_font(34, bold=True), cx + 40, y_cur + max(28, (bh - 44) // 2), cw - 80, col_accent, align="center", max_lines=2)

        elif btype == "question_card":
            eyebrow = str(b.get("eyebrow") or "").strip().upper()
            q_text = str(b.get("text") or "")
            draw.rounded_rectangle((cx, y_cur, cx + cw, y_cur + bh), radius=26, fill=pal["card_bg"], outline=col_accent, width=3)
            # Subtle left or top accent highlight bar
            draw.rounded_rectangle((cx + 22, y_cur + 22, cx + 28, y_cur + bh - 22), radius=3, fill=col_accent)
            text_top = y_cur + 24
            if eyebrow:
                draw_wrapped_text(draw, eyebrow, get_font(20, bold=True), cx + 52, text_top, cw - 90, col_accent, align="center", max_lines=1)
                text_top += 34
            else:
                text_top = y_cur + max(24, (bh - _estimate_wrapped_lines(q_text, font_q, cw - 110, 3) * 48) // 2)
            draw_wrapped_text(draw, q_text, font_q, cx + 52, text_top, cw - 104, pal["text"], align="center", max_lines=3, line_spacing=8)

        elif btype == "pills":
            items = b.get("items") or []
            mode = str(b.get("mode", "row")).lower().strip()
            clean_items = []
            for it in items[:4]:
                if isinstance(it, dict):
                    clean_items.append((str(it.get("label") or it.get("text") or ""), it.get("color", "")))
                else:
                    clean_items.append((str(it), ""))
            n_it = len(clean_items)
            pill_cols = [pal["cyan"], pal["purple"], pal["emerald"], pal["amber"]]

            if n_it == 2 and mode == "vs":
                pw = 415
                gap_p = cw - pw * 2
                for pi, (ptxt, pcol) in enumerate(clean_items):
                    if pi == 1 and progress < gate + 0.10:
                        continue
                    px = cx + pi * (pw + gap_p)
                    pc = _pal_color_name(pcol, pill_cols[pi % len(pill_cols)])
                    draw.rounded_rectangle((px, y_cur, px + pw, y_cur + bh), radius=22, fill=pal["card_bg"], outline=pc, width=3)
                    draw_wrapped_text(draw, ptxt, get_font(28, bold=True), px + 18, y_cur + (bh - 34) // 2, pw - 36, pc, align="center", max_lines=2)
                if progress >= gate + 0.08:
                    vx, vy = cx + cw // 2, y_cur + bh // 2
                    draw.ellipse((vx - 30, vy - 30, vx + 30, vy + 30), fill=pal["bg"], outline=pal["amber"], width=3)
                    draw.text((vx - 17, vy - 14), "VS", fill=pal["amber"], font=get_font(22, bold=True))
            elif mode == "grid" or n_it > 3:
                col_w_g = (cw - 20) // 2
                rows = math.ceil(n_it / 2)
                cell_h = max(62, (bh - (rows - 1) * 14) // max(1, rows))
                for pi, (ptxt, pcol) in enumerate(clean_items):
                    if progress < gate + pi * 0.08:
                        continue
                    r_idx, c_idx = pi // 2, pi % 2
                    px = cx + c_idx * (col_w_g + 20)
                    py_i = y_cur + r_idx * (cell_h + 14)
                    pc = _pal_color_name(pcol, pill_cols[pi % len(pill_cols)])
                    draw.rounded_rectangle((px, py_i, px + col_w_g, py_i + cell_h), radius=18, fill=pal["card_bg"], outline=pc, width=2)
                    draw_wrapped_text(draw, ptxt, get_font(24, bold=True), px + 16, py_i + max(14, (cell_h - 30) // 2), col_w_g - 32, pal["text"], align="center", max_lines=2)
            else:
                pgap = 20 if mode != "arrow" else 42
                pw = (cw - max(0, n_it - 1) * pgap) // max(1, n_it)
                f_pill = get_font(26 if n_it <= 2 else 22, bold=True)
                for pi, (ptxt, pcol) in enumerate(clean_items):
                    if progress < gate + pi * 0.09:
                        continue
                    px = cx + pi * (pw + pgap)
                    pc = _pal_color_name(pcol, pill_cols[pi % len(pill_cols)])
                    draw.rounded_rectangle((px, y_cur, px + pw, y_cur + bh), radius=20, fill=pal["card_bg"], outline=pc, width=3)
                    draw_wrapped_text(draw, ptxt, f_pill, px + 14, y_cur + max(18, (bh - 32) // 2), pw - 28, pal["text"], align="center", max_lines=2)
                    if mode == "arrow" and pi < n_it - 1:
                        ax1 = px + pw + 6
                        ax2 = ax1 + pgap - 12
                        ay = y_cur + bh // 2
                        draw.line((ax1, ay, ax2, ay), fill=pal["amber"], width=4)
                        draw.polygon([(ax2 + 6, ay), (ax2 - 6, ay - 7), (ax2 - 6, ay + 7)], fill=pal["amber"])

        elif btype == "flow_chain":
            nodes = b.get("nodes") or []
            edges = b.get("edges") or []
            cnt = min(4, max(1, len(nodes)))
            ag = max(28, min(72, int(bh * 0.14))) if cnt > 1 else 0
            nh = max(66, (bh - max(0, cnt - 1) * ag) // cnt)
            step_span = 0.72 / max(1, cnt)
            node_cols = [pal["cyan"], pal["purple"], pal["emerald"], pal["amber"]]
            centers: List[Tuple[int, int]] = []
            for ni, raw_n in enumerate(nodes[:4]):
                n_gate = gate + (0.0 if ni == 0 else ni * step_span * 0.55)
                if progress < n_gate:
                    continue
                ny = y_cur + ni * (nh + ag)
                nc = node_cols[ni % len(node_cols)]
                is_focus = (n_gate <= progress < n_gate + step_span)
                if isinstance(raw_n, dict):
                    nlbl = str(raw_n.get("label") or raw_n.get("title") or "")
                    nsub = str(raw_n.get("sub") or "")
                else:
                    nlbl = str(raw_n)
                    nsub = ""
                draw.rounded_rectangle((cx, ny, cx + cw, ny + nh), radius=20, fill=pal["card_bg"], outline=nc, width=4 if is_focus else 2)
                num_r = 22 if nh < 95 else 26
                num_cx, num_cy = cx + 44, ny + nh // 2
                draw.ellipse((num_cx - num_r, num_cy - num_r, num_cx + num_r, num_cy + num_r), fill=nc)
                num_s = str(ni + 1)
                nf = get_font(22, bold=True)
                nb = nf.getbbox(num_s)
                draw.text((num_cx - (nb[2] - nb[0]) // 2, num_cy - 13), num_s, fill=(255, 255, 255), font=nf)
                if nsub:
                    draw_wrapped_text(draw, nlbl, get_font(28, bold=True), cx + 88, ny + 14, cw - 115, pal["text"], max_lines=1)
                    draw_wrapped_text(draw, nsub, get_font(21), cx + 88, ny + 50, cw - 115, pal["muted"], max_lines=1)
                else:
                    draw_wrapped_text(draw, nlbl, get_font(27 if nh < 95 else 31, bold=True), cx + 88, ny + max(16, (nh - 32) // 2), cw - 115, pal["text"], max_lines=2)
                centers.append((ni, cx + cw // 2, ny + nh))

            # Animated arrows + exact edge labels between connected revealed nodes
            for ci in range(len(nodes[:4]) - 1):
                ny_src_bot = y_cur + ci * (nh + ag) + nh
                ny_dst_top = y_cur + (ci + 1) * (nh + ag)
                a_start = gate + (ci + 0.35) * step_span * 0.55
                a_t = _stage_reveal(progress, a_start, a_start + 0.16)
                if a_t <= 0.02:
                    continue
                edge_lbl = str(edges[ci]) if ci < len(edges) else ""
                _draw_data_packet_arrow(
                    draw,
                    (cx + cw // 2, ny_src_bot + 2),
                    (cx + cw // 2, ny_dst_top - 2),
                    label=edge_lbl,
                    progress=progress,
                    color=node_cols[ci % len(node_cols)],
                    reveal_t=a_t,
                )

        elif btype == "code":
            code_txt = str(b.get("code") or "")
            lang = str(b.get("lang") or "py").lower()
            draw.rounded_rectangle((cx, y_cur, cx + cw, y_cur + bh), radius=20, fill=(13, 17, 23, 250), outline=pal["card_border"], width=2)
            draw.rounded_rectangle((cx, y_cur, cx + cw, y_cur + 42), radius=20, fill=(30, 41, 59, 250))
            draw.text((cx + 22, y_cur + 10), f"{lang.upper()} SNIPPET", fill=NEON_CYAN, font=get_font(18, bold=True))
            f_c = get_font(24)
            clines = code_txt.splitlines()[:5]
            tot_chars = max(1, len(code_txt))
            show_chars = int(tot_chars * min(1.0, local_p * 1.4 + 0.25))
            seen = 0
            cy_line = y_cur + 56
            for ln in clines:
                rem = max(0, show_chars - seen)
                vis = ln[:rem]
                draw.text((cx + 24, cy_line), vis, fill=NEON_EMERALD if any(k in ln for k in ("def ", "SELECT", "return", "FROM")) else TEXT_PRIMARY, font=f_c)
                seen += len(ln) + 1
                cy_line += 38

        elif btype == "banner":
            b_txt = str(b.get("text") or "")
            btone = str(b.get("tone") or "highlight").lower().strip()
            if btone == "warn":
                b_fill, b_out, b_tcol = pal["warn_bg"], pal["amber"], pal["amber"]
            elif btone == "cta":
                b_fill, b_out, b_tcol = pal["cyan_bg"], pal["cyan"], pal["text"]
            else:
                b_fill, b_out, b_tcol = pal["emerald_bg"], pal["emerald"], pal["text"]
            rad = min(44, bh // 2) if btone == "cta" else 20
            draw.rounded_rectangle((cx + 12, y_cur, cx + cw - 12, y_cur + bh), radius=rad, fill=b_fill, outline=b_out, width=3)
            draw_wrapped_text(draw, b_txt, font_banner, cx + 36, y_cur + max(16, (bh - 34) // 2), cw - 72, b_tcol, align="center", max_lines=2)

        else:  # list_cards
            items = (b.get("items") or [])[:4]
            variant = str(b.get("variant") or "check").lower().strip()
            cnt = max(1, len(items))
            igap = 14
            rh = max(72, (bh - max(0, cnt - 1) * igap) // cnt)
            for li, raw_it in enumerate(items):
                lgate = gate + li * 0.14
                if progress < lgate:
                    continue
                ry = y_cur + li * (rh + igap)
                if isinstance(raw_it, dict):
                    head = str(raw_it.get("title") or raw_it.get("label") or "")
                    sub = str(raw_it.get("sub") or raw_it.get("desc") or "")
                else:
                    s_it = str(raw_it)
                    parts = s_it.split(":", 1) if ":" in s_it else (s_it.split("—", 1) if "—" in s_it else [s_it, ""])
                    head = parts[0].strip()
                    sub = parts[1].strip() if len(parts) > 1 else ""
                is_f = (lgate <= progress < lgate + 0.18)
                card_out = pal["amber"] if variant == "warn" else (pal["accent"] if is_f else pal["card_border"])
                draw.rounded_rectangle((cx, ry, cx + cw, ry + rh), radius=20, fill=pal["card_bg"], outline=card_out, width=3 if is_f else 2)
                if variant == "warn":
                    _draw_vector_warning(draw, cx + 48, ry + rh // 2, radius=20)
                else:
                    _draw_vector_check(draw, cx + 48, ry + rh // 2, radius=20)
                if sub:
                    draw_wrapped_text(draw, head, get_font(27, bold=True), cx + 92, ry + 16, cw - 115, pal["text"], max_lines=1)
                    draw_wrapped_text(draw, sub, get_font(21), cx + 92, ry + 52, cw - 115, pal["muted"], max_lines=2)
                else:
                    draw_wrapped_text(draw, head, get_font(27, bold=True), cx + 92, ry + max(18, (rh - 34) // 2), cw - 115, pal["text"], max_lines=2)

        y_cur += bh + gap

# =========================================================================
# 1. SPLIT COMPARISON (Left vs Right - Problem vs Solution)
# =========================================================================
def _render_split_comparison(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    left_label = data.get("left_label") or data.get("left_side", {}).get("label") or "TRADITIONAL APPROACH"
    right_label = data.get("right_label") or data.get("right_side", {}).get("label") or "OPTIMIZED SOLUTION"
    
    left_points = data.get("left_points") or data.get("cons") or []
    if not left_points and "left_side" in data:
        ls = data["left_side"]
        left_points = [ls.get("status", "")] + ls.get("points", [])
    left_points = [p for p in left_points if p]
    if not left_points:
        left_points = ["High Operational Overhead", "Resource Contention & Latency", "Fragile Manual Workflows"]
        
    right_points = data.get("right_points") or data.get("pros") or []
    if not right_points and "right_side" in data:
        rs = data["right_side"]
        right_points = [rs.get("status", "")] + rs.get("points", [])
    right_points = [p for p in right_points if p]
    if not right_points:
        right_points = ["Zero Downtime & Fast Execution", "Low Latency & High Throughput", "Automated Scalable Architecture"]
    
    pal = _ACTIVE_PAL
    col_w = 445
    card_h = 680
    top_y = 440
    lx = 65
    rx = 570
    neutral_mode = bool(data.get("neutral_mode", False))
    show_vs = bool(data.get("show_vs", not neutral_mode))

    left_out = pal["cyan"] if neutral_mode else pal["rose"]
    left_hdr_fill = pal["cyan_bg"] if neutral_mode else pal["rose_bg"]
    left_title_str = left_label.upper() if neutral_mode else f"X  {left_label.upper()}"

    right_out = pal["purple"] if neutral_mode else pal["emerald"]
    right_hdr_fill = pal["card_alt"] if neutral_mode else pal["emerald_bg"]
    right_title_str = right_label.upper() if neutral_mode else f"+  {right_label.upper()}"

    # Left Card - visible immediately at 0.0s (no blank frame)
    draw.rounded_rectangle((lx, top_y, lx + col_w, top_y + card_h), radius=24, fill=pal["card_bg"], outline=left_out, width=3)
    draw.rounded_rectangle((lx + 20, top_y + 20, lx + col_w - 20, top_y + 80), radius=14, fill=left_hdr_fill)
    draw_wrapped_text(draw, left_title_str, get_font(25, bold=True), lx + 30, top_y + 36, col_w - 60, left_out, align="center", max_lines=1)

    for i, pt in enumerate(left_points[:3]):
        if progress < (0.04 + i * 0.12):
            continue
        py = top_y + 120 + (i * 170)
        draw.rounded_rectangle((lx + 20, py, lx + col_w - 20, py + 140), radius=16, fill=pal["card_alt"], outline=pal["card_border"], width=1)
        draw.ellipse((lx + 36, py + 30, lx + 54, py + 48), fill=left_out)
        draw_wrapped_text(draw, pt, get_font(26), lx + 68, py + 22, col_w - 102, pal["text"], max_lines=3, line_spacing=6)

    # Right Card - reveals progressively
    if progress >= 0.44:
        draw.rounded_rectangle((rx, top_y, rx + col_w, top_y + card_h), radius=24, fill=pal["card_bg"], outline=right_out, width=3)
        draw.rounded_rectangle((rx + 20, top_y + 20, rx + col_w - 20, top_y + 80), radius=14, fill=right_hdr_fill)
        draw_wrapped_text(draw, right_title_str, get_font(25, bold=True), rx + 30, top_y + 36, col_w - 60, right_out, align="center", max_lines=1)

        for i, pt in enumerate(right_points[:3]):
            if progress < (0.50 + i * 0.12):
                continue
            py = top_y + 120 + (i * 170)
            draw.rounded_rectangle((rx + 20, py, rx + col_w - 20, py + 140), radius=16, fill=pal["card_alt"], outline=pal["card_border"], width=1)
            if neutral_mode:
                draw.ellipse((rx + 36, py + 30, rx + 54, py + 48), fill=right_out)
                draw_wrapped_text(draw, pt, get_font(26), rx + 68, py + 22, col_w - 102, pal["text"], max_lines=3, line_spacing=6)
            else:
                _draw_vector_check(draw, rx + 46, py + 38, radius=14)
                draw_wrapped_text(draw, pt, get_font(26), rx + 70, py + 22, col_w - 104, pal["text"], max_lines=3, line_spacing=6)

    # Center "VS" Badge (only when explicitly a side-by-side comparison)
    if show_vs and progress >= 0.42:
        vx, vy = VIDEO_WIDTH // 2, top_y + card_h // 2
        draw.ellipse((vx - 42, vy - 42, vx + 42, vy + 42), fill=pal["bg"], outline=pal["amber"], width=4)
        draw.text((vx - 22, vy - 18), "VS", fill=pal["amber"], font=get_font(28, bold=True))

# =========================================================================
# 2. BENCHMARK PERFORMANCE COMPARISON BARS
# =========================================================================
def _render_benchmark_chart(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    bars = data.get("bars") or data.get("benchmarks") or data.get("comparisons") or [
        {"label": "Naive Unoptimized Pattern", "value": 4500, "display": "4.5s Latency", "color": "#EF4444", "is_winner": False},
        {"label": "Standard Implementation", "value": 180, "display": "180ms", "color": "#FBBF24", "is_winner": False},
        {"label": "High-Performance Architecture", "value": 12, "display": "12ms (15x Faster)", "color": "#10B981", "is_winner": True}
    ]
    winner_badge = data.get("winner_badge", "15X FASTER")
    
    pal = _ACTIVE_PAL
    container_w = 940
    cx = (VIDEO_WIDTH - container_w) // 2
    start_y = 440

    # Outer Panel
    panel_h = 740
    draw.rounded_rectangle((cx, start_y, cx + container_w, start_y + panel_h), radius=26, fill=pal["card_bg"], outline=pal["card_border"], width=2)

    font_lbl = get_font(30, bold=True)
    font_val = get_font(28, bold=True)

    bar_max_w = 860
    base_bar_y = start_y + 60
    track_col = (226, 232, 240, 220) if pal.get("is_light") else (30, 41, 59, 200)

    for i, b in enumerate(bars[:3]):
        bar_start = 0.05 + (i * 0.22)
        bar_fill_t = _stage_reveal(progress, bar_start, bar_start + 0.22)
        if bar_fill_t <= 0.0:
            continue
        by = base_bar_y + (i * 190)
        color = _hex_to_rgb(b.get("color", "#38BDF8"))
        is_winner = b.get("is_winner", False)

        # Label
        draw.text((cx + 40, by), b.get("label", ""), fill=pal["text"], font=font_lbl)

        # Background track
        track_y = by + 50
        track_h = 56
        draw.rounded_rectangle((cx + 40, track_y, cx + 40 + bar_max_w, track_y + track_h), radius=14, fill=track_col)

        # Animated filling progress
        val_ratio = 1.0 if not is_winner and i == 0 else (0.55 if i == 1 else 0.20)
        animated_w = max(80, int(bar_max_w * val_ratio * bar_fill_t))

        draw.rounded_rectangle((cx + 40, track_y, cx + 40 + animated_w, track_y + track_h), radius=14, fill=(*color, 230), outline=color, width=2)
        draw.text((cx + 60, track_y + 10), b.get("display", ""), fill=(10, 15, 25) if is_winner else (248, 250, 252), font=font_val)

    # Winner Banner at bottom
    if winner_badge and progress >= 0.72:
        wy = start_y + panel_h - 110
        draw.rounded_rectangle((cx + 40, wy, cx + container_w - 40, wy + 80), radius=18, fill=pal["emerald_bg"], outline=pal["emerald"], width=3)
        draw_wrapped_text(draw, str(winner_badge).upper(), get_font(28, bold=True), cx + 50, wy + 22, container_w - 100, pal["emerald"], align="center", max_lines=1)

# =========================================================================
# 3. CIRCULAR HUB & SPOKE MESH CLUSTER
# =========================================================================
def _render_circular_hub_mesh(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    hub_name = data.get("hub_name", "CORE SYSTEM")
    satellites = data.get("satellites") or data.get("nodes") or data.get("components") or [
        {"name": "Client Ingestion", "role": "API Requests", "color": "#EF4444"},
        {"name": "App Cluster", "role": "State Processing", "color": "#10B981"},
        {"name": "Event Broker", "role": "Message Stream", "color": "#FBBF24"},
        {"name": "Storage Tier", "role": "Data Store", "color": "#38BDF8"}
    ]
    
    center_x = VIDEO_WIDTH // 2
    center_y = 760
    
    # Pulsing Radar Rings
    for ring in range(3):
        pulse = (progress * 2.0 + (ring * 0.33)) % 1.0
        rad = int(140 + pulse * 240)
        alpha = int(120 * (1.0 - pulse))
        draw.ellipse((center_x - rad, center_y - rad, center_x + rad, center_y + rad), outline=(56, 189, 248, alpha), width=2)
        
    # Satellite Nodes placed symmetrically around center (progressive reveal one by one)
    radius_dist = 280
    sat_coords = []
    angles = [math.pi * 0.25, math.pi * 0.75, math.pi * 1.25, math.pi * 1.75]
    
    for i, sat in enumerate(satellites[:4]):
        ang = angles[i]
        sx = int(center_x + math.cos(ang) * radius_dist)
        sy = int(center_y + math.sin(ang) * radius_dist)
        spoke_t = _stage_reveal(progress, 0.14 + i * 0.18, 0.28 + i * 0.18)
        if spoke_t <= 0.0:
            continue
        _draw_data_packet_arrow(draw, (center_x, center_y), (sx, sy), progress=progress, color=_hex_to_rgb(sat.get("color", "#38BDF8")), reveal_t=spoke_t)
        if spoke_t >= 0.85:
            sat_coords.append((sx, sy, sat))

    # Draw Satellites Cards
    pal = _ACTIVE_PAL
    for sx, sy, sat in sat_coords:
        sw, sh = 280, 110
        color = _hex_to_rgb(sat.get("color", "#38BDF8"))
        draw.rounded_rectangle((sx - sw//2, sy - sh//2, sx + sw//2, sy + sh//2), radius=18, fill=pal["card_bg"], outline=color, width=3)
        draw_wrapped_text(draw, sat.get("name", ""), get_font(24, bold=True), sx - sw//2 + 10, sy - sh//2 + 18, sw - 20, pal["text"], align="center", max_lines=1)
        draw_wrapped_text(draw, sat.get("role", ""), get_font(18), sx - sw//2 + 10, sy - sh//2 + 56, sw - 20, pal["muted"], align="center", max_lines=1)

    # Center Hub Core (Pulsing Glow)
    hub_r = 110
    draw.ellipse((center_x - hub_r - 6, center_y - hub_r - 6, center_x + hub_r + 6, center_y + hub_r + 6), fill=(*pal["cyan"], 40))
    draw.ellipse((center_x - hub_r, center_y - hub_r, center_x + hub_r, center_y + hub_r), fill=pal["card_bg"], outline=pal["cyan"], width=5)
    draw_wrapped_text(draw, hub_name, get_font(30, bold=True), center_x - 90, center_y - 25, 180, pal["cyan"], align="center", max_lines=2)

# =========================================================================
# 4. METRIC GAUGE HUD (Speedometer / Radial Telemetry)
# =========================================================================
def _render_metric_gauge_hud(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    pal = _ACTIVE_PAL
    main_val = data.get("main_value", "1,500,000")
    main_unit = data.get("main_unit", "EVENTS / SEC")
    gauge_pct = float(data.get("gauge_percent", 94))
    telemetry = data.get("telemetry", [
        {"label": "CPU USAGE", "val": "14%"},
        {"label": "DATA LOSS", "val": "0.00%"},
        {"label": "FAILOVER", "val": "< 1s"}
    ])

    panel_w = 940
    px = (VIDEO_WIDTH - panel_w) // 2
    py = 440

    # Circular Gauge Arc
    arc_cx = VIDEO_WIDTH // 2
    arc_cy = 660
    arc_r = 210

    arc_track = (203, 213, 225) if pal.get("is_light") else (30, 41, 59)
    draw.arc((arc_cx - arc_r, arc_cy - arc_r, arc_cx + arc_r, arc_cy + arc_r), start=140, end=400, fill=arc_track, width=28)

    fill_end = 140 + int((400 - 140) * (gauge_pct / 100.0) * min(1.0, progress * 1.5))
    draw.arc((arc_cx - arc_r, arc_cy - arc_r, arc_cx + arc_r, arc_cy + arc_r), start=140, end=fill_end, fill=pal["emerald"], width=28)

    # Center Big Stat
    draw_wrapped_text(draw, str(main_val), get_font(68, bold=True), arc_cx - 210, arc_cy - 45, 420, pal["text"], align="center", max_lines=1)
    draw_wrapped_text(draw, str(main_unit), get_font(28, bold=True), arc_cx - 200, arc_cy + 45, 400, pal["emerald"], align="center", max_lines=1)

    # 3 Telemetry Cards below
    card_w = 285
    card_h = 170
    card_y = 960

    for i, t in enumerate(telemetry[:3]):
        if progress < (0.35 + i * 0.18):
            continue
        cx = px + (i * (card_w + 42))
        draw.rounded_rectangle((cx, card_y, cx + card_w, card_y + card_h), radius=20, fill=pal["card_bg"], outline=pal["card_border"], width=2)
        draw.text((cx + 25, card_y + 25), t.get("label", ""), fill=pal["muted"], font=get_font(22, bold=True))
        draw.text((cx + 25, card_y + 75), t.get("val", ""), fill=pal["cyan"], font=get_font(46, bold=True))

# =========================================================================
# 5. DATA STRUCTURE / MEMORY BUFFER / PARTITIONS
# =========================================================================
def _render_data_structure_memory(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    panel_w = 940
    px = (VIDEO_WIDTH - panel_w) // 2
    py = 440
    
    # Memory Layout Container
    draw.rounded_rectangle((px, py, px + panel_w, py + 720), radius=26, fill=CARD_BG, outline=CARD_BORDER, width=2)
    header_title = data.get("title") or data.get("badge") or "MEMORY LAYOUT & STATE BUFFER"
    draw_wrapped_text(draw, header_title.upper(), get_font(26, bold=True), px + 40, py + 30, panel_w - 80, NEON_CYAN, max_lines=1)
    
    entries = data.get("log_sequence_entries") or data.get("entries") or data.get("slots") or data.get("memory_blocks") or []
    slots = max(3, min(5, len(entries))) if entries else 4
    slot_w = 860
    slot_h = 95
    base_y = py + 95
    
    active_idx = int(progress * slots * 1.5) % slots
    
    for i in range(slots):
        if progress < (0.06 + i * 0.18):
            continue
        sy = base_y + (i * 115)
        is_active = (i == active_idx)
        color = NEON_EMERALD if is_active else CARD_BORDER
        fill_bg = (52, 211, 153, 35) if is_active else (20, 27, 45, 230)
        
        draw.rounded_rectangle((px + 40, sy, px + 40 + slot_w, sy + slot_h), radius=16, fill=fill_bg, outline=color, width=2 if is_active else 1)
        
        if entries and i < len(entries):
            e = entries[i]
            if isinstance(e, dict):
                offset_label = e.get("address") or e.get("lsn") or e.get("offset") or f"0x{i*1024:04X}"
                op = e.get("op") or e.get("label") or ""
                tbl = e.get("table") or e.get("value") or ""
                st = e.get("status", "")
                msg = f"{op} • {tbl}" if (op and tbl) else (op or tbl or e.get("data", f"Block #{i+1}"))
                if st:
                    msg += f" ({st})"
            else:
                offset_label = f"0x{i*1024:04X}"
                msg = str(e)
        else:
            offset_label = f"0x{i*1024:04X}"
            msg = f"Block #{i+101} • Active State Execution" if i <= active_idx else "[ Allocated Buffer Slot ]"

        # Offset block
        draw.rounded_rectangle((px + 55, sy + 15, px + 220, sy + slot_h - 15), radius=10, fill=(30, 41, 59))
        draw.text((px + 70, sy + 25), str(offset_label).upper()[:10], fill=NEON_AMBER, font=get_font(20, bold=True))
        
        # Message Data
        draw.text((px + 245, sy + 30), str(msg)[:42], fill=TEXT_PRIMARY if i <= active_idx else TEXT_DIM, font=get_font(24))
        
        if is_active:
            draw.text((px + slot_w - 70, sy + 22), "◀ LIVE", fill=NEON_EMERALD, font=get_font(20, bold=True))

# =========================================================================
# 6. SQL TABLE
# =========================================================================
def _render_sql_table(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    topic_title = data.get("title") or "Query Execution"
    code = data.get("code_snippet") or data.get("query") or data.get("sql") or data.get("code")
    if not code:
        tbl_name = topic_title.lower().replace(" ", "_")[:14]
        code = f"SELECT id, metric_val, DENSE_RANK() OVER (ORDER BY metric_val DESC) FROM {tbl_name};"
        
    table_data = data.get("table_data") or data.get("table") or data.get("dataset") or {}
    headers = table_data.get("headers") or table_data.get("columns") or table_data.get("cols")
    rows = table_data.get("rows") or table_data.get("data")
    if not headers:
        headers = ["ID", "ENTITY", "VALUE", "RANK"]
    if not rows:
        rows = [
            ["101", f"{topic_title[:8]} A", "120,000", "1"],
            ["102", f"{topic_title[:8]} B", "95,000", "2"],
            ["103", f"{topic_title[:8]} C", "95,000", "2"],
            ["104", f"{topic_title[:8]} D", "80,000", "3"]
        ]
    
    pal = _ACTIVE_PAL
    qx, qy, qw, qh = 70, 440, 940, 140
    draw.rounded_rectangle((qx, qy, qx + qw, qy + qh), radius=20, fill=pal["card_bg"], outline=pal["purple"], width=3)
    q_lbl = str(data.get("query_label") or "SQL QUERY").upper()
    draw.text((qx + 30, qy + 18), q_lbl, fill=pal["purple"], font=get_font(22, bold=True))
    draw_wrapped_text(draw, code, get_font(26, bold=True), qx + 30, qy + 58, 880, pal["text"], max_lines=2)

    tx, ty, tw = 70, 610, 940
    col_w = tw // max(1, len(headers))
    row_h = 90

    draw.rounded_rectangle((tx, ty, tx + tw, ty + row_h), radius=16, fill=pal["card_alt"], outline=pal["card_border"], width=2)
    for c_idx, h in enumerate(headers):
        h_str = str(h).upper()
        draw.text((tx + (c_idx * col_w) + 20, ty + 28), h_str, fill=pal["cyan"], font=get_font(26, bold=True))

    active_row = int((progress * len(rows)) % len(rows)) if rows else 0
    for r_idx, row in enumerate(rows[:4]):
        if progress < (0.14 + r_idx * 0.18):
            continue
        ry = ty + ((r_idx + 1) * row_h) + 12
        is_highlighted = (r_idx == active_row)
        bg = pal["cyan_bg"] if is_highlighted else pal["card_bg"]
        border = pal["amber"] if is_highlighted else pal["card_border"]

        draw.rounded_rectangle((tx, ry, tx + tw, ry + row_h - 10), radius=14, fill=bg, outline=border, width=3 if is_highlighted else 1)
        for c_idx, cell in enumerate(row[:len(headers)]):
            txt_color = pal["amber"] if (is_highlighted and c_idx == len(row) - 1) else pal["text"]
            draw.text((tx + (c_idx * col_w) + 20, ry + 24), str(cell), fill=txt_color, font=get_font(24))

# =========================================================================
# 7. CODE TERMINAL
# =========================================================================
def _render_code_terminal(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    raw_code = data.get("code_snippet") or ""
    if not raw_code:
        cmd_text = data.get("command") or data.get("cli") or ""
        out_text = data.get("output") or ""
        if cmd_text:
            raw_code = f"$ {cmd_text}"
            if out_text:
                raw_code += f"\n\n{out_text}"
    if not raw_code:
        topic_title = data.get("title") or "Technical Implementation"
        raw_code = (
            f"# Execution Logic: {topic_title}\n"
            f"async def execute_task(ctx):\n"
            f"    # Real-time state synchronization\n"
            f"    cluster = await init_active_pipeline()\n"
            f"    result = cluster.sync_event(ctx)\n"
            f"    return {{'status': 200, 'synced': True}}"
        )
    lines = raw_code.split("\n")
    
    tx, ty, tw, th = 70, 460, 940, 750
    draw.rounded_rectangle((tx, ty, tx + tw, ty + th), radius=24, fill=(15, 23, 42, 245), outline=CARD_BORDER, width=3)
    
    draw.rounded_rectangle((tx, ty, tx + tw, ty + 70), radius=24, fill=(30, 41, 59, 255))
    draw.ellipse((tx + 30, ty + 24, tx + 52, ty + 46), fill=(239, 68, 68))
    draw.ellipse((tx + 65, ty + 24, tx + 87, ty + 46), fill=(245, 158, 11))
    draw.ellipse((tx + 100, ty + 24, tx + 122, ty + 46), fill=(16, 185, 129))
    upper_code = raw_code.upper()
    if any(kw in upper_code for kw in ["CREATE TABLE", "SELECT ", "INSERT INTO", "ALTER TABLE"]):
        term_title = "migration.sql — Query Execution"
    elif raw_code.lstrip().startswith("$") or any(kw in raw_code for kw in ["aws ", "docker ", "kubectl ", "python -m"]):
        term_title = "terminal.sh — CLI Execution"
    else:
        term_title = "terminal.py — Execution Output"
    draw.text((tx + 140, ty + 20), term_title, fill=TEXT_MUTED, font=get_font(26))
    
    font_code = get_font(30)
    total_chars = len(raw_code)
    chars_to_show = int(progress * total_chars * 1.5)
    
    current_char_count = 0
    line_y = ty + 120
    max_code_w = 760
    for i, line in enumerate(lines[:8]):
        line_num = f"{i + 1:2d}  "
        draw.text((tx + 30, line_y), line_num, fill=(71, 85, 105), font=font_code)
        
        remaining = max(0, chars_to_show - current_char_count)
        visible = line[:remaining]
        
        while visible and (font_code.getbbox(visible)[2] - font_code.getbbox(visible)[0]) > max_code_w:
            visible = visible[:-1]
            
        draw.text((tx + 95, line_y), visible, fill=NEON_EMERALD if "def " in line or "return" in line else TEXT_PRIMARY, font=font_code)
        current_char_count += len(line) + 1
        line_y += 68
        if current_char_count >= chars_to_show:
            bbox_vis = font_code.getbbox(visible) if visible else (0, 0, 0, 0)
            vis_w = bbox_vis[2] - bbox_vis[0]
            cx = tx + 95 + vis_w + 4
            draw.rectangle((cx, line_y - 62, cx + 4, line_y - 25), fill=NEON_CYAN)
            break

# =========================================================================
# 8. ALERT DIAGRAM (Radar Warning & Problem Statement)
# =========================================================================
def _render_alert_diagram(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    center_x = VIDEO_WIDTH // 2
    center_y = 560
    pulse = (progress * 2.5) % 1.0
    for ring in range(3):
        r_prog = (pulse + (ring * 0.33)) % 1.0
        rad = int(80 + r_prog * 230)
        alpha = int(120 * (1.0 - r_prog))
        draw.ellipse((center_x - rad, center_y - rad, center_x + rad, center_y + rad), outline=(244, 63, 94, alpha), width=3)
        
    _draw_vector_warning(draw, center_x, center_y, radius=65)
    
    if progress >= 0.18:
        box_w, box_h = 920, 240
        bx = (VIDEO_WIDTH - box_w) // 2
        by = 760
        draw.rounded_rectangle((bx, by, bx + box_w, by + box_h), radius=24, fill=(24, 15, 23, 245), outline=NEON_ROSE, width=4)
        
        p_title = data.get("problem_title", data.get("title", "High-Volume Production Bottleneck"))
        p_sub = data.get("problem_desc", data.get("subtitle", "Traditional message brokers hit I/O locks and JVM garbage collection crashes at scale."))
        
        draw_wrapped_text(draw, p_title, get_font(38, bold=True), bx + 40, by + 32, max_width=840, fill=TEXT_PRIMARY, max_lines=1)
        draw_wrapped_text(draw, p_sub, get_font(28), bx + 40, by + 90, max_width=840, fill=TEXT_MUTED, max_lines=3, line_spacing=6)
        
    if progress >= 0.55:
        box_w = 920
        bx = (VIDEO_WIDTH - box_w) // 2
        cx, cy, cw, ch = bx, 1060, box_w, 150
        draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=20, fill=CARD_BG, outline=NEON_AMBER, width=3)
        draw.text((cx + 40, cy + 26), "CRITICAL CHALLENGE", fill=NEON_AMBER, font=get_font(24, bold=True))
        draw_wrapped_text(draw, data.get("challenge", "How do you achieve 100% Zero Data Loss without speed drops?"), get_font(28, bold=True), cx + 40, cy + 70, max_width=840, fill=TEXT_PRIMARY, max_lines=2)

# =========================================================================
# 9. ARCHITECTURE PIPELINE FLOW
# =========================================================================
def _render_architecture_flow(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    raw_nodes = data.get("nodes") or data.get("stages") or data.get("steps") or data.get("services") or data.get("pipeline") or []
    default_colors = ["#38BDF8", "#FBBF24", "#34D399", "#A855F7"]
    if not raw_nodes:
        topic_title = data.get("title") or "System Architecture"
        raw_nodes = [
            {"label": "Client Ingestion Layer", "sub": "Incoming Requests & Routing", "color": "#38BDF8"},
            {"label": f"{topic_title[:24]}", "sub": "Core Engine & State Sync", "color": "#FBBF24"},
            {"label": "Target Database Cluster", "sub": "Distributed Persistent Storage", "color": "#34D399"}
        ]
    nodes = []
    for idx, n in enumerate(raw_nodes[:4]):
        if isinstance(n, str):
            nodes.append({"label": n, "sub": "Service Component", "color": default_colors[idx % len(default_colors)]})
        elif isinstance(n, dict):
            nodes.append({
                "label": n.get("label") or n.get("name") or n.get("title") or f"Stage {idx+1}",
                "sub": n.get("sub") or n.get("description") or n.get("type") or "Cloud Service",
                "color": n.get("color") or default_colors[idx % len(default_colors)]
            })

    font_title = get_font(34, bold=True)
    font_sub = get_font(24)
    node_w = 860
    center_x = (VIDEO_WIDTH - node_w) // 2
    
    n_count = len(nodes)
    if n_count <= 2:
        node_h, gap, start_y = 200, 310, 480
    elif n_count == 3:
        node_h, gap, start_y = 170, 240, 440
    else:
        node_h, gap, start_y = 135, 180, 405
    
    pal = _ACTIVE_PAL
    node_coords = []
    edges = data.get("edges") or []
    # Progressive step-by-step reveal: Node 0 visible from 0.0s -> Arrow 0->1 -> Node 1 -> Arrow 1->2 -> Node 2
    step_span = 0.85 / max(1, n_count)
    for i, node in enumerate(nodes):
        node_start = 0.0 if i == 0 else (0.04 + (i * step_span))
        if progress < node_start:
            continue
        ny = start_y + (i * gap)
        node_coords.append((i, center_x + node_w // 2, ny + node_h // 2))
        color_hex = node.get("color", "#38BDF8")
        accent_rgb = _hex_to_rgb(color_hex)
        is_current_focus = (node_start <= progress < node_start + step_span)

        draw.rounded_rectangle((center_x, ny, center_x + node_w, ny + node_h), radius=22, fill=pal["card_bg"], outline=accent_rgb, width=4 if is_current_focus else 2)
        draw.ellipse((center_x + 35, ny + (node_h - 45) // 2, center_x + 80, ny + (node_h + 45) // 2), fill=accent_rgb)

        draw_wrapped_text(draw, node.get("label", ""), font_title, center_x + 100, ny + 22, 720, pal["text"], max_lines=1)
        sub_text = node.get("sub") or ""
        if sub_text:
            draw_wrapped_text(draw, str(sub_text), font_sub, center_x + 100, ny + 70, 720, pal["muted"], max_lines=2)

    for idx_pos in range(len(node_coords) - 1):
        i_src, x1, y1 = node_coords[idx_pos]
        _, x2, y2 = node_coords[idx_pos + 1]
        arrow_start = 0.04 + (i_src * step_span) + (step_span * 0.45)
        arrow_t = _stage_reveal(progress, arrow_start, arrow_start + (step_span * 0.55))
        e_lbl = str(edges[i_src]) if i_src < len(edges) else str(nodes[i_src].get("edge", "")) if isinstance(nodes[i_src], dict) else ""
        _draw_data_packet_arrow(
            draw,
            (x1, y1 + node_h // 2),
            (x2, y2 - node_h // 2),
            label=e_lbl,
            progress=progress,
            color=pal["cyan"],
            reveal_t=arrow_t
        )

# =========================================================================
# 10. CONCEPT COMPARISON CARDS (with Warning Box & CTA Support)
# =========================================================================
def _render_concept_cards(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    pal = _ACTIVE_PAL
    raw_bullets = data.get("bullets") or data.get("points") or data.get("key_points") or data.get("features") or data.get("concepts") or []
    if not raw_bullets:
        topic_title = data.get("title") or "Key Concepts"
        raw_bullets = [topic_title]
    font_head = get_font(33, bold=True)
    font_sub = get_font(25)
    card_w = 940
    has_warn = bool(data.get("warning_box"))
    has_cta = bool(data.get("footer_cta") or data.get("cta_text"))
    card_h = 165 if (has_warn or len(raw_bullets) >= 3) else 185
    start_y = 420
    gap = card_h + 28
    cx = (VIDEO_WIDTH - card_w) // 2

    for i, bullet in enumerate(raw_bullets[:3]):
        card_start = 0.0 if i == 0 else (i * 0.24)
        if progress < card_start:
            continue
        is_focused = (card_start <= progress < card_start + 0.25)
        cy = start_y + (i * gap)
        parts = bullet.split(":", 1) if ":" in bullet else (bullet.split("—", 1) if "—" in bullet else [bullet, ""])
        headline = parts[0].strip()
        subtext = parts[1].strip() if len(parts) > 1 else ""

        draw.rounded_rectangle((cx, cy, cx + card_w, cy + card_h), radius=24, fill=pal["card_bg"], outline=pal["cyan"] if is_focused else pal["card_border"], width=4 if is_focused else 2)
        _draw_vector_check(draw, cx + 68, cy + card_h // 2, radius=30)
        if subtext:
            draw_wrapped_text(draw, headline, font_head, cx + 128, cy + 28, 765, pal["text"], max_lines=1)
            draw_wrapped_text(draw, subtext, font_sub, cx + 128, cy + 78, 765, pal["muted"], max_lines=2)
        else:
            draw_wrapped_text(draw, headline, font_head, cx + 128, cy + (card_h // 2) - 24, 765, pal["text"], max_lines=2)

    last_y = start_y + (min(3, len(raw_bullets)) * gap) + 12

    # Optional Amber Warning Callout Box
    if has_warn and progress >= 0.68:
        warn_h = 145
        wy = min(1140, last_y)
        draw.rounded_rectangle((cx, wy, cx + card_w, wy + warn_h), radius=22, fill=pal["warn_bg"], outline=pal["amber"], width=3)
        warn_hdr = str(data.get("warning_title") or "KEY NOTE").upper()
        draw_wrapped_text(draw, warn_hdr, get_font(21, bold=True), cx + 36, wy + 22, 860, pal["amber"], max_lines=1)
        draw_wrapped_text(draw, str(data["warning_box"]), get_font(27, bold=True), cx + 36, wy + 60, 860, pal["text"], max_lines=2)
        last_y = wy + warn_h + 24

    # Optional Metrics HUD only when explicitly supplied in visual_data
    elif data.get("metrics") and progress >= 0.72:
        metrics = data["metrics"]
        hud_w, hud_h = 940, 145
        hy = min(1120, last_y)
        draw.rounded_rectangle((cx, hy, cx + hud_w, hy + hud_h), radius=24, fill=pal["card_bg"], outline=pal["emerald"], width=3)
        if isinstance(metrics, list) and len(metrics) >= 2:
            draw_wrapped_text(draw, str(metrics[0].get("label", "")).upper(), get_font(20, bold=True), cx + 45, hy + 24, 420, pal["emerald"], max_lines=1)
            draw_wrapped_text(draw, str(metrics[0].get("val", "")), get_font(38, bold=True), cx + 45, hy + 62, 420, pal["text"], max_lines=1)
            draw_wrapped_text(draw, str(metrics[1].get("label", "")).upper(), get_font(20, bold=True), cx + 510, hy + 24, 400, pal["cyan"], max_lines=1)
            draw_wrapped_text(draw, str(metrics[1].get("val", "")), get_font(38, bold=True), cx + 510, hy + 62, 400, pal["cyan"], max_lines=1)

    # Optional Bottom CTA Strip
    if has_cta and progress >= 0.65:
        cta_txt = str(data.get("footer_cta") or data.get("cta_text")).replace("•", " | ")
        cta_y = max(last_y + 10, 1210)
        cta_h = 84
        draw.rounded_rectangle((cx + 40, cta_y, cx + card_w - 40, cta_y + cta_h), radius=42, fill=pal["cyan_bg"], outline=pal["cyan"], width=3)
        draw_wrapped_text(draw, cta_txt.upper(), get_font(28, bold=True), cx + 60, cta_y + 24, card_w - 120, pal["text"], align="center", max_lines=1)


# =========================================================================
# 11. HERO HOOK (Question Card + Dynamic Pills + Optional Stat — Zero Canned Labels!)
# =========================================================================
def _render_hero_hook(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    pal = _ACTIVE_PAL
    question = data.get("question") or data.get("title") or ""
    eyebrow = str(data.get("eyebrow") or data.get("kicker") or "").strip().upper()
    pills = data.get("pills")
    if not isinstance(pills, list):
        pills = [p for p in [data.get("left_pill"), data.get("right_pill")] if p]
    stat_badge = str(data.get("stat_badge") or "").strip()
    sub_callouts = data.get("sub_callouts") or []
    show_vs = bool(data.get("show_vs", (" vs " in question.lower()) and len(pills) == 2))

    # 1. Center Hero Question Card (visible immediately at 0.0s!)
    cw, ch = 940, 260
    cx = (VIDEO_WIDTH - cw) // 2
    cy = 430
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=28, fill=pal["card_bg"], outline=pal["accent"], width=4)
    if eyebrow:
        draw_wrapped_text(draw, eyebrow, get_font(21, bold=True), cx + 40, cy + 26, cw - 80, pal["cyan"], align="center", max_lines=1)
        draw_wrapped_text(draw, question, get_font(40, bold=True), cx + 45, cy + 74, cw - 90, pal["text"], align="center", max_lines=3, line_spacing=8)
    else:
        draw_wrapped_text(draw, question, get_font(42, bold=True), cx + 45, cy + 56, cw - 90, pal["text"], align="center", max_lines=3, line_spacing=8)

    # 2. Dynamic Topic Pills (1, 2, or 3 pills — NO forced VS unless actually comparing two options!)
    next_y = cy + ch + 52
    if pills and progress >= 0.16:
        clean_pills = [str(p) for p in pills[:3] if str(p).strip()]
        n_p = len(clean_pills)
        ph = 115
        pill_cols = [pal["cyan"], pal["purple"], pal["emerald"]]
        if n_p == 2 and show_vs:
            pw = 390
            lx, rx = 70, VIDEO_WIDTH - 70 - pw
            draw.rounded_rectangle((lx, next_y, lx + pw, next_y + ph), radius=24, fill=pal["card_bg"], outline=pill_cols[0], width=3)
            draw_wrapped_text(draw, clean_pills[0], get_font(30, bold=True), lx + 20, next_y + 36, pw - 40, pill_cols[0], align="center", max_lines=1)
            if progress >= 0.28:
                vx, vy = VIDEO_WIDTH // 2, next_y + ph // 2
                draw.ellipse((vx - 36, vy - 36, vx + 36, vy + 36), fill=pal["bg"], outline=pal["amber"], width=4)
                draw.text((vx - 20, vy - 17), "VS", fill=pal["amber"], font=get_font(25, bold=True))
                draw.rounded_rectangle((rx, next_y, rx + pw, next_y + ph), radius=24, fill=pal["card_bg"], outline=pill_cols[1], width=3)
                draw_wrapped_text(draw, clean_pills[1], get_font(30, bold=True), rx + 20, next_y + 36, pw - 40, pill_cols[1], align="center", max_lines=1)
        elif n_p >= 1:
            total_w = 940
            pgap = 20
            pw = (total_w - (n_p - 1) * pgap) // n_p
            sx0 = (VIDEO_WIDTH - total_w) // 2
            for pi, ptxt in enumerate(clean_pills):
                if progress < (0.16 + pi * 0.10):
                    continue
                px = sx0 + pi * (pw + pgap)
                pc = pill_cols[pi % len(pill_cols)]
                draw.rounded_rectangle((px, next_y, px + pw, next_y + ph), radius=22, fill=pal["card_bg"], outline=pc, width=3)
                draw_wrapped_text(draw, ptxt, get_font(28 if n_p <= 2 else 23, bold=True), px + 14, next_y + 36, pw - 28, pal["text"], align="center", max_lines=2)
        next_y += ph + 44

    # 3. Optional Highlight Callout Stat Badge
    if stat_badge and progress >= 0.45:
        bw, bh = 880, 100
        bx = (VIDEO_WIDTH - bw) // 2
        draw.rounded_rectangle((bx, next_y, bx + bw, next_y + bh), radius=22, fill=pal["warn_bg"], outline=pal["amber"], width=3)
        draw_wrapped_text(draw, stat_badge.upper(), get_font(28, bold=True), bx + 30, next_y + 32, bw - 60, pal["amber"], align="center", max_lines=1)
        next_y += bh + 34

    # 4. Optional Trap / Takeaway Sub-Callouts
    if sub_callouts and progress >= 0.68:
        for idx, sc_txt in enumerate(sub_callouts[:2]):
            if progress < (0.68 + idx * 0.14):
                continue
            row_y = next_y + (idx * 85)
            draw.rounded_rectangle((100, row_y, VIDEO_WIDTH - 100, row_y + 70), radius=16, fill=pal["card_bg"], outline=pal["rose"] if idx == 0 else pal["card_border"], width=2)
            draw_wrapped_text(draw, str(sc_txt), get_font(24, bold=True), 130, row_y + 20, VIDEO_WIDTH - 260, pal["text"], align="center", max_lines=1)


# =========================================================================
# 12. HYBRID MERGE DIAGRAM (Left Pillar + Right Pillar -> Merged System -> Outcomes)
# =========================================================================
def _render_hybrid_merge(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    pal = _ACTIVE_PAL
    lp = data.get("left_pillar") or {"label": "Pillar 1", "sub": ""}
    rp = data.get("right_pillar") or {"label": "Pillar 2", "sub": ""}
    merged = data.get("merged_label") or "Combined System"
    merge_badge = str(data.get("merge_badge") or "").strip().upper()
    outcomes = data.get("outcomes") or []

    pw, ph = 420, 175
    top_y = 435
    lx, rx = 75, VIDEO_WIDTH - 75 - pw

    # 1. Left & Right Input Pillars
    draw.rounded_rectangle((lx, top_y, lx + pw, top_y + ph), radius=24, fill=pal["card_bg"], outline=pal["purple"], width=3)
    draw_wrapped_text(draw, str(lp.get("label", "Pillar 1")), get_font(30, bold=True), lx + 20, top_y + 36, pw - 40, pal["purple"], align="center", max_lines=1)
    draw_wrapped_text(draw, str(lp.get("sub", "")), get_font(22), lx + 20, top_y + 88, pw - 40, pal["text"], align="center", max_lines=2)

    if progress >= 0.14:
        draw.ellipse((VIDEO_WIDTH // 2 - 28, top_y + ph // 2 - 28, VIDEO_WIDTH // 2 + 28, top_y + ph // 2 + 28), fill=pal["bg"], outline=pal["amber"], width=3)
        draw.text((VIDEO_WIDTH // 2 - 11, top_y + ph // 2 - 20), "+", fill=pal["amber"], font=get_font(36, bold=True))

        draw.rounded_rectangle((rx, top_y, rx + pw, top_y + ph), radius=24, fill=pal["card_bg"], outline=pal["cyan"], width=3)
        draw_wrapped_text(draw, str(rp.get("label", "Pillar 2")), get_font(30, bold=True), rx + 20, top_y + 36, pw - 40, pal["cyan"], align="center", max_lines=1)
        draw_wrapped_text(draw, str(rp.get("sub", "")), get_font(22), rx + 20, top_y + 88, pw - 40, pal["text"], align="center", max_lines=2)

    # 2. Converging Dotted/Glowing Merge Arrows -> Merged Block
    merge_y = 770
    mw, mh = 700, 150
    mx = (VIDEO_WIDTH - mw) // 2
    arr_t = _stage_reveal(progress, 0.28, 0.48)
    _draw_data_packet_arrow(draw, (lx + pw // 2, top_y + ph), (mx + 160, merge_y), progress=progress, color=pal["purple"], reveal_t=arr_t)
    _draw_data_packet_arrow(draw, (rx + pw // 2, top_y + ph), (mx + mw - 160, merge_y), progress=progress, color=pal["cyan"], reveal_t=arr_t)

    if progress >= 0.42:
        draw.rounded_rectangle((mx, merge_y, mx + mw, merge_y + mh), radius=26, fill=pal["emerald_bg"], outline=pal["emerald"], width=4)
        if merge_badge:
            draw_wrapped_text(draw, merge_badge, get_font(20, bold=True), mx + 30, merge_y + 24, mw - 60, pal["emerald"], align="center", max_lines=1)
            draw_wrapped_text(draw, str(merged), get_font(34, bold=True), mx + 30, merge_y + 66, mw - 60, pal["text"], align="center", max_lines=1)
        else:
            draw_wrapped_text(draw, str(merged), get_font(36, bold=True), mx + 30, merge_y + 52, mw - 60, pal["text"], align="center", max_lines=1)

    # 3. Three Outcome Badges popping in one by one
    if outcomes and progress >= 0.60:
        out_y = 1030
        bw = 290
        gap = 25
        start_x = (VIDEO_WIDTH - (bw * 3 + gap * 2)) // 2
        colors = [pal["emerald"], pal["cyan"], pal["amber"]]
        for idx, out_lbl in enumerate(outcomes[:3]):
            if progress < (0.60 + idx * 0.11):
                continue
            bx = start_x + idx * (bw + gap)
            c = colors[idx % len(colors)]
            draw.rounded_rectangle((bx, out_y, bx + bw, out_y + 135), radius=22, fill=pal["card_bg"], outline=c, width=3)
            _draw_vector_check(draw, bx + bw // 2, out_y + 42, radius=18)
            draw_wrapped_text(draw, str(out_lbl).upper(), get_font(22, bold=True), bx + 12, out_y + 80, bw - 24, pal["text"], align="center", max_lines=1)

def _draw_vector_warning(draw: ImageDraw.Draw, cx: int, cy: int, radius: int = 34) -> None:
    pal = _ACTIVE_PAL
    rose = pal["rose"]
    ink = pal["text"]
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(rose[0], rose[1], rose[2], 45), outline=rose, width=4)
    draw.line((cx, cy - max(8, int(radius * 0.42)), cx, cy + max(3, int(radius * 0.15))), fill=ink, width=4)
    draw.ellipse((cx - 3, cy + max(6, int(radius * 0.30)), cx + 3, cy + max(12, int(radius * 0.48))), fill=ink)

def _draw_vector_check(draw: ImageDraw.Draw, cx: int, cy: int, radius: int = 34) -> None:
    pal = _ACTIVE_PAL
    em = pal["emerald"]
    ink = pal["text"]
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(em[0], em[1], em[2], 45), outline=em, width=4)
    points = [
        (cx - radius * 0.45, cy),
        (cx - radius * 0.1, cy + radius * 0.35),
        (cx + radius * 0.5, cy - radius * 0.35)
    ]
    draw.line(points, fill=ink, width=4)

def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    return (56, 189, 248)


# =========================================================================
# 13. KINETIC STATEMENT (Minimalist High-Impact Typographic Focus — Full Reveal Guaranteed)
# =========================================================================
def _render_kinetic_statement(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    pal = _ACTIVE_PAL
    kicker = str(data.get("kicker") or "").strip().upper()
    statement = str(data.get("statement") or data.get("title") or "").strip()
    hl_word = str(data.get("highlight_word") or "").strip().lower()
    tags = data.get("bottom_tags") or []

    # Expanding luminous divider line across center stage
    line_w = int(680 * _stage_reveal(progress, 0.0, 0.22))
    lx_mid = VIDEO_WIDTH // 2
    draw.line((lx_mid - line_w // 2, 455, lx_mid + line_w // 2, 455), fill=pal["amber"], width=4)
    if kicker:
        draw_wrapped_text(draw, kicker, get_font(26, bold=True), 120, 405, VIDEO_WIDTH - 240, pal["amber"], align="center", max_lines=1)

    # Reveal 100% of statement words well before scene end (by progress >= 0.65)
    words = statement.split()
    total_w = len(words)
    vis_words = total_w if progress >= 0.65 else max(2, int(math.ceil(total_w * min(1.0, 0.25 + progress * 1.25))))
    shown_words = words[:vis_words]

    # Dynamic font scaling so longer takeaways never truncate or overflow
    font_size = 56 if total_w <= 9 else (48 if total_w <= 15 else 42)
    font_big = get_font(font_size, bold=True)
    line_h = font_size + 24

    # Measure and wrap ALL words cleanly into balanced centered lines
    lines = []
    cur = []
    for w in shown_words:
        test = " ".join(cur + [w])
        if (font_big.getbbox(test)[2] - font_big.getbbox(test)[0]) <= 880:
            cur.append(w)
        else:
            if cur:
                lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)

    y_cursor = 525
    for line_words in lines[:6]:
        line_str = " ".join(line_words)
        line_bbox = font_big.getbbox(line_str)
        line_px = line_bbox[2] - line_bbox[0]
        cur_x = (VIDEO_WIDTH - line_px) // 2
        for w in line_words:
            is_hl = bool(hl_word and hl_word in w.lower())
            fill_c = pal["cyan"] if is_hl else pal["text"]
            w_draw = w + " "
            draw.text((cur_x, y_cursor), w_draw, fill=fill_c, font=font_big)
            if is_hl:
                wb = font_big.getbbox(w)
                draw.line((cur_x, y_cursor + font_size + 10, cur_x + (wb[2] - wb[0]), y_cursor + font_size + 10), fill=pal["amber"], width=5)
            cur_x += font_big.getbbox(w_draw)[2] - font_big.getbbox(w_draw)[0]
        y_cursor += line_h

    # Clean floating bottom accent tags (appear progressively >= 0.42 so all 3 are visible cleanly)
    if tags and progress >= 0.42:
        tag_y = max(y_cursor + 50, 1030)
        spacing = 24
        tag_w = 270
        visible_tags = tags[:3]
        total_tags_w = len(visible_tags) * tag_w + (len(visible_tags) - 1) * spacing
        tx0 = (VIDEO_WIDTH - total_tags_w) // 2
        for idx, tg in enumerate(visible_tags):
            if progress < (0.42 + idx * 0.08):
                continue
            bx = tx0 + idx * (tag_w + spacing)
            draw.rounded_rectangle((bx, tag_y, bx + tag_w, tag_y + 72), radius=36, fill=pal["card_bg"], outline=pal["emerald"], width=3)
            draw_wrapped_text(draw, str(tg).upper(), get_font(21, bold=True), bx + 12, tag_y + 22, tag_w - 24, pal["text"], align="center", max_lines=1)


# =========================================================================
# 14. STEP TIMELINE (Glowing Vertical Progress Rail + Numbered Milestones)
# =========================================================================
def _render_step_timeline(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    pal = _ACTIVE_PAL
    steps = data.get("steps") or data.get("nodes") or []
    if not steps:
        steps = [
            {"num": "01", "title": "Trigger & Ingest", "desc": "Incoming user query arrives"},
            {"num": "02", "title": "Retrieve Context", "desc": "Semantic search matches live docs"},
            {"num": "03", "title": "Inject & Reason", "desc": "Prompt carries grounded facts"},
            {"num": "04", "title": "Stream Response", "desc": "Deterministic output returned"}
        ]
    steps = steps[:4]
    n = len(steps)
    rail_x = 155
    start_y = 450
    gap = 215 if n <= 4 else 180
    end_y = start_y + (n - 1) * gap

    # Background vertical rail + animated glowing active progress fill
    rail_track = (203, 213, 225, 220) if pal.get("is_light") else (51, 65, 85, 220)
    draw.line((rail_x, start_y, rail_x, end_y), fill=rail_track, width=8)
    fill_y = start_y + int((end_y - start_y) * min(1.0, progress * 1.05))
    draw.line((rail_x, start_y, rail_x, fill_y), fill=pal["cyan"], width=8)

    colors = [pal["cyan"], pal["purple"], pal["amber"], pal["emerald"]]
    for i, st_item in enumerate(steps):
        gate = 0.0 if i == 0 else (i * (0.80 / max(1, n - 1)))
        if progress < gate:
            continue
        sy = start_y + i * gap
        c = colors[i % len(colors)]
        is_active = (gate <= progress < gate + 0.28)
        num_txt = str(st_item.get("num") or f"0{i+1}")
        st_title = str(st_item.get("title") or st_item.get("label") or f"Step {i+1}")
        st_desc = str(st_item.get("desc") or st_item.get("sub") or "")

        # Glowing milestone circle node
        r = 38 if is_active else 34
        draw.ellipse((rail_x - r, sy - r, rail_x + r, sy + r), fill=pal["card_bg"], outline=c, width=4)
        nb = get_font(26, bold=True).getbbox(num_txt)
        draw.text((rail_x - (nb[2] - nb[0]) // 2, sy - 16), num_txt, fill=c, font=get_font(26, bold=True))

        # Horizontal branch line into floating row text
        draw.line((rail_x + r, sy, rail_x + r + 35, sy), fill=c, width=3)
        rx = rail_x + r + 48
        rw = VIDEO_WIDTH - rx - 80
        draw.rounded_rectangle((rx, sy - 62, rx + rw, sy + 62), radius=18, fill=pal["card_bg"], outline=c if is_active else pal["card_border"], width=3 if is_active else 1)
        draw_wrapped_text(draw, st_title, get_font(31, bold=True), rx + 26, sy - 42, rw - 52, pal["text"], max_lines=1)
        if st_desc:
            draw_wrapped_text(draw, st_desc, get_font(23), rx + 26, sy + 6, rw - 52, pal["muted"], max_lines=2)

# =========================================================================
# ALL-IN-ONE TECH CANVAS VECTOR SHAPES & 2D MOTION GRAPHICS
# =========================================================================

def _draw_database_cylinder(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    w: int = 240,
    h: int = 180,
    label: str = "PostgreSQL DB",
    sub: str = "Storage Cylinder (ACID)",
    color: Tuple[int, int, int] = NEON_CYAN,
    progress: float = 0.0
) -> None:
    """Draws a 2D isometric/cylindrical database storage unit with disk partitions and animated write-pulse."""
    x1 = cx - w // 2
    x2 = cx + w // 2
    y1 = cy - h // 2
    y2 = cy + h // 2
    ellipse_h = 42

    body_top = y1 + ellipse_h // 2
    body_bot = y2 - ellipse_h // 2
    draw.rectangle((x1, body_top, x2, body_bot), fill=(15, 23, 42, 240))
    draw.line((x1, body_top, x1, body_bot), fill=color, width=3)
    draw.line((x2, body_top, x2, body_bot), fill=color, width=3)

    # Bottom curved base
    draw.ellipse((x1, y2 - ellipse_h, x2, y2), fill=(15, 23, 42, 240), outline=color, width=3)

    # Disk partitions across height (showing internal storage sectors)
    num_disks = 3
    disk_gap = (body_bot - body_top) // num_disks
    active_disk = int((progress * 4) % num_disks)
    for i in range(1, num_disks):
        dy = body_top + (i * disk_gap)
        is_active = (i == active_disk)
        disk_color = NEON_AMBER if is_active else (color[0], color[1], color[2], 140)
        draw.arc((x1, dy - ellipse_h // 2, x2, dy + ellipse_h // 2), start=0, end=180, fill=disk_color, width=2 if not is_active else 4)

    # Top Cap (Perspective Lid)
    draw.ellipse((x1, y1, x2, y1 + ellipse_h), fill=(24, 35, 58, 255), outline=color, width=3)

    # Active blinking read/write LED on the top rim
    led_blink = (int(progress * 8) % 2 == 0)
    led_x = x2 - 28
    led_y = y1 + ellipse_h // 2
    draw.ellipse((led_x - 5, led_y - 5, led_x + 5, led_y + 5), fill=NEON_EMERALD if led_blink else (51, 65, 85))

    # Text Labels (dark backing pill inside cylinder so ring lines never cut through text + sub cleanly below base!)
    lbl_bg_y1, lbl_bg_y2 = cy - 16, cy + 20
    draw.rounded_rectangle((x1 + 14, lbl_bg_y1, x2 - 14, lbl_bg_y2), radius=8, fill=(11, 18, 33, 220))
    draw_wrapped_text(draw, label, get_font(19, bold=True), x1 - 15, cy - 11, w + 30, TEXT_PRIMARY, align="center", max_lines=1)
    draw_wrapped_text(draw, sub, get_font(15), x1 - 15, y2 + 6, w + 30, color, align="center", max_lines=1)


def _draw_server_rack(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    w: int = 260,
    h: int = 165,
    label: str = "K8s Worker Pod",
    sub: str = "EC2 Cluster",
    color: Tuple[int, int, int] = NEON_PURPLE,
    progress: float = 0.0
) -> None:
    """Draws a datacenter blade server rack with cooling ventilation grilles and blinking LED lights."""
    x1 = cx - w // 2
    x2 = cx + w // 2
    y1 = cy - h // 2
    y2 = cy + h // 2

    # Chassis
    draw.rounded_rectangle((x1, y1, x2, y2), radius=16, fill=(15, 23, 42, 245), outline=color, width=3)

    # 3 Blade Unit Bays
    bay_h = (h - 24) // 3
    for b in range(3):
        by1 = y1 + 8 + (b * bay_h)
        by2 = by1 + bay_h - 5
        draw.rounded_rectangle((x1 + 10, by1, x2 - 10, by2), radius=7, fill=(30, 41, 59, 230), outline=(51, 65, 85), width=1)

        # Ventilation Grille Lines
        for g in range(4):
            gx = x1 + 22 + (g * 14)
            draw.line((gx, by1 + 5, gx, by2 - 5), fill=(71, 85, 105), width=2)

        # Blinking Status LEDs
        led1 = (int(progress * 12 + b) % 2 == 0)
        led2 = (int(progress * 9 + b) % 3 != 0)
        draw.ellipse((x2 - 36, by1 + 8, x2 - 28, by1 + 16), fill=NEON_EMERALD if led1 else (20, 80, 50))
        draw.ellipse((x2 - 22, by1 + 8, x2 - 14, by1 + 16), fill=NEON_CYAN if led2 else (30, 60, 90))

    # Central Label Badge
    draw_wrapped_text(draw, label, get_font(19, bold=True), x1 - 10, y2 - 42, w + 20, TEXT_PRIMARY, align="center", max_lines=2, line_spacing=2)


def _draw_ai_robot(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    size: int = 170,
    label: str = "AI Agent / LLM",
    sub: str = "Transformer Core",
    progress: float = 0.0
) -> None:
    """Draws an intelligent 2D AI Bot/Robot with scanning digital visor and pulsing antenna radio waves."""
    hw = size // 2
    hh = (size - 20) // 2
    x1, y1, x2, y2 = cx - hw, cy - hh, cx + hw, cy + hh

    # Pulsing RF Waves from Antenna
    for r in range(1, 3):
        wave_pulse = (progress * 2.0 + (r * 0.4)) % 1.0
        rad = int(22 + wave_pulse * 30)
        alpha = int(180 * (1.0 - wave_pulse))
        draw.arc((cx - rad, y1 - 30 - rad, cx + rad, y1 - 30 + rad), start=210, end=330, fill=(168, 85, 247, alpha), width=3)

    # Antenna
    draw.line((cx, y1, cx, y1 - 22), fill=NEON_PURPLE, width=4)
    draw.ellipse((cx - 6, y1 - 30, cx + 6, y1 - 18), fill=NEON_AMBER)

    # Ear pods
    draw.rounded_rectangle((x1 - 10, cy - 18, x1, cy + 18), radius=5, fill=NEON_CYAN)
    draw.rounded_rectangle((x2, cy - 18, x2 + 10, cy + 18), radius=5, fill=NEON_CYAN)

    # Head Chassis
    draw.rounded_rectangle((x1, y1, x2, y2), radius=26, fill=(15, 23, 42, 250), outline=NEON_PURPLE, width=3)

    # Digital Visor Window
    vx1, vy1, vx2, vy2 = x1 + 16, y1 + 20, x2 - 16, y1 + 68
    draw.rounded_rectangle((vx1, vy1, vx2, vy2), radius=12, fill=(10, 15, 28, 255), outline=(56, 189, 248, 120), width=2)

    # Scanning Neon Eyes / Visor Beam
    scan_x = int(vx1 + 10 + ((vx2 - vx1 - 42) * (0.5 + 0.5 * math.sin(progress * 8))))
    draw.rounded_rectangle((scan_x, vy1 + 8, scan_x + 30, vy2 - 8), radius=6, fill=NEON_CYAN)

    # Neural Waveform Bars at bottom of visor
    for i in range(5):
        bx = cx - 34 + (i * 17)
        bar_h = int(6 + 12 * abs(math.sin(progress * 12 + i)))
        draw.line((bx, y2 - 25, bx, y2 - 25 - bar_h), fill=NEON_EMERALD, width=3)

    # Label
    draw_wrapped_text(draw, label, get_font(18, bold=True), x1 - 45, y2 + 6, size + 90, TEXT_PRIMARY, align="center", max_lines=2, line_spacing=2)
    draw_wrapped_text(draw, sub, get_font(14), x1 - 45, y2 + 48, size + 90, NEON_PURPLE, align="center", max_lines=1)


def _draw_python_chip(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    size: int = 175,
    label: str = "Python 3.12 Engine",
    sub: str = "GIL & Threading",
    progress: float = 0.0
) -> None:
    """Draws a silicon microchip with Python dual-snake colors (Blue & Gold) and etched circuits."""
    hw = size // 2
    x1, y1, x2, y2 = cx - hw, cy - hw, cx + hw, cy + hw

    # Gold Pin Leads (Left & Right)
    for p in range(5):
        py = y1 + 18 + (p * 27)
        draw.line((x1 - 15, py, x1, py), fill=(251, 191, 36), width=3)
        draw.line((x2, py, x2 + 15, py), fill=(251, 191, 36), width=3)

    # Silicon Chip Body
    draw.rounded_rectangle((x1, y1, x2, y2), radius=16, fill=(15, 23, 42, 245), outline=NEON_CYAN, width=3)

    # Python Snake Glyphs
    draw.rounded_rectangle((cx - 34, cy - 38, cx + 16, cy - 6), radius=7, fill=(56, 189, 248, 220))
    draw.ellipse((cx - 16, cy - 30, cx - 10, cy - 24), fill=COLOR_BG_DARK)
    draw.rounded_rectangle((cx - 16, cy + 6, cx + 34, cy + 38), radius=7, fill=(251, 191, 36, 220))
    draw.ellipse((cx + 10, cy + 24, cx + 16, cy + 30), fill=COLOR_BG_DARK)

    # Label
    draw_wrapped_text(draw, label, get_font(18, bold=True), x1 - 45, y2 + 6, size + 90, TEXT_PRIMARY, align="center", max_lines=2, line_spacing=2)
    draw_wrapped_text(draw, sub, get_font(14), x1 - 45, y2 + 48, size + 90, NEON_AMBER, align="center", max_lines=1)


def _draw_s3_bucket(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    w: int = 210,
    h: int = 170,
    label: str = "Amazon S3 Lake",
    sub: str = "Parquet / Delta",
    color: Tuple[int, int, int] = NEON_EMERALD,
    progress: float = 0.0
) -> None:
    """Draws an Amazon S3 storage bucket shape with metallic wire handle and data levels."""
    x1 = cx - w // 2
    x2 = cx + w // 2
    y1 = cy - h // 2
    y2 = cy + h // 2
    rim_h = 36

    # Wire Handle
    draw.arc((cx - 52, y1 - 26, cx + 52, y1 + 16), start=180, end=360, fill=(148, 163, 184), width=3)

    # Tapered Bucket Body
    taper = 18
    poly = [
        (x1, y1 + rim_h // 2),
        (x2, y1 + rim_h // 2),
        (x2 - taper, y2),
        (x1 + taper, y2)
    ]
    draw.polygon(poly, fill=(15, 23, 42, 245), outline=color)

    # Top Rim
    draw.ellipse((x1, y1, x2, y1 + rim_h), fill=(30, 41, 59, 255), outline=color, width=3)

    # Storage Fill Waves
    wave_h = y2 - 30
    draw.line((x1 + taper + 8, wave_h, x2 - taper - 8, wave_h), fill=NEON_EMERALD, width=3)

    # Labels
    draw_wrapped_text(draw, label, get_font(19, bold=True), x1 - 10, cy - 8, w + 20, TEXT_PRIMARY, align="center", max_lines=1)
    draw_wrapped_text(draw, sub, get_font(15), x1 - 10, cy + 14, w + 20, NEON_EMERALD, align="center", max_lines=1)


def _draw_cloud_vpc_boundary(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str = "AWS VPC REGION (us-east-1)",
    color: Tuple[int, int, int] = NEON_CYAN
) -> None:
    """Draws a crisp dark-embedded glowing cloud/VPC security boundary enclosing vector nodes."""
    fill_col = (15, 23, 42, 245) if _ACTIVE_PAL.get("is_light") else (15, 23, 42, 165)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=fill_col, outline=color, width=3)
    clean_lbl = label.strip()
    lbl_font = get_font(17, bold=True)
    bbox = lbl_font.getbbox(clean_lbl)
    text_w = bbox[2] - bbox[0]
    badge_w = min(680, text_w + 52)
    draw.rounded_rectangle((x + 28, y - 18, x + 28 + badge_w, y + 18), radius=14, fill=(15, 23, 42, 248), outline=color, width=2)
    draw.ellipse((x + 42, y - 6, x + 54, y + 6), fill=color)
    draw.text((x + 62, y - 11), clean_lbl, fill=color, font=lbl_font)


def _draw_data_packet_arrow(
    draw: ImageDraw.Draw,
    p1: Tuple[int, int],
    p2: Tuple[int, int],
    label: str = "",
    progress: float = 0.0,
    color: Tuple[int, int, int] = NEON_CYAN,
    reveal_t: float = 1.0
) -> None:
    """
    Draws a progressive dotted/glowing data flow connection line.
    - When reveal_t <= 0: hidden.
    - When 0 < reveal_t < 1: animates growing dotted pipeline from p1 to p2 with glowing tip.
    - When reveal_t >= 1: complete pipeline with arrowhead + moving blinking data packets.
    """
    if reveal_t <= 0.02:
        return

    x1, y1 = p1
    x2, y2 = p2
    cx2 = x1 + (x2 - x1) * min(1.0, reveal_t)
    cy2 = y1 + (y2 - y1) * min(1.0, reveal_t)

    # Animated dashed/dotted base line
    dist = math.hypot(cx2 - x1, cy2 - y1)
    if dist < 2:
        return
    ux = (cx2 - x1) / dist
    uy = (cy2 - y1) / dist

    dash_len = 14
    gap_len = 10
    step = dash_len + gap_len
    dash_offset = (progress * 120) % step
    pos = -dash_offset
    while pos < dist:
        seg_start = max(0.0, pos)
        seg_end = min(dist, pos + dash_len)
        if seg_end > seg_start:
            sx1, sy1 = x1 + ux * seg_start, y1 + uy * seg_start
            sx2, sy2 = x1 + ux * seg_end, y1 + uy * seg_end
            draw.line((sx1, sy1, sx2, sy2), fill=(*color, 180), width=4)
        pos += step

    # Glowing leading tip while line is drawing
    if reveal_t < 0.98:
        draw.ellipse((cx2 - 12, cy2 - 12, cx2 + 12, cy2 + 12), fill=(*color, 110))
        draw.ellipse((cx2 - 6, cy2 - 6, cx2 + 6, cy2 + 6), fill=TEXT_PRIMARY)
        return

    # Full arrowhead once connected
    ang = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 16
    arrow_ang = math.pi / 6
    ax1 = x2 - arrow_len * math.cos(ang - arrow_ang)
    ay1 = y2 - arrow_len * math.sin(ang - arrow_ang)
    ax2 = x2 - arrow_len * math.cos(ang + arrow_ang)
    ay2 = y2 - arrow_len * math.sin(ang + arrow_ang)
    draw.polygon([(x2, y2), (ax1, ay1), (ax2, ay2)], fill=color)

    # Blinking / moving data packets along the connected line
    num_packets = 2
    for pk in range(num_packets):
        t = (progress * 2.4 + (pk * (1.0 / num_packets))) % 1.0
        if 0.05 < t < 0.95:
            px = int(x1 + (x2 - x1) * t)
            py = int(y1 + (y2 - y1) * t)
            draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=(*color, 95))
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=TEXT_PRIMARY)

    if label:
        mx = (x1 + x2) // 2
        my = (y1 + y2) // 2 - 16
        lbl_font = get_font(14, bold=True)
        bbox = lbl_font.getbbox(label)
        tw = bbox[2] - bbox[0]
        bw = tw + 20
        draw.rounded_rectangle((mx - bw // 2, my - 12, mx + bw // 2, my + 12), radius=8, fill=(15, 23, 42, 235), outline=(51, 65, 85), width=1)
        draw.text((mx - tw // 2, my - 9), label, fill=NEON_AMBER, font=lbl_font)


def _draw_motion_pointer(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    label: str = "ACTIVE EXECUTION",
    progress: float = 0.0,
    color: Tuple[int, int, int] = NEON_ROSE
) -> None:
    """Draws an animated target reticle / motion spotlight pointing at a critical component."""
    pulse = (progress * 2.5) % 1.0
    r = int(30 + pulse * 22)
    alpha = int(200 * (1.0 - pulse))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*color, alpha), width=3)
    draw.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=(*color, 90), outline=color, width=2)
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=TEXT_PRIMARY)

    draw.line((cx - 22, cy, cx - 13, cy), fill=color, width=2)
    draw.line((cx + 13, cy, cx + 22, cy), fill=color, width=2)
    draw.line((cx, cy - 22, cx, cy - 13), fill=color, width=2)
    draw.line((cx, cy + 13, cx, cy + 22), fill=color, width=2)

    if label:
        lbl_font = get_font(14, bold=True)
        lbl_txt = f">> {label}"
        bbox = lbl_font.getbbox(lbl_txt)
        tw = bbox[2] - bbox[0]
        pw = tw + 20
        ly = cy - 46
        draw.rounded_rectangle((cx - pw // 2, ly - 12, cx + pw // 2, ly + 12), radius=10, fill=(11, 15, 25, 235), outline=color, width=1)
        draw.text((cx - tw // 2, ly - 9), lbl_txt, fill=color, font=lbl_font)


def _draw_semantic_node(
    draw: ImageDraw.Draw,
    cx: int,
    cy: int,
    label: str,
    sub: str,
    progress: float,
    default_shape: str = "rack",
    color: Tuple[int, int, int] = NEON_CYAN
) -> None:
    """Chooses the right vector icon semantically from label keywords (e.g. LLM Engine won't draw as a DB cylinder!)."""
    lbl_l = f"{label} {sub}".lower()
    if any(k in lbl_l for k in ["s3", "bucket", "lake", "parquet", "archive"]):
        shape = "bucket"
    elif any(k in lbl_l for k in ["postgres", "mysql", "aurora", "oracle", "sql", "database", "db", "store"]):
        shape = "db"
    elif any(k in lbl_l for k in ["llm", "agent", "ai", "model", "reason", "vector", "embed"]):
        shape = "robot"
    elif any(k in lbl_l for k in ["python", "api", "source", "client", "ingest", "code"]):
        shape = "chip"
    else:
        shape = default_shape

    if shape == "chip":
        _draw_python_chip(draw, cx=cx, cy=cy, size=165, label=label, sub=sub, progress=progress)
    elif shape == "robot":
        _draw_ai_robot(draw, cx=cx, cy=cy, size=160, label=label, sub=sub, progress=progress)
    elif shape == "db":
        _draw_database_cylinder(draw, cx=cx, cy=cy, w=250, h=165, label=label, sub=sub, color=color, progress=progress)
    elif shape == "bucket":
        _draw_s3_bucket(draw, cx=cx, cy=cy, w=220, h=160, label=label, sub=sub, color=color, progress=progress)
    else:
        _draw_server_rack(draw, cx=cx, cy=cy, w=280, h=160, label=label, sub=sub, color=color, progress=progress)


def _render_all_in_one_tech_canvas(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """
    Voice-Synced Progressive Reveal 2D Architecture Canvas:
    Objects and dotted/glowing pipeline arrows appear STEP-BY-STEP from 0.0s,
    using semantic icons and clean spacing so pointers never touch VPC borders.
    """
    # 1. Cloud & VPC Boundary
    vpc_label = data.get("vpc_label") or "SYSTEM ARCHITECTURE • HIGH AVAILABILITY"
    _draw_cloud_vpc_boundary(draw, 50, 425, 980, 815, label=vpc_label, color=NEON_CYAN)

    # Node 1 visible immediately at 0.0s (no blank frame)
    show_c1 = True
    arrow1_t = _stage_reveal(progress, 0.10, 0.25)
    show_c3 = progress >= 0.20
    show_c2 = progress >= 0.34
    arrow2_t = _stage_reveal(progress, 0.40, 0.54)
    arrow3_t = _stage_reveal(progress, 0.55, 0.68)
    show_c4 = progress >= 0.60
    arrow4_t = _stage_reveal(progress, 0.70, 0.82)
    show_c5 = progress >= 0.75
    show_hud = progress >= 0.85

    # 2. Semantic Component Placement (clear vertical clearance under VPC badge y=425)
    c1_lbl = data.get("comp1_label") or "Client / Ingestion"
    c1_sub = data.get("comp1_sub") or "API & Request Layer"
    if show_c1:
        _draw_semantic_node(draw, 260, 595, c1_lbl, c1_sub, progress, default_shape="chip", color=NEON_CYAN)

    c2_lbl = data.get("comp2_label") or "AI Agent / Compute"
    c2_sub = data.get("comp2_sub") or "Reasoning & Logic"
    if show_c2:
        _draw_semantic_node(draw, 820, 595, c2_lbl, c2_sub, progress, default_shape="robot", color=NEON_PURPLE)

    c3_lbl = data.get("comp3_label") or "Core Orchestrator"
    c3_sub = data.get("comp3_sub") or "Distributed Pipeline"
    if show_c3:
        _draw_semantic_node(draw, 540, 810, c3_lbl, c3_sub, progress, default_shape="rack", color=NEON_PURPLE)

    c4_lbl = data.get("comp4_label") or "Primary Database"
    c4_sub = data.get("comp4_sub") or "Transactional Store"
    if show_c4:
        _draw_semantic_node(draw, 270, 1075, c4_lbl, c4_sub, progress, default_shape="db", color=NEON_CYAN)

    c5_lbl = data.get("comp5_label") or "Target Sink / Lake"
    c5_sub = data.get("comp5_sub") or "Analytics & Output"
    if show_c5:
        _draw_semantic_node(draw, 810, 1075, c5_lbl, c5_sub, progress, default_shape="bucket", color=NEON_EMERALD)

    # 3. Progressive Dotted/Glowing Pipeline Arrows
    a1_lbl = data.get("arrow1_label") or "Stream"
    a2_lbl = data.get("arrow2_label") or "Retrieve / Compute"
    a3_lbl = data.get("arrow3_label") or "State Write"
    a4_lbl = data.get("arrow4_label") or "Output Sync"

    _draw_data_packet_arrow(draw, (350, 615), (450, 750), label=a1_lbl, progress=progress, color=NEON_CYAN, reveal_t=arrow1_t)
    _draw_data_packet_arrow(draw, (730, 615), (630, 750), label=a2_lbl, progress=progress, color=NEON_PURPLE, reveal_t=arrow2_t)
    _draw_data_packet_arrow(draw, (440, 890), (330, 985), label=a3_lbl, progress=progress, color=NEON_AMBER, reveal_t=arrow3_t)
    _draw_data_packet_arrow(draw, (640, 890), (750, 985), label=a4_lbl, progress=progress, color=NEON_EMERALD, reveal_t=arrow4_t)

    # 4. Active Motion Pointer cleanly below top VPC pill
    if progress < 0.20:
        px, py, plbl = 260, 508, "STEP 1: INPUT"
    elif progress < 0.34:
        px, py, plbl = 540, 718, "STEP 2: ORCHESTRATE"
    elif progress < 0.60:
        px, py, plbl = 820, 508, "STEP 3: PROCESS"
    elif progress < 0.75:
        px, py, plbl = 270, 978, "STEP 4: STAGE"
    else:
        px, py, plbl = 810, 978, "STEP 5: OUTPUT"
    _draw_motion_pointer(draw, px, py, label=plbl, progress=progress, color=NEON_AMBER)

    # 5. Optional Bottom Status Tag or explicit HUD (zero fake placeholder metrics!)
    if show_hud:
        pal = _ACTIVE_PAL
        hx, hy, hw, hh = 50, 1265, 980, 155
        status_tag = data.get("status_tag") or data.get("bottom_tag")
        hud_items = data.get("hud_items")
        if status_tag:
            draw.rounded_rectangle((hx, hy + 20, hx + hw, hy + 115), radius=22, fill=pal["emerald_bg"], outline=pal["emerald"], width=3)
            draw_wrapped_text(draw, str(status_tag).upper(), get_font(26, bold=True), hx + 30, hy + 52, hw - 60, pal["emerald"], align="center", max_lines=1)
        elif isinstance(hud_items, list) and len(hud_items) >= 2:
            draw.rounded_rectangle((hx, hy, hx + hw, hy + hh), radius=22, fill=pal["card_bg"], outline=pal["accent"], width=3)
            col_w = hw // min(3, len(hud_items))
            for h_idx, h_it in enumerate(hud_items[:3]):
                DrawX = hx + (col_w * h_idx) + 25
                draw_wrapped_text(draw, str(h_it.get("label", "")).upper(), get_font(18, bold=True), DrawX, hy + 24, col_w - 40, pal["accent"], max_lines=1)
                draw_wrapped_text(draw, str(h_it.get("val", "")), get_font(28, bold=True), DrawX, hy + 62, col_w - 40, pal["text"], max_lines=1)


def _draw_watermark(
    draw: ImageDraw.Draw,
    canvas_w: int,
    canvas_h: int,
    watermark_text: str = DEFAULT_WATERMARK
) -> None:
    """Draws a sleek channel watermark in the top-right corner adapted to light/dark art style."""
    if not watermark_text:
        return
    pal = _ACTIVE_PAL
    font_wm = get_font(24, bold=True)
    text = watermark_text.strip()
    bbox = font_wm.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x = 16
    pad_y = 8
    badge_w = tw + (pad_x * 2) + 16
    badge_h = th + (pad_y * 2)

    bx = canvas_w - badge_w - 36
    by = 44
    accent = pal["accent"]
    fill_bg = (255, 255, 255, 235) if pal.get("is_light") else (15, 23, 42, 220)
    txt_col = pal["text"]

    draw.rounded_rectangle(
        (bx - 1, by - 1, bx + badge_w + 1, by + badge_h + 1),
        radius=badge_h // 2,
        fill=(*accent, 38)
    )
    draw.rounded_rectangle(
        (bx, by, bx + badge_w, by + badge_h),
        radius=badge_h // 2,
        fill=fill_bg,
        outline=(*accent, 180),
        width=2
    )

    dot_r = 4
    dot_x = bx + pad_x + 4
    dot_y = by + (badge_h // 2)
    draw.ellipse((dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r), fill=(*accent, 255))

    tx = dot_x + dot_r + 8
    ty = by + pad_y - 2
    draw.text((tx, ty), text, fill=txt_col, font=font_wm)


def generate_thumbnail_9_16(
    topic: str,
    timeline: Any = None,
    watermark: str = DEFAULT_WATERMARK,
    visual_engine: str = "hybrid_modern",
    output_path: Any = None
) -> Path:
    """
    Generates a high-impact 1080x1920 (9:16) thumbnail image matching the reel's
    art_style and centerpiece visual (supports custom_scene & all modular engines).
    """
    import time
    canvas_w = 1080
    canvas_h = 1920
    art_style = str(timeline.get("art_style", "editorial_dark")) if isinstance(timeline, dict) else "editorial_dark"
    if visual_engine == "cinematic_studio":
        from core.cinematic_engine import (
            StudioStage,
            _build_volumetric_studio_bg,
            _draw_studio_header,
            _draw_wrapped_text as _cin_wrap,
            _get_font as _cin_font,
            dispatch_studio_layout,
            resolve_studio_world,
        )
        sc0 = timeline.get("scenes", [{}])[0] if isinstance(timeline, dict) else {}
        world = resolve_studio_world(
            art_style=art_style,
            tone=sc0.get("scene_tone", "staff_engineer") if isinstance(sc0, dict) else "staff_engineer",
            visual_data=sc0.get("visual_data", {}) if isinstance(sc0, dict) else {},
            topic=topic.strip(),
        )
        bg = _build_volumetric_studio_bg(canvas_w, canvas_h, world)
        stage = StudioStage(canvas_w, canvas_h, world)
        c_accent = world["cyan"]
        badge_text = str(sc0.get("visual_data", {}).get("badge", "")) if isinstance(sc0, dict) else ""
        _draw_studio_header(stage, badge_text, topic.strip()[:85], c_accent)
        t_sc = None
        preferred_thumb = {
            "iso_architecture", "node_graph", "iso_comparison", "spatial_canvas", "svg_scene",
            "layer_stack_3d", "matrix_2x2", "pyramid_hierarchy", "radial_gauge", "benchmark_3d",
            "sequence_diagram", "er_schema", "custom_scene", "architecture_flow",
            "split_comparison", "terminal_studio", "code_terminal",
        }
        if isinstance(timeline, dict) and timeline.get("scenes"):
            for sc in timeline["scenes"]:
                if sc.get("visual_type") in preferred_thumb:
                    t_sc = sc
                    break
            if not t_sc:
                t_sc = timeline["scenes"][0]
        if t_sc:
            dispatch_studio_layout(stage, t_sc.get("visual_type", "custom_scene"), t_sc.get("visual_data", {}), 1.0, world, topic=topic.strip())
        card_w, card_h = 940, 150
        cx, cy = (canvas_w - card_w) // 2, 1600
        stage.draw_glass_card((cx, cy, cx + card_w, cy + card_h), radius=26, accent_col=c_accent, alpha_mul=1.0, active=True)
        hook_txt = str(timeline.get("hook_headline") or topic.strip())[:70] if isinstance(timeline, dict) else topic.strip()[:70]
        _cin_wrap(stage.draw, (cx + 40, cy + 28), hook_txt, _cin_font(34, bold=True), world["text"], card_w - 80, align="center", max_lines=1)
        if watermark:
            _cin_wrap(stage.draw, (cx + 40, cy + 84), watermark, _cin_font(26, bold=True), c_accent, card_w - 80, align="center", max_lines=1)
        im_out = stage.composite_onto(bg)
        chrome = ImageDraw.Draw(im_out, "RGBA")
        _draw_story_progress_bar(chrome, total_scenes=4, current_scene=1, progress=0.25, canvas_w=canvas_w, accent=c_accent)
        if watermark:
            wm_font = _cin_font(23, bold=True)
            wt = watermark.strip()
            wbb = wm_font.getbbox(wt)
            bw = (wbb[2] - wbb[0]) + 46
            bx, by = canvas_w - bw - 36, 44
            wfill = (255, 255, 255, 234) if world["is_light"] else (15, 23, 42, 218)
            chrome.rounded_rectangle((bx, by, bx + bw, by + 38), radius=19, fill=wfill, outline=(*c_accent, 185), width=2)
            chrome.ellipse((bx + 14, by + 15, bx + 22, by + 23), fill=c_accent)
            chrome.text((bx + 30, by + 6), wt, fill=world["text"], font=wm_font)
        if output_path is None:
            output_path = OUTPUT_DIR / f"thumbnail_9x16_{int(time.time())}.png"
        im_out.convert("RGB").save(output_path, "PNG", quality=98)
        return output_path

    im, theme_cfg = _build_themed_canvas(canvas_w, canvas_h, "cyber_cyan", art_style=art_style)
    pal = _ACTIVE_PAL
    draw = ImageDraw.Draw(im, "RGBA")
    accent = pal["accent"]

    # Top story progress bar & watermark
    _draw_story_progress_bar(draw, total_scenes=4, current_scene=1, progress=0.25, canvas_w=canvas_w, accent=accent)
    _draw_watermark(draw, canvas_w, canvas_h, watermark)

    # Top category badge & headline
    badge_text = ""
    if timeline and isinstance(timeline, dict) and timeline.get("scenes"):
        badge_text = str(timeline["scenes"][0].get("visual_data", {}).get("badge", ""))
    _draw_header(draw, badge_text, topic.strip()[:85], accent=accent, art_style=art_style)

    # Centerpiece graphic (render scene visual at progress 1.0)
    target_scene = None
    if timeline and isinstance(timeline, dict) and timeline.get("scenes"):
        for sc in timeline["scenes"]:
            if sc.get("visual_type") in ["custom_scene", "architecture_flow", "code_terminal", "sql_table", "split_comparison", "benchmark_chart", "hero_hook"]:
                target_scene = sc
                break
        if not target_scene:
            target_scene = timeline["scenes"][0]

    if target_scene:
        _dispatch_visual_renderer(draw, target_scene.get("visual_type", "custom_scene"), target_scene.get("visual_data", {}), 1.0)

    # Clean bottom channel footer card (zero canned slogans)
    card_w = 940
    card_h = 150
    cx = (canvas_w - card_w) // 2
    cy = 1600
    draw.rounded_rectangle((cx, cy, cx + card_w, cy + card_h), radius=26, fill=pal["card_bg"], outline=accent, width=3)
    draw_wrapped_text(draw, str(timeline.get("hook_headline") or topic.strip())[:70] if isinstance(timeline, dict) else topic.strip()[:70], get_font(34, bold=True), cx + 40, cy + 28, card_w - 80, pal["text"], align="center", max_lines=1)
    if watermark:
        draw_wrapped_text(draw, watermark, get_font(26, bold=True), cx + 40, cy + 84, card_w - 80, accent, align="center", max_lines=1)

    if output_path is None:
        output_path = OUTPUT_DIR / f"thumbnail_9x16_{int(time.time())}.png"

    im.save(output_path, "PNG", quality=98)
    return output_path
