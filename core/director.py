import json
import re
from typing import Dict, Any, Optional, List, Tuple
from core.config import GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, MISTRAL_API_KEY, OUTPUT_DIR
from core.tone_engine import (
    DEFAULT_CONCRETE_TONE,
    DEFAULT_TONE_KEY,
    DUAL_TONE_KEY,
    is_dual_tone,
    TONE_PROFILES,
    get_tone_directive,
    get_tone_profile,
    resolve_effective_tone,
)

VISUAL_HISTORY_PATH = OUTPUT_DIR / "visual_history.json"

# Compatible geometry families across ALL_STUDIO_LAYOUTS (Core 153 + Pro 154 + IT/SDLC 155 + Domain 360 + Grammar 156)
_DIVERSE_LAYOUT_FAMILIES: Dict[str, Tuple[str, ...]] = {
    "hook": (
        "hero_hook", "custom_scene", "cap_theorem_triangle", "incident_radar", "alert_diagram",
        "kinetic_statement", "grammar:grid:2x2", "grammar:bento:4", "grammar:quadrant:2x2",
        "checklist_scorecard", "pacelc_tradeoff", "venn_overlap", "incident_thundering_herd",
        "incident_split_brain", "incident_connection_exhaust", "incident_oom_kill_loop",
        "chaos_monkey_fault_inj", "dora_metrics_four_keys", "status_outage_banner",
        "grammar:bento:kpi_4", "grammar:quadrant:cost_latency", "grammar:triangle:cap",
    ),
    "flow": (
        "architecture_flow", "iso_architecture", "cdc_debezium_flow", "etl_elt_pipeline", "outbox_pattern_cdc",
        "saga_orchestration", "step_timeline", "roadmap_wave", "cicd_pipeline_stages", "sequence_diagram",
        "lsm_tree_compaction", "write_ahead_log_wal", "rate_limiter_token_bucket", "idempotency_key_store",
        "strangler_fig_migration", "event_sourcing_snapshots", "rag_chunk_overlap_pipe", "llm_tokenization_bpe",
        "browser_critical_path", "payment_idempotent_retry", "kalman_sensor_fusion", "flink_watermarks_window",
        "iso_saga_compensator", "iso_outbox_relay", "iso_zero_downtime_mig", "iso_vector_hybrid_rag",
        "debezium_chunk_snap", "e2e_test_sharding", "s3_presigned_upload", "io_uring_shared_ring",
        "grammar:flow:4", "grammar:flow:5", "grammar:chevron:4", "grammar:swimlane:3",
        "grammar:timeline_v:4", "grammar:pipeline:stream_5",
    ),
    "hub": (
        "circular_hub_mesh", "node_graph", "consistent_hashing_ring", "raft_leader_election",
        "circuit_breaker_states", "epoll_event_loop", "gossip_protocol_cluster", "sdlc_cycle_wheel",
        "sharding_hash_range", "hexagonal_ports_adapters", "radar_spider", "agent_react_tool_loop",
        "mcp_client_host_server", "supervisor_agent_orbit", "service_mesh_envoy_proxy", "ros2_dds_pubsub",
        "iso_observability_mesh", "iso_canary_rollout_tree", "hash_ring_vnodes", "redis_cluster_16k",
        "cf_durable_objects", "canary_score_judge",
        "grammar:ring:5", "grammar:hub:4", "grammar:orbit:4", "grammar:cycle:6",
    ),
    "tiers": (
        "layer_stack_3d", "pyramid_hierarchy", "l1_l2_l3_cache_tiers", "osi_7_layers", "medallion_lakehouse",
        "docker_cgroups_namespaces", "hnsw_vector_graph", "clean_architecture_rings", "tree_hierarchy",
        "b_plus_tree_pages", "merkle_tree_proof", "k8s_pod_scheduling", "iceberg_snapshot_tables",
        "llm_guardrails_safety", "pci_dss_token_vault", "quic_http3_0rtt", "mtls_handshake_1rtt",
        "cot_reasoning_tree", "docker_image_layers_ui", "dnssec_trust_chain", "vault_dynamic_leases",
        "grammar:tiers:4", "grammar:pyramid:4", "grammar:funnel:4", "grammar:tree:3", "grammar:ladder:4",
    ),
    "compare": (
        "split_comparison", "iso_comparison", "code_diff_split", "hybrid_merge", "pacelc_tradeoff",
        "process_thread_context", "index_seek_vs_scan", "dma_zero_copy_io", "matrix_2x2",
        "monolith_modular_vs_micro", "bfs_dfs_traversal", "venn_overlap", "compare_sync_vs_async",
        "compare_rest_vs_grpc", "compare_pull_vs_push", "compare_b_tree_vs_lsm",
        "llm_prefill_vs_decode", "optimistic_vs_zk_rollup", "crdt_gcounter_merge", "reward_hacking_shield",
        "grammar:dual:vs", "grammar:dual:tradeoff", "grammar:grid:3x2", "grammar:split:sync_async",
    ),
    "metrics": (
        "benchmark_chart", "benchmark_3d", "metric_gauge_hud", "radial_gauge", "latency_waterfall",
        "flamegraph_perf", "funnel_metrics", "stat_grid_2x2", "line_area_chart", "donut_3d",
        "pareto_frontier_plot", "box_whisker_latency", "slo_burn_rate_gauge", "big_o_complexity_curves",
        "gauge_slo_availability", "benchmark_throughput_ops", "multi_series_area", "p99_tail_cdf_curve",
        "latency_knee_point", "error_budget_burn", "amdahl_parallel_law", "usl_scalability_curve",
        "benchmark_p99_tail_latency", "perf_flamegraph_mutex", "perf_waterfall_db_lock",
        "grammar:waterfall:5", "grammar:funnel:latency_4",
    ),
    "code": (
        "code_terminal", "terminal_studio", "sql_table", "sql_studio", "data_structure_memory",
        "memory_lanes", "api_request_response", "er_schema", "columnar_parquet_blocks",
        "isolation_levels_matrix", "jwt_header_payload_sig", "memory_ring_buffer", "memory_lsm_memtable",
        "memory_wal_checkpoint", "memory_mvcc_tuple_hdr", "sql_window_partition", "sql_covering_index",
        "sql_jsonb_gin_index", "diff_n_plus_one_fix", "diff_mutex_to_atomic", "api_webhook_hmac_verify",
        "explain_plan_viewer", "openapi_schema_docs",
        "grammar:slots:5", "grammar:table:4x4", "grammar:code_flow:4",
    ),
    "summary": (
        "concept_cards", "checklist_scorecard", "kinetic_statement", "hybrid_merge",
        "step_timeline", "grammar:grid:2x2", "grammar:bento:5", "pyramid_hierarchy",
        "rfc_adr_decision_log", "checklist_prod_readiness", "checklist_sql_tuning",
        "checklist_migration_safety", "roadmap_zero_to_billion", "grammar:ladder:5",
    ),
}

_LAYOUT_TO_FAMILY: Dict[str, str] = {
    ly: fam for fam, group in _DIVERSE_LAYOUT_FAMILIES.items() for ly in group
}


