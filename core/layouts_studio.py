import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core.config import ASSETS_DIR
from core.layouts_domain_220 import DOMAIN_220_LAYOUTS, render_domain_220_or_grammar
from core.layouts_domain_specialists import DOMAIN_SPECIALIST_LAYOUTS, render_domain_specialist_layout
from core.layouts_it_sdlc import IT_SDLC_35_LAYOUTS, render_it_sdlc_layout
from core.layouts_pro import EXTRA_32_LAYOUTS, render_pro_layout
from core.mesh_shader_engine import draw_procedural_3d_mesh
from core.palette_engine import resolve_studio_world
from core.shapes_3d import ALL_50_SHAPES, ALL_100_SHAPES, ALL_145_SHAPES, draw_3d_shape, draw_vector_glyph, infer_3d_shape
from core.svg_engine import ICON_ALIASES, fetch_iconify_svg, prepare_generative_svg_layers, prepare_keyframed_svg_layers

# Stage safe geometry inside 1080x1920 vertical frame (leaves y>=1410 clear for ASS karaoke)
STAGE_X0 = 64
STAGE_Y0 = 328
STAGE_X1 = 1016
STAGE_Y1 = 1406
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


import threading

_GATE_TLS = threading.local()


def _set_active_voice_gates(gates: Optional[List[float]] = None) -> None:
    """Sets per-component spoken-word gate overrides cleanly in thread-local storage."""
    _GATE_TLS.gates = list(gates) if gates else None


def _spring_gate(progress: float, idx: int, total: int, span: float = 0.22) -> float:
    """Locks each component entrance to exact spoken-word timestamps when available, else distributes evenly."""
    active_gates = getattr(_GATE_TLS, "gates", None)
    if active_gates:
        gi = max(0, min(len(active_gates) - 1, int(idx)))
        return _clamp01(active_gates[gi])
    n = max(1, total)
    if n <= 1:
        return _clamp01((progress - 0.02) / max(0.14, span))
    start = 0.02 + (idx / float(n)) * 0.72
    eff_span = max(0.16, min(0.24, span if span > 0.16 else 0.90 / float(n)))
    return _clamp01((progress - start) / eff_span)


def _sub_gate(node_gate: float, part: str = "box") -> float:
    """
    Staggers sub-elements inside a component sequentially as the voice describes it:
      box (0.00..0.44) -> badge/icon (0.14..0.56) -> title (0.28..0.72) -> sub/details (0.46..0.96) -> link (0.40..1.00).
    """
    g = _clamp01(node_gate)
    if part == "box":
        return _ease_out_cubic(_clamp01(g / 0.44))
    if part in ("badge", "icon", "shape"):
        return _ease_out_cubic(_clamp01((g - 0.14) / 0.42))
    if part in ("title", "label"):
        return _ease_out_cubic(_clamp01((g - 0.28) / 0.44))
    if part in ("sub", "desc", "detail"):
        return _ease_out_cubic(_clamp01((g - 0.46) / 0.50))
    if part in ("link", "edge", "conn"):
        return _clamp01((g - 0.36) / 0.58)
    return _ease_out_cubic(g)


def _footer_gate(progress: float) -> float:
    """Reveals bottom takeaway / summary strip during the closing vocal beat."""
    return _ease_out_cubic(_clamp01((progress - 0.74) / 0.22))


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
        self.anchors: List[Tuple[int, int, str]] = []
        self.anchor_cards: List[Dict[str, Any]] = []
        self.focus_dimming: bool = False
        self.motion_profile: str = "flow_slide"

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
        label: str = "",
        stage_idx: int = -1,
    ) -> Tuple[int, int, int, int]:
        eff = _clamp01(alpha_mul) * self.t_alpha
        if eff <= 0.02:
            return bbox
        if self.focus_dimming and not active and (bbox[2] - bbox[0]) < 860:
            eff *= 0.80
        x0, y0, x1, y1 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        # Voice-beat Elastic Focus + 5 Role-Adaptive Entrance Physics (works across ALL 1,041 Studio layouts)
        mprof = str(getattr(self, "motion_profile", "flow_slide") or "flow_slide")
        if eff < 0.96:
            ent = 1.0 - _clamp01(alpha_mul)
            if mprof == "pop_bounce":
                pad_s = int(round(math.sin(_clamp01(alpha_mul) * math.pi) * 10))
                x0 -= pad_s; y0 -= pad_s; x1 += pad_s; y1 += pad_s
            elif mprof == "stack_snap":
                dy_s = -int(round(ent * 42))
                y0 += dy_s; y1 += dy_s
            elif mprof == "split_collide":
                dx_s = int(round(ent * (52 if (x0 + x1) * 0.5 < self.width * 0.5 else -52)))
                x0 -= dx_s; x1 -= dx_s
            else:
                dx_s = int(round(ent * 36))
                x0 -= dx_s; x1 -= dx_s
        if active and (x1 - x0) < 780 and (y1 - y0) < 640:
            x0 -= 6; y0 -= 5; x1 += 6; y1 += 5
        if flip_t < 0.99:
            sx = _card_flip_scale_x(flip_t)
            cx = (x0 + x1) * 0.5
            hw = max(8.0, (x1 - x0) * 0.5 * sx)
            x0, x1 = int(round(cx - hw)), int(round(cx + hw))
        b = (x0, y0, x1, y1)
        if (x1 - x0) >= 80 and 300 <= (y0 + y1) * 0.5 <= 1560 and eff > 0.15:
            cx_a, cy_a = int((x0 + x1) * 0.5), int((y0 + y1) * 0.5)
            self.anchors.append((cx_a, cy_a, "active" if active else "card"))
            self.anchor_cards.append({
                "cx": cx_a, "cy": cy_a, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "label": str(label or ""), "active": bool(active), "idx": int(stage_idx if stage_idx >= 0 else len(self.anchor_cards)),
            })
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
def _harvest_generic_items(data: Dict[str, Any], topic: str = "") -> List[Dict[str, Any]]:
    """Extracts structured items from ANY schema key so no layout renderer ever returns a blank frame."""
    d = data or {}
    for k in ("nodes", "steps", "stages", "milestones", "satellites", "layers", "tiers", "units", "items", "bullets", "lanes", "commits"):
        raw = d.get(k)
        if isinstance(raw, list) and raw:
            out: List[Dict[str, Any]] = []
            for it in raw[:6]:
                if isinstance(it, dict):
                    out.append({
                        "name": str(it.get("name") or it.get("title") or it.get("label") or it.get("message") or it.get("op") or "").strip(),
                        "sub": str(it.get("sub") or it.get("desc") or it.get("role") or it.get("table") or it.get("proto") or "").strip(),
                        "color": it.get("color", ""),
                        "shape": it.get("shape", ""),
                        "icon": it.get("icon", ""),
                        "val": str(it.get("val") or it.get("value") or it.get("display") or it.get("edge") or "").strip(),
                    })
                elif str(it).strip():
                    out.append({"name": str(it).strip(), "sub": ""})
            if out:
                return out
    if isinstance(d.get("entries"), list) and d["entries"]:
        return [
            {
                "name": str(e.get("op") or e.get("address") or "Log Entry"),
                "sub": f"{e.get('address', '')} • {e.get('table', '')} [{e.get('status', '')}]".strip(" •"),
            }
            for e in d["entries"][:5] if isinstance(e, dict)
        ]
    if isinstance(d.get("bars"), list) and d["bars"]:
        return [
            {"name": str(b.get("label") or "Metric"), "sub": str(b.get("display") or b.get("value") or ""), "color": b.get("color", "")}
            for b in d["bars"][:5] if isinstance(b, dict)
        ]
    if d.get("problem_title") or d.get("problem_desc") or d.get("challenge"):
        res = []
        if d.get("problem_title"):
            res.append({"name": str(d["problem_title"]), "sub": str(d.get("problem_desc") or "")[:90], "color": "rose"})
        if d.get("challenge"):
            res.append({"name": str(d["challenge"]), "sub": "Target Engineering Goal", "color": "cyan"})
        if res:
            return res
    title_s = str(d.get("title") or topic or "Architecture Core").strip()
    return [
        {"name": title_s[:44], "sub": "Primary System Stage"},
        {"name": "Processing & Sync", "sub": "Low-Latency Pipeline"},
        {"name": "Verified State", "sub": "Zero-Downtime Output"},
    ]


