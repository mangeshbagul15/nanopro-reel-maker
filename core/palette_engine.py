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


def _rel_luminance(rgb: Tuple[int, ...]) -> float:
    """WCAG relative luminance for (R, G, B)."""
    def _lin(c: float) -> float:
        x = max(0.0, min(1.0, c / 255.0))
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(rgb[0]) + 0.7152 * _lin(rgb[1]) + 0.0722 * _lin(rgb[2])


def _contrast_ratio(c1: Tuple[int, ...], c2: Tuple[int, ...]) -> float:
    l1, l2 = _rel_luminance(c1[:3]), _rel_luminance(c2[:3])
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _clamp_accent_for_bg(rgb: Tuple[int, ...], bg_rgb: Tuple[int, ...], is_light: bool, min_ratio: float = 4.6) -> Tuple[int, int, int]:
    """Adjusts accent brightness so text/badges/lines always have strong contrast against bg/card."""
    cur = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    if _contrast_ratio(cur, bg_rgb) >= min_ratio:
        return cur
    r, g, b = cur[0] / 255.0, cur[1] / 255.0, cur[2] / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    for step in range(1, 20):
        nl = max(0.16, l - step * 0.035) if is_light else min(0.84, l + step * 0.035)
        ns = min(0.95, max(0.45, s))
        nr, ng, nb = colorsys.hls_to_rgb(h, nl, ns)
        cand = (int(round(nr * 255)), int(round(ng * 255)), int(round(nb * 255)))
        if _contrast_ratio(cand, bg_rgb) >= min_ratio:
            return cand
    return (15, 23, 42) if is_light else (248, 250, 252)


def _enforce_world_contrast(w: Dict[str, Any]) -> Dict[str, Any]:
    """Guarantees clean opposite foreground/background contrast on Dark & Light/White studio worlds."""
    out = dict(w)
    is_light = bool(out.get("is_light"))
    if is_light:
        # Clean white / light-grey canvas -> crisp deep-charcoal/navy opposite text
        bg_l = _rel_luminance(out["bg_top"])
        if bg_l < 0.78:
            out["bg_top"] = (246, 248, 251)
            out["bg_bot"] = (232, 236, 243)
        out["card_bg"] = (255, 255, 255, 248)
        out["card_alt"] = (241, 245, 249, 248)
        out["text"] = (12, 18, 32)
        out["muted"] = (45, 58, 78)
        ref_bg = (255, 255, 255)
        for ak in ("cyan", "purple", "emerald", "amber", "rose"):
            if ak in out:
                out[ak] = _clamp_accent_for_bg(out[ak], ref_bg, is_light=True, min_ratio=4.8)
    else:
        # Deep black / navy blue / espresso brown / charcoal grey -> crisp opposite white text
        bg_l = _rel_luminance(out["bg_top"])
        if bg_l > 0.14:
            out["bg_top"] = (11, 15, 25)
            out["bg_bot"] = (18, 24, 38)
        out["text"] = (248, 250, 252)
        out["muted"] = (196, 208, 224)
        ref_bg = out["card_bg"][:3]
        if _contrast_ratio(out["text"], ref_bg) < 8.5:
            out["card_bg"] = (16, 21, 34, 238)
            out["card_alt"] = (24, 32, 50, 242)
            ref_bg = out["card_bg"][:3]
        for ak in ("cyan", "purple", "emerald", "amber", "rose"):
            if ak in out:
                out[ak] = _clamp_accent_for_bg(out[ak], ref_bg, is_light=False, min_ratio=4.6)
    return out


