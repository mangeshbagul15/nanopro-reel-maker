import math
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image


def _with_alpha(col: Tuple[int, ...], alpha_mul: float) -> Tuple[int, int, int, int]:
    a_m = max(0.0, min(1.0, alpha_mul))
    base_a = col[3] if len(col) >= 4 else 255
    return (int(col[0]), int(col[1]), int(col[2]), max(0, min(255, int(base_a * a_m))))


# =========================================================================
# 60+ COMPACT PATH-DRIVEN DEVELOPER & UI VECTOR ICONS (-1.0 .. +1.0 space)
# Primitives: ('L', x1,y1,x2,y2), ('C', cx,cy,r), ('R', x1,y1,x2,y2), ('P', [(x,y),...]), ('A', cx,cy,r,start,end)
# =========================================================================
VECTOR_GLYPHS: Dict[str, List[Tuple[Any, ...]]] = {
    "check": [("P", [(-0.52, 0.02), (-0.12, 0.44), (0.58, -0.40)])],
    "warn": [("L", 0, -0.52, 0, 0.14), ("C", 0, 0.44, 0.08)],
    "close": [("L", -0.45, -0.45, 0.45, 0.45), ("L", 0.45, -0.45, -0.45, 0.45)],
    "plus": [("L", 0, -0.52, 0, 0.52), ("L", -0.52, 0, 0.52, 0)],
    "minus": [("L", -0.52, 0, 0.52, 0)],
    "bolt": [("P", [(0.12, -0.68), (-0.42, 0.08), (0.04, 0.08), (-0.12, 0.68), (0.44, -0.08), (-0.02, -0.08)])],
    "lock": [("A", 0, -0.22, 0.34, 180, 360), ("R", -0.48, -0.14, 0.48, 0.58)],
    "unlock": [("A", -0.16, -0.28, 0.30, 180, 360), ("R", -0.48, -0.10, 0.48, 0.58)],
    "key": [("C", -0.34, 0.0, 0.28), ("L", -0.06, 0.0, 0.62, 0.0), ("L", 0.36, 0.0, 0.36, 0.28), ("L", 0.58, 0.0, 0.58, 0.28)],
    "db": [("A", 0, -0.44, 0.50, 0, 360), ("L", -0.50, -0.44, -0.50, 0.44), ("L", 0.50, -0.44, 0.50, 0.44), ("A", 0, 0.44, 0.50, 0, 180), ("A", 0, 0.0, 0.50, 0, 180)],
    "code": [("P", [(-0.26, -0.38), (-0.64, 0.0), (-0.26, 0.38)]), ("P", [(0.26, -0.38), (0.64, 0.0), (0.26, 0.38)]), ("L", 0.12, -0.46, -0.12, 0.46)],
    "terminal": [("R", -0.62, -0.48, 0.62, 0.48), ("P", [(-0.42, -0.18), (-0.18, 0.02), (-0.42, 0.22)]), ("L", -0.02, 0.22, 0.36, 0.22)],
    "search": [("C", -0.14, -0.14, 0.40), ("L", 0.16, 0.16, 0.56, 0.56)],
    "chart": [("R", -0.56, 0.08, -0.26, 0.56), ("R", -0.14, -0.32, 0.16, 0.56), ("R", 0.28, -0.58, 0.58, 0.56)],
    "line_chart": [("P", [(-0.58, 0.36), (-0.18, -0.06), (0.14, 0.16), (0.58, -0.42)]), ("L", -0.60, 0.54, 0.60, 0.54)],
    "cloud": [("A", -0.26, -0.02, 0.32, 120, 320), ("A", 0.08, -0.20, 0.34, 180, 360), ("A", 0.34, 0.06, 0.26, -60, 90), ("L", -0.36, 0.32, 0.40, 0.32)],
    "upload": [("L", 0, 0.44, 0, -0.46), ("P", [(-0.34, -0.16), (0, -0.52), (0.34, -0.16)]), ("L", -0.48, 0.54, 0.48, 0.54)],
    "download": [("L", 0, -0.46, 0, 0.44), ("P", [(-0.34, 0.14), (0, 0.50), (0.34, 0.14)]), ("L", -0.48, 0.58, 0.48, 0.58)],
    "cpu": [("R", -0.38, -0.38, 0.38, 0.38), ("L", -0.60, -0.20, -0.38, -0.20), ("L", -0.60, 0.20, -0.38, 0.20), ("L", 0.38, -0.20, 0.60, -0.20), ("L", 0.38, 0.20, 0.60, 0.20), ("L", -0.20, -0.60, -0.20, -0.38), ("L", 0.20, -0.60, 0.20, -0.38)],
    "chip": [("R", -0.44, -0.44, 0.44, 0.44), ("R", -0.20, -0.20, 0.20, 0.20), ("L", -0.64, 0, -0.44, 0), ("L", 0.44, 0, 0.64, 0), ("L", 0, -0.64, 0, -0.44), ("L", 0, 0.44, 0, 0.64)],
    "network": [("C", 0, -0.44, 0.16), ("C", -0.44, 0.38, 0.16), ("C", 0.44, 0.38, 0.16), ("L", 0, -0.28, -0.36, 0.24), ("L", 0, -0.28, 0.36, 0.24), ("L", -0.28, 0.38, 0.28, 0.38)],
    "wifi": [("A", 0, 0.32, 0.62, 220, 320), ("A", 0, 0.32, 0.38, 220, 320), ("C", 0, 0.34, 0.08)],
    "globe": [("C", 0, 0, 0.56), ("L", -0.56, 0, 0.56, 0), ("L", 0, -0.56, 0, 0.56), ("A", 0, 0, 0.30, 0, 360)],
    "shield": [("P", [(0, -0.58), (-0.50, -0.34), (-0.40, 0.22), (0, 0.60), (0.40, 0.22), (0.50, -0.34), (0, -0.58)])],
    "bug": [("C", 0, 0.08, 0.32), ("L", -0.54, -0.10, -0.30, 0.04), ("L", 0.54, -0.10, 0.30, 0.04), ("L", -0.54, 0.26, -0.30, 0.16), ("L", 0.54, 0.26, 0.30, 0.16)],
    "fire": [("P", [(0, -0.60), (-0.42, -0.02), (-0.30, 0.52), (0.30, 0.52), (0.44, 0.02), (0.14, -0.20), (0, -0.60)])],
    "clock": [("C", 0, 0, 0.56), ("L", 0, 0, 0, -0.34), ("L", 0, 0, 0.28, 0.18)],
    "calendar": [("R", -0.52, -0.42, 0.52, 0.52), ("L", -0.52, -0.12, 0.52, -0.12), ("L", -0.24, -0.58, -0.24, -0.32), ("L", 0.24, -0.58, 0.24, -0.32)],
    "layers": [("P", [(0, -0.54), (0.56, -0.24), (0, 0.06), (-0.56, -0.24), (0, -0.54)]), ("P", [(-0.56, 0.08), (0, 0.38), (0.56, 0.08)]), ("P", [(-0.56, 0.36), (0, 0.64), (0.56, 0.36)])],
    "filter": [("P", [(-0.56, -0.46), (0.56, -0.46), (0.14, 0.08), (0.14, 0.54), (-0.14, 0.54), (-0.14, 0.08), (-0.56, -0.46)])],
    "users": [("C", -0.20, -0.24, 0.22), ("A", -0.20, 0.56, 0.42, 200, 340), ("C", 0.28, -0.18, 0.18)],
    "user": [("C", 0, -0.24, 0.24), ("A", 0, 0.58, 0.46, 200, 340)],
    "sparkles": [("P", [(0, -0.60), (0.14, -0.14), (0.60, 0), (0.14, 0.14), (0, 0.60), (-0.14, 0.14), (-0.60, 0), (-0.14, -0.14), (0, -0.60)])],
    "refresh": [("A", 0, 0, 0.48, 30, 320), ("P", [(0.36, -0.48), (0.54, -0.16), (0.20, -0.18)])],
    "sync": [("L", -0.44, -0.20, 0.44, -0.20), ("P", [(0.22, -0.40), (0.48, -0.20), (0.22, 0.0)]), ("L", 0.44, 0.22, -0.44, 0.22), ("P", [(-0.22, 0.02), (-0.48, 0.22), (-0.22, 0.42)])],
    "rocket": [("P", [(0, -0.62), (0.30, -0.06), (0.24, 0.40), (-0.24, 0.40), (-0.30, -0.06), (0, -0.62)]), ("C", 0, -0.12, 0.12)],
    "link": [("R", -0.58, -0.20, 0.08, 0.20), ("R", -0.08, -0.20, 0.58, 0.20)],
    "webhook": [("C", -0.34, 0.26, 0.22), ("C", 0.34, 0.26, 0.22), ("C", 0, -0.34, 0.22), ("L", -0.22, 0.10, -0.08, -0.16)],
    "folder": [("P", [(-0.58, -0.44), (-0.12, -0.44), (0.04, -0.24), (0.58, -0.24), (0.58, 0.46), (-0.58, 0.46), (-0.58, -0.44)])],
    "file": [("P", [(-0.42, -0.56), (0.18, -0.56), (0.44, -0.28), (0.44, 0.56), (-0.42, 0.56), (-0.42, -0.56)])],
    "gear": [("C", 0, 0, 0.42), ("C", 0, 0, 0.16), ("L", 0, -0.62, 0, -0.42), ("L", 0, 0.42, 0, 0.62), ("L", -0.62, 0, -0.42, 0), ("L", 0.42, 0, 0.62, 0)],
    "sliders": [("L", -0.54, -0.30, 0.54, -0.30), ("C", -0.16, -0.30, 0.12), ("L", -0.54, 0.26, 0.54, 0.26), ("C", 0.22, 0.26, 0.12)],
    "bell": [("A", 0, 0.06, 0.42, 180, 360), ("L", -0.50, 0.28, 0.50, 0.28), ("C", 0, 0.46, 0.10)],
    "eye": [("A", 0, 0.34, 0.68, 215, 325), ("A", 0, -0.34, 0.68, 35, 145), ("C", 0, 0, 0.18)],
    "target": [("C", 0, 0, 0.56), ("C", 0, 0, 0.32), ("C", 0, 0, 0.10)],
    "compass": [("C", 0, 0, 0.56), ("P", [(0, -0.34), (0.16, 0), (0, 0.34), (-0.16, 0), (0, -0.34)])],
    "flag": [("L", -0.34, -0.56, -0.34, 0.58), ("P", [(-0.34, -0.54), (0.46, -0.30), (-0.34, -0.02)])],
    "trophy": [("P", [(-0.42, -0.48), (0.42, -0.48), (0.28, 0.12), (-0.28, 0.12), (-0.42, -0.48)]), ("L", 0, 0.12, 0, 0.46), ("L", -0.28, 0.48, 0.28, 0.48)],
    "star": [("P", [(0, -0.58), (0.16, -0.16), (0.58, -0.16), (0.24, 0.12), (0.36, 0.54), (0, 0.28), (-0.36, 0.54), (-0.24, 0.12), (-0.58, -0.16), (-0.16, -0.16), (0, -0.58)])],
    "heart": [("C", -0.22, -0.16, 0.24), ("C", 0.22, -0.16, 0.24), ("P", [(-0.44, -0.08), (0, 0.48), (0.44, -0.08)])],
    "copy": [("R", -0.44, -0.18, 0.18, 0.52), ("R", -0.18, -0.52, 0.44, 0.18)],
    "play": [("P", [(-0.32, -0.46), (0.48, 0.0), (-0.32, 0.46), (-0.32, -0.46)])],
    "arrow_up": [("L", 0, 0.52, 0, -0.48), ("P", [(-0.34, -0.14), (0, -0.52), (0.34, -0.14)])],
    "arrow_down": [("L", 0, -0.52, 0, 0.48), ("P", [(-0.34, 0.14), (0, 0.52), (0.34, 0.14)])],
    "arrow_right": [("L", -0.52, 0, 0.48, 0), ("P", [(0.14, -0.34), (0.52, 0), (0.14, 0.34)])],
    "branch": [("C", -0.32, -0.38, 0.14), ("C", -0.32, 0.38, 0.14), ("C", 0.34, -0.16, 0.14), ("L", -0.32, -0.24, -0.32, 0.24), ("P", [(-0.32, 0.24), (0.34, -0.02)])],
    "box": [("R", -0.50, -0.50, 0.50, 0.50), ("L", -0.50, -0.14, 0.50, -0.14)],
    "server": [("R", -0.54, -0.48, 0.54, -0.06), ("R", -0.54, 0.06, 0.54, 0.48), ("C", -0.32, -0.27, 0.06), ("C", -0.32, 0.27, 0.06)],
    "mobile": [("R", -0.34, -0.58, 0.34, 0.58), ("C", 0, 0.42, 0.06)],
    "monitor": [("R", -0.58, -0.46, 0.58, 0.26), ("L", 0, 0.26, 0, 0.50), ("L", -0.28, 0.50, 0.28, 0.50)],
    "battery": [("R", -0.56, -0.32, 0.44, 0.32), ("R", 0.44, -0.14, 0.58, 0.14), ("R", -0.44, -0.18, 0.12, 0.18)],
    "plug": [("L", -0.22, -0.54, -0.22, -0.20), ("L", 0.22, -0.54, 0.22, -0.20), ("R", -0.38, -0.20, 0.38, 0.24), ("L", 0, 0.24, 0, 0.58)],
    "magnet": [("A", 0, -0.08, 0.42, 0, 180), ("L", -0.42, -0.46, -0.42, -0.08), ("L", 0.42, -0.46, 0.42, -0.08)],
    "dashboard": [("R", -0.54, -0.54, -0.06, -0.06), ("R", 0.06, -0.54, 0.54, 0.12), ("R", -0.54, 0.06, -0.06, 0.54), ("R", 0.06, 0.24, 0.54, 0.54)],
}