def load_visual_history(session_history: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Loads recent visual generation history from session and disk so consecutive clicks vary completely."""
    base: Dict[str, Any] = {
        "run_count": 0,
        "recent_art_styles": [],
        "recent_visual_types": [],
        "recent_backdrops": [],
        "recent_transitions": [],
        "recent_text_fx": [],
    }
    if VISUAL_HISTORY_PATH.exists():
        try:
            loaded = json.loads(VISUAL_HISTORY_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for k in base:
                    if k in loaded:
                        base[k] = loaded[k]
        except Exception:
            pass
    if isinstance(session_history, dict) and session_history:
        if int(session_history.get("run_count", 0)) >= int(base.get("run_count", 0)):
            for k in base:
                if k in session_history:
                    base[k] = list(session_history[k]) if isinstance(base[k], list) else session_history[k]
    return base


def _save_visual_history(
    hist: Dict[str, Any],
    timeline: Dict[str, Any],
    session_history: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Records the newly generated art_style, visual_types, backdrops, transitions, and text_fx into history."""
    updated = dict(hist)
    updated["run_count"] = int(updated.get("run_count", 0)) + 1

    def _push_unique(key: str, items: List[str], cap: int) -> None:
        cur = [x for x in (updated.get(key) or []) if isinstance(x, str) and x]
        for it in items:
            if not it:
                continue
            cur = [x for x in cur if x != it]
            cur.append(it)
        updated[key] = cur[-cap:]

    scenes = timeline.get("scenes") or []
    _push_unique("recent_art_styles", [str(timeline.get("art_style") or "")], 24)
    _push_unique(
        "recent_visual_types",
        [
            str((sc.get("visual_data") or {}).get("option1_archetype") or (sc.get("visual_data") or {}).get("_intent") or sc.get("visual_type") or "")
            for sc in scenes if isinstance(sc, dict)
        ],
        96,
    )
    _push_unique("recent_backdrops", [str(sc.get("backdrop") or "") for sc in scenes if isinstance(sc, dict)], 18)
    _push_unique("recent_transitions", [str(sc.get("transition") or "") for sc in scenes if isinstance(sc, dict)], 12)
    _push_unique("recent_text_fx", [str(sc.get("text_fx") or "") for sc in scenes if isinstance(sc, dict)], 12)

    if isinstance(session_history, dict):
        session_history.clear()
        session_history.update(updated)
    try:
        VISUAL_HISTORY_PATH.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    except Exception:
        pass
    return updated


def reset_visual_history(session_history: Optional[Dict[str, Any]] = None) -> None:
    """Clears persisted visual layout history."""
    if isinstance(session_history, dict):
        session_history.clear()
    try:
        if VISUAL_HISTORY_PATH.exists():
            VISUAL_HISTORY_PATH.unlink()
    except Exception:
        pass

SYSTEM_PROMPT = """You are an elite Tech Content Director and Visual Storyteller for viral 9:16 vertical tech videos and reels (inspired by Fireship and ByteByteGo).
Your mission is to analyze any technical topic and autonomously design a realistic, topic-accurate, deeply engaging storyboard blueprint JSON.

CRITICAL DIRECTING PRINCIPLES:
1. PERFECT VOICE & VISUAL CORRESPONDENCE + COMPONENT-BY-COMPONENT SYNC (MANDATORY):
   - In EVERY scene, design DEEP, multi-section visual breakdowns (**4 to 5 richly detailed progressive components/steps/layers/nodes** per scene + clear `edge` connector labels + a concrete bottom `footer` / `summary` insight!). Never produce bare 2-card summaries!
   - Structure each scene's `narration` in **4 to 5 sequential spoken clauses** matching each component on screen in exact chronological order (`Clause 1` explains Box 1 -> `Clause 2` traces Link + Box 2 -> `Clause 3` reveals Box 3 metrics/code -> `Clause 4` explains Box 4 + takeaway).
   - Provide **4 to 5 exact chronological `choreography.triggers`** keywords (from start, middle, deep-detail, and closing clauses of `narration`) so every box, label, text, and connector link appears progressively RIGHT AS THE NARRATOR SPEAKS IT — never everything all at once!
   - Never output generic placeholder text (e.g., "Client Ingestion", "Block #101", "Pipeline logic"). Use REAL service names, SQL queries, commands, latency numbers, and real architectural internals.

2. DURATION & SCENE FLOW (TRUE TOPIC-ADAPTIVE — ZERO SCENE LIMIT):
   - Choose BOTH exact scene count AND runtime purely from the topic's depth and natural structure — NO artificial min/max scene cap (`3`, `5`, `9`, `12+`, or however many scenes explain the topic cleanly without rushing or filler).
   - Every distinct architectural tier, failure mode, code/SQL trace, trade-off, or execution step earns its own dedicated scene.
   - Flow naturally across Hook / Myth / Outage -> Architecture / System Design -> Internal Mechanism / Code / Data Flow -> Trade-offs / Recovery / Verdict.

3. CONVERSATIONAL HIGH-OCTANE NARRATION:
   - Explain like a staff engineer explaining a real production architecture over coffee.
   - Use natural pauses ("...") for emphasis and dramatic timing.
   - High information density, zero fluff, zero introductory throat-clearing ("In this video we will..."). Start immediately with the core engineering challenge or mechanism.

4. EXACT VISUAL ENGINE SCHEMAS:
Select the most appropriate visual_type for each scene from the following supported engines, and populate its visual_data with the exact schema:

- "architecture_flow":
  visual_data: {
    "badge": "SERVICE TOPOLOGY",
    "title": "Architecture Overview",
    "nodes": [
      {"id": "src", "label": "Source DB / Service", "sub": "MySQL / PostgreSQL / Client", "color": "#38BDF8"},
      {"id": "engine", "label": "Processing Instance / Engine", "sub": "Replication / CDC / Broker", "color": "#FBBF24"},
      {"id": "target", "label": "Target Cluster", "sub": "Amazon Aurora / Snowflake / S3", "color": "#34D399"}
    ]
  }

- "code_terminal":
  visual_data: {
    "badge": "TERMINAL EXECUTION",
    "title": "CLI / Code Implementation",
    "command": "optional CLI command (e.g. aws dms start-replication-task)",
    "code_snippet": "Actual code/SQL/script syntax (5-8 lines)",
    "output": "Optional terminal output"
  }

- "sql_table":
  visual_data: {
    "badge": "QUERY & DATASET",
    "title": "Data Schema & Execution",
    "code_snippet": "SELECT emp_id, salary, DENSE_RANK() OVER (ORDER BY salary DESC) FROM emp;",
    "table_data": {
      "headers": ["EMP_ID", "NAME", "SALARY", "DENSE_RANK"],
      "rows": [
        ["101", "Alice", "120,000", "1"],
        ["102", "Bob", "95,000", "2"],
        ["103", "Charlie", "95,000", "2"],
        ["104", "Diana", "80,000", "3"]
      ]
    }
  }

- "data_structure_memory":
  visual_data: {
    "badge": "MEMORY & BUFFER INTERNALS",
    "title": "CDC WAL Buffer / Memory Offsets",
    "entries": [
      {"address": "0x00A1", "op": "COMMIT LSN 4920", "table": "orders", "status": "REPLICATED"},
      {"address": "0x00B4", "op": "INSERT LSN 4921", "table": "payments", "status": "IN-TRANSIT"},
      {"address": "0x00C8", "op": "UPDATE LSN 4922", "table": "inventory", "status": "BUFFERED"}
    ]
  }

- "split_comparison":
  visual_data: {
    "badge": "ARCHITECTURAL TRADE-OFF",
    "title": "Legacy Approach vs Modern Solution",
    "left_label": "TRADITIONAL ETL",
    "left_points": ["Heavy Table Locks", "Hours of Downtime", "High Latency Failovers"],
    "right_label": "CDC ZERO-DOWNTIME",
    "right_points": ["Sub-Second Lag", "Zero Production Locks", "Continuous Sync"]
  }

- "benchmark_chart":
  visual_data: {
    "badge": "PERFORMANCE BENCHMARK",
    "title": "Throughput & Latency Comparison",
    "winner_badge": "10X FASTER REPLICATION",
    "bars": [
      {"label": "Standard Batch Load", "value": 4500, "display": "4.5s Batch Latency", "color": "#EF4444", "is_winner": false},
      {"label": "Micro-Batch Ingestion", "value": 350, "display": "350ms", "color": "#FBBF24", "is_winner": false},
      {"label": "Direct CDC Memory Stream", "value": 24, "display": "24ms Lag (Winner)", "color": "#10B981", "is_winner": true}
    ]
  }

- "alert_diagram":
  visual_data: {
    "badge": "PRODUCTION ALERT",
    "title": "System Bottleneck & Dilemma",
    "problem_title": "Production Table Locking Under Migration",
    "problem_desc": "Running traditional mysqldump on a multi-terabyte database locks production rows and drops client transactions.",
    "challenge": "How do we replicate petabytes of live data with zero downtime?"
  }

- "circular_hub_mesh":
  visual_data: {
    "badge": "DISTRIBUTED CLUSTER",
    "title": "Event Mesh Topology",
    "hub_name": "CENTRAL BROKER",
    "satellites": [
      {"name": "Client Ingestion", "role": "REST / gRPC", "color": "#38BDF8"},
      {"name": "Replication Worker", "role": "CDC Parser", "color": "#10B981"},
      {"name": "Aurora Target", "role": "Multi-AZ Writer", "color": "#FBBF24"},
      {"name": "Dead Letter Queue", "role": "Error Buffer", "color": "#EF4444"}
    ]
  }

- "metric_gauge_hud":
  visual_data: {
    "badge": "TELEMETRY METRICS",
    "title": "Live System Health",
    "main_value": "99.999%",
    "main_unit": "CDC SYNCHRONIZATION",
    "gauge_percent": 98,
    "telemetry": [
      {"label": "REPLICATION LAG", "val": "< 12ms"},
      {"label": "DROPPED BYTES", "val": "0 B"},
      {"label": "CPU LOAD", "val": "18%"}
    ]
  }

- "concept_cards":
  visual_data: {
    "badge": "CORE MECHANISMS",
    "title": "Key Engineering Principles",
    "bullets": [
      "Strict Output Format: Enforce JSON, SQL, or specific domain tone",
      "Relatively Stable Data: Ideal when rules rarely change"
    ],
    "warning_box": "Optional warning box (e.g. NOT for live facts or frequent policy updates)",
    "footer_cta": "Optional bottom CTA strip (e.g. Save • Share • Follow for More)",
    "accent_theme": "emerald_matrix"
  }

- "hero_hook":
  visual_data: {
    "badge": "INTERVIEW QUESTION / TOPIC HOOK",
    "title": "Scene Headline",
    "question": "Central Hero Question or Core Dilemma",
    "left_pill": "Option A (e.g. RAG)",
    "right_pill": "Option B (e.g. Fine-Tuning)",
    "stat_badge": "90% Candidates Confused",
    "sub_callouts": ["Trap 1: Using A everywhere", "Trap 2: Using B for live data"],
    "accent_theme": "indigo_cyan"
  }

- "hybrid_merge":
  visual_data: {
    "badge": "PRODUCTION BEST PRACTICE: HYBRID",
    "title": "The Hybrid Architecture",
    "left_pillar": {"label": "Fine-Tuning", "sub": "Clean Structure & Tone"},
    "right_pillar": {"label": "RAG System", "sub": "Fresh Context & Policies"},
    "merged_label": "Production AI System",
    "outcomes": ["Accuracy", "Consistency", "Freshness"],
    "accent_theme": "gold_purple"
  }

- "kinetic_statement":
  visual_data: {
    "badge": "KEY INSIGHT",
    "title": "Scene Headline",
    "kicker": "THE GOLDEN RULE",
    "statement": "Punchy bold focal sentence (5-9 words max)",
    "highlight_word": "Keyword",
    "bottom_tags": ["Tag 1", "Tag 2", "Tag 3"],
    "accent_theme": "fireship / indigo_cyan"
  }

- "step_timeline":
  visual_data: {
    "badge": "STEP-BY-STEP EXECUTION",
    "title": "How The Flow Works",
    "steps": [
      {"num": "01", "title": "Step 1 Title", "desc": "Exact detail from narration"},
      {"num": "02", "title": "Step 2 Title", "desc": "Exact detail from narration"},
      {"num": "03", "title": "Step 3 Title", "desc": "Exact detail from narration"},
      {"num": "04", "title": "Step 4 Title", "desc": "Exact detail from narration"}
    ],
    "accent_theme": "cyber_cyan"
  }

- "custom_scene":
  visual_data: {
    "badge": "SCENE CATEGORY",
    "title": "Concise Scene Title",
    "art_style": "light_whiteboard / editorial_dark / blueprint_grid / neon_fireship",
    "blocks": [
      {"block": "big_stat", "number": "3", "label": "QUESTIONS ASKED IN SOC INTERVIEWS", "sub": "", "stage": 1},
      {"block": "question_card", "eyebrow": "", "text": "Your exact focal question or hook line", "stage": 1},
      {"block": "pills", "items": ["Item 1", "Item 2", "Item 3"], "mode": "row / grid / vs", "stage": 2},
      {"block": "flow_chain", "nodes": [{"title": "Node A", "sub": "Detail"}, {"title": "Node B", "sub": "Detail"}], "arrows": ["Action Label ->"], "stage": 2},
      {"block": "list_cards", "items": [{"title": "Point 1", "desc": "Exact detail", "kind": "check / warn / info"}], "stage": 3},
      {"block": "banner", "text": "Bottom CTA or Warning Callout", "tone": "cta / warn / highlight", "stage": 4}
    ]
  }

- "all_in_one_tech_canvas":
  visual_data: {
    "badge": "SYSTEM ARCHITECTURE",
    "title": "Scene Specific Title",
    "vpc_label": "CLOUD / SYSTEM BOUNDARY",
    "comp1_label": "Primary Input / Client",
    "comp1_sub": "Role in this scene",
    "comp2_label": "AI / Reasoning / Secondary",
    "comp2_sub": "Role in this scene",
    "comp3_label": "Core Orchestrator / Bus",
    "comp3_sub": "Role in this scene",
    "comp4_label": "Primary Storage / DB",
    "comp4_sub": "Role in this scene",
    "comp5_label": "Target Output / Lake",
    "comp5_sub": "Role in this scene",
    "arrow1_label": "Step 1 Flow",
    "arrow2_label": "Step 2 Flow",
    "arrow3_label": "Step 3 Flow",
    "arrow4_label": "Step 4 Flow"
  }

STRICT JSON OUTPUT FORMAT ONLY:
Output a single valid JSON object matching this structure:
{
  "title": "Topic Title",
  "topic_category": "cloud / database / programming / system_design / security / ai",
  "art_style": "editorial_dark / blueprint_grid / light_whiteboard / neon_fireship",
  "total_target_seconds": 75,
  "scenes": [
    {
      "scene_id": 1,
      "role": "hook",
      "scene_tone": "war_story_postmortem / myth_buster_contrarian / live_debug_pair / whiteboard_analogy / cage_match_vs / release_radar_tldr / bigtech_reverse_engineer / dual_creator_debate",
      "narration": "Narration with crisp Hook-to-Climax cadence and natural '...' pauses (or full spoken transcript if dialogue array is used)...",
      "dialogue": [
        {"speaker": "female", "text": "Optional for dual_creator_debate: Builder's sharp engineering question/challenge..."},
        {"speaker": "male", "text": "Optional for dual_creator_debate: Staff architect's direct mechanism & counter-proof..."}
      ],
      "visual_type": "custom_scene",
      "choreography": {
        "mode": "progressive_node_edge",
        "triggers": [
          {"stage": 1, "keyword": "first_keyword_from_narration"},
          {"stage": 2, "keyword": "second_keyword_from_narration"},
          {"stage": 3, "keyword": "third_keyword_from_narration"},
          {"stage": 4, "keyword": "fourth_keyword_from_narration"}
        ]
      },
      "visual_data": {
        "badge": "BADGE TEXT",
        "title": "Scene Title",
        "art_style": "editorial_dark / blueprint_grid / light_whiteboard / neon_fireship",
        "accent_theme": "indigo_cyan / cyber_cyan / emerald_matrix / gold_purple / crimson_alert",
        "...": "Fields strictly populated from the schema above (for big_stat ALWAYS use 'value' key)"
      }
    }
  ]
}
"""

ENGINE_STYLE_DIRECTIVES = {
    "omni_smart_director": (
        "OMNI SMART DIRECTOR (ALL 25 ENGINES UNIFIED — ZERO-HARDCODE 6-GEOMETRY SCENE ROUTER): "
        "Select the SINGLE BEST specialist visual engine & layout for EACH INDIVIDUAL SCENE while pulling authentic topic entities, numbers, SQL, code, and flows directly from the spoken narration/dialogue:\n"
        "- Hook / Opening Scene: Use `chat_thread_ai` (populating `messages` directly from `dialogue`), `mobile_app_mockup`, `browser_window`, `incident_radar`, or `hero_hook` with exact spoken question/metrics.\n"
        "- Architecture Scene: Pick matching Dual-Plane Topology (`topo_kafka_isr_quorum_dlq`, `cdc_debezium_flow`, `topo_saga_choreo_compensate`, `rag_chunk_overlap_pipe`, etc.) AND populate BOTH `plane_a` (3 ingress/control nodes) and `plane_b` (3 execution/storage nodes) using actual concepts spoken in that scene.\n"
        "- Data / SQL / Flow Scene: Populate `sql_studio`/`sql_window_partition` with exact spoken `query`, `columns`, `rows`, OR use `sequence_diagram`/`sankey_flow`/`radar_spider`/`donut_3d` with real spoken entities.\n"
        "- Code / Metrics / Memory Scene: Populate `code_diff_split`/`code_terminal` with real spoken commands/snippets, `benchmark_3d`/`p99_tail_cdf_curve` with exact spoken latencies/speedups, OR `memory_wal_checkpoint`.\n"
        "- Trade-off & Closing Scene: Populate `compare_sync_vs_async`/`iso_comparison` (`left_points`/`right_points`), Composable Grammar (`grammar:pyramid:4`, `grammar:funnel:4`, `grammar:ring:6`), or Option 1 WebGL (`spatial_constellation`, `svg_ecdh_key_exchange`).\n"
        "NEVER use dummy names or generic code; every on-screen text/metric MUST mirror that scene's spoken words!"
    ),
    "multi_topology_mix": (
        "MULTI-TOPOLOGY INTERCONNECTED ARCHITECTURE ENGINE: "
        "Every scene in the reel MUST visualize rich multi-component System Topologies (`all_in_one_tech_canvas`, `iso_observability_mesh`, "
        "`service_mesh_envoy_proxy`, `medallion_lakehouse`, `cdc_debezium_flow`, `zero_trust_proxy`, `kafka_event_backbone`, `saga_orchestration`, "
        "`k8s_pod_scheduling`, `consistent_hashing_ring`, `spatial_microservice_grid`, `svg_pipeline_choreography`, `rag_chunk_overlap_pipe`). "
        "Include 4-5 connected nodes with clear `edge` protocol/action labels AND `voice_beats` across distinct topology layers in EVERY scene!"
    ),
    "interactive_storyboard": (
        "INTERACTIVE MOTION STORYBOARD MAX: "
        "Compose crystal-clear multi-stage visual storyboards where EVERY narration phrase activates a specific UI card/badge/link/bubble "
        "(`thought`, `warning`, `pro-tip`, `status`, `quiz`, `delta`) aligned word-for-word to `choreography.triggers` & `voice_beats`. "
        "Vary across ALL visual families (`quiz`, `radar`, `flamegraph`, `sequence`, `er_schema`, `kanban`, `sankey`, `mesh_3d`, `web_scene`, `svg_scene`)."
    ),
    "studio_300_domain": (
        "UNLIMITED STUDIO MAX + ZERO-TEMPLATE HYBRID ENGINE (OPTION 1 + OPTION 2 COMBINED — 820+ DOMAIN LAYOUTS + 158 GRAMMAR + 156 OPTION 1 WEBGL/SVG/SPATIAL): "
        "Mix bespoke zero-template scenes (`web_scene`, `svg_scene`, `spatial_canvas` with `visual_data.option1_archetype`) AND specialized 820+ Domain Layouts across every scene! NEVER use the same layout twice in one reel or repeat modes across videos!\n"
        "1. COLOR WORLDS: Any of 32+ contrast-locked worlds (`obsidian_studio`, `sapphire_3d`, `navy_studio`, `espresso_brown`, `studio_white`, `light_grey_editorial`, etc.).\n"
        "2. BACKDROP, TRANSITION & TEXT FX: Vary `backdrop` (18 styles), `transition` (12 styles), and `text_fx` (14 styles) per scene.\n"
        "3. USE DIVERSE VISUAL TYPES & MULTIPLE SYSTEM TOPOLOGIES ACROSS SCENES (populate 4-5 detailed sub-sections + `edge` labels + `footer` + `voice_beats`!):\n"
        "   - Zero-Template Custom (156 archetypes): `web_scene`, `svg_scene`, `spatial_canvas` (`elements` 0..1000 + `connections`).\n"
        "   - Domain, Topologies & Pro Charts: `all_in_one_tech_canvas`, `cdc_debezium_flow`, `iceberg_snapshot_tables`, `k8s_pod_scheduling`, `transformer_self_attn`, `mcp_tool_bridge`, `quic_http3_0rtt`, `rag_chunk_overlap_pipe`, `double_entry_ledger`, `ros2_dds_pubsub`, `medallion_lakehouse`, `consistent_hashing_ring`, `raft_leader_election`, `circuit_breaker_states`, `write_ahead_log_wal`, `mesh_3d_stage`, `sequence_diagram`, `er_schema`, `flamegraph_perf`, `latency_waterfall`, `sankey_flow`, `radar_spider`, `kanban_board`, `benchmark_3d`.\n"
        "   - Composable Diagram Grammar (158 presets): `grammar:grid:3x2`, `grammar:flow:5`, `grammar:ring:6`, `grammar:bento:5`, `grammar:swimlane:3`, `grammar:chevron:4`, `grammar:pyramid:4`, `grammar:funnel:4`, `grammar:quadrant:2x2`.\n"
        "4. Populate `scene_tone` & 5 chronological `choreography.triggers` aligned to voice words per scene."
    ),
    "pure_zero_template": (
        "PURE ZERO-TEMPLATE AI CODE-AS-VIDEO ENGINE (OPTION 1 — 54+ INTERACTIVE WEBGL / SVG / SPATIAL CODE ARCHETYPES, ZERO REPEATING TEMPLATES): "
        "CRITICAL RULE: NEVER repeat the same layout or generic placeholders across scenes! Write rich, topic-specific structured details in `visual_data` (including optional `visual_data.option1_archetype` from `web_*`, `svg_*`, `spatial_*`) for EVERY scene so our dedicated AI HTML5/Canvas3D Code Synthesizer builds a completely unique interactive visual composition per scene:\n"
        "- Scene 1 (Hook/Problem): Use `alert_diagram` or `split_comparison` with real production dilemma, risk blips (`alerts`), `left_points`/`right_points`, or metrics.\n"
        "- Scene 2 (Architecture/Flow): Use `architecture_flow`, `cdc_debezium_flow`, or `circular_hub_mesh` with concrete `nodes`/`stages`/`satellites` and service icons (`postgres`, `kafka`, `aws`, `router`, `server`).\n"
        "- Scene 3 (Internals/Code/Stream): Use `data_structure_memory` (`entries` with hex offsets/LSN), `code_terminal` (`command`, `code_snippet`, `output`), or `sql_table`.\n"
        "- Scene 4 (Proof/Metrics/Switch): Use `benchmark_chart` (`bars` with numeric `value`, unit `display`, `is_winner`, `winner_badge`), `metric_gauge_hud` (`main_value`, `gauge_percent`, `telemetry`), or `step_timeline`.\n"
        "Optionally provide `visual_data.html` or `visual_data.svg` directly, AND vary `art_style`, `backdrop`, `transition`, `text_fx`, `scene_tone`, and 4 `choreography.triggers` per scene!"
    ),
    "studio_domain_library": (
        "DOMAIN LAYOUT LIBRARY PRO (OPTION 2 — 670+ SPECIALIZED DOMAIN LAYOUTS + 56 COMPOSABLE GRAMMAR PRESETS): "
        "Select the most technically authentic specialized layout from the **670+ Domain Library across 18 Engineering Domains + Pro Charts + IT/SDLC** (never repeat the same layout twice in one reel!):\n"
        "- Algorithms & DSA: `binary_search_trace`, `two_pointers_window`, `sliding_window_buffer`, `quicksort_partition`, `heap_priority_tree`, `trie_prefix_tree`, `bloom_filter_bits`, `lru_cache_eviction`, `consistent_hashing_ring`, `merkle_tree_proof`.\n"
        "- Databases & Storage: `b_plus_tree_pages`, `lsm_tree_compaction`, `write_ahead_log_wal`, `mvcc_snapshot_versions`, `two_phase_commit_2pc`, `saga_orchestration`, `sharding_hash_range`, `hnsw_vector_graph`, `columnar_parquet_blocks`.\n"
        "- Distributed Systems: `raft_leader_election`, `paxos_quorum_rounds`, `cap_theorem_triangle`, `circuit_breaker_states`, `rate_limiter_token_bucket`, `idempotency_key_store`, `outbox_pattern_cdc`, `backpressure_reactive`.\n"
        "- AI/LLM, Web, Mobile, FinTech, Web3 & Robotics: `llm_tokenization_bpe`, `rag_chunk_overlap_pipe`, `mcp_client_host_server`, `browser_critical_path`, `react_fiber_reconciler`, `double_entry_ledger`, `merkle_patricia_trie`, `ros2_dds_pubsub`, `kalman_sensor_fusion`.\n"
        "- Networking, Data Eng, Hardware & SDLC: `client_server_cluster`, `osi_7_layers`, `quic_http3_0rtt`, `iceberg_snapshot_tables`, `k8s_pod_scheduling`, `medallion_lakehouse`, `etl_elt_pipeline`, `cdc_debezium_flow`, `sdlc_cycle_wheel`, `cicd_pipeline_stages`.\n"
        "- Also supports 56 Composable Grammar Presets (`grammar:grid:3x2`, `grammar:flow:5`, `grammar:ring:6`, `grammar:bento:5`, `grammar:swimlane:3`, `grammar:pyramid:4`, `grammar:funnel:4`) + all 145 3D shapes + 200k+ 3D SVGs.\n"
        "- Vary 46 `art_style` worlds / `#HEX`, 18 `backdrop`s, 12 `transition`s, 14 `text_fx`. Populate `scene_tone` & 4 `choreography.triggers`."
    ),
    "cinematic_studio": (
        "CINEMATIC 2.5D/3D STUDIO MAX MODE (100+ LAYOUTS, 145+ 3D SHAPES & 200k+ 3D SVGS): "
        "Combine 46+ studio palettes + Infinite HSL/Gradient colors, 100+ dedicated layouts + Spatial Composer + Keyframe AI <svg>, 145 3D Shapes & Meshes, 168 Glyphs, 200k+ 3D-Extruded Iconify SVGs, 18 Procedural Backdrops, 12 Transitions & 14 Text FX!\n"
        "1. COLOR WORLD (`art_style` & `palette`): Pick any of 46 curated worlds (`obsidian_studio`, `aurora_borealis`, `synthwave_84`, `quantum_indigo`, `studio_white`, `cream_notion`, `terminal_phosphor`, etc.) OR any `#HEX` / `visual_data.palette: {\"stops\":[\"#...\",\"#...\"],\"mode\":\"dark\"|\"light\"}`.\n"
        "2. PER-SCENE ATMOSPHERE & MOTION FX (`backdrop`, `transition`, `text_fx`):\n"
        "   - `backdrop`: `subtle_grid`, `aurora_mesh`, `pcb_circuits`, `topo_contours`, `hex_honeycomb`, `dot_matrix`, `starfield_cosmos`, `bokeh_cinema`, `concentric_radar`, `isometric_cubes_subtle`, `duotone_beam`, `paper_editorial`, `glass_caustics`, `plasma_wave`, `voronoi_cells`, `orbital_arcs`, `prism_rays`, `code_stream_subtle`.\n"
        "   - `transition`: `crossfade`, `slide_up`, `slide_down`, `slide_left`, `slide_right`, `zoom_push`, `zoom_pull`, `wipe_reveal`, `iris_circle`, `curtain_split`, `parallax_pan`, `glitch_snap`.\n"
        "   - `text_fx`: `clean_fade`, `word_pop`, `highlighter_brush`, `typewriter_cursor`, `gradient_shimmer`, `neon_underline`, `glitch_text`, `slide_reveal`, `strike_vs_new`, `quote_serif_glow`.\n"
        "3. 100+ DEDICATED LAYOUTS (Match the topic domain!):\n"
        "   - Networking & IT Infra: `osi_7_layers`, `tcp_ip_handshake`, `dns_resolution_flow`, `vpc_subnet_topology`, `cdn_edge_routing`, `vpn_tunnel_mesh`, `firewall_dmz_zones`, `vlan_switch_ports`, `bgp_routing_table`, `zero_trust_mesh`, `hardware_rack_diagram`, `client_server_cluster`.\n"
        "   - Data Engineering & Lakehouse: `etl_elt_pipeline`, `medallion_lakehouse`, `lambda_kappa_arch`, `kafka_streaming_topology`, `star_snowflake_schema`, `cdc_debezium_flow`, `data_warehouse_cluster`, `data_quality_lineage`, `spark_dag_stages`, `feature_store_ml`.\n"
        "   - SDLC, DevOps & Software Tools: `sdlc_cycle_wheel`, `cicd_pipeline_stages`, `agile_sprint_board`, `gitflow_release_lanes`, `test_pyramid_qa`, `blue_green_canary`, `microservices_mesh`, `event_driven_cqrs`, `observability_pillars`, `devsecops_shield_gate`, `tech_stack_layers`, `cloud_services_map`, `language_ecosystem`.\n"
        "   - Core, Spatial, AI SVG & Analytics: `iso_architecture`, `node_graph`, `iso_comparison`, `terminal_studio`, `kinetic_statement`, `custom_scene`, `spatial_canvas`, `svg_scene` (Animated `<g id='stage_1..6'>`), `neural_net_layers`, `attention_heatmap`, `embedding_cluster`, `rag_pipeline_3d`, `agent_loop_3d`, `token_prob_bars`, `mesh_3d_stage`, `line_area_chart`, `donut_3d`, `radar_spider`, `sankey_flow`, `candlestick_pro`, `heatmap_matrix`, `scatter_plot`, `confusion_matrix`, `mobile_app_mockup`, `browser_window`, `chat_thread_ai`, `kanban_board`, `pricing_tiers`, `layer_stack_3d`, `matrix_2x2`, `pyramid_hierarchy`, `sql_studio`, `benchmark_3d`, `radial_gauge`, `sequence_diagram`, `er_schema`, `state_machine`, `git_branch_tree`, `flamegraph_perf`, `latency_waterfall`.\n"
        "4. 145 3D SHAPES + 200k+ 3D-EXTRUDED LANGUAGE / TOOL / CLOUD / HARDWARE SVGS:\n"
        "   - Hardware & Networking Shapes: `mobile`, `tablet`, `laptop`, `desktop`, `server_rack`, `rack_cabinet`, `blade_server`, `hub`, `network_switch`, `router`, `firewall_wall`, `ssd_nvme`, `smartwatch`, `printer`, `webcam`, `headset`, `usb_drive`, `ethernet_port`, `patch_panel`, `fiber_cable`, `cell_tower`, `dns_server`, `vpn_tunnel`, `subnet_zone`, `vlan_ring`, `ups_battery`.\n"
        "   - Data / SDLC / 3D Meshes: `data_pipe`, `data_lake`, `lakehouse`, `spark_engine`, `kafka_broker`, `warehouse_3d`, `schema_table`, `dag_pipeline`, `sdlc_wheel`, `ci_runner`, `unit_test_cube`, `pr_merge`, `release_tag_3d`, `k8s_pod_mesh`, `torus_3d`, `dna_helix`, `atom_orbit`, `geodesic_sphere`, `neural_lattice`.\n"
        "   - Real SVG Icons (auto 3D extruded!): `python`, `java`, `javascript`, `typescript`, `cpp`, `csharp`, `go`, `rust`, `php`, `ruby`, `scala`, `r`, `dart`, `bash`, `react`, `fastapi`, `postgres`, `mysql`, `mongodb`, `redis`, `clickhouse`, `duckdb`, `snowflake`, `databricks`, `spark`, `kafka`, `airflow`, `dbt`, `hadoop`, `flink`, `trino`, `aws_s3`, `aws_lambda`, `aws_ec2`, `aws_rds`, `aws_eks`, `gcp`, `azure`, `docker`, `kubernetes`, `helm`, `terraform`, `ansible`, `jenkins`, `argocd`, `git`, `gitlab`, `jira`, `postman`, `vscode`, `playwright`, `selenium`, `cypress`, `jest`, `sonarqube`, `prometheus`, `grafana`, `datadog`, `sentry`, `nginx`, `envoy`, `cisco`, `wireshark`, `cloudflare`, or ANY `logos:*` / `lucide:*` / `simple-icons:*`.\n"
        "5. ZERO HARDCODED FILLER: Populate `scene_tone` & 4 `choreography.triggers`."
    ),
    "dual_generative": (
        "ZERO-LIMIT DUAL GENERATIVE ENGINE (WEBGL / THREE.JS / HTML5 + 3D MESH / SHADER / KEYFRAME SVG): "
        "Zero template limits! Generate `web_scene` (`visual_data.html` with interactive HTML5 + CSS3 + Three.js/Canvas + `window.__setStudioProgress(p, curTime, energy)`) OR use any of 100+ IT/Networking/Data Eng/SDLC/AI layouts + 145 3D Hardware/Mesh shapes + 200k+ 3D-Extruded Language/Cloud SVGs + 18 Shaders + 12 Transitions + 14 Text FX."
    ),
    "auto_dynamic": (
        "AI AUTONOMOUS VISUAL & STORYBOARD COMPOSER MODE (ZERO HARDCODED TEMPLATES): "
        "Every topic and custom script MUST feel visually unique in composition, typography, color world, and layout! "
        "1. MATCH `art_style` TO THE TOPIC DOMAIN (never default every topic to the same style!):\n"
        "   - `blueprint_grid`: Deep sapphire CAD grid (best for cybersecurity, SOC, networking, infra, Cloud/K8s, SRE, systems internals).\n"
        "   - `editorial_dark`: Sleek charcoal matte keynote with bold left-aligned editorial type (best for interviews, career advice, trade-offs, staff engineering stories).\n"
        "   - `light_whiteboard`: Clean off-white ByteByteGo whiteboard paper (best for step-by-step tutorials, ML/AI comparisons, RAG/data pipelines, conceptual diagrams).\n"
        "   - `neon_fireship`: High-energy cyber streaks (best for rapid coding comparisons, hot takes, benchmarks, debugging bugs).\n"
        "2. PREFER COMPOSABLE `custom_scene` OR VARIED ENGINES PER SCENE:\n"
        "   - NEVER force non-comparison lists (like '3 questions', '3 rules', '4 stages') into a `VS` template!\n"
        "   - For 3-item hooks or custom user Visuals/Progressive Flow specs, use `custom_scene` with exact `blocks` (`big_stat`, `question_card`, `pills` with mode='row'/'grid'/'vs', `flow_chain`, `list_cards`, `banner`).\n"
        "   - Also mix `step_timeline`, `kinetic_statement`, `split_comparison` (set `neutral_mode: true` & `show_vs: true/false` appropriately), `sql_table`, `code_terminal`, `benchmark_chart`, `hybrid_merge`, `circular_hub_mesh`, and `all_in_one_tech_canvas`.\n"
        "   - ONLY use `alert_diagram` for real production crashes/outages.\n"
        "3. ZERO CANNED FILLER TEXT: Put the user's ACTUAL question, Hinglish/Marathi/English terms, CTAs ('Comment SOC...'), and warnings verbatim into visual_data.\n"
        "4. MANDATORY AUDIO-VISUAL SYNC CHOREOGRAPHY: For EVERY scene, output `scene_tone` and `choreography.triggers` (4 chronological keywords from `narration`)."
    ),
    "all_in_one_tech_canvas": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'All-in-One Tech Canvas'. "
        "EVERY scene's visual_type MUST BE 'all_in_one_tech_canvas'. "
        "Illustrate the complete modern technical ecosystem: 2D Database Cylinders, Python Silicon Chip, "
        "Server Blade Racks, AI Robot / LLM Reasoning, Amazon S3 Storage Buckets, Cloud VPC Boundaries, "
        "animated data packet arrows, and active motion pointers."
    ),
    "terminal_screencast": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Terminal Screencast'. "
        "EVERY scene's visual_type MUST BE 'code_terminal'. "
        "Populate visual_data with real CLI commands ($ ...), execution logs, scripts, and code snippets strictly relevant to the topic."
    ),
    "bytebytego_dsl": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'ByteByteGo Architecture'. "
        "EVERY scene MUST use visual_type 'architecture_flow' or 'circular_hub_mesh'. "
        "Show concrete cloud service pipelines (Source -> Engine -> Target) with labeled nodes and descriptions."
    ),
    "sql_deepdive": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'SQL Table & Query'. "
        "EVERY scene MUST use visual_type 'sql_table'. "
        "Show real SQL table schemas, formatted row data, and active SQL queries (e.g. DENSE_RANK, Window functions, JOINs)."
    ),
    "split_comparison": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Split Comparison'. "
        "EVERY scene MUST use visual_type 'split_comparison'. "
        "Show side-by-side trade-offs with left_label (Problem/Legacy), right_label (Solution/Modern), left_points, and right_points."
    ),
    "benchmark_speed": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Performance Benchmarks'. "
        "Scenes MUST use visual_type 'benchmark_chart' or 'metric_gauge_hud'. "
        "Show latency bars, throughput comparisons, and winner badges."
    ),
    "memory_internals": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Memory Internals & Buffer Slots'. "
        "Scenes MUST use visual_type 'data_structure_memory'. "
        "Show hex addresses (0x00A1), WAL log entries, and active buffer slots."
    ),
    "network_mesh": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Circular Hub & Spoke Mesh'. "
        "Scenes MUST use visual_type 'circular_hub_mesh'. "
        "Show a central core broker with satellite services and radar pulses."
    ),
    "telemetry_hud": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Speedometer & Telemetry HUD'. "
        "Scenes MUST use visual_type 'metric_gauge_hud'. "
        "Show speedometer radial arcs, main telemetry statistics, and real-time SLA metrics."
    ),
    "alert_troubleshoot": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Production Alert & Post-Mortem'. "
        "Scenes MUST use visual_type 'alert_diagram'. "
        "Show warning radar alerts, problem bottleneck boxes, and critical engineering dilemmas."
    ),
    "concept_keynote": (
        "CRITICAL MANDATORY INSTRUCTION: The user explicitly selected 'Kinetic Concept Keynote'. "
        "Scenes MUST use visual_type 'concept_cards'. "
        "Show bold headline bullets with engineering principles and throughput HUDs."
    ),
    "hybrid_modern": (
        "BALANCED COMPOSITION: The user selected 'Hybrid Modern'. "
        "Use an intelligent mix across the video: Scene 1 alert_diagram or split_comparison, Scene 2 architecture_flow, Scene 3 code_terminal or data_structure_memory, Scene 4 concept_cards."
    ),
    "custom_user_style": (
        "CUSTOM USER AESTHETIC: Follow the user's custom style prompt strictly across all scenes."
    )
}

