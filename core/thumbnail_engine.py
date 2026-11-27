"""
High-Tech Dark 9:16 Thumbnail Engine (16 Distinct Layouts x 12 Dark Palettes x 8 Geometric Backdrops).

Produces ultra-crisp, strictly dark-background YouTube Shorts / Instagram Reels cover posters
with zero bright glow washes, zero missing-glyph Unicode boxes, and genuine variety on every click.
"""

from __future__ import annotations

import copy
import json
import math
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from core.config import DEFAULT_WATERMARK, GEMINI_API_KEY, GROQ_API_KEY, OUTPUT_DIR
from core.tone_engine import resolve_effective_tone

_THUMB_DARK_THEMES: List[Dict[str, Any]] = [
    {"name": "midnight_cyan", "bg": (8, 13, 27), "grid": (30, 48, 82), "pri": (56, 189, 248), "btn": (37, 99, 235), "soft": (125, 211, 252), "hex": "#38BDF8"},
    {"name": "obsidian_emerald", "bg": (6, 17, 14), "grid": (20, 62, 48), "pri": (52, 211, 153), "btn": (5, 150, 105), "soft": (110, 231, 183), "hex": "#34D399"},
    {"name": "crimson_outage", "bg": (17, 9, 14), "grid": (68, 26, 38), "pri": (244, 63, 94), "btn": (225, 29, 72), "soft": (253, 164, 175), "hex": "#F43F5E"},
    {"name": "carbon_amber", "bg": (11, 13, 21), "grid": (56, 46, 22), "pri": (251, 191, 36), "btn": (217, 119, 6), "soft": (253, 224, 71), "hex": "#FBBF24"},
    {"name": "velvet_purple", "bg": (11, 8, 22), "grid": (49, 32, 82), "pri": (168, 85, 247), "btn": (126, 34, 206), "soft": (216, 180, 254), "hex": "#A855F7"},
    {"name": "cobalt_indigo", "bg": (6, 12, 26), "grid": (28, 44, 88), "pri": (96, 165, 250), "btn": (37, 99, 235), "soft": (147, 197, 253), "hex": "#60A5FA"},
    {"name": "neon_teal", "bg": (5, 16, 20), "grid": (18, 60, 68), "pri": (45, 212, 191), "btn": (13, 148, 136), "soft": (153, 246, 228), "hex": "#2DD4BF"},
    {"name": "cyber_magenta", "bg": (18, 8, 20), "grid": (66, 24, 64), "pri": (236, 72, 153), "btn": (219, 39, 119), "soft": (249, 168, 212), "hex": "#EC4899"},
    {"name": "solar_orange", "bg": (17, 11, 8), "grid": (64, 38, 20), "pri": (251, 146, 60), "btn": (234, 88, 12), "soft": (253, 186, 116), "hex": "#FB923C"},
    {"name": "acid_lime", "bg": (9, 16, 10), "grid": (34, 58, 24), "pri": (163, 230, 53), "btn": (101, 163, 13), "soft": (217, 249, 157), "hex": "#A3E635"},
    {"name": "titanium_ice", "bg": (9, 13, 20), "grid": (38, 50, 72), "pri": (226, 232, 240), "btn": (37, 99, 235), "soft": (148, 163, 184), "hex": "#E2E8F0"},
    {"name": "electric_violet", "bg": (10, 9, 24), "grid": (40, 38, 92), "pri": (129, 140, 248), "btn": (79, 70, 229), "soft": (199, 210, 254), "hex": "#818CF8"},
]

_THUMB_BG_STYLES: Tuple[str, ...] = (
    "square_grid",
    "dot_matrix",
    "diagonal_blueprint",
    "isometric_mesh",
    "concentric_radar",
    "hex_honeycomb",
    "circuit_traces",
    "perspective_horizon",
)

_THUMB_ANGLES: List[Tuple[str, str, str, Callable[[str], str]]] = [
    ("bento_telemetry", "2026 TELEMETRY", "terminal_dots", lambda s: f"{s}: Live Telemetry & Scale"),
    ("datacenter_rack", "DATA CENTER CORE", "hud_brackets", lambda s: f"Inside {s} Server Architecture"),
    ("live_code", "UNDER THE HOOD", "terminal_dots", lambda s: f"{s} Live Execution & Fix"),
    ("pipeline_dag", "PIPELINE TOPOLOGY", "frameless_3d", lambda s: f"End-to-End {s} Data Flow"),
    ("myth_vs_fix", "STOP THIS MISTAKE", "hud_brackets", lambda s: f"{s}: Wrong vs Production Way"),
    ("latency_gauge", "LATENCY KILLER", "frameless_3d", lambda s: f"Make {s} 10x Faster Now"),
    ("blueprint", "WHITEBOARD BLUEPRINT", "blueprint_rulers", lambda s: f"Draw {s} in 60 Seconds"),
    ("sequence_trace", "REQUEST TRACE", "blueprint_rulers", lambda s: f"Step-by-Step {s} Packet Trace"),
    ("git_diff_patch", "PRODUCTION PR DIFF", "terminal_dots", lambda s: f"The 3-Line Fix for {s}"),
    ("warroom_radar", "3AM OUTAGE RADAR", "hud_brackets", lambda s: f"Why {s} Crashes Under Load"),
    ("agent_mesh", "INTELLIGENT MESH", "frameless_3d", lambda s: f"Autonomous {s} System Design"),
    ("benchmark_bars", "SPEED BENCHMARK", "bento_tiles", lambda s: f"{s} Performance Benchmarks"),
    ("iso_layers", "LAYERED INTERNALS", "hud_brackets", lambda s: f"Inside {s}: 3 Core Layers"),
    ("interview_hub", "SYSTEM INTERVIEW", "terminal_dots", lambda s: f"Cracking {s} Live"),
    ("card_carousel_stack", "3-STEP PLAYBOOK", "bento_tiles", lambda s: f"Master {s} in 3 Steps"),
    ("architecture", "PRO ARCHITECTURE", "terminal_dots", lambda s: f"How {s} Actually Scales"),
]


