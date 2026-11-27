"""
Studio V5 — Enterprise Data Center & IT Park World Renderer.
Renders an expansive, dark-mode 2.5D Isometric IT Park & Mega Data Center campus with:
  - 8 Enterprise Departments + 20 Specialist Engineers at animated dual-monitor workstations
  - Corner Cooling Towers (spinning fans), Core Server Rack Hall (pulsing LEDs), Fiber Conduits
  - 3 Selectable Travel Modes: Camera Fly, Drone Escort (quadcopter + spotlight cone), Fiber Packet Ride
  - 3 Scene Modes: `campus_fly` (Macro -> Dept), `desk_focus` (Engineer Desk + Dialogue), `campus_outro` (Zoom Out + CTA)
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS
from core.tone_engine import get_tone_profile

DC_TRAVEL_MODES: List[Tuple[str, str]] = [
    ("auto", "⚡ AI Auto-Pick (Matches Topic: Drone / Camera / Fiber)"),
    ("camera", "🎥 Camera Fly (Smooth Cinematic Map Swoop)"),
    ("drone", "🚁 Drone Escort (Quadcopter + Spotlight Cone)"),
    ("fiber", "⚡ Fiber Packet Ride (High-Speed Conduit Orb)"),
]

_ACCENT_HEX = {
    "cyan": "#38BDF8",
    "emerald": "#34D399",
    "amber": "#FBBF24",
    "rose": "#F43F5E",
    "purple": "#C084FC",
    "blue": "#60A5FA",
}

# 10 Enterprise Departments laid out across an 1800x1800 virtual 2.5D Data Center & IT Park campus
DC_DEPARTMENTS: List[Dict[str, Any]] = [
    {"id": "ad_iam", "name": "AD, IAM & POLICY", "full": "AD, Identity & Security Policy", "x": 330, "y": 310, "w": 380, "h": 260, "color": "cyan", "icon": "🔐"},
    {"id": "infosec", "name": "INFOSEC (IS)", "full": "Information Security (IS)", "x": 900, "y": 250, "w": 390, "h": 260, "color": "rose", "icon": "🛡️"},
    {"id": "audit_grc", "name": "AUDIT & IT NEWS", "full": "Compliance Audit, Policy & IT News", "x": 1470, "y": 310, "w": 380, "h": 260, "color": "emerald", "icon": "📰"},
    {"id": "data_eng", "name": "DATA ENG & DW", "full": "Data Eng, Snowflake & Data Warehouse", "x": 260, "y": 730, "w": 380, "h": 270, "color": "emerald", "icon": "❄️"},
    {"id": "data_ds", "name": "ANALYST & DS", "full": "Data Analyst & Data Science Lab", "x": 260, "y": 1170, "w": 380, "h": 270, "color": "amber", "icon": "📊"},
    {"id": "ai_agents", "name": "AI, LLM & AGENTS", "full": "AI Agents, LLMs & Tech Hacks Lab", "x": 1540, "y": 730, "w": 380, "h": 270, "color": "purple", "icon": "🤖"},
    {"id": "infra", "name": "INFRA & STORAGE", "full": "Infra, Hardware & Data Storage", "x": 1540, "y": 1170, "w": 380, "h": 270, "color": "amber", "icon": "🖥️"},
    {"id": "sql_dba", "name": "SQL & DATABASE", "full": "SQL Analytics & Database Engine", "x": 330, "y": 1530, "w": 380, "h": 260, "color": "blue", "icon": "🗄️"},
    {"id": "mcs", "name": "AWS · AZURE · GCP", "full": "MCS Multi-Cloud (AWS / Azure / GCP)", "x": 900, "y": 1570, "w": 400, "h": 260, "color": "purple", "icon": "☁️"},
    {"id": "app_py", "name": "DEV, API & PYTHON", "full": "Software Dev, APIs & Python", "x": 1470, "y": 1530, "w": 380, "h": 260, "color": "cyan", "icon": "🐍"},
]

# 25 Specialist Engineers positioned inside their Departments + recommended hybrid handoff engine
DC_SPECIALISTS: List[Dict[str, Any]] = [
    # 1. AD, IAM & POLICY (3)
    {"id": "ad_gpo", "dept_id": "ad_iam", "title": "AD & Group Policy (GPO) Engineer", "short": "AD GPO Eng", "tools": "Active Directory · GPO · OU · Kerberos", "handoff": "blueprint_whiteboard", "dx": -95, "dy": -15, "keywords": ["active directory", "ad ", "group policy", "gpo", "ldap", "kerberos"]},
    {"id": "aws_iam", "dept_id": "ad_iam", "title": "IAM Roles & Policy Engineer", "short": "IAM & Policy", "tools": "IAM Policies · STS AssumeRole · SSO · RBAC", "handoff": "blueprint_whiteboard", "dx": 5, "dy": 32, "keywords": ["iam", "sts", "assume role", "policy", "policies", "least privilege", "sso", "identity", "oauth", "jwt", "rbac"]},
    {"id": "dms_pam", "dept_id": "ad_iam", "title": "Data Management & Access Governance Eng", "short": "Data Mgmt / PAM", "tools": "Data Management · Catalog · Lineage · Vault", "handoff": "blueprint_whiteboard", "dx": 100, "dy": -15, "keywords": ["data management", "data governance", "catalog", "lineage", "pam", "privileged", "vault"]},
    # 2. INFOSEC (IS) (3)
    {"id": "sec_fw", "dept_id": "infosec", "title": "Firewall & Port Opening Engineer", "short": "Firewall Eng", "tools": "Palo Alto · Security Groups · TCP 443/5432", "handoff": "blueprint_whiteboard", "dx": -100, "dy": -15, "keywords": ["firewall", "port opening", "port", "tcp", "security group", "nacl", "iptables", "dmz", "waf"]},
    {"id": "sec_url", "dept_id": "infosec", "title": "URL Whitelisting & Proxy Engineer", "short": "URL Proxy Eng", "tools": "Zscaler Proxy · Allowlist · SSL Inspect", "handoff": "blueprint_whiteboard", "dx": 0, "dy": 32, "keywords": ["whitelist", "url", "proxy", "domain", "allowlist", "egress"]},
    {"id": "sec_soc", "dept_id": "infosec", "title": "Cyber Security & SOC Analyst", "short": "CyberSec / SOC", "tools": "SIEM · VAPT · Zero Trust · Encryption", "handoff": "blueprint_whiteboard", "dx": 105, "dy": -15, "keywords": ["security", "cyber", "soc", "siem", "vapt", "vulnerability", "ddos", "breach", "is team", "zero trust"]},
    # 3. AUDIT, POLICY & IT NEWS (2)
    {"id": "audit_iso", "dept_id": "audit_grc", "title": "IT Audit & Compliance Policy Lead", "short": "Audit & Policy", "tools": "ISO 27001 · SOC2 · WORM Audit Trails", "handoff": "blueprint_whiteboard", "dx": -60, "dy": 0, "keywords": ["audit", "compliance", "soc2", "iso 27001", "iso27001", "grc", "governance", "pci", "rbi"]},
    {"id": "it_news", "dept_id": "audit_grc", "title": "IT News & Tech Radar Brief", "short": "IT News Desk", "tools": "Breaking Releases · Benchmarks · Cloud News", "handoff": "blueprint_whiteboard", "dx": 70, "dy": 15, "keywords": ["it news", "tech news", "release", "launch", "update", "announcement", "industry", "layoff", "funding"]},
    # 4. DATA ENG & WAREHOUSE (3)
    {"id": "data_ingest", "dept_id": "data_eng", "title": "Data Ingestion & CDC Engineer", "short": "CDC Ingest Eng", "tools": "Oracle DMS · Debezium · Kafka · S3 Parquet", "handoff": "spatial_isometric", "dx": -95, "dy": -18, "keywords": ["dms", "cdc", "debezium", "ingest", "ingestion", "kafka", "oracle", "parquet", "streaming"]},
    {"id": "data_migrate", "dept_id": "data_eng", "title": "Data Warehouse & Migration Engineer", "short": "Data Warehouse", "tools": "Snowflake · Redshift · BigQuery · Migration", "handoff": "spatial_isometric", "dx": 0, "dy": 32, "keywords": ["data warehouse", "warehouse", "migration", "migrate", "full load", "cutover", "redshift", "bigquery"]},
    {"id": "data_pipe", "dept_id": "data_eng", "title": "Snowflake & Medallion Data Engineer", "short": "Snowflake DE", "tools": "Airflow · Snowflake L0->L1->L2 · dbt · Spark", "handoff": "spatial_isometric", "dx": 95, "dy": -15, "keywords": ["snowflake", "airflow", "lambda", "l0", "l1", "l2", "medallion", "lakehouse", "etl", "elt", "pipeline", "data engineer", "spark"]},
    # 5. DATA ANALYST & DATA SCIENCE (2)
    {"id": "data_analyst", "dept_id": "data_ds", "title": "Data Analyst & BI Insights Engineer", "short": "Data Analyst", "tools": "SQL · PowerBI · Tableau · Funnel & Cohort KPI", "handoff": "live_ide", "dx": -65, "dy": 0, "keywords": ["data analyst", "analytics", "dashboard", "bi ", "powerbi", "tableau", "kpi", "cohort", "funnel", "reporting"]},
    {"id": "data_scientist", "dept_id": "data_ds", "title": "Data Scientist & ML Modeling Lab", "short": "Data Science", "tools": "PyTorch · Scikit-Learn · Feature Store · Eval", "handoff": "live_ide", "dx": 68, "dy": 15, "keywords": ["data science", "data scientist", "machine learning", "ml ", "feature", "training", "regression", "xgboost", "pytorch", "statistics"]},
    # 6. AI, LLM & TECH HACKS LAB (3)
    {"id": "ai_agents", "dept_id": "ai_agents", "title": "AI Agents & MCP Systems Architect", "short": "AI Agents / MCP", "tools": "Multi-Agent DAG · MCP · Tool Calling · Memory", "handoff": "blueprint_whiteboard", "dx": -95, "dy": -18, "keywords": ["agent", "agents", "agentic", "mcp", "rag", "vector", "embedding", "langgraph"]},
    {"id": "ai_llm", "dept_id": "ai_agents", "title": "LLM & Foundation Models Engineer", "short": "LLM Models Lab", "tools": "Gemini · GPT · Claude · Llama · KV Cache", "handoff": "blueprint_whiteboard", "dx": 5, "dy": 32, "keywords": ["llm", "gpt", "gemini", "claude", "llama", "transformer", "fine-tune", "quantization", "token", "ai model", "artificial intelligence", "ai "]},
    {"id": "ai_hacks", "dept_id": "ai_agents", "title": "AI Tech Hacks, Tips & Tricks Creator", "short": "AI Tips & Hacks", "tools": "Prompt Tricks · Local AI · Speed Hacks · Tools", "handoff": "blueprint_whiteboard", "dx": 98, "dy": -15, "keywords": ["hack", "hacks", "tip", "tips", "trick", "tricks", "shortcut", "productivity", "prompt engineering"]},
    # 7. INFRA & DATA STORAGE (3)
    {"id": "infra_srv", "dept_id": "infra", "title": "Server Hardware & Infrastructure Eng", "short": "Infra / Compute", "tools": "Bare Metal Racks · Kubernetes · Docker · ESXi", "handoff": "spatial_isometric", "dx": -95, "dy": -15, "keywords": ["hardware", "server", "rack", "compute", "kubernetes", "k8s", "docker", "blue-green", "deployment", "infra", "infrastructure"]},
    {"id": "infra_san", "dept_id": "infra", "title": "Enterprise Data Storage SAN/NAS Eng", "short": "Data Storage", "tools": "NVMe Pool · S3 Object · Block SAN · RAID · DR", "handoff": "spatial_isometric", "dx": 0, "dy": 32, "keywords": ["data storage", "storage", "san", "nas", "nvme", "raid", "disk", "backup", "dr ", "disaster", "object store", "iceberg"]},
    {"id": "infra_net", "dept_id": "infra", "title": "Core Network & Load Balancer Engineer", "short": "Net & LB Eng", "tools": "BGP · L7 Load Balancer · VLAN · Rate Limit", "handoff": "spatial_isometric", "dx": 95, "dy": -15, "keywords": ["network", "load balancer", "bgp", "vlan", "vpc", "routing", "cdn", "rate limit"]},
    # 8. SQL & DATABASE (2)
    {"id": "sql_arch", "dept_id": "sql_dba", "title": "SQL Query & Window Functions Architect", "short": "SQL Query Arch", "tools": "JOIN · GROUP BY · DENSE_RANK · EXPLAIN", "handoff": "live_ide", "dx": -62, "dy": 5, "keywords": ["sql", "join", "group by", "dense_rank", "window", "cte", "query", "select ", "index"]},
    {"id": "sql_dba_ops", "dept_id": "sql_dba", "title": "Production DBA & Replication Engineer", "short": "Prod DBA Eng", "tools": "Postgres / Oracle · WAL · Locks · Sharding", "handoff": "live_ide", "dx": 65, "dy": 15, "keywords": ["dba", "database", "deadlock", "vacuum", "replication", "sharding", "wal", "postgres"]},
    # 9. MULTI-CLOUD MCS (AWS / AZURE / GCP) (2)
    {"id": "mcs_ops", "dept_id": "mcs", "title": "AWS · Azure · GCP Cloud Architect", "short": "Multi-Cloud Ops", "tools": "AWS · Azure · GCP · Terraform · MCS", "handoff": "spatial_isometric", "dx": -65, "dy": 5, "keywords": ["aws", "azure", "gcp", "google cloud", "mcs", "managed cloud", "multi-cloud", "terraform", "s3 ", "ec2", "lambda"]},
    {"id": "mcs_finops", "dept_id": "mcs", "title": "Cloud Auto-Scaling & FinOps Engineer", "short": "Cloud FinOps", "tools": "Autoscale · Cost Optimization · Serverless", "handoff": "blueprint_whiteboard", "dx": 68, "dy": 15, "keywords": ["finops", "autoscale", "cloud cost", "serverless", "cloud"]},
    # 10. SOFTWARE DEV, API & PYTHON (2)
    {"id": "py_auto", "dept_id": "app_py", "title": "Python & Automation Engineer", "short": "Python Eng", "tools": "Python 3.12 · Asyncio · GIL · FastAPI · N+1", "handoff": "live_ide", "dx": -62, "dy": 5, "keywords": ["python", "asyncio", "gil", "pandas", "n+1", "orm", "script", "automation", "debug"]},
    {"id": "app_dev", "dept_id": "app_py", "title": "Software & API Systems Developer", "short": "Software / API", "tools": "REST · GraphQL · Microservices · CI/CD · Webhook", "handoff": "live_ide", "dx": 65, "dy": 15, "keywords": ["software", "developer", "development", "api", "rest", "graphql", "webhook", "microservice", "ci/cd", "cicd", "backend", "redis", "cache"]},
]


def _synthesize_custom_specialist(topic: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Dynamically creates a custom Department Pod + Specialist Engineer (+ peer desks)
    whenever a brand-new niche topic/scenario does not match existing built-in desks.
    """
    import re
    from core.config import GEMINI_API_KEY, GROQ_API_KEY

    clean = re.sub(r"[^A-Za-z0-9_+/\- ]", " ", str(topic or "")).strip()
    words = [w for w in clean.split() if w.lower() not in (
        "how", "what", "why", "explain", "works", "work", "with", "using", "into",
        "from", "for", "and", "the", "this", "that", "system", "architecture", "video",
    )]
    domain_lbl = (" ".join(words[:2]) if words else "Custom Tech").strip()[:16]
    spec_short = (f"{words[0][:11]} Eng" if words else "Tech Specialist")[:16]
    spec_title = f"{domain_lbl} Specialist Engineer"
    tools_str = " · ".join(words[:3]) if len(words) >= 2 else f"{domain_lbl} · Production · Telemetry"
    dept_color = "cyan"
    dept_icon = "⚡"
    handoff = "blueprint_whiteboard"
    if any(k in clean.lower() for k in ("code", "python", "sql", "script", "api", "query", "sdk", "solidity")):
        handoff = "live_ide"
        dept_color = "emerald"
    elif any(k in clean.lower() for k in ("cluster", "node", "pipeline", "mesh", "kafka", "erp", "switch", "bank")):
        handoff = "spatial_isometric"
        dept_color = "amber"

    prompt = f"""Topic/Scenario: "{topic}"
This topic did not match a fixed Data Center desk. Design ONE new custom Enterprise IT Park Department Pod + Specialist Engineer.
Return STRICT JSON ONLY:
{{"dept_name":"SHORT UPPERCASE <=16 chars","dept_full":"Full Department Name","dept_icon":"1 emoji","dept_color":"cyan|emerald|amber|rose|purple|blue","spec_title":"Exact Engineer Role Title","spec_short":"Short Pill <=15 chars","peer_a":"Peer Role 1 <=15 chars","peer_b":"Peer Role 2 <=15 chars","tools":"Tool1 · Tool2 · Tool3","handoff":"live_ide|blueprint_whiteboard|spatial_isometric"}}"""

    parsed = None
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            res = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
            m = re.search(r"\{[\s\S]*\}", str(getattr(res, "text", "") or ""))
            if m:
                parsed = json.loads(m.group(0))
        except Exception:
            parsed = None
    if not parsed and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=8,
            )
            m = re.search(r"\{[\s\S]*\}", (res.choices[0].message.content if res.choices else ""))
            if m:
                parsed = json.loads(m.group(0))
        except Exception:
            parsed = None

    if isinstance(parsed, dict) and parsed.get("dept_name") and parsed.get("spec_short"):
        d_name = str(parsed["dept_name"])[:18].upper()
        d_full = str(parsed.get("dept_full") or d_name)[:36]
        dept_icon = str(parsed.get("dept_icon") or "⚡")[:4]
        dc_cand = str(parsed.get("dept_color") or dept_color).lower()
        dept_color = dc_cand if dc_cand in _ACCENT_HEX else "cyan"
        spec_title = str(parsed.get("spec_title") or spec_title)[:42]
        spec_short = str(parsed["spec_short"])[:17]
        peer_a = str(parsed.get("peer_a") or f"{domain_lbl[:9]} Ops")[:17]
        peer_b = str(parsed.get("peer_b") or f"{domain_lbl[:9]} QA")[:17]
        tools_str = str(parsed.get("tools") or tools_str)[:54]
        ho = str(parsed.get("handoff") or handoff)
        handoff = ho if ho in ("live_ide", "blueprint_whiteboard", "spatial_isometric") else handoff
    else:
        d_name = f"{domain_lbl.upper()[:14]} HUB"
        d_full = f"{domain_lbl} Engineering Hub"
        peer_a = f"{domain_lbl[:9]} Ops"
        peer_b = f"{domain_lbl[:9]} Audit"

    custom_dept = {
        "id": "custom_dynamic",
        "name": d_name,
        "full": d_full,
        "x": 900,
        "y": 560,
        "w": 390,
        "h": 265,
        "color": dept_color,
        "icon": dept_icon,
        "is_custom": True,
    }
    target_sp = {
        "id": "custom_spec_main",
        "dept_id": "custom_dynamic",
        "title": spec_title,
        "short": spec_short,
        "tools": tools_str,
        "handoff": handoff,
        "dx": 0,
        "dy": 22,
        "keywords": [],
    }
    peer_specs = [
        {"id": "custom_spec_a", "dept_id": "custom_dynamic", "title": peer_a, "short": peer_a, "tools": tools_str, "handoff": handoff, "dx": -105, "dy": -16, "keywords": []},
        target_sp,
        {"id": "custom_spec_b", "dept_id": "custom_dynamic", "title": peer_b, "short": peer_b, "tools": tools_str, "handoff": handoff, "dx": 105, "dy": -16, "keywords": []},
    ]
    return custom_dept, peer_specs, target_sp


