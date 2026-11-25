import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from core.layouts_studio import (
    ALL_STUDIO_LAYOUTS,
    StudioStage,
    _clamp01,
    _draw_wrapped_text,
    _ease_out_cubic,
    _est_lines,
    _get_font,
    _with_alpha,
    dispatch_studio_layout,
)
from core.palette_engine import STUDIO_WORLDS, generate_hsl_world, resolve_studio_world
from core.shapes_3d import ALL_50_SHAPES, VECTOR_GLYPHS, draw_3d_shape, draw_vector_glyph, infer_3d_shape
from core.svg_engine import fetch_iconify_svg, prepare_generative_svg_layers

__all__ = [
    "ALL_50_SHAPES",
    "ALL_STUDIO_LAYOUTS",
    "STUDIO_WORLDS",
    "VECTOR_GLYPHS",
    "StudioStage",
    "generate_hsl_world",
    "resolve_studio_world",
    "fetch_iconify_svg",
    "prepare_generative_svg_layers",
    "draw_3d_shape",
    "draw_vector_glyph",
    "infer_3d_shape",
    "dispatch_studio_layout",
    "_dispatch_cinematic",
    "_build_volumetric_studio_bg",
    "_draw_studio_header",
    "_get_font",
    "_draw_wrapped_text",
    "_est_lines",
    "render_cinematic_scene_frames",
]


def _fade_transition_alpha(linear_p: float) -> float:
    """Smooth enter/exit envelope for Clean Transitions between scenes."""
    if linear_p < 0.05:
        return 0.40 + 0.60 * _ease_out_cubic(linear_p / 0.05)
    if linear_p > 0.95:
        return 0.45 + 0.55 * ((1.0 - linear_p) / 0.05)
    return 1.0


def _build_anchors(duration: float, scene: Dict[str, Any], scene_words: List[Dict[str, Any]] = None) -> List[Tuple[float, float]]:
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
    target_stages = [0.06, 0.28, 0.54, 0.78]
    cursor = 0
    prev_t = 0.0
    for idx, trig in enumerate(triggers[:4]):
        kw = "".join(ch for ch in str(trig.get("keyword", "")).lower() if ch.isalnum() or "\u0900" <= ch <= "\u097f")
        if not kw:
            continue
        matched_t = None
        for wi in range(cursor, len(clean_words)):
            wt, ws = clean_words[wi]
            if kw in wt or wt in kw:
                matched_t = (ws - sc_start) / max(0.5, duration)
                cursor = wi + 1
                break
        if matched_t is not None:
            tc = max(prev_t + 0.06, min(0.90, matched_t))
            prev_t = tc
            anchors.append((tc, target_stages[idx]))
    anchors.append((1.0, 1.0))
    return anchors


def _voice_progress(
    frame_idx: int,
    total_frames: int,
    duration: float,
    scene: Dict[str, Any],
    scene_words: List[Dict[str, Any]] = None,
    anchors: List[Tuple[float, float]] = None,
) -> float:
    linear_p = frame_idx / max(1, total_frames - 1)
    if not scene_words:
        return linear_p
    choreo_p = linear_p
    if anchors and len(anchors) >= 3:
        for i in range(len(anchors) - 1):
            t0, p0 = anchors[i]
            t1, p1 = anchors[i + 1]
            if t0 <= linear_p <= t1:
                choreo_p = p0 + ((linear_p - t0) / max(1e-5, t1 - t0)) * (p1 - p0)
                break
    sc_start = float(scene.get("start_time", 0.0))
    cur_t = sc_start + (linear_p * duration)
    spoken = sum(1 for w in scene_words if float(w.get("start", 0.0)) <= cur_t)
    word_p = spoken / max(1, len(scene_words))
    return _clamp01(0.55 * choreo_p + 0.30 * word_p + 0.15 * linear_p)


