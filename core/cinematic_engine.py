import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH


# =========================================================================
# STUDIO WORLDS & COLOR PALETTES
# =========================================================================
STUDIO_WORLDS: Dict[str, Dict[str, Any]] = {
    "obsidian_studio": {
        "is_light": False,
        "bg_top": (7, 10, 18),
        "bg_bot": (13, 18, 34),
        "spot_a": (56, 189, 248),
        "spot_b": (168, 85, 247),
        "grid_col": (56, 189, 248),
        "card_bg": (17, 24, 40, 224),
        "card_alt": (26, 35, 58, 232),
        "glass_rim": (255, 255, 255, 48),
        "border": (96, 165, 250, 125),
        "shadow_col": (2, 4, 10, 165),
        "text": (248, 250, 252),
        "muted": (156, 173, 196),
        "cyan": (56, 189, 248),
        "purple": (168, 85, 247),
        "emerald": (52, 211, 153),
        "amber": (251, 191, 36),
        "rose": (244, 63, 94),
    },
    "sapphire_3d": {
        "is_light": False,
        "bg_top": (5, 14, 30),
        "bg_bot": (10, 26, 54),
        "spot_a": (34, 211, 238),
        "spot_b": (99, 102, 241),
        "grid_col": (34, 211, 238),
        "card_bg": (12, 27, 52, 226),
        "card_alt": (18, 38, 70, 235),
        "glass_rim": (186, 230, 253, 52),
        "border": (56, 189, 248, 135),
        "shadow_col": (2, 6, 16, 170),
        "text": (248, 250, 252),
        "muted": (148, 175, 206),
        "cyan": (34, 211, 238),
        "purple": (129, 140, 248),
        "emerald": (52, 211, 153),
        "amber": (251, 191, 36),
        "rose": (251, 113, 133),
    },
    "studio_white": {
        "is_light": True,
        "bg_top": (244, 247, 252),
        "bg_bot": (228, 236, 248),
        "spot_a": (14, 165, 233),
        "spot_b": (139, 92, 246),
        "grid_col": (100, 116, 139),
        "card_bg": (255, 255, 255, 240),
        "card_alt": (241, 245, 249, 245),
        "glass_rim": (255, 255, 255, 220),
        "border": (148, 163, 184, 170),
        "shadow_col": (15, 23, 42, 46),
        "text": (15, 23, 42),
        "muted": (71, 85, 105),
        "cyan": (2, 132, 199),
        "purple": (124, 58, 237),
        "emerald": (5, 150, 105),
        "amber": (217, 119, 6),
        "rose": (225, 29, 72),
    },
    "crimson_studio": {
        "is_light": False,
        "bg_top": (16, 9, 18),
        "bg_bot": (28, 12, 26),
        "spot_a": (244, 63, 94),
        "spot_b": (251, 191, 36),
        "grid_col": (244, 63, 94),
        "card_bg": (28, 16, 26, 228),
        "card_alt": (40, 20, 34, 236),
        "glass_rim": (254, 205, 211, 46),
        "border": (244, 63, 94, 130),
        "shadow_col": (6, 2, 6, 175),
        "text": (248, 250, 252),
        "muted": (196, 166, 178),
        "cyan": (56, 189, 248),
        "purple": (192, 132, 252),
        "emerald": (52, 211, 153),
        "amber": (251, 191, 36),
        "rose": (244, 63, 94),
    },
}


# =========================================================================
# FONT & TYPOGRAPHY HELPERS (CROSS-PLATFORM WINDOWS + LINUX)
# =========================================================================
_FONT_CACHE: Dict[Tuple[int, bool], ImageFont.ImageFont] = {}


def _get_font(size: int = 40, bold: bool = False) -> ImageFont.ImageFont:
    key = (int(size), bool(bold))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
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
            f = ImageFont.truetype(name, size)
            _FONT_CACHE[key] = f
            return f
        except Exception:
            continue
    try:
        f = ImageFont.load_default(size=size)
    except TypeError:
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def _draw_wrapped_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    max_width: int,
    fill: Tuple[int, ...],
    line_spacing: int = 8,
    align: str = "left",
    max_lines: int = 5,
) -> int:
    words = str(text or "").split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        cand = " ".join(cur + [w])
        if (font.getbbox(cand)[2] - font.getbbox(cand)[0]) <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                lines.append(w)
                cur = []
    if cur:
        lines.append(" ".join(cur))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > 3:
            lines[-1] = lines[-1][:-3] + "..."

    cur_y = y
    for ln in lines:
        bbox = font.getbbox(ln)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = x + (max_width - tw) // 2 if align == "center" else x
        draw.text((tx, cur_y), ln, fill=fill, font=font)
        cur_y += th + line_spacing
    return cur_y - y


def _est_lines(text: str, font: ImageFont.ImageFont, max_w: int, max_lines: int = 4) -> int:
    words = str(text or "").split()
    if not words:
        return 1
    cnt = 1
    cur: List[str] = []
    for w in words:
        cand = " ".join(cur + [w])
        if (font.getbbox(cand)[2] - font.getbbox(cand)[0]) <= max_w:
            cur.append(w)
        else:
            if cur:
                cnt += 1
            cur = [w]
    return min(max_lines, max(1, cnt))


# =========================================================================
# MOTION EASING & SPRING PHYSICS
# =========================================================================
def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _ease_out_cubic(t: float) -> float:
    u = 1.0 - _clamp01(t)
    return 1.0 - u * u * u


def _ease_out_back(t: float, s: float = 1.45) -> float:
    x = _clamp01(t)
    x1 = x - 1.0
    return 1.0 + (s + 1.0) * (x1 ** 3) + s * (x1 ** 2)


def _spring_gate(progress: float, gate: float, span: float = 0.14) -> Tuple[float, int, float]:
    """
    Returns (visibility_alpha_0_1, y_slide_offset_px, spring_scale) for buttery
    After-Effects spring slide-in + fade motion instead of hard abrupt cuts.
    """
    if progress < gate:
        return 0.0, 42, 0.90
    raw = _clamp01((progress - gate) / max(1e-4, span))
    back = _ease_out_back(raw, s=1.35)
    alpha = _clamp01(raw * 1.45)
    dy = int((1.0 - back) * 38)
    scale = 0.92 + 0.08 * back
    return alpha, dy, scale


def _with_alpha(col: Tuple[int, ...], alpha_mul: float) -> Tuple[int, int, int, int]:
    r, g, b = col[0], col[1], col[2]
    base_a = col[3] if len(col) >= 4 else 255
    return (int(r), int(g), int(b), max(0, min(255, int(base_a * _clamp01(alpha_mul)))))


def _resolve_color(name: str, world: Dict[str, Any], fallback: Tuple[int, int, int] = None) -> Tuple[int, int, int]:
    raw = str(name or "").strip()
    if raw.startswith("#") and len(raw.lstrip("#")) == 6:
        h = raw.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    k = raw.lower()
    if k in ("cyan", "blue", "info", "primary"):
        return world["cyan"]
    if k in ("purple", "violet"):
        return world["purple"]
    if k in ("emerald", "green", "success"):
        return world["emerald"]
    if k in ("amber", "yellow", "gold", "warn", "warning"):
        return world["amber"]
    if k in ("rose", "red", "danger", "alert"):
        return world["rose"]
    return fallback or world["cyan"]


def _resolve_world(art_style: str, effective_tone: str) -> Dict[str, Any]:
    s = str(art_style or "").lower().strip()
    t = str(effective_tone or "").lower().strip()
    if s in ("light_whiteboard", "studio_white", "white"):
        return STUDIO_WORLDS["studio_white"]
    if s in ("blueprint_grid", "sapphire_3d"):
        return STUDIO_WORLDS["sapphire_3d"]
    if t == "dramatic_performance":
        return STUDIO_WORLDS["crimson_studio"]
    if t == "staff_engineer":
        return STUDIO_WORLDS["sapphire_3d"]
    return STUDIO_WORLDS["obsidian_studio"]


# =========================================================================
# CHOREOGRAPHY PROGRESS (VOICE-WORD SYNCED)
# =========================================================================
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


