import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core.config import ASSETS_DIR
from core.layouts_it_sdlc import IT_SDLC_35_LAYOUTS, render_it_sdlc_layout
from core.layouts_pro import EXTRA_32_LAYOUTS, render_pro_layout
from core.palette_engine import resolve_studio_world
from core.shapes_3d import ALL_50_SHAPES, ALL_100_SHAPES, ALL_145_SHAPES, draw_3d_shape, draw_vector_glyph, infer_3d_shape
from core.svg_engine import ICON_ALIASES, fetch_iconify_svg, prepare_generative_svg_layers, prepare_keyframed_svg_layers

# Stage safe geometry inside 1080x1920 vertical frame
STAGE_X0 = 64
STAGE_Y0 = 358
STAGE_X1 = 1016
STAGE_Y1 = 1426
STAGE_W = STAGE_X1 - STAGE_X0
STAGE_H = STAGE_Y1 - STAGE_Y0

_FONT_CACHE: Dict[Tuple[int, bool, bool], ImageFont.FreeTypeFont] = {}
_ACCENT_CYCLE = ("cyan", "purple", "emerald", "amber", "rose")


# =========================================================================
# MOTION PHYSICS & MATH HELPERS
# =========================================================================
def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def _ease_out_cubic(t: float) -> float:
    t = _clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def _ease_out_back(t: float) -> float:
    t = _clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _ease_out_elastic(t: float) -> float:
    t = _clamp01(t)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    c4 = (2.0 * math.pi) / 3.0
    return (2.0 ** (-10.0 * t)) * math.sin((t * 10.0 - 0.75) * c4) + 1.0


def _micro_bounce(t: float) -> float:
    t = _clamp01(t)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return 1.0 - math.exp(-7.5 * t) * math.cos(t * math.pi * 2.5)


def _pulse_wave(progress: float, phase: float = 0.0, speed: float = 4.0) -> float:
    return 0.5 + 0.5 * math.sin(progress * math.pi * speed + phase)


def _card_flip_scale_x(t: float) -> float:
    t = _clamp01(t)
    if t >= 0.99:
        return 1.0
    # Half-turn reveal from edge-on (0.14) to full width (1.0)
    return max(0.14, math.sin(_ease_out_cubic(t) * (math.pi / 2.0)))


def _spring_gate(progress: float, idx: int, total: int, span: float = 0.24) -> float:
    n = max(1, total)
    start = (idx / max(1, n)) * min(0.56, 0.14 * max(1, n - 1))
    return _clamp01((progress - start) / max(0.08, span))


def _animate_counter_text(raw_val: Any, p: float) -> str:
    txt = str(raw_val or "").strip()
    if p >= 0.98 or not txt:
        return txt
    m = re.search(r"([+-]?\d[\d,]*(?:\.\d+)?)", txt)
    if not m:
        return txt
    num_str = m.group(1)
    clean_num = num_str.replace(",", "")
    try:
        target = float(clean_num)
    except ValueError:
        return txt
    eased = _ease_out_cubic(p)
    cur = target * eased
    if "." in clean_num:
        dec = len(clean_num.split(".", 1)[1])
        formatted = f"{cur:,.{dec}f}" if "," in num_str else f"{cur:.{dec}f}"
    else:
        iv = int(round(cur))
        formatted = f"{iv:,}" if "," in num_str else str(iv)
    return txt[:m.start(1)] + formatted + txt[m.end(1):]


# =========================================================================
# COLOR & FONT UTILITIES
# =========================================================================
def _rgb_to_hex(rgb: Tuple[int, ...]) -> str:
    return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"


def _hex_to_rgb(h: str, fallback: Tuple[int, int, int] = (56, 189, 248)) -> Tuple[int, int, int]:
    raw = str(h or "").strip().lstrip("#")
    if len(raw) == 6:
        try:
            return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
        except ValueError:
            pass
    return fallback


def resolve_world_color(world: Dict[str, Any], col_spec: Any = "", fallback_key: str = "cyan") -> Tuple[int, int, int]:
    s = str(col_spec or "").lower().strip()
    if s.startswith("#") and len(s.lstrip("#")) == 6:
        return _hex_to_rgb(s, world.get(fallback_key, (56, 189, 248)))
    alias = {
        "primary": "cyan", "blue": "cyan", "sky": "cyan", "teal": "cyan", "cyan": "cyan",
        "secondary": "purple", "violet": "purple", "indigo": "purple", "purple": "purple", "magenta": "purple",
        "green": "emerald", "mint": "emerald", "success": "emerald", "emerald": "emerald", "ok": "emerald",
        "yellow": "amber", "gold": "amber", "orange": "amber", "warn": "amber", "amber": "amber",
        "red": "rose", "crimson": "rose", "pink": "rose", "error": "rose", "danger": "rose", "rose": "rose",
    }.get(s, "")
    if alias and alias in world:
        return tuple(world[alias][:3])
    return tuple(world.get(fallback_key, (56, 189, 248))[:3])


def _with_alpha(col: Tuple[int, ...], alpha_mul: float) -> Tuple[int, int, int, int]:
    a_m = _clamp01(alpha_mul)
    base_a = col[3] if len(col) >= 4 else 255
    return (int(col[0]), int(col[1]), int(col[2]), max(0, min(255, int(base_a * a_m))))


