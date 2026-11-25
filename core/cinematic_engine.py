import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH


# =========================================================================
# STUDIO WORLDS & COLOR PALETTES (DARK MODE UI + STUDIO LIGHT)
# =========================================================================
STUDIO_WORLDS: Dict[str, Dict[str, Any]] = {
    "obsidian_studio": {
        "is_light": False,
        "bg_top": (7, 10, 18),
        "bg_bot": (13, 18, 32),
        "spot_a": (56, 189, 248),
        "spot_b": (168, 85, 247),
        "grid_col": (100, 140, 190),
        "card_bg": (17, 24, 40, 224),
        "card_layer": (10, 15, 28, 210),
        "card_alt": (26, 35, 58, 232),
        "glass_rim": (255, 255, 255, 72),
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
        "bg_top": (5, 13, 28),
        "bg_bot": (10, 22, 46),
        "spot_a": (34, 211, 238),
        "spot_b": (99, 102, 241),
        "grid_col": (56, 189, 248),
        "card_bg": (12, 26, 50, 226),
        "card_layer": (8, 17, 36, 215),
        "card_alt": (18, 37, 68, 235),
        "glass_rim": (186, 230, 253, 76),
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
        "bg_top": (245, 248, 253),
        "bg_bot": (232, 239, 249),
        "spot_a": (14, 165, 233),
        "spot_b": (139, 92, 246),
        "grid_col": (148, 163, 184),
        "card_bg": (255, 255, 255, 242),
        "card_layer": (226, 234, 246, 235),
        "card_alt": (241, 245, 249, 246),
        "glass_rim": (255, 255, 255, 235),
        "border": (148, 163, 184, 175),
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
        "bg_top": (15, 9, 18),
        "bg_bot": (26, 12, 24),
        "spot_a": (244, 63, 94),
        "spot_b": (251, 191, 36),
        "grid_col": (244, 63, 94),
        "card_bg": (28, 16, 26, 228),
        "card_layer": (18, 10, 18, 215),
        "card_alt": (40, 20, 34, 236),
        "glass_rim": (254, 205, 211, 70),
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
# MOTION PHYSICS SUITE (SPRING, ELASTIC POP, SNAPPY SLIDE, MICRO-BOUNCE, FLIP, COUNTER)
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


def _ease_out_elastic(t: float) -> float:
    x = _clamp01(t)
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return math.pow(2.0, -9.0 * x) * math.sin((x * 10.0 - 0.75) * (2.0 * math.pi / 3.0)) + 1.0


def _micro_bounce(progress: float, phase: float = 0.0, amp: float = 5.0) -> int:
    """Gentle continuous vertical levitation / micro-bounce for active 3D nodes."""
    return int(round(math.sin(progress * math.pi * 4.0 + phase) * amp))


def _pulse_wave(progress: float, speed: float = 4.0) -> float:
    """Oscillating glow intensity wave in [0.55 .. 1.0]."""
    return 0.55 + 0.45 * (0.5 + 0.5 * math.sin(progress * math.pi * speed))


def _card_flip_scale_x(progress: float, gate: float, span: float = 0.14) -> float:
    """Returns horizontal scale factor simulating a crisp 3D Y-axis Card Flip entry."""
    if progress < gate:
        return 0.08
    raw = _clamp01((progress - gate) / max(1e-4, span))
    # Smooth half-flip opening 0.12 -> 1.0
    return 0.12 + 0.88 * math.sin(raw * math.pi * 0.5)


def _spring_gate(progress: float, gate: float, span: float = 0.14, snappy: bool = False) -> Tuple[float, int, float]:
    """
    Returns (visibility_alpha_0_1, y_slide_offset_px, spring_scale) for buttery
    Spring Physics, Snappy Slide, and Elastic Pop choreography.
    """
    if progress < gate:
        return 0.0, 48, 0.88
    raw = _clamp01((progress - gate) / max(1e-4, span))
    curve = _ease_out_cubic(raw) if snappy else _ease_out_back(raw, s=1.35)
    alpha = _clamp01(raw * 1.5)
    dy = int((1.0 - curve) * (58 if snappy else 40))
    scale = 0.90 + 0.10 * curve
    return alpha, dy, scale


def _animate_counter_text(val_str: str, t: float) -> str:
    """Live rolling numeric counter (`0% -> 90%`, `0x -> 100x`, `0.0ms -> 14.2ms`)."""
    s = str(val_str or "").strip()
    if t >= 0.98 or not s:
        return s
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return s
    num_str = m.group(1)
    try:
        target = float(num_str)
    except ValueError:
        return s
    val = target * _ease_out_cubic(t)
    formatted = f"{val:.1f}" if "." in num_str else f"{int(round(val))}"
    return s[:m.start(1)] + formatted + s[m.end(1):]


def _fade_transition_alpha(linear_p: float) -> float:
    """Smooth enter/exit envelope for Clean Transitions between scenes."""
    if linear_p < 0.05:
        return 0.40 + 0.60 * _ease_out_cubic(linear_p / 0.05)
    if linear_p > 0.95:
        return 0.45 + 0.55 * ((1.0 - linear_p) / 0.05)
    return 1.0


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
# LAYER 1: SUBTLE GRID BACKDROP + VOLUMETRIC LIGHTING (NO HEAVY FLOOR MESH)
# =========================================================================
def _build_volumetric_studio_bg(w: int, h: int, world: Dict[str, Any]) -> Image.Image:
    """
    NumPy-vectorized dark/light volumetric studio backdrop with radial spotlights
    and ultra-subtle editorial coordinate backdrop (NO distracting bottom Tron mesh!).
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

    # Whisper-subtle editorial grid lines faded organically by radial vignette (zero heavy jali!)
    grid_rgb = np.array(world["grid_col"], dtype=np.float32)[None, None, :]
    step = 84
    gx_mask = (np.arange(w)[None, :] % step == 0)
    gy_mask = (np.arange(h)[:, None] % step == 0)
    grid_mask = (gx_mask | gy_mask).astype(np.float32)
    vignette = np.exp(-(((x - 0.5) * 1.55) ** 2 + ((y - 0.48) * 1.35) ** 2))
    grid_alpha = (grid_mask * vignette * (0.045 if not world["is_light"] else 0.08))[..., None]
    arr = arr * (1.0 - grid_alpha) + grid_rgb * grid_alpha

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    return img


# =========================================================================
# STUDIO RENDER CONTEXT (LAYERED CARDS, NEON RIM LIGHT, SHADOWS & BLOOM)
# =========================================================================
class StudioStage:
    def __init__(self, width: int, height: int, world: Dict[str, Any], transition_alpha: float = 1.0):
        self.w = width
        self.h = height
        self.world = world
        self.t_alpha = transition_alpha
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
        sc = _with_alpha(self.world["shadow_col"], alpha_mul * self.t_alpha)
        self.sdraw.rounded_rectangle(
            (x1 // 4, (y1 + offset_y) // 4, x2 // 4, (y2 + offset_y) // 4),
            radius=max(2, radius // 4),
            fill=sc,
        )

    def add_shadow_ellipse(self, box: Tuple[int, int, int, int], alpha_mul: float = 1.0) -> None:
        if alpha_mul <= 0.05:
            return
        x1, y1, x2, y2 = box
        sc = _with_alpha(self.world["shadow_col"], alpha_mul * self.t_alpha)
        self.sdraw.ellipse((x1 // 4, y1 // 4, x2 // 4, y2 // 4), fill=sc)

    def add_glow_box(self, box: Tuple[int, int, int, int], color: Tuple[int, int, int], radius: int = 24, alpha: int = 90) -> None:
        a = int(alpha * self.t_alpha)
        if a <= 4:
            return
        x1, y1, x2, y2 = box
        self.gdraw.rounded_rectangle(
            (x1 // 4, y1 // 4, x2 // 4, y2 // 4),
            radius=max(2, radius // 4),
            outline=(*color[:3], a),
            width=3,
        )

    def add_glow_orb(self, cx: float, cy: float, r: float, color: Tuple[int, int, int], alpha: int = 160) -> None:
        a = int(alpha * self.t_alpha)
        if a <= 4:
            return
        qx, qy, qr = cx / 4.0, cy / 4.0, max(2.0, r / 4.0)
        self.gdraw.ellipse((qx - qr, qy - qr, qx + qr, qy + qr), fill=(*color[:3], a))

    def add_glow_line(self, pts: List[Tuple[float, float]], color: Tuple[int, int, int], alpha: int = 130, width_q: int = 3) -> None:
        a = int(alpha * self.t_alpha)
        if len(pts) < 2 or a <= 4:
            return
        qpts = [(x / 4.0, y / 4.0) for x, y in pts]
        self.gdraw.line(qpts, fill=(*color[:3], a), width=width_q)

    def draw_glass_card(
        self,
        box: Tuple[int, int, int, int],
        accent: Tuple[int, int, int],
        radius: int = 24,
        alpha_mul: float = 1.0,
        active: bool = False,
        fill_override: Tuple[int, ...] = None,
        layered: bool = False,
        flip_x: float = 1.0,
    ) -> Tuple[int, int, int, int]:
        """Draws frosted glass card with optional Layered Depth backplate, Neon Rim Light, and 3D Card Flip."""
        eff_a = alpha_mul * self.t_alpha
        if eff_a <= 0.02:
            return box
        x1, y1, x2, y2 = box
        if flip_x < 0.99:
            mid_x = (x1 + x2) // 2
            half_w = max(8, int(((x2 - x1) * 0.5) * max(0.08, flip_x)))
            x1, x2 = mid_x - half_w, mid_x + half_w
            box = (x1, y1, x2, y2)

        w = self.world
        self.add_shadow_box(box, radius=radius, offset_y=16 if active else 12, alpha_mul=alpha_mul)
        if layered and (x2 - x1) > 60:
            back_box = (x1 + 10, y1 + 10, x2 + 10, y2 + 10)
            self.draw.rounded_rectangle(back_box, radius=radius, fill=_with_alpha(w["card_layer"], eff_a * 0.92), outline=_with_alpha(accent, eff_a * 0.28), width=1)

        if active:
            self.add_glow_box(box, accent, radius=radius, alpha=int(135 * alpha_mul))
        fill_c = _with_alpha(fill_override or w["card_bg"], eff_a)
        border_c = _with_alpha(accent if active else w["border"], eff_a * (1.0 if active else 0.72))
        self.draw.rounded_rectangle(box, radius=radius, fill=fill_c, outline=border_c, width=3 if active else 2)

        # Neon Rim Light specular highlight along top + left bevel
        if (x2 - x1) > 50 and flip_x > 0.45:
            rim_c = _with_alpha(accent if active else w["glass_rim"], eff_a * (0.9 if active else 0.65))
            self.draw.line((x1 + radius, y1 + 2, x2 - radius, y1 + 2), fill=rim_c, width=2)
            self.draw.line((x1 + 2, y1 + radius, x1 + 2, min(y2 - radius, y1 + radius + 55)), fill=rim_c, width=2)
        return box

    def composite_onto(self, bg_rgb: Optional[Image.Image] = None) -> Image.Image:
        out = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0)) if bg_rgb is None else bg_rgb.convert("RGBA")
        sh = self.shadow_q.filter(ImageFilter.GaussianBlur(radius=6))
        gl = self.glow_q.filter(ImageFilter.GaussianBlur(radius=7))
        sh.alpha_composite(gl)
        atmos = sh.resize((self.w, self.h), Image.Resampling.BILINEAR)
        out.alpha_composite(atmos)
        out.alpha_composite(self.fg)
        return out


# =========================================================================
# ALL 3D ISOMETRIC & VECTOR SHAPES + CRISP INLINE ICONS
# =========================================================================
def _infer_shape(label: str, fallback: str = "box") -> str:
    low = str(label or "").lower()
    if any(k in low for k in ("db", "database", "vector", "sql", "pg", "redis", "store", "cache", "index", "table")):
        return "cylinder"
    if any(k in low for k in ("cloud", "aws", "gcp", "azure", "vpc", "cdn", "edge", "internet", "saas")):
        return "cloud"
    if any(k in low for k in ("auth", "sec", "soc", "guard", "shield", "firewall", "siem", "jwt", "vault", "trust")):
        return "shield"
    if any(k in low for k in ("ai", "llm", "gpt", "agent", "bot", "reasoning", "neural")):
        return "bot"
    if any(k in low for k in ("cpu", "gpu", "chip", "kernel", "embed", "tokenizer", "inference", "wasm")):
        return "chip"
    if any(k in low for k in ("s3", "bucket", "lake", "parquet", "blob")):
        return "bucket"
    if any(k in low for k in ("k8s", "kube", "mesh", "docker", "cluster", "microservice", "pod")):
        return "hexagon"
    if any(k in low for k in ("model", "stack", "layer", "server", "rack", "pipeline", "rag", "fine-tuning")):
        return "stack"
    if any(k in low for k in ("hub", "core", "global", "world", "mesh", "graph", "network")):
        return "sphere"
    if any(k in low for k in ("route", "router", "decision", "branch", "gateway", "proxy", "switch")):
        return "diamond"
    if any(k in low for k in ("pyramid", "tier", "hierarchy", "rank", "funnel", "level")):
        return "pyramid"
    if any(k in low for k in ("cron", "worker", "job", "queue", "config", "engine", "automation")):
        return "gear"
    return fallback


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
    progress: float = 0.0,
    phase: float = 0.0,
) -> None:
    """
    Draws ALL 12 crisp 2.5D Isometric & Tech Vector Shapes with soft shadow,
    micro-bounce hover, 3-plane lighting, and Neon Rim glow:
    box | stack | cylinder | sphere | hexagon | pyramid | diamond | cloud | shield | chip | bucket | gear | bot
    """
    eff_a = alpha_mul * stage.t_alpha
    if eff_a <= 0.03:
        return

    # Active nodes gently levitate with Micro-Bounce physics
    bob = _micro_bounce(progress, phase=phase, amp=4.5) if active else 0
    cy_live = cy + bob
    shp = str(shape or "box").lower().strip()

    stage.add_shadow_ellipse((cx - rx - 8, cy + depth + 6, cx + rx + 8, cy + depth + ry + 18), alpha_mul * 0.85)
    if active:
        stage.add_glow_orb(cx, cy_live + depth * 0.25, rx * 1.08, color, alpha=int(155 * _pulse_wave(progress)))

    r, g, b = color[:3]
    top_col = _with_alpha((min(255, r + 58), min(255, g + 58), min(255, b + 58), 246), eff_a)
    left_col = _with_alpha((max(18, int(r * 0.56)), max(22, int(g * 0.58)), max(30, int(b * 0.62)), 250), eff_a)
    right_col = _with_alpha((max(10, int(r * 0.34)), max(14, int(g * 0.36)), max(20, int(b * 0.42)), 252), eff_a)
    wire_col = _with_alpha((min(255, r + 95), min(255, g + 95), min(255, b + 95), 245 if active else 175), eff_a)
    dark_core = _with_alpha((14, 21, 38, 250), eff_a)

    if shp == "cylinder":
        stage.draw.rectangle((cx - rx, cy_live, cx + rx, cy_live + depth), fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - rx, cy_live + depth - ry, cx + rx, cy_live + depth + ry), fill=right_col, outline=wire_col, width=2)
        mid_y = cy_live + depth // 2
        stage.draw.arc((cx - rx, mid_y - ry, cx + rx, mid_y + ry), start=0, end=180, fill=wire_col, width=2)
        stage.draw.ellipse((cx - rx, cy_live - ry, cx + rx, cy_live + ry), fill=top_col, outline=wire_col, width=3 if active else 2)

    elif shp == "stack":
        tier_d = max(11, depth // 3 - 4)
        for ti in range(3):
            ty = cy_live + (2 - ti) * (tier_d + 6)
            t_pts = [(cx, ty - ry), (cx + rx, ty), (cx, ty + ry), (cx - rx, ty)]
            l_pts = [(cx - rx, ty), (cx, ty + ry), (cx, ty + ry + tier_d), (cx - rx, ty + tier_d)]
            r_pts = [(cx + rx, ty), (cx, ty + ry), (cx, ty + ry + tier_d), (cx + rx, ty + tier_d)]
            stage.draw.polygon(l_pts, fill=left_col, outline=wire_col, width=1)
            stage.draw.polygon(r_pts, fill=right_col, outline=wire_col, width=1)
            stage.draw.polygon(t_pts, fill=top_col if ti == 2 else left_col, outline=wire_col, width=2)

    elif shp == "sphere":
        rad = min(rx, ry + depth // 2)
        mid_cy = cy_live + depth // 3
        stage.draw.ellipse((cx - rad, mid_cy - rad, cx + rad, mid_cy + rad), fill=right_col, outline=wire_col, width=3 if active else 2)
        stage.draw.ellipse((cx - int(rad * 0.85), mid_cy - int(rad * 0.88), cx + int(rad * 0.65), mid_cy + int(rad * 0.62)), fill=left_col)
        stage.draw.ellipse((cx - int(rad * 0.55), mid_cy - int(rad * 0.68), cx - int(rad * 0.05), mid_cy - int(rad * 0.18)), fill=top_col)
        # Orbital Saturn ring
        stage.draw.arc((cx - int(rad * 1.35), mid_cy - int(rad * 0.42), cx + int(rad * 1.35), mid_cy + int(rad * 0.42)), start=-18, end=198, fill=wire_col, width=3)

    elif shp == "hexagon":
        hr = int(rx * 0.92)
        hr_y = int(ry * 1.15)
        hex_top = [(cx + int(hr * math.cos(math.radians(a))), cy_live + int(hr_y * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
        ext = int(depth * 0.72)
        # Extruded front-facing walls (indices 0->1, 1->2, 2->3)
        for idx in (0, 1, 2):
            p1, p2 = hex_top[idx], hex_top[(idx + 1) % 6]
            wall = [p1, p2, (p2[0], p2[1] + ext), (p1[0], p1[1] + ext)]
            stage.draw.polygon(wall, fill=left_col if idx < 2 else right_col, outline=wire_col, width=2)
        stage.draw.polygon(hex_top, fill=top_col, outline=wire_col, width=3 if active else 2)
        inner = [(cx + int(hr * 0.55 * math.cos(math.radians(a))), cy_live + int(hr_y * 0.55 * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
        stage.draw.polygon(inner, outline=_with_alpha(color, alpha_mul * 0.85), width=2)

    elif shp == "pyramid":
        apex = (cx, cy_live - int(depth * 0.55))
        p_left = (cx - rx, cy_live + int(depth * 0.42))
        p_front = (cx, cy_live + int(depth * 0.82))
        p_right = (cx + rx, cy_live + int(depth * 0.42))
        stage.draw.polygon([apex, p_left, p_front], fill=top_col, outline=wire_col, width=2)
        stage.draw.polygon([apex, p_front, p_right], fill=right_col, outline=wire_col, width=2)
        stage.draw.line((apex[0], apex[1], p_front[0], p_front[1]), fill=wire_col, width=3)

    elif shp == "diamond":
        mid_cy = cy_live + depth // 3
        top_v = (cx, mid_cy - ry - depth // 3)
        bot_v = (cx, mid_cy + ry + depth // 2)
        left_v = (cx - rx, mid_cy)
        right_v = (cx + rx, mid_cy)
        stage.draw.polygon([top_v, left_v, (cx, mid_cy + 10)], fill=top_col, outline=wire_col, width=2)
        stage.draw.polygon([top_v, right_v, (cx, mid_cy + 10)], fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon([left_v, (cx, mid_cy + 10), bot_v], fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon([right_v, (cx, mid_cy + 10), bot_v], fill=right_col, outline=wire_col, width=2)

    elif shp == "cloud":
        by = cy_live + depth // 2 + 6
        stage.draw.rounded_rectangle((cx - rx, by - 26, cx + rx, by + 18), radius=22, fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - int(rx * 0.78), by - 54, cx - int(rx * 0.08), by + 4), fill=top_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - int(rx * 0.34), by - 72, cx + int(rx * 0.48), by + 4), fill=top_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx + int(rx * 0.16), by - 46, cx + int(rx * 0.85), by + 10), fill=left_col, outline=wire_col, width=2)
        stage.draw.rounded_rectangle((cx - rx + 6, by - 12, cx + rx - 6, by + 14), radius=12, fill=left_col)

    elif shp == "shield":
        sw = int(rx * 0.85)
        ty_s = cy_live - ry // 2 - 4
        by_s = cy_live + depth + 16
        my_s = cy_live + depth // 2
        pts_l = [(cx, ty_s), (cx - sw, ty_s + 14), (cx - int(sw * 0.78), my_s + 12), (cx, by_s)]
        pts_r = [(cx, ty_s), (cx + sw, ty_s + 14), (cx + int(sw * 0.78), my_s + 12), (cx, by_s)]
        stage.draw.polygon(pts_l, fill=top_col, outline=wire_col, width=2)
        stage.draw.polygon(pts_r, fill=right_col, outline=wire_col, width=2)
        # Inner emblem line
        stage.draw.line((cx, ty_s + 12, cx, by_s - 12), fill=wire_col, width=3)

    elif shp == "chip":
        cw_c = int(rx * 0.78)
        mid_cy = cy_live + depth // 3
        for p_idx in range(-2, 3):
            py_p = mid_cy + p_idx * 11
            stage.draw.line((cx - cw_c - 12, py_p, cx - cw_c, py_p), fill=_with_alpha(stage.world["amber"], eff_a), width=3)
            stage.draw.line((cx + cw_c, py_p, cx + cw_c + 12, py_p), fill=_with_alpha(stage.world["amber"], eff_a), width=3)
            px_p = cx + p_idx * 12
            stage.draw.line((px_p, mid_cy - cw_c - 10, px_p, mid_cy - cw_c), fill=wire_col, width=3)
        stage.draw.rounded_rectangle((cx - cw_c, mid_cy - cw_c, cx + cw_c, mid_cy + cw_c), radius=14, fill=dark_core, outline=wire_col, width=3)
        ic = int(cw_c * 0.54)
        stage.draw.rounded_rectangle((cx - ic, mid_cy - ic, cx + ic, mid_cy + ic), radius=8, fill=top_col, outline=wire_col, width=2)

    elif shp == "bucket":
        bw_b = int(rx * 0.85)
        rim_h = max(18, ry)
        taper = 14
        stage.draw.arc((cx - bw_b // 2, cy_live - 20, cx + bw_b // 2, cy_live + 14), start=180, end=360, fill=wire_col, width=3)
        stage.draw.polygon([(cx - bw_b, cy_live + rim_h // 2), (cx + bw_b, cy_live + rim_h // 2), (cx + bw_b - taper, cy_live + depth + 10), (cx - bw_b + taper, cy_live + depth + 10)], fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - bw_b, cy_live, cx + bw_b, cy_live + rim_h), fill=top_col, outline=wire_col, width=3)
        stage.draw.line((cx - bw_b + taper + 6, cy_live + depth - 4, cx + bw_b - taper - 6, cy_live + depth - 4), fill=wire_col, width=3)

    elif shp == "gear":
        mid_cy = cy_live + depth // 3
        gr = int(min(rx, ry + depth // 2) * 0.88)
        for ti in range(8):
            ang = math.radians(ti * 45 + (progress * 35.0 if active else 0.0))
            tx = cx + int(math.cos(ang) * (gr + 6))
            ty = mid_cy + int(math.sin(ang) * (gr + 6))
            stage.draw.ellipse((tx - 7, ty - 7, tx + 7, ty + 7), fill=top_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - gr, mid_cy - gr, cx + gr, mid_cy + gr), fill=left_col, outline=wire_col, width=3)
        stage.draw.ellipse((cx - gr // 2, mid_cy - gr // 2, cx + gr // 2, mid_cy + gr // 2), fill=dark_core, outline=wire_col, width=2)

    elif shp == "bot":
        bw_t = int(rx * 0.78)
        mid_cy = cy_live + depth // 3
        stage.draw.line((cx, mid_cy - bw_t, cx, mid_cy - bw_t - 14), fill=wire_col, width=3)
        stage.draw.ellipse((cx - 5, mid_cy - bw_t - 20, cx + 5, mid_cy - bw_t - 10), fill=_with_alpha(stage.world["amber"], eff_a))
        stage.draw.rounded_rectangle((cx - bw_t, mid_cy - bw_t + 6, cx + bw_t, mid_cy + bw_t - 4), radius=18, fill=left_col, outline=wire_col, width=3)
        stage.draw.rounded_rectangle((cx - bw_t + 10, mid_cy - 14, cx + bw_t - 10, mid_cy + 12), radius=8, fill=dark_core, outline=wire_col, width=2)
        scan_x = cx - 12 + int(math.sin(progress * 6.0) * 14)
        stage.draw.rounded_rectangle((scan_x, mid_cy - 8, scan_x + 18, mid_cy + 6), radius=4, fill=top_col)

    else:  # "box" default extruded 3D Isometric Cube
        t_pts = [(cx, cy_live - ry), (cx + rx, cy_live), (cx, cy_live + ry), (cx - rx, cy_live)]
        l_pts = [(cx - rx, cy_live), (cx, cy_live + ry), (cx, cy_live + ry + depth), (cx - rx, cy_live + depth)]
        r_pts = [(cx + rx, cy_live), (cx, cy_live + ry), (cx, cy_live + ry + depth), (cx + rx, cy_live + depth)]
        stage.draw.polygon(l_pts, fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon(r_pts, fill=right_col, outline=wire_col, width=2)
        stage.draw.polygon(t_pts, fill=top_col, outline=wire_col, width=3 if active else 2)
        irx, iry = int(rx * 0.62), int(ry * 0.62)
        inner_top = [(cx, cy_live - iry), (cx + irx, cy_live), (cx, cy_live + iry), (cx - irx, cy_live)]
        stage.draw.polygon(inner_top, outline=_with_alpha(color, alpha_mul * 0.85), width=2)
        stage.draw.line((cx - rx + 10, cy_live + 12, cx - rx + 10, cy_live + depth - 4), fill=wire_col, width=3)


def _draw_vector_icon(
    stage: StudioStage,
    cx: int,
    cy: int,
    kind: str,
    radius: int,
    color: Tuple[int, int, int],
    alpha_mul: float,
) -> None:
    """Crisp Vector Icons inside list cards, metric badges, and headers (zero emoji tofu issues!)."""
    eff_a = alpha_mul * stage.t_alpha
    c = _with_alpha(color, eff_a)
    ink = _with_alpha(stage.world["text"], eff_a)
    stage.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_with_alpha((*color[:3], 42), eff_a), outline=c, width=3)
    k = str(kind or "check").lower().strip()
    if k in ("warn", "warning", "alert"):
        stage.draw.line((cx, cy - int(radius * 0.42), cx, cy + int(radius * 0.14)), fill=ink, width=4)
        stage.draw.ellipse((cx - 3, cy + int(radius * 0.28), cx + 3, cy + int(radius * 0.46)), fill=ink)
    elif k in ("bolt", "fast", "speed", "flash"):
        pts = [(cx + 2, cy - 11), (cx - 7, cy + 1), (cx + 1, cy + 1), (cx - 2, cy + 11), (cx + 8, cy - 1), (cx, cy - 1)]
        stage.draw.polygon(pts, fill=c)
    elif k in ("lock", "shield", "sec"):
        stage.draw.arc((cx - 6, cy - 11, cx + 6, cy), start=180, end=360, fill=ink, width=3)
        stage.draw.rounded_rectangle((cx - 8, cy - 3, cx + 8, cy + 9), radius=3, fill=c)
    elif k in ("db", "database", "storage"):
        stage.draw.ellipse((cx - 8, cy - 9, cx + 8, cy - 3), outline=ink, width=2)
        stage.draw.line((cx - 8, cy - 6, cx - 8, cy + 6), fill=ink, width=2)
        stage.draw.line((cx + 8, cy - 6, cx + 8, cy + 6), fill=ink, width=2)
        stage.draw.arc((cx - 8, cy + 3, cx + 8, cy + 9), start=0, end=180, fill=ink, width=2)
    elif k in ("code", "dev", "api"):
        stage.draw.line((cx - 4, cy - 6, cx - 10, cy, cx - 4, cy + 6), fill=ink, width=3)
        stage.draw.line((cx + 4, cy - 6, cx + 10, cy, cx + 4, cy + 6), fill=ink, width=3)
    elif k in ("search", "rag", "query"):
        stage.draw.ellipse((cx - 8, cy - 8, cx + 4, cy + 4), outline=ink, width=3)
        stage.draw.line((cx + 3, cy + 3, cx + 9, cy + 9), fill=ink, width=3)
    elif k in ("chart", "metric", "graph"):
        stage.draw.rectangle((cx - 8, cy + 1, cx - 4, cy + 8), fill=c)
        stage.draw.rectangle((cx - 2, cy - 5, cx + 2, cy + 8), fill=ink)
        stage.draw.rectangle((cx + 4, cy - 9, cx + 8, cy + 8), fill=c)
    else:  # "check"
        pts = [(cx - radius * 0.42, cy), (cx - radius * 0.1, cy + radius * 0.34), (cx + radius * 0.46, cy - radius * 0.34)]
        stage.draw.line(pts, fill=ink, width=4)


# =========================================================================
# CUBIC BEZIER GLOWING FLOW ARROWS & STEP PROGRESS BAR
# =========================================================================
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
    """Animated Flow Arrows + Data Flow Lines using Cubic Bezier conduits and optical bloom comets."""
    if reveal_t <= 0.02:
        return
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    c1 = (p0[0] + curve_offset_x + dx * 0.15, p0[1] + dy * 0.45)
    c2 = (p3[0] + curve_offset_x - dx * 0.15, p3[1] - dy * 0.45)

    all_pts = _bezier_points(p0, c1, c2, p3, steps=30)
    vis_n = max(2, int(len(all_pts) * min(1.0, reveal_t)))
    vis_pts = all_pts[:vis_n]

    stage.add_glow_line(vis_pts, color, alpha=145, width_q=3)
    stage.draw.line(vis_pts, fill=_with_alpha(color, 0.78 * stage.t_alpha), width=4)

    if reveal_t < 0.96:
        hx, hy = vis_pts[-1]
        stage.add_glow_orb(hx, hy, 16, color, alpha=210)
        stage.draw.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), fill=_with_alpha((255, 255, 255), stage.t_alpha))
        return

    ax_prev, ay_prev = vis_pts[-3]
    ax_end, ay_end = vis_pts[-1]
    ang = math.atan2(ay_end - ay_prev, ax_end - ax_prev)
    alen = 15.0
    aang = math.pi / 6.0
    p_a = (ax_end - alen * math.cos(ang - aang), ay_end - alen * math.sin(ang - aang))
    p_b = (ax_end - alen * math.cos(ang + aang), ay_end - alen * math.sin(ang + aang))
    stage.draw.polygon([(ax_end, ay_end), p_a, p_b], fill=_with_alpha(color, stage.t_alpha))

    head_t = (progress * 1.95) % 1.0
    n_tot = len(all_pts) - 1
    for tail_i in range(7):
        tt = head_t - tail_i * 0.024
        if tt < 0.0 or tt > 1.0:
            continue
        p_idx = int(tt * n_tot)
        px, py = all_pts[p_idx]
        fade = (1.0 - (tail_i / 7.0)) * stage.t_alpha
        rad = max(2, int(7 * (1.0 - tail_i / 7.0)))
        if tail_i == 0:
            stage.add_glow_orb(px, py, 16, color, alpha=int(220 * stage.t_alpha))
            stage.draw.ellipse((px - 6, py - 6, px + 6, py + 6), fill=_with_alpha((255, 255, 255), stage.t_alpha))
        else:
            stage.draw.ellipse((px - rad, py - rad, px + rad, py + rad), fill=_with_alpha(color, 0.85 * fade))

    if label:
        mx, my = all_pts[len(all_pts) // 2]
        f_lbl = _get_font(17, bold=True)
        bb = f_lbl.getbbox(label)
        tw = bb[2] - bb[0]
        bw = tw + 26
        box = (int(mx - bw // 2), int(my - 15), int(mx + bw // 2), int(my + 15))
        stage.draw.rounded_rectangle(box, radius=10, fill=_with_alpha(stage.world["card_alt"], stage.t_alpha), outline=_with_alpha(color, 0.85 * stage.t_alpha), width=2)
        stage.draw.text((int(mx - tw // 2), int(my - 10)), label, fill=_with_alpha(stage.world["amber"], stage.t_alpha), font=f_lbl)


def _draw_step_progress_bar(
    stage: StudioStage,
    progress: float,
    step_labels: List[str],
    accent: Tuple[int, int, int],
    y: int = 1352,
) -> None:
    """Renders an in-scene milestone Step Progress Bar cleanly above caption zone."""
    cnt = min(4, len(step_labels))
    if cnt < 2:
        return
    w = stage.world
    x1, x2 = 110, VIDEO_WIDTH - 110
    span = x2 - x1
    track_col = _with_alpha(w["border"], 0.45 * stage.t_alpha)
    stage.draw.rounded_rectangle((x1, y - 3, x2, y + 3), radius=3, fill=track_col)
    fill_x = x1 + int(span * _clamp01(progress * 1.05))
    stage.add_glow_line([(x1, y), (fill_x, y)], accent, alpha=140, width_q=3)
    stage.draw.rounded_rectangle((x1, y - 3, fill_x, y + 3), radius=3, fill=_with_alpha(accent, stage.t_alpha))

    f_st = _get_font(16, bold=True)
    for idx in range(cnt):
        frac = idx / float(cnt - 1)
        nx = x1 + int(span * frac)
        reached = progress >= (frac * 0.85)
        r = 12 if reached else 9
        fill_dot = _with_alpha(accent if reached else w["card_alt"], stage.t_alpha)
        stage.draw.ellipse((nx - r, y - r, nx + r, y + r), fill=fill_dot, outline=_with_alpha(accent, stage.t_alpha), width=2)
        lbl = str(step_labels[idx])[:14]
        bb = f_st.getbbox(lbl)
        lw = bb[2] - bb[0]
        lx = max(55, min(VIDEO_WIDTH - 55 - lw, nx - lw // 2))
        stage.draw.text((lx, y + 18), lbl, fill=_with_alpha(w["text"] if reached else w["muted"], stage.t_alpha), font=f_st)


def _draw_metric_badges_row(
    stage: StudioStage,
    badges: List[str],
    progress: float,
    gate: float,
    y: int,
) -> None:
    """Renders Metric Badges / Callout Badges strip with Elastic Pop entrance."""
    if not badges:
        return
    w = stage.world
    clean = [str(b).strip() for b in badges[:3] if str(b).strip()]
    if not clean:
        return
    cols = [w["emerald"], w["cyan"], w["amber"]]
    n = len(clean)
    gap = 18
    total_w = 940
    bw = (total_w - (n - 1) * gap) // n
    x0 = (VIDEO_WIDTH - total_w) // 2
    f_b = _get_font(20, bold=True)
    for idx, txt in enumerate(clean):
        bg_t = gate + idx * 0.06
        if progress < bg_t:
            continue
        raw = _clamp01((progress - bg_t) / 0.14)
        el = _ease_out_elastic(raw)
        dy = int((1.0 - min(1.1, el)) * 24)
        al = _clamp01(raw * 1.6)
        bx = x0 + idx * (bw + gap)
        bc = cols[idx % len(cols)]
        stage.draw_glass_card((bx, y + dy, bx + bw, y + 54 + dy), bc, radius=27, alpha_mul=al, active=True)
        _draw_wrapped_text(stage.draw, txt.upper(), f_b, bx + 12, y + 14 + dy, bw - 24, _with_alpha(bc, al), align="center", max_lines=1)


# =========================================================================
# VOICE-REACTIVE SPECTRUM VISUALIZER & HEADER CHROME
# =========================================================================
def _draw_voice_waveform(
    draw: ImageDraw.Draw,
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
        stage.draw.rounded_rectangle(pill_box, radius=14, fill=_with_alpha(w["card_alt"], stage.t_alpha), outline=_with_alpha(accent, 0.85 * stage.t_alpha), width=2)
        stage.draw.ellipse((lx + 14, y_cur + 15, lx + 24, y_cur + 25), fill=_with_alpha(accent, stage.t_alpha))
        stage.draw.text((lx + 34, y_cur + 7), badge_s, fill=_with_alpha(accent, stage.t_alpha), font=f_b)
        y_cur += 54

    if title:
        _draw_wrapped_text(stage.draw, str(title), _get_font(46, bold=True), lx, y_cur, 940, _with_alpha(w["text"], stage.t_alpha), line_spacing=8, max_lines=2)


# =========================================================================
# STUDIO VISUAL ARCHETYPES (ISO ARCHITECTURE, NODE GRAPH, SPLIT 3D, TERMINAL, CUSTOM)
# =========================================================================
def _render_iso_architecture(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    Signature 2.5D Isometric Architecture & Data-Flow Scene:
    Uses ALL 12 3D shapes, Micro-Bounce levitation, Layered Glass Cards,
    Cubic Bezier Plasma Comets, Metric Badges, and in-scene Step Progress Bar.
    """
    w = stage.world
    raw_nodes = data.get("nodes") or data.get("stages") or data.get("steps") or []
    edges = data.get("edges") or data.get("arrows") or []
    if not raw_nodes:
        raw_nodes = [
            {"label": str(data.get("title") or "Input Stream"), "sub": "Ingress", "shape": "cloud"},
            {"label": "Core Processing", "sub": "Transform & Route", "shape": "stack"},
            {"label": "Storage Tier", "sub": "Durable Index", "shape": "cylinder"},
        ]

    nodes: List[Dict[str, Any]] = []
    shapes_cycle = ["cloud", "stack", "cylinder", "shield"]
    cols_cycle = [w["cyan"], w["purple"], w["emerald"], w["amber"]]
    for idx, rn in enumerate(raw_nodes[:4]):
        if isinstance(rn, dict):
            lbl = str(rn.get("label") or rn.get("title") or rn.get("name") or f"Stage {idx+1}")
            sub = str(rn.get("sub") or rn.get("desc") or rn.get("description") or "")
            shp = str(rn.get("shape") or "").lower().strip() or _infer_shape(lbl + " " + sub, shapes_cycle[idx % len(shapes_cycle)])
            col = _resolve_color(rn.get("color", ""), w, cols_cycle[idx % len(cols_cycle)])
        else:
            lbl, sub = str(rn), ""
            shp = _infer_shape(lbl, shapes_cycle[idx % len(shapes_cycle)])
            col = cols_cycle[idx % len(cols_cycle)]
        nodes.append({"label": lbl, "sub": sub, "shape": shp, "color": col})

    n = len(nodes)
    has_step_bar = n >= 3
    start_y = 375 if n == 4 else (400 if n == 3 else 470)
    step_y = 228 if n == 4 else (292 if n == 3 else 380)
    span_each = 0.72 / max(1, n)

    anchors_conn: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int, int], float]] = []
    for i, nd in enumerate(nodes):
        gate = 0.0 if i == 0 else (0.04 + i * span_each * 0.78)
        alpha, dy, _ = _spring_gate(progress, gate, span=0.14)
        iso_on_left = (i % 2 == 0)
        iso_cx = 235 if iso_on_left else 845
        card_x1 = 365 if iso_on_left else 70
        card_x2 = 1010 if iso_on_left else 715
        card_h = 140 if n <= 3 else 122
        cy_base = start_y + i * step_y
        anchors_conn.append(((iso_cx, cy_base + card_h // 2 + 66), (iso_cx, cy_base + card_h // 2 - 58), nd["color"], gate))
        if alpha <= 0.02:
            continue

        cy = cy_base + dy
        is_active = (gate <= progress < gate + span_each) or (i == n - 1 and progress >= gate)
        # Spotlight Focus softly dims earlier cards slightly while lighting current node
        focus_mul = alpha if is_active else alpha * 0.80

        stage.draw_glass_card((card_x1, cy, card_x2, cy + card_h), nd["color"], radius=22, alpha_mul=focus_mul, active=is_active, layered=is_active)
        _draw_iso_prism(stage, iso_cx, cy + card_h // 2 - 22, rx=70, ry=30, depth=54, color=nd["color"], alpha_mul=focus_mul, shape=nd["shape"], active=is_active, progress=progress, phase=i * 1.1)

        tether_x1 = iso_cx + 80 if iso_on_left else card_x2
        tether_x2 = card_x1 if iso_on_left else iso_cx - 80
        stage.draw.line((tether_x1, cy + card_h // 2, tether_x2, cy + card_h // 2), fill=_with_alpha(nd["color"], focus_mul * 0.8), width=3)

        badge_txt = f"0{i+1}"
        f_num = _get_font(20, bold=True)
        stage.draw.rounded_rectangle((card_x1 + 22, cy + 20, card_x1 + 66, cy + 52), radius=10, fill=_with_alpha(nd["color"], focus_mul))
        stage.draw.text((card_x1 + 31, cy + 25), badge_txt, fill=(255, 255, 255, int(255 * focus_mul)), font=f_num)

        txt_x = card_x1 + 82
        txt_w = (card_x2 - card_x1) - 104
        if nd["sub"]:
            _draw_wrapped_text(stage.draw, nd["label"], _get_font(29, bold=True), txt_x, cy + 16, txt_w, _with_alpha(w["text"], focus_mul), max_lines=1)
            _draw_wrapped_text(stage.draw, nd["sub"], _get_font(21), txt_x, cy + 58, txt_w, _with_alpha(w["muted"], focus_mul), max_lines=2)
        else:
            _draw_wrapped_text(stage.draw, nd["label"], _get_font(30, bold=True), txt_x, cy + max(24, (card_h - 38) // 2), txt_w, _with_alpha(w["text"], focus_mul), max_lines=2)

    for i in range(n - 1):
        p_out, _, col_i, g_i = anchors_conn[i]
        _, p_in, _, g_next = anchors_conn[i + 1]
        conn_start = g_i + 0.05
        rev_t = _clamp01((progress - conn_start) / max(0.08, (g_next - conn_start + 0.04)))
        if progress >= g_i + 0.05 and rev_t > 0.02:
            e_lbl = str(edges[i]) if i < len(edges) else ""
            _draw_bezier_comet(stage, p_out, p_in, col_i, progress, rev_t, label=e_lbl)

    if data.get("metric_badges"):
        _draw_metric_badges_row(stage, data["metric_badges"], progress, 0.72, 1270)
    elif has_step_bar:
        _draw_step_progress_bar(stage, progress, [nd["label"] for nd in nodes], w["cyan"], y=1322)


def _render_node_graph(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    2.5D Node Graph Constellation:
    Central 3D Hub (`sphere`/`hexagon`/`bot`) radiating Animated Flow Arrows & Bezier
    Data Flow Lines to orbiting 3D satellite nodes (`cloud`, `shield`, `cylinder`, `chip`).
    """
    w = stage.world
    hub_lbl = str(data.get("hub_name") or data.get("center") or data.get("title") or "Core Engine")
    hub_shape = str(data.get("hub_shape") or _infer_shape(hub_lbl, "sphere")).lower()
    raw_sats = data.get("satellites") or data.get("nodes") or data.get("components") or [
        {"name": "API Gateway", "role": "Routing", "shape": "diamond"},
        {"name": "Auth Guard", "role": "Zero Trust", "shape": "shield"},
        {"name": "Vector DB", "role": "Embeddings", "shape": "cylinder"},
        {"name": "Cloud Lake", "role": "Analytics", "shape": "cloud"},
    ]

    cx, cy = VIDEO_WIDTH // 2, 745
    # Gentle orbital Smooth Zoom aura around center hub
    zoom_r = int(175 + 25 * _ease_out_cubic(progress))
    stage.draw.ellipse((cx - zoom_r, cy - zoom_r, cx + zoom_r, cy + zoom_r), outline=_with_alpha(w["cyan"], 0.25 * stage.t_alpha), width=2)
    stage.draw.ellipse((cx - zoom_r - 95, cy - zoom_r - 95, cx + zoom_r + 95, cy + zoom_r + 95), outline=_with_alpha(w["purple"], 0.16 * stage.t_alpha), width=2)

    sats = raw_sats[:4]
    sat_positions = [(290, 480), (790, 480), (290, 1025), (790, 1025)]
    cols = [w["cyan"], w["purple"], w["emerald"], w["amber"]]
    default_shps = ["cloud", "shield", "cylinder", "chip"]

    for i, sat in enumerate(sats):
        gate = 0.12 + i * 0.16
        conn_t = _clamp01((progress - gate) / 0.16)
        sx, sy = sat_positions[i % len(sat_positions)]
        is_top = (sy < cy)
        sc = cols[i % len(cols)]
        if isinstance(sat, dict):
            sname = str(sat.get("name") or sat.get("label") or sat.get("title") or f"Node {i+1}")
            srole = str(sat.get("role") or sat.get("sub") or "")
            sshp = str(sat.get("shape") or "").lower().strip() or _infer_shape(sname, default_shps[i % len(default_shps)])
            elbl = str(sat.get("edge") or "")
        else:
            sname, srole, sshp, elbl = str(sat), "", _infer_shape(str(sat), default_shps[i % len(default_shps)]), ""

        p_hub = (cx + (-95 if sx < cx else 95), cy - 55 if is_top else cy + 124)
        p_sat = (sx, sy + 104 if is_top else sy - 58)
        if conn_t > 0.02:
            _draw_bezier_comet(stage, p_hub, p_sat, sc, progress, conn_t, label=elbl, curve_offset_x=24 if i % 2 == 0 else -24)
        na, ndy, _ = _spring_gate(progress, gate + 0.06, 0.12, snappy=True)
        if na > 0.02:
            is_f = (gate <= progress < gate + 0.22)
            _draw_iso_prism(stage, sx, sy - 42 + ndy, rx=46, ry=18, depth=28, color=sc, alpha_mul=na, shape=sshp, active=is_f, progress=progress, phase=i * 0.9)
            box = (sx - 135, sy + 20 + ndy, sx + 135, sy + 102 + ndy)
            stage.draw_glass_card(box, sc, radius=18, alpha_mul=na, active=is_f, layered=True)
            _draw_wrapped_text(stage.draw, sname, _get_font(22, bold=True), box[0] + 10, box[1] + 12, 250, _with_alpha(w["text"], na), align="center", max_lines=1)
            if srole:
                _draw_wrapped_text(stage.draw, srole, _get_font(17), box[0] + 10, box[1] + 46, 250, _with_alpha(w["muted"], na), align="center", max_lines=1)

    # Central 3D Hub
    _draw_iso_prism(stage, cx, cy - 36, rx=72, ry=32, depth=52, color=w["cyan"], alpha_mul=1.0, shape=hub_shape, active=True, progress=progress)
    hub_card = (cx - 140, cy + 54, cx + 140, cy + 124)
    stage.draw_glass_card(hub_card, w["cyan"], radius=20, alpha_mul=1.0, active=True, layered=True)
    _draw_wrapped_text(stage.draw, hub_lbl.upper(), _get_font(22, bold=True), hub_card[0] + 12, hub_card[1] + 18, 256, _with_alpha(w["cyan"], stage.t_alpha), align="center", max_lines=2)


def _render_dual_pedestal_3d(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    2.5D Split Comparison Pedestals with Layered Glass Cards, 3D Card Flip,
    all 3D shapes, Snappy Slide items, and VS Energy Core.
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
    l_shape = str(data.get("left_shape") or _infer_shape(left_label, "pyramid" if not neutral else "box")).lower()
    r_shape = str(data.get("right_shape") or _infer_shape(right_label, "stack")).lower()

    col_w = 435
    lx, rx = 70, 575
    top_y = 485
    card_h = 660

    al_l, dy_l, _ = _spring_gate(progress, 0.0, 0.14)
    _draw_iso_prism(stage, lx + col_w // 2, top_y - 72 + dy_l, rx=62, ry=24, depth=38, color=l_col, alpha_mul=al_l, shape=l_shape, active=(progress < 0.45), progress=progress)
    stage.draw_glass_card((lx, top_y + dy_l, lx + col_w, top_y + card_h + dy_l), l_col, radius=26, alpha_mul=al_l, active=(progress < 0.45), layered=True)
    _draw_wrapped_text(stage.draw, left_label.upper(), _get_font(26, bold=True), lx + 24, top_y + 28 + dy_l, col_w - 48, _with_alpha(l_col, al_l), align="center", max_lines=2)

    for i, pt in enumerate(left_pts[:3]):
        ap, pdy, _ = _spring_gate(progress, 0.08 + i * 0.11, 0.10, snappy=True)
        if ap <= 0.02:
            continue
        py = top_y + 118 + i * 168 + dy_l + pdy
        stage.draw.rounded_rectangle((lx + 22, py, lx + col_w - 22, py + 142), radius=18, fill=_with_alpha(w["card_alt"], ap), outline=_with_alpha((*l_col, 110), ap), width=1)
        stage.draw.ellipse((lx + 40, py + 28, lx + 56, py + 44), fill=_with_alpha(l_col, ap))
        _draw_wrapped_text(stage.draw, str(pt), _get_font(25), lx + 70, py + 22, col_w - 104, _with_alpha(w["text"], ap), max_lines=3, line_spacing=6)

    # Right Pedestal uses smooth 3D Card Flip entrance!
    al_r, dy_r, _ = _spring_gate(progress, 0.30, 0.14)
    flip_rx = _card_flip_scale_x(progress, 0.30, 0.14)
    if al_r > 0.02:
        _draw_iso_prism(stage, rx + col_w // 2, top_y - 72 + dy_r, rx=62, ry=24, depth=38, color=r_col, alpha_mul=al_r, shape=r_shape, active=(progress >= 0.44), progress=progress, phase=1.4)
        stage.draw_glass_card((rx, top_y + dy_r, rx + col_w, top_y + card_h + dy_r), r_col, radius=26, alpha_mul=al_r, active=(progress >= 0.44), layered=True, flip_x=flip_rx)
        if flip_rx > 0.55:
            _draw_wrapped_text(stage.draw, right_label.upper(), _get_font(26, bold=True), rx + 24, top_y + 28 + dy_r, col_w - 48, _with_alpha(r_col, al_r), align="center", max_lines=2)
            for i, pt in enumerate(right_pts[:3]):
                ap, pdy, _ = _spring_gate(progress, 0.42 + i * 0.11, 0.10, snappy=True)
                if ap <= 0.02:
                    continue
                py = top_y + 118 + i * 168 + dy_r + pdy
                stage.draw.rounded_rectangle((rx + 22, py, rx + col_w - 22, py + 142), radius=18, fill=_with_alpha(w["card_alt"], ap), outline=_with_alpha((*r_col, 110), ap), width=1)
                if neutral:
                    stage.draw.ellipse((rx + 40, py + 28, rx + 56, py + 44), fill=_with_alpha(r_col, ap))
                else:
                    _draw_vector_icon(stage, rx + 50, py + 38, "check", 14, r_col, ap)
                _draw_wrapped_text(stage.draw, str(pt), _get_font(25), rx + 74, py + 22, col_w - 106, _with_alpha(w["text"], ap), max_lines=3, line_spacing=6)

    if show_vs and progress >= 0.34:
        va, _, _ = _spring_gate(progress, 0.34, 0.12)
        vx, vy = VIDEO_WIDTH // 2, top_y + card_h // 2
        stage.add_glow_orb(vx, vy, 48, w["amber"], alpha=int(180 * va * _pulse_wave(progress)))
        stage.draw.ellipse((vx - 40, vy - 40, vx + 40, vy + 40), fill=_with_alpha(w["card_alt"], va), outline=_with_alpha(w["amber"], va), width=3)
        stage.draw.text((vx - 21, vy - 16), "VS", fill=_with_alpha(w["amber"], va), font=_get_font(26, bold=True))


def _render_terminal_studio(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """Layered Glass IDE Terminal with Code Highlight spotlight beam + stdout drawer."""
    w = stage.world
    raw_code = str(data.get("code_snippet") or data.get("code") or data.get("command") or "")
    if not raw_code:
        raw_code = "# Real-time pipeline configuration\nasync def process_event(payload):\n    return await store.commit(payload)"
    lines = raw_code.splitlines()[:9]

    tx, ty, tw, th = 68, 390, 944, 760
    al, dy, _ = _spring_gate(progress, 0.0, 0.12)
    box = (tx, ty + dy, tx + tw, ty + th + dy)
    stage.add_shadow_box(box, radius=28, offset_y=20, alpha_mul=al)
    stage.draw.rounded_rectangle((tx + 12, ty + dy + 12, tx + tw + 12, ty + th + dy + 12), radius=28, fill=_with_alpha(w["card_layer"], al * 0.9), outline=_with_alpha(w["cyan"], al * 0.3), width=1)
    stage.add_glow_box(box, w["cyan"], radius=28, alpha=115)

    stage.draw.rounded_rectangle(box, radius=28, fill=(13, 18, 30, int(245 * al * stage.t_alpha)), outline=_with_alpha(w["cyan"], 0.72 * al), width=3)
    stage.draw.rounded_rectangle((tx, ty + dy, tx + tw, ty + dy + 62), radius=28, fill=(24, 33, 54, int(250 * al * stage.t_alpha)))
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
        if li == active_line_idx:
            stage.draw.rounded_rectangle((tx + 18, ly - 10, tx + tw - 18, ly + row_h - 18), radius=12, fill=(56, 189, 248, 32), outline=(56, 189, 248, 105), width=1)
        stage.draw.text((tx + 32, ly), f"{li+1:2d}", fill=(100, 116, 139), font=f_code)
        rem = max(0, chars_shown - seen)
        vis = ln[:rem]
        while vis and (f_code.getbbox(vis)[2] - f_code.getbbox(vis)[0]) > tw - 150:
            vis = vis[:-1]
        if ln.lstrip().startswith("#") or ln.lstrip().startswith("//"):
            code_col = (148, 163, 184)
        elif any(k in ln for k in ("def ", "async ", "SELECT", "FROM", "return", "await ", "import ")):
            code_col = (52, 211, 153)
        elif "'" in ln or '"' in ln:
            code_col = (251, 191, 36)
        else:
            code_col = (248, 250, 252)
        stage.draw.text((tx + 96, ly), vis, fill=code_col, font=f_code)
        seen += len(ln) + 1
        if seen >= chars_shown:
            vx = tx + 98 + (f_code.getbbox(vis)[2] - f_code.getbbox(vis)[0] if vis else 0)
            stage.draw.rounded_rectangle((vx, ly + 2, vx + 10, ly + 32), radius=2, fill=w["cyan"])
            break

    out_txt = str(data.get("output") or "").strip()
    if out_txt and progress >= 0.65:
        oa, ody, _ = _spring_gate(progress, 0.65, 0.14)
        oy = ty + th + dy + 28 + ody
        stage.draw_glass_card((tx, oy, tx + tw, oy + 145), w["emerald"], radius=22, alpha_mul=oa, active=True, layered=True)
        stage.draw.text((tx + 28, oy + 20), "STDOUT", fill=_with_alpha(w["emerald"], oa), font=_get_font(19, bold=True))
        _draw_wrapped_text(stage.draw, out_txt, _get_font(25, bold=True), tx + 28, oy + 56, tw - 56, _with_alpha(w["text"], oa), max_lines=2)


def _render_cinematic_custom_scene(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """
    Composable Block Studio with Live Counter, Elastic Pop pills, Layered Cards,
    All 12 3D Shapes, Bezier Flow Chains, Vector Icons, Metric Badges & Step Progress.
    """
    w = stage.world
    blocks = list(data.get("blocks") or [])[:4]
    if not blocks:
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

    if len(blocks) == 1 and str(blocks[0].get("block", "")).lower().strip() == "flow_chain":
        fc = blocks[0]
        _render_iso_architecture(stage, {"nodes": fc.get("nodes", []), "edges": fc.get("edges") or fc.get("arrows") or [], "metric_badges": data.get("metric_badges")}, progress)
        return

    n_b = len(blocks)
    avail_top = 365
    avail_bot = 1320 if data.get("metric_badges") else 1385
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
    icon_cycle = ["bolt", "db", "code", "lock"]

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
        focus_mul = alpha if is_active else alpha * 0.84
        col_acc = _resolve_color(b.get("color", ""), w, w["cyan"])
        yc = y_cur + dy

        if bt == "big_stat":
            raw_val = str(b.get("value") or b.get("val") or b.get("number") or b.get("stat") or b.get("metric") or b.get("headline") or b.get("text") or "").strip()
            count_t = _clamp01((progress - gate) / 0.34)
            val_str = _animate_counter_text(raw_val, count_t)
            lbl_str = str(b.get("label") or "").upper().strip()
            shp_stat = str(b.get("shape") or _infer_shape(lbl_str, "pyramid")).lower()
            stage.draw_glass_card((cx, yc, cx + cw, yc + bh), col_acc, radius=26, alpha_mul=focus_mul, active=is_active, layered=True)
            _draw_iso_prism(stage, cx + 84, yc + bh // 2 - 14, rx=38, ry=16, depth=26, color=col_acc, alpha_mul=focus_mul, shape=shp_stat, active=is_active, progress=progress)
            if val_str:
                fb = _get_font(66 if len(val_str) <= 6 else (48 if len(val_str) <= 14 else 38), bold=True)
                vb = fb.getbbox(val_str)
                vx = cx + 150 + max(0, ((cw - 175) - (vb[2] - vb[0])) // 2)
                stage.add_glow_orb(vx + (vb[2] - vb[0]) // 2, yc + 48, 46, col_acc, alpha=int(135 * focus_mul * _pulse_wave(progress)))
                stage.draw.text((vx, yc + (20 if lbl_str else max(26, (bh - 70) // 2))), val_str, fill=_with_alpha(col_acc, focus_mul), font=fb)
                if lbl_str:
                    _draw_wrapped_text(stage.draw, lbl_str, _get_font(22, bold=True), cx + 150, yc + bh - 48, cw - 175, _with_alpha(w["text"], focus_mul), align="center", max_lines=1)
            elif lbl_str:
                _draw_wrapped_text(stage.draw, lbl_str, _get_font(32, bold=True), cx + 150, yc + max(28, (bh - 42) // 2), cw - 175, _with_alpha(col_acc, focus_mul), align="center", max_lines=2)

        elif bt == "question_card":
            eyebrow = str(b.get("eyebrow") or "").strip().upper()
            q_text = str(b.get("text") or "")
            stage.draw_glass_card((cx, yc, cx + cw, yc + bh), col_acc, radius=28, alpha_mul=focus_mul, active=is_active, layered=True)
            stage.draw.rounded_rectangle((cx + 22, yc + 22, cx + 29, yc + bh - 22), radius=3, fill=_with_alpha(col_acc, focus_mul))
            ttop = yc + 24
            if eyebrow:
                _draw_wrapped_text(stage.draw, eyebrow, _get_font(20, bold=True), cx + 52, ttop, cw - 90, _with_alpha(col_acc, focus_mul), align="center", max_lines=1)
                ttop += 34
            else:
                ttop = yc + max(22, (bh - _est_lines(q_text, font_q, cw - 110, 3) * 48) // 2)
            _draw_wrapped_text(stage.draw, q_text, font_q, cx + 52, ttop, cw - 104, _with_alpha(w["text"], focus_mul), align="center", max_lines=3, line_spacing=8)

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
                    fl = _card_flip_scale_x(progress, gate + 0.08, 0.12) if pi == 1 else 1.0
                    stage.draw_glass_card((px, yc + pdy, px + pw, yc + bh + pdy), pc, radius=22, alpha_mul=pa, active=(pi == 1 or progress < gate + 0.16), flip_x=fl)
                    if fl > 0.55:
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
                    pa, pdy, _ = _spring_gate(progress, gate + pi * 0.07, 0.11, snappy=True)
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
                    bg_t = gate + pi * 0.08
                    if progress < bg_t:
                        continue
                    raw = _clamp01((progress - bg_t) / 0.14)
                    el = _ease_out_elastic(raw)
                    pdy = int((1.0 - min(1.12, el)) * 28)
                    pa = _clamp01(raw * 1.6)
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
                    nshp = str(rn.get("shape") or "").lower().strip() or _infer_shape(nl + " " + ns, "box")
                else:
                    nl, ns = str(rn), ""
                    nshp = _infer_shape(nl, "box")
                stage.draw_glass_card((cx + 78, ny, cx + cw, ny + nh), nc, radius=20, alpha_mul=na, active=is_f, layered=is_f)
                _draw_iso_prism(stage, cx + 38, ny + nh // 2 - 12, rx=30, ry=13, depth=22, color=nc, alpha_mul=na, shape=nshp, active=is_f, progress=progress, phase=ni * 0.8)
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
            stage.draw.rounded_rectangle(box, radius=22, fill=(13, 18, 30, int(246 * alpha * stage.t_alpha)), outline=_with_alpha(w["cyan"], alpha), width=2)
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
                la, ldy, _ = _spring_gate(progress, gate + li * 0.12, 0.11, snappy=True)
                if la <= 0.02:
                    continue
                ry = y_cur + li * (rh + igap) + ldy
                if isinstance(rit, dict):
                    hd = str(rit.get("title") or rit.get("label") or "")
                    sb = str(rit.get("desc") or rit.get("sub") or "")
                    ikind = str(rit.get("icon") or rit.get("kind") or var).lower()
                else:
                    si = str(rit)
                    pts = si.split(":", 1) if ":" in si else (si.split("—", 1) if "—" in si else [si, ""])
                    hd, sb = pts[0].strip(), (pts[1].strip() if len(pts) > 1 else "")
                    ikind = var if var != "check" else icon_cycle[li % len(icon_cycle)]
                is_f = (gate + li * 0.12 <= progress < gate + (li + 1) * 0.14)
                ccol = w["amber"] if ikind in ("warn", "warning") else w["cyan"]
                stage.draw_glass_card((cx, ry, cx + cw, ry + rh), ccol, radius=22, alpha_mul=la if is_f else la * 0.85, active=is_f, layered=is_f)
                _draw_vector_icon(stage, cx + 48, ry + rh // 2, ikind, 20, w["amber"] if ikind in ("warn", "warning") else w["emerald"], la)
                if sb:
                    _draw_wrapped_text(stage.draw, hd, _get_font(27, bold=True), cx + 92, ry + 16, cw - 115, _with_alpha(w["text"], la), max_lines=1)
                    _draw_wrapped_text(stage.draw, sb, _get_font(21), cx + 92, ry + 52, cw - 115, _with_alpha(w["muted"], la), max_lines=2)
                else:
                    _draw_wrapped_text(stage.draw, hd, _get_font(27, bold=True), cx + 92, ry + max(18, (rh - 34) // 2), cw - 115, _with_alpha(w["text"], la), max_lines=2)

        y_cur += bh + gap

    if data.get("metric_badges"):
        _draw_metric_badges_row(stage, data["metric_badges"], progress, 0.72, 1345)


def _render_cinematic_kinetic(stage: StudioStage, data: Dict[str, Any], progress: float) -> None:
    """Kinetic Typography with Pulse Highlight glow waves, Smooth Zoom scale, and Elastic Pop badges."""
    w = stage.world
    kicker = str(data.get("kicker") or "").strip().upper()
    stmt = str(data.get("statement") or data.get("title") or "").strip()
    hl = str(data.get("highlight_word") or "").strip().lower()
    tags = data.get("bottom_tags") or []

    line_t = _ease_out_cubic(min(1.0, progress / 0.22))
    lw = int(680 * line_t)
    mx = VIDEO_WIDTH // 2
    stage.add_glow_line([(mx - lw // 2, 462), (mx + lw // 2, 462)], w["amber"], alpha=160, width_q=3)
    stage.draw.line((mx - lw // 2, 462, mx + lw // 2, 462), fill=_with_alpha(w["amber"], stage.t_alpha), width=4)
    if kicker:
        _draw_wrapped_text(stage.draw, kicker, _get_font(25, bold=True), 120, 410, VIDEO_WIDTH - 240, _with_alpha(w["amber"], stage.t_alpha), align="center", max_lines=1)

    words = stmt.split()
    tot = len(words)
    vis = tot if progress >= 0.62 else max(2, int(math.ceil(tot * min(1.0, 0.25 + progress * 1.25))))
    shown = words[:vis]
    # Subtle Smooth Zoom growth (56 -> 58 / 48 -> 50)
    zoom_bump = 2 if progress > 0.65 else 0
    fsize = (56 if tot <= 9 else (48 if tot <= 15 else 42)) + zoom_bump
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
    pulse_val = _pulse_wave(progress, speed=5.0)
    for lw_list in lines[:6]:
        lstr = " ".join(lw_list)
        lpx = fb.getbbox(lstr)[2] - fb.getbbox(lstr)[0]
        cx_w = (VIDEO_WIDTH - lpx) // 2
        for wd in lw_list:
            is_hl = bool(hl and hl in wd.lower())
            if is_hl:
                wb = fb.getbbox(wd)
                stage.add_glow_orb(cx_w + (wb[2] - wb[0]) // 2, yc + fsize // 2, 58 * pulse_val, w["cyan"], alpha=int(180 * pulse_val))
                stage.draw.line((cx_w, yc + fsize + 10, cx_w + (wb[2] - wb[0]), yc + fsize + 10), fill=_with_alpha(w["amber"], stage.t_alpha), width=5)
            wd_s = wd + " "
            stage.draw.text((cx_w, yc), wd_s, fill=_with_alpha(w["cyan"] if is_hl else w["text"], stage.t_alpha), font=fb)
            cx_w += fb.getbbox(wd_s)[2] - fb.getbbox(wd_s)[0]
        yc += fsize + 24

    if tags and progress >= 0.40:
        tag_y = max(yc + 55, 1020)
        vis_t = tags[:3]
        tw, sp = 280, 22
        tx0 = (VIDEO_WIDTH - (len(vis_t) * tw + (len(vis_t) - 1) * sp)) // 2
        for ti, tg in enumerate(vis_t):
            bg_t = 0.40 + ti * 0.08
            if progress < bg_t:
                continue
            raw = _clamp01((progress - bg_t) / 0.14)
            el = _ease_out_elastic(raw)
            tdy = int((1.0 - min(1.12, el)) * 26)
            ta = _clamp01(raw * 1.6)
            bx = tx0 + ti * (tw + sp)
            stage.draw_glass_card((bx, tag_y + tdy, bx + tw, tag_y + tdy + 76), w["emerald"], radius=38, alpha_mul=ta, active=True)
            _draw_wrapped_text(stage.draw, str(tg).upper(), _get_font(21, bold=True), bx + 12, tag_y + tdy + 24, tw - 24, _with_alpha(w["text"], ta), align="center", max_lines=1)


# =========================================================================
# MAIN SCENE DISPATCH & FRAME GENERATION LOOP
# =========================================================================
def _dispatch_cinematic(stage: StudioStage, visual_type: str, visual_data: Dict[str, Any], progress: float) -> None:
    vt = str(visual_type or "custom_scene").lower().strip()
    if vt in ("node_graph", "circular_hub_mesh", "network_mesh", "hub_spoke", "mesh"):
        _render_node_graph(stage, visual_data, progress)
    elif vt in ("iso_architecture", "iso_stack", "architecture_flow", "hybrid_merge", "all_in_one_tech_canvas"):
        if vt == "hybrid_merge" and not visual_data.get("nodes"):
            lp = visual_data.get("left_pillar") or {}
            rp = visual_data.get("right_pillar") or {}
            merged = visual_data.get("merged_label") or "Unified Engine"
            visual_data = {
                **visual_data,
                "nodes": [
                    {"label": lp.get("label", "Input Layer"), "sub": lp.get("sub", ""), "shape": "stack", "color": "purple"},
                    {"label": rp.get("label", "Live Source"), "sub": rp.get("sub", ""), "shape": "cylinder", "color": "cyan"},
                    {"label": merged, "sub": " | ".join(str(x) for x in (visual_data.get("outcomes") or [])[:3]), "shape": "shield", "color": "emerald"},
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
        nds = [{"label": s.get("title", f"Step {i+1}"), "sub": s.get("desc", ""), "shape": _infer_shape(s.get("title", ""), "hexagon")} for i, s in enumerate(steps[:4])]
        _render_iso_architecture(stage, {"nodes": nds, "edges": [], "metric_badges": visual_data.get("metric_badges")}, progress)
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
    Renders studio-grade 2.5D isometric frames (Zero heavy bottom grid!) with ALL 12 shapes,
    Spring Physics, Elastic Pop, Card Flip, Live Counter, Parallax Depth, Node Graph,
    Step Progress Bar, Subtle Grid Backdrop, Optical Bloom, and Voice-Reactive Waveform.
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

    # Dual-plane Parallax Depth particles (plane 0: distant slow bokeh; plane 1: nearer drifting diamonds/rings)
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
        # Parallax Far Plane (slow drift 70px)
        for px0, py0, pr, pa in far_particles:
            py_live = int((py0 - linear_p * 70) % canvas_h)
            px_live = int((px0 + math.sin(linear_p * 3.14 + py0) * 10) % canvas_w)
            p_draw.ellipse((px_live - pr, py_live - pr, px_live + pr, py_live + pr), fill=(*accent, pa))
        # Parallax Near Plane (faster drift 175px with tiny micro rings/diamonds)
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
            _dispatch_cinematic(stage, visual_type, visual_data, progress)

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