def _build_volumetric_studio_bg(w: int, h: int, world: Dict[str, Any]) -> Image.Image:
    """
    NumPy-vectorized dark/light volumetric studio backdrop with radial spotlights
    and ultra-subtle editorial coordinate backdrop (NO heavy bottom Tron mesh).
    """
    y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]

    top = np.array(world["bg_top"], dtype=np.float32)[None, None, :]
    bot = np.array(world["bg_bot"], dtype=np.float32)[None, None, :]
    arr = top * (1.0 - y[..., None]) + bot * y[..., None]

    d2_a = ((x - 0.50) * 1.15) ** 2 + ((y - 0.28) * 1.40) ** 2
    spot_a_intensity = np.exp(-d2_a * 4.5)[..., None]
    d2_b = ((x - 0.78) * 1.25) ** 2 + ((y - 0.72) * 1.35) ** 2
    spot_b_intensity = np.exp(-d2_b * 5.0)[..., None]

    spot_a = np.array(world["spot_a"], dtype=np.float32)[None, None, :]
    spot_b = np.array(world["spot_b"], dtype=np.float32)[None, None, :]

    if world["is_light"]:
        arr = arr - 10.0 * spot_a_intensity + (spot_a - arr) * (spot_a_intensity * 0.08)
        arr = arr + (spot_b - arr) * (spot_b_intensity * 0.05)
    else:
        arr = arr + spot_a * (spot_a_intensity * 0.14) + spot_b * (spot_b_intensity * 0.10)

    grid_rgb = np.array(world["grid_col"], dtype=np.float32)[None, None, :]
    step = 84
    gx_mask = (np.arange(w)[None, :] % step == 0)
    gy_mask = (np.arange(h)[:, None] % step == 0)
    grid_mask = (gx_mask | gy_mask).astype(np.float32)
    vignette = np.exp(-(((x - 0.5) * 1.55) ** 2 + ((y - 0.48) * 1.35) ** 2))
    grid_alpha = (grid_mask * vignette * (0.045 if not world["is_light"] else 0.08))[..., None]
    arr = arr * (1.0 - grid_alpha) + grid_rgb * grid_alpha

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")


def _draw_voice_waveform(
    draw: ImageDraw.ImageDraw,
    world: Dict[str, Any],
    scene_words: List[Dict[str, Any]],
    cur_time: float,
    progress: float,
    canvas_w: int,
) -> None:
    is_speaking = False
    word_energy = 0.25
    if scene_words:
        for w in scene_words:
            ws = float(w.get("start", 0.0))
            we = float(w.get("end", ws + 0.25))
            if ws - 0.04 <= cur_time <= we + 0.05:
                is_speaking = True
                span = max(0.08, we - ws)
                local = (cur_time - ws) / span
                word_energy = 0.55 + 0.45 * math.sin(local * math.pi)
                break
    else:
        is_speaking = True
        word_energy = 0.65

    bx, by = 40, 44
    bw, bh = 230, 38
    pill_bg = (255, 255, 255, 232) if world["is_light"] else (15, 23, 42, 215)
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=19, fill=pill_bg, outline=(*world["cyan"], 150), width=2)
    draw.text((bx + 14, by + 9), "AUDIO", fill=world["cyan"], font=_get_font(15, bold=True))

    n_bars = 14
    bar_x0 = bx + 78
    base_mid = by + bh // 2
    for bi in range(n_bars):
        phase = progress * 46.0 + bi * 0.85
        amp = (0.35 + 0.65 * abs(math.sin(phase) * math.cos(phase * 0.43))) * (word_energy if is_speaking else 0.16)
        hh = max(3, int(13 * amp))
        x_b = bar_x0 + bi * 10
        b_col = world["emerald"] if is_speaking and amp > 0.55 else world["cyan"]
        draw.rounded_rectangle((x_b, base_mid - hh, x_b + 5, base_mid + hh), radius=2, fill=(*b_col, 235))