def match_datacenter_specialist(topic: str, preferred_travel: str = "auto", allow_custom: bool = True) -> Dict[str, Any]:
    """
    Matches a prompt topic to the best Department & Specialist Engineer.
    If no built-in role matches strongly (`best_score < 2`), dynamically synthesizes a custom
    Department Pod & Specialist Engineer right on the Data Center campus!
    """
    import re
    low = f" {str(topic or '').lower()} "
    best_sp = DC_SPECIALISTS[8]
    best_score = -1
    for sp in DC_SPECIALISTS:
        score = 0
        for kw in sp["keywords"]:
            kw_s = kw.strip()
            if kw_s and re.search(rf"(?<![a-z0-9]){re.escape(kw_s)}(?![a-z0-9])", low):
                score += (3 if len(kw_s) >= 5 else 2)
        if score > best_score:
            best_score = score
            best_sp = sp

    eff_depts = [dict(d) for d in DC_DEPARTMENTS]
    eff_specs = [dict(s) for s in DC_SPECIALISTS]

    if best_score < 2 and allow_custom:
        c_dept, c_peers, c_target = _synthesize_custom_specialist(topic)
        eff_depts.append(c_dept)
        eff_specs.extend(c_peers)
        dept = c_dept
        best_sp = c_target
    else:
        dept = next((d for d in eff_depts if d["id"] == best_sp["dept_id"]), eff_depts[0])

    travel = str(preferred_travel or "auto").lower().strip()
    if travel not in ("camera", "drone", "fiber"):
        if dept["id"] in ("infosec", "audit_grc", "ad_iam", "ai_agents", "custom_dynamic"):
            travel = "drone"
        elif dept["id"] in ("data_eng", "infra", "sql_dba", "data_ds"):
            travel = "fiber"
        else:
            travel = "camera"

    return {
        "department": dict(dept),
        "specialist": dict(best_sp),
        "travel_mode": travel,
        "engineer_x": dept["x"] + best_sp["dx"],
        "engineer_y": dept["y"] + best_sp["dy"],
        "departments": eff_depts,
        "specialists": eff_specs,
        "is_custom": bool(dept.get("is_custom")),
    }