def draw_vector_glyph(
    stage: Any,
    cx: int,
    cy: int,
    kind: str,
    radius: int,
    color: Tuple[int, int, int],
    alpha_mul: float,
    with_badge: bool = True,
) -> None:
    """Renders any of the 60+ VECTOR_GLYPHS crisp icons cleanly with optional circle backing."""
    eff_a = alpha_mul * stage.t_alpha
    if eff_a <= 0.02:
        return
    c = _with_alpha(color, eff_a)
    ink = _with_alpha(stage.world["text"], eff_a)
    if with_badge:
        stage.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_with_alpha((*color[:3], 42), eff_a), outline=c, width=3)
    k = str(kind or "check").lower().strip()
    if k in ("warning",):
        k = "warn"
    elif k in ("fast", "speed", "flash", "zap"):
        k = "bolt"
    elif k in ("storage", "database", "sql", "postgres"):
        k = "db"
    elif k in ("api", "dev"):
        k = "code"
    elif k in ("rag", "query"):
        k = "search"
    elif k in ("metric", "bar"):
        k = "chart"
    elif k in ("sec", "security"):
        k = "shield"

    ops = VECTOR_GLYPHS.get(k, VECTOR_GLYPHS["check"])
    sc = radius * 0.68
    pen = c if k in ("bolt", "fire", "star", "heart") else ink
    lw = max(2, int(round(radius * 0.15)))
    for op in ops:
        t = op[0]
        if t == "L":
            stage.draw.line((cx + op[1] * sc, cy + op[2] * sc, cx + op[3] * sc, cy + op[4] * sc), fill=pen, width=lw)
        elif t == "C":
            r = max(2.0, op[3] * sc)
            stage.draw.ellipse((cx + op[1] * sc - r, cy + op[2] * sc - r, cx + op[1] * sc + r, cy + op[2] * sc + r), outline=pen, width=lw)
        elif t == "R":
            stage.draw.rounded_rectangle((cx + op[1] * sc, cy + op[2] * sc, cx + op[3] * sc, cy + op[4] * sc), radius=max(2, int(sc * 0.14)), outline=pen, width=lw)
        elif t == "P":
            pts = [(cx + px * sc, cy + py * sc) for px, py in op[1]]
            if len(pts) >= 2:
                stage.draw.line(pts, fill=pen, width=lw)
        elif t == "A":
            r = max(2.0, op[3] * sc)
            stage.draw.arc((cx + op[1] * sc - r, cy + op[2] * sc - r, cx + op[1] * sc + r, cy + op[2] * sc + r), start=op[4], end=op[5], fill=pen, width=lw)


