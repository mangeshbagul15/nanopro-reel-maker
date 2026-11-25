import json
import re
from typing import Dict, Any, Optional, List, Tuple
from core.config import GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, MISTRAL_API_KEY, OUTPUT_DIR

VISUAL_HISTORY_PATH = OUTPUT_DIR / "visual_history.json"

# Compatible geometry families across ALL_STUDIO_LAYOUTS (Core 103 + Pro 104 + IT/SDLC 105 + Domain 360 + Grammar 56)
_DIVERSE_LAYOUT_FAMILIES: Dict[str, Tuple[str, ...]] = {
    "hook": (
        "hero_hook", "custom_scene", "cap_theorem_triangle", "incident_radar", "alert_diagram",
        "kinetic_statement", "grammar:grid:2x2", "grammar:bento:4", "grammar:quadrant:2x2",
        "checklist_scorecard", "pacelc_tradeoff", "venn_overlap", "incident_thundering_herd",
        "incident_split_brain", "chaos_monkey_fault_inj", "dora_metrics_four_keys",
    ),
    "flow": (
        "architecture_flow", "iso_architecture", "cdc_debezium_flow", "etl_elt_pipeline", "outbox_pattern_cdc",
        "saga_orchestration", "step_timeline", "roadmap_wave", "cicd_pipeline_stages", "sequence_diagram",
        "lsm_tree_compaction", "write_ahead_log_wal", "rate_limiter_token_bucket", "idempotency_key_store",
        "strangler_fig_migration", "event_sourcing_snapshots", "rag_chunk_overlap_pipe", "llm_tokenization_bpe",
        "browser_critical_path", "payment_idempotent_retry", "kalman_sensor_fusion", "flink_watermarks_window",
        "grammar:flow:4", "grammar:flow:5", "grammar:chevron:4", "grammar:swimlane:3", "grammar:timeline_v:4",
    ),
    "hub": (
        "circular_hub_mesh", "node_graph", "consistent_hashing_ring", "raft_leader_election",
        "circuit_breaker_states", "epoll_event_loop", "gossip_protocol_cluster", "sdlc_cycle_wheel",
        "sharding_hash_range", "hexagonal_ports_adapters", "radar_spider", "agent_react_tool_loop",
        "mcp_client_host_server", "multi_agent_supervisor", "service_mesh_envoy_proxy", "ros2_dds_pubsub",
        "grammar:ring:5", "grammar:hub:4", "grammar:orbit:4",
    ),
    "tiers": (
        "layer_stack_3d", "pyramid_hierarchy", "l1_l2_l3_cache_tiers", "osi_7_layers", "medallion_lakehouse",
        "docker_cgroups_namespaces", "hnsw_vector_graph", "clean_architecture_rings", "tree_hierarchy",
        "b_plus_tree_pages", "merkle_tree_proof", "k8s_pod_scheduling", "iceberg_snapshot_tables",
        "llm_guardrails_safety", "pci_dss_token_vault", "quic_http3_0rtt", "tls_13_handshake",
        "grammar:tiers:4", "grammar:pyramid:4", "grammar:funnel:4", "grammar:tree:3", "grammar:ladder:4",
    ),
    "compare": (
        "split_comparison", "iso_comparison", "code_diff_split", "hybrid_merge", "pacelc_tradeoff",
        "process_thread_context", "index_seek_vs_scan", "dma_zero_copy_io", "matrix_2x2",
        "monolith_modular_vs_micro", "bfs_dfs_traversal", "venn_overlap", "compare_sync_vs_async",
        "compare_rest_vs_grpc", "llm_prefill_vs_decode", "optimistic_vs_zk_rollup",
        "grammar:dual:vs", "grammar:dual:tradeoff", "grammar:grid:3x2",
    ),
    "metrics": (
        "benchmark_chart", "benchmark_3d", "metric_gauge_hud", "radial_gauge", "latency_waterfall",
        "flamegraph_perf", "funnel_metrics", "stat_grid_2x2", "line_area_chart", "donut_3d",
        "pareto_frontier_plot", "box_whisker_latency", "slo_burn_rate_gauge", "big_o_complexity_curves",
        "gauge_slo_availability", "benchmark_throughput_ops", "grammar:waterfall:5",
    ),
    "code": (
        "code_terminal", "terminal_studio", "sql_table", "sql_studio", "data_structure_memory",
        "memory_lanes", "api_request_response", "er_schema", "columnar_parquet_blocks",
        "isolation_levels_matrix", "jwt_header_payload_sig", "memory_ring_buffer", "memory_lsm_memtable",
        "sql_window_partition", "sql_covering_index", "diff_n_plus_one_fix", "grammar:slots:5", "grammar:table:4x4",
    ),
    "summary": (
        "concept_cards", "checklist_scorecard", "kinetic_statement", "hybrid_merge",
        "step_timeline", "grammar:grid:2x2", "grammar:bento:5", "pyramid_hierarchy",
        "rfc_adr_decision_log", "checklist_prod_readiness", "checklist_sql_tuning",
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
    _push_unique("recent_art_styles", [str(timeline.get("art_style") or "")], 14)
    _push_unique(
        "recent_visual_types",
        [str((sc.get("visual_data") or {}).get("_intent") or sc.get("visual_type") or "") for sc in scenes if isinstance(sc, dict)],
        28,
    )
    _push_unique("recent_backdrops", [str(sc.get("backdrop") or "") for sc in scenes if isinstance(sc, dict)], 12)
    _push_unique("recent_transitions", [str(sc.get("transition") or "") for sc in scenes if isinstance(sc, dict)], 10)
    _push_unique("recent_text_fx", [str(sc.get("text_fx") or "") for sc in scenes if isinstance(sc, dict)], 10)

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
1. PERFECT VOICE & VISUAL CORRESPONDENCE (MANDATORY):
   - In EVERY scene, the `visual_data` MUST DIRECTLY and PRECISELY reflect the exact technical concept, architecture, code, schema, or system component being spoken in that scene's `narration`.
   - Never output generic placeholder text (e.g., "Client Ingestion", "Block #101", "Pipeline logic"). Use the REAL service names, REAL SQL queries, REAL code syntax, REAL performance metrics, and REAL architecture components relevant to the user's specific prompt.
   - What the viewer SEES on the screen must match 100% with what the narrator is SAYING at that exact moment.

2. DURATION & SCENE FLOW (ZERO ARTIFICIAL 60-SECOND LIMIT):
   - The video should naturally cover the depth required for the topic.
   - For short overviews: 3 to 4 focused scenes.
   - For standard / detailed explainers: 4 to 6 scenes.
   - For comprehensive deep-dives: 6 to 8 scenes.
   - Each scene should have a clear purpose: Hook / Problem -> Architecture / System Design -> Internal Mechanism / Code / Data Flow -> Resolution / Trade-offs / Takeaway.

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
  "total_target_seconds": 60,
  "scenes": [
    {
      "scene_id": 1,
      "role": "hook",
      "scene_tone": "fireship_octane / dramatic_performance / staff_engineer / conversational_casual / interview_prep",
      "narration": "Narration text with natural pauses...",
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
    "studio_300_domain": (
        "UNLIMITED STUDIO MAX + ZERO-TEMPLATE HYBRID ENGINE (OPTION 1 + OPTION 2 COMBINED — 670+ DOMAIN LAYOUTS + 56 GRAMMAR + 54 OPTION 1 WEBGL/SVG/SPATIAL): "
        "Mix bespoke zero-template scenes (`web_scene`, `svg_scene`, `spatial_canvas` with `visual_data.option1_archetype`) AND specialized 670+ Domain Layouts across every scene! NEVER use the same layout twice in one reel!\n"
        "1. COLOR WORLDS: Any of 46 curated worlds (`obsidian_studio`, `sapphire_3d`, `aurora_borealis`, `synthwave_84`, `studio_white`, `emerald_matrix`, `cobalt_blueprint`, `midnight_gold`, etc.) OR `#HEX`.\n"
        "2. BACKDROP, TRANSITION & TEXT FX: Vary `backdrop` (18 styles), `transition` (12 styles), and `text_fx` (14 styles) per scene.\n"
        "3. USE DIVERSE VISUAL TYPES ACROSS SCENES (populate rich schema fields for whichever you pick!):\n"
        "   - Zero-Template Custom (54+ archetypes): `web_scene`, `svg_scene`, `spatial_canvas` (`elements` 0..1000 + `connections`).\n"
        "   - 670+ Domain & Pro/IT Layouts: NEVER fall back to bare `alert_diagram` without `alerts`! Populate `nodes`/`stages`/`items` (with `icon` like `'postgres'`, `'aws_rds'`, `'kafka'`, `'docker'`, `'kubernetes'`, `'router'`, `'server'` & `shape` like `'server_rack'`, `'router'`, `'network_switch'`, `'laptop'`, `'database_cluster'`). Examples: `cdc_debezium_flow`, `iceberg_snapshot_tables`, `k8s_pod_scheduling`, `transformer_self_attn`, `mcp_tool_bridge`, `quic_http3_0rtt`, `rag_chunk_overlap_pipe`, `double_entry_ledger`, `ros2_dds_pubsub`, `medallion_lakehouse`, `consistent_hashing_ring`, `raft_leader_election`, `circuit_breaker_states`, `write_ahead_log_wal`, `mesh_3d_stage`, `sequence_diagram`, `benchmark_3d`.\n"
        "   - Composable Diagram Grammar (56+ presets): `grammar:grid:3x2`, `grammar:flow:5`, `grammar:ring:6`, `grammar:bento:5`, `grammar:swimlane:3`, `grammar:chevron:4`, `grammar:pyramid:4`, `grammar:funnel:4`, `grammar:quadrant:2x2`.\n"
        "4. Populate `scene_tone` & 4 `choreography.triggers` per scene."
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

TONE_DIRECTIVES = {
    "trusted_dost_guide": (
        "TRUSTED DOST, HAPPY CURIOUS HINGLISH & PEACEFUL GUIDE MANDATE: "
        "Speak with a happy, deeply human, curious Hinglish voice — like a trusted best friend (`dost / yaar`), peaceful guide, and supportive problem solver who genuinely understands the viewer's mindset and walks through every intuition step warmly ('Aao dost, is concept ko ekdam simple aur clear tarike se decode karte hain!'). "
        "STRICT DIALOG RULE: NEVER use repetitive cliché reassurance phrases or filler sympathy — express warmth purely through genuine curiosity, encouraging clarity, and collaborative storytelling instead!\n"
        "1. 00:00 CLEVER SECRET / SHORTCUT HOOK: Open Scene 1 immediately with an exciting, curious secret or smart engineering shortcut ('Ek chhota sa secret shortcut bataun jo 90% log miss kar dete hain?... [pause]').\n"
        "2. NATURAL Q&A CLARITY CHECKS: Check concept clarity through natural, conversational friend-like Q&A ('Ab socho agar 10,000 requests ek saath aayein toh kya hoga? [pause] Simple hai dost — yahan ek smart pattern kaam aata hai!').\n"
        "3. ENJOYABLE VISIONARY FLOW + PROGRESSIVE VISUAL SYNC: Build an uplifting, enjoyable, visionary momentum from curiosity -> clarity -> mastery without skipping any step. Populate rich progressive cards/flows/diagrams and 4 exact `choreography.triggers` per scene so visuals light up in tight lockstep with your words. Set each scene's `scene_tone` to `trusted_dost_guide`."
    ),
    "purposeful_hinglish_mentor": (
        "PURPOSEFUL HINGLISH MENTOR ('MUST UNDERSTAND' CLARITY + EDGE CASES) MANDATE: "
        "Speak with a warm, authoritative yet approachable Hinglish male mentor voice delivered at a slightly brisk, purposeful pace that stays crystal clear and ensures the viewer genuinely understands every concept ('must understand'). "
        "Write `narration` in clean Roman Hinglish mixed naturally with crisp English technical terms and ASCII numbers, using brief intentional pauses (`...` / `[pause]`) only for rhetorical weight so pacing stays tight and cohesive.\n"
        "1. 00:00 SHARP INTERVIEW-TRAP / REAL-WORLD HOOK (Scene 1): Open immediately at 00:00 with a concrete interview trap or production failure scenario (e.g., 'Interview mein jab puchte hain ki 100K RPS par connection pool kyun choke hota hai... [pause] 85% engineers yahin galti karte hain!').\n"
        "2. ZERO-SKIP STEP-BY-STEP MECHANICS (Middle Scenes): Explain every essential step, internal data flow, and mental model clearly from A to B without jumping steps, seamlessly bridging each scene's conclusion into the next scene's visual transition.\n"
        "3. EDGE CASES, TRADE-OFFS & PRACTICAL FIX (Deep Scene -> Close): Explicitly break down edge cases, latency/cost/memory trade-offs, and an actionable production fix (`split_comparison`, `code_diff_split`, `sql_studio`, or domain diagrams) so the viewer walks away with complete mastery.\n"
        "4. TIGHT VISUAL SYNC: Populate 4 exact `choreography.triggers` per scene synced to key spoken terms, matching progressive diagrams, highlights, and transitions from start to finish. Set each scene's `scene_tone` to `purposeful_hinglish_mentor`."
    ),
    "senior_hinglish_mentor": (
        "SENIOR HINGLISH MENTOR & TECHNICAL STORYTELLER MANDATE: "
        "Adopt a warm, brisk yet crisp conversational Hinglish persona with a confident senior-engineer/mentor vibe and natural crisp English tech terms (`latency`, `throughput`, `race condition`, `index`, `cache invalidation`, `trade-off`). "
        "Unless the selected Voice Persona explicitly specifies Devanagari Hindi/Marathi or pure English, write `narration` in natural, clean conversational Hinglish (Roman script + crisp English technical terms, with tight intentional `...` / `[pause]` breath cues). "
        "FOLLOW THIS EXACT 4-ACT STORY ARC ACROSS SCENES:\n"
        "1. 00:00 HOOK (Scene 1): Start immediately with a crisp interview-trap or real-world production problem hook (e.g., 'Interview mein 90% log yahin phaste hain... [pause] ek simple query production DB ko kaise freeze kar sakti hai?').\n"
        "2. BRISK STEP-BY-STEP WALKTHROUGH (Middle Scenes): Move seamlessly into a crisp, step-by-step walkthrough with smooth scene-to-scene connectors using progressive UI cards, animated diagrams/flow chains, and crisp key-term emphasis.\n"
        "3. CANDID ANALYTICAL TRADE-OFFS & FIXES (Pre-Closing / Deep Scene): Cover real trade-offs, edge cases, and practical fixes cleanly (`split_comparison`, `data_structure_memory`, `code_terminal`, or `benchmark_chart`).\n"
        "4. FRIENDLY DIRECT CTA (Final Scene): End cleanly with a direct CTA ('Save this reel for your next interview aur comment karo apna next topic!').\n"
        "CRITICAL SYNC: Populate 4 exact `choreography.triggers` matching key spoken terms per scene so progressive UI cards & diagrams emphasize each concept in tight lockstep, and set each scene's `scene_tone` to `senior_hinglish_mentor`."
    ),
    "youth_friend_turbo": (
        "YOUTH DOST, ENERGETIC Q&A DETAILER & BALANCED SYNC EXPLAINER MANDATE (COMPLETE + ZERO RUSH/SKIP): "
        "Speak like a smart, energetic young friend (`dost / yaar`) delivering an engaging story-driven tech breakdown — lively, crystal clear, relatable, and complete with zero rushed truncation or skipped ideas!\n"
        "1. STRUCTURED FRIENDLY Q&A IN EVERY SCENE: Open scenes with a crisp relatable question ('Socho zara — ek saath 10,000 requests aane par checkout slow kyun padta hai?'), insert ONE clean breath beat ('... [pause]'), then deliver the full step-by-step answer and concrete internals (`WAL`, `lsn`, exact latency ms, tradeoffs) clearly.\n"
        "2. COMPLETE SENTENCES & SMOOTH SCENE BRIDGES (ZERO GHAI-GADBAD): Never compress too many disconnected buzzwords into one rushed breath! Use smooth, complete 12-16 word conversational sentences with explicit scene transitions ('Ab yahan asli magic shuru hota hai -> let's trace step 2!') so voice, visuals, effects, and karaoke finish cleanly together.\n"
        "3. FULL VISUAL SYNC: Populate 4 balanced visual items (`nodes`, `stages`, `bars`, `entries`, `bullets`) + 4 exact `choreography.triggers` spaced evenly across the sentence timings so zero cards or words ever skip.\n"
        "Set each scene's `scene_tone` to `youth_friend_turbo`."
    ),
    "mentor_storyteller": (
        "STUDENT-BOND MENTOR & EXCITING STORYTELLING MANDATE: Speak directly to one curious student like their favorite energetic mentor — warm, simple, electric, and deeply intuitive! "
        "1. SIMPLE HUMAN LANGUAGE: Zero stiff textbook jargon. Explain concepts with everyday relatable analogies and speak directly ('you', 'socho zara', 'लक्षात घ्या') as if sitting right beside the listener. "
        "2. INTENTIONAL BREATH PAUSES (`...` / `[pause]`): Build curiosity, then insert 1-2 short natural breathing pauses (`...`) RIGHT BEFORE revealing the core twist or 'aha!' insight so the learner absorbs why it matters before hearing the answer (e.g., 'Wait... why did everything freeze? [pause] Look closely—every user was waiting on a single lock!'). "
        "3. INFECTIOUS EXCITEMENT & BONDING: Sound genuinely excited when the concept clicks ('Boom—latency drops 10x!', 'And here is the magic part!'). Keep sentences rhythmic, punchy, and human. "
        "Set each scene's `scene_tone` to `mentor_storyteller` and compose engaging progressive visuals (`custom_scene`, `iso_architecture`, `step_timeline`, `kinetic_statement`)."
    ),
    "auto_dynamic": (
        "DYNAMIC PER-SCENE TONE & VOICE CHOREOGRAPHY (RECOMMENDED): "
        "Dynamically shift emotional tone & pacing across the video storyboard: "
        "Hook/Intro -> energetic (`fireship_octane` or `interview_prep`), Problem/Mistake -> suspenseful (`dramatic_performance`), "
        "Architecture/Mechanism -> authoritative (`staff_engineer`), Closing Summary/CTA -> warm (`conversational_casual`). "
        "Set each scene's `scene_tone` field accordingly so both TTS voice prosody AND visual motion/subtitle energy adapt per scene!"
    ),
    "fireship_octane": (
        "SCRIPT TONE & VISUAL SYNC MANDATE: Write in high-octane Fireship style. "
        "Punchy sentences, witty comparisons, rapid pacing, zero corporate throat-clearing. "
        "Set each scene's `scene_tone` to `fireship_octane` and prefer fast kinetic visuals (`kinetic_statement`, `split_comparison`, `code_terminal`, `hero_hook`)."
    ),
    "dramatic_performance": (
        "SCRIPT TONE & VISUAL SYNC MANDATE: Emotionally rich, theatrical, dramatic performance. "
        "Build tension and suspense around the problem. Use natural dramatic pauses ('...') before revealing key insights. "
        "Set each scene's `scene_tone` to `dramatic_performance` and use high-drama themes (`crimson_alert`, `gold_purple`) and dramatic story visuals (`alert_diagram`, `hero_hook`, `kinetic_statement`, `hybrid_merge`)."
    ),
    "staff_engineer": (
        "SCRIPT TONE & VISUAL SYNC MANDATE: Senior Staff Engineer / ByteByteGo masterclass style. "
        "Calm, deeply authoritative, mature technical confidence focusing on real-world trade-offs and internals. "
        "Set each scene's `scene_tone` to `staff_engineer` and prefer structured diagrams (`step_timeline`, `architecture_flow`, `all_in_one_tech_canvas`, `data_structure_memory`)."
    ),
    "conversational_casual": (
        "SCRIPT TONE & VISUAL SYNC MANDATE: Conversational, warm, and friendly, like explaining over coffee. "
        "Set each scene's `scene_tone` to `conversational_casual` and use approachable `emerald_matrix`/`cyber_cyan` visuals (`concept_cards`, `step_timeline`, `hybrid_merge`)."
    ),
    "interview_prep": (
        "SCRIPT TONE & VISUAL SYNC MANDATE: High-stakes FAANG Technical Interview Prep. "
        "Clear interview question hook, candidate traps, crisp trade-offs, and a 30-second crisp answer. "
        "Set each scene's `scene_tone` to `interview_prep` and use interview-aligned visuals (`hero_hook`, `split_comparison`, `concept_cards`, `hybrid_merge`)."
    )
}

def generate_timeline(
    topic: str,
    tone: str = "conversational",
    engine_style: str = "hybrid_modern",
    duration_mode: str = "auto",
    custom_style_prompt: str = "",
    voice: str = "en-US-ChristopherNeural",
    format_ratio: str = "9:16",
    visual_history: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini/Groq/OpenRouter models,
    maintaining persistent visual history for Option 1, Option 2, and Combined engines so
    every click produces distinct layouts, palettes, shaders, and compositions.
    """
    hist = load_visual_history(visual_history)
    run_num = int(hist.get("run_count", 0)) + 1
    _DIVERSE_ENGINES = (
        "studio_domain_library", "pure_zero_template", "studio_300_domain",
        "dual_generative", "cinematic_studio", "auto_dynamic", "hybrid_modern",
    )
    if engine_style == "custom_user_style" and custom_style_prompt.strip():
        style_directive = (
            f"MANDATORY CUSTOM STYLE DIRECTIVE: The user explicitly requested this custom visual aesthetic: "
            f"'{custom_style_prompt.strip()}'. You MUST tailor your visual_type and visual_data to reflect this custom design aesthetic across all scenes."
        )
    else:
        style_directive = ENGINE_STYLE_DIRECTIVES.get(engine_style, ENGINE_STYLE_DIRECTIVES["auto_dynamic"])
    
    # 1. Language & Dialect based on the selected Voice Persona
    if voice.endswith("|hinglish") or voice == "en-IN-NeerjaExpressiveNeural":
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
    elif tone in ("senior_hinglish_mentor", "purposeful_hinglish_mentor", "trusted_dost_guide", "youth_friend_turbo"):
        lang_directive = (
            f"LANGUAGE & DIALECT MANDATE ({tone}): Write the spoken `narration` in warm, clear, deeply human conversational Hinglish "
            "using clean LATIN / ROMAN letters mixed naturally with crisp English technical terms and ASCII numbers "
            "(e.g., 'Socho zara yaar... is complex concept ko 30 seconds mein crystal clear decode karte hain!'). "
            "Express warmth through curious, uplifting clarity rather than repetitive reassurance clichés. "
            "Keep all on-screen visual_data (titles, labels, code, queries, badges) in crisp English!"
        )
    elif voice == "en-IN-PrabhatNeural":
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: Write in crisp, authoritative Indian Tech English with high technical clarity."
        )
    else:
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: Write in natural, high-octane conversational tech English (Fireship / ByteByteGo style)."
        )

    # 2. Duration & Depth guidance
    duration_instructions = {
        "auto": "Natural duration based on topic depth (typically 4 to 6 scenes). Completely explain the core architecture and trade-offs.",
        "short": "Quick, punchy overview (EXACTLY 3 scenes, ~30-45 seconds). High-impact summary.",
        "standard": "Standard explainer (4 to 5 scenes, ~60 seconds). Balanced walkthrough.",
        "deep_dive": "Comprehensive in-depth breakdown (6 to 8 scenes, 90 to 180+ seconds). Detail every pipeline stage, internal buffer, and real implementation commands."
    }
    dur_guidance = duration_instructions.get(duration_mode, duration_instructions["auto"])

    # 3. Format & Universal Spoken English Numbers/Dates/Tech Rules
    format_directive = f"Target Aspect Ratio: '{format_ratio}'."
    tone_directive = TONE_DIRECTIVES.get(tone, f"SCRIPT TONE & CADENCE: {tone}.")
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
        # Rotate curated layout suggestions across runs so LLM sees completely fresh templates every click
        all_candidates = [ly for grp in _DIVERSE_LAYOUT_FAMILIES.values() for ly in grp if ly not in avoid_vtypes[-14:]]
        if len(all_candidates) < 10:
            all_candidates = [ly for grp in _DIVERSE_LAYOUT_FAMILIES.values() for ly in grp]
        rot_offset = (run_num * 7) % max(1, len(all_candidates))
        fresh_layout_picks = (all_candidates[rot_offset:] + all_candidates[:rot_offset])[:14]
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
            f"\nFRESH VISUAL VARIATION MANDATE (Generation Run #{run_num} — ZERO REPETITION):\n"
            f"- The user clicked Generate again and expects a COMPLETELY DIFFERENT visual composition, layout geometry, palette, and motion feel from prior videos.\n"
            f"- Use fresh `art_style`: `\"{suggested_world}\"` (AVOID repeating recent styles: {avoid_arts[-8:]}).\n"
            + (
                f"- AVOID reusing recent visual_types {avoid_vtypes[-12:]}! Prefer fresh layouts from this rotation: {fresh_layout_picks}.\n"
                if engine_style in ("studio_domain_library", "studio_300_domain")
                else f"- Design bespoke `web_scene` compositions inspired by `{chosen_paradigm}` and completely avoid recent intents {avoid_vtypes[-8:]}.\n"
            )
            + f"- AVOID repeating recent backdrops {avoid_bds[-6:]}; pick distinct `backdrop`, `transition`, and `text_fx` per scene.\n"
        )

    user_prompt = (
        f"Topic: '{topic}'.\n"
        f"{tone_directive}\n"
        f"Selected Visual Engine: '{engine_style}'.\n"
        f"Selected Voice Persona: '{voice}'.\n"
        f"{lang_directive}\n"
        f"{english_tech_num_rule}\n"
        f"{format_directive}\n"
        f"Target Depth / Duration: {dur_guidance}\n"
        f"{style_directive}\n"
        f"{variety_directive}\n"
        f"MANDATORY REQUIREMENT: For EVERY scene, make sure the visual_data fields (node labels, schemas, table rows, code snippet, bullet points, metrics) "
        f"EXACTLY match and illustrate what the narrator is speaking in that scene's narration. Never use generic or unrelated placeholders.\n"
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
                            clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num)
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
                        clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num)
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
                            clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num)
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
    fallback_tl = _enforce_engine_style(fallback_tl, engine_style, topic, tone=tone, format_ratio=format_ratio, visual_history=hist, run_num=run_num)
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
        if str(sc.get("visual_type", "")).lower().strip() == "web_scene" and not str(vd.get("html") or vd.get("web_code") or "").strip():
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


def _mirror_items_for_domain_layout(v_data: Dict[str, Any], sc: Dict[str, Any], title: str) -> None:
    """Ensures any rotated 320+ Domain / Grammar layout has structured `items` grounded in the scene data."""
    if v_data.get("items") or v_data.get("nodes") or v_data.get("steps") or v_data.get("stages"):
        return
    mirrored: List[Dict[str, Any]] = []
    if v_data.get("satellites"):
        for s in v_data["satellites"][:5]:
            mirrored.append({"name": s.get("name", ""), "sub": s.get("role", ""), "color": s.get("color", "")})
    elif v_data.get("left_points") or v_data.get("right_points"):
        lp = v_data.get("left_points") or []
        rp = v_data.get("right_points") or []
        for pt in lp[:2]:
            mirrored.append({"name": str(pt), "sub": str(v_data.get("left_label") or "Legacy"), "color": "#F43F5E"})
        for pt in rp[:2]:
            mirrored.append({"name": str(pt), "sub": str(v_data.get("right_label") or "Modern"), "color": "#34D399"})
    elif v_data.get("bars"):
        for b in v_data["bars"][:4]:
            mirrored.append({"name": f"{b.get('label', '')}: {b.get('display', b.get('value', ''))}", "sub": "Benchmark", "color": b.get("color", "")})
    elif v_data.get("entries"):
        for e in v_data["entries"][:4]:
            mirrored.append({"name": f"{e.get('op', '')} ({e.get('address', '')})", "sub": f"{e.get('table', '')} • {e.get('status', '')}"})
    elif v_data.get("bullets"):
        for b in v_data["bullets"][:4]:
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
            if blk.get("text") and len(mirrored) < 4:
                mirrored.append({"name": str(blk["text"])[:48], "sub": str(blk.get("eyebrow") or "")})
    if not mirrored:
        sents = [s.strip() for s in re.split(r"[.!?\n]+", str(sc.get("narration") or "")) if len(s.strip()) > 6][:4]
        mirrored = [{"name": s[:44], "sub": title[:28]} for s in sents] or [{"name": title[:40], "sub": "Architecture"}]
    v_data["items"] = mirrored[:5]


def _enforce_engine_style(
    timeline: Dict[str, Any],
    engine_style: str,
    topic: str,
    tone: str = "auto_dynamic",
    format_ratio: str = "9:16",
    visual_history: Optional[Dict[str, Any]] = None,
    run_num: int = 1,
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
    recent_arts = set((hist.get("recent_art_styles") or [])[-10:])
    recent_vtypes = set((hist.get("recent_visual_types") or [])[-16:])
    recent_bds = set((hist.get("recent_backdrops") or [])[-6:])
    recent_trs = set((hist.get("recent_transitions") or [])[-5:])
    recent_tfxs = set((hist.get("recent_text_fx") or [])[-5:])
    is_diverse_engine = engine_style in (
        "studio_domain_library", "pure_zero_template", "studio_300_domain",
        "dual_generative", "cinematic_studio", "auto_dynamic", "hybrid_modern",
    )

    art_styles = ["light_whiteboard", "editorial_dark", "blueprint_grid", "neon_fireship"]
    raw_art = str(timeline.get("art_style") or "").strip()
    _STUDIO_SET = ("studio_300_domain", "pure_zero_template", "studio_domain_library", "cinematic_studio", "dual_generative")
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

    role_tone_defaults = ["fireship_octane", "staff_engineer", "dramatic_performance", "interview_prep", "conversational_casual"]
    used_vtypes: set = set()
    used_bds_local: set = set()
    for idx, sc in enumerate(scenes):
        if tone != "auto_dynamic":
            sc["scene_tone"] = tone
        elif not sc.get("scene_tone"):
            sc["scene_tone"] = role_tone_defaults[idx % len(role_tone_defaults)]

        v_data = sc.get("visual_data", {})
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

        # Rotate away from recently used or intra-reel repeated visual_types across all multi-layout engines
        if is_diverse_engine and engine_style != "pure_zero_template":
            needs_swap = (current_vtype in recent_vtypes) or (current_vtype in used_vtypes)
            if needs_swap and current_vtype not in ("web_scene", "svg_scene", "spatial_canvas"):
                fam = _LAYOUT_TO_FAMILY.get(current_vtype)
                if not fam:
                    role_l = str(sc.get("role") or "").lower()
                    fam = "hook" if idx == 0 else ("compare" if "trade" in role_l or "vs" in role_l else ("summary" if idx == len(scenes) - 1 else "flow"))
                if engine_style in _STUDIO_SET:
                    fam_pool = _DIVERSE_LAYOUT_FAMILIES.get(fam, _DIVERSE_LAYOUT_FAMILIES["flow"])
                else:
                    # Non-studio modular animator engines (auto_dynamic / hybrid_modern)
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
                new_vtype = fresh_fam[(run_num * 3 + idx) % len(fresh_fam)]
                if new_vtype != current_vtype:
                    current_vtype = new_vtype
                    sc["visual_type"] = new_vtype
                    _mirror_items_for_domain_layout(v_data, sc, str(v_data.get("title") or topic[:40]))

        # Ensure required data structures are present and rich for the active visual_type
        title = v_data.get("title") or sc.get("narration", "")[:45] or topic[:40]
        default_badge = "" if engine_style in ["auto_dynamic", "studio_300_domain", "pure_zero_template", "studio_domain_library", "cinematic_studio", "dual_generative", "hybrid_modern"] else engine_style.replace("_", " ").upper()
        badge = v_data.get("badge") or default_badge
        v_data["title"] = title
        v_data["badge"] = badge

        if current_vtype == "code_terminal":
            if not v_data.get("code_snippet") and not v_data.get("command"):
                v_data["command"] = f"python -m engine --run {topic.lower().replace(' ', '_')[:16]}"
                v_data["code_snippet"] = (
                    f"# Scene {idx+1}: {title}\n"
                    f"async def handle_sync_event(ctx):\n"
                    f"    cluster = await init_pipeline()\n"
                    f"    res = cluster.replicate(ctx)\n"
                    f"    return {{'status': 200, 'synced': True}}"
                )

        elif current_vtype == "sql_table":
            if not v_data.get("code_snippet"):
                tbl_name = topic.lower().replace(" ", "_")[:12]
                v_data["code_snippet"] = f"SELECT emp_id, salary, DENSE_RANK() OVER (ORDER BY salary DESC) FROM {tbl_name};"
            if not v_data.get("table_data"):
                v_data["table_data"] = {
                    "headers": ["ID", "COMPONENT", "METRIC", "RANK"],
                    "rows": [
                        ["101", f"{topic[:10]} A", "120,000", "1"],
                        ["102", f"{topic[:10]} B", "95,000", "2"],
                        ["103", f"{topic[:10]} C", "95,000", "2"],
                        ["104", f"{topic[:10]} D", "80,000", "3"]
                    ]
                }

        elif current_vtype == "architecture_flow":
            if not v_data.get("nodes"):
                v_data["nodes"] = [
                    {"id": "src", "label": "Client Ingestion", "sub": "Traffic & Event Stream", "color": "#38BDF8"},
                    {"id": "engine", "label": f"{topic[:16]} Engine", "sub": "Distributed State Sync", "color": "#FBBF24"},
                    {"id": "target", "label": "Target Cluster", "sub": "Persistent Replicated Store", "color": "#34D399"}
                ]

        elif current_vtype == "split_comparison":
            if not v_data.get("left_points") or not v_data.get("right_points"):
                v_data["left_label"] = v_data.get("left_label") or "LEGACY / UNOPTIMIZED"
                v_data["left_points"] = v_data.get("left_points") or [
                    "High Latency & Contention",
                    "Fragile Manual Failover",
                    "Table Locks & Downtime"
                ]
                v_data["right_label"] = v_data.get("right_label") or "MODERN / SCALABLE"
                v_data["right_points"] = v_data.get("right_points") or [
                    "Sub-Second Zero-Lock Sync",
                    "Zero Production Downtime",
                    "Automated Resilient Scale"
                ]

        elif current_vtype == "benchmark_chart":
            if not v_data.get("bars"):
                v_data["winner_badge"] = v_data.get("winner_badge") or "15X SPEEDUP"
                v_data["bars"] = [
                    {"label": "Standard Batch Load", "value": 4500, "display": "4.5s Latency", "color": "#EF4444", "is_winner": False},
                    {"label": "Optimized Buffer Stream", "value": 350, "display": "350ms", "color": "#FBBF24", "is_winner": False},
                    {"label": f"{topic[:16]} Stream", "value": 24, "display": "24ms Lag (Winner)", "color": "#10B981", "is_winner": True}
                ]

        elif current_vtype == "data_structure_memory":
            if not v_data.get("entries"):
                v_data["entries"] = [
                    {"address": "0x00A1", "op": "COMMIT LSN 4920", "table": "orders", "status": "REPLICATED"},
                    {"address": "0x00B4", "op": "INSERT LSN 4921", "table": "payments", "status": "IN-TRANSIT"},
                    {"address": "0x00C8", "op": "UPDATE LSN 4922", "table": "inventory", "status": "BUFFERED"}
                ]

        elif current_vtype == "circular_hub_mesh":
            if not v_data.get("satellites"):
                v_data["hub_name"] = v_data.get("hub_name") or "CORE BROKER"
                v_data["satellites"] = [
                    {"name": "Client Ingestion", "role": "API Gateway", "color": "#EF4444"},
                    {"name": "App Workers", "role": "Compute Nodes", "color": "#10B981"},
                    {"name": "State Cache", "role": "Sub-millisecond", "color": "#FBBF24"},
                    {"name": "Database Cluster", "role": "ACID Store", "color": "#38BDF8"}
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
                v_data["pills"] = [p for p in [v_data.get("left_pill"), v_data.get("right_pill")] if p]

        elif current_vtype == "custom_scene":
            if not v_data.get("blocks"):
                bullets = [s.strip() for s in sc.get("narration", "").split(".") if len(s.strip()) > 6][:3]
                v_data["blocks"] = [
                    {"block": "question_card", "text": title, "stage": 1},
                    {"block": "list_cards", "items": [{"title": b[:48], "desc": "", "kind": "info"} for b in bullets], "stage": 2}
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
            v_data["bottom_tags"] = v_data.get("bottom_tags") or ["High Precision", "Production Ready"]

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
        from core.web_generative_engine import ZERO_TEMPLATE_50_ARCHETYPES
        fresh_opt1 = [a for a in ZERO_TEMPLATE_50_ARCHETYPES if a not in recent_vtypes] or list(ZERO_TEMPLATE_50_ARCHETYPES)
        chosen_opt1 = fresh_opt1[(run_num * 5 + idx * 3 + abs(hash(topic.strip().lower()))) % len(fresh_opt1)]
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
        elif engine_style == "studio_300_domain" and (idx + run_num) % max(2, len(scenes)) == 0 and current_vtype not in ("web_scene", "svg_scene", "spatial_canvas"):
            # Both Combined: rotate which scene renders as bespoke Option 1 web/svg/spatial vs Option 2 domain layouts
            v_data.setdefault("_intent", current_vtype)
            v_data.setdefault("option1_archetype", chosen_opt1)
            sc["visual_type"] = "svg_scene" if chosen_opt1.startswith("svg_") else ("spatial_canvas" if chosen_opt1.startswith("spatial_") else "web_scene")
            used_vtypes.add(current_vtype)
            used_vtypes.add(chosen_opt1)
        else:
            used_vtypes.add(sc["visual_type"])

        sc["visual_data"] = v_data

        # Ensure Audio-Visual Choreography triggers exist for voice-synced Progressive Reveal
        choreo = sc.get("choreography")
        if not isinstance(choreo, dict) or not choreo.get("triggers"):
            narration_words = [
                re.sub(r"[^a-zA-Z0-9_\u0900-\u097F-]", "", w)
                for w in sc.get("narration", "").split()
            ]
            narration_words = [w for w in narration_words if len(w) >= 4]
            auto_triggers = []
            if len(narration_words) >= 4:
                step = len(narration_words) / 4.0
                for st_i in range(4):
                    kw = narration_words[min(len(narration_words) - 1, int(st_i * step))]
                    auto_triggers.append({"stage": st_i + 1, "keyword": kw.lower()})
            sc["choreography"] = {
                "mode": "node_edge_traversal" if current_vtype in ["all_in_one_tech_canvas", "architecture_flow", "circular_hub_mesh"] else "progressive_build",
                "triggers": auto_triggers
            }

    if engine_style in ("pure_zero_template", "dual_generative", "studio_300_domain"):
        _synthesize_bespoke_web_scenes(scenes, topic, format_ratio=format_ratio, run_num=run_num)

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
    tone: str = "senior_hinglish_mentor",
    engine_style: str = "studio_domain_library",
    duration_mode: str = "auto",
    voice: str = "en-IN-PrabhatNeural|hinglish",
    format_ratio: str = "9:16",
) -> Dict[str, Any]:
    """Deterministic multi-scene storyboard used only if every external LLM API fails simultaneously."""
    clean_topic = (topic or "System Design Architecture").strip()[:70]
    scene_tone = tone if tone != "auto_dynamic" else "senior_hinglish_mentor"
    is_marathi = voice.startswith("mr-") or voice.endswith("|mr")
    is_hindi = voice.startswith("hi-") or voice.endswith("|hi")

    if is_marathi:
        narrs = [
            (f"मित्रांनो, {clean_topic} मध्ये 90% engineers एका common trap मध्ये अडकतात... [pause] ते कसे टाळायचे?", f"Mitrano, {clean_topic} madhe 90% engineers eka common trap madhe adaktat... [pause] te kase talayche?"),
            (f"{clean_topic} चे core architecture 3 simple steps मध्ये काम करते — request routing, state sync, आणि fast execution.", f"{clean_topic} che core architecture 3 simple steps madhe kaam karte — request routing, state sync, ani fast execution."),
            (f"Pan trade-off लक्षात ठेवा: latency 50% कमी होते, पण edge cases साठी proper limits सेट करा.", f"Pan trade-off lakshat theva: latency 50% kami hote, pan edge cases saathi proper limits set kara."),
            (f"ही reel save करा आणि comment मध्ये तुमचा next topic सांगा!", f"Hi reel save kara ani comment madhe tumcha next topic sanga!"),
        ]
    elif is_hindi:
        narrs = [
            (f"Interview में 90% लोग {clean_topic} के एक simple question में फंस जाते हैं... [pause] आइए reason समझते हैं।", f"Interview mein 90% log {clean_topic} ke ek simple question mein phans jaate hain... [pause] aaiye reason samajhte hain."),
            (f"{clean_topic} की architecture 3 clear stages में चलती है — fast ingestion, core engine processing, और reliable storage sync.", f"{clean_topic} ki architecture 3 clear stages mein chalti hai — fast ingestion, core engine processing, aur reliable storage sync."),
            (f"Real trade-off ये है कि latency 10x कम होती है, लेकिन production edge cases के लिए retry और limits ज़रूरी हैं।", f"Real trade-off yeh hai ki latency 10x kam hoti hai, lekin production edge cases ke liye retry aur limits zaroori hain."),
            (f"इस reel को save करें और next interview topic comment करें!", f"Is reel ko save karein aur next interview topic comment karein!"),
        ]
    else:
        narrs = [
            (f"90% engineers hit a hidden bottleneck in {clean_topic}... [pause] let's see why systems freeze under load.", ""),
            (f"{clean_topic} works in 3 clean stages: request routing, in-memory processing, and resilient state sync.", ""),
            (f"The real trade-off: latency drops by 10x, while proper backpressure and limits protect edge cases.", ""),
            (f"Save this breakdown for your next interview and comment your next topic below!", ""),
        ]

    scenes = [
        {
            "scene_id": 1,
            "role": "hook",
            "scene_tone": scene_tone,
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
            "scene_tone": scene_tone,
            "narration": narrs[1][0],
            **({"narration_hinglish": narrs[1][1]} if narrs[1][1] else {}),
            "visual_type": "architecture_flow",
            "visual_data": {
                "badge": "SYSTEM TOPOLOGY",
                "title": f"{clean_topic} Pipeline",
                "nodes": [
                    {"id": "in", "label": "Client Requests", "sub": "Ingress & Validation", "color": "#38BDF8"},
                    {"id": "core", "label": f"{clean_topic[:18]} Core", "sub": "Fast State Engine", "color": "#FBBF24"},
                    {"id": "out", "label": "Persistent Store", "sub": "Consistent Output", "color": "#34D399"},
                ],
            },
        },
        {
            "scene_id": 3,
            "role": "tradeoff",
            "scene_tone": scene_tone,
            "narration": narrs[2][0],
            **({"narration_hinglish": narrs[2][1]} if narrs[2][1] else {}),
            "visual_type": "split_comparison",
            "visual_data": {
                "badge": "TRADE-OFFS & FIX",
                "title": "Latency vs Reliability",
                "left_label": "UNOPTIMIZED",
                "left_points": ["Blocking contention", "High tail latency", "Cascade failures"],
                "right_label": "PRODUCTION FIX",
                "right_points": ["10x lower latency", "Bounded queues", "Graceful fallback"],
            },
        },
        {
            "scene_id": 4,
            "role": "cta",
            "scene_tone": scene_tone,
            "narration": narrs[3][0],
            **({"narration_hinglish": narrs[3][1]} if narrs[3][1] else {}),
            "visual_type": "concept_cards",
            "visual_data": {
                "badge": "KEY TAKEAWAYS",
                "title": f"{clean_topic} Checklist",
                "bullets": [
                    "Measure bottlenecks before optimizing",
                    "Guard edge cases with explicit limits",
                ],
                "footer_cta": "Save • Share • Comment Next Topic",
            },
        },
    ]
    if duration_mode == "short":
        scenes = scenes[:3]
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
