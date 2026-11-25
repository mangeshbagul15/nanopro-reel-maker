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
    custom_style_prompt: str = ""
) -> List[Path]:
    """
    Renders high-octane 2D frames across 10+ rich motion-graphics visual engines,
    strictly adhering to the user-selected Visual Engine & Style, Voice-Synced Progressive Reveal,
    and Target Aspect Ratio (9:16, 16:9, 1:1).
    """
    duration = max(1.5, float(scene.get("duration", 5.0)))
    total_frames = max(15, round(duration * VIDEO_FPS))
    
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
    base_canvas = Image.new("RGB", (canvas_w, canvas_h), COLOR_BG_DARK)
    needs_aspect_fit = (canvas_w != VIDEO_WIDTH or canvas_h != VIDEO_HEIGHT)
    anchors = _build_choreography_anchors(duration, scene, scene_words)
    
    for f in range(total_frames):
        linear_p = f / max(1, total_frames - 1)
        progress = _compute_voice_synced_progress(f, total_frames, duration, scene, scene_words, anchors=anchors)
        frame = base_canvas.copy()

        if needs_aspect_fit:
            # Render scene content on virtual 1080x1500 content stage, then fit cleanly onto 16:9 or 1:1
            stage = Image.new("RGBA", (VIDEO_WIDTH, 1500), (*COLOR_BG_DARK, 0))
            s_draw = ImageDraw.Draw(stage, "RGBA")
            _draw_header(s_draw, visual_data.get("badge", "TECH ARCHITECTURE"), visual_data.get("title", ""))
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
            _draw_header(draw, visual_data.get("badge", "TECH ARCHITECTURE"), visual_data.get("title", ""))
            _dispatch_visual_renderer(draw, visual_type, visual_data, progress)

        # Top Story Progress Bar & Watermark always crisp at native canvas resolution
        _draw_story_progress_bar(draw, total_scenes, scene_idx, linear_p, canvas_w=canvas_w)
        if watermark:
            _draw_watermark(draw, canvas_w, canvas_h, watermark)
            
        # Save lossless/high-fidelity crystal clear frame
        frame_file = scene_frames_dir / f"frame_{f:04d}.jpg"
        frame.convert("RGB").save(frame_file, "JPEG", quality=96, subsampling=0)
        frame_paths.append(frame_file)
        
    return frame_paths


def _dispatch_visual_renderer(draw: ImageDraw.Draw, visual_type: str, visual_data: Dict[str, Any], progress: float) -> None:
    aliases = {
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
    }
    vt = aliases.get(str(visual_type).lower().strip(), visual_type)
    if vt == "split_comparison":
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


def _draw_story_progress_bar(draw: ImageDraw.Draw, total_scenes: int, current_scene: int, progress: float, canvas_w: int = VIDEO_WIDTH) -> None:
    """Draws a continuous sleek modern YouTube Shorts / Fireship progress bar across the entire video."""
    global_progress = ((current_scene - 1) + progress) / max(1, total_scenes)
    bar_y = 25
    bar_h = 6
    padding = 40
    track_w = canvas_w - (padding * 2)
    fill_w = max(10, int(track_w * min(1.0, max(0.01, global_progress))))
    
    # Sleek dark track
    draw.rounded_rectangle((padding, bar_y, padding + track_w, bar_y + bar_h), radius=3, fill=(255, 255, 255, 35))
    # Glowing neon cyan progress
    draw.rounded_rectangle((padding, bar_y, padding + fill_w, bar_y + bar_h), radius=3, fill=NEON_CYAN)

