import json
import re
from typing import Dict, Any
from core.config import GEMINI_API_KEY, GROQ_API_KEY

SYSTEM_PROMPT = """You are an elite Tech Content Director and Visual Storyteller for viral 9:16 vertical tech reels and shorts (inspired by Fireship and ByteByteGo).
Your mission is to analyze any technical topic and autonomously design a realistic, topic-accurate, highly engaging 45-60 second storyboard blueprint JSON.

GUIDELINES FOR TOPIC-ACCURATE VISUAL DIRECTING:
1. STRICT BAN ON REPETITIVE TEMPLATE FORMULAS:
   - CRITICAL: NEVER output the generic sequence of 'split_comparison' -> 'circular_hub_mesh' -> 'benchmark_chart' -> 'metric_gauge_hud'. That formula is strictly prohibited.
   - Do NOT insert benchmark charts or speedometer gauges unless the topic is specifically about performance benchmarks or latency tests.
   - Do NOT insert circular hub meshes unless the architecture specifically involves a central event hub/broker.

2. TOPIC-SPECIFIC VISUAL ENGINE SELECTION:
   - For Cloud, Pipelines & Architecture (e.g. AWS DMS, Kafka, S3, Docker, Kubernetes, Microservices):
     * Primary visual MUST BE 'architecture_flow' showing the concrete service pipeline (e.g. Source Database -> DMS CDC Replication Instance -> Target Aurora Cluster).
     * Follow with 'code_terminal' (actual CLI commands or pipeline scripts) or 'data_structure_memory' (CDC write-ahead log buffers).
   - For Databases & SQL (e.g. SQL DENSE_RANK, Window Functions, PostgreSQL, Snowflake, Indexes):
     * Primary visual MUST BE 'sql_table' showing real schemas, row data, and active calculation outputs.
     * Follow with 'code_terminal' showing the actual SQL SELECT query.
   - For Programming & Systems (e.g. Python GIL, Concurrency, Rust, Memory Management):
     * Primary visual MUST BE 'code_terminal' with syntax-highlighted code execution.
     * Follow with 'data_structure_memory' showing thread locks, mutexes, and memory offsets.
   - For Comparative Trade-offs (e.g. Redis vs Memcached, Monolith vs Microservices):
     * Use 'split_comparison' comparing real architectural constraints.

3. CONVERSATIONAL VIRAL SCRIPT (110 - 145 WORDS TOTAL):
   - Hook in Scene 1 (First 3 seconds): Real-world engineering question or relatable developer dilemma.
   - Natural cadence: Explain like a senior staff engineer over coffee. Use "..." for subtle dramatic pauses.
   - Pure technical value without fluff or buzzwords.

4. DYNAMIC SCENE COUNT:
   - 3 to 4 scenes maximum (concise, high impact, zero filler scenes).
   - Each scene's visual_data MUST be completely populated with technical details directly relevant to the user's specific prompt.

STRICT JSON OUTPUT FORMAT ONLY:
Output a single valid JSON object matching this structure:
{
  "title": "Topic Title",
  "topic_category": "cloud / database / programming / system_design",
  "total_target_seconds": 55,
  "scenes": [
    {
      "scene_id": 1,
      "role": "hook",
      "narration": "Narration words with natural pauses...",
      "visual_type": "chosen_visual_engine",
      "visual_data": {
        "badge": "BADGE TEXT",
        "title": "Scene Title",
        "...": "Dynamic fields tailored to the chosen visual_type"
      }
    }
  ]
}
"""

ENGINE_STYLE_DIRECTIVES = {
    "terminal_screencast": "MANDATORY STYLE DIRECTIVE: The user explicitly selected 'Terminal Screencast'. The video MUST heavily prioritize 'code_terminal' scenes featuring real terminal commands, shell scripts, execution logs, and code outputs.",
    "bytebytego_dsl": "MANDATORY STYLE DIRECTIVE: The user explicitly selected 'ByteByteGo Architecture'. The video MUST heavily prioritize 'architecture_flow' showing multi-tier system designs, cloud services, and pipeline topologies.",
    "manim_math": "MANDATORY STYLE DIRECTIVE: The user explicitly selected 'Mathematical & Algorithmic'. Focus on 'data_structure_memory' buffers, algorithmic steps, and 'benchmark_chart' performance comparisons.",
    "handdrawn_sketch": "MANDATORY STYLE DIRECTIVE: The user explicitly selected 'Whiteboard Sketch'. Focus on intuitive conceptual breakdowns using 'concept_cards' and 'split_comparison'.",
    "kinetic_type": "MANDATORY STYLE DIRECTIVE: The user explicitly selected 'Kinetic Typography'. Focus on punchy technical principles using bold 'concept_cards' and crisp 'split_comparison'.",
    "hybrid_modern": "MANDATORY STYLE DIRECTIVE: The user selected 'Hybrid Modern'. Use a balanced, high-octane mix of 'architecture_flow', 'code_terminal', and 'data_structure_memory'.",
    "remotion_web": "MANDATORY STYLE DIRECTIVE: Focus on cyberpunk developer motion graphics with 'code_terminal' and 'architecture_flow'.",
    "blender_local_gpu": "MANDATORY STYLE DIRECTIVE: Structure deep system internals with detailed 'architecture_flow' and 'data_structure_memory' buffers.",
    "cloud_serverless_gpu": "MANDATORY STYLE DIRECTIVE: Focus on distributed cloud pipeline flows ('architecture_flow') and live streaming buffers."
}

def generate_timeline(topic: str, tone: str = "conversational", engine_style: str = "hybrid_modern") -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini models with full AI autonomy,
    strictly adapted to the chosen Visual Engine & Style.
    """
    style_directive = ENGINE_STYLE_DIRECTIVES.get(engine_style, ENGINE_STYLE_DIRECTIVES["hybrid_modern"])
    user_prompt = (
        f"Topic: '{topic}'.\n"
        f"Tone: {tone}.\n"
        f"Selected Visual Engine: '{engine_style}'.\n"
        f"{style_directive}\n"
        f"Autonomously plan the best visual scenes and conversational script matching this style exactly."
    )
    
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
            )
            raw_text = response.text.strip()
            clean_json = _extract_json(raw_text)
            if clean_json and "scenes" in clean_json and len(clean_json["scenes"]) > 0:
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