def is_light_studio_world(art_style: str = "", world: Dict[str, Any] = None) -> bool:
    if isinstance(world, dict) and "is_light" in world:
        return bool(world["is_light"])
    s = str(art_style or "").lower().strip()
    if s in STUDIO_WORLDS:
        return bool(STUDIO_WORLDS[s].get("is_light"))
    return s in ("light_whiteboard", "white", "pure_white", "light_grey_editorial", "studio_white", "cream_notion", "warm_sand_light", "mint_paper_light", "lavender_light", "peach_editorial", "forest_paper", "slate_ivory", "sky_daylight", "blush_quartz", "glacier_frost", "swiss_poster", "pistachio_soft", "matcha_minimal")


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
    bg_bot = _hsl_rgb((bh + 20.0) % 360.0, min(0.58, bg_sat + 0.06), min(0.11, bg_lit + 0.032))
    spot_a = _hsl_rgb(hue, sat, 0.62)
    spot_b = _hsl_rgb(sh, min(0.94, sat), 0.64)
    spot_c = _hsl_rgb(th, min(0.88, sat), 0.58)
    card_rgb = _hsl_rgb(bh, min(0.40, bg_sat), min(0.125, bg_lit + 0.048))
    layer_rgb = _hsl_rgb(bh, min(0.38, bg_sat), max(0.03, bg_lit + 0.018))
    alt_rgb = _hsl_rgb(bh, min(0.45, bg_sat + 0.05), min(0.175, bg_lit + 0.08))
    return _enforce_world_contrast({
        "is_light": False,
        "bg_top": bg_top,
        "bg_bot": bg_bot,
        "spot_a": spot_a,
        "spot_b": spot_b,
        "spot_c": spot_c,
        "grid_col": _hsl_rgb(hue, 0.45, 0.55),
        "card_bg": (*card_rgb, 234),
        "card_layer": (*layer_rgb, 224),
        "card_alt": (*alt_rgb, 240),
        "glass_rim": (255, 255, 255, 86),
        "border": (*spot_a, 145),
        "shadow_col": (2, 4, 10, 175),
        "text": (248, 250, 252),
        "muted": (196, 208, 224),
        "cyan": spot_a,
        "purple": spot_b,
        "emerald": _hsl_rgb(154.0, 0.78, 0.58),
        "amber": _hsl_rgb(42.0, 0.94, 0.62),
        "rose": _hsl_rgb(348.0, 0.90, 0.64),
    })


def _make_light_world(
    hue: float,
    tint_bg: Tuple[int, int, int] = None,
    sec_hue: float = None,
) -> Dict[str, Any]:
    sh = (hue + 52.0) % 360.0 if sec_hue is None else sec_hue
    bg_top = tint_bg or _hsl_rgb(hue, 0.16, 0.96)
    bg_bot = (max(218, bg_top[0] - 10), max(222, bg_top[1] - 10), max(228, bg_top[2] - 8))
    pri = _hsl_rgb(hue, 0.88, 0.34)
    sec = _hsl_rgb(sh, 0.84, 0.38)
    return _enforce_world_contrast({
        "is_light": True,
        "bg_top": bg_top,
        "bg_bot": bg_bot,
        "spot_a": _hsl_rgb(hue, 0.85, 0.42),
        "spot_b": _hsl_rgb(sh, 0.80, 0.46),
        "spot_c": _hsl_rgb((hue + 140.0) % 360.0, 0.72, 0.40),
        "grid_col": (120, 134, 154),
        "card_bg": (255, 255, 255, 248),
        "card_layer": (236, 241, 247, 242),
        "card_alt": (241, 245, 249, 250),
        "glass_rim": (255, 255, 255, 240),
        "border": (100, 116, 139, 195),
        "shadow_col": (15, 23, 42, 42),
        "text": (12, 18, 32),
        "muted": (45, 58, 78),
        "cyan": pri,
        "purple": sec,
        "emerald": (4, 120, 87),
        "amber": (180, 83, 9),
        "rose": (190, 18, 60),
    })


