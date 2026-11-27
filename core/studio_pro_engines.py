"""
Specialized 2026 Studio Visual Engines (V17, V18, V19, V21, V23, V24, V25, V26, V27, V28).

All 10 Studios render crisp 2026 dark-navy animated HTML5/SVG scenes via the shared
Chromium Playwright 4K/60FPS pipeline (`capture_studio_playwright_frames`), tightly locked
to spoken word timestamps (`compute_synced_visual_progress`).
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, GEMINI_API_KEY, GROQ_API_KEY, OUTPUT_DIR, VIDEO_FPS
from core.tone_engine import get_tone_profile

STUDIO_PRO_OPTIONS: List[Tuple[str, str]] = [
    ("v17_sql_simulator", "🧬 Studio V17 — SQL Joins, WHERE/HAVING, GROUP BY & Window Simulator (Row Match & Rank Highlights)"),
    ("v18_agent_loop", "🧠 Studio V18 — ReAct / LangGraph / MCP Agent Loop (Thought → MCP Tool → Observation → Answer)"),
    ("v19_storage_pruning", "🗄️ Studio V19 — DB & Parquet Storage Internals (B+ Tree, Micro-Partitions, Full Scan vs Pruning)"),
    ("v21_api_inspector", "🌐 Studio V21 — API, Webhook & MCP Inspector (Payload Diff, OAuth/JWT, Status Badges & Latency)"),
    ("v23_decision_tree", "🗺️ Studio V23 — Decision Tree & Trade-Off Navigator (ETL vs ELT, SQL vs NoSQL, Winner Badge)"),
    ("v24_editorial_cards", "📰 Studio V24 — Editorial Motion Cards & Myth-Buster (Kinetic Cards, Spotlight Quotes & Code Mistakes)"),
    ("v25_iceberg_lakehouse", "🧊 Studio V25 — Apache Iceberg V4, Snowflake & AWS (Single Copy → Multi-Engine + Cost/Pruning Meter)"),
    ("v26_multi_agent_ops", "🤖 Studio V26 — Autonomous Multi-Agent & MCP Guardrails (Plan → Tool → Policy/Audit → Verified Out)"),
    ("v27_cdc_contracts", "🔄 Studio V27 — Data Migration, CDC & Data Contracts (Source → Schema Contract → Zero-Downtime Sync)"),
    ("v28_semantic_eval_hub", "⚙️ Studio V28 — Python, SQL, Analytics, DS & SE Hub (Semantic Layer + Vector Flow + Eval Pass Badges)"),
]

STUDIO_PRO_KEYS = tuple(k for k, _ in STUDIO_PRO_OPTIONS)

_ACCENT_HEX = {
    "cyan": "#38BDF8",
    "emerald": "#34D399",
    "amber": "#FBBF24",
    "rose": "#F43F5E",
    "purple": "#C084FC",
    "blue": "#60A5FA",
}


def _studio_pro_label(mode_key: str) -> str:
    for k, lbl in STUDIO_PRO_OPTIONS:
        if k == mode_key:
            return lbl.split("(")[0].strip()
    return mode_key


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _build_fallback_scenes(topic: str, mode_key: str, tone: str, watermark: str, cta_keyword: str) -> List[Dict[str, Any]]:
    clean_t = str(topic or "Modern System Architecture").strip()[:54]
    short_t = " ".join(clean_t.split()[:4]) or "System"
    cta = f"Comment '{cta_keyword.strip().upper()}' 👇" if cta_keyword.strip() else "Save & follow for more!"

    if mode_key == "v17_sql_simulator":
        return [
            {
                "role": "hook",
                "narration": f"अरे रुको... {short_t} में लोग JOIN और WHERE को एक ही समझ लेते हैं, और वहीं पूरा result गलत हो जाता है!",
                "visual_data": {
                    "hud_pill": "SQL EXECUTION TRAP", "headline_white": "JOIN vs WHERE", "headline_accent": "Row Trap!", "accent_color": "rose",
                    "sql_clause": "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.uid WHERE o.amt > 500;",
                    "left_rows": ["u1 | Aarav", "u2 | Priya", "u3 | Rohan"],
                    "right_rows": ["o1 | u1 | 900", "o2 | u1 | 200", "o3 | NULL"],
                    "match_indices": [0], "dropped_indices": [1, 2],
                    "result_badge": "WHERE killed NULL rows!", "metric": "LEFT JOIN Broken",
                    "footer_note": "WHERE runs AFTER the JOIN and removes NULL rows!",
                },
            },
            {
                "role": "solution",
                "narration": "सही तरीका देखो... filter condition को ON या HAVING में रखो, और Window function से exact rank निकालो!",
                "visual_data": {
                    "hud_pill": "PRO SQL FLOW", "headline_white": "ON + GROUP BY", "headline_accent": "DENSE_RANK()", "accent_color": "emerald",
                    "sql_clause": "LEFT JOIN orders o ON u.id=o.uid AND o.amt>500 ... DENSE_RANK() OVER(ORDER BY total DESC)",
                    "left_rows": ["u1 | Aarav (#1)", "u2 | Priya (#2)", "u3 | Rohan (#3)"],
                    "right_rows": ["amt: 900 ✓", "amt: 0 (kept!)", "amt: 0 (kept!)"],
                    "match_indices": [0, 1, 2], "dropped_indices": [],
                    "result_badge": "All 3 Users Preserved ✓", "metric": "100% Accurate Rank",
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v18_agent_loop":
        return [
            {
                "role": "hook",
                "narration": f"सिर्फ ChatGPT को prompt देने से {short_t} production-ready नहीं बनता... असली AI Agent एक Think-Tool-Observe loop चलाता है!",
                "visual_data": {
                    "hud_pill": "REACT / LANGGRAPH", "headline_white": "Single Prompt vs", "headline_accent": "Agent Loop.", "accent_color": "cyan",
                    "active_step": 1,
                    "steps": [
                        ("1. THOUGHT", "Need live DB lag & schema metrics"),
                        ("2. MCP TOOL", "call mcp.query_warehouse(table='L2')"),
                        ("3. OBSERVE", "lag=0.8s, 4 partitions pruned"),
                        ("4. ANSWER", "Verified root-cause + fix emitted ✓"),
                    ],
                    "trace_line": "loop_iter=2 | tool_calls=2 | hallucination=0%", "metric": "LangGraph + MCP",
                    "footer_note": "Observation grounds the next reasoning step!",
                },
            },
            {
                "role": "solution",
                "narration": f"हर iteration में MCP tool real data लाता है, LangGraph state verify करता है, और तभी final answer निकलता है — {cta}",
                "visual_data": {
                    "hud_pill": "LOOP VERIFIED", "headline_white": "4-Node MCP", "headline_accent": "State Cycle.", "accent_color": "emerald",
                    "active_step": 3,
                    "steps": [
                        ("1. THOUGHT", "Plan verified sub-tasks"),
                        ("2. MCP TOOL", "Typed JSON schema call"),
                        ("3. OBSERVE", "Assert tool output non-empty"),
                        ("4. ANSWER", "Final response grounded in tool data ✓"),
                    ],
                    "trace_line": "state=CONVERGED | grounded=True | p99=420ms", "metric": "99.4% Grounded",
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v19_storage_pruning":
        return [
            {
                "role": "problem",
                "narration": f"{short_t} में बिना Partition Key और Zone Map के query पूरे 1,000 GB blocks scan करती है... बिल भी बढ़ता है और speed भी मरती है!",
                "visual_data": {
                    "hud_pill": "STORAGE FULL SCAN", "headline_white": "Full Table Scan", "headline_accent": "Kills Speed!", "accent_color": "rose",
                    "scan_mode": "full",
                    "query_box": "WHERE event_date = '2026-11-27'  (No Partition / No Index)",
                    "blocks": [("B01", "Jan"), ("B02", "Feb"), ("B03", "Mar"), ("B04", "Apr"), ("B05", "May"), ("B06", "Nov ✓"), ("B07", "Jul"), ("B08", "Aug")],
                    "scanned_indices": [0, 1, 2, 3, 4, 5, 6, 7],
                    "left_metric": "8/8 Blocks Scanned", "right_metric": "18.4s · High Cost",
                    "footer_note": "Full Scan reads 100% Parquet / B+ Tree pages!",
                },
            },
            {
                "role": "solution",
                "narration": f"जैसे ही Min-Max metadata या B+ Tree pruning ऑन होती है, 95% blocks सीधे SKIP हो जाते हैं — और query 14x तेज़ चलती है! {cta}",
                "visual_data": {
                    "hud_pill": "MICRO-PARTITION PRUNING", "headline_white": "Min-Max Pruning", "headline_accent": "Skips 95% Data!", "accent_color": "emerald",
                    "scan_mode": "pruned",
                    "query_box": "Parquet RowGroup / Snowflake Micro-Partition ZoneMap: min='2026-11-01', max='2026-11-30'",
                    "blocks": [("B01", "SKIP"), ("B02", "SKIP"), ("B03", "SKIP"), ("B04", "SKIP"), ("B05", "SKIP"), ("B06", "MATCH ✓"), ("B07", "SKIP"), ("B08", "SKIP")],
                    "scanned_indices": [5],
                    "left_metric": "1/8 Blocks Scanned", "right_metric": "1.2s · 15x Faster",
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v21_api_inspector":
        return [
            {
                "role": "hook",
                "narration": f"{short_t} में सिर्फ endpoint बनाना काफी नहीं... auth header, rate limit और payload contract टूटते ही API 401/429 फेंकती है!",
                "visual_data": {
                    "hud_pill": "API & MCP INSPECTOR", "headline_white": "Payload Diff &", "headline_accent": "Auth Guard.", "accent_color": "cyan",
                    "method": "POST", "endpoint": "/v1/mcp/tools/execute", "status_code": "200 OK", "latency": "38ms p99",
                    "auth_badge": "OAuth 2.1 + mTLS Token Valid ✓",
                    "diff_lines": [
                        ("- payload: { user: 'raw_string', retry: false }", "bad"),
                        ("+ payload: { user_id: 4092, idempotency_key: 'uuid' }", "good"),
                        ("+ headers: { Authorization: 'Bearer eyJ...', Trace: '9f2a' }", "good"),
                    ],
                    "footer_note": "Idempotency key + OAuth scope stops duplicate webhooks!",
                },
            },
            {
                "role": "solution",
                "narration": f"Strict schema validation, webhook signature verification और retry backoff के साथ API zero-error चलती है — {cta}",
                "visual_data": {
                    "hud_pill": "WEBHOOK VERIFIED", "headline_white": "Zero-Retry-Storm", "headline_accent": "API Design.", "accent_color": "emerald",
                    "method": "POST", "endpoint": "/webhooks/events/verified", "status_code": "200 OK", "latency": "19ms p99",
                    "auth_badge": "HMAC-SHA256 Signature + Schema Pass ✓",
                    "diff_lines": [
                        ("- status: 429 Too Many Requests (blind retry loop)", "bad"),
                        ("+ status: 200 OK (exponential backoff + DLQ)", "good"),
                        ("+ contract: schema_v3 validated before queue", "good"),
                    ],
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v23_decision_tree":
        return [
            {
                "role": "hook",
                "narration": f"{short_t} में कौनसा architecture चुनें? हर जगह एक ही tool ठोकने से cost फटती है — ये 20-second decision tree देखो!",
                "visual_data": {
                    "hud_pill": "DECISION MATRIX", "headline_white": "ETL vs ELT vs", "headline_accent": "Streaming?", "accent_color": "amber",
                    "root_q": "IF Latency Required < 5 Seconds?",
                    "yes_branch": ("YES → STREAMING CDC", "Kafka / Flink / DMS", True),
                    "no_branch": ("NO → CLOUD ELT", "S3 + Snowflake / dbt", False),
                    "matrix": [("Throughput", "100k msg/s", "Batch GB/hr"), ("Freshness", "Sub-second", "15m – 24h"), ("Ops Cost", "Medium", "Low")],
                    "winner": "WINNER: STREAMING CDC (Real-Time) ✓",
                    "footer_note": cta,
                },
            },
            {
                "role": "solution",
                "narration": f"ACID transactions और structured joins चाहिए तो SQL चुनें, massive unstructured scale चाहिए तो NoSQL + Lakehouse — {cta}",
                "visual_data": {
                    "hud_pill": "FINAL PICK", "headline_white": "SQL vs NoSQL", "headline_accent": "Final Pick.", "accent_color": "emerald",
                    "root_q": "IF Strict ACID & Multi-Table Joins?",
                    "yes_branch": ("YES → RELATIONAL SQL", "Postgres / Snowflake", True),
                    "no_branch": ("NO → NOSQL / KV", "DynamoDB / Redis", False),
                    "matrix": [("Consistency", "ACID Strong", "Eventual / Tunable"), ("Schema", "Enforced", "Flexible JSON"), ("Best For", "Ledger & BI", "Session & Feeds")],
                    "winner": "PICK BASED ON ACCESS PATTERN ✓",
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v24_editorial_cards":
        return [
            {
                "role": "hook",
                "narration": f"90% developers {short_t} में एक ही classic coding mistake करते हैं — और interview में यहीं पकड़े जाते हैं!",
                "visual_data": {
                    "hud_pill": "MYTH-BUSTER SPOTLIGHT", "headline_white": "Stop This", "headline_accent": "Coding Myth!", "accent_color": "rose",
                    "quote": f'"{short_t} works fine in local testing — until 10x traffic hits production."',
                    "wrong_card": ("THE MYTH / MISTAKE", "Manual sync loops, unindexed lookups & zero backpressure"),
                    "right_card": ("PRO PATTERN", "Batch / indexed execution, async queues & observable SLAs"),
                    "metric": "100x More Reliable",
                    "footer_note": "Production tests what local toys hide!",
                },
            },
            {
                "role": "solution",
                "narration": f"बस यह 2 editorial principles अपनाओ और आपका system और interview दोनों rock-solid हो जाएंगे — {cta}",
                "visual_data": {
                    "hud_pill": "EDITORIAL TAKEAWAY", "headline_white": "Clean Engineering", "headline_accent": "Standard.", "accent_color": "emerald",
                    "quote": '"Simplicity + observability beats clever hacks in every real system."',
                    "wrong_card": ("AVOID BLIND COMPLEXITY", "Over-engineered layers with zero alerts"),
                    "right_card": ("SHIP VERIFIED PATTERNS", "Clear contracts, bounded retries & fast rollback"),
                    "metric": "99.99% Uptime",
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v25_iceberg_lakehouse":
        return [
            {
                "role": "hook",
                "narration": f"एक ही data की 4 अलग copies बनाकर Snowflake, Spark और Athena का बिल क्यों भरना? Apache Iceberg V4 एक single copy से सबको चलाता है!",
                "visual_data": {
                    "hud_pill": "ICEBERG V4 LAKEHOUSE", "headline_white": "One Data Copy.", "headline_accent": "Every Engine.", "accent_color": "cyan",
                    "catalog_title": "APACHE ICEBERG V4 CATALOG + S3 PARQUET",
                    "catalog_sub": "Atomic Snapshots · Deletion Vectors · Partition Evolution",
                    "engines": [("❄️ SNOWFLAKE", "Direct Iceberg Read"), ("⚡ APACHE SPARK", "Zero-Copy Write/ML"), ("🔍 TRINO / ATHENA", "Ad-Hoc BI SQL")],
                    "cost_meter": "-72% Storage & Zero ETL Duplication", "pruning_pct": 91,
                    "footer_note": "Single open Parquet copy + multi-engine ACID transactions!",
                },
            },
            {
                "role": "solution",
                "narration": f"Iceberg V4 के metadata pruning और deletion vectors से multi-engine queries blazing fast और cost-effective चलती हैं — {cta}",
                "visual_data": {
                    "hud_pill": "COST & PRUNING METER", "headline_white": "Zero Duplication", "headline_accent": "Lakehouse.", "accent_color": "emerald",
                    "catalog_title": "OPEN TABLE FORMAT (ICEBERG + AWS S3)",
                    "catalog_sub": "Time Travel · Schema Evolution · Partition Pruning",
                    "engines": [("❄️ SNOWFLAKE", "Read Snapshot v42"), ("🤖 AI / FEATURE STORE", "Read Parquet Vectors"), ("📊 BI DASHBOARD", "Sub-second Pruning")],
                    "cost_meter": "91% Files Pruned · 3.8x Lower Bill", "pruning_pct": 91,
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v26_multi_agent_ops":
        return [
            {
                "role": "hook",
                "narration": f"Production AI Agents को बिना Policy Guard और Audit Check के सीधे DB/API देना खतरनाक है — {short_t} का असली 4-step pipeline देखो!",
                "visual_data": {
                    "hud_pill": "MULTI-AGENT + GUARD", "headline_white": "Autonomous Agents", "headline_accent": "With Guardrails.", "accent_color": "purple",
                    "stages": [
                        ("1. PLANNER AGENT", "Decomposes goal into safe sub-steps", "cyan"),
                        ("2. MCP TOOL CALLS", "SQL / Vector RAG / API Executors", "amber"),
                        ("3. POLICY & AUDIT", "PII Masking · RBAC · SQL Read-Only ✓", "emerald"),
                        ("4. VERIFIED OUTPUT", "Citation + schema check before user", "cyan"),
                    ],
                    "audit_badge": "ZERO UNSAFE WRITES · AUDIT TRAIL LOGGED",
                    "footer_note": "Never skip the Policy/Audit checkpoint before execution!",
                },
            },
            {
                "role": "solution",
                "narration": f"Planner + MCP Tools + Policy Audit Gate मिलकर 100% reliable और auditable AI output देते हैं — {cta}",
                "visual_data": {
                    "hud_pill": "PRODUCTION VERIFIED", "headline_white": "Auditable AI", "headline_accent": "Agent Ops.", "accent_color": "emerald",
                    "stages": [
                        ("1. ROUTER PLAN", "Select specialist agent + budget cap", "cyan"),
                        ("2. SANDBOXED MCP", "Timeout + least-privilege tokens", "amber"),
                        ("3. GUARD VERIFIER", "Fact ground >= 98% · Policy PASS ✓", "emerald"),
                        ("4. FINAL RESPONSE", "Clean answer + trace telemetry", "emerald"),
                    ],
                    "audit_badge": "SOC2 / ENTERPRISE SAFE AGENT LOOP ✓",
                    "footer_note": cta,
                },
            },
        ]

    if mode_key == "v27_cdc_contracts":
        return [
            {
                "role": "hook",
                "narration": f"{short_t} migration में अगर source team ने एक column बदल दिया, तो पूरा downstream warehouse रात को फट जाता है!",
                "visual_data": {
                    "hud_pill": "CDC + DATA CONTRACTS", "headline_white": "Schema Drift", "headline_accent": "Breaks ETL!", "accent_color": "rose",
                    "source_lbl": "SOURCE OLTP WAL", "contract_lbl": "SCHEMA CONTRACT GATE", "target_lbl": "CLOUD WAREHOUSE",
                    "checks": [("Type & Null Check", "PASS ✓"), ("Breaking Rename", "BLOCKED → DLQ ✗"), ("Lag SLA < 2s", "MONITORED")],
                    "sync_pct": 98, "downtime": "0ms Downtime",
                    "footer_note": "Data Contracts catch breaking schema changes before L2 breaks!",
                },
            },
            {
                "role": "solution",
                "narration": f"CDC Stream के बीच Schema Contract Gate और Shadow Parity Check लगाने से zero-downtime migration 100% safe होती है — {cta}",
                "visual_data": {
                    "hud_pill": "ZERO-DOWNTIME SYNC", "headline_white": "Contract-Safe", "headline_accent": "Live Migration.", "accent_color": "emerald",
                    "source_lbl": "ORACLE / RDS CDC", "contract_lbl": "CONTRACT REGISTRY ✓", "target_lbl": "SNOWFLAKE L0→L2",
                    "checks": [("Schema Contract v4", "VALIDATED ✓"), ("Row Count Parity", "100.00% MATCH ✓"), ("Cutover Switch", "0ms DOWNTIME ✓")],
                    "sync_pct": 100, "downtime": "0ms Downtime · Parity 100%",
                    "footer_note": cta,
                },
            },
        ]

    # v28_semantic_eval_hub (default & Python/SQL/Analytics/DS/SE hub)
    return [
        {
            "role": "hook",
            "narration": f"Data, AI और Software Engineering को जोड़ने का असली secret है: एक clean Semantic Layer, Feature/Vector flow और Automated Eval checks!",
            "visual_data": {
                "hud_pill": "FULL-STACK DATA/AI", "headline_white": "Semantic Layer +", "headline_accent": "Eval Gates.", "accent_color": "cyan",
                "layers": [
                    ("SEMANTIC & METRICS", "Single KPI definitions (SQL / dbt Metrics)"),
                    ("PYTHON + VECTOR FLOW", "Async pipelines, embeddings & feature transforms"),
                    ("AUTOMATED EVAL & CI", "Unit tests · Data quality · LLM eval passes"),
                ],
                "badges": [("UNIT TESTS", "14/14 PASS ✓"), ("SQL PARITY", "100% ✓"), ("AI EVAL", "96.8% ✓")],
                "footer_note": "Same metric definitions across BI, Python ML & AI Agents!",
            },
        },
        {
            "role": "solution",
            "narration": f"जब Semantic definitions, code tests और eval badges एक pipeline में जुड़ते हैं, तब production bugs 90% कम होते हैं — {cta}",
            "visual_data": {
                "hud_pill": "PRODUCTION BENCHMARK", "headline_white": "Unified DS, AI", "headline_accent": "& SE Flow.", "accent_color": "emerald",
                "layers": [
                    ("1. GOVERNED METRICS", "Zero conflicting revenue/churn numbers"),
                    ("2. FEATURE + VECTOR", "Real-time Python + Hybrid RAG embeddings"),
                    ("3. CONTINUOUS EVAL", "Regression gate blocks drift before deploy ✓"),
                ],
                "badges": [("PYTEST CI", "PASS ✓"), ("DATA DRIFT", "0.02 OK ✓"), ("LATENCY", "14ms p99 ✓")],
                "footer_note": cta,
            },
        },
    ]


def _generate_pro_llm(
    topic: str,
    mode_key: str,
    tone: str,
    duration_mode: str,
    voice: str,
    watermark: str,
    audience_level: str,
    hook_style: str,
    cta_style: str,
    cta_keyword: str,
) -> Optional[List[Dict[str, Any]]]:
    from core.studio_v2_director import _language_rule, _scene_count_guidance

    lang_instr = _language_rule(voice, topic, tone=tone)
    sc_guide = _scene_count_guidance(duration_mode, "blueprint_whiteboard")
    cta_note = f"Comment '{cta_keyword.strip().upper()}'" if cta_style == "comment_keyword" and cta_keyword.strip() else "Save & follow!"
    fb_example = json.dumps(_build_fallback_scenes(topic, mode_key, tone, watermark, cta_keyword), ensure_ascii=False)

    prompt = f"""You are {_studio_pro_label(mode_key)} Visual Director.
