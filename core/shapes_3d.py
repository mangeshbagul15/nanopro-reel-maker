import math
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from core.mesh_shader_engine import ALL_3D_MESHES, draw_procedural_3d_mesh
from core.svg_engine import extrude_image_to_3d


def _with_alpha(col: Tuple[int, ...], alpha_mul: float) -> Tuple[int, int, int, int]:
    a_m = max(0.0, min(1.0, alpha_mul))
    base_a = col[3] if len(col) >= 4 else 255
    return (int(col[0]), int(col[1]), int(col[2]), max(0, min(255, int(base_a * a_m))))


# =========================================================================
# 168 CRISP VECTOR ICONS (IT, Hardware, Networking, Data Eng, SDLC, Langs, AI)
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
    "arrow_left": [("L", 0.52, 0, -0.48, 0), ("P", [(-0.14, -0.34), (-0.52, 0), (-0.14, 0.34)])],
    "pause": [("R", -0.36, -0.46, -0.12, 0.46), ("R", 0.12, -0.46, 0.36, 0.46)],
    "stop": [("R", -0.42, -0.42, 0.42, 0.42)],
    "mic": [("R", -0.22, -0.54, 0.22, 0.16), ("A", 0, -0.04, 0.42, 0, 180), ("L", 0, 0.38, 0, 0.58)],
    "volume": [("P", [(-0.54, -0.20), (-0.22, -0.20), (0.14, -0.48), (0.14, 0.48), (-0.22, 0.20), (-0.54, 0.20), (-0.54, -0.20)]), ("A", 0.18, 0, 0.34, -55, 55)],
    "camera": [("R", -0.56, -0.32, 0.56, 0.46), ("C", 0, 0.08, 0.22), ("P", [(-0.24, -0.32), (-0.12, -0.50), (0.12, -0.50), (0.24, -0.32)])],
    "video": [("R", -0.56, -0.38, 0.22, 0.38), ("P", [(0.22, -0.18), (0.58, -0.36), (0.58, 0.36), (0.22, 0.18)])],
    "image": [("R", -0.54, -0.46, 0.54, 0.46), ("C", -0.22, -0.16, 0.10), ("P", [(-0.46, 0.40), (-0.08, 0.04), (0.16, 0.24), (0.48, -0.10)])],
    "music": [("C", -0.28, 0.36, 0.16), ("C", 0.26, 0.26, 0.16), ("P", [(-0.12, 0.36), (-0.12, -0.44), (0.42, -0.52), (0.42, 0.26)])],
    "trash": [("L", -0.52, -0.38, 0.52, -0.38), ("P", [(-0.38, -0.38), (-0.30, 0.52), (0.30, 0.52), (0.38, -0.38)]), ("L", -0.16, -0.54, 0.16, -0.54)],
    "edit": [("P", [(-0.48, 0.48), (-0.38, 0.14), (0.28, -0.52), (0.52, -0.28), (-0.14, 0.38), (-0.48, 0.48)])],
    "pin": [("P", [(0, -0.56), (-0.28, -0.06), (0.28, -0.06), (0, -0.56)]), ("L", 0, -0.06, 0, 0.56)],
    "bookmark": [("P", [(-0.36, -0.52), (0.36, -0.52), (0.36, 0.54), (0, 0.24), (-0.36, 0.54), (-0.36, -0.52)])],
    "tag": [("P", [(-0.54, -0.54), (0.04, -0.54), (0.54, -0.04), (-0.04, 0.54), (-0.54, 0.04), (-0.54, -0.54)]), ("C", -0.26, -0.26, 0.08)],
    "mail": [("R", -0.56, -0.38, 0.56, 0.38), ("P", [(-0.54, -0.36), (0, 0.08), (0.54, -0.36)])],
    "message": [("R", -0.54, -0.44, 0.54, 0.26), ("P", [(-0.28, 0.26), (-0.36, 0.54), (0.02, 0.26)])],
    "send": [("P", [(-0.52, -0.10), (0.56, -0.52), (0.14, 0.56), (-0.12, 0.14), (-0.52, -0.10)]), ("L", -0.12, 0.14, 0.52, -0.48)],
    "share": [("C", -0.38, 0.0, 0.16), ("C", 0.36, -0.36, 0.16), ("C", 0.36, 0.36, 0.16), ("L", -0.24, -0.08, 0.22, -0.28), ("L", -0.24, 0.08, 0.22, 0.28)],
    "bot_head": [("R", -0.48, -0.36, 0.48, 0.44), ("C", -0.20, 0.04, 0.09), ("C", 0.20, 0.04, 0.09), ("L", 0, -0.56, 0, -0.36)],
    "brain": [("A", -0.24, -0.06, 0.34, 90, 290), ("A", 0.24, -0.06, 0.34, -110, 90), ("L", 0, -0.40, 0, 0.42)],
    "atom": [("C", 0, 0, 0.12), ("A", 0, 0, 0.58, 0, 360), ("L", -0.48, -0.28, 0.48, 0.28), ("L", -0.48, 0.28, 0.48, -0.28)],
    "dna": [("P", [(-0.34, -0.54), (0.34, -0.18), (-0.34, 0.18), (0.34, 0.54)]), ("P", [(0.34, -0.54), (-0.34, -0.18), (0.34, 0.18), (-0.34, 0.54)]), ("L", -0.34, -0.54, 0.34, -0.54), ("L", -0.34, 0.18, 0.34, 0.18)],
    "flask": [("L", -0.20, -0.54, 0.20, -0.54), ("P", [(-0.14, -0.54), (-0.14, -0.14), (-0.48, 0.50), (0.48, 0.50), (0.14, -0.14), (0.14, -0.54)])],
    "microscope": [("L", -0.44, 0.52, 0.44, 0.52), ("L", 0, 0.52, 0, 0.18), ("P", [(-0.10, -0.52), (0.20, -0.52), (0.04, 0.12), (-0.26, 0.12), (-0.10, -0.52)])],
    "sigma": [("P", [(0.42, -0.52), (-0.42, -0.52), (0.08, 0.0), (-0.42, 0.52), (0.42, 0.52)])],
    "infinity": [("C", -0.30, 0.0, 0.26), ("C", 0.30, 0.0, 0.26)],
    "lambda": [("L", -0.42, 0.54, 0.04, -0.12), ("P", [(-0.24, -0.54), (0.04, -0.12), (0.44, 0.54)])],
    "pi": [("L", -0.48, -0.38, 0.48, -0.38), ("L", -0.22, -0.38, -0.22, 0.48), ("L", 0.22, -0.38, 0.22, 0.48)],
    "percent": [("C", -0.32, -0.32, 0.14), ("C", 0.32, 0.32, 0.14), ("L", 0.42, -0.46, -0.42, 0.46)],
    "dollar": [("L", 0, -0.58, 0, 0.58), ("A", 0, -0.20, 0.24, 90, 320), ("A", 0, 0.22, 0.24, -90, 140)],
    "bank": [("P", [(-0.56, -0.18), (0, -0.56), (0.56, -0.18), (-0.56, -0.18)]), ("L", -0.36, -0.14, -0.36, 0.42), ("L", 0, -0.14, 0, 0.42), ("L", 0.36, -0.14, 0.36, 0.42), ("L", -0.58, 0.48, 0.58, 0.48)],
    "wallet": [("R", -0.54, -0.38, 0.54, 0.42), ("R", 0.14, -0.10, 0.54, 0.18), ("C", 0.30, 0.04, 0.06)],
    "cart": [("P", [(-0.58, -0.44), (-0.36, -0.44), (-0.22, 0.24), (0.46, 0.24), (0.58, -0.22), (-0.32, -0.22)]), ("C", -0.18, 0.46, 0.10), ("C", 0.38, 0.46, 0.10)],
    "package": [("P", [(0, -0.56), (0.52, -0.28), (0, 0), (-0.52, -0.28), (0, -0.56)]), ("P", [(-0.52, -0.28), (-0.52, 0.30), (0, 0.58), (0.52, 0.30), (0.52, -0.28)]), ("L", 0, 0, 0, 0.58)],
    "truck": [("R", -0.58, -0.32, 0.16, 0.30), ("P", [(0.16, -0.18), (0.48, -0.18), (0.58, 0.08), (0.58, 0.30), (0.16, 0.30)]), ("C", -0.34, 0.42, 0.14), ("C", 0.38, 0.42, 0.14)],
    "map_pin": [("C", 0, -0.16, 0.32), ("P", [(-0.30, -0.02), (0, 0.58), (0.30, -0.02)])],
    "anchor": [("C", 0, -0.42, 0.12), ("L", 0, -0.30, 0, 0.48), ("L", -0.28, -0.14, 0.28, -0.14), ("A", 0, 0.08, 0.44, 15, 165)],
    "feather": [("P", [(-0.44, 0.48), (0.44, -0.48), (0.48, -0.12), (0.04, 0.34), (-0.44, 0.48)])],
    "award": [("C", 0, -0.16, 0.34), ("P", [(-0.18, 0.16), (-0.26, 0.58), (0, 0.42), (0.26, 0.58), (0.18, 0.16)])],
    "crown": [("P", [(-0.52, 0.38), (-0.56, -0.24), (-0.22, 0.08), (0, -0.38), (0.22, 0.08), (0.56, -0.24), (0.52, 0.38), (-0.52, 0.38)])],
    "flame": [("P", [(0, -0.58), (0.36, -0.12), (0.34, 0.40), (-0.02, 0.56), (-0.36, 0.36), (-0.30, -0.06), (0, -0.58)])],
    "sun": [("C", 0, 0, 0.28), ("L", 0, -0.58, 0, -0.42), ("L", 0, 0.42, 0, 0.58), ("L", -0.58, 0, -0.42, 0), ("L", 0.42, 0, 0.58, 0)],
    "moon": [("A", 0, 0, 0.52, 40, 290), ("A", 0.24, -0.12, 0.42, 85, 255)],
    "umbrella": [("A", 0, 0.02, 0.54, 180, 360), ("L", -0.54, 0.02, 0.54, 0.02), ("L", 0, 0.02, 0, 0.48)],
    "home": [("P", [(-0.54, -0.04), (0, -0.54), (0.54, -0.04)]), ("R", -0.38, -0.04, 0.38, 0.52)],
    "building": [("R", -0.42, -0.54, 0.42, 0.54), ("R", -0.18, -0.30, -0.02, -0.12), ("R", 0.06, -0.30, 0.22, -0.12), ("R", -0.18, 0.02, -0.02, 0.20), ("R", 0.06, 0.02, 0.22, 0.20)],
    "briefcase": [("R", -0.54, -0.26, 0.54, 0.46), ("P", [(-0.22, -0.26), (-0.22, -0.46), (0.22, -0.46), (0.22, -0.26)]), ("L", -0.54, 0.06, 0.54, 0.06)],
    "book": [("R", -0.50, -0.48, 0.50, 0.48), ("L", -0.24, -0.48, -0.24, 0.48)],
    "newspaper": [("R", -0.54, -0.44, 0.54, 0.44), ("R", -0.36, -0.26, 0.06, 0.06), ("L", 0.16, -0.22, 0.40, -0.22), ("L", 0.16, -0.04, 0.40, -0.04)],
    "clipboard": [("R", -0.46, -0.42, 0.46, 0.54), ("R", -0.18, -0.54, 0.18, -0.32), ("L", -0.26, 0.04, 0.26, 0.04)],
    "list_ul": [("C", -0.44, -0.30, 0.06), ("L", -0.22, -0.30, 0.48, -0.30), ("C", -0.44, 0.0, 0.06), ("L", -0.22, 0.0, 0.48, 0.0), ("C", -0.44, 0.30, 0.06), ("L", -0.22, 0.30, 0.48, 0.30)],
    "grid": [("R", -0.50, -0.50, -0.08, -0.08), ("R", 0.08, -0.50, 0.50, -0.08), ("R", -0.50, 0.08, -0.08, 0.50), ("R", 0.08, 0.08, 0.50, 0.50)],
    "kanban": [("R", -0.56, -0.48, -0.24, 0.46), ("R", -0.16, -0.48, 0.16, 0.18), ("R", 0.24, -0.48, 0.56, 0.36)],
    "git_merge": [("C", -0.32, -0.38, 0.14), ("C", -0.32, 0.38, 0.14), ("C", 0.34, 0.12, 0.14), ("L", -0.32, -0.24, -0.32, 0.24), ("P", [(-0.32, -0.22), (0.34, 0.0)])],
    "commit": [("L", -0.58, 0, -0.18, 0), ("C", 0, 0, 0.18), ("L", 0.18, 0, 0.58, 0)],
    "bug_fix": [("C", 0, 0.08, 0.30), ("L", -0.52, -0.52, 0.52, 0.52)],
    "fingerprint": [("A", 0, 0.08, 0.52, 160, 380), ("A", 0, 0.08, 0.32, 170, 370), ("L", 0, -0.06, 0, 0.38)],
    "radar_scan": [("C", 0, 0, 0.54), ("C", 0, 0, 0.26), ("L", 0, 0, 0.40, -0.38)],
    "hourglass": [("P", [(-0.40, -0.52), (0.40, -0.52), (-0.40, 0.52), (0.40, 0.52), (-0.40, -0.52)])],
    "scale": [("L", -0.52, -0.12, 0.52, -0.12), ("L", 0, -0.42, 0, 0.48), ("L", -0.30, 0.48, 0.30, 0.48), ("P", [(-0.52, -0.12), (-0.64, 0.20), (-0.40, 0.20), (-0.52, -0.12)]), ("P", [(0.52, -0.12), (0.40, 0.20), (0.64, 0.20), (0.52, -0.12)])],
    # +44 Dedicated IT Devices, Hardware, Networking, Data Engineering & SDLC Glyphs
    "laptop": [("R", -0.48, -0.44, 0.48, 0.14), ("P", [(-0.62, 0.44), (-0.48, 0.14), (0.48, 0.14), (0.62, 0.44), (-0.62, 0.44)])],
    "desktop": [("R", -0.58, -0.48, 0.22, 0.22), ("R", 0.30, -0.46, 0.60, 0.46), ("L", -0.18, 0.22, -0.18, 0.48), ("L", -0.38, 0.48, 0.02, 0.48)],
    "tablet": [("R", -0.42, -0.54, 0.42, 0.54), ("C", 0, 0.40, 0.06)],
    "smartwatch": [("R", -0.28, -0.32, 0.28, 0.32), ("L", -0.14, -0.54, 0.14, -0.54), ("L", -0.14, 0.54, 0.14, 0.54)],
    "printer": [("R", -0.52, -0.16, 0.52, 0.28), ("R", -0.30, -0.50, 0.30, -0.16), ("R", -0.30, 0.16, 0.30, 0.52)],
    "webcam": [("C", 0, -0.08, 0.38), ("C", 0, -0.08, 0.14), ("L", -0.30, 0.48, 0.30, 0.48), ("L", 0, 0.30, 0, 0.48)],
    "headset": [("A", 0, 0.02, 0.46, 180, 360), ("R", -0.56, 0.0, -0.34, 0.38), ("R", 0.34, 0.0, 0.56, 0.38)],
    "usb_drive": [("R", -0.24, -0.22, 0.24, 0.54), ("R", -0.16, -0.54, 0.16, -0.22)],
    "ssd": [("R", -0.46, -0.52, 0.46, 0.34), ("L", -0.28, 0.50, 0.28, 0.50), ("L", -0.32, -0.20, 0.14, -0.20)],
    "router_wifi": [("R", -0.56, 0.08, 0.56, 0.46), ("L", -0.32, 0.08, -0.32, -0.42), ("L", 0.32, 0.08, 0.32, -0.42), ("C", -0.24, 0.27, 0.05), ("C", 0.0, 0.27, 0.05)],
    "switch_ports": [("R", -0.60, -0.24, 0.60, 0.24), ("R", -0.46, -0.08, -0.32, 0.10), ("R", -0.20, -0.08, -0.06, 0.10), ("R", 0.06, -0.08, 0.20, 0.10), ("R", 0.32, -0.08, 0.46, 0.10)],
    "hub_star": [("C", 0, 0, 0.18), ("C", 0, -0.48, 0.10), ("C", -0.44, 0.32, 0.10), ("C", 0.44, 0.32, 0.10), ("L", 0, -0.18, 0, -0.38), ("L", -0.14, 0.10, -0.34, 0.24), ("L", 0.14, 0.10, 0.34, 0.24)],
    "firewall_brick": [("R", -0.56, -0.44, 0.56, 0.44), ("L", -0.56, -0.14, 0.56, -0.14), ("L", -0.56, 0.14, 0.56, 0.14), ("L", 0, -0.44, 0, -0.14), ("L", -0.22, -0.14, -0.22, 0.14), ("L", 0.22, 0.14, 0.22, 0.44)],
    "ethernet": [("R", -0.42, -0.46, 0.42, 0.26), ("L", -0.20, -0.46, -0.20, -0.20), ("L", 0, -0.46, 0, -0.20), ("L", 0.20, -0.46, 0.20, -0.20), ("L", 0, 0.26, 0, 0.58)],
    "patch_panel": [("R", -0.58, -0.36, 0.58, 0.36), ("L", -0.42, -0.10, 0.42, -0.10), ("L", -0.42, 0.14, 0.42, 0.14)],
    "fiber_cable": [("A", -0.24, 0.0, 0.36, 120, 300), ("A", 0.24, 0.0, 0.36, -60, 120), ("L", -0.56, 0, 0.56, 0)],
    "satellite_dish": [("A", -0.18, 0.18, 0.56, 225, 360), ("L", -0.18, 0.18, 0.32, -32), ("L", -0.44, 0.52, 0.18, 0.52)],
    "cell_tower": [("L", 0, -0.52, -0.28, 0.54), ("L", 0, -0.52, 0.28, 0.54), ("L", -0.16, 0.10, 0.16, 0.10), ("A", 0, -0.42, 0.36, 210, 330)],
    "dns_server": [("C", 0, -0.16, 0.36), ("R", -0.48, 0.30, 0.48, 0.58), ("C", -0.26, 0.44, 0.06)],
    "vpn_tunnel": [("A", 0, 0.10, 0.54, 180, 360), ("A", 0, 0.10, 0.28, 180, 360), ("L", -0.54, 0.10, 0.54, 0.10)],
    "load_balance": [("L", -0.54, 0, -0.12, 0), ("P", [(-0.12, 0), (0.46, -0.38)]), ("P", [(-0.12, 0), (0.46, 0.38)]), ("C", 0.50, -0.38, 0.10), ("C", 0.50, 0.38, 0.10)],
    "subnet_box": [("R", -0.56, -0.52, 0.56, 0.52), ("R", -0.34, -0.28, 0.0, 0.06), ("R", 0.08, 0.08, 0.42, 0.42)],
    "vlan_ring": [("C", -0.20, 0.0, 0.34), ("C", 0.20, 0.0, 0.34)],
    "data_pipe": [("L", -0.58, -0.22, 0.58, -0.22), ("L", -0.58, 0.22, 0.58, 0.22), ("P", [(-0.12, -0.10), (0.14, 0), (-0.12, 0.10)])],
    "data_lake": [("A", -0.34, 0.24, 0.22, 0, 180), ("A", 0.12, 0.24, 0.24, 0, 180), ("A", 0, -0.40, 0.42, 180, 360), ("L", -0.42, -0.16, -0.42, 0.22), ("L", 0.42, -0.16, 0.42, 0.22)],
    "lakehouse": [("P", [(-0.52, -0.12), (0, -0.54), (0.52, -0.12)]), ("L", -0.42, -0.12, -0.42, 0.44), ("L", 0.42, -0.12, 0.42, 0.44), ("A", 0, 0.44, 0.42, 0, 180)],
    "spark_star": [("P", [(0, -0.60), (0.16, -0.16), (0.60, 0), (0.16, 0.16), (0, 0.60), (-0.16, 0.16), (-0.60, 0), (-0.16, -0.16), (0, -0.60)])],
    "kafka_stream": [("C", 0, -0.44, 0.14), ("C", 0, 0.44, 0.14), ("C", 0.44, 0.0, 0.14), ("C", -0.32, 0.0, 0.18), ("L", -0.14, 0, 0.30, 0)],
    "warehouse": [("P", [(-0.56, -0.14), (0, -0.56), (0.56, -0.14), (0.56, 0.50), (-0.56, 0.50), (-0.56, -0.14)]), ("R", -0.26, 0.06, 0.26, 0.50)],
    "schema_rel": [("R", -0.56, -0.48, -0.12, 0.12), ("R", 0.12, -0.12, 0.56, 0.48), ("L", -0.12, -0.18, 0.12, 0.18)],
    "dag_nodes": [("C", -0.42, -0.36, 0.14), ("C", 0.42, -0.36, 0.14), ("C", 0.0, 0.40, 0.16), ("L", -0.32, -0.24, -0.08, 0.26), ("L", 0.32, -0.24, 0.08, 0.26)],
    "sdlc_cycle": [("A", 0, 0, 0.50, 25, 330), ("P", [(0.36, -0.48), (0.54, -0.16), (0.20, -0.18)]), ("C", 0, 0, 0.16)],
    "ci_rocket": [("L", -0.48, 0.48, 0.48, -0.48), ("P", [(0.08, -0.48), (0.48, -0.48), (0.48, -0.08)])],
    "unit_test": [("R", -0.52, -0.52, 0.52, 0.52), ("P", [(-0.26, 0.02), (-0.06, 0.24), (0.30, -0.22)])],
    "code_review": [("C", -0.22, -0.20, 0.24), ("C", 0.26, 0.24, 0.22), ("L", -0.04, -0.02, 0.10, 0.10)],
    "release_tag": [("P", [(-0.50, -0.48), (0.04, -0.48), (0.52, 0.0), (0.0, 0.52), (-0.48, 0.04), (-0.50, -0.48)])],
    "rollback": [("A", 0, 0.08, 0.46, 180, 30), ("P", [(-0.48, -0.32), (-0.52, 0.08), (-0.16, 0.02)])],
    "k8s_wheel": [("C", 0, 0, 0.48), ("C", 0, 0, 0.16), ("L", 0, -0.58, 0, 0.58), ("L", -0.54, -0.20, 0.54, 0.20), ("L", -0.54, 0.20, 0.54, -0.20)],
    "container_pod": [("P", [(0, -0.56), (0.52, -0.28), (0, 0), (-0.52, -0.28), (0, -0.56)]), ("R", -0.44, -0.06, 0.44, 0.52)],
    "git_pr": [("C", -0.34, -0.36, 0.12), ("C", -0.34, 0.36, 0.12), ("C", 0.36, 0.36, 0.12), ("L", -0.34, -0.24, -0.34, 0.24), ("P", [(-0.20, -0.36), (0.36, -0.36), (0.36, 0.24)])],
    "api_plug": [("R", -0.48, -0.24, 0.48, 0.24), ("L", -0.24, -0.52, -0.24, -0.24), ("L", 0.24, -0.52, 0.24, -0.24), ("L", 0, 0.24, 0, 0.56)],
    "sdk_box": [("R", -0.50, -0.50, 0.50, 0.50), ("P", [(-0.24, -0.14), (0, -0.36), (0.24, -0.14)]), ("L", -0.24, 0.18, 0.24, 0.18)],
    "blade_rack": [("R", -0.54, -0.54, 0.54, 0.54), ("L", -0.54, -0.18, 0.54, -0.18), ("L", -0.54, 0.18, 0.54, 0.18), ("C", 0.32, -0.36, 0.05), ("C", 0.32, 0.0, 0.05), ("C", 0.32, 0.36, 0.05)],
    "ups_power": [("R", -0.44, -0.56, 0.44, 0.56), ("P", [(0.08, -0.32), (-0.18, 0.02), (0.04, 0.02), (-0.08, 0.36), (0.20, 0.0), (-0.02, 0.0)])],
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
    eff_a = alpha_mul * stage.t_alpha
    if eff_a <= 0.02:
        return
    c = _with_alpha(color, eff_a)
    ink = _with_alpha(stage.world["text"], eff_a)
    if with_badge:
        stage.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_with_alpha((*color[:3], 42), eff_a), outline=c, width=3)
    k = str(kind or "check").lower().strip()
    alias = {"warning": "warn", "fast": "bolt", "speed": "bolt", "flash": "bolt", "zap": "bolt", "storage": "db", "database": "db", "sql": "db", "postgres": "db", "api": "code", "dev": "code", "rag": "search", "query": "search", "metric": "chart", "bar": "chart", "sec": "shield", "security": "shield", "pc": "desktop", "workstation": "desktop", "router": "router_wifi", "switch": "switch_ports", "hub": "hub_star", "firewall": "firewall_brick"}
    k = alias.get(k, k)

    ops = VECTOR_GLYPHS.get(k, VECTOR_GLYPHS["check"])
    sc = radius * 0.68
    pen = c if k in ("bolt", "fire", "flame", "star", "heart", "crown") else ink
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
# 145 3D SHAPES: TRUE HARDWARE MODELS + 3D CAMERA MESHES + PEDESTALS + 200K SVGs
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

