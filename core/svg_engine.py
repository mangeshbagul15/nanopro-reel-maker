import hashlib
import io
import math
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from PIL import Image, ImageChops

from core.config import ASSETS_DIR

try:
    import resvg_py
    HAS_RESVG = True
except Exception:
    HAS_RESVG = False

ICONS_CACHE_DIR = ASSETS_DIR / "icons_cache"
ICONS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_SVG_RASTER_MEM_CACHE: Dict[str, Optional[Image.Image]] = {}
_SVG_3D_EXTRUDE_MEM_CACHE: Dict[str, Optional[Image.Image]] = {}
_SVG_LAYERS_MEM_CACHE: Dict[str, List[Dict[str, Any]]] = {}

# 100+ Curated instant aliases across Iconify (200,000+ SVGs: logos, lucide, mdi, tabler, fluent-emoji-flat)
ICON_ALIASES: Dict[str, str] = {
    "python": "logos:python", "aws": "logos:aws", "gcp": "logos:google-cloud", "azure": "logos:microsoft-azure",
    "kubernetes": "logos:kubernetes", "k8s": "logos:kubernetes", "docker": "logos:docker-icon",
    "postgres": "logos:postgresql", "postgresql": "logos:postgresql", "redis": "logos:redis",
    "kafka": "logos:kafka-icon", "react": "logos:react", "nextjs": "logos:nextjs-icon",
    "fastapi": "logos:fastapi-icon", "nginx": "logos:nginx", "linux": "logos:linux-tux",
    "git": "logos:git-icon", "github": "simple-icons:github", "gitlab": "logos:gitlab-icon",
    "openai": "simple-icons:openai", "anthropic": "simple-icons:anthropic", "gemini": "simple-icons:googlegemini",
    "huggingface": "logos:hugging-face-icon", "elasticsearch": "logos:elasticsearch", "mongodb": "logos:mongodb-icon",
    "graphql": "logos:graphql", "terraform": "logos:terraform-icon", "prometheus": "logos:prometheus",
    "grafana": "logos:grafana", "cloudflare": "logos:cloudflare-icon", "vercel": "simple-icons:vercel",
    "pytorch": "logos:pytorch-icon", "tensorflow": "logos:tensorflow", "rust": "simple-icons:rust",
    "go": "logos:go", "typescript": "logos:typescript-icon", "javascript": "logos:javascript",
    "java": "logos:java", "cpp": "logos:c-plusplus", "csharp": "logos:c-sharp", "swift": "logos:swift",
    "kotlin": "logos:kotlin-icon", "android": "logos:android-icon", "apple": "simple-icons:apple",
    "stripe": "logos:stripe", "supabase": "logos:supabase-icon", "firebase": "logos:firebase-icon",
    "snowflake": "logos:snowflake-icon", "spark": "logos:apache-spark", "airflow": "logos:airflow-icon",
    "dbt": "logos:dbt-icon", "databricks": "simple-icons:databricks", "pinecone": "lucide:sparkles",
    "ray": "lucide:zap", "vllm": "lucide:cpu", "ollama": "lucide:bot", "langchain": "lucide:link",
    "sql": "lucide:database", "vector": "lucide:cpu", "rag": "lucide:brain-circuit", "llm": "lucide:sparkles",
    "ai": "lucide:bot", "brain": "lucide:brain", "neural": "lucide:network", "shield": "lucide:shield-check",
    "security": "lucide:shield-alert", "firewall": "lucide:flame", "lock": "lucide:lock", "cloud": "lucide:cloud",
    "server": "lucide:server", "rocket": "lucide:rocket", "speed": "lucide:zap", "latency": "lucide:timer",
    "search": "lucide:search", "chart": "lucide:bar-chart-3", "network": "lucide:network", "code": "lucide:code-2",
    "dna": "lucide:dna", "atom": "lucide:atom", "microscope": "lucide:microscope", "flask": "lucide:flask-conical",
    "money": "lucide:badge-dollar-sign", "wallet": "lucide:wallet", "bank": "lucide:landmark",
    "emoji_rocket": "fluent-emoji-flat:rocket", "emoji_brain": "fluent-emoji-flat:brain",
    "emoji_fire": "fluent-emoji-flat:fire", "emoji_bolt": "fluent-emoji-flat:high-voltage",
    "emoji_robot": "fluent-emoji-flat:robot", "emoji_gem": "fluent-emoji-flat:gem-stone",
    "emoji_trophy": "fluent-emoji-flat:trophy", "emoji_chart": "fluent-emoji-flat:chart-increasing",
    "emoji_lock": "fluent-emoji-flat:locked", "emoji_sparkles": "fluent-emoji-flat:sparkles",
}


