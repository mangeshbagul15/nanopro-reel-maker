import json
import re
from typing import Dict, Any, Optional, List
from core.config import GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, MISTRAL_API_KEY

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
    format_ratio: str = "9:16"
) -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini models with full AI autonomy,
    strictly adapted to the chosen Visual Engine, Voice Persona (Language/Dialect), Format and Duration.
    """
    if engine_style == "custom_user_style" and custom_style_prompt.strip():
        style_directive = (
            f"MANDATORY CUSTOM STYLE DIRECTIVE: The user explicitly requested this custom visual aesthetic: "
            f"'{custom_style_prompt.strip()}'. You MUST tailor your visual_type and visual_data to reflect this custom design aesthetic across all scenes."
        )
    else:
        style_directive = ENGINE_STYLE_DIRECTIVES.get(engine_style, ENGINE_STYLE_DIRECTIVES["auto_dynamic"])
    
    # 1. Language & Dialect based on the selected Voice Persona
    if voice.startswith("hi-") or voice == "en-IN-NeerjaExpressiveNeural" or voice.endswith("|hi"):
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: The user explicitly selected a Hindi / Hinglish voice persona. "
            "You MUST write the spoken `narration` in natural, conversational Hindi-English using Devanagari for Hindi words "
            "mixed seamlessly with crisp English technical terms (e.g., 'आज हम समझेंगे कि Database Migration बिना Downtime के कैसे काम करता है...'). "
            "Keep all on-screen visual_data (titles, labels, code, queries, badges) in crisp English!"
        )
    elif voice.startswith("mr-") or voice.endswith("|mr"):
        lang_directive = (
            "LANGUAGE & DIALECT MANDATE: The user explicitly selected a Marathi voice persona. "
            "You MUST write the spoken `narration` in natural conversational Marathi using Devanagari for Marathi words "
            "mixed seamlessly with English technical nouns (e.g., 'मित्रांनो, आज आपण पाहणार आहोत की Database Migration झिरो Downtime सह कसे चालते...'). "
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

    # 3. Format guidance
    format_directive = f"Target Aspect Ratio: '{format_ratio}'."
    tone_directive = TONE_DIRECTIVES.get(tone, f"SCRIPT TONE & CADENCE: {tone}.")

    user_prompt = (
        f"Topic: '{topic}'.\n"
        f"{tone_directive}\n"
        f"Selected Visual Engine: '{engine_style}'.\n"
        f"Selected Voice Persona: '{voice}'.\n"
        f"{lang_directive}\n"
        f"{format_directive}\n"
        f"Target Depth / Duration: {dur_guidance}\n"
        f"{style_directive}\n\n"
        f"MANDATORY REQUIREMENT: For EVERY scene, make sure the visual_data fields (node labels, schemas, table rows, code snippet, bullet points, metrics) "
        f"EXACTLY match and illustrate what the narrator is speaking in that scene's narration. Never use generic or unrelated placeholders.\n"
        f"Autonomously design the complete storyboard blueprint JSON now."
    )
    
    last_errors = []

    # 1. Primary: High-speed Gemini Models
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            models_to_try = [
                "gemini-3.1-flash-lite",
                "gemini-3.1-flash-lite-preview",
                "gemini-flash-lite-latest",
                "gemini-flash-latest",
                "gemini-3-flash-preview",
                "gemini-3.5-flash",
                "gemini-3.8-flash"
            ]
            
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
                    )
                    raw_text = response.text.strip() if response.text else ""
                    clean_json = _extract_json(raw_text)
                    if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                        clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone)
                        clean_json["meta_director"] = {
                            "model_used": model_name,
                            "engine_style": engine_style,
                            "custom_style_prompt": custom_style_prompt,
                            "duration_mode": duration_mode,
                            "topic": topic,
                            "voice": voice,
                            "format_ratio": format_ratio
                        }
                        return clean_json
                except Exception as e:
                    err_str = str(e)
                    print(f"[Director] Model {model_name} error: {err_str[:120]}")
                    last_errors.append(f"{model_name}: {err_str[:120]}")
                    continue
        except Exception as e:
            last_errors.append(f"Gemini client error: {e}")

    # 2. Resilient Secondary Fallback: Groq Ultra-Fast LLM
    if GROQ_API_KEY:
        try:
            from groq import Groq
            g_client = Groq(api_key=GROQ_API_KEY)
            for g_model in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
                try:
                    g_res = g_client.chat.completions.create(
                        model=g_model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7
                    )
                    raw_text = g_res.choices[0].message.content.strip() if g_res.choices else ""
                    clean_json = _extract_json(raw_text)
                    if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                        clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone)
                        clean_json["meta_director"] = {
                            "model_used": f"groq/{g_model}",
                            "engine_style": engine_style,
                            "custom_style_prompt": custom_style_prompt,
                            "duration_mode": duration_mode,
                            "topic": topic,
                            "voice": voice,
                            "format_ratio": format_ratio
                        }
                        return clean_json
                except Exception as e:
                    last_errors.append(f"groq/{g_model}: {str(e)[:120]}")
                    continue
        except Exception as e:
            last_errors.append(f"Groq client error: {e}")

    # 3. Third-Tier Fail-Safe: OpenRouter
    if OPENROUTER_API_KEY:
        try:
            import requests
            or_models = ["meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat"]
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
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.7
                        },
                        timeout=30
                    )
                    if r.status_code == 200:
                        res_json = r.json()
                        raw_text = res_json["choices"][0]["message"]["content"].strip()
                        clean_json = _extract_json(raw_text)
                        if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
                            clean_json = _enforce_engine_style(clean_json, engine_style, topic, tone=tone)
                            clean_json["meta_director"] = {
                                "model_used": f"openrouter/{or_model}",
                                "engine_style": engine_style,
                                "custom_style_prompt": custom_style_prompt,
                                "duration_mode": duration_mode,
                                "topic": topic,
                                "voice": voice,
                                "format_ratio": format_ratio
                            }
                            return clean_json
                except Exception as e:
                    last_errors.append(f"openrouter/{or_model}: {str(e)[:120]}")
        except Exception as e:
            last_errors.append(f"OpenRouter client error: {e}")

    err_summary = "; ".join(last_errors) if last_errors else "No valid API keys configured."
    raise RuntimeError(f"Failed to generate video timeline from AI Director. Details: {err_summary}")

def _enforce_engine_style(timeline: Dict[str, Any], engine_style: str, topic: str, tone: str = "auto_dynamic") -> Dict[str, Any]:
    """
    Guarantees that every scene in the timeline strictly adheres to the user-selected Visual Engine & Style,
    adapting visual_type, scene_tone, and populating rich topic-specific visual_data fields.
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

    # Deterministically pick a fresh visual art_style from topic hash if AI omitted one
    art_styles = ["light_whiteboard", "editorial_dark", "blueprint_grid", "neon_fireship"]
    topic_art_style = timeline.get("art_style") or art_styles[abs(hash(topic.strip().lower())) % len(art_styles)]
    if topic_art_style not in art_styles:
        topic_art_style = art_styles[0]
    timeline["art_style"] = topic_art_style

    role_tone_defaults = ["fireship_octane", "staff_engineer", "dramatic_performance", "interview_prep", "conversational_casual"]
    for idx, sc in enumerate(scenes):
        if tone != "auto_dynamic":
            sc["scene_tone"] = tone
        elif not sc.get("scene_tone"):
            sc["scene_tone"] = role_tone_defaults[idx % len(role_tone_defaults)]

        v_data = sc.get("visual_data", {})
        if not v_data.get("art_style"):
            v_data["art_style"] = topic_art_style
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

        # Anti-Repetition Safety in auto_dynamic: if Scene 1 defaulted to alert_diagram on non-outage topics, use custom_scene
        if engine_style == "auto_dynamic" and idx == 0 and current_vtype == "alert_diagram":
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

        # Ensure required data structures are present and rich for the active visual_type
        title = v_data.get("title") or sc.get("narration", "")[:45] or topic[:40]
        default_badge = "" if engine_style in ["auto_dynamic", "hybrid_modern"] else engine_style.replace("_", " ").upper()
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

        elif current_vtype == "alert_diagram":
            if not v_data.get("challenge"):
                v_data["problem_title"] = v_data.get("problem_title") or f"Production Bottleneck: {title}"
                v_data["problem_desc"] = v_data.get("problem_desc") or "High concurrency spikes caused thread contention and system degradation."
                v_data["challenge"] = "How to achieve 100% availability without sacrificing latency?"

        elif current_vtype == "hero_hook":
            v_data["question"] = v_data.get("question") or v_data.get("problem_title") or title
            # Do NOT inject fake "Approach A / B" or "KEY ENGINEERING DECISION" filler!
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
            for m in ["gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.5-flash"]:
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
            for m in ["gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.5-flash"]:
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
