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
    {"id": "audit_iso", "dept_id": "audit_grc", "title": "IT Audit & Compliance Policy Lead", "short": "Audit & Policy", "tools": "ISO 27001 · SOC2 · WORM Audit Trails", "handoff": "blueprint_whiteboard", "dx": -60, "dy": 0, "keywords": ["audit", "compliance", "soc2", "iso", "grc", "governance", "pci", "rbi"]},
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


def match_datacenter_specialist(topic: str, preferred_travel: str = "auto") -> Dict[str, Any]:
    """Deterministically matches a prompt topic to the best Department, Specialist Engineer, and Travel Mode."""
    low = f" {str(topic or '').lower()} "
    best_sp = DC_SPECIALISTS[8]  # default: data_ingest
    best_score = -1
    for sp in DC_SPECIALISTS:
        score = sum(3 if len(k.strip()) >= 5 else 2 for k in sp["keywords"] if k in low)
        if score > best_score:
            best_score = score
            best_sp = sp
    if best_score <= 0:
        best_sp = DC_SPECIALISTS[10]  # default: Snowflake / Data Engineer

    dept = next((d for d in DC_DEPARTMENTS if d["id"] == best_sp["dept_id"]), DC_DEPARTMENTS[0])

    travel = str(preferred_travel or "auto").lower().strip()
    if travel not in ("camera", "drone", "fiber"):
        if dept["id"] in ("infosec", "audit_grc", "ad_iam", "ai_agents"):
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
    }