# =========================================================================
# LAYER 1: VECTORIZED VOLUMETRIC STUDIO BACKDROP + 3D PERSPECTIVE FLOOR
# =========================================================================
def _build_volumetric_studio_bg(w: int, h: int, world: Dict[str, Any]) -> Image.Image:
    """
    Fast NumPy-vectorized studio backdrop:
    - Smooth vertical vignette gradient
    - Dual radial volumetric spotlights
    - 3D vanishing-point perspective floor mesh
    """
    y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]

    top = np.array(world["bg_top"], dtype=np.float32)[None, None, :]
    bot = np.array(world["bg_bot"], dtype=np.float32)[None, None, :]
    arr = top * (1.0 - y[..., None]) + bot * y[..., None]

    # Volumetric Spot A (upper hero spotlight) and Spot B (lower rim glow)
    d2_a = ((x - 0.50) * 1.15) ** 2 + ((y - 0.24) * 1.45) ** 2
    spot_a_intensity = np.exp(-d2_a * 4.8)[..., None]
    d2_b = ((x - 0.80) * 1.2) ** 2 + ((y - 0.72) * 1.3) ** 2
    spot_b_intensity = np.exp(-d2_b * 5.2)[..., None]

    spot_a = np.array(world["spot_a"], dtype=np.float32)[None, None, :]
    spot_b = np.array(world["spot_b"], dtype=np.float32)[None, None, :]

    if world["is_light"]:
        # Soft sunlit paper halo tint
        arr = arr - 14.0 * spot_a_intensity + (spot_a - arr) * (spot_a_intensity * 0.09)
        arr = arr + (spot_b - arr) * (spot_b_intensity * 0.06)
    else:
        arr = arr + spot_a * (spot_a_intensity * 0.16) + spot_b * (spot_b_intensity * 0.12)

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # 3D Perspective Floor Plane near bottom third
    horizon_y = int(h * 0.68)
    grid_rgb = world["grid_col"]
    alpha_floor = 26 if not world["is_light"] else 34
    vx = w // 2
    vanish_y = int(h * 0.36)

    # Radial rays converging toward vanishing point
    for k in range(-7, 8):
        bx = vx + int(k * (w * 0.18))
        # Clip ray from horizon_y to h
        t0 = (horizon_y - vanish_y) / max(1.0, float(h - vanish_y))
        hx = int(vx + (bx - vx) * t0)
        draw.line((hx, horizon_y, bx, h), fill=(*grid_rgb, alpha_floor), width=2)

    # Perspective horizontal rings spacing out toward viewer
    for i in range(1, 9):
        t = (i / 8.0) ** 1.75
        ry = int(horizon_y + (h - horizon_y) * t)
        a_row = int(alpha_floor * (0.35 + 0.65 * t))
        draw.line((0, ry, w, ry), fill=(*grid_rgb, a_row), width=2)

    # Horizon subtle glow line
    draw.line((int(w * 0.06), horizon_y, int(w * 0.94), horizon_y), fill=(*grid_rgb, alpha_floor + 18), width=2)
    return img.convert("RGB")