def _draw_studio_header(stage: StudioStage, badge: str, title: str, accent: Tuple[int, int, int], callout: str = "") -> None:
    """Draws Callout Badge pill + Neon Rim Light + Crisp Studio Title."""
    w = stage.world
    lx = 68
    y_cur = 104
    badge_s = str(badge or callout or "").strip().upper()
    if badge_s:
        f_b = _get_font(23, bold=True)
        bb = f_b.getbbox(badge_s)
        pw = min(860, (bb[2] - bb[0]) + 56)
        pill_box = (lx, y_cur, lx + pw, y_cur + 40)
        stage.add_glow_box(pill_box, accent, radius=14, alpha=85)
        stage.draw.rounded_rectangle(
            pill_box, radius=14,
            fill=_with_alpha(w["card_alt"], stage.t_alpha),
            outline=_with_alpha(accent, 0.85 * stage.t_alpha),
            width=2,
        )
        stage.draw.ellipse((lx + 14, y_cur + 15, lx + 24, y_cur + 25), fill=_with_alpha(accent, stage.t_alpha))
        stage.draw.text((lx + 34, y_cur + 7), badge_s, fill=_with_alpha(accent, stage.t_alpha), font=f_b)
        y_cur += 54

    if title:
        _draw_wrapped_text(
            stage.draw, (lx, y_cur), str(title), _get_font(46, bold=True),
            _with_alpha(w["text"], stage.t_alpha), 940, line_gap=8, max_lines=2,
        )


def _dispatch_cinematic(stage: StudioStage, visual_type: str, visual_data: Dict[str, Any], progress: float) -> None:
    dispatch_studio_layout(stage, visual_type, visual_data, progress, stage.world)


_resolve_world = resolve_studio_world