def _safe_cache_name(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", key)[:90]


def _resolve_iconify_id(query_or_id: str) -> str:
    q = str(query_or_id or "").strip().lower()
    if not q:
        return ""
    if q in ICON_ALIASES:
        return ICON_ALIASES[q]
    if ":" in q:
        return q
    if "/" in q:
        return q.replace("/", ":", 1)

    search_cache = ICONS_CACHE_DIR / f"search_{_safe_cache_name(q)}.txt"
    if search_cache.exists():
        cached = search_cache.read_text(encoding="utf-8").strip()
        if cached:
            return cached
    try:
        r = requests.get("https://api.iconify.design/search", params={"query": q, "limit": 3}, timeout=3)
        if r.status_code == 200:
            icons = r.json().get("icons", [])
            if icons:
                best = str(icons[0])
                search_cache.write_text(best, encoding="utf-8")
                return best
    except Exception:
        pass
    return f"lucide:{re.sub(r'[^a-z0-9-]+', '-', q).strip('-')}"


def fetch_iconify_svg(icon_name_or_query: str, size_px: int = 96, tint_hex: str = "#38BDF8") -> Optional[Image.Image]:
    """Fetches any of 200,000+ open-source vector icons via Iconify API & rasterizes via Rust resvg_py."""
    if not HAS_RESVG or not icon_name_or_query:
        return None
    icon_id = _resolve_iconify_id(icon_name_or_query)
    if ":" not in icon_id:
        return None

    prefix, name = icon_id.split(":", 1)
    is_monochrome = not prefix.startswith(("logos", "fluent-emoji", "twemoji", "noto", "circle-flags"))
    mem_key = f"{icon_id}|{size_px}|{tint_hex if is_monochrome else 'orig'}"
    if mem_key in _SVG_RASTER_MEM_CACHE:
        return _SVG_RASTER_MEM_CACHE[mem_key]

    svg_file = ICONS_CACHE_DIR / f"{_safe_cache_name(prefix)}_{_safe_cache_name(name)}.svg"
    svg_text = ""
    if svg_file.exists():
        try:
            svg_text = svg_file.read_text(encoding="utf-8")
        except Exception:
            svg_text = ""

    if not svg_text:
        url = f"https://api.iconify.design/{prefix}/{name}.svg"
        try:
            res = requests.get(url, timeout=4)
            if res.status_code == 200 and "<svg" in res.text:
                svg_text = res.text
                try:
                    svg_file.write_text(svg_text, encoding="utf-8")
                except Exception:
                    pass
        except Exception:
            svg_text = ""

    if not svg_text or "<svg" not in svg_text:
        _SVG_RASTER_MEM_CACHE[mem_key] = None
        return None

    try:
        render_svg = svg_text
        if is_monochrome and tint_hex:
            render_svg = render_svg.replace("currentColor", tint_hex)
            if "fill=" not in render_svg and "stroke=" not in render_svg:
                render_svg = render_svg.replace("<svg ", f'<svg stroke="{tint_hex}" ', 1)
        png_bytes = resvg_py.svg_to_bytes(render_svg, width=size_px, height=size_px)
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        _SVG_RASTER_MEM_CACHE[mem_key] = img
        return img
    except Exception:
        _SVG_RASTER_MEM_CACHE[mem_key] = None
        return None


def extrude_image_to_3d(
    img: Image.Image,
    depth: int = 12,
    tint_rgb: Optional[Tuple[int, int, int]] = None,
) -> Image.Image:
    """
    Converts ANY rasterized 200,000+ Iconify SVG or shape sprite into a genuine
    isometric 3D-extruded relief model using darkened stacked Z-slices + specular top rim.
    """
    if img is None:
        return Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    rgba = img.convert("RGBA")
    arr = np.array(rgba, dtype=np.float32)
    h, w = arr.shape[:2]
    dx_total = int(math.ceil(depth * 0.75)) + 6
    dy_total = int(math.ceil(depth * 1.15)) + 6
    cw, ch = w + dx_total, h + dy_total
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    # Build extrusion sidewall slices back-to-front
    alpha_mask = arr[:, :, 3]
    for step in range(depth, 0, -1):
        frac = step / max(1, depth)
        shade = 0.24 + 0.36 * (1.0 - frac)
        slice_arr = np.zeros_like(arr, dtype=np.uint8)
        if tint_rgb is not None:
            slice_arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.55 + tint_rgb[0] * 0.45 * shade, 0, 255).astype(np.uint8)
            slice_arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.55 + tint_rgb[1] * 0.45 * shade, 0, 255).astype(np.uint8)
            slice_arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.55 + tint_rgb[2] * 0.45 * shade, 0, 255).astype(np.uint8)
        else:
            slice_arr[:, :, :3] = np.clip(arr[:, :, :3] * shade, 0, 255).astype(np.uint8)
        slice_arr[:, :, 3] = np.clip(alpha_mask * 0.92, 0, 255).astype(np.uint8)
        sl_img = Image.fromarray(slice_arr, mode="RGBA")
        ox = int(round(step * 0.55))
        oy = int(round(step * 1.05))
        out.alpha_composite(sl_img, (ox, oy))

    # Front bright crisp SVG face
    out.alpha_composite(rgba, (0, 0))
    return out


