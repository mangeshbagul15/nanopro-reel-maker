import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from core.layouts_pro import ALL_TEXT_FX, ALL_TRANSITIONS, apply_scene_transition, draw_kinetic_text
from core.layouts_domain_220 import DOMAIN_220_LAYOUTS
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
from core.mesh_shader_engine import ALL_3D_MESHES, ALL_BACKDROPS, draw_procedural_3d_mesh, render_procedural_backdrop
from core.palette_engine import STUDIO_WORLDS, generate_hsl_world, resolve_studio_world
from core.shapes_3d import ALL_50_SHAPES, ALL_100_SHAPES, ALL_145_SHAPES, VECTOR_GLYPHS, draw_3d_shape, draw_vector_glyph, infer_3d_shape
from core.svg_engine import ICON_ALIASES, fetch_3d_extruded_svg, fetch_iconify_svg, prepare_generative_svg_layers, prepare_keyframed_svg_layers
from core.web_generative_engine import detect_web_engine, is_web_engine_available, render_web_generative_frames

__all__ = [
    "ALL_50_SHAPES",
    "ALL_100_SHAPES",
    "ALL_145_SHAPES",
    "ALL_3D_MESHES",
    "ALL_BACKDROPS",
    "ALL_TRANSITIONS",
    "ALL_TEXT_FX",
    "ALL_STUDIO_LAYOUTS",
    "DOMAIN_220_LAYOUTS",
    "ICON_ALIASES",
    "STUDIO_WORLDS",
    "VECTOR_GLYPHS",
    "StudioStage",
    "generate_hsl_world",
    "resolve_studio_world",
    "fetch_iconify_svg",
    "fetch_3d_extruded_svg",
    "prepare_generative_svg_layers",
    "prepare_keyframed_svg_layers",
    "draw_3d_shape",
    "draw_procedural_3d_mesh",
    "draw_vector_glyph",
    "infer_3d_shape",
    "dispatch_studio_layout",
    "_dispatch_cinematic",
    "_resolve_world",
    "_build_volumetric_studio_bg",
    "render_procedural_backdrop",
    "apply_scene_transition",
    "draw_kinetic_text",
    "_draw_studio_header",
    "_get_font",
    "_draw_wrapped_text",
    "_est_lines",
    "is_web_engine_available",
    "render_web_generative_frames",
    "render_cinematic_scene_frames",
]

_ANIMATED_BACKDROPS = {"aurora_mesh", "plasma_wave", "glass_caustics", "topo_contours"}


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


def _build_volumetric_studio_bg(w: int, h: int, world: Dict[str, Any], style: str = "subtle_grid", progress: float = 0.0) -> Image.Image:
    """Renders any of 18 Procedural Studio & Shader Backdrops cleanly without heavy floor jali."""
    return render_procedural_backdrop(w, h, world, style=style, progress=progress)


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