# Canonical 2026 TONE_DIRECTIVES imported from core/tone_engine.py (Zero overlapping/legacy tones)
TONE_DIRECTIVES: Dict[str, str] = {
    k: str(v["directive"]) for k, v in TONE_PROFILES.items()
}

def generate_timeline(
    topic: str,
    tone: str = DEFAULT_TONE_KEY,
    engine_style: str = "hybrid_modern",
    duration_mode: str = "auto",
    custom_style_prompt: str = "",
    voice: str = "en-US-ChristopherNeural",
    format_ratio: str = "9:16",
    visual_history: Optional[Dict[str, Any]] = None,
    audience_level: str = "working_dev",
    hook_style: str = "ai_auto",
    cta_style: str = "save_share",
    cta_keyword: str = "",
) -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini/Groq/OpenRouter models,
    maintaining persistent visual history for Option 1, Option 2, and Combined engines so
    every click produces distinct layouts, palettes, shaders, and compositions.
    """
    hist = load_visual_history(visual_history)
    run_num = int(hist.get("run_count", 0)) + 1
    _DIVERSE_ENGINES = (
        "omni_smart_director", "studio_domain_library", "pure_zero_template", "studio_300_domain",
        "multi_topology_mix", "interactive_storyboard",
        "data_streaming_pipelines", "distributed_consensus_labs", "ai_rag_agents_studio",
        "dual_generative", "cinematic_studio", "auto_dynamic", "hybrid_modern",
    )
    if engine_style == "custom_user_style" and custom_style_prompt.strip():
        style_directive = (
            f"MANDATORY CUSTOM STYLE DIRECTIVE: The user explicitly requested this custom visual aesthetic: "
            f"'{custom_style_prompt.strip()}'. You MUST tailor your visual_type and visual_data to reflect this custom design aesthetic across all scenes."
        )
    else:
        style_directive = ENGINE_STYLE_DIRECTIVES.get(engine_style, ENGINE_STYLE_DIRECTIVES["auto_dynamic"])
    
    # 1. Language & Dialect based on the selected Voice Persona & Tone
    if is_dual_tone(tone) or str(voice).startswith("dual:"):
        v_low = str(voice).lower()
        if "mr-in" in v_low:
            lang_directive = (
                "LANGUAGE & DIALECT MANDATE (DUAL VOICE MARATHI/MINGLISH DIALOGUE): "
                "Generate alternating `dialogue` turns (`female` curious builder + `male` staff architect) in natural conversational Hinglish/Minglish Roman script mixed with crisp English tech terms (`Latency`, `Queue`, `Cache`, `Thread`) and ASCII numbers so Edge-TTS voices speak smoothly and subtitles stay 100% readable!"
            )
        elif "en-us-jenny" in v_low and "en-us-christopher" in v_low:
            lang_directive = (
                "LANGUAGE & DIALECT MANDATE (DUAL VOICE ENGLISH TECH DEBATE): "
                "Generate alternating `dialogue` turns (`female` builder challenging production edge-cases + `male` staff engineer countering with architecture proofs) in natural high-signal tech English."
            )
        else:
            lang_directive = (
                "LANGUAGE & DIALECT MANDATE (DUAL VOICE HINGLISH DEBATE): "
                "Write EVERY turn inside `dialogue` (`speaker: 'female'` and `speaker: 'male'`) AND `narration` in sharp, natural **Roman Hinglish** mixed with crisp English engineering nouns (`Database`, `Latency`, `Lock`, `Retry`, `Scale`) and ASCII numbers (`100K`, `24ms`). "
                "Do NOT use Devanagari letters or `Female:`/`Male:` prefixes, and keep all on-screen `visual_data` in crisp English!"
            )
    elif voice.endswith("|hinglish") or voice == "en-IN-NeerjaExpressiveNeural":
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: The user explicitly selected an Indian-accent Hinglish voice persona (`en-IN`). "
            "You MUST write the spoken `narration` in natural, punchy conversational Hinglish strictly using LATIN / ROMAN letters mixed with English tech terms "
            "(e.g., 'Socho zara... aapke paas 1 million records hain, bina index ke query freeze ho jaati hai!'). "
            "Do NOT use Devanagari characters for this voice so pronunciation stays 100% fluent. Keep all on-screen visual_data in crisp English!"
        )
    elif voice.startswith("hi-") or voice.endswith("|hi"):
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: The user explicitly selected a Hindi / Hinglish voice persona. "
            "You MUST write the spoken `narration` in natural, conversational Hindi-English using Devanagari for Hindi grammar words "
            "mixed seamlessly with crisp English technical terms (e.g., 'आज हम समझेंगे कि Database Migration Zero Downtime के साथ कैसे काम करता है...'). "
            "ALSO include `\"narration_hinglish\"` on every scene with the exact natural Roman Hinglish version of `narration` (e.g., 'Aaj hum samjhenge ki Database Migration Zero Downtime ke saath kaise kaam karta hai...') for karaoke captions! "
            "Keep all on-screen visual_data (titles, labels, code, queries, badges) in crisp English!"
        )
    elif voice.startswith("mr-") or voice.endswith("|mr"):
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: The user explicitly selected a Marathi voice persona. "
            "You MUST write the spoken `narration` in natural conversational Marathi using Devanagari for Marathi grammar words "
            "mixed seamlessly with crisp English technical nouns (e.g., 'मित्रांनो, आज आपण पाहणार आहोत की Database Migration Zero Downtime सह कसे चालते...'). "
            "ALSO include `\"narration_hinglish\"` on every scene with the exact natural Roman Minglish/Hinglish version of `narration` (e.g., 'Mitrano, aaj aapan pahnar aahot ki Database Migration Zero Downtime sobat kase chalte...') for karaoke captions! "
            "Keep all on-screen visual_data (titles, labels, code, queries, badges) in crisp English!"
        )
    elif voice == "en-IN-PrabhatNeural":
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: Write in crisp, authoritative Indian Tech English with high technical clarity."
        )
    else:
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: Write in natural, high-octane 2026 conversational tech English (Fireship / ByteByteGo / Theo style)."
        )

    # 2. Duration & Depth guidance (NO Scene Count Caps — AI chooses scenes freely in ALL modes)
    duration_instructions = {
        "auto": (
            "TRUE TOPIC-ADAPTIVE DEPTH & SCENE COUNT (ZERO SCENE LIMIT — AI DECIDES FREELY): "
            "Choose whatever scene count and duration fit the topic complexity naturally (whether 3 crisp scenes, 7 architectural stages, or 12+ deep technical scenes — ZERO upper/lower scene cap, never pad or compress artificially)."
        ),
        "short": "Target Pacing: Quick Explainer (~30-45 sec runtime target). NO fixed scene cap — AI decides the ideal number of tight rapid scenes naturally without fluff.",
        "standard": "Target Pacing: Standard Explainer (~60-90 sec runtime target). NO fixed scene cap — AI autonomously decides exact scene count based on topic layers & clarity.",
        "deep_dive": "Target Pacing: Comprehensive Deep-Dive (~90-240+ sec runtime target). NO fixed scene cap — generate as many sequential scenes as needed to thoroughly cover every pipeline stage, internal buffer, code/SQL trace, failure mode, and recovery path."
    }
    dur_guidance = duration_instructions.get(duration_mode, duration_instructions["auto"])

    # 3. Format, Audience Depth, Hook Formula, Ending CTA & Universal Spoken English Rules
    format_directive = f"Target Aspect Ratio: '{format_ratio}'."
    tone_directive = get_tone_directive(tone)

    _aud_map = {
        "beginner_interview": "TARGET AUDIENCE LEVEL: Beginner / Interview Prep — explain with intuitive everyday analogies, zero unexplained jargon, and highlight classic interview pitfalls.",
        "working_dev": "TARGET AUDIENCE LEVEL: Working Software / Data Engineer — focus on real production bugs, concrete SQL/code snippets, benchmarks, and practical architecture patterns.",
        "staff_architect": "TARGET AUDIENCE LEVEL: Staff / Principal Systems Architect — focus on distributed invariants, P99 tail latency, consensus/quorum, failover RPO/RTO, and cost trade-offs.",
    }
    _hook_map = {
        "ai_auto": "",
        "contrarian_stop": "OPENING 2-SECOND HOOK FORMULA: Open Scene 1 immediately with a sharp contrarian truth ('Stop doing X at scale — here is why it breaks').",
        "outage_3am": "OPENING 2-SECOND HOOK FORMULA: Open Scene 1 as a high-stakes 3AM production incident cold open ('Friday 11:45 PM — one config change dropped production latency by 10x').",
        "interview_question": "OPENING 2-SECOND HOOK FORMULA: Open Scene 1 as a direct top-tier engineering interview challenge ('Asked at Google/Uber: Why does naive X fail under burst load?').",
        "shocking_stat": "OPENING 2-SECOND HOOK FORMULA: Open Scene 1 with a concrete eye-opening engineering metric/threshold ('90% teams waste 4x budget by skipping partition pruning').",
    }
    clean_kw = re.sub(r"[^A-Za-z0-9_-]", "", str(cta_keyword or "").strip()).upper()[:18] or "NOTES"
    _cta_map = {
        "save_share": "CLOSING CTA MANDATE: End final scene cleanly inviting builders to save/share the architecture checklist.",
        "comment_keyword": f"CLOSING CTA MANDATE (GROWTH TRIGGER): End final scene explicitly telling viewers: 'Comment {clean_kw} below for full architecture notes and code' AND set final scene `footer_cta` to `Comment {clean_kw} for Notes & Code`.",
        "debate_poll": "CLOSING CTA MANDATE: End final scene with a crisp A-vs-B engineering poll question inviting comments on their production stack choice.",
        "clean_zero_cta": "CLOSING CTA MANDATE: End crisply with the core engineering takeaway ONLY — ZERO social-media 'like/follow/comment/save' filler.",
    }
    creator_controls_directive = "\n".join(
        line for line in (
            _aud_map.get(str(audience_level or "working_dev").lower().strip(), ""),
            _hook_map.get(str(hook_style or "ai_auto").lower().strip(), ""),
            _cta_map.get(str(cta_style or "save_share").lower().strip(), ""),
        ) if line
    )
    english_tech_num_rule = (
        "UNIVERSAL SPOKEN ENGLISH NUMBERS, DATES & TECH TERMS MANDATE (APPLIES TO ALL VOICES): "
        "In EVERY scene's `narration`, ALL numbers, counts, percentages, latencies, capacities, versions, dates, months, years, days, time durations, and technical words "
        "MUST be written in clean English ASCII (e.g., `100`, `1,000`, `10 million`, `50%`, `24ms`, `January 2026`, `25 November`, `5 minutes`, `10 seconds`, `Zero Downtime`, `Database`, `Cache`, `Thread`, `Interview`, `Trade-off`). "
        "NEVER use Devanagari digits (`०-९`), NEVER write Hindi/Marathi number or unit words (`एक`, `दो`, `तीन`, `पांच`, `दस`, `सौ`, `हज़ार`, `लाख`, `करोड़`, `lakhon`, `hazaaron`, `दोन`, `पाच`, `दहा`, `शंभर`, `कोटी`, `प्रतिशत`, `टक्के`, `मिनट`, `सेकंड`, `तास` — prefer English `thousands of`, `millions of`, `1M`, `100K`), "
        "NEVER write Hindi/Marathi month names (`जनवरी`, `नोव्हेंबर`), and NEVER transliterate English technical words into Devanagari (`डेटाबेस`, `थ्रेड`, `कैश`, `सर्व्हर`, `झिरो`, `डाउनटाइम`, `इंटरव्यू`, `लेटेंसी`). "
        "Keep English terms natural and conversational like authentic Hinglish / spoken tech speech."
    )

    variety_directive = ""
    if engine_style in _DIVERSE_ENGINES:
        avoid_arts = hist.get("recent_art_styles") or []
        avoid_vtypes = hist.get("recent_visual_types") or []
        avoid_bds = hist.get("recent_backdrops") or []
        from core.palette_engine import STUDIO_WORLDS
        fresh_worlds = [w for w in STUDIO_WORLDS.keys() if w not in avoid_arts[-10:]] or list(STUDIO_WORLDS.keys())
        suggested_world = fresh_worlds[(run_num * 3 + abs(hash(topic.strip().lower()))) % len(fresh_worlds)]
        from core.semantic_router import retrieve_prompt_candidates
        sem_cands = retrieve_prompt_candidates(topic, avoid_vtypes=avoid_vtypes[-14:], run_num=run_num, limit_studio=22, limit_opt1=10)
        fresh_layout_picks = sem_cands["studio"]
        fresh_opt1_picks = sem_cands["opt1"]
        web_paradigms = [
            "Asymmetric Bento Grid + Flowing SVG Bezier Comets",
            "3D Isometric Floating Orbit + Glowing Radar Waves",
            "Split Interactive Code Terminal + Live Bar Telemetry",
            "Neon Blueprint Schematic + Concentric Layer Stack",
            "Kinetic Timeline Stepper + Dual Matrix Quadrant",
            "Particle Physics Network Hub + Live Memory Offsets",
        ]
        chosen_paradigm = web_paradigms[run_num % len(web_paradigms)]
        variety_directive = (
            f"\nFRESH VISUAL VARIATION & DYNAMIC CATALOG SELECTION MANDATE (Generation Run #{run_num} — ZERO REPETITION):\n"
            f"- The user clicked Generate again and expects a COMPLETELY DIFFERENT visual composition, layout geometry, palette, and motion feel from prior videos.\n"
            f"- Use fresh `art_style`: `\"{suggested_world}\"` (AVOID repeating recent styles: {avoid_arts[-8:]}).\n"
            + (
                f"- SELECT a distinct `visual_type` PER SCENE matched to what that scene teaches (AVOID generic `custom_scene` or repeating recent types {avoid_vtypes[-12:]}).\n"
                f"- Top semantically-matched Studio layouts from the 1,011-layout library for '{topic}': {fresh_layout_picks}.\n"
                f"- For closing / interactive showcase scenes, set `visual_type: \"web_scene\"` AND choose `visual_data.option1_archetype` from these topic-matched Option 1 3D/SVG engines: {fresh_opt1_picks}.\n"
                f"- When you choose valid distinct catalog IDs, the Validator preserves your exact scene routing directly!\n"
                if engine_style in ("omni_smart_director", "studio_domain_library", "studio_300_domain", "multi_topology_mix", "interactive_storyboard")
                else f"- Design bespoke `web_scene` compositions inspired by `{chosen_paradigm}` (or choose `option1_archetype` from {fresh_opt1_picks}) and avoid recent intents {avoid_vtypes[-8:]}.\n"
            )
            + f"- AVOID repeating recent backdrops {avoid_bds[-6:]}; pick distinct `backdrop`, `transition`, and `text_fx` per scene.\n"
        )

    user_prompt = (
        f"Topic: '{topic}'.\n"
        f"{tone_directive}\n"
        f"{creator_controls_directive}\n"
        f"Selected Visual Engine: '{engine_style}'.\n"
        f"Selected Voice Persona: '{voice}'.\n"
        f"{lang_directive}\n"
        f"{english_tech_num_rule}\n"
        f"{format_directive}\n"
        f"Target Depth / Duration: {dur_guidance}\n"
        f"{style_directive}\n"
        f"{variety_directive}\n"
        f"MANDATORY REQUIREMENT: For EVERY scene, make sure the visual_data fields (node labels, schemas, table rows, code snippet, bullet points, metrics) "
        f"EXACTLY match and illustrate what the narrator is speaking cleanly (NEVER cut Hinglish sentences in half — use concise English tech nouns on cards!). "
        f"You may also optionally include `actions` ([{{'verb': 'travel_token|wire_handshake|construct_assemble|spotlight_sequence|disrupt_shake|filter_gate|fanout_split|inspect_zoom|state_flip|buffer_fill_drain|cipher_scramble|slot_reorder', 'word': 'spoken_trigger_word', 'from_idx': 0, 'to_idx': 1, 'label': 'SHORT TAG'}}]), "
        f"`sub_visual_type` for >12s long scenes, or custom Layer-2 `visual_data.html` (`window.__setStudioProgress(p)`) for rare physics simulations.\n"
        f"Autonomously design the complete storyboard blueprint JSON now."
    )
    
    last_errors = []

    # 1. Primary: High-speed Gemini Models (v1beta for preview/latest aliases + JSON mode + transient retry)
    if GEMINI_API_KEY:
        try:
            import time
            from google import genai
            try:
                client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta", "timeout": 12000})
            except Exception:
                client = genai.Client(api_key=GEMINI_API_KEY)

            models_to_try = [
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemini-3.1-flash-lite-preview",
                "gemini-flash-lite-latest",
                "gemini-flash-latest",
                "gemini-3-flash-preview",
                "gemini-3.5-flash",
                "gemini-3.8-flash",
                "gemma-4-31b-it",
                "gemma-4-26b-a4b-it",
            ]

            consec_transient = 0
            for model_name in models_to_try:
                attempts = 2 if model_name == "gemini-3.5-flash-lite" else 1
                hit_transient = False
                for attempt in range(attempts):
                    try:
                        req_kwargs = {
                            "model": model_name,
                            "contents": f"{SYSTEM_PROMPT}\n\n{user_prompt}",
                        }
                        if not model_name.startswith("gemma-"):
                            req_kwargs["config"] = {"response_mime_type": "application/json"}
                        response = client.models.generate_content(**req_kwargs)
                        raw_text = response.text.strip() if getattr(response, "text", None) else ""
                        clean_json = _extract_json(raw_text)
                        if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                            clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num, cta_style=cta_style, cta_keyword=cta_keyword)
                            _save_visual_history(hist, clean_json, session_history=visual_history)
                            clean_json["meta_director"] = {
                                "model_used": model_name,
                                "engine_style": engine_style,
                                "custom_style_prompt": custom_style_prompt,
                                "duration_mode": duration_mode,
                                "topic": topic,
                                "voice": voice,
                                "format_ratio": format_ratio,
                                "variation_run": run_num,
                            }
                            return clean_json
                        last_errors.append(f"{model_name}: invalid/empty JSON ({len(raw_text)} chars)")
                        consec_transient = 0
                        break
                    except Exception as e:
                        err_str = str(e)
                        is_transient = ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str)
                        if attempt + 1 < attempts and is_transient:
                            time.sleep(0.8)
                            continue
                        print(f"[Director] Model {model_name} error: {err_str[:120]}")
                        last_errors.append(f"{model_name}: {err_str[:120]}")
                        hit_transient = is_transient
                        break
                if hit_transient:
                    consec_transient += 1
                    if consec_transient >= 3:
                        break
                else:
                    consec_transient = 0
        except Exception as e:
            last_errors.append(f"Gemini client error: {e}")

    # 2. Resilient Secondary Fallback: Groq Ultra-Fast LLM (high max_tokens so reasoning models never truncate)
    if GROQ_API_KEY:
        try:
            from groq import Groq
            g_client = Groq(api_key=GROQ_API_KEY)
            groq_candidates = [
                ("openai/gpt-oss-120b", False),
                ("openai/gpt-oss-120b", True),
                ("qwen/qwen3.8-27b", False),
                ("openai/gpt-oss-20b", False),
            ]
            for g_model, use_json_mode in groq_candidates:
                try:
                    req_kw = {
                        "model": g_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"{user_prompt}\nReturn ONLY valid JSON."}
                        ],
                        "temperature": 0.6,
                        "max_tokens": 8192,
                        "timeout": 18,
                    }
                    if use_json_mode:
                        req_kw["response_format"] = {"type": "json_object"}
                    g_res = g_client.chat.completions.create(**req_kw)
                    raw_text = (g_res.choices[0].message.content or "").strip() if g_res.choices else ""
                    clean_json = _extract_json(raw_text)
                    if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                        clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num, cta_style=cta_style, cta_keyword=cta_keyword)
                        _save_visual_history(hist, clean_json, session_history=visual_history)
                        clean_json["meta_director"] = {
                            "model_used": f"groq/{g_model}",
                            "engine_style": engine_style,
                            "custom_style_prompt": custom_style_prompt,
                            "duration_mode": duration_mode,
                            "topic": topic,
                            "voice": voice,
                            "format_ratio": format_ratio,
                            "variation_run": run_num,
                        }
                        return clean_json
                    last_errors.append(f"groq/{g_model}(json={use_json_mode}): empty/unparsed ({len(raw_text)} chars)")
                except Exception as e:
                    last_errors.append(f"groq/{g_model}(json={use_json_mode}): {str(e)[:120]}")
                    continue
        except Exception as e:
            last_errors.append(f"Groq client error: {e}")

    # 3. Third-Tier Fail-Safe: OpenRouter Free Tier Models (0 credits required)
    if OPENROUTER_API_KEY:
        try:
            import requests
            or_models = [
                "google/gemma-4-31b-it:free",
                "nvidia/nemotron-3-ultra-550b-a55b:free",
                "baidu/ernie-5.5-flash-preview:free",
                "nvidia/nemotron-3.5-lightning:free",
            ]
            for or_model in or_models:
                try:
                    r = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": or_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": f"{user_prompt}\nReturn ONLY valid JSON."}
                            ],
                            "temperature": 0.6,
                            "max_tokens": 6144,
                        },
                        timeout=30
                    )
                    if r.status_code == 200:
                        res_json = r.json()
                        msg = res_json["choices"][0]["message"]
                        raw_text = (msg.get("content") or msg.get("reasoning") or "").strip()
                        clean_json = _extract_json(raw_text)
                        if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                            clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num, cta_style=cta_style, cta_keyword=cta_keyword)
                            _save_visual_history(hist, clean_json, session_history=visual_history)
                            clean_json["meta_director"] = {
                                "model_used": f"openrouter/{or_model}",
                                "engine_style": engine_style,
                                "custom_style_prompt": custom_style_prompt,
                                "duration_mode": duration_mode,
                                "topic": topic,
                                "voice": voice,
                                "format_ratio": format_ratio,
                                "variation_run": run_num,
                            }
                            return clean_json
                        last_errors.append(f"openrouter/{or_model}: invalid JSON ({len(raw_text)} chars)")
                    else:
                        last_errors.append(f"openrouter/{or_model}: HTTP {r.status_code}")
                except Exception as e:
                    last_errors.append(f"openrouter/{or_model}: {str(e)[:120]}")
        except Exception as e:
            last_errors.append(f"OpenRouter client error: {e}")

    # 4. Tier-4 Emergency Deterministic Storyboard (prevents crash when all external LLM APIs hit 503 simultaneously)
    print(f"[Director] All external LLMs unavailable ({'; '.join(last_errors)[:240]}). Using deterministic storyboard composer...")
    fallback_tl = _build_emergency_fallback_timeline(
        topic=topic,
        tone=tone,
        engine_style=engine_style,
        duration_mode=duration_mode,
        voice=voice,
        format_ratio=format_ratio,
    )
    fallback_tl = _enforce_engine_style(fallback_tl, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num, cta_style=cta_style, cta_keyword=cta_keyword)
    _save_visual_history(hist, fallback_tl, session_history=visual_history)
    fallback_tl["meta_director"] = {
        "model_used": "emergency_deterministic_composer",
        "engine_style": engine_style,
        "custom_style_prompt": custom_style_prompt,
        "duration_mode": duration_mode,
        "topic": topic,
        "voice": voice,
        "format_ratio": format_ratio,
        "variation_run": run_num,
        "upstream_errors": last_errors[:6],
    }
    return fallback_tl

def _synthesize_bespoke_web_scenes(
    scenes: List[Dict[str, Any]],
    topic: str,
    format_ratio: str = "9:16",
    run_num: int = 1,
) -> None:
    """
    Parallel Zero-Template Code-as-Video Enricher (Option 1 + Both Combined):
    Asks Gemini/Groq to author bespoke interactive HTML5 + Canvas/SVG motion code for scenes
    marked `web_scene` that lack custom HTML. Rotates visual paradigms by `run_num` so
    every click produces a genuinely new layout composition.
    """
    from core.config import FORMAT_SPECS
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    w, h = spec.get("width", 1080), spec.get("height", 1920)
    sub_safe = 500 if h >= 1600 else 160

    targets: List[Tuple[int, Dict[str, Any]]] = []
    for idx, sc in enumerate(scenes):
        vd = sc.get("visual_data") or {}
        if str(sc.get("visual_type", "")).lower().strip() == "web_scene" and not vd.get("option1_archetype") and not str(vd.get("html") or vd.get("web_code") or "").strip():
            targets.append((idx, sc))
    if not targets:
        return
    if not (GEMINI_API_KEY or GROQ_API_KEY):
        return

    archetype_hints = [
        "Interactive Failure/Problem Alert Simulation (pulsing alert nodes, bottleneck counter, impact cards)",
        "Animated System Architecture Flow (connected service boxes, animated flowing SVG Bezier data packets, live labels)",
        "Low-level Memory/Buffer/Terminal Inspector OR Live Telemetry Stream (animated hex/log rows scanning live)",
        "Before-vs-After Benchmark Arena OR Switchover Timeline (animated bar chart, speedup badge, checklist cards)",
        "3D Isometric Floating Orbit Topology (concentric rings, rotating orbital satellites, live glowing edge pulses)",
        "Asymmetric Bento Metric & Code Grid (2x2 glowing stat tiles + live mini terminal trace + arrow connectors)",
    ]
    layout_flavors = [
        "Asymmetric Bento Grid with frosted glass cards and neon corner accents",
        "Vertical Orbital Node-Link Graph with glowing curved SVG Bezier packet trails",
        "Split Top-vs-Bottom Blueprint Schematic with animated CAD gridlines and metric callouts",
        "Floating 3D Isometric Layer Stack with progressive z-depth reveal cards",
        "Cyber Command Console with live scrolling event log + radial SVG arc meter",
        "Horizontal Milestone Stepper Rail with expanding detail drawers and live badges",
    ]

    def _gen_one(item: Tuple[int, Dict[str, Any]]) -> Tuple[int, str]:
        idx, sc = item
        vd = sc.get("visual_data") or {}
        narr = str(sc.get("narration") or "")
        hint = archetype_hints[(idx + run_num) % len(archetype_hints)]
        flavor = layout_flavors[(idx * 2 + run_num) % len(layout_flavors)]
        compact_vd = {k: v for k, v in vd.items() if k not in ("html", "web_code", "svg", "svg_code")}
        prompt = f"""Build ONE self-contained interactive HTML5 motion-graphic scene (`<!DOCTYPE html>...</html>`) for a {w}x{h} tech video frame.