EXTRA_55_SHAPES: Tuple[str, ...] = (
    "torus_3d", "dna_helix", "atom_orbit", "geodesic_sphere", "neural_lattice", "terrain_wave_3d",
    "bar_landscape_3d", "cube_cluster_3d", "vortex_spiral_3d", "mobius_ring", "icosahedron_3d", "octahedron_3d",
    "microservice", "wallet_3d", "bank_vault", "shopping_cart", "package_3d", "truck_delivery",
    "pin_beacon", "anchor_node", "crown_vip", "flame_core", "sun_star", "moon_phase",
    "building_dc", "book_docs", "clipboard_audit", "kanban_card", "merge_gate", "radar_dish",
    "hourglass_ttl", "fingerprint_auth", "sigma_math", "infinity_loop", "lambda_fn", "pie_disc",
    "mic_voice", "camera_vision", "video_stream", "music_wave", "mail_relay", "chat_node",
    "send_packet", "bot_agent", "flask_lab", "microscope_bio", "shield_zero", "usb_plug",
    "power_core", "satellite_link", "cloud_mesh", "vault_safe", "ledger_chain", "gpu_rack", "tpu_pod",
)

IT_NETWORK_DATA_SDLC_40_SHAPES: Tuple[str, ...] = (
    # Dedicated 3D Physical Hardware & Networking Devices
    "laptop", "desktop", "tablet", "network_switch", "hub", "firewall_wall", "ssd_nvme", "rack_cabinet",
    "smartwatch", "printer", "webcam", "headset", "usb_drive", "ethernet_port", "patch_panel", "fiber_cable",
    "cell_tower", "dns_server", "vpn_tunnel", "subnet_zone", "vlan_ring", "ups_battery",
    # Data Engineering & Big Data Shapes
    "data_pipe", "data_lake", "lakehouse", "spark_engine", "kafka_broker", "warehouse_3d", "schema_table", "dag_pipeline",
    # SDLC, CI/CD, Languages & Cloud Shapes
    "sdlc_wheel", "ci_runner", "unit_test_cube", "pr_merge", "release_tag_3d", "rollback_gate", "k8s_pod_mesh", "api_plug_3d", "sdk_module", "blade_server",
)