# =========================================================================
# ALL 50 3D ISOMETRIC & PARAMETRIC TECH SHAPES (+ ICONIFY SVG PEDESTAL)
# =========================================================================
ALL_50_SHAPES: Tuple[str, ...] = (
    "box", "stack", "cylinder", "sphere", "hexagon", "pyramid", "diamond", "cloud",
    "shield", "chip", "bucket", "gear", "bot",
    "server_rack", "lock", "key", "globe", "router", "funnel", "queue", "rocket",
    "bolt_3d", "document", "terminal_box", "bell", "clock", "magnifier", "container",
    "bridge", "brain_node", "database_cluster", "load_balancer", "cdn_edge", "antenna",
    "monitor", "mobile", "folder", "code_cube", "plug", "battery", "gauge_dial",
    "magnet", "layers_wafer", "prism_tri", "torus", "cube_cutout", "gate_xor",
    "packet_envelope", "scale_balance", "trophy",
)

# Maps semantic extra 3D shapes (14..50) cleanly to base 3D silhouette + crisp front/top 3D emblem
_PEDESTAL_SHAPES: Dict[str, Tuple[str, str]] = {
    "server_rack": ("stack", "server"),
    "lock": ("hexagon", "lock"),
    "key": ("diamond", "key"),
    "globe": ("sphere", "globe"),
    "router": ("box", "wifi"),
    "queue": ("stack", "sync"),
    "rocket": ("hexagon", "rocket"),
    "bolt_3d": ("diamond", "bolt"),
    "document": ("box", "file"),
    "terminal_box": ("box", "terminal"),
    "bell": ("hexagon", "bell"),
    "clock": ("sphere", "clock"),
    "magnifier": ("hexagon", "search"),
    "container": ("box", "layers"),
    "bridge": ("box", "link"),
    "brain_node": ("sphere", "sparkles"),
    "database_cluster": ("cylinder", "db"),
    "load_balancer": ("diamond", "network"),
    "cdn_edge": ("cloud", "globe"),
    "antenna": ("pyramid", "wifi"),
    "monitor": ("box", "monitor"),
    "mobile": ("hexagon", "mobile"),
    "folder": ("box", "folder"),
    "code_cube": ("box", "code"),
    "plug": ("hexagon", "plug"),
    "battery": ("cylinder", "battery"),
    "gauge_dial": ("sphere", "chart"),
    "magnet": ("hexagon", "magnet"),
    "layers_wafer": ("stack", "layers"),
    "gate_xor": ("diamond", "branch"),
    "packet_envelope": ("box", "arrow_right"),
    "scale_balance": ("pyramid", "sliders"),
    "trophy": ("hexagon", "trophy"),
}