# =========================================================================
# STUDIO RENDER CONTEXT (MULTI-PASS: SHADOW + CRISP FG + QUARTER-RES BLOOM)
# =========================================================================
class StudioStage:
    def __init__(self, width: int, height: int, world: Dict[str, Any]):
        self.w = width
        self.h = height
        self.world = world
        # Quarter-res buffers for ultra-fast shadows & optical Gaussian bloom (~1ms per frame)
        self.q_w = max(64, width // 4)
        self.q_h = max(64, height // 4)
        self.shadow_q = Image.new("RGBA", (self.q_w, self.q_h), (0, 0, 0, 0))
        self.sdraw = ImageDraw.Draw(self.shadow_q, "RGBA")
        self.glow_q = Image.new("RGBA", (self.q_w, self.q_h), (0, 0, 0, 0))
        self.gdraw = ImageDraw.Draw(self.glow_q, "RGBA")
        self.fg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.fg, "RGBA")

    def add_shadow_box(self, box: Tuple[int, int, int, int], radius: int = 24, offset_y: int = 14, alpha_mul: float = 1.0) -> None:
        if alpha_mul <= 0.05:
            return
        x1, y1, x2, y2 = box
        sc = _with_alpha(self.world["shadow_col"], alpha_mul)
        self.sdraw.rounded_rectangle(
            (x1 // 4, (y1 + offset_y) // 4, x2 // 4, (y2 + offset_y) // 4),
            radius=max(2, radius // 4),
            fill=sc,
        )

    def add_shadow_ellipse(self, box: Tuple[int, int, int, int], alpha_mul: float = 1.0) -> None:
        if alpha_mul <= 0.05:
            return
        x1, y1, x2, y2 = box
        sc = _with_alpha(self.world["shadow_col"], alpha_mul)
        self.sdraw.ellipse((x1 // 4, y1 // 4, x2 // 4, y2 // 4), fill=sc)

    def add_glow_box(self, box: Tuple[int, int, int, int], color: Tuple[int, int, int], radius: int = 24, alpha: int = 90) -> None:
        if alpha <= 4:
            return
        x1, y1, x2, y2 = box
        self.gdraw.rounded_rectangle(
            (x1 // 4, y1 // 4, x2 // 4, y2 // 4),
            radius=max(2, radius // 4),
            outline=(*color[:3], alpha),
            width=3,
        )

    def add_glow_orb(self, cx: float, cy: float, r: float, color: Tuple[int, int, int], alpha: int = 160) -> None:
        if alpha <= 4:
            return
        qx, qy, qr = cx / 4.0, cy / 4.0, max(2.0, r / 4.0)
        self.gdraw.ellipse((qx - qr, qy - qr, qx + qr, qy + qr), fill=(*color[:3], alpha))

    def add_glow_line(self, pts: List[Tuple[float, float]], color: Tuple[int, int, int], alpha: int = 130, width_q: int = 3) -> None:
        if len(pts) < 2 or alpha <= 4:
            return
        qpts = [(x / 4.0, y / 4.0) for x, y in pts]
        self.gdraw.line(qpts, fill=(*color[:3], alpha), width=width_q)

    def draw_glass_card(
        self,
        box: Tuple[int, int, int, int],
        accent: Tuple[int, int, int],
        radius: int = 24,
        alpha_mul: float = 1.0,
        active: bool = False,
        fill_override: Tuple[int, ...] = None,
    ) -> None:
        if alpha_mul <= 0.02:
            return
        x1, y1, x2, y2 = box
        w = self.world
        self.add_shadow_box(box, radius=radius, offset_y=16 if active else 12, alpha_mul=alpha_mul)
        if active:
            self.add_glow_box(box, accent, radius=radius, alpha=int(130 * alpha_mul))
        fill_c = _with_alpha(fill_override or w["card_bg"], alpha_mul)
        border_c = _with_alpha(accent if active else w["border"], alpha_mul * (1.0 if active else 0.78))
        self.draw.rounded_rectangle(box, radius=radius, fill=fill_c, outline=border_c, width=3 if active else 2)
        # Specular glass top highlight rim
        if x2 - x1 > 40:
            rim_c = _with_alpha(w["glass_rim"], alpha_mul)
            self.draw.line((x1 + radius, y1 + 2, x2 - radius, y1 + 2), fill=rim_c, width=2)

    def composite_onto(self, bg_rgb: Optional[Image.Image] = None) -> Image.Image:
        out = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0)) if bg_rgb is None else bg_rgb.convert("RGBA")
        # 1. Merge quarter-res shadow + bloom buffers BEFORE upsampling once (~2x faster compositing)
        sh = self.shadow_q.filter(ImageFilter.GaussianBlur(radius=6))
        gl = self.glow_q.filter(ImageFilter.GaussianBlur(radius=7))
        sh.alpha_composite(gl)
        atmos = sh.resize((self.w, self.h), Image.Resampling.BILINEAR)
        out.alpha_composite(atmos)
        # 2. Sharp Foreground Studio Layer
        out.alpha_composite(self.fg)
        return out


# =========================================================================
# 2.5D ISOMETRIC VECTOR PRIMITIVES & CUBIC BEZIER COMET CURVES
# =========================================================================
def _draw_iso_prism(
    stage: StudioStage,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    depth: int,
    color: Tuple[int, int, int],
    alpha_mul: float = 1.0,
    shape: str = "box",
    active: bool = False,
) -> None:
    """Draws an extruded 2.5D isometric 3D hardware block, layered stack, or database vault."""
    if alpha_mul <= 0.03:
        return
    # Soft floor shadow below prism
    stage.add_shadow_ellipse((cx - rx - 10, cy + depth + 4, cx + rx + 10, cy + depth + ry + 18), alpha_mul * 0.9)
    if active:
        stage.add_glow_orb(cx, cy + depth * 0.2, rx * 1.05, color, alpha=int(145 * alpha_mul))

    r, g, b = color[:3]
    top_col = _with_alpha((min(255, r + 52), min(255, g + 52), min(255, b + 52), 245), alpha_mul)
    left_col = _with_alpha((max(18, int(r * 0.56)), max(22, int(g * 0.58)), max(30, int(b * 0.62)), 250), alpha_mul)
    right_col = _with_alpha((max(10, int(r * 0.34)), max(14, int(g * 0.36)), max(20, int(b * 0.42)), 252), alpha_mul)
    wire_col = _with_alpha((min(255, r + 85), min(255, g + 85), min(255, b + 85), 240 if active else 170), alpha_mul)

    if shape == "cylinder":
        # 3D Isometric Storage Cylinder (DB / Vector Vault)
        body_poly = [
            (cx - rx, cy),
            (cx + rx, cy),
            (cx + rx, cy + depth),
            (cx - rx, cy + depth),
        ]
        stage.draw.rectangle((cx - rx, cy, cx + rx, cy + depth), fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - rx, cy + depth - ry, cx + rx, cy + depth + ry), fill=right_col, outline=wire_col, width=2)
        # Mid disk platter rings
        mid_y = cy + depth // 2
        stage.draw.arc((cx - rx, mid_y - ry, cx + rx, mid_y + ry), start=0, end=180, fill=wire_col, width=2)
        stage.draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=top_col, outline=wire_col, width=3 if active else 2)
    elif shape == "stack":
        # 3-Tier Stacked Isometric Compute Slabs
        tier_d = max(12, depth // 3 - 4)
        for ti in range(3):
            ty = cy + (2 - ti) * (tier_d + 6)
            t_pts = [(cx, ty - ry), (cx + rx, ty), (cx, ty + ry), (cx - rx, ty)]
            l_pts = [(cx - rx, ty), (cx, ty + ry), (cx, ty + ry + tier_d), (cx - rx, ty + tier_d)]
            r_pts = [(cx + rx, ty), (cx, ty + ry), (cx, ty + ry + tier_d), (cx + rx, ty + tier_d)]
            stage.draw.polygon(l_pts, fill=left_col, outline=wire_col, width=1)
            stage.draw.polygon(r_pts, fill=right_col, outline=wire_col, width=1)
            stage.draw.polygon(t_pts, fill=top_col if ti == 2 else left_col, outline=wire_col, width=2)
    else:
        # Extruded 3D Isometric Cube / Node Block
        t_pts = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]
        l_pts = [(cx - rx, cy), (cx, cy + ry), (cx, cy + ry + depth), (cx - rx, cy + depth)]
        r_pts = [(cx + rx, cy), (cx, cy + ry), (cx, cy + ry + depth), (cx + rx, cy + depth)]
        stage.draw.polygon(l_pts, fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon(r_pts, fill=right_col, outline=wire_col, width=2)
        stage.draw.polygon(t_pts, fill=top_col, outline=wire_col, width=3 if active else 2)
        # Inner bright wireframe bevel on top diamond
        irx, iry = int(rx * 0.62), int(ry * 0.62)
        inner_top = [(cx, cy - iry), (cx + irx, cy), (cx, cy + iry), (cx - irx, cy)]
        stage.draw.polygon(inner_top, outline=_with_alpha(color, alpha_mul * 0.85), width=2)
        # Hardware status LED bar on left wall
        stage.draw.line((cx - rx + 10, cy + 12, cx - rx + 10, cy + depth - 4), fill=wire_col, width=3)


def _bezier_points(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    steps: int = 28,
) -> List[Tuple[float, float]]:
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        mt = 1.0 - t
        bx = (mt ** 3) * p0[0] + 3 * (mt ** 2) * t * p1[0] + 3 * mt * (t ** 2) * p2[0] + (t ** 3) * p3[0]
        by = (mt ** 3) * p0[1] + 3 * (mt ** 2) * t * p1[1] + 3 * mt * (t ** 2) * p2[1] + (t ** 3) * p3[1]
        pts.append((bx, by))
    return pts


def _draw_bezier_comet(
    stage: StudioStage,
    p0: Tuple[float, float],
    p3: Tuple[float, float],
    color: Tuple[int, int, int],
    progress: float,
    reveal_t: float,
    label: str = "",
    curve_offset_x: float = 0.0,
) -> None:
    """Draws a smooth cubic Bezier energy conduit with glowing bloom and trailing data comet."""
    if reveal_t <= 0.02:
        return
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    c1 = (p0[0] + curve_offset_x + dx * 0.15, p0[1] + dy * 0.45)
    c2 = (p3[0] + curve_offset_x - dx * 0.15, p3[1] - dy * 0.45)

    all_pts = _bezier_points(p0, c1, c2, p3, steps=30)
    vis_n = max(2, int(len(all_pts) * min(1.0, reveal_t)))
    vis_pts = all_pts[:vis_n]

    # Soft glow path + sharp inner core conduit
    stage.add_glow_line(vis_pts, color, alpha=145, width_q=3)
    stage.draw.line(vis_pts, fill=_with_alpha(color, 0.72), width=4)

    # Moving plasma comet + trailing glow tail
    if reveal_t < 0.96:
        hx, hy = vis_pts[-1]
        stage.add_glow_orb(hx, hy, 16, color, alpha=210)
        stage.draw.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), fill=(255, 255, 255, 255))
        return

    # Arrowhead
    ax_prev, ay_prev = vis_pts[-3]
    ax_end, ay_end = vis_pts[-1]
    ang = math.atan2(ay_end - ay_prev, ax_end - ax_prev)
    alen = 15.0
    aang = math.pi / 6.0
    p_a = (ax_end - alen * math.cos(ang - aang), ay_end - alen * math.sin(ang - aang))
    p_b = (ax_end - alen * math.cos(ang + aang), ay_end - alen * math.sin(ang + aang))
    stage.draw.polygon([(ax_end, ay_end), p_a, p_b], fill=(*color[:3], 245))

    # Orbiting comet pulse along finished curve
    head_t = (progress * 1.85) % 1.0
    n_tot = len(all_pts) - 1
    for tail_i in range(7):
        tt = head_t - tail_i * 0.024
        if tt < 0.0 or tt > 1.0:
            continue
        p_idx = int(tt * n_tot)
        px, py = all_pts[p_idx]
        fade = 1.0 - (tail_i / 7.0)
        rad = max(2, int(7 * fade))
        if tail_i == 0:
            stage.add_glow_orb(px, py, 16, color, alpha=220)
            stage.draw.ellipse((px - 6, py - 6, px + 6, py + 6), fill=(255, 255, 255, 255))
        else:
            stage.draw.ellipse((px - rad, py - rad, px + rad, py + rad), fill=_with_alpha(color, 0.85 * fade))

    if label:
        mx, my = all_pts[len(all_pts) // 2]
        f_lbl = _get_font(17, bold=True)
        bb = f_lbl.getbbox(label)
        tw = bb[2] - bb[0]
        bw = tw + 24
        box = (int(mx - bw // 2), int(my - 15), int(mx + bw // 2), int(my + 15))
        stage.draw.rounded_rectangle(box, radius=10, fill=stage.world["card_alt"], outline=(*color[:3], 200), width=2)
        stage.draw.text((int(mx - tw // 2), int(my - 10)), label, fill=stage.world["amber"], font=f_lbl)


# =========================================================================
# VOICE-REACTIVE SPECTRUM VISUALIZER, HEADER & STUDIO CHROME
# =========================================================================
def _draw_voice_waveform(
    draw: ImageDraw.Draw,
    world: Dict[str, Any],
    scene_words: List[Dict[str, Any]],
    cur_time: float,
    progress: float,
    canvas_w: int,
) -> None:
    """Draws a crisp audio-reactive live waveform ribbon in top-left Chrome aligned with watermark."""
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


def _draw_studio_header(stage: StudioStage, badge: str, title: str, accent: Tuple[int, int, int]) -> None:
    w = stage.world
    lx = 68
    y_cur = 104
    badge_s = str(badge or "").strip().upper()
    if badge_s:
        f_b = _get_font(23, bold=True)
        bb = f_b.getbbox(badge_s)
        pw = min(860, (bb[2] - bb[0]) + 56)
        pill_box = (lx, y_cur, lx + pw, y_cur + 40)
        stage.add_glow_box(pill_box, accent, radius=14, alpha=80)
        stage.draw.rounded_rectangle(pill_box, radius=14, fill=w["card_alt"], outline=(*accent, 210), width=2)
        stage.draw.ellipse((lx + 14, y_cur + 15, lx + 24, y_cur + 25), fill=accent)
        stage.draw.text((lx + 34, y_cur + 7), badge_s, fill=accent, font=f_b)
        y_cur += 54

    if title:
        _draw_wrapped_text(stage.draw, str(title), _get_font(46, bold=True), lx, y_cur, 940, w["text"], line_spacing=8, max_lines=2)


# =========================================================================
# CINEMATIC 2.5D ARCHETYPES & DYNAMIC BLOCK STUDIO
# =========================================================================
def _draw_vector_check(stage: StudioStage, cx: int, cy: int, radius: int, color: Tuple[int, int, int], alpha_mul: float) -> None:
    c = _with_alpha(color, alpha_mul)
    ink = _with_alpha(stage.world["text"], alpha_mul)
    stage.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_with_alpha((*color[:3], 45), alpha_mul), outline=c, width=3)
    pts = [(cx - radius * 0.42, cy), (cx - radius * 0.1, cy + radius * 0.34), (cx + radius * 0.46, cy - radius * 0.34)]
    stage.draw.line(pts, fill=ink, width=4)


def _draw_vector_warn(stage: StudioStage, cx: int, cy: int, radius: int, color: Tuple[int, int, int], alpha_mul: float) -> None:
    c = _with_alpha(color, alpha_mul)
    ink = _with_alpha(stage.world["text"], alpha_mul)
    stage.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_with_alpha((*color[:3], 45), alpha_mul), outline=c, width=3)
    stage.draw.line((cx, cy - int(radius * 0.42), cx, cy + int(radius * 0.14)), fill=ink, width=4)
    stage.draw.ellipse((cx - 3, cy + int(radius * 0.28), cx + 3, cy + int(radius * 0.46)), fill=ink)


def _render_iso_architecture(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    Signature 2.5D Isometric Architecture & Data-Flow Scene:
    Staggered 3D extruded nodes (prisms / stacks / cylinders) joined by
    glowing cubic Bezier S-curves and animated plasma comets.
    """
    w = stage.world
    raw_nodes = data.get("nodes") or data.get("stages") or data.get("steps") or []
    edges = data.get("edges") or data.get("arrows") or []
    if not raw_nodes:
        raw_nodes = [
            {"label": str(data.get("title") or "Input Stream"), "sub": "Ingress", "shape": "box"},
            {"label": "Core Processing", "sub": "Transform & Route", "shape": "stack"},
            {"label": "Storage Tier", "sub": "Durable Index", "shape": "cylinder"},
        ]

    nodes: List[Dict[str, str]] = []
    shapes_cycle = ["box", "stack", "cylinder", "box"]
    cols_cycle = [w["cyan"], w["purple"], w["emerald"], w["amber"]]
    for idx, rn in enumerate(raw_nodes[:4]):
        if isinstance(rn, dict):
            lbl = str(rn.get("label") or rn.get("title") or rn.get("name") or f"Stage {idx+1}")
            sub = str(rn.get("sub") or rn.get("desc") or rn.get("description") or "")
            shp = str(rn.get("shape") or "").lower().strip()
            if not shp:
                low_l = lbl.lower()
                shp = "cylinder" if any(k in low_l for k in ["db", "vector", "sql", "store", "cache", "lake", "s3"]) else ("stack" if any(k in low_l for k in ["model", "llm", "cluster", "engine", "gpu", "rag"]) else shapes_cycle[idx % len(shapes_cycle)])
            col = _resolve_color(rn.get("color", ""), w, cols_cycle[idx % len(cols_cycle)])
        else:
            lbl = str(rn)
            sub = ""
            low_l = lbl.lower()
            shp = "cylinder" if any(k in low_l for k in ["db", "vector", "sql", "store", "cache", "lake"]) else ("stack" if any(k in low_l for k in ["model", "llm", "cluster", "engine", "rag"]) else shapes_cycle[idx % len(shapes_cycle)])
            col = cols_cycle[idx % len(cols_cycle)]
        nodes.append({"label": lbl, "sub": sub, "shape": shp, "color": col})

    n = len(nodes)
    start_y = 390 if n == 4 else (420 if n == 3 else 480)
    step_y = 248 if n == 4 else (315 if n == 3 else 390)
    span_each = 0.72 / max(1, n)

    anchors_conn: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int, int], float]] = []
    for i, nd in enumerate(nodes):
        gate = 0.0 if i == 0 else (0.04 + i * span_each * 0.78)
        alpha, dy, _ = _spring_gate(progress, gate, span=0.14)
        iso_on_left = (i % 2 == 0)
        iso_cx = 235 if iso_on_left else 845
        card_x1 = 365 if iso_on_left else 70
        card_x2 = 1010 if iso_on_left else 715
        card_h = 148 if n <= 3 else 128
        cy_base = start_y + i * step_y
        anchors_conn.append(((iso_cx, cy_base + card_h // 2 + 66), (iso_cx, cy_base + card_h // 2 - 58), nd["color"], gate))
        if alpha <= 0.02:
            continue

        cy = cy_base + dy
        is_active = (gate <= progress < gate + span_each) or (i == n - 1 and progress >= gate)

        # Draw Glass Label Card first, then 3D Isometric Prism cleanly floating beside it
        stage.draw_glass_card((card_x1, cy, card_x2, cy + card_h), nd["color"], radius=22, alpha_mul=alpha, active=is_active)
        _draw_iso_prism(stage, iso_cx, cy + card_h // 2 - 22, rx=72, ry=32, depth=56, color=nd["color"], alpha_mul=alpha, shape=nd["shape"], active=is_active)

        # Horizontal tether glow bar connecting prism -> glass card
        tether_x1 = iso_cx + 82 if iso_on_left else card_x2
        tether_x2 = card_x1 if iso_on_left else iso_cx - 82
        stage.draw.line((tether_x1, cy + card_h // 2, tether_x2, cy + card_h // 2), fill=_with_alpha(nd["color"], alpha * 0.8), width=3)

        # Step Pill + Text inside Card
        badge_txt = f"0{i+1}"
        f_num = _get_font(20, bold=True)
        stage.draw.rounded_rectangle((card_x1 + 22, cy + 20, card_x1 + 66, cy + 52), radius=10, fill=_with_alpha(nd["color"], alpha))
        stage.draw.text((card_x1 + 31, cy + 25), badge_txt, fill=(255, 255, 255, int(255 * alpha)), font=f_num)

        txt_x = card_x1 + 82
        txt_w = (card_x2 - card_x1) - 104
        if nd["sub"]:
            _draw_wrapped_text(stage.draw, nd["label"], _get_font(29, bold=True), txt_x, cy + 18, txt_w, _with_alpha(w["text"], alpha), max_lines=1)
            _draw_wrapped_text(stage.draw, nd["sub"], _get_font(22), txt_x, cy + 62, txt_w, _with_alpha(w["muted"], alpha), max_lines=2)
        else:
            _draw_wrapped_text(stage.draw, nd["label"], _get_font(30, bold=True), txt_x, cy + max(24, (card_h - 38) // 2), txt_w, _with_alpha(w["text"], alpha), max_lines=2)

    # Sweeping Cubic Bezier Comet Curves connecting Prism i -> Prism i+1
    for i in range(n - 1):
        p_out, _, col_i, g_i = anchors_conn[i]
        _, p_in, _, g_next = anchors_conn[i + 1]
        conn_start = g_i + 0.05
        rev_t = _clamp01((progress - conn_start) / max(0.08, (g_next - conn_start + 0.04)))
        if progress >= g_i + 0.05 and rev_t > 0.02:
            e_lbl = str(edges[i]) if i < len(edges) else ""
            _draw_bezier_comet(stage, p_out, p_in, col_i, progress, rev_t, label=e_lbl)


def _render_dual_pedestal_3d(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    2.5D Dual Comparison Pedestals with floating 3D Isometric emblem prisms,
    specular glass panels, progressive check items, and energy core bridge.
    """
    w = stage.world
    left_label = str(data.get("left_label") or data.get("left_pillar", {}).get("label") or "Option A")
    right_label = str(data.get("right_label") or data.get("right_pillar", {}).get("label") or "Option B")
    left_pts = data.get("left_points") or data.get("cons") or ([data["left_pillar"]["sub"]] if isinstance(data.get("left_pillar"), dict) and data["left_pillar"].get("sub") else [])
    right_pts = data.get("right_points") or data.get("pros") or ([data["right_pillar"]["sub"]] if isinstance(data.get("right_pillar"), dict) and data["right_pillar"].get("sub") else [])

    neutral = bool(data.get("neutral_mode", False))
    show_vs = bool(data.get("show_vs", True))
    l_col = w["cyan"] if neutral else w["rose"]
    r_col = w["purple"] if neutral else w["emerald"]

    col_w = 435
    lx, rx = 70, 575
    top_y = 485
    card_h = 660

    # Left floating 3D isometric emblem prism + spring card
    al_l, dy_l, _ = _spring_gate(progress, 0.0, 0.14)
    _draw_iso_prism(stage, lx + col_w // 2, top_y - 70 + dy_l, rx=62, ry=24, depth=38, color=l_col, alpha_mul=al_l, shape="box", active=(progress < 0.48))
    stage.draw_glass_card((lx, top_y + dy_l, lx + col_w, top_y + card_h + dy_l), l_col, radius=26, alpha_mul=al_l, active=(progress < 0.48))
    _draw_wrapped_text(stage.draw, left_label.upper(), _get_font(26, bold=True), lx + 24, top_y + 28 + dy_l, col_w - 48, _with_alpha(l_col, al_l), align="center", max_lines=2)

    for i, pt in enumerate(left_pts[:3]):
        ga = 0.08 + i * 0.11
        ap, pdy, _ = _spring_gate(progress, ga, 0.12)
        if ap <= 0.02:
            continue
        py = top_y + 118 + i * 168 + dy_l + pdy
        stage.draw.rounded_rectangle((lx + 22, py, lx + col_w - 22, py + 142), radius=18, fill=_with_alpha(w["card_alt"], ap), outline=_with_alpha((*l_col, 110), ap), width=1)
        stage.draw.ellipse((lx + 40, py + 28, lx + 56, py + 44), fill=_with_alpha(l_col, ap))
        _draw_wrapped_text(stage.draw, str(pt), _get_font(25), lx + 70, py + 22, col_w - 104, _with_alpha(w["text"], ap), max_lines=3, line_spacing=6)

    # Right floating 3D isometric emblem prism + spring card
    al_r, dy_r, _ = _spring_gate(progress, 0.32, 0.15)
    if al_r > 0.02:
        _draw_iso_prism(stage, rx + col_w // 2, top_y - 70 + dy_r, rx=62, ry=24, depth=38, color=r_col, alpha_mul=al_r, shape="stack", active=(progress >= 0.45))
        stage.draw_glass_card((rx, top_y + dy_r, rx + col_w, top_y + card_h + dy_r), r_col, radius=26, alpha_mul=al_r, active=(progress >= 0.45))
        _draw_wrapped_text(stage.draw, right_label.upper(), _get_font(26, bold=True), rx + 24, top_y + 28 + dy_r, col_w - 48, _with_alpha(r_col, al_r), align="center", max_lines=2)

        for i, pt in enumerate(right_pts[:3]):
            ga = 0.40 + i * 0.11
            ap, pdy, _ = _spring_gate(progress, ga, 0.12)
            if ap <= 0.02:
                continue
            py = top_y + 118 + i * 168 + dy_r + pdy
            stage.draw.rounded_rectangle((rx + 22, py, rx + col_w - 22, py + 142), radius=18, fill=_with_alpha(w["card_alt"], ap), outline=_with_alpha((*r_col, 110), ap), width=1)
            if neutral:
                stage.draw.ellipse((rx + 40, py + 28, rx + 56, py + 44), fill=_with_alpha(r_col, ap))
            else:
                _draw_vector_check(stage, rx + 50, py + 38, 14, r_col, ap)
            _draw_wrapped_text(stage.draw, str(pt), _get_font(25), rx + 74, py + 22, col_w - 106, _with_alpha(w["text"], ap), max_lines=3, line_spacing=6)

    # Energy VS Orb Bridge
    if show_vs and progress >= 0.34:
        va, _, _ = _spring_gate(progress, 0.34, 0.12)
        vx, vy = VIDEO_WIDTH // 2, top_y + card_h // 2
        stage.add_glow_orb(vx, vy, 48, w["amber"], alpha=int(180 * va))
        stage.draw.ellipse((vx - 40, vy - 40, vx + 40, vy + 40), fill=_with_alpha(w["card_alt"], va), outline=_with_alpha(w["amber"], va), width=3)
        stage.draw.text((vx - 21, vy - 16), "VS", fill=_with_alpha(w["amber"], va), font=_get_font(26, bold=True))


def _render_terminal_studio(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """Glassmorphic IDE Terminal with active-line spotlight beam and smooth typewriter cursor."""
    w = stage.world
    raw_code = str(data.get("code_snippet") or data.get("code") or data.get("command") or "")
    if not raw_code:
        raw_code = "# Real-time pipeline configuration\nasync def process_event(payload):\n    return await store.commit(payload)"
    lines = raw_code.splitlines()[:9]

    tx, ty, tw, th = 68, 390, 944, 770
    al, dy, _ = _spring_gate(progress, 0.0, 0.12)
    box = (tx, ty + dy, tx + tw, ty + th + dy)
    stage.add_shadow_box(box, radius=28, offset_y=20, alpha_mul=al)
    stage.add_glow_box(box, w["cyan"], radius=28, alpha=110)

    # Frosted dark IDE glass shell (always high-contrast code window even on light studio!)
    stage.draw.rounded_rectangle(box, radius=28, fill=(13, 18, 30, 245), outline=(*w["cyan"], 175), width=3)
    stage.draw.rounded_rectangle((tx, ty + dy, tx + tw, ty + dy + 62), radius=28, fill=(24, 33, 54, 250))
    stage.draw.ellipse((tx + 26, ty + dy + 22, tx + 44, ty + dy + 40), fill=(244, 63, 94))
    stage.draw.ellipse((tx + 56, ty + dy + 22, tx + 74, ty + dy + 40), fill=(251, 191, 36))
    stage.draw.ellipse((tx + 86, ty + dy + 22, tx + 104, ty + dy + 40), fill=(52, 211, 153))

    title_bar = "query.sql — Studio" if any(k in raw_code.upper() for k in ("SELECT", "FROM", "WHERE")) else "studio_runner.py"
    stage.draw.text((tx + 135, ty + dy + 19), title_bar, fill=(148, 163, 184), font=_get_font(23, bold=True))

    total_chars = max(1, len(raw_code))
    chars_shown = int(total_chars * min(1.0, progress * 1.38 + 0.18))
    f_code = _get_font(28)
    seen = 0
    active_line_idx = 0
    for li, ln in enumerate(lines):
        if seen <= chars_shown:
            active_line_idx = li
        seen += len(ln) + 1

    seen = 0
    line_y0 = ty + dy + 98
    row_h = 68
    for li, ln in enumerate(lines):
        ly = line_y0 + li * row_h
        is_cur_line = (li == active_line_idx)
        if is_cur_line:
            stage.draw.rounded_rectangle((tx + 18, ly - 10, tx + tw - 18, ly + row_h - 18), radius=12, fill=(56, 189, 248, 28), outline=(56, 189, 248, 90), width=1)
        stage.draw.text((tx + 32, ly), f"{li+1:2d}", fill=(100, 116, 139), font=f_code)
        rem = max(0, chars_shown - seen)
        vis = ln[:rem]
        while vis and (f_code.getbbox(vis)[2] - f_code.getbbox(vis)[0]) > tw - 150:
            vis = vis[:-1]
        if ln.lstrip().startswith("#") or ln.lstrip().startswith("//"):
            code_col = (148, 163, 184)
        elif any(k in ln for k in ("def ", "async ", "SELECT", "FROM", "return", "await ", "import ")):
            code_col = (52, 211, 153)
        else:
            code_col = (248, 250, 252)
        stage.draw.text((tx + 96, ly), vis, fill=code_col, font=f_code)
        seen += len(ln) + 1
        if seen >= chars_shown:
            vx = tx + 98 + (f_code.getbbox(vis)[2] - f_code.getbbox(vis)[0] if vis else 0)
            stage.draw.rounded_rectangle((vx, ly + 2, vx + 10, ly + 32), radius=2, fill=w["cyan"])
            break

    # Optional Output Console Drawer below code
    out_txt = str(data.get("output") or "").strip()
    if out_txt and progress >= 0.65:
        oa, ody, _ = _spring_gate(progress, 0.65, 0.14)
        oy = ty + th + dy + 28 + ody
        stage.draw_glass_card((tx, oy, tx + tw, oy + 145), w["emerald"], radius=22, alpha_mul=oa, active=True)
        stage.draw.text((tx + 28, oy + 20), "STDOUT", fill=_with_alpha(w["emerald"], oa), font=_get_font(19, bold=True))
        _draw_wrapped_text(stage.draw, out_txt, _get_font(25, bold=True), tx + 28, oy + 56, tw - 56, _with_alpha(w["text"], oa), max_lines=2)


def _render_cinematic_custom_scene(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    Upgraded Studio Block Renderer with Spring Physics, 3D Isometric Prism Flow Chains,
    Cubic Bezier Comets, Soft Blurred Drop Shadows, and Luminous Glass Focus.
    """
    w = stage.world
    blocks = list(data.get("blocks") or [])[:4]
    if not blocks:
        # Synthesize clean blocks from visual_data fields
        if data.get("question") or data.get("problem_title"):
            blocks.append({"block": "question_card", "text": str(data.get("question") or data.get("problem_title")), "eyebrow": str(data.get("eyebrow") or ""), "stage": 1})
        pills = data.get("pills") or ([data.get("left_pill"), data.get("right_pill")] if data.get("left_pill") and data.get("right_pill") else [])
        if pills:
            blocks.append({"block": "pills", "items": pills, "mode": "vs" if data.get("show_vs") else "row", "stage": 2})
        if data.get("stat_badge"):
            blocks.append({"block": "banner", "text": str(data["stat_badge"]), "tone": "highlight", "stage": 3})
        if data.get("bullets") or data.get("points"):
            blocks.append({"block": "list_cards", "items": list((data.get("bullets") or data.get("points"))[:4]), "stage": 1 if not blocks else 3})
        if data.get("statement"):
            blocks.append({"block": "question_card", "text": str(data["statement"]), "stage": 1})
        if data.get("warning_box"):
            blocks.append({"block": "banner", "text": str(data["warning_box"]), "tone": "warn", "stage": 3})
        if data.get("footer_cta") or data.get("cta_text"):
            blocks.append({"block": "banner", "text": str(data.get("footer_cta") or data.get("cta_text")), "tone": "cta", "stage": 4})
        if not blocks:
            blocks.append({"block": "question_card", "text": str(data.get("title") or "Architecture Deep Dive"), "stage": 1})

    # If the ONLY block is a 3-4 node flow_chain, showcase full 2.5D Isometric Architecture!
    if len(blocks) == 1 and str(blocks[0].get("block", "")).lower().strip() == "flow_chain":
        fc = blocks[0]
        _render_iso_architecture(stage, {"nodes": fc.get("nodes", []), "edges": fc.get("edges") or fc.get("arrows") or []}, progress)
        return

    n_b = len(blocks)
    avail_top = 365
    avail_bot = 1395
    avail_h = avail_bot - avail_top
    only_one = (n_b == 1)

    font_q = _get_font(38, bold=True)
    font_ban = _get_font(27, bold=True)
    ideal_h: List[int] = []
    for b in blocks:
        bt = str(b.get("block", "list_cards")).lower().strip()
        if bt == "big_stat":
            ideal_h.append(186 if only_one else 160)
        elif bt == "question_card":
            ey = str(b.get("eyebrow") or "").strip()
            nl = _est_lines(str(b.get("text", "")), font_q, 830, 3)
            ideal_h.append((86 if ey else 58) + nl * 50)
        elif bt == "pills":
            its = b.get("items") or []
            mode = str(b.get("mode", "row")).lower().strip()
            rows = math.ceil(min(4, max(1, len(its))) / 2) if (mode == "grid" or len(its) > 3) else 1
            ideal_h.append(rows * 94 + max(0, rows - 1) * 16)
        elif bt == "flow_chain":
            nds = b.get("nodes") or []
            cnt = min(4, max(1, len(nds)))
            nh = 88 if cnt <= 3 else 76
            ag = 50 if cnt <= 3 else 38
            ideal_h.append(cnt * nh + max(0, cnt - 1) * ag)
        elif bt == "code":
            cl = str(b.get("code", "")).splitlines()[:5]
            ideal_h.append(72 + max(2, len(cl)) * 44)
        elif bt == "banner":
            nl = _est_lines(str(b.get("text", "")), font_ban, 820, 2)
            ideal_h.append(58 + nl * 36)
        else:
            cnt = max(1, min(4, len(b.get("items") or [])))
            rh = 152 if only_one else (112 if cnt <= 3 else 94)
            ideal_h.append(cnt * rh + max(0, cnt - 1) * 16)

    gap = 28 if n_b <= 3 else 20
    tot_h = sum(ideal_h) + max(0, n_b - 1) * gap
    scale = 1.0 if tot_h <= avail_h else max(0.74, avail_h / max(1, tot_h))
    gap = max(14, int(gap * scale))
    heights = [max(72, int(h * scale)) for h in ideal_h]
    y_cur = avail_top + max(0, min(90, (avail_h - (sum(heights) + max(0, n_b - 1) * gap)) // 3))

    cx = 70
    cw = VIDEO_WIDTH - 140
    cols_cycle = [w["cyan"], w["purple"], w["emerald"], w["amber"]]

    for idx, (b, bh) in enumerate(zip(blocks, heights)):
        bt = str(b.get("block", "list_cards")).lower().strip()
        stage_num = int(b.get("stage", idx + 1)) if str(b.get("stage", "")).isdigit() else (idx + 1)
        gate = 0.0 if (idx == 0 or stage_num <= 1) else min(0.70, (stage_num - 1) * 0.20)
        alpha, dy, _ = _spring_gate(progress, gate, span=0.14)
        if alpha <= 0.02:
            y_cur += bh + gap
            continue

        next_gate = min(0.95, gate + 0.22)
        is_active = (gate <= progress < next_gate) or (idx == n_b - 1 and progress >= gate)
        col_acc = _resolve_color(b.get("color", ""), w, w["cyan"])
        yc = y_cur + dy

        if bt == "big_stat":
            val_str = str(b.get("value") or b.get("val") or b.get("number") or b.get("stat") or b.get("metric") or b.get("headline") or b.get("text") or "").strip()
            lbl_str = str(b.get("label") or "").upper().strip()
            stage.draw_glass_card((cx, yc, cx + cw, yc + bh), col_acc, radius=26, alpha_mul=alpha, active=is_active)
            # Subtle 3D prism icon accent on left side of metric card
            _draw_iso_prism(stage, cx + 84, yc + bh // 2 - 14, rx=38, ry=16, depth=26, color=col_acc, alpha_mul=alpha, shape="box", active=is_active)
            if val_str:
                fb = _get_font(66 if len(val_str) <= 6 else (48 if len(val_str) <= 14 else 38), bold=True)
                vb = fb.getbbox(val_str)
                vx = cx + 150 + max(0, ((cw - 175) - (vb[2] - vb[0])) // 2)
                stage.add_glow_orb(vx + (vb[2] - vb[0]) // 2, yc + 48, 42, col_acc, alpha=int(120 * alpha))
                stage.draw.text((vx, yc + (20 if lbl_str else max(26, (bh - 70) // 2))), val_str, fill=_with_alpha(col_acc, alpha), font=fb)
                if lbl_str:
                    _draw_wrapped_text(stage.draw, lbl_str, _get_font(22, bold=True), cx + 150, yc + bh - 48, cw - 175, _with_alpha(w["text"], alpha), align="center", max_lines=1)
            elif lbl_str:
                _draw_wrapped_text(stage.draw, lbl_str, _get_font(32, bold=True), cx + 150, yc + max(28, (bh - 42) // 2), cw - 175, _with_alpha(col_acc, alpha), align="center", max_lines=2)

        elif bt == "question_card":
            eyebrow = str(b.get("eyebrow") or "").strip().upper()
            q_text = str(b.get("text") or "")
            stage.draw_glass_card((cx, yc, cx + cw, yc + bh), col_acc, radius=28, alpha_mul=alpha, active=is_active)
            stage.draw.rounded_rectangle((cx + 22, yc + 22, cx + 29, yc + bh - 22), radius=3, fill=_with_alpha(col_acc, alpha))
            ttop = yc + 24
            if eyebrow:
                _draw_wrapped_text(stage.draw, eyebrow, _get_font(20, bold=True), cx + 52, ttop, cw - 90, _with_alpha(col_acc, alpha), align="center", max_lines=1)
                ttop += 34
            else:
                ttop = yc + max(22, (bh - _est_lines(q_text, font_q, cw - 110, 3) * 48) // 2)
            _draw_wrapped_text(stage.draw, q_text, font_q, cx + 52, ttop, cw - 104, _with_alpha(w["text"], alpha), align="center", max_lines=3, line_spacing=8)

        elif bt == "pills":
            items = b.get("items") or []
            mode = str(b.get("mode", "row")).lower().strip()
            clean_it = [(str(it.get("label") or it.get("text") or ""), it.get("color", "")) if isinstance(it, dict) else (str(it), "") for it in items[:4]]
            ni = len(clean_it)
            if ni == 2 and mode == "vs":
                pw = 415
                gp = cw - pw * 2
                for pi, (pt, pc_s) in enumerate(clean_it):
                    pa, pdy, _ = _spring_gate(progress, gate + pi * 0.08, 0.12)
                    if pa <= 0.02:
                        continue
                    px = cx + pi * (pw + gp)
                    pc = _resolve_color(pc_s, w, cols_cycle[pi % len(cols_cycle)])
                    stage.draw_glass_card((px, yc + pdy, px + pw, yc + bh + pdy), pc, radius=22, alpha_mul=pa, active=(pi == 1 or progress < gate + 0.16))
                    _draw_wrapped_text(stage.draw, pt, _get_font(28, bold=True), px + 18, yc + pdy + max(18, (bh - 34) // 2), pw - 36, _with_alpha(pc, pa), align="center", max_lines=2)
                if progress >= gate + 0.08:
                    va, _, _ = _spring_gate(progress, gate + 0.08, 0.10)
                    vx, vy = cx + cw // 2, yc + bh // 2
                    stage.add_glow_orb(vx, vy, 34, w["amber"], alpha=int(180 * va))
                    stage.draw.ellipse((vx - 30, vy - 30, vx + 30, vy + 30), fill=_with_alpha(w["card_alt"], va), outline=_with_alpha(w["amber"], va), width=3)
                    stage.draw.text((vx - 17, vy - 14), "VS", fill=_with_alpha(w["amber"], va), font=_get_font(22, bold=True))
            elif mode == "grid" or ni > 3:
                cwg = (cw - 20) // 2
                rows = math.ceil(ni / 2)
                ch = max(62, (bh - (rows - 1) * 14) // max(1, rows))
                for pi, (pt, pc_s) in enumerate(clean_it):
                    pa, pdy, _ = _spring_gate(progress, gate + pi * 0.07, 0.11)
                    if pa <= 0.02:
                        continue
                    r_i, c_i = pi // 2, pi % 2
                    px = cx + c_i * (cwg + 20)
                    py_i = yc + r_i * (ch + 14) + pdy
                    pc = _resolve_color(pc_s, w, cols_cycle[pi % len(cols_cycle)])
                    stage.draw_glass_card((px, py_i, px + cwg, py_i + ch), pc, radius=18, alpha_mul=pa, active=is_active)
                    _draw_wrapped_text(stage.draw, pt, _get_font(24, bold=True), px + 16, py_i + max(14, (ch - 30) // 2), cwg - 32, _with_alpha(w["text"], pa), align="center", max_lines=2)
            else:
                pgap = 20 if mode != "arrow" else 42
                pw = (cw - max(0, ni - 1) * pgap) // max(1, ni)
                fp = _get_font(26 if ni <= 2 else 22, bold=True)
                for pi, (pt, pc_s) in enumerate(clean_it):
                    pa, pdy, _ = _spring_gate(progress, gate + pi * 0.08, 0.11)
                    if pa <= 0.02:
                        continue
                    px = cx + pi * (pw + pgap)
                    pc = _resolve_color(pc_s, w, cols_cycle[pi % len(cols_cycle)])
                    stage.draw_glass_card((px, yc + pdy, px + pw, yc + bh + pdy), pc, radius=20, alpha_mul=pa, active=is_active)
                    _draw_wrapped_text(stage.draw, pt, fp, px + 14, yc + pdy + max(16, (bh - 32) // 2), pw - 28, _with_alpha(w["text"], pa), align="center", max_lines=2)
                    if mode == "arrow" and pi < ni - 1:
                        ax1 = px + pw + 6
                        ax2 = ax1 + pgap - 12
                        ay = yc + bh // 2
                        stage.draw.line((ax1, ay, ax2, ay), fill=_with_alpha(w["amber"], pa), width=4)
                        stage.draw.polygon([(ax2 + 6, ay), (ax2 - 6, ay - 7), (ax2 - 6, ay + 7)], fill=_with_alpha(w["amber"], pa))

        elif bt == "flow_chain":
            nds = b.get("nodes") or []
            eds = b.get("edges") or b.get("arrows") or []
            cnt = min(4, max(1, len(nds)))
            ag = max(32, min(58, int(bh * 0.14))) if cnt > 1 else 0
            nh = max(66, (bh - max(0, cnt - 1) * ag) // cnt)
            step_span = 0.68 / max(1, cnt)
            for ni, rn in enumerate(nds[:4]):
                ng = gate + (0.0 if ni == 0 else ni * step_span * 0.55)
                na, ndy, _ = _spring_gate(progress, ng, 0.12)
                if na <= 0.02:
                    continue
                ny = y_cur + ni * (nh + ag) + ndy
                nc = cols_cycle[ni % len(cols_cycle)]
                is_f = (ng <= progress < ng + step_span)
                if isinstance(rn, dict):
                    nl = str(rn.get("label") or rn.get("title") or "")
                    ns = str(rn.get("sub") or rn.get("desc") or "")
                else:
                    nl, ns = str(rn), ""
                stage.draw_glass_card((cx + 78, ny, cx + cw, ny + nh), nc, radius=20, alpha_mul=na, active=is_f)
                # Mini 2.5D isometric prism badge on left of each flow step
                _draw_iso_prism(stage, cx + 38, ny + nh // 2 - 12, rx=30, ry=13, depth=22, color=nc, alpha_mul=na, shape="cylinder" if "db" in nl.lower() or "vector" in nl.lower() else "box", active=is_f)
                if ns:
                    _draw_wrapped_text(stage.draw, nl, _get_font(27, bold=True), cx + 102, ny + 14, cw - 126, _with_alpha(w["text"], na), max_lines=1)
                    _draw_wrapped_text(stage.draw, ns, _get_font(20), cx + 102, ny + 48, cw - 126, _with_alpha(w["muted"], na), max_lines=1)
                else:
                    _draw_wrapped_text(stage.draw, nl, _get_font(27, bold=True), cx + 102, ny + max(16, (nh - 32) // 2), cw - 126, _with_alpha(w["text"], na), max_lines=2)

            for ci in range(cnt - 1):
                ny_src = y_cur + ci * (nh + ag) + nh // 2 + 24
                ny_dst = y_cur + (ci + 1) * (nh + ag) + nh // 2 - 26
                a_start = gate + (ci + 0.25) * step_span * 0.55
                a_t = _clamp01((progress - a_start) / 0.14)
                if a_t > 0.02:
                    _draw_bezier_comet(stage, (cx + 38, ny_src), (cx + 38, ny_dst), cols_cycle[ci % len(cols_cycle)], progress, a_t, label="", curve_offset_x=-18)
                    if ci < len(eds) and str(eds[ci]).strip() and a_t >= 0.95:
                        elbl = str(eds[ci]).strip()
                        my_e = (y_cur + ci * (nh + ag) + nh + y_cur + (ci + 1) * (nh + ag)) // 2
                        f_e = _get_font(16, bold=True)
                        ebb = f_e.getbbox(elbl)
                        ew = (ebb[2] - ebb[0]) + 22
                        stage.draw.rounded_rectangle((cx + 90, my_e - 14, cx + 90 + ew, my_e + 14), radius=9, fill=w["card_alt"], outline=(*cols_cycle[ci % len(cols_cycle)], 190), width=1)
                        stage.draw.text((cx + 101, my_e - 10), elbl, fill=w["amber"], font=f_e)

        elif bt == "code":
            code_txt = str(b.get("code") or "")
            box = (cx, yc, cx + cw, yc + bh)
            stage.add_shadow_box(box, radius=22, alpha_mul=alpha)
            stage.draw.rounded_rectangle(box, radius=22, fill=(13, 18, 30, int(246 * alpha)), outline=_with_alpha(w["cyan"], alpha), width=2)
            fc = _get_font(23)
            clines = code_txt.splitlines()[:5]
            tot_c = max(1, len(code_txt))
            show_c = int(tot_c * min(1.0, (progress - gate) * 2.5 + 0.35))
            seen = 0
            cyl = yc + 24
            for ln in clines:
                rem = max(0, show_c - seen)
                stage.draw.text((cx + 26, cyl), ln[:rem], fill=_with_alpha((52, 211, 153) if any(k in ln for k in ("def ", "SELECT", "return")) else (248, 250, 252), alpha), font=fc)
                seen += len(ln) + 1
                cyl += 38

        elif bt == "banner":
            b_txt = str(b.get("text") or "")
            btone = str(b.get("tone") or "highlight").lower().strip()
            bcol = w["amber"] if btone == "warn" else (w["cyan"] if btone == "cta" else w["emerald"])
            bfill = (42, 28, 14, 232) if (not w["is_light"] and btone == "warn") else ((12, 36, 56, 232) if (not w["is_light"] and btone == "cta") else ((12, 36, 30, 232) if not w["is_light"] else w["card_alt"]))
            rad = min(44, bh // 2) if btone == "cta" else 22
            stage.draw_glass_card((cx + 12, yc, cx + cw - 12, yc + bh), bcol, radius=rad, alpha_mul=alpha, active=True, fill_override=bfill)
            _draw_wrapped_text(stage.draw, b_txt, font_ban, cx + 36, yc + max(16, (bh - 34) // 2), cw - 72, _with_alpha(w["amber"] if btone == "warn" else w["text"], alpha), align="center", max_lines=2)

        else:  # list_cards
            its = (b.get("items") or [])[:4]
            var = str(b.get("variant") or "check").lower().strip()
            cnt = max(1, len(its))
            igap = 16
            rh = max(72, (bh - max(0, cnt - 1) * igap) // cnt)
            for li, rit in enumerate(its):
                la, ldy, _ = _spring_gate(progress, gate + li * 0.12, 0.12)
                if la <= 0.02:
                    continue
                ry = y_cur + li * (rh + igap) + ldy
                if isinstance(rit, dict):
                    hd = str(rit.get("title") or rit.get("label") or "")
                    sb = str(rit.get("desc") or rit.get("sub") or "")
                    ikind = str(rit.get("kind") or var).lower()
                else:
                    si = str(rit)
                    pts = si.split(":", 1) if ":" in si else (si.split("—", 1) if "—" in si else [si, ""])
                    hd, sb, ikind = pts[0].strip(), (pts[1].strip() if len(pts) > 1 else ""), var
                is_f = (gate + li * 0.12 <= progress < gate + (li + 1) * 0.14)
                ccol = w["amber"] if ikind == "warn" else w["cyan"]
                stage.draw_glass_card((cx, ry, cx + cw, ry + rh), ccol, radius=22, alpha_mul=la, active=is_f)
                if ikind == "warn":
                    _draw_vector_warn(stage, cx + 48, ry + rh // 2, 20, w["amber"], la)
                else:
                    _draw_vector_check(stage, cx + 48, ry + rh // 2, 20, w["emerald"], la)
                if sb:
                    _draw_wrapped_text(stage.draw, hd, _get_font(27, bold=True), cx + 92, ry + 16, cw - 115, _with_alpha(w["text"], la), max_lines=1)
                    _draw_wrapped_text(stage.draw, sb, _get_font(21), cx + 92, ry + 52, cw - 115, _with_alpha(w["muted"], la), max_lines=2)
                else:
                    _draw_wrapped_text(stage.draw, hd, _get_font(27, bold=True), cx + 92, ry + max(18, (rh - 34) // 2), cw - 115, _with_alpha(w["text"], la), max_lines=2)

        y_cur += bh + gap


def _render_cinematic_kinetic(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """Typographic centerpiece with glowing horizon laser, radial spotlight, and spring-loaded bottom badges."""
    w = stage.world
    kicker = str(data.get("kicker") or "").strip().upper()
    stmt = str(data.get("statement") or data.get("title") or "").strip()
    hl = str(data.get("highlight_word") or "").strip().lower()
    tags = data.get("bottom_tags") or []

    # Glowing laser divider rule
    line_t = _ease_out_cubic(min(1.0, progress / 0.22))
    lw = int(680 * line_t)
    mx = VIDEO_WIDTH // 2
    stage.add_glow_line([(mx - lw // 2, 462), (mx + lw // 2, 462)], w["amber"], alpha=160, width_q=3)
    stage.draw.line((mx - lw // 2, 462, mx + lw // 2, 462), fill=w["amber"], width=4)
    if kicker:
        _draw_wrapped_text(stage.draw, kicker, _get_font(25, bold=True), 120, 410, VIDEO_WIDTH - 240, w["amber"], align="center", max_lines=1)

    words = stmt.split()
    tot = len(words)
    vis = tot if progress >= 0.62 else max(2, int(math.ceil(tot * min(1.0, 0.25 + progress * 1.25))))
    shown = words[:vis]
    fsize = 56 if tot <= 9 else (48 if tot <= 15 else 42)
    fb = _get_font(fsize, bold=True)

    lines: List[List[str]] = []
    cur: List[str] = []
    for wd in shown:
        if (fb.getbbox(" ".join(cur + [wd]))[2] - fb.getbbox(" ".join(cur + [wd]))[0]) <= 880:
            cur.append(wd)
        else:
            if cur:
                lines.append(cur)
            cur = [wd]
    if cur:
        lines.append(cur)

    yc = 530
    for lw_list in lines[:6]:
        lstr = " ".join(lw_list)
        lpx = fb.getbbox(lstr)[2] - fb.getbbox(lstr)[0]
        cx_w = (VIDEO_WIDTH - lpx) // 2
        for wd in lw_list:
            is_hl = bool(hl and hl in wd.lower())
            if is_hl:
                wb = fb.getbbox(wd)
                stage.add_glow_orb(cx_w + (wb[2] - wb[0]) // 2, yc + fsize // 2, 55, w["cyan"], alpha=150)
                stage.draw.line((cx_w, yc + fsize + 10, cx_w + (wb[2] - wb[0]), yc + fsize + 10), fill=w["amber"], width=5)
            wd_s = wd + " "
            stage.draw.text((cx_w, yc), wd_s, fill=w["cyan"] if is_hl else w["text"], font=fb)
            cx_w += fb.getbbox(wd_s)[2] - fb.getbbox(wd_s)[0]
        yc += fsize + 24

    if tags and progress >= 0.40:
        tag_y = max(yc + 55, 1020)
        vis_t = tags[:3]
        tw, sp = 280, 22
        tx0 = (VIDEO_WIDTH - (len(vis_t) * tw + (len(vis_t) - 1) * sp)) // 2
        for ti, tg in enumerate(vis_t):
            ta, tdy, _ = _spring_gate(progress, 0.40 + ti * 0.08, 0.12)
            if ta <= 0.02:
                continue
            bx = tx0 + ti * (tw + sp)
            stage.draw_glass_card((bx, tag_y + tdy, bx + tw, tag_y + tdy + 76), w["emerald"], radius=38, alpha_mul=ta, active=True)
            _draw_wrapped_text(stage.draw, str(tg).upper(), _get_font(21, bold=True), bx + 12, tag_y + tdy + 24, tw - 24, _with_alpha(w["text"], ta), align="center", max_lines=1)


# =========================================================================
# MAIN SCENE DISPATCH & FRAME GENERATION LOOP
# =========================================================================
def _dispatch_cinematic(stage: StudioStage, visual_type: str, visual_data: Dict[str, Any], progress: float) -> None:
    vt = str(visual_type or "custom_scene").lower().strip()
    if vt in ("iso_architecture", "iso_stack", "architecture_flow", "hybrid_merge", "circular_hub_mesh", "all_in_one_tech_canvas"):
        # Map hybrid_merge pillars smoothly into a 3-node isometric flow chain if nodes missing
        if vt == "hybrid_merge" and not visual_data.get("nodes"):
            lp = visual_data.get("left_pillar") or {}
            rp = visual_data.get("right_pillar") or {}
            merged = visual_data.get("merged_label") or "Unified Engine"
            visual_data = {
                **visual_data,
                "nodes": [
                    {"label": lp.get("label", "Input Layer"), "sub": lp.get("sub", ""), "shape": "stack", "color": "purple"},
                    {"label": rp.get("label", "Live Source"), "sub": rp.get("sub", ""), "shape": "cylinder", "color": "cyan"},
                    {"label": merged, "sub": " | ".join(str(x) for x in (visual_data.get("outcomes") or [])[:3]), "shape": "box", "color": "emerald"},
                ],
                "edges": ["Combine", "Deliver"],
            }
        _render_iso_architecture(stage, visual_data, progress)
    elif vt in ("iso_comparison", "dual_3d_pedestal", "split_comparison", "trade_off"):
        _render_dual_pedestal_3d(stage, visual_data, progress)
    elif vt in ("terminal_studio", "code_terminal", "terminal", "cli", "code"):
        _render_terminal_studio(stage, visual_data, progress)
    elif vt in ("kinetic_statement", "kinetic", "statement", "callout"):
        _render_cinematic_kinetic(stage, visual_data, progress)
    elif vt == "step_timeline":
        steps = visual_data.get("steps") or []
        nds = [{"label": s.get("title", f"Step {i+1}"), "sub": s.get("desc", ""), "shape": "box"} for i, s in enumerate(steps[:4])]
        _render_iso_architecture(stage, {"nodes": nds, "edges": []}, progress)
    else:
        _render_cinematic_custom_scene(stage, visual_data, progress)


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
    Renders studio-grade 2.5D isometric frames with spring physics, soft ambient shadows,
    quarter-res optical Gaussian bloom, cubic Bezier comet conduits, audio-reactive spectrum
    ribbon, and subtle smooth camera zoom drift.
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
    art_style = str(visual_data.get("art_style") or scene.get("art_style") or "editorial_dark").lower().strip()
    world = _resolve_world(art_style, effective_tone)

    # Pre-bake static volumetric studio background once per scene (~8ms)
    base_bg = _build_volumetric_studio_bg(canvas_w, canvas_h, world)
    needs_aspect_fit = (canvas_w != VIDEO_WIDTH or canvas_h != VIDEO_HEIGHT)
    anchors = _build_anchors(duration, scene, scene_words)
    sc_start = float(scene.get("start_time", 0.0))

    badge = str(visual_data.get("badge") or "")
    title = str(visual_data.get("title") or "")
    accent = (
        world["emerald"] if effective_tone == "mentor_storyteller"
        else (world["amber"] if effective_tone == "interview_prep"
              else (world["rose"] if effective_tone == "dramatic_performance" else world["cyan"]))
    )

    # Deterministic ambient depth particles (22 bokeh orbs drifting gently upward)
    particles = [
        ((i * 197 + scene_idx * 53) % canvas_w, (i * 313 + 71) % canvas_h, 2 + (i % 4), 16 + (i % 3) * 10)
        for i in range(22)
    ]

    frame_paths: List[Path] = []
    for f in range(total_frames):
        linear_p = f / max(1, total_frames - 1)
        raw_p = _voice_progress(f, total_frames, duration, scene, scene_words, anchors=anchors)
        progress = min(1.0, raw_p * 1.10) if effective_tone == "fireship_octane" else raw_p
        cur_time = sc_start + (linear_p * duration)

        frame_bg = base_bg.copy()
        p_draw = ImageDraw.Draw(frame_bg, "RGBA")
        # Floating bokeh orbs
        for px0, py0, pr, pa in particles:
            py_live = int((py0 - linear_p * 140) % canvas_h)
            px_live = int((px0 + math.sin(linear_p * 3.14 + py0) * 14) % canvas_w)
            p_draw.ellipse((px_live - pr, py_live - pr, px_live + pr, py_live + pr), fill=(*accent, pa))

        if needs_aspect_fit:
            stage = StudioStage(VIDEO_WIDTH, 1500, world)
            _draw_studio_header(stage, badge, title, accent)
            _dispatch_cinematic(stage, visual_type, visual_data, progress)

            # Composite transparent shadows + optical bloom + sharp UI onto full-bleed volumetric studio backdrop
            virtual_rgba = stage.composite_onto(None)
            avail_h = canvas_h - 140
            avail_w = canvas_w - 80
            zoom = 1.0 + 0.022 * _ease_out_cubic(linear_p)
            scale = min(avail_w / VIDEO_WIDTH, avail_h / 1420.0) * zoom
            nw = max(100, int(VIDEO_WIDTH * scale))
            nh = max(100, int(1500 * scale))
            rs = virtual_rgba.resize((nw, nh), Image.Resampling.BILINEAR)
            frame_rgba = frame_bg.convert("RGBA")
            frame_rgba.alpha_composite(rs, ((canvas_w - nw) // 2, 42))
            final_img = frame_rgba
        else:
            stage = StudioStage(VIDEO_WIDTH, VIDEO_HEIGHT, world)
            _draw_studio_header(stage, badge, title, accent)
            _dispatch_cinematic(stage, visual_type, visual_data, progress)
            final_img = stage.composite_onto(frame_bg)

        # Native Crisp HUD Chrome: Progress Bar, Audio-Reactive Waveform, Watermark
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
            wtw = wbb[2] - wbb[0]
            bw = wtw + 46
            bx = canvas_w - bw - 36
            by = 44
            wfill = (255, 255, 255, 234) if world["is_light"] else (15, 23, 42, 218)
            chrome.rounded_rectangle((bx, by, bx + bw, by + 38), radius=19, fill=wfill, outline=(*accent, 185), width=2)
            chrome.ellipse((bx + 14, by + 15, bx + 22, by + 23), fill=accent)
            chrome.text((bx + 30, by + 6), wt, fill=world["text"], font=wm_font)

        frame_file = scene_frames_dir / f"frame_{f:04d}.jpg"
        final_img.convert("RGB").save(frame_file, "JPEG", quality=90)
        frame_paths.append(frame_file)

    return frame_paths