ALL_100_SHAPES: Tuple[str, ...] = ALL_50_SHAPES + EXTRA_55_SHAPES
ALL_145_SHAPES: Tuple[str, ...] = ALL_50_SHAPES + EXTRA_55_SHAPES + IT_NETWORK_DATA_SDLC_40_SHAPES

_PEDESTAL_SHAPES: Dict[str, Tuple[str, str]] = {
    "lock": ("hexagon", "lock"), "key": ("diamond", "key"), "globe": ("sphere", "globe"), "queue": ("stack", "sync"),
    "rocket": ("hexagon", "rocket"), "bolt_3d": ("diamond", "bolt"), "document": ("box", "file"),
    "terminal_box": ("box", "terminal"), "bell": ("hexagon", "bell"), "clock": ("sphere", "clock"),
    "magnifier": ("hexagon", "search"), "container": ("box", "layers"), "bridge": ("box", "link"),
    "brain_node": ("sphere", "brain"), "database_cluster": ("cylinder", "db"), "load_balancer": ("diamond", "load_balance"),
    "cdn_edge": ("cloud", "globe"), "antenna": ("pyramid", "wifi"), "monitor": ("desktop", "monitor"),
    "folder": ("box", "folder"), "code_cube": ("box", "code"), "plug": ("hexagon", "plug"),
    "battery": ("cylinder", "battery"), "gauge_dial": ("sphere", "chart"), "magnet": ("hexagon", "magnet"),
    "layers_wafer": ("stack", "layers"), "gate_xor": ("diamond", "branch"), "packet_envelope": ("box", "arrow_right"),
    "scale_balance": ("pyramid", "scale"), "trophy": ("hexagon", "trophy"),
    "microservice": ("hexagon", "grid"), "wallet_3d": ("box", "wallet"), "bank_vault": ("box", "bank"),
    "shopping_cart": ("box", "cart"), "package_3d": ("box", "package"), "truck_delivery": ("box", "truck"),
    "pin_beacon": ("pyramid", "map_pin"), "anchor_node": ("hexagon", "anchor"), "crown_vip": ("hexagon", "crown"),
    "flame_core": ("sphere", "flame"), "sun_star": ("sphere", "sun"), "moon_phase": ("sphere", "moon"),
    "building_dc": ("stack", "building"), "book_docs": ("box", "book"), "clipboard_audit": ("box", "clipboard"),
    "kanban_card": ("box", "kanban"), "merge_gate": ("diamond", "git_merge"), "radar_dish": ("sphere", "radar_scan"),
    "hourglass_ttl": ("cylinder", "hourglass"), "fingerprint_auth": ("hexagon", "fingerprint"),
    "sigma_math": ("box", "sigma"), "infinity_loop": ("torus", "infinity"), "lambda_fn": ("hexagon", "lambda"),
    "pie_disc": ("cylinder", "chart"), "mic_voice": ("cylinder", "mic"), "camera_vision": ("box", "camera"),
    "video_stream": ("box", "video"), "music_wave": ("sphere", "music"), "mail_relay": ("box", "mail"),
    "chat_node": ("hexagon", "message"), "send_packet": ("diamond", "send"), "bot_agent": ("bot", "bot_head"),
    "flask_lab": ("pyramid", "flask"), "microscope_bio": ("hexagon", "microscope"), "shield_zero": ("shield", "lock"),
    "usb_plug": ("box", "plug"), "power_core": ("sphere", "bolt"), "satellite_link": ("sphere", "satellite_dish"),
    "cloud_mesh": ("cloud", "network"), "vault_safe": ("box", "lock"), "ledger_chain": ("stack", "link"),
    "gpu_rack": ("chip", "cpu"), "tpu_pod": ("chip", "sparkles"),
    "smartwatch": ("hexagon", "smartwatch"), "printer": ("box", "printer"), "webcam": ("sphere", "webcam"),
    "headset": ("hexagon", "headset"), "usb_drive": ("ssd_nvme", "usb_drive"), "ethernet_port": ("network_switch", "ethernet"),
    "patch_panel": ("network_switch", "patch_panel"), "fiber_cable": ("torus", "fiber_cable"),
    "cell_tower": ("pyramid", "cell_tower"), "dns_server": ("cylinder", "dns_server"), "vpn_tunnel": ("shield", "vpn_tunnel"),
    "subnet_zone": ("hexagon", "subnet_box"), "vlan_ring": ("torus", "vlan_ring"), "ups_battery": ("rack_cabinet", "ups_power"),
    "data_pipe": ("cylinder", "data_pipe"), "data_lake": ("cylinder", "data_lake"), "lakehouse": ("pyramid", "lakehouse"),
    "spark_engine": ("diamond", "spark_star"), "kafka_broker": ("stack", "kafka_stream"), "warehouse_3d": ("stack", "warehouse"),
    "schema_table": ("box", "schema_rel"), "dag_pipeline": ("hexagon", "dag_nodes"),
    "sdlc_wheel": ("torus", "sdlc_cycle"), "ci_runner": ("hexagon", "ci_rocket"), "unit_test_cube": ("box", "unit_test"),
    "pr_merge": ("diamond", "git_pr"), "release_tag_3d": ("hexagon", "release_tag"), "rollback_gate": ("shield", "rollback"),
    "k8s_pod_mesh": ("container", "k8s_wheel"), "api_plug_3d": ("hexagon", "api_plug"), "sdk_module": ("box", "sdk_box"), "blade_server": ("server_rack", "blade_rack"),
}