Topic: {topic}
Variation Seed #{run_num} Visual Paradigm: {flavor}
Scene {idx + 1} Role ({sc.get('role', 'explain')}): {hint}
Spoken Narration: "{narr}"
Scene Data: {json.dumps(compact_vd, ensure_ascii=False)[:900]}

STRICT ENGINEERING & LAYOUT RULES:
1. Viewport MUST be exact {w}x{h}px (`overflow:hidden; margin:0; padding:112px 58px {sub_safe}px; box-sizing:border-box`).
2. TOP 100px is reserved for system HUD (do NOT draw header nav bars/watermarks there). BOTTOM {sub_safe}px MUST BE 100% EMPTY (no text boxes, no subtitles, no narration captions at bottom — ASS subtitles render there!).
3. Define `window.__setStudioProgress = function(p, curTime, energy) {{ ... }}` cleanly with ZERO errors for ANY `p` in `0.0..1.0`! Animate SVG paths (`stroke-dashoffset`), glowing packets, counters, cards, or 2D/3D Canvas shapes driven strictly by `p` (never `requestAnimationFrame` alone, because Chromium captures frames by calling `__setStudioProgress(p)`).
4. Zero CDN `<script src>` dependencies (pure inline HTML/CSS/SVG/Canvas JS only so offline rendering is 100% deterministic).
5. Visual text must strictly match THIS scene's topic/narration in crisp English — NEVER generic labels or filler. Make the visual layout distinctly reflect `{flavor}`.
Output ONLY the raw HTML starting with <!DOCTYPE html> and ending with </html>."""

        html_out = ""
        if GEMINI_API_KEY:
            try:
                from google import genai
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta", "timeout": 12000})
                except Exception:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]:
                    try:
                        res = client.models.generate_content(model=m, contents=prompt)
                        raw = str(getattr(res, "text", "") or "").strip()
                        m_html = re.search(r"(<!DOCTYPE html[\s\S]*?</html>|<html[\s\S]*?</html>)", raw, re.IGNORECASE)
                        if m_html:
                            cand = m_html.group(1)
                            if "__setStudioProgress" in cand and ("<svg" in cand.lower() or "<canvas" in cand.lower()):
                                html_out = cand
                                break
                    except Exception:
                        continue
            except Exception:
                pass
        if not html_out and GROQ_API_KEY:
            try:
                from groq import Groq
                gc = Groq(api_key=GROQ_API_KEY)
                res = gc.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,
                    timeout=12,
                )
                raw = res.choices[0].message.content.strip() if res.choices else ""
                m_html = re.search(r"(<!DOCTYPE html[\s\S]*?</html>|<html[\s\S]*?</html>)", raw, re.IGNORECASE)
                if m_html and "__setStudioProgress" in m_html.group(1):
                    html_out = m_html.group(1)
            except Exception:
                pass
        return idx, html_out

    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        pool = ThreadPoolExecutor(max_workers=min(4, len(targets)))
        try:
            futs = [pool.submit(_gen_one, t) for t in targets[:6]]
            for fut in as_completed(futs, timeout=20):
                try:
                    idx, h_code = fut.result(timeout=1)
                    if h_code:
                        scenes[idx].setdefault("visual_data", {})["html"] = h_code
                except Exception:
                    continue
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
    except Exception:
        pass


def _split_narration_clauses(narration: str, target_count: int = 4) -> List[str]:
    """Splits a narration string cleanly into sequential spoken clauses for progressive visuals."""
    raw = str(narration or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[.!?\n;]+|\s+[—-]\s+|,\s+(?=[A-Za-z0-9])", raw) if len(p.strip()) > 6]
    if len(parts) < target_count:
        words = raw.split()
        if len(words) >= target_count * 3:
            step = max(3, len(words) // target_count)
            parts = [" ".join(words[i:i + step]).strip(" ,.;:-") for i in range(0, len(words), step)][:5]
    return [p for p in parts if len(p) > 4][:5]


def _mirror_items_for_domain_layout(v_data: Dict[str, Any], sc: Dict[str, Any], title: str) -> None:
    """Ensures any rotated 320+ Domain / Grammar layout has 4-5 rich progressive stages grounded in narration."""
    existing = v_data.get("items") or v_data.get("nodes") or v_data.get("steps") or v_data.get("stages")
    clauses = _split_narration_clauses(sc.get("narration", ""), target_count=5)
    if isinstance(existing, list) and len(existing) >= 4:
        for idx, it in enumerate(existing[:5]):
            if isinstance(it, dict) and not it.get("sub") and idx < len(clauses):
                it["sub"] = clauses[idx][:64]
        return

    mirrored: List[Dict[str, Any]] = []
    if isinstance(existing, list):
        for it in existing:
            if isinstance(it, dict):
                mirrored.append(dict(it))
            elif isinstance(it, str) and it.strip():
                mirrored.append({"name": it.strip(), "sub": ""})

    if not mirrored:
        if v_data.get("satellites"):
            for s in v_data["satellites"][:5]:
                mirrored.append({"name": s.get("name", ""), "sub": s.get("role", ""), "color": s.get("color", "")})
        elif v_data.get("left_points") or v_data.get("right_points"):
            lp = v_data.get("left_points") or []
            rp = v_data.get("right_points") or []
            for pt in lp[:2]:
                mirrored.append({"name": str(pt), "sub": str(v_data.get("left_label") or "Legacy"), "color": "#F43F5E"})
            for pt in rp[:3]:
                mirrored.append({"name": str(pt), "sub": str(v_data.get("right_label") or "Modern"), "color": "#34D399"})
        elif v_data.get("bars"):
            for b in v_data["bars"][:5]:
                mirrored.append({"name": f"{b.get('label', '')}: {b.get('display', b.get('value', ''))}", "sub": "Benchmark", "color": b.get("color", "")})
        elif v_data.get("entries"):
            for e in v_data["entries"][:5]:
                mirrored.append({"name": f"{e.get('op', '')} ({e.get('address', '')})", "sub": f"{e.get('table', '')} • {e.get('status', '')}"})
        elif v_data.get("bullets"):
            for b in v_data["bullets"][:5]:
                mirrored.append({"name": str(b), "sub": ""})
        elif v_data.get("blocks"):
            for blk in v_data["blocks"]:
                if not isinstance(blk, dict):
                    continue
                for it in (blk.get("items") or blk.get("nodes") or []):
                    if isinstance(it, dict):
                        mirrored.append({"name": str(it.get("title") or it.get("name") or ""), "sub": str(it.get("desc") or it.get("sub") or "")})
                    elif isinstance(it, str):
                        mirrored.append({"name": it, "sub": ""})
                if blk.get("text") and len(mirrored) < 5:
                    mirrored.append({"name": str(blk["text"])[:48], "sub": str(blk.get("eyebrow") or "")})

    # Top-up to 4-5 sequential stages from narration clauses so components enter progressively with the voice
    c_idx = 0
    while len(mirrored) < 4 and c_idx < len(clauses):
        cl = clauses[c_idx]
        c_idx += 1
        words = cl.split()
        head = " ".join(words[:5]).strip(" ,.;:-")
        if any(head.lower() in str(m.get("name", "")).lower() for m in mirrored):
            continue
        mirrored.append({"name": head[:40], "sub": cl[:68]})

    if not mirrored:
        mirrored = [{"name": s[:42], "sub": title[:28]} for s in clauses] or [{"name": title[:40], "sub": "Architecture"}]

    for idx, m in enumerate(mirrored[:5]):
        if not m.get("sub") and idx < len(clauses):
            m["sub"] = clauses[idx][:68]
        if idx + 1 < len(mirrored) and not m.get("edge"):
            m["edge"] = ["Ingest", "Process", "Route", "Verify"][idx % 4]

    v_data["items"] = mirrored[:5]
    if not v_data.get("footer") and clauses:
        v_data["footer"] = clauses[-1][:64]


def _extract_voice_facts(narration: str, topic: str, title: str, dialogue: Any = None) -> Dict[str, Any]:
    """
    Zero-Hardcode Voice-Text Hydrator:
    Extracts actual spoken SQL queries/columns/tables, CLI commands, technical entity names,
    and numeric latencies/speedups directly from the scene's narration & dialogue so every visual
    widget renders content spoken in THAT scene instead of generic dummy placeholders.
    """
    text = str(narration or "").strip()
    if not text and isinstance(dialogue, list):
        text = " ".join(str(d.get("text") or "") for d in dialogue if isinstance(d, dict))
    clauses = _split_narration_clauses(text, target_count=6)

    # 1. Extract technical multi-word/single concepts mentioned in spoken voice
    _SKIP_W = {
        "yaar", "honestly", "relax", "main", "samajhta", "hoon", "yeh", "aur", "par", "mein",
        "hain", "hai", "karta", "karte", "karti", "kaise", "kyun", "kya", "hota", "hoti",
        "jaati", "jaate", "aao", "chalo", "dekhte", "samajhte", "lagao", "karo", "rakho",
        "simple", "bahut", "smart", "wait", "achha", "waah", "poora", "bas", "abhi", "liye",
        "bina", "toh", "bhi", "se", "ko", "ka", "ki", "ke", "ek", "sabse", "zaroori", "zaroor",
        "isko", "hum", "aap", "tum", "mera", "tera", "matlab", "matlabi", "aate", "hi", "jabki",
        "terminal", "sql", "query", "select", "from", "over", "where", "window", "function",
    }
    tech_phrases: List[str] = []
    # Match multi-word Title/UPPER phrases or snake_case / hyphenated / dot identifiers
    for m in re.finditer(r"\b(?:[A-Z][A-Za-z0-9_+.-]*(?:\s+[A-Z0-9][A-Za-z0-9_+.-]*){0,2}|[a-z]+_[a-z0-9_]+)\b", text):
        ph = m.group(0).strip(" .,:;?!-")
        if not ph or len(ph) < 3:
            continue
        low_tokens = [w.lower() for w in ph.split()]
        if all(t in _SKIP_W for t in low_tokens):
            continue
        if low_tokens[0] in _SKIP_W and len(low_tokens) > 1:
            ph = " ".join(ph.split()[1:])
        if ph and ph.lower() not in [x.lower() for x in tech_phrases]:
            tech_phrases.append(ph[:28])

    # Top up with crisp clause heads if fewer than 6 phrases
    for c_i, cl in enumerate(clauses):
        if len(tech_phrases) >= 6:
            break
        cleaned_words = [re.sub(r"[^A-Za-z0-9_+\-()/]", "", w) for w in cl.split()]
        kept = [w for w in cleaned_words if w and w.lower() not in _SKIP_W]
        cand = " ".join(kept[:3]).strip(" .,:;-")
        if len(cand) >= 4 and cand.lower() not in [x.lower() for x in tech_phrases]:
            tech_phrases.append(cand[:28])

    # 2. Extract numeric metrics + units from voice text (e.g. 920ms, 2ms, 15x, 100K RPS, 24ms, 4s)
    metrics: List[Tuple[str, float, str]] = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(ms|s|sec|msec|rps|k\s*rps|x|%|gb|mb|k|m)?\b", text, flags=re.IGNORECASE):
        num_s = m.group(1)
        unit_s = (m.group(2) or "").strip()
        if not unit_s and len(num_s) < 3:
            continue
        try:
            val = float(num_s)
        except Exception:
            continue
        # Normalize seconds vs ms for meaningful bar comparison when unit is s
        norm_val = val * 1000.0 if unit_s.lower() in ("s", "sec") else val
        ctx_win = text[max(0, m.start() - 32):m.start()].strip()
        lbl_words = [re.sub(r"[^A-Za-z0-9_-]", "", w) for w in ctx_win.split() if w.lower() not in _SKIP_W]
        lbl = " ".join(lbl_words[-2:]).strip() or f"Metric {len(metrics) + 1}"
        metrics.append((lbl[:22], norm_val, f"{num_s}{unit_s}"))

    # 3. Extract SQL query / columns / table directly from spoken text
    sql_m = re.search(r"SELECT\s+(.+?)(?:\s+FROM\s+([A-Za-z0-9_]+))?(?:\s+WHERE\b|\s+ORDER\b|\s+GROUP\b|\s+query|\s+window|$)", text, flags=re.IGNORECASE)
    sql_query = ""
    sql_cols: List[str] = []
    sql_rows: List[List[str]] = []
    if sql_m:
        raw_sel = sql_m.group(1).strip(" ,.;")
        raw_tbl = (sql_m.group(2) or "").strip(" ,.;") or re.sub(r"[^a-z0-9_]", "_", topic.lower())[:18].strip("_") or "events"
        raw_sel_parts = [re.sub(r"[^A-Za-z0-9_*()_ ]", "", p).strip() for p in raw_sel.split(",") if p.strip()]
        # Clean trailing Hinglish words after OVER / table name
        clean_cols: List[str] = []
        for p in raw_sel_parts:
            toks = [t for t in p.split() if t.lower() not in ("over", "window", "function", "lagao", "aur", "se", "mein")]
            if toks:
                clean_cols.append(toks[0].lower()[:14])
        if clean_cols:
            sql_cols = (clean_cols + ["rank" if "rank" not in clean_cols else "p99_ms"])[:4]
            sql_query = f"SELECT {', '.join(clean_cols[:3])}" + (" , DENSE_RANK() OVER (...)" if "dense_rank" in text.lower() or "rank" in text.lower() else "") + f"\nFROM {raw_tbl} LIMIT 5;"
            seed_noun = (tech_phrases[0] if tech_phrases else topic[:12]).split()[0][:10]
            for ri in range(4):
                row_vals = []
                for ci, cname in enumerate(sql_cols):
                    if "id" in cname or "tenant" in cname or "user" in cname:
                        row_vals.append(f"{seed_noun.lower()}_{101 + ri}")
                    elif "rank" in cname or cname == "rk":
                        row_vals.append(str(ri + 1))
                    elif "count" in cname or "amt" in cname or "metric" in cname or "rps" in cname:
                        row_vals.append(f"{(4 - ri) * 24 + 12}k")
                    else:
                        row_vals.append(f"{max(2, (ri + 1) * 6)}ms")
                sql_rows.append(row_vals)

    # 4. Extract spoken CLI command / function identifiers (strip Hinglish connector tokens)
    cli_m = re.search(r"((?:kubectl|python(?:\s+-m)?|docker|curl|redis-cli)\s+[A-Za-z0-9_./:-]+(?:\s+[A-Za-z0-9_./:-]+)?)", text, flags=re.IGNORECASE)
    fn_m = re.search(r"(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.IGNORECASE)
    spoken_cmd = ""
    if cli_m:
        cmd_toks = cli_m.group(1).strip().split()
        while len(cmd_toks) > 2 and cmd_toks[-1].lower() in _SKIP_W:
            cmd_toks.pop()
        spoken_cmd = " ".join(cmd_toks)
    spoken_fn = fn_m.group(1).strip() if fn_m else ""

    return {
        "phrases": tech_phrases,
        "clauses": clauses,
        "metrics": metrics,
        "sql_query": sql_query,
        "sql_cols": sql_cols,
        "sql_rows": sql_rows,
        "command": spoken_cmd,
        "fn_name": spoken_fn,
    }


def _route_omni_best_scene(
    sc: Dict[str, Any],
    idx: int,
    total_scenes: int,
    topic: str,
    tone: str,
    run_num: int,
    used_vtypes: set,
    recent_vtypes: set,
    v_data: Dict[str, Any],
    used_geometries: Optional[set] = None,
) -> Tuple[str, str]:
    """Delegates to the zero-hardcode Full-Catalog Dynamic Semantic Router across all 1,179 engines."""
    from core.semantic_router import select_semantic_scene_layout
    return select_semantic_scene_layout(
        sc=sc,
        idx=idx,
        total_scenes=total_scenes,
        topic=topic,
        tone=tone,
        run_num=run_num,
        used_vtypes=used_vtypes,
        recent_vtypes=recent_vtypes,
        v_data=v_data,
        used_geometries=used_geometries,
    )


def _extract_crisp_beat_label(clause: str, fallback_idx: int) -> str:
    """Extracts a sharp, readable English/tech milestone title without trailing or broken Hinglish grammar scraps."""
    _STOP = {
        "par", "aur", "karke", "mein", "hai", "hain", "ko", "ki", "ka", "ke", "se", "toh", "bhi",
        "yeh", "woh", "jab", "tab", "ab", "bas", "bahut", "achha", "waah", "yaar", "honestly",
        "relax", "simple", "ek", "do", "charo", "lagao", "karo", "deti", "dete", "hota", "hoti",
        "nahi", "karta", "karti", "karte", "hote", "rahte", "rahta", "jaati", "jaata", "lekin",
        "jabki", "dono", "liya", "liye", "wala", "wali", "wale", "isse", "uske", "isme", "apne",
        "yahan", "wahan", "tarah", "sath", "saath", "the", "and", "for", "with", "from", "that", "this",
    }
    words = [re.sub(r"[^A-Za-z0-9_+.\-()/]", "", w) for w in str(clause or "").split()]
    kept = [w for w in words if w and len(w) >= 2 and w.lower() not in _STOP]
    pick = kept[:3] if kept else [w for w in words if len(w) >= 2][:3]
    lbl = " ".join(pick).strip(" .,:;-")
    if len(lbl) < 3:
        return f"Stage {fallback_idx + 1}"
    return lbl[:28]


def _enforce_engine_style(
    timeline: Dict[str, Any],
    engine_style: str,
    topic: str,
    tone: str = DEFAULT_TONE_KEY,
    format_ratio: str = "9:16",
    visual_history: Optional[Dict[str, Any]] = None,
    run_num: int = 1,
    cta_style: str = "save_share",
    cta_keyword: str = "",
) -> Dict[str, Any]:
    """
    Guarantees that every scene in the timeline strictly adheres to the user-selected Visual Engine & Style,
    adapting visual_type, scene_tone, backdrop/transition variety, and rotating away from prior runs'
    visuals when history is maintained (Option 1, Option 2, and Both Combined).
    """
    if not timeline or "scenes" not in timeline:
        return timeline

    scenes = timeline.get("scenes", [])
    
    # Engine to target visual_type mapping
    engine_type_map = {
        "all_in_one_tech_canvas": "all_in_one_tech_canvas",
        "terminal_screencast": "code_terminal",
        "sql_deepdive": "sql_table",
        "bytebytego_dsl": "architecture_flow",
        "split_comparison": "split_comparison",
        "benchmark_speed": "benchmark_chart",
        "memory_internals": "data_structure_memory",
        "network_mesh": "circular_hub_mesh",
        "telemetry_hud": "metric_gauge_hud",
        "alert_troubleshoot": "alert_diagram",
        "concept_keynote": "concept_cards"
    }

    target_type = engine_type_map.get(engine_style)

    vtype_aliases = {
        "service_topology": "architecture_flow",
        "topology": "architecture_flow",
        "pipeline": "architecture_flow",
        "pipeline_flow": "architecture_flow",
        "data_flow": "architecture_flow",
        "memory_buffer": "data_structure_memory",
        "memory_internals": "data_structure_memory",
        "wal_log": "data_structure_memory",
        "buffer": "data_structure_memory",
        "terminal": "code_terminal",
        "cli": "code_terminal",
        "code": "code_terminal",
        "comparison": "split_comparison",
        "trade_off": "split_comparison",
        "chart": "benchmark_chart",
        "benchmark": "benchmark_chart",
        "mesh": "circular_hub_mesh",
        "hub_spoke": "circular_hub_mesh",
        "gauge": "metric_gauge_hud",
        "metrics": "metric_gauge_hud",
        "kpi": "metric_gauge_hud",
        "alert": "alert_diagram",
        "incident": "alert_diagram",
        "bottleneck": "alert_diagram",
        "sql": "sql_table",
        "question_hook": "hero_hook",
        "hook_card": "hero_hook",
        "interview_hook": "hero_hook",
        "hero": "hero_hook",
        "merge_diagram": "hybrid_merge",
        "combination_diagram": "hybrid_merge",
        "hybrid_architecture": "hybrid_merge",
        "hybrid_approach": "hybrid_merge",
        "kinetic": "kinetic_statement",
        "statement": "kinetic_statement",
        "callout": "kinetic_statement",
        "timeline": "step_timeline",
        "steps": "step_timeline",
        "step_flow": "step_timeline",
        "custom": "custom_scene",
        "storyboard": "custom_scene",
        "composable": "custom_scene",
        "custom_canvas": "custom_scene",
    }

    # Pick a fresh visual art_style, avoiding prior runs in diverse engines
    hist = visual_history or {}
    recent_arts = set((hist.get("recent_art_styles") or [])[-24:])
    recent_vtypes = set((hist.get("recent_visual_types") or [])[-72:])
    recent_bds = set((hist.get("recent_backdrops") or [])[-10:])
    recent_trs = set((hist.get("recent_transitions") or [])[-8:])
    recent_tfxs = set((hist.get("recent_text_fx") or [])[-8:])
    is_diverse_engine = engine_style in (
        "omni_smart_director", "studio_domain_library", "pure_zero_template", "studio_300_domain",
        "multi_topology_mix", "interactive_storyboard",
        "data_streaming_pipelines", "distributed_consensus_labs", "ai_rag_agents_studio",
        "dual_generative", "cinematic_studio", "auto_dynamic", "hybrid_modern",
    )

    art_styles = ["light_whiteboard", "editorial_dark", "blueprint_grid", "neon_fireship"]
    raw_art = str(timeline.get("art_style") or "").strip()
    _STUDIO_SET = (
        "omni_smart_director", "studio_300_domain", "pure_zero_template", "studio_domain_library",
        "multi_topology_mix", "interactive_storyboard",
        "data_streaming_pipelines", "distributed_consensus_labs", "ai_rag_agents_studio",
        "cinematic_studio", "dual_generative", "auto_dynamic", "hybrid_modern",
    )
    if engine_style in _STUDIO_SET:
        from core.palette_engine import STUDIO_WORLDS
        studio_pool = list(STUDIO_WORLDS.keys())
        if is_diverse_engine and (not raw_art or raw_art.lower() in recent_arts or raw_art.lower() not in STUDIO_WORLDS):
            fresh_pool = [w for w in studio_pool if w not in recent_arts] or studio_pool
            topic_art_style = fresh_pool[(run_num * 5 + abs(hash(topic.strip().lower()))) % len(fresh_pool)]
        elif raw_art and (raw_art.lower() in STUDIO_WORLDS or raw_art.lower() in art_styles or raw_art.startswith("#") or raw_art.lower().startswith("hue:") or raw_art.lower() in ("dynamic_hsl", "procedural", "hsl")):
            topic_art_style = raw_art
        else:
            topic_art_style = studio_pool[(run_num * 3 + abs(hash(topic.strip().lower()))) % len(studio_pool)]
    else:
        if not raw_art or raw_art not in art_styles or raw_art in recent_arts:
            fresh_std = [a for a in art_styles if a not in recent_arts] or art_styles
            topic_art_style = fresh_std[(run_num + abs(hash(topic.strip().lower()))) % len(fresh_std)]
        else:
            topic_art_style = raw_art
    timeline["art_style"] = topic_art_style

    if engine_style in _STUDIO_SET:
        from core.mesh_shader_engine import ALL_BACKDROPS
        from core.layouts_pro import ALL_TRANSITIONS, ALL_TEXT_FX
    else:
        ALL_BACKDROPS, ALL_TRANSITIONS, ALL_TEXT_FX = (), (), ()

    used_vtypes: set = set()
    used_bds_local: set = set()
    used_geoms_local: set = set()
    # Omni Smart Director: Curated Multi-World Cinema Cadence (contrasting dark/light worlds across scenes unless single-world forced)
    _OMNI_WORLD_CADENCE = (
        "obsidian_studio", "sapphire_3d", "slate_ivory", "midnight_gold", "emerald_matrix", "aurora_borealis"
    )
    multi_world_omni = (engine_style == "omni_smart_director") and bool(timeline.get("multi_world", True))
    for idx, sc in enumerate(scenes):
        eff_scene_tone = resolve_effective_tone(tone, scene_tone=sc.get("scene_tone"), role=sc.get("role"), idx=idx)
        sc["scene_tone"] = eff_scene_tone
        t_prof = get_tone_profile(eff_scene_tone)
        sc["sfx_cue"] = str(t_prof.get("default_sfx") or "whoosh")

        v_data = sc.get("visual_data", {})
        if multi_world_omni:
            sc_world = _OMNI_WORLD_CADENCE[(idx + run_num) % len(_OMNI_WORLD_CADENCE)]
            sc["art_style"] = sc_world
            v_data["art_style"] = sc_world
        else:
            v_data["art_style"] = topic_art_style
        if engine_style in _STUDIO_SET and ALL_BACKDROPS:
            cur_bd = str(v_data.get("backdrop") or sc.get("backdrop") or "").lower().strip()
            if is_diverse_engine and (not cur_bd or cur_bd in recent_bds or cur_bd in used_bds_local):
                bd_pool = [b for b in ALL_BACKDROPS if b not in recent_bds and b not in used_bds_local] or list(ALL_BACKDROPS)
                bd = bd_pool[(idx * 3 + run_num * 5 + abs(hash(topic))) % len(bd_pool)]
            elif cur_bd in ALL_BACKDROPS:
                bd = cur_bd
            else:
                bd = ALL_BACKDROPS[(idx * 3 + run_num * 5 + abs(hash(topic))) % len(ALL_BACKDROPS)]
            sc["backdrop"] = bd
            v_data["backdrop"] = bd
            used_bds_local.add(bd)

            cur_tr = str(v_data.get("transition") or sc.get("transition") or "").lower().strip()
            if is_diverse_engine and (not cur_tr or cur_tr in recent_trs):
                tr_pool = [t for t in ALL_TRANSITIONS if t not in recent_trs] or list(ALL_TRANSITIONS)
                tr = tr_pool[(idx * 2 + run_num * 3) % len(tr_pool)]
            elif cur_tr in ALL_TRANSITIONS:
                tr = cur_tr
            else:
                tr = ALL_TRANSITIONS[(idx * 2 + 1 + run_num) % len(ALL_TRANSITIONS)]
            sc["transition"] = tr
            v_data["transition"] = tr

            cur_tfx = str(v_data.get("text_fx") or sc.get("text_fx") or "").lower().strip()
            if is_diverse_engine and (not cur_tfx or cur_tfx in recent_tfxs):
                tfx_pool = [t for t in ALL_TEXT_FX if t not in recent_tfxs] or list(ALL_TEXT_FX)
                tfx = tfx_pool[(idx * 3 + run_num * 2) % len(tfx_pool)]
            elif cur_tfx in ALL_TEXT_FX:
                tfx = cur_tfx
            else:
                tfx = ALL_TEXT_FX[(idx * 3 + 2 + run_num) % len(ALL_TEXT_FX)]
            sc["text_fx"] = tfx
            v_data["text_fx"] = tfx

        raw_vtype = str(sc.get("visual_type", "custom_scene")).lower().strip()
        current_vtype = vtype_aliases.get(raw_vtype, raw_vtype)
        sc["visual_type"] = current_vtype

        # If user explicitly chose a single-focus engine (not hybrid/auto), enforce it
        if target_type:
            if engine_style == "bytebytego_dsl" and current_vtype in ["architecture_flow", "circular_hub_mesh"]:
                pass
            elif engine_style == "benchmark_speed" and current_vtype in ["benchmark_chart", "metric_gauge_hud"]:
                pass
            else:
                sc["visual_type"] = target_type
                current_vtype = target_type

        # Anti-Repetition Safety in auto/studio modes: if Scene 1 defaulted to alert_diagram on non-outage topics, use custom_scene
        if engine_style in ["auto_dynamic", "studio_300_domain", "studio_domain_library", "cinematic_studio", "dual_generative"] and idx == 0 and current_vtype == "alert_diagram":
            topic_l = topic.lower()
            outage_kw = ["crash", "outage", "down", "lock", "deadlock", "incident", "failure", "oom"]
            if not any(kw in topic_l for kw in outage_kw):
                sc["visual_type"] = "custom_scene"
                current_vtype = "custom_scene"
                if not v_data.get("blocks"):
                    q_title = v_data.get("problem_title") or v_data.get("title") or topic[:60]
                    v_data["blocks"] = [
                        {"block": "question_card", "text": q_title, "stage": 1},
                        {"block": "banner", "text": v_data.get("challenge") or sc.get("narration", "")[:70], "tone": "highlight", "stage": 2}
                    ]

        # Force diverse engine visual modes + multiple System Topologies across scenes & consecutive videos
        _SYSTEM_TOPOLOGY_POOL = (
            "all_in_one_tech_canvas", "iso_observability_mesh", "service_mesh_envoy_proxy", "medallion_lakehouse",
            "cdc_debezium_flow", "zero_trust_proxy", "iso_event_backbone", "saga_orchestration",
            "k8s_pod_scheduling", "consistent_hashing_ring", "spatial_microservice_grid", "svg_pipeline_choreography",
            "rag_chunk_overlap_pipe", "circuit_breaker_states", "raft_leader_election", "circular_hub_mesh",
            "topo_ingress_mesh_wal", "topo_dual_plane_control_data", "topo_cdn_edge_origin_shield",
            "topo_cqrs_read_write_split", "topo_saga_choreo_compensate", "topo_rag_hybrid_rerank",
            "topo_k8s_hpa_metrics_mesh", "topo_zero_trust_spiffe_mtls", "topo_kafka_isr_quorum_dlq",
            "topo_redis_cluster_sentinel", "topo_multi_region_active_active", "topo_sharded_vitess_vtgate",
            "topo_ebpf_xdp_kernel_bypass", "topo_grpc_envoy_circuit_mesh", "topo_flink_cep_iceberg_lake",
            "topo_payment_idempotent_ledger", "topo_agent_mcp_tool_sandbox", "topo_gpu_tensor_pipeline_ring",
            "topo_webrtc_sfu_turn_relay", "topo_graphql_federation_subgraphs", "topo_oauth_pkce_jwks_rotator",
            "topo_vault_dynamic_creds_k8s", "topo_otel_trace_span_collector", "topo_chaos_mesh_blast_radius",
            "topo_clickhouse_mergetree_s3", "topo_wasm_isolate_edge_kv", "topo_blue_green_canary_alb",
            "topo_outbox_debezium_snowflake", "topo_blockchain_l2_rollup_da", "topo_ros2_lidar_slam_planner",
        )
        _THEME_ENGINE_POOLS = {
            "data_streaming_pipelines": (
                "cdc_debezium_flow", "medallion_lakehouse", "topo_flink_cep_iceberg_lake", "topo_outbox_debezium_snowflake",
                "topo_kafka_isr_quorum_dlq", "topo_clickhouse_mergetree_s3", "etl_elt_pipeline", "write_ahead_log_wal",
                "grammar:flow:5", "grammar:swimlane:4", "all_in_one_tech_canvas", "memory_wal_checkpoint",
            ),
            "distributed_consensus_labs": (
                "raft_leader_election", "consistent_hashing_ring", "circuit_breaker_states", "topo_multi_region_active_active",
                "topo_sharded_vitess_vtgate", "topo_saga_choreo_compensate", "topo_redis_cluster_sentinel",
                "topo_chaos_mesh_blast_radius", "iso_consensus_quorum", "grammar:ring:6", "sequence_diagram", "state_machine",
            ),
            "ai_rag_agents_studio": (
                "rag_chunk_overlap_pipe", "topo_rag_hybrid_rerank", "topo_agent_mcp_tool_sandbox", "topo_gpu_tensor_pipeline_ring",
                "mcp_client_host_server", "agent_react_tool_loop", "transformer_self_attn", "hnsw_vector_graph",
                "llm_guardrails_safety", "chat_thread_ai", "mesh_3d_stage", "neural_net_layers",
            ),
        }
        if engine_style == "omni_smart_director":
            from core.semantic_router import infer_geometry_family, select_semantic_scene_layout, validate_ai_scene_choice
            ai_valid = validate_ai_scene_choice(
                orig_vtype=current_vtype,
                orig_opt1=v_data.get("option1_archetype"),
                sc=sc,
                idx=idx,
                total_scenes=len(scenes),
                topic=topic,
                used_vtypes=used_vtypes,
                used_geoms=used_geoms_local,
                v_data=v_data,
            )
            if ai_valid is not None:
                routed_v, routed_opt1, routed_lbl = ai_valid
                if routed_opt1:
                    v_data["option1_archetype"] = routed_opt1
                used_geoms_local.add(infer_geometry_family(routed_v))
            else:
                routed_v, routed_lbl = select_semantic_scene_layout(
                    sc, idx, len(scenes), topic, eff_scene_tone, run_num, used_vtypes, recent_vtypes, v_data, used_geometries=used_geoms_local
                )
            current_vtype = routed_v
            sc["visual_type"] = routed_v
            sc["routed_engine"] = routed_lbl
            v_data["routed_engine"] = routed_lbl
            _mirror_items_for_domain_layout(v_data, sc, str(v_data.get("title") or topic[:40]))
        elif engine_style == "multi_topology_mix":
            fresh_topos = [t for t in _SYSTEM_TOPOLOGY_POOL if t not in recent_vtypes and t not in used_vtypes] or [t for t in _SYSTEM_TOPOLOGY_POOL if t not in used_vtypes] or list(_SYSTEM_TOPOLOGY_POOL)
            chosen_topo = fresh_topos[(run_num * 7 + idx * 5) % len(fresh_topos)]
            current_vtype = chosen_topo
            sc["visual_type"] = chosen_topo
            _mirror_items_for_domain_layout(v_data, sc, str(v_data.get("title") or topic[:40]))
        elif engine_style in _THEME_ENGINE_POOLS:
            t_pool = _THEME_ENGINE_POOLS[engine_style]
            fresh_tp = [t for t in t_pool if t not in recent_vtypes and t not in used_vtypes] or [t for t in t_pool if t not in used_vtypes] or list(t_pool)
            chosen_tp = fresh_tp[(run_num * 5 + idx * 3) % len(fresh_tp)]
            current_vtype = chosen_tp
            sc["visual_type"] = chosen_tp
            _mirror_items_for_domain_layout(v_data, sc, str(v_data.get("title") or topic[:40]))
        elif is_diverse_engine and engine_style != "pure_zero_template":
            fam_keys_all = ("hook", "flow", "hub", "tiers", "compare", "metrics", "code", "summary")
            rot_fam = fam_keys_all[(idx * 2 + run_num) % len(fam_keys_all)]
            orig_fam = _LAYOUT_TO_FAMILY.get(current_vtype)
            needs_swap = (current_vtype in recent_vtypes) or (current_vtype in used_vtypes) or (engine_style in ("interactive_storyboard", "auto_dynamic") and idx > 0 and orig_fam in ("hook", "summary") and idx != len(scenes) - 1)
            if needs_swap and current_vtype not in ("web_scene", "svg_scene", "spatial_canvas"):
                fam = orig_fam
                if not fam or (run_num >= 2 and idx in (1, 2)):
                    fam = rot_fam
                if engine_style == "interactive_storyboard":
                    inter_pool = (
                        "sequence_diagram", "er_schema", "flamegraph_perf", "latency_waterfall",
                        "sankey_flow", "radar_spider", "kanban_board", "chat_thread_ai",
                        "code_diff_split", "api_request_response", "mesh_3d_stage", "benchmark_3d",
                        "consistent_hashing_ring", "all_in_one_tech_canvas", "grammar:bento:5", "grammar:quadrant:2x2",
                    )
                    fam_pool = tuple([p for p in inter_pool if p not in used_vtypes] or list(inter_pool))
                elif engine_style in _STUDIO_SET:
                    # Mix both native family AND cross-family system topologies / pro charts so 15 reels never repeat!
                    base_pool = _DIVERSE_LAYOUT_FAMILIES.get(fam, _DIVERSE_LAYOUT_FAMILIES["flow"])
                    if idx % 2 == 1 and fam not in ("code", "metrics"):
                        fam_pool = tuple(list(_SYSTEM_TOPOLOGY_POOL) + list(base_pool))
                    else:
                        fam_pool = base_pool
                else:
                    modular_pool = {
                        "hook": ("hero_hook", "custom_scene", "alert_diagram", "kinetic_statement"),
                        "flow": ("architecture_flow", "step_timeline", "all_in_one_tech_canvas", "circular_hub_mesh"),
                        "hub": ("circular_hub_mesh", "architecture_flow", "all_in_one_tech_canvas"),
                        "tiers": ("step_timeline", "architecture_flow", "concept_cards"),
                        "compare": ("split_comparison", "hybrid_merge", "benchmark_chart"),
                        "metrics": ("benchmark_chart", "metric_gauge_hud", "split_comparison"),
                        "code": ("code_terminal", "sql_table", "data_structure_memory"),
                        "summary": ("concept_cards", "kinetic_statement", "hybrid_merge", "step_timeline"),
                    }
                    fam_pool = modular_pool.get(fam, modular_pool["flow"])
                fresh_fam = [ly for ly in fam_pool if ly not in recent_vtypes and ly not in used_vtypes]
                if not fresh_fam:
                    fresh_fam = [ly for ly in fam_pool if ly not in used_vtypes] or list(fam_pool)
                new_vtype = fresh_fam[(run_num * 5 + idx * 3) % len(fresh_fam)]
                if new_vtype != current_vtype:
                    current_vtype = new_vtype
                    sc["visual_type"] = new_vtype
                    _mirror_items_for_domain_layout(v_data, sc, str(v_data.get("title") or topic[:40]))

        # Ensure required data structures are present and rich for the active visual_type
        # Voice-Text Concept Hydration: ground EVERY layout field in what this scene's voice actually speaks
        title = v_data.get("title") or sc.get("narration", "")[:45] or topic[:40]
        default_badge = "" if engine_style in ["omni_smart_director", "auto_dynamic", "studio_300_domain", "pure_zero_template", "studio_domain_library", "cinematic_studio", "dual_generative", "hybrid_modern"] else engine_style.replace("_", " ").upper()
        badge = v_data.get("badge") or default_badge
        v_data["title"] = title
        v_data["badge"] = badge
        _vfacts = _extract_voice_facts(sc.get("narration", ""), topic, str(title), sc.get("dialogue"))
        _vphrases = _vfacts["phrases"] or [str(title)[:24]]
        _vclauses = _vfacts["clauses"] or [str(title)]
        _slug = re.sub(r"[^a-z0-9_]", "_", topic.lower())[:16].strip("_") or "service"

        if current_vtype.startswith("topo_") or current_vtype in ("multi_topology_dual", "dual_topology", "topology_dual"):
            # Hydrate BOTH upper Plane A and lower Plane B directly from spoken narration concepts instead of generic defaults
            if not v_data.get("plane_a") or not v_data.get("plane_b"):
                existing_n = [dict(n) if isinstance(n, dict) else {"name": str(n)} for n in (v_data.get("nodes") or v_data.get("items") or [])]
                pool_n = list(existing_n)
                for ph_i, ph in enumerate(_vphrases):
                    if len(pool_n) >= 6:
                        break
                    if not any(ph.lower() in str(x.get("name", "")).lower() for x in pool_n):
                        cl_s = _vclauses[min(ph_i, len(_vclauses) - 1)][:42]
                        pool_n.append({"name": ph[:26], "sub": cl_s})
                while len(pool_n) < 6:
                    idx_p = len(pool_n)
                    lbl_fallback = f"{_vphrases[idx_p % len(_vphrases)][:18]} Stage {idx_p + 1}"
                    pool_n.append({"name": lbl_fallback, "sub": str(_vclauses[idx_p % len(_vclauses)])[:40]})
                _shapes_a = ("router", "kafka_broker", "api_gateway")
                _shapes_b = ("server_rack", "k8s_pod_mesh", "database_cluster")
                if not v_data.get("plane_a"):
                    v_data["plane_a"] = [dict(pool_n[k], shape=pool_n[k].get("shape") or _shapes_a[k % 3]) for k in range(3)]
                if not v_data.get("plane_b"):
                    v_data["plane_b"] = [dict(pool_n[3 + k], shape=pool_n[3 + k].get("shape") or _shapes_b[k % 3]) for k in range(3)]

        from core.semantic_router import infer_geometry_family as _infer_geom
        _vgeom = _infer_geom(current_vtype)

        if _vgeom == "code_diff" or current_vtype.startswith(("code_", "terminal_", "diff_")) or current_vtype == "api_request_response":
            if not v_data.get("code_snippet") and not v_data.get("command"):
                fn_nm = _vfacts["fn_name"] or f"run_{_slug}"
                ent_a = (_vphrases[0] if _vphrases else topic[:16]).lower().replace(" ", "_")[:18]
                ent_b = (_vphrases[1] if len(_vphrases) > 1 else "quorum_store").lower().replace(" ", "_")[:18]
                v_data["command"] = _vfacts["command"] or f"python -m {_slug} --worker {ent_a}"
                v_data["code_snippet"] = (
                    f"# {title[:36]}\n"
                    f"async def {fn_nm}(ctx):\n"
                    f"    state = await {ent_a}.acquire(ctx)\n"
                    f"    return await {ent_b}.commit_async(state)"
                )
            if current_vtype in ("code_diff_split", "diff_mutex_to_atomic", "diff_n_plus_one_fix"):
                ent_a = (_vphrases[0] if _vphrases else _slug).lower().replace(" ", "_")[:16]
                v_data.setdefault("before_label", "NAIVE / BLOCKING")
                v_data.setdefault("after_label", f"OPTIMIZED {ent_a.upper()[:14]}")
                v_data.setdefault("before", f"with {ent_a}.lock():\n    res = query_sync()\n    block_wait(res)")
                v_data.setdefault("after", f"async with {ent_a}.stream() as s:\n    await s.commit()\n    return {{'lag_ms': 2}}")
                v_data.setdefault("left_label", v_data["before_label"])
                v_data.setdefault("right_label", v_data["after_label"])
                v_data.setdefault("left_code", v_data["before"])
                v_data.setdefault("right_code", v_data["after"])

        elif _vgeom == "sql_schema" or current_vtype == "star_snowflake_schema":
            if not v_data.get("code_snippet") and not v_data.get("query"):
                v_data["code_snippet"] = _vfacts["sql_query"] or f"SELECT key_id, COUNT(*), DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)\nFROM {_slug}_events GROUP BY key_id;"
            v_data.setdefault("query", v_data["code_snippet"])
            if not v_data.get("table_data"):
                cols_s = _vfacts["sql_cols"] or ["entity", "stage", "throughput", "rk"]
                rows_s = _vfacts["sql_rows"] or [
                    [_vphrases[ri % len(_vphrases)][:12], f"shard_{ri + 1}", f"{max(2, 96 - ri * 22)}k/s", str(ri + 1)]
                    for ri in range(4)
                ]
                v_data["table_data"] = {"headers": cols_s, "rows": rows_s}
                v_data["columns"] = cols_s
                v_data["rows"] = rows_s

        elif current_vtype == "architecture_flow":
            if not v_data.get("nodes"):
                pal_c = ("#38BDF8", "#818CF8", "#FBBF24", "#34D399")
                v_data["nodes"] = [
                    {
                        "id": f"n{k}",
                        "label": _vphrases[k % len(_vphrases)][:24],
                        "sub": _vclauses[k % len(_vclauses)][:48],
                        "edge": ["Ingest", "Process", "Route", "Sync"][k % 4] if k < 3 else "",
                        "color": pal_c[k % 4],
                    }
                    for k in range(4)
                ]

        elif _vgeom == "compare_matrix":
            if not v_data.get("left_points") or not v_data.get("right_points"):
                p0 = _vphrases[0] if _vphrases else topic[:20]
                p1 = _vphrases[1] if len(_vphrases) > 1 else "Async Pattern"
                v_data["left_label"] = v_data.get("left_label") or f"LEGACY {p0.upper()[:16]}"
                v_data["left_points"] = v_data.get("left_points") or [
                    cl[:42] for cl in _vclauses[:3]
                ] or [f"Blocking on {p0[:20]}", "Tail latency spikes", "Retry queue backlog"]
                v_data["right_label"] = v_data.get("right_label") or f"MODERN {p1.upper()[:16]}"
                v_data["right_points"] = v_data.get("right_points") or [
                    f"Zero-lock {p1[:20]}", "Bounded backpressure", "Sub-millisecond P99", "Deterministic failover"
                ]

        elif _vgeom == "metrics_charts":
            _vm = _vfacts["metrics"]
            if not v_data.get("bars"):
                if len(_vm) >= 2:
                    s_m = sorted(_vm, key=lambda x: x[1], reverse=True)
                    bars_dyn = []
                    bcols = ("#EF4444", "#F97316", "#FBBF24", "#10B981")
                    for bi, (ml, mv, md) in enumerate(s_m[:4]):
                        is_w = (bi == len(s_m[:4]) - 1)
                        bars_dyn.append({"label": ml or _vphrases[bi % len(_vphrases)], "value": max(1, int(mv)), "display": md, "color": "#10B981" if is_w else bcols[bi % 3], "is_winner": is_w})
                    v_data["bars"] = bars_dyn
                    v_data["winner_badge"] = v_data.get("winner_badge") or (f"{_vm[-1][2].upper()} VERIFIED")
                else:
                    v_data["winner_badge"] = v_data.get("winner_badge") or f"{(_vphrases[0] if _vphrases else topic)[:12].upper()} FAST PATH"
                    v_data["bars"] = [
                        {"label": f"Legacy {_vphrases[0][:14]}", "value": 920, "display": "920ms", "color": "#EF4444", "is_winner": False},
                        {"label": "Pooled Sync Queue", "value": 340, "display": "340ms", "color": "#F97316", "is_winner": False},
                        {"label": f"Async {_vphrases[-1][:14]}", "value": 24, "display": "24ms P99 (Winner)", "color": "#10B981", "is_winner": True},
                    ]
            if current_vtype in ("radial_gauge", "slo_burn_rate_gauge", "gauge_slo_availability") and not v_data.get("main_value"):
                _best_m = _vm[-1] if _vm else ("P99 SPEEDUP", 98, "99.9%")
                v_data["main_value"] = _best_m[2]
                v_data["main_unit"] = (_best_m[0] or "LIVE METRIC").upper()
                v_data["gauge_percent"] = 96
                v_data["telemetry"] = [{"label": (ml or f"M{k+1}").upper()[:14], "val": md} for k, (ml, _, md) in enumerate(_vm[:3])] or [
                    {"label": _vphrases[0][:14].upper(), "val": "24ms"},
                    {"label": "SLA", "val": "99.99%"},
                ]
                v_data["slices"] = [{"label": f"{ml or _vphrases[k % len(_vphrases)][:12]} ({md})", "value": max(10, int(mv))} for k, (ml, mv, md) in enumerate(_vm[:3])] or [
                    {"label": _vphrases[0][:16], "value": 65}, {"label": "Headroom", "value": 35}
                ]
            if current_vtype in ("p99_tail_cdf_curve", "line_area_chart") and not v_data.get("values"):
                if len(_vm) >= 2:
                    vals_m = [int(max(2, min(100, (x[1] / max(1.0, max(y[1] for y in _vm))) * 96))) for x in _vm]
                    while len(vals_m) < 6:
                        vals_m.append(max(4, vals_m[-1] // 2))
                    v_data["values"] = vals_m[:8]
                else:
                    v_data["values"] = [92, 74, 48, 28, 12, 4]
                v_data.setdefault("caption", f"{title[:28]} — Latency Profile")
            if current_vtype == "radar_spider" and not v_data.get("axes"):
                v_data["axes"] = [{"label": _vphrases[k % len(_vphrases)][:14], "value": 92 - k * 5} for k in range(5)]
            if current_vtype == "donut_3d" and not v_data.get("slices"):
                v_data["slices"] = [{"label": _vphrases[k % len(_vphrases)][:18], "value": max(15, 45 - k * 10)} for k in range(3)]
            if current_vtype == "sankey_flow" and not v_data.get("flows"):
                v_data["flows"] = [
                    {"from": _vphrases[k % len(_vphrases)][:16], "to": _vphrases[(k + 1) % len(_vphrases)][:16], "label": ["Stream", "Route", "Commit"][k % 3]}
                    for k in range(3)
                ]

        elif current_vtype in ("data_structure_memory", "write_ahead_log_wal", "memory_wal_checkpoint", "memory_ring_buffer", "memory_lsm_memtable"):
            if not v_data.get("entries"):
                ops = ("APPEND", "BUFFER", "COMMIT", "SYNC")
                sts = ("REPLICATED", "IN-TRANSIT", "BUFFERED", "SYNCED")
                v_data["entries"] = [
                    {"address": f"0x00{chr(65 + k)}{k + 1}", "op": f"{ops[k]} {_vphrases[k % len(_vphrases)][:16]}", "table": _slug[:14], "status": sts[k]}
                    for k in range(4)
                ]

        elif current_vtype == "circular_hub_mesh":
            if not v_data.get("satellites"):
                v_data["hub_name"] = v_data.get("hub_name") or (_vphrases[0][:18].upper() if _vphrases else topic[:18].upper())
                pal_s = ("#38BDF8", "#34D399", "#FBBF24", "#A855F7")
                v_data["satellites"] = [
                    {"name": _vphrases[k % len(_vphrases)][:20], "role": _vclauses[k % len(_vclauses)][:22], "color": pal_s[k % 4]}
                    for k in range(4)
                ]

        elif current_vtype == "chat_thread_ai":
            if not v_data.get("messages"):
                dlg_src = sc.get("dialogue")
                if isinstance(dlg_src, list) and dlg_src:
                    v_data["messages"] = [
                        {
                            "role": "user" if str(d.get("speaker") or "").lower() == "female" else "ai",
                            "badge": "CURIOUS Q" if str(d.get("speaker") or "").lower() == "female" else "MENTOR",
                            "text": str(d.get("text") or "")[:140],
                        }
                        for d in dlg_src[:4] if isinstance(d, dict) and d.get("text")
                    ]
                else:
                    cl_chat = _split_narration_clauses(sc.get("narration", ""), target_count=4)
                    v_data["messages"] = [
                        {"role": "ai" if c_i % 2 else "user", "text": c_t[:140]}
                        for c_i, c_t in enumerate(cl_chat)
                    ]

        elif current_vtype == "metric_gauge_hud":
            if not v_data.get("main_value"):
                v_data["main_value"] = "99.999%"
                v_data["main_unit"] = "PRODUCTION SLA"
                v_data["gauge_percent"] = 99
                v_data["telemetry"] = [
                    {"label": "THROUGHPUT", "val": "1.2M req/s"},
                    {"label": "AVG LATENCY", "val": "1.8 ms"},
                    {"label": "AVAILABILITY", "val": "99.999%"}
                ]

        elif current_vtype in ("alert_diagram", "incident_radar"):
            if not v_data.get("challenge"):
                v_data["problem_title"] = v_data.get("problem_title") or f"Production Bottleneck: {title}"
                v_data["problem_desc"] = v_data.get("problem_desc") or "High concurrency spikes caused thread contention and system degradation."
                v_data["challenge"] = "How to achieve 100% availability without sacrificing latency?"
            if not v_data.get("alerts") and not v_data.get("blips"):
                pt = str(v_data.get("problem_title") or title)
                ch = str(v_data.get("challenge") or "")
                v_data["alerts"] = [
                    {"title": pt[:24], "severity": "critical", "sub": str(v_data.get("problem_desc") or "")[:95]},
                    {"title": "Table Lock Risk", "severity": "high"},
                    {"title": "Downtime Impact", "severity": "warn"},
                    {"title": ch[:22] if ch else "Zero-Lock Need", "severity": "warn"},
                ]

        elif current_vtype == "hero_hook":
            v_data["question"] = v_data.get("question") or v_data.get("problem_title") or title
            if "pills" not in v_data and (v_data.get("left_pill") or v_data.get("right_pill")):
                v_data["pills"] = [p for p in [v_data.get("left_pill"), v_data.get("right_pill"), v_data.get("badge") or "DEEP DIVE"] if p]
            if not v_data.get("pills"):
                v_data["pills"] = ["Naive Bottleneck", "Core Fix", "Production Scale"]
            if not v_data.get("sub_callouts"):
                cl_hook = _split_narration_clauses(sc.get("narration", ""), target_count=4)
                v_data["sub_callouts"] = [c[:72] for c in cl_hook[:4]] or [
                    f"Trap: Ignoring {topic[:20]} edge contention",
                    "Root Cause: Synchronous blocking under peak load",
                    "Smart Fix: Lock-free staged async pipeline",
                ]

        elif current_vtype == "custom_scene":
            if not v_data.get("blocks"):
                bullets = _split_narration_clauses(sc.get("narration", ""), target_count=4)
                v_data["blocks"] = [
                    {"block": "question_card", "text": title, "stage": 1},
                    {"block": "list_cards", "items": [
                        {"title": " ".join(b.split()[:4])[:36], "sub": b[:64], "kind": "info"}
                        for b in bullets[:4]
                    ], "stage": 2},
                    {"block": "banner", "text": bullets[-1][:58] if bullets else f"{title[:34]} Breakdown", "stage": 3},
                ]

        elif current_vtype == "hybrid_merge":
            v_data["left_pillar"] = v_data.get("left_pillar") or {"label": "Core Logic / Style", "sub": "Consistent Output"}
            v_data["right_pillar"] = v_data.get("right_pillar") or {"label": "Live Retrieval / State", "sub": "Fresh Data Context"}
            v_data["merged_label"] = v_data.get("merged_label") or f"{title[:20]} Hybrid"
            v_data["outcomes"] = v_data.get("outcomes") or ["Accuracy", "Consistency", "Low Latency"]

        elif current_vtype == "kinetic_statement":
            v_data["kicker"] = v_data.get("kicker") or "KEY ENGINEERING TAKEAWAY"
            v_data["statement"] = v_data.get("statement") or sc.get("narration", "")[:80] or title
            v_data["highlight_word"] = v_data.get("highlight_word") or ""
            cl_ks = _split_narration_clauses(sc.get("narration", ""), target_count=4)
            v_data["bottom_tags"] = v_data.get("bottom_tags") or ["High Precision", "Low Latency", "Production Ready"]
            if not v_data.get("sub_points"):
                v_data["sub_points"] = [
                    {"name": _extract_crisp_beat_label(c, i), "sub": _extract_crisp_beat_label(c, i), "edge": ["Next", "Verify", "Scale", ""][i % 4]}
                    for i, c in enumerate(cl_ks[:4])
                ]

        elif current_vtype == "step_timeline":
            if not v_data.get("steps"):
                v_data["steps"] = [
                    {"num": "01", "title": f"{title[:18]} Init", "desc": "Incoming request or query"},
                    {"num": "02", "title": "Core Processing", "desc": "Contextual lookup & validation"},
                    {"num": "03", "title": "Execution Engine", "desc": "Apply rules & transformation"},
                    {"num": "04", "title": "Verified Output", "desc": "Deterministic production response"}
                ]

        elif current_vtype == "all_in_one_tech_canvas":
            v_data["vpc_label"] = v_data.get("vpc_label") or f"SYSTEM ARCHITECTURE • {title.upper()[:24]}"
            v_data["comp1_label"] = v_data.get("comp1_label") or "Client / Ingestion"
            v_data["comp1_sub"] = v_data.get("comp1_sub") or "API & Request Layer"
            v_data["comp2_label"] = v_data.get("comp2_label") or "AI / Compute Engine"
            v_data["comp2_sub"] = v_data.get("comp2_sub") or "Processing & Logic"
            v_data["comp3_label"] = v_data.get("comp3_label") or f"{title[:14]} Core"
            v_data["comp3_sub"] = v_data.get("comp3_sub") or "Orchestrator / Broker"
            v_data["comp4_label"] = v_data.get("comp4_label") or "Primary Database"
            v_data["comp4_sub"] = v_data.get("comp4_sub") or "Transactional Store"
            v_data["comp5_label"] = v_data.get("comp5_label") or "Target Sink / Cache"
            v_data["comp5_sub"] = v_data.get("comp5_sub") or "Analytics / Output"
            v_data["arrow1_label"] = v_data.get("arrow1_label") or "gRPC Stream"
            v_data["arrow2_label"] = v_data.get("arrow2_label") or "Async Inference"
            v_data["arrow3_label"] = v_data.get("arrow3_label") or "State Write"
            v_data["arrow4_label"] = v_data.get("arrow4_label") or "Event Sync"

        v_data["_variation_seed"] = run_num
        from core.semantic_router import pick_best_opt1_archetype
        chosen_opt1 = v_data.get("option1_archetype") or pick_best_opt1_archetype(
            topic,
            narration=sc.get("narration", ""),
            title=str(title),
            run_num=run_num,
            idx=idx,
            recent_vtypes=recent_vtypes,
        )
        if engine_style == "pure_zero_template" and current_vtype not in ("svg_scene", "spatial_canvas"):
            v_data.setdefault("_intent", current_vtype)
            v_data.setdefault("option1_archetype", chosen_opt1)
            if chosen_opt1.startswith("svg_"):
                sc["visual_type"] = "svg_scene"
            elif chosen_opt1.startswith("spatial_"):
                sc["visual_type"] = "spatial_canvas"
            else:
                sc["visual_type"] = "web_scene"
            used_vtypes.add(chosen_opt1)
        elif engine_style in ("studio_300_domain", "interactive_storyboard", "auto_dynamic", "hybrid_modern") and (idx + run_num) % 2 == 0 and current_vtype not in ("web_scene", "svg_scene", "spatial_canvas", "sql_table", "sql_studio", "code_terminal", "terminal_studio", "chat_thread_ai", "split_comparison", "benchmark_3d", "benchmark_chart"):
            # Combined, Interactive Max & Dynamic Auto: alternate Option 1 web/svg/spatial archetypes cleanly!
            v_data.setdefault("_intent", current_vtype)
            v_data.setdefault("option1_archetype", chosen_opt1)
            sc["visual_type"] = "svg_scene" if chosen_opt1.startswith("svg_") else ("spatial_canvas" if chosen_opt1.startswith("spatial_") else "web_scene")
            used_vtypes.add(current_vtype)
            used_vtypes.add(chosen_opt1)
        elif engine_style == "omni_smart_director" and idx == len(scenes) - 1 and current_vtype not in ("web_scene", "svg_scene", "spatial_canvas"):
            # Pick semantically best Option 1 3D WebGL/SVG archetype dynamically across all 168 Option 1 engines
            w_pick = pick_best_opt1_archetype(
                topic,
                narration=sc.get("narration", ""),
                title=str(title),
                run_num=run_num,
                idx=idx,
                recent_vtypes=recent_vtypes,
            )
            v_data.setdefault("_intent", current_vtype)
            v_data.setdefault("option1_archetype", w_pick)
            sc["visual_type"] = "web_scene"
            sc["routed_engine"] = "Option 1 Interactive 3D WebGL"
            v_data["routed_engine"] = sc["routed_engine"]
            used_vtypes.add(w_pick)
        else:
            used_vtypes.add(sc["visual_type"])

        # Guarantee deep multi-section content (4-5 progressive stages + cue_phrase + connector labels + footer + voice_beats)
        clauses = _split_narration_clauses(sc.get("narration", ""), target_count=5)
        for col_key in ("nodes", "steps", "stages", "milestones"):
            seq = v_data.get(col_key)
            if isinstance(seq, list) and seq and clauses:
                norm_seq = [dict(x) if isinstance(x, dict) else {"name": str(x)} for x in seq]
                c_i = 0
                while len(norm_seq) < 4 and c_i < len(clauses):
                    cl = clauses[c_i]
                    c_i += 1
                    head = _extract_crisp_beat_label(cl, c_i)
                    if any(head.lower() in str(x.get("name", "")).lower() for x in norm_seq):
                        continue
                    norm_seq.append({"name": head[:28], "sub": _extract_crisp_beat_label(cl, c_i)})
                for x_i, x in enumerate(norm_seq):
                    if not x.get("sub") and x_i < len(clauses):
                        x["sub"] = _extract_crisp_beat_label(clauses[x_i], x_i)
                    if not x.get("cue_phrase") and x_i < len(clauses):
                        cws = [re.sub(r"[^a-zA-Z0-9_\u0900-\u097F-]", "", w) for w in clauses[x_i].split()]
                        kws = [w for w in cws if len(w) >= 4]
                        x["cue_phrase"] = " ".join(kws[:3]) if kws else ""
                    if x_i + 1 < len(norm_seq) and not x.get("edge"):
                        x["edge"] = ["Ingest", "Route", "Process", "Commit"][x_i % 4]
                v_data[col_key] = norm_seq[:5]

        # Top up sparse bullets, comparison lists, and custom blocks cleanly without broken Hinglish fragments
        if isinstance(v_data.get("bullets"), list) and 0 < len(v_data["bullets"]) < 4 and clauses:
            bl = list(v_data["bullets"])
            for bi, cl in enumerate(clauses):
                if len(bl) >= 4:
                    break
                hd = _extract_crisp_beat_label(cl, bi)
                if not any(hd.lower() in str(x).lower() for x in bl):
                    bl.append(hd)
            v_data["bullets"] = bl[:5]
        for pt_key in ("left_points", "right_points"):
            pts_l = v_data.get(pt_key)
            if isinstance(pts_l, list) and 0 < len(pts_l) < 4 and clauses:
                for bi, cl in enumerate(clauses):
                    if len(pts_l) >= 4:
                        break
                    pts_l.append(_extract_crisp_beat_label(cl, bi))
                v_data[pt_key] = pts_l[:5]
        if isinstance(v_data.get("blocks"), list) and len(v_data["blocks"]) < 2 and clauses:
            v_data["blocks"].append({
                "block": "list_cards",
                "items": [{"title": _extract_crisp_beat_label(c, bi), "sub": _extract_crisp_beat_label(c, bi), "kind": "info"} for bi, c in enumerate(clauses[:4])],
                "stage": 2,
            })

        # Populate chronological Voice-Synced Highlight Beats on EVERY scene so sparse visuals ALWAYS have multi-label voice progression
        existing_vb = v_data.get("voice_beats")
        if not isinstance(existing_vb, list) or len(existing_vb) < 4:
            vb_list = []
            for c_idx, cl in enumerate(clauses[:5]):
                head = _extract_crisp_beat_label(cl, c_idx)
                vb_list.append({
                    "label": head,
                    "sub": cl[:64],
                    "edge": ["Next", "Process", "Verify", "Scale"][c_idx % 4] if c_idx + 1 < len(clauses[:5]) else "",
                })
            if vb_list:
                v_data["voice_beats"] = vb_list[:5]

        if not v_data.get("footer") and clauses:
            v_data["footer"] = clauses[-1][:64]

        # Guarantee clean Dual-Voice Conversation turns (`dialogue`) whenever `dual_creator_debate` or a `dual:` voice is selected
        if is_dual_tone(tone) or is_dual_tone(sc.get("scene_tone")) or (isinstance(sc.get("dialogue"), list) and len(sc.get("dialogue") or []) >= 1):
            sc["scene_tone"] = DUAL_TONE_KEY if tone != "dual_dialogue_curious" else "dual_dialogue_curious"
            raw_dlg = sc.get("dialogue")
            clean_dlg: List[Dict[str, str]] = []
            if isinstance(raw_dlg, list):
                for item in raw_dlg:
                    if not isinstance(item, dict):
                        continue
                    spk_raw = str(item.get("speaker") or "male").strip().lower()
                    spk = "female" if spk_raw in ("female", "f", "she", "questioner", "curious", "girl", "student") else "male"
                    txt = re.sub(
                        r"^\s*(?:female|male|she|he|questioner|solver|mentor|dost|host)\s*:\s*",
                        "",
                        str(item.get("text") or "").strip(),
                        flags=re.IGNORECASE,
                    )
                    if txt:
                        clean_dlg.append({"speaker": spk, "text": txt})
            if len(clean_dlg) < 2:
                narr_clean = re.sub(
                    r"^\s*(?:female|male|she|he|questioner|solver|mentor)\s*:\s*",
                    "",
                    str(sc.get("narration") or "").strip(),
                    flags=re.IGNORECASE,
                )
                role_s = str(sc.get("role") or "").lower()
                if role_s == "hook" or idx == 0:
                    q_txt = f"{title[:38]} ka core problem kya hai aur yeh scale par kaise behave karta hai?"
                    a_txt = narr_clean or f"{title[:34]} mein exact architecture aur data flow step-by-step dekhte hain."
                elif role_s == "cta" or idx == len(scenes) - 1:
                    q_txt = f"{title[:34]} mein production architecture finalize karte waqt kaunsa pattern choose karna chahiye?"
                    a_txt = narr_clean or "Workload ke throughput, ACID guarantees aur cost trade-offs ke basis par pattern decide hota hai."
                else:
                    q_txt = f"{title[:36]} ke internal pipeline mein key components kaise interact karte hain?"
                    a_txt = narr_clean or f"{title[:30]} ki execution layer state consistency aur latency maintain karti hai."
                clean_dlg = [
                    {"speaker": "female", "text": q_txt},
                    {"speaker": "male", "text": a_txt},
                ]
            sc["dialogue"] = clean_dlg
            sc["narration"] = " ".join(d["text"] for d in clean_dlg).strip()
            clauses = _split_narration_clauses(sc["narration"], target_count=5) or clauses
            if current_vtype == "chat_thread_ai":
                v_data["messages"] = [
                    {
                        "role": "user" if d["speaker"] == "female" else "ai",
                        "badge": "CURIOUS Q" if d["speaker"] == "female" else "MENTOR",
                        "text": d["text"][:140],
                    }
                    for d in clean_dlg[:4]
                ]

        sc["visual_data"] = v_data

        # Ensure Audio-Visual Choreography triggers exist for voice-synced Progressive Reveal (4-5 chronological beats)
        choreo = sc.get("choreography")
        existing_trig = list(choreo.get("triggers") or []) if isinstance(choreo, dict) else []
        if len(existing_trig) < 4:
            narration_words = [
                re.sub(r"[^a-zA-Z0-9_\u0900-\u097F-]", "", w)
                for w in sc.get("narration", "").split()
            ]
            narration_words = [w for w in narration_words if len(w) >= 4]
            auto_triggers = []
            if len(narration_words) >= 5:
                step = len(narration_words) / 5.0
                for st_i in range(5):
                    kw = narration_words[min(len(narration_words) - 1, int(st_i * step))]
                    auto_triggers.append({"stage": st_i + 1, "keyword": kw.lower()})
            elif len(narration_words) >= 2:
                for st_i, kw in enumerate(narration_words[:5]):
                    auto_triggers.append({"stage": st_i + 1, "keyword": kw.lower()})
            sc["choreography"] = {
                "mode": "node_edge_traversal" if current_vtype in ["all_in_one_tech_canvas", "architecture_flow", "circular_hub_mesh"] else "progressive_build",
                "triggers": existing_trig if len(existing_trig) >= len(auto_triggers) else auto_triggers
            }

    if engine_style in ("omni_smart_director", "pure_zero_template", "dual_generative", "studio_300_domain", "auto_dynamic", "hybrid_modern"):
        _synthesize_bespoke_web_scenes(scenes, topic, format_ratio=format_ratio, run_num=run_num)

    if scenes:
        last_vd = scenes[-1].setdefault("visual_data", {})
        c_cta = str(cta_style or "save_share").lower().strip()
        if c_cta == "comment_keyword":
            clean_kw = re.sub(r"[^A-Za-z0-9_-]", "", str(cta_keyword or "").strip()).upper()[:18] or "NOTES"
            cta_line = f"Comment {clean_kw} for Notes & Code"
            last_vd["footer_cta"] = cta_line
            last_vd["footer"] = cta_line
            if not re.search(rf"\bcomment\b.*\b{re.escape(clean_kw.lower())}\b", str(scenes[-1].get("narration") or "").lower()):
                scenes[-1]["narration"] = str(scenes[-1].get("narration") or "").rstrip(".") + f". Comment {clean_kw} below for full architecture notes!"
        elif c_cta == "clean_zero_cta":
            last_vd.pop("footer_cta", None)

    return timeline

def generate_video_titles(topic: str, channel_tag: str = "@Code_With_Mangesh") -> List[Dict[str, str]]:
    """
    Generates 6 distinct, high-CTR, viral titles categorized by marketing hooks.
    """
    clean_topic = topic.strip()
    
    # 1. Try Gemini
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""You are a YouTube Shorts & Instagram Reels viral growth strategist.
Generate 6 ultra-high CTR video titles for this technical topic:
Topic: "{clean_topic}"

Return ONLY a valid JSON array of 6 objects matching this schema:
[
  {{"title": "🔥 Catchy Title 1 (Punchy, with emojis, under 65 chars)", "category": "Viral Hook"}},
  {{"title": "⚡ Architecture Title 2", "category": "System Design"}},
  {{"title": "❌ Trade-off Title 3", "category": "Common Mistake"}},
  {{"title": "🧠 Interview Title 4", "category": "Interview"}},
  {{"title": "🚀 Staff Engineer Title 5", "category": "Staff Engineer"}},
  {{"title": "💡 Crash Course Title 6", "category": "Quick Explainer"}}
]
"""
            for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.5-flash"]:
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    raw_text = res.text.strip() if hasattr(res, "text") and res.text else ""
                    match = re.search(r"\[[\s\S]*\]", raw_text)
                    if match:
                        parsed = json.loads(match.group(0))
                        if isinstance(parsed, list) and len(parsed) >= 3:
                            return parsed
                except Exception:
                    continue
        except Exception:
            pass
            
    # 2. Resilient Fallback Template
    safe_topic = clean_topic.title()
    return [
        {"title": f"🔥 {safe_topic} Explained Like a Staff Engineer!", "category": "Staff Engineer"},
        {"title": f"⚡ Why 99% of Developers Get {safe_topic} Wrong!", "category": "Common Mistake"},
        {"title": f"🧠 System Design Interview: {safe_topic} Architecture", "category": "Interview"},
        {"title": f"🚀 How Production Systems Scale {safe_topic} to Millions!", "category": "Production Scale"},
        {"title": f"❌ Stop Using Traditional Patterns for {safe_topic}!", "category": "Trade-off"},
        {"title": f"💡 Zero-Fluff 60s Visual Guide to {safe_topic}", "category": "Quick Explainer"}
    ]