def _get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    key = (int(size), bool(bold), bool(mono))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates: List[str] = []
    font_dir = ASSETS_DIR / "fonts"
    if mono:
        candidates.extend([
            str(font_dir / ("JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf")),
            "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ])
    elif bold:
        candidates.extend([
            str(font_dir / "Inter-Bold.ttf"),
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            str(font_dir / "Inter-Regular.ttf"),
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ])
    for p in candidates:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, int(size))
                _FONT_CACHE[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    words = str(text or "").split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = words[0]
    for w in words[1:]:
        cand = f"{cur} {w}"
        if draw.textlength(cand, font=font) <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _est_lines(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> int:
    dummy = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    return len(_wrap_lines(dummy, text, font, max_w))


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, ...],
    max_w: int,
    line_gap: int = 8,
    align: str = "left",
    max_lines: int = 12,
) -> int:
    lines = _wrap_lines(draw, text, font, max_w)[:max_lines]
    x, y = xy
    sz = getattr(font, "size", 26)
    lh = int(sz * 1.18) + line_gap
    for ln in lines:
        lw = draw.textlength(ln, font=font)
        dx = x
        if align == "center":
            dx = int(x + (max_w - lw) / 2.0)
        elif align == "right":
            dx = int(x + max_w - lw)
        draw.text((dx, y), ln, font=font, fill=fill)
        y += lh
    return y


# =========================================================================
# STUDIO LAYERED COMPOSITOR STAGE
# =========================================================================
class StudioStage:
    """Fast multi-layer RGBA compositor with quarter-res blurred shadows & optical bloom."""

    def __init__(self, width: int = 1080, height: int = 1920, world: Optional[Dict[str, Any]] = None, transition_alpha: float = 1.0):
        self.width = width
        self.height = height
        self.world = world or resolve_studio_world()
        self.t_alpha = _clamp01(transition_alpha)
        self._q_scale = 4
        qw, qh = max(1, width // self._q_scale), max(1, height // self._q_scale)
        self.shadow = Image.new("RGBA", (qw, qh), (0, 0, 0, 0))
        self.glow = Image.new("RGBA", (qw, qh), (0, 0, 0, 0))
        self.fg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.sdraw = ImageDraw.Draw(self.shadow)
        self.gdraw = ImageDraw.Draw(self.glow)
        self.draw = ImageDraw.Draw(self.fg)

    def add_shadow_ellipse(self, bbox: Tuple[int, int, int, int], alpha_mul: float = 1.0) -> None:
        eff = alpha_mul * self.t_alpha
        if eff <= 0.02:
            return
        q = self._q_scale
        scol = _with_alpha(self.world["shadow_col"], eff)
        self.sdraw.ellipse((bbox[0] / q, bbox[1] / q, bbox[2] / q, bbox[3] / q), fill=scol)

    def add_shadow_rect(self, bbox: Tuple[int, int, int, int], radius: int = 24, alpha_mul: float = 1.0) -> None:
        eff = alpha_mul * self.t_alpha
        if eff <= 0.02:
            return
        q = self._q_scale
        scol = _with_alpha(self.world["shadow_col"], eff)
        self.sdraw.rounded_rectangle(
            (bbox[0] / q, bbox[1] / q, bbox[2] / q, bbox[3] / q),
            radius=max(2, radius // q),
            fill=scol,
        )

    def add_glow_orb(self, cx: float, cy: float, radius: float, color: Tuple[int, ...], alpha: int = 135) -> None:
        eff = self.t_alpha
        if eff <= 0.02 or radius <= 1:
            return
        q = self._q_scale
        gx, gy, gr = cx / q, cy / q, max(2.0, radius / q)
        col = (int(color[0]), int(color[1]), int(color[2]), max(0, min(255, int(alpha * eff))))
        self.gdraw.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=col)

    def add_glow_line(self, pts: List[Tuple[float, float]], color: Tuple[int, ...], width: int = 10, alpha: int = 120) -> None:
        eff = self.t_alpha
        if eff <= 0.02 or len(pts) < 2:
            return
        q = self._q_scale
        qpts = [(x / q, y / q) for x, y in pts]
        col = (int(color[0]), int(color[1]), int(color[2]), max(0, min(255, int(alpha * eff))))
        self.gdraw.line(qpts, fill=col, width=max(2, width // q))

    def add_glow_box(self, bbox: Tuple[int, int, int, int], color: Tuple[int, ...], radius: int = 14, alpha: int = 90) -> None:
        eff = self.t_alpha
        if eff <= 0.02:
            return
        q = self._q_scale
        col = (int(color[0]), int(color[1]), int(color[2]), max(0, min(255, int(alpha * eff))))
        self.gdraw.rounded_rectangle((bbox[0] / q, bbox[1] / q, bbox[2] / q, bbox[3] / q), radius=max(2, radius // q), fill=col)

    def draw_glass_card(
        self,
        bbox: Tuple[int, int, int, int],
        radius: int = 24,
        accent_col: Optional[Tuple[int, ...]] = None,
        alpha_mul: float = 1.0,
        active: bool = False,
        fill_override: Optional[Tuple[int, ...]] = None,
        elev: int = 10,
        flip_t: float = 1.0,
        layered: bool = False,
    ) -> Tuple[int, int, int, int]:
        eff = _clamp01(alpha_mul) * self.t_alpha
        if eff <= 0.02:
            return bbox
        x0, y0, x1, y1 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        if flip_t < 0.99:
            sx = _card_flip_scale_x(flip_t)
            cx = (x0 + x1) * 0.5
            hw = max(8.0, (x1 - x0) * 0.5 * sx)
            x0, x1 = int(round(cx - hw)), int(round(cx + hw))
        b = (x0, y0, x1, y1)
        if elev > 0:
            self.add_shadow_rect((x0 + 3, y0 + elev, x1 + 3, y1 + elev + 4), radius=radius, alpha_mul=alpha_mul)
        if layered and (x1 - x0) > 40:
            back_b = (x0 + 10, y0 + 10, x1 + 10, y1 + 10)
            self.draw.rounded_rectangle(back_b, radius=radius, fill=_with_alpha(self.world["card_layer"], eff * 0.85), outline=_with_alpha(self.world["border"], eff * 0.45), width=1)
        bg = fill_override or (self.world["card_alt"] if active else self.world["card_bg"])
        ac = accent_col or self.world["cyan"]
        border_col = _with_alpha((*ac[:3], 235 if active else 145), eff) if accent_col or active else _with_alpha(self.world["border"], eff)
        bw = 3 if active else 2
        if active:
            gl_alpha = 26 if self.world.get("is_light") else 48
            self.add_glow_box((x0 - 8, y0 - 8, x1 + 8, y1 + 8), ac, radius=radius + 8, alpha=gl_alpha)
        self.draw.rounded_rectangle(b, radius=radius, fill=_with_alpha(bg, eff), outline=border_col, width=bw)
        # Subtle glass top rim highlight
        if (x1 - x0) > 2 * radius + 12:
            rim = _with_alpha(self.world["glass_rim"], eff * (0.95 if active else 0.72))
            self.draw.line((x0 + radius, y0 + 2, x1 - radius, y0 + 2), fill=rim, width=2)
        return b

    def draw_pill(
        self,
        cx: int,
        cy: int,
        text: str,
        bg_col: Tuple[int, ...],
        text_col: Tuple[int, ...],
        border_col: Optional[Tuple[int, ...]] = None,
        font: Optional[ImageFont.FreeTypeFont] = None,
        alpha_mul: float = 1.0,
        pad_x: int = 18,
        pad_y: int = 8,
    ) -> Tuple[int, int, int, int]:
        eff = _clamp01(alpha_mul) * self.t_alpha
        if eff <= 0.02:
            return (cx, cy, cx, cy)
        f = font or _get_font(22, bold=True)
        tw = self.draw.textlength(text, font=f)
        th = getattr(f, "size", 22)
        w = int(tw + pad_x * 2)
        h = int(th + pad_y * 2)
        box = (int(cx - w // 2), int(cy - h // 2), int(cx + w // 2), int(cy + h // 2))
        self.draw.rounded_rectangle(box, radius=h // 2, fill=_with_alpha(bg_col, eff), outline=_with_alpha(border_col, eff) if border_col else None, width=2 if border_col else 0)
        self.draw.text((int(cx - tw / 2), int(cy - th * 0.58)), text, font=f, fill=_with_alpha(text_col, eff))
        return box

    def composite_onto(self, bg_img: Optional[Image.Image] = None) -> Image.Image:
        if bg_img is None:
            base = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        else:
            base = bg_img.convert("RGBA") if bg_img.mode != "RGBA" else bg_img.copy()
        sh_blur = self.shadow.filter(ImageFilter.GaussianBlur(radius=6)).resize((self.width, self.height), Image.Resampling.BILINEAR)
        gl_blur = self.glow.filter(ImageFilter.GaussianBlur(radius=9)).resize((self.width, self.height), Image.Resampling.BILINEAR)
        base.alpha_composite(sh_blur)
        base.alpha_composite(gl_blur)
        base.alpha_composite(self.fg)
        return base


# =========================================================================
# SHARED VECTOR BEZIER ARROWS, NODE VISUALS & CHROME
# =========================================================================
def _eval_bezier(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], t: float) -> Tuple[float, float]:
    u = 1.0 - t
    x = (u ** 3) * p0[0] + 3 * (u ** 2) * t * p1[0] + 3 * u * (t ** 2) * p2[0] + (t ** 3) * p3[0]
    y = (u ** 3) * p0[1] + 3 * (u ** 2) * t * p1[1] + 3 * u * (t ** 2) * p2[1] + (t ** 3) * p3[1]
    return (x, y)


def _draw_bezier_comet(
    stage: StudioStage,
    p0: Tuple[float, float],
    p3: Tuple[float, float],
    color: Tuple[int, int, int],
    reveal: float = 1.0,
    progress: float = 0.0,
    phase: float = 0.0,
    label: str = "",
    curve_bend: float = 0.0,
    alpha_mul: float = 1.0,
    world: Optional[Dict[str, Any]] = None,
) -> None:
    eff = _clamp01(reveal) * _clamp01(alpha_mul) * stage.t_alpha
    if eff <= 0.03:
        return
    w = world or stage.world
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    mx = (p0[0] + p3[0]) * 0.5
    my = (p0[1] + p3[1]) * 0.5
    if abs(dx) >= abs(dy):
        p1 = (p0[0] + dx * 0.45, p0[1] + curve_bend)
        p2 = (p3[0] - dx * 0.45, p3[1] - curve_bend)
    else:
        p1 = (p0[0] + curve_bend, p0[1] + dy * 0.45)
        p2 = (p3[0] - curve_bend, p3[1] - dy * 0.45)

    steps = 20
    max_t = _ease_out_cubic(_clamp01(reveal))
    pts = [_eval_bezier(p0, p1, p2, p3, (i / steps) * max_t) for i in range(steps + 1)]
    stage.add_glow_line(pts, color, width=10, alpha=int(135 * eff))
    stage.draw.line(pts, fill=_with_alpha((*color[:3], 225), eff), width=4)

    # Arrowhead
    if len(pts) >= 2 and max_t > 0.25:
        tip = pts[-1]
        prev = pts[-2]
        ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        sz = 13
        ah = [
            tip,
            (tip[0] - sz * math.cos(ang - 0.52), tip[1] - sz * math.sin(ang - 0.52)),
            (tip[0] - sz * math.cos(ang + 0.52), tip[1] - sz * math.sin(ang + 0.52)),
        ]
        stage.draw.polygon(ah, fill=_with_alpha((*color[:3], 245), eff))

    # Moving data-flow comet orb
    if max_t > 0.7:
        ct = ((progress * 1.45 + phase) % 1.0) * max_t
        cx, cy = _eval_bezier(p0, p1, p2, p3, ct)
        stage.add_glow_orb(cx, cy, 14, color, alpha=int(210 * eff))
        stage.draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=_with_alpha((255, 255, 255, 250), eff))

    if label and max_t > 0.5:
        lx, ly = _eval_bezier(p0, p1, p2, p3, 0.5)
        bg = (*w["bg_top"][:3], 236)
        stage.draw_pill(int(lx), int(ly), str(label)[:20], bg, w["text"], border_col=(*color[:3], 200), font=_get_font(19, bold=True), alpha_mul=eff, pad_x=12, pad_y=5)


def _resolve_iconify_if_any(icon_spec: str, tint_rgb: Tuple[int, int, int], size_px: int = 84) -> Optional[Image.Image]:
    ic = str(icon_spec or "").strip()
    if not ic:
        return None
    low = ic.lower()
    if ":" in low or low in ICON_ALIASES:
        return fetch_iconify_svg(low, size_px=size_px, tint_hex=_rgb_to_hex(tint_rgb))
    return None


def _draw_node_visual(
    stage: StudioStage,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    depth: int,
    color: Tuple[int, int, int],
    alpha_mul: float,
    shape: str = "",
    icon: str = "",
    label: str = "",
    active: bool = False,
    progress: float = 0.0,
    phase: float = 0.0,
) -> None:
    """Unified renderer supporting Iconify 200,000+ SVGs on 3D pedestals + all 50 3D shapes."""
    ic_spec = str(icon or "").strip()
    shp_spec = str(shape or "").strip().lower()
    if not ic_spec and (":" in shp_spec or shp_spec in ICON_ALIASES):
        ic_spec = shp_spec
    icon_img = _resolve_iconify_if_any(ic_spec, color, size_px=max(72, int(rx * 1.9))) if ic_spec else None

    if shp_spec in ALL_145_SHAPES:
        final_shp = shp_spec
    else:
        final_shp = infer_3d_shape(f"{label} {shp_spec} {ic_spec}", fallback="box")

    draw_3d_shape(
        stage, cx, cy, rx, ry, depth, color,
        alpha_mul=alpha_mul, shape=final_shp, active=active,
        progress=progress, phase=phase, icon_img=icon_img, extrude_3d=True,
    )


def _draw_metric_badges_row(stage: StudioStage, badges: List[Any], progress: float, world: Dict[str, Any]) -> None:
    if not badges:
        return
    clean = [str(b).strip()[:24] for b in badges[:3] if str(b).strip()]
    if not clean:
        return
    f = _get_font(20, bold=True)
    gap = 14
    widths = [int(stage.draw.textlength(t, font=f)) + 34 for t in clean]
    total_w = sum(widths) + gap * (len(clean) - 1)
    sx = int((1080 - total_w) / 2.0)
    y = 324
    for i, txt in enumerate(clean):
        g = _ease_out_cubic(_spring_gate(progress, i, len(clean), 0.20))
        if g <= 0.05:
            continue
        ac = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        bw = widths[i]
        stage.draw_pill(sx + bw // 2, y, txt, (*ac[:3], 34), world["text"], border_col=(*ac[:3], 180), font=f, alpha_mul=g, pad_x=16, pad_y=6)
        sx += bw + gap


def _draw_step_progress_bar(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    try:
        step_idx = int(data.get("step_index", data.get("step", 0)) or 0)
        total_steps = int(data.get("total_steps", data.get("steps_count", 0)) or 0)
    except Exception:
        return
    if total_steps <= 1 or step_idx <= 0:
        return
    total_steps = max(2, min(8, total_steps))
    step_idx = max(1, min(total_steps, step_idx))
    x0, y0, x1, y1 = 180, 1458, 900, 1472
    seg_gap = 12
    seg_w = (x1 - x0 - seg_gap * (total_steps - 1)) / float(total_steps)
    for i in range(total_steps):
        sx0 = int(x0 + i * (seg_w + seg_gap))
        sx1 = int(sx0 + seg_w)
        done = (i + 1) < step_idx
        cur = (i + 1) == step_idx
        col = world["emerald"] if done else (world["cyan"] if cur else (*world["muted"][:3], 70))
        stage.draw.rounded_rectangle((sx0, y0, sx1, y1), radius=7, fill=_with_alpha(col, stage.t_alpha))
        if cur:
            fill_w = max(8, int((sx1 - sx0) * _ease_out_cubic(progress)))
            stage.draw.rounded_rectangle((sx0, y0, sx0 + fill_w, y1), radius=7, fill=_with_alpha(world["amber"], stage.t_alpha))


# =========================================================================
# LAYOUT FAMILY 1: CORE 6 UPGRADED CINEMATIC ARCHITECTURES
# =========================================================================
def _render_iso_architecture(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    raw_nodes = data.get("nodes") or data.get("steps") or []
    nodes = list(raw_nodes)[:4]
    if not nodes:
        return
    n = len(nodes)
    edges = data.get("edges") or []
    y_top = 420 if n == 4 else (475 if n == 3 else 560)
    y_step = 246 if n == 4 else (310 if n == 3 else 360)

    anchors: List[Tuple[int, int]] = []
    for i, nd in enumerate(nodes):
        if isinstance(nd, str):
            nd = {"name": nd}
        g = _spring_gate(progress, i, n, 0.24)
        e_pop = _ease_out_elastic(g) if g < 0.95 else 1.0
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            anchors.append((540, y_top + i * y_step))
            continue

        cy = y_top + i * y_step
        is_left = (i % 2 == 0)
        col = resolve_world_color(world, nd.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        active = (int(progress * n) == i) or bool(nd.get("highlight"))
        slide_off = int((1.0 - _ease_out_cubic(g)) * (-40 if is_left else 40))

        shape_cx = (196 if is_left else 884) + slide_off
        card_x0 = (318 if is_left else 88) + slide_off
        card_x1 = (992 if is_left else 762) + slide_off
        card_b = (card_x0, cy - 66, card_x1, cy + 72)

        stage.draw_glass_card(card_b, radius=22, accent_col=col, alpha_mul=a_mul, active=active, layered=(i == n - 1))
        # Badge pill 01..04
        b_cx = card_x0 + 42
        stage.draw_pill(b_cx, cy - 22, f"{i+1:02d}", (*col[:3], 42), world["text"], border_col=(*col[:3], 210), font=_get_font(20, bold=True), alpha_mul=a_mul, pad_x=12, pad_y=4)

        name = str(nd.get("name") or nd.get("title") or nd.get("label") or "").strip()
        sub = str(nd.get("sub") or nd.get("role") or nd.get("desc") or "").strip()
        f_title = _get_font(30, bold=True)
        f_sub = _get_font(22, bold=False)
        tx0 = card_x0 + 82
        max_tw = card_x1 - tx0 - 20
        ny = _draw_wrapped_text(stage.draw, (tx0, cy - 38), name, f_title, _with_alpha(world["text"], a_mul), max_tw, line_gap=4, max_lines=2)
        if sub:
            _draw_wrapped_text(stage.draw, (tx0, ny + 2), sub, f_sub, _with_alpha(world["muted"], a_mul), max_tw, line_gap=4, max_lines=2)

        # Connector stub between prism and card
        stub_x0 = shape_cx + (58 if is_left else -58)
        stub_x1 = card_x0 if is_left else card_x1
        stage.draw.line((stub_x0, cy, stub_x1, cy), fill=_with_alpha((*col[:3], 170), a_mul), width=3)

        rx = int(52 * (0.65 + 0.35 * min(1.12, e_pop)))
        _draw_node_visual(
            stage, shape_cx, cy - 18, rx, int(rx * 0.48), int(rx * 0.72), col, a_mul,
            shape=nd.get("shape", ""), icon=nd.get("icon", ""), label=name,
            active=active, progress=progress, phase=i * 0.7,
        )
        anchors.append((shape_cx, cy + 44))

    # Draw Bezier connections between sequential stages
    for i in range(n - 1):
        g = _spring_gate(progress, i + 1, n, 0.25)
        edge_lbl = ""
        edge_col = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        if i < len(edges) and isinstance(edges[i], dict):
            edge_lbl = str(edges[i].get("label", ""))
            if edges[i].get("color"):
                edge_col = resolve_world_color(world, edges[i].get("color"))
        p0 = (anchors[i][0], anchors[i][1] + 10)
        p3 = (anchors[i + 1][0], anchors[i + 1][1] - 92)
        _draw_bezier_comet(stage, p0, p3, edge_col, reveal=g, progress=progress, phase=i * 0.27, label=edge_lbl, world=world)


def _render_node_graph(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    hub_name = str(data.get("hub_name") or data.get("center") or "CORE ENGINE").strip()
    hub_shape = str(data.get("hub_shape") or "sphere")
    hub_icon = str(data.get("hub_icon") or "")
    sats = list(data.get("satellites") or data.get("nodes") or [])[:6]
    if not sats:
        return

    hub_cx, hub_cy = 540, 865
    hub_col = world["cyan"]
    g_hub = _ease_out_cubic(_clamp01(progress / 0.22))

    # Concentric radar rings behind hub
    for rad in (175, 290, 395):
        stage.draw.ellipse(
            (hub_cx - rad, hub_cy - rad, hub_cx + rad, hub_cy + rad),
            outline=_with_alpha((*hub_col[:3], 46), g_hub),
            width=2,
        )

    # Symmetric grid spots so pills sit in clean open air
    n = len(sats)
    if n <= 4:
        pos_map = [(285, 515), (795, 515), (285, 1215), (795, 1215)]
    else:
        pos_map = [(275, 480), (805, 480), (225, 865), (855, 865), (275, 1245), (805, 1245)]

    for i, sat in enumerate(sats):
        if isinstance(sat, str):
            sat = {"name": sat}
        sx, sy = pos_map[i % len(pos_map)]
        g = _spring_gate(progress, i + 1, n + 1, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, sat.get("color"), _ACCENT_CYCLE[(i + 1) % len(_ACCENT_CYCLE)])
        active = _pulse_wave(progress, i * 0.9) > 0.65

        # Outer-edge Bezier connection (hub edge -> satellite edge)
        dx = sx - hub_cx
        dy = sy - hub_cy
        dist = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / dist, dy / dist
        p0 = (hub_cx + ux * 115, hub_cy + uy * 82)
        p3 = (sx - ux * 105, sy - uy * 84)
        _draw_bezier_comet(stage, p0, p3, col, reveal=g, progress=progress, phase=i * 0.23, label=str(sat.get("edge", "")), curve_bend=26 if i % 2 == 0 else -26, world=world)

        # Satellite card
        cw, ch = 360, 126
        cb = (sx - cw // 2, sy - ch // 2 + 26, sx + cw // 2, sy + ch // 2 + 26)
        stage.draw_glass_card(cb, radius=20, accent_col=col, alpha_mul=a_mul, active=active)
        _draw_node_visual(
            stage, sx, sy - 64, 42, 20, 32, col, a_mul,
            shape=sat.get("shape", ""), icon=sat.get("icon", ""), label=sat.get("name", ""),
            active=active, progress=progress, phase=i * 0.6,
        )
        name = str(sat.get("name") or "").strip()
        role = str(sat.get("role") or sat.get("sub") or "").strip()
        _draw_wrapped_text(stage.draw, (cb[0] + 16, cb[1] + 18), name, _get_font(26, bold=True), _with_alpha(world["text"], a_mul), cw - 32, line_gap=2, align="center", max_lines=2)
        if role:
            _draw_wrapped_text(stage.draw, (cb[0] + 16, cb[1] + 64), role, _get_font(20), _with_alpha(world["muted"], a_mul), cw - 32, line_gap=2, align="center", max_lines=2)

    # Center Hub visual + nameplate
    _draw_node_visual(
        stage, hub_cx, hub_cy - 38, 60, 28, 44, hub_col, g_hub,
        shape=hub_shape, icon=hub_icon, label=hub_name,
        active=True, progress=progress, phase=0.0,
    )
    stage.draw_pill(hub_cx, hub_cy + 58, hub_name[:22], world["card_alt"], world["text"], border_col=(*hub_col[:3], 220), font=_get_font(24, bold=True), alpha_mul=g_hub, pad_x=22, pad_y=10)


def _render_iso_comparison(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    l_lbl = str(data.get("left_label") or data.get("left_title") or "Option A").strip()
    r_lbl = str(data.get("right_label") or data.get("right_title") or "Option B").strip()
    l_pts = [str(x).strip() for x in (data.get("left_points") or data.get("left_items") or []) if str(x).strip()][:5]
    r_pts = [str(x).strip() for x in (data.get("right_points") or data.get("right_items") or []) if str(x).strip()][:5]
    neutral = bool(data.get("neutral_mode", False))

    l_col = world["purple"] if neutral else world["rose"]
    r_col = world["cyan"] if neutral else world["emerald"]
    cols = [(72, 518, l_lbl, l_pts, l_col, data.get("left_shape", "box"), data.get("left_icon", ""), "warn" if not neutral else "check"),
            (558, 1004, r_lbl, r_pts, r_col, data.get("right_shape", "hexagon"), data.get("right_icon", ""), "check")]

    for idx, (x0, x1, title, pts, col, shp, icn, gkind) in enumerate(cols):
        g = _spring_gate(progress, idx, 2, 0.25)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        cx = (x0 + x1) // 2
        card_b = (x0, 448, x1, 1368)
        stage.draw_glass_card(card_b, radius=26, accent_col=col, alpha_mul=a_mul, active=(idx == 1), flip_t=g if g < 0.85 else 1.0, layered=(idx == 1))
        _draw_node_visual(stage, cx, 424, 54, 24, 38, col, a_mul, shape=shp, icon=icn, label=title, active=(idx == 1), progress=progress, phase=idx * 0.9)
        _draw_wrapped_text(stage.draw, (x0 + 22, 520), title, _get_font(31, bold=True), _with_alpha(col, a_mul), (x1 - x0) - 44, align="center", max_lines=2)
        stage.draw.line((x0 + 36, 598, x1 - 36, 598), fill=_with_alpha((*col[:3], 120), a_mul), width=2)

        py = 626
        f_pt = _get_font(23, bold=False)
        for j, pt in enumerate(pts):
            pg = _ease_out_cubic(_clamp01((progress - 0.16 - j * 0.11 - idx * 0.06) / 0.20))
            if pg <= 0.03:
                continue
            draw_vector_glyph(stage, x0 + 44, py + 15, gkind, 15, col, pg * a_mul, with_badge=True)
            next_y = _draw_wrapped_text(stage.draw, (x0 + 74, py), pt, f_pt, _with_alpha(world["text"], pg * a_mul), (x1 - x0) - 96, line_gap=5, max_lines=4)
            py = max(py + 96, next_y + 26)

    if data.get("show_vs", True):
        gv = _ease_out_elastic(_clamp01((progress - 0.12) / 0.24))
        if gv > 0.05:
            stage.add_glow_orb(540, 880, 46, world["amber"], alpha=int(140 * gv))
            stage.draw_pill(540, 880, "VS", world["card_alt"], world["amber"], border_col=world["amber"], font=_get_font(26, bold=True), alpha_mul=gv, pad_x=20, pad_y=12)


def _render_terminal_studio(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    code_raw = str(data.get("code_snippet") or data.get("code") or "").strip("\n")
    out_raw = str(data.get("output") or "").strip()
    lines = code_raw.splitlines()[:14] or ["# ready"]
    term_b = (74, 405, 1006, 1145 if out_raw else 1365)
    g_box = _ease_out_cubic(_clamp01(progress / 0.18))
    stage.draw_glass_card(term_b, radius=26, accent_col=world["cyan"], alpha_mul=g_box, active=True, layered=True)

    # Traffic lights + filename bar
    for k, c in enumerate(((244, 63, 94), (245, 158, 11), (16, 185, 129))):
        stage.draw.ellipse((term_b[0] + 28 + k * 28, term_b[1] + 26, term_b[0] + 44 + k * 28, term_b[1] + 42), fill=_with_alpha(c, g_box))
    fn_label = str(data.get("filename") or "studio_runtime.py")
    stage.draw.text((term_b[0] + 132, term_b[1] + 22), fn_label, font=_get_font(21, bold=True, mono=True), fill=_with_alpha(world["muted"], g_box))
    stage.draw.line((term_b[0] + 20, term_b[1] + 64, term_b[2] - 20, term_b[1] + 64), fill=_with_alpha(world["border"], g_box), width=2)

    f_code = _get_font(24, bold=False, mono=True)
    ty = term_b[1] + 84
    hl_line = int(data.get("highlight_line", -1))
    total_chars = sum(len(l) + 1 for l in lines)
    typed_budget = int(total_chars * _clamp01(progress / 0.72))

    consumed = 0
    for idx, ln in enumerate(lines):
        if consumed >= typed_budget:
            break
        show = ln[: max(0, typed_budget - consumed)]
        consumed += len(ln) + 1
        if idx == hl_line:
            stage.draw.rounded_rectangle((term_b[0] + 18, ty - 4, term_b[2] - 18, ty + 34), radius=10, fill=_with_alpha((*world["amber"][:3], 42), g_box))
        stage.draw.text((term_b[0] + 28, ty), f"{idx+1:2d}", font=f_code, fill=_with_alpha(world["muted"], g_box * 0.7))
        col = world["emerald"] if ln.lstrip().startswith(("#", "//")) else (world["cyan"] if any(kw in ln for kw in ("def ", "async ", "return ", "SELECT ", "import ", "class ")) else world["text"])
        stage.draw.text((term_b[0] + 76, ty), show[:54], font=f_code, fill=_with_alpha(col, g_box))
        ty += 42

    if out_raw:
        go = _ease_out_cubic(_clamp01((progress - 0.65) / 0.25))
        if go > 0.03:
            out_b = (94, 1175, 986, 1375)
            stage.draw_glass_card(out_b, radius=20, accent_col=world["emerald"], alpha_mul=go, active=True)
            stage.draw_pill(out_b[0] + 92, out_b[1] + 28, "STDOUT", (*world["emerald"][:3], 40), world["emerald"], border_col=world["emerald"], font=_get_font(18, bold=True), alpha_mul=go, pad_x=12, pad_y=4)
            _draw_wrapped_text(stage.draw, (out_b[0] + 28, out_b[1] + 62), out_raw, _get_font(23, mono=True), _with_alpha(world["emerald"], go), (out_b[2] - out_b[0]) - 56, max_lines=3)


def _render_kinetic_statement(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    kicker = str(data.get("kicker") or "").strip()
    stmt = str(data.get("statement") or data.get("title") or "").strip()
    hl = str(data.get("highlight_word") or "").strip()
    tags = [str(t).strip() for t in (data.get("bottom_tags") or []) if str(t).strip()][:4]

    g_card = _ease_out_cubic(_clamp01(progress / 0.22))
    stage.draw_glass_card((80, 480, 1000, 1255), radius=32, accent_col=world["cyan"], alpha_mul=g_card, active=True, layered=True)

    # Decorative flanking 3D shapes floating harmoniously inside card margins
    flank_s = str(data.get("shape") or "hexagon")
    _draw_node_visual(stage, 162, 540, 42, 20, 32, world["purple"], g_card * 0.9, shape=flank_s, active=True, progress=progress, phase=0.2)
    _draw_node_visual(stage, 918, 1185, 42, 20, 32, world["amber"], g_card * 0.9, shape=data.get("secondary_shape", "diamond"), active=True, progress=progress, phase=1.8)

    if kicker:
        gk = _ease_out_elastic(_clamp01((progress - 0.05) / 0.25))
        stage.draw_pill(540, 560, kicker.upper()[:28], (*world["amber"][:3], 42), world["amber"], border_col=world["amber"], font=_get_font(23, bold=True), alpha_mul=gk, pad_x=22, pad_y=9)

    gs = _ease_out_cubic(_clamp01((progress - 0.14) / 0.30))
    if gs > 0.03:
        f_main = _get_font(54, bold=True)
        cy = 655
        if hl and hl.lower() in stmt.lower():
            idx = stmt.lower().index(hl.lower())
            before = stmt[:idx].strip()
            exact_hl = stmt[idx:idx + len(hl)]
            after = stmt[idx + len(hl):].strip()
            if before:
                cy = _draw_wrapped_text(stage.draw, (124, cy), before, f_main, _with_alpha(world["text"], gs), 832, line_gap=10, align="center", max_lines=3) + 14
            stage.add_glow_orb(540, cy + 44, 150, world["cyan"], alpha=int(130 * gs))
            cy = _draw_wrapped_text(stage.draw, (124, cy), exact_hl, _get_font(66, bold=True), _with_alpha(world["cyan"], gs), 832, line_gap=10, align="center", max_lines=2) + 14
            if after:
                _draw_wrapped_text(stage.draw, (124, cy), after, f_main, _with_alpha(world["text"], gs), 832, line_gap=10, align="center", max_lines=3)
        else:
            _draw_wrapped_text(stage.draw, (124, cy + 40), stmt, f_main, _with_alpha(world["text"], gs), 832, line_gap=12, align="center", max_lines=5)

    if tags:
        tx = 540 - (len(tags) * 205) // 2 + 100
        for i, tg in enumerate(tags):
            gt = _ease_out_cubic(_spring_gate(progress, i + 1, len(tags) + 1, 0.25))
            col = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_pill(tx + i * 205, 1320, tg[:16], (*col[:3], 36), world["text"], border_col=(*col[:3], 185), font=_get_font(21, bold=True), alpha_mul=gt, pad_x=16, pad_y=8)


def _render_custom_scene(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    blocks = data.get("blocks") or []
    if not blocks:
        _render_kinetic_statement(stage, data, progress, world)
        return
    y = STAGE_Y0 + 14
    n = len(blocks)
    for idx, blk in enumerate(blocks[:5]):
        if y > STAGE_Y1 - 95:
            break
        if isinstance(blk, str):
            blk = {"type": "question_card", "text": blk}
        btype = str(blk.get("type") or blk.get("block") or "question_card").lower().strip()
        g = _spring_gate(progress, idx, n, 0.25)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, blk.get("color"), _ACCENT_CYCLE[idx % len(_ACCENT_CYCLE)])
        slide_y = int((1.0 - a_mul) * 22)

        if btype == "big_stat":
            h = 198
            b = (84, y + slide_y, 996, y + slide_y + h)
            stage.draw_glass_card(b, radius=26, accent_col=col, alpha_mul=a_mul, active=True, layered=True)
            val_txt = _animate_counter_text(blk.get("value", "0"), _clamp01((progress - 0.12) / 0.55))
            _draw_wrapped_text(stage.draw, (110, b[1] + 24), val_txt, _get_font(76, bold=True), _with_alpha(col, a_mul), 860, align="center", max_lines=1)
            _draw_wrapped_text(stage.draw, (110, b[1] + 122), str(blk.get("label", "")), _get_font(27, bold=True), _with_alpha(world["text"], a_mul), 860, align="center", max_lines=2)
            y += h + 24

        elif btype == "question_card":
            txt = str(blk.get("text") or blk.get("title") or "").strip()
            lines_n = min(4, _est_lines(txt, _get_font(31, bold=True), 830))
            h = max(116, 48 + lines_n * 42)
            b = (84, y + slide_y, 996, y + slide_y + h)
            stage.draw_glass_card(b, radius=24, accent_col=col, alpha_mul=a_mul, flip_t=g if g < 0.85 else 1.0)
            _draw_wrapped_text(stage.draw, (124, b[1] + 24), txt, _get_font(31, bold=True), _with_alpha(world["text"], a_mul), 830, line_gap=8, align="center", max_lines=4)
            y += h + 22

        elif btype == "pills":
            items = [str(p).strip() for p in (blk.get("items") or []) if str(p).strip()][:5]
            if items:
                cols_p = min(3, max(2, len(items)))
                pw = (912 - (cols_p - 1) * 16) // cols_p
                for j, ptxt in enumerate(items):
                    r_i, c_i = divmod(j, cols_p)
                    pcx = 84 + c_i * (pw + 16) + pw // 2
                    pcy = y + slide_y + 34 + r_i * 78
                    pc = resolve_world_color(world, _ACCENT_CYCLE[(idx + j) % len(_ACCENT_CYCLE)])
                    stage.draw_pill(pcx, pcy, ptxt[:18], (*pc[:3], 34), world["text"], border_col=(*pc[:3], 185), font=_get_font(22, bold=True), alpha_mul=a_mul, pad_x=18, pad_y=10)
                rows_n = (len(items) + cols_p - 1) // cols_p
                y += rows_n * 78 + 20

        elif btype == "flow_chain":
            steps = [str(s).strip() for s in (blk.get("steps") or []) if str(s).strip()][:4]
            if steps:
                m = len(steps)
                bw = (912 - (m - 1) * 34) // m
                for j, st in enumerate(steps):
                    sx0 = 84 + j * (bw + 34)
                    sc = resolve_world_color(world, _ACCENT_CYCLE[j % len(_ACCENT_CYCLE)])
                    stage.draw_glass_card((sx0, y + slide_y, sx0 + bw, y + slide_y + 106), radius=18, accent_col=sc, alpha_mul=a_mul, active=(int(progress * m) == j))
                    _draw_wrapped_text(stage.draw, (sx0 + 10, y + slide_y + 24), st, _get_font(21, bold=True), _with_alpha(world["text"], a_mul), bw - 20, align="center", max_lines=3)
                    if j < m - 1:
                        _draw_bezier_comet(stage, (sx0 + bw + 2, y + slide_y + 53), (sx0 + bw + 32, y + slide_y + 53), sc, reveal=a_mul, progress=progress, phase=j * 0.3, world=world)
                y += 130

        elif btype == "list_cards":
            items = (blk.get("items") or [])[:5]
            for j, it in enumerate(items):
                if y > STAGE_Y1 - 95:
                    break
                if isinstance(it, str):
                    it = {"title": it}
                ig = _ease_out_cubic(_clamp01((progress - idx * 0.08 - j * 0.10) / 0.22))
                if ig <= 0.03:
                    continue
                ic = resolve_world_color(world, it.get("color"), _ACCENT_CYCLE[j % len(_ACCENT_CYCLE)])
                title = str(it.get("title") or it.get("name") or "").strip()
                sub = str(it.get("sub") or it.get("desc") or "").strip()
                h = 104 if sub else 78
                b = (84, y, 996, y + h)
                stage.draw_glass_card(b, radius=20, accent_col=ic, alpha_mul=ig, active=(j == int(progress * len(items))))
                icon_kind = str(it.get("icon") or "check")
                if ":" in icon_kind or icon_kind.lower() in ICON_ALIASES:
                    im = _resolve_iconify_if_any(icon_kind, ic, 48)
                    if im:
                        stage.fg.alpha_composite(im.resize((44, 44)), (110, y + (h - 44) // 2))
                    else:
                        draw_vector_glyph(stage, 132, y + h // 2, "check", 20, ic, ig)
                else:
                    draw_vector_glyph(stage, 132, y + h // 2, icon_kind, 20, ic, ig)
                _draw_wrapped_text(stage.draw, (182, y + (16 if sub else 22)), title, _get_font(26, bold=True), _with_alpha(world["text"], ig), 785, max_lines=1)
                if sub:
                    _draw_wrapped_text(stage.draw, (182, y + 54), sub, _get_font(21), _with_alpha(world["muted"], ig), 785, max_lines=1)
                y += h + 16

        elif btype == "banner":
            txt = str(blk.get("text") or "").strip()
            h = 88
            stage.draw_glass_card((84, y + slide_y, 996, y + slide_y + h), radius=20, accent_col=col, alpha_mul=a_mul, active=True)
            _draw_wrapped_text(stage.draw, (114, y + slide_y + 24), txt, _get_font(26, bold=True), _with_alpha(col, a_mul), 852, align="center", max_lines=2)
            y += h + 20

        elif btype == "code":
            txt = str(blk.get("text") or blk.get("code") or "").strip()
            clines = txt.splitlines()[:4]
            h = 46 + len(clines) * 34
            stage.draw_glass_card((84, y + slide_y, 996, y + slide_y + h), radius=18, accent_col=col, alpha_mul=a_mul)
            for k, cl in enumerate(clines):
                stage.draw.text((114, y + slide_y + 22 + k * 34), cl[:56], font=_get_font(22, mono=True), fill=_with_alpha(col, a_mul))
            y += h + 20


# =========================================================================
# LAYOUT FAMILY 2: SPATIAL COMPOSER & AI MULTI-LAYER <svg> RENDERER
# =========================================================================
def _render_spatial_canvas(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    """
    Spatial Composer: accepts freeform normalized elements (`x, y, w, h` inside 0..1000 canvas)
    plus semantic `connections` (`from` -> `to`) so AI can compose novel spatial diagrams on demand.
    """
    elems = list(data.get("elements") or data.get("zones") or data.get("nodes") or [])[:10]
    conns = list(data.get("connections") or data.get("edges") or [])
    if not elems:
        return

    box_map: Dict[str, Tuple[int, int, int, int]] = {}
    n = len(elems)
    cols = 2 if n <= 4 else 3

    for i, el in enumerate(elems):
        if isinstance(el, str):
            el = {"id": f"e{i}", "type": "card", "title": el}
        eid = str(el.get("id") or el.get("name") or f"e{i}")
        # Support normalized 0..1000 coordinates or automatic clean grid fallback
        if all(k in el for k in ("x", "y", "w", "h")):
            nx, ny, nw, nh = float(el["x"]), float(el["y"]), float(el["w"]), float(el["h"])
            x0 = int(STAGE_X0 + (nx / 1000.0) * STAGE_W)
            y0 = int(STAGE_Y0 + (ny / 1000.0) * STAGE_H)
            bw = max(140, int((nw / 1000.0) * STAGE_W))
            bh = max(90, int((nh / 1000.0) * STAGE_H))
        else:
            r_i, c_i = divmod(i, cols)
            rows_n = max(1, (n + cols - 1) // cols)
            bw = (STAGE_W - (cols - 1) * 26) // cols
            bh = min(280, (STAGE_H - (rows_n - 1) * 26) // rows_n)
            x0 = STAGE_X0 + c_i * (bw + 26)
            y0 = STAGE_Y0 + 30 + r_i * (bh + 26)
        b = (max(STAGE_X0, x0), max(STAGE_Y0, y0), min(STAGE_X1, x0 + bw), min(STAGE_Y1, y0 + bh))
        box_map[eid] = b

    # Render connections behind foreground cards/shapes
    for i, cn in enumerate(conns):
        if not isinstance(cn, dict):
            continue
        b0 = box_map.get(str(cn.get("from", "")))
        b1 = box_map.get(str(cn.get("to", "")))
        if not b0 or not b1:
            continue
        p0 = ((b0[0] + b0[2]) * 0.5, (b0[1] + b0[3]) * 0.5)
        p3 = ((b1[0] + b1[2]) * 0.5, (b1[1] + b1[3]) * 0.5)
        gc = _spring_gate(progress, i + 1, max(2, len(conns)), 0.25)
        cc = resolve_world_color(world, cn.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        _draw_bezier_comet(stage, p0, p3, cc, reveal=gc, progress=progress, phase=i * 0.22, label=str(cn.get("label", "")), world=world)

    # Render spatial elements
    for i, el in enumerate(elems):
        if isinstance(el, str):
            el = {"id": f"e{i}", "type": "card", "title": el}
        eid = str(el.get("id") or el.get("name") or f"e{i}")
        b = box_map[eid]
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        etype = str(el.get("type") or "card").lower().strip()
        col = resolve_world_color(world, el.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        title = str(el.get("title") or el.get("label") or el.get("name") or "").strip()
        sub = str(el.get("sub") or el.get("desc") or "").strip()
        cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
        bw, bh = b[2] - b[0], b[3] - b[1]

        if etype in ("shape", "svg_icon"):
            rx = min(72, max(36, bw // 3))
            _draw_node_visual(stage, cx, cy - 18, rx, int(rx * 0.48), int(rx * 0.72), col, a_mul, shape=el.get("shape", ""), icon=el.get("icon", ""), label=title, active=(i == int(progress * n)), progress=progress, phase=i * 0.5)
            if title:
                stage.draw_pill(cx, min(b[3] - 18, cy + rx + 26), title[:24], world["card_alt"], world["text"], border_col=(*col[:3], 200), font=_get_font(21, bold=True), alpha_mul=a_mul, pad_x=14, pad_y=6)
        elif etype == "stat":
            stage.draw_glass_card(b, radius=22, accent_col=col, alpha_mul=a_mul, active=True)
            val_txt = _animate_counter_text(el.get("value", title), _clamp01((progress - 0.12) / 0.55))
            _draw_wrapped_text(stage.draw, (b[0] + 16, b[1] + 22), val_txt, _get_font(min(58, max(34, bh // 3)), bold=True), _with_alpha(col, a_mul), bw - 32, align="center", max_lines=1)
            if title and str(el.get("value", "")):
                _draw_wrapped_text(stage.draw, (b[0] + 16, b[3] - 58), title, _get_font(22, bold=True), _with_alpha(world["text"], a_mul), bw - 32, align="center", max_lines=2)
        elif etype == "code":
            stage.draw_glass_card(b, radius=20, accent_col=col, alpha_mul=a_mul, active=False)
            code_txt = str(el.get("code") or title)
            for k, cl in enumerate(code_txt.splitlines()[:max(2, (bh - 36) // 30)]):
                stage.draw.text((b[0] + 20, b[1] + 20 + k * 30), cl[:max(16, bw // 14)], font=_get_font(20, mono=True), fill=_with_alpha(col, a_mul))
        else:
            stage.draw_glass_card(b, radius=22, accent_col=col, alpha_mul=a_mul, active=(int(progress * n) == i))
            if el.get("icon") or el.get("shape"):
                _draw_node_visual(stage, b[0] + 46, b[1] + 46, 26, 12, 18, col, a_mul, shape=el.get("shape", ""), icon=el.get("icon", ""), label=title, progress=progress)
                tx_off = 88
            else:
                tx_off = 22
            _draw_wrapped_text(stage.draw, (b[0] + tx_off, b[1] + 22), title, _get_font(25, bold=True), _with_alpha(world["text"], a_mul), bw - tx_off - 18, line_gap=4, max_lines=3)
            if sub:
                _draw_wrapped_text(stage.draw, (b[0] + 22, b[1] + 78), sub, _get_font(20), _with_alpha(world["muted"], a_mul), bw - 44, line_gap=4, max_lines=4)


def _render_svg_scene(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    """
    AI Keyframe Multi-Layer <svg> Renderer: pre-rasterizes `<svg>` stage layers via Rust resvg_py
    and drives per-layer scale, rotate, float, pulse & slide transforms smoothly at 30fps.
    """
    svg_code = str(data.get("svg") or data.get("svg_code") or "").strip()
    layer_objs = prepare_keyframed_svg_layers(svg_code, width=880, height=840) if svg_code else []
    if not layer_objs:
        if data.get("nodes"):
            _render_iso_architecture(stage, data, progress, world)
        else:
            _render_kinetic_statement(stage, data, progress, world)
        return

    caption = str(data.get("caption") or data.get("summary") or "").strip()
    frame_h = 890 if caption else 990
    frame_b = (70, STAGE_Y0 + 18, 1010, STAGE_Y0 + 18 + frame_h)
    g_frame = _ease_out_cubic(_clamp01(progress / 0.16))
    stage.draw_glass_card(frame_b, radius=28, accent_col=world["cyan"], alpha_mul=g_frame, active=True, layered=True)

    anim_specs = {}
    for a_item in (data.get("svg_animations") or []):
        if isinstance(a_item, dict) and a_item.get("target"):
            anim_specs[str(a_item["target"]).lower()] = a_item

    n = len(layer_objs)
    ox = (1080 - layer_objs[0]["image"].width) // 2
    oy = frame_b[1] + (frame_h - layer_objs[0]["image"].height) // 2
    for i, item in enumerate(layer_objs):
        gid = str(item.get("id", f"stage_{i+1}")).lower()
        lay = item["image"]
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g) * stage.t_alpha
        if a_mul <= 0.03:
            continue

        spec = anim_specs.get(gid, {})
        dy_enter = int((1.0 - _micro_bounce(g)) * 28)
        float_amp = float(spec.get("float_amp", 6.0 if i == n - 1 else 0.0))
        dy_float = int(math.sin(progress * math.pi * 4.0 + i) * float_amp)
        dx_slide = int(float(spec.get("dx", 0.0)) * (1.0 - _ease_out_cubic(g)))
        dy_slide = int(float(spec.get("dy", 0.0)) * (1.0 - _ease_out_cubic(g)))

        im = lay.copy()
        rot_deg = float(spec.get("rotate_deg", 0.0)) * _ease_out_cubic(g)
        if abs(rot_deg) > 0.2:
            im = im.rotate(-rot_deg, resample=Image.Resampling.BILINEAR)

        sc_from = float(spec.get("scale_from", 1.0))
        sc_pulse = 0.04 * math.sin(progress * math.pi * 6.0) if spec.get("pulse") else 0.0
        sc = (sc_from + (1.0 - sc_from) * _ease_out_cubic(g)) + sc_pulse
        if abs(sc - 1.0) > 0.01:
            nw, nh = max(32, int(im.width * sc)), max(32, int(im.height * sc))
            im = im.resize((nw, nh), Image.Resampling.BILINEAR)
            px = ox + (lay.width - nw) // 2 + dx_slide
            py = oy + (lay.height - nh) // 2 + dy_enter + dy_slide + dy_float
        else:
            px, py = ox + dx_slide, oy + dy_enter + dy_slide + dy_float

        if a_mul < 0.99:
            alpha_ch = im.split()[3].point(lambda p: int(p * a_mul))
            im.putalpha(alpha_ch)
        # Clip cleanly inside frame bounds
        x_paste = max(frame_b[0] + 4, px)
        y_paste = max(frame_b[1] + 4, py)
        stage.fg.alpha_composite(im, (x_paste, y_paste))

    if caption:
        gc = _ease_out_cubic(_clamp01((progress - 0.35) / 0.28))
        cb = (84, frame_b[3] + 22, 996, min(STAGE_Y1 - 12, frame_b[3] + 132))
        stage.draw_glass_card(cb, radius=20, accent_col=world["purple"], alpha_mul=gc)
        _draw_wrapped_text(stage.draw, (cb[0] + 26, cb[1] + 22), caption, _get_font(24, bold=True), _with_alpha(world["text"], gc), (cb[2] - cb[0]) - 52, align="center", max_lines=2)


# =========================================================================
# LAYOUT FAMILY 3: SPECIALIZED SYSTEM & TECHNICAL DIAGRAM RENDERERS (25+)
# =========================================================================
def _render_layer_stack_3d(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    layers = list(data.get("layers") or data.get("nodes") or data.get("items") or [])[:5]
    if not layers:
        return
    n = len(layers)
    start_y = STAGE_Y0 + 60
    step_y = min(195, (STAGE_H - 90) // max(1, n))
    for i, lay in enumerate(layers):
        if isinstance(lay, str):
            lay = {"name": lay}
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, lay.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        cy = start_y + i * step_y + 72
        dy = int((1.0 - _micro_bounce(g)) * 42)
        active = (int(progress * n) == i)

        # Left 3D isometric wafer/slab + Right glass explanation card
        slab_cx = 235
        draw_3d_shape(stage, slab_cx, cy + dy - 18, 125, 44, 34, col, a_mul, shape=lay.get("shape", "layers_wafer"), active=active, progress=progress, phase=i * 0.5)
        stage.draw_pill(slab_cx, cy + dy - 20, f"L{n - i}", world["card_alt"], world["text"], border_col=col, font=_get_font(20, bold=True), alpha_mul=a_mul, pad_x=14, pad_y=4)

        cb = (395, cy + dy - 56, 998, cy + dy + 68)
        stage.draw_glass_card(cb, radius=20, accent_col=col, alpha_mul=a_mul, active=active)
        stage.draw.line((365, cy + dy, 395, cy + dy), fill=_with_alpha((*col[:3], 190), a_mul), width=3)
        name = str(lay.get("name") or lay.get("title") or "").strip()
        sub = str(lay.get("sub") or lay.get("role") or lay.get("desc") or "").strip()
        _draw_wrapped_text(stage.draw, (cb[0] + 24, cb[1] + 18), name, _get_font(27, bold=True), _with_alpha(world["text"], a_mul), cb[2] - cb[0] - 48, max_lines=1)
        if sub:
            _draw_wrapped_text(stage.draw, (cb[0] + 24, cb[1] + 60), sub, _get_font(21), _with_alpha(world["muted"], a_mul), cb[2] - cb[0] - 48, max_lines=2)


def _render_pyramid_or_funnel(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any], is_funnel: bool = False) -> None:
    tiers = list(data.get("tiers") or data.get("stages") or data.get("items") or [])[:5]
    if not tiers:
        return
    n = len(tiers)
    tier_h = min(155, (STAGE_H - 120) // max(1, n))
    y_start = STAGE_Y0 + 60
    for i, tr in enumerate(tiers):
        if isinstance(tr, str):
            tr = {"name": tr}
        g = _spring_gate(progress, i, n, 0.25)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, tr.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        frac_top = (1.0 - i / max(1, n)) if is_funnel else ((i + 0.45) / max(1, n))
        frac_bot = (1.0 - (i + 0.85) / max(1, n)) if is_funnel else ((i + 1.15) / max(1, n))
        w_top = max(140, int(440 * max(0.28, frac_top)))
        w_bot = max(120, int(440 * max(0.24, frac_bot)))
        cx = 290
        y0 = y_start + i * (tier_h + 14)
        y1 = y0 + tier_h - 14
        pts = [(cx - w_top // 2, y0), (cx + w_top // 2, y0), (cx + w_bot // 2, y1), (cx - w_bot // 2, y1)]
        stage.add_glow_orb(cx, (y0 + y1) // 2, w_top // 2, col, alpha=int(85 * a_mul))
        stage.draw.polygon(pts, fill=_with_alpha((*col[:3], 178), a_mul), outline=_with_alpha(world["glass_rim"], a_mul), width=2)

        val = str(tr.get("value") or tr.get("metric") or "").strip()
        if val:
            stage.draw_pill(cx, (y0 + y1) // 2, val[:14], world["card_alt"], world["text"], border_col=col, font=_get_font(21, bold=True), alpha_mul=a_mul, pad_x=12, pad_y=4)

        cb = (545, y0 + 4, 1004, y1 - 4)
        stage.draw_glass_card(cb, radius=18, accent_col=col, alpha_mul=a_mul, active=(int(progress * n) == i))
        stage.draw.line((cx + (w_top + w_bot) // 4, (y0 + y1) // 2, cb[0], (y0 + y1) // 2), fill=_with_alpha(col, a_mul), width=3)
        name = str(tr.get("name") or tr.get("title") or "").strip()
        sub = str(tr.get("sub") or tr.get("desc") or "").strip()
        _draw_wrapped_text(stage.draw, (cb[0] + 20, y0 + 18), name, _get_font(25, bold=True), _with_alpha(world["text"], a_mul), cb[2] - cb[0] - 40, max_lines=1)
        if sub:
            _draw_wrapped_text(stage.draw, (cb[0] + 20, y0 + 56), sub, _get_font(20), _with_alpha(world["muted"], a_mul), cb[2] - cb[0] - 40, max_lines=2)


def _render_grid_2x2(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any], is_matrix: bool = False) -> None:
    cells = list(data.get("quadrants") or data.get("stats") or data.get("cards") or data.get("items") or [])[:4]
    if not cells:
        return
    pad_top = 80 if is_matrix else 40
    cw, ch = 442, (STAGE_H - pad_top - 70) // 2
    x_cols = [STAGE_X0 + 20, STAGE_X0 + 20 + cw + 28]
    y_rows = [STAGE_Y0 + pad_top, STAGE_Y0 + pad_top + ch + 28]

    if is_matrix:
        gx = _ease_out_cubic(_clamp01(progress / 0.18))
        x_mid = 540
        y_mid = STAGE_Y0 + pad_top + ch + 14
        stage.draw.line((STAGE_X0 + 12, y_mid, STAGE_X1 - 12, y_mid), fill=_with_alpha(world["border"], gx), width=3)
        stage.draw.line((x_mid, STAGE_Y0 + 36, x_mid, STAGE_Y1 - 16), fill=_with_alpha(world["border"], gx), width=3)
        x_axis = str(data.get("x_axis") or "").strip()
        y_axis = str(data.get("y_axis") or "").strip()
        if y_axis:
            stage.draw_pill(x_mid, STAGE_Y0 + 24, y_axis[:28], world["card_alt"], world["cyan"], border_col=world["cyan"], font=_get_font(20, bold=True), alpha_mul=gx)
        if x_axis:
            stage.draw_pill(STAGE_X1 - 110, y_mid, x_axis[:20], world["card_alt"], world["purple"], border_col=world["purple"], font=_get_font(20, bold=True), alpha_mul=gx)

    for i, cell in enumerate(cells):
        if isinstance(cell, str):
            cell = {"title": cell}
        r_i, c_i = divmod(i, 2)
        b = (x_cols[c_i], y_rows[r_i], x_cols[c_i] + cw, y_rows[r_i] + ch)
        g = _spring_gate(progress, i, len(cells), 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, cell.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        active = bool(cell.get("highlight")) or (int(progress * 4) == i)
        stage.draw_glass_card(b, radius=24, accent_col=col, alpha_mul=a_mul, active=active, flip_t=g if g < 0.85 else 1.0, layered=active)

        val = str(cell.get("value") or "").strip()
        title = str(cell.get("title") or cell.get("label") or "").strip()
        sub = str(cell.get("sub") or cell.get("desc") or "").strip()
        if val and not is_matrix:
            anim_v = _animate_counter_text(val, _clamp01((progress - 0.10) / 0.55))
            _draw_wrapped_text(stage.draw, (b[0] + 24, b[1] + 44), anim_v, _get_font(56, bold=True), _with_alpha(col, a_mul), cw - 48, align="center", max_lines=1)
            _draw_wrapped_text(stage.draw, (b[0] + 24, b[1] + 132), title, _get_font(28, bold=True), _with_alpha(world["text"], a_mul), cw - 48, align="center", max_lines=2)
            if sub:
                _draw_wrapped_text(stage.draw, (b[0] + 24, b[1] + 218), sub, _get_font(21), _with_alpha(world["muted"], a_mul), cw - 48, align="center", max_lines=3)
        else:
            if cell.get("icon") or cell.get("shape"):
                _draw_node_visual(stage, b[0] + cw // 2, b[1] + 74, 38, 18, 26, col, a_mul, shape=cell.get("shape", ""), icon=cell.get("icon", ""), label=title, active=active, progress=progress, phase=i * 0.6)
                ty = b[1] + 150
            else:
                stage.draw_pill(b[0] + 84, b[1] + 42, f"Q{i+1}", (*col[:3], 40), col, border_col=col, font=_get_font(20, bold=True), alpha_mul=a_mul, pad_x=14, pad_y=4)
                ty = b[1] + 84
            _draw_wrapped_text(stage.draw, (b[0] + 24, ty), title, _get_font(28, bold=True), _with_alpha(world["text"], a_mul), cw - 48, align="center", max_lines=2)
            if sub:
                _draw_wrapped_text(stage.draw, (b[0] + 24, ty + 78), sub, _get_font(21), _with_alpha(world["muted"], a_mul), cw - 48, align="center", max_lines=4)


def _render_benchmark_3d(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    bars = list(data.get("bars") or data.get("metrics") or data.get("items") or [])[:6]
    if not bars:
        return
    n = len(bars)
    vals = []
    for b in bars:
        try:
            vals.append(float(b.get("score") or b.get("value_num") or re.sub(r"[^0-9.]", "", str(b.get("value", "50"))) or 50))
        except Exception:
            vals.append(50.0)
    max_v = max([v for v in vals if v > 0] + [1.0])

    row_h = min(155, (STAGE_H - 60) // max(1, n))
    y0 = STAGE_Y0 + 34
    for i, b_item in enumerate(bars):
        if isinstance(b_item, str):
            b_item = {"label": b_item, "value": "100"}
        g = _spring_gate(progress, i, n, 0.28)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, b_item.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        ry = y0 + i * row_h
        lbl = str(b_item.get("label") or b_item.get("name") or "").strip()
        val_disp = _animate_counter_text(str(b_item.get("value") or int(vals[i])), g)

        stage.draw_glass_card((76, ry, 1004, ry + row_h - 18), radius=20, accent_col=col, alpha_mul=a_mul, active=(vals[i] == max_v))
        stage.draw.text((108, ry + 18), lbl[:34], font=_get_font(26, bold=True), fill=_with_alpha(world["text"], a_mul))
        _draw_wrapped_text(stage.draw, (760, ry + 18), val_disp, _get_font(27, bold=True), _with_alpha(col, a_mul), 215, align="right", max_lines=1)

        # 3D Isometric extruded bar
        bx0, by0, bx_max = 108, ry + 64, 966
        bw = max(28, int((bx_max - bx0) * (vals[i] / max_v) * _ease_out_cubic(g)))
        bh = 34
        stage.draw.rounded_rectangle((bx0, by0, bx_max, by0 + bh), radius=12, fill=_with_alpha(world["card_layer"], a_mul))
        stage.add_glow_orb(bx0 + bw - 12, by0 + bh // 2, 26, col, alpha=int(120 * a_mul))
        stage.draw.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=12, fill=_with_alpha(col, a_mul))
        # Top highlights give instant 3D bar bevel
        stage.draw.line((bx0 + 10, by0 + 4, max(bx0 + 12, bx0 + bw - 10), by0 + 4), fill=_with_alpha((255, 255, 255, 165), a_mul), width=3)


def _render_radial_gauge(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    pct = float(data.get("percent") or data.get("score") or 85)
    pct = max(0.0, min(100.0, pct))
    g_arc = _ease_out_cubic(_clamp01(progress / 0.55))
    cx, cy, rad = 540, 680, 225
    ac = resolve_world_color(world, data.get("color"), "emerald" if pct >= 70 else ("amber" if pct >= 40 else "rose"))

    stage.draw_glass_card((100, STAGE_Y0 + 16, 980, 965), radius=30, accent_col=ac, alpha_mul=_clamp01(progress / 0.18), active=True, layered=True)
    # Background track + Animated Gauge Arc
    bbox = (cx - rad, cy - rad, cx + rad, cy + rad)
    stage.draw.arc(bbox, start=135, end=405, fill=_with_alpha(world["card_layer"], stage.t_alpha), width=34)
    sweep = int(270 * (pct / 100.0) * g_arc)
    if sweep > 2:
        stage.add_glow_orb(cx, cy, rad + 18, ac, alpha=int(95 * g_arc))
        stage.draw.arc(bbox, start=135, end=135 + sweep, fill=_with_alpha(ac, stage.t_alpha), width=34)

    val_label = _animate_counter_text(str(data.get("value") or f"{int(pct)}%"), g_arc)
    _draw_wrapped_text(stage.draw, (cx - 180, cy - 58), val_label, _get_font(74, bold=True), _with_alpha(world["text"], stage.t_alpha), 360, align="center", max_lines=1)
    lbl = str(data.get("label") or data.get("subtitle") or "SCORE").strip()
    _draw_wrapped_text(stage.draw, (cx - 180, cy + 36), lbl, _get_font(25, bold=True), _with_alpha(ac, stage.t_alpha), 360, align="center", max_lines=2)

    sub_cards = list(data.get("metrics") or data.get("items") or [])[:3]
    if sub_cards:
        cw = (880 - 2 * 20) // len(sub_cards)
        for i, sc in enumerate(sub_cards):
            if isinstance(sc, str):
                sc = {"label": sc, "value": ""}
            g = _spring_gate(progress, i + 1, len(sub_cards) + 1, 0.25)
            a_mul = _ease_out_cubic(g)
            sx0 = 100 + i * (cw + 20)
            cc = resolve_world_color(world, sc.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((sx0, 995, sx0 + cw, 1295), radius=22, accent_col=cc, alpha_mul=a_mul)
            _draw_wrapped_text(stage.draw, (sx0 + 14, 1035), _animate_counter_text(sc.get("value", ""), g), _get_font(40, bold=True), _with_alpha(cc, a_mul), cw - 28, align="center", max_lines=1)
            _draw_wrapped_text(stage.draw, (sx0 + 14, 1110), str(sc.get("label") or sc.get("title") or ""), _get_font(23, bold=True), _with_alpha(world["text"], a_mul), cw - 28, align="center", max_lines=3)


def _render_sql_or_diff_or_api(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any], mode: str) -> None:
    g = _ease_out_cubic(_clamp01(progress / 0.20))
    if mode == "sql":
        query = str(data.get("query") or data.get("sql") or data.get("code_snippet") or "SELECT * FROM events LIMIT 5;")
        tbl = data.get("table_data") if isinstance(data.get("table_data"), dict) else {}
        rows = list(data.get("rows") or tbl.get("rows") or [])[:5]
        cols = list(data.get("columns") or tbl.get("headers") or [])[:5]
        qb = (74, STAGE_Y0 + 12, 1006, STAGE_Y0 + 235)
        stage.draw_glass_card(qb, radius=22, accent_col=world["cyan"], alpha_mul=g, active=True)
        for k, line in enumerate(query.splitlines()[:4]):
            stage.draw.text((qb[0] + 28, qb[1] + 24 + k * 38), line[:54], font=_get_font(23, bold=True, mono=True), fill=_with_alpha(world["cyan"], g))

        tb = (74, qb[3] + 28, 1006, STAGE_Y1 - 24)
        stage.draw_glass_card(tb, radius=22, accent_col=world["emerald"], alpha_mul=g)
        if cols:
            cw = (tb[2] - tb[0] - 40) // len(cols)
            for c_i, c_name in enumerate(cols):
                stage.draw.text((tb[0] + 26 + c_i * cw, tb[1] + 24), str(c_name)[:14], font=_get_font(22, bold=True), fill=_with_alpha(world["emerald"], g))
            stage.draw.line((tb[0] + 20, tb[1] + 66, tb[2] - 20, tb[1] + 66), fill=_with_alpha(world["border"], g), width=2)
        for r_i, row in enumerate(rows):
            rg = _spring_gate(progress, r_i + 1, max(2, len(rows) + 1), 0.22)
            if rg <= 0.03:
                continue
            ry = tb[1] + 84 + r_i * 74
            vals = list(row) if isinstance(row, (list, tuple)) else [str(row)]
            cw = (tb[2] - tb[0] - 40) // max(1, len(vals))
            if r_i == int(data.get("highlight_row", 0)):
                stage.draw.rounded_rectangle((tb[0] + 18, ry - 8, tb[2] - 18, ry + 50), radius=12, fill=_with_alpha((*world["emerald"][:3], 36), rg))
            for c_i, v in enumerate(vals):
                stage.draw.text((tb[0] + 26 + c_i * cw, ry + 6), str(v)[:14], font=_get_font(22, mono=True), fill=_with_alpha(world["text"], rg))

    elif mode == "diff":
        before = str(data.get("before") or "").splitlines()[:8]
        after = str(data.get("after") or "").splitlines()[:8]
        b0 = (74, STAGE_Y0 + 10, 1006, STAGE_Y0 + 485)
        b1 = (74, STAGE_Y0 + 515, 1006, STAGE_Y1 - 24)
        stage.draw_glass_card(b0, radius=22, accent_col=world["rose"], alpha_mul=g)
        stage.draw_pill(b0[0] + 120, b0[1] + 32, str(data.get("before_label") or "BEFORE (-)"), (*world["rose"][:3], 42), world["rose"], border_col=world["rose"], font=_get_font(20, bold=True), alpha_mul=g)
        for k, ln in enumerate(before):
            stage.draw.text((b0[0] + 26, b0[1] + 72 + k * 42), f"- {ln[:52]}", font=_get_font(22, mono=True), fill=_with_alpha(world["rose"], g))

        g2 = _ease_out_cubic(_clamp01((progress - 0.25) / 0.25))
        stage.draw_glass_card(b1, radius=22, accent_col=world["emerald"], alpha_mul=g2, active=True)
        stage.draw_pill(b1[0] + 120, b1[1] + 32, str(data.get("after_label") or "AFTER (+)"), (*world["emerald"][:3], 42), world["emerald"], border_col=world["emerald"], font=_get_font(20, bold=True), alpha_mul=g2)
        for k, ln in enumerate(after):
            stage.draw.text((b1[0] + 26, b1[1] + 72 + k * 42), f"+ {ln[:52]}", font=_get_font(22, mono=True), fill=_with_alpha(world["emerald"], g2))

    else:  # api_request_response
        method = str(data.get("method") or "POST").upper()
        ep = str(data.get("endpoint") or "/v1/query")
        status = str(data.get("status") or "200 OK")
        req_b = (74, STAGE_Y0 + 18, 1006, STAGE_Y0 + 455)
        resp_b = (74, STAGE_Y0 + 555, 1006, STAGE_Y1 - 24)
        stage.draw_glass_card(req_b, radius=22, accent_col=world["cyan"], alpha_mul=g)
        stage.draw_pill(req_b[0] + 84, req_b[1] + 38, method, (*world["cyan"][:3], 45), world["cyan"], border_col=world["cyan"], font=_get_font(21, bold=True), alpha_mul=g)
        stage.draw.text((req_b[0] + 160, req_b[1] + 24), ep[:40], font=_get_font(24, bold=True, mono=True), fill=_with_alpha(world["text"], g))
        for k, ln in enumerate(str(data.get("request_body") or "{}").splitlines()[:7]):
            stage.draw.text((req_b[0] + 28, req_b[1] + 84 + k * 42), ln[:52], font=_get_font(22, mono=True), fill=_with_alpha(world["muted"], g))

        g2 = _ease_out_cubic(_clamp01((progress - 0.30) / 0.28))
        _draw_bezier_comet(stage, (540, req_b[3] + 4), (540, resp_b[1] - 4), world["emerald"], reveal=g2, progress=progress, label=status, world=world)
        stage.draw_glass_card(resp_b, radius=22, accent_col=world["emerald"], alpha_mul=g2, active=True)
        stage.draw_pill(resp_b[0] + 105, resp_b[1] + 38, status[:16], (*world["emerald"][:3], 45), world["emerald"], border_col=world["emerald"], font=_get_font(21, bold=True), alpha_mul=g2)
        for k, ln in enumerate(str(data.get("response_body") or "{}").splitlines()[:7]):
            stage.draw.text((resp_b[0] + 28, resp_b[1] + 84 + k * 42), ln[:52], font=_get_font(22, mono=True), fill=_with_alpha(world["emerald"], g2))


def _render_sequence_diagram(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    actors = [str(a).strip() for a in (data.get("actors") or data.get("participants") or []) if str(a).strip()][:4]
    msgs = list(data.get("messages") or data.get("steps") or [])[:7]
    if len(actors) < 2 and msgs:
        actors = ["Client", "Gateway", "Service"][:3]
    n = len(actors)
    xs = [int(150 + i * (780 / max(1, n - 1))) for i in range(n)]
    g_top = _ease_out_cubic(_clamp01(progress / 0.16))

    for i, act in enumerate(actors):
        ac = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        stage.draw_glass_card((xs[i] - 96, STAGE_Y0 + 16, xs[i] + 96, STAGE_Y0 + 100), radius=18, accent_col=ac, alpha_mul=g_top, active=True)
        _draw_wrapped_text(stage.draw, (xs[i] - 88, STAGE_Y0 + 36), act, _get_font(22, bold=True), _with_alpha(world["text"], g_top), 176, align="center", max_lines=2)
        # Dashed vertical lifeline
        for ly in range(STAGE_Y0 + 112, STAGE_Y1 - 24, 24):
            stage.draw.line((xs[i], ly, xs[i], min(STAGE_Y1 - 24, ly + 12)), fill=_with_alpha((*ac[:3], 130), g_top), width=3)

    m_cnt = len(msgs)
    my_step = min(130, (STAGE_H - 170) // max(1, m_cnt))
    for i, ms in enumerate(msgs):
        if isinstance(ms, str):
            ms = {"label": ms, "from": 0, "to": min(1, n - 1)}
        g = _spring_gate(progress, i + 1, m_cnt + 1, 0.22)
        if g <= 0.03:
            continue
        f_idx = ms.get("from", 0)
        t_idx = ms.get("to", min(1, n - 1))
        if isinstance(f_idx, str) and f_idx in actors:
            f_idx = actors.index(f_idx)
        if isinstance(t_idx, str) and t_idx in actors:
            t_idx = actors.index(t_idx)
        f_idx = max(0, min(n - 1, int(f_idx)))
        t_idx = max(0, min(n - 1, int(t_idx)))
        y = STAGE_Y0 + 168 + i * my_step
        mc = resolve_world_color(world, ms.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        _draw_bezier_comet(stage, (xs[f_idx], y), (xs[t_idx], y), mc, reveal=g, progress=progress, phase=i * 0.25, label=str(ms.get("label") or ms.get("msg") or ""), world=world)


def _render_er_schema(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    tables = list(data.get("tables") or data.get("entities") or [])[:4]
    if not tables:
        return
    n = len(tables)
    cw, ch = (442, 465) if n > 2 else (442, 720)
    coords = [(72, STAGE_Y0 + 30), (566, STAGE_Y0 + 30), (72, STAGE_Y0 + 545), (566, STAGE_Y0 + 545)]
    for i in range(n - 1):
        b0, b1 = coords[i], coords[i + 1]
        g = _spring_gate(progress, i + 1, n, 0.24)
        _draw_bezier_comet(stage, (b0[0] + cw // 2, b0[1] + ch // 2), (b1[0] + cw // 2, b1[1] + ch // 2), world["cyan"], reveal=g, progress=progress, label="1:N", world=world)

    for i, tb in enumerate(tables):
        if isinstance(tb, str):
            tb = {"name": tb, "fields": []}
        x0, y0 = coords[i]
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, tb.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        stage.draw_glass_card((x0, y0, x0 + cw, y0 + ch), radius=22, accent_col=col, alpha_mul=a_mul, active=(int(progress * n) == i))
        stage.draw.rounded_rectangle((x0 + 2, y0 + 2, x0 + cw - 2, y0 + 68), radius=20, fill=_with_alpha((*col[:3], 42), a_mul))
        _draw_wrapped_text(stage.draw, (x0 + 20, y0 + 18), str(tb.get("name") or tb.get("table") or "TABLE"), _get_font(26, bold=True), _with_alpha(col, a_mul), cw - 40, max_lines=1)
        fields = list(tb.get("fields") or tb.get("columns") or [])[:6]
        for k, fld in enumerate(fields):
            if isinstance(fld, dict):
                line = f"{fld.get('key', '')} {fld.get('name', '')}: {fld.get('type', '')}".strip()
            else:
                line = str(fld)
            stage.draw.text((x0 + 22, y0 + 88 + k * 56), line[:30], font=_get_font(21, mono=True), fill=_with_alpha(world["text"], a_mul))


def _render_state_machine(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    states = list(data.get("states") or data.get("nodes") or [])[:5]
    if not states:
        return
    n = len(states)
    cx, cy, rad = 540, 880, 325
    pts: List[Tuple[int, int]] = []
    for i in range(n):
        ang = -math.pi / 2.0 + i * (2.0 * math.pi / n)
        pts.append((int(cx + rad * math.cos(ang)), int(cy + rad * 0.92 * math.sin(ang))))

    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        g = _spring_gate(progress, i + 1, n + 1, 0.24)
        sc = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        lbl = ""
        if isinstance(states[i], dict):
            lbl = str(states[i].get("next_label") or states[i].get("trigger") or "")
        _draw_bezier_comet(stage, p0, p1, sc, reveal=g, progress=progress, phase=i * 0.25, label=lbl, curve_bend=28, world=world)

    for i, st in enumerate(states):
        if isinstance(st, str):
            st = {"name": st}
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        sx, sy = pts[i]
        col = resolve_world_color(world, st.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        active = (int(progress * n) == i)
        stage.draw_glass_card((sx - 120, sy - 60, sx + 120, sy + 60), radius=30, accent_col=col, alpha_mul=a_mul, active=active)
        _draw_wrapped_text(stage.draw, (sx - 106, sy - 24), str(st.get("name") or st.get("state") or ""), _get_font(24, bold=True), _with_alpha(world["text"], a_mul), 212, align="center", max_lines=2)


def _render_git_branch_tree(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    commits = list(data.get("commits") or data.get("steps") or [])[:6]
    if not commits:
        return
    lanes = {"main": 260, "feature": 540, "hotfix": 820}
    g_base = _ease_out_cubic(_clamp01(progress / 0.16))
    for lname, lx in lanes.items():
        lc = world["cyan"] if lname == "main" else (world["purple"] if lname == "feature" else world["amber"])
        stage.draw_pill(lx, STAGE_Y0 + 34, lname, (*lc[:3], 40), lc, border_col=lc, font=_get_font(21, bold=True), alpha_mul=g_base)
        stage.draw.line((lx, STAGE_Y0 + 68, lx, STAGE_Y1 - 40), fill=_with_alpha((*lc[:3], 85), g_base), width=4)

    n = len(commits)
    y_step = min(155, (STAGE_H - 140) // max(1, n))
    prev_xy: Optional[Tuple[int, int]] = None
    for i, cm in enumerate(commits):
        if isinstance(cm, str):
            cm = {"message": cm, "branch": "main"}
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        br = str(cm.get("branch") or "main").lower()
        lx = lanes.get(br, 260 if i % 2 == 0 else 540)
        ly = STAGE_Y0 + 135 + i * y_step
        cc = world["cyan"] if lx == 260 else (world["purple"] if lx == 540 else world["amber"])
        if prev_xy is not None:
            _draw_bezier_comet(stage, prev_xy, (lx, ly), cc, reveal=a_mul, progress=progress, phase=i * 0.2, world=world)
        stage.add_glow_orb(lx, ly, 26, cc, alpha=int(130 * a_mul))
        stage.draw.ellipse((lx - 18, ly - 18, lx + 18, ly + 18), fill=_with_alpha(cc, a_mul), outline=_with_alpha(world["glass_rim"], a_mul), width=3)
        msg = str(cm.get("message") or cm.get("name") or "").strip()
        cb_x0 = lx + 34 if lx < 650 else lx - 380
        stage.draw_glass_card((cb_x0, ly - 32, cb_x0 + 345, ly + 36), radius=16, accent_col=cc, alpha_mul=a_mul)
        _draw_wrapped_text(stage.draw, (cb_x0 + 16, ly - 16), msg, _get_font(22, bold=True), _with_alpha(world["text"], a_mul), 312, max_lines=2)
        prev_xy = (lx, ly)


def _render_flamegraph_perf(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    spans = list(data.get("spans") or data.get("frames") or [])[:10]
    if not spans:
        return
    g_box = _ease_out_cubic(_clamp01(progress / 0.18))
    stage.draw_glass_card((68, STAGE_Y0 + 20, 1012, STAGE_Y1 - 40), radius=24, accent_col=world["amber"], alpha_mul=g_box)
    for i, sp in enumerate(spans):
        if isinstance(sp, str):
            sp = {"name": sp, "depth": i, "start": 0.0, "width": 1.0 - i * 0.1}
        g = _spring_gate(progress, i, len(spans), 0.22)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        d = int(sp.get("depth", i % 5))
        s = _clamp01(float(sp.get("start", 0.0)))
        w = max(0.14, min(1.0 - s, float(sp.get("width", 1.0))))
        hot = bool(sp.get("hot", False))
        col = world["rose"] if hot else resolve_world_color(world, sp.get("color"), _ACCENT_CYCLE[d % len(_ACCENT_CYCLE)])
        x0 = int(96 + s * 888)
        x1 = int(x0 + w * 888 * _ease_out_cubic(g))
        y0 = STAGE_Y1 - 140 - d * 135
        stage.draw_glass_card((x0, y0, max(x0 + 60, x1), y0 + 104), radius=14, accent_col=col, alpha_mul=a_mul, active=hot)
        _draw_wrapped_text(stage.draw, (x0 + 14, y0 + 20), str(sp.get("name") or ""), _get_font(22, bold=True), _with_alpha(world["text"], a_mul), max(40, x1 - x0 - 28), max_lines=1)
        if sp.get("duration") or sp.get("pct"):
            _draw_wrapped_text(stage.draw, (x0 + 14, y0 + 58), str(sp.get("duration") or sp.get("pct")), _get_font(19, mono=True), _with_alpha(col, a_mul), max(40, x1 - x0 - 28), max_lines=1)


def _render_latency_waterfall(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    spans = list(data.get("spans") or data.get("traces") or data.get("items") or [])[:7]
    if not spans:
        return
    n = len(spans)
    rh = min(132, (STAGE_H - 60) // max(1, n))
    for i, sp in enumerate(spans):
        if isinstance(sp, str):
            sp = {"name": sp, "offset": i * 0.1, "width": 0.35}
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, sp.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        y = STAGE_Y0 + 36 + i * rh
        off = _clamp01(float(sp.get("offset", i * 0.1)))
        dur = max(0.10, min(1.0 - off, float(sp.get("width", 0.32))))
        stage.draw_glass_card((74, y, 1006, y + rh - 14), radius=18, accent_col=col, alpha_mul=a_mul, active=bool(sp.get("critical")))
        stage.draw.text((98, y + 16), str(sp.get("name") or "")[:30], font=_get_font(23, bold=True), fill=_with_alpha(world["text"], a_mul))
        stage.draw.text((820, y + 16), str(sp.get("ms") or sp.get("duration") or ""), font=_get_font(22, bold=True, mono=True), fill=_with_alpha(col, a_mul))
        bx0 = int(102 + off * 870)
        bw = max(24, int(dur * 870 * _ease_out_cubic(g)))
        stage.draw.rounded_rectangle((102, y + 58, 972, y + 84), radius=10, fill=_with_alpha(world["card_layer"], a_mul))
        stage.draw.rounded_rectangle((bx0, y + 58, bx0 + bw, y + 84), radius=10, fill=_with_alpha(col, a_mul))


def _render_memory_lanes(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    lanes = list(data.get("lanes") or data.get("blocks") or data.get("items") or [])[:5]
    if not lanes:
        return
    n = len(lanes)
    lh = min(185, (STAGE_H - 60) // max(1, n))
    for i, ln in enumerate(lanes):
        if isinstance(ln, str):
            ln = {"name": ln, "segments": [{"label": "DATA", "pct": 0.6}]}
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        y = STAGE_Y0 + 30 + i * lh
        col = resolve_world_color(world, ln.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        stage.draw_glass_card((74, y, 1006, y + lh - 18), radius=20, accent_col=col, alpha_mul=a_mul)
        stage.draw.text((104, y + 18), str(ln.get("name") or "")[:34], font=_get_font(25, bold=True), fill=_with_alpha(world["text"], a_mul))
        segs = list(ln.get("segments") or [{"label": "Used", "pct": 0.68}])[:4]
        sx = 104
        avail = 870
        for j, sg in enumerate(segs):
            if isinstance(sg, str):
                sg = {"label": sg, "pct": 1.0 / len(segs)}
            pw = max(60, int(avail * min(1.0, float(sg.get("pct", 0.25))) * _ease_out_cubic(g))) - 8
            sc = resolve_world_color(world, sg.get("color"), _ACCENT_CYCLE[(i + j) % len(_ACCENT_CYCLE)])
            stage.draw.rounded_rectangle((sx, y + 66, sx + pw, y + lh - 38), radius=12, fill=_with_alpha((*sc[:3], 185), a_mul), outline=_with_alpha(world["glass_rim"], a_mul), width=2)
            stage.draw.text((sx + 14, y + 78), str(sg.get("label") or "")[:14], font=_get_font(20, bold=True), fill=_with_alpha(world["text"], a_mul))
            sx += pw + 8


def _render_roadmap_wave(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    milestones = list(data.get("milestones") or data.get("steps") or data.get("items") or [])[:5]
    if not milestones:
        return
    n = len(milestones)
    anchors = [(250 if i % 2 == 0 else 830, STAGE_Y0 + 110 + i * min(200, (STAGE_H - 180) // max(1, n))) for i in range(n)]
    for i in range(n - 1):
        g = _spring_gate(progress, i + 1, n, 0.24)
        _draw_bezier_comet(stage, anchors[i], anchors[i + 1], resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)]), reveal=g, progress=progress, phase=i * 0.25, world=world)
    for i, ms in enumerate(milestones):
        if isinstance(ms, str):
            ms = {"title": ms}
        g = _spring_gate(progress, i, n, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        ax, ay = anchors[i]
        col = resolve_world_color(world, ms.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        cb_x0 = ax + 54 if ax < 540 else 84
        cb_x1 = 996 if ax < 540 else ax - 54
        stage.draw_glass_card((cb_x0, ay - 56, cb_x1, ay + 64), radius=20, accent_col=col, alpha_mul=a_mul, active=(int(progress * n) == i))
        _draw_node_visual(stage, ax, ay - 16, 40, 18, 28, col, a_mul, shape=ms.get("shape", "hexagon"), icon=ms.get("icon", ""), active=(int(progress * n) == i), progress=progress)
        stage.draw_pill(ax, ay + 40, str(ms.get("phase") or f"P{i+1}")[:10], world["card_alt"], col, border_col=col, font=_get_font(19, bold=True), alpha_mul=a_mul)
        _draw_wrapped_text(stage.draw, (cb_x0 + 20, ay - 36), str(ms.get("title") or ms.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], a_mul), cb_x1 - cb_x0 - 40, max_lines=1)
        if ms.get("sub"):
            _draw_wrapped_text(stage.draw, (cb_x0 + 20, ay + 8), str(ms["sub"]), _get_font(20), _with_alpha(world["muted"], a_mul), cb_x1 - cb_x0 - 40, max_lines=2)


def _render_checklist_scorecard(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    items = list(data.get("items") or data.get("checks") or [])[:6]
    score = str(data.get("score") or f"{sum(1 for it in items if not isinstance(it, dict) or it.get('passed', True))}/{len(items) or 1}")
    g0 = _ease_out_cubic(_clamp01(progress / 0.18))
    stage.draw_glass_card((80, STAGE_Y0 + 18, 1000, STAGE_Y0 + 168), radius=24, accent_col=world["emerald"], alpha_mul=g0, active=True)
    _draw_wrapped_text(stage.draw, (112, STAGE_Y0 + 42), str(data.get("summary") or "Verification Scorecard"), _get_font(30, bold=True), _with_alpha(world["text"], g0), 620, max_lines=2)
    stage.draw_pill(880, STAGE_Y0 + 92, score[:12], (*world["emerald"][:3], 42), world["emerald"], border_col=world["emerald"], font=_get_font(30, bold=True), alpha_mul=g0, pad_x=22, pad_y=12)

    y = STAGE_Y0 + 196
    rh = min(132, (STAGE_Y1 - y - 16) // max(1, len(items)))
    for i, it in enumerate(items):
        if isinstance(it, str):
            it = {"title": it, "passed": True}
        g = _spring_gate(progress, i + 1, len(items) + 1, 0.22)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        passed = bool(it.get("passed", True))
        col = world["emerald"] if passed else world["rose"]
        stage.draw_glass_card((80, y, 1000, y + rh - 14), radius=18, accent_col=col, alpha_mul=a_mul)
        draw_vector_glyph(stage, 134, y + (rh - 14) // 2, "check" if passed else "close", 22, col, a_mul)
        _draw_wrapped_text(stage.draw, (184, y + 20), str(it.get("title") or it.get("label") or ""), _get_font(25, bold=True), _with_alpha(world["text"], a_mul), 790, max_lines=1)
        if it.get("sub"):
            _draw_wrapped_text(stage.draw, (184, y + 58), str(it["sub"]), _get_font(20), _with_alpha(world["muted"], a_mul), 790, max_lines=1)
        y += rh


def _render_incident_radar(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    alerts = list(data.get("alerts") or data.get("blips") or data.get("items") or [])[:5]
    cx, cy, rad = 540, 745, 315
    g0 = _ease_out_cubic(_clamp01(progress / 0.18))
    for r_i, rr in enumerate((110, 210, 315)):
        stage.draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=_with_alpha((*world["rose"][:3], 95 - r_i * 22), g0), width=2)
    # Sweep beam
    ang = progress * math.pi * 3.0
    stage.add_glow_line([(cx, cy), (cx + rad * math.cos(ang), cy + rad * math.sin(ang))], world["cyan"], width=12, alpha=160)
    stage.draw.line((cx, cy, int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))), fill=_with_alpha(world["cyan"], g0), width=4)

    for i, al in enumerate(alerts):
        if isinstance(al, str):
            al = {"title": al, "severity": "high"}
        g = _spring_gate(progress, i + 1, len(alerts) + 1, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        ba = -math.pi * 0.8 + i * 1.15
        br = 135 + (i % 2) * 105
        bx, by = int(cx + br * math.cos(ba)), int(cy + br * math.sin(ba))
        sev = str(al.get("severity") or "warn").lower()
        col = world["rose"] if sev in ("high", "critical", "p0") else (world["amber"] if sev == "warn" else world["emerald"])
        stage.add_glow_orb(bx, by, 28, col, alpha=int(150 * a_mul))
        stage.draw.ellipse((bx - 12, by - 12, bx + 12, by + 12), fill=_with_alpha(col, a_mul))
        stage.draw_pill(bx, by + 34, str(al.get("title") or "")[:18], world["card_alt"], world["text"], border_col=col, font=_get_font(19, bold=True), alpha_mul=a_mul)

    if alerts:
        top_al = alerts[0] if isinstance(alerts[0], dict) else {"title": str(alerts[0])}
        stage.draw_glass_card((84, 1140, 996, 1345), radius=22, accent_col=world["rose"], alpha_mul=g0, active=True)
        _draw_wrapped_text(stage.draw, (118, 1172), str(top_al.get("title") or ""), _get_font(28, bold=True), _with_alpha(world["rose"], g0), 840, align="center", max_lines=1)
        if top_al.get("sub") or data.get("mitigation"):
            _draw_wrapped_text(stage.draw, (118, 1226), str(top_al.get("sub") or data.get("mitigation")), _get_font(22), _with_alpha(world["text"], g0), 840, align="center", max_lines=2)


def _render_topology_flow(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any], mode: str) -> None:
    """Shared crisp renderer for `queue_workers`, `load_balancer_fanout`, and `cache_hit_miss`."""
    if mode == "cache":
        g1 = _ease_out_cubic(_clamp01(progress / 0.25))
        g2 = _ease_out_cubic(_clamp01((progress - 0.30) / 0.25))
        # Fast Hit Row
        stage.draw_glass_card((80, STAGE_Y0 + 36, 1000, STAGE_Y0 + 440), radius=26, accent_col=world["emerald"], alpha_mul=g1, active=True)
        stage.draw_pill(240, STAGE_Y0 + 96, str(data.get("hit_label") or "CACHE HIT (2ms)"), (*world["emerald"][:3], 42), world["emerald"], border_col=world["emerald"], font=_get_font(23, bold=True), alpha_mul=g1)
        _draw_node_visual(stage, 220, STAGE_Y0 + 250, 56, 26, 38, world["cyan"], g1, shape="monitor", label="App", active=True, progress=progress)
        _draw_node_visual(stage, 840, STAGE_Y0 + 250, 58, 26, 42, world["emerald"], g1, shape="database_cluster", icon="redis", label="Redis Cache", active=True, progress=progress)
        _draw_bezier_comet(stage, (295, STAGE_Y0 + 250), (765, STAGE_Y0 + 250), world["emerald"], reveal=g1, progress=progress, label="0.4ms Fast Return", world=world)
        # Slow Miss Row
        stage.draw_glass_card((80, STAGE_Y0 + 495, 1000, STAGE_Y0 + 915), radius=26, accent_col=world["rose"], alpha_mul=g2)
        stage.draw_pill(250, STAGE_Y0 + 555, str(data.get("miss_label") or "CACHE MISS (140ms)"), (*world["rose"][:3], 42), world["rose"], border_col=world["rose"], font=_get_font(23, bold=True), alpha_mul=g2)
        _draw_node_visual(stage, 220, STAGE_Y0 + 720, 56, 26, 38, world["purple"], g2, shape="monitor", label="App", progress=progress)
        _draw_node_visual(stage, 540, STAGE_Y0 + 720, 48, 22, 34, world["amber"], g2, shape="load_balancer", label="Miss", progress=progress)
        _draw_node_visual(stage, 860, STAGE_Y0 + 720, 58, 26, 42, world["rose"], g2, shape="cylinder", icon="postgres", label="Cold Disk DB", progress=progress)
        _draw_bezier_comet(stage, (295, STAGE_Y0 + 720), (475, STAGE_Y0 + 720), world["amber"], reveal=g2, progress=progress, world=world)
        _draw_bezier_comet(stage, (605, STAGE_Y0 + 720), (790, STAGE_Y0 + 720), world["rose"], reveal=g2, progress=progress, world=world)
        return

    # queue_workers or load_balancer_fanout
    src_label = str(data.get("source") or data.get("ingress") or ("Producers" if mode == "queue" else "Client Traffic")).strip()
    mid_label = str(data.get("broker") or data.get("balancer") or ("Message Queue" if mode == "queue" else "Load Balancer")).strip()
    targets = list(data.get("workers") or data.get("backends") or data.get("nodes") or ["Worker 1", "Worker 2", "Worker 3"])[:4]
    g0 = _ease_out_cubic(_clamp01(progress / 0.20))

    _draw_node_visual(stage, 200, 880, 62, 28, 44, world["cyan"], g0, shape="cloud" if mode == "lb" else "code_cube", label=src_label, active=True, progress=progress)
    stage.draw_pill(200, 995, src_label[:18], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(21, bold=True), alpha_mul=g0)

    _draw_node_visual(stage, 500, 880, 66, 30, 46, world["purple"], g0, shape="queue" if mode == "queue" else "load_balancer", label=mid_label, active=True, progress=progress)
    stage.draw_pill(500, 995, mid_label[:18], world["card_alt"], world["text"], border_col=world["purple"], font=_get_font(21, bold=True), alpha_mul=g0)

    _draw_bezier_comet(stage, (280, 880), (420, 880), world["cyan"], reveal=g0, progress=progress, label="Stream" if mode == "queue" else "HTTPS", world=world)

    n = len(targets)
    y_step = min(215, (STAGE_H - 120) // max(1, n))
    y_base = 880 - ((n - 1) * y_step) // 2
    for i, tg in enumerate(targets):
        if isinstance(tg, str):
            tg = {"name": tg}
        gt = _spring_gate(progress, i + 1, n + 1, 0.24)
        a_mul = _ease_out_cubic(gt)
        if a_mul <= 0.03:
            continue
        ty = y_base + i * y_step
        tc = resolve_world_color(world, tg.get("color"), _ACCENT_CYCLE[(i + 2) % len(_ACCENT_CYCLE)])
        _draw_bezier_comet(stage, (575, 880), (705, ty), tc, reveal=a_mul, progress=progress, phase=i * 0.25, label=str(tg.get("weight", "")), world=world)
        stage.draw_glass_card((710, ty - 54, 1004, ty + 54), radius=20, accent_col=tc, alpha_mul=a_mul, active=(int(progress * n) == i))
        _draw_node_visual(stage, 770, ty - 14, 34, 16, 24, tc, a_mul, shape=tg.get("shape", "server_rack"), icon=tg.get("icon", ""), label=tg.get("name", ""), progress=progress)
        _draw_wrapped_text(stage.draw, (818, ty - 28), str(tg.get("name") or ""), _get_font(23, bold=True), _with_alpha(world["text"], a_mul), 175, max_lines=2)


def _render_venn_overlap(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    sets = list(data.get("sets") or data.get("circles") or [])[:3]
    if len(sets) < 2:
        sets = [{"label": "Domain A"}, {"label": "Domain B"}]
    g0 = _ease_out_cubic(_clamp01(progress / 0.24))
    centers = [(375, 760), (705, 760)] if len(sets) == 2 else [(375, 700), (705, 700), (540, 965)]
    rad = 245 if len(sets) == 2 else 215

    for i, st in enumerate(sets):
        if isinstance(st, str):
            st = {"label": st}
        cx, cy = centers[i]
        col = resolve_world_color(world, st.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        stage.add_glow_orb(cx, cy, rad, col, alpha=int(75 * g0))
        stage.draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=_with_alpha((*col[:3], 64), g0), outline=_with_alpha(col, g0), width=4)
        lx = cx - (60 if i == 0 else (-60 if i == 1 else 0))
        ly = cy - 90 if len(sets) == 3 and i < 2 else (cy + 90 if i == 2 else cy)
        _draw_wrapped_text(stage.draw, (lx - 110, ly - 24), str(st.get("label") or ""), _get_font(28, bold=True), _with_alpha(world["text"], g0), 220, align="center", max_lines=2)

    inter = str(data.get("intersection") or data.get("overlap") or "").strip()
    if inter:
        gi = _ease_out_elastic(_clamp01((progress - 0.35) / 0.25))
        stage.draw_glass_card((120, 1185, 960, 1345), radius=24, accent_col=world["amber"], alpha_mul=gi, active=True)
        _draw_wrapped_text(stage.draw, (150, 1218), inter, _get_font(29, bold=True), _with_alpha(world["amber"], gi), 780, align="center", max_lines=2)


def _render_tree_hierarchy(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    root_lbl = str(data.get("root") or "Root").strip()
    children = list(data.get("children") or data.get("branches") or [])[:4]
    g0 = _ease_out_cubic(_clamp01(progress / 0.20))
    stage.draw_glass_card((350, STAGE_Y0 + 26, 730, STAGE_Y0 + 130), radius=22, accent_col=world["cyan"], alpha_mul=g0, active=True)
    _draw_wrapped_text(stage.draw, (370, STAGE_Y0 + 58), root_lbl, _get_font(28, bold=True), _with_alpha(world["text"], g0), 340, align="center", max_lines=1)

    n = max(1, len(children))
    cw = min(295, (STAGE_W - (n - 1) * 20) // n)
    tot_w = n * cw + (n - 1) * 20
    sx0 = 540 - tot_w // 2
    for i, ch in enumerate(children):
        if isinstance(ch, str):
            ch = {"name": ch, "leaves": []}
        g = _spring_gate(progress, i + 1, n + 1, 0.24)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        bx0 = sx0 + i * (cw + 20)
        bcx = bx0 + cw // 2
        col = resolve_world_color(world, ch.get("color"), _ACCENT_CYCLE[(i + 1) % len(_ACCENT_CYCLE)])
        _draw_bezier_comet(stage, (540, STAGE_Y0 + 132), (bcx, STAGE_Y0 + 255), col, reveal=a_mul, progress=progress, world=world)
        stage.draw_glass_card((bx0, STAGE_Y0 + 258, bx0 + cw, STAGE_Y0 + 365), radius=18, accent_col=col, alpha_mul=a_mul)
        _draw_wrapped_text(stage.draw, (bx0 + 12, STAGE_Y0 + 286), str(ch.get("name") or ""), _get_font(23, bold=True), _with_alpha(world["text"], a_mul), cw - 24, align="center", max_lines=2)

        leaves = list(ch.get("leaves") or ch.get("items") or [])[:3]
        for j, lf in enumerate(leaves):
            ly = STAGE_Y0 + 440 + j * 140
            _draw_bezier_comet(stage, (bcx, STAGE_Y0 + 368), (bcx, ly), col, reveal=a_mul, progress=progress, world=world)
            stage.draw_glass_card((bx0 + 8, ly, bx0 + cw - 8, ly + 98), radius=16, accent_col=col, alpha_mul=a_mul)
            _draw_wrapped_text(stage.draw, (bx0 + 18, ly + 26), str(lf), _get_font(20, bold=True), _with_alpha(world["muted"], a_mul), cw - 36, align="center", max_lines=2)


# =========================================================================
# UNIFIED 33+ STUDIO LAYOUT DISPATCHER
# =========================================================================
ALL_STUDIO_LAYOUTS: Tuple[str, ...] = (
    "custom_scene", "iso_architecture", "node_graph", "iso_comparison", "terminal_studio", "kinetic_statement",
    "spatial_canvas", "svg_scene",
    "layer_stack_3d", "matrix_2x2", "pyramid_hierarchy", "sql_studio", "benchmark_3d",
    "radial_gauge", "memory_lanes", "roadmap_wave", "checklist_scorecard", "incident_radar",
    "sequence_diagram", "er_schema", "state_machine", "git_branch_tree", "flamegraph_perf",
    "queue_workers", "load_balancer_fanout", "cache_hit_miss", "code_diff_split", "api_request_response",
    "venn_overlap", "funnel_metrics", "stat_grid_2x2", "latency_waterfall", "tree_hierarchy",
) + EXTRA_32_LAYOUTS + IT_SDLC_35_LAYOUTS

_PRO_HELPERS: Dict[str, Any] = {
    "_get_font": _get_font,
    "_draw_wrapped_text": _draw_wrapped_text,
    "_with_alpha": _with_alpha,
    "_spring_gate": _spring_gate,
    "_ease_out_cubic": _ease_out_cubic,
    "_animate_counter_text": _animate_counter_text,
    "resolve_world_color": resolve_world_color,
    "_draw_bezier_comet": _draw_bezier_comet,
    "_draw_node_visual": _draw_node_visual,
}


def dispatch_studio_layout(
    stage: StudioStage,
    layout: str,
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    topic: str = "",
) -> None:
    l = str(layout or "custom_scene").lower().strip()
    d = data or {}
    if render_pro_layout(stage, l, d, progress, world, _PRO_HELPERS):
        pass
    elif render_it_sdlc_layout(stage, l, d, progress, world, _PRO_HELPERS):
        pass
    elif l in ("custom_scene", "custom", "cards", "concept_cards"):
        _render_custom_scene(stage, d, progress, world)
    elif l in ("iso_architecture", "architecture", "architecture_flow", "pipeline", "flow"):
        _render_iso_architecture(stage, d, progress, world)
    elif l in ("node_graph", "mesh", "hub_spoke", "circular_hub_mesh"):
        _render_node_graph(stage, d, progress, world)
    elif l in ("iso_comparison", "comparison", "split_comparison", "versus", "vs"):
        _render_iso_comparison(stage, d, progress, world)
    elif l in ("terminal_studio", "code", "terminal", "code_terminal"):
        _render_terminal_studio(stage, d, progress, world)
    elif l in ("kinetic_statement", "statement", "hook", "hero_hook", "cta"):
        _render_kinetic_statement(stage, d, progress, world)
    elif l in ("spatial_canvas", "spatial", "freeform", "composer"):
        _render_spatial_canvas(stage, d, progress, world)
    elif l in ("svg_scene", "generative_svg", "svg"):
        _render_svg_scene(stage, d, progress, world)
    elif l in ("layer_stack_3d", "stack_3d", "layers"):
        _render_layer_stack_3d(stage, d, progress, world)
    elif l in ("matrix_2x2", "quadrant"):
        _render_grid_2x2(stage, d, progress, world, is_matrix=True)
    elif l in ("stat_grid_2x2", "kpi_grid", "bento_stats"):
        _render_grid_2x2(stage, d, progress, world, is_matrix=False)
    elif l in ("pyramid_hierarchy", "pyramid"):
        _render_pyramid_or_funnel(stage, d, progress, world, is_funnel=False)
    elif l in ("funnel_metrics", "funnel"):
        _render_pyramid_or_funnel(stage, d, progress, world, is_funnel=True)
    elif l in ("sql_studio", "sql", "sql_table"):
        _render_sql_or_diff_or_api(stage, d, progress, world, mode="sql")
    elif l in ("code_diff_split", "diff", "code_diff"):
        _render_sql_or_diff_or_api(stage, d, progress, world, mode="diff")
    elif l in ("api_request_response", "http", "rest_api"):
        _render_sql_or_diff_or_api(stage, d, progress, world, mode="api")
    elif l in ("benchmark_3d", "barchart", "bars", "benchmark_chart"):
        _render_benchmark_3d(stage, d, progress, world)
    elif l in ("radial_gauge", "gauge", "speedometer", "metric_gauge_hud"):
        _render_radial_gauge(stage, d, progress, world)
    elif l in ("memory_lanes", "memory", "storage_blocks", "data_structure_memory"):
        _render_memory_lanes(stage, d, progress, world)
    elif l in ("roadmap_wave", "timeline", "roadmap", "step_timeline"):
        _render_roadmap_wave(stage, d, progress, world)
    elif l in ("checklist_scorecard", "checklist", "scorecard"):
        _render_checklist_scorecard(stage, d, progress, world)
    elif l in ("incident_radar", "radar", "alerts", "alert_diagram"):
        _render_incident_radar(stage, d, progress, world)
    elif l in ("sequence_diagram", "sequence"):
        _render_sequence_diagram(stage, d, progress, world)
    elif l in ("er_schema", "erd", "database_schema"):
        _render_er_schema(stage, d, progress, world)
    elif l in ("state_machine", "fsm"):
        _render_state_machine(stage, d, progress, world)
    elif l in ("git_branch_tree", "git_graph", "git"):
        _render_git_branch_tree(stage, d, progress, world)
    elif l in ("flamegraph_perf", "flamegraph", "profiler"):
        _render_flamegraph_perf(stage, d, progress, world)
    elif l in ("latency_waterfall", "waterfall", "trace"):
        _render_latency_waterfall(stage, d, progress, world)
    elif l in ("queue_workers", "queue", "pubsub"):
        _render_topology_flow(stage, d, progress, world, mode="queue")
    elif l in ("load_balancer_fanout", "load_balancer", "fanout"):
        _render_topology_flow(stage, d, progress, world, mode="lb")
    elif l in ("cache_hit_miss", "cache"):
        _render_topology_flow(stage, d, progress, world, mode="cache")
    elif l in ("venn_overlap", "venn"):
        _render_venn_overlap(stage, d, progress, world)
    elif l in ("tree_hierarchy", "tree", "ast"):
        _render_tree_hierarchy(stage, d, progress, world)
    else:
        _render_custom_scene(stage, d, progress, world)

    if isinstance(d.get("metric_badges"), list):
        _draw_metric_badges_row(stage, d["metric_badges"], progress, world)
    _draw_step_progress_bar(stage, d, progress, world)