def render_cinematic_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    total_scenes: int = 4,
    format_ratio: str = "9:16",
    watermark: str = DEFAULT_WATERMARK,
    scene_words: List[Dict[str, Any]] = None,
    tone: str = "auto_dynamic",
) -> List[Path]:
    """
    Renders studio-grade 2.5D isometric & SVG frames across Unlimited HSL Color Worlds,
    33+ Studio Layouts, Spatial Composer, AI Multi-Layer <svg>, 50 3D Shapes & 200k+ Iconify SVGs.
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

    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    canvas_w = spec.get("width", VIDEO_WIDTH)
    canvas_h = spec.get("height", VIDEO_HEIGHT)

    visual_type = scene.get("visual_type", "custom_scene")
    visual_data = scene.get("visual_data", {}) or {}
    effective_tone = (scene.get("scene_tone") or "conversational_casual") if tone == "auto_dynamic" else tone
    art_style = str(visual_data.get("art_style") or scene.get("art_style") or "editorial_dark").strip()
    topic_seed = str(scene.get("topic") or visual_data.get("title") or "").strip()
    world = resolve_studio_world(art_style=art_style, tone=effective_tone, visual_data=visual_data, topic=topic_seed)

    base_bg = _build_volumetric_studio_bg(canvas_w, canvas_h, world)
    needs_aspect_fit = (canvas_w != VIDEO_WIDTH or canvas_h != VIDEO_HEIGHT)
    anchors = _build_anchors(duration, scene, scene_words)
    sc_start = float(scene.get("start_time", 0.0))

    badge = str(visual_data.get("badge") or "")
    callout = str(visual_data.get("callout_badge") or "")
    title = str(visual_data.get("title") or "")
    accent = (
        world["emerald"] if effective_tone == "mentor_storyteller"
        else (world["amber"] if effective_tone == "interview_prep"
              else (world["rose"] if effective_tone == "dramatic_performance" else world["cyan"]))
    )

    far_particles = [((i * 197 + scene_idx * 53) % canvas_w, (i * 313 + 71) % canvas_h, 2 + (i % 3), 12 + (i % 3) * 6) for i in range(16)]
    near_glyphs = [((i * 271 + scene_idx * 89) % canvas_w, (i * 199 + 43) % canvas_h, 5 + (i % 4), 16 + (i % 2) * 8) for i in range(8)]

    frame_paths: List[Path] = []
    for f in range(total_frames):
        linear_p = f / max(1, total_frames - 1)
        raw_p = _voice_progress(f, total_frames, duration, scene, scene_words, anchors=anchors)
        progress = min(1.0, raw_p * 1.10) if effective_tone == "fireship_octane" else raw_p
        cur_time = sc_start + (linear_p * duration)
        t_alpha = _fade_transition_alpha(linear_p)

        frame_bg = base_bg.copy()
        p_draw = ImageDraw.Draw(frame_bg, "RGBA")
        for px0, py0, pr, pa in far_particles:
            py_live = int((py0 - linear_p * 70) % canvas_h)
            px_live = int((px0 + math.sin(linear_p * 3.14 + py0) * 10) % canvas_w)
            p_draw.ellipse((px_live - pr, py_live - pr, px_live + pr, py_live + pr), fill=(*accent, pa))
        for gi, (gx0, gy0, gr, ga) in enumerate(near_glyphs):
            gy_live = int((gy0 - linear_p * 175) % canvas_h)
            gx_live = int((gx0 + math.cos(linear_p * 2.5 + gy0) * 18) % canvas_w)
            if gi % 2 == 0:
                p_draw.ellipse((gx_live - gr, gy_live - gr, gx_live + gr, gy_live + gr), outline=(*world["purple"], ga), width=1)
            else:
                p_draw.polygon([(gx_live, gy_live - gr), (gx_live + gr, gy_live), (gx_live, gy_live + gr), (gx_live - gr, gy_live)], outline=(*accent, ga))

        if needs_aspect_fit:
            stage = StudioStage(VIDEO_WIDTH, 1500, world, transition_alpha=t_alpha)
            _draw_studio_header(stage, badge, title, accent, callout=callout)
            dispatch_studio_layout(stage, visual_type, visual_data, progress, world, topic=topic_seed)

            virtual_rgba = stage.composite_onto(None)
            avail_h = canvas_h - 140
            avail_w = canvas_w - 80
            scale = min(avail_w / VIDEO_WIDTH, avail_h / 1420.0)
            nw = max(100, int(VIDEO_WIDTH * scale))
            nh = max(100, int(1500 * scale))
            rs = virtual_rgba.resize((nw, nh), Image.Resampling.BILINEAR)
            frame_rgba = frame_bg.convert("RGBA")
            frame_rgba.alpha_composite(rs, ((canvas_w - nw) // 2, 42))
            final_img = frame_rgba
        else:
            stage = StudioStage(VIDEO_WIDTH, VIDEO_HEIGHT, world, transition_alpha=t_alpha)
            _draw_studio_header(stage, badge, title, accent, callout=callout)
            dispatch_studio_layout(stage, visual_type, visual_data, progress, world, topic=topic_seed)
            final_img = stage.composite_onto(frame_bg)

        chrome = ImageDraw.Draw(final_img, "RGBA")
        track_col = (15, 23, 42, 32) if world["is_light"] else (255, 255, 255, 34)
        global_p = ((scene_idx - 1) + linear_p) / max(1, total_scenes)
        bar_w = canvas_w - 80
        chrome.rounded_rectangle((40, 24, 40 + bar_w, 30), radius=3, fill=track_col)
        chrome.rounded_rectangle((40, 24, 40 + max(10, int(bar_w * _clamp01(global_p))), 30), radius=3, fill=accent)

        _draw_voice_waveform(chrome, world, scene_words or [], cur_time, progress, canvas_w)

        if watermark:
            wm_font = _get_font(23, bold=True)
            wt = watermark.strip()
            wbb = wm_font.getbbox(wt)
            bw = (wbb[2] - wbb[0]) + 46
            bx, by = canvas_w - bw - 36, 44
            wfill = (255, 255, 255, 234) if world["is_light"] else (15, 23, 42, 218)
            chrome.rounded_rectangle((bx, by, bx + bw, by + 38), radius=19, fill=wfill, outline=(*accent, 185), width=2)
            chrome.ellipse((bx + 14, by + 15, bx + 22, by + 23), fill=accent)
            chrome.text((bx + 30, by + 6), wt, fill=world["text"], font=wm_font)

        frame_file = scene_frames_dir / f"frame_{f:04d}.jpg"
        final_img.convert("RGB").save(frame_file, "JPEG", quality=90)
        frame_paths.append(frame_file)

    return frame_paths
