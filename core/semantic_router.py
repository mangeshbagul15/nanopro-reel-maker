"""
Dynamic Full-Catalog Semantic Router & AI Validator Mode (1,179 Engines).

Zero hardcoded topic `if/elif` buckets: indexes ALL 1,011 Studio/Domain/Grammar
layouts plus ALL 168 Option 1 WebGL/SVG/Spatial archetypes with full preset metadata,
scores any engineering topic/narration using IDF-weighted BM25 + role geometry
affinity + strict per-video structural deduplication, and preserves valid
AI-chosen visual modes without blind overrides.
"""

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

_STOPWORDS = frozenset({
    "the", "and", "for", "with", "into", "from", "that", "this", "what", "when", "where",
    "which", "how", "why", "are", "was", "were", "will", "can", "not", "but", "all",
    "any", "your", "our", "you", "they", "have", "has", "had", "does", "did", "done",
    "use", "using", "used", "make", "makes", "made", "very", "more", "most", "much",
    "hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "par", "aur", "kya", "kyun",
    "kaise", "jab", "tab", "ab", "yaar", "bhai", "dost", "aaj", "hum", "aap", "yeh",
    "woh", "bhi", "toh", "hota", "hoti", "hote", "karta", "karti", "karte", "karo",
    "dekh", "dekho", "samjho", "batao", "chalo", "bas", "ek", "do", "teen", "ya",
    "data", "system", "engineering", "engineer", "production", "modern", "cleanly",
    "run", "fast", "best", "way", "vs", "versus",
})

# Linguistic query-term expansion (pure synonym bridge for short abbreviations/terms, NOT domain code paths)
_QUERY_EXPANSIONS: Dict[str, Tuple[str, ...]] = {
    "lakehouse": ("medallion", "iceberg", "delta", "parquet", "lake", "warehouse", "acid"),
    "warehouse": ("olap", "snowflake", "star", "bigquery", "redshift", "cluster", "bi"),
    "lake": ("medallion", "iceberg", "delta", "parquet", "storage", "object"),
    "spark": ("parquet", "iceberg", "delta", "lakehouse", "etl", "shuffle", "cluster"),
    "dbt": ("etl", "elt", "warehouse", "lineage", "quality", "medallion"),
    "kafka": ("cdc", "debezium", "isr", "dlq", "consumer", "partition", "event", "backbone", "stream"),
    "flink": ("watermark", "cep", "window", "stream", "event", "iceberg"),
    "cdc": ("debezium", "outbox", "binlog", "replication", "stream"),
    "sql": ("query", "table", "window", "dense_rank", "explain", "schema", "postgres", "index"),
    "postgres": ("mvcc", "wal", "btree", "vacuum", "sql", "explain", "index"),
    "mysql": ("btree", "wal", "binlog", "innodb", "sql", "mvcc"),
    "redis": ("cache", "sentinel", "cluster", "limiter", "token", "bloom", "lua", "memory"),
    "cache": ("redis", "lru", "ttl", "hit", "miss", "cdn", "bloom"),
    "k8s": ("kubernetes", "pod", "hpa", "scheduling", "mesh", "container"),
    "kubernetes": ("k8s", "pod", "hpa", "scheduling", "envoy", "mesh"),
    "ebpf": ("xdp", "kernel", "packet", "bypass", "ring", "socket"),
    "webrtc": ("sfu", "turn", "stun", "ice", "relay", "media", "udp"),
    "payment": ("stripe", "ledger", "idempotent", "settlement", "outbox", "saga"),
    "stripe": ("payment", "idempotent", "ledger", "webhook", "retry"),
    "robotics": ("ros2", "lidar", "slam", "dds", "planner", "pubsub"),
    "ros2": ("lidar", "slam", "dds", "planner", "pubsub"),
    "llm": ("transformer", "attention", "vllm", "kv", "rag", "agent", "token", "neural"),
    "rag": ("chunk", "hybrid", "rerank", "hnsw", "vector", "embedding", "fusion"),
    "agent": ("mcp", "react", "tool", "sandbox", "guardrails"),
    "auth": ("oauth", "pkce", "jwks", "jwt", "passkey", "webauthn", "zero", "trust", "mtls"),
    "security": ("zero", "trust", "spiffe", "mtls", "oauth", "vault", "tls", "firewall"),
    "consensus": ("raft", "paxos", "quorum", "leader", "election", "ballot"),
    "shard": ("vitess", "vtgate", "consistent", "hashing", "ring", "partition"),
    "graphql": ("federation", "supergraph", "subgraphs", "api"),
    "grpc": ("protobuf", "mux", "envoy", "http2", "circuit"),
    "vs": ("comparison", "compare", "quadrant", "venn", "split", "tradeoff"),
    "versus": ("comparison", "compare", "quadrant", "venn", "split", "tradeoff"),
    "difference": ("comparison", "compare", "quadrant", "venn", "split"),
    "benchmark": ("latency", "p99", "throughput", "cdf", "race", "speed"),
    "lock": ("mutex", "atomic", "fencing", "deadlock", "contention"),
}