def _salvage_scenes_from_truncated_json(text: str, topic_hint: str = "") -> Dict[str, Any]:
    """Recovers complete scene objects from truncated LLM JSON when output cut off mid-response."""
    m = re.search(r'"scenes"\s*:\s*\[', text)
    if not m:
        return {}
    decoder = json.JSONDecoder(strict=False)
    idx = m.end()
    n = len(text)
    scenes: List[Dict[str, Any]] = []
    while idx < n:
        while idx < n and text[idx] in " \t\r\n,":
            idx += 1
        if idx >= n or text[idx] == "]":
            break
        if text[idx] != "{":
            nxt = text.find("{", idx)
            if nxt == -1:
                break
            idx = nxt
        try:
            obj, end_idx = decoder.raw_decode(text, idx)
            if isinstance(obj, dict) and (obj.get("narration") or obj.get("visual_data") or obj.get("visual_type")):
                scenes.append(obj)
            idx = end_idx
        except Exception:
            break
    if not scenes:
        return {}
    title_m = re.search(r'"title"\s*:\s*"([^"]+)"', text)
    style_m = re.search(r'"art_style"\s*:\s*"([^"]+)"', text)
    return {
        "title": title_m.group(1) if title_m else (topic_hint or "Tech Deep Dive"),
        "art_style": style_m.group(1) if style_m else "sapphire_3d",
        "scenes": scenes,
    }