def fetch_3d_extruded_svg(
    icon_name_or_query: str,
    size_px: int = 96,
    tint_hex: str = "#38BDF8",
    depth: int = 12,
    tint_rgb: Optional[Tuple[int, int, int]] = None,
) -> Optional[Image.Image]:
    """Cached 200,000+ Iconify SVG -> Genuine 3D Extruded Isometric Object pipeline."""
    key = f"{icon_name_or_query}|{size_px}|{tint_hex}|{depth}"
    if key in _SVG_3D_EXTRUDE_MEM_CACHE:
        return _SVG_3D_EXTRUDE_MEM_CACHE[key]
    flat = fetch_iconify_svg(icon_name_or_query, size_px=size_px, tint_hex=tint_hex)
    if flat is None:
        _SVG_3D_EXTRUDE_MEM_CACHE[key] = None
        return None
    ext = extrude_image_to_3d(flat, depth=depth, tint_rgb=tint_rgb)
    _SVG_3D_EXTRUDE_MEM_CACHE[key] = ext
    return ext


def _sanitize_svg_root(svg_code: str, width: int, height: int) -> Optional[ET.Element]:
    raw = str(svg_code or "").strip()
    m = re.search(r"<svg[\s\S]*</svg>", raw, re.IGNORECASE)
    if not m:
        return None
    clean = m.group(0)
    clean = re.sub(r"<script[\s\S]*?</script>", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<foreignObject[\s\S]*?</foreignObject>", "", clean, flags=re.IGNORECASE)
    try:
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        root = ET.fromstring(clean)
    except Exception:
        return None
    if "viewBox" not in root.attrib and "viewbox" not in root.attrib:
        w_orig = re.sub(r"[^0-9.]", "", str(root.attrib.get("width", str(width)))) or str(width)
        h_orig = re.sub(r"[^0-9.]", "", str(root.attrib.get("height", str(height)))) or str(height)
        root.attrib["viewBox"] = f"0 0 {w_orig} {h_orig}"
    root.attrib["width"] = str(width)
    root.attrib["height"] = str(height)
    if not root.tag.startswith("{"):
        root.attrib.setdefault("xmlns", "http://www.w3.org/2000/svg")
    return root


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1].lower() if "}" in tag else tag.lower()


def prepare_generative_svg_layers(svg_code: str, width: int = 880, height: int = 840) -> List[Image.Image]:
    """Pre-renders progressive stage groups (<g id='stage_1'>..'<g id='stage_6'>) via Rust resvg_py."""
    items = prepare_keyframed_svg_layers(svg_code, width=width, height=height)
    return [it["image"] for it in items]


def prepare_keyframed_svg_layers(svg_code: str, width: int = 880, height: int = 840) -> List[Dict[str, Any]]:
    """
    Parses an AI-generated <svg> vector scene into layer objects carrying id + RGBA bitmap
    so Keyframe Animator can drive scale, rotation, slide, float wave & pulse smoothly per stage.
    """
    if not HAS_RESVG or not svg_code:
        return []
    key = hashlib.sha256(f"kf|{width}x{height}|{svg_code}".encode("utf-8")).hexdigest()[:24]
    if key in _SVG_LAYERS_MEM_CACHE:
        return _SVG_LAYERS_MEM_CACHE[key]

    root = _sanitize_svg_root(svg_code, width, height)
    if root is None:
        return []

    defs_elems: List[ET.Element] = []
    draw_elems: List[ET.Element] = []
    for child in list(root):
        tname = _strip_ns(child.tag)
        if tname in ("defs", "style", "lineargradient", "radialgradient"):
            defs_elems.append(child)
        elif tname in ("title", "desc", "metadata"):
            continue
        else:
            draw_elems.append(child)

    if not draw_elems:
        return []

    has_explicit_stages = any("stage" in str(el.attrib.get("id", "")).lower() for el in draw_elems)
    groups: List[Tuple[str, List[ET.Element]]] = []
    if has_explicit_stages:
        buckets: Dict[int, List[ET.Element]] = {}
        for el in draw_elems:
            eid = str(el.attrib.get("id", "")).lower()
            m_num = re.search(r"(\d+)", eid)
            idx = max(1, min(6, int(m_num.group(1)))) if m_num else 1
            buckets.setdefault(idx, []).append(el)
        for k_idx in sorted(buckets.keys()):
            groups.append((f"stage_{k_idx}", buckets[k_idx]))
    else:
        n_el = len(draw_elems)
        chunk = 1 if n_el <= 6 else max(1, (n_el + 5) // 6)
        for i in range(0, n_el, chunk):
            chunk_els = draw_elems[i:i + chunk]
            eid = str(chunk_els[0].attrib.get("id") or f"stage_{len(groups)+1}")
            groups.append((eid, chunk_els))

    out_layers: List[Dict[str, Any]] = []
    for gid, grp in groups[:6]:
        new_root = ET.Element("svg", dict(root.attrib))
        for d in defs_elems:
            new_root.append(d)
        for el in grp:
            new_root.append(el)
        svg_str = ET.tostring(new_root, encoding="unicode")
        try:
            png_bytes = resvg_py.svg_to_bytes(svg_str, width=width, height=height)
            im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            out_layers.append({"id": gid, "image": im})
        except Exception:
            continue

    _SVG_LAYERS_MEM_CACHE[key] = out_layers
    return out_layers