def _tokenize_text(text: str) -> List[str]:
    """Extracts clean lowercased engineering tokens from identifiers and prose."""
    norm = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(text or ""))
    raw = re.findall(r"[A-Za-z0-9]+", norm.lower())
    out: List[str] = []
    for tok in raw:
        if len(tok) < 2 or tok in _STOPWORDS or tok.isdigit():
            continue
        out.append(tok)
        if len(tok) > 5 and tok.endswith("s") and not tok.endswith("ss"):
            out.append(tok[:-1])
        if len(tok) > 6 and tok.endswith("ing"):
            out.append(tok[:-3])
    return out


def _flatten_strings(obj: Any, depth: int = 0) -> List[str]:
    """Recursively extracts human-readable label strings from preset dicts/tuples."""
    if depth > 4 or obj is None:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        acc: List[str] = []
        for k, v in obj.items():
            if str(k) in ("color", "shape", "accent_theme", "art_style"):
                continue
            acc.extend(_flatten_strings(v, depth + 1))
        return acc
    if isinstance(obj, (list, tuple, set)):
        acc = []
        for item in obj:
            acc.extend(_flatten_strings(item, depth + 1))
        return acc
    return []


def infer_geometry_family(layout_key: str, base_kind: str = "") -> str:
    """
    Infers pure visual geometry class (how components are drawn on screen —
    NEVER topic/domain!). Used only for structural variety across scenes.
    """
    k = str(layout_key or "").lower()
    bk = str(base_kind or "").lower()
    if k.startswith(("web_", "svg_", "spatial_")) and not k.endswith("_3d") and k not in (
        "svg_scene", "spatial_canvas", "svg_pipeline_choreography", "spatial_microservice_grid"
    ):
        return "option1_webgl"
    if any(x in k for x in ("hero_hook", "chat_thread", "mobile_app_mockup", "browser_window", "kinetic_statement", "incident_radar", "alert_diagram")):
        return "hook_ui"
    if any(x in k for x in ("sql_", "er_schema", "explain_plan", "b_plus_tree", "mvcc_")) or bk == "sql_studio":
        return "sql_schema"
    if any(x in k for x in ("code_", "diff_", "terminal_", "git_branch", "api_request_response", "json_payload", "yaml_", "regex_")) or bk in ("terminal_studio", "code_diff_split"):
        return "code_diff"
    if any(x in k for x in ("compare", "comparison", "venn_", "quadrant", "matrix_2x2", "hybrid_merge", "cap_theorem")) or bk == "iso_comparison":
        return "compare_matrix"
    if any(x in k for x in ("benchmark", "radar_", "donut_", "radial_gauge", "metric_gauge", "flamegraph", "waterfall", "p99_", "sankey_")) or bk in ("benchmark_3d", "radial_gauge"):
        return "metrics_charts"
    if any(x in k for x in ("memory_", "wal_", "_wal", "buffer", "cache_", "parquet", "iceberg", "delta_lake", "lsm_", "bloom_", "data_structure_memory")) or bk in ("memory_lanes", "slots"):
        return "memory_storage"
    if any(x in k for x in ("checklist", "roadmap", "pyramid", "funnel", "sdlc_", "tiers", "concept_cards", "kanban_")) or k.startswith(("grammar:pyramid", "grammar:tiers", "grammar:funnel", "grammar:checklist")):
        return "summary_checklist"
    return "topology"