def _build_emergency_fallback_timeline(
    topic: str,
    tone: str = DEFAULT_CONCRETE_TONE,
    engine_style: str = "studio_domain_library",
    duration_mode: str = "auto",
    voice: str = "en-IN-PrabhatNeural|hinglish",
    format_ratio: str = "9:16",
) -> Dict[str, Any]:
    """Deterministic multi-scene storyboard used only if every external LLM API fails simultaneously."""
    clean_topic = (topic or "System Design Architecture").strip()[:70]
    scene_tone = resolve_effective_tone(tone)
    is_marathi = voice.startswith("mr-") or voice.endswith("|mr")
    is_hindi = voice.startswith("hi-") or voice.endswith("|hi")

    if is_dual_tone(scene_tone) or str(voice).startswith("dual:"):
        dual_scenes = [
            {
                "scene_id": 1,
                "role": "hook",
                "scene_tone": DUAL_TONE_KEY,
                "dialogue": [
                    {"speaker": "female", "text": f"{clean_topic} mein production architecture design karte waqt sabse badi limitation kahan aati hai?"},
                    {"speaker": "male", "text": f"{clean_topic} mein raw ingestion aur query serving ke beech contention hoti hai — aao iske internal stages decode karte hain."},
                ],
                "narration": f"{clean_topic} mein production architecture design karte waqt sabse badi limitation kahan aati hai? {clean_topic} mein raw ingestion aur query serving ke beech contention hoti hai — aao iske internal stages decode karte hain.",
                "visual_type": "hero_hook",
                "visual_data": {
                    "badge": "ARCHITECTURE QUESTION",
                    "title": clean_topic,
                    "question": f"Core Architectural Choice in {clean_topic}",
                    "left_pill": "Naive Pattern",
                    "right_pill": "Production Pattern",
                    "stat_badge": "System Design Breakdown",
                },
            },
            {
                "scene_id": 2,
                "role": "architecture",
                "scene_tone": DUAL_TONE_KEY,
                "dialogue": [
                    {"speaker": "female", "text": "High concurrency requests handle karte waqt data pipeline aur storage layer kaise sync rehte hain?"},
                    {"speaker": "male", "text": f"{clean_topic} mein requests directly DB lock nahi karte; edge routing, async buffer, state engine, aur replicated storage 4 stages mein chalte hain."},
                ],
                "narration": f"High concurrency requests handle karte waqt data pipeline aur storage layer kaise sync rehte hain? {clean_topic} mein requests directly DB lock nahi karte; edge routing, async buffer, state engine, aur replicated storage 4 stages mein chalte hain.",
                "visual_type": "architecture_flow",
                "visual_data": {
                    "badge": "SYSTEM ARCHITECTURE",
                    "title": f"{clean_topic} Flow",
                    "nodes": [
                        {"id": "in", "label": "Edge Router", "sub": "Rate limit & validation", "edge": "Buffer", "color": "#38BDF8"},
                        {"id": "buf", "label": "Async Queue", "sub": "Burst smoothing", "edge": "Compute", "color": "#818CF8"},
                        {"id": "core", "label": f"{clean_topic[:18]} Engine", "sub": "Lock-free processing", "edge": "Commit", "color": "#FBBF24"},
                        {"id": "out", "label": "Synced Store", "sub": "Consistent replication", "color": "#34D399"},
                    ],
                    "footer": "Ingress -> Async Queue -> Engine -> Consistent Store",
                },
            },
            {
                "scene_id": 3,
                "role": "tradeoff",
                "scene_tone": DUAL_TONE_KEY,
                "dialogue": [
                    {"speaker": "female", "text": "Is architecture ke main performance trade-offs aur reliability guarantees kya hain?"},
                    {"speaker": "male", "text": "Latency 10x kam hoti hai, lekin bounded queues, idempotency keys aur retry safeguards enforce karna zaroori hai."},
                ],
                "narration": "Is architecture ke main performance trade-offs aur reliability guarantees kya hain? Latency 10x kam hoti hai, lekin bounded queues, idempotency keys aur retry safeguards enforce karna zaroori hai.",
                "visual_type": "split_comparison",
                "visual_data": {
                    "badge": "ARCHITECTURE TRADE-OFFS",
                    "title": "Trade-Off Comparison",
                    "left_label": "UNBOUNDED",
                    "left_points": ["Memory growth", "Duplicate retries", "High P99 tail latency", "Cascade failures"],
                    "right_label": "GUARDED DESIGN",
                    "right_points": ["Bounded queues", "Idempotency keys", "Low P99 latency", "Circuit breakers"],
                },
            },
            {
                "scene_id": 4,
                "role": "cta",
                "scene_tone": DUAL_TONE_KEY,
                "dialogue": [
                    {"speaker": "female", "text": "Toh production deployment ke liye final architectural takeaway kya rahega?"},
                    {"speaker": "male", "text": f"{clean_topic} ke liye decoupled ingestion, clear schema governance aur bounded concurrency hi key design principles hain."},
                ],
                "narration": f"Toh production deployment ke liye final architectural takeaway kya rahega? {clean_topic} ke liye decoupled ingestion, clear schema governance aur bounded concurrency hi key design principles hain.",
                "visual_type": "concept_cards",
                "visual_data": {
                    "badge": "KEY TAKEAWAYS",
                    "title": f"{clean_topic} Summary",
                    "bullets": [
                        "Decouple ingestion from serving path",
                        "Preserve schema governance & durability",
                        "Enforce bounded queues & idempotency",
                        "Measure P95/P99 latency under load",
                    ],
                    "footer_cta": "Production Architecture Blueprint",
                },
            },
        ]
        return {
            "title": clean_topic,
            "topic_category": "system_design",
            "art_style": "sapphire_3d",
            "scenes": dual_scenes,
        }

    if is_marathi:
        narrs = [
            (f"{clean_topic} मध्ये production scale वर मुख्य architectural bottleneck कुठे तयार होतो ते समजून घेऊया.", f"{clean_topic} madhe production scale var mukhya architectural bottleneck kuthe tayar hoto te samjun gheuya."),
            (f"{clean_topic} चे core architecture तीन स्पष्ट stages मध्ये काम करते — request routing, state sync, आणि fast execution.", f"{clean_topic} che core architecture teen spashta stages madhe kaam karte — request routing, state sync, ani fast execution."),
            (f"याचा मुख्य trade-off म्हणजे latency 50% कमी होते, पण edge cases साठी proper backpressure limits आवश्यक असतात.", f"Yacha mukhya trade-off mhanje latency 50% kami hote, pan edge cases saathi proper backpressure limits avashyak astat."),
            (f"{clean_topic} मध्ये decoupled execution आणि clear observability मुळे system reliable राहते.", f"{clean_topic} madhe decoupled execution ani clear observability mule system reliable rahte."),
        ]
    elif is_hindi:
        narrs = [
            (f"{clean_topic} में production scale पर मुख्य architectural bottleneck कहां आता है, आइए समझते हैं।", f"{clean_topic} mein production scale par mukhya architectural bottleneck kahan aata hai, aaiye samajhte hain."),
            (f"{clean_topic} की architecture 3 clear stages में चलती है — fast ingestion, core engine processing, और reliable storage sync.", f"{clean_topic} ki architecture 3 clear stages mein chalti hai — fast ingestion, core engine processing, aur reliable storage sync."),
            (f"इसका real trade-off यह है कि latency 10x कम होती है, लेकिन edge cases के लिए retry और limits ज़रूरी हैं।", f"Iska real trade-off yeh hai ki latency 10x kam hoti hai, lekin edge cases ke liye retry aur limits zaroori hain."),
            (f"{clean_topic} में decoupled queues और schema governance system को stable रखते हैं।", f"{clean_topic} mein decoupled queues aur schema governance system ko stable rakhte hain."),
        ]
    else:
        narrs = [
            (f"Let's break down the core architectural bottleneck in {clean_topic} under production scale.", ""),
            (f"{clean_topic} works in 3 clean stages: request routing, in-memory processing, and resilient state sync.", ""),
            (f"The real trade-off: latency drops by 10x, while bounded backpressure and limits protect edge cases.", ""),
            (f"Decoupled execution and clear governance keep {clean_topic} predictable at scale.", ""),
        ]

    scenes = [
        {
            "scene_id": 1,
            "role": "hook",
            "scene_tone": resolve_effective_tone(tone, role="hook", idx=0),
            "narration": narrs[0][0],
            **({"narration_hinglish": narrs[0][1]} if narrs[0][1] else {}),
            "visual_type": "hero_hook",
            "visual_data": {
                "badge": "INTERVIEW TRAP",
                "title": clean_topic,
                "question": f"Why does {clean_topic} fail at scale?",
                "left_pill": "Naive Approach",
                "right_pill": "Production Pattern",
                "stat_badge": "90% Candidates Miss This",
            },
        },
        {
            "scene_id": 2,
            "role": "architecture",
            "scene_tone": resolve_effective_tone(tone, role="architecture", idx=1),
            "narration": narrs[1][0],
            **({"narration_hinglish": narrs[1][1]} if narrs[1][1] else {}),
            "visual_type": "architecture_flow",
            "visual_data": {
                "badge": "SYSTEM TOPOLOGY",
                "title": f"{clean_topic} Pipeline",
                "nodes": [
                    {"id": "in", "label": "Client Requests", "sub": "Auth & Edge Routing", "edge": "Route", "color": "#38BDF8"},
                    {"id": "buf", "label": "In-Memory Queue", "sub": "Batch & Backpressure", "edge": "Process", "color": "#818CF8"},
                    {"id": "core", "label": f"{clean_topic[:18]} Core", "sub": "Fast State Engine", "edge": "Persist", "color": "#FBBF24"},
                    {"id": "out", "label": "Persistent Store", "sub": "Consistent Replica Sync", "color": "#34D399"},
                ],
                "footer": "Ingress -> Queue -> Compute -> Persistent Sync",
            },
        },
        {
            "scene_id": 3,
            "role": "tradeoff",
            "scene_tone": resolve_effective_tone(tone, role="tradeoff", idx=2),
            "narration": narrs[2][0],
            **({"narration_hinglish": narrs[2][1]} if narrs[2][1] else {}),
            "visual_type": "split_comparison",
            "visual_data": {
                "badge": "TRADE-OFFS & FIX",
                "title": "Latency vs Reliability",
                "left_label": "UNOPTIMIZED",
                "left_points": ["Blocking lock contention", "High P99 tail latency", "Cascade retry failures", "Unbounded memory growth"],
                "right_label": "PRODUCTION FIX",
                "right_points": ["10x lower P99 latency", "Bounded backpressure queues", "Idempotent circuit breaker", "Graceful edge fallback"],
            },
        },
        {
            "scene_id": 4,
            "role": "cta",
            "scene_tone": resolve_effective_tone(tone, role="cta", idx=3),
            "narration": narrs[3][0],
            **({"narration_hinglish": narrs[3][1]} if narrs[3][1] else {}),
            "visual_type": "concept_cards",
            "visual_data": {
                "badge": "KEY TAKEAWAYS",
                "title": f"{clean_topic} Checklist",
                "bullets": [
                    "Measure bottlenecks: Profile P95/P99 before optimizing",
                    "Protect edges: Set strict timeouts & bounded retries",
                    "Eliminate locks: Isolate hot paths into async stages",
                    "Verify in staging: Replay traffic spikes safely",
                ],
                "footer_cta": "Save • Share • Comment Next Topic",
            },
        },
    ]
    return {
        "title": clean_topic,
        "topic_category": "system_design",
        "art_style": "sapphire_3d",
        "scenes": scenes,
    }