def infer_3d_shape(label: str, fallback: str = "box") -> str:
    low = str(label or "").lower()
    checks = [
        (("db", "database", "vector", "sql", "pg", "redis", "store", "cache", "index", "table"), "cylinder"),
        (("cluster", "replica", "shard"), "database_cluster"),
        (("cloud", "aws", "gcp", "azure", "vpc", "saas"), "cloud"),
        (("cdn", "edge", "cloudflare"), "cdn_edge"),
        (("auth", "sec", "soc", "guard", "firewall", "siem", "jwt", "vault", "trust"), "shield"),
        (("lock", "encrypt", "tls", "ssl", "secret"), "lock"),
        (("key", "token", "oauth"), "key"),
        (("ai", "llm", "gpt", "agent", "bot"), "bot"),
        (("brain", "neural", "reasoning"), "brain_node"),
        (("cpu", "gpu", "chip", "kernel", "embed", "tokenizer", "inference", "wasm"), "chip"),
        (("s3", "bucket", "lake", "parquet", "blob"), "bucket"),
        (("k8s", "kube", "docker", "pod", "container"), "container"),
        (("microservice", "hexagon", "mesh"), "hexagon"),
        (("rack", "server", "host", "node"), "server_rack"),
        (("stack", "layer", "rag", "fine-tuning"), "layers_wafer"),
        (("queue", "kafka", "rabbit", "sqs", "stream", "broker"), "queue"),
        (("balancer", "gateway", "proxy", "ingress"), "load_balancer"),
        (("router", "switch", "dns"), "router"),
        (("search", "retrieve", "query"), "magnifier"),
        (("code", "python", "script", "fn", "lambda"), "code_cube"),
        (("terminal", "cli", "bash", "shell"), "terminal_box"),
        (("funnel", "filter", "triage"), "funnel"),
        (("pyramid", "hierarchy", "tier"), "pyramid"),
        (("rocket", "deploy", "launch", "fast"), "rocket"),
        (("globe", "region", "multi-region", "world"), "globe"),
        (("latency", "timer", "timeout", "ttl"), "clock"),
        (("alert", "alarm", "notify", "webhook"), "bell"),
        (("cron", "worker", "job", "engine"), "gear"),
        (("hub", "core", "network"), "sphere"),
    ]
    for kws, shp in checks:
        if any(k in low for k in kws):
            return shp
    return fallback