def _describe_engine(vtype: str, opt1_arch: Optional[str] = None, ai_chosen: bool = False) -> str:
    """Formats a clear human-readable engine badge for the Streamlit Scene Routing Table."""
    prefix = "AI-Chosen • " if ai_chosen else ""
    if opt1_arch or vtype in ("web_scene", "svg_scene", "spatial_canvas"):
        return f"{prefix}Option 1 Interactive 3D WebGL"
    fam = infer_geometry_family(vtype)
    labels = {
        "hook_ui": "Kinetic Concept & Q&A Hook",
        "sql_schema": "SQL Studio & Query Schema",
        "code_diff": "Code Diff & Terminal Studio",
        "compare_matrix": "Architectural Trade-Off Comparison",
        "metrics_charts": "Benchmark Charts & Telemetry",
        "memory_storage": "Storage & Memory Internals",
        "summary_checklist": "Summary & Decision Architecture",
        "topology": "System & Domain Topology",
    }
    if vtype.startswith("topo_") or vtype == "multi_topology_dual":
        return f"{prefix}Dual-Plane System Topology"
    return f"{prefix}{labels.get(fam, 'Adaptive Studio Canvas')}"


_CLASSIC_STUDIO_DESCRIPTIONS: Dict[str, str] = {
    "hero_hook": "hero hook interview dilemma question card concept scope",
    "architecture_flow": "architecture flow pipeline nodes edges stages data flow",
    "split_comparison": "split comparison trade off legacy vs modern contrast",
    "benchmark_chart": "benchmark chart latency speedup bar metrics comparison",
    "sql_table": "sql table query window dense_rank group by postgres results",
    "code_terminal": "code terminal cli command bash kubectl python script async",
    "alert_diagram": "alert diagram incident bottleneck production lock outage",
    "concept_cards": "concept cards core engineering principles bullets takeaways",
    "circular_hub_mesh": "circular hub mesh distributed cluster satellites broker",
    "step_timeline": "step timeline sequential execution steps walkthrough",
    "metric_gauge_hud": "metric gauge hud telemetry sla throughput cpu lag",
    "data_structure_memory": "memory buffer wal lsn offsets ring buffer page slots",
    "hybrid_merge": "hybrid merge combined architecture accuracy consistency",
}


