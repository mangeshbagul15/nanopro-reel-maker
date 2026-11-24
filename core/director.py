import json
import re
from typing import Dict, Any, Optional
from core.config import GEMINI_API_KEY, GROQ_API_KEY

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
      "Continuous CDC: Streaming transaction log updates in real-time",
      "Schema Conversion: Automated mapping between heterogeneous engines",
      "Multi-AZ High Availability: Standby failover with sub-second switchover"
    ]
  }

STRICT JSON OUTPUT FORMAT ONLY:
Output a single valid JSON object matching this structure:
{
  "title": "Topic Title",
  "topic_category": "cloud / database / programming / system_design",
  "total_target_seconds": 60,
  "scenes": [
    {
      "scene_id": 1,
      "role": "hook",
      "narration": "Narration text with natural pauses...",
      "visual_type": "alert_diagram",
      "visual_data": {
        "badge": "BADGE TEXT",
        "title": "Scene Title",
        "...": "Fields strictly populated from the schema above"
      }
    }
  ]
}
"""

ENGINE_STYLE_DIRECTIVES = {
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

def generate_timeline(
    topic: str,
    tone: str = "conversational",
    engine_style: str = "hybrid_modern",
    duration_mode: str = "auto",
    custom_style_prompt: str = ""
) -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini models with full AI autonomy,
    strictly adapted to the chosen Visual Engine & Style, with no artificial 60-second limit.
    """
    if engine_style == "custom_user_style" and custom_style_prompt.strip():
        style_directive = (
            f"MANDATORY CUSTOM STYLE DIRECTIVE: The user explicitly requested this custom visual aesthetic: "
            f"'{custom_style_prompt.strip()}'. You MUST tailor your visual_type and visual_data to reflect this custom design aesthetic across all scenes."
        )
    else:
        style_directive = ENGINE_STYLE_DIRECTIVES.get(engine_style, ENGINE_STYLE_DIRECTIVES["hybrid_modern"])
    
    duration_instructions = {
        "auto": "Natural duration based on topic depth (typically 4 to 6 scenes). Completely explain the core architecture and trade-offs.",
        "short": "Quick, punchy overview (3 scenes, ~30-45 seconds). High-impact summary.",
        "standard": "Standard explainer (4 to 5 scenes, ~60 seconds). Balanced walkthrough.",
        "deep_dive": "Comprehensive in-depth breakdown (6 to 8 scenes, 90 to 180+ seconds). Detail every pipeline stage, internal buffer, and real implementation commands."
    }
    dur_guidance = duration_instructions.get(duration_mode, duration_instructions["auto"])

    user_prompt = (
        f"Topic: '{topic}'.\n"
        f"Tone: {tone}.\n"
        f"Selected Visual Engine: '{engine_style}'.\n"
        f"Target Depth / Duration: {dur_guidance}\n"
        f"{style_directive}\n\n"
        f"MANDATORY REQUIREMENT: For EVERY scene, make sure the visual_data fields (node labels, schemas, table rows, code snippet, bullet points, metrics) "
        f"EXACTLY match and illustrate what the narrator is speaking in that scene's narration. Never use generic or unrelated placeholders.\n"
        f"Autonomously design the complete storyboard blueprint JSON now."
    )
    
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    models_to_try = [
        "gemini-3-flash-preview",
        "gemini-3.1-pro-preview",
        "gemini-2.5-pro",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
            )
            raw_text = response.text.strip()
            clean_json = _extract_json(raw_text)
            if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                clean_json["meta_director"] = {
                    "model_used": model_name,
                    "engine_style": engine_style,
                    "custom_style_prompt": custom_style_prompt,
                    "duration_mode": duration_mode,
                    "topic": topic
                }
                return clean_json
        except Exception as e:
            print(f"[Director] Model {model_name} error: {e}")
            continue

    raise RuntimeError("Failed to generate video timeline from Gemini.")

def _extract_json(text: str) -> Dict[str, Any]:
    """Helper to extract JSON from markdown or raw string."""
    try:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1)
        return json.loads(text.strip())
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        return {}
