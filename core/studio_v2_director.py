"""
Studio V2 AI Director — Isolated from Classic NanoPro (zero interference with core/director.py).

Produces two flagship 2026 visual reel architectures:
1. `v2_vector_storyboard` (GyanaHut Style):
   Unified dark navy stage + top segmented story progress bar + clean progressive SVG widgets
   (chat dialogue, score meter + stamp, incremental icon cards, spaghetti red curves -> glowing hub,
    paired real-world analogy tree, split takeaway, and branded follow card).
2. `v2_spatial_isometric` (@thetechypenguin Style):
   Persistent 2.5D Isometric Architecture World (`world_nodes`, `world_edges`, `world_zones`)
   built progressively scene-by-scene with smooth camera pan/zoom (`focus_node_ids`, `node_overrides`)
   and a sleek colored-border Glassy Top HUD Card.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from core.config import DEFAULT_WATERMARK, GEMINI_API_KEY, GROQ_API_KEY
from core.tone_engine import get_tone_profile

STUDIO_V2_MODE_OPTIONS = [
    ("classic_nanopro", "🧠 Classic NanoPro Studio (All 1,221 Engines + 24 Specialist Modes — Untouched)"),
    ("v2_auto", "⚡ Studio V2 Auto-Director (Smart Picks: Vector / Isometric / V3 IDE / V4 Whiteboard / V5 Data Center)"),
    ("v2_vector_storyboard", "📐 Studio V2 — Clean Vector Storyboard (GyanaHut Style · Progressive SVG + Paired Analogy)"),
    ("v2_spatial_isometric", "🌐 Studio V2 — Spatial Isometric World (@thetechypenguin Style · 2.5D Map + Camera Fly + Top HUD)"),
    ("v3_live_ide", "🖥️ Studio V3 — Live IDE & SQL/Python Simulator (Code Highlight · Click Ripple · Callout · Live Output Drawer)"),
    ("v4_blueprint_whiteboard", "✏️ Studio V4 — Blueprint Whiteboard Studio (ByteByteGo / Excalidraw · Dark Grid · Marker Diagrams · Sticky Bubbles)"),
    ("v5_datacenter_park", "🏢 Studio V5 — Enterprise Data Center & IT Park (Campus → Dept → Engineer Fly-In)"),
]


def is_studio_v2_mode(mode_key: str) -> bool:
    return str(mode_key or "").strip() in (
        "v2_auto",
        "v2_vector_storyboard",
        "v2_spatial_isometric",
        "v3_live_ide",
        "v4_blueprint_whiteboard",
        "v5_datacenter_park",
        "v5_live_ide",
        "v7_blueprint_whiteboard",
    )


def resolve_v2_sub_engine(topic: str, mode_key: str, duration_mode: str = "auto") -> str:
    """Routes `v2_auto` cleanly between `vector_storyboard`, `spatial_isometric`, `live_ide`, `blueprint_whiteboard`, and `datacenter_park`."""
    mk = str(mode_key or "v2_auto").strip()
    if mk == "v2_vector_storyboard":
        return "vector_storyboard"
    if mk == "v2_spatial_isometric":
        return "spatial_isometric"
    if mk in ("v3_live_ide", "v5_live_ide"):
        return "live_ide"
    if mk in ("v4_blueprint_whiteboard", "v7_blueprint_whiteboard"):
        return "blueprint_whiteboard"
    if mk == "v5_datacenter_park":
        return "datacenter_park"

    low = f" {str(topic or '').lower()} "
    dc_kw = (
        "data center", "datacenter", "it park", "port opening", "url whitelist",
        "group policy", "gpo", "active directory", "mcs", "managed cloud",
        "is team", "infra team", "audit team", "it news", "ai hack",
    )
    if any(k in low for k in dc_kw):
        return "datacenter_park"

    low = f" {str(topic or '').lower()} "
    ide_kw = (
        "sql", "select ", "join", "dense_rank", "window function", "cte", "query", "n+1",
        "orm", "python", "asyncio", "gil", "pandas", "dataframe", "pytorch", "code",
        "debug", "ide", "traceback", "exception", "decorator", "generator", "index scan",
    )
    if any(k in low for k in ide_kw):
        return "live_ide"

    wb_kw = (
        "whiteboard", "excalidraw", "bytebytego", "rate limit", "consistent hash",
        "cap theorem", "url shortener", "webhook", "oauth", "jwt", "circuit breaker",
        "pub/sub", "fanout", "system design",
    )
    if any(k in low for k in wb_kw):
        return "blueprint_whiteboard"

    iso_kw = (
        "blue-green", "blue green", "canary", "deployment", "devops", "ci/cd", "cicd",
        "kubernetes", "k8s", "docker", "kafka", "flink", "spark", "snowflake", "lakehouse",
        "load balancer", "microservice", "architecture", "pipeline", "etl", "cdc", "debezium",
        "redis", "cache", "sharding", "replication", "failover", "disaster recovery", "rag",
        "agent", "aws", "azure", "gcp", "terraform", "distributed", "queue",
    )
    if any(k in low for k in iso_kw) or str(duration_mode).lower() == "deep_dive":
        return "spatial_isometric"
    return "vector_storyboard"


def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    raw = str(text or "").strip()
    if not raw:
        return None
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _language_rule(voice: str, topic: str) -> str:
    v = str(voice or "").lower()
    if "mr-in" in v or "marathi" in topic.lower():
        return (
            "Narration Language: Natural conversational Marathi + English technical terms mixed naturally "
            "(spoken Devanagari Marathi like 'तुम्ही', 'मग', 'समजा', and keep English tech terms in Latin e.g. 'MCP', 'Load Balancer', 'CI/CD'). "
            "On-screen HUD titles/labels: crisp concise Roman Hinglish/Marathi OR Devanagari + English tech keywords (max 4-6 words per heading)."
        )
    if "hi-in" in v or "hindi" in topic.lower() or "hinglish" in topic.lower():
        return (
            "Narration Language: Natural conversational Hinglish (Devanagari Hindi grammar + English technical nouns cleanly spelled in Latin so Edge-TTS reads smoothly, e.g. 'interviewer', 'production', 'Blue-Green deployment', 'Redis'). "
            "On-screen HUD titles/labels: punchy short Hindi/Roman-Hinglish + English tech words (e.g. 'Build sirf ek baar.', 'हर बार अलग integration')."
        )
    return (
        "Narration Language: Crisp conversational Creator English (punchy short sentences, high retention, zero fluff). "
        "On-screen HUD titles/labels: short 3-6 word impactful English headlines."
    )


def _scene_count_guidance(duration_mode: str, sub_engine: str) -> str:
    dm = str(duration_mode or "auto").lower()
    if dm == "short":
        return "6 to 8 tight scenes (~35-50s total)"
    if dm == "standard":
        return "8 to 11 clear scenes (~55-85s total)"
    if dm == "deep_dive":
        return "11 to 16 comprehensive walkthrough scenes (~95-150s total)"
    if sub_engine == "spatial_isometric":
        return "9 to 14 scenes (covering Hook -> Live Baseline -> Build -> Provision -> Test -> Switch -> Edge Cases/State -> Rollback/Cost/DB -> Poll CTA, NO artificial time cap)"
    if sub_engine == "live_ide":
        return "7 to 10 punchy coding scenes (Hook Bug -> Naive Query/Loop -> Live Run Traceback/Slow Plan -> Exact Line Fix -> Fast Execution Output -> Benchmark Proof -> CTA)"
    if sub_engine == "blueprint_whiteboard":
        return "7 to 11 clear whiteboard scenes (Hook Dilemma -> Naive Sketch Flaw -> Core Blueprint Architecture -> Data Flow & Edge Case -> Trade-Off Sticky Summary -> CTA)"
    return "8 to 11 crisp storyboard scenes (Interview Hook -> Misconception Meter -> Problem Scenario -> Spaghetti vs Clean Hub -> Paired Real-World Analogy -> Takeaway -> Follow CTA)"


def _sanitize_whiteboard_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enforces clean spacing inside the 1000x1000 blueprint canvas so marker boxes never overlap."""
    import math
    clean = [dict(n) for n in (nodes or []) if isinstance(n, dict)]
    if not clean:
        return clean
    for idx_n, n in enumerate(clean):
        n["x"] = float(n.get("x", 240 + (idx_n % 3) * 260))
        n["y"] = float(n.get("y", 260 + (idx_n // 3) * 280))
        n["w"] = float(n.get("w", 230))
        n["h"] = float(n.get("h", 110))
    if len(clean) >= 2:
        min_dist = 255.0
        for _ in range(12):
            moved = False
            for i in range(len(clean)):
                for j in range(i + 1, len(clean)):
                    dx = clean[j]["x"] - clean[i]["x"]
                    dy = clean[j]["y"] - clean[i]["y"]
                    d = math.hypot(dx, dy)
                    if d < min_dist:
                        if d < 1e-3:
                            dx, dy, d = 1.0, 0.7, 1.22
                        push = (min_dist - d) * 0.55
                        ux, uy = dx / d, dy / d
                        clean[i]["x"] = max(145.0, min(855.0, clean[i]["x"] - ux * push))
                        clean[i]["y"] = max(145.0, min(855.0, clean[i]["y"] - uy * push))
                        clean[j]["x"] = max(145.0, min(855.0, clean[j]["x"] + ux * push))
                        clean[j]["y"] = max(145.0, min(855.0, clean[j]["y"] + uy * push))
                        moved = True
            if not moved:
                break
    for n in clean:
        n["x"] = round(max(135.0, min(865.0, n["x"])))
        n["y"] = round(max(135.0, min(865.0, n["y"])))
    return clean


def _sanitize_isometric_world_spec(world_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Enforces minimum spatial separation (>= 310 iso units) between nodes so 3D shapes & labels never collide."""
    import math
    ws = dict(world_spec or {})
    nodes = [dict(n) for n in (ws.get("nodes") or []) if isinstance(n, dict)]
    if len(nodes) >= 2:
        for idx_n, n in enumerate(nodes):
            n["x"] = float(n.get("x", 240 + (idx_n % 3) * 330))
            n["y"] = float(n.get("y", 280 + (idx_n // 3) * 330))
        min_dist = 315.0
        for _ in range(14):
            moved = False
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    dx = nodes[j]["x"] - nodes[i]["x"]
                    dy = nodes[j]["y"] - nodes[i]["y"]
                    d = math.hypot(dx, dy)
                    if d < min_dist:
                        if d < 1e-3:
                            dx, dy, d = 1.0, 0.7, 1.22
                        push = (min_dist - d) * 0.55
                        ux, uy = dx / d, dy / d
                        nodes[i]["x"] = max(160.0, min(1320.0, nodes[i]["x"] - ux * push))
                        nodes[i]["y"] = max(180.0, min(1320.0, nodes[i]["y"] - uy * push))
                        nodes[j]["x"] = max(160.0, min(1320.0, nodes[j]["x"] + ux * push))
                        nodes[j]["y"] = max(180.0, min(1320.0, nodes[j]["y"] + uy * push))
                        moved = True
            if not moved:
                break
        for n in nodes:
            n["x"] = round(n["x"])
            n["y"] = round(n["y"])
    ws["nodes"] = nodes
    return ws


def _normalize_v2_scenes(
    scenes: List[Dict[str, Any]],
    tone: str,
    watermark: str,
    sub_engine: str,
    topic: str = "",
) -> List[Dict[str, Any]]:
    norm: List[Dict[str, Any]] = []
    valid_roles = {"hook", "misconception", "scenario", "problem", "solution", "analogy", "proof", "edge_case", "tradeoff", "cta"}
    short_top = " ".join(str(topic or "this architecture").strip().split()[:6])
    for i, sc in enumerate(scenes):
        if not isinstance(sc, dict):
            continue
        nar = str(sc.get("narration") or "").strip()
        if not nar:
            continue
        role = str(sc.get("role") or ("hook" if i == 0 else ("cta" if i == len(scenes) - 1 else "solution"))).lower().strip()
        if role not in valid_roles:
            role = "solution"
        sc_tone = str(sc.get("scene_tone") or get_tone_profile(tone, role=role, idx=i).get("key") or "warm_mentor_hi")
        vd = dict(sc.get("visual_data") or {})
        vd["watermark"] = watermark

        if sub_engine == "spatial_isometric":
            sm = str(vd.get("scene_mode") or "world_cam").strip()
            if sm == "hook_chat":
                vd.setdefault("chat_channel", "meet · architecture-interview")
                vd.setdefault("question_sender", "INTERVIEWER")
                if not str(vd.get("question_text") or "").strip():
                    vd["question_text"] = f'"{nar[:130]}"'
                if not str(vd.get("bad_answer") or "").strip():
                    vd["bad_answer"] = f'"Manual cron scripts se {short_top} dump kar denge..."'
                vd.setdefault("stamp", "REJECTED ✗")
            elif sm == "split_compare":
                if not isinstance(vd.get("left_card"), dict) or not vd["left_card"].get("title"):
                    vd["left_card"] = {"title": "MANUAL BATCH", "sub": "Cron & Downtime", "color": "rose"}
                if not isinstance(vd.get("right_card"), dict) or not vd["right_card"].get("title"):
                    vd["right_card"] = {"title": "AUTO CDC FLOW", "sub": "Zero Data Loss", "color": "emerald"}
            elif sm == "cta_poll":
                vd.setdefault("option_a", "⚡ Automated CDC")
                vd.setdefault("option_b", "🕰️ Nightly Cron")
                vd.setdefault("footer_note", "Save & follow for production architectures!")
            else:
                if not str(vd.get("card_title") or "").strip():
                    vd["card_title"] = str(vd.get("hud_pill") or role.upper())
        elif sub_engine == "live_ide":
            lang = str(vd.get("language") or ("sql" if "sql" in topic.lower() else "python")).lower()
            vd["language"] = lang if lang in ("python", "sql", "bash") else "python"
            vd.setdefault("file_name", "query.sql" if vd["language"] == "sql" else "app.py")
            if not isinstance(vd.get("code_lines"), list) or not vd["code_lines"]:
                vd["code_lines"] = [f"# {short_top}", "result = run_optimized()"]
            if not isinstance(vd.get("callout"), dict):
                vd["callout"] = {"title": "INSIGHT", "text": nar[:85], "line": 1, "color": "amber"}
            if not isinstance(vd.get("output_drawer"), dict):
                vd["output_drawer"] = {"mode": "terminal", "title": "LIVE OUTPUT", "metric": "OK", "lines": ["$ run", "✓ Done"]}
        elif sub_engine == "blueprint_whiteboard":
            vd["diagram_nodes"] = _sanitize_whiteboard_nodes(list(vd.get("diagram_nodes") or []))
            if not vd["diagram_nodes"]:
                vd["diagram_nodes"] = [
                    {"id": "n1", "kind": "box", "label": "Client", "sublabel": "Request", "x": 230, "y": 460, "color": "cyan"},
                    {"id": "n2", "kind": "cylinder", "label": short_top[:18], "sublabel": "Core Layer", "x": 760, "y": 460, "color": "emerald"},
                ]
                vd["diagram_edges"] = [{"from": "n1", "to": "n2", "label": "flow", "color": "amber"}]
            vd.setdefault("diagram_edges", [])
            vd.setdefault("sticky_notes", [])

        _engine_labels = {
            "vector_storyboard": ("v2_vector_storyboard", "Studio V2 (Vector Storyboard)"),
            "spatial_isometric": ("v2_spatial_isometric", "Studio V2 (Spatial Isometric World)"),
            "live_ide": ("v3_live_ide", "Studio V3 (Live IDE & SQL/Python Simulator)"),
            "blueprint_whiteboard": ("v4_blueprint_whiteboard", "Studio V4 (Blueprint Whiteboard Studio)"),
        }
        v_type_out, r_eng_out = _engine_labels.get(sub_engine, (f"v2_{sub_engine}", f"Studio ({sub_engine})"))

        norm.append({
            "scene_id": i + 1,
            "role": role,
            "scene_tone": sc_tone,
            "sfx_cue": str(sc.get("sfx_cue") or ("punch_impact" if i == 0 else ("alert_ping" if "error" in role or "problem" in role else "pop_snap"))),
            "narration": nar,
            "visual_type": v_type_out,
            "routed_engine": r_eng_out,
            "art_style": "v2_midnight_navy",
            "backdrop": "v2_clean_canvas",
            "transition": "smooth_fade",
            "text_fx": "clean_hud",
            "visual_data": vd,
            "actions": [],
            "_disable_actions_overlay": True,
            "_disable_camera_actions": True,
        })
    return norm


# ---------------------------------------------------------------------------
# Offline / Fallback Deterministic High-Craft Blueprints (Never Fails)
# ---------------------------------------------------------------------------
def _fallback_vector_storyboard(topic: str, watermark: str, tone: str, hook_style: str, cta_style: str, cta_keyword: str) -> Dict[str, Any]:
    clean_topic = (topic.strip() or "MCP (Model Context Protocol)")[:54]
    raw_words = re.sub(r"[^A-Za-z0-9_+ ]", "", clean_topic).strip().split()
    short_title = (raw_words[0] if (raw_words and raw_words[0].isupper() and len(raw_words[0]) <= 8) else " ".join(raw_words[:3])) or "Core Concept"
    cta_btn = f"Comment '{cta_keyword.strip().upper()}' 👇" if cta_style == "comment_keyword" and cta_keyword.strip() else "+ Follow करो"

    scenes = [
        {
            "role": "hook",
            "sfx_cue": "punch_impact",
            "narration": f"अगर interviewer तुमसे पूछे कि {short_title} क्या है, तो सिर्फ एक रटी हुई line बोलकर चुप मत हो जाना.",
            "visual_data": {
                "tag_pill": "INTERVIEW QUESTION",
                "headline_white": f"{short_title} क्या है?",
                "headline_accent": "सिर्फ नाम मत बोलो",
                "accent_color": "amber",
                "widget_type": "chat_dialogue",
                "messages": [
                    {"sender": "HR", "text": f"{short_title} कैसे काम करता है?", "color": "cyan", "delay_p": 0.08},
                    {"sender": "YOU", "text": f"{short_title} एक technical term है...", "color": "amber", "delay_p": 0.50},
                ],
            },
        },
        {
            "role": "misconception",
            "sfx_cue": "alert_ping",
            "narration": "क्योंकि इससे interviewer को तुरंत पता चल जाता है कि तुमने definition रट ली है, concept समझा नहीं है.",
            "visual_data": {
                "tag_pill": "INTERVIEWER KO PATA",
                "headline_white": "रटी हुई",
                "headline_accent": "definition = ✗",
                "accent_color": "cyan",
                "widget_type": "meter_verdict",
                "highlight_eyebrow": "COPY-PASTE DEFINITION",
                "highlight_text": clean_topic,
                "dialogue_sender": "HR",
                "dialogue_text": '"इसने तो रट लिया है..."',
                "bars": [
                    {"label": "याद (memory)", "pct": 95, "color": "emerald", "right_label": ""},
                    {"label": "समझ (understanding)", "pct": 5, "color": "rose", "right_label": "0%"},
                ],
                "stamp": "रटा ✗",
            },
        },
        {
            "role": "scenario",
            "sfx_cue": "pop_snap",
            "narration": f"मान लो तुम एक real production system बना रहे हो, जिसे अलग-अलग data sources, live APIs और tools से जोड़ना है.",
            "visual_data": {
                "tag_pill": "REAL SYSTEM",
                "headline_white": "मान लो एक",
                "headline_accent": "Production App है",
                "accent_color": "amber",
                "widget_type": "progressive_cards",
                "hero_icon": "robot",
                "hero_label": "Production System",
                "cards": [
                    {"icon": "file", "text": "Files & Docs पढ़े"},
                    {"icon": "db", "text": "Database से live data निकाले"},
                    {"icon": "git", "text": "APIs व external tools चलाए"},
                ],
                "footer_pill": "3 काम, 3 अलग-अलग sources",
            },
        },
        {
            "role": "problem",
            "sfx_cue": "alert_ping",
            "narration": "तो बिना सही architecture के हर एक integration के लिए अलग custom glue code लिखना और संभालना पड़ता है.",
            "visual_data": {
                "tag_pill": "PROBLEM → SOLUTION",
                "headline_white": "हर बार अलग",
                "headline_accent": "integration ✗",
                "accent_color": "amber",
                "widget_type": "spaghetti_wires",
                "left_node": {"icon": "robot", "label": "App"},
                "right_nodes": [
                    {"icon": "file", "label": "Files", "color": "cyan", "wire_tag": "custom code 1"},
                    {"icon": "db", "label": "Database", "color": "amber", "wire_tag": "custom code 2"},
                    {"icon": "git", "label": "External API", "color": "emerald", "wire_tag": "custom code 3"},
                ],
            },
        },
        {
            "role": "solution",
            "sfx_cue": "success_chime",
            "narration": f"यहीं पर {short_title} एक clean standard layer बनकर बीच में आता है, जो हर tool को एक ही protocol से जोड़ता है.",
            "visual_data": {
                "tag_pill": "CORE ARCHITECTURE",
                "headline_white": f"{short_title} = STANDARD",
                "headline_accent": "UNIFIED LAYER",
                "accent_color": "cyan",
                "widget_type": "hub_radiate",
                "left_node": {"icon": "robot", "label": "Core App"},
                "hub_label": short_title[:12].upper(),
                "hub_sub": "standard protocol",
                "right_nodes": [
                    {"icon": "file", "label": "Files", "color": "cyan"},
                    {"icon": "db", "label": "Database", "color": "amber"},
                    {"icon": "git", "label": "Git / CI", "color": "emerald"},
                    {"icon": "plug", "label": "APIs", "color": "purple"},
                ],
                "equation_line": "Application ⇄ Unified Standard Layer ⇄ Tools",
                "footer_pill": "connect करने का clean तरीका",
            },
        },
        {
            "role": "analogy",
            "sfx_cue": "pop_snap",
            "narration": "इसे ऐसे समझो जैसे USB अकेले एक port से keyboard, pen drive और phone सबको connect कर देता है.",
            "visual_data": {
                "tag_pill": "ANALOGY · USB",
                "headline_white": "जैसे USB",
                "headline_accent": "सबके लिए एक port",
                "accent_color": "amber",
                "widget_type": "analogy_tree",
                "top_node": {"icon": "monitor", "label": "Computer"},
                "hub_label": "USB",
                "hub_color": "cyan",
                "branches": [
                    {"icon": "keyboard", "label": "Keyboard", "color": "cyan", "check": True},
                    {"icon": "usb", "label": "Pen drive", "color": "amber", "check": True},
                    {"icon": "phone", "label": "Phone", "color": "emerald", "check": True},
                ],
                "equation_line": "",
                "footer_pill": "",
            },
        },
        {
            "role": "analogy",
            "sfx_cue": "success_chime",
            "narration": f"बिल्कुल वैसे ही {short_title} पूरे system के लिए एक universal port की तरह काम करता है.",
            "visual_data": {
                "tag_pill": f"SAME IDEA · {short_title[:12].upper()}",
                "headline_white": f"वैसे ही {short_title}",
                "headline_accent": "System का एक port",
                "accent_color": "cyan",
                "widget_type": "analogy_tree",
                "top_node": {"icon": "robot", "label": "Core System"},
                "hub_label": short_title[:12].upper(),
                "hub_color": "amber",
                "branches": [
                    {"icon": "file", "label": "Files", "color": "cyan", "check": True},
                    {"icon": "db", "label": "Database", "color": "amber", "check": True},
                    {"icon": "git", "label": "APIs", "color": "emerald", "check": True},
                ],
                "equation_line": "Clean universal standard communication",
                "footer_pill": "सबकी भाषा एक",
            },
        },
        {
            "role": "proof",
            "sfx_cue": "pop_snap",
            "narration": "यही असली फर्क है सिर्फ definition रटने में और system architecture गहराई से समझने में.",
            "visual_data": {
                "tag_pill": "यही फर्क है",
                "headline_white": "रटना vs",
                "headline_accent": "समझना",
                "accent_color": "amber",
                "widget_type": "split_verdict",
                "left_col": {"title": "याद करना", "body": f"{short_title} की लाइन", "status": "cross"},
                "right_col": {"title": "समझना", "body": "USB जैसा एक Universal Standard", "status": "check"},
                "equation_line": "याद ≠ समझ",
                "footer_pill": "Concept समझो, definition नहीं",
            },
        },
        {
            "role": "cta",
            "sfx_cue": "success_chime",
            "narration": "ऐसे ही practical system design और coding concepts के लिए चैनल को अभी follow और video को save कर लो.",
            "visual_data": {
                "tag_pill": "FOLLOW",
                "headline_white": "practical TECH +",
                "headline_accent": "SYSTEM concepts",
                "accent_color": "cyan",
                "widget_type": "follow_cta",
                "pills": ["System Design", "Coding", "Architecture", "Practical"],
                "handle_title": watermark,
                "handle_sub": "Tech & Engineering, आसान भाषा में",
                "cta_button": cta_btn,
            },
        },
    ]
    return {
        "topic": topic,
        "v2_engine": "vector_storyboard",
        "art_style": "v2_midnight_navy",
        "header_brand": (watermark or "NANOPRO TECH").lstrip("@").upper(),
        "category_tag": "TECH · ARCHITECTURE",
        "scenes": _normalize_v2_scenes(scenes, tone, watermark, "vector_storyboard"),
    }


def _fallback_spatial_isometric(topic: str, watermark: str, tone: str, cta_style: str, cta_keyword: str) -> Dict[str, Any]:
    clean_topic = (topic.strip() or "Blue-Green Zero-Downtime Deployment")[:54]
    short_title = " ".join(clean_topic.split()[:4])
    cta_sub = f"Comment '{cta_keyword.strip().upper()}'" if cta_style == "comment_keyword" and cta_keyword.strip() else "Share with a friend!"

    world_spec = {
        "nodes": [
            {"id": "cicd", "kind": "factory_cube", "label": "CI/CD", "sublabel": "BUILD ONCE", "x": 210, "y": 320, "color": "amber"},
            {"id": "lb", "kind": "balancer_bar", "label": "LOAD BALANCER", "sublabel": "TRAFFIC ROUTER", "x": 360, "y": 870, "color": "purple"},
            {"id": "blue", "kind": "server_cluster", "label": "BLUE · V1.0", "sublabel": "LIVE PRODUCTION", "x": 580, "y": 840, "color": "blue", "version": "V1.0"},
            {"id": "green", "kind": "server_cluster", "label": "GREEN · V2.0", "sublabel": "NEW BUILD", "x": 640, "y": 480, "color": "emerald", "version": "V2.0"},
            {"id": "gate", "kind": "test_gate", "label": "INTERNAL-TEST URL", "sublabel": "APPROVED", "x": 450, "y": 570, "color": "amber"},
            {"id": "redis", "kind": "cylinder_store", "label": "REDIS", "sublabel": "SESSIONS", "x": 910, "y": 600, "color": "rose"},
            {"id": "db", "kind": "cylinder_store", "label": "DATABASE", "sublabel": "SHARED", "x": 920, "y": 890, "color": "purple", "schema_pills": ["id", "v2_col"]},
        ],
        "edges": [
            {"id": "e_cicd_green", "from": "cicd", "to": "green", "color": "amber", "style": "packets"},
            {"id": "e_lb_blue", "from": "lb", "to": "blue", "color": "cyan", "style": "packets"},
            {"id": "e_lb_green", "from": "lb", "to": "green", "color": "emerald", "style": "packets"},
            {"id": "e_blue_redis", "from": "blue", "to": "redis", "color": "rose", "style": "dashed"},
            {"id": "e_green_redis", "from": "green", "to": "redis", "color": "emerald", "style": "dashed"},
            {"id": "e_redis_db", "from": "redis", "to": "db", "color": "purple", "style": "dashed"},
        ],
        "zones": [
            {"label": "INFRASTRUCTURE AS CODE", "x": 470, "y": 390, "w": 360, "h": 260, "color": "emerald"},
            {"label": "PRODUCTION", "x": 410, "y": 720, "w": 390, "h": 260, "color": "cyan"},
        ],
    }

    scenes = [
        {
            "role": "hook",
            "sfx_cue": "punch_impact",
            "narration": f"Interviewer ने पूछा: {short_title} में बिना 1 second downtime के नया version कैसे deploy करोगे?",
            "visual_data": {
                "scene_mode": "hook_chat",
                "hud_pill": "SYSTEM INTERVIEW",
                "headline_white": "Zero downtime",
                "headline_accent": "deploy?",
                "accent_color": "cyan",
                "chat_channel": "meet · system-interview",
                "question_sender": "INTERVIEWER",
                "question_text": f'"{clean_topic} बिना 1 second downtime के कैसे करोगे?"',
                "bad_answer": '"रात 2 बजे deploy कर देंगे, तब traffic कम होता है"',
                "stamp": "REJECTED ✗",
                "stamp_delay_p": 0.65,
            },
        },
        {
            "role": "solution",
            "sfx_cue": "pop_snap",
            "narration": "सही जवाब है — दो समानांतर environments और instant traffic routing, ताकि एक version live रहे और दूसरा चुपचाप तैयार हो.",
            "visual_data": {
                "scene_mode": "split_compare",
                "hud_pill": "DEPLOYMENT STRATEGY",
                "headline_white": "Zero-Downtime",
                "headline_accent": "Architecture.",
                "accent_color": "cyan",
                "left_card": {"title": "BLUE", "sub": "Live Traffic v1.0", "color": "blue"},
                "right_card": {"title": "GREEN", "sub": "Staging / New v2.0", "color": "emerald"},
            },
        },
        {
            "role": "scenario",
            "sfx_cue": "pop_snap",
            "narration": "अभी सारा real user traffic Load Balancer से होकर Blue v1.0 servers पर चल रहा है.",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "LIVE BASELINE",
                "headline_white": "Abhi live:",
                "headline_accent": "Blue.",
                "accent_color": "cyan",
                "card_eyebrow": "BLUE ENVIRONMENT",
                "card_title": "Blue · v1.0",
                "card_bullets": ["User traffic → Load Balancer → Blue Servers"],
                "focus_node_ids": ["lb", "blue"],
                "active_edge_ids": ["e_lb_blue"],
                "node_overrides": {
                    "cicd": {"visible": False},
                    "green": {"visible": False},
                    "gate": {"visible": False},
                    "redis": {"visible": False},
                    "db": {"visible": False},
                    "blue": {"visible": True, "badge": "● LIVE"},
                },
            },
        },
        {
            "role": "solution",
            "sfx_cue": "whoosh",
            "narration": "सबसे पहले CI/CD Pipeline नया version सिर्फ एक बार build करता है और वही single artifact आगे बढ़ता है.",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "CI / CD",
                "headline_white": "Build",
                "headline_accent": "sirf ek baar.",
                "accent_color": "amber",
                "card_eyebrow": "CI/CD PIPELINE",
                "card_title": "Artifact · v2.0",
                "card_bullets": ["Immutable single build pushed forward"],
                "focus_node_ids": ["cicd"],
                "active_edge_ids": [],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": False},
                    "gate": {"visible": False},
                    "redis": {"visible": False},
                    "db": {"visible": False},
                    "blue": {"visible": True, "badge": "● LIVE"},
                },
            },
        },
        {
            "role": "solution",
            "sfx_cue": "pop_snap",
            "narration": "अब Infrastructure as Code से बिल्कुल वैसा ही Green v2.0 cluster बनता है, और users अभी भी Blue पर ही आराम से काम कर रहे हैं.",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "GREEN ENVIRONMENT",
                "headline_white": "Ye hai",
                "headline_accent": "Green.",
                "accent_color": "emerald",
                "card_eyebrow": "SAME ENVIRONMENT · IAC",
                "card_title": "Green · v2.0",
                "card_bullets": ["Same servers + same config", "Real users still safe on Blue"],
                "focus_node_ids": ["cicd", "green"],
                "active_edge_ids": ["e_cicd_green"],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": True},
                    "gate": {"visible": False},
                    "redis": {"visible": False},
                    "db": {"visible": False},
                    "blue": {"visible": True, "badge": "● LIVE"},
                },
            },
        },
        {
            "role": "proof",
            "sfx_cue": "success_chime",
            "narration": "Green को public करने से पहले internal test URL पर automated health checks और smoke tests चलते हैं.",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "TESTING GATE",
                "headline_white": "Pehle",
                "headline_accent": "testing.",
                "accent_color": "emerald",
                "card_eyebrow": "HEALTH CHECKS · SMOKE TESTS",
                "card_title": "Internal test URL",
                "card_bullets": ["✓ health checks · ✓ smoke tests", "✓ manual approval passed"],
                "focus_node_ids": ["gate", "green"],
                "active_edge_ids": ["e_cicd_green"],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": True, "checks": True},
                    "gate": {"visible": True, "badge": "APPROVED"},
                    "redis": {"visible": False},
                    "db": {"visible": False},
                    "blue": {"visible": True, "badge": "● LIVE"},
                },
            },
        },
        {
            "role": "solution",
            "sfx_cue": "success_chime",
            "narration": "सब पास होने के बाद Load Balancer एक झटके में 100% traffic Blue से Green पर switch कर देता है!",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "TRAFFIC SWITCH",
                "headline_white": "Blue →",
                "headline_accent": "Green.",
                "accent_color": "emerald",
                "card_eyebrow": "LOAD BALANCER",
                "card_title": "Switch · ek hi baar mein",
                "card_bullets": ["100% live traffic → Green v2.0 ⚡"],
                "focus_node_ids": ["lb", "green", "blue"],
                "active_edge_ids": ["e_lb_green"],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": True, "checks": True, "badge": "● LIVE"},
                    "gate": {"visible": True, "badge": "APPROVED"},
                    "redis": {"visible": True},
                    "db": {"visible": False},
                    "blue": {"visible": True, "badge": "STANDBY"},
                },
            },
        },
        {
            "role": "edge_case",
            "sfx_cue": "pop_snap",
            "narration": "Users log out भी नहीं होते, क्योंकि उनके sessions server memory में नहीं बल्कि Redis जैसे shared store में safe रहते हैं.",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "SHARED SESSIONS",
                "headline_white": "Users",
                "headline_accent": "logout nahi.",
                "accent_color": "rose",
                "card_eyebrow": "SHARED SESSION STORE",
                "card_title": "Redis · not server memory",
                "card_bullets": ["✓ Logged in · ✓ Session & cart safe"],
                "focus_node_ids": ["redis", "green"],
                "active_edge_ids": ["e_green_redis"],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": True, "checks": True, "badge": "● LIVE"},
                    "gate": {"visible": True, "badge": "APPROVED"},
                    "redis": {"visible": True, "badge": "CART SAFE"},
                    "db": {"visible": False},
                    "blue": {"visible": True, "badge": "STANDBY"},
                },
            },
        },
        {
            "role": "edge_case",
            "sfx_cue": "alert_ping",
            "narration": "और अगर Green में कोई bug निकले, तो Blue पहले से चालू है — तुरंत 1 second में rollback हो जाता है!",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "INSTANT ROLLBACK",
                "headline_white": "Bug? Wapas",
                "headline_accent": "Blue pe!",
                "accent_color": "amber",
                "card_eyebrow": "ZERO-DOWNTIME RECOVERY",
                "card_title": "Blue ready on standby",
                "card_bullets": ["Latency spike → 1-click rollback to Blue"],
                "focus_node_ids": ["green", "blue", "lb"],
                "active_edge_ids": ["e_lb_blue"],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": True, "bug": True},
                    "gate": {"visible": True, "badge": "APPROVED"},
                    "redis": {"visible": True},
                    "db": {"visible": True},
                    "blue": {"visible": True, "badge": "● ROLLBACK LIVE"},
                },
            },
        },
        {
            "role": "tradeoff",
            "sfx_cue": "pop_snap",
            "narration": "असली trade-off ये है कि database दोनों share करते हैं, इसलिए schema changes हमेशा backward compatible रखने होते हैं.",
            "visual_data": {
                "scene_mode": "world_cam",
                "hud_pill": "TRADE-OFF · DB",
                "headline_white": "Shared",
                "headline_accent": "database.",
                "accent_color": "purple",
                "card_eyebrow": "EXPAND AND CONTRACT",
                "card_title": "Backward compatible changes",
                "card_bullets": ["Add new column first, drop old later"],
                "focus_node_ids": ["db", "redis"],
                "active_edge_ids": ["e_redis_db"],
                "node_overrides": {
                    "cicd": {"visible": True},
                    "green": {"visible": True, "checks": True, "badge": "● LIVE"},
                    "gate": {"visible": True, "badge": "APPROVED"},
                    "redis": {"visible": True},
                    "db": {"visible": True},
                    "blue": {"visible": True, "badge": "STANDBY"},
                },
            },
        },
        {
            "role": "cta",
            "sfx_cue": "success_chime",
            "narration": "तुम्हारी company में deployment कैसे होता है? Comment में बताओ और इस reel को save करो!",
            "visual_data": {
                "scene_mode": "cta_poll",
                "hud_pill": "COMMENT KARO",
                "headline_white": "Tumhari team mein",
                "headline_accent": "kaise deploy?",
                "accent_color": "cyan",
                "option_a": "🔵 Blue-Green",
                "option_b": "🌙 Raat 2 baje",
                "footer_note": cta_sub,
            },
        },
    ]
    return {
        "topic": topic,
        "v2_engine": "spatial_isometric",
        "art_style": "v2_midnight_navy",
        "header_brand": (watermark or "@nanopro").strip(),
        "world_spec": world_spec,
        "scenes": _normalize_v2_scenes(scenes, tone, watermark, "spatial_isometric"),
    }


def _generate_v2_vector_llm(
    topic: str,
    tone: str,
    duration_mode: str,
    voice: str,
    watermark: str,
    audience_level: str,
    hook_style: str,
    cta_style: str,
    cta_keyword: str,
) -> Optional[Dict[str, Any]]:
    lang_instr = _language_rule(voice, topic)
    sc_guide = _scene_count_guidance(duration_mode, "vector_storyboard")
    cta_instr = (
        f"Final CTA button label MUST trigger Comment Keyword '{cta_keyword.strip().upper()}'."
        if cta_style == "comment_keyword" and cta_keyword.strip()
        else "Final CTA encourages Follow / Save."
    )

    prompt = f"""You are a viral technical explainer storyboard director (GyanaHut Tech style).
Design ONE clean, unified Vector Storyboard Reel JSON for topic: "{topic}"
Audience depth: {audience_level} | Hook style: {hook_style} | {cta_instr}
Target Pacing: {sc_guide}
{lang_instr}

CRITICAL DESIGN PHILOSOPHY (ZERO RANDOM LAYOUTS):
Every scene shares ONE dark navy stage card (`#0B1228`), top 10-segment story bar, pill tag, and punchy 2-line bilingual title (`headline_white` + `headline_accent`).
Inside each scene's `visual_data`, choose the most fitting `widget_type` from ONLY these 8 clean purpose-built widgets:
1. "chat_dialogue": `messages`: [{{"sender": "HR"|"YOU"|"DEV", "text": "...", "color": "cyan"|"amber"|"rose", "delay_p": 0.1..0.6}}], optional `stamp` (e.g. "REJECTED ✗")
2. "meter_verdict": `highlight_eyebrow`, `highlight_text`, `dialogue_sender`, `dialogue_text`, `bars`: [{{"label": "...", "pct": 0..100, "color": "emerald"|"rose", "right_label": "..."}}], `stamp`
3. "progressive_cards": `hero_icon` ("robot"|"server"|"db"|"code"|"cloud"|"api"|"shield"|"brain"), `hero_label`, `cards`: [{{"icon": "file"|"db"|"git"|"plug"|"cpu"|"shield"|"globe", "text": "short 3-5 words"}}] (2-4 cards revealing 1-by-1 with voice!), optional `footer_pill`
4. "spaghetti_wires": `left_node`: {{"icon":"robot"|"server"|"app", "label":"..."}}, `right_nodes`: [3-4 items {{"icon":"file"|"db"|"git"|"plug", "label":"...", "color":"cyan"|"amber"|"emerald"|"purple", "wire_tag":"custom code 1"}}]
5. "hub_radiate": `left_node`: {{"icon":"robot"|"app", "label":"..."}}, `hub_label` (max 10 chars e.g. "MCP"), `hub_sub` ("standard protocol"), `right_nodes`: [3-4 items {{"icon":"...", "label":"...", "color":"..."}}], `equation_line`, `footer_pill`
6. "analogy_tree": PAIR TWO CONSECUTIVE SCENES! Scene N uses a real-world analogy (e.g. Computer -> USB -> Keyboard/Pen drive/Phone) and Scene N+1 uses the EXACT SAME `analogy_tree` geometry mapped to the tech topic (e.g. AI App -> MCP -> Files/DB/GitHub)! Keys: `top_node`: {{"icon":"monitor"|"robot"|"server", "label":"..."}}, `hub_label`, `hub_color` ("cyan"|"amber"|"emerald"), `branches`: [3 items {{"icon":"keyboard"|"usb"|"phone"|"file"|"db"|"git"|"plug", "label":"...", "color":"cyan"|"amber"|"emerald", "check": true}}], `equation_line`, `footer_pill`
7. "split_verdict": `left_col`: {{"title":"...", "body":"...", "status":"cross"}}, `right_col`: {{"title":"...", "body":"...", "status":"check"}}, `equation_line`, `footer_pill`
8. "follow_cta": `pills`: [4 short words], `handle_title`: "{watermark}", `handle_sub`: "short tagline", `cta_button`: "+ Follow" or keyword CTA

Every `headline_white` and `headline_accent` MUST be max 2-4 crisp words. Keep text short and legible!
Return STRICT JSON:
{{
  "header_brand": "{(watermark or 'TECH').lstrip('@').upper()[:22]}",
  "category_tag": "AI · ENGINEERING",
  "scenes": [
    {{
      "scene_id": 1,
      "role": "hook|misconception|scenario|problem|solution|analogy|proof|cta",
      "sfx_cue": "punch_impact|pop_snap|alert_ping|success_chime|whoosh",
      "narration": "spoken sentence matching this scene's widget cues",
      "visual_data": {{
        "tag_pill": "INTERVIEW QUESTION",
        "headline_white": "white part",
        "headline_accent": "colored part",
        "accent_color": "amber|cyan|emerald|rose",
        "widget_type": "...",
        ...widget keys...
      }}
    }}
  ]
}}"""

    raw_text = ""
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    cand = str(getattr(res, "text", "") or "").strip()
                    if cand:
                        raw_text = cand
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if not raw_text and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                timeout=20,
            )
            raw_text = res.choices[0].message.content.strip() if res.choices else ""
        except Exception:
            pass

    parsed = _extract_json_block(raw_text)
    if not parsed or not isinstance(parsed.get("scenes"), list) or len(parsed["scenes"]) < 4:
        return None
    norm = _normalize_v2_scenes(parsed["scenes"], tone, watermark, "vector_storyboard")
    if len(norm) < 4:
        return None
    return {
        "topic": topic,
        "v2_engine": "vector_storyboard",
        "art_style": "v2_midnight_navy",
        "header_brand": str(parsed.get("header_brand") or watermark.lstrip("@").upper()),
        "category_tag": str(parsed.get("category_tag") or "TECH · ARCHITECTURE"),
        "scenes": norm,
    }


def _generate_v2_isometric_llm(
    topic: str,
    tone: str,
    duration_mode: str,
    voice: str,
    watermark: str,
    audience_level: str,
    hook_style: str,
    cta_style: str,
    cta_keyword: str,
) -> Optional[Dict[str, Any]]:
    lang_instr = _language_rule(voice, topic)
    sc_guide = _scene_count_guidance(duration_mode, "spatial_isometric")
    cta_note = f"Comment '{cta_keyword.strip().upper()}'" if cta_style == "comment_keyword" and cta_keyword.strip() else "Share with a developer!"

    prompt = f"""You are @thetechypenguin style 2.5D Spatial Isometric Technical Explainer Director.
Design ONE continuous 2.5D Isometric Architecture World + Camera-Fly Storyboard JSON for topic: "{topic}"
Audience: {audience_level} | Hook: {hook_style}
Target Scenes: {sc_guide}
{lang_instr}

ARCHITECTURE PARADIGM (CRITICAL FOR ZERO VISUAL COLLISION!):
1. First, define `world_spec` — a SINGLE continuous 1400x1400 virtual isometric map containing `nodes` (5 to 8 nodes spaced AT LEAST 320 units apart on the grid, e.g. `(220,260)`, `(580,260)`, `(940,260)`, `(580,620)`, `(940,620)`, `(940,960)`, `(580,960)` so NO 3D shapes or badges EVER overlap!), `edges` connecting them, and `zones`.
   - IMPORTANT FOR MULTI-LAYER DATA PIPELINES (e.g. L0 Raw / L1 Harmonized / L2 Curated, Bronze/Silver/Gold): create SEPARATE distinct nodes for major stages (e.g. `sf_l0` cylinder, `sf_l1` cluster/cylinder, `sf_l2` cylinder OR separate nodes spaced >=320 units apart) so the camera actually FLIES from L0 -> L1 -> L2 -> Reports/Alerts!
Allowed `kind` for nodes:
  - "factory_cube" (Producer / CI/CD / AWS DMS / Ingest / Reports & Alerts Engine)
  - "balancer_bar" (Load Balancer / API Gateway / Airflow & Lambda Orchestrator / Router)
  - "server_cluster" (3 isometric server racks — e.g. Transform Workers / dbt / Compute Cluster)
  - "cylinder_store" (Database / S3 Bucket / Redis / Snowflake L0/L1/L2 — supports optional `"schema_pills": ["tag1","tag2"]`)
  - "test_gate" (Approval / Health-Check / Data Quality Gate Archway)
Allowed node `color`: "blue", "emerald", "amber", "purple", "rose", "cyan".
2. Next, design `scenes` with STRICT mode-specific keys AND concise headlines (`headline_white` max 2-3 words, `headline_accent` max 2-3 words — NEVER exceed 28 chars combined!):
  - `"hook_chat"` (Scene 1): MUST include `"chat_channel"`, `"question_sender": "INTERVIEWER"`, `"question_text"` (the exact sharp scenario question), `"bad_answer"` (the common naive mistake), `"stamp": "REJECTED ✗"`.
  - `"split_compare"` (Optional Scene 2): MUST include `"left_card": {{"title":"...","sub":"...","color":"rose"|"blue"}}`, `"right_card": {{"title":"...","sub":"...","color":"emerald"|"cyan"}}`.
  - `"world_cam"` (Core Walkthrough Scenes): MUST include `"focus_node_ids"` (1 to 2 node IDs per scene for smooth pan/zoom), `"active_edge_ids"`, `"node_overrides"` (`{{"node_id": {{"visible": true/false, "badge": "● LIVE"|"CDC SYNC"|"● ACTIVE"|"L1 CLEAN", "checks": true/false, "bug": true/false}}}}`), `"card_eyebrow"`, `"card_title"` (max 5 words), `"card_bullets"` (max 2 short bullets!).
  - `"cta_poll"` (Final Scene): MUST include `"option_a"`, `"option_b"`, `"footer_note": "{cta_note}".

Return STRICT JSON:
{{
  "world_spec": {{
    "nodes": [{{"id":"n1","kind":"cylinder_store","label":"Oracle DB","sublabel":"Banking OLTP","x":220,"y":260,"color":"amber"}}],
    "edges": [{{"id":"e1","from":"n1","to":"n2","color":"cyan","style":"packets"}}],
    "zones": [{{"label":"AWS INGESTION","x":420,"y":150,"w":460,"h":300,"color":"cyan"}}]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "role": "hook|solution|scenario|proof|edge_case|tradeoff|cta",
      "sfx_cue": "punch_impact|pop_snap|alert_ping|success_chime|whoosh",
      "narration": "...",
      "visual_data": {{
        "scene_mode": "hook_chat|split_compare|world_cam|cta_poll",
        "hud_pill": "SYSTEM INTERVIEW",
        "headline_white": "Zero Downtime",
        "headline_accent": "Pipeline?",
        "accent_color": "cyan|emerald|amber|rose|purple"
      }}
    }}
  ]
}}"""

    raw_text = ""
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    cand = str(getattr(res, "text", "") or "").strip()
                    if cand:
                        raw_text = cand
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if not raw_text and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                timeout=22,
            )
            raw_text = res.choices[0].message.content.strip() if res.choices else ""
        except Exception:
            pass

    parsed = _extract_json_block(raw_text)
    ws = (parsed or {}).get("world_spec") or {}
    if not parsed or not isinstance(ws.get("nodes"), list) or len(ws["nodes"]) < 3 or not isinstance(parsed.get("scenes"), list) or len(parsed["scenes"]) < 4:
        return None
    norm = _normalize_v2_scenes(parsed["scenes"], tone, watermark, "spatial_isometric", topic=topic)
    if len(norm) < 4:
        return None
    ws_clean = _sanitize_isometric_world_spec(ws)
    return {
        "topic": topic,
        "v2_engine": "spatial_isometric",
        "art_style": "v2_midnight_navy",
        "header_brand": (watermark or DEFAULT_WATERMARK).strip(),
        "world_spec": ws_clean,
        "scenes": norm,
    }


def _fallback_live_ide(topic: str, watermark: str, tone: str, cta_style: str, cta_keyword: str) -> Dict[str, Any]:
    clean_topic = (topic.strip() or "SQL JOIN & N+1 Query Optimization")[:54]
    low = clean_topic.lower()
    is_sql = any(k in low for k in ("sql", "join", "dense_rank", "rank", "window", "cte", "query", "select", "index", "snowflake"))
    cta_note = f"Comment '{cta_keyword.strip().upper()}' 👇" if cta_style == "comment_keyword" and cta_keyword.strip() else "Save this code pattern!"

    if is_sql:
        scenes = [
            {
                "role": "hook",
                "sfx_cue": "punch_impact",
                "narration": f"ये SQL query production में दिखती innocent है, लेकिन {clean_topic[:28]} पर database को 10x slow कर देती है.",
                "visual_data": {
                    "hud_pill": "SQL CODE AUDIT",
                    "headline_white": "Slow Query",
                    "headline_accent": "Exposed.",
                    "accent_color": "rose",
                    "language": "sql",
                    "file_name": "analytics_slow.sql",
                    "tab_secondary": "explain_plan.log",
                    "code_lines": [
                        "SELECT u.id, u.name, o.total",
                        "FROM users u",
                        "JOIN orders o ON LOWER(o.email) = LOWER(u.email)",
                        "WHERE o.created_at >= '2026-01-01';",
                    ],
                    "focus_lines": [3],
                    "line_status": "error",
                    "diff_marks": {"3": "-"},
                    "ide_steps": [{"line": 3, "p": 0.14, "click": True}, {"target": "run_btn", "p": 0.45, "click": True}],
                    "callout": {"title": "⚠️ INDEX BYPASS", "text": "Function LOWER() breaks B-Tree index!", "line": 3, "color": "rose", "delay_p": 0.22},
                    "output_drawer": {
                        "mode": "terminal",
                        "title": "EXPLAIN ANALYZE",
                        "metric": "Seq Scan · 1,840ms",
                        "metric_color": "rose",
                        "open_p": 0.48,
                        "lines": [
                            "Seq Scan on orders (cost=0.00..482910.00)",
                            "✗ Dropped Index idx_orders_email -> full table scan!",
                            "✗ Execution Time: 1,840 ms (DB CPU 92%)",
                        ],
                    },
                },
            },
            {
                "role": "solution",
                "sfx_cue": "success_chime",
                "narration": "एक छोटा fix: indexed column पर functional wrapper हटाकर direct indexed key या expression index use करो.",
                "visual_data": {
                    "hud_pill": "LIVE IDE FIX",
                    "headline_white": "Indexed",
                    "headline_accent": "Join Fix.",
                    "accent_color": "emerald",
                    "language": "sql",
                    "file_name": "analytics_fast.sql",
                    "tab_secondary": "explain_plan.log",
                    "code_lines": [
                        "SELECT u.id, u.name, o.total,",
                        "       DENSE_RANK() OVER (ORDER BY o.total DESC) AS rnk",
                        "FROM users u",
                        "INNER JOIN orders o ON o.user_id = u.id",
                        "WHERE o.created_at >= '2026-01-01';",
                    ],
                    "focus_lines": [2, 4],
                    "line_status": "active",
                    "diff_marks": {"4": "+"},
                    "ide_steps": [{"line": 4, "p": 0.14, "click": True}, {"target": "run_btn", "p": 0.40, "click": True}],
                    "callout": {"title": "⚡ INDEX SEEK", "text": "Direct FK join + single-pass window rank", "line": 4, "color": "emerald", "delay_p": 0.20},
                    "output_drawer": {
                        "mode": "sql_table",
                        "title": "LIVE QUERY RESULT",
                        "metric": "3 rows · 1.2ms ⚡",
                        "metric_color": "emerald",
                        "open_p": 0.44,
                        "table": {
                            "headers": ["id", "name", "total", "rnk"],
                            "rows": [["104", "Aarav", "$940", "1"], ["219", "Diya", "$780", "2"], ["308", "Kabir", "$620", "3"]],
                        },
                    },
                },
            },
            {
                "role": "cta",
                "sfx_cue": "success_chime",
                "narration": f"1,840ms से सीधा 1.2ms! Next time query slow हो तो पहले EXPLAIN plan देखो — {cta_note}",
                "visual_data": {
                    "hud_pill": "BENCHMARK PROOF",
                    "headline_white": "1,500x",
                    "headline_accent": "Faster Query!",
                    "accent_color": "cyan",
                    "language": "sql",
                    "file_name": "benchmark.sql",
                    "tab_secondary": "results.csv",
                    "code_lines": [
                        "-- Before: LOWER(email) -> Seq Scan  (1,840 ms)",
                        "-- After : o.user_id = u.id -> Seek  (1.2 ms)",
                        "EXPLAIN ANALYZE SELECT ... LIMIT 10;",
                    ],
                    "focus_lines": [2],
                    "line_status": "active",
                    "ide_steps": [{"line": 2, "p": 0.15, "click": True}, {"target": "run_btn", "p": 0.42, "click": True}],
                    "callout": {"title": "🚀 VERIFIED", "text": "Always inspect Index Scan vs Seq Scan!", "line": 2, "color": "cyan", "delay_p": 0.20},
                    "output_drawer": {
                        "mode": "terminal",
                        "title": "FINAL BENCHMARK",
                        "metric": "99.9% Latency Drop",
                        "metric_color": "emerald",
                        "open_p": 0.44,
                        "lines": [
                            "✓ Before: 1,840.0 ms (Full Table Scan)",
                            "✓ After :     1.2 ms (B-Tree Index Seek)",
                        ],
                    },
                    "footer_pill": cta_note,
                },
            },
        ]
    else:
        scenes = [
            {
                "role": "hook",
                "sfx_cue": "punch_impact",
                "narration": f"Line 2 को ध्यान से देखो — ये innocent Python loop production में DB को 1,000 queries से crash कर रहा है!",
                "visual_data": {
                    "hud_pill": "N+1 BUG CATCH",
                    "headline_white": "Look at",
                    "headline_accent": "Line 2.",
                    "accent_color": "rose",
                    "language": "python",
                    "file_name": "orders_api.py",
                    "tab_secondary": "db_profiler.log",
                    "code_lines": [
                        "users = db.fetch_active_users()  # 1 query",
                        "for user in users:",
                        "    orders = db.fetch_orders(user.id)  # +1000!",
                        "    payload.append((user, orders))",
                    ],
                    "focus_lines": [2, 3],
                    "line_status": "error",
                    "diff_marks": {"3": "-"},
                    "ide_steps": [{"line": 3, "p": 0.12, "click": True}, {"target": "run_btn", "p": 0.44, "click": True}],
                    "callout": {"title": "🚨 N+1 QUERY LEAK", "text": "1,000 users = 1,001 DB roundtrips!", "line": 3, "color": "rose", "delay_p": 0.20},
                    "output_drawer": {
                        "mode": "terminal",
                        "title": "LIVE TRACE & PROFILER",
                        "metric": "1,001 queries · 940ms",
                        "metric_color": "rose",
                        "open_p": 0.46,
                        "lines": [
                            "$ python orders_api.py",
                            "✗ SQL Count: 1,001 roundtrips executed",
                            "✗ TimeoutWarning: DB Pool exhausted (940ms)",
                        ],
                    },
                },
            },
            {
                "role": "solution",
                "sfx_cue": "success_chime",
                "narration": "Fix super clean है: loop के अंदर query चलाने की बजाय single batch IN clause या eager JOIN use करो.",
                "visual_data": {
                    "hud_pill": "BATCH FIX",
                    "headline_white": "Single Batch",
                    "headline_accent": "Query Fix.",
                    "accent_color": "emerald",
                    "language": "python",
                    "file_name": "orders_fixed.py",
                    "tab_secondary": "db_profiler.log",
                    "code_lines": [
                        "users = db.fetch_active_users()",
                        "user_ids = [u.id for u in users]",
                        "orders_map = db.fetch_orders_batch(user_ids)",
                        "payload = [(u, orders_map[u.id]) for u in users]",
                    ],
                    "focus_lines": [3],
                    "line_status": "active",
                    "diff_marks": {"3": "+"},
                    "ide_steps": [{"line": 3, "p": 0.14, "click": True}, {"target": "run_btn", "p": 0.40, "click": True}],
                    "callout": {"title": "⚡ 2 QUERIES TOTAL", "text": "SELECT ... WHERE user_id IN (...)", "line": 3, "color": "emerald", "delay_p": 0.20},
                    "output_drawer": {
                        "mode": "terminal",
                        "title": "PROFILER OUTPUT",
                        "metric": "2 queries · 8ms ⚡",
                        "metric_color": "emerald",
                        "open_p": 0.44,
                        "lines": [
                            "$ python orders_fixed.py",
                            "✓ SQL Count: 2 queries total (117x fewer!)",
                            "✓ Response Time: 8.1 ms • Pool healthy",
                        ],
                    },
                },
            },
            {
                "role": "cta",
                "sfx_cue": "success_chime",
                "narration": f"940ms सीधा 8ms पर! Production PR review में loop के अंदर DB call हमेशा flag करो — {cta_note}",
                "visual_data": {
                    "hud_pill": "CODE TAKEAWAY",
                    "headline_white": "940ms →",
                    "headline_accent": "8.1ms ⚡",
                    "accent_color": "cyan",
                    "language": "python",
                    "file_name": "benchmark.py",
                    "tab_secondary": "metrics.json",
                    "code_lines": [
                        "# Rule: NEVER query inside a loop",
                        "assert sql_queries <= 2",
                        "print(f'Speedup: {940 / 8.1:.0f}x faster!')",
                    ],
                    "focus_lines": [2],
                    "line_status": "active",
                    "ide_steps": [{"line": 2, "p": 0.14, "click": True}, {"target": "run_btn", "p": 0.38, "click": True}],
                    "callout": {"title": "💡 PRO RULE", "text": "Always prefetch or batch JOIN!", "line": 2, "color": "amber", "delay_p": 0.20},
                    "output_drawer": {
                        "mode": "terminal",
                        "title": "BENCHMARK SUMMARY",
                        "metric": "116x Speedup",
                        "metric_color": "emerald",
                        "open_p": 0.42,
                        "lines": [
                            "✓ N+1 Loop : 940.0 ms (1,001 queries)",
                            "✓ Batch IN :   8.1 ms (2 queries)",
                        ],
                    },
                    "footer_pill": cta_note,
                },
            },
        ]

    # Expand to 6 cohesive scenes by adding scenario/edge_case/proof beats cleanly when needed
    if len(scenes) < 6:
        extra_mid = {
            "role": "edge_case",
            "sfx_cue": "pop_snap",
            "narration": "साथ ही memory spike रोकने के लिए batch chunks (size=500) और connection timeout guard जरूर लगाओ.",
            "visual_data": {
                "hud_pill": "PRODUCTION GUARD",
                "headline_white": "Chunking +",
                "headline_accent": "Safe Guard.",
                "accent_color": "amber",
                "language": "sql" if is_sql else "python",
                "file_name": "guard.sql" if is_sql else "guard.py",
                "tab_secondary": "tests.py",
                "code_lines": (
                    ["SET statement_timeout = '500ms';", "CREATE INDEX CONCURRENTLY idx_orders_uid", "ON orders(user_id, created_at);"]
                    if is_sql else
                    ["for batch in chunked(user_ids, size=500):", "    orders_map.update(db.fetch_orders_batch(batch))"]
                ),
                "focus_lines": [1, 2],
                "line_status": "active",
                "ide_steps": [{"line": 1, "p": 0.14, "click": True}, {"target": "run_btn", "p": 0.42, "click": True}],
                "callout": {"title": "🛡️ ZERO LOCKING", "text": "Prevents huge IN-lists & locks", "line": 2, "color": "amber", "delay_p": 0.22},
                "output_drawer": {
                    "mode": "terminal",
                    "title": "TEST SUITE",
                    "metric": "All 12 checks PASS",
                    "metric_color": "emerald",
                    "open_p": 0.45,
                    "lines": ["✓ No table locks detected", "✓ Memory bounded under 32MB"],
                },
            },
        }
        scenes.insert(2, extra_mid)

    return {
        "topic": topic,
        "v2_engine": "live_ide",
        "art_style": "v2_midnight_navy",
        "header_brand": watermark,
        "scenes": _normalize_v2_scenes(scenes, tone, watermark, "live_ide", topic=topic),
    }


def _fallback_blueprint_whiteboard(topic: str, watermark: str, tone: str, cta_style: str, cta_keyword: str) -> Dict[str, Any]:
    clean_topic = (topic.strip() or "Rate Limiter & API Gateway System Design")[:54]
    short_title = " ".join(clean_topic.split()[:3]) or "System"
    cta_note = f"Comment '{cta_keyword.strip().upper()}' 👇" if cta_style == "comment_keyword" and cta_keyword.strip() else "Save this blueprint!"

    scenes = [
        {
            "role": "hook",
            "sfx_cue": "punch_impact",
            "narration": f"अगर अचानक 100k requests/sec आए, तो बिना {short_title} blueprint के तुम्हारा backend 5 सेकंड में crash हो जाएगा!",
            "visual_data": {
                "hud_pill": "SYSTEM DILEMMA",
                "headline_white": "100k RPS Spike?",
                "headline_accent": "Backend Crashes!",
                "accent_color": "rose",
                "diagram_nodes": [
                    {"id": "cli", "kind": "box", "label": "100k Users", "sublabel": "Traffic Spike", "x": 220, "y": 210, "w": 240, "h": 115, "color": "amber", "dp": 0.05},
                    {"id": "api", "kind": "box", "label": "Single API", "sublabel": "Overloaded!", "x": 500, "y": 405, "w": 240, "h": 115, "color": "rose", "dp": 0.20},
                    {"id": "db", "kind": "cylinder", "label": "Primary DB", "sublabel": "CPU 100% ✗", "x": 770, "y": 600, "w": 235, "h": 125, "color": "rose", "dp": 0.35},
                ],
                "diagram_edges": [
                    {"from": "cli", "to": "api", "label": "flood", "color": "rose", "dp": 0.15},
                    {"from": "api", "to": "db", "label": "locks", "color": "rose", "dp": 0.30},
                ],
                "sticky_notes": [
                    {"title": "⚠️ NAIVE FLUSH", "text": "No queue or guard = instant 502 outage!", "color": "rose", "x_pct": 6, "y_pct": 72, "dp": 0.30},
                ],
            },
        },
        {
            "role": "solution",
            "sfx_cue": "pop_snap",
            "narration": f"इसलिए ByteByteGo style blueprint में सबसे आगे Gateway + {short_title} guard रखा जाता है, जो extra load filter करता है.",
            "visual_data": {
                "hud_pill": "BLUEPRINT LAYER 1",
                "headline_white": "Clean Edge",
                "headline_accent": "Architecture.",
                "accent_color": "cyan",
                "blueprint_zones": [{"label": "EDGE PROTECTION ZONE", "x": 335, "y": 140, "w": 360, "h": 410, "color": "cyan"}],
                "diagram_nodes": [
                    {"id": "u", "kind": "box", "label": "Clients", "sublabel": "Mobile / Web", "x": 145, "y": 325, "w": 185, "h": 110, "color": "white", "dp": 0.05},
                    {"id": "gw", "kind": "diamond", "label": "Gateway", "sublabel": "Auth + Limit", "x": 500, "y": 325, "w": 210, "h": 140, "color": "cyan", "dp": 0.18},
                    {"id": "rd", "kind": "cylinder", "label": "Redis State", "sublabel": "O(1) Counter", "x": 500, "y": 640, "w": 235, "h": 118, "color": "amber", "dp": 0.34},
                    {"id": "svc", "kind": "box", "label": "Core Service", "sublabel": "Protected", "x": 855, "y": 325, "w": 195, "h": 112, "color": "emerald", "dp": 0.48},
                ],
                "diagram_edges": [
                    {"from": "u", "to": "gw", "label": "HTTPS", "color": "cyan", "dp": 0.14},
                    {"from": "gw", "to": "rd", "label": "check", "color": "amber", "dashed": True, "dp": 0.30},
                    {"from": "gw", "to": "svc", "label": "allow ✓", "color": "emerald", "dp": 0.44},
                ],
                "sticky_notes": [
                    {"title": "✏️ MARKER TIP", "text": "In-memory Redis keeps latency < 1ms", "color": "amber", "x_pct": 6, "y_pct": 74, "dp": 0.48},
                ],
            },
        },
        {
            "role": "analogy",
            "sfx_cue": "whoosh",
            "narration": "भारी traffic को async Queue में buffer करके Workers आराम से process करते हैं — ताकि database कभी choke न हो.",
            "visual_data": {
                "hud_pill": "ASYNC BUFFERING",
                "headline_white": "Queue Absorbs",
                "headline_accent": "Traffic Burst.",
                "accent_color": "emerald",
                "diagram_nodes": [
                    {"id": "svc", "kind": "box", "label": "API Tier", "sublabel": "Fast Ack 202", "x": 195, "y": 240, "w": 225, "h": 112, "color": "cyan", "dp": 0.06},
                    {"id": "q", "kind": "queue", "label": "Event Queue", "sublabel": "Kafka / SQS", "x": 520, "y": 280, "w": 245, "h": 112, "color": "amber", "dp": 0.22},
                    {"id": "w", "kind": "box", "label": "Workers", "sublabel": "Steady Rate", "x": 815, "y": 405, "w": 220, "h": 112, "color": "emerald", "dp": 0.38},
                    {"id": "db", "kind": "cylinder", "label": "Storage DB", "sublabel": "Safe Writes", "x": 775, "y": 645, "w": 225, "h": 118, "color": "purple", "dp": 0.52},
                ],
                "diagram_edges": [
                    {"from": "svc", "to": "q", "label": "push", "color": "cyan", "dp": 0.16},
                    {"from": "q", "to": "w", "label": "pull", "color": "amber", "dp": 0.32},
                    {"from": "w", "to": "db", "label": "batch", "color": "emerald", "dp": 0.48},
                ],
                "sticky_notes": [
                    {"title": "📌 WHY QUEUES WIN", "text": "Decouples peak burst from DB writes!", "color": "emerald", "x_pct": 6, "y_pct": 70, "dp": 0.46},
                ],
            },
        },
        {
            "role": "cta",
            "sfx_cue": "success_chime",
            "narration": f"बस यही 3 whiteboard boxes हर scalable system interview में काम आते हैं — {cta_note}",
            "visual_data": {
                "hud_pill": "WHITEBOARD CHECKLIST",
                "headline_white": "3-Layer",
                "headline_accent": "Scale Pattern.",
                "accent_color": "amber",
                "diagram_nodes": [
                    {"id": "l1", "kind": "box", "label": "1. Edge Guard", "sublabel": "Gateway + Cache", "x": 225, "y": 215, "w": 245, "h": 115, "color": "cyan", "dp": 0.08},
                    {"id": "l2", "kind": "queue", "label": "2. Buffer", "sublabel": "Async Queue", "x": 515, "y": 405, "w": 235, "h": 115, "color": "amber", "dp": 0.26},
                    {"id": "l3", "kind": "cylinder", "label": "3. Durable DB", "sublabel": "Partitioned", "x": 780, "y": 595, "w": 240, "h": 120, "color": "emerald", "dp": 0.44},
                ],
                "diagram_edges": [
                    {"from": "l1", "to": "l2", "label": "filter", "color": "cyan", "dp": 0.20},
                    {"from": "l2", "to": "l3", "label": "flush", "color": "emerald", "dp": 0.38},
                ],
                "sticky_notes": [
                    {"title": "✅ INTERVIEW GOLD", "text": "Always draw Cache -> Queue -> DB!", "color": "amber", "x_pct": 6, "y_pct": 72, "dp": 0.48},
                ],
                "footer_pill": cta_note,
            },
        },
    ]

    return {
        "topic": topic,
        "v2_engine": "blueprint_whiteboard",
        "art_style": "v2_midnight_navy",
        "header_brand": watermark,
        "scenes": _normalize_v2_scenes(scenes, tone, watermark, "blueprint_whiteboard", topic=topic),
    }


def _generate_v3_ide_llm(
    topic: str,
    tone: str,
    duration_mode: str,
    voice: str,
    watermark: str,
    audience_level: str,
    hook_style: str,
    cta_style: str,
    cta_keyword: str,
) -> Optional[Dict[str, Any]]:
    lang_instr = _language_rule(voice, topic)
    sc_guide = _scene_count_guidance(duration_mode, "live_ide")
    cta_note = f"Comment '{cta_keyword.strip().upper()}'" if cta_style == "comment_keyword" and cta_keyword.strip() else "Save this code tip!"

    prompt = f"""You are Studio V3 Live IDE & SQL/Python Simulator Director.
Design ONE cohesive coding explainer reel JSON for topic: "{topic}"
Audience: {audience_level} | Hook: {hook_style} | Final CTA: {cta_note}
Target Scenes: {sc_guide}
{lang_instr}

EVERY scene renders inside a realistic dark IDE (VS Code / DataGrip) with syntax highlighting, animated mouse click ripple, a floating callout bubble, and a live output drawer.
For EVERY scene's `visual_data`, provide:
- `hud_pill`, `headline_white` (max 3 words), `headline_accent` (max 3 words), `accent_color` ("cyan"|"emerald"|"amber"|"rose")
- `language`: "python" or "sql"
- `file_name`: e.g. "query.sql" or "app.py", `tab_secondary`
- `code_lines`: 4 to 8 realistic, crisp lines of actual code/SQL for that beat (never truncated placeholders!)
- `focus_lines`: [1-based line numbers] highlighted for this scene
- `line_status`: "error" for bug/slow scenes, "active" for fix/proof scenes
- `diff_marks`: optional {{"2": "-", "3": "+"}}
- `ide_steps`: [{{"line": 2, "p": 0.14, "click": true}}, {{"target": "run_btn", "p": 0.42, "click": true}}]
- `callout`: {{"title": "⚠️ BUG"|"⚡ FIX", "text": "crisp <55 char note", "line": 2, "color": "rose"|"emerald"|"amber", "delay_p": 0.22}}
- `output_drawer`: EITHER
  {{"mode": "sql_table", "title": "QUERY RESULT", "metric": "3 rows · 1.2ms", "metric_color": "emerald", "open_p": 0.44, "table": {{"headers": [...], "rows": [[...],[...]]}}}}
  OR
  {{"mode": "terminal", "title": "EXECUTION TRACE", "metric": "940ms -> 8ms", "metric_color": "rose"|"emerald", "open_p": 0.44, "lines": ["$ ...", "✓ ..."]}}

Return STRICT JSON:
{{ "scenes": [ {{ "scene_id": 1, "role": "hook|problem|solution|edge_case|proof|cta", "sfx_cue": "punch_impact|key_tick|alert_ping|success_chime", "narration": "...", "visual_data": {{...}} }} ] }}"""

    raw_text = ""
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    cand = str(getattr(res, "text", "") or "").strip()
                    if cand:
                        raw_text = cand
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if not raw_text and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.35,
                timeout=20,
            )
            raw_text = res.choices[0].message.content.strip() if res.choices else ""
        except Exception:
            pass

    parsed = _extract_json_block(raw_text)
    if not parsed or not isinstance(parsed.get("scenes"), list) or len(parsed["scenes"]) < 3:
        return None
    norm = _normalize_v2_scenes(parsed["scenes"], tone, watermark, "live_ide", topic=topic)
    if len(norm) < 3:
        return None
    return {
        "topic": topic,
        "v2_engine": "live_ide",
        "art_style": "v2_midnight_navy",
        "header_brand": watermark,
        "scenes": norm,
    }


def _generate_v4_whiteboard_llm(
    topic: str,
    tone: str,
    duration_mode: str,
    voice: str,
    watermark: str,
    audience_level: str,
    hook_style: str,
    cta_style: str,
    cta_keyword: str,
) -> Optional[Dict[str, Any]]:
    lang_instr = _language_rule(voice, topic)
    sc_guide = _scene_count_guidance(duration_mode, "blueprint_whiteboard")
    cta_note = f"Comment '{cta_keyword.strip().upper()}'" if cta_style == "comment_keyword" and cta_keyword.strip() else "Save this blueprint!"

    prompt = f"""You are Studio V4 Blueprint Whiteboard Director (ByteByteGo / Excalidraw dark blueprint grid style).
Design ONE clean whiteboard diagram reel JSON for topic: "{topic}"
Audience: {audience_level} | Hook: {hook_style} | Final CTA: {cta_note}
Target Scenes: {sc_guide}
{lang_instr}

Each scene draws hand-drawn marker shapes on a 1000x1000 virtual blueprint canvas (nodes spaced >=260 units apart inside x:150..850, y:160..840 so ZERO shapes overlap!) plus sticky callout bubbles.
For EVERY scene's `visual_data`, provide:
- `hud_pill`, `headline_white` (max 3 words), `headline_accent` (max 3 words), `accent_color` ("cyan"|"emerald"|"amber"|"rose"|"purple")
- `blueprint_zones`: optional [{{"label":"ZONE NAME","x":120,"y":180,"w":420,"h":400,"color":"cyan"}}]
- `diagram_nodes`: 2 to 5 nodes: {{"id":"n1","kind":"box"|"cylinder"|"diamond"|"queue","label":"short name","sublabel":"detail","x":220,"y":420,"w":220,"h":110,"color":"cyan"|"emerald"|"amber"|"rose"|"purple","dp":0.06..0.5}}
- `diagram_edges`: 1 to 5 arrows: {{"from":"n1","to":"n2","label":"short tag","color":"cyan"|"amber"|"emerald"|"rose","dashed":false,"dp":0.16..0.6}}
- `sticky_notes`: 1 to 2 sticky callout bubbles placed away from main nodes: {{"title":"📌 KEY RULE","text":"short 5-8 word insight","color":"amber"|"emerald"|"rose","x_pct":8..62,"y_pct":12..72,"dp":0.45..0.7}}
- Optional `footer_pill` on the CTA scene.

Return STRICT JSON:
{{ "scenes": [ {{ "scene_id": 1, "role": "hook|problem|solution|analogy|proof|cta", "sfx_cue": "punch_impact|pop_snap|whoosh|success_chime", "narration": "...", "visual_data": {{...}} }} ] }}"""

    raw_text = ""
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    cand = str(getattr(res, "text", "") or "").strip()
                    if cand:
                        raw_text = cand
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if not raw_text and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                timeout=20,
            )
            raw_text = res.choices[0].message.content.strip() if res.choices else ""
        except Exception:
            pass

    parsed = _extract_json_block(raw_text)
    if not parsed or not isinstance(parsed.get("scenes"), list) or len(parsed["scenes"]) < 3:
        return None
    norm = _normalize_v2_scenes(parsed["scenes"], tone, watermark, "blueprint_whiteboard", topic=topic)
    if len(norm) < 3:
        return None
    return {
        "topic": topic,
        "v2_engine": "blueprint_whiteboard",
        "art_style": "v2_midnight_navy",
        "header_brand": watermark,
        "scenes": norm,
    }


def _build_dc_narration(
    kind: str,
    dept_name: str,
    spec_title: str,
    topic: str,
    voice: str,
    cta_note: str = "",
) -> str:
    v = str(voice or "").lower()
    t_low = str(topic or "").lower()
    short_top = " ".join(str(topic or "").strip().split()[:6])
    if "mr-in" in v or "marathi" in t_low:
        if kind == "fast_intro":
            return f"Data Center मधल्या {dept_name} मधल्या {spec_title} कडे बघा — {short_top} थेट ३ सेकंदात सुरू करूया!"
        if kind == "campus":
            return f"चला आज आपल्या Enterprise Data Center मध्ये जाऊया आणि थेट {dept_name} department मध्ये entry करूया."
        if kind == "desk":
            return f"इथे आपल्या {spec_title} यांच्या workstation वर बघूया की {short_top} हे काम प्रत्यक्षात कसं चालतं!"
        return f"अशा प्रकारे {dept_name} मधील {spec_title} काम करतात — {cta_note}"
    if "hi-in" in v or "hindi" in t_low or "hinglish" in t_low:
        if kind == "fast_intro":
            return f"Data Center के {dept_name} में {spec_title} के desk पर चलते हैं — आइए {short_top} सीधे शुरू करते हैं!"
        if kind == "campus":
            return f"चलो आज Enterprise Data Center के अंदर चलकर सीधे {dept_name} department में fly करते हैं."
        if kind == "desk":
            return f"ये हैं हमारे {spec_title} — आइए समझते हैं इस desk पर {short_top} का काम असल में कैसे होता है!"
        return f"इसी तरह {dept_name} के {spec_title} काम करते हैं — {cta_note}"
    if kind == "fast_intro":
        return f"Flying straight into our Data Center's {dept_name} desk ({spec_title}) — let's break down {short_top}!"
    if kind == "campus":
        return f"Welcome inside our Enterprise Data Center — let's fly straight into the {dept_name} department."
    if kind == "desk":
        return f"Meet our {spec_title} at their console — let's trace step by step how {short_top} works in production!"
    return f"And that is how the {spec_title} in {dept_name} runs production — {cta_note}"


def _generate_v5_datacenter_hybrid(
    topic: str,
    tone: str,
    duration_mode: str,
    voice: str,
    watermark: str,
    audience_level: str,
    hook_style: str,
    cta_style: str,
    cta_keyword: str,
    dc_travel_mode: str = "auto",
) -> Dict[str, Any]:
    """
    Fast Option B Hybrid Cinema Hand-off for Studio V5 Data Center & IT Park:
      Scene 1: Fast 1-scene Campus -> Dept -> Engineer Desk arrival (`campus_to_desk`)
      Scenes 2..N-1: Immediate Main Topic Deep-Dive (V3 Live IDE / V4 Blueprint Whiteboard / V2 Spatial Isometric)
      Scene N: Data Center Campus Zoom-Out + CTA
    """
    from core.studio_v5_datacenter import match_datacenter_specialist

    match = match_datacenter_specialist(topic, preferred_travel=dc_travel_mode)
    dept = match["department"]
    spec = match["specialist"]
    travel = match["travel_mode"]
    handoff = spec.get("handoff", "blueprint_whiteboard")
    cta_note = f"Comment '{cta_keyword.strip().upper()}' 👇" if cta_style == "comment_keyword" and cta_keyword.strip() else "Comment next department!"

    # Generate deep-dive body scenes using the matched specialist engine
    if handoff == "live_ide":
        inner_tl = _generate_v3_ide_llm(topic, tone, duration_mode, voice, watermark, audience_level, hook_style, cta_style, cta_keyword)
        if inner_tl is None:
            inner_tl = _fallback_live_ide(topic, watermark, tone, cta_style, cta_keyword)
    elif handoff == "spatial_isometric":
        inner_tl = _generate_v2_isometric_llm(topic, tone, duration_mode, voice, watermark, audience_level, hook_style, cta_style, cta_keyword)
        if inner_tl is None:
            inner_tl = _fallback_spatial_isometric(topic, watermark, tone, cta_style, cta_keyword)
    else:
        inner_tl = _generate_v4_whiteboard_llm(topic, tone, duration_mode, voice, watermark, audience_level, hook_style, cta_style, cta_keyword)
        if inner_tl is None:
            inner_tl = _fallback_blueprint_whiteboard(topic, watermark, tone, cta_style, cta_keyword)

    inner_scenes = list(inner_tl.get("scenes") or [])
    # Skip only generic chat interview hooks (`hook_chat`) & trailing CTA; keep real problem hooks so content starts at Scene 2!
    start_i = 1 if (inner_scenes and (inner_scenes[0].get("visual_data") or {}).get("scene_mode") == "hook_chat") else 0
    if len(inner_scenes) - start_i >= 3:
        body_scenes = inner_scenes[start_i:-1]
    else:
        body_scenes = inner_scenes[start_i:]

    fast_txt = _build_dc_narration("fast_intro", dept["full"], spec["title"], topic, voice, cta_note=cta_note)

    sc_intro = {
        "scene_id": 1,
        "role": "hook",
        "scene_tone": get_tone_profile(tone, role="hook", idx=0).get("key") or "auto_2026_director",
        "sfx_cue": "whoosh",
        "narration": fast_txt,
        "visual_type": "v5_datacenter_park",
        "routed_engine": f"Studio V5 Fast Fly-In ({travel.title()} → {spec['short']})",
        "art_style": "v2_midnight_navy",
        "backdrop": "v2_clean_canvas",
        "transition": "smooth_fade",
        "text_fx": "clean_hud",
        "visual_data": {
            "dc_mode": "campus_to_desk",
            "travel_mode": travel,
            "department": dept,
            "specialist": spec,
            "departments": match.get("departments"),
            "specialists": match.get("specialists"),
            "engineer_x": match["engineer_x"],
            "engineer_y": match["engineer_y"],
            "hud_pill": f"DATA CENTER · {dept['name']}",
            "headline_white": spec["short"],
            "headline_accent": "Live Desk.",
            "accent_color": dept["color"],
            "dialogue_text": fast_txt[:135],
            "watermark": watermark,
        },
        "actions": [],
        "_disable_actions_overlay": True,
        "_disable_camera_actions": True,
    }

    sc_outro = {
        "scene_id": 99,
        "role": "cta",
        "scene_tone": get_tone_profile(tone, role="cta", idx=len(body_scenes) + 1).get("key") or "whiteboard_analogy",
        "sfx_cue": "success_chime",
        "narration": _build_dc_narration("outro", dept["full"], spec["title"], topic, voice, cta_note=cta_note),
        "visual_type": "v5_datacenter_park",
        "routed_engine": "Studio V5 Data Center Zoom-Out",
        "art_style": "v2_midnight_navy",
        "backdrop": "v2_clean_canvas",
        "transition": "smooth_fade",
        "text_fx": "clean_hud",
        "visual_data": {
            "dc_mode": "campus_outro",
            "travel_mode": travel,
            "department": dept,
            "specialist": spec,
            "departments": match.get("departments"),
            "specialists": match.get("specialists"),
            "engineer_x": match["engineer_x"],
            "engineer_y": match["engineer_y"],
            "hud_pill": "IT PARK TOUR",
            "headline_white": "Complete",
            "headline_accent": f"{dept['name']}!",
            "accent_color": dept["color"],
            "option_a": f"{dept['icon']} {dept['name']}",
            "option_b": "🤖 AI / Data / Cloud",
            "footer_note": cta_note,
            "watermark": watermark,
        },
        "actions": [],
        "_disable_actions_overlay": True,
        "_disable_camera_actions": True,
    }

    combined = [sc_intro] + body_scenes + [sc_outro]
    for idx_c, sc in enumerate(combined, start=1):
        sc["scene_id"] = idx_c

    out_tl: Dict[str, Any] = {
        "topic": topic,
        "v2_engine": "datacenter_park",
        "art_style": "v2_midnight_navy",
        "header_brand": watermark,
        "scenes": combined,
    }
    if inner_tl.get("world_spec"):
        out_tl["world_spec"] = inner_tl["world_spec"]
    return out_tl


def generate_v2_timeline(
    topic: str,
    v2_mode: str = "v2_auto",
    tone: str = "warm_mentor_hi",
    duration_mode: str = "auto",
    voice: str = "",
    watermark: str = DEFAULT_WATERMARK,
    audience_level: str = "mid_senior",
    hook_style: str = "auto",
    cta_style: str = "save_share",
    cta_keyword: str = "",
    dc_travel_mode: str = "auto",
) -> Dict[str, Any]:
    """Entry point for Studio V2 / V3 / V4 / V5 Storyboard Directors (isolated from classic NanoPro)."""
    wm_clean = str(watermark or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    sub = resolve_v2_sub_engine(topic, v2_mode, duration_mode=duration_mode)
    if sub == "datacenter_park":
        tl = _generate_v5_datacenter_hybrid(
            topic, tone, duration_mode, voice, wm_clean,
            audience_level, hook_style, cta_style, cta_keyword,
            dc_travel_mode=dc_travel_mode,
        )
    elif sub == "spatial_isometric":
        tl = _generate_v2_isometric_llm(
            topic, tone, duration_mode, voice, wm_clean,
            audience_level, hook_style, cta_style, cta_keyword,
        )
        if tl is None:
            tl = _fallback_spatial_isometric(topic, wm_clean, tone, cta_style, cta_keyword)
    elif sub == "live_ide":
        tl = _generate_v3_ide_llm(
            topic, tone, duration_mode, voice, wm_clean,
            audience_level, hook_style, cta_style, cta_keyword,
        )
        if tl is None:
            tl = _fallback_live_ide(topic, wm_clean, tone, cta_style, cta_keyword)
    elif sub == "blueprint_whiteboard":
        tl = _generate_v4_whiteboard_llm(
            topic, tone, duration_mode, voice, wm_clean,
            audience_level, hook_style, cta_style, cta_keyword,
        )
        if tl is None:
            tl = _fallback_blueprint_whiteboard(topic, wm_clean, tone, cta_style, cta_keyword)
    else:
        tl = _generate_v2_vector_llm(
            topic, tone, duration_mode, voice, wm_clean,
            audience_level, hook_style, cta_style, cta_keyword,
        )
        if tl is None:
            tl = _fallback_vector_storyboard(topic, wm_clean, tone, hook_style, cta_style, cta_keyword)

    # Propagate global metadata onto every scene cleanly so parallel scene rendering is self-contained
    ws = tl.get("world_spec")
    tot = len(tl.get("scenes", []))
    for idx, sc in enumerate(tl.get("scenes", [])):
        vd = sc.setdefault("visual_data", {})
        vd["watermark"] = wm_clean
        if vd.get("widget_type") == "follow_cta":
            vd["handle_title"] = wm_clean
        vd.setdefault("_scene_idx", idx)
        vd.setdefault("_total_scenes", tot)
        if ws and "world_spec" not in vd:
            vd["world_spec"] = ws
    return tl