def _extract_json(text: str) -> Dict[str, Any]:
    """Extracts a JSON object reliably from raw, reasoning-wrapped, or truncated LLM output."""
    if not text:
        return {}
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    # Handle unclosed <think> if model hit output limit before </think>, keeping any JSON portion after it
    if "<think>" in cleaned.lower() and "</think>" not in cleaned.lower():
        brace_after = cleaned.find('{"')
        if brace_after != -1:
            cleaned = cleaned[brace_after:]

    candidates: List[str] = []
    # 1. Outermost braces (immune to inner triple backticks inside code_snippet fields)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(cleaned[start:end + 1])

    # 2. Markdown fenced block fallback
    fenced = re.search(r"```(?:json)?\s*([\s\S]*)\s*```", cleaned)
    if fenced:
        candidates.append(fenced.group(1).strip())
    candidates.append(cleaned)

    for cand in candidates:
        for strict_flag in (True, False):
            try:
                parsed = json.loads(cand, strict=strict_flag)
                if isinstance(parsed, dict) and parsed:
                    return parsed
            except Exception:
                pass
        no_trailing = re.sub(r",\s*([}\]])", r"\1", cand)
        try:
            parsed = json.loads(no_trailing, strict=False)
            if isinstance(parsed, dict) and parsed:
                return parsed
        except Exception:
            pass

    # 3. Truncated JSON scene recovery (salvages completed scenes from 2k-6k char partial outputs)
    salvaged = _salvage_scenes_from_truncated_json(cleaned)
    if salvaged and salvaged.get("scenes"):
        return salvaged
    return {}

