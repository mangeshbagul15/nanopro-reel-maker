import json
import re
from typing import Dict, Any
from core.config import GEMINI_API_KEY, GROQ_API_KEY

SYSTEM_PROMPT = """You are an elite Tech Content Director and Motion Graphics Architect for viral 9:16 Instagram Reels and YouTube Shorts.
Your mission is to take any technical topic (AWS, Snowflake, SQL, Python, AI, Cloud) and output a comprehensive, structured timeline blueprint JSON for a 45-60 second educational vertical video.

CRITICAL RULES:
1. HUMAN CONVERSATIONAL SCRIPT:
   - Must sound like an expert engineer casually explaining a concept to a peer over coffee.
   - Use natural pauses indicated by "..." or commas.
   - No robotic jargon without immediate visual analogy.
   - Scene 1 MUST be a 3-second killer HOOK (e.g., "Ever wondered why migrating a 10TB database can crash your production?").
   - Total words across all scenes must be between 110 and 150 words (ideal for 45-60 seconds spoken pacing).

2. ZERO HARDCODED TEMPLATES:
   - You must choose the exact visual_type appropriate for the topic:
     * 'architecture_flow' -> For Cloud/AWS/System pipelines (Source DB -> Engine -> Target DB).
     * 'sql_table' -> For SQL queries, window functions, joins, indexing.
     * 'code_terminal' -> For Python, CLI tools, scripts, debugging.
     * 'concept_cards' -> For comparisons, architecture trade-offs, pros vs cons.
     * 'alert_diagram' -> For problem statements, race conditions, error scenarios.

3. STRICT JSON OUTPUT ONLY:
   Output ONLY valid JSON matching this exact structure:
{
  "title": "Title of the Reel",
  "topic_category": "cloud_architecture",
  "total_target_seconds": 55,
  "scenes": [
    {
      "scene_id": 1,
      "role": "hook",
      "narration": "Natural spoken words with pauses...",
      "visual_type": "architecture_flow",
      "visual_data": {
        "title": "Card or Diagram Title",
        "subtitle": "Brief subtitle or context",
        "badge": "AWS DMS",
        "nodes": [
          {"id": "src", "label": "Source DB", "sub": "Oracle / MySQL", "color": "#EF4444"},
          {"id": "eng", "label": "Replication Instance", "sub": "CDC Engine", "color": "#F59E0B"},
          {"id": "tgt", "label": "Target Cloud", "sub": "AWS Aurora", "color": "#10B981"}
        ],
        "connections": [
          {"from": "src", "to": "eng", "label": "CDC Stream"},
          {"from": "eng", "to": "tgt", "label": "Continuous Load"}
        ],
        "table_data": {
          "headers": ["id", "dept", "salary", "rank"],
          "rows": [
            ["101", "IT", "$120k", "1"],
            ["102", "IT", "$120k", "1"],
            ["103", "IT", "$95k", "2"]
          ]
        },
        "code_snippet": "SELECT emp_id, salary FROM employees;",
        "bullets": ["Zero Downtime", "Continuous CDC Replication", "Minimal Latency"]
      }
    }
  ]
}
"""

def generate_timeline(topic: str, tone: str = "conversational") -> Dict[str, Any]:
    """
    Generates a structured video timeline blueprint using Gemini models.
    """
    user_prompt = f"Create a viral 45-60 second 2D tech reel blueprint for the topic: '{topic}'. Tone: {tone}."
    
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Try gemini-3.5-flash-lite, then gemini-3.8-flash
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
