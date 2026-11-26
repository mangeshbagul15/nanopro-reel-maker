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
    ("v2_auto", "⚡ Studio V2 Auto-Director (Picks Clean Vector Storyboard OR Spatial Isometric World)"),
    ("v2_vector_storyboard", "📐 Studio V2 — Clean Vector Storyboard (GyanaHut Style · Progressive SVG + Paired Analogy)"),
    ("v2_spatial_isometric", "🌐 Studio V2 — Spatial Isometric World (@thetechypenguin Style · 2.5D Map + Camera Fly + Top HUD)"),
]


def is_studio_v2_mode(mode_key: str) -> bool:
    return str(mode_key or "").strip() in ("v2_auto", "v2_vector_storyboard", "v2_spatial_isometric")


def resolve_v2_sub_engine(topic: str, mode_key: str, duration_mode: str = "auto") -> str:
    """Routes `v2_auto` cleanly between `vector_storyboard` and `spatial_isometric`."""
    mk = str(mode_key or "v2_auto").strip()
    if mk == "v2_vector_storyboard":
        return "vector_storyboard"
    if mk == "v2_spatial_isometric":
        return "spatial_isometric"

    low = f" {str(topic or '').lower()} "
    iso_kw = (
        "blue-green", "blue green", "canary", "deployment", "devops", "ci/cd", "cicd",
        "kubernetes", "k8s", "docker", "kafka", "flink", "spark", "snowflake", "lakehouse",
        "load balancer", "microservice", "architecture", "pipeline", "etl", "cdc", "debezium",
        "redis", "cache", "sharding", "replication", "failover", "disaster recovery", "rag",
        "agent", "aws", "azure", "gcp", "terraform", "system design", "distributed", "queue",
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
    return "8 to 11 crisp storyboard scenes (Interview Hook -> Misconception Meter -> Problem Scenario -> Spaghetti vs Clean Hub -> Paired Real-World Analogy -> Takeaway -> Follow CTA)"


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

        norm.append({
            "scene_id": i + 1,
            "role": role,
            "scene_tone": sc_tone,
            "sfx_cue": str(sc.get("sfx_cue") or ("punch_impact" if i == 0 else ("alert_ping" if "error" in role or "problem" in role else "pop_snap"))),
            "narration": nar,
            "visual_type": f"v2_{sub_engine}",
            "routed_engine": f"Studio V2 ({'Vector Storyboard' if sub_engine == 'vector_storyboard' else 'Spatial Isometric World'})",
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
) -> Dict[str, Any]:
    """Entry point for Studio V2 Storyboard Director (completely isolated from classic NanoPro)."""
    wm_clean = str(watermark or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    sub = resolve_v2_sub_engine(topic, v2_mode, duration_mode=duration_mode)
    if sub == "spatial_isometric":
        tl = _generate_v2_isometric_llm(
            topic, tone, duration_mode, voice, wm_clean,
            audience_level, hook_style, cta_style, cta_keyword,
        )
        if tl is None:
            tl = _fallback_spatial_isometric(topic, wm_clean, tone, cta_style, cta_keyword)
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