@lru_cache(maxsize=1)
def _get_catalog() -> Dict[str, Any]:
    """
    Indexes ALL classic Studio primitives + ALL 1,011 Studio/Domain/Grammar layouts +
    ALL 168 Option 1 archetypes once per process with BM25 document frequency stats.
    """
    from core.layouts_studio import ALL_STUDIO_LAYOUTS, MULTI_TOPOLOGY_30_PRESETS, _CORE_STUDIO_PRESETS_LC
    from core.layouts_pro import _PRO_EXTRA_PRESETS
    from core.layouts_it_sdlc import _IT_70_EXTRA_PRESETS
    from core.layouts_domain_220 import DOMAIN_PRESETS_220
    from core.web_generative_engine import ZERO_TEMPLATE_50_ARCHETYPES, _OPTION1_ARCH_FAMILY

    preset_maps = (
        _CORE_STUDIO_PRESETS_LC,
        MULTI_TOPOLOGY_30_PRESETS,
        _PRO_EXTRA_PRESETS,
        _IT_70_EXTRA_PRESETS,
        DOMAIN_PRESETS_220,
    )

    entries: List[Dict[str, Any]] = []
    studio_map: Dict[str, Dict[str, Any]] = {}
    opt1_map: Dict[str, Dict[str, Any]] = {}

    # 1. Index ALL Classic Studio Primitives + 1,011 Domain/Pro/Grammar layouts
    generic_skip = {"custom_scene"}
    all_studio_keys = list(dict.fromkeys(list(_CLASSIC_STUDIO_DESCRIPTIONS.keys()) + list(ALL_STUDIO_LAYOUTS)))
    for layout_key in all_studio_keys:
        if layout_key in generic_skip:
            continue
        meta_texts: List[str] = []
        base_kind = ""
        if layout_key in _CLASSIC_STUDIO_DESCRIPTIONS:
            meta_texts.append(_CLASSIC_STUDIO_DESCRIPTIONS[layout_key])
        for pm in preset_maps:
            if layout_key in pm:
                raw = pm[layout_key]
                if isinstance(raw, tuple) and raw and isinstance(raw[0], str):
                    base_kind = raw[0]
                meta_texts.extend(_flatten_strings(raw))
                break

        key_toks = _tokenize_text(layout_key)
        meta_toks = _tokenize_text(" ".join(meta_texts))
        tf: Counter = Counter()
        for t in key_toks:
            tf[t] += 3.2
        for t in meta_toks:
            tf[t] += 1.4
        # Bigrams from key tokens give exact compound concept boost (e.g. data_warehouse, zero_trust)
        for i in range(len(key_toks) - 1):
            tf[f"{key_toks[i]}_{key_toks[i + 1]}"] += 4.5

        entry = {
            "id": layout_key,
            "kind": "studio",
            "geom": infer_geometry_family(layout_key, base_kind),
            "key_toks": set(key_toks),
            "tf": dict(tf),
            "len": max(1.0, sum(tf.values())),
        }
        entries.append(entry)
        studio_map[layout_key] = entry

    # 2. Index ALL 168 Option 1 WebGL/SVG/Spatial archetypes
    for arch_id in ZERO_TEMPLATE_50_ARCHETYPES:
        fam = str(_OPTION1_ARCH_FAMILY.get(arch_id, ""))
        key_toks = _tokenize_text(arch_id)
        fam_toks = _tokenize_text(fam)
        tf = Counter()
        for t in key_toks:
            tf[t] += 3.4
        for t in fam_toks:
            tf[t] += 1.2
        for i in range(len(key_toks) - 1):
            tf[f"{key_toks[i]}_{key_toks[i + 1]}"] += 4.5

        entry = {
            "id": arch_id,
            "kind": "opt1",
            "geom": "option1_webgl",
            "key_toks": set(key_toks),
            "tf": dict(tf),
            "len": max(1.0, sum(tf.values())),
        }
        entries.append(entry)
        opt1_map[arch_id] = entry

    # Compute IDF across complete 1,179 engine corpus
    n_docs = float(len(entries))
    df: Counter = Counter()
    for ent in entries:
        for tok in ent["tf"]:
            df[tok] += 1
    avg_len = sum(e["len"] for e in entries) / max(1.0, n_docs)
    idf = {tok: math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5)) for tok, freq in df.items()}

    return {
        "entries": entries,
        "studio_entries": [e for e in entries if e["kind"] == "studio"],
        "opt1_entries": [e for e in entries if e["kind"] == "opt1"],
        "studio_map": studio_map,
        "opt1_map": opt1_map,
        "idf": idf,
        "avg_len": avg_len,
    }


def _expand_query_weights(topic: str, narration: str = "", title: str = "") -> Dict[str, float]:
    """
    Produces weighted query terms cleanly prioritizing topic identity (1.6x),
    scene title/narration (1.2x), bigrams (2.0x), and linguistic expansions (0.55x).
    """
    top_toks = _tokenize_text(topic)
    nar_toks = _tokenize_text(f"{title} {narration}")
    weights: Counter = Counter()

    for tok in top_toks:
        weights[tok] += 1.65
    for tok in nar_toks:
        weights[tok] += 1.15

    # Exact topic + narration bigrams
    for seq, mult in ((top_toks, 2.2), (nar_toks, 1.5)):
        for i in range(len(seq) - 1):
            weights[f"{seq[i]}_{seq[i + 1]}"] += mult

    # Subtle query-side synonym bridge (never overrides exact literal hits)
    base_keys = list(weights.keys())
    for tok in base_keys:
        exps = _QUERY_EXPANSIONS.get(tok)
        if exps:
            w_base = weights[tok]
            for ex in exps:
                weights[ex] += min(0.70, w_base * 0.42)
    return dict(weights)


def _bm25_score(entry: Dict[str, Any], q_weights: Dict[str, float], idf: Dict[str, float], avg_len: float) -> float:
    """Computes clean BM25 similarity score between a weighted query and a catalog entry."""
    tf = entry["tf"]
    doc_len = entry["len"]
    k1 = 1.45
    b = 0.45
    score = 0.0
    for q_tok, q_w in q_weights.items():
        if q_tok in tf:
            f = tf[q_tok]
            tok_idf = idf.get(q_tok, 1.5)
            denom = f + k1 * (1.0 - b + b * (doc_len / avg_len))
            score += q_w * tok_idf * ((f * (k1 + 1.0)) / max(0.01, denom))
    return score