def draw_3d_shape(
    stage: Any,
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
    icon_img: Optional[Image.Image] = None,
) -> None:
    """
    Draws any of the 50 3D Shapes or floats an Iconify SVG brand/tech logo cleanly
    above an illuminated 3D isometric pedestal.
    """
    eff_a = alpha_mul * stage.t_alpha
    if eff_a <= 0.03:
        return
    bob = int(round(math.sin(progress * math.pi * 4.0 + phase) * 4.5)) if active else 0
    cy_live = cy + bob
    shp = str(shape or "box").lower().strip()

    stage.add_shadow_ellipse((cx - rx - 8, cy + depth + 6, cx + rx + 8, cy + depth + ry + 18), alpha_mul * 0.85)
    if active:
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(progress * math.pi * 4.0))
        stage.add_glow_orb(cx, cy_live + depth * 0.25, rx * 1.08, color, alpha=int(155 * pulse))

    r, g, b = color[:3]
    top_col = _with_alpha((min(255, r + 58), min(255, g + 58), min(255, b + 58), 246), eff_a)
    left_col = _with_alpha((max(18, int(r * 0.56)), max(22, int(g * 0.58)), max(30, int(b * 0.62)), 250), eff_a)
    right_col = _with_alpha((max(10, int(r * 0.34)), max(14, int(g * 0.36)), max(20, int(b * 0.42)), 252), eff_a)
    wire_col = _with_alpha((min(255, r + 95), min(255, g + 95), min(255, b + 95), 245 if active else 175), eff_a)
    dark_core = _with_alpha((14, 21, 38, 250), eff_a)

    # If a real Iconify SVG raster logo is provided, mount it cleanly over an illuminated 3D disc/pedestal
    if icon_img is not None:
        ped_y = cy_live + depth // 2 + 6
        stage.draw.ellipse((cx - rx, ped_y, cx + rx, ped_y + ry), fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - int(rx * 0.72), ped_y + 4, cx + int(rx * 0.72), ped_y + ry - 4), fill=top_col)
        target_sz = max(36, int(min(rx * 1.5, depth + ry * 1.1)))
        if not stage.world.get("is_light"):
            # Subtle frosted glow backing keeps dark SVG brand marks (AWS/GitHub/Linux) crisp on dark backgrounds
            stage.add_glow_orb(cx, cy_live + target_sz // 8, target_sz * 0.58, (226, 232, 240), alpha=78)
        ic = icon_img.resize((target_sz, target_sz), Image.Resampling.BILINEAR)
        if eff_a < 0.99:
            alpha_ch = ic.split()[3].point(lambda p: int(p * eff_a))
            ic.putalpha(alpha_ch)
        stage.fg.alpha_composite(ic, (cx - target_sz // 2, cy_live - target_sz // 3))
        return

    # Check if composite pedestal shape
    pedestal_glyph = None
    if shp in _PEDESTAL_SHAPES:
        base_shp, pedestal_glyph = _PEDESTAL_SHAPES[shp]
        shp = base_shp

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
        stage.draw.arc((cx - int(rad * 1.35), mid_cy - int(rad * 0.42), cx + int(rad * 1.35), mid_cy + int(rad * 0.42)), start=-18, end=198, fill=wire_col, width=3)

    elif shp == "hexagon":
        hr = int(rx * 0.92)
        hr_y = int(ry * 1.15)
        hex_top = [(cx + int(hr * math.cos(math.radians(a))), cy_live + int(hr_y * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
        ext = int(depth * 0.72)
        for idx in (0, 1, 2):
            p1, p2 = hex_top[idx], hex_top[(idx + 1) % 6]
            stage.draw.polygon([p1, p2, (p2[0], p2[1] + ext), (p1[0], p1[1] + ext)], fill=left_col if idx < 2 else right_col, outline=wire_col, width=2)
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

    elif shp == "funnel":
        bot_apex = (cx, cy_live + depth + 16)
        tl = (cx - rx, cy_live - ry // 2)
        tf = (cx, cy_live + ry // 2)
        tr = (cx + rx, cy_live - ry // 2)
        stage.draw.polygon([tl, tf, bot_apex], fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon([tf, tr, bot_apex], fill=right_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - rx, cy_live - ry, cx + rx, cy_live), fill=top_col, outline=wire_col, width=2)

    elif shp == "prism_tri":
        t_tri = [(cx, cy_live - ry - 6), (cx + rx, cy_live + ry), (cx - rx, cy_live + ry)]
        d = int(depth * 0.75)
        stage.draw.polygon([(cx - rx, cy_live + ry), (cx + rx, cy_live + ry), (cx + rx, cy_live + ry + d), (cx - rx, cy_live + ry + d)], fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon(t_tri, fill=top_col, outline=wire_col, width=3)

    elif shp == "torus":
        mid_cy = cy_live + depth // 3
        stage.draw.ellipse((cx - rx, mid_cy - ry - 10, cx + rx, mid_cy + ry + 18), fill=left_col, outline=wire_col, width=3)
        stage.draw.ellipse((cx - rx, mid_cy - ry - 18, cx + rx, mid_cy + ry + 10), fill=top_col, outline=wire_col, width=3)
        stage.draw.ellipse((cx - rx // 2, mid_cy - ry // 2 - 4, cx + rx // 2, mid_cy + ry // 2 - 4), fill=dark_core, outline=wire_col, width=2)

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
        stage.draw.polygon([(cx, ty_s), (cx - sw, ty_s + 14), (cx - int(sw * 0.78), my_s + 12), (cx, by_s)], fill=top_col, outline=wire_col, width=2)
        stage.draw.polygon([(cx, ty_s), (cx + sw, ty_s + 14), (cx + int(sw * 0.78), my_s + 12), (cx, by_s)], fill=right_col, outline=wire_col, width=2)
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

    else:  # "box" / "cube_cutout"
        t_pts = [(cx, cy_live - ry), (cx + rx, cy_live), (cx, cy_live + ry), (cx - rx, cy_live)]
        l_pts = [(cx - rx, cy_live), (cx, cy_live + ry), (cx, cy_live + ry + depth), (cx - rx, cy_live + depth)]
        r_pts = [(cx + rx, cy_live), (cx, cy_live + ry), (cx, cy_live + ry + depth), (cx + rx, cy_live + depth)]
        stage.draw.polygon(l_pts, fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon(r_pts, fill=right_col, outline=wire_col, width=2)
        stage.draw.polygon(t_pts, fill=top_col, outline=wire_col, width=3 if active else 2)
        irx, iry = int(rx * (0.45 if shp == "cube_cutout" else 0.62)), int(ry * (0.45 if shp == "cube_cutout" else 0.62))
        inner_top = [(cx, cy_live - iry), (cx + irx, cy_live), (cx, cy_live + iry), (cx - irx, cy_live)]
        stage.draw.polygon(inner_top, fill=dark_core if shp == "cube_cutout" else None, outline=_with_alpha(color, alpha_mul * 0.85), width=2)
        stage.draw.line((cx - rx + 10, cy_live + 12, cx - rx + 10, cy_live + depth - 4), fill=wire_col, width=3)

    if pedestal_glyph:
        draw_vector_glyph(stage, cx, cy_live + depth // 3, pedestal_glyph, max(16, int(rx * 0.38)), color, eff_a, with_badge=True)