def _draw_header(draw: ImageDraw.Draw, badge_text: str, title_text: str) -> None:
    font_badge = get_font(26, bold=True)
    font_title = get_font(44, bold=True)
    
    badge_str = badge_text.upper().strip()
    bbox = font_badge.getbbox(badge_str)
    raw_bw = bbox[2] - bbox[0]
    bw = min(880, raw_bw + 44)
    bh = 50
    bx = (VIDEO_WIDTH - bw) // 2
    by = 115
    
    draw.rounded_rectangle((bx - 2, by - 2, bx + bw + 2, by + bh + 2), radius=26, fill=(56, 189, 248, 50))
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=25, fill=(15, 23, 42, 240), outline=NEON_CYAN, width=3)
    tx_badge = bx + (bw - raw_bw) // 2
    draw.text((tx_badge, by + 10), badge_str, fill=NEON_CYAN, font=font_badge)
    
    if title_text:
        max_title_w = 940
        start_x = (VIDEO_WIDTH - max_title_w) // 2
        draw_wrapped_text(draw, title_text, font_title, start_x, by + 75, max_title_w, TEXT_PRIMARY, line_spacing=8, align="center", max_lines=2)

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
    
    col_w = 445
    card_h = 680
    top_y = 440
    lx = 65
    rx = 570
    
    # Left Card (Problem / Legacy - Red Tint) - reveals first (0.04 -> 0.45)
    if progress >= 0.03:
        draw.rounded_rectangle((lx, top_y, lx + col_w, top_y + card_h), radius=24, fill=(26, 15, 20, 245), outline=NEON_ROSE, width=3)
        draw.rounded_rectangle((lx + 20, top_y + 20, lx + col_w - 20, top_y + 80), radius=14, fill=(244, 63, 94, 40))
        draw_wrapped_text(draw, f"X  {left_label.upper()}", get_font(25, bold=True), lx + 30, top_y + 36, col_w - 60, NEON_ROSE, align="center", max_lines=1)
        
        for i, pt in enumerate(left_points[:3]):
            if progress < (0.10 + i * 0.11):
                continue
            py = top_y + 120 + (i * 170)
            draw.rounded_rectangle((lx + 20, py, lx + col_w - 20, py + 140), radius=16, fill=(15, 23, 42, 220), outline=(244, 63, 94, 80), width=1)
            draw.text((lx + 35, py + 20), "•", fill=NEON_ROSE, font=get_font(34, bold=True))
            draw_wrapped_text(draw, pt, get_font(26), lx + 65, py + 22, col_w - 100, TEXT_PRIMARY, max_lines=3, line_spacing=6)
        
    # Right Card (Solution / Modern - Green/Cyan Tint) - reveals in second half (0.48 -> 0.90)
    if progress >= 0.48:
        draw.rounded_rectangle((rx, top_y, rx + col_w, top_y + card_h), radius=24, fill=(11, 28, 26, 245), outline=NEON_EMERALD, width=3)
        draw.rounded_rectangle((rx + 20, top_y + 20, rx + col_w - 20, top_y + 80), radius=14, fill=(52, 211, 153, 40))
        draw_wrapped_text(draw, f"+  {right_label.upper()}", get_font(25, bold=True), rx + 30, top_y + 36, col_w - 60, NEON_EMERALD, align="center", max_lines=1)
        
        for i, pt in enumerate(right_points[:3]):
            if progress < (0.54 + i * 0.11):
                continue
            py = top_y + 120 + (i * 170)
            draw.rounded_rectangle((rx + 20, py, rx + col_w - 20, py + 140), radius=16, fill=(15, 23, 42, 220), outline=(52, 211, 153, 90), width=1)
            draw.text((rx + 35, py + 20), "✓", fill=NEON_EMERALD, font=get_font(30, bold=True))
            draw_wrapped_text(draw, pt, get_font(26), rx + 65, py + 22, col_w - 100, TEXT_PRIMARY, max_lines=3, line_spacing=6)
        
    # Center "VS" Badge
    if progress >= 0.42:
        vx, vy = VIDEO_WIDTH // 2, top_y + card_h // 2
        draw.ellipse((vx - 42, vy - 42, vx + 42, vy + 42), fill=(15, 23, 42), outline=NEON_AMBER, width=4)
        draw.text((vx - 22, vy - 18), "VS", fill=NEON_AMBER, font=get_font(28, bold=True))

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
    
    container_w = 940
    cx = (VIDEO_WIDTH - container_w) // 2
    start_y = 440
    
    # Outer Panel
    panel_h = 740
    draw.rounded_rectangle((cx, start_y, cx + container_w, start_y + panel_h), radius=26, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    font_lbl = get_font(30, bold=True)
    font_val = get_font(28, bold=True)
    
    bar_max_w = 860
    base_bar_y = start_y + 60
    
    for i, b in enumerate(bars[:3]):
        bar_start = 0.05 + (i * 0.22)
        bar_fill_t = _stage_reveal(progress, bar_start, bar_start + 0.22)
        if bar_fill_t <= 0.0:
            continue
        by = base_bar_y + (i * 190)
        color = _hex_to_rgb(b.get("color", "#38BDF8"))
        is_winner = b.get("is_winner", False)
        
        # Label
        draw.text((cx + 40, by), b.get("label", ""), fill=TEXT_PRIMARY, font=font_lbl)
        
        # Background track
        track_y = by + 50
        track_h = 56
        draw.rounded_rectangle((cx + 40, track_y, cx + 40 + bar_max_w, track_y + track_h), radius=14, fill=(30, 41, 59, 200))
        
        # Animated filling progress
        val_ratio = 1.0 if not is_winner and i == 0 else (0.55 if i == 1 else 0.20)
        animated_w = max(80, int(bar_max_w * val_ratio * bar_fill_t))
        
        draw.rounded_rectangle((cx + 40, track_y, cx + 40 + animated_w, track_y + track_h), radius=14, fill=(*color, 230), outline=color, width=2)
        draw.text((cx + 60, track_y + 10), b.get("display", ""), fill=(10, 15, 25) if is_winner else TEXT_PRIMARY, font=font_val)

    # Winner Banner at bottom
    if progress >= 0.72:
        wy = start_y + panel_h - 110
        draw.rounded_rectangle((cx + 40, wy, cx + container_w - 40, wy + 80), radius=18, fill=(16, 185, 129, 45), outline=NEON_EMERALD, width=3)
        draw_wrapped_text(draw, f"* {winner_badge} WITH ZERO DATA LOSS", get_font(30, bold=True), cx + 50, wy + 20, container_w - 100, NEON_EMERALD, align="center", max_lines=1)

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
    for sx, sy, sat in sat_coords:
        sw, sh = 280, 110
        color = _hex_to_rgb(sat.get("color", "#38BDF8"))
        draw.rounded_rectangle((sx - sw//2, sy - sh//2, sx + sw//2, sy + sh//2), radius=18, fill=CARD_BG, outline=color, width=3)
        draw_wrapped_text(draw, sat.get("name", ""), get_font(24, bold=True), sx - sw//2 + 10, sy - sh//2 + 18, sw - 20, TEXT_PRIMARY, align="center", max_lines=1)
        draw_wrapped_text(draw, sat.get("role", ""), get_font(18), sx - sw//2 + 10, sy - sh//2 + 56, sw - 20, TEXT_MUTED, align="center", max_lines=1)

    # Center Hub Core (Pulsing Glow)
    hub_r = 110
    draw.ellipse((center_x - hub_r - 6, center_y - hub_r - 6, center_x + hub_r + 6, center_y + hub_r + 6), fill=(56, 189, 248, 40))
    draw.ellipse((center_x - hub_r, center_y - hub_r, center_x + hub_r, center_y + hub_r), fill=(15, 23, 42, 250), outline=NEON_CYAN, width=5)
    draw_wrapped_text(draw, hub_name, get_font(30, bold=True), center_x - 90, center_y - 25, 180, NEON_CYAN, align="center", max_lines=2)

# =========================================================================
# 4. METRIC GAUGE HUD (Speedometer / Radial Telemetry)
# =========================================================================
def _render_metric_gauge_hud(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
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
    
    # Outer Background Arc
    draw.arc((arc_cx - arc_r, arc_cy - arc_r, arc_cx + arc_r, arc_cy + arc_r), start=140, end=400, fill=(30, 41, 59), width=28)
    
    # Animated Filled Arc
    fill_end = 140 + int((400 - 140) * (gauge_pct / 100.0) * min(1.0, progress * 1.5))
    draw.arc((arc_cx - arc_r, arc_cy - arc_r, arc_cx + arc_r, arc_cy + arc_r), start=140, end=fill_end, fill=NEON_EMERALD, width=28)
    
    # Center Big Stat
    draw.text((arc_cx - 200, arc_cy - 45), main_val, fill=TEXT_PRIMARY, font=get_font(68, bold=True))
    draw.text((arc_cx - 130, arc_cy + 45), main_unit, fill=NEON_EMERALD, font=get_font(28, bold=True))
    
    # 3 Telemetry Cards below
    card_w = 285
    card_h = 170
    card_y = 960
    
    for i, t in enumerate(telemetry[:3]):
        if progress < (0.35 + i * 0.18):
            continue
        cx = px + (i * (card_w + 42))
        draw.rounded_rectangle((cx, card_y, cx + card_w, card_y + card_h), radius=20, fill=CARD_BG, outline=CARD_BORDER, width=2)
        draw.text((cx + 25, card_y + 25), t.get("label", ""), fill=TEXT_MUTED, font=get_font(22, bold=True))
        draw.text((cx + 25, card_y + 75), t.get("val", ""), fill=NEON_CYAN, font=get_font(46, bold=True))

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
    
    qx, qy, qw, qh = 70, 440, 940, 140
    draw.rounded_rectangle((qx, qy, qx + qw, qy + qh), radius=20, fill=CARD_BG, outline=NEON_PURPLE, width=3)
    draw.text((qx + 30, qy + 18), "PIPELINE LOGIC:", fill=NEON_PURPLE, font=get_font(22, bold=True))
    draw_wrapped_text(draw, code, get_font(26, bold=True), qx + 30, qy + 58, 880, TEXT_PRIMARY, max_lines=2)
    
    tx, ty, tw = 70, 610, 940
    col_w = tw // max(1, len(headers))
    row_h = 90
    
    draw.rounded_rectangle((tx, ty, tx + tw, ty + row_h), radius=16, fill=(30, 41, 59, 240), outline=CARD_BORDER, width=2)
    for c_idx, h in enumerate(headers):
        h_str = str(h).upper()
        draw.text((tx + (c_idx * col_w) + 20, ty + 28), h_str, fill=NEON_CYAN, font=get_font(26, bold=True))
        
    active_row = int((progress * len(rows)) % len(rows)) if rows else 0
    for r_idx, row in enumerate(rows[:4]):
        if progress < (0.14 + r_idx * 0.18):
            continue
        ry = ty + ((r_idx + 1) * row_h) + 12
        is_highlighted = (r_idx == active_row)
        bg = (56, 189, 248, 45) if is_highlighted else CARD_BG
        border = NEON_AMBER if is_highlighted else CARD_BORDER
        
        draw.rounded_rectangle((tx, ry, tx + tw, ry + row_h - 10), radius=14, fill=bg, outline=border, width=3 if is_highlighted else 1)
        for c_idx, cell in enumerate(row[:len(headers)]):
            txt_color = NEON_AMBER if (is_highlighted and c_idx == len(row) - 1) else TEXT_PRIMARY
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
    
    node_coords = []
    # Progressive step-by-step reveal: Node 0 -> Arrow 0->1 -> Node 1 -> Arrow 1->2 -> Node 2
    step_span = 0.85 / max(1, n_count)
    for i, node in enumerate(nodes):
        node_start = 0.04 + (i * step_span)
        if progress < node_start:
            continue
        ny = start_y + (i * gap)
        node_coords.append((i, center_x + node_w // 2, ny + node_h // 2))
        color_hex = node.get("color", "#38BDF8")
        accent_rgb = _hex_to_rgb(color_hex)
        is_current_focus = (node_start <= progress < node_start + step_span)

        draw.rounded_rectangle((center_x, ny, center_x + node_w, ny + node_h), radius=22, fill=CARD_BG, outline=accent_rgb, width=4 if is_current_focus else 2)
        draw.ellipse((center_x + 35, ny + (node_h - 45) // 2, center_x + 80, ny + (node_h + 45) // 2), fill=accent_rgb)
        
        draw_wrapped_text(draw, node.get("label", ""), font_title, center_x + 100, ny + 20, 720, TEXT_PRIMARY, max_lines=1)
        sub_text = node.get("sub") or "Cloud Service"
        if isinstance(sub_text, str):
            sub_text = sub_text.title()
        draw_wrapped_text(draw, sub_text, font_sub, center_x + 100, ny + 68, 720, TEXT_MUTED, max_lines=2)

    for idx_pos in range(len(node_coords) - 1):
        i_src, x1, y1 = node_coords[idx_pos]
        _, x2, y2 = node_coords[idx_pos + 1]
        arrow_start = 0.04 + (i_src * step_span) + (step_span * 0.45)
        arrow_t = _stage_reveal(progress, arrow_start, arrow_start + (step_span * 0.55))
        _draw_data_packet_arrow(
            draw,
            (x1, y1 + node_h // 2),
            (x2, y2 - node_h // 2),
            progress=progress,
            color=NEON_CYAN,
            reveal_t=arrow_t
        )

# =========================================================================
# 10. CONCEPT COMPARISON CARDS
# =========================================================================
def _render_concept_cards(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    raw_bullets = data.get("bullets") or data.get("points") or data.get("key_points") or data.get("features") or data.get("concepts") or []
    if not raw_bullets:
        topic_title = data.get("title") or "Key System Architecture"
        raw_bullets = [
            f"{topic_title}: Core execution and distributed state replication",
            "Zero Production Downtime: Continuous transaction sync without row locks",
            "High-Availability Failover: Multi-AZ automated disaster recovery"
        ]
    font_head = get_font(34, bold=True)
    font_sub = get_font(26)
    card_w = 940
    card_h = 180
    start_y = 440
    gap = 215
    cx = (VIDEO_WIDTH - card_w) // 2
    
    for i, bullet in enumerate(raw_bullets[:3]):
        card_start = 0.05 + (i * 0.24)
        if progress < card_start:
            continue
        is_focused = (card_start <= progress < card_start + 0.24)
        cy = start_y + (i * gap)
        parts = bullet.split(":") if ":" in bullet else (bullet.split("—") if "—" in bullet else [bullet, ""])
        headline = parts[0].strip()
        subtext = parts[1].strip() if len(parts) > 1 else "High performance architecture principle"
        
        draw.rounded_rectangle((cx, cy, cx + card_w, cy + card_h), radius=24, fill=CARD_BG, outline=NEON_CYAN if is_focused else CARD_BORDER, width=4 if is_focused else 2)
        _draw_vector_check(draw, cx + 70, cy + card_h // 2, radius=32)
        draw_wrapped_text(draw, headline, font_head, cx + 135, cy + 32, 740, TEXT_PRIMARY, max_lines=1)
        draw_wrapped_text(draw, subtext, font_sub, cx + 135, cy + 86, 740, TEXT_MUTED, max_lines=2)

    # Metric HUD reveals after cards
    if progress >= 0.78:
        hud_w, hud_h = 940, 150
        hx = (VIDEO_WIDTH - hud_w) // 2
        hy = 1110
        draw.rounded_rectangle((hx, hy, hx + hud_w, hy + hud_h), radius=24, fill=(11, 18, 33, 245), outline=NEON_EMERALD, width=3)
        draw_wrapped_text(draw, "THROUGHPUT CAPACITY", get_font(22, bold=True), hx + 50, hy + 28, 450, NEON_EMERALD, max_lines=1)
        draw_wrapped_text(draw, "1,000,000+ msgs/s", get_font(42, bold=True), hx + 50, hy + 65, 450, TEXT_PRIMARY, max_lines=1)
        draw.text((hx + 560, hy + 28), "SYSTEM LATENCY", fill=NEON_CYAN, font=get_font(22, bold=True))
        draw.text((hx + 560, hy + 65), "< 2.5 ms", fill=NEON_CYAN, font=get_font(42, bold=True))

def _draw_vector_warning(draw: ImageDraw.Draw, cx: int, cy: int, radius: int = 34) -> None:
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(244, 63, 94, 60), outline=NEON_ROSE, width=4)
    draw.line((cx, cy - 14, cx, cy + 5), fill=TEXT_PRIMARY, width=5)
    draw.ellipse((cx - 3, cy + 12, cx + 3, cy + 18), fill=TEXT_PRIMARY)

def _draw_vector_check(draw: ImageDraw.Draw, cx: int, cy: int, radius: int = 34) -> None:
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(16, 185, 129, 60), outline=NEON_EMERALD, width=4)
    points = [
        (cx - radius * 0.45, cy),
        (cx - radius * 0.1, cy + radius * 0.35),
        (cx + radius * 0.5, cy - radius * 0.35)
    ]
    draw.line(points, fill=TEXT_PRIMARY, width=5)

def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    return (56, 189, 248)

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

    # Text Labels (wider box + 2 lines allowed so full names don't truncate)
    draw_wrapped_text(draw, label, get_font(19, bold=True), x1 - 15, cy - 18, w + 30, TEXT_PRIMARY, align="center", max_lines=2, line_spacing=2)
    draw_wrapped_text(draw, sub, get_font(15), x1 - 15, cy + 28, w + 30, color, align="center", max_lines=1)


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
    """Draws a dashed glowing cloud/VPC security boundary enclosing services."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=(15, 23, 42, 130), outline=color, width=2)
    clean_lbl = label.strip()
    lbl_font = get_font(17, bold=True)
    bbox = lbl_font.getbbox(clean_lbl)
    text_w = bbox[2] - bbox[0]
    badge_w = min(680, text_w + 52)
    draw.rounded_rectangle((x + 28, y - 18, x + 28 + badge_w, y + 18), radius=14, fill=(15, 23, 42, 240), outline=color, width=2)
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
        bw = len(label) * 9 + 18
        draw.rounded_rectangle((mx - bw // 2, my - 12, mx + bw // 2, my + 12), radius=8, fill=(15, 23, 42, 235), outline=(51, 65, 85), width=1)
        draw.text((mx - bw // 2 + 9, my - 9), label, fill=NEON_AMBER, font=get_font(14, bold=True))


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


def _render_all_in_one_tech_canvas(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """
    Voice-Synced Progressive Reveal 2D Architecture Canvas:
    Objects and dotted/glowing pipeline arrows appear STEP-BY-STEP as narration progresses,
    never dumping the entire diagram at frame 0.
    """
    # 1. Cloud & VPC Security Group Boundary (reveals immediately at start)
    vpc_label = data.get("vpc_label") or "SYSTEM ARCHITECTURE • HIGH AVAILABILITY"
    _draw_cloud_vpc_boundary(draw, 50, 420, 980, 800, label=vpc_label, color=NEON_CYAN)

    # Progressive reveal gates across scene duration (0.0 -> 1.0)
    show_c1 = progress >= 0.04
    arrow1_t = _stage_reveal(progress, 0.16, 0.30)
    show_c3 = progress >= 0.25
    show_c2 = progress >= 0.36
    arrow2_t = _stage_reveal(progress, 0.42, 0.54)
    arrow3_t = _stage_reveal(progress, 0.55, 0.68)
    show_c4 = progress >= 0.62
    arrow4_t = _stage_reveal(progress, 0.70, 0.82)
    show_c5 = progress >= 0.76
    show_hud = progress >= 0.85

    # 2. Progressive Component Placement
    c1_lbl = data.get("comp1_label") or "Client / Ingestion"
    c1_sub = data.get("comp1_sub") or "API & Request Layer"
    if show_c1:
        _draw_python_chip(draw, cx=260, cy=560, size=175, label=c1_lbl, sub=c1_sub, progress=progress)

    c2_lbl = data.get("comp2_label") or "AI Agent / Compute"
    c2_sub = data.get("comp2_sub") or "Reasoning & Logic"
    if show_c2:
        _draw_ai_robot(draw, cx=820, cy=560, size=170, label=c2_lbl, sub=c2_sub, progress=progress)

    c3_lbl = data.get("comp3_label") or "Core Orchestrator"
    c3_sub = data.get("comp3_sub") or "Distributed Pipeline"
    if show_c3:
        _draw_server_rack(draw, cx=540, cy=780, w=280, h=165, label=c3_lbl, sub=c3_sub, color=NEON_PURPLE, progress=progress)

    c4_lbl = data.get("comp4_label") or "Primary Database"
    c4_sub = data.get("comp4_sub") or "Transactional Store"
    if show_c4:
        _draw_database_cylinder(draw, cx=270, cy=1050, w=260, h=180, label=c4_lbl, sub=c4_sub, color=NEON_CYAN, progress=progress)

    c5_lbl = data.get("comp5_label") or "Target Sink / Lake"
    c5_sub = data.get("comp5_sub") or "Analytics & Output"
    if show_c5:
        _draw_s3_bucket(draw, cx=810, cy=1050, w=230, h=170, label=c5_lbl, sub=c5_sub, color=NEON_EMERALD, progress=progress)

    # 3. Progressive Dotted/Glowing Pipeline Arrows
    a1_lbl = data.get("arrow1_label") or "gRPC Stream"
    a2_lbl = data.get("arrow2_label") or "Async Inference"
    a3_lbl = data.get("arrow3_label") or "State Write"
    a4_lbl = data.get("arrow4_label") or "Event Sync"

    _draw_data_packet_arrow(draw, (350, 580), (450, 720), label=a1_lbl, progress=progress, color=NEON_CYAN, reveal_t=arrow1_t)
    _draw_data_packet_arrow(draw, (730, 580), (630, 720), label=a2_lbl, progress=progress, color=NEON_PURPLE, reveal_t=arrow2_t)
    _draw_data_packet_arrow(draw, (440, 860), (330, 960), label=a3_lbl, progress=progress, color=NEON_AMBER, reveal_t=arrow3_t)
    _draw_data_packet_arrow(draw, (640, 860), (750, 960), label=a4_lbl, progress=progress, color=NEON_EMERALD, reveal_t=arrow4_t)

    # 4. Active Motion Pointer tracking the currently revealing component
    if progress < 0.25:
        px, py, plbl = 260, 560, "STEP 1: INGESTION"
    elif progress < 0.36:
        px, py, plbl = 540, 780, "STEP 2: ROUTING"
    elif progress < 0.62:
        px, py, plbl = 820, 560, "STEP 3: COMPUTE"
    elif progress < 0.76:
        px, py, plbl = 270, 1050, "STEP 4: STORAGE"
    else:
        px, py, plbl = 810, 1050, "STEP 5: OUTPUT"
    _draw_motion_pointer(draw, px, py - 95, label=plbl, progress=progress, color=NEON_AMBER)

    # 5. Bottom Architectural Telemetry & KPI HUD (reveals cleanly near end of scene)
    if show_hud:
        hx = 50
        hy = 1250
        hw = 980
        hh = 175
        draw.rounded_rectangle((hx, hy, hx + hw, hy + hh), radius=22, fill=(11, 18, 33, 245), outline=NEON_EMERALD, width=3)
        
        col_w = hw // 3
        draw_wrapped_text(draw, "* DATA PIPELINE FLOW", get_font(17, bold=True), hx + 25, hy + 22, col_w - 40, NEON_CYAN, max_lines=1)
        draw_wrapped_text(draw, "100K+ msgs/s", get_font(25, bold=True), hx + 25, hy + 52, col_w - 40, TEXT_PRIMARY, max_lines=1)
        draw_wrapped_text(draw, "Zero-Copy Memory Bus", get_font(15), hx + 25, hy + 94, col_w - 40, TEXT_MUTED, max_lines=1)

        draw_wrapped_text(draw, "* REPLICATION LAG", get_font(17, bold=True), hx + col_w + 25, hy + 22, col_w - 40, NEON_AMBER, max_lines=1)
        draw_wrapped_text(draw, "< 4.2 ms", get_font(25, bold=True), hx + col_w + 25, hy + 52, col_w - 40, NEON_AMBER, max_lines=1)
        draw_wrapped_text(draw, "Sub-second CDC Sync", get_font(15), hx + col_w + 25, hy + 94, col_w - 40, TEXT_MUTED, max_lines=1)

        draw_wrapped_text(draw, "* CLOUD RESILIENCE", get_font(17, bold=True), hx + (col_w * 2) + 25, hy + 22, col_w - 40, NEON_EMERALD, max_lines=1)
        draw_wrapped_text(draw, "99.999% SLA", get_font(25, bold=True), hx + (col_w * 2) + 25, hy + 52, col_w - 40, NEON_EMERALD, max_lines=1)
        draw_wrapped_text(draw, "Multi-AZ Auto-Failover", get_font(15), hx + (col_w * 2) + 25, hy + 94, col_w - 40, TEXT_MUTED, max_lines=1)

        draw.rounded_rectangle((hx + 20, hy + hh - 38, hx + hw - 20, hy + hh - 12), radius=8, fill=(16, 185, 129, 45), outline=NEON_EMERALD, width=1)
        draw_wrapped_text(draw, "PRODUCTION VERIFIED  |  ZERO DATA LOSS ARCHITECTURE", get_font(16, bold=True), hx + 40, hy + hh - 34, hw - 80, TEXT_PRIMARY, align="center", max_lines=1)


def _draw_watermark(
    draw: ImageDraw.Draw,
    canvas_w: int,
    canvas_h: int,
    watermark_text: str = DEFAULT_WATERMARK
) -> None:
    """Draws a sleek, glassmorphic channel watermark in the top-right corner."""
    if not watermark_text:
        return
    font_wm = get_font(24, bold=True)
    text = watermark_text.strip()
    bbox = font_wm.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    pad_x = 16
    pad_y = 8
    badge_w = tw + (pad_x * 2) + 16  # room for cyan dot
    badge_h = th + (pad_y * 2)
    
    # Top-right corner, below the top progress bar
    bx = canvas_w - badge_w - 36
    by = 44
    
    # Outer glow
    draw.rounded_rectangle(
        (bx - 1, by - 1, bx + badge_w + 1, by + badge_h + 1),
        radius=badge_h // 2,
        fill=(56, 189, 248, 40)
    )
    # Glassmorphic dark card
    draw.rounded_rectangle(
        (bx, by, bx + badge_w, by + badge_h),
        radius=badge_h // 2,
        fill=(15, 23, 42, 220),
        outline=(56, 189, 248, 180),
        width=2
    )
    
    # Glowing neon cyan dot
    dot_r = 4
    dot_x = bx + pad_x + 4
    dot_y = by + (badge_h // 2)
    draw.ellipse((dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r), fill=(56, 189, 248, 255))
    
    # Text
    tx = dot_x + dot_r + 8
    ty = by + pad_y - 2
    draw.text((tx, ty), text, fill=(248, 250, 252, 240), font=font_wm)

def generate_thumbnail_9_16(
    topic: str,
    timeline: Any = None,
    watermark: str = DEFAULT_WATERMARK,
    visual_engine: str = "hybrid_modern",
    output_path: Any = None
) -> Path:
    """
    Generates a high-impact 1080x1920 (9:16) thumbnail image for YouTube Shorts & Instagram Reels:
    - High-contrast viral topic headline
    - Cyber-tech neon border & background styling
    - Channel watermark @Code_With_Mangesh in top corner
    - Centerpiece tech architecture/code/comparison graphic card
    - Bottom punchy badge hook
    """
    import time
    canvas_w = 1080
    canvas_h = 1920
    im = Image.new("RGB", (canvas_w, canvas_h), COLOR_BG_DARK)
    draw = ImageDraw.Draw(im, "RGBA")
    
    # Outer modern neon frame (inset 24px)
    draw.rounded_rectangle((24, 24, canvas_w - 24, canvas_h - 24), radius=36, outline=(56, 189, 248, 120), width=4)
    draw.rounded_rectangle((32, 32, canvas_w - 32, canvas_h - 32), radius=30, outline=(168, 85, 247, 50), width=2)
    
    # Story progress bar at top
    _draw_story_progress_bar(draw, total_scenes=4, current_scene=1, progress=0.25)
    
    # Top-right watermark (@Code_With_Mangesh)
    _draw_watermark(draw, canvas_w, canvas_h, watermark)
    
    # Top category pill badge
    badge_text = "⚡ SYSTEM DESIGN & ARCHITECTURE"
    if timeline and isinstance(timeline, dict) and "scenes" in timeline and len(timeline["scenes"]) > 0:
        first_sc = timeline["scenes"][0]
        badge_text = first_sc.get("visual_data", {}).get("badge", badge_text)
    
    font_badge = get_font(28, bold=True)
    badge_bbox = font_badge.getbbox(badge_text)
    bw = min(880, (badge_bbox[2] - badge_bbox[0]) + 50)
    bh = 54
    bx = (canvas_w - bw) // 2
    by = 120
    draw.rounded_rectangle((bx - 2, by - 2, bx + bw + 2, by + bh + 2), radius=27, fill=(56, 189, 248, 45))
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=26, fill=(15, 23, 42, 240), outline=NEON_CYAN, width=3)
    draw.text((bx + (bw - (badge_bbox[2] - badge_bbox[0])) // 2, by + 11), badge_text, fill=NEON_CYAN, font=font_badge)
    
    # Viral Topic Title (Large, 58pt bold)
    title_text = topic.strip()
    if len(title_text) > 90:
        title_text = title_text[:87] + "..."
    font_title = get_font(58, bold=True)
    max_title_w = 920
    title_x = (canvas_w - max_title_w) // 2
    title_y = by + 85
    draw_wrapped_text(draw, title_text, font_title, title_x, title_y, max_title_w, TEXT_PRIMARY, line_spacing=12, align="center", max_lines=3)
    
    # Center Graphic (Render scene visual at progress 1.0)
    target_scene = None
    if timeline and isinstance(timeline, dict) and "scenes" in timeline:
        for sc in timeline["scenes"]:
            if sc.get("visual_type") in ["architecture_flow", "code_terminal", "sql_table", "split_comparison", "benchmark_chart"]:
                target_scene = sc
                break
        if not target_scene and len(timeline["scenes"]) > 0:
            target_scene = timeline["scenes"][0]
            
    if not target_scene:
        target_scene = {
            "visual_type": "architecture_flow",
            "visual_data": {
                "badge": "SYSTEM DESIGN",
                "title": topic[:40],
                "nodes": [
                    {"id": "src", "label": "Client / Ingestion", "sub": "Requests & Traffic", "color": "#38BDF8"},
                    {"id": "eng", "label": "Core Engine", "sub": "Zero-Downtime Pipeline", "color": "#FBBF24"},
                    {"id": "dst", "label": "Distributed Store", "sub": "HA Cluster & Cache", "color": "#34D399"}
                ]
            }
        }
        
    v_type = target_scene.get("visual_type", "architecture_flow")
    v_data = target_scene.get("visual_data", {})
    
    if v_type == "split_comparison":
        _render_split_comparison(draw, v_data, 1.0)
    elif v_type == "benchmark_chart":
        _render_benchmark_chart(draw, v_data, 1.0)
    elif v_type == "circular_hub_mesh":
        _render_circular_hub_mesh(draw, v_data, 1.0)
    elif v_type == "metric_gauge_hud":
        _render_metric_gauge_hud(draw, v_data, 1.0)
    elif v_type == "data_structure_memory":
        _render_data_structure_memory(draw, v_data, 1.0)
    elif v_type == "sql_table":
        _render_sql_table(draw, v_data, 1.0)
    elif v_type == "code_terminal":
        _render_code_terminal(draw, v_data, 1.0)
    elif v_type == "alert_diagram":
        _render_alert_diagram(draw, v_data, 1.0)
    elif v_type == "architecture_flow":
        _render_architecture_flow(draw, v_data, 1.0)
    elif v_type == "all_in_one_tech_canvas":
        _render_all_in_one_tech_canvas(draw, v_data, 1.0)
    else:
        _render_concept_cards(draw, v_data, 1.0)
        
    # Bottom Viral Callout Card (y = 1540 to y = 1780)
    card_w = 940
    card_h = 240
    cx = (canvas_w - card_w) // 2
    cy = 1540
    
    draw.rounded_rectangle((cx - 2, cy - 2, cx + card_w + 2, cy + card_h + 2), radius=32, fill=(56, 189, 248, 50))
    draw.rounded_rectangle((cx, cy, cx + card_w, cy + card_h), radius=30, fill=(15, 23, 42, 245), outline=NEON_CYAN, width=3)
    
    tag_font = get_font(26, bold=True)
    draw.text((cx + 50, cy + 30), "🔥 100% PRODUCTION ARCHITECTURE", fill=NEON_AMBER, font=tag_font)
    
    hook_font = get_font(38, bold=True)
    draw_wrapped_text(draw, "Explain Like a Staff Engineer • Zero Fluff", hook_font, cx + 50, cy + 72, 840, TEXT_PRIMARY, max_lines=1)
    
    ch_font = get_font(30, bold=True)
    draw.text((cx + 50, cy + 145), f"🎬 Follow {watermark} for Daily Tech Reels", fill=NEON_CYAN, font=ch_font)
    
    if output_path is None:
        output_path = OUTPUT_DIR / f"thumbnail_9x16_{int(time.time())}.png"
        
    im.save(output_path, "PNG", quality=98)
    return output_path