def generate_viral_meta(
    topic: str,
    timeline: Optional[Dict[str, Any]] = None,
    channel_tag: str = "@Code_With_Mangesh"
) -> Dict[str, Any]:
    """
    Generates high-engagement YouTube Shorts & Instagram Reels titles, description, and hashtags.
    """
    cleaned_topic = topic.strip()
    tag_name = channel_tag.lstrip("@").replace(" ", "")
    
    # Extract scene summaries if available
    script_points = []
    if timeline and isinstance(timeline, dict) and "scenes" in timeline:
        for idx, sc in enumerate(timeline["scenes"]):
            v_title = sc.get("visual_data", {}).get("title") or sc.get("narration", "")[:60]
            if v_title:
                script_points.append(f"• Scene {idx+1}: {v_title}")
    
    # 1. Try Gemini LLM for dynamic tailored generation
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""You are a viral YouTube Shorts and Instagram Reels growth strategist.
Create high-conversion metadata for a vertical tech explainer video.
Topic: "{cleaned_topic}"
Channel: {channel_tag}
Key Breakdown:
{chr(10).join(script_points[:4]) if script_points else "Production architecture & system design deep dive"}

Return ONLY a valid JSON object matching this schema:
{{
  "titles": [
    "🔥 Viral Catchy Title 1 (Punchy, under 60 chars)",
    "⚡ High-CTR Title 2 (Curiosity or trade-off)",
    "🧠 Interview / System Design Title 3"
  ],
  "hook": "2-line engaging hook description explaining the core problem and why it matters.",
  "takeaways": [
    "Key engineering insight or architectural trade-off",
    "Production-level mechanism or query optimization",
    "How to prevent bottlenecks or downtime"
  ],
  "hashtags": [
    "#{tag_name}", "#CodeWithMangesh", "#SystemDesign", "#SoftwareEngineering"
  ]
}}
"""
            for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.5-flash"]:
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    raw_text = res.text.strip() if hasattr(res, "text") and res.text else ""
                    parsed = _extract_json(raw_text)
                    if parsed and "titles" in parsed and "hashtags" in parsed:
                        titles = parsed.get("titles", [])
                        hook = parsed.get("hook", f"Ever wondered how {cleaned_topic} works in production?")
                        takeaways = parsed.get("takeaways", [])
                        tags = parsed.get("hashtags", [])
                        
                        # Ensure channel hashtag is present
                        if f"#{tag_name}" not in tags:
                            tags.insert(0, f"#{tag_name}")
                        if "#CodeWithMangesh" not in tags:
                            tags.insert(1, "#CodeWithMangesh")
                        
                        full_text = (
                            f"{titles[0] if titles else cleaned_topic}\n\n"
                            f"📌 {hook}\n\n"
                            f"Key Engineering Takeaways:\n"
                            + "\n".join([f"✅ {t}" for t in takeaways]) + "\n\n"
                            f"🚀 Follow {channel_tag} for daily System Design & Coding breakdowns!\n"
                            f"💾 Save this reel so you have it ready for your next tech interview!\n\n"
                            + " ".join(tags)
                        )
                        return {
                            "titles": titles,
                            "hook": hook,
                            "takeaways": takeaways,
                            "hashtags": tags,
                            "full_text": full_text
                        }
                except Exception:
                    continue
        except Exception:
            pass

    # 2. Resilient Fallback Template Engine
    safe_topic = cleaned_topic.title()
    titles = [
        f"🔥 {safe_topic} Explained Like a Staff Engineer!",
        f"⚡ Why 99% of Developers Get {safe_topic} Wrong!",
        f"🧠 {safe_topic}: Zero Downtime Architecture Blueprint"
    ]
    hook = f"Here is the complete architectural breakdown of {safe_topic} with zero fluff and real production trade-offs."
    takeaways = [
        f"Core internal mechanism behind {safe_topic}",
        "Trade-offs between latency, throughput, and operational complexity",
        "How senior engineers implement this pattern in production"
    ]
    
    words = re.findall(r"[A-Za-z0-9]+", cleaned_topic)
    topic_tags = [f"#{w.capitalize()}" for w in words if len(w) > 2][:6]
    base_tags = [
        f"#{tag_name}",
        "#CodeWithMangesh",
        "#SystemDesign",
        "#SoftwareEngineering",
        "#CloudComputing",
        "#Coding",
        "#Programming",
        "#DevCommunity",
        "#BackendEngineering",
        "#TechReels",
        "#ComputerScience",
        "#WebDevelopment",
        "#Python",
        "#Database",
        "#DevOps",
        "#TechInterview",
        "#FullStack",
        "#LearnToCode",
        "#DataEngineering",
        "#Microservices"
    ]
    all_tags = list(dict.fromkeys(topic_tags + base_tags))
    
    full_text = (
        f"{titles[0]}\n\n"
        f"📌 {hook}\n\n"
        f"Key Engineering Takeaways:\n"
        + "\n".join([f"✅ {t}" for t in takeaways]) + "\n\n"
        f"🚀 Follow {channel_tag} for daily System Design, Cloud & Architecture deep dives!\n"
        f"💾 Save this reel for your next technical interview.\n\n"
        + " ".join(all_tags)
    )
    return {
        "titles": titles,
        "hook": hook,
        "takeaways": takeaways,
        "hashtags": all_tags,
        "full_text": full_text
    }