Design a crisp, high-retention 9:16 storyboard JSON for topic: "{topic}"
Audience: {audience_level} | Hook: {hook_style} | Final CTA: {cta_note}
Target Pacing: {sc_guide} (generate 4 to 7 rich focused scenes!)
{lang_instr}

STRICT JSON SCHEMA: Follow the exact keys inside each scene's `visual_data` shown in this reference structure for `{mode_key}` (adapt EVERY label, SQL, metric, node, and quote 100% to "{topic}" — keep headlines <= 4 words white + <= 3 words accent!):
Reference example:
{fb_example}

Return STRICT JSON ONLY:
{{ "scenes": [ {{ "scene_id": 1, "role": "hook|problem|solution|proof|cta", "sfx_cue": "punch_impact|pop_snap|whoosh|success_chime", "narration": "...", "visual_data": {{...}} }} ] }}"""

    raw = ""
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    cand = str(getattr(res, "text", "") or "").strip()
                    if cand:
                        raw = cand
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if not raw and GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                timeout=20,
            )
            raw = res.choices[0].message.content.strip() if res.choices else ""
        except Exception:
            pass

    parsed = _extract_json(raw)
    if not parsed or not isinstance(parsed.get("scenes"), list) or len(parsed["scenes"]) < 2:
        return None
    return parsed["scenes"]


def generate_studio_pro_timeline(
    topic: str,
    mode_key: str,
    tone: str = "auto_2026_director",
    duration_mode: str = "auto",
    voice: str = "",
    watermark: str = DEFAULT_WATERMARK,
    audience_level: str = "mid_senior",
    hook_style: str = "ai_auto",
    cta_style: str = "save_share",
    cta_keyword: str = "",
) -> Dict[str, Any]:
    """Generates and normalizes a complete storyboard timeline for Studio V17–V28."""
    raw_scenes = _generate_pro_llm(
        topic, mode_key, tone, duration_mode, voice, watermark,
        audience_level, hook_style, cta_style, cta_keyword,
    )
    if not raw_scenes:
        raw_scenes = _build_fallback_scenes(topic, mode_key, tone, watermark, cta_keyword)

    lbl = _studio_pro_label(mode_key)
    norm: List[Dict[str, Any]] = []
    for i, sc in enumerate(raw_scenes):
        if not isinstance(sc, dict):
            continue
        nar = str(sc.get("narration") or "").strip()
        if not nar:
            continue
        role = str(sc.get("role") or ("hook" if i == 0 else ("cta" if i == len(raw_scenes) - 1 else "solution"))).lower().strip()
        sc_tone = str(sc.get("scene_tone") or get_tone_profile(tone, role=role, idx=i).get("key") or "auto_2026_director")
        vd = dict(sc.get("visual_data") or {})
        vd["watermark"] = watermark
        vd["_pro_mode"] = mode_key
        out_item: Dict[str, Any] = {
            "scene_id": len(norm) + 1,
            "role": role,
            "scene_tone": sc_tone,
            "sfx_cue": str(sc.get("sfx_cue") or ("punch_impact" if i == 0 else ("success_chime" if role == "cta" else "pop_snap"))),
            "narration": nar,
            "visual_type": mode_key,
            "routed_engine": lbl,
            "art_style": "v2_midnight_navy",
            "backdrop": "v2_clean_canvas",
            "transition": "smooth_fade",
            "text_fx": "clean_hud",
            "visual_data": vd,
            "actions": [],
            "_disable_actions_overlay": True,
            "_disable_camera_actions": True,
        }
        if isinstance(sc.get("dialogue"), list) and sc.get("dialogue"):
            out_item["dialogue"] = sc["dialogue"]
        norm.append(out_item)

    if not norm:
        return generate_studio_pro_timeline(topic, mode_key, tone, "short", voice, watermark, audience_level, hook_style, cta_style, cta_keyword)

    return {
        "topic": topic,
        "v2_engine": mode_key,
        "art_style": "v2_midnight_navy",
        "header_brand": watermark,
        "scenes": norm,
    }


def _build_pro_html(scene: Dict[str, Any], width: int, height: int, tone: str = "auto_2026_director") -> str:
    vd = dict(scene.get("visual_data") or {})
    mode = str(scene.get("visual_type") or vd.get("_pro_mode") or "v24_editorial_cards")
    prof = get_tone_profile(tone, scene_tone=scene.get("scene_tone"), role=str(scene.get("role") or ""))
    acc_key = str(vd.get("accent_color") or prof.get("accent_key") or "cyan")
    acc = _ACCENT_HEX.get(acc_key, "#38BDF8")

    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = f'<span class="at">@</span>{html.escape(raw_wm[1:])}' if raw_wm.startswith("@") else html.escape(raw_wm)
    hud_pill = html.escape(str(vd.get("hud_pill") or _studio_pro_label(mode).upper()))
    h_w = html.escape(str(vd.get("headline_white") or ""))
    h_a = html.escape(str(vd.get("headline_accent") or ""))
    footer = html.escape(str(vd.get("footer_note") or ""))

    idx_s = int(vd.get("_scene_idx", max(0, int(scene.get("scene_id", 1)) - 1)))
    tot_s = max(1, int(vd.get("_total_scenes", 6)))
    seg_html = "".join(
        f'<div class="seg {"done" if i < idx_s else ("act" if i == idx_s else "")}"></div>'
        for i in range(tot_s)
    )

    sc = min(width, height) / 1080.0
    is_wide = width > height
    pad_x = int((42 if not is_wide else 88) * sc)
    hl_px = int((56 if not is_wide else 42) * sc)

    safe_state = {
        "mode": mode,
        "acc": acc,
        "vd": vd,
    }

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: radial-gradient(circle at 50% 18%, #10254A 0%, #071124 58%, #030712 100%);
    color: #F8FAFC;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }}
  .grid-bg {{
    position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(56,189,248,0.06) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,189,248,0.06) 1px, transparent 1px);
    background-size: 46px 46px;
  }}
  .root {{
    position: relative; width: 100%; height: 100%; z-index: 2;
    display: flex; flex-direction: column;
    padding: {int(30*sc)}px {pad_x}px {int(38*sc)}px;
    gap: {int(16*sc)}px;
  }}
  .seg-bar {{ display: flex; gap: 8px; height: 6px; }}
  .seg {{ flex: 1; border-radius: 999px; background: rgba(148,163,184,0.22); }}
  .seg.done {{ background: rgba(56,189,248,0.65); }}
  .seg.act {{ background: {acc}; box-shadow: 0 0 12px {acc}; }}
  .top-row {{ display: flex; align-items: center; justify-content: space-between; }}
  .wm-pill {{
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.92); border: 1.8px solid rgba(148,163,184,0.34);
    font-size: {int(22*sc)}px; font-weight: 800; color: #FFFFFF;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .hud-pill {{
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.92); border: 2px solid {acc};
    color: {acc}; font-size: {int(19*sc)}px; font-weight: 900; letter-spacing: 1.8px;
  }}
  .headline {{
    text-align: center; line-height: 1.14; font-size: {hl_px}px; font-weight: 900;
    text-shadow: 0 6px 24px rgba(0,0,0,0.65);
  }}
  .headline .acc {{ color: {acc}; }}
  .stage {{
    flex: 1; position: relative; border-radius: {int(28*sc)}px;
    background: rgba(8, 16, 36, 0.84);
    border: 2px solid rgba(148,163,184,0.22);
    box-shadow: 0 24px 60px rgba(0,0,0,0.62), inset 0 0 40px rgba(56,189,248,0.06);
    padding: {int(28*sc)}px;
    display: flex; flex-direction: column; justify-content: space-evenly; gap: {int(18*sc)}px;
    overflow: hidden;
  }}
  .card {{
    background: rgba(15, 25, 48, 0.94);
    border: 2px solid rgba(148,163,184,0.24);
    border-radius: {int(20*sc)}px;
    padding: {int(22*sc)}px {int(24*sc)}px;
    transition: opacity 0.25s ease, transform 0.25s ease;
  }}
  .flow-arrow {{
    text-align: center; font-size: {int(26*sc)}px; font-weight: 900;
    color: {acc}; letter-spacing: 2px; opacity: 0.88;
    line-height: 1; padding: {int(2*sc)}px 0;
  }}
  .mono {{ font-family: "Cascadia Code", Consolas, monospace; }}
  .code-bar {{
    background: rgba(5, 10, 22, 0.96); border: 2px solid {acc}66;
    border-radius: 16px; padding: {int(18*sc)}px {int(20*sc)}px;
    font-family: "Cascadia Code", monospace; font-size: {int(25*sc)}px; font-weight: 700; color: #E2E8F0;
    line-height: 1.42; word-break: break-word;
  }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: {int(18*sc)}px; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: {int(14*sc)}px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: {int(16*sc)}px; }}
  .pill-badge {{
    display: inline-block; padding: {int(8*sc)}px {int(18*sc)}px; border-radius: 12px;
    font-size: {int(21*sc)}px; font-weight: 900; letter-spacing: 0.6px;
  }}
  .row-item {{
    padding: {int(16*sc)}px {int(18*sc)}px; border-radius: 14px;
    background: rgba(20, 32, 58, 0.92); border: 1.8px solid rgba(148,163,184,0.24);
    font-size: {int(25*sc)}px; font-weight: 800; color: #F8FAFC;
    margin-bottom: {int(12*sc)}px;
  }}
  .row-item:last-child {{ margin-bottom: 0; }}
  .row-hit {{ border-color: #34D399; background: rgba(52,211,153,0.16); color: #A7F3D0; }}
  .row-drop {{ border-color: #F43F5E88; background: rgba(244,63,94,0.12); color: #FDA4AF; opacity: 0.6; text-decoration: line-through; }}
  .meter-track {{
    width: 100%; height: {int(28*sc)}px; border-radius: 999px;
    background: rgba(30,41,59,0.92); overflow: hidden; border: 1.5px solid rgba(148,163,184,0.28);
  }}
  .meter-fill {{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, {acc}, #34D399); }}
  .footer-pill {{
    align-self: center; padding: {int(12*sc)}px {int(30*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.94); border: 2px solid {acc};
    color: #FFFFFF; font-size: {int(23*sc)}px; font-weight: 800; text-align: center;
  }}
</style>
</head>
<body>
  <div class="grid-bg"></div>
  <div class="root">
    <div class="seg-bar">{seg_html}</div>
    <div class="top-row">
      <div class="wm-pill">{wm_html}</div>
      <div class="hud-pill">{hud_pill}</div>
    </div>
    <div class="headline">{h_w} <span class="acc">{h_a}</span></div>
    <div class="stage" id="proStage"></div>
    {f'<div class="footer-pill" id="footerPill">{footer}</div>' if footer else ''}
  </div>

  <script>
    const ST = {json.dumps(safe_state, ensure_ascii=False)};
    const stage = document.getElementById('proStage');
    const vd = ST.vd || {{}};
    const acc = ST.acc || '#38BDF8';
    const esc = (s) => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const PAL = {{ cyan:'#38BDF8', emerald:'#34D399', amber:'#FBBF24', rose:'#F43F5E', purple:'#C084FC' }};
    const items = [];

    function addReveal(el, dp) {{
      items.push({{ el, dp }});
      return el;
    }}

    if (ST.mode === 'v17_sql_simulator') {{
      const sqlBox = document.createElement('div');
      sqlBox.className = 'code-bar';
      sqlBox.textContent = vd.sql_clause || 'SELECT * FROM users JOIN orders ...';
      stage.appendChild(addReveal(sqlBox, 0.04));

      const g2 = document.createElement('div');
      g2.className = 'grid-2';
      const lCol = document.createElement('div'); lCol.className = 'card';
      lCol.innerHTML = '<div class="mono" style="color:#38BDF8;font-size:21px;font-weight:900;margin-bottom:16px;">LEFT TABLE (USERS)</div>';
      const hits = new Set(vd.match_indices || [0]);
      const drops = new Set(vd.dropped_indices || []);
      (vd.left_rows || []).forEach((r, i) => {{
        const cls = drops.has(i) ? 'row-item row-drop' : (hits.has(i) ? 'row-item row-hit' : 'row-item');
        lCol.innerHTML += `<div class="${{cls}}">${{esc(r)}}</div>`;
      }});
      const rCol = document.createElement('div'); rCol.className = 'card';
      rCol.innerHTML = '<div class="mono" style="color:#FBBF24;font-size:21px;font-weight:900;margin-bottom:16px;">RIGHT TABLE / FILTER</div>';
      (vd.right_rows || []).forEach((r, i) => {{
        const cls = drops.has(i) ? 'row-item row-drop' : (hits.has(i) ? 'row-item row-hit' : 'row-item');
        rCol.innerHTML += `<div class="${{cls}}">${{esc(r)}}</div>`;
      }});
      g2.appendChild(addReveal(lCol, 0.16));
      g2.appendChild(addReveal(rCol, 0.28));
      stage.appendChild(g2);

      const flowTag = document.createElement('div');
      flowTag.className = 'flow-arrow';
      flowTag.textContent = '↓  ROW MATCH • FILTER • WINDOW EVALUATION  ↓';
      stage.appendChild(addReveal(flowTag, 0.36));

      const res = document.createElement('div');
      res.className = 'card';
      res.style.borderColor = acc;
      res.style.display = 'flex'; res.style.justifyContent = 'space-between'; res.style.alignItems = 'center';
      res.innerHTML = `<div style="font-size:30px;font-weight:900;color:#FFFFFF;">${{esc(vd.result_badge || 'OUTPUT')}}</div>` +
        `<div class="pill-badge" style="background:${{acc}}24;color:${{acc}};border:2px solid ${{acc}}">${{esc(vd.metric || 'SQL VERIFIED')}}</div>`;
      stage.appendChild(addReveal(res, 0.45));

    }} else if (ST.mode === 'v18_agent_loop' || ST.mode === 'v26_multi_agent_ops') {{
      const list = vd.steps || vd.stages || [];
      const wrap = document.createElement('div');
      wrap.style.display = 'flex'; wrap.style.flexDirection = 'column'; wrap.style.gap = '14px'; wrap.style.justifyContent = 'space-evenly';
      list.forEach((st, i) => {{
        const title = Array.isArray(st) ? st[0] : (st.title || `Step ${{i+1}}`);
        const desc = Array.isArray(st) ? st[1] : (st.desc || '');
        const cKey = Array.isArray(st) && st[2] ? st[2] : (i === list.length - 1 ? 'emerald' : 'cyan');
        const col = PAL[cKey] || acc;
        const c = document.createElement('div');
        c.className = 'card';
        c.style.borderColor = col;
        c.style.borderLeft = `8px solid ${{col}}`;
        c.innerHTML = `<div class="mono" style="color:${{col}};font-size:23px;font-weight:900;margin-bottom:8px;">${{esc(title)}}</div>` +
          `<div style="font-size:29px;font-weight:800;color:#FFFFFF;line-height:1.3;">${{esc(desc)}}</div>`;
        wrap.appendChild(addReveal(c, 0.08 + i * 0.13));
        if (i < list.length - 1) {{
          const arr = document.createElement('div');
          arr.className = 'flow-arrow';
          arr.textContent = '↓';
          wrap.appendChild(addReveal(arr, 0.12 + i * 0.13));
        }}
      }});
      stage.appendChild(wrap);

      const tr = document.createElement('div');
      tr.className = 'code-bar';
      tr.style.borderColor = '#34D399';
      tr.style.textAlign = 'center';
      tr.innerHTML = `<span style="color:#34D399;">✓ ${{esc(vd.trace_line || vd.audit_badge || 'AGENT LOOP CONVERGED')}}</span>`;
      stage.appendChild(addReveal(tr, 0.62));

    }} else if (ST.mode === 'v19_storage_pruning') {{
      const qb = document.createElement('div'); qb.className = 'code-bar'; qb.textContent = vd.query_box || 'WHERE date = ...';
      stage.appendChild(addReveal(qb, 0.06));

      const grid = document.createElement('div'); grid.className = 'grid-4';
      const scanSet = new Set(vd.scanned_indices || [5]);
      (vd.blocks || []).forEach((b, i) => {{
        const hit = scanSet.has(i);
        const col = hit ? (vd.scan_mode === 'full' ? '#F43F5E' : '#34D399') : '#475569';
        const bc = document.createElement('div'); bc.className = 'card';
        bc.style.borderColor = col;
        bc.style.minHeight = '145px';
        bc.style.display = 'flex'; bc.style.flexDirection = 'column'; bc.style.justifyContent = 'center';
        bc.style.opacity = hit ? '1' : '0.52';
        bc.style.background = hit ? (col + '22') : 'rgba(15,23,42,0.75)';
        bc.innerHTML = `<div class="mono" style="font-size:23px;font-weight:900;color:${{col}};">${{esc(b[0])}}</div>` +
          `<div style="font-size:29px;font-weight:900;color:#FFFFFF;margin-top:8px;">${{esc(b[1])}}</div>`;
        grid.appendChild(addReveal(bc, 0.14 + i * 0.05));
      }});
      stage.appendChild(grid);

      const sum = document.createElement('div'); sum.className = 'grid-2';
      sum.innerHTML = `<div class="card" style="border-color:${{acc}}"><div class="mono" style="color:${{acc}};font-size:20px;">I/O SCOPE</div><div style="font-size:30px;font-weight:900;margin-top:6px;">${{esc(vd.left_metric || '')}}</div></div>` +
        `<div class="card" style="border-color:#34D399"><div class="mono" style="color:#34D399;font-size:20px;">LATENCY & COST</div><div style="font-size:30px;font-weight:900;margin-top:6px;">${{esc(vd.right_metric || '')}}</div></div>`;
      stage.appendChild(addReveal(sum, 0.56));

    }} else if (ST.mode === 'v21_api_inspector') {{
      const top = document.createElement('div'); top.className = 'card'; top.style.borderColor = acc;
      top.style.display = 'flex'; top.style.justifyContent = 'space-between'; top.style.alignItems = 'center';
      top.innerHTML = `<div><span class="pill-badge" style="background:${{acc}};color:#040914;margin-right:10px;">${{esc(vd.method || 'POST')}}</span><span class="mono" style="font-size:25px;font-weight:800;">${{esc(vd.endpoint || '/v1/api')}}</span></div>` +
        `<div class="pill-badge" style="background:#34D39926;color:#34D399;border:2px solid #34D399">${{esc(vd.status_code || '200 OK')}}</div>`;
      stage.appendChild(addReveal(top, 0.06));

      const auth = document.createElement('div'); auth.className = 'card'; auth.style.borderColor = '#34D399';
      auth.innerHTML = `<div class="mono" style="color:#34D399;font-size:23px;font-weight:900;">AUTH & LATENCY: ${{esc(vd.auth_badge || 'VERIFIED')}} · ${{esc(vd.latency || '24ms')}}</div>`;
      stage.appendChild(addReveal(auth, 0.18));

      const diffBox = document.createElement('div'); diffBox.className = 'card';
      diffBox.innerHTML = '<div class="mono" style="color:#94A3B8;font-size:21px;font-weight:800;margin-bottom:16px;">PAYLOAD & HEADER DIFF</div>';
      (vd.diff_lines || []).forEach((dl, i) => {{
        const txt = Array.isArray(dl) ? dl[0] : String(dl);
        const kind = Array.isArray(dl) ? dl[1] : 'good';
        const col = kind === 'bad' ? '#F43F5E' : '#34D399';
        const line = document.createElement('div'); line.className = 'row-item';
        line.style.borderColor = col; line.style.background = col + '18'; line.style.color = '#FFFFFF';
        line.style.fontFamily = 'Cascadia Code, monospace'; line.style.fontSize = '24px'; line.style.padding = '20px 22px';
        line.textContent = txt;
        diffBox.appendChild(addReveal(line, 0.28 + i * 0.12));
      }});
      stage.appendChild(diffBox);

    }} else if (ST.mode === 'v23_decision_tree') {{
      const q = document.createElement('div'); q.className = 'card'; q.style.borderColor = acc; q.style.textAlign = 'center';
      q.innerHTML = `<div class="mono" style="color:${{acc}};font-size:21px;font-weight:900;">CONDITION</div><div style="font-size:33px;font-weight:900;margin-top:8px;">${{esc(vd.root_q || '')}}</div>`;
      stage.appendChild(addReveal(q, 0.08));

      const bRow = document.createElement('div'); bRow.className = 'grid-2';
      [vd.yes_branch, vd.no_branch].forEach((br, bi) => {{
        if (!br) return;
        const win = Boolean(br[2]);
        const col = win ? '#34D399' : '#64748B';
        const bc = document.createElement('div'); bc.className = 'card';
        bc.style.borderColor = col; bc.style.opacity = win ? '1' : '0.48';
        bc.innerHTML = `<div style="font-size:26px;font-weight:900;color:${{col}}">${{esc(br[0])}}</div><div style="font-size:23px;color:#E2E8F0;margin-top:8px;">${{esc(br[1])}}</div>`;
        bRow.appendChild(addReveal(bc, 0.22 + bi * 0.10));
      }});
      stage.appendChild(bRow);

      const mat = document.createElement('div'); mat.className = 'card';
      (vd.matrix || []).forEach((mr, i) => {{
        const row = document.createElement('div'); row.className = 'row-item';
        row.style.display = 'flex'; row.style.justifyContent = 'space-between'; row.style.fontSize = '25px'; row.style.padding = '18px 20px';
        row.innerHTML = `<span style="color:#94A3B8;">${{esc(mr[0])}}</span><span style="color:#34D399;">${{esc(mr[1])}}</span><span style="color:#FBBF24;">${{esc(mr[2])}}</span>`;
        mat.appendChild(addReveal(row, 0.36 + i * 0.09));
      }});
      stage.appendChild(mat);

      const wBox = document.createElement('div'); wBox.className = 'card'; wBox.style.borderColor = '#34D399'; wBox.style.textAlign = 'center';
      wBox.innerHTML = `<div style="font-size:30px;font-weight:900;color:#34D399;">${{esc(vd.winner || 'RECOMMENDED PICK ✓')}}</div>`;
      stage.appendChild(addReveal(wBox, 0.62));

    }} else if (ST.mode === 'v24_editorial_cards') {{
      const q = document.createElement('div'); q.className = 'card';
      q.style.borderColor = acc; q.style.borderLeft = `10px solid ${{acc}}`; q.style.padding = '28px 30px';
      q.innerHTML = `<div class="mono" style="color:${{acc}};font-size:21px;font-weight:900;margin-bottom:12px;">❝ SPOTLIGHT INSIGHT</div><div style="font-size:35px;font-weight:900;line-height:1.34;color:#FFFFFF;">${{esc(vd.quote || '')}}</div>`;
      stage.appendChild(addReveal(q, 0.08));

      const w = vd.wrong_card || ['CODING MISTAKE', ''];
      const wc = document.createElement('div'); wc.className = 'card';
      wc.style.borderColor = '#F43F5E'; wc.style.borderLeft = '10px solid #F43F5E'; wc.style.padding = '26px 28px';
      wc.innerHTML = `<div class="mono" style="color:#F43F5E;font-size:22px;font-weight:900;">✗ ${{esc(w[0])}}</div><div style="font-size:30px;font-weight:800;margin-top:10px;line-height:1.3;color:#FECDD3;">${{esc(w[1])}}</div>`;
      stage.appendChild(addReveal(wc, 0.26));

      const r = vd.right_card || ['PRO PATTERN', ''];
      const rc = document.createElement('div'); rc.className = 'card';
      rc.style.borderColor = '#34D399'; rc.style.borderLeft = '10px solid #34D399'; rc.style.padding = '26px 28px';
      rc.innerHTML = `<div class="mono" style="color:#34D399;font-size:22px;font-weight:900;">✓ ${{esc(r[0])}}</div><div style="font-size:30px;font-weight:800;margin-top:10px;line-height:1.3;color:#D1FAE5;">${{esc(r[1])}}</div>`;
      stage.appendChild(addReveal(rc, 0.44));

    }} else if (ST.mode === 'v25_iceberg_lakehouse') {{
      const cat = document.createElement('div'); cat.className = 'card'; cat.style.borderColor = acc; cat.style.textAlign = 'center'; cat.style.padding = '28px';
      cat.innerHTML = `<div style="font-size:32px;font-weight:900;color:${{acc}}">${{esc(vd.catalog_title || 'APACHE ICEBERG V4')}}</div><div class="mono" style="font-size:22px;color:#E2E8F0;margin-top:10px;">${{esc(vd.catalog_sub || '')}}</div>`;
      stage.appendChild(addReveal(cat, 0.08));

      const ptr = document.createElement('div'); ptr.className = 'flow-arrow';
      ptr.textContent = '↓   SINGLE ZERO-COPY STORAGE  →  MULTI-ENGINE READS   ↓';
      stage.appendChild(addReveal(ptr, 0.16));

      const engs = document.createElement('div'); engs.className = 'grid-3';
      (vd.engines || []).forEach((e, i) => {{
        const ec = document.createElement('div'); ec.className = 'card'; ec.style.borderColor = '#34D399';
        ec.style.minHeight = '210px';
        ec.style.display = 'flex'; ec.style.flexDirection = 'column'; ec.style.justifyContent = 'center'; ec.style.textAlign = 'center';
        ec.innerHTML = `<div style="font-size:28px;font-weight:900;color:#FFFFFF;">${{esc(e[0])}}</div><div class="mono" style="font-size:21px;color:#34D399;margin-top:12px;">${{esc(e[1])}}</div>`;
        engs.appendChild(addReveal(ec, 0.22 + i * 0.12));
      }});
      stage.appendChild(engs);

      const meter = document.createElement('div'); meter.className = 'card'; meter.style.borderColor = '#FBBF24';
      const pct = Number(vd.pruning_pct || 90);
      meter.innerHTML = `<div style="display:flex;justify-content:space-between;font-size:25px;font-weight:900;margin-bottom:12px;"><span>COST & PRUNING METER</span><span style="color:#34D399;">${{esc(vd.cost_meter || '')}}</span></div>` +
        `<div class="meter-track"><div class="meter-fill" style="width:${{pct}}%"></div></div>`;
      stage.appendChild(addReveal(meter, 0.56));

    }} else if (ST.mode === 'v27_cdc_contracts') {{
      const flow = document.createElement('div'); flow.className = 'grid-3';
      [vd.source_lbl || 'SOURCE WAL', vd.contract_lbl || 'CONTRACT GATE', vd.target_lbl || 'TARGET DB'].forEach((lbl, i) => {{
        const col = i === 1 ? '#FBBF24' : (i === 2 ? '#34D399' : acc);
        const fc = document.createElement('div'); fc.className = 'card'; fc.style.borderColor = col; fc.style.textAlign = 'center';
        fc.innerHTML = `<div class="mono" style="font-size:22px;font-weight:900;color:${{col}};">${{esc(lbl)}}</div>`;
        flow.appendChild(addReveal(fc, 0.08 + i * 0.12));
      }});
      stage.appendChild(flow);

      const chks = document.createElement('div'); chks.className = 'card';
      (vd.checks || []).forEach((ck, i) => {{
        const ok = !String(ck[1]).includes('BLOCK') && !String(ck[1]).includes('✗');
        const col = ok ? '#34D399' : '#F43F5E';
        const rc = document.createElement('div'); rc.className = 'row-item';
        rc.style.borderColor = col; rc.style.display = 'flex'; rc.style.justifyContent = 'space-between';
        rc.style.fontSize = '26px'; rc.style.padding = '20px 22px';
        rc.innerHTML = `<span>${{esc(ck[0])}}</span><span style="color:${{col}}">${{esc(ck[1])}}</span>`;
        chks.appendChild(addReveal(rc, 0.28 + i * 0.10));
      }});
      stage.appendChild(chks);

      const syn = document.createElement('div'); syn.className = 'card'; syn.style.borderColor = '#34D399';
      syn.innerHTML = `<div style="display:flex;justify-content:space-between;font-size:25px;font-weight:900;margin-bottom:12px;"><span>SYNC PARITY</span><span style="color:#34D399;">${{esc(vd.downtime || '0ms Downtime')}}</span></div>` +
        `<div class="meter-track"><div class="meter-fill" style="width:${{Number(vd.sync_pct || 100)}}%"></div></div>`;
      stage.appendChild(addReveal(syn, 0.58));

    }} else {{
      // v28_semantic_eval_hub
      const stack = document.createElement('div'); stack.style.display = 'flex'; stack.style.flexDirection = 'column'; stack.style.gap = '14px'; stack.style.justifyContent = 'space-evenly';
      const layers = vd.layers || [];
      layers.forEach((ly, i) => {{
        const col = i === 0 ? acc : (i === 1 ? '#FBBF24' : '#34D399');
        const lc = document.createElement('div'); lc.className = 'card'; lc.style.borderColor = col; lc.style.borderLeft = `8px solid ${{col}}`;
        lc.innerHTML = `<div class="mono" style="color:${{col}};font-size:22px;font-weight:900;">${{esc(ly[0])}}</div><div style="font-size:29px;font-weight:800;margin-top:8px;">${{esc(ly[1])}}</div>`;
        stack.appendChild(addReveal(lc, 0.10 + i * 0.14));
        if (i < layers.length - 1) {{
          const arr = document.createElement('div'); arr.className = 'flow-arrow'; arr.textContent = '↓';
          stack.appendChild(addReveal(arr, 0.14 + i * 0.14));
        }}
      }});
      stage.appendChild(stack);

      const bRow = document.createElement('div'); bRow.className = 'grid-3';
      (vd.badges || []).forEach((bg, i) => {{
        const bc = document.createElement('div'); bc.className = 'card'; bc.style.borderColor = '#34D399'; bc.style.textAlign = 'center';
        bc.innerHTML = `<div class="mono" style="color:#94A3B8;font-size:19px;">${{esc(bg[0])}}</div><div style="font-size:27px;font-weight:900;color:#34D399;margin-top:8px;">${{esc(bg[1])}}</div>`;
        bRow.appendChild(addReveal(bc, 0.50 + i * 0.08));
      }});
      stage.appendChild(bRow);
    }}

    window.__setStudioProgress = function(wp, lp) {{
      const p = Math.max(0, Math.min(1, Number(wp) || 0));
      items.forEach(it => {{
        const f = Math.max(0, Math.min(1, (p - it.dp + 0.08) / 0.12));
        it.el.style.opacity = f.toFixed(3);
        it.el.style.transform = `translateY(${{(12 * (1 - f)).toFixed(1)}}px) scale(${{(0.96 + 0.04 * f).toFixed(3)}})`;
      }});
      const fp = document.getElementById('footerPill');
      if (fp) {{
        const ff = Math.max(0, Math.min(1, (p - 0.56) / 0.14));
        fp.style.opacity = ff.toFixed(3);
      }}
    }};
    window.__setStudioProgress(1.0, 1.0);
  </script>
</body>
</html>"""


def render_studio_pro_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
    fps: int = VIDEO_FPS,
    res_scale: float = 1.0,
    frame_ext: str = "jpg",
) -> Path:
    """Renders FPS frames for any Studio V17–V28 engine using the shared 4K/60FPS Chromium loop."""
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    w, h = spec["width"], spec["height"]
    duration = max(1.4, float(scene.get("duration", 4.5)))
    total_frames = max(18, int(round(duration * max(15, int(fps or VIDEO_FPS)))))
    out_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.*"):
        try:
            old.unlink()
        except Exception:
            pass

    html_doc = _build_pro_html(scene, w, h, tone=tone)
    from core.web_generative_engine import capture_studio_playwright_frames
    if capture_studio_playwright_frames(
        html_doc, out_dir, w, h, duration, scene, scene_words,
        tone=tone, fps=fps, res_scale=res_scale, frame_ext=frame_ext, arg_order="wp_lp",
    ):
        return out_dir

    # Headless fallback
    from PIL import Image, ImageDraw
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (7, 17, 36))
    dr = ImageDraw.Draw(img)
    dr.text((64, 120), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(56, 189, 248))
    ext = "png" if str(frame_ext or "jpg").lower() == "png" else "jpg"
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.{ext}")
    return out_dir