def _render_iso_architecture(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    raw_nodes = data.get("nodes") or data.get("steps") or _harvest_generic_items(data)
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
        g = _spring_gate(progress, i, n, 0.22)
        g_box = _sub_gate(g, "box")
        if g_box <= 0.03:
            anchors.append((540, y_top + i * y_step))
            continue
        g_badge = _sub_gate(g, "badge")
        g_title = _sub_gate(g, "title")
        g_sub = _sub_gate(g, "sub")
        e_pop = _ease_out_elastic(g) if g < 0.95 else 1.0

        cy = y_top + i * y_step
        is_left = (i % 2 == 0) if stage.motion_profile != "stack_snap" else True
        col = resolve_world_color(world, nd.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        active = (int(min(n - 1, progress * n)) == i) or bool(nd.get("highlight"))
        slide_off = int((1.0 - g_box) * (-42 if is_left else 42))

        if stage.motion_profile == "stack_snap":
            shape_cx = 166 + (i * 18) + slide_off
            card_x0 = 264 + (i * 18) + slide_off
            card_x1 = 992
        else:
            shape_cx = (196 if is_left else 884) + slide_off
            card_x0 = (318 if is_left else 88) + slide_off
            card_x1 = (992 if is_left else 762) + slide_off
        card_b = (card_x0, cy - 66, card_x1, cy + 72)

        name_lbl = str(nd.get("name") or nd.get("title") or nd.get("label") or "").strip()
        stage.draw_glass_card(card_b, radius=22, accent_col=col, alpha_mul=g_box, active=active, layered=(i == n - 1), label=name_lbl, stage_idx=i)
        b_cx = card_x0 + 42
        if g_badge > 0.03:
            stage.draw_pill(b_cx, cy - 22, f"{i+1:02d}", (*col[:3], 42), world["text"], border_col=(*col[:3], 210), font=_get_font(20, bold=True), alpha_mul=g_badge, pad_x=12, pad_y=4)

        name = str(nd.get("name") or nd.get("title") or nd.get("label") or "").strip()
        sub = str(nd.get("sub") or nd.get("role") or nd.get("desc") or "").strip()
        f_title = _get_font(30, bold=True)
        f_sub = _get_font(22, bold=False)
        tx0 = card_x0 + 82
        max_tw = card_x1 - tx0 - 20
        ny = cy - 10
        if g_title > 0.03:
            ny = _draw_wrapped_text(stage.draw, (tx0, cy - 38), name, f_title, _with_alpha(world["text"], g_title), max_tw, line_gap=4, max_lines=2)
        if sub and g_sub > 0.03:
            _draw_wrapped_text(stage.draw, (tx0, ny + 2), sub, f_sub, _with_alpha(world["muted"], g_sub), max_tw, line_gap=4, max_lines=2)

        stub_x0 = shape_cx + (58 if is_left else -58)
        stub_x1 = card_x0 if is_left else card_x1
        if g_badge > 0.03:
            cur_sx1 = int(stub_x0 + (stub_x1 - stub_x0) * g_badge)
            stage.draw.line((stub_x0, cy, cur_sx1, cy), fill=_with_alpha((*col[:3], 185), g_badge), width=3)

        if g_badge > 0.03:
            rx = int(52 * (0.65 + 0.35 * min(1.12, e_pop)))
            _draw_node_visual(
                stage, shape_cx, cy - 18, rx, int(rx * 0.48), int(rx * 0.72), col, g_badge,
                shape=nd.get("shape", ""), icon=nd.get("icon", ""), label=name,
                active=active, progress=progress, phase=i * 0.7,
            )
        anchors.append((shape_cx, cy + 44))

    # Draw Bezier connections sequentially AFTER source builds and RIGHT AS target enters
    for i in range(n - 1):
        g_link = _sub_gate(_spring_gate(progress, i + 1, n, 0.22), "link")
        if g_link <= 0.03:
            continue
        edge_lbl = str(nodes[i].get("edge") or "") if isinstance(nodes[i], dict) else ""
        edge_col = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        if i < len(edges) and isinstance(edges[i], dict):
            edge_lbl = str(edges[i].get("label", edge_lbl))
            if edges[i].get("color"):
                edge_col = resolve_world_color(world, edges[i].get("color"))
        p0 = (anchors[i][0], anchors[i][1] + 10)
        p3 = (anchors[i + 1][0], anchors[i + 1][1] - 92)
        _draw_bezier_comet(stage, p0, p3, edge_col, reveal=g_link, progress=progress, phase=i * 0.27, label=edge_lbl, world=world)

    # Bottom Deep Takeaway / Footer Strip arrives on the closing beat
    ft_txt = str(data.get("footer") or data.get("summary") or data.get("challenge") or "").strip()
    if ft_txt and n <= 4:
        gf = _footer_gate(progress)
        if gf > 0.03:
            stage.draw_glass_card((80, STAGE_Y1 - 122, 1000, STAGE_Y1 - 24), radius=20, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped_text(stage.draw, (112, STAGE_Y1 - 92), ft_txt, _get_font(24, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=2)


def _render_node_graph(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    hub_name = str(data.get("hub_name") or data.get("center") or "CORE ENGINE").strip()
    hub_shape = str(data.get("hub_shape") or "sphere")
    hub_icon = str(data.get("hub_icon") or "")
    sats = list(data.get("satellites") or data.get("nodes") or _harvest_generic_items(data))[:6]
    if not sats:
        return

    hub_cx, hub_cy = 540, 865
    hub_col = world["cyan"]
    g_hub = _ease_out_cubic(_clamp01(progress / 0.18))

    # Concentric radar rings behind hub expand with hub reveal
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
        g = _spring_gate(progress, i + 1, n + 1, 0.22)
        g_link = _sub_gate(g, "box")
        g_box = _sub_gate(g, "badge")
        g_title = _sub_gate(g, "title")
        g_sub = _sub_gate(g, "sub")
        if g_link <= 0.03:
            continue
        col = resolve_world_color(world, sat.get("color"), _ACCENT_CYCLE[(i + 1) % len(_ACCENT_CYCLE)])
        active = (int(min(n - 1, progress * n)) == i)

        # Link fires outward from Hub -> Satellite first, then card & text appear
        dx, dy = sx - hub_cx, sy - hub_cy
        dist = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / dist, dy / dist
        p0 = (hub_cx + ux * 115, hub_cy + uy * 82)
        p3 = (sx - ux * 105, sy - uy * 84)
        _draw_bezier_comet(stage, p0, p3, col, reveal=g_link, progress=progress, phase=i * 0.23, label=str(sat.get("edge", "")), curve_bend=26 if i % 2 == 0 else -26, world=world)

        if g_box <= 0.03:
            continue
        cw, ch = 360, 126
        cb = (sx - cw // 2, sy - ch // 2 + 26, sx + cw // 2, sy + ch // 2 + 26)
        stage.draw_glass_card(cb, radius=20, accent_col=col, alpha_mul=g_box, active=active)
        _draw_node_visual(
            stage, sx, sy - 64, 42, 20, 32, col, g_box,
            shape=sat.get("shape", ""), icon=sat.get("icon", ""), label=sat.get("name", ""),
            active=active, progress=progress, phase=i * 0.6,
        )
        name = str(sat.get("name") or "").strip()
        role = str(sat.get("role") or sat.get("sub") or "").strip()
        if g_title > 0.03:
            _draw_wrapped_text(stage.draw, (cb[0] + 16, cb[1] + 18), name, _get_font(26, bold=True), _with_alpha(world["text"], g_title), cw - 32, line_gap=2, align="center", max_lines=2)
        if role and g_sub > 0.03:
            _draw_wrapped_text(stage.draw, (cb[0] + 16, cb[1] + 64), role, _get_font(20), _with_alpha(world["muted"], g_sub), cw - 32, line_gap=2, align="center", max_lines=2)

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
        # Sequential Left column (0.02..0.46) then VS pill (0.46) then Right column (0.48..0.94)
        col_start = 0.02 if idx == 0 else 0.48
        g = _clamp01((progress - col_start) / 0.18)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        g_hdr = _ease_out_cubic(_clamp01((progress - col_start - 0.04) / 0.16))
        cx = (x0 + x1) // 2
        card_b = (x0, 448, x1, 1368)
        stage.draw_glass_card(card_b, radius=26, accent_col=col, alpha_mul=a_mul, active=(idx == 1 and progress >= 0.48) or (idx == 0 and progress < 0.48), flip_t=g if g < 0.85 else 1.0, layered=(idx == 1))
        _draw_node_visual(stage, cx, 424, 54, 24, 38, col, g_hdr, shape=shp, icon=icn, label=title, active=(idx == 1), progress=progress, phase=idx * 0.9)
        _draw_wrapped_text(stage.draw, (x0 + 22, 520), title, _get_font(31, bold=True), _with_alpha(col, g_hdr), (x1 - x0) - 44, align="center", max_lines=2)
        stage.draw.line((x0 + 36, 598, int(x0 + 36 + (x1 - x0 - 72) * g_hdr), 598), fill=_with_alpha((*col[:3], 140), g_hdr), width=2)

        py = 626
        f_pt = _get_font(23, bold=False)
        for j, pt in enumerate(pts):
            pt_st = col_start + 0.08 + (j / max(1, len(pts))) * 0.34
            pg = _ease_out_cubic(_clamp01((progress - pt_st) / 0.14))
            if pg <= 0.03:
                continue
            draw_vector_glyph(stage, x0 + 44, py + 15, gkind, 15, col, pg * a_mul, with_badge=True)
            next_y = _draw_wrapped_text(stage.draw, (x0 + 74, py), pt, f_pt, _with_alpha(world["text"], pg * a_mul), (x1 - x0) - 96, line_gap=5, max_lines=4)
            py = max(py + 96, next_y + 26)

    if data.get("show_vs", True):
        gv = _ease_out_elastic(_clamp01((progress - 0.42) / 0.16))
        if gv > 0.05:
            stage.add_glow_orb(540, 880, 46, world["amber"], alpha=int(140 * gv))
            stage.draw_pill(540, 880, "VS", world["card_alt"], world["amber"], border_col=world["amber"], font=_get_font(26, bold=True), alpha_mul=gv, pad_x=20, pad_y=12)


def _render_terminal_studio(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    code_raw = str(data.get("code_snippet") or data.get("code") or "").strip("\n")
    out_raw = str(data.get("output") or "").strip()
    lines = code_raw.splitlines()[:12] or ["# ready"]
    has_beats = bool(data.get("voice_beats") or data.get("items") or data.get("sub_points"))
    term_bottom = 965 if (out_raw and has_beats) else (1145 if out_raw else (1060 if has_beats else 1365))
    term_b = (74, 405, 1006, term_bottom)
    g_box = _ease_out_cubic(_clamp01(progress / 0.16))
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
        if consumed >= typed_budget or ty > term_b[3] - 42:
            break
        show = ln[: max(0, typed_budget - consumed)]
        consumed += len(ln) + 1
        if idx == hl_line:
            stage.draw.rounded_rectangle((term_b[0] + 18, ty - 4, term_b[2] - 18, ty + 34), radius=10, fill=_with_alpha((*world["amber"][:3], 42), g_box))
        stage.draw.text((term_b[0] + 28, ty), f"{idx+1:2d}", font=f_code, fill=_with_alpha(world["muted"], g_box * 0.7))
        col = world["emerald"] if ln.lstrip().startswith(("#", "//")) else (world["cyan"] if any(kw in ln for kw in ("def ", "async ", "return ", "SELECT ", "import ", "class ")) else world["text"])
        stage.draw.text((term_b[0] + 76, ty), show[:54], font=f_code, fill=_with_alpha(col, g_box))
        ty += 40

    if out_raw:
        go = _ease_out_cubic(_clamp01((progress - 0.28) / 0.24))
        if go > 0.03:
            oy0 = term_b[3] + 18
            out_b = (94, oy0, 986, min(1150 if has_beats else 1375, oy0 + 160))
            stage.draw_glass_card(out_b, radius=20, accent_col=world["emerald"], alpha_mul=go, active=True)
            stage.draw_pill(out_b[0] + 92, out_b[1] + 28, "STDOUT", (*world["emerald"][:3], 40), world["emerald"], border_col=world["emerald"], font=_get_font(18, bold=True), alpha_mul=go, pad_x=12, pad_y=4)
            _draw_wrapped_text(stage.draw, (out_b[0] + 28, out_b[1] + 58), out_raw, _get_font(22, mono=True), _with_alpha(world["emerald"], go), (out_b[2] - out_b[0]) - 56, max_lines=3)

    if has_beats:
        raw_b = list(data.get("voice_beats") or data.get("sub_points") or data.get("items") or [])[:4]
        if raw_b:
            y_bt = 1170 if out_raw else (term_b[3] + 22)
            gw = (STAGE_W - 22) // 2
            rows_b = 2 if len(raw_b) > 2 else 1
            gh = min(162, max(120, (STAGE_Y1 - 24 - y_bt - 16) // max(1, rows_b)))
            act_b = min(len(raw_b) - 1, int(max(0.0, min(0.999, progress)) * len(raw_b)))
            for bi, bt in enumerate(raw_b):
                if isinstance(bt, str):
                    bt = {"label": bt, "sub": ""}
                g_raw = _spring_gate(progress, bi, len(raw_b), 0.22)
                if g_raw <= 0.02:
                    continue
                gb, gbdg, gtit, gsub, glnk = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "badge"), _sub_gate(g_raw, "title"), _sub_gate(g_raw, "sub"), _sub_gate(g_raw, "link")
                r_i, c_i = divmod(bi, 2)
                bx0 = STAGE_X0 + c_i * (gw + 22)
                by0 = y_bt + r_i * (gh + 14)
                col = resolve_world_color(world, bt.get("color") if isinstance(bt, dict) else None, _ACCENT_CYCLE[bi % len(_ACCENT_CYCLE)])
                is_act = (act_b == bi and progress > 0.03)
                stage.draw_glass_card((bx0, by0, bx0 + gw, by0 + gh), radius=18, accent_col=col, alpha_mul=gb, active=is_act, layered=is_act)
                if gbdg > 0.02:
                    stage.draw_pill(bx0 + 44, by0 + 28, f"{bi+1:02d}", (*col[:3], 44), col, border_col=col, font=_get_font(17, bold=True, mono=True), alpha_mul=gbdg)
                lbl_t = str(bt.get("label") or bt.get("name") or bt.get("title") or "")[:30]
                sub_t = str(bt.get("sub") or bt.get("desc") or "")[:56]
                if gtit > 0.02:
                    _draw_wrapped_text(stage.draw, (bx0 + 80, by0 + 16), lbl_t, _get_font(21, bold=True), _with_alpha(world["text"], gtit), gw - 94, max_lines=2)
                if sub_t and gsub > 0.02:
                    _draw_wrapped_text(stage.draw, (bx0 + 18, by0 + 76), sub_t, _get_font(18), _with_alpha(world["muted"], gsub), gw - 36, max_lines=2)
                if bi + 1 < len(raw_b) and glnk > 0.02 and c_i == 0:
                    _draw_bezier_comet(stage, (bx0 + gw + 2, by0 + gh // 2), (bx0 + gw + 20, by0 + gh // 2), col, reveal=glnk, progress=progress, phase=bi * 0.25, world=world)


def _render_kinetic_statement(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    kicker = str(data.get("kicker") or "").strip()
    stmt = str(data.get("statement") or data.get("title") or "").strip()
    hl = str(data.get("highlight_word") or "").strip()
    tags = [str(t).strip() for t in (data.get("bottom_tags") or []) if str(t).strip()][:4]
    sub_pts = list(data.get("sub_points") or data.get("voice_beats") or [])[:4]
    if not sub_pts and tags:
        sub_pts = [{"name": tg, "sub": "Verified Key Engineering Rule"} for tg in tags]

    g_card = _ease_out_cubic(_clamp01(progress / 0.16))
    hero_bot = 825 if sub_pts else 1235
    stage.draw_glass_card((80, 415, 1000, hero_bot), radius=30, accent_col=world["cyan"], alpha_mul=g_card, active=True, layered=True)

    # Decorative flanking 3D shapes floating harmoniously inside card margins
    flank_s = str(data.get("shape") or "hexagon")
    _draw_node_visual(stage, 158, 475, 38, 18, 28, world["purple"], g_card * 0.9, shape=flank_s, active=True, progress=progress, phase=0.2)
    _draw_node_visual(stage, 922, hero_bot - 60, 38, 18, 28, world["amber"], g_card * 0.9, shape=data.get("secondary_shape", "diamond"), active=True, progress=progress, phase=1.8)

    if kicker:
        gk = _ease_out_elastic(_clamp01((progress - 0.04) / 0.22))
        stage.draw_pill(540, 468, kicker.upper()[:30], (*world["amber"][:3], 42), world["amber"], border_col=world["amber"], font=_get_font(21, bold=True), alpha_mul=gk, pad_x=22, pad_y=8)

    gs = _ease_out_cubic(_clamp01((progress - 0.08) / 0.24))
    if gs > 0.03:
        f_main = _get_font(44 if sub_pts else 54, bold=True)
        cy = 528 if kicker else 475
        if hl and hl.lower() in stmt.lower():
            idx = stmt.lower().index(hl.lower())
            before = stmt[:idx].strip()
            exact_hl = stmt[idx:idx + len(hl)]
            after = stmt[idx + len(hl):].strip()
            if before:
                cy = _draw_wrapped_text(stage.draw, (124, cy), before, f_main, _with_alpha(world["text"], gs), 832, line_gap=8, align="center", max_lines=2) + 10
            stage.add_glow_orb(540, cy + 36, 130, world["cyan"], alpha=int(120 * gs))
            cy = _draw_wrapped_text(stage.draw, (124, cy), exact_hl, _get_font(54 if sub_pts else 64, bold=True), _with_alpha(world["cyan"], gs), 832, line_gap=8, align="center", max_lines=2) + 10
            if after:
                _draw_wrapped_text(stage.draw, (124, cy), after, f_main, _with_alpha(world["text"], gs), 832, line_gap=8, align="center", max_lines=2)
        else:
            _draw_wrapped_text(stage.draw, (124, cy + 16), stmt, f_main, _with_alpha(world["text"], gs), 832, line_gap=10, align="center", max_lines=4)

    # Progressive Voice-Synced Highlight Cards Below Hero Statement
    if sub_pts:
        n_sp = len(sub_pts)
        y_sp = hero_bot + 24
        rh_sp = min(155, (STAGE_Y1 - 24 - y_sp) // max(1, n_sp))
        act_i = min(n_sp - 1, int(max(0.0, min(0.999, progress)) * n_sp))
        prev_pt = None
        for i, sp in enumerate(sub_pts):
            if isinstance(sp, str):
                sp = {"name": sp, "sub": ""}
            g_raw = _spring_gate(progress, i, n_sp, 0.22)
            if g_raw <= 0.02:
                continue
            gb, gbdg, gt, gsub, glnk = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "badge"), _sub_gate(g_raw, "title"), _sub_gate(g_raw, "sub"), _sub_gate(g_raw, "link")
            col = resolve_world_color(world, sp.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            ry = y_sp + i * rh_sp
            ch = rh_sp - 16
            is_act = (act_i == i and progress > 0.04)
            if prev_pt is not None:
                _draw_bezier_comet(stage, prev_pt, (132, ry + 4), col, reveal=gb, progress=progress, phase=i * 0.2, world=world)
            stage.draw_glass_card((80, ry, 1000, ry + ch), radius=19, accent_col=col, alpha_mul=gb, active=is_act, layered=is_act)
            if gbdg > 0.02:
                stage.draw_pill(134, ry + ch // 2, f"{i+1:02d}", (*col[:3], 44), col, border_col=col, font=_get_font(20, bold=True, mono=True), alpha_mul=gbdg)
            nm = str(sp.get("name") or sp.get("label") or sp.get("title") or "").strip()
            sb = str(sp.get("sub") or sp.get("desc") or "").strip()
            if gt > 0.02:
                _draw_wrapped_text(stage.draw, (186, ry + (16 if sb else ch // 2 - 18)), nm, _get_font(25, bold=True), _with_alpha(world["text"], gt), 785, max_lines=1 if sb else 2)
            if sb and gsub > 0.02:
                _draw_wrapped_text(stage.draw, (186, ry + 56), sb, _get_font(20), _with_alpha(world["muted"], gsub), 785, max_lines=2)
            prev_pt = (132, ry + ch) if glnk > 0.02 or i + 1 < n_sp else None
    elif tags:
        tx = 540 - (len(tags) * 205) // 2 + 100
        for i, tg in enumerate(tags):
            gt = _ease_out_cubic(_spring_gate(progress, i + 1, len(tags) + 1, 0.25))
            col = resolve_world_color(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_pill(tx + i * 205, 1320, tg[:16], (*col[:3], 36), world["text"], border_col=(*col[:3], 185), font=_get_font(21, bold=True), alpha_mul=gt, pad_x=16, pad_y=8)


def _render_custom_scene(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    blocks = data.get("blocks") or []
    if not blocks:
        if data.get("bullets") or data.get("warning_box"):
            _render_concept_cards(stage, data, progress, world)
        elif data.get("nodes") or data.get("steps") or data.get("stages"):
            _render_iso_architecture(stage, data, progress, world)
        elif data.get("entries"):
            _render_memory_lanes(stage, data, progress, world)
        elif data.get("bars"):
            _render_benchmark_3d(stage, data, progress, world)
        else:
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
        g = _spring_gate(progress, idx, n, 0.24)
        a_mul = _sub_gate(g, "box")
        g_bdg = _sub_gate(g, "badge")
        g_tit = _sub_gate(g, "title")
        g_sub = _sub_gate(g, "sub")
        if a_mul <= 0.03:
            continue
        col = resolve_world_color(world, blk.get("color"), _ACCENT_CYCLE[idx % len(_ACCENT_CYCLE)])
        slide_y = int((1.0 - a_mul) * 22)

        if btype == "big_stat":
            h = 198
            b = (84, y + slide_y, 996, y + slide_y + h)
            stage.draw_glass_card(b, radius=26, accent_col=col, alpha_mul=a_mul, active=True, layered=True)
            val_txt = _animate_counter_text(blk.get("value", "0"), _clamp01((progress - 0.12) / 0.55))
            if g_bdg > 0.02:
                _draw_wrapped_text(stage.draw, (110, b[1] + 24), val_txt, _get_font(76, bold=True), _with_alpha(col, g_bdg), 860, align="center", max_lines=1)
            if g_tit > 0.02:
                _draw_wrapped_text(stage.draw, (110, b[1] + 122), str(blk.get("label", "")), _get_font(27, bold=True), _with_alpha(world["text"], g_tit), 860, align="center", max_lines=2)
            y += h + 24

        elif btype == "question_card":
            txt = str(blk.get("text") or blk.get("title") or "").strip()
            lines_n = min(4, _est_lines(txt, _get_font(31, bold=True), 830))
            h = max(116, 48 + lines_n * 42)
            b = (84, y + slide_y, 996, y + slide_y + h)
            stage.draw_glass_card(b, radius=24, accent_col=col, alpha_mul=a_mul, flip_t=g if g < 0.85 else 1.0)
            if g_tit > 0.02:
                _draw_wrapped_text(stage.draw, (124, b[1] + 24), txt, _get_font(31, bold=True), _with_alpha(world["text"], g_tit), 830, line_gap=8, align="center", max_lines=4)
            y += h + 22

        elif btype == "pills":
            items = [str(p).strip() for p in (blk.get("items") or []) if str(p).strip()][:5]
            if items:
                cols_p = min(3, max(2, len(items)))
                pw = (912 - (cols_p - 1) * 16) // cols_p
                for j, ptxt in enumerate(items):
                    jp_raw = _spring_gate(progress, idx * 2 + j, max(3, n + len(items)), 0.22)
                    jp = _sub_gate(jp_raw, "badge")
                    if jp <= 0.03:
                        continue
                    r_i, c_i = divmod(j, cols_p)
                    pcx = 84 + c_i * (pw + 16) + pw // 2
                    pcy = y + slide_y + 34 + r_i * 78
                    pc = resolve_world_color(world, _ACCENT_CYCLE[(idx + j) % len(_ACCENT_CYCLE)])
                    stage.draw_pill(pcx, pcy, ptxt[:18], (*pc[:3], 34), world["text"], border_col=(*pc[:3], 185), font=_get_font(22, bold=True), alpha_mul=jp, pad_x=18, pad_y=10)
                rows_n = (len(items) + cols_p - 1) // cols_p
                y += rows_n * 78 + 20

        elif btype == "flow_chain":
            steps = [str(s).strip() for s in (blk.get("steps") or []) if str(s).strip()][:4]
            if steps:
                m = len(steps)
                bw = (912 - (m - 1) * 34) // m
                for j, st in enumerate(steps):
                    sg_raw = _spring_gate(progress, j, m, 0.24)
                    if sg_raw <= 0.02:
                        continue
                    sb, st_a, sl_a = _sub_gate(sg_raw, "box"), _sub_gate(sg_raw, "title"), _sub_gate(sg_raw, "link")
                    sx0 = 84 + j * (bw + 34)
                    sc = resolve_world_color(world, _ACCENT_CYCLE[j % len(_ACCENT_CYCLE)])
                    stage.draw_glass_card((sx0, y + slide_y, sx0 + bw, y + slide_y + 106), radius=18, accent_col=sc, alpha_mul=sb, active=(int(progress * m) == j))
                    if st_a > 0.02:
                        _draw_wrapped_text(stage.draw, (sx0 + 10, y + slide_y + 24), st, _get_font(21, bold=True), _with_alpha(world["text"], st_a), bw - 20, align="center", max_lines=3)
                    if j < m - 1 and sl_a > 0.02:
                        _draw_bezier_comet(stage, (sx0 + bw + 2, y + slide_y + 53), (sx0 + bw + 32, y + slide_y + 53), sc, reveal=sl_a, progress=progress, phase=j * 0.3, world=world)
                y += 130

        elif btype == "list_cards":
            items = (blk.get("items") or [])[:5]
            for j, it in enumerate(items):
                if y > STAGE_Y1 - 95:
                    break
                if isinstance(it, str):
                    it = {"title": it}
                ig_raw = _spring_gate(progress, j, max(1, len(items)), 0.22)
                if ig_raw <= 0.02:
                    continue
                ig = _sub_gate(ig_raw, "box")
                ig_ico = _sub_gate(ig_raw, "badge")
                ig_tit = _sub_gate(ig_raw, "title")
                ig_sub = _sub_gate(ig_raw, "sub")
                ic = resolve_world_color(world, it.get("color"), _ACCENT_CYCLE[j % len(_ACCENT_CYCLE)])
                title = str(it.get("title") or it.get("name") or "").strip()
                sub = str(it.get("sub") or it.get("desc") or "").strip()
                h = 104 if sub else 78
                b = (84, y, 996, y + h)
                stage.draw_glass_card(b, radius=20, accent_col=ic, alpha_mul=ig, active=(j == int(progress * len(items))))
                icon_kind = str(it.get("icon") or "check")
                if ig_ico > 0.02:
                    if ":" in icon_kind or icon_kind.lower() in ICON_ALIASES:
                        im = _resolve_iconify_if_any(icon_kind, ic, 48)
                        if im:
                            stage.fg.alpha_composite(im.resize((44, 44)), (110, y + (h - 44) // 2))
                        else:
                            draw_vector_glyph(stage, 132, y + h // 2, "check", 20, ic, ig_ico)
                    else:
                        draw_vector_glyph(stage, 132, y + h // 2, icon_kind, 20, ic, ig_ico)
                if ig_tit > 0.02:
                    _draw_wrapped_text(stage.draw, (182, y + (16 if sub else 22)), title, _get_font(26, bold=True), _with_alpha(world["text"], ig_tit), 785, max_lines=1)
                if sub and ig_sub > 0.02:
                    _draw_wrapped_text(stage.draw, (182, y + 54), sub, _get_font(21), _with_alpha(world["muted"], ig_sub), 785, max_lines=1)
                y += h + 16

        elif btype == "banner":
            txt = str(blk.get("text") or "").strip()
            gb = _footer_gate(progress) if idx == len(blocks[:5]) - 1 else g_tit
            if gb <= 0.03:
                continue
            h = 88
            stage.draw_glass_card((84, y + slide_y, 996, y + slide_y + h), radius=20, accent_col=col, alpha_mul=gb, active=True)
            _draw_wrapped_text(stage.draw, (114, y + slide_y + 24), txt, _get_font(26, bold=True), _with_alpha(col, gb), 852, align="center", max_lines=2)
            y += h + 20

        elif btype == "code":
            txt = str(blk.get("text") or blk.get("code") or "").strip()
            clines = txt.splitlines()[:4]
            h = 46 + len(clines) * 34
            stage.draw_glass_card((84, y + slide_y, 996, y + slide_y + h), radius=18, accent_col=col, alpha_mul=a_mul)
            for k, cl in enumerate(clines):
                stage.draw.text((114, y + slide_y + 22 + k * 34), cl[:56], font=_get_font(22, mono=True), fill=_with_alpha(col, a_mul))
            y += h + 20

    # Fill lower void cleanly when custom_scene only has 1-2 short top blocks (e.g. question_card + banner)
    if y < STAGE_Y1 - 360:
        g_m = _ease_out_cubic(_clamp01((progress - 0.15) / 0.30))
        if g_m > 0.03:
            cy_m = (y + STAGE_Y1 - 24) // 2
            rad_m = min(195, (STAGE_Y1 - y - 90) // 2)
            box_b = (84, y + 12, 996, STAGE_Y1 - 22)
            stage.draw_glass_card(box_b, radius=26, accent_col=world["cyan"], alpha_mul=g_m, active=True, layered=True)
            draw_procedural_3d_mesh(stage, 540, cy_m - 12, rad_m, "geodesic_sphere", world["cyan"], progress=progress, active=True, alpha_mul=g_m, secondary_color=world["purple"])
            cap_s = str(data.get("title") or "Architecture Breakdown").strip()
            stage.draw_pill(540, STAGE_Y1 - 62, cap_s[:36], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g_m, pad_x=22, pad_y=8)


# =========================================================================
# LAYOUT FAMILY 2: SPATIAL COMPOSER & AI MULTI-LAYER <svg> RENDERER
# =========================================================================
def _render_spatial_canvas(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    """
    Spatial Composer: accepts freeform normalized elements (`x, y, w, h` inside 0..1000 canvas)
    plus semantic `connections` (`from` -> `to`) so AI can compose novel spatial diagrams on demand.
    """
    elems = list(data.get("elements") or data.get("zones") or data.get("nodes") or _harvest_generic_items(data))[:10]
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
        if data.get("entries"):
            _render_memory_lanes(stage, data, progress, world)
        elif data.get("bars"):
            _render_benchmark_3d(stage, data, progress, world)
        elif data.get("left_points") or data.get("right_points"):
            _render_iso_comparison(stage, data, progress, world)
        elif data.get("alerts") or data.get("problem_title") or data.get("challenge"):
            _render_incident_radar(stage, data, progress, world)
        elif data.get("table_data"):
            _render_sql_or_diff_or_api(stage, data, progress, world, mode="sql")
        elif data.get("code_snippet") or data.get("command"):
            _render_terminal_studio(stage, data, progress, world)
        elif data.get("main_value") or data.get("telemetry"):
            _render_radial_gauge(stage, data, progress, world)
        elif data.get("satellites"):
            _render_node_graph(stage, data, progress, world)
        elif data.get("nodes") or data.get("steps") or data.get("stages"):
            _render_iso_architecture(stage, data, progress, world)
        else:
            _render_custom_scene(stage, data, progress, world)
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
    layers = list(data.get("layers") or data.get("nodes") or data.get("items") or _harvest_generic_items(data))[:5]
    if not layers:
        return
    n = len(layers)
    start_y = STAGE_Y0 + 60
    step_y = min(185, (STAGE_H - 135) // max(1, n))
    prev_cx = None
    for i, lay in enumerate(layers):
        if isinstance(lay, str):
            lay = {"name": lay}
        g = _spring_gate(progress, i, n, 0.24)
        if g <= 0.02:
            continue
        g_box = _sub_gate(g, "box")
        g_slab = _sub_gate(g, "badge")
        g_tit = _sub_gate(g, "title")
        g_sub = _sub_gate(g, "sub")
        g_lnk = _sub_gate(g, "link")
        col = resolve_world_color(world, lay.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        cy = start_y + i * step_y + 72
        dy = int((1.0 - _micro_bounce(g_box)) * 38)
        active = (int(progress * n) == i and progress > 0.03)

        # Left 3D isometric wafer/slab + Right glass explanation card
        slab_cx = 235
        if prev_cx is not None:
            _draw_bezier_comet(stage, prev_cx, (slab_cx, cy + dy - 42), col, reveal=g_box, progress=progress, phase=i * 0.2, world=world)
        if g_slab > 0.02:
            draw_3d_shape(stage, slab_cx, cy + dy - 18, 125, 44, 34, col, g_slab, shape=lay.get("shape", "layers_wafer"), active=active, progress=progress, phase=i * 0.5)
            stage.draw_pill(slab_cx, cy + dy - 20, f"L{n - i}", world["card_alt"], world["text"], border_col=col, font=_get_font(20, bold=True), alpha_mul=g_slab, pad_x=14, pad_y=4)

        cb = (395, cy + dy - 56, 998, cy + dy + 64)
        stage.draw_glass_card(cb, radius=20, accent_col=col, alpha_mul=g_box, active=active)
        if g_slab > 0.02:
            stage.draw.line((365, cy + dy, 395, cy + dy), fill=_with_alpha((*col[:3], 190), g_slab), width=3)
        name = str(lay.get("name") or lay.get("title") or "").strip()
        sub = str(lay.get("sub") or lay.get("role") or lay.get("desc") or "").strip()
        if g_tit > 0.02:
            _draw_wrapped_text(stage.draw, (cb[0] + 24, cb[1] + 18), name, _get_font(27, bold=True), _with_alpha(world["text"], g_tit), cb[2] - cb[0] - 48, max_lines=1)
        if sub and g_sub > 0.02:
            _draw_wrapped_text(stage.draw, (cb[0] + 24, cb[1] + 60), sub, _get_font(21), _with_alpha(world["muted"], g_sub), cb[2] - cb[0] - 48, max_lines=2)
        prev_cx = (slab_cx, cy + dy + 16) if g_lnk > 0.02 or i + 1 < n else None
    gf = _footer_gate(progress)
    ft_txt = str(data.get("footer") or data.get("summary") or "").strip()
    if gf > 0.03 and ft_txt:
        stage.draw_glass_card((80, STAGE_Y1 - 78, 1000, STAGE_Y1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
        _draw_wrapped_text(stage.draw, (112, STAGE_Y1 - 60), ft_txt[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)


def _render_pyramid_or_funnel(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any], is_funnel: bool = False) -> None:
    tiers = list(data.get("tiers") or data.get("stages") or data.get("items") or _harvest_generic_items(data))[:5]
    if not tiers:
        return
    n = len(tiers)
    tier_h = min(155, (STAGE_H - 135) // max(1, n))
    y_start = STAGE_Y0 + 50
    for i, tr in enumerate(tiers):
        if isinstance(tr, str):
            tr = {"name": tr}
        g = _spring_gate(progress, i, n, 0.24)
        if g <= 0.02:
            continue
        g_box = _sub_gate(g, "box")
        g_bdg = _sub_gate(g, "badge")
        g_tit = _sub_gate(g, "title")
        g_sub = _sub_gate(g, "sub")
        col = resolve_world_color(world, tr.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        frac_top = (1.0 - i / max(1, n)) if is_funnel else ((i + 0.45) / max(1, n))
        frac_bot = (1.0 - (i + 0.85) / max(1, n)) if is_funnel else ((i + 1.15) / max(1, n))
        w_top = max(140, int(440 * max(0.28, frac_top)))
        w_bot = max(120, int(440 * max(0.24, frac_bot)))
        cx = 290
        y0 = y_start + i * (tier_h + 14)
        y1 = y0 + tier_h - 14
        pts = [(cx - w_top // 2, y0), (cx + w_top // 2, y0), (cx + w_bot // 2, y1), (cx - w_bot // 2, y1)]
        stage.add_glow_orb(cx, (y0 + y1) // 2, w_top // 2, col, alpha=int(85 * g_box))
        stage.draw.polygon(pts, fill=_with_alpha((*col[:3], 178), g_box), outline=_with_alpha(world["glass_rim"], g_box), width=2)

        val = str(tr.get("value") or tr.get("metric") or "").strip()
        if val and g_bdg > 0.02:
            stage.draw_pill(cx, (y0 + y1) // 2, val[:14], world["card_alt"], world["text"], border_col=col, font=_get_font(21, bold=True), alpha_mul=g_bdg, pad_x=12, pad_y=4)

        cb = (545, y0 + 4, 1004, y1 - 4)
        stage.draw_glass_card(cb, radius=18, accent_col=col, alpha_mul=g_box, active=(int(progress * n) == i))
        if g_bdg > 0.02:
            stage.draw.line((cx + (w_top + w_bot) // 4, (y0 + y1) // 2, cb[0], (y0 + y1) // 2), fill=_with_alpha(col, g_bdg), width=3)
        name = str(tr.get("name") or tr.get("title") or "").strip()
        sub = str(tr.get("sub") or tr.get("desc") or "").strip()
        if g_tit > 0.02:
            _draw_wrapped_text(stage.draw, (cb[0] + 20, y0 + 18), name, _get_font(25, bold=True), _with_alpha(world["text"], g_tit), cb[2] - cb[0] - 40, max_lines=1)
        if sub and g_sub > 0.02:
            _draw_wrapped_text(stage.draw, (cb[0] + 20, y0 + 56), sub, _get_font(20), _with_alpha(world["muted"], g_sub), cb[2] - cb[0] - 40, max_lines=2)


def _render_grid_2x2(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any], is_matrix: bool = False) -> None:
    cells = list(data.get("quadrants") or data.get("stats") or data.get("cards") or data.get("items") or _harvest_generic_items(data))[:4]
    if not cells:
        return
    pad_top = 80 if is_matrix else 40
    cw, ch = 442, (STAGE_H - pad_top - 70) // 2
    x_cols = [STAGE_X0 + 20, STAGE_X0 + 20 + cw + 28]
    y_rows = [STAGE_Y0 + pad_top, STAGE_Y0 + pad_top + ch + 28]

    if is_matrix:
        gx = _ease_out_cubic(_clamp01(progress / 0.16))
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
        if g <= 0.02:
            continue
        g_box = _sub_gate(g, "box")
        g_bdg = _sub_gate(g, "badge")
        g_tit = _sub_gate(g, "title")
        g_sub = _sub_gate(g, "sub")
        col = resolve_world_color(world, cell.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        active = bool(cell.get("highlight")) or (int(progress * 4) == i and progress > 0.03)
        stage.draw_glass_card(b, radius=24, accent_col=col, alpha_mul=g_box, active=active, flip_t=g if g < 0.85 else 1.0, layered=active)

        val = str(cell.get("value") or "").strip()
        title = str(cell.get("title") or cell.get("label") or "").strip()
        sub = str(cell.get("sub") or cell.get("desc") or "").strip()
        if val and not is_matrix:
            anim_v = _animate_counter_text(val, _clamp01((progress - 0.10) / 0.55))
            if g_bdg > 0.02:
                _draw_wrapped_text(stage.draw, (b[0] + 24, b[1] + 44), anim_v, _get_font(56, bold=True), _with_alpha(col, g_bdg), cw - 48, align="center", max_lines=1)
            if g_tit > 0.02:
                _draw_wrapped_text(stage.draw, (b[0] + 24, b[1] + 132), title, _get_font(28, bold=True), _with_alpha(world["text"], g_tit), cw - 48, align="center", max_lines=2)
            if sub and g_sub > 0.02:
                _draw_wrapped_text(stage.draw, (b[0] + 24, b[1] + 218), sub, _get_font(21), _with_alpha(world["muted"], g_sub), cw - 48, align="center", max_lines=3)
        else:
            if cell.get("icon") or cell.get("shape"):
                if g_bdg > 0.02:
                    _draw_node_visual(stage, b[0] + cw // 2, b[1] + 74, 38, 18, 26, col, g_bdg, shape=cell.get("shape", ""), icon=cell.get("icon", ""), label=title, active=active, progress=progress, phase=i * 0.6)
                ty = b[1] + 150
            else:
                if g_bdg > 0.02:
                    stage.draw_pill(b[0] + 84, b[1] + 42, f"Q{i+1}", (*col[:3], 40), col, border_col=col, font=_get_font(20, bold=True), alpha_mul=g_bdg, pad_x=14, pad_y=4)
                ty = b[1] + 84
            if g_tit > 0.02:
                _draw_wrapped_text(stage.draw, (b[0] + 24, ty), title, _get_font(28, bold=True), _with_alpha(world["text"], g_tit), cw - 48, align="center", max_lines=2)
            if sub and g_sub > 0.02:
                _draw_wrapped_text(stage.draw, (b[0] + 24, ty + 78), sub, _get_font(21), _with_alpha(world["muted"], g_sub), cw - 48, align="center", max_lines=4)


def _render_benchmark_3d(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    bars = list(data.get("bars") or data.get("metrics") or data.get("items") or [])[:5]
    if not bars:
        bars = [{"label": it["name"], "value": 80 - i * 15, "display": it.get("sub") or it.get("val") or ""} for i, it in enumerate(_harvest_generic_items(data)[:3])]
    n = len(bars)
    vals: List[float] = []
    for b in bars:
        try:
            vals.append(float(b.get("score") or b.get("value_num") or re.sub(r"[^0-9.]", "", str(b.get("value", "50"))) or 50))
        except Exception:
            vals.append(50.0)
    pos_vals = [v for v in vals if v > 0] or [1.0]
    max_v = max(pos_vals)
    min_v = min(pos_vals)

    # Detect lower-is-better latency/downtime metrics automatically vs explicit `is_winner`
    explicit_wins = [i for i, b in enumerate(bars) if isinstance(b, dict) and b.get("is_winner")]
    title_l = f"{data.get('title', '')} {' '.join(str(b.get('display', '')) for b in bars if isinstance(b, dict))}".lower()
    lower_is_better = any(kw in title_l for kw in ("downtime", "latency", "lag", "loss", "ms", "wait", "slow", "lock"))
    if explicit_wins:
        win_idx = explicit_wins[0]
    elif lower_is_better:
        win_idx = vals.index(min(vals))
    else:
        win_idx = vals.index(max_v)

    bars_zone_h = 560 if n <= 4 else 690
    row_h = min(180, bars_zone_h // max(1, n))
    y0 = STAGE_Y0 + 18
    for i, b_item in enumerate(bars):
        if isinstance(b_item, str):
            b_item = {"label": b_item, "value": "100"}
        g = _spring_gate(progress, i, n, 0.25)
        if g <= 0.02:
            continue
        g_box = _sub_gate(g, "box")
        g_tit = _sub_gate(g, "title")
        g_bar = _sub_gate(g, "link")
        is_win = (i == win_idx)
        col = world["emerald"] if is_win else resolve_world_color(world, b_item.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        ry = y0 + i * row_h
        lbl = str(b_item.get("label") or b_item.get("name") or "").strip()
        raw_disp = str(b_item.get("display") or b_item.get("value") or int(vals[i]))
        val_disp = _animate_counter_text(raw_disp, max(g_tit, g_bar))

        stage.draw_glass_card((76, ry, 1004, ry + row_h - 18), radius=22, accent_col=col, alpha_mul=g_box, active=is_win, layered=is_win)
        lbl_col = col if is_win else world["text"]
        if g_tit > 0.02:
            if is_win:
                draw_vector_glyph(stage, 118, ry + 34, "check", 16, col, g_tit, with_badge=True)
                stage.draw.text((146, ry + 18), lbl[:30], font=_get_font(27, bold=True), fill=_with_alpha(lbl_col, g_tit))
            else:
                stage.draw.text((108, ry + 18), lbl[:32], font=_get_font(27, bold=True), fill=_with_alpha(lbl_col, g_tit))
            _draw_wrapped_text(stage.draw, (640, ry + 18), val_disp, _get_font(26, bold=True), _with_alpha(col, g_tit), 336, align="right", max_lines=1)

        # 3D Isometric extruded bar (sweeps left-to-right sequentially with g_bar)
        bx0, by0, bx_max = 108, ry + 68, 966
        ratio = vals[i] / max(1e-5, max_v)
        vis_frac = (ratio ** 0.45) if (max_v / max(1e-5, min_v) > 20.0) else ratio
        bw = max(54, int((bx_max - bx0) * vis_frac * max(0.08, g_bar)))
        bh = 38
        stage.draw.rounded_rectangle((bx0, by0, bx_max, by0 + bh), radius=12, fill=_with_alpha(world["card_layer"], g_box))
        if g_bar > 0.02:
            stage.add_glow_orb(bx0 + bw - 12, by0 + bh // 2, 28, col, alpha=int(130 * g_bar))
            stage.draw.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=12, fill=_with_alpha(col, g_bar))
            stage.draw.line((bx0 + 10, by0 + 4, max(bx0 + 14, bx0 + bw - 10), by0 + 4), fill=_with_alpha((255, 255, 255, 175), g_bar), width=3)

    # Bottom Impact / Speedup Hero Card reveals last in sync with conclusion voice
    sum_y0 = max(y0 + n * row_h + 18, STAGE_Y1 - 435)
    if sum_y0 < STAGE_Y1 - 180:
        gs = _footer_gate(progress)
        if gs > 0.03:
            win_item = bars[win_idx] if isinstance(bars[win_idx], dict) else {"label": str(bars[win_idx])}
            win_lbl = str(win_item.get("label") or win_item.get("name") or "Optimal")
            win_val = str(win_item.get("display") or win_item.get("value") or "")
            factor = max_v / max(1e-5, vals[win_idx]) if (lower_is_better and vals[win_idx] > 0) else (vals[win_idx] / max(1e-5, min_v))
            badge_str = str(data.get("winner_badge") or (f"{int(round(factor))}x IMPROVEMENT" if factor >= 2.0 else "PRODUCTION WINNER"))
            cb = (76, sum_y0, 1004, STAGE_Y1 - 24)
            stage.draw_glass_card(cb, radius=26, accent_col=world["emerald"], alpha_mul=gs, active=True, layered=True)
            _draw_node_visual(stage, 190, (sum_y0 + STAGE_Y1 - 24) // 2 - 12, 54, 24, 38, world["emerald"], gs, shape="rocket", icon="trophy", label=win_lbl, active=True, progress=progress)
            stage.draw_pill(595, sum_y0 + 54, badge_str[:28], (*world["emerald"][:3], 44), world["emerald"], border_col=world["emerald"], font=_get_font(23, bold=True), alpha_mul=gs, pad_x=22, pad_y=8)
            _draw_wrapped_text(stage.draw, (285, sum_y0 + 106), f"{win_lbl}: {win_val}", _get_font(36, bold=True), _with_alpha(world["text"], gs), 690, align="center", max_lines=2)
            _draw_wrapped_text(stage.draw, (285, sum_y0 + 215), "Benchmarked Zero-Lock Architecture Performance", _get_font(22), _with_alpha(world["muted"], gs), 690, align="center", max_lines=1)


def _render_radial_gauge(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    pct = float(data.get("gauge_percent") or data.get("percent") or data.get("score") or 92)
    pct = max(0.0, min(100.0, pct))
    g_arc = _ease_out_cubic(_clamp01(progress / 0.55))
    cx, cy, rad = 540, 645, 225
    ac = resolve_world_color(world, data.get("color"), "emerald" if pct >= 70 else ("amber" if pct >= 40 else "rose"))

    stage.draw_glass_card((100, STAGE_Y0 + 12, 980, 935), radius=30, accent_col=ac, alpha_mul=_clamp01(progress / 0.18), active=True, layered=True)
    bbox = (cx - rad, cy - rad, cx + rad, cy + rad)
    stage.draw.arc(bbox, start=135, end=405, fill=_with_alpha(world["card_layer"], stage.t_alpha), width=34)
    sweep = int(270 * (pct / 100.0) * g_arc)
    if sweep > 2:
        stage.add_glow_orb(cx, cy, rad + 18, ac, alpha=int(95 * g_arc))
        stage.draw.arc(bbox, start=135, end=135 + sweep, fill=_with_alpha(ac, stage.t_alpha), width=34)

    val_label = _animate_counter_text(str(data.get("main_value") or data.get("value") or f"{int(pct)}%"), g_arc)
    _draw_wrapped_text(stage.draw, (cx - 190, cy - 58), val_label, _get_font(72, bold=True), _with_alpha(world["text"], stage.t_alpha), 380, align="center", max_lines=1)
    lbl = str(data.get("main_unit") or data.get("label") or data.get("subtitle") or "SCORE").strip()
    _draw_wrapped_text(stage.draw, (cx - 190, cy + 36), lbl, _get_font(24, bold=True), _with_alpha(ac, stage.t_alpha), 380, align="center", max_lines=2)

    sub_cards = list(data.get("telemetry") or data.get("metrics") or data.get("items") or [])[:3]
    if not sub_cards:
        sub_cards = [{"label": "SLA", "val": "99.99%"}, {"label": "SYNC", "val": "Real-Time"}, {"label": "LOCKS", "val": "Zero"}]
    cw = (880 - max(0, len(sub_cards) - 1) * 20) // len(sub_cards)
    for i, sc in enumerate(sub_cards):
        if isinstance(sc, str):
            sc = {"label": sc, "val": ""}
        g = _spring_gate(progress, i + 1, len(sub_cards) + 1, 0.25)
        a_mul = _ease_out_cubic(g)
        sx0 = 100 + i * (cw + 20)
        cc = resolve_world_color(world, sc.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        stage.draw_glass_card((sx0, 965, sx0 + cw, 1295), radius=22, accent_col=cc, alpha_mul=a_mul)
        _draw_wrapped_text(stage.draw, (sx0 + 14, 1018), _animate_counter_text(sc.get("val") or sc.get("value") or "", g), _get_font(38, bold=True), _with_alpha(cc, a_mul), cw - 28, align="center", max_lines=1)
        _draw_wrapped_text(stage.draw, (sx0 + 14, 1105), str(sc.get("label") or sc.get("title") or ""), _get_font(23, bold=True), _with_alpha(world["text"], a_mul), cw - 28, align="center", max_lines=3)


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
    msgs = list(data.get("messages") or data.get("steps") or _harvest_generic_items(data))[:7]
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
    tables = list(data.get("tables") or data.get("entities") or _harvest_generic_items(data))[:4]
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
    states = list(data.get("states") or data.get("nodes") or _harvest_generic_items(data))[:5]
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
    commits = list(data.get("commits") or data.get("steps") or _harvest_generic_items(data))[:6]
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
        br = str(cm.get("branch") or ("main" if i % 3 == 0 else ("feature" if i % 3 == 1 else "hotfix"))).lower()
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
    spans = list(data.get("spans") or data.get("frames") or _harvest_generic_items(data))[:10]
    if not spans:
        return
    g_box = _ease_out_cubic(_clamp01(progress / 0.18))
    stage.draw_glass_card((68, STAGE_Y0 + 20, 1012, STAGE_Y1 - 40), radius=24, accent_col=world["amber"], alpha_mul=g_box)
    depths = [int(sp.get("depth", i % 5)) if isinstance(sp, dict) else i for i, sp in enumerate(spans)]
    max_d = max(1, max(depths))
    avail_h = max(320, (STAGE_Y1 - 70) - (STAGE_Y0 + 60))
    row_step = min(145, max(108, avail_h // max(2, max_d + 1)))
    box_h = min(110, row_step - 16)
    stack_total_h = (max_d + 1) * row_step - 16
    base_bottom = (STAGE_Y0 + 45) + (avail_h + stack_total_h) // 2
    base_bottom = min(STAGE_Y1 - 56, max(STAGE_Y0 + 220, base_bottom))
    inner_x0, inner_w = 94, 892
    for i, sp in enumerate(spans):
        if isinstance(sp, str):
            sp = {"name": sp, "depth": i, "start": 0.0, "width": 1.0 - i * 0.1}
        g = _spring_gate(progress, i, len(spans), 0.22)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        d = int(sp.get("depth", i % 5))
        s = _clamp01(float(sp.get("start", 0.0)))
        w = max(0.16, min(1.0 - s, float(sp.get("width", max(0.28, 1.0 - i * 0.16)))))
        hot = bool(sp.get("hot", False))
        col = world["rose"] if hot else resolve_world_color(world, sp.get("color"), _ACCENT_CYCLE[d % len(_ACCENT_CYCLE)])
        x0 = int(inner_x0 + s * inner_w)
        x1 = min(inner_x0 + inner_w, int(x0 + w * inner_w * _ease_out_cubic(g)))
        x1 = max(x0 + 72, x1)
        y0 = base_bottom - (d + 1) * row_step + 16
        y0 = max(STAGE_Y0 + 46, y0)
        stage.draw_glass_card((x0, y0, x1, y0 + box_h), radius=14, accent_col=col, alpha_mul=a_mul, active=hot)
        txt_max = max(36, x1 - x0 - 28)
        raw_nm = str(sp.get("name") or "")
        f_nm = _get_font(21 if txt_max >= 200 else 17, bold=True)
        while len(raw_nm) > 6 and stage.draw.textlength(raw_nm, font=f_nm) > txt_max:
            raw_nm = raw_nm[:-4].rstrip() + "..."
        stage.draw.text((x0 + 14, y0 + 20), raw_nm, font=f_nm, fill=_with_alpha(world["text"], a_mul))
        if sp.get("duration") or sp.get("pct"):
            sub_s = str(sp.get("duration") or sp.get("pct"))
            f_sb = _get_font(18, mono=True)
            while len(sub_s) > 4 and stage.draw.textlength(sub_s, font=f_sb) > txt_max:
                sub_s = sub_s[:-4].rstrip() + ".."
            stage.draw.text((x0 + 14, y0 + 56), sub_s, font=f_sb, fill=_with_alpha(col, a_mul))


def _render_latency_waterfall(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    spans = list(data.get("spans") or data.get("traces") or data.get("items") or _harvest_generic_items(data))[:7]
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
    """Renders BOTH WAL/LSN Offset Entries (`entries` schema) AND multi-lane memory/storage diagrams."""
    entries = list(data.get("entries") or [])[:5]
    if entries:
        g0 = _ease_out_cubic(_clamp01(progress / 0.18))
        n = len(entries)
        hdr_b = (74, STAGE_Y0 + 12, 1006, STAGE_Y0 + 128)
        stage.draw_glass_card(hdr_b, radius=22, accent_col=world["cyan"], alpha_mul=g0, active=True)
        active_idx = min(n - 1, int(progress * n))
        cur_addr = str(entries[active_idx].get("address") or "0x00A1") if isinstance(entries[active_idx], dict) else "0x00A1"
        stage.draw.text((104, hdr_b[1] + 20), "SEQUENTIAL WAL BUFFER STREAM", font=_get_font(23, bold=True), fill=_with_alpha(world["cyan"], g0))
        stage.draw_pill(876, hdr_b[1] + 34, f"CURSOR {cur_addr}", (*world["emerald"][:3], 42), world["emerald"], border_col=world["emerald"], font=_get_font(19, bold=True, mono=True), alpha_mul=g0)
        fill_w = max(60, int(860 * (0.15 + 0.85 * progress)))
        stage.draw.rounded_rectangle((104, hdr_b[1] + 72, 964, hdr_b[1] + 94), radius=10, fill=_with_alpha(world["card_layer"], g0))
        stage.draw.rounded_rectangle((104, hdr_b[1] + 72, 104 + fill_w, hdr_b[1] + 94), radius=10, fill=_with_alpha(world["emerald"], g0))

        y_top = hdr_b[3] + 22
        row_h = min(182, (STAGE_Y1 - 240 - y_top) // max(1, n))
        for i, ent in enumerate(entries):
            if isinstance(ent, str):
                ent = {"address": f"0x{160+i*16:04X}", "op": ent, "table": "wal_stream", "status": "SYNCED"}
            g = _spring_gate(progress, i, n, 0.22)
            a_mul = _ease_out_cubic(g)
            if a_mul <= 0.03:
                continue
            status = str(ent.get("status") or "SYNCED").upper()
            is_act = (i == active_idx)
            col = world["emerald"] if ("REP" in status or "SYNC" in status or "COM" in status) else (world["amber"] if "TRANS" in status else world["cyan"])
            ry = y_top + i * row_h
            cb = (74, ry, 1006, ry + row_h - 18)
            stage.draw_glass_card(cb, radius=20, accent_col=col, alpha_mul=a_mul, active=is_act, layered=is_act)
            stage.draw_pill(168, ry + (row_h - 18) // 2, str(ent.get("address") or f"0x0{i}"), (*col[:3], 44), col, border_col=col, font=_get_font(21, bold=True, mono=True), alpha_mul=a_mul, pad_x=16, pad_y=10)
            _draw_wrapped_text(stage.draw, (268, ry + 22), str(ent.get("op") or ""), _get_font(27, bold=True), _with_alpha(world["text"], a_mul), 490, max_lines=1)
            tbl_txt = str(ent.get("table") or "stream").strip()
            _draw_wrapped_text(stage.draw, (268, ry + 66), f"TABLE: {tbl_txt}", _get_font(20, mono=True), _with_alpha(world["muted"], a_mul), 460, max_lines=1)
            stage.draw_pill(880, ry + (row_h - 18) // 2, status[:13], (*col[:3], 42), col, border_col=col, font=_get_font(18, bold=True), alpha_mul=a_mul, pad_x=16, pad_y=8)

        bot_y0 = max(y_top + n * row_h + 12, STAGE_Y1 - 210)
        cb_bot = (74, bot_y0, 1006, STAGE_Y1 - 20)
        stage.draw_glass_card(cb_bot, radius=24, accent_col=world["emerald"], alpha_mul=g0, active=True)
        _draw_node_visual(stage, 182, (bot_y0 + cb_bot[3]) // 2 - 14, 48, 22, 34, world["emerald"], g0, shape="database_cluster", icon="postgres", active=True, progress=progress)
        _draw_wrapped_text(stage.draw, (268, bot_y0 + 30), "Zero-Lock Append Stream -> Continuous Sync", _get_font(27, bold=True), _with_alpha(world["text"], g0), 705, max_lines=2)
        _draw_wrapped_text(stage.draw, (268, bot_y0 + 102), "Zero Production Locks • Ordered LSN Commit Pipeline", _get_font(21), _with_alpha(world["muted"], g0), 705, max_lines=1)
        return

    lanes = list(data.get("lanes") or data.get("blocks") or data.get("items") or _harvest_generic_items(data))[:5]
    if not lanes:
        return
    n = len(lanes)
    lh = min(195, (STAGE_H - 60) // max(1, n))
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
        segs = list(ln.get("segments") or [{"label": ln.get("sub") or "Used", "pct": 0.72}])[:4]
        sx = 104
        avail = 870
        for j, sg in enumerate(segs):
            if isinstance(sg, str):
                sg = {"label": sg, "pct": 1.0 / len(segs)}
            pw = max(80, int(avail * min(1.0, float(sg.get("pct", 0.35))) * _ease_out_cubic(g))) - 8
            sc = resolve_world_color(world, sg.get("color"), _ACCENT_CYCLE[(i + j) % len(_ACCENT_CYCLE)])
            stage.draw.rounded_rectangle((sx, y + 66, sx + pw, y + lh - 38), radius=12, fill=_with_alpha((*sc[:3], 185), a_mul), outline=_with_alpha(world["glass_rim"], a_mul), width=2)
            stage.draw.text((sx + 14, y + 78), str(sg.get("label") or "")[:24], font=_get_font(20, bold=True), fill=_with_alpha(world["text"], a_mul))
            sx += pw + 8


def _render_roadmap_wave(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    milestones = list(data.get("milestones") or data.get("steps") or data.get("items") or _harvest_generic_items(data))[:5]
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
        _draw_node_visual(stage, ax, ay - 16, 40, 18, 28, col, a_mul, shape=ms.get("shape", "hexagon"), icon=ms.get("icon", ""), label=str(ms.get("title") or ms.get("name") or ""), active=(int(progress * n) == i), progress=progress)
        stage.draw_pill(ax, ay + 40, str(ms.get("phase") or ms.get("num") or f"P{i+1}")[:10], world["card_alt"], col, border_col=col, font=_get_font(19, bold=True), alpha_mul=a_mul)
        _draw_wrapped_text(stage.draw, (cb_x0 + 20, ay - 36), str(ms.get("title") or ms.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], a_mul), cb_x1 - cb_x0 - 40, max_lines=1)
        desc_s = str(ms.get("sub") or ms.get("desc") or "").strip()
        if desc_s:
            _draw_wrapped_text(stage.draw, (cb_x0 + 20, ay + 8), desc_s, _get_font(20), _with_alpha(world["muted"], a_mul), cb_x1 - cb_x0 - 40, max_lines=2)


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
    prob_title = str(data.get("problem_title") or data.get("title") or "Production System Risk").strip()
    prob_desc = str(data.get("problem_desc") or "").strip()
    challenge = str(data.get("challenge") or data.get("warning_box") or "").strip()
    if not alerts:
        alerts = [
            {"title": prob_title[:22], "severity": "critical", "sub": prob_desc},
            {"title": "Table / Lock Stall", "severity": "high"},
            {"title": "Traffic Drops", "severity": "warn"},
            {"title": (challenge[:20] if challenge else "Zero-Lock Target"), "severity": "warn"},
        ]

    cx, cy, rad = 540, 675, 295
    g0 = _ease_out_cubic(_clamp01(progress / 0.18))
    stage.draw_glass_card((96, STAGE_Y0 + 12, 984, 1020), radius=30, accent_col=world["rose"], alpha_mul=g0, active=True)
    for r_i, rr in enumerate((100, 198, 295)):
        stage.draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=_with_alpha((*world["rose"][:3], 155 - r_i * 30), g0), width=3)
    # Crosshair axis ticks
    stage.draw.line((cx - rad - 16, cy, cx + rad + 16, cy), fill=_with_alpha((*world["rose"][:3], 75), g0), width=2)
    stage.draw.line((cx, cy - rad - 16, cx, cy + rad + 16), fill=_with_alpha((*world["rose"][:3], 75), g0), width=2)

    # Rotating Glowing Sweep Wedge + Beam
    ang = progress * math.pi * 3.0
    ang0 = ang - 0.52
    wedge_pts = [(cx, cy)] + [
        (cx + rad * math.cos(ang0 + (ang - ang0) * k / 10.0), cy + rad * math.sin(ang0 + (ang - ang0) * k / 10.0))
        for k in range(11)
    ]
    stage.draw.polygon(wedge_pts, fill=_with_alpha((*world["cyan"][:3], 52), g0))
    stage.add_glow_line([(cx, cy), (cx + rad * math.cos(ang), cy + rad * math.sin(ang))], world["cyan"], width=14, alpha=170)
    stage.draw.line((cx, cy, int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))), fill=_with_alpha(world["cyan"], g0), width=5)

    for i, al in enumerate(alerts):
        if isinstance(al, str):
            al = {"title": al, "severity": "high"}
        g = _spring_gate(progress, i + 1, len(alerts) + 1, 0.22)
        a_mul = _ease_out_cubic(g)
        if a_mul <= 0.03:
            continue
        ba = -math.pi * 0.78 + i * 1.45
        br = 135 + (i % 2) * 105
        bx, by = int(cx + br * math.cos(ba)), int(cy + br * math.sin(ba))
        sev = str(al.get("severity") or "warn").lower()
        col = world["rose"] if sev in ("high", "critical", "p0") else (world["amber"] if sev == "warn" else world["emerald"])
        stage.add_glow_orb(bx, by, 34, col, alpha=int(165 * a_mul))
        stage.draw.ellipse((bx - 22, by - 22, bx + 22, by + 22), outline=_with_alpha(col, a_mul * 0.65), width=2)
        stage.draw.ellipse((bx - 12, by - 12, bx + 12, by + 12), fill=_with_alpha(col, a_mul))
        raw_blip = str(al.get("title") or "").strip()
        if len(raw_blip) > 22 and " " in raw_blip[:23]:
            raw_blip = raw_blip[:22].rsplit(" ", 1)[0]
        else:
            raw_blip = raw_blip[:22]
        stage.draw_pill(max(210, min(870, bx)), by + 36, raw_blip, world["card_alt"], world["text"], border_col=col, font=_get_font(19, bold=True), alpha_mul=a_mul, pad_x=14, pad_y=6)

    # Bold Bottom Bottleneck + Challenge Card (ALWAYS rendered, fills lower screen cleanly!)
    card_b = (74, 1046, 1006, STAGE_Y1 - 22)
    stage.draw_glass_card(card_b, radius=24, accent_col=world["rose"], alpha_mul=g0, active=True, layered=True)
    draw_vector_glyph(stage, 134, 1106, "warn", 26, world["rose"], g0, with_badge=True)
    _draw_wrapped_text(stage.draw, (176, 1084), prob_title, _get_font(30, bold=True), _with_alpha(world["rose"], g0), 800, max_lines=1)
    if prob_desc:
        _draw_wrapped_text(stage.draw, (112, 1142), prob_desc, _get_font(22), _with_alpha(world["text"], g0), 860, line_gap=4, max_lines=3)
    if challenge:
        stage.draw_pill(540, STAGE_Y1 - 68, f"-> {challenge[:48]}", (*world["cyan"][:3], 42), world["cyan"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g0, pad_x=22, pad_y=10)


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
    root_lbl = str(data.get("root") or data.get("title") or "Root").strip()
    children = list(data.get("children") or data.get("branches") or _harvest_generic_items(data))[:4]
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


def _render_concept_cards(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    bullets = list(data.get("bullets") or data.get("items") or _harvest_generic_items(data))[:4]
    warn_box = str(data.get("warning_box") or "").strip()
    footer = str(data.get("footer_cta") or "").strip()
    y = STAGE_Y0 + 18
    n = max(1, len(bullets))
    rh = min(205, (STAGE_Y1 - y - (245 if warn_box else 96)) // n)
    active_idx = min(n - 1, int(max(0.0, min(0.999, progress)) * n))
    prev_cx = None
    for i, b in enumerate(bullets):
        g_raw = _spring_gate(progress, i, n, 0.22)
        if g_raw <= 0.02:
            continue
        g_box = _sub_gate(g_raw, "box")
        g_ico = _sub_gate(g_raw, "badge")
        g_tit = _sub_gate(g_raw, "title")
        g_sub = _sub_gate(g_raw, "sub")
        g_lnk = _sub_gate(g_raw, "link")
        col = resolve_world_color(world, None, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        txt = str(b.get("name") or b.get("title") or "") if isinstance(b, dict) else str(b)
        sub = str(b.get("sub") or b.get("desc") or "") if isinstance(b, dict) else ""
        if ":" in txt and not sub and len(txt.split(":", 1)[0]) < 30:
            txt, sub = txt.split(":", 1)[0].strip(), txt.split(":", 1)[1].strip()
        cb = (76, y, 1004, y + rh - 18)
        is_act = (active_idx == i and progress > 0.03)
        if prev_cx is not None:
            _draw_bezier_comet(stage, prev_cx, (146, y + 4), col, reveal=g_box, progress=progress, phase=i * 0.2, world=world)
        stage.draw_glass_card(cb, radius=22, accent_col=col, alpha_mul=g_box, active=is_act)
        if g_ico > 0.02:
            _draw_node_visual(stage, 146, y + (rh - 18) // 2 - 12, 34, 15, 22, col, g_ico, shape="hexagon", label=txt, active=is_act, progress=progress)
        if g_tit > 0.02:
            _draw_wrapped_text(stage.draw, (212, y + 22), txt, _get_font(28, bold=True), _with_alpha(world["text"], g_tit), 760, max_lines=2)
        if sub and g_sub > 0.02:
            _draw_wrapped_text(stage.draw, (212, y + 72), sub, _get_font(21), _with_alpha(world["muted"], g_sub), 760, max_lines=2)
        prev_cx = (146, y + rh - 18) if g_lnk > 0.02 or i + 1 < n else None
        y += rh
    gf = _footer_gate(progress)
    if warn_box and gf > 0.03:
        wb = (76, max(y + 8, STAGE_Y1 - 215), 1004, STAGE_Y1 - 68)
        stage.draw_glass_card(wb, radius=20, accent_col=world["amber"], alpha_mul=gf, active=True)
        draw_vector_glyph(stage, 130, (wb[1] + wb[3]) // 2, "warn", 24, world["amber"], gf, with_badge=True)
        _draw_wrapped_text(stage.draw, (176, wb[1] + 24), warn_box, _get_font(24, bold=True), _with_alpha(world["amber"], gf), 800, max_lines=3)
    if footer and gf > 0.03:
        stage.draw_pill(540, STAGE_Y1 - 30, footer[:48], world["card_alt"], world["cyan"], border_col=world["cyan"], font=_get_font(20, bold=True), alpha_mul=gf)


def _render_hero_hook(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    g0 = _ease_out_cubic(_clamp01(progress / 0.16))
    stat_b = str(data.get("stat_badge") or "").strip()
    q_txt = str(data.get("question") or data.get("title") or "").strip()
    pills = [str(p).strip() for p in (data.get("pills") or [data.get("left_pill"), data.get("right_pill")]) if p and str(p).strip()][:3]
    subs = [str(s).strip() for s in (data.get("sub_callouts") or []) if str(s).strip()][:4]

    y = STAGE_Y0 + 24
    if stat_b:
        stage.draw_pill(540, y + 22, stat_b[:34], (*world["amber"][:3], 44), world["amber"], border_col=world["amber"], font=_get_font(23, bold=True), alpha_mul=g0, pad_x=24, pad_y=10)
        y += 68
    q_b = (78, y, 1002, y + 300)
    stage.draw_glass_card(q_b, radius=28, accent_col=world["cyan"], alpha_mul=g0, active=True, layered=True)
    _draw_wrapped_text(stage.draw, (120, y + 50), q_txt, _get_font(42, bold=True), _with_alpha(world["text"], g0), 840, line_gap=10, align="center", max_lines=4)
    y = q_b[3] + 28
    tot_beats = max(1, len(pills) + len(subs))
    beat_idx = 0
    if pills:
        pw = (920 - max(0, len(pills) - 1) * 20) // len(pills)
        for i, pl in enumerate(pills):
            g_raw = _spring_gate(progress, beat_idx, tot_beats, 0.22)
            beat_idx += 1
            if g_raw <= 0.02:
                continue
            g_b, g_t = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "title")
            pc = resolve_world_color(world, None, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            x0 = 80 + i * (pw + 20)
            stage.draw_glass_card((x0, y, x0 + pw, y + 106), radius=20, accent_col=pc, alpha_mul=g_b, active=(int(progress * tot_beats) == i))
            if g_t > 0.02:
                _draw_wrapped_text(stage.draw, (x0 + 16, y + 30), pl, _get_font(26, bold=True), _with_alpha(pc, g_t), pw - 32, align="center", max_lines=2)
        y += 132
    for i, sc in enumerate(subs):
        if y > STAGE_Y1 - 95:
            break
        g_raw = _spring_gate(progress, beat_idx, tot_beats, 0.22)
        beat_idx += 1
        if g_raw <= 0.02:
            continue
        g_b, g_ico, g_t = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "badge"), _sub_gate(g_raw, "title")
        col = world["rose"] if "trap" in sc.lower() or "avoid" in sc.lower() else world["emerald"]
        stage.draw_glass_card((80, y, 1000, y + 98), radius=18, accent_col=col, alpha_mul=g_b, active=(int(progress * tot_beats) == (beat_idx - 1)))
        if g_ico > 0.02:
            draw_vector_glyph(stage, 128, y + 49, "warn" if col == world["rose"] else "bolt", 20, col, g_ico)
        if g_t > 0.02:
            _draw_wrapped_text(stage.draw, (172, y + 26), sc, _get_font(24, bold=True), _with_alpha(world["text"], g_t), 800, max_lines=2)
        y += 114


def _render_hybrid_merge(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    lp = data.get("left_pillar") if isinstance(data.get("left_pillar"), dict) else {"label": str(data.get("left_pillar") or "Engine A"), "sub": ""}
    rp = data.get("right_pillar") if isinstance(data.get("right_pillar"), dict) else {"label": str(data.get("right_pillar") or "Engine B"), "sub": ""}
    merged = str(data.get("merged_label") or data.get("title") or "Hybrid Core").strip()
    outcomes = [str(o).strip() for o in (data.get("outcomes") or ["Accuracy", "Consistency", "Zero Downtime"]) if str(o).strip()][:3]

    g_left = _spring_gate(progress, 0, 5, 0.24)
    g_right = _spring_gate(progress, 1, 5, 0.24)
    g_merge = _spring_gate(progress, 2, 5, 0.24)
    # Sequential Left Pillar -> Right Pillar -> Merge Comets & Core
    for g_pil, (x0, x1, pl, col, shp) in ((g_left, (76, 514, lp, world["cyan"], "chip")), (g_right, (566, 1004, rp, world["purple"], "cloud"))):
        if g_pil <= 0.02:
            continue
        g_b, g_ico, g_t, g_s = _sub_gate(g_pil, "box"), _sub_gate(g_pil, "badge"), _sub_gate(g_pil, "title"), _sub_gate(g_pil, "sub")
        stage.draw_glass_card((x0, STAGE_Y0 + 18, x1, STAGE_Y0 + 305), radius=24, accent_col=col, alpha_mul=g_b, active=True)
        if g_ico > 0.02:
            _draw_node_visual(stage, (x0 + x1) // 2, STAGE_Y0 + 96, 46, 20, 32, col, g_ico, shape=shp, active=True, progress=progress)
        if g_t > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 20, STAGE_Y0 + 168), str(pl.get("label") or ""), _get_font(28, bold=True), _with_alpha(world["text"], g_t), (x1 - x0) - 40, align="center", max_lines=2)
        if pl.get("sub") and g_s > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 20, STAGE_Y0 + 232), str(pl.get("sub")), _get_font(20), _with_alpha(world["muted"], g_s), (x1 - x0) - 40, align="center", max_lines=2)

    g_c1 = _sub_gate(g_left, "link")
    g_c2 = _sub_gate(g_right, "link")
    if g_c1 > 0.02:
        _draw_bezier_comet(stage, (295, STAGE_Y0 + 308), (485, STAGE_Y0 + 472), world["cyan"], reveal=g_c1, progress=progress, label="Merge", world=world)
    if g_c2 > 0.02:
        _draw_bezier_comet(stage, (785, STAGE_Y0 + 308), (595, STAGE_Y0 + 472), world["purple"], reveal=g_c2, progress=progress, label="Combine", world=world)

    if g_merge > 0.02:
        g_mb, g_mi, g_mt = _sub_gate(g_merge, "box"), _sub_gate(g_merge, "badge"), _sub_gate(g_merge, "title")
        cb = (130, STAGE_Y0 + 474, 950, STAGE_Y0 + 710)
        stage.draw_glass_card(cb, radius=28, accent_col=world["emerald"], alpha_mul=g_mb, active=True, layered=True)
        if g_mi > 0.02:
            _draw_node_visual(stage, 240, STAGE_Y0 + 575, 52, 24, 38, world["emerald"], g_mi, shape="geodesic_sphere", active=True, progress=progress)
        if g_mt > 0.02:
            _draw_wrapped_text(stage.draw, (320, STAGE_Y0 + 545), merged, _get_font(34, bold=True), _with_alpha(world["emerald"], g_mt), 590, align="center", max_lines=2)

    if outcomes:
        cw = (920 - (len(outcomes) - 1) * 20) // len(outcomes)
        oy = STAGE_Y0 + 765
        for i, oc in enumerate(outcomes):
            go = _spring_gate(progress, 3 + i, 3 + len(outcomes), 0.22)
            if go <= 0.02:
                continue
            gb, gi, gt_o = _sub_gate(go, "box"), _sub_gate(go, "badge"), _sub_gate(go, "title")
            cc = resolve_world_color(world, None, _ACCENT_CYCLE[(i + 2) % len(_ACCENT_CYCLE)])
            x0 = 80 + i * (cw + 20)
            stage.draw_glass_card((x0, oy, x0 + cw, min(STAGE_Y1 - 24, oy + 210)), radius=20, accent_col=cc, alpha_mul=gb)
            if gi > 0.02:
                draw_vector_glyph(stage, x0 + cw // 2, oy + 58, "check", 24, cc, gi, with_badge=True)
            if gt_o > 0.02:
                _draw_wrapped_text(stage.draw, (x0 + 14, oy + 106), oc, _get_font(23, bold=True), _with_alpha(world["text"], gt_o), cw - 28, align="center", max_lines=2)


def _render_all_in_one_tech(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    g0 = _ease_out_cubic(_clamp01(progress / 0.16))
    vpc = str(data.get("vpc_label") or "CLOUD VPC TOPOLOGY").strip()
    stage.draw.rounded_rectangle((68, STAGE_Y0 + 14, 1012, STAGE_Y1 - 92), radius=28, outline=_with_alpha((*world["cyan"][:3], 145), g0), width=3)
    stage.draw_pill(540, STAGE_Y0 + 50, vpc[:38], (*world["cyan"][:3], 40), world["cyan"], border_col=world["cyan"], font=_get_font(20, bold=True), alpha_mul=g0, pad_x=22, pad_y=8)

    comps = [
        (295, STAGE_Y0 + 200, str(data.get("comp1_label") or "Client Ingestion"), str(data.get("comp1_sub") or "API / Ingress"), "monitor", world["cyan"]),
        (785, STAGE_Y0 + 200, str(data.get("comp2_label") or "AI / Compute"), str(data.get("comp2_sub") or "Processing"), "bot", world["purple"]),
        (540, STAGE_Y0 + 495, str(data.get("comp3_label") or "Core Broker"), str(data.get("comp3_sub") or "Orchestrator"), "server_rack", world["amber"]),
        (295, STAGE_Y0 + 790, str(data.get("comp4_label") or "Primary DB"), str(data.get("comp4_sub") or "WAL Storage"), "database_cluster", world["emerald"]),
        (785, STAGE_Y0 + 790, str(data.get("comp5_label") or "Target Sink"), str(data.get("comp5_sub") or "Cloud Lake"), "warehouse_3d", world["cyan"]),
    ]
    arrows = [
        ((295, STAGE_Y0 + 265), (500, STAGE_Y0 + 425), str(data.get("arrow1_label") or "Stream"), world["cyan"], 0),
        ((785, STAGE_Y0 + 265), (580, STAGE_Y0 + 425), str(data.get("arrow2_label") or "Compute"), world["purple"], 1),
        ((500, STAGE_Y0 + 565), (295, STAGE_Y0 + 725), str(data.get("arrow3_label") or "Write"), world["amber"], 2),
        ((580, STAGE_Y0 + 565), (785, STAGE_Y0 + 725), str(data.get("arrow4_label") or "Sync"), world["emerald"], 3),
    ]
    active_idx = min(4, int(max(0.0, min(0.999, progress)) * 5))
    for i, (cx, cy, nm, sb, shp, col) in enumerate(comps):
        gc = _spring_gate(progress, i, 5, 0.22)
        if gc <= 0.02:
            continue
        g_box = _sub_gate(gc, "box")
        g_ico = _sub_gate(gc, "badge")
        g_tit = _sub_gate(gc, "title")
        g_sub = _sub_gate(gc, "sub")
        is_act = (active_idx == i and progress > 0.04)
        stage.draw_glass_card((cx - 195, cy - 64, cx + 195, cy + 70), radius=20, accent_col=col, alpha_mul=g_box, active=is_act)
        if g_ico > 0.02:
            _draw_node_visual(stage, cx - 125, cy - 10, 38, 17, 26, col, g_ico, shape=shp, label=nm, active=is_act, progress=progress)
        if g_tit > 0.02:
            _draw_wrapped_text(stage.draw, (cx - 72, cy - 38), nm, _get_font(23, bold=True), _with_alpha(world["text"], g_tit), 255, max_lines=2)
        if sb and g_sub > 0.02:
            _draw_wrapped_text(stage.draw, (cx - 72, cy + 16), sb, _get_font(18), _with_alpha(world["muted"], g_sub), 255, max_lines=1)
        if i < len(arrows):
            p0, p1, lbl, acol, a_phase = arrows[i]
            g_link = _sub_gate(gc, "link")
            if g_link > 0.02:
                _draw_bezier_comet(stage, p0, p1, acol, reveal=g_link, progress=progress, phase=a_phase * 0.22, label=lbl, world=world)
    gf = _footer_gate(progress)
    ft_txt = str(data.get("footer") or data.get("summary") or f"{comps[0][2]} -> {comps[2][2]} -> {comps[4][2]}")
    if gf > 0.03 and ft_txt:
        stage.draw_glass_card((80, STAGE_Y1 - 76, 1000, STAGE_Y1 - 14), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
        _draw_wrapped_text(stage.draw, (110, STAGE_Y1 - 58), ft_txt[:62], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 860, align="center", max_lines=1)


from core.layouts_domain_220 import GRAMMAR_50_PRESETS


# =========================================================================
# +70 CORE STUDIO ARCHITECTURAL PRESETS (Core 33 + 70 = 103 Core Studio!)
# =========================================================================
CORE_STUDIO_EXTRA_70: Dict[str, Tuple[str, Dict[str, Any]]] = {
    # Isometric & System Topologies (12)
    "iso_microservice_Mesh": ("iso_architecture", {"badge": "MICROSERVICES", "nodes": [{"name": "API Gateway", "sub": "Auth + Rate Limit", "shape": "router"}, {"name": "Orders Service", "sub": "Async gRPC", "shape": "k8s_pod_mesh"}, {"name": "Ledger Vault", "sub": "Serializable DB", "shape": "database_cluster"}]}),
    "iso_event_backbone": ("iso_architecture", {"badge": "EVENT BACKBONE", "nodes": [{"name": "Domain Producer", "sub": "CloudEvents v1", "shape": "api_plug_3d"}, {"name": "Partitioned Log", "sub": "Durable Replay", "shape": "kafka_broker"}, {"name": "CQRS Materializer", "sub": "Read Projections", "shape": "warehouse_3d"}]}),
    "iso_edge_compute": ("iso_architecture", {"badge": "EDGE RUNTIME", "nodes": [{"name": "Global Anycast POP", "sub": "<15ms RTT", "shape": "cdn_edge"}, {"name": "WASM V8 Isolate", "sub": "0ms Cold Start", "shape": "chip"}, {"name": "Distributed KV", "sub": "Read-Heavy Edge", "shape": "ssd_nvme"}]}),
    "iso_zero_trust_proxy": ("iso_architecture", {"badge": "ZERO TRUST", "nodes": [{"name": "Device Posture Check", "sub": "SPIFFE Workload ID", "shape": "laptop"}, {"name": "Identity Aware Proxy", "sub": "mTLS + JWT Policy", "shape": "firewall_wall"}, {"name": "Private Workload", "sub": "Zero Public IP", "shape": "server_rack"}]}),
    "iso_read_replica_topology": ("iso_architecture", {"badge": "READ SCALING", "nodes": [{"name": "Primary Writer DB", "sub": "Strict ACID Writes", "shape": "database_cluster"}, {"name": "WAL Async Stream", "sub": "Sub-10ms LSN Lag", "shape": "data_pipe"}, {"name": "3x Read Replicas", "sub": "RO Analytics Pool", "shape": "server_rack"}]}),
    "iso_cqrs_segregation": ("iso_architecture", {"badge": "CQRS PATTERN", "nodes": [{"name": "Command Write Model", "sub": "Normalized Constraints", "shape": "schema_table"}, {"name": "Projector Worker", "sub": "Async Denormalizer", "shape": "gear"}, {"name": "Read View Elastic", "sub": "<5ms Search Query", "shape": "warehouse_3d"}]}),
    "iso_sharded_cluster": ("iso_architecture", {"badge": "SHARDING", "nodes": [{"name": "Scatter-Gather Router", "sub": "Consistent Hash Key", "shape": "load_balancer"}, {"name": "Shard 01 (A-M)", "sub": "Isolated IOPS Pool", "shape": "database_cluster"}, {"name": "Shard 02 (N-Z)", "sub": "Linear Write Scale", "shape": "database_cluster"}]}),
    "iso_worker_autoscaler": ("iso_architecture", {"badge": "KEDA AUTOSCALE", "nodes": [{"name": "Queue Lag Monitor", "sub": "Depth > 500 msgs", "shape": "gauge_dial"}, {"name": "Ephemeral Worker Pool", "sub": "Scale 2 -> 64 Pods", "shape": "k8s_pod_mesh"}, {"name": "Graceful Drain Sig", "sub": "Zero Job Loss", "shape": "shield"}]}),
    "iso_graphql_federation": ("iso_architecture", {"badge": "FEDERATION", "nodes": [{"name": "Apollo Supergraph", "sub": "Unified Schema Plan", "shape": "hub"}, {"name": "Users Subgraph", "sub": "Identity Entities", "shape": "server_rack"}, {"name": "Catalog Subgraph", "sub": "Inventory Pricing", "shape": "database_cluster"}]}),
    "iso_search_indexing": ("iso_architecture", {"badge": "HYBRID SEARCH", "nodes": [{"name": "Ingestion Tokenizer", "sub": "BM25 + 1536d Embed", "shape": "code_cube"}, {"name": "Inverted + HNSW Index", "sub": "Milliseond Recall", "shape": "dag_pipeline"}, {"name": "RRF Score Fusion", "sub": "Top-K Ranked Hits", "shape": "radar_dish"}]}),
    "iso_observability_mesh": ("node_graph", {"badge": "OTEL MESH", "hub_name": "OTel Collector", "satellites": [{"name": "Metrics PromQL"}, {"name": "Trace Spans"}, {"name": "Structured Logs"}, {"name": "eBPF Profiler"}]}),
    "iso_consensus_quorum": ("node_graph", {"badge": "QUORUM 3/5", "hub_name": "Raft Leader", "satellites": [{"name": "Follower N1"}, {"name": "Follower N2"}, {"name": "Follower N3"}, {"name": "Witness"}]}),
    # Memory, Storage & Queues (12)
    "memory_ring_buffer": ("memory_lanes", {"badge": "LMAX DISRUPTOR", "entries": [{"address": "0x00", "op": "HEAD_CURSOR", "table": "producer_seq", "status": "LOCK-FREE"}, {"address": "0x40", "op": "CACHE_LINE_PAD", "table": "zero_false_share", "status": "ALIGNED"}, {"address": "0x80", "op": "TAIL_CONSUMER", "table": "batch_commit", "status": "10M_OPS/S"}]}),
    "memory_slab_allocator": ("memory_lanes", {"badge": "SLAB CACHE", "entries": [{"address": "64B", "op": "SMALL_POOL", "table": "zero_frag", "status": "O(1) FREE"}, {"address": "256B", "op": "STRUCT_SLAB", "table": "hot_reuse", "status": "LOCKLESS"}, {"address": "4KB", "op": "PAGE_SLAB", "table": "mmap_backed", "status": "READY"}]}),
    "memory_lsm_memtable": ("memory_lanes", {"badge": "LSM ENGINE", "entries": [{"address": "WAL", "op": "APPEND_DISK", "table": "durable_log", "status": "SYNCED"}, {"address": "MEM", "op": "SKIPLIST_RAM", "table": "write_fast", "status": "HOT"}, {"address": "SST", "op": "LEVEL0_FLUSH", "table": "compacted", "status": "IMMUTABLE"}]}),
    "memory_btree_slotted": ("memory_lanes", {"badge": "8KB SLOTTED PAGE", "entries": [{"address": "HDR", "op": "PAGE_LSN_FREE", "table": "b_plus_root", "status": "PINNED"}, {"address": "PTR", "op": "OFFSET_ARRAY", "table": "binary_search", "status": "SORTED"}, {"address": "TUP", "op": "ROW_PAYLOADS", "table": "mvcc_xmin", "status": "ACTIVE"}]}),
    "memory_stack_heap_split": ("memory_lanes", {"badge": "STACK VS HEAP", "entries": [{"address": "RSP", "op": "STACK_FRAME", "table": "pop_1_cycle", "status": "THREAD_LOCAL"}, {"address": "PTR", "op": "GC_HEAP_ALLOC", "table": "escape_analysis", "status": "TRACKED"}, {"address": "ESC", "op": "ZERO_ALLOC_FAST", "table": "inlined_val", "status": "OPTIMIZED"}]}),
    "memory_arena_bump": ("memory_lanes", {"badge": "ARENA ALLOCATOR", "entries": [{"address": "0x10", "op": "BUMP_PTR++", "table": "request_ctx", "status": "2_CYCLES"}, {"address": "0x90", "op": "ZERO_INDIV_FREE", "table": "bulk_objects", "status": "CONTIGUOUS"}, {"address": "RST", "op": "RESET_ALL_AT_END", "table": "zero_leak", "status": "CLEARED"}]}),
    "queue_dlq_backoff": ("queue_workers", {"badge": "RETRY + DLQ", "items": [{"name": "Primary Queue", "sub": "Fast First Attempt"}, {"name": "Exp Backoff + Jitter", "sub": "Prevents Retry Storm"}, {"name": "Dead-Letter Vault", "sub": "Replay & Inspect Later"}]}),
    "queue_priority_lanes": ("queue_workers", {"badge": "PRIORITY QOS", "items": [{"name": "P0 Checkout / Auth", "sub": "Dedicated Workers"}, {"name": "P1 Webhook Notify", "sub": "Bounded Concurrency"}, {"name": "P2 Bulk Email Export", "sub": "Spot Idle Drain"}]}),
    "lb_consistent_hash_mesh": ("load_balancer_fanout", {"badge": "HASH RING LB", "items": [{"name": "Envoy Edge Router", "sub": "xxHash Session Sticky"}, {"name": "Pod A (Hot Cache)", "sub": "94% Local Hit Rate"}, {"name": "Pod B & C Failover", "sub": "Bounded Load Shed"}]}),
    "lb_least_connections": ("load_balancer_fanout", {"badge": "SMART ROUTING", "items": [{"name": "Peak-EWMA Scorer", "sub": "Tracks Live RTT"}, {"name": "Skip Slow Degraded Node", "sub": "Sub-5ms Route Pick"}, {"name": "Zero Queue Head Stall", "sub": "Balanced Tail P99"}]}),
    "cache_write_through": ("cache_hit_miss", {"badge": "WRITE-THROUGH", "items": [{"name": "App Write Request", "sub": "Update Cache + DB Sync"}, {"name": "Zero Stale Reads", "sub": "Consistent Always"}, {"name": "L1 Cache Hit (0.3ms)", "sub": "Next Reads Instant"}]}),
    "cache_stampede_singleflight": ("cache_hit_miss", {"badge": "SINGLEFLIGHT", "items": [{"name": "1000 Concurrent Misses", "sub": "Coalesced Into 1 Leader"}, {"name": "999 Wait Shared Future", "sub": "Zero DB Stampede"}, {"name": "Cache Repopulated Once", "sub": "DB CPU Drops 95%"}]}),
    # Compare, Tradeoff, Code, SQL & API (14)
    "compare_sync_vs_async": ("iso_comparison", {"left_label": "BLOCKING SYNC", "right_label": "NON-BLOCKING ASYNC", "left_points": ["Thread blocks on DB I/O", "10K threads = 10GB RAM", "Context switch thrash"], "right_points": ["Epoll / kqueue event loop", "Tiny 4KB coroutine tasks", "100K+ sockets/core"]}),
    "compare_sql_vs_nosql": ("iso_comparison", {"left_label": "RELATIONAL ACID", "right_label": "WIDE-COL / DOC", "left_points": ["Strict foreign key joins", "Strong transactional locks", "Vertical + Read Replicas"], "right_points": ["Schema-free partition keys", "Horizontal shard auto-split", "Tunable quorum consistency"]}),
    "compare_rest_vs_grpc": ("iso_comparison", {"left_label": "JSON OVER HTTP/1.1", "right_label": "GRPC + PROTOBUF", "left_points": ["Human-readable text JSON", "Head-of-line connection stall", "~400B payload tax"], "right_points": ["Compact binary fields", "HTTP/2 multiplexed streams", "5x lower wire latency"]}),
    "compare_polling_vs_sse": ("iso_comparison", {"left_label": "SHORT POLLING", "right_label": "SSE / WEBSOCKET", "left_points": ["95% empty 304 responses", "Wastes mobile radio", "Stale up to poll interval"], "right_points": ["Instant zero-delay push", "Single persistent TCP stream", "Sub-50ms live updates"]}),
    "compare_offset_vs_keyset": ("iso_comparison", {"left_label": "OFFSET 50000", "right_label": "SEEK id > last", "left_points": ["Scans & discards 50K rows", "Duplicates on concurrent insert", "Degrades linearly O(N)"], "right_points": ["Direct B-Tree index seek", "O(log N) constant 0.4ms", "Stable cursor pagination"]}),
    "compare_locks_vs_lockfree": ("iso_comparison", {"left_label": "MUTEX CONTENTION", "right_label": "ATOMIC CAS / RCU", "left_points": ["OS sleeps & wakes threads", "Convoy deadlock hazard", "Tail latency spikes 40x"], "right_points": ["Hardware CMPXCHG instruction", "Zero kernel wait queue", "Predictable nanoseconds"]}),
    "sql_window_partition": ("sql_studio", {"badge": "POSTGRES WINDOW", "query": "SELECT user_id, amt, DENSE_RANK() OVER (PARTITION BY dept ORDER BY amt DESC) FROM sales;", "columns": ["user", "dept", "amt", "rk"], "rows": [["Asha", "Eng", "$92k", "1"], ["Vikram", "Eng", "$84k", "2"]]}),
    "sql_cte_recursive": ("sql_studio", {"badge": "RECURSIVE CTE", "query": "WITH RECURSIVE tree AS (SELECT id, parent FROM org UNION ALL SELECT c.id, c.parent FROM org c JOIN tree t ON c.parent=t.id) SELECT * FROM tree;", "columns": ["lvl", "node", "parent"], "rows": [["0", "VP", "NULL"], ["1", "Staff", "VP"]]}),
    "sql_covering_index": ("sql_studio", {"badge": "INDEX ONLY SCAN", "query": "CREATE INDEX CONCURRENTLY idx_orders_cov ON orders(tenant_id, created_at) INCLUDE (total, status);", "columns": ["step", "io_cost", "latency"], "rows": [["Seq Scan", "48,000", "910ms"], ["Covering", "4 pages", "0.6ms"]]}),
    "sql_upsert_conflict": ("sql_studio", {"badge": "ATOMIC UPSERT", "query": "INSERT INTO quotas(uid, hits) VALUES ($1, 1) ON CONFLICT (uid) DO UPDATE SET hits = quotas.hits + 1;", "columns": ["op", "lock_mode", "safe"], "rows": [["Race Check", "Lost Update", "NO"], ["ON CONFLICT", "Atomic Row", "YES"]]}),
    "diff_n_plus_one_fix": ("code_diff_split", {"badge": "FIX N+1 QUERY", "left_label": "N+1 (101 QUERIES)", "right_label": "BATCH JOIN (1 QUERY)", "before": "for u in users:\n  orders = db.get(u.id)", "after": "SELECT * FROM orders\nWHERE user_id = ANY($1)"}),
    "diff_async_gather": ("code_diff_split", {"badge": "PARALLEL AWAIT", "left_label": "SEQUENTIAL 600ms", "right_label": "GATHER 210ms", "before": "a = await fetch_a()\nb = await fetch_b()", "after": "a, b = await asyncio.gather(\n  fetch_a(), fetch_b()\n)"}),
    "api_idempotent_post": ("api_request_response", {"badge": "IDEMPOTENT API", "method": "POST", "endpoint": "/v1/charges", "request_headers": "Idempotency-Key: 9f2c-41a0", "status": "201 Created (Replay Safe)", "response_body": "{\"charge_id\": \"ch_881\", \"deduped\": true}"}),
    "api_rate_limit_429": ("api_request_response", {"badge": "RATE LIMIT RFC", "method": "GET", "endpoint": "/v2/search?q=logs", "status": "429 Too Many Requests", "response_body": "{\"retry_after_sec\": 12, \"limit\": \"100/min\"}"}),
    # Performance, Gauges, Telemetry & Incidents (12)
    "perf_flamegraph_cpu": ("flamegraph_perf", {"badge": "CPU FLAMEGRAPH", "frames": [{"name": "http_handler (100%)", "pct": 1.0}, {"name": "json.loads_hot_path (72%)", "pct": 0.72}, {"name": "orjson_simd (6%)", "pct": 0.14}]}),
    "perf_flamegraph_alloc": ("flamegraph_perf", {"badge": "HEAP ALLOC PROFILER", "frames": [{"name": "worker_loop (100%)", "pct": 1.0}, {"name": "bytes_copy_slice (68%)", "pct": 0.68}, {"name": "zero_copy_memview (4%)", "pct": 0.12}]}),
    "perf_waterfall_ssr": ("latency_waterfall", {"badge": "WATERFALL TRACE", "spans": [{"label": "Edge TLS + DNS", "start": 0.0, "end": 0.18}, {"label": "DB Pool Wait (Alert)", "start": 0.18, "end": 0.78}, {"label": "Render & Flush", "start": 0.78, "end": 1.0}]}),
    "perf_waterfall_grpc": ("latency_waterfall", {"badge": "DISTRIBUTED TRACE", "spans": [{"label": "API Gateway Parse", "start": 0.0, "end": 0.15}, {"label": "Parallel Auth + Fraud", "start": 0.15, "end": 0.55}, {"label": "Ledger Commit + Ack", "start": 0.55, "end": 1.0}]}),
    "benchmark_throughput_ops": ("benchmark_3d", {"badge": "OPS / SECOND", "bars": [{"label": "Unindexed Full Scan", "value": 420, "display": "420/s"}, {"label": "Redis + Read Replica", "value": 18500, "display": "18.5K/s"}, {"label": "Local L1 + Shard", "value": 94000, "display": "94K/s", "is_winner": True}]}),
    "benchmark_memory_footprint": ("benchmark_3d", {"badge": "RAM FOOTPRINT", "bars": [{"label": "Raw Python Dicts", "value": 920, "display": "920 MB"}, {"label": "__slots__ Class", "value": 310, "display": "310 MB"}, {"name": "NumPy Compact Struct", "value": 64, "display": "64 MB", "is_winner": True}]}),
    "gauge_slo_availability": ("radial_gauge", {"badge": "99.99% SLO BUDGET", "main_value": "99.99%", "main_unit": "FOUR NINES UPTIME", "gauge_percent": 99, "telemetry": [{"label": "Monthly Budget", "val": "4.3 min"}, {"label": "Current Burn", "val": "0.4 min"}]}),
    "gauge_cache_efficiency": ("radial_gauge", {"badge": "L1/L2 HIT RATIO", "main_value": "96.4%", "main_unit": "CACHE HIT RATIO", "gauge_percent": 96, "telemetry": [{"label": "Origin DB Load", "val": "-91%"}, {"label": "P99 Saved", "val": "44ms"}]}),
    "incident_thundering_herd": ("incident_radar", {"badge": "THUNDERING HERD", "problem_title": "Midnight Cache Expiry Storm", "problem_desc": "12,000 clients miss TTL at 00:00 simultaneously", "alerts": ["DB CPU 100%", "Pool Exhausted", "Add Jitter + Lock"]}),
    "incident_split_brain": ("incident_radar", {"badge": "SPLIT BRAIN", "problem_title": "Two Primary Leaders Accept Writes", "problem_desc": "Network partition without fencing tokens corrupts state", "alerts": ["Dual Writers", "Diverged LSN", "Fencing Epoch Fix"]}),
    "checklist_prod_readiness": ("checklist_scorecard", {"badge": "PROD CHECKLIST", "items": [{"name": "Structured Timeouts + Retries", "sub": "Jittered Backoff + Budget"}, {"name": "Graceful SIGTERM Drain", "sub": "In-Flight Requests Safe"}, {"name": "Circuit Breaker + Alerts", "sub": "Actionable SLO Runbook"}]}),
    "checklist_sql_tuning": ("checklist_scorecard", {"badge": "SQL TUNING CHECK", "items": [{"name": "Inspect EXPLAIN ANALYZE", "sub": "Verify Buffers & Seq Scans"}, {"name": "Composite Equality-Range Order", "sub": "Match Index Sort Order"}, {"name": "PgBouncer Transaction Pool", "sub": "Cap Idle Backend Connections"}]}),
    # Hierarchy, Sequence, FSM, Timeline & Venn (12)
    "seq_oauth_authorization": ("sequence_diagram", {"badge": "OAUTH 2.1 FLOW", "steps": [{"name": "Auth Code + PKCE"}, {"name": "User Login Consent"}, {"name": "Code + Verifier Exchange"}, {"name": "Signed JWT + Refresh"}]}),
    "seq_two_phase_commit": ("sequence_diagram", {"badge": "2PC PROTOCOL", "steps": [{"name": "Coordinator: PREPARE"}, {"name": "Shards Lock & ACK"}, {"name": "Coordinator: COMMIT"}, {"name": "All Release & Persist"}]}),
    "erd_multi_tenant_saas": ("er_schema", {"badge": "SAAS ERD SCHEMA", "tables": [{"name": "organizations", "cols": ["id PK", "plan_tier", "slug UK"]}, {"name": "users", "cols": ["id PK", "org_id FK", "role"]}, {"name": "api_keys", "cols": ["id PK", "org_id FK", "hash"]}]}),
    "erd_ecommerce_orders": ("er_schema", {"badge": "ORDERS SCHEMA", "tables": [{"name": "orders", "cols": ["id PK", "user_fk", "status"]}, {"name": "order_items", "cols": ["id PK", "order_fk", "sku_fk"]}, {"name": "payments", "cols": ["id PK", "order_fk", "idem_key"]}]}),
    "fsm_order_fulfillment": ("state_machine", {"badge": "ORDER FSM", "states": ["CREATED", "AUTHORIZED", "PACKED", "SHIPPED", "SETTLED"]}),
    "fsm_connection_lifecycle": ("state_machine", {"badge": "SOCKET FSM", "states": ["CLOSED", "SYN_SENT", "ESTABLISHED", "FIN_WAIT", "TIME_WAIT"]}),
    "git_trunk_cherrypick": ("git_branch_tree", {"badge": "GIT TRUNK FLOW", "commits": [{"name": "main: feat flag off", "sub": "C104 Safe Merge"}, {"name": "fix/hotpatch -> cherry-pick", "sub": "Zero Rebase Conflict"}, {"name": "tag v2.14.1 Prod", "sub": "Verified Artifact"}]}),
    "roadmap_scale_milestones": ("roadmap_wave", {"badge": "0 TO 10M USERS", "milestones": [{"name": "10K: Single Postgres + Redis", "sub": "Simple Vertical Scale"}, {"name": "1M: Replicas + CDN + Async", "sub": "Offload Heavy Reads"}, {"name": "10M: Partition + Geo-Edge", "sub": "Isolated Blast Radius"}]}),
    "venn_cap_tradeoff": ("venn_overlap", {"badge": "SYSTEM TRADE-OFFS", "sets": ["Consistency", "Availability", "Partition Tolerant"]}),
    "venn_sec_usability": ("venn_overlap", {"badge": "AUTH BALANCE", "sets": ["Zero Trust Crypto", "1-Tap Passkey UX", "Enterprise Compliance"]}),
    "tree_ast_compiler": ("tree_hierarchy", {"badge": "COMPILER AST", "items": [{"name": "Program Root"}, {"name": "Lexical Tokens"}, {"name": "Typed IR Graph"}, {"name": "LLVM Machine Code"}]}),
    "pyramid_testing_roi": ("pyramid_hierarchy", {"badge": "TEST PYRAMID", "items": [{"name": "10% E2E Playwright Flows"}, {"name": "25% API Integration Contracts"}, {"name": "65% Fast Deterministic Unit"}]}),
    # Generative Spatial & SVG Core Presets (8)
    "matrix_effort_impact": ("matrix_2x2", {"badge": "ENGINEERING ROI", "items": [{"name": "Quick Wins (High/Low)", "sub": "Index + Cache Fix Now"}, {"name": "Strategic Bets (High/High)", "sub": "Sharding Architecture"}, {"name": "Fill-Ins (Low/Low)", "sub": "Minor Refactor"}, {"name": "Avoid (Low/High)", "sub": "Over-Engineered Mesh"}]}),
    "stat_bento_slo": ("stat_grid_2x2", {"badge": "LIVE BENCHMARK", "items": [{"name": "0.8 ms P50", "sub": "In-Memory Hit"}, {"name": "14 ms P99", "sub": "With Backpressure"}, {"name": "99.99% SLA", "sub": "Multi-AZ Failover"}, {"name": "62% Lower Bill", "sub": "Right-Sized Pool"}]}),
    "funnel_latency_drop": ("funnel_metrics", {"badge": "BOTTLENECK FUNNEL", "items": [{"name": "920ms Cold Uncached"}, {"name": "240ms Query Indexed"}, {"name": "42ms Pooled + Prepared"}, {"name": "2ms Edge Redis Cache"}]}),
    "stack_osi_transport": ("layer_stack_3d", {"badge": "NETWORK STACK", "layers": [{"name": "L7 App (HTTP/3 gRPC)"}, {"name": "L4 Transport (QUIC / TCP)"}, {"name": "L3 Network (IPv6 / BGP)"}, {"name": "L2 Fiber / NIC Ring"}]}),
    "kinetic_interview_rule": ("kinetic_statement", {"badge": "GOLDEN RULE", "statement": "Measure First. Never Optimize Without Tracing P99!", "sub": "Staff Engineering Heuristic"}),
    "terminal_explain_analyze": ("terminal_studio", {"badge": "EXPLAIN ANALYZE", "command": "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM logs WHERE org=42;", "output": "Index Scan using idx_logs_org (cost=0.43..8.45)\nBuffers: shared hit=4 | Execution Time: 0.312 ms"}),
    "spatial_blueprint_core": ("spatial_canvas", {"badge": "SPATIAL SYSTEM", "elements": [{"title": "Edge Gateway", "sub": "TLS + Rate Limit", "x": 220, "y": 460}, {"title": "Async Queue", "sub": "Kafka Partition", "x": 540, "y": 780}, {"title": "Worker Cluster", "sub": "Auto-Scaled Pods", "x": 840, "y": 1090}]}),
    "svg_architecture_core": ("svg_scene", {"badge": "VECTOR SCHEMATIC", "nodes": [{"name": "Client SDK", "sub": "Optimistic Mutation"}, {"name": "Sync Engine", "sub": "CRDT Conflict-Free"}, {"name": "Durable Vault", "sub": "Replicated Storage"}]}),
    # +50 Extended Core Studio Layouts (Core 33 + 120 = 153 Core Studio!)
    "iso_saga_compensator": ("iso_architecture", {"badge": "SAGA PATTERN", "nodes": [{"name": "Order Debit", "sub": "Local Tx 1", "shape": "server_rack"}, {"name": "Inventory Lock", "sub": "Local Tx 2", "shape": "database_cluster"}, {"name": "Compensate Refund", "sub": "Rollback On Fail", "shape": "shield"}]}),
    "iso_outbox_relay": ("iso_architecture", {"badge": "OUTBOX CDC", "nodes": [{"name": "App Write + Outbox", "sub": "Single ACID Commit", "shape": "database_cluster"}, {"name": "Debezium Relay", "sub": "Tail WAL Changes", "shape": "kafka_broker"}, {"name": "Kafka Topic Publish", "sub": "Zero Dual-Write Loss", "shape": "hub"}]}),
    "iso_geo_sharded_db": ("iso_architecture", {"badge": "GEO SHARDS", "nodes": [{"name": "Region Router", "sub": "Read tenant_region", "shape": "router"}, {"name": "EU Vault Shard", "sub": "GDPR Local Disk", "shape": "database_cluster"}, {"name": "US Vault Shard", "sub": "Low Latency East", "shape": "database_cluster"}]}),
    "iso_cdc_stream_mesh": ("iso_architecture", {"badge": "CDC MESH", "nodes": [{"name": "Primary Postgres", "sub": "Logical Replication", "shape": "database_cluster"}, {"name": "Kafka Transform", "sub": "PII Redact + Enrich", "shape": "kafka_broker"}, {"name": "ClickHouse Sink", "sub": "Real-Time OLAP", "shape": "warehouse_3d"}]}),
    "iso_api_bff_gateway": ("iso_architecture", {"badge": "BFF GATEWAY", "nodes": [{"name": "Mobile/Web Clients", "sub": "Lean Tailored Graph", "shape": "mobile"}, {"name": "BFF Aggregator", "sub": "Parallel Fanout Merge", "shape": "router"}, {"name": "Microservices Pool", "sub": "Auth • Cart • Stock", "shape": "k8s_pod_mesh"}]}),
    "iso_rate_limit_cluster": ("iso_architecture", {"badge": "RATE LIMIT", "nodes": [{"name": "Edge Envoy Proxy", "sub": "Inspect API Key", "shape": "firewall_wall"}, {"name": "Redis Lua Atomic", "sub": "Sliding Window <1ms", "shape": "chip"}, {"name": "Upstream API Pods", "sub": "Protected From Flood", "shape": "server_rack"}]}),
    "iso_vector_hybrid_rag": ("iso_architecture", {"badge": "HYBRID RAG", "nodes": [{"name": "Query + Sparse BM25", "sub": "Exact Keyword Signal", "shape": "terminal_box"}, {"name": "Dense HNSW Index", "sub": "Semantic Embedding", "shape": "dag_pipeline"}, {"name": "RRF + Reranker", "sub": "Grounded Top-5 Hits", "shape": "server_rack"}]}),
    "iso_zero_downtime_mig": ("iso_architecture", {"badge": "LIVE MIGRATION", "nodes": [{"name": "Dual-Write Proxy", "sub": "Sync Legacy -> New", "shape": "load_balancer"}, {"name": "Shadow Diff Check", "sub": "Verify 100% Parity", "shape": "radar_dish"}, {"name": "Atomic DNS Cutover", "sub": "Zero Lock Drop", "shape": "database_cluster"}]}),
    "iso_multi_cloud_dr": ("iso_architecture", {"badge": "MULTI-CLOUD DR", "nodes": [{"name": "Primary Cloud EKS", "sub": "99% Steady Traffic", "shape": "cloud"}, {"name": "Async Bucket Sync", "sub": "Cross-Provider Snap", "shape": "data_lake"}, {"name": "Warm DR Failover", "sub": "Auto-Promote <3m", "shape": "server_rack"}]}),
    "iso_canary_rollout_tree": ("node_graph", {"badge": "CANARY GATES", "hub_name": "Argo Rollouts", "satellites": [{"name": "1% Smoke Test"}, {"name": "10% Metrics Check"}, {"name": "50% Bake Window"}, {"name": "100% Promote"}]}),
    "memory_wal_checkpoint": ("memory_lanes", {"badge": "WAL CHECKPOINT", "entries": [{"address": "0x100", "op": "DIRTY_PAGES_RAM", "table": "buffer_pool", "status": "MODIFIED"}, {"address": "0x200", "op": "FSYNC_BATCH_FLUSH", "table": "data_files", "status": "DURABLE"}, {"address": "0x300", "op": "REDO_PTR_ADVANCE", "table": "wal_truncate", "status": "CLEAN"}]}),
    "memory_mvcc_tuple_hdr": ("memory_lanes", {"badge": "MVCC TUPLE HDR", "entries": [{"address": "xmin", "op": "TX_INSERT_1042", "table": "visible_new", "status": "COMMITTED"}, {"address": "xmax", "op": "TX_DELETE_1089", "table": "old_snapshot", "status": "CONCURRENT"}, {"address": "ctid", "op": "HOT_CHAIN_PTR", "table": "page_42_off_3", "status": "LINKED"}]}),
    "memory_buffer_pool_clock": ("memory_lanes", {"badge": "CLOCK SWEEP", "entries": [{"address": "P01", "op": "PIN_COUNT=2", "table": "ref_bit=1", "status": "KEEP_HOT"}, {"address": "P02", "op": "PIN_COUNT=0", "table": "ref_bit=1->0", "status": "SECOND_CHANCE"}, {"address": "P03", "op": "PIN_COUNT=0", "table": "ref_bit=0", "status": "EVICT_PAGE"}]}),
    "memory_trie_radix_node": ("memory_lanes", {"badge": "ADAPTIVE RADIX", "entries": [{"address": "N4", "op": "NODE4_INLINE", "table": "4_child_ptrs", "status": "L1_FIT"}, {"address": "N16", "op": "SIMD_CMP_KEY", "table": "16_sorted_keys", "status": "2_CYCLES"}, {"address": "N256", "op": "DIRECT_BYTE_IDX", "table": "o1_lookup", "status": "DENSE"}]}),
    "queue_competing_consumers": ("queue_workers", {"badge": "COMPETING WORKERS", "items": [{"name": "Shared Work Queue", "sub": "FIFO Partition Stream"}, {"name": "Stateless Consumer N", "sub": "Scale Out On Queue Lag"}, {"name": "Visibility Timeout Lease", "sub": "Auto-Requeue Crashed Jobs"}]}),
    "queue_partition_ordering": ("queue_workers", {"badge": "ORDERED KEY", "items": [{"name": "Hash(user_id) % P", "sub": "Same Key -> Same Partition"}, {"name": "Strictly Serial Offsets", "sub": "Zero Out-of-Order Events"}, {"name": "Parallel Across Keys", "sub": "Scales With Partitions"}]}),
    "cache_write_behind_async": ("cache_hit_miss", {"badge": "WRITE-BEHIND", "items": [{"name": "Instant Cache Write", "sub": "Return 200 OK In 0.4ms"}, {"name": "Coalesce Hot Key Edits", "sub": "Merge 100 Writes -> 1"}, {"name": "Async Batch DB Flush", "sub": "Protect Disk IOPS Peak"}]}),
    "cache_negative_bloom": ("cache_hit_miss", {"badge": "NEGATIVE CACHE", "items": [{"name": "Probe Missing User ID", "sub": "Bypass Flood Attack"}, {"name": "Bloom Filter + Null TTL", "sub": "Rejects 99% Ghost Keys"}, {"name": "Origin DB Protected", "sub": "Zero Cold Penetration"}]}),
    "lb_maglev_consistent": ("load_balancer_fanout", {"badge": "MAGLEV HASH", "items": [{"name": "Lookup Permutation Table", "sub": "O(1) Minimal Disruption"}, {"name": "Backend Drops From Pool", "sub": "<2% Flows Remapped"}, {"name": "Even Connection Balance", "sub": "High-Throughput L4/L7"}]}),
    "lb_circuit_shedding": ("load_balancer_fanout", {"badge": "ADAPTIVE SHED", "items": [{"name": "In-Flight > Max Concurrency", "sub": "CoDel Queue Sojourn High"}, {"name": "Drop Low-Prio Load Early", "sub": "Save Critical Auth/Checkout"}, {"name": "Fast 503 Overload Signal", "sub": "Zero Cascade Collapse"}]}),
    "compare_pull_vs_push": ("iso_comparison", {"left_label": "FAN-OUT ON READ", "right_label": "FAN-OUT ON WRITE", "left_points": ["Fast write O(1) celebrity", "Heavy query merge on load", "Good for infrequent readers"], "right_points": ["Pre-materialized feeds RAM", "Instant <5ms home timeline", "Hybrid push + celeb pull"]}),
    "compare_b_tree_vs_lsm": ("iso_comparison", {"left_label": "B+ TREE (POSTGRES)", "right_label": "LSM TREE (ROCKSDB)", "left_points": ["Random 8KB page updates", "Sub-ms predictable point reads", "Write amplification on index"], "right_points": ["Sequential WAL + MemTable", "10x higher write throughput", "Background SST compaction"]}),
    "compare_threads_vs_async": ("iso_comparison", {"left_label": "OS PREEMPTIVE THREAD", "right_label": "COOPERATIVE ASYNC", "left_points": ["2MB stack per kernel thread", "Scheduler context switch cost", "Parallel CPU bound win"], "right_points": ["4KB green coroutine state", "Zero syscall park overhead", "100K+ idle I/O sockets"]}),
    "compare_monolith_vs_mesh": ("iso_comparison", {"left_label": "MODULAR MONOLITH", "right_label": "MICROSERVICE MESH", "left_points": ["In-process function calls (ns)", "Single atomic DB transaction", "Fast small-team iteration"], "right_points": ["Network hop + serialization", "Independent deploy & blast cap", "Needs OTel + retries + saga"]}),
    "sql_jsonb_gin_index": ("sql_studio", {"badge": "POSTGRES GIN", "query": "CREATE INDEX idx_meta_gin ON events USING GIN (payload jsonb_path_ops);", "columns": ["query_type", "pages", "time"], "rows": [["No GIN", "124,000", "1.4s"], ["GIN Path", "3 pages", "0.5ms"]]}),
    "sql_partition_pruning": ("sql_studio", {"badge": "RANGE PRUNE", "query": "SELECT COUNT(*) FROM logs WHERE created_at >= '2026-11-01' AND created_at < '2026-12-01';", "columns": ["partition", "scanned", "status"], "rows": [["2026_10", "SKIPPED", "PRUNED"], ["2026_11", "ACTIVE", "12ms"]]}),
    "diff_mutex_to_atomic": ("code_diff_split", {"badge": "LOCKFREE FIX", "left_label": "MUTEX LOCK CONTEND", "right_label": "ATOMIC FETCH_ADD", "before": "with lock:\n  counter += 1", "after": "counter.fetch_add(\n  1, Ordering::Relaxed\n)"}),
    "diff_sync_to_batch_bulk": ("code_diff_split", {"badge": "BULK BATCH", "left_label": "1000 ROUNDTRIPS", "right_label": "1 COPY STREAM", "before": "for r in rows:\n  cur.execute(ins, r)", "after": "await cur.executemany(\n  copy_stmt, rows\n)"}),
    "api_webhook_hmac_verify": ("api_request_response", {"badge": "HMAC WEBHOOK", "method": "POST", "endpoint": "/webhooks/payments", "request_headers": "X-Sig-256: t=1701,v1=9f4a", "status": "200 OK (Constant-Time Verify)", "response_body": "{\"verified\": true, \"enqueued\": \"evt_44\"}"}),
    "api_graphql_dataloader": ("api_request_response", {"badge": "DATALOADER", "method": "POST", "endpoint": "/graphql", "request_headers": "Batched 40 UserKeys -> 1 IN()", "status": "200 OK (Zero N+1)", "response_body": "{\"users_loaded\": 40, \"db_queries\": 1}"}),
    "perf_flamegraph_mutex": ("flamegraph_perf", {"badge": "LOCK FLAME", "frames": [{"name": "worker_serve (100%)", "pct": 1.0}, {"name": "pthread_mutex_lock_wait (78%)", "pct": 0.78}, {"name": "sharded_map_bucket (4%)", "pct": 0.14}]}),
    "perf_flamegraph_gc_pause": ("flamegraph_perf", {"badge": "GC PAUSE TRACE", "frames": [{"name": "event_loop (100%)", "pct": 1.0}, {"name": "stop_the_world_mark (64%)", "pct": 0.64}, {"name": "object_pool_reuse (5%)", "pct": 0.15}]}),
    "perf_waterfall_db_lock": ("latency_waterfall", {"badge": "LOCK TRACE", "spans": [{"label": "Acquire Auth JWT", "start": 0.0, "end": 0.12}, {"label": "Waiting RowExclusiveLock", "start": 0.12, "end": 0.84}, {"label": "Commit & Flush", "start": 0.84, "end": 1.0}]}),
    "benchmark_p99_tail_latency": ("benchmark_3d", {"badge": "TAIL LATENCY P99", "bars": [{"label": "No Timeout + Retry Storm", "value": 4200, "display": "4.2s P99"}, {"label": "Circuit Breaker Only", "value": 310, "display": "310ms P99"}, {"label": "Hedged Request + Pool", "value": 28, "display": "28ms P99", "is_winner": True}]}),
    "benchmark_serialization_fmt": ("benchmark_3d", {"badge": "WIRE FORMAT BENCH", "bars": [{"label": "Text JSON Parse", "value": 1850, "display": "18.5 ms"}, {"label": "MsgPack Compact", "value": 420, "display": "4.2 ms"}, {"label": "Protobuf Zero-Alloc", "value": 110, "display": "1.1 ms", "is_winner": True}]}),
    "gauge_cpu_saturation": ("radial_gauge", {"badge": "CPU HEADROOM", "main_value": "64.2%", "main_unit": "SAFE AUTO-SCALE ZONE", "gauge_percent": 64, "telemetry": [{"label": "Run Queue", "val": "1.2"}, {"label": "Steal Time", "val": "0.1%"}]}),
    "gauge_queue_headroom": ("radial_gauge", {"badge": "CONSUMER LAG", "main_value": "12 ms", "main_unit": "KAFKA END-TO-END LAG", "gauge_percent": 94, "telemetry": [{"label": "Drain Rate", "val": "48K/s"}, {"label": "DLQ Count", "val": "0"}]}),
    "incident_connection_exhaust": ("incident_radar", {"badge": "POOL STARVATION", "problem_title": "Postgres max_connections Exhausted", "problem_desc": "Slow external webhooks held DB transactions open 8s", "alerts": ["Idle-in-Tx Lock", "502 Gateway Burst", "Split Pool Fix"]}),
    "incident_oom_kill_loop": ("incident_radar", {"badge": "K8S OOMKILL 137", "problem_title": "CrashLoopBackOff Container Memory Limit", "problem_desc": "Unbounded result streaming loaded 4GB batch into pod", "alerts": ["Exit Code 137", "RSS Spike 2.4GB", "Stream Chunking"]}),
    "checklist_migration_safety": ("checklist_scorecard", {"badge": "ZERO-LOCK DDL", "items": [{"name": "Add Nullable Col Instant", "sub": "Metadata Only in PG 11+"}, {"name": "Create Index Concurrently", "sub": "Never Blocks Writes"}, {"name": "Backfill Small Batches", "sub": "Throttle 1000 Rows/50ms"}]}),
    "seq_saga_distributed": ("sequence_diagram", {"badge": "SAGA SEQUENCE", "steps": [{"name": "Reserve Balance"}, {"name": "Lock Seat Inventory"}, {"name": "Capture Carrier Label"}, {"name": "Compensate On Error"}]}),
    "seq_jwt_refresh_rotation": ("sequence_diagram", {"badge": "TOKEN ROTATION", "steps": [{"name": "Access Token Expires (15m)"}, {"name": "Send Single-Use Refresh"}, {"name": "Invalidate Old + Mint New"}, {"name": "Replay Triggers Revoke All"}]}),
    "erd_ledger_double_entry": ("er_schema", {"badge": "LEDGER ERD", "tables": [{"name": "accounts", "cols": ["id PK", "currency", "balance"]}, {"name": "journal_tx", "cols": ["id PK", "idem_key UK", "ts"]}, {"name": "postings", "cols": ["id PK", "acct_fk", "delta"]}]}),
    "erd_event_store_streams": ("er_schema", {"badge": "EVENT STORE", "tables": [{"name": "streams", "cols": ["stream_id PK", "version"]}, {"name": "events", "cols": ["global_seq PK", "stream_fk", "payload"]}, {"name": "snapshots", "cols": ["stream_fk", "state_json"]}]}),
    "fsm_payment_settlement": ("state_machine", {"badge": "PAYMENT FSM", "states": ["PENDING", "AUTHORIZED", "CAPTURED", "SETTLED", "RECONCILED"]}),
    "fsm_circuit_breaker_tri": ("state_machine", {"badge": "BREAKER FSM", "states": ["CLOSED", "OPEN_FAST_FAIL", "HALF_OPEN_PROBE", "RECOVERED"]}),
    "roadmap_zero_to_billion": ("roadmap_wave", {"badge": "HYPER-SCALE", "milestones": [{"name": "Phase 1: Indexed Single DB", "sub": "Simple Fast Correct"}, {"name": "Phase 2: Cache + Async Queue", "sub": "10x Read Throughput"}, {"name": "Phase 3: Multi-Region Shards", "sub": "Zero Single Point Fail"}]}),
    "venn_cap_availability": ("venn_overlap", {"badge": "SYSTEM BALANCE", "sets": ["Low Latency", "Strong Consistency", "Fault Tolerance"]}),
    "spatial_microservice_grid": ("spatial_canvas", {"badge": "SERVICE MESH", "elements": [{"title": "Ingress Proxy", "sub": "TLS 1.3 + JWT", "x": 200, "y": 460}, {"title": "Order Worker", "sub": "Idempotent Saga", "x": 540, "y": 780}, {"title": "Outbox Store", "sub": "Guaranteed Emit", "x": 850, "y": 1080}]}),
    "svg_pipeline_choreography": ("svg_scene", {"badge": "EVENT MESH SVG", "nodes": [{"name": "Event Emitter", "sub": "Publishes Fact"}, {"name": "Topic Router", "sub": "Filters Subscribers"}, {"name": "Independent Sinks", "sub": "Audit • Billing • Search"}]}),
}


def _render_multi_topology_dual(stage: StudioStage, data: Dict[str, Any], progress: float, world: Dict[str, Any]) -> None:
    """Renders TWO stacked interconnected System Topologies (Control/Ingress Plane -> Execution/Storage Plane) in one 9:16 frame."""
    plane_a_lbl = str(data.get("plane_a_label") or "INGRESS & CONTROL PLANE").strip().upper()
    plane_b_lbl = str(data.get("plane_b_label") or "EXECUTION & STORAGE CLUSTER").strip().upper()
    bridge_lbl = str(data.get("bridge_label") or "Async Mesh Bridge").strip()

    plane_a = list(data.get("plane_a") or [])[:3]
    plane_b = list(data.get("plane_b") or [])[:3]
    if not plane_a or not plane_b:
        raw_all = list(data.get("nodes") or data.get("items") or data.get("steps") or _harvest_generic_items(data))
        plane_a = plane_a or (raw_all[:3] if len(raw_all) >= 3 else [{"name": "Anycast Edge", "sub": "TLS + Auth", "shape": "cdn_edge"}, {"name": "API Gateway", "sub": "Rate Limit", "shape": "router"}, {"name": "Control Router", "sub": "Policy Mesh", "shape": "load_balancer"}])
        plane_b = plane_b or (raw_all[3:6] if len(raw_all) >= 6 else [{"name": "Stream Broker", "sub": "Partition Log", "shape": "kafka_broker"}, {"name": "Compute Pool", "sub": "Stateless Pods", "shape": "k8s_pod_mesh"}, {"name": "Replica Vault", "sub": "WAL Storage", "shape": "database_cluster"}])

    n_a, n_b = len(plane_a), len(plane_b)
    tot = max(2, n_a + n_b)
    g0 = _ease_out_cubic(_clamp01(progress / 0.16))

    # Plane A Upper Container Box
    stage.draw.rounded_rectangle((66, STAGE_Y0 + 10, 1014, STAGE_Y0 + 445), radius=24, outline=_with_alpha((*world["cyan"][:3], 130), g0), width=2)
    stage.draw_pill(250, STAGE_Y0 + 36, plane_a_lbl[:28], (*world["cyan"][:3], 36), world["cyan"], border_col=world["cyan"], font=_get_font(17, bold=True), alpha_mul=g0, pad_x=16, pad_y=6)

    cw_a = (STAGE_W - 36 - max(0, n_a - 1) * 18) // max(1, n_a)
    centers_a: List[Tuple[int, int]] = []
    for i, it in enumerate(plane_a):
        if isinstance(it, str):
            it = {"name": it}
        g_raw = _spring_gate(progress, i, tot, 0.22)
        if g_raw <= 0.02:
            centers_a.append((STAGE_X0 + 18 + i * (cw_a + 18) + cw_a // 2, STAGE_Y0 + 255))
            continue
        gb, gico, gtit, gsub, glnk = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "badge"), _sub_gate(g_raw, "title"), _sub_gate(g_raw, "sub"), _sub_gate(g_raw, "link")
        col = resolve_world_color(world, it.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        x0 = STAGE_X0 + 18 + i * (cw_a + 18)
        y0, y1 = STAGE_Y0 + 78, STAGE_Y0 + 418
        is_act = (int(max(0.0, min(0.999, progress)) * tot) == i and progress > 0.03)
        stage.draw_glass_card((x0, y0, x0 + cw_a, y1), radius=18, accent_col=col, alpha_mul=gb, active=is_act, layered=is_act)
        if gico > 0.02:
            _draw_node_visual(stage, x0 + cw_a // 2, y0 + 70, 38, 17, 26, col, gico, shape=it.get("shape", "router"), active=is_act, progress=progress)
        if gtit > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 14, y0 + 136), str(it.get("name") or it.get("title") or "")[:28], _get_font(22, bold=True), _with_alpha(world["text"], gtit), cw_a - 28, align="center", max_lines=2)
        if it.get("sub") and gsub > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 14, y0 + 216), str(it["sub"])[:44], _get_font(17), _with_alpha(world["muted"], gsub), cw_a - 28, align="center", max_lines=2)
        cx_i = x0 + cw_a // 2
        centers_a.append((cx_i, y1))
        if i + 1 < n_a and glnk > 0.02:
            nx0 = STAGE_X0 + 18 + (i + 1) * (cw_a + 18)
            _draw_bezier_comet(stage, (x0 + cw_a + 2, y0 + 150), (nx0 - 2, y0 + 150), col, reveal=glnk, progress=progress, phase=i * 0.25, label=str(it.get("edge") or ""), world=world)

    # Cross-Plane Bridge Arrow connecting Topology A -> Topology B
    g_br = _spring_gate(progress, max(1, n_a - 1), tot, 0.24)
    g_br_lnk = _sub_gate(g_br, "link")
    if g_br_lnk > 0.02:
        _draw_bezier_comet(stage, (540, STAGE_Y0 + 448), (540, STAGE_Y0 + 536), world["emerald"], reveal=g_br_lnk, progress=progress, label=bridge_lbl[:24], world=world)

    # Plane B Lower Container Box
    g_b0 = _ease_out_cubic(_clamp01((progress - 0.30) / 0.22))
    if g_b0 > 0.02:
        stage.draw.rounded_rectangle((66, STAGE_Y0 + 540, 1014, STAGE_Y1 - 90), radius=24, outline=_with_alpha((*world["purple"][:3], 130), g_b0), width=2)
        stage.draw_pill(275, STAGE_Y0 + 566, plane_b_lbl[:30], (*world["purple"][:3], 36), world["purple"], border_col=world["purple"], font=_get_font(17, bold=True), alpha_mul=g_b0, pad_x=16, pad_y=6)

    cw_b = (STAGE_W - 36 - max(0, n_b - 1) * 18) // max(1, n_b)
    for j, it in enumerate(plane_b):
        if isinstance(it, str):
            it = {"name": it}
        g_raw = _spring_gate(progress, n_a + j, tot, 0.22)
        if g_raw <= 0.02:
            continue
        gb, gico, gtit, gsub, glnk = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "badge"), _sub_gate(g_raw, "title"), _sub_gate(g_raw, "sub"), _sub_gate(g_raw, "link")
        col = resolve_world_color(world, it.get("color"), _ACCENT_CYCLE[(n_a + j) % len(_ACCENT_CYCLE)])
        x0 = STAGE_X0 + 18 + j * (cw_b + 18)
        y0, y1 = STAGE_Y0 + 606, STAGE_Y1 - 114
        is_act = (int(max(0.0, min(0.999, progress)) * tot) == (n_a + j) and progress > 0.03)
        stage.draw_glass_card((x0, y0, x0 + cw_b, y1), radius=18, accent_col=col, alpha_mul=gb, active=is_act, layered=is_act)
        if gico > 0.02:
            _draw_node_visual(stage, x0 + cw_b // 2, y0 + 78, 40, 18, 28, col, gico, shape=it.get("shape", "database_cluster"), active=is_act, progress=progress)
        if gtit > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 14, y0 + 148), str(it.get("name") or it.get("title") or "")[:28], _get_font(22, bold=True), _with_alpha(world["text"], gtit), cw_b - 28, align="center", max_lines=2)
        if it.get("sub") and gsub > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 14, y0 + 230), str(it["sub"])[:44], _get_font(17), _with_alpha(world["muted"], gsub), cw_b - 28, align="center", max_lines=2)
        if j + 1 < n_b and glnk > 0.02:
            nx0 = STAGE_X0 + 18 + (j + 1) * (cw_b + 18)
            _draw_bezier_comet(stage, (x0 + cw_b + 2, y0 + 165), (nx0 - 2, y0 + 165), col, reveal=glnk, progress=progress, phase=(n_a + j) * 0.25, label=str(it.get("edge") or ""), world=world)

    gf = _footer_gate(progress)
    ft_txt = str(data.get("footer") or data.get("summary") or f"{plane_a_lbl[:22]} -> {plane_b_lbl[:22]}").strip()
    if gf > 0.03 and ft_txt:
        stage.draw_glass_card((76, STAGE_Y1 - 76, 1004, STAGE_Y1 - 14), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
        _draw_wrapped_text(stage.draw, (108, STAGE_Y1 - 58), ft_txt[:62], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 864, align="center", max_lines=1)


MULTI_TOPOLOGY_30_PRESETS: Dict[str, Tuple[str, Dict[str, Any]]] = {
    "topo_ingress_mesh_wal": ("multi_topology_dual", {"badge": "DUAL PLANE", "plane_a_label": "INGRESS MESH", "plane_b_label": "DURABLE WAL STORE", "bridge_label": "Async Batch"}),
    "topo_dual_plane_control_data": ("multi_topology_dual", {"badge": "CONTROL + DATA", "plane_a_label": "CONTROL PLANE", "plane_b_label": "DATA PLANE", "bridge_label": "xDS Config Push"}),
    "topo_cdn_edge_origin_shield": ("multi_topology_dual", {"badge": "CDN SHIELD", "plane_a_label": "ANYCAST EDGE POP", "plane_b_label": "ORIGIN SHIELD POOL", "bridge_label": "Coalesced Fill"}),
    "topo_cqrs_read_write_split": ("multi_topology_dual", {"badge": "CQRS TOPOLOGY", "plane_a_label": "WRITE COMMANDS", "plane_b_label": "READ PROJECTIONS", "bridge_label": "CDC Event Bus"}),
    "topo_saga_choreo_compensate": ("multi_topology_dual", {"badge": "SAGA ENGINE", "plane_a_label": "FORWARD TX CHAIN", "plane_b_label": "COMPENSATE ROLLBACK", "bridge_label": "Failure Trigger"}),
    "topo_rag_hybrid_rerank": ("multi_topology_dual", {"badge": "HYBRID RAG", "plane_a_label": "BM25 + DENSE SEARCH", "plane_b_label": "RRF + LLM GROUND", "bridge_label": "Top-K Context"}),
    "topo_k8s_hpa_metrics_mesh": ("multi_topology_dual", {"badge": "K8S AUTOSCALE", "plane_a_label": "PROMETHEUS METRICS", "plane_b_label": "POD WORKER FLEET", "bridge_label": "HPA Scale Out"}),
    "topo_zero_trust_spiffe_mtls": ("multi_topology_dual", {"badge": "ZERO TRUST", "plane_a_label": "IDENTITY ATTEST", "plane_b_label": "MTLS ENVOY MESH", "bridge_label": "Short-Lived Cert"}),
    "topo_kafka_isr_quorum_dlq": ("multi_topology_dual", {"badge": "KAFKA QUORUM", "plane_a_label": "PARTITION PRODUCERS", "plane_b_label": "ISR REPLICAS + DLQ", "bridge_label": "Zero-Copy WAL"}),
    "topo_redis_cluster_sentinel": ("multi_topology_dual", {"badge": "REDIS CLUSTER", "plane_a_label": "HASH SLOT ROUTING", "plane_b_label": "SENTINEL FAILOVER", "bridge_label": "Sub-ms Replica"}),
    "topo_multi_region_active_active": ("multi_topology_dual", {"badge": "ACTIVE-ACTIVE", "plane_a_label": "GLOBAL DNS GEO", "plane_b_label": "CROSS-REGION CRDT", "bridge_label": "Conflict Merge"}),
    "topo_sharded_vitess_vtgate": ("multi_topology_dual", {"badge": "VTGATE SHARDS", "plane_a_label": "VTGATE SQL ROUTER", "plane_b_label": "KEYSPACE SHARDS", "bridge_label": "Parallel Plan"}),
    "topo_ebpf_xdp_kernel_bypass": ("multi_topology_dual", {"badge": "EBPF XDP", "plane_a_label": "NIC RING XDP HOOK", "plane_b_label": "USERSPACE WORKER", "bridge_label": "Zero-Copy AF_XDP"}),
    "topo_grpc_envoy_circuit_mesh": ("multi_topology_dual", {"badge": "ENVOY MESH", "plane_a_label": "GRPC HTTP/2 MUX", "plane_b_label": "BREAKER + HEDGING", "bridge_label": "EWMA Load Pick"}),
    "topo_flink_cep_iceberg_lake": ("multi_topology_dual", {"badge": "LAKEHOUSE", "plane_a_label": "FLINK WATERMARK", "plane_b_label": "ICEBERG SNAPSHOTS", "bridge_label": "ACID Commit"}),
    "topo_payment_idempotent_ledger": ("multi_topology_dual", {"badge": "LEDGER MESH", "plane_a_label": "IDEMPOTENCY GATE", "plane_b_label": "DOUBLE-ENTRY VAULT", "bridge_label": "Serializable Tx"}),
    "topo_agent_mcp_tool_sandbox": ("multi_topology_dual", {"badge": "MCP AGENTS", "plane_a_label": "PLANNER LLM HOST", "plane_b_label": "ISOLATED TOOL PODS", "bridge_label": "Typed JSON-RPC"}),
    "topo_gpu_tensor_pipeline_ring": ("multi_topology_dual", {"badge": "ALLREDUCE RING", "plane_a_label": "KV PREFILL CLUSTER", "plane_b_label": "DECODE NVLINK RING", "bridge_label": "Tensor AllReduce"}),
    "topo_webrtc_sfu_turn_relay": ("multi_topology_dual", {"badge": "REALTIME SFU", "plane_a_label": "SIGNALING + ICE", "plane_b_label": "MEDIA SFU ROUTERS", "bridge_label": "SRTP Simulcast"}),
    "topo_graphql_federation_subgraphs": ("multi_topology_dual", {"badge": "SUPERGRAPH", "plane_a_label": "FEDERATION ROUTER", "plane_b_label": "DOMAIN SUBGRAPHS", "bridge_label": "Query Plan DAG"}),
    "topo_oauth_pkce_jwks_rotator": ("multi_topology_dual", {"badge": "AUTH TOPOLOGY", "plane_a_label": "PKCE EDGE EXCHANGE", "plane_b_label": "JWKS KEY ROTATOR", "bridge_label": "RS256 Verify"}),
    "topo_vault_dynamic_creds_k8s": ("multi_topology_dual", {"badge": "SECRET LEASE", "plane_a_label": "K8S SERVICE AUTH", "plane_b_label": "DYNAMIC DB CREDS", "bridge_label": "15m Auto Revoke"}),
    "topo_otel_trace_span_collector": ("multi_topology_dual", {"badge": "OTEL PIPELINE", "plane_a_label": "SDK SPAN EMITTERS", "plane_b_label": "TAIL SAMPLER SINK", "bridge_label": "OTLP gRPC"}),
    "topo_chaos_mesh_blast_radius": ("multi_topology_dual", {"badge": "CHAOS GUARD", "plane_a_label": "FAULT INJECTOR", "plane_b_label": "BULKHEAD ISOLATION", "bridge_label": "SLO Guardrail"}),
    "topo_clickhouse_mergetree_s3": ("multi_topology_dual", {"badge": "OLAP ENGINE", "plane_a_label": "VECTOR PART WRITER", "plane_b_label": "S3 TIERED MERGE", "bridge_label": "Background Merge"}),
    "topo_wasm_isolate_edge_kv": ("multi_topology_dual", {"badge": "EDGE ISOLATES", "plane_a_label": "V8 WASM ISOLATE", "plane_b_label": "LOCAL EDGE KV", "bridge_label": "0ms Cold Start"}),
    "topo_blue_green_canary_alb": ("multi_topology_dual", {"badge": "CANARY SHIFT", "plane_a_label": "WEIGHTED ALB EDGE", "plane_b_label": "BLUE / GREEN POOLS", "bridge_label": "Zero-Drop Drain"}),
    "topo_outbox_debezium_snowflake": ("multi_topology_dual", {"badge": "OUTBOX CDC", "plane_a_label": "APP + OUTBOX TABLE", "plane_b_label": "DEBEZIUM -> WAREHOUSE", "bridge_label": "WAL Tail Stream"}),
    "topo_blockchain_l2_rollup_da": ("multi_topology_dual", {"badge": "ZK ROLLUP", "plane_a_label": "L2 SEQUENCER BATCH", "plane_b_label": "L1 VERIFIER + DA", "bridge_label": "Validity Proof"}),
    "topo_ros2_lidar_slam_planner": ("multi_topology_dual", {"badge": "ROBOTICS DDS", "plane_a_label": "SENSOR FUSION BUS", "plane_b_label": "MPC TRAJ PLANNER", "bridge_label": "100Hz Control"}),
}

CORE_STUDIO_100_LAYOUTS: Tuple[str, ...] = (
    "custom_scene", "iso_architecture", "node_graph", "iso_comparison", "terminal_studio", "kinetic_statement",
    "spatial_canvas", "svg_scene", "multi_topology_dual",
    "layer_stack_3d", "matrix_2x2", "pyramid_hierarchy", "sql_studio", "benchmark_3d",
    "radial_gauge", "memory_lanes", "roadmap_wave", "checklist_scorecard", "incident_radar",
    "sequence_diagram", "er_schema", "state_machine", "git_branch_tree", "flamegraph_perf",
    "queue_workers", "load_balancer_fanout", "cache_hit_miss", "code_diff_split", "api_request_response",
    "venn_overlap", "funnel_metrics", "stat_grid_2x2", "latency_waterfall", "tree_hierarchy",
) + tuple(k.lower() for k in CORE_STUDIO_EXTRA_70.keys()) + tuple(k.lower() for k in MULTI_TOPOLOGY_30_PRESETS.keys())

_CORE_STUDIO_PRESETS_LC: Dict[str, Tuple[str, Dict[str, Any]]] = {
    **{k.lower(): v for k, v in CORE_STUDIO_EXTRA_70.items()},
    **{k.lower(): v for k, v in MULTI_TOPOLOGY_30_PRESETS.items()},
}


# =========================================================================
# UNIFIED 1010+ STUDIO LAYOUT DISPATCHER (Core 184 + Pro 154 + IT 155 + Domain 360 + Grammar 158)
# =========================================================================
ALL_STUDIO_LAYOUTS: Tuple[str, ...] = (
    CORE_STUDIO_100_LAYOUTS + EXTRA_32_LAYOUTS + IT_SDLC_35_LAYOUTS + DOMAIN_220_LAYOUTS + GRAMMAR_50_PRESETS + DOMAIN_SPECIALIST_LAYOUTS
)

_PRO_HELPERS: Dict[str, Any] = {
    "_get_font": _get_font,
    "_draw_wrapped_text": _draw_wrapped_text,
    "_with_alpha": _with_alpha,
    "_spring_gate": _spring_gate,
    "_sub_gate": _sub_gate,
    "_footer_gate": _footer_gate,
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
    d = dict(data or {})
    if l in _CORE_STUDIO_PRESETS_LC:
        target_l, preset_d = _CORE_STUDIO_PRESETS_LC[l]
        merged = dict(preset_d)
        for pk, pv in d.items():
            if pv not in (None, "", [], {}):
                merged[pk] = pv
        # Never let static preset table/query placeholders override live topic-hydrated table_data / code_snippet
        if isinstance(d.get("table_data"), dict) and (d["table_data"].get("rows") or d["table_data"].get("headers")):
            merged["columns"] = list(d.get("columns") or d["table_data"].get("headers") or [])
            merged["rows"] = list(d.get("rows") or d["table_data"].get("rows") or [])
        if d.get("code_snippet") and not d.get("query"):
            merged["query"] = d["code_snippet"]
        l = target_l
        d = merged
    if render_domain_specialist_layout(stage, l, d, progress, world, _PRO_HELPERS):
        pass
    elif render_pro_layout(stage, l, d, progress, world, _PRO_HELPERS):
        pass
    elif render_it_sdlc_layout(stage, l, d, progress, world, _PRO_HELPERS):
        pass
    elif render_domain_220_or_grammar(stage, l, d, progress, world, _PRO_HELPERS):
        pass
    elif l in ("multi_topology_dual", "dual_topology", "topology_dual") or l.startswith("topo_"):
        _render_multi_topology_dual(stage, d, progress, world)
    elif l == "concept_cards" and (d.get("bullets") or not d.get("blocks")):
        _render_concept_cards(stage, d, progress, world)
    elif l in ("hero_hook", "question_hook", "hook_card", "interview_hook", "hero"):
        _render_hero_hook(stage, d, progress, world)
    elif l in ("hybrid_merge", "merge_diagram", "hybrid_architecture"):
        _render_hybrid_merge(stage, d, progress, world)
    elif l == "all_in_one_tech_canvas":
        _render_all_in_one_tech(stage, d, progress, world)
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
    elif l in ("kinetic_statement", "statement", "hook", "cta"):
        _render_kinetic_statement(stage, d, progress, world)
    elif l in ("spatial_canvas", "spatial", "freeform", "composer") or l.startswith("spatial_"):
        _render_spatial_canvas(stage, d, progress, world)
    elif l in ("svg_scene", "generative_svg", "svg", "web_scene", "webgl_scene", "html_scene") or l.startswith(("svg_", "web_")):
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
    if not d.get("_skip_companion"):
        _draw_voice_beats_companion(stage, d, l, progress, world, topic=topic)
    _draw_step_progress_bar(stage, d, progress, world)


_COMPANION_NEEDED_CACHE: Dict[str, bool] = {}


def _needs_companion_strip(
    stage: StudioStage,
    layout: str,
    data: Dict[str, Any],
    world: Dict[str, Any],
    topic: str = "",
) -> bool:
    """Probes at progress=0.85 (once per layout+content shape) so the companion grid never flickers mid-scene."""
    # Specialized diagrams, 3D meshes, charts, UI mockups, and geometric grammars keep pure silhouette without extra bottom 2x2 grid
    l_low = str(layout or "").lower()
    _PURE_GEOM = (
        "mesh_3d_stage", "atom_orbit_3d", "dna_helix_3d", "radar_spider", "donut_3d",
        "sankey_flow", "neural_net_layers", "attention_heatmap", "heatmap_matrix",
        "confusion_matrix", "candlestick_pro", "line_area_chart", "sequence_diagram",
        "er_schema", "sdlc_cycle_wheel", "circular_hub_mesh", "mobile_app_mockup",
        "browser_window", "chat_thread_ai", "kanban_board", "pricing_tiers",
        "code_diff_split", "diff_n_plus_one_fix", "diff_mutex_to_atomic",
        "p99_tail_cdf_curve", "box_whisker_latency", "pareto_frontier_plot",
        "all_in_one_tech_canvas", "benchmark_3d", "benchmark_chart", "radial_gauge",
    )
    if l_low in _PURE_GEOM or l_low in DOMAIN_SPECIALIST_LAYOUTS or any(l_low.startswith(p) for p in ("grammar:pyramid", "grammar:funnel", "grammar:ring", "grammar:quadrant", "grammar:chevron", "grammar:swimlane", "grammar:bento")):
        return False
    shape_sig = (
        f"{layout}|{len(data.get('nodes') or [])}|{len(data.get('steps') or [])}"
        f"|{len(data.get('items') or [])}|{len(data.get('bullets') or [])}"
        f"|{len(data.get('bars') or [])}|{len(data.get('blocks') or [])}"
        f"|{bool(data.get('output'))}|{bool(data.get('voice_beats'))}"
        f"|{len(str(data.get('code_snippet') or data.get('code') or '').splitlines())}"
    )
    if shape_sig in _COMPANION_NEEDED_CACHE:
        return _COMPANION_NEEDED_CACHE[shape_sig]
    needed = False
    try:
        import numpy as np
        probe_stage = StudioStage(stage.w, stage.h, world, transition_alpha=1.0)
        probe_data = dict(data)
        probe_data["_skip_companion"] = True
        dispatch_studio_layout(probe_stage, layout, probe_data, progress=0.85, world=world, topic=topic)
        bot_alpha = np.asarray(probe_stage.fg.crop((80, 1200, 1000, 1515)).getchannel("A"))
        needed = int((bot_alpha > 15).sum()) < 42000
    except Exception:
        needed = False
    if len(_COMPANION_NEEDED_CACHE) > 256:
        _COMPANION_NEEDED_CACHE.clear()
    _COMPANION_NEEDED_CACHE[shape_sig] = needed
    return needed


def _draw_voice_beats_companion(
    stage: StudioStage,
    data: Dict[str, Any],
    layout: str,
    progress: float,
    world: Dict[str, Any],
    topic: str = "",
) -> None:
    """
    Universal Anti-Sparse & Voice-Synced Highlight Strip:
    Whenever a scene layout leaves the lower canvas zone airy/empty at full reveal (< 52k fg pixels in y=1155..1515),
    renders a persistent 2x2 progressive multi-label highlight deck synced clause-by-clause with voice.
    """
    if not _needs_companion_strip(stage, layout, data, world, topic=topic):
        return

    beats: List[Dict[str, str]] = []
    for key in ("voice_beats", "sub_points", "items", "nodes", "steps", "stages", "bullets"):
        raw = data.get(key)
        if isinstance(raw, list) and raw:
            for idx, it in enumerate(raw[:4]):
                if isinstance(it, dict):
                    lbl = str(it.get("label") or it.get("name") or it.get("title") or "").strip()
                    sub = str(it.get("sub") or it.get("desc") or it.get("role") or "").strip()
                    if lbl or sub:
                        beats.append({"label": lbl or f"Step {idx+1}", "sub": sub})
                elif isinstance(it, str) and it.strip():
                    parts = it.split(":", 1)
                    beats.append({"label": parts[0].strip(), "sub": parts[1].strip() if len(parts) > 1 else ""})
            if len(beats) >= 2:
                break

    if len(beats) < 3:
        seed_t = str(data.get("title") or data.get("statement") or topic or "Architecture").strip()[:28]
        defaults = [
            {"label": f"01 • {seed_t[:18]}", "sub": "Core bottleneck & execution trigger"},
            {"label": "02 • Signal Flow", "sub": "Structured state & async routing"},
            {"label": "03 • Edge Guard", "sub": "Backpressure, limits & failover"},
            {"label": "04 • Verified Outcome", "sub": "Predictable sub-second production scale"},
        ]
        for df in defaults:
            if len(beats) >= 4:
                break
            beats.append(df)

    beats = beats[:4]
    nb = len(beats)
    cols = 2
    rows = 2 if nb > 2 else 1
    gw = (STAGE_W - 22) // 2
    gh = 166 if rows == 2 else 210
    y_start = 1158 if rows == 2 else 1245
    active_idx = min(nb - 1, int(max(0.0, min(0.999, progress)) * nb))

    # Small section eyebrow header
    gh0 = _ease_out_cubic(_clamp01(progress / 0.16))
    if gh0 > 0.03:
        stage.draw_pill(540, y_start - 20, "VOICE-SYNCED BREAKDOWN", (*world["cyan"][:3], 36), world["cyan"], border_col=world["border"], font=_get_font(17, bold=True), alpha_mul=gh0, pad_x=18, pad_y=6)

    for i, bt in enumerate(beats):
        g_raw = _spring_gate(progress, i, nb, 0.22)
        if g_raw <= 0.02:
            continue
        gb, gbdg, gtit, gsub, glnk = _sub_gate(g_raw, "box"), _sub_gate(g_raw, "badge"), _sub_gate(g_raw, "title"), _sub_gate(g_raw, "sub"), _sub_gate(g_raw, "link")
        r_i, c_i = divmod(i, cols)
        x0 = STAGE_X0 + c_i * (gw + 22)
        y0 = y_start + 8 + r_i * (gh + 16)
        col = resolve_world_color(world, None, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
        is_act = (active_idx == i and progress > 0.03)
        stage.draw_glass_card((x0, y0, x0 + gw, y0 + gh), radius=18, accent_col=col, alpha_mul=gb, active=is_act, layered=is_act)
        if gbdg > 0.02:
            stage.draw_pill(x0 + 46, y0 + 28, f"{i+1:02d}", (*col[:3], 44), col, border_col=col, font=_get_font(17, bold=True, mono=True), alpha_mul=gbdg)
        if gtit > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 82, y0 + 16), bt["label"][:32], _get_font(21, bold=True), _with_alpha(world["text"], gtit), gw - 98, max_lines=2)
        if bt.get("sub") and gsub > 0.02:
            _draw_wrapped_text(stage.draw, (x0 + 18, y0 + 78), bt["sub"][:58], _get_font(18), _with_alpha(world["muted"], gsub), gw - 36, max_lines=2)
        if i + 1 < nb and glnk > 0.02 and c_i == 0:
            _draw_bezier_comet(stage, (x0 + gw + 2, y0 + gh // 2), (x0 + gw + 20, y0 + gh // 2), col, reveal=glnk, progress=progress, phase=i * 0.25, world=world)
