import colorsys
import hashlib
from typing import Any, Dict, List, Tuple


def _hex_to_rgb(h: str, fallback: Tuple[int, int, int] = (56, 189, 248)) -> Tuple[int, int, int]:
    raw = str(h or "").strip().lstrip("#")
    if len(raw) == 6:
        try:
            return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
        except ValueError:
            pass
    return fallback


def _hsl_rgb(h_deg: float, s: float, l: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb((h_deg % 360.0) / 360.0, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def _make_dark_world(
    hue: float,
    sat: float = 0.86,
    sec_hue: float = None,
    bg_hue: float = None,
    bg_sat: float = 0.45,
    bg_lit: float = 0.055,
    third_hue: float = None,
) -> Dict[str, Any]:
    sh = (hue + 48.0) % 360.0 if sec_hue is None else sec_hue
    th = (hue + 145.0) % 360.0 if third_hue is None else third_hue
    bh = hue if bg_hue is None else bg_hue
    bg_top = _hsl_rgb(bh, bg_sat, bg_lit)
    bg_bot = _hsl_rgb((bh + 20.0) % 360.0, min(0.58, bg_sat + 0.06), min(0.13, bg_lit + 0.036))
    spot_a = _hsl_rgb(hue, sat, 0.58)
    spot_b = _hsl_rgb(sh, min(0.94, sat), 0.60)
    spot_c = _hsl_rgb(th, min(0.88, sat), 0.54)
    card_rgb = _hsl_rgb(bh, min(0.42, bg_sat), min(0.14, bg_lit + 0.055))
    layer_rgb = _hsl_rgb(bh, min(0.40, bg_sat), max(0.03, bg_lit + 0.02))
    alt_rgb = _hsl_rgb(bh, min(0.48, bg_sat + 0.05), min(0.20, bg_lit + 0.095))
    return {
        "is_light": False,
        "bg_top": bg_top,
        "bg_bot": bg_bot,
        "spot_a": spot_a,
        "spot_b": spot_b,
        "spot_c": spot_c,
        "grid_col": _hsl_rgb(hue, 0.45, 0.55),
        "card_bg": (*card_rgb, 226),
        "card_layer": (*layer_rgb, 212),
        "card_alt": (*alt_rgb, 234),
        "glass_rim": (255, 255, 255, 76),
        "border": (*spot_a, 132),
        "shadow_col": (2, 4, 10, 170),
        "text": (248, 250, 252),
        "muted": (158, 174, 198),
        "cyan": spot_a,
        "purple": spot_b,
        "emerald": _hsl_rgb(154.0, 0.72, 0.54),
        "amber": _hsl_rgb(42.0, 0.94, 0.58),
        "rose": _hsl_rgb(348.0, 0.88, 0.60),
    }


def _make_light_world(
    hue: float,
    tint_bg: Tuple[int, int, int] = None,
    sec_hue: float = None,
) -> Dict[str, Any]:
    sh = (hue + 52.0) % 360.0 if sec_hue is None else sec_hue
    bg_top = tint_bg or _hsl_rgb(hue, 0.35, 0.97)
    bg_bot = (max(206, bg_top[0] - 12), max(210, bg_top[1] - 10), max(218, bg_top[2] - 8))
    pri = _hsl_rgb(hue, 0.86, 0.40)
    sec = _hsl_rgb(sh, 0.82, 0.44)
    return {
        "is_light": True,
        "bg_top": bg_top,
        "bg_bot": bg_bot,
        "spot_a": _hsl_rgb(hue, 0.85, 0.52),
        "spot_b": _hsl_rgb(sh, 0.80, 0.58),
        "spot_c": _hsl_rgb((hue + 140.0) % 360.0, 0.72, 0.52),
        "grid_col": (148, 163, 184),
        "card_bg": (255, 255, 255, 242),
        "card_layer": (max(200, bg_top[0] - 18), max(206, bg_top[1] - 16), max(216, bg_top[2] - 12), 235),
        "card_alt": (241, 245, 249, 246),
        "glass_rim": (255, 255, 255, 235),
        "border": (148, 163, 184, 178),
        "shadow_col": (15, 23, 42, 46),
        "text": (15, 23, 42),
        "muted": (71, 85, 105),
        "cyan": pri,
        "purple": sec,
        "emerald": (5, 145, 100),
        "amber": (212, 114, 6),
        "rose": (220, 28, 70),
    }


# 46 Curated Named Studio Color Worlds (Dark, Light, Cyberpunk, Editorial, Metallic, Pastel)
STUDIO_WORLDS: Dict[str, Dict[str, Any]] = {
    "obsidian_studio": _make_dark_world(198, sec_hue=272, bg_hue=220, bg_sat=0.38, bg_lit=0.05),
    "sapphire_3d": _make_dark_world(192, sec_hue=238, bg_hue=215, bg_sat=0.62, bg_lit=0.065),
    "studio_white": _make_light_world(198, tint_bg=(245, 248, 253), sec_hue=265),
    "crimson_studio": _make_dark_world(348, sec_hue=38, bg_hue=325, bg_sat=0.45, bg_lit=0.055),
    "emerald_matrix": _make_dark_world(156, sec_hue=192, bg_hue=165, bg_sat=0.48, bg_lit=0.052),
    "amber_carbon": _make_dark_world(38, sec_hue=198, bg_hue=28, bg_sat=0.22, bg_lit=0.055),
    "violet_nebula": _make_dark_world(275, sec_hue=325, bg_hue=268, bg_sat=0.52, bg_lit=0.06),
    "warm_sand_light": _make_light_world(24, tint_bg=(250, 246, 238), sec_hue=214),
    "mint_paper_light": _make_light_world(158, tint_bg=(241, 249, 245), sec_hue=202),
    "arctic_ice": _make_dark_world(188, sec_hue=212, bg_hue=205, bg_sat=0.38, bg_lit=0.07),
    "cyber_lime": _make_dark_world(88, sec_hue=184, bg_hue=140, bg_sat=0.32, bg_lit=0.048),
    "midnight_rose": _make_dark_world(335, sec_hue=275, bg_hue=310, bg_sat=0.40, bg_lit=0.055),
    "solarized_dark": _make_dark_world(184, sec_hue=44, bg_hue=194, bg_sat=0.72, bg_lit=0.075),
    "nordic_slate": _make_dark_world(205, sat=0.55, sec_hue=175, bg_hue=218, bg_sat=0.26, bg_lit=0.09),
    "lavender_light": _make_light_world(262, tint_bg=(246, 244, 253), sec_hue=196),
    "peach_editorial": _make_light_world(16, tint_bg=(253, 245, 242), sec_hue=278),
    "cobalt_blueprint": _make_dark_world(214, sec_hue=184, bg_hue=218, bg_sat=0.74, bg_lit=0.085),
    "graphite_gold": _make_dark_world(45, sat=0.88, sec_hue=210, bg_hue=220, bg_sat=0.10, bg_lit=0.07),
    "teal_abyss": _make_dark_world(174, sec_hue=142, bg_hue=182, bg_sat=0.60, bg_lit=0.05),
    "coral_sunset": _make_dark_world(14, sec_hue=322, bg_hue=345, bg_sat=0.40, bg_lit=0.065),
    "monochrome_ink": _make_dark_world(215, sat=0.18, sec_hue=215, bg_hue=220, bg_sat=0.08, bg_lit=0.055),
    "neon_tokyo": _make_dark_world(318, sat=0.92, sec_hue=184, bg_hue=255, bg_sat=0.55, bg_lit=0.055),
    "forest_paper": _make_light_world(145, tint_bg=(243, 248, 243), sec_hue=36),
    "copper_rust": _make_dark_world(22, sec_hue=186, bg_hue=16, bg_sat=0.38, bg_lit=0.058),
    "slate_ivory": _make_light_world(218, tint_bg=(247, 247, 245), sec_hue=350),
    "aurora_borealis": _make_dark_world(162, sat=0.90, sec_hue=278, bg_hue=205, bg_sat=0.58, bg_lit=0.05, third_hue=320),
    "synthwave_84": _make_dark_world(302, sat=0.94, sec_hue=186, bg_hue=265, bg_sat=0.64, bg_lit=0.058, third_hue=44),
    "quantum_indigo": _make_dark_world(236, sat=0.85, sec_hue=182, bg_hue=238, bg_sat=0.55, bg_lit=0.055),
    "plasma_magenta": _make_dark_world(328, sat=0.92, sec_hue=252, bg_hue=315, bg_sat=0.48, bg_lit=0.05),
    "deep_oceanic": _make_dark_world(194, sat=0.84, sec_hue=164, bg_hue=202, bg_sat=0.68, bg_lit=0.052),
    "terracotta_warm": _make_dark_world(18, sat=0.80, sec_hue=42, bg_hue=12, bg_sat=0.36, bg_lit=0.068),
    "ruby_velvet": _make_dark_world(352, sat=0.86, sec_hue=288, bg_hue=346, bg_sat=0.45, bg_lit=0.052),
    "jade_imperial": _make_dark_world(160, sat=0.78, sec_hue=48, bg_hue=166, bg_sat=0.52, bg_lit=0.055),
    "electric_citron": _make_dark_world(68, sat=0.92, sec_hue=178, bg_hue=90, bg_sat=0.32, bg_lit=0.05),
    "titanium_silver": _make_dark_world(210, sat=0.28, sec_hue=192, bg_hue=215, bg_sat=0.14, bg_lit=0.085),
    "sky_daylight": _make_light_world(204, tint_bg=(240, 247, 255), sec_hue=252),
    "cream_notion": _make_light_world(34, tint_bg=(252, 249, 242), sec_hue=210),
    "blush_quartz": _make_light_world(342, tint_bg=(254, 243, 247), sec_hue=268),
    "glacier_frost": _make_light_world(188, tint_bg=(241, 250, 252), sec_hue=224),
    "swiss_poster": _make_light_world(4, tint_bg=(248, 246, 242), sec_hue=220),
    "pistachio_soft": _make_light_world(112, tint_bg=(243, 250, 241), sec_hue=196),
    "matcha_minimal": _make_light_world(96, tint_bg=(245, 248, 238), sec_hue=28),
    "midnight_gold": _make_dark_world(46, sat=0.92, sec_hue=280, bg_hue=230, bg_sat=0.36, bg_lit=0.048),
    "biotech_teal": _make_dark_world(176, sat=0.90, sec_hue=96, bg_hue=188, bg_sat=0.56, bg_lit=0.048),
    "solar_flare": _make_dark_world(26, sat=0.94, sec_hue=346, bg_hue=15, bg_sat=0.45, bg_lit=0.055),
    "terminal_phosphor": _make_dark_world(132, sat=0.94, sec_hue=176, bg_hue=135, bg_sat=0.42, bg_lit=0.04),
}


def generate_hsl_world(
    seed_or_hex: str = "",
    mode: str = "auto",
    secondary_hex: str = "",
    stops: List[str] = None,
) -> Dict[str, Any]:
    """
    Unlimited Procedural HSL & Multi-Stop Gradient World Generator:
    Accepts any #HEX, multi-stop list, hue angle ('hue:210'), or freeform topic string.
    """
    if stops and len(stops) >= 2:
        seed_or_hex = str(stops[0])
        secondary_hex = str(stops[1])
        third_hex = str(stops[2]) if len(stops) >= 3 else ""
    else:
        third_hex = ""

    raw = str(seed_or_hex or "nanopro").strip()
    sec_hue = None
    third_hue = None
    if raw.startswith("#") and len(raw.lstrip("#")) == 6:
        r, g, b = _hex_to_rgb(raw)
        h_f, _, s_f = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        hue = h_f * 360.0
        sat = max(0.65, min(0.95, s_f if s_f > 0.2 else 0.85))
    elif raw.lower().startswith("hue:"):
        try:
            hue = float(raw.split(":", 1)[1]) % 360.0
        except ValueError:
            hue = 198.0
        sat = 0.86
    else:
        digest = int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)
        hue = float(digest % 360)
        sat = 0.78 + ((digest >> 8) % 16) * 0.01

    if secondary_hex and secondary_hex.startswith("#") and len(secondary_hex.lstrip("#")) == 6:
        sr, sg, sb = _hex_to_rgb(secondary_hex)
        sh_f, _, _ = colorsys.rgb_to_hls(sr / 255.0, sg / 255.0, sb / 255.0)
        sec_hue = sh_f * 360.0
    if third_hex and third_hex.startswith("#") and len(third_hex.lstrip("#")) == 6:
        tr, tg, tb = _hex_to_rgb(third_hex)
        th_f, _, _ = colorsys.rgb_to_hls(tr / 255.0, tg / 255.0, tb / 255.0)
        third_hue = th_f * 360.0

    m = str(mode or "auto").lower().strip()
    if m == "auto":
        digest = int(hashlib.sha256((raw + "_m").encode("utf-8")).hexdigest()[:4], 16)
        m = "light" if (digest % 5 == 0) else "dark"

    if m == "light":
        return _make_light_world(hue, sec_hue=sec_hue)
    return _make_dark_world(hue, sat=sat, sec_hue=sec_hue, third_hue=third_hue)


def resolve_studio_world(
    art_style: str = "",
    tone: str = "",
    visual_data: Dict[str, Any] = None,
    topic: str = "",
) -> Dict[str, Any]:
    """Resolves either one of 46 curated studio worlds or an infinite procedural HSL/gradient world."""
    vd = visual_data or {}
    pal_spec = vd.get("palette")
    if isinstance(pal_spec, dict) and (pal_spec.get("primary") or pal_spec.get("hue") or pal_spec.get("mode") or pal_spec.get("stops")):
        seed = str(pal_spec.get("primary") or (f"hue:{pal_spec['hue']}" if "hue" in pal_spec else topic or "custom"))
        return generate_hsl_world(
            seed,
            mode=str(pal_spec.get("mode", "auto")),
            secondary_hex=str(pal_spec.get("secondary", "")),
            stops=pal_spec.get("stops") if isinstance(pal_spec.get("stops"), list) else None,
        )

    s = str(art_style or "").lower().strip()
    if s in STUDIO_WORLDS:
        return STUDIO_WORLDS[s]
    if s.startswith("#") or s.startswith("hue:") or s in ("dynamic_hsl", "procedural", "hsl", "gradient"):
        return generate_hsl_world(s if s not in ("dynamic_hsl", "procedural", "hsl", "gradient") else (topic or "dynamic"))
    if s in ("light_whiteboard", "white"):
        return STUDIO_WORLDS["studio_white"]
    if s in ("blueprint_grid",):
        return STUDIO_WORLDS["sapphire_3d"]
    if s in ("neon_fireship",):
        return STUDIO_WORLDS["neon_tokyo"]
    if s in ("editorial_dark",):
        dark_pool = ["obsidian_studio", "nordic_slate", "graphite_gold", "emerald_matrix", "violet_nebula", "arctic_ice", "aurora_borealis", "quantum_indigo"]
        if topic:
            idx = int(hashlib.sha256(topic.encode("utf-8")).hexdigest()[:4], 16) % len(dark_pool)
            return STUDIO_WORLDS[dark_pool[idx]]
        return STUDIO_WORLDS["obsidian_studio"]

    t = str(tone or "").lower().strip()
    if t == "dramatic_performance":
        return STUDIO_WORLDS["crimson_studio"]
    if t == "staff_engineer":
        return STUDIO_WORLDS["sapphire_3d"]
    if t == "mentor_storyteller":
        return STUDIO_WORLDS["emerald_matrix"]
    if topic:
        return generate_hsl_world(topic, mode="dark")
    return STUDIO_WORLDS["obsidian_studio"]