def _detect_scene_structural_signals(
    sc: Dict[str, Any],
    idx: int,
    total_scenes: int,
    topic: str,
    v_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extracts purely structural scene cues (Hook/Dialogue, explicit SQL syntax,
    explicit CLI/Code, A vs B contrast, numeric telemetry, memory/storage, closing summary).
    Never checks domain/topic buckets!
    """
    raw_narr = str(sc.get("narration") or "")
    narr_l = raw_narr.lower()
    role_l = str(sc.get("role") or "").lower()
    full_l = f"{topic.lower()} {narr_l}"

    has_sql_syntax = bool(
        v_data.get("table_data")
        or re.search(
            r"\bSELECT\b.+\bFROM\b|\bDENSE_RANK\b|\bROW_NUMBER\b|\bGROUP\s+BY\b|\bCREATE\s+INDEX\b|\bEXPLAIN\s+ANALYZE\b|\bWINDOW\s+FUNCTION\b",
            raw_narr,
            re.IGNORECASE,
        )
        or (role_l in ("query", "schema"))
        or (re.search(r"\b(sql|postgres|mysql|cte|join)\b", narr_l) and re.search(r"\b(sql|postgres|mysql|query)\b", topic.lower()))
    )
    has_code_cli = bool(
        v_data.get("code_snippet")
        or v_data.get("command")
        or role_l == "code"
        or re.search(r"\b(?:kubectl|python\s+-m|docker\s+run|async\s+def|def\s+\w+|curl\s+http|pip\s+install|helm\s+upgrade)\b", raw_narr, re.IGNORECASE)
    )
    has_compare = bool(
        (v_data.get("left_points") and v_data.get("right_points"))
        or role_l in ("tradeoff", "comparison")
        or re.search(r"\b(?:trade-?off|versus|vs|difference|jabki|compare|comparison)\b", narr_l, re.IGNORECASE)
    )
    has_metrics = bool(
        v_data.get("bars")
        or role_l in ("benchmark", "metrics")
        or re.search(r"\b(?:benchmark|speedup|throughput|p99|latency)\b|\d+x\b|\d+\s*ms\b", narr_l, re.IGNORECASE)
    )
    has_storage = bool(
        v_data.get("entries")
        or re.search(r"\b(?:wal|write-?ahead|buffer\s+pool|lsn|ring\s+buffer|page\s+cache|lsm|memtable|parquet|iceberg|delta|snapshot|manifest)\b", narr_l, re.IGNORECASE)
    )
    is_hook = (idx == 0 or role_l == "hook")
    is_final = (total_scenes >= 3 and (idx == total_scenes - 1 or role_l in ("cta", "resolution", "summary", "takeaway")))
    topic_compare = bool(re.search(r"\b(?:vs|versus|difference|compare|comparison)\b", full_l))

    return {
        "is_hook": is_hook,
        "is_final": is_final,
        "has_sql_syntax": has_sql_syntax,
        "has_code_cli": has_code_cli,
        "has_compare": has_compare or (is_hook and topic_compare) or (role_l == "problem" and topic_compare),
        "has_metrics": has_metrics,
        "has_storage": has_storage,
        "role_l": role_l,
    }


def _apply_role_bonus(entry: Dict[str, Any], sig: Dict[str, Any], idx: int, used_geoms: Set[str], tone: str) -> float:
    """Applies geometry-structure bonus + already-used geometry penalty cleanly."""
    geom = entry["geom"]
    eid = entry["id"]
    bonus = 0.0

    # Strict anti-repetition of geometry family within one video (especially SQL & Compare)
    if geom in used_geoms:
        bonus -= 7.5 if geom in ("sql_schema", "code_diff", "compare_matrix", "metrics_charts", "hook_ui") else 3.2

    if sig["is_hook"]:
        if geom == "hook_ui":
            bonus += 14.0
        if tone == "dual_dialogue_curious" and eid in ("chat_thread_ai", "mobile_app_mockup", "hero_hook"):
            bonus += 6.5
        if sig["has_compare"] and geom == "compare_matrix":
            bonus += 13.0
        # Keep browser_window strictly out unless browser/DOM/HTTP topic is actually asked
        if eid == "browser_window":
            bonus -= 4.5

    if sig["has_sql_syntax"] and "sql_schema" not in used_geoms:
        if geom == "sql_schema":
            bonus += 24.0
        else:
            bonus -= 6.0
    elif geom == "sql_schema" and not sig["has_sql_syntax"]:
        bonus -= 12.0

    if sig["has_code_cli"] and "code_diff" not in used_geoms:
        if geom == "code_diff":
            bonus += 24.0
            if eid in ("code_terminal", "terminal_studio", "code_diff_split", "diff_mutex_to_atomic", "diff_n_plus_one_fix"):
                bonus += 9.5
        else:
            bonus -= 6.0

    if sig["has_compare"] and not sig["is_hook"] and "compare_matrix" not in used_geoms:
        if geom == "compare_matrix":
            bonus += 22.0
        else:
            bonus -= 5.0

    if sig["has_metrics"] and "metrics_charts" not in used_geoms:
        if geom == "metrics_charts":
            bonus += 10.0 if sig["has_compare"] else 18.0
        elif not sig["has_compare"]:
            bonus -= 3.5

    if sig["has_storage"] and "memory_storage" not in used_geoms and geom == "memory_storage":
        bonus += 8.0

    if not sig["is_hook"] and not sig["is_final"] and idx in (1, 2, 3):
        if geom in ("topology", "memory_storage") and geom not in used_geoms:
            bonus += 3.2

    return bonus


def retrieve_prompt_candidates(
    topic: str,
    avoid_vtypes: Optional[Iterable[str]] = None,
    run_num: int = 1,
    limit_studio: int = 22,
    limit_opt1: int = 10,
) -> Dict[str, List[str]]:
    """
    Dynamically retrieves the highest-scoring topic-relevant Studio layouts AND
    Option 1 WebGL/SVG/Spatial archetypes directly from the 1,179 catalog so Gemini/Groq
    can make an informed AI selection for ANY technical topic.
    """
    cat = _get_catalog()
    avoid = set(avoid_vtypes or ())
    q_weights = _expand_query_weights(topic)
    idf, avg_len = cat["idf"], cat["avg_len"]

    # Include essential versatile structural primitives so AI always has full storytelling range
    versatile_geoms = ("hook_ui", "compare_matrix", "topology", "metrics_charts", "code_diff", "sql_schema", "memory_storage", "summary_checklist")

    scored_studio = []
    for ent in cat["studio_entries"]:
        s = _bm25_score(ent, q_weights, idf, avg_len)
        if ent["id"] in avoid:
            s -= 1.8
        scored_studio.append((s, ent))
    scored_studio.sort(key=lambda x: x[0], reverse=True)

    picked_studio: List[str] = []
    seen_geoms: Set[str] = set()
    # First pass: top matches guaranteeing structural diversity
    for s, ent in scored_studio[:45]:
        if len(picked_studio) >= limit_studio:
            break
        if s > 0.5 or len(picked_studio) < 12:
            picked_studio.append(ent["id"])
            seen_geoms.add(ent["geom"])
    # Second pass: ensure at least 1 crisp representative per unrepresented structural geometry
    for vg in versatile_geoms:
        if vg not in seen_geoms and len(picked_studio) < limit_studio + 6:
            for s, ent in scored_studio:
                if ent["geom"] == vg and ent["id"] not in picked_studio:
                    picked_studio.append(ent["id"])
                    seen_geoms.add(vg)
                    break

    scored_opt1 = [
        (_bm25_score(ent, q_weights, idf, avg_len) - (1.2 if ent["id"] in avoid else 0.0), ent["id"])
        for ent in cat["opt1_entries"]
    ]
    scored_opt1.sort(key=lambda x: x[0], reverse=True)
    rot = (run_num - 1) % 3
    picked_opt1 = [eid for _, eid in scored_opt1[rot : rot + limit_opt1]] or [eid for _, eid in scored_opt1[:limit_opt1]]

    return {"studio": picked_studio, "opt1": picked_opt1}


def pick_best_opt1_archetype(
    topic: str,
    narration: str = "",
    title: str = "",
    run_num: int = 1,
    idx: int = 0,
    recent_vtypes: Optional[Set[str]] = None,
) -> str:
    """
    Zero-hardcode Option 1 selector: dynamically ranks all 168 Option 1 WebGL/SVG/Spatial
    archetypes by BM25 similarity to `topic + narration + title` and picks from the top relevant pool.
    """
    cat = _get_catalog()
    recent = recent_vtypes or set()
    q_weights = _expand_query_weights(topic, narration, title)
    idf, avg_len = cat["idf"], cat["avg_len"]

    scored: List[Tuple[float, str]] = []
    for ent in cat["opt1_entries"]:
        s = _bm25_score(ent, q_weights, idf, avg_len)
        # Prefer versatile non-niche architectures when BM25 score is tied at zero
        if s <= 0.05 and ent["id"] in (
            "web_cloud_circuit", "web_dual_topology", "web_pipeline_3d",
            "web_timeline_ribbon", "spatial_constellation", "web_bento_layers",
        ):
            s += 0.45
        if ent["id"] in recent:
            s -= 0.35
        scored.append((s, ent["id"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0] if scored else 0.0
    if top_score > 1.2:
        # Prefer strong semantic matches that have NOT appeared in recent reels; widen safely before repeating
        fresh_strong = [eid for sc_val, eid in scored if sc_val >= max(0.8, top_score * 0.45) and eid not in recent]
        if fresh_strong:
            pool = fresh_strong[:5]
        else:
            pool = [eid for sc_val, eid in scored if eid not in recent][:12] or [eid for _, eid in scored[:4]]
    else:
        pool = [eid for _, eid in scored if eid not in recent][:16] or [eid for _, eid in scored[:6]]
    return pool[(run_num + idx) % len(pool)]


def validate_ai_scene_choice(
    orig_vtype: str,
    orig_opt1: Optional[str],
    sc: Dict[str, Any],
    idx: int,
    total_scenes: int,
    topic: str,
    used_vtypes: Set[str],
    used_geoms: Set[str],
    v_data: Dict[str, Any],
) -> Optional[Tuple[str, Optional[str], str]]:
    """
    AI Validator Mode: Preserves Gemini/Groq's explicit visual_type / option1_archetype
    when it is a valid catalog entry, non-duplicate, structurally non-colliding,
    and semantically coherent with the topic/narration. Returns None only when
    fallback dynamic scoring should take over.
    """
    cat = _get_catalog()
    vt = str(orig_vtype or "").strip()
    if not vt or vt in ("custom_scene", "custom", "auto") or vt in used_vtypes:
        return None

    sig = _detect_scene_structural_signals(sc, idx, total_scenes, topic, v_data)
    q_weights = _expand_query_weights(topic, str(sc.get("narration") or ""), str(v_data.get("title") or ""))
    idf, avg_len = cat["idf"], cat["avg_len"]

    # Case A: AI chose an Option 1 WebGL/SVG/Spatial mode
    if vt in ("web_scene", "svg_scene", "spatial_canvas"):
        opt1_str = str(orig_opt1 or "").strip()
        if opt1_str and opt1_str in cat["opt1_map"]:
            ent = cat["opt1_map"][opt1_str]
            # Coherence check: reject only if an explicit topic-specific archetype clashes completely (score == 0 while catalog has strong >= 4.0 match)
            ent_score = _bm25_score(ent, q_weights, idf, avg_len)
            best_opt1_score = max(_bm25_score(e, q_weights, idf, avg_len) for e in cat["opt1_entries"])
            if best_opt1_score >= 4.0 and ent_score <= 0.05 and not opt1_str.startswith(("web_cloud_", "web_dual_", "web_pipeline_", "spatial_constellation")):
                chosen_opt1 = pick_best_opt1_archetype(topic, str(sc.get("narration") or ""), str(v_data.get("title") or ""), idx=idx)
            else:
                chosen_opt1 = opt1_str
        else:
            chosen_opt1 = pick_best_opt1_archetype(topic, str(sc.get("narration") or ""), str(v_data.get("title") or ""), idx=idx)
        return vt, chosen_opt1, _describe_engine(vt, opt1_arch=chosen_opt1, ai_chosen=True)

    # Case B: AI chose a real Studio / Domain / Pro / Grammar layout directly
    is_valid_studio = (vt in cat["studio_map"]) or vt.startswith("grammar:")
    if not is_valid_studio:
        return None

    ent = cat["studio_map"].get(vt)
    geom = ent["geom"] if ent else infer_geometry_family(vt)

    # Guard against AI repeating SQL/compare geometry twice or picking SQL without SQL context
    if geom == "sql_schema" and not sig["has_sql_syntax"]:
        return None
    if geom in used_geoms and geom in ("sql_schema", "code_diff", "compare_matrix", "hook_ui"):
        return None

    # Coherence check: if catalog has a strong topic-matched layout (IDF score >= 4.5) and AI picked an unrelated domain-locked singleton
    if ent is not None:
        ent_score = _bm25_score(ent, q_weights, idf, avg_len)
        max_studio_score = max(_bm25_score(e, q_weights, idf, avg_len) for e in cat["studio_entries"])
        if max_studio_score >= 4.5 and ent_score <= 0.0 and geom in ("topology", "memory_storage"):
            # Don't block versatile structural shapes like architecture_flow / iso_architecture / all_in_one_tech_canvas
            if vt not in ("architecture_flow", "iso_architecture", "all_in_one_tech_canvas", "step_timeline", "split_comparison", "concept_cards"):
                return None

    return vt, None, _describe_engine(vt, ai_chosen=True)


def select_semantic_scene_layout(
    sc: Dict[str, Any],
    idx: int,
    total_scenes: int,
    topic: str,
    tone: str,
    run_num: int,
    used_vtypes: Set[str],
    recent_vtypes: Set[str],
    v_data: Dict[str, Any],
    used_geometries: Optional[Set[str]] = None,
) -> Tuple[str, str]:
    """
    Zero-hardcode dynamic full-catalog router across all 1,179 Studio + Option 1 engines.
    Uses BM25 token/bigram/IDF relevance + pure structural role affinity + diversity lock.
    """
    cat = _get_catalog()
    geoms = used_geometries if used_geometries is not None else set()
    sig = _detect_scene_structural_signals(sc, idx, total_scenes, topic, v_data)
    q_weights = _expand_query_weights(topic, str(sc.get("narration") or ""), str(v_data.get("title") or ""))
    idf, avg_len = cat["idf"], cat["avg_len"]

    # Closing scene showcases Option 1 Interactive 3D WebGL/SVG when multi-scene reel
    if sig["is_final"] and "web_scene" not in used_vtypes:
        arch = pick_best_opt1_archetype(
            topic,
            narration=str(sc.get("narration") or ""),
            title=str(v_data.get("title") or ""),
            run_num=run_num,
            idx=idx,
            recent_vtypes=recent_vtypes,
        )
        v_data["option1_archetype"] = arch
        geoms.add("option1_webgl")
        return "web_scene", _describe_engine("web_scene", opt1_arch=arch)

    # Score every Studio layout across the full 1,011 catalog
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for ent in cat["studio_entries"]:
        eid = ent["id"]
        if eid in used_vtypes:
            continue
        base_bm25 = _bm25_score(ent, q_weights, idf, avg_len)
        role_bonus = _apply_role_bonus(ent, sig, idx, geoms, tone)
        recency_pen = -1.6 if eid in recent_vtypes else 0.0
        # Tiny deterministic jitter among close near-ties so repeated Generate clicks vary fresh layouts
        tie_jitter = ((run_num * 13 + idx * 7 + abs(hash(eid))) % 11) * 0.035
        total_score = base_bm25 + role_bonus + recency_pen + tie_jitter
        scored.append((total_score, ent))

    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return "all_in_one_tech_canvas", _describe_engine("all_in_one_tech_canvas")

    best_score, best_ent = scored[0]
    # Rotate only inside a tight top relevance band (>= 88% of top score) on strong topic matches
    band = [ent for sc_val, ent in scored[:6] if sc_val >= best_score * 0.88] or [best_ent]
    pick_ent = band[(run_num + idx) % len(band)]
    geoms.add(pick_ent["geom"])
    return pick_ent["id"], _describe_engine(pick_ent["id"])