def _compute_dc_camera(
    dc_mode: str,
    dept: Dict[str, Any],
    eng_x: float,
    eng_y: float,
    width: int,
    height: int,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Computes fast start/end camera keyframes across the 1800x1800 campus."""
    is_wide = width > height
    campus_zoom = 0.62 if is_wide else 0.48
    dept_zoom = 1.25 if is_wide else 1.08
    desk_zoom = 1.92 if is_wide else 1.72

    if dc_mode == "campus_to_desk":
        # Fast 1-scene arrival: Macro Campus -> Straight onto Engineer Desk!
        start = {"cx": 900.0, "cy": 900.0, "zoom": campus_zoom}
        end = {"cx": float(eng_x), "cy": float(eng_y), "zoom": desk_zoom}
    elif dc_mode == "campus_fly":
        start = {"cx": 900.0, "cy": 900.0, "zoom": campus_zoom}
        end = {"cx": float(dept["x"]), "cy": float(dept["y"]), "zoom": dept_zoom}
    elif dc_mode == "desk_focus":
        start = {"cx": float(dept["x"]), "cy": float(dept["y"]), "zoom": dept_zoom}
        end = {"cx": float(eng_x), "cy": float(eng_y), "zoom": desk_zoom}
    else:  # campus_outro
        start = {"cx": float(eng_x), "cy": float(eng_y), "zoom": round(desk_zoom * 0.85, 2)}
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
        "departments": DC_DEPARTMENTS,
        "specialists": DC_SPECIALISTS,
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

    function drawEngineerDesk(sp, dept, isTarget, camX, camY, zoom, prog) {{
      const wx = dept.x + sp.dx;
      const wy = dept.y + sp.dy;
      const col = PAL[dept.color] || PAL.cyan;

      // Desk slab
      drawPrism(wx, wy, 58, 34, 16, {{ hi: '#334155', mid: '#1E293B', lo: '#0F172A' }}, camX, camY, zoom, 0);
      // Dual glowing monitors
      drawPrism(wx - 12, wy - 10, 18, 6, 16, col, camX, camY, zoom, 16);
      drawPrism(wx + 12, wy - 10, 18, 6, 16, col, camX, camY, zoom, 16);
      // Engineer torso + head with subtle typing bounce
      const bob = Math.sin(prog * Math.PI * 10 + wx) * 1.6;
      drawPrism(wx, wy + 12, 18, 16, 22 + bob, {{ hi: col.hi, mid: '#1D4ED8', lo: '#1E3A8A' }}, camX, camY, zoom, 4);
      const [hx, hy] = iso(wx, wy + 12, 34 + bob, camX, camY, zoom);
      ctx.beginPath();
      ctx.arc(hx, hy, Math.max(4, 7 * zoom), 0, Math.PI * 2);
      ctx.fillStyle = '#FDE68A'; ctx.fill();

      if (isTarget) {{
        // Pulsing floor beacon ring around target engineer
        const pulse = 1 + 0.22 * Math.sin(prog * Math.PI * 6);
        const [bx, by] = iso(wx, wy, 2, camX, camY, zoom);
        ctx.save();
        ctx.strokeStyle = col.hex; ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.ellipse(bx, by, 44 * zoom * pulse, 24 * zoom * pulse, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        if (zoom >= 0.88) {{
          const [lx, ly] = iso(wx, wy, 64, camX, camY, zoom);
          drawBadge(lx, ly, `👨‍💻 ${{sp.short}}`, '#091124EE', col.hi, zoom * 1.1);
        }}
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
      // Fast arrival: complete campus->desk travel within first 78% so final moments lock on the engineer desk
      const flyDone = STATE.dc_mode === 'campus_to_desk' ? 0.74 : 0.86;
      const ease = easeInOut(Math.min(1, prog / flyDone));
      const camX = STATE.start_cam.cx + (STATE.end_cam.cx - STATE.start_cam.cx) * ease;
      const camY = STATE.start_cam.cy + (STATE.end_cam.cy - STATE.start_cam.cy) * ease;
      const zoom = STATE.start_cam.zoom + (STATE.end_cam.zoom - STATE.start_cam.zoom) * ease;

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

      // 4. Department Glass Floor Pads + Banners
      STATE.departments.forEach(d => {{
        const col = PAL[d.color] || PAL.cyan;
        const isTgt = d.id === STATE.target_dept_id;
        const p0 = iso(d.x - d.w*0.5, d.y - d.h*0.5, 0, camX, camY, zoom);
        const p1 = iso(d.x + d.w*0.5, d.y - d.h*0.5, 0, camX, camY, zoom);
        const p2 = iso(d.x + d.w*0.5, d.y + d.h*0.5, 0, camX, camY, zoom);
        const p3 = iso(d.x - d.w*0.5, d.y + d.h*0.5, 0, camX, camY, zoom);
        ctx.save();
        ctx.beginPath(); ctx.moveTo(...p0); ctx.lineTo(...p1); ctx.lineTo(...p2); ctx.lineTo(...p3); ctx.closePath();
        ctx.fillStyle = isTgt ? col.hex + '28' : 'rgba(15,23,42,0.55)';
        ctx.fill();
        ctx.strokeStyle = isTgt ? col.hex : col.hex + '66';
        ctx.lineWidth = isTgt ? 3.2 : 1.5;
        ctx.stroke();
        ctx.restore();
      }});

      // 5. Render all 20 Specialist Engineer Workstations sorted back-to-front
      const sortedSpecs = [...STATE.specialists].sort((a, b) => {{
        const da = STATE.departments.find(d => d.id === a.dept_id);
        const db = STATE.departments.find(d => d.id === b.dept_id);
        return (da.x + a.dx + da.y + a.dy) - (db.x + b.dx + db.y + b.dy);
      }});
      sortedSpecs.forEach(sp => {{
        const dept = STATE.departments.find(d => d.id === sp.dept_id);
        if (!dept) return;
        const isTarget = sp.id === STATE.target_spec_id;
        drawEngineerDesk(sp, dept, isTarget, camX, camY, zoom, prog);
      }});

      // Department Sign Badges on campus view
      if (zoom < 1.35) {{
        STATE.departments.forEach(d => {{
          const col = PAL[d.color] || PAL.cyan;
          const isTgt = d.id === STATE.target_dept_id;
          const [bx, by] = iso(d.x, d.y - d.h * 0.44, 42, camX, camY, zoom);
          drawBadge(bx, by, `${{d.icon}} ${{d.name}}`, isTgt ? '#091124F2' : '#0F172ACC', isTgt ? col.hi : '#CBD5E1', zoom);
        }});
      }}

      // 6. Active Travel Entity (Drone Escort or Fiber Data Orb) during Campus Fly
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