def infer_3d_shape(label: str, fallback: str = "box") -> str:
    low = str(label or "").lower()
    checks = [
        (("laptop", "macbook", "notebook"), "laptop"),
        (("desktop", "pc", "workstation", "imac"), "desktop"),
        (("mobile", "phone", "iphone", "android"), "mobile"),
        (("tablet", "ipad"), "tablet"),
        (("router", "wifi", "gateway"), "router"),
        (("switch", "l2", "l3 switch", "ethernet"), "network_switch"),
        (("hub", "repeater", "mesh"), "hub"),
        (("firewall", "waf", "dmz"), "firewall_wall"),
        (("nvme", "ssd", "disk", "storage"), "ssd_nvme"),
        (("rack", "cabinet", "datacenter"), "rack_cabinet"),
        (("server", "host", "node", "ec2", "vm"), "server_rack"),
        (("lakehouse", "medallion", "bronze", "silver", "gold"), "lakehouse"),
        (("lake", "s3", "bucket", "parquet", "iceberg"), "data_lake"),
        (("warehouse", "snowflake", "bigquery", "redshift", "clickhouse"), "warehouse_3d"),
        (("kafka", "pulsar", "kinesis", "pubsub"), "kafka_broker"),
        (("spark", "flink", "beam", "transform", "dbt"), "spark_engine"),
        (("airflow", "dagster", "prefect", "dag", "etl", "elt", "pipeline"), "dag_pipeline"),
        (("sdlc", "lifecycle", "agile", "sprint"), "sdlc_wheel"),
        (("ci/cd", "ci", "cd", "jenkins", "actions", "deploy"), "ci_runner"),
        (("test", "qa", "pytest", "playwright", "jest"), "unit_test_cube"),
        (("git", "commit", "branch", "pr", "pull request"), "pr_merge"),
        (("db", "database", "vector", "sql", "pg", "redis", "store", "cache", "index", "table"), "cylinder"),
        (("cloud", "aws", "gcp", "azure", "vpc", "saas"), "cloud"),
        (("cdn", "edge", "cloudflare"), "cdn_edge"),
        (("auth", "sec", "soc", "guard", "siem", "jwt", "vault", "trust"), "shield"),
        (("lock", "encrypt", "tls", "ssl", "secret"), "lock"),
        (("key", "token", "oauth"), "key"),
        (("ai", "llm", "gpt", "agent", "bot"), "bot"),
        (("brain", "neural", "reasoning"), "brain_node"),
        (("dna", "gene", "bio"), "dna_helix"),
        (("atom", "quantum", "physics"), "atom_orbit"),
        (("cpu", "gpu", "chip", "kernel", "embed", "tokenizer", "inference", "wasm"), "chip"),
        (("k8s", "kube", "docker", "pod", "container"), "k8s_pod_mesh"),
        (("balancer", "proxy", "ingress"), "load_balancer"),
        (("search", "retrieve", "query"), "magnifier"),
        (("code", "python", "java", "script", "fn", "lambda"), "code_cube"),
        (("terminal", "cli", "bash", "shell"), "terminal_box"),
        (("funnel", "filter", "triage"), "funnel"),
        (("rocket", "fast"), "rocket"),
        (("globe", "region", "world"), "globe"),
        (("cron", "worker", "job", "engine"), "gear"),
        (("torus", "ring", "loop"), "torus_3d"),
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
    extrude_3d: bool = True,
) -> None:
    eff_a = alpha_mul * stage.t_alpha
    if eff_a <= 0.03:
        return
    bob = int(round(math.sin(progress * math.pi * 4.0 + phase) * 4.5)) if active else 0
    cy_live = cy + bob
    shp = str(shape or "box").lower().strip()
    if shp == "switch":
        shp = "network_switch"

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
    em_led = _with_alpha(stage.world.get("emerald", (16, 185, 129)), eff_a)
    am_led = _with_alpha(stage.world.get("amber", (245, 158, 11)), eff_a)

    if icon_img is not None:
        ped_y = cy_live + depth // 2 + 6
        stage.draw.ellipse((cx - rx, ped_y, cx + rx, ped_y + ry), fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - int(rx * 0.72), ped_y + 4, cx + int(rx * 0.72), ped_y + ry - 4), fill=top_col)
        target_sz = max(40, int(min(rx * 1.5, depth + ry * 1.15)))
        if not stage.world.get("is_light"):
            stage.add_glow_orb(cx, cy_live + target_sz // 8, target_sz * 0.58, (226, 232, 240), alpha=78)
        ic_resized = icon_img.resize((target_sz, target_sz), Image.Resampling.BILINEAR)
        ic_final = extrude_image_to_3d(ic_resized, depth=10, tint_rgb=color) if extrude_3d else ic_resized
        if eff_a < 0.99:
            alpha_ch = ic_final.split()[3].point(lambda p: int(p * eff_a))
            ic_final.putalpha(alpha_ch)
        stage.fg.alpha_composite(ic_final, (cx - ic_final.width // 2, cy_live - ic_final.height // 3))
        return

    if shp in ALL_3D_MESHES:
        draw_procedural_3d_mesh(stage, cx, cy_live + depth // 4, max(rx, depth), shp, color, progress=progress, active=active, alpha_mul=alpha_mul)
        return

    pedestal_glyph = None
    if shp in _PEDESTAL_SHAPES:
        shp, pedestal_glyph = _PEDESTAL_SHAPES[shp]

    # --- BESPOKE 3D PHYSICAL IT & NETWORKING HARDWARE GEOMETRIES ---
    if shp == "laptop":
        w_b, h_b = int(rx * 0.92), max(18, int(depth * 0.72))
        scr = [(cx - int(w_b * 0.78), cy_live - h_b), (cx + int(w_b * 0.78), cy_live - h_b), (cx + int(w_b * 0.78), cy_live + 4), (cx - int(w_b * 0.78), cy_live + 4)]
        stage.draw.polygon(scr, fill=dark_core, outline=wire_col, width=3)
        stage.draw.rounded_rectangle((cx - int(w_b * 0.64), cy_live - h_b + 6, cx + int(w_b * 0.64), cy_live - 2), radius=4, fill=left_col)
        deck = [(cx - int(w_b * 0.78), cy_live + 4), (cx + int(w_b * 0.78), cy_live + 4), (cx + w_b, cy_live + ry + 10), (cx - w_b, cy_live + ry + 10)]
        stage.draw.polygon(deck, fill=top_col, outline=wire_col, width=2)
        stage.draw.line((cx - int(w_b * 0.55), cy_live + 11, cx + int(w_b * 0.55), cy_live + 11), fill=dark_core, width=3)
    elif shp == "desktop":
        mw = int(rx * 0.72)
        stage.draw.rounded_rectangle((cx - rx, cy_live - ry - 8, cx + int(rx * 0.34), cy_live + depth // 2 + 2), radius=6, fill=dark_core, outline=wire_col, width=3)
        stage.draw.rounded_rectangle((cx - rx + 5, cy_live - ry - 3, cx + int(rx * 0.34) - 5, cy_live + depth // 2 - 4), radius=4, fill=left_col)
        stage.draw.line((cx - mw // 2, cy_live + depth // 2 + 2, cx - mw // 2, cy_live + depth), fill=wire_col, width=4)
        stage.draw.line((cx - rx // 2, cy_live + depth, cx, cy_live + depth), fill=wire_col, width=3)
        # Side PC Tower in 3D
        stage.draw.rounded_rectangle((cx + int(rx * 0.44), cy_live - ry, cx + rx, cy_live + depth + 4), radius=6, fill=right_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx + int(rx * 0.68), cy_live - ry + 8, cx + int(rx * 0.78), cy_live - ry + 16), fill=em_led)
    elif shp in ("mobile", "tablet"):
        bw = int(rx * (0.48 if shp == "mobile" else 0.74))
        bh = int(depth + ry * 0.8)
        stage.draw.rounded_rectangle((cx - bw, cy_live - ry // 2 - 6, cx + bw, cy_live + bh // 2 + 12), radius=10, fill=left_col, outline=wire_col, width=3)
        stage.draw.rounded_rectangle((cx - bw + 5, cy_live - ry // 2 + 2, cx + bw - 5, cy_live + bh // 2 + 2), radius=6, fill=dark_core, outline=top_col, width=2)
        stage.draw.line((cx - 8, cy_live + bh // 2 + 6, cx + 8, cy_live + bh // 2 + 6), fill=top_col, width=2)
    elif shp == "router":
        # 2 upright dual WiFi antennas + chamfered 3D body + LED dots
        stage.draw.line((cx - rx // 2, cy_live, cx - rx // 2 - 4, cy_live - ry - 18), fill=wire_col, width=4)
        stage.draw.line((cx + rx // 2, cy_live, cx + rx // 2 + 4, cy_live - ry - 18), fill=wire_col, width=4)
        stage.draw.ellipse((cx - rx // 2 - 7, cy_live - ry - 22, cx - rx // 2 - 1, cy_live - ry - 16), fill=em_led)
        stage.draw.ellipse((cx + rx // 2 + 1, cy_live - ry - 22, cx + rx // 2 + 7, cy_live - ry - 16), fill=em_led)
        t_pts = [(cx, cy_live - ry // 2), (cx + rx, cy_live + 4), (cx, cy_live + ry // 2 + 4), (cx - rx, cy_live + 4)]
        stage.draw.polygon(t_pts, fill=top_col, outline=wire_col, width=2)
        stage.draw.rounded_rectangle((cx - rx, cy_live + 4, cx + rx, cy_live + depth // 2 + 18), radius=6, fill=left_col, outline=wire_col, width=2)
        for li in range(-2, 3):
            stage.draw.ellipse((cx + li * 10 - 2, cy_live + depth // 2 + 8, cx + li * 10 + 2, cy_live + depth // 2 + 12), fill=em_led if li % 2 == 0 else am_led)
    elif shp == "network_switch":
        sh = max(20, depth // 2 + 8)
        t_pts = [(cx - int(rx * 0.85), cy_live - ry // 2), (cx + int(rx * 0.85), cy_live - ry // 2), (cx + rx, cy_live + 4), (cx - rx, cy_live + 4)]
        stage.draw.polygon(t_pts, fill=top_col, outline=wire_col, width=2)
        stage.draw.rounded_rectangle((cx - rx, cy_live + 4, cx + rx, cy_live + sh + 6), radius=5, fill=left_col, outline=wire_col, width=2)
        n_ports = 5
        pw = max(6, (rx * 2 - 22) // (n_ports * 2))
        for pi in range(n_ports):
            px = cx - rx + 12 + pi * ((rx * 2 - 24) // n_ports)
            stage.draw.rectangle((px, cy_live + 11, px + pw + 3, cy_live + sh), fill=dark_core, outline=wire_col, width=1)
            stage.draw.ellipse((px + 1, cy_live + 6, px + 5, cy_live + 10), fill=em_led if (pi + int(progress * 8)) % 3 else am_led)
    elif shp == "hub":
        hr, hry = int(rx * 0.92), int(ry * 1.05)
        oct_t = [(cx + int(hr * math.cos(math.radians(a + 22.5))), cy_live + int(hry * math.sin(math.radians(a + 22.5)))) for a in range(0, 360, 45)]
        d_h = max(14, depth // 2)
        stage.draw.polygon([(p[0], p[1] + d_h) for p in oct_t], fill=right_col, outline=wire_col, width=2)
        stage.draw.polygon(oct_t, fill=top_col, outline=wire_col, width=3)
        stage.draw.ellipse((cx - 8, cy_live - 6, cx + 8, cy_live + 6), fill=em_led)
        for p in oct_t[::2]:
            stage.draw.line((cx, cy_live, p[0], p[1]), fill=wire_col, width=2)
    elif shp in ("server_rack", "rack_cabinet"):
        bw, top_y, bot_y = int(rx * 0.85), cy_live - ry // 2, cy_live + depth + 12
        stage.draw.rounded_rectangle((cx - bw, top_y, cx + bw, bot_y), radius=8, fill=dark_core, outline=wire_col, width=3)
        n_blades = 4
        bh = max(8, (bot_y - top_y - 14) // n_blades)
        for bi in range(n_blades):
            y0 = top_y + 6 + bi * bh
            stage.draw.rounded_rectangle((cx - bw + 6, y0, cx + bw - 6, y0 + bh - 3), radius=3, fill=left_col if bi % 2 == 0 else right_col, outline=wire_col, width=1)
            stage.draw.ellipse((cx + bw - 16, y0 + bh // 2 - 3, cx + bw - 10, y0 + bh // 2 + 3), fill=em_led if (bi + int(progress * 6)) % 2 == 0 else am_led)
    elif shp == "firewall_wall":
        bw, top_y, bot_y = int(rx * 0.92), cy_live - ry // 2, cy_live + depth + 6
        stage.draw.rounded_rectangle((cx - bw, top_y, cx + bw, bot_y), radius=6, fill=right_col, outline=wire_col, width=3)
        rows_b = 3
        rh_b = max(6, (bot_y - top_y) // rows_b)
        for r_i in range(rows_b):
            yy = top_y + r_i * rh_b
            stage.draw.line((cx - bw, yy, cx + bw, yy), fill=top_col, width=2)
            off = 0 if r_i % 2 == 0 else bw // 2
            stage.draw.line((cx - bw // 2 + off, yy, cx - bw // 2 + off, min(bot_y, yy + rh_b)), fill=top_col, width=2)
    elif shp == "ssd_nvme":
        bw, bh = int(rx * 0.88), int(depth * 0.72)
        stage.draw.rounded_rectangle((cx - bw, cy_live - bh // 2, cx + bw, cy_live + bh // 2 + 12), radius=7, fill=left_col, outline=wire_col, width=2)
        stage.draw.rounded_rectangle((cx - bw + 8, cy_live - bh // 2 + 6, cx + int(bw * 0.4), cy_live + bh // 2 + 4), radius=4, fill=dark_core)
        for gi in range(4):
            gy = cy_live - bh // 2 + 6 + gi * max(4, bh // 4)
            stage.draw.line((cx + int(bw * 0.65), gy, cx + bw - 2, gy), fill=am_led, width=3)
    elif shp == "cylinder":
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
        hr, hr_y = int(rx * 0.92), int(ry * 1.15)
        hex_top = [(cx + int(hr * math.cos(math.radians(a))), cy_live + int(hr_y * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
        ext = int(depth * 0.72)
        for idx in (0, 1, 2):
            p1, p2 = hex_top[idx], hex_top[(idx + 1) % 6]
            stage.draw.polygon([p1, p2, (p2[0], p2[1] + ext), (p1[0], p1[1] + ext)], fill=left_col if idx < 2 else right_col, outline=wire_col, width=2)
        stage.draw.polygon(hex_top, fill=top_col, outline=wire_col, width=3 if active else 2)
    elif shp == "pyramid":
        apex = (cx, cy_live - int(depth * 0.55))
        p_left, p_front, p_right = (cx - rx, cy_live + int(depth * 0.42)), (cx, cy_live + int(depth * 0.82)), (cx + rx, cy_live + int(depth * 0.42))
        stage.draw.polygon([apex, p_left, p_front], fill=top_col, outline=wire_col, width=2)
        stage.draw.polygon([apex, p_front, p_right], fill=right_col, outline=wire_col, width=2)
    elif shp == "funnel":
        bot_apex = (cx, cy_live + depth + 16)
        stage.draw.polygon([(cx - rx, cy_live - ry // 2), (cx, cy_live + ry // 2), bot_apex], fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon([(cx, cy_live + ry // 2), (cx + rx, cy_live - ry // 2), bot_apex], fill=right_col, outline=wire_col, width=2)
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
        top_v, bot_v, left_v, right_v = (cx, mid_cy - ry - depth // 3), (cx, mid_cy + ry + depth // 2), (cx - rx, mid_cy), (cx + rx, mid_cy)
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
    elif shp == "shield":
        sw, ty_s, by_s, my_s = int(rx * 0.85), cy_live - ry // 2 - 4, cy_live + depth + 16, cy_live + depth // 2
        stage.draw.polygon([(cx, ty_s), (cx - sw, ty_s + 14), (cx - int(sw * 0.78), my_s + 12), (cx, by_s)], fill=top_col, outline=wire_col, width=2)
        stage.draw.polygon([(cx, ty_s), (cx + sw, ty_s + 14), (cx + int(sw * 0.78), my_s + 12), (cx, by_s)], fill=right_col, outline=wire_col, width=2)
    elif shp == "chip":
        cw_c, mid_cy = int(rx * 0.78), cy_live + depth // 3
        for p_idx in range(-2, 3):
            py_p = mid_cy + p_idx * 11
            stage.draw.line((cx - cw_c - 12, py_p, cx - cw_c, py_p), fill=am_led, width=3)
            stage.draw.line((cx + cw_c, py_p, cx + cw_c + 12, py_p), fill=am_led, width=3)
        stage.draw.rounded_rectangle((cx - cw_c, mid_cy - cw_c, cx + cw_c, mid_cy + cw_c), radius=14, fill=dark_core, outline=wire_col, width=3)
        ic = int(cw_c * 0.54)
        stage.draw.rounded_rectangle((cx - ic, mid_cy - ic, cx + ic, mid_cy + ic), radius=8, fill=top_col, outline=wire_col, width=2)
    elif shp == "bucket":
        bw_b, rim_h, taper = int(rx * 0.85), max(18, ry), 14
        stage.draw.arc((cx - bw_b // 2, cy_live - 20, cx + bw_b // 2, cy_live + 14), start=180, end=360, fill=wire_col, width=3)
        stage.draw.polygon([(cx - bw_b, cy_live + rim_h // 2), (cx + bw_b, cy_live + rim_h // 2), (cx + bw_b - taper, cy_live + depth + 10), (cx - bw_b + taper, cy_live + depth + 10)], fill=left_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - bw_b, cy_live, cx + bw_b, cy_live + rim_h), fill=top_col, outline=wire_col, width=3)
    elif shp == "gear":
        mid_cy, gr = cy_live + depth // 3, int(min(rx, ry + depth // 2) * 0.88)
        for ti in range(8):
            ang = math.radians(ti * 45 + (progress * 35.0 if active else 0.0))
            tx, ty = cx + int(math.cos(ang) * (gr + 6)), mid_cy + int(math.sin(ang) * (gr + 6))
            stage.draw.ellipse((tx - 7, ty - 7, tx + 7, ty + 7), fill=top_col, outline=wire_col, width=2)
        stage.draw.ellipse((cx - gr, mid_cy - gr, cx + gr, mid_cy + gr), fill=left_col, outline=wire_col, width=3)
        stage.draw.ellipse((cx - gr // 2, mid_cy - gr // 2, cx + gr // 2, mid_cy + gr // 2), fill=dark_core, outline=wire_col, width=2)
    elif shp == "bot":
        bw_t, mid_cy = int(rx * 0.78), cy_live + depth // 3
        stage.draw.line((cx, mid_cy - bw_t, cx, mid_cy - bw_t - 14), fill=wire_col, width=3)
        stage.draw.ellipse((cx - 5, mid_cy - bw_t - 20, cx + 5, mid_cy - bw_t - 10), fill=am_led)
        stage.draw.rounded_rectangle((cx - bw_t, mid_cy - bw_t + 6, cx + bw_t, mid_cy + bw_t - 4), radius=18, fill=left_col, outline=wire_col, width=3)
        stage.draw.rounded_rectangle((cx - bw_t + 10, mid_cy - 14, cx + bw_t - 10, mid_cy + 12), radius=8, fill=dark_core, outline=wire_col, width=2)
        scan_x = cx - 12 + int(math.sin(progress * 6.0) * 14)
        stage.draw.rounded_rectangle((scan_x, mid_cy - 8, scan_x + 18, mid_cy + 6), radius=4, fill=top_col)
    else:
        t_pts = [(cx, cy_live - ry), (cx + rx, cy_live), (cx, cy_live + ry), (cx - rx, cy_live)]
        l_pts = [(cx - rx, cy_live), (cx, cy_live + ry), (cx, cy_live + ry + depth), (cx - rx, cy_live + depth)]
        r_pts = [(cx + rx, cy_live), (cx, cy_live + ry), (cx, cy_live + ry + depth), (cx + rx, cy_live + depth)]
        stage.draw.polygon(l_pts, fill=left_col, outline=wire_col, width=2)
        stage.draw.polygon(r_pts, fill=right_col, outline=wire_col, width=2)
        stage.draw.polygon(t_pts, fill=top_col, outline=wire_col, width=3 if active else 2)
        irx, iry = int(rx * (0.45 if shp == "cube_cutout" else 0.62)), int(ry * (0.45 if shp == "cube_cutout" else 0.62))
        inner_top = [(cx, cy_live - iry), (cx + irx, cy_live), (cx, cy_live + iry), (cx - irx, cy_live)]
        stage.draw.polygon(inner_top, fill=dark_core if shp == "cube_cutout" else None, outline=_with_alpha(color, alpha_mul * 0.85), width=2)

    if pedestal_glyph:
        draw_vector_glyph(stage, cx, cy_live, pedestal_glyph, max(14, min(rx // 2, 22)), color, alpha_mul * 0.95, with_badge=True)