# Curated High-Contrast Dark (Black, Navy Blue, Espresso Brown, Charcoal Grey) & Light (White, Light Grey) Studio Worlds
STUDIO_WORLDS: Dict[str, Dict[str, Any]] = {
    "obsidian_studio": _make_dark_world(198, sec_hue=272, bg_hue=220, bg_sat=0.14, bg_lit=0.045),
    "sapphire_3d": _make_dark_world(196, sec_hue=228, bg_hue=220, bg_sat=0.58, bg_lit=0.075),
    "navy_studio": _make_dark_world(202, sec_hue=162, bg_hue=222, bg_sat=0.65, bg_lit=0.085),
    "espresso_brown": _make_dark_world(34, sec_hue=190, bg_hue=24, bg_sat=0.38, bg_lit=0.070),
    "onyx_black": _make_dark_world(194, sec_hue=44, bg_hue=220, bg_sat=0.05, bg_lit=0.035),
    "charcoal_grey": _make_dark_world(198, sec_hue=158, bg_hue=215, bg_sat=0.08, bg_lit=0.095),
    "studio_white": _make_light_world(214, tint_bg=(252, 253, 255), sec_hue=258),
    "pure_white": _make_light_world(210, tint_bg=(255, 255, 255), sec_hue=162),
    "light_grey_editorial": _make_light_world(216, tint_bg=(238, 241, 246), sec_hue=24),
    "cobalt_blueprint": _make_dark_world(206, sec_hue=42, bg_hue=220, bg_sat=0.70, bg_lit=0.082),
    "nordic_slate": _make_dark_world(202, sat=0.75, sec_hue=162, bg_hue=216, bg_sat=0.16, bg_lit=0.090),
    "graphite_gold": _make_dark_world(44, sat=0.90, sec_hue=205, bg_hue=220, bg_sat=0.06, bg_lit=0.065),
    "amber_carbon": _make_dark_world(38, sec_hue=196, bg_hue=26, bg_sat=0.28, bg_lit=0.062),
    "copper_rust": _make_dark_world(24, sec_hue=192, bg_hue=18, bg_sat=0.36, bg_lit=0.068),
    "terracotta_warm": _make_dark_world(22, sat=0.84, sec_hue=44, bg_hue=18, bg_sat=0.34, bg_lit=0.072),
    "crimson_studio": _make_dark_world(348, sec_hue=40, bg_hue=225, bg_sat=0.22, bg_lit=0.055),
    "emerald_matrix": _make_dark_world(158, sec_hue=196, bg_hue=215, bg_sat=0.22, bg_lit=0.052),
    "violet_nebula": _make_dark_world(262, sec_hue=192, bg_hue=232, bg_sat=0.45, bg_lit=0.062),
    "quantum_indigo": _make_dark_world(224, sat=0.86, sec_hue=184, bg_hue=228, bg_sat=0.58, bg_lit=0.065),
    "deep_oceanic": _make_dark_world(196, sat=0.86, sec_hue=162, bg_hue=212, bg_sat=0.62, bg_lit=0.062),
    "arctic_ice": _make_dark_world(192, sec_hue=216, bg_hue=214, bg_sat=0.32, bg_lit=0.075),
    "monochrome_ink": _make_dark_world(214, sat=0.24, sec_hue=200, bg_hue=218, bg_sat=0.04, bg_lit=0.050),
    "titanium_silver": _make_dark_world(208, sat=0.42, sec_hue=188, bg_hue=215, bg_sat=0.08, bg_lit=0.090),
    "midnight_gold": _make_dark_world(45, sat=0.92, sec_hue=214, bg_hue=224, bg_sat=0.42, bg_lit=0.060),
    "aurora_borealis": _make_dark_world(162, sat=0.88, sec_hue=214, bg_hue=218, bg_sat=0.52, bg_lit=0.060),
    "teal_abyss": _make_dark_world(176, sec_hue=210, bg_hue=208, bg_sat=0.48, bg_lit=0.055),
    "warm_sand_light": _make_light_world(24, tint_bg=(248, 245, 239), sec_hue=216),
    "cream_notion": _make_light_world(28, tint_bg=(252, 249, 244), sec_hue=214),
    "slate_ivory": _make_light_world(216, tint_bg=(242, 244, 247), sec_hue=26),
    "sky_daylight": _make_light_world(212, tint_bg=(244, 248, 253), sec_hue=248),
    "glacier_frost": _make_light_world(202, tint_bg=(240, 245, 250), sec_hue=226),
    "swiss_poster": _make_light_world(14, tint_bg=(248, 247, 245), sec_hue=218),
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
        m = "light" if (digest % 4 == 0) else "dark"

    # Anchor dark bases toward clean Navy Blue, Espresso Brown, Charcoal Grey or Deep Black
    if m == "light":
        light_bases = ((255, 255, 255), (242, 244, 248), (250, 247, 241), (245, 247, 250))
        pick = light_bases[int(hue) % len(light_bases)]
        return _make_light_world(hue, tint_bg=pick, sec_hue=sec_hue)
    anchor_bgs = ((220, 0.58, 0.075), (24, 0.36, 0.068), (220, 0.08, 0.045), (216, 0.12, 0.088))
    bg_h, bg_s, bg_l = anchor_bgs[int(hue) % len(anchor_bgs)]
    return _make_dark_world(hue, sat=sat, sec_hue=sec_hue, bg_hue=bg_h, bg_sat=bg_s, bg_lit=bg_l, third_hue=third_hue)


def resolve_studio_world(
    art_style: str = "",
    tone: str = "",
    visual_data: Dict[str, Any] = None,
    topic: str = "",
) -> Dict[str, Any]:
    """Resolves a high-contrast curated studio world (Dark Black/Navy/Brown/Grey or Light White/Grey) or HSL world."""
    vd = visual_data or {}
    pal_spec = vd.get("palette")
    if isinstance(pal_spec, dict) and (pal_spec.get("primary") or pal_spec.get("hue") or pal_spec.get("mode") or pal_spec.get("stops")):
        seed = str(pal_spec.get("primary") or (f"hue:{pal_spec['hue']}" if "hue" in pal_spec else topic or "custom"))
        return _enforce_world_contrast(generate_hsl_world(
            seed,
            mode=str(pal_spec.get("mode", "auto")),
            secondary_hex=str(pal_spec.get("secondary", "")),
            stops=pal_spec.get("stops") if isinstance(pal_spec.get("stops"), list) else None,
        ))

    s = str(art_style or "").lower().strip()
    if s in STUDIO_WORLDS:
        return _enforce_world_contrast(STUDIO_WORLDS[s])
    if s.startswith("#") or s.startswith("hue:") or s in ("dynamic_hsl", "procedural", "hsl", "gradient"):
        return _enforce_world_contrast(generate_hsl_world(s if s not in ("dynamic_hsl", "procedural", "hsl", "gradient") else (topic or "dynamic")))
    if s in ("light_whiteboard", "white", "pure_white"):
        return _enforce_world_contrast(STUDIO_WORLDS["studio_white"])
    if s in ("light_grey",):
        return _enforce_world_contrast(STUDIO_WORLDS["light_grey_editorial"])
    if s in ("blueprint_grid", "navy"):
        return _enforce_world_contrast(STUDIO_WORLDS["navy_studio"])
    if s in ("brown", "espresso"):
        return _enforce_world_contrast(STUDIO_WORLDS["espresso_brown"])
    if s in ("neon_fireship",):
        return _enforce_world_contrast(STUDIO_WORLDS["obsidian_studio"])
    if s in ("editorial_dark",):
        dark_pool = ["obsidian_studio", "navy_studio", "espresso_brown", "charcoal_grey", "nordic_slate", "graphite_gold", "onyx_black", "quantum_indigo"]
        if topic:
            idx = int(hashlib.sha256(topic.encode("utf-8")).hexdigest()[:4], 16) % len(dark_pool)
            return _enforce_world_contrast(STUDIO_WORLDS[dark_pool[idx]])
        return _enforce_world_contrast(STUDIO_WORLDS["obsidian_studio"])

    t = str(tone or "").lower().strip()
    if t:
        try:
            from core.tone_engine import get_tone_profile
            pw = str(get_tone_profile(t).get("preferred_world") or "")
            if pw in STUDIO_WORLDS:
                return _enforce_world_contrast(STUDIO_WORLDS[pw])
        except Exception:
            pass
    if topic:
        return _enforce_world_contrast(generate_hsl_world(topic, mode="dark"))
    return _enforce_world_contrast(STUDIO_WORLDS["obsidian_studio"])