def _draw_vector_glyph(
    draw: ImageDraw.ImageDraw,
    kind: str,
    cx: int,
    cy: int,
    size: int,
    color: Tuple[int, ...],
    width: int = 3,
) -> None:
    """Draws crisp geometric icons directly so zero Unicode glyphs render as missing boxes."""
    r = max(4, size // 2)
    if kind == "check":
        draw.line([(cx - r, cy), (cx - r // 4, cy + r // 2 + 2), (cx + r, cy - r + 2)], fill=color, width=width)
    elif kind == "cross":
        draw.line([(cx - r + 2, cy - r + 2), (cx + r - 2, cy + r - 2)], fill=color, width=width)
        draw.line([(cx - r + 2, cy + r - 2), (cx + r - 2, cy - r + 2)], fill=color, width=width)
    elif kind == "play":
        draw.polygon([(cx - r // 2, cy - r + 2), (cx - r // 2, cy + r - 2), (cx + r, cy)], fill=color)
    elif kind == "bolt":
        draw.polygon([
            (cx + 2, cy - r),
            (cx - r + 2, cy + 2),
            (cx, cy + 2),
            (cx - 2, cy + r),
            (cx + r - 2, cy - 2),
            (cx, cy - 2),
        ], fill=color)
    elif kind == "arrow_r":
        draw.line([(cx - r, cy), (cx + r - 2, cy)], fill=color, width=width)
        draw.line([(cx + 2, cy - r // 2), (cx + r, cy), (cx + 2, cy + r // 2)], fill=color, width=width)
    elif kind == "pin":
        draw.ellipse((cx - r // 2, cy - r, cx + r // 2, cy), fill=color)
        draw.line([(cx, cy), (cx, cy + r)], fill=color, width=max(2, width - 1))
    elif kind == "shield":
        draw.polygon([
            (cx, cy - r),
            (cx + r, cy - r // 2),
            (cx + r - 2, cy + r // 3),
            (cx, cy + r),
            (cx - r + 2, cy + r // 3),
            (cx - r, cy - r // 2),
        ], outline=color, width=width)


def _draw_dark_thumb_backdrop(bg: Image.Image, theme: Dict[str, Any], bg_style: str) -> None:
    """Draws subtle dark-only engineering patterns with zero bright gradient wash."""
    w, h = bg.size
    dr = ImageDraw.Draw(bg, "RGBA")
    gr = theme["grid"]

    if bg_style == "dot_matrix":
        for gy in range(32, h, 44):
            for gx in range(32, w, 44):
                dr.ellipse((gx - 2, gy - 2, gx + 2, gy + 2), fill=(*gr, 115))
    elif bg_style == "diagonal_blueprint":
        for offset in range(-h, w + h, 88):
            dr.line((offset, 0, offset + h, h), fill=(*gr, 70), width=1)
        for gy in range(0, h, 132):
            dr.line((0, gy, w, gy), fill=(*gr, 52), width=1)
    elif bg_style == "isometric_mesh":
        for offset in range(-h, w + h, 108):
            dr.line((offset, 0, offset + int(h * 0.65), h), fill=(*gr, 64), width=1)
            dr.line((offset, 0, offset - int(h * 0.65), h), fill=(*gr, 64), width=1)
    elif bg_style == "concentric_radar":
        cx, cy = w // 2, 980
        for r in range(140, 980, 130):
            dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*gr, 74), width=2)
        dr.line((0, cy, w, cy), fill=(*gr, 48), width=1)
        dr.line((cx, 0, cx, h), fill=(*gr, 48), width=1)
    elif bg_style == "hex_honeycomb":
        r = 56
        dx = int(r * 1.5)
        dy = int(r * 1.732)
        for row in range(-1, h // dy + 2):
            for col in range(-1, w // dx + 2):
                cx = col * dx
                cy = row * dy + (dy // 2 if col % 2 else 0)
                pts = [(cx + r * math.cos(math.radians(60 * k)), cy + r * math.sin(math.radians(60 * k))) for k in range(6)]
                dr.polygon(pts, outline=(*gr, 62))
    elif bg_style == "circuit_traces":
        for row_y in range(80, h, 140):
            dr.line((0, row_y, 260, row_y), fill=(*gr, 65), width=2)
            dr.line((260, row_y, 320, row_y + 44), fill=(*gr, 65), width=2)
            dr.line((320, row_y + 44, 760, row_y + 44), fill=(*gr, 65), width=2)
            dr.line((760, row_y + 44, 820, row_y), fill=(*gr, 65), width=2)
            dr.line((820, row_y, w, row_y), fill=(*gr, 65), width=2)
            dr.ellipse((255, row_y - 4, 265, row_y + 4), fill=(*gr, 120))
            dr.ellipse((755, row_y + 40, 765, row_y + 48), fill=(*gr, 120))
    elif bg_style == "perspective_horizon":
        hy = 1040
        for vx in range(-600, w + 601, 150):
            dr.line((w // 2, 420, vx, h), fill=(*gr, 62), width=1)
        for k in range(1, 14):
            y_row = hy + int((k ** 1.65) * 14)
            if y_row < h:
                dr.line((0, y_row, w, y_row), fill=(*gr, 66), width=1)
    else:  # square_grid
        for gy in range(0, h, 64):
            dr.line((0, gy, w, gy), fill=(*gr, 72), width=1)
        for gx in range(0, w, 64):
            dr.line((gx, 0, gx, h), fill=(*gr, 72), width=1)


def _draw_thumb_stage_chrome(
    stage: Any,
    chrome_style: str,
    win_label: str,
    c_pri: Tuple[int, int, int],
    c_muted: Tuple[int, int, int],
    box: Tuple[int, int, int, int] = (56, 542, 1024, 1492),
    font_fn: Optional[Callable[..., Any]] = None,
) -> None:
    """Draws one of 5 distinct high-tech showcase container chromes around the centerpiece area."""
    bx0, by0, bx1, by1 = box
    lbl_font = font_fn(19, bold=True, mono=True)
    if chrome_style == "bento_tiles":
        # Lightweight corner markers only so modular bento cards float cleanly on the dark backdrop
        dr = stage.draw
        for px, py, sx, sy in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
            dr.line([(px, py + sy * 28), (px, py), (px + sx * 28, py)], fill=(*c_pri, 180), width=3)
        dr.text((bx0 + 36, by0 + 8), f"SYS.BENTO // {win_label}", fill=c_pri, font=lbl_font)
        return
    if chrome_style == "frameless_3d":
        stage.draw.line((bx0 + 20, by0 + 20, bx1 - 20, by0 + 20), fill=(*c_pri, 95), width=2)
        stage.draw.line((bx0 + 20, by1 - 12, bx1 - 20, by1 - 12), fill=(*c_pri, 95), width=2)
        stage.draw.rounded_rectangle((bx0 + 36, by0 + 4, bx0 + 380, by0 + 38), radius=14, fill=(14, 20, 34, 240), outline=(*c_pri, 150), width=2)
        stage.draw.text((bx0 + 56, by0 + 10), f"HUD // {win_label}", fill=c_pri, font=lbl_font)
        return

    stage.draw_glass_card(box, radius=34, accent_col=None, active=False, elev=14, layered=False)
    stage.draw.rounded_rectangle(box, radius=34, outline=(*c_pri, 115), width=2)
    if chrome_style == "hud_brackets":
        for px, py, sx, sy in ((bx0 + 10, by0 + 10, 1, 1), (bx1 - 10, by0 + 10, -1, 1), (bx0 + 10, by1 - 10, 1, -1), (bx1 - 10, by1 - 10, -1, -1)):
            stage.draw.line([(px, py + sy * 36), (px, py), (px + sx * 36, py)], fill=(*c_pri, 235), width=4)
        stage.draw.ellipse((bx0 + 36, by0 + 22, bx0 + 48, by0 + 34), fill=c_pri)
        stage.draw.text((bx0 + 60, by0 + 17), f"TELEMETRY // {win_label}", fill=c_pri, font=lbl_font)
        stage.draw.line((bx0 + 24, by0 + 54, bx1 - 24, by0 + 54), fill=(*c_pri, 75), width=2)
    elif chrome_style == "blueprint_rulers":
        for tx in range(bx0 + 48, bx1 - 36, 40):
            tick_h = 10 if (tx - bx0) % 120 == 48 else 5
            stage.draw.line((tx, by0 + 48 - tick_h, tx, by0 + 48), fill=(*c_pri, 125), width=2)
        stage.draw.text((bx0 + 36, by0 + 16), f"ARCH SPEC :: {win_label}", fill=c_pri, font=lbl_font)
        stage.draw.line((bx0 + 24, by0 + 54, bx1 - 24, by0 + 54), fill=(*c_pri, 100), width=2)
    else:  # terminal_dots
        for di in range(3):
            dx = bx0 + 34 + di * 22
            stage.draw.ellipse((dx, by0 + 22, dx + 12, by0 + 34), fill=c_pri if di == 0 else (71, 85, 105, 190))
        stage.draw.text((bx0 + 114, by0 + 17), f"// {win_label}", fill=c_muted, font=lbl_font)
        stage.draw.line((bx0 + 24, by0 + 54, bx1 - 24, by0 + 54), fill=(51, 65, 85, 160), width=2)


def _infer_thumb_category_and_icons(topic: str, timeline: Any = None) -> Tuple[str, List[str]]:
    """Infers a crisp cover category badge and matching Iconify icon keys from topic/timeline."""
    tl = topic.lower()
    cat_map = [
        (("python", "gil", "thread", "async", "asyncio", "rust", "java", "go", "js", "typescript"), "CODE INTERNALS"),
        (("sql", "postgres", "mysql", "database", "db", "index", "wal", "cdc", "dms", "mongo", "sharding", "snowflake"), "DATABASE ARCHITECTURE"),
        (("redis", "cache", "kafka", "queue", "mq", "stream", "event", "microservice"), "DISTRIBUTED SYSTEMS"),
        (("aws", "cloud", "k8s", "kubernetes", "docker", "terraform", "ci/cd", "devops", "s3"), "CLOUD & DEVOPS"),
        (("rag", "llm", "ai", "agent", "vector", "transformer", "fine-tun", "ml"), "AI ENGINEERING"),
        (("oauth", "jwt", "tls", "ssl", "security", "soc", "auth", "firewall", "zero trust"), "SECURITY & AUTH"),
        (("http", "tcp", "dns", "cdn", "vpc", "network", "load balancer", "nginx"), "NETWORKING"),
    ]
    cat = ""
    if isinstance(timeline, dict) and timeline.get("topic_category"):
        cat = str(timeline["topic_category"]).replace("_", " ").upper()
    if not cat or cat in ("GENERAL", "TECH"):
        for kws, label in cat_map:
            if any(k in tl for k in kws):
                cat = label
                break
    if not cat:
        cat = "SYSTEM DESIGN"

    from core.svg_engine import ICON_ALIASES
    matched_icons: List[str] = []
    for alias in sorted(ICON_ALIASES.keys(), key=len, reverse=True):
        clean_a = alias.replace("_", " ")
        if re.search(rf"\b{re.escape(clean_a)}\b", tl) or re.search(rf"\b{re.escape(alias)}\b", tl):
            if alias not in matched_icons:
                matched_icons.append(alias)
            if len(matched_icons) >= 3:
                break
    for fb in ("cpu", "workflow", "rocket"):
        if len(matched_icons) >= 3:
            break
        if fb not in matched_icons:
            matched_icons.append(fb)
    return cat, matched_icons


def _fit_cover_headline(draw: ImageDraw.ImageDraw, text: str, max_w: int, font_fn: Callable[..., Any]) -> Tuple[Any, List[str], int]:
    """Selects the largest readable bold font (66 -> 46px) that fits headline cleanly in <= 3 lines."""
    words = str(text or "").split()
    for sz in (66, 60, 54, 48):
        fnt = font_fn(sz, bold=True)
        lines: List[str] = []
        if words:
            cur = words[0]
            for w in words[1:]:
                cand = f"{cur} {w}"
                if draw.textlength(cand, font=fnt) <= max_w:
                    cur = cand
                else:
                    lines.append(cur)
                    cur = w
            lines.append(cur)
        if len(lines) <= 3:
            return fnt, lines, sz
    fnt = font_fn(46, bold=True)
    lines = []
    cur = words[0] if words else ""
    for w in words[1:]:
        cand = f"{cur} {w}"
        if draw.textlength(cand, font=fnt) <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = w
            if len(lines) == 2:
                break
    if len(lines) < 3 and cur:
        lines.append(cur)
    return fnt, lines[:3], 46


def _build_thumb_variant_spec(
    topic: str,
    variant_idx: int,
    matched_icons: List[str],
    timeline: Any = None,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """Produces topic-adapted specs across all 16 high-tech layouts, optionally enriched by fast LLM JSON."""
    clean_topic = str(topic or "System Design Deep Dive").strip()
    words = [
        w for w in re.sub(r"[^A-Za-z0-9_+/\- ]", " ", clean_topic).split()
        if w.lower() not in ("explain", "how", "what", "why", "with", "using", "into", "from", "for", "and", "the")
    ]
    short_top = (" ".join(words[:4]) if words else clean_topic)[:32]
    key_noun = (words[0] if words else "System")[:14]

    layout_mode, angle_tag, chrome_style, hl_fn = _THUMB_ANGLES[variant_idx % len(_THUMB_ANGLES)]
    default_hl = hl_fn(short_top)

    low = clean_topic.lower()
    def _has_kw(*kws: str) -> bool:
        return any(re.search(rf"\b{re.escape(k)}", low) for k in kws)

    is_sql = _has_kw("sql", "join", "dense_rank", "window", "query", "select", "index", "postgres", "mysql")
    is_py = _has_kw("python", "asyncio", "gil", "pandas", "pytorch", "orm", "n+1")
    is_data = _has_kw("dms", "cdc", "snowflake", "kafka", "s3", "airflow", "etl", "elt", "pipeline", "parquet", "warehouse", "databricks", "spark")
    is_sec = _has_kw("security", "firewall", "port", "iam", "gpo", "whitelist", "oauth", "jwt", "zero trust")
    is_ai = _has_kw("ai", "agent", "llm", "rag", "vector", "embedding", "mcp", "genai", "openai", "gemini")
    is_cloud = _has_kw("k8s", "kubernetes", "docker", "terraform", "aws", "azure", "gcp", "cloud", "deploy")

    if is_data:
        code_lines = [
            "ORACLE_CDC -> AWS DMS (Parquet)",
            "S3_RAW     -> Airflow -> L0_RAW",
            "MERGE L1_HARMONIZED -> L2_CURATED",
            "ALERT on lag > 5s (Zero Data Loss)",
        ]
        diff_bad = ["- Full nightly table dump (4 hrs)", "- Schema drift breaks downstream"]
        diff_good = ["+ Continuous WAL CDC + S3 Parquet", "+ Idempotent MERGE L0 -> L1 -> L2"]
        code_focus, code_note, code_metric = 3, "Continuous CDC -> L0 -> L1 -> L2!", "SUB-SECOND CDC"
        pipe_nodes = [("SOURCE CDC", "DMS / Stream"), ("CLOUD LAKE", "S3 Parquet"), ("WAREHOUSE", "L0 -> L1 -> L2")]
        seq_actors = ["SOURCE DB", "CDC STREAM", "WAREHOUSE"]
        bench_rows = [("Nightly Dump", 95, "4h 12m"), ("Hourly Batch", 60, "58m"), ("Micro-Batch", 28, "90s"), ("Streaming CDC", 7, "0.8s")]
    elif is_sql:
        code_lines = [
            "SELECT u.id, COUNT(o.id) AS total",
            "FROM users u INNER JOIN orders o",
            "  ON o.user_id = u.id  -- Indexed!",
            "GROUP BY u.id ORDER BY total DESC;",
        ]
        diff_bad = ["- SELECT * FROM orders WHERE ...;", "- Full Seq Scan (1,840ms lock)"]
        diff_good = ["+ CREATE INDEX idx_orders_uid;", "+ B-Tree Index Seek (1.2ms!)"]
        code_focus, code_note, code_metric = 3, "B-Tree Index Seek: 1,840ms -> 1.2ms!", "1,500x FASTER"
        pipe_nodes = [("RAW TABLES", "Orders + Users"), ("INDEXED JOIN", "B-Tree Seek"), ("AGGREGATE", "GROUP BY Rank")]
        seq_actors = ["CLIENT", "PLANNER", "BTREE DB"]
        bench_rows = [("Naive Subquery", 92, "1,840ms"), ("Temp Join", 64, "620ms"), ("Composite Index", 22, "38ms"), ("Covering Index", 9, "1.2ms")]
    elif is_py:
        code_lines = [
            "ids = [u.id for u in users]",
            "orders = db.fetch_batch(ids)  # 1 query",
            "for u in users:",
            "    res.append(orders[u.id])  # O(1)",
        ]
        diff_bad = ["- for u in users: db.query(u.id)", "- 1,000 serial roundtrips (940ms)"]
        diff_good = ["+ batch = db.fetch_batch(ids)", "+ Single vectorized roundtrip (8ms!)"]
        code_focus, code_note, code_metric = 2, "Eliminates 1,000 N+1 DB roundtrips!", "940ms -> 8ms"
        pipe_nodes = [("EVENT LOOP", "Async Tasks"), ("BATCH PREFETCH", "Zero N+1 Lock"), ("FAST PAYLOAD", "116x Speedup")]
        seq_actors = ["API ROUTE", "ASYNC POOL", "DB BATCH"]
        bench_rows = [("Sync N+1 Loop", 94, "940ms"), ("Thread Pool", 55, "280ms"), ("Async Gather", 24, "42ms"), ("Batch Prefetch", 8, "8ms")]
    elif is_sec:
        code_lines = [
            "ALLOW tcp:443 FROM app_subnet",
            "DENY  tcp:5432 FROM 0.0.0.0/0",
            "VERIFY mTLS + IAM Role STS Token",
            "LOG   audit_trail -> SIEM Vault",
        ]
        diff_bad = ["- ALLOW 0.0.0.0/0 port 5432", "- Static long-lived root API keys"]
        diff_good = ["+ ALLOW app_subnet tcp:443 mTLS", "+ Short-lived IAM STS Role Token"]
        code_focus, code_note, code_metric = 2, "Least-privilege firewall + zero public DB!", "ZERO TRUST"
        pipe_nodes = [("EDGE PROXY", "URL Allowlist"), ("FIREWALL GATE", "TCP 443 Only"), ("IAM & AUDIT", "Least Privilege")]
        seq_actors = ["CLIENT", "WAF GATE", "IAM STS"]
        bench_rows = [("Public Subnet", 96, "HIGH RISK"), ("Static Keys", 68, "MEDIUM"), ("VPC Peering", 26, "HARDENED"), ("Zero Trust mTLS", 8, "VERIFIED")]
    elif is_ai:
        code_lines = [
            "plan = orchestrator.route(query)",
            "ctx  = rag_store.hybrid_search(plan)",
            "res  = verifier.check(agent_out, ctx)",
            "emit(res, latency_ms=42, grounded=True)",
        ]
        diff_bad = ["- Single prompt loop without tools", "- Unverified hallucinated outputs"]
        diff_good = ["+ Hybrid RAG + Tool Router DAG", "+ Guardrail Verifier + Memory Sync"]
        code_focus, code_note, code_metric = 3, "Grounded Agent + Guardrail Verification!", "99.4% ACCURACY"
        pipe_nodes = [("PLANNER AGENT", "Intent Routing"), ("HYBRID TOOLS", "Vector + SQL"), ("VERIFIER GATE", "Fact Grounding")]
        seq_actors = ["USER", "AGENT HUB", "TOOL/RAG"]
        bench_rows = [("Zero-Shot LLM", 88, "42% Acc"), ("Basic RAG", 62, "68% Acc"), ("Agent + Tools", 30, "89% Acc"), ("Multi-Agent + Guard", 11, "99.4% Acc")]
    elif is_cloud:
        code_lines = [
            "ingress -> ALB (Health Check /ready)",
            "hpa.scale(min=3, max=40, cpu=65%)",
            "rollout canary(weight=10% -> 100%)",
            "rollback_on(p99 > 120ms or 5xx > 0.1%)",
        ]
        diff_bad = ["- Single EC2 + manual SSH deploy", "- Downtime & cold boot spikes"]
        diff_good = ["+ Multi-AZ Canary + Auto HPA", "+ Zero-Downtime Health Gate"]
        code_focus, code_note, code_metric = 3, "Zero-downtime multi-AZ canary rollout!", "99.99% UPTIME"
        pipe_nodes = [("INGRESS LB", "TLS + Health"), ("AUTOSCALE PODS", "HPA Multi-AZ"), ("CANARY GATE", "Instant Rollback")]
        seq_actors = ["TRAFFIC", "INGRESS", "POD MESH"]
        bench_rows = [("Single VM", 91, "4.2m Down"), ("Manual Blue/Green", 54, "45s Swap"), ("Rolling K8s", 26, "12s Warm"), ("Canary Auto-Gate", 8, "0ms Loss")]
    else:
        code_lines = [
            f"INGEST  {key_noun} -> Gateway Guard",
            "BUFFER  Async Queue + Backpressure",
            "PROCESS Idempotent Worker Pool",
            "METRICS p99 < 12ms | 99.99% SLA",
        ]
        diff_bad = [f"- Unbounded sync calls in {key_noun}", "- Cascading timeout & retry storm"]
        diff_good = [f"+ Backpressure queue + {key_noun} pool", "+ Sub-12ms p99 + 99.99% SLA"]
        code_focus, code_note, code_metric = 2, f"How production {key_noun} prevents crashes!", "99.99% SLA"
        pipe_nodes = [(f"{key_noun.upper()} EDGE", "Validate & Route"), ("CORE ENGINE", "Scale & Process"), ("DURABLE STORE", "Zero Loss")]
        seq_actors = ["PRODUCER", "GATEWAY", "ENGINE"]
        bench_rows = [("Naive Sync", 92, "1,420ms"), ("Queued Pool", 58, "410ms"), ("Sharded Cache", 24, "34ms"), ("Production Path", 9, "11ms")]

    spec: Dict[str, Any] = {
        "layout_mode": layout_mode,
        "chrome_style": chrome_style,
        "angle_tag": angle_tag,
        "headline": default_hl,
        "sub_hook": code_note,
        "metric_big": code_metric,
        "pipe_nodes": pipe_nodes,
        "bad_title": "NAIVE WAY",
        "bad_points": [f"Manual bottlenecks in {key_noun}", "High p99 latency & outages", "Unbounded locks under load"],
        "good_title": "PRODUCTION FIX",
        "good_points": [pipe_nodes[1][1], code_note, f"Verified {code_metric}"],
        "code_lines": code_lines,
        "code_focus": code_focus,
        "code_note": code_note,
        "diff_bad": diff_bad,
        "diff_good": diff_good,
        "sticky_title": angle_tag,
        "sticky_text": code_note,
        "interview_q": f'"How would you architect {short_top} for 10x traffic?"',
        "hub_center": key_noun.upper()[:10],
        "hub_targets": [p[0] for p in pipe_nodes],
        "seq_actors": seq_actors,
        "bench_rows": bench_rows,
        "gauge_before": bench_rows[0][2],
        "gauge_after": bench_rows[-1][2],
    }

    if not use_llm:
        return spec

    prompt = f"""Generate ONE unique dark-theme 9:16 YouTube Shorts thumbnail concept #{variant_idx + 1} for topic: "{clean_topic}".
Required Visual Angle: {layout_mode} ({angle_tag}). Make the headline & insight punchy, high-CTR, and fresh!
Return STRICT JSON ONLY:
{{
  "headline": "punchy 4-7 word high-CTR title",
  "sub_hook": "short 5-8 word curiosity line",
  "metric_big": "short badge e.g. 15x FASTER or ZERO LOSS",
  "pipe_nodes": [["NODE 1","3 words"],["NODE 2","3 words"],["NODE 3","3 words"]],
  "bad_points": ["mistake 1","mistake 2"],
  "good_points": ["fix 1","fix 2"],
  "code_lines": ["line 1","line 2","line 3","line 4"],
  "sticky_text": "short sticky note insight <=44 chars",
  "interview_q": "sharp question <=65 chars"
}}"""

    raw = ""
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            res = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
            raw = str(getattr(res, "text", "") or "").strip()
        except Exception:
            raw = ""
    if not raw and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=min(0.95, 0.45 + (variant_idx % 6) * 0.08),
                timeout=7,
            )
            raw = res.choices[0].message.content.strip() if res.choices else ""
        except Exception:
            raw = ""

    if raw:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, dict):
                    if parsed.get("headline"):
                        spec["headline"] = str(parsed["headline"])[:64]
                    if parsed.get("sub_hook"):
                        spec["sub_hook"] = str(parsed["sub_hook"])[:68]
                    if parsed.get("metric_big"):
                        spec["metric_big"] = str(parsed["metric_big"])[:18].upper()
                    if isinstance(parsed.get("pipe_nodes"), list) and len(parsed["pipe_nodes"]) >= 3:
                        spec["pipe_nodes"] = [
                            (str(x[0])[:18], str(x[1])[:26])
                            for x in parsed["pipe_nodes"][:3]
                            if isinstance(x, (list, tuple)) and len(x) >= 2
                        ] or spec["pipe_nodes"]
                    if isinstance(parsed.get("bad_points"), list) and parsed["bad_points"]:
                        spec["bad_points"] = [str(x)[:36] for x in parsed["bad_points"][:3]]
                    if isinstance(parsed.get("good_points"), list) and parsed["good_points"]:
                        spec["good_points"] = [str(x)[:36] for x in parsed["good_points"][:3]]
                    if isinstance(parsed.get("code_lines"), list) and len(parsed["code_lines"]) >= 3:
                        spec["code_lines"] = [str(x)[:46] for x in parsed["code_lines"][:4]]
                    if parsed.get("sticky_text"):
                        spec["sticky_text"] = str(parsed["sticky_text"])[:54]
                    if parsed.get("interview_q"):
                        spec["interview_q"] = str(parsed["interview_q"])[:72]
                    spec["hub_targets"] = [p[0] for p in spec["pipe_nodes"]]
            except Exception:
                pass
    return spec


# ---------------------------------------------------------------------------
# Modular High-Tech Centerpiece Layout Renderers (All 16 Variants)
# ---------------------------------------------------------------------------

def _draw_card(stage: Any, coords: Tuple[int, int, int, int], outline: Tuple[int, ...], radius: int = 22, elev: int = 10, width: int = 2) -> None:
    stage.draw_glass_card(coords, radius=radius, accent_col=None, active=False, elev=elev)
    stage.draw.rounded_rectangle(coords, radius=radius, outline=outline, width=width)


def _render_myth_vs_fix(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    m_txt = spec["metric_big"]
    m_fnt = fnt(60, bold=True)
    mw = min(840, int(stage.draw.textlength(m_txt, font=m_fnt)) + 76)
    mx0 = (1080 - mw) // 2
    stage.draw.rounded_rectangle((mx0, 636, mx0 + mw, 738), radius=24, fill=(*c_pri, 34), outline=(*c_pri, 220), width=3)
    wrap(stage.draw, (mx0 + 20, 650), m_txt, m_fnt, c_pri, mw - 40, align="center", max_lines=1)
    ctx["mesh"](stage, 540, 865, 92, "torus_3d", c_pri, progress=0.72, active=False, alpha_mul=0.55, secondary_color=c_soft)

    _draw_card(stage, (92, 955, 524, 1435), (244, 63, 94, 195), radius=24)
    _draw_vector_glyph(stage.draw, "cross", 136, 998, 22, (244, 63, 94), width=4)
    stage.draw.text((160, 982), spec["bad_title"], fill=(253, 164, 175), font=fnt(27, bold=True))
    stage.draw.line((122, 1030, 494, 1030), fill=(244, 63, 94, 120), width=2)
    for bi, bp in enumerate(spec["bad_points"][:3]):
        _draw_vector_glyph(stage.draw, "cross", 134, 1068 + bi * 112, 14, (244, 63, 94), width=3)
        wrap(stage.draw, (156, 1054 + bi * 112), bp, fnt(23, bold=True), (248, 250, 252), 342, max_lines=3)

    _draw_card(stage, (556, 955, 988, 1435), (52, 211, 153, 195), radius=24)
    _draw_vector_glyph(stage.draw, "check", 600, 998, 22, (52, 211, 153), width=4)
    stage.draw.text((624, 982), spec["good_title"], fill=(110, 231, 183), font=fnt(27, bold=True))
    stage.draw.line((586, 1030, 958, 1030), fill=(52, 211, 153, 120), width=2)
    for gi, gp in enumerate(spec["good_points"][:3]):
        _draw_vector_glyph(stage.draw, "check", 598, 1068 + gi * 112, 14, (52, 211, 153), width=3)
        wrap(stage.draw, (620, 1054 + gi * 112), gp, fnt(23, bold=True), (248, 250, 252), 342, max_lines=3)


def _render_live_code(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_muted, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_muted"], ctx["fnt"], ctx["wrap"]
    stage.draw.rounded_rectangle((94, 636, 986, 1210), radius=22, fill=(9, 14, 28, 245), outline=(*c_pri, 175), width=2)
    stage.draw.text((126, 656), "main.py  ·  LIVE SIMULATOR", fill=c_pri, font=fnt(22, bold=True, mono=True))
    stage.draw.rounded_rectangle((838, 650, 956, 692), radius=10, fill=(52, 211, 153, 45), outline=(52, 211, 153, 210), width=2)
    _draw_vector_glyph(stage.draw, "play", 862, 671, 12, (110, 231, 183))
    stage.draw.text((880, 658), "RUN", fill=(110, 231, 183), font=fnt(21, bold=True))
    stage.draw.line((112, 708, 968, 708), fill=(51, 65, 85, 160), width=2)

    c_focus = int(spec.get("code_focus", 2))
    for li, cl in enumerate(spec["code_lines"][:4], start=1):
        ly = 736 + (li - 1) * 92
        if li == c_focus:
            stage.draw.rounded_rectangle((112, ly - 10, 968, ly + 62), radius=12, fill=(*c_pri, 44), outline=(*c_pri, 210), width=2)
        stage.draw.text((130, ly + 6), f"0{li}", fill=c_muted, font=fnt(24, bold=True, mono=True))
        stage.draw.text((192, ly + 4), cl[:40], fill=(248, 250, 252), font=fnt(25, bold=True, mono=True))

    stage.draw.rounded_rectangle((132, 1110, 950, 1230), radius=16, fill=(17, 24, 39, 250), outline=(251, 191, 36, 225), width=3)
    _draw_vector_glyph(stage.draw, "bolt", 168, 1138, 16, (251, 191, 36))
    stage.draw.text((186, 1126), f"LINE 0{c_focus} INSIGHT", fill=(251, 191, 36), font=fnt(20, bold=True))
    wrap(stage.draw, (160, 1162), spec["code_note"], fnt(26, bold=True), (248, 250, 252), 760, max_lines=1)

    _draw_card(stage, (94, 1265, 986, 1445), (52, 211, 153, 190), radius=20, elev=8)
    stage.draw.text((126, 1290), "OUTPUT TRACE", fill=(148, 163, 184), font=fnt(21, bold=True, mono=True))
    _draw_vector_glyph(stage.draw, "check", 138, 1356, 18, (110, 231, 183), width=4)
    stage.draw.text((164, 1340), f"{spec['metric_big']}  -  Verified Production Run", fill=(110, 231, 183), font=fnt(27, bold=True))


def _render_blueprint(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    for gy in range(620, 1460, 60):
        stage.draw.line((80, gy, 1000, gy), fill=(*c_pri, 32), width=1)
    for gx in range(80, 1020, 60):
        stage.draw.line((gx, 620, gx, 1460), fill=(*c_pri, 32), width=1)
    box_coords = [(120, 660, 480, 845), (590, 825, 960, 1010), (140, 1015, 520, 1200)]
    for idx_b, ((bx0, by0, bx1, by1), (n_title, n_sub)) in enumerate(zip(box_coords, spec["pipe_nodes"])):
        stage.draw.rounded_rectangle((bx0, by0, bx1, by1), radius=18, fill=(10, 22, 46, 240), outline=(*c_pri, 235), width=3)
        stage.draw.text((bx0 + 26, by0 + 34), n_title, fill=(255, 255, 255), font=fnt(28, bold=True))
        wrap(stage.draw, (bx0 + 26, by0 + 84), n_sub, fnt(23, bold=False, mono=True), c_pri, bx1 - bx0 - 48, max_lines=2)
        if idx_b < 2:
            nx0, ny0 = (bx1, (by0 + by1) // 2) if idx_b == 0 else (bx0 + 180, by1)
            tx0, ty0 = (box_coords[idx_b + 1][0], (box_coords[idx_b + 1][1] + box_coords[idx_b + 1][3]) // 2) if idx_b == 0 else (box_coords[idx_b + 1][2], (box_coords[idx_b + 1][1] + box_coords[idx_b + 1][3]) // 2)
            stage.draw.line((nx0, ny0, tx0, ty0), fill=(*c_pri, 215), width=4)
            stage.draw.ellipse((tx0 - 6, ty0 - 6, tx0 + 6, ty0 + 6), fill=c_pri)
    stage.draw.rounded_rectangle((490, 1235, 960, 1440), radius=18, fill=(24, 22, 12, 245), outline=(251, 191, 36, 240), width=3)
    _draw_vector_glyph(stage.draw, "pin", 528, 1272, 16, (251, 191, 36))
    stage.draw.text((548, 1260), spec["sticky_title"], fill=(251, 191, 36), font=fnt(22, bold=True))
    wrap(stage.draw, (520, 1304), spec["sticky_text"], fnt(26, bold=True), (255, 255, 255), 410, max_lines=3)


def _render_iso_layers(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    ctx["mesh"](stage, 540, 745, 118, "cube_cluster_3d", c_pri, progress=0.8, active=False, alpha_mul=0.55, secondary_color=c_soft)
    layer_colors = [c_pri, (52, 211, 153), (251, 191, 36)]
    for li, (n_title, n_sub) in enumerate(spec["pipe_nodes"][:3]):
        ly = 890 + li * 175
        lc = layer_colors[li % 3]
        _draw_card(stage, (120, ly, 960, ly + 138), (*lc, 175), radius=24)
        stage.draw.rounded_rectangle((148, ly + 28, 232, ly + 110), radius=16, fill=(*lc, 34), outline=(*lc, 200), width=2)
        stage.draw.text((168, ly + 48), f"L{li+1}", fill=lc, font=fnt(32, bold=True, mono=True))
        stage.draw.text((258, ly + 26), n_title, fill=(255, 255, 255), font=fnt(30, bold=True))
        wrap(stage.draw, (258, ly + 72), n_sub, fnt(24, bold=False), (203, 213, 225), 660, max_lines=1)
        if li < 2:
            stage.draw.line((540, ly + 138, 540, ly + 175), fill=(*c_pri, 210), width=4)


def _render_interview_hub(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    _draw_card(stage, (100, 636, 980, 815), (*c_pri, 185), radius=22)
    stage.draw.text((134, 658), "INTERVIEWER QUESTION", fill=c_pri, font=fnt(21, bold=True))
    wrap(stage.draw, (134, 700), spec["interview_q"], fnt(28, bold=True), (255, 255, 255), 810, max_lines=2)

    hub_x, hub_y = 540, 1020
    targets_xy = [(220, 1320), (540, 1320), (860, 1320)]
    for tx, ty in targets_xy:
        stage.draw.line((hub_x, hub_y + 52, tx, ty - 68), fill=(*c_pri, 210), width=4)
    stage.draw.rounded_rectangle((hub_x - 150, hub_y - 68, hub_x + 150, hub_y + 68), radius=24, fill=(*c_pri, 245))
    wrap(stage.draw, (hub_x - 135, hub_y - 26), spec["hub_center"], fnt(38, bold=True), (8, 13, 27), 270, align="center", max_lines=1)
    for (tx, ty), (n_title, n_sub) in zip(targets_xy, spec["pipe_nodes"][:3]):
        _draw_card(stage, (tx - 135, ty - 70, tx + 135, ty + 115), (*c_pri, 165), radius=20, elev=8)
        wrap(stage.draw, (tx - 120, ty - 40), n_title, fnt(22, bold=True), (255, 255, 255), 240, align="center", max_lines=2)
        wrap(stage.draw, (tx - 120, ty + 28), n_sub, fnt(19, bold=False), c_pri, 240, align="center", max_lines=2)


def _render_bento_telemetry(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    # Wide Hero Bento Tile (top)
    _draw_card(stage, (72, 608, 1008, 882), (*c_pri, 175), radius=26, elev=12)
    stage.draw.text((112, 636), "PRODUCTION TELEMETRY", fill=c_pri, font=fnt(21, bold=True, mono=True))
    stage.draw.text((112, 676), spec["metric_big"], fill=(248, 250, 252), font=fnt(58, bold=True))
    wrap(stage.draw, (112, 760), spec["code_note"], fnt(25, bold=False), (203, 213, 225), 540, max_lines=2)
    # Mini live sparkline inside hero card
    pts = [(690, 818), (735, 795), (780, 804), (825, 750), (870, 762), (915, 695), (964, 676)]
    stage.draw.line(pts, fill=c_pri, width=5)
    stage.draw.ellipse((956, 668, 972, 684), fill=(52, 211, 153))

    # Bottom 2x2 Bento Grid
    tiles = [
        ((72, 906, 526, 1180), "STAGE 01", spec["pipe_nodes"][0][0], spec["pipe_nodes"][0][1], c_pri),
        ((554, 906, 1008, 1180), "STAGE 02", spec["pipe_nodes"][1][0], spec["pipe_nodes"][1][1], (52, 211, 153)),
        ((72, 1204, 526, 1468), "STAGE 03", spec["pipe_nodes"][2][0], spec["pipe_nodes"][2][1], (251, 191, 36)),
        ((554, 1204, 1008, 1468), "SYSTEM CORE", spec["hub_center"], f"{spec['gauge_before']} -> {spec['gauge_after']}", c_soft),
    ]
    for box, tag, t_head, t_sub, col in tiles:
        _draw_card(stage, box, (*col, 155), radius=24, elev=10)
        stage.draw.rounded_rectangle((box[0] + 24, box[1] + 24, box[0] + 158, box[1] + 58), radius=12, fill=(*col, 32), outline=(*col, 175), width=2)
        stage.draw.text((box[0] + 40, box[1] + 30), tag, fill=col, font=fnt(18, bold=True, mono=True))
        wrap(stage.draw, (box[0] + 26, box[1] + 82), t_head, fnt(30, bold=True), (255, 255, 255), 395, max_lines=2)
        wrap(stage.draw, (box[0] + 26, box[1] + 168), t_sub, fnt(23, bold=False), col, 395, max_lines=2)


def _render_latency_gauge(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    # Radial Arc Gauge at top center
    _draw_card(stage, (84, 608, 996, 1110), (*c_pri, 155), radius=30, elev=12)
    cx, cy, r = 540, 895, 210
    stage.draw.arc((cx - r, cy - r, cx + r, cy + r), start=165, end=375, fill=(51, 65, 85, 190), width=26)
    stage.draw.arc((cx - r, cy - r, cx + r, cy + r), start=165, end=342, fill=(*c_pri, 245), width=26)
    # Indicator needle
    ang = math.radians(342)
    stage.draw.line((cx, cy, int(cx + (r - 36) * math.cos(ang)), int(cy + (r - 36) * math.sin(ang))), fill=(52, 211, 153), width=6)
    stage.draw.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(248, 250, 252))
    wrap(stage.draw, (240, 945), spec["metric_big"], fnt(48, bold=True), c_pri, 600, align="center", max_lines=1)
    wrap(stage.draw, (200, 1020), spec["code_note"], fnt(24, bold=False), (226, 232, 240), 680, align="center", max_lines=1)

    # Bottom Before vs After telemetry bars
    _draw_card(stage, (84, 1138, 996, 1468), (*c_pri, 135), radius=26, elev=10)
    rows = [("BEFORE (BOTTLENECK)", spec["gauge_before"], 0.88, (244, 63, 94)), ("AFTER (OPTIMIZED)", spec["gauge_after"], 0.14, (52, 211, 153))]
    for ri, (lbl, val, pct, col) in enumerate(rows):
        ry = 1175 + ri * 140
        stage.draw.text((124, ry), lbl, fill=(148, 163, 184), font=fnt(20, bold=True, mono=True))
        stage.draw.text((790, ry - 4), val, fill=col, font=fnt(28, bold=True))
        stage.draw.rounded_rectangle((124, ry + 42, 956, ry + 86), radius=16, fill=(24, 34, 54, 230), outline=(51, 65, 85, 160), width=2)
        stage.draw.rounded_rectangle((124, ry + 42, 124 + max(72, int(832 * pct)), ry + 86), radius=16, fill=(*col, 235))


def _render_datacenter_rack(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    # Dual Glowing Data Center Server Racks + Fiber Link Between Them
    stage.draw.line((360, 900, 720, 900), fill=(*c_pri, 215), width=5)
    for px in (440, 540, 640):
        stage.draw.ellipse((px - 10, 890, px + 10, 910), fill=c_pri)
        stage.draw.ellipse((px - 5, 895, px + 5, 905), fill=(255, 255, 255))

    for rx0, title, col in ((125, spec["pipe_nodes"][0][0], c_pri), (665, spec["pipe_nodes"][2][0], (52, 211, 153))):
        stage.draw.rounded_rectangle((rx0, 648, rx0 + 290, 1140), radius=20, fill=(10, 16, 30, 245), outline=(*col, 195), width=3)
        stage.draw.text((rx0 + 24, 672), title[:15], fill=col, font=fnt(22, bold=True, mono=True))
        for bi in range(6):
            by = 720 + bi * 64
            stage.draw.rounded_rectangle((rx0 + 22, by, rx0 + 268, by + 46), radius=10, fill=(18, 28, 48, 240), outline=(*col, 120), width=2)
            stage.draw.ellipse((rx0 + 40, by + 17, rx0 + 52, by + 29), fill=(52, 211, 153) if bi != 2 else (251, 191, 36))
            stage.draw.line((rx0 + 70, by + 23, rx0 + 235, by + 23), fill=(*col, 110), width=4)

    # Center Core Router Pill
    stage.draw.rounded_rectangle((435, 835, 645, 965), radius=24, fill=(*c_pri, 245))
    wrap(stage.draw, (448, 876), spec["hub_center"], fnt(30, bold=True), (8, 13, 27), 184, align="center", max_lines=1)

    _draw_card(stage, (112, 1175, 968, 1445), (*c_pri, 165), radius=24)
    stage.draw.text((146, 1205), f"CLUSTER STATUS: {spec['metric_big']}", fill=c_pri, font=fnt(24, bold=True, mono=True))
    for i, (pt, pd) in enumerate(spec["pipe_nodes"][:3]):
        stage.draw.text((146, 1260 + i * 54), f"NODE 0{i+1}  {pt}: {pd}", fill=(248, 250, 252), font=fnt(24, bold=True))


def _render_sequence_trace(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    cols_x = [210, 540, 870]
    for cx, actor in zip(cols_x, spec["seq_actors"]):
        _draw_card(stage, (cx - 120, 640, cx + 120, 720), (*c_pri, 200), radius=18)
        wrap(stage.draw, (cx - 108, 666), actor, fnt(23, bold=True, mono=True), (255, 255, 255), 216, align="center", max_lines=1)
        stage.draw.line((cx, 720, cx, 1245), fill=(71, 85, 105, 165), width=3)

    arrows = [
        (210, 540, 800, f"1. {spec['pipe_nodes'][0][0]}", c_pri),
        (540, 870, 930, f"2. {spec['pipe_nodes'][1][0]}", (251, 191, 36)),
        (870, 540, 1060, f"3. {spec['pipe_nodes'][2][0]}", (52, 211, 153)),
        (540, 210, 1190, f"4. {spec['metric_big']}", (52, 211, 153)),
    ]
    for x0, x1, y, lbl, col in arrows:
        stage.draw.line((x0, y, x1, y), fill=(*col, 230), width=4)
        dir_s = 1 if x1 > x0 else -1
        stage.draw.polygon([(x1, y), (x1 - dir_s * 18, y - 10), (x1 - dir_s * 18, y + 10)], fill=col)
        tx = min(x0, x1) + 20
        stage.draw.text((tx, y - 34), lbl[:24], fill=col, font=fnt(22, bold=True))

    _draw_card(stage, (104, 1270, 976, 1445), (52, 211, 153, 185), radius=22)
    wrap(stage.draw, (140, 1304), f"ZERO-BOTTLENECK PATH: {spec['code_note']}", fnt(26, bold=True), (248, 250, 252), 800, max_lines=2)


def _render_git_diff_patch(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    _draw_card(stage, (94, 636, 986, 935), (244, 63, 94, 185), radius=22)
    stage.draw.text((130, 662), "BEFORE.py  (- SLOW / BUG)", fill=(253, 164, 175), font=fnt(22, bold=True, mono=True))
    for i, ln in enumerate(spec["diff_bad"][:2]):
        stage.draw.rounded_rectangle((124, 718 + i * 94, 956, 796 + i * 94), radius=12, fill=(244, 63, 94, 34), outline=(244, 63, 94, 130), width=2)
        stage.draw.text((146, 742 + i * 94), ln[:46], fill=(254, 205, 211), font=fnt(25, bold=True, mono=True))

    _draw_card(stage, (94, 965, 986, 1265), (52, 211, 153, 195), radius=22)
    stage.draw.text((130, 992), "AFTER.py  (+ PRODUCTION FIX)", fill=(110, 231, 183), font=fnt(22, bold=True, mono=True))
    stage.draw.rounded_rectangle((760, 984, 956, 1028), radius=12, fill=(52, 211, 153, 42), outline=(52, 211, 153, 210), width=2)
    stage.draw.text((786, 994), "APPROVED", fill=(110, 231, 183), font=fnt(20, bold=True))
    for i, ln in enumerate(spec["diff_good"][:2]):
        stage.draw.rounded_rectangle((124, 1048 + i * 94, 956, 1126 + i * 94), radius=12, fill=(52, 211, 153, 34), outline=(52, 211, 153, 135), width=2)
        stage.draw.text((146, 1072 + i * 94), ln[:46], fill=(209, 250, 229), font=fnt(25, bold=True, mono=True))

    _draw_card(stage, (94, 1295, 986, 1445), (*c_pri, 180), radius=22)
    stage.draw.text((130, 1326), f"PR IMPACT: {spec['metric_big']}", fill=c_pri, font=fnt(26, bold=True))
    wrap(stage.draw, (130, 1372), spec["code_note"], fnt(24, bold=False), (248, 250, 252), 820, max_lines=1)


def _render_pipeline_dag(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    # Diamond / Pill DAG Topology: Top Source -> 2 Parallel Branches -> Bottom Merge Sink
    p0 = (540, 680)
    p1 = (275, 965)
    p2 = (805, 965)
    p3 = (540, 1260)
    for a, b in ((p0, p1), (p0, p2), (p1, p3), (p2, p3)):
        stage.draw.line((*a, *b), fill=(*c_pri, 200), width=5)
        mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
        stage.draw.ellipse((mx - 10, my - 10, mx + 10, my + 10), fill=(52, 211, 153))

    dag_nodes = [
        (p0, "SOURCE INGEST", spec["pipe_nodes"][0][1], c_pri),
        (p1, spec["pipe_nodes"][1][0], spec["pipe_nodes"][1][1], (251, 191, 36)),
        (p2, "VERIFY + METRICS", spec["metric_big"], (52, 211, 153)),
        (p3, spec["pipe_nodes"][2][0], spec["pipe_nodes"][2][1], c_pri),
    ]
    for (nx, ny), title, sub, col in dag_nodes:
        _draw_card(stage, (nx - 190, ny - 64, nx + 190, ny + 64), (*col, 210), radius=24)
        wrap(stage.draw, (nx - 172, ny - 40), title, fnt(24, bold=True), (255, 255, 255), 344, align="center", max_lines=1)
        wrap(stage.draw, (nx - 172, ny + 6), sub, fnt(20, bold=False, mono=True), col, 344, align="center", max_lines=1)


def _render_warroom_radar(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    cx, cy = 540, 860
    for r in (75, 140, 205):
        stage.draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(244, 63, 94, 155), width=2)
    stage.draw.polygon([(cx, cy), (cx + 150, cy - 140), (cx + 205, cy - 30)], fill=(244, 63, 94, 48))
    stage.draw.ellipse((cx + 95, cy - 88, cx + 119, cy - 64), fill=(244, 63, 94))
    stage.draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=c_pri)
    stage.draw.text((130, 648), "ALERT DETECTED", fill=(253, 164, 175), font=fnt(22, bold=True, mono=True))
    stage.draw.text((740, 648), "SLA GUARD ACTIVE", fill=(110, 231, 183), font=fnt(22, bold=True, mono=True))

    _draw_card(stage, (104, 1110, 976, 1268), (244, 63, 94, 190), radius=22)
    stage.draw.text((138, 1134), "ROOT CAUSE", fill=(253, 164, 175), font=fnt(21, bold=True, mono=True))
    wrap(stage.draw, (138, 1172), spec["bad_points"][1], fnt(27, bold=True), (255, 255, 255), 800, max_lines=2)

    _draw_card(stage, (104, 1292, 976, 1450), (52, 211, 153, 195), radius=22)
    stage.draw.text((138, 1316), f"MITIGATION ({spec['metric_big']})", fill=(110, 231, 183), font=fnt(21, bold=True, mono=True))
    wrap(stage.draw, (138, 1354), spec["code_note"], fnt(27, bold=True), (255, 255, 255), 800, max_lines=2)


def _render_agent_mesh(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    cx, cy = 540, 1020
    stage.draw.ellipse((cx - 285, cy - 285, cx + 285, cy + 285), outline=(*c_pri, 120), width=3)
    satellites = [
        (540, 695, spec["pipe_nodes"][0][0], c_pri),
        (850, 1020, spec["pipe_nodes"][1][0], (52, 211, 153)),
        (540, 1345, spec["pipe_nodes"][2][0], (251, 191, 36)),
        (230, 1020, spec["metric_big"][:14], c_soft),
    ]
    for sx, sy, lbl, col in satellites:
        stage.draw.line((cx, cy, sx, sy), fill=(*col, 175), width=4)
        _draw_card(stage, (sx - 135, sy - 54, sx + 135, sy + 54), (*col, 215), radius=22)
        wrap(stage.draw, (sx - 120, sy - 18), lbl, fnt(22, bold=True), (255, 255, 255), 240, align="center", max_lines=1)

    stage.draw.ellipse((cx - 128, cy - 128, cx + 128, cy + 128), fill=(11, 18, 34, 250), outline=(*c_pri, 245), width=4)
    wrap(stage.draw, (cx - 110, cy - 26), spec["hub_center"], fnt(34, bold=True), c_pri, 220, align="center", max_lines=1)


def _render_benchmark_bars(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["fnt"], ctx["wrap"]
    _draw_card(stage, (78, 608, 1002, 742), (*c_pri, 185), radius=24)
    wrap(stage.draw, (110, 640), f"VERIFIED WINNER: {spec['metric_big']}", fnt(40, bold=True), c_pri, 860, align="center", max_lines=1)

    colors = [(244, 63, 94), (251, 191, 36), c_pri, (52, 211, 153)]
    for i, (label, pct, val) in enumerate(spec["bench_rows"][:4]):
        by = 776 + i * 168
        col = colors[i % 4]
        _draw_card(stage, (78, by, 1002, by + 144), (*col, 155), radius=22, elev=8)
        stage.draw.text((112, by + 22), label, fill=(248, 250, 252), font=fnt(26, bold=True))
        stage.draw.text((790, by + 20), val, fill=col, font=fnt(28, bold=True))
        stage.draw.rounded_rectangle((112, by + 74, 968, by + 114), radius=14, fill=(22, 30, 48, 235))
        stage.draw.rounded_rectangle((112, by + 74, 112 + max(72, int(856 * (pct / 100.0))), by + 114), radius=14, fill=(*col, 235))


def _render_card_carousel_stack(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["fnt"], ctx["wrap"]
    ctx["mesh"](stage, 840, 740, 110, "geodesic_sphere", c_pri, progress=0.7, active=False, alpha_mul=0.45, secondary_color=c_soft)
    colors = [c_pri, (52, 211, 153), (251, 191, 36)]
    for i, (p_title, p_desc) in enumerate(spec["pipe_nodes"][:3]):
        off_x = 76 + i * 32
        cy = 650 + i * 260
        col = colors[i % 3]
        _draw_card(stage, (off_x, cy, off_x + 860, cy + 220), (*col, 200), radius=28, elev=12)
        stage.draw.rounded_rectangle((off_x + 32, cy + 32, off_x + 140, cy + 84), radius=14, fill=(*col, 34), outline=(*col, 210), width=2)
        stage.draw.text((off_x + 54, cy + 43), f"0{i+1}", fill=col, font=fnt(28, bold=True, mono=True))
        stage.draw.text((off_x + 168, cy + 34), p_title, fill=(255, 255, 255), font=fnt(34, bold=True))
        wrap(stage.draw, (off_x + 34, cy + 112), p_desc, fnt(28, bold=False), (226, 232, 240), 790, max_lines=2)


def _render_architecture(ctx: Dict[str, Any]) -> None:
    stage, spec, c_pri, c_soft, c_hex, fnt, wrap = ctx["stage"], ctx["spec"], ctx["c_pri"], ctx["c_soft"], ctx["c_hex"], ctx["fnt"], ctx["wrap"]
    ctx["mesh"](stage, 540, 755, 145, "geodesic_sphere", c_pri, progress=0.65, active=False, alpha_mul=0.45, secondary_color=c_soft)
    icon_positions = [(250, 755), (540, 755), (830, 755)]
    stage.draw.line((295, 755, 785, 755), fill=(*c_pri, 140), width=3)
    for ii, (ix, iy) in enumerate(icon_positions):
        _draw_card(stage, (ix - 82, iy - 82, ix + 82, iy + 82), (*c_pri, 160), radius=28)
        ext_icon = ctx["fetch_svg"](ctx["matched_icons"][ii], size_px=92, tint_hex=c_hex, depth=10, tint_rgb=c_pri)
        if ext_icon is not None:
            stage.fg.alpha_composite(ext_icon, (ix - ext_icon.width // 2, iy - ext_icon.height // 2))
        else:
            ctx["mesh"](stage, ix, iy, 46, ("torus_3d", "atom_orbit", "cube_cluster_3d")[ii], c_pri, progress=0.75, active=False)

    card_y = 940
    for num_s, (p_title, p_desc) in zip(("01", "02", "03"), spec["pipe_nodes"][:3]):
        _draw_card(stage, (94, card_y, 986, card_y + 150), (*c_pri, 130), radius=22, elev=8)
        stage.draw.rounded_rectangle((114, card_y + 34, 188, card_y + 108), radius=18, fill=(*c_pri, 28), outline=(*c_pri, 180), width=2)
        stage.draw.text((132, card_y + 52), num_s, fill=c_pri, font=fnt(32, bold=True, mono=True))
        stage.draw.text((214, card_y + 30), p_title, fill=c_pri, font=fnt(24, bold=True))
        wrap(stage.draw, (214, card_y + 68), p_desc, fnt(25, bold=False), ctx["text_col"], 748, max_lines=2)
        card_y += 170


_THUMB_LAYOUT_DISPATCH: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "architecture": _render_architecture,
    "myth_vs_fix": _render_myth_vs_fix,
    "live_code": _render_live_code,
    "blueprint": _render_blueprint,
    "iso_layers": _render_iso_layers,
    "interview_hub": _render_interview_hub,
    "bento_telemetry": _render_bento_telemetry,
    "latency_gauge": _render_latency_gauge,
    "datacenter_rack": _render_datacenter_rack,
    "sequence_trace": _render_sequence_trace,
    "git_diff_patch": _render_git_diff_patch,
    "pipeline_dag": _render_pipeline_dag,
    "warroom_radar": _render_warroom_radar,
    "agent_mesh": _render_agent_mesh,
    "benchmark_bars": _render_benchmark_bars,
    "card_carousel_stack": _render_card_carousel_stack,
}


def generate_thumbnail_9_16(
    topic: str,
    timeline: Any = None,
    watermark: str = DEFAULT_WATERMARK,
    visual_engine: str = "hybrid_modern",
    output_path: Any = None,
    tone: str = "auto_2026_director",
    variant_seed: Optional[int] = None,
    use_llm: bool = True,
) -> Path:
    """
    Generates a fresh, high-CTR 1080x1920 (9:16) DARK-THEME YouTube Shorts / Reels Cover Poster.
    Cycles across 16 distinct high-tech layouts, 12 dark color themes, 8 geometric dark grids,
    and 5 frame chromes so repeated clicks deliver radically different modern thumbnails.
    """
    from core.cinematic_engine import (
        StudioStage,
        _draw_wrapped_text as _cin_wrap,
        _get_font as _cin_font,
        dispatch_studio_layout,
        draw_procedural_3d_mesh,
        fetch_3d_extruded_svg,
        resolve_studio_world,
    )

    canvas_w, canvas_h = 1080, 1920
    clean_topic = str(topic or "System Design Deep Dive").strip()
    v_idx = int(variant_seed) if variant_seed is not None else int(time.time_ns() // 1000000)

    theme = _THUMB_DARK_THEMES[(v_idx * 5 + v_idx // len(_THUMB_ANGLES)) % len(_THUMB_DARK_THEMES)]
    bg_style = _THUMB_BG_STYLES[(v_idx * 3 + v_idx // len(_THUMB_DARK_THEMES)) % len(_THUMB_BG_STYLES)]

    art_style = str(timeline.get("art_style", "editorial_dark")) if isinstance(timeline, dict) else "editorial_dark"
    sc0 = timeline.get("scenes", [{}])[0] if (isinstance(timeline, dict) and timeline.get("scenes")) else {}
    eff_tone = resolve_effective_tone(tone, scene_tone=sc0.get("scene_tone") if isinstance(sc0, dict) else None, role="hook", idx=0)
    world = resolve_studio_world(
        art_style=art_style,
        tone=eff_tone,
        visual_data=sc0.get("visual_data", {}) if isinstance(sc0, dict) else {},
        topic=clean_topic,
    )

    c_pri = theme["pri"]
    c_btn = theme["btn"]
    c_muted_ui = (148, 163, 184)
    c_soft_tint = theme["soft"]
    c_hex = theme["hex"]
    bg_col = theme["bg"]

    thumb_world = dict(world)
    thumb_world.update({
        "is_light": False,
        "bg_top": bg_col,
        "bg_bot": (max(4, bg_col[0] - 3), max(6, bg_col[1] - 4), max(10, bg_col[2] - 6)),
        "spot_a": (15, 23, 42),
        "spot_b": (15, 23, 42),
        "spot_c": (15, 23, 42),
        "grid_col": theme["grid"],
        "text": (248, 250, 252),
        "muted": c_muted_ui,
        "cyan": c_pri,
        "purple": c_soft_tint,
        "emerald": (52, 211, 153),
        "amber": (251, 191, 36),
        "rose": (244, 63, 94),
        "card_bg": (14, 20, 34, 244),
        "card_layer": (11, 16, 28, 236),
        "card_alt": (20, 28, 45, 246),
        "border": (*c_pri, 130),
        "glass_rim": (148, 163, 184, 58),
        "shadow_col": (2, 4, 10, 195),
    })

    bg = Image.new("RGBA", (canvas_w, canvas_h), (*bg_col, 255))
    _draw_dark_thumb_backdrop(bg, theme, bg_style)
    stage = StudioStage(canvas_w, canvas_h, thumb_world)

    category_label, matched_icons = _infer_thumb_category_and_icons(clean_topic, timeline=timeline)
    spec = _build_thumb_variant_spec(clean_topic, v_idx, matched_icons, timeline=timeline, use_llm=use_llm)

    # 1. Top Creator Chrome
    cat_font = _cin_font(22, bold=True)
    cat_txt = f"{category_label} · {spec['angle_tag']}" if len(category_label) < 16 else spec["angle_tag"]
    cat_w = min(640, int(stage.draw.textlength(cat_txt, font=cat_font)) + 64)
    _draw_card(stage, (56, 52, 56 + cat_w, 104), (*c_pri, 145), radius=26, elev=6)
    stage.draw.ellipse((76, 72, 88, 84), fill=c_pri)
    stage.draw.text((98, 65), cat_txt, fill=thumb_world["text"], font=cat_font)

    if watermark and watermark.strip():
        wt = watermark.strip()
        wm_font = _cin_font(22, bold=True)
        wm_w = int(stage.draw.textlength(wt, font=wm_font)) + 52
        wx0 = canvas_w - wm_w - 56
        _draw_card(stage, (wx0, 52, wx0 + wm_w, 104), (*c_pri, 110), radius=26, elev=6)
        stage.draw.ellipse((wx0 + 18, 72, wx0 + 30, 84), fill=c_pri)
        stage.draw.text((wx0 + 38, 65), wt, fill=thumb_world["text"], font=wm_font)

    # 2. High-Impact Cover Headline & Curiosity Sub-Hook
    raw_headline = spec["headline"]
    if isinstance(timeline, dict) and v_idx == 0:
        tl_hl = str(timeline.get("hook_headline") or timeline.get("title") or "").strip()
        if tl_hl:
            raw_headline = tl_hl
    if len(raw_headline) > 72:
        raw_headline = raw_headline[:69].rsplit(" ", 1)[0] + "..."

    h_font, h_lines, h_sz = _fit_cover_headline(stage.draw, raw_headline, 956, _cin_font)
    lh = int(h_sz * 1.18)
    hy = 148 if len(h_lines) >= 3 else (172 if len(h_lines) == 2 else 200)
    for li, ln in enumerate(h_lines):
        lw = stage.draw.textlength(ln, font=h_font)
        lx = int((canvas_w - lw) / 2.0)
        is_accent_line = (len(h_lines) > 1 and li == len(h_lines) - 1) or bool(re.search(r"\b\d+[%xmsKMB]?\b", ln))
        t_col = c_pri if is_accent_line else thumb_world["text"]
        stage.draw.text((lx + 2, hy + 4), ln, fill=(4, 8, 18, 195), font=h_font)
        stage.draw.text((lx, hy), ln, fill=t_col, font=h_font)
        hy += lh

    sub_hook = spec["sub_hook"]
    if len(sub_hook) > 68:
        sub_hook = sub_hook[:65].rsplit(" ", 1)[0] + "..."
    sub_y = min(446, hy + 18)
    sub_font = _cin_font(27, bold=True)
    sub_w = min(950, int(stage.draw.textlength(sub_hook, font=sub_font)) + 64)
    sx0 = (canvas_w - sub_w) // 2
    _draw_card(stage, (sx0, sub_y, sx0 + sub_w, sub_y + 62), (*c_pri, 145), radius=31, elev=8)
    _cin_wrap(stage.draw, (sx0 + 24, sub_y + 15), sub_hook, sub_font, (226, 232, 240), sub_w - 48, align="center", max_lines=1)

    # 3. Showcase Container Chrome + Dispatched Layout Renderer
    best_sc = None
    if isinstance(timeline, dict) and timeline.get("scenes"):
        sc_pool = [s for s in timeline["scenes"] if isinstance(s, dict) and not str(s.get("visual_type") or "").startswith(("v2_", "v3_", "v4_", "v5_"))]
        if sc_pool:
            best_sc = sc_pool[v_idx % len(sc_pool)]

    l_mode = spec["layout_mode"]
    win_label = (str((best_sc or {}).get("visual_type") or l_mode).replace("_", " ").upper())[:32]
    _draw_thumb_stage_chrome(stage, spec["chrome_style"], win_label, c_pri, c_muted_ui, font_fn=_cin_font)

    if best_sc is not None:
        box_x0, box_y0, box_x1, box_y1 = 56, 542, 1024, 1492
        clean_vd = copy.deepcopy(best_sc.get("visual_data") or {})
        for list_k in ("nodes", "satellites", "bars", "items", "steps", "stages"):
            if isinstance(clean_vd.get(list_k), list):
                for item in clean_vd[list_k]:
                    if isinstance(item, dict) and "color" in item:
                        item["color"] = c_hex
        inner_stage = StudioStage(canvas_w, canvas_h, thumb_world)
        dispatch_studio_layout(inner_stage, best_sc.get("visual_type", "architecture_flow"), clean_vd, 1.0, thumb_world, topic=clean_topic)
        inner_rgba = inner_stage.composite_onto(None)
        cropped = inner_rgba.crop((44, 308, 1036, 1420))
        target_w, target_h = box_x1 - box_x0 - 44, box_y1 - box_y0 - 82
        scale = min(target_w / cropped.width, target_h / cropped.height)
        nw, nh = max(64, int(cropped.width * scale)), max(64, int(cropped.height * scale))
        resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
        px = box_x0 + ((box_x1 - box_x0) - nw) // 2
        py = box_y0 + 62 + ((box_y1 - box_y0 - 70) - nh) // 2
        stage.fg.alpha_composite(resized, (px, py))
    else:
        render_ctx = {
            "stage": stage,
            "spec": spec,
            "c_pri": c_pri,
            "c_soft": c_soft_tint,
            "c_muted": c_muted_ui,
            "c_hex": c_hex,
            "text_col": thumb_world["text"],
            "matched_icons": matched_icons,
            "fnt": _cin_font,
            "wrap": _cin_wrap,
            "mesh": draw_procedural_3d_mesh,
            "fetch_svg": fetch_3d_extruded_svg,
        }
        renderer = _THUMB_LAYOUT_DISPATCH.get(l_mode, _render_architecture)
        renderer(render_ctx)

    # 4. Bottom Safe-Zone Value Strip & Crisp Accent CTA
    _draw_card(stage, (56, 1532, 1024, 1722), (*c_pri, 115), radius=30, elev=12)
    chip_cat = "AI Engineering" if category_label.upper() in ("AI", "AI ENGINEERING") else category_label.title()
    chips = [chip_cat, spec["metric_big"], "Step-by-Step"]
    chip_font = _cin_font(22, bold=True)
    chip_ws = [int(stage.draw.textlength(ch, font=chip_font)) + 52 for ch in chips]
    total_cw = sum(chip_ws) + 18 * (len(chips) - 1)
    ch_x = (canvas_w - total_cw) // 2
    for ch_txt, cw in zip(chips, chip_ws):
        stage.draw.rounded_rectangle((ch_x, 1554, ch_x + cw, 1604), radius=25, fill=(24, 34, 54, 230), outline=(*c_pri, 145), width=2)
        stage.draw.ellipse((ch_x + 18, 1574, ch_x + 28, 1584), fill=c_pri)
        stage.draw.text((ch_x + 36, 1566), ch_txt, fill=thumb_world["text"], font=chip_font)
        ch_x += cw + 18

    cta_text = f"WATCH FULL BREAKDOWN   •   {watermark.strip()}" if watermark and watermark.strip() else "WATCH FULL BREAKDOWN"
    cta_font = _cin_font(26, bold=True)
    cta_w = min(880, int(stage.draw.textlength(cta_text, font=cta_font)) + 104)
    cta_x = (canvas_w - cta_w) // 2
    stage.draw.rounded_rectangle((cta_x, 1628, cta_x + cta_w, 1696), radius=34, fill=(*c_btn, 255))
    cta_txt_col = (255, 255, 255)
    _draw_vector_glyph(stage.draw, "play", cta_x + 42, 1662, 20, cta_txt_col)
    _cin_wrap(stage.draw, (cta_x + 58, 1646), cta_text, cta_font, cta_txt_col, cta_w - 80, align="center", max_lines=1)

    im_out = stage.composite_onto(bg)
    if output_path is None:
        output_path = OUTPUT_DIR / f"thumbnail_9x16_v{(v_idx % len(_THUMB_ANGLES)) + 1}_{int(time.time())}.png"
    im_out.convert("RGB").save(output_path, "PNG", quality=98)
    return output_path


def generate_thumbnail_pack(
    topic: str,
    count: int = 4,
    start_seed: int = 0,
    watermark: str = DEFAULT_WATERMARK,
    visual_engine: str = "hybrid_modern",
    tone: str = "auto_2026_director",
) -> List[Dict[str, Any]]:
    """Generates `count` distinct dark high-tech thumbnails in one batch without blocking on N LLM calls."""
    ts = int(time.time())
    results: List[Dict[str, Any]] = []
    for k in range(max(1, min(8, int(count)))):
        seed = int(start_seed) + k
        layout_mode, angle_tag, _, _ = _THUMB_ANGLES[seed % len(_THUMB_ANGLES)]
        out_p = OUTPUT_DIR / f"thumbnail_9x16_pack_{seed}_{ts}_{k}.png"
        p = generate_thumbnail_9_16(
            topic=topic,
            watermark=watermark,
            visual_engine=visual_engine,
            output_path=out_p,
            tone=tone,
            variant_seed=seed,
            use_llm=False,
        )
        results.append({
            "path": p,
            "seed": seed,
            "layout_mode": layout_mode,
            "angle_tag": angle_tag,
        })
    return results