def _draw_studio_header(
    stage: StudioStage,
    badge: str,
    title: str,
    accent: Tuple[int, int, int],
    callout: str = "",
    text_fx: str = "clean_fade",
    progress: float = 1.0,
) -> None:
    """Draws Callout Badge pill + Neon Rim Light + 14-FX Kinetic Studio Title cleanly above STAGE_Y0."""
    w = stage.world
    lx = 68
    y_cur = 96
    badge_s = str(badge or callout or "").strip().upper()
    if badge_s:
        f_b = _get_font(22, bold=True)
        bb = f_b.getbbox(badge_s)
        pw = min(860, (bb[2] - bb[0]) + 56)
        pill_box = (lx, y_cur, lx + pw, y_cur + 38)
        stage.add_glow_box(pill_box, accent, radius=14, alpha=65)
        stage.draw.rounded_rectangle(
            pill_box, radius=14,
            fill=_with_alpha(w["card_alt"], stage.t_alpha),
            outline=_with_alpha(accent, 0.85 * stage.t_alpha),
            width=2,
        )
        stage.draw.ellipse((lx + 14, y_cur + 14, lx + 24, y_cur + 24), fill=_with_alpha(accent, stage.t_alpha))
        stage.draw.text((lx + 34, y_cur + 7), badge_s, fill=_with_alpha(accent, stage.t_alpha), font=f_b)
        y_cur += 48

    if title:
        draw_kinetic_text(
            stage, str(title), (lx, y_cur), 940, _get_font(45, bold=True),
            accent, progress=progress, fx=text_fx, world=w,
            _with_alpha_fn=_with_alpha, _draw_wrapped_fn=_draw_wrapped_text,
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
    Studio Max Dual Generative Engine:
    - Uses live Playwright WebGL/Three.js/HTML5 when `visual_type == "web_scene"` or `html` is provided locally;
    - Otherwise renders 46+ Worlds + Infinite HSL, 65+ Studio Layouts, 105 3D Shapes + 200k+ 3D-Extruded SVGs,
      124 Glyphs, 18 Procedural Backdrops/Shaders, 12 Transitions, 14 Text FX, and Keyframe Animated <svg> in pure Python.
    """
    visual_type = str(scene.get("visual_type", "custom_scene")).lower().strip()
    visual_data = scene.get("visual_data", {}) or {}

    if (visual_type in ("web_scene", "webgl_scene", "html_scene") or visual_data.get("html")) and is_web_engine_available():
        web_frames = render_web_generative_frames(
            scene=scene, scene_idx=scene_idx, total_scenes=total_scenes,
            format_ratio=format_ratio, watermark=watermark, scene_words=scene_words, tone=tone,
        )
        if web_frames:
            return web_frames

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

    effective_tone = (scene.get("scene_tone") or "conversational_casual") if tone == "auto_dynamic" else tone
    art_style = str(visual_data.get("art_style") or scene.get("art_style") or "editorial_dark").strip()
    topic_seed = str(scene.get("topic") or visual_data.get("title") or "").strip()
    world = resolve_studio_world(art_style=art_style, tone=effective_tone, visual_data=visual_data, topic=topic_seed)

    backdrop_style = str(visual_data.get("backdrop") or scene.get("backdrop") or ALL_BACKDROPS[(scene_idx - 1) % len(ALL_BACKDROPS)]).lower().strip()
    transition_style = str(visual_data.get("transition") or scene.get("transition") or ALL_TRANSITIONS[(scene_idx - 1) % len(ALL_TRANSITIONS)]).lower().strip()
    text_fx = str(visual_data.get("text_fx") or scene.get("text_fx") or "clean_fade").lower().strip()
    is_live_shader_bg = backdrop_style in _ANIMATED_BACKDROPS

    static_bg = None if is_live_shader_bg else render_procedural_backdrop(canvas_w, canvas_h, world, style=backdrop_style, progress=0.0)
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

        if is_live_shader_bg:
            frame_bg = render_procedural_backdrop(canvas_w, canvas_h, world, style=backdrop_style, progress=linear_p)
        else:
            frame_bg = static_bg.copy()

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
            stage = StudioStage(VIDEO_WIDTH, 1500, world, transition_alpha=1.0)
            _draw_studio_header(stage, badge, title, accent, callout=callout, text_fx=text_fx, progress=progress)
            dispatch_studio_layout(stage, visual_type, visual_data, progress, world, topic=topic_seed)

            virtual_rgba = stage.composite_onto(None)
            avail_h, avail_w = canvas_h - 140, canvas_w - 80
            scale = min(avail_w / VIDEO_WIDTH, avail_h / 1420.0)
            nw, nh = max(100, int(VIDEO_WIDTH * scale)), max(100, int(1500 * scale))
            rs = virtual_rgba.resize((nw, nh), Image.Resampling.BILINEAR)
            full_stage = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            full_stage.alpha_composite(rs, ((canvas_w - nw) // 2, 42))
            final_img = apply_scene_transition(full_stage, frame_bg, transition_style, linear_p)
        else:
            stage = StudioStage(VIDEO_WIDTH, VIDEO_HEIGHT, world, transition_alpha=t_alpha if transition_style == "crossfade" else 1.0)
            _draw_studio_header(stage, badge, title, accent, callout=callout, text_fx=text_fx, progress=progress)
            dispatch_studio_layout(stage, visual_type, visual_data, progress, world, topic=topic_seed)
            stage_rgba = stage.composite_onto(None)
            final_img = apply_scene_transition(stage_rgba, frame_bg, transition_style, linear_p)

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
