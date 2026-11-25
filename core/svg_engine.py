import hashlib
import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from PIL import Image

from core.config import ASSETS_DIR

try:
    import resvg_py
    HAS_RESVG = True
except Exception:
    HAS_RESVG = False

ICONS_CACHE_DIR = ASSETS_DIR / "icons_cache"
ICONS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_SVG_RASTER_MEM_CACHE: Dict[str, Optional[Image.Image]] = {}
_SVG_LAYERS_MEM_CACHE: Dict[str, List[Image.Image]] = {}

# Curated instant alias map into Iconify prefixes (200,000+ open-source SVG icons!)
ICON_ALIASES: Dict[str, str] = {
    "python": "logos:python",
    "aws": "logos:aws",
    "gcp": "logos:google-cloud",
    "azure": "logos:microsoft-azure",
    "kubernetes": "logos:kubernetes",
    "k8s": "logos:kubernetes",
    "docker": "logos:docker-icon",
    "postgres": "logos:postgresql",
    "postgresql": "logos:postgresql",
    "redis": "logos:redis",
    "kafka": "logos:kafka-icon",
    "react": "logos:react",
    "fastapi": "logos:fastapi-icon",
    "nginx": "logos:nginx",
    "linux": "logos:linux-tux",
    "git": "logos:git-icon",
    "github": "simple-icons:github",
    "openai": "simple-icons:openai",
    "anthropic": "simple-icons:anthropic",
    "gemini": "simple-icons:googlegemini",
    "elasticsearch": "logos:elasticsearch",
    "mongodb": "logos:mongodb-icon",
    "graphql": "logos:graphql",
    "terraform": "logos:terraform-icon",
    "prometheus": "logos:prometheus",
    "grafana": "logos:grafana",
    "cloudflare": "logos:cloudflare-icon",
    "vercel": "simple-icons:vercel",
    "pytorch": "logos:pytorch-icon",
    "tensorflow": "logos:tensorflow",
    "rust": "simple-icons:rust",
    "go": "logos:go",
    "typescript": "logos:typescript-icon",
    "javascript": "logos:javascript",
    "sql": "lucide:database",
    "vector": "lucide:cpu",
    "rag": "lucide:brain-circuit",
    "llm": "lucide:sparkles",
    "ai": "lucide:bot",
    "shield": "lucide:shield-check",
    "security": "lucide:shield-alert",
    "firewall": "lucide:flame",
    "lock": "lucide:lock",
    "cloud": "lucide:cloud",
    "server": "lucide:server",
    "rocket": "lucide:rocket",
    "speed": "lucide:zap",
    "latency": "lucide:timer",
    "search": "lucide:search",
    "chart": "lucide:bar-chart-3",
    "network": "lucide:network",
    "code": "lucide:code-2",
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

    # Search Iconify's 200,000+ icon catalog dynamically
    search_cache = ICONS_CACHE_DIR / f"search_{_safe_cache_name(q)}.txt"
    if search_cache.exists():
        cached = search_cache.read_text(encoding="utf-8").strip()
        if cached:
            return cached
    try:
        r = requests.get(
            "https://api.iconify.design/search",
            params={"query": q, "limit": 3},
            timeout=3,
        )
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
    """
    Fetches any of 200,000+ open-source vector icons via Iconify API (disk + memory cached)
    and rasterizes cleanly at high DPI using Rust resvg_py.
    """
    if not HAS_RESVG or not icon_name_or_query:
        return None
    icon_id = _resolve_iconify_id(icon_name_or_query)
    if ":" not in icon_id:
        return None

    prefix, name = icon_id.split(":", 1)
    is_monochrome = not prefix.startswith("logos")
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


def prepare_generative_svg_layers(svg_code: str, width: int = 940, height: int = 980) -> List[Image.Image]:
    """
    Parses an AI-generated <svg> vector composition, splits stage layers
    (<g id='stage_1'>..<g id='stage_4'>, or automatic sequential grouping),
    and pre-renders crisp RGBA layers ONCE via Rust resvg_py for smooth Spring/Bloom animation.
    """
    if not HAS_RESVG or not svg_code:
        return []
    key = hashlib.sha256(f"{width}x{height}|{svg_code}".encode("utf-8")).hexdigest()[:24]
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

    # Group elements into progressive reveal stages
    stage_buckets: List[List[ET.Element]] = [[], [], [], []]
    has_explicit_stages = any("stage" in str(el.attrib.get("id", "")).lower() for el in draw_elems)
    if has_explicit_stages:
        for el in draw_elems:
            eid = str(el.attrib.get("id", "")).lower()
            m_num = re.search(r"(\d)", eid)
            idx = max(0, min(3, int(m_num.group(1)) - 1)) if m_num else 0
            stage_buckets[idx].append(el)
        groups = [b for b in stage_buckets if b]
    else:
        n_el = len(draw_elems)
        if n_el <= 4:
            groups = [[el] for el in draw_elems]
        else:
            chunk = max(1, (n_el + 3) // 4)
            groups = [draw_elems[i:i + chunk] for i in range(0, n_el, chunk)][:4]

    rendered_layers: List[Image.Image] = []
    for grp in groups:
        new_root = ET.Element("svg", dict(root.attrib))
        for d in defs_elems:
            new_root.append(d)
        for el in grp:
            new_root.append(el)
        svg_str = ET.tostring(new_root, encoding="unicode")
        try:
            png_bytes = resvg_py.svg_to_bytes(svg_str, width=width, height=height)
            im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            rendered_layers.append(im)
        except Exception:
            continue

    _SVG_LAYERS_MEM_CACHE[key] = rendered_layers
    return rendered_layers