def _compute_dc_camera(
    dc_mode: str,
    dept: Dict[str, Any],
    eng_x: float,
    eng_y: float,
    width: int,
    height: int,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Computes fast start/end camera keyframes with tight close-up onto the specific engineer's desk."""
    is_wide = width > height
    campus_zoom = 0.62 if is_wide else 0.48
    dept_zoom = 1.55 if is_wide else 1.38
    desk_zoom = 3.35 if is_wide else 3.05

    # Focus right between the seated engineer and their dual glowing monitors
    tgt_x = float(eng_x)
    tgt_y = float(eng_y) - 10.0

    if dc_mode == "campus_to_desk":
        start = {"cx": 900.0, "cy": 900.0, "zoom": campus_zoom}
        end = {"cx": tgt_x, "cy": tgt_y, "zoom": desk_zoom}
    elif dc_mode == "campus_fly":
        start = {"cx": 900.0, "cy": 900.0, "zoom": campus_zoom}
        end = {"cx": float(dept["x"]), "cy": float(dept["y"]), "zoom": dept_zoom}
    elif dc_mode == "desk_focus":
        start = {"cx": float(dept["x"]), "cy": float(dept["y"]), "zoom": dept_zoom}
        end = {"cx": tgt_x, "cy": tgt_y, "zoom": desk_zoom}
    else:  # campus_outro
        start = {"cx": tgt_x, "cy": tgt_y, "zoom": round(desk_zoom * 0.78, 2)}
        end = {"cx": 900.0, "cy": 890.0, "zoom": round(campus_zoom * 1.08, 2)}
    return start, end


def _build_datacenter_html(
    scene: Dict[str, Any],
    width: int,
    height: int,
    tone: str = "auto_2026_director",
) -> str:
    vd = dict(scene.get("visual_data") or {})
    dc_mode = str(vd.get("dc_mode") or "campus_fly")
    travel_mode = str(vd.get("travel_mode") or "drone")
    dept = dict(vd.get("department") or DC_DEPARTMENTS[0])
    spec = dict(vd.get("specialist") or DC_SPECIALISTS[0])
    eng_x = float(vd.get("engineer_x") or (dept["x"] + spec.get("dx", 0)))
    eng_y = float(vd.get("engineer_y") or (dept["y"] + spec.get("dy", 0)))

    accent_key = str(vd.get("accent_color") or dept.get("color") or "cyan")
    accent_hex = _ACCENT_HEX.get(accent_key, "#38BDF8")

    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = (
        f'<span class="at">@</span>{html.escape(raw_wm[1:])}'
        if raw_wm.startswith("@")
        else html.escape(raw_wm)
    )
    hud_pill = html.escape(str(vd.get("hud_pill") or f"IT PARK · {dept.get('name', 'DATA CENTER')}"))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))

    travel_badges = {
        "drone": "🚁 DRONE ESCORT ACTIVE",
        "fiber": "⚡ FIBER PACKET TRACE",
        "camera": "🎥 CAMERA FLYOVER",
    }
    travel_lbl = html.escape(travel_badges.get(travel_mode, "🎥 CAMERA FLYOVER"))

    start_cam, end_cam = _compute_dc_camera(dc_mode, dept, eng_x, eng_y, width, height)
    is_wide = width > height
    sc = min(width, height) / 1080.0
    hl_px = int((54 if not is_wide else 40) * sc)

    # Top HUD Card depends on scene mode
    if dc_mode in ("desk_focus", "campus_to_desk"):
        dlg_text = html.escape(str(vd.get("dialogue_text") or scene.get("narration") or ""))
        sp_title = html.escape(str(spec.get("title") or "Specialist Engineer"))
        sp_tools = html.escape(str(spec.get("tools") or ""))
        hud_card = f"""
        <div class="hud-card reveal" data-p="0.04" style="border-top:4px solid {accent_hex}">
          <div class="card-top-row">
            <span class="sp-badge" style="background:{accent_hex}28;border-color:{accent_hex};color:{accent_hex}">{html.escape(str(dept.get('icon','👨‍💻')))} {sp_title}</span>
            <span class="dept-chip">{travel_lbl}</span>
          </div>
          <div class="dlg-quote">"{dlg_text}"</div>
          <div class="tools-line">🛠️ {sp_tools}</div>
        </div>"""
    elif dc_mode == "campus_outro":
        oa = html.escape(str(vd.get("option_a") or f"🏢 {dept.get('name', 'Tech')} Deep-Dive"))
        ob = html.escape(str(vd.get("option_b") or "⚡ Next Dept Tour"))
        fn = html.escape(str(vd.get("footer_note") or "Comment which department you want next!"))
        hud_card = f"""
        <div class="hud-card reveal" data-p="0.10" style="border-top:4px solid {accent_hex};text-align:center">
          <div class="tools-line" style="color:{accent_hex};margin-bottom:10px">🏢 ENTERPRISE DATA CENTER TOUR COMPLETE</div>
          <div class="poll-row">
            <div class="poll-btn primary">{oa}</div>
            <div class="poll-btn">{ob}</div>
          </div>
          <div class="poll-note">{fn}</div>
        </div>"""
    else:  # campus_fly
        sub_txt = html.escape(str(vd.get("campus_sub") or f"Target: {dept.get('full', '')} → {spec.get('title', '')}"))
        hud_card = f"""
        <div class="hud-card reveal" data-p="0.04" style="border-top:4px solid {accent_hex}">
          <div class="card-top-row">
            <span class="sp-badge" style="background:{accent_hex}28;border-color:{accent_hex};color:{accent_hex}">{travel_lbl}</span>
            <span class="dept-chip">10 DEPTS · 25 SPECIALISTS</span>
          </div>
          <div class="dlg-quote" style="font-size:{int(27*sc)}px">{sub_txt}</div>
        </div>"""

    eff_depts = list(vd.get("departments") or DC_DEPARTMENTS)
    eff_specs = list(vd.get("specialists") or DC_SPECIALISTS)
    if not any(d.get("id") == dept.get("id") for d in eff_depts):
        eff_depts.append(dept)
    if not any(s.get("id") == spec.get("id") for s in eff_specs):
        eff_specs.append(spec)

    state_json = json.dumps({
        "dc_mode": dc_mode,
        "travel_mode": travel_mode,
        "target_dept_id": dept["id"],
        "target_spec_id": spec["id"],
        "target_dept": dept,
        "eng_x": eng_x,
        "eng_y": eng_y,
        "start_cam": start_cam,
        "end_cam": end_cam,
        "departments": eff_depts,
        "specialists": eff_specs,
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: radial-gradient(circle at 50% 14%, {accent_hex}24 0%, #091124 46%, #040711 100%);
    color: #F8FAFC;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }}
  canvas#dc {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
  .wm-pill {{
    position: absolute; top: {int(32*sc)}px; left: {int(40*sc)}px; z-index: 12;
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.92); border: 1.6px solid rgba(148,163,184,0.34);
    font-size: {int(22*sc)}px; font-weight: 800; color: #FFFFFF;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .top-zone {{
    position: relative; z-index: 8; width: 100%;
    padding: {int(96*sc if not is_wide else 72*sc)}px {int(44*sc)}px {int(32*sc)}px;
    display: flex; flex-direction: column; align-items: center; text-align: center;
    background: linear-gradient(180deg, rgba(4,7,17,0.96) 0%, rgba(7,12,28,0.88) 78%, rgba(7,12,28,0.0) 100%);
  }}
  .hud-pill {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: {int(7*sc)}px {int(18*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.88); border: 1.8px solid {accent_hex};
    font-size: {int(19*sc)}px; font-weight: 900; letter-spacing: 2.2px; color: {accent_hex};
    margin-bottom: {int(10*sc)}px;
  }}
  .headline {{
    font-size: {hl_px}px; font-weight: 900; line-height: 1.12; margin-bottom: {int(16*sc)}px;
    text-shadow: 0 6px 24px rgba(0,0,0,0.75);
  }}
  .headline .acc {{ color: {accent_hex}; }}
  .hud-card {{
    width: min(100%, {int(950*sc)}px); text-align: left;
    background: rgba(11, 18, 38, 0.94);
    border-radius: {int(20*sc)}px; border: 1.5px solid rgba(148,163,184,0.28);
    padding: {int(20*sc)}px {int(26*sc)}px;
    box-shadow: 0 20px 52px rgba(0,0,0,0.65);
  }}
  .card-top-row {{
    display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;
    margin-bottom: {int(10*sc)}px;
  }}
  .sp-badge {{
    padding: {int(5*sc)}px {int(14*sc)}px; border-radius: 999px; border: 1.6px solid;
    font-size: {int(18*sc)}px; font-weight: 900; letter-spacing: 0.8px;
  }}
  .dept-chip {{
    font-size: {int(17*sc)}px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;
  }}
  .dlg-quote {{
    font-size: {int(28*sc)}px; font-weight: 800; color: #FFFFFF; line-height: 1.32;
  }}
  .tools-line {{
    margin-top: {int(10*sc)}px; font-size: {int(20*sc)}px; font-weight: 700; color: #94A3B8;
  }}
  .poll-row {{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; margin: 10px 0; }}
  .poll-btn {{
    padding: {int(12*sc)}px {int(24*sc)}px; border-radius: 14px;
    background: rgba(15,23,42,0.92); border: 2px solid rgba(148,163,184,0.4);
    font-size: {int(22*sc)}px; font-weight: 800; color: #E2E8F0;
  }}
  .poll-btn.primary {{ border-color: {accent_hex}; background: {accent_hex}22; color: #FFFFFF; }}
  .poll-note {{ font-size: {int(21*sc)}px; color: #FACC15; font-weight: 800; margin-top: 6px; }}
</style>
</head>
<body>
  <canvas id="dc" width="{width}" height="{height}"></canvas>
  <div class="wm-pill">{wm_html}</div>
  <div class="top-zone">
    <div class="hud-pill">🏢 {hud_pill}</div>
    <div class="headline">{h_white} <span class="acc">{h_accent}</span></div>
    {hud_card}
  </div>

  <script>
    const STATE = {state_json};
    const canvas = document.getElementById('dc');
    const ctx = canvas.getContext('2d');
    const W = {width}, H = {height};
    const PAL = {{
      cyan:    {{ hi: '#67E8F9', mid: '#0891B2', lo: '#0E7490', hex: '#38BDF8' }},
      emerald: {{ hi: '#6EE7B7', mid: '#16A34A', lo: '#15803D', hex: '#34D399' }},
      amber:   {{ hi: '#FDE047', mid: '#D97706', lo: '#B45309', hex: '#FBBF24' }},
      rose:    {{ hi: '#FDA4AF', mid: '#E11D48', lo: '#BE123C', hex: '#F43F5E' }},
      purple:  {{ hi: '#D8B4FE', mid: '#7E22CE', lo: '#6B21A8', hex: '#C084FC' }},
      blue:    {{ hi: '#93C5FD', mid: '#2563EB', lo: '#1D4ED8', hex: '#60A5FA' }},
    }};

    function easeInOut(t) {{
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }}

    function iso(wx, wy, wz, camX, camY, zoom) {{
      const dx = (wx - camX) * zoom;
      const dy = (wy - camY) * zoom;
      const sx = W * 0.5 + (dx - dy) * 0.72;
      const sy = H * 0.67 + (dx + dy) * 0.38 - wz * zoom;
      return [sx, sy];
    }}

    function drawPrism(wx, wy, sxL, syL, hz, col, camX, camY, zoom, zB = 0) {{
      const hw = sxL * 0.5, hh = syL * 0.5;
      const b00 = iso(wx - hw, wy - hh, zB, camX, camY, zoom);
      const b10 = iso(wx + hw, wy - hh, zB, camX, camY, zoom);
      const b11 = iso(wx + hw, wy + hh, zB, camX, camY, zoom);
      const b01 = iso(wx - hw, wy + hh, zB, camX, camY, zoom);
      const t00 = iso(wx - hw, wy - hh, zB + hz, camX, camY, zoom);
      const t10 = iso(wx + hw, wy - hh, zB + hz, camX, camY, zoom);
      const t11 = iso(wx + hw, wy + hh, zB + hz, camX, camY, zoom);
      const t01 = iso(wx - hw, wy + hh, zB + hz, camX, camY, zoom);

      ctx.beginPath(); ctx.moveTo(...b01); ctx.lineTo(...b11); ctx.lineTo(...t11); ctx.lineTo(...t01); ctx.closePath();
      ctx.fillStyle = col.mid; ctx.fill();
      ctx.beginPath(); ctx.moveTo(...b11); ctx.lineTo(...b10); ctx.lineTo(...t10); ctx.lineTo(...t11); ctx.closePath();
      ctx.fillStyle = col.lo; ctx.fill();
      ctx.beginPath(); ctx.moveTo(...t00); ctx.lineTo(...t10); ctx.lineTo(...t11); ctx.lineTo(...t01); ctx.closePath();
      ctx.fillStyle = col.hi; ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.22)'; ctx.lineWidth = 1.2; ctx.stroke();
    }}

    function drawBadge(sx, sy, txt, bg, fg, zoom) {{
      const fs = Math.max(12, Math.min(24, Math.round(16 * Math.sqrt(zoom))));
      ctx.font = `900 ${{fs}}px "Nirmala UI","Segoe UI",sans-serif`;
      const tw = ctx.measureText(txt).width;
      const bw = tw + 22, bh = fs + 14;
      ctx.save();
      ctx.fillStyle = bg; ctx.strokeStyle = fg; ctx.lineWidth = 1.8;
      ctx.beginPath(); ctx.roundRect(sx - bw * 0.5, sy - bh * 0.5, bw, bh, 9);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = fg; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(txt, sx, sy + 1);
      ctx.restore();
    }}

    function drawGlassPartition(d, col, camX, camY, zoom) {{
      const isTgt = d.id === STATE.target_dept_id;
      const x0 = d.x - d.w * 0.48, x1 = d.x + d.w * 0.48;
      const yb = d.y - d.h * 0.48;
      const p0 = iso(x0, yb, 0, camX, camY, zoom);
      const p1 = iso(x1, yb, 0, camX, camY, zoom);
      const t1 = iso(x1, yb, 95, camX, camY, zoom);
      const t0 = iso(x0, yb, 95, camX, camY, zoom);
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(...p0); ctx.lineTo(...p1); ctx.lineTo(...t1); ctx.lineTo(...t0); ctx.closePath();
      ctx.fillStyle = isTgt ? col.hex + '16' : 'rgba(56,189,248,0.06)';
      ctx.fill();
      ctx.strokeStyle = isTgt ? col.hi + 'CC' : col.hex + '44';
      ctx.lineWidth = isTgt ? 2.2 : 1.1;
      ctx.stroke();
      ctx.restore();
    }}

    function drawServerRack(wx, wy, col, camX, camY, zoom, prog, seed) {{
      // Tall dark obsidian server rack with glowing horizontal LED status bars (like reference!)
      const darkCol = {{ hi: '#0B1324', mid: '#050914', lo: '#02040A' }};
      drawPrism(wx, wy, 30, 28, 92, darkCol, camX, camY, zoom, 0);
      const hw = 15, hh = 14;
      // Glowing cyan wireframe rim
      const t00 = iso(wx - hw, wy - hh, 92, camX, camY, zoom);
      const t10 = iso(wx + hw, wy - hh, 92, camX, camY, zoom);
      const t11 = iso(wx + hw, wy + hh, 92, camX, camY, zoom);
      const t01 = iso(wx - hw, wy + hh, 92, camX, camY, zoom);
      const b01 = iso(wx - hw, wy + hh, 0, camX, camY, zoom);
      const b11 = iso(wx + hw, wy + hh, 0, camX, camY, zoom);
      ctx.save();
      ctx.strokeStyle = col.hi + '99'; ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(...t00); ctx.lineTo(...t10); ctx.lineTo(...t11); ctx.lineTo(...t01); ctx.closePath();
      ctx.moveTo(...t01); ctx.lineTo(...b01); ctx.lineTo(...b11); ctx.lineTo(...t11);
      ctx.stroke();

      // 6 horizontal illuminated blade LED strips on front face
      for (let slot = 0; slot < 6; slot++) {{
        const zs = 14 + slot * 12;
        const lA = iso(wx - 10, wy + hh + 0.5, zs, camX, camY, zoom);
        const lB = iso(wx + 10, wy + hh + 0.5, zs, camX, camY, zoom);
        const blink = (Math.sin(prog * 18 + seed + slot * 1.4) > -0.65);
        ctx.strokeStyle = blink ? col.hi : col.mid;
        ctx.lineWidth = Math.max(1.8, 3.0 * zoom);
        ctx.beginPath(); ctx.moveTo(...lA); ctx.lineTo(...lB); ctx.stroke();
      }}
      ctx.restore();
    }}

    function drawEngineerDesk(sp, dept, isTarget, camX, camY, zoom, prog) {{
      const wx = dept.x + sp.dx;
      const wy = dept.y + sp.dy;
      const col = PAL[dept.color] || PAL.cyan;
      const isActiveDept = dept.id === STATE.target_dept_id;

      // Circular glowing floor pedestal ring under chair
      const [rx, ry] = iso(wx, wy + 12, 1, camX, camY, zoom);
      ctx.save();
      const pulse = isTarget ? (1 + 0.18 * Math.sin(prog * Math.PI * 8)) : 1.0;
      ctx.strokeStyle = isTarget ? col.hi : col.hex + '77';
      ctx.lineWidth = isTarget ? 3.2 : 1.8;
      ctx.beginPath();
      ctx.ellipse(rx, ry, 25 * zoom * pulse, 14 * zoom * pulse, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // Sleek dark glass desk slab with bright wireframe rim
      drawPrism(wx, wy, 64, 36, 15, {{ hi: '#172542', mid: '#0C162B', lo: '#060B18' }}, camX, camY, zoom, 8);
      const dTop0 = iso(wx - 32, wy - 18, 23, camX, camY, zoom);
      const dTop1 = iso(wx + 32, wy - 18, 23, camX, camY, zoom);
      const dTop2 = iso(wx + 32, wy + 18, 23, camX, camY, zoom);
      const dTop3 = iso(wx - 32, wy + 18, 23, camX, camY, zoom);
      ctx.save();
      ctx.strokeStyle = isActiveDept ? col.hi : col.hex + '88'; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.moveTo(...dTop0); ctx.lineTo(...dTop1); ctx.lineTo(...dTop2); ctx.lineTo(...dTop3); ctx.closePath(); ctx.stroke();
      ctx.restore();

      // Dual angled glowing monitors with illuminated screen face
      drawPrism(wx - 14, wy - 10, 22, 5, 18, {{ hi: col.hi, mid: '#0B162C', lo: col.mid }}, camX, camY, zoom, 23);
      drawPrism(wx + 14, wy - 10, 22, 5, 18, {{ hi: col.hi, mid: '#0B162C', lo: col.mid }}, camX, camY, zoom, 23);

      // Seated engineer torso + white head sphere + dark office chair back
      const bob = Math.sin(prog * Math.PI * 10 + wx) * 1.4;
      drawPrism(wx, wy + 12, 18, 15, 22 + bob, {{ hi: col.hi, mid: col.hex, lo: col.lo }}, camX, camY, zoom, 8);
      drawPrism(wx, wy + 22, 16, 6, 26, {{ hi: '#334155', mid: '#1E293B', lo: '#0F172A' }}, camX, camY, zoom, 6);
      const [hx, hy] = iso(wx, wy + 12, 36 + bob, camX, camY, zoom);
      ctx.beginPath();
      ctx.arc(hx, hy, Math.max(4, 7.5 * zoom), 0, Math.PI * 2);
      ctx.fillStyle = '#F8FAFC'; ctx.fill();

      // Show crisp pill tags on all desks inside zoomed-in active department (capped smoothly so extreme zoom stays razor sharp)
      const badgeZoom = Math.min(1.65, zoom);
      if (isTarget && zoom >= 0.88) {{
        const [lx, ly] = iso(wx, wy - 20, 54, camX, camY, zoom);
        drawBadge(lx, ly, `• ${{sp.short}}`, '#061124F2', col.hi, badgeZoom);
      }} else if (isActiveDept && zoom >= 1.18) {{
        const [lx, ly] = iso(wx, wy - 20, 50, camX, camY, zoom);
        drawBadge(lx, ly, `• ${{sp.short}}`, '#091428DD', '#CBD5E1', badgeZoom * 0.88);
      }}
    }}

    function drawDrone(wx, wy, wz, camX, camY, zoom, prog, colHex) {{
      const [dx, dy] = iso(wx, wy, wz, camX, camY, zoom);
      const [gx, gy] = iso(wx, wy, 0, camX, camY, zoom);
      // Volumetric spotlight cone onto campus below
      ctx.save();
      const grad = ctx.createLinearGradient(dx, dy, gx, gy);
      grad.addColorStop(0, colHex + '88');
      grad.addColorStop(1, colHex + '08');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.moveTo(dx - 8 * zoom, dy);
      ctx.lineTo(dx + 8 * zoom, dy);
      ctx.lineTo(gx + 58 * zoom, gy);
      ctx.lineTo(gx - 58 * zoom, gy);
      ctx.closePath();
      ctx.fill();

      // Drone chassis & spinning rotors
      ctx.fillStyle = '#0F172A'; ctx.strokeStyle = colHex; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.roundRect(dx - 24 * zoom, dy - 9 * zoom, 48 * zoom, 18 * zoom, 8);
      ctx.fill(); ctx.stroke();
      const spin = Math.cos(prog * Math.PI * 36) * 16 * zoom;
      [-28, 28].forEach(ox => {{
        ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.moveTo(dx + ox * zoom - spin, dy - 12 * zoom);
        ctx.lineTo(dx + ox * zoom + spin, dy - 12 * zoom); ctx.stroke();
      }});
      ctx.fillStyle = '#FACC15';
      ctx.beginPath(); ctx.arc(dx, dy, 4.5 * zoom, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }}

    function drawWorld(prog) {{
      ctx.clearRect(0, 0, W, H);
      // Fast arrival: complete campus->desk travel within first 74%, then punch smoothly into the monitor portal
      const flyDone = STATE.dc_mode === 'campus_to_desk' ? 0.74 : 0.86;
      const ease = easeInOut(Math.min(1, prog / flyDone));
      let camX = STATE.start_cam.cx + (STATE.end_cam.cx - STATE.start_cam.cx) * ease;
      let camY = STATE.start_cam.cy + (STATE.end_cam.cy - STATE.start_cam.cy) * ease;
      let zoom = STATE.start_cam.zoom + (STATE.end_cam.zoom - STATE.start_cam.zoom) * ease;

      if (STATE.dc_mode === 'campus_to_desk' && prog > 0.76) {{
        const pPush = easeInOut((prog - 0.76) / 0.24);
        zoom *= (1.0 + 0.22 * pPush);
        camY -= 8 * pPush;
      }}

      // 1. Enterprise Campus Ground Grid (1800x1800)
      ctx.save();
      ctx.strokeStyle = 'rgba(56,189,248,0.10)'; ctx.lineWidth = 1;
      for (let g = 100; g <= 1700; g += 100) {{
        const a = iso(g, 100, 0, camX, camY, zoom), b = iso(g, 1700, 0, camX, camY, zoom);
        ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke();
        const c = iso(100, g, 0, camX, camY, zoom), d = iso(1700, g, 0, camX, camY, zoom);
        ctx.beginPath(); ctx.moveTo(...c); ctx.lineTo(...d); ctx.stroke();
      }}
      ctx.restore();

      // 2. Fiber Conduit Ring connecting Core Server Hall (900,900) -> All 10 Departments
      STATE.departments.forEach(d => {{
        const col = PAL[d.color] || PAL.cyan;
        const p0 = iso(900, 900, 3, camX, camY, zoom);
        const p1 = iso(d.x, d.y, 3, camX, camY, zoom);
        ctx.save();
        ctx.strokeStyle = d.id === STATE.target_dept_id ? col.hex : 'rgba(56,189,248,0.22)';
        ctx.lineWidth = d.id === STATE.target_dept_id ? 4 : 2;
        ctx.setLineDash([10, 8]);
        ctx.beginPath(); ctx.moveTo(...p0); ctx.lineTo(...p1); ctx.stroke();
        ctx.restore();
      }});

      // 3. Central Core Server Rack Hall + 4 Corner Cooling Towers
      for (let rx = -1; rx <= 1; rx++) {{
        for (let ry = -1; ry <= 1; ry++) {{
          drawPrism(900 + rx * 62, 900 + ry * 62, 36, 36, 72, PAL.blue, camX, camY, zoom, 0);
        }}
      }}
      const [hcx, hcy] = iso(900, 900, 96, camX, camY, zoom);
      drawBadge(hcx, hcy, 'CORE SERVER HALL', '#091124DD', '#60A5FA', zoom);

      [[120,120],[1680,120],[120,1680],[1680,1680]].forEach(([tx, ty]) => {{
        drawPrism(tx, ty, 78, 78, 86, {{ hi: '#475569', mid: '#334155', lo: '#1E293B' }}, camX, camY, zoom, 0);
      }});

      // 4. Department Floor Pads + Translucent Glass Back Walls + Server Racks
      STATE.departments.forEach((d, dIdx) => {{
        const col = PAL[d.color] || PAL.cyan;
        const isTgt = d.id === STATE.target_dept_id;
        const p0 = iso(d.x - d.w*0.5, d.y - d.h*0.5, 0, camX, camY, zoom);
        const p1 = iso(d.x + d.w*0.5, d.y - d.h*0.5, 0, camX, camY, zoom);
        const p2 = iso(d.x + d.w*0.5, d.y + d.h*0.5, 0, camX, camY, zoom);
        const p3 = iso(d.x - d.w*0.5, d.y + d.h*0.5, 0, camX, camY, zoom);
        ctx.save();
        ctx.beginPath(); ctx.moveTo(...p0); ctx.lineTo(...p1); ctx.lineTo(...p2); ctx.lineTo(...p3); ctx.closePath();
        ctx.fillStyle = isTgt ? col.hex + '22' : 'rgba(11,20,40,0.62)';
        ctx.fill();
        ctx.strokeStyle = isTgt ? col.hi : col.hex + '55';
        ctx.lineWidth = isTgt ? 2.8 : 1.4;
        ctx.stroke();
        ctx.restore();

        // Back glass wall + 3 glowing dark server racks behind desks
        drawGlassPartition(d, col, camX, camY, zoom);
        if (isTgt || zoom < 1.15) {{
          [-108, 0, 108].forEach((rxOff, rIdx) => {{
            drawServerRack(d.x + rxOff, d.y - d.h * 0.32, col, camX, camY, zoom, prog, dIdx * 7 + rIdx);
          }});
        }}
      }});

      // 5. Render all Specialist Engineer Workstations sorted back-to-front
      const sortedSpecs = [...STATE.specialists].sort((a, b) => {{
        const da = STATE.departments.find(d => d.id === a.dept_id);
        const db = STATE.departments.find(d => d.id === b.dept_id);
        if (!da || !db) return 0;
        return (da.x + a.dx + da.y + a.dy) - (db.x + b.dx + db.y + b.dy);
      }});
      sortedSpecs.forEach(sp => {{
        const dept = STATE.departments.find(d => d.id === sp.dept_id);
        if (!dept) return;
        const isTarget = sp.id === STATE.target_spec_id;
        drawEngineerDesk(sp, dept, isTarget, camX, camY, zoom, prog);
      }});

      // Department Sign Badges mounted cleanly on back glass wall (including engineer count like reference!)
      STATE.departments.forEach(d => {{
        const col = PAL[d.color] || PAL.cyan;
        const isTgt = d.id === STATE.target_dept_id;
        if (zoom >= 1.35 && !isTgt) return;
        const engCnt = STATE.specialists.filter(s => s.dept_id === d.id).length;
        const [bx, by] = iso(d.x, d.y - d.h * 0.46, 108, camX, camY, zoom);
        drawBadge(bx, by, `${{d.icon}} ${{d.name}} (${{engCnt}} Eng)`, isTgt ? '#061124F2' : '#0B162CCC', isTgt ? col.hi : '#CBD5E1', zoom);
      }});

      // 6. Active Travel Entity (Drone Escort or Fiber Data Orb) + Monitor Portal Glow
      if (STATE.dc_mode === 'campus_fly' || STATE.dc_mode === 'campus_to_desk') {{
        const u = easeInOut(Math.min(1, prog / (STATE.dc_mode === 'campus_to_desk' ? 0.72 : 0.88)));
        const tgtCol = (PAL[STATE.target_dept.color] || PAL.cyan).hex;
        if (STATE.travel_mode === 'drone') {{
          const drX = 900 + (STATE.eng_x - 900) * u;
          const drY = 900 + (STATE.eng_y - 900) * u;
          const drZ = 140 + Math.sin(u * Math.PI) * 90;
          drawDrone(drX, drY, drZ, camX, camY, zoom, prog, tgtCol);
        }} else if (STATE.travel_mode === 'fiber') {{
          const fx = 900 + (STATE.eng_x - 900) * u;
          const fy = 900 + (STATE.eng_y - 900) * u;
          const [ox, oy] = iso(fx, fy, 8, camX, camY, zoom);
          ctx.save();
          ctx.shadowColor = tgtCol; ctx.shadowBlur = 24;
          ctx.fillStyle = '#FFFFFF';
          ctx.beginPath(); ctx.arc(ox, oy, 11 * zoom, 0, Math.PI * 2); ctx.fill();
          ctx.strokeStyle = tgtCol; ctx.lineWidth = 4; ctx.stroke();
          ctx.restore();
        }}

        // Smooth monitor portal glow right at end of campus_to_desk (0.80 -> 1.00)
        if (STATE.dc_mode === 'campus_to_desk' && prog > 0.80) {{
          const gp = easeInOut((prog - 0.80) / 0.20);
          const [mx, my] = iso(STATE.eng_x, STATE.eng_y - 10, 26, camX, camY, zoom);
          ctx.save();
          const rad = Math.max(80, gp * Math.max(W, H) * 0.65);
          const rg = ctx.createRadialGradient(mx, my, rad * 0.08, mx, my, rad);
          rg.addColorStop(0, tgtCol + '66');
          rg.addColorStop(0.55, '#091124CC');
          rg.addColorStop(1, 'rgba(9,17,36,0.0)');
          ctx.fillStyle = rg;
          ctx.fillRect(0, 0, W, H);
          ctx.restore();
        }}
      }}
    }}

    window.__setStudioProgress = function(wp, lp) {{
      const t = Math.max(0, Math.min(1, Number(lp !== undefined ? lp : wp) || 0));
      drawWorld(t);
    }};
    window.__setStudioProgress(1.0, 1.0);
  </script>
</body>
</html>"""


def render_v5_datacenter_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
) -> Path:
    """Renders 2.5D Enterprise Data Center & IT Park Campus / Engineer Focus frames via Chromium."""
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    w, h = spec["width"], spec["height"]
    duration = max(1.4, float(scene.get("duration", 4.5)))
    total_frames = max(18, int(round(duration * VIDEO_FPS)))
    out_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.*"):
        try:
            old.unlink()
        except Exception:
            pass

    html_doc = _build_datacenter_html(scene, w, h, tone=tone)
    from core.web_generative_engine import detect_web_engine
    pw_ok, exe_path = detect_web_engine()
    if pw_ok:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-vsync"]}
        if exe_path:
            kwargs["executable_path"] = exe_path
        browser = p.chromium.launch(**kwargs)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="domcontentloaded", timeout=12000)

        sc_start = float(scene.get("start_time", 0.0))
        words = list(scene_words or [])
        for f in range(total_frames):
            lin_p = f / max(1, total_frames - 1)
            cur_t = sc_start + lin_p * duration
            if words:
                spoken = sum(1 for wd in words if float(wd.get("start", 0.0)) <= cur_t)
                word_p = spoken / max(1, len(words))
                word_blend = min(1.0, 0.72 * word_p + 0.28 * lin_p)
            else:
                word_blend = lin_p
            if lin_p >= 0.94:
                word_blend = 1.0
            page.evaluate(
                "(args) => { if (window.__setStudioProgress) window.__setStudioProgress(args.wp, args.lp); }",
                {"wp": round(word_blend, 4), "lp": round(lin_p, 4)},
            )
            page.screenshot(path=str(out_dir / f"frame_{f:04d}.jpg"), type="jpeg", quality=90)

        browser.close()
        p.stop()
        return out_dir

    # Graceful headless Pillow fallback
    from PIL import Image, ImageDraw
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (9, 17, 36))
    draw = ImageDraw.Draw(img)
    draw.rectangle([48, 220, w - 48, h - 220], outline=(56, 189, 248), width=3)
    draw.text((76, 110), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(248, 250, 252))
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir


def blend_datacenter_scene_transitions(
    aligned_scenes: List[Dict[str, Any]],
    frame_dirs: List[Path],
    transition_frames: int = 12,
) -> None:
    """
    Smoothly zooms & cross-dissolves the opening frames of any scene entering from or exiting to
    `v5_datacenter_park` so the transition from Engineer Desk -> Main Content Window feels seamless.
    Preserves exact frame count per scene (zero audio/subtitle drift).
    """
    from PIL import Image

    if len(aligned_scenes) < 2 or len(frame_dirs) != len(aligned_scenes):
        return

    for idx in range(len(aligned_scenes) - 1):
        vt_a = str(aligned_scenes[idx].get("visual_type") or "")
        vt_b = str(aligned_scenes[idx + 1].get("visual_type") or "")
        if vt_a != "v5_datacenter_park" and vt_b != "v5_datacenter_park":
            continue

        dir_a, dir_b = frame_dirs[idx], frame_dirs[idx + 1]
        if not dir_a.exists() or not dir_b.exists():
            continue
        frames_a = sorted(p for p in dir_a.iterdir() if p.name.startswith("frame_") and p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        frames_b = sorted(p for p in dir_b.iterdir() if p.name.startswith("frame_") and p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        if not frames_a or len(frames_b) < 4:
            continue

        n_blend = min(int(transition_frames), len(frames_b) // 2)
        if n_blend < 3:
            continue

        try:
            tail_im = Image.open(frames_a[-1]).convert("RGB")
            w, h = tail_im.size
            for k in range(n_blend):
                t = (k + 1) / float(n_blend + 1)
                ease = t * t * (3.0 - 2.0 * t)
                fb_path = frames_b[k]
                fg_im = Image.open(fb_path).convert("RGB")
                if fg_im.size != (w, h):
                    fg_im = fg_im.resize((w, h), Image.Resampling.BILINEAR)

                # Zoom-up reveal for main content window emerging from engineer workstation
                if vt_a == "v5_datacenter_park" and vt_b != "v5_datacenter_park":
                    scale = 0.80 + 0.20 * ease
                    sw, sh = max(16, int(round(w * scale))), max(16, int(round(h * scale)))
                    scaled = fg_im.resize((sw, sh), Image.Resampling.BILINEAR)
                    bg_zoom = tail_im.copy()
                    # Subtle push-in on background desk frame too
                    bg_s = 1.0 + 0.14 * ease
                    bw, bh = int(round(w * bg_s)), int(round(h * bg_s))
                    bg_crop = tail_im.resize((bw, bh), Image.Resampling.BILINEAR).crop(
                        ((bw - w) // 2, (bh - h) // 2, (bw - w) // 2 + w, (bh - h) // 2 + h)
                    )
                    bg_zoom.paste(scaled, ((w - sw) // 2, (h - sh) // 2))
                    out_im = Image.blend(bg_crop, bg_zoom, ease)
                else:
                    out_im = Image.blend(tail_im, fg_im, ease)

                out_im.save(fb_path, quality=92)
        except Exception:
            continue
