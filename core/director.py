import json
import re
from typing import Dict, Any
from core.config import GEMINI_API_KEY, GROQ_API_KEY

SYSTEM_PROMPT = """You are an elite Tech Content Director and Visual Storyteller for viral 9:16 vertical tech reels and shorts (inspired by Fireship, ByteByteGo, and 3Blue1Brown).
Your mission is to analyze any technical topic and autonomously design a cohesive, highly engaging 45-60 second storyboard blueprint JSON.

GUIDELINES FOR AUTONOMOUS DIRECTOR:
1. FULL VISUAL FREEDOM (ZERO HARDCODED SEQUENCES):
   - You have complete creative autonomy. You are NOT bound to any fixed sequence of scenes or mandatory templates.
   - Analyze the specific subject matter and organically choose the visual types that best explain it:
     * 'code_terminal' -> For programming, scripts, debugging, CLI, terminal outputs, Python/Go/Rust.
     * 'sql_table' -> For SQL queries, databases, joins, window functions, tabular data, indexing.
     * 'architecture_flow' -> For cloud services, pipelines, API flows, microservices, multi-tier systems.
     * 'circular_hub_mesh' -> For central clusters, event buses, distributed systems, hubs & spokes.
     * 'benchmark_chart' -> For performance comparisons, latency, speedups, throughput benchmarks.
     * 'split_comparison' -> For pros vs cons, before vs after, anti-pattern vs best practice.
     * 'data_structure_memory' -> For memory layouts, partitions, B-Trees, queues, buffers, registers.
     * 'metric_gauge_hud' -> For telemetry, uptime, throughput, KPIs, production numbers.
     * 'alert_diagram' -> For bottlenecks, production crashes, critical challenges, radar alerts.
     * 'concept_cards' -> For core principles, architectural trade-offs, key takeaways.

2. CONVERSATIONAL VIRAL SCRIPT (110 - 145 WORDS TOTAL):
   - Hook in Scene 1 (First 3 seconds): Grab attention with an immediate real-world engineering problem, surprising metric, or provocative question.
   - Pacing: Conversational engineer explaining to a peer over coffee. Use "..." for natural dramatic pauses.
   - Explain the concept with intuitive analogies before technical depth.

3. DYNAMIC SCENE COMPOSITION:
   - Organize the story into 3 to 5 scenes as naturally required by the technical topic.
   - Each scene must select the visual_type that best serves that specific explanation.
   - Ensure visual_data is rich, specific to the topic, and contains appropriate fields (e.g., nodes for architecture, code_snippet for terminal, table_data for sql_table, bars for benchmark_chart, left/right points for split_comparison, satellites for hub_mesh, or bullets for concept_cards).

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

def generate_timeline(topic: str, tone: str = "conversational", engine_style: str = "hybrid_modern") -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini models with full AI autonomy.
    """
    user_prompt = f"Topic: '{topic}'. Tone: {tone}. Preferred Engine Style: '{engine_style}'. Autonomously plan the best visual scenes and script for this topic."
    
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
