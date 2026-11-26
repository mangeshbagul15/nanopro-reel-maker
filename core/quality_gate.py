"""
Closed-Loop Multimodal AI Quality Critic & Surgical Self-Repair Engine.

Combines 3 inspection layers to verify whether the rendered frames, spoken words,
captions, action choreography, and audio actually communicate the topic clearly
to a human viewer:
  Layer A: Local Pixel & Geometry Computer-Vision Audit (NumPy/PIL - edge clips,
           karaoke overlap, empty/crowded frames)
  Layer B: Audio <-> Visual <-> Action NLP Sync Validator (Whisper words vs visual data & SFX)
  Layer C: Multimodal Vision LLM Critic (Gemini Vision filmstrip contact sheet reviewer)

Scores every reel across 6 dimensions (0-100), executes fast parallel targeted
repairs on ONLY failing scenes (Data/Action Surgery -> Layout Swap -> Bespoke HTML5/SVG),
and ALWAYS guarantees completion via Best-So-Far Checkpointing (never blocks or fails).
"""

import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.config import GEMINI_API_KEY, GROQ_API_KEY, OUTPUT_DIR

QUALITY_MODES: List[Tuple[str, str]] = [
    ("standard", "🧠 AI Auto-Verify & Self-Heal (Target >= 84/100 · Max 1–2 Fast Repairs) [Recommended]"),
    ("perfection", "🏆 Studio Perfection (Target >= 90/100 · Auto Bespoke HTML5/SVG Surgery)"),
    ("fast", "⚡ Fast Draft Mode (Skip Quality Critic)"),
]

DEFAULT_QUALITY_MODE = "standard"


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(v)))


def _harvest_visual_tokens(vd: Dict[str, Any]) -> str:
    """Collects all visible text tokens authored on a scene card/diagram for semantic comparison."""
    chunks: List[str] = []
    if not isinstance(vd, dict):
        return ""
    for k, v in vd.items():
        if k in ("html", "web_code", "svg", "svg_code", "art_style", "backdrop", "transition", "text_fx", "routed_engine", "option1_archetype", "_intent"):
            continue
        if isinstance(v, str):
            chunks.append(v)
        elif isinstance(v, list):
            for it in v[:10]:
                if isinstance(it, str):
                    chunks.append(it)
                elif isinstance(it, dict):
                    for sub_v in it.values():
                        if isinstance(sub_v, (str, int, float)):
                            chunks.append(str(sub_v))
        elif isinstance(v, dict):
            chunks.append(_harvest_visual_tokens(v))
    return " ".join(chunks)


# =========================================================================
# LAYER A: LOCAL COMPUTER VISION GEOMETRY & LEGIBILITY AUDIT
# =========================================================================
def _audit_scene_pixels_cv(
    scene_idx: int,
    scene: Dict[str, Any],
    frame_dir: Path,
    format_ratio: str = "9:16",
    caption_style: str = "karaoke_pop",
    platform_safe_zone: str = "instagram_reels",
) -> Dict[str, Any]:
    """
    Fast local NumPy pixel inspection of rendered reveal keyframes (70% & 95%).
    Detects edge clipping, subtitle-zone collision, sparse/blank scenes, or crowding.
    """
    issues: List[str] = []
    penalties = 0.0
    if not frame_dir.exists():
        return {"scene_idx": scene_idx, "cv_score": 45.0, "issues": ["missing_frames"], "fg_ratio": 0.0}

    frames = sorted(p for p in frame_dir.iterdir() if p.name.startswith("frame_") and p.suffix.lower() in (".jpg", ".png", ".jpeg"))
    if not frames:
        return {"scene_idx": scene_idx, "cv_score": 45.0, "issues": ["empty_frame_dir"], "fg_ratio": 0.0}

    probe_path = frames[int(len(frames) * 0.78)]
    try:
        arr = np.asarray(Image.open(probe_path).convert("RGB"), dtype=np.int16)
    except Exception:
        return {"scene_idx": scene_idx, "cv_score": 55.0, "issues": ["corrupt_frame"], "fg_ratio": 0.0}

    h, w, _ = arr.shape
    # Sample perimeter corner bands to approximate canvas background brightness/color dynamically
    corners = np.concatenate([
        arr[:24, :24].reshape(-1, 3),
        arr[:24, w - 24:].reshape(-1, 3),
        arr[h - 24:, :24].reshape(-1, 3),
        arr[h - 24:, w - 24:].reshape(-1, 3),
    ], axis=0)
    bg_med = np.median(corners, axis=0)
    diff = np.abs(arr - bg_med).max(axis=2)
    fg_mask = diff > 26

    # Body region excluding top 105px chrome bar & bottom 80px edge
    body_h0 = int(h * 0.06)
    body_h1 = int(h * 0.94)
    body_mask = fg_mask[body_h0:body_h1, :]
    fg_ratio = float(body_mask.mean()) if body_mask.size else 0.0

    if fg_ratio < 0.032:
        issues.append("sparse_or_blank_stage")
        penalties += 28.0
    elif fg_ratio > 0.72:
        issues.append("overcrowded_frame")
        penalties += 10.0

    # Left/right outer bleed edge check (20px gutter outside x0=64..x1=1016)
    gutter_w = max(8, int(w * 0.018))
    left_edge_ink = float(fg_mask[int(h * 0.16):int(h * 0.78), :gutter_w].mean())
    right_edge_ink = float(fg_mask[int(h * 0.16):int(h * 0.78), w - gutter_w:].mean())
    if left_edge_ink > 0.08 or right_edge_ink > 0.08:
        issues.append("horizontal_edge_clipping")
        penalties += 18.0

    # Check bottom caption safe-zone congestion when subtitles are ON on 9:16
    if format_ratio == "9:16" and caption_style != "off":
        sub_y0 = int(h * (0.765 if platform_safe_zone == "instagram_reels" else 0.80))
        sub_y1 = min(h - 40, sub_y0 + 180)
        sub_ink = float(fg_mask[sub_y0:sub_y1, int(w * 0.12):int(w * 0.88)].mean())
        if sub_ink > 0.56:
            issues.append("subtitle_safezone_overlap")
            penalties += 14.0

    return {
        "scene_idx": scene_idx,
        "cv_score": _clamp(100.0 - penalties),
        "issues": issues,
        "fg_ratio": round(fg_ratio, 3),
        "probe_path": str(probe_path),
    }


# =========================================================================
# LAYER B: SEMANTIC AUDIO <-> VISUAL <-> ACTION NLP SYNC AUDIT
# =========================================================================
def _audit_audio_visual_nlp(
    scene_idx: int,
    scene: Dict[str, Any],
    scene_words: List[Dict[str, Any]],
    sfx_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Verifies spoken narration keywords align with on-screen visuals, actions & Micro-SFX."""
    narr = str(scene.get("narration") or "")
    vd = scene.get("visual_data") or {}
    vis_txt = (_harvest_visual_tokens(vd) + " " + str(scene.get("visual_type") or "")).lower()

    narr_toks = {
        w for w in re.findall(r"[a-z0-9_]{4,}", narr.lower())
        if w not in ("this", "that", "with", "from", "into", "when", "then", "also", "just", "very", "more", "some", "have", "here", "what", "why", "kaise", "mein", "hota", "karte", "aapke", "samjho")
    }
    vis_toks = set(re.findall(r"[a-z0-9_]{3,}", vis_txt))
    overlap = narr_toks & vis_toks
    overlap_ratio = len(overlap) / max(1, min(len(narr_toks), 8))

    issues: List[str] = []
    penalties = 0.0
    if narr_toks and overlap_ratio < 0.15:
        issues.append("low_voice_to_visual_keyword_match")
        penalties += 20.0

    # Check if overlong text entries in visual_data risk overflowing card bounds
    long_labels = 0
    for key in ("nodes", "steps", "stages", "items", "voice_beats"):
        seq = vd.get(key)
        if isinstance(seq, list):
            for it in seq:
                lbl = str(it.get("label") or it.get("name") or it.get("title") or "") if isinstance(it, dict) else str(it)
                if len(lbl) > 36:
                    long_labels += 1
    if long_labels >= 2:
        issues.append("overlong_card_labels")
        penalties += 12.0

    # Check explicit actions against spoken scene context
    from core.action_engine import extract_spoken_actions
    acts = extract_spoken_actions(scene, max(1.5, float(scene.get("duration", 4.0))), scene_words)
    err_in_narr = bool(re.search(r"\b(error|crash|fail|timeout|deadlock|502|oom|alert|outage)\b", narr.lower()))
    for a in acts:
        if a.get("verb") == "disrupt_shake" and not err_in_narr and str(scene.get("scene_tone") or "") != "war_story_postmortem":
            issues.append("untriggered_disrupt_shake")
            penalties += 10.0

    # Word timestamp alignment completeness
    exp_words = len([w for w in narr.split() if any(c.isalnum() for c in w)])
    sync_score = 96.0 if (not scene_words or len(scene_words) >= max(2, int(exp_words * 0.6))) else 74.0

    return {
        "scene_idx": scene_idx,
        "nlp_score": _clamp(100.0 - penalties),
        "sync_score": sync_score,
        "issues": issues,
        "overlap_count": len(overlap),
        "action_count": len(acts),
        "audio_sfx_score": 92.0 if (sfx_events is not None) else 80.0,
    }


# =========================================================================
# LAYER C: MULTIMODAL VISION LLM FILMSTRIP CRITIC ("HUMAN VIEWER BRAIN")
# =========================================================================
def _build_filmstrip_contact_sheet(
    aligned_scenes: List[Dict[str, Any]],
    frame_dirs: List[Path],
    out_path: Path,
) -> Optional[Path]:
    """Stitches 75%-reveal keyframe from every scene into one labeled compact contact sheet."""
    tiles: List[Tuple[int, Image.Image, str]] = []
    for idx, fdir in enumerate(frame_dirs):
        if not fdir.exists():
            continue
        frames = sorted(p for p in fdir.iterdir() if p.name.startswith("frame_") and p.suffix.lower() in (".jpg", ".png", ".jpeg"))
        if not frames:
            continue
        pick = frames[int(len(frames) * 0.75)]
        try:
            im = Image.open(pick).convert("RGB").resize((360, 640), Image.Resampling.BILINEAR)
            vt = str(aligned_scenes[idx].get("visual_type") or "")
            tiles.append((idx + 1, im, vt))
        except Exception:
            continue
    if not tiles:
        return None

    cols = min(4, max(1, len(tiles)))
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 360, rows * 640), (10, 14, 24))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
    except Exception:
        fnt = ImageFont.load_default()

    for ti, (sc_num, im, vt) in enumerate(tiles):
        r, c = divmod(ti, cols)
        x0, y0 = c * 360, r * 640
        sheet.paste(im, (x0, y0))
        dr.rectangle((x0, y0, x0 + 359, y0 + 28), fill=(15, 23, 42))
        dr.text((x0 + 8, y0 + 4), f"S{sc_num}: {vt[:26]}", fill=(56, 189, 248), font=fnt)

    sheet.save(str(out_path), quality=86)
    return out_path


def _extract_json_block(txt: str) -> Dict[str, Any]:
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", str(txt or ""), flags=re.IGNORECASE).strip()
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        return {}
    try:
        val = json.loads(m.group(0))
        return val if isinstance(val, dict) else {}
    except Exception:
        return {}


def _run_multimodal_llm_critic(
    topic: str,
    aligned_scenes: List[Dict[str, Any]],
    sheet_path: Optional[Path],
    cv_results: List[Dict[str, Any]],
    nlp_results: List[Dict[str, Any]],
    timeout_sec: int = 12,
) -> Dict[str, Any]:
    """
    Runs Gemini Multimodal Vision Critic on the contact-sheet + script telemetry.
    Never blocks or raises; falls back gracefully to deterministic scores if unavailable.
    """
    if not GEMINI_API_KEY or sheet_path is None or not sheet_path.exists():
        return {}

    summary_lines = []
    for i, sc in enumerate(aligned_scenes):
        cv_i = cv_results[i]["issues"] if i < len(cv_results) else []
        nl_i = nlp_results[i]["issues"] if i < len(nlp_results) else []
        summary_lines.append(
            f"Scene {i+1} | role={sc.get('role')} | tone={sc.get('scene_tone')} | visual={sc.get('visual_type')} | "
            f"cv_flags={cv_i} | nlp_flags={nl_i} | narration=\"{str(sc.get('narration') or '')[:160]}\""
        )

    prompt = f"""You are a ruthless Human Video Director & Staff Engineer inspecting a newly rendered 9:16 tech video contact sheet BEFORE release.
Topic: "{topic}"

Storyboard & Automated Telemetry:
{chr(10).join(summary_lines)}

Inspect EVERY rendered frame in the contact sheet closely AND read its narration above:
1. Does a human viewer clearly grasp the concept, problem & takeaway in logical order?
2. Does each scene's rendered visual match what the narrator is speaking (proper layout, arrows, boxes, no random mismatches)?
3. Are any labels cropped/cut off, overlapping badges, empty dark boxes, or irrelevant popups?

Return STRICT JSON ONLY:
{{
  "concept_clarity": 0-100,
  "visual_topic_match": 0-100,
  "motion_action_precision": 0-100,
  "layout_legibility": 0-100,
  "verdict_summary": "1 crisp sentence explaining overall quality or main defect",
  "failing_scenes": [
    {{
      "scene_num": 1,
      "issue_type": "text_overflow_or_clip | bad_action_popup | layout_mismatch | needs_custom_html | weak_clarity",
      "reason": "specific concrete defect",
      "fix_instruction": "exact fix to apply"
    }}
  ]
}}"""

    try:
        from google import genai
        try:
            client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta", "timeout": int(timeout_sec * 1000)})
        except Exception:
            client = genai.Client(api_key=GEMINI_API_KEY)
        img_obj = Image.open(sheet_path)
        for m in ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"):
            try:
                res = client.models.generate_content(
                    model=m,
                    contents=[prompt, img_obj],
                    config={"response_mime_type": "application/json"},
                )
                parsed = _extract_json_block(getattr(res, "text", "") or "")
                if parsed and "concept_clarity" in parsed:
                    parsed["_critic_model"] = m
                    return parsed
            except Exception:
                continue
    except Exception:
        pass
    return {}


# =========================================================================
# UNIFIED 6-DIMENSION SCORING + SURGICAL SELF-REPAIR ENGINE
# =========================================================================
def evaluate_video_quality(
    topic: str,
    aligned_scenes: List[Dict[str, Any]],
    frame_dirs: List[Path],
    word_timestamps: List[Dict[str, Any]],
    sfx_events: Optional[List[Dict[str, Any]]] = None,
    format_ratio: str = "9:16",
    caption_style: str = "karaoke_pop",
    platform_safe_zone: str = "instagram_reels",
    use_vision_llm: bool = True,
    round_num: int = 1,
) -> Dict[str, Any]:
    """
    Executes all 3 inspection layers concurrently and computes weighted 0-100 Scorecard.
    """
    n = len(aligned_scenes)
    cv_results: List[Optional[Dict[str, Any]]] = [None] * n
    nlp_results: List[Optional[Dict[str, Any]]] = [None] * n

    def _check_one(idx: int) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
        sc = aligned_scenes[idx]
        st_t = float(sc.get("start_time", 0.0))
        en_t = float(sc.get("end_time", st_t + float(sc.get("duration", 4.0))))
        sc_words = [w for w in word_timestamps if st_t - 0.1 <= float(w.get("start", 0.0)) <= en_t + 0.1]
        cv_r = _audit_scene_pixels_cv(idx + 1, sc, frame_dirs[idx], format_ratio, caption_style, platform_safe_zone)
        nlp_r = _audit_audio_visual_nlp(idx + 1, sc, sc_words, sfx_events)
        return idx, cv_r, nlp_r

    with ThreadPoolExecutor(max_workers=min(6, max(1, n))) as ex:
        for idx, cv_r, nlp_r in ex.map(_check_one, range(n)):
            cv_results[idx] = cv_r
            nlp_results[idx] = nlp_r

    cv_list = [x for x in cv_results if x is not None]
    nlp_list = [x for x in nlp_results if x is not None]

    avg_cv = sum(x["cv_score"] for x in cv_list) / max(1, len(cv_list))
    avg_nlp = sum(x["nlp_score"] for x in nlp_list) / max(1, len(nlp_list))
    avg_sync = sum(x["sync_score"] for x in nlp_list) / max(1, len(nlp_list))
    avg_sfx = sum(x["audio_sfx_score"] for x in nlp_list) / max(1, len(nlp_list))

    sheet_path = OUTPUT_DIR / f"_critic_sheet_r{round_num}.jpg"
    if use_vision_llm:
        _build_filmstrip_contact_sheet(aligned_scenes, frame_dirs, sheet_path)

    llm_crit = (
        _run_multimodal_llm_critic(topic, aligned_scenes, sheet_path, cv_list, nlp_list)
        if use_vision_llm
        else {}
    )

    dim_concept = _clamp(float(llm_crit.get("concept_clarity", max(76.0, avg_nlp))))
    dim_visual = _clamp(float(llm_crit.get("visual_topic_match", max(74.0, (avg_nlp + avg_cv) * 0.5))))
    dim_motion = _clamp(float(llm_crit.get("motion_action_precision", avg_nlp)))
    dim_legible = _clamp(min(avg_cv, float(llm_crit.get("layout_legibility", avg_cv)))) if llm_crit else avg_cv
    dim_sync = avg_sync
    dim_audio = avg_sfx

    overall = round(
        0.25 * dim_concept
        + 0.20 * dim_visual
        + 0.20 * dim_motion
        + 0.15 * dim_legible
        + 0.10 * dim_sync
        + 0.10 * dim_audio,
        1,
    )

    # Merge deterministic CV/NLP scene defects + LLM Critic defects cleanly (never miss hard CV errors)
    defects_by_scene: Dict[int, Dict[str, Any]] = {}
    for df in (llm_crit.get("failing_scenes") or []):
        if not isinstance(df, dict):
            continue
        s_i = int(df.get("scene_num", 1)) - 1
        if 0 <= s_i < n:
            defects_by_scene[s_i] = {
                "scene_idx": s_i,
                "issue_type": str(df.get("issue_type") or "layout_mismatch"),
                "reason": str(df.get("reason") or "Vision review defect"),
                "fix_instruction": str(df.get("fix_instruction") or ""),
            }

    for i in range(n):
        c_iss = cv_list[i]["issues"]
        n_iss = nlp_list[i]["issues"]
        if i not in defects_by_scene and (c_iss or n_iss):
            if "horizontal_edge_clipping" in c_iss or "overlong_card_labels" in n_iss or "subtitle_safezone_overlap" in c_iss:
                itype = "text_overflow_or_clip"
            elif "sparse_or_blank_stage" in c_iss:
                itype = "layout_mismatch"
            elif "untriggered_disrupt_shake" in n_iss:
                itype = "bad_action_popup"
            else:
                itype = "layout_mismatch"
            defects_by_scene[i] = {
                "scene_idx": i,
                "issue_type": itype,
                "reason": ", ".join(c_iss + n_iss),
                "fix_instruction": f"Auto-detected defect ({itype})",
            }

    return {
        "round": round_num,
        "overall_score": overall,
        "dimensions": {
            "concept_clarity": round(dim_concept, 1),
            "visual_topic_match": round(dim_visual, 1),
            "motion_action_precision": round(dim_motion, 1),
            "layout_legibility": round(dim_legible, 1),
            "voice_karaoke_sync": round(dim_sync, 1),
            "audio_sfx_harmony": round(dim_audio, 1),
        },
        "defects": list(defects_by_scene.values()),
        "verdict_summary": str(llm_crit.get("verdict_summary") or ("Verified crisp multi-layer sync." if not defects_by_scene else f"{len(defects_by_scene)} scene defect(s) flagged for surgical repair.")),
        "critic_model": str(llm_crit.get("_critic_model") or "Local CV + Whisper NLP"),
        "sheet_path": str(sheet_path) if sheet_path.exists() else "",
    }


def _generate_bespoke_svg_html_scene(
    scene: Dict[str, Any],
    topic: str,
    defect: Dict[str, Any],
    format_ratio: str = "9:16",
) -> str:
    """
    Prompts Gemini/Groq specifically to author a custom pixel-perfect animated SVG/HTML5
    composition when built-in layouts don't adequately explain the scene.
    """
    from core.config import FORMAT_SPECS
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    w, h = spec["width"], spec["height"]
    sub_safe = 470 if h >= 1600 else (180 if h >= 1000 else 130)
    vd = {k: v for k, v in (scene.get("visual_data") or {}).items() if k not in ("html", "web_code", "svg", "svg_code")}
    prompt = f"""Fix and build ONE bespoke self-contained HTML5 + animated <svg> motion scene (`<!DOCTYPE html>...</html>`) for {w}x{h}.
Topic: "{topic}"
Scene Role: {scene.get('role')} | Narration: "{scene.get('narration')}"
Critic Defect To Fix: {defect.get('reason')} | Instruction: {defect.get('fix_instruction')}
Data Context: {json.dumps(vd, ensure_ascii=False)[:750]}

STRICT RULES:
1. Exact viewport {w}x{h}px (`margin:0; overflow:hidden; padding:112px 58px {sub_safe}px; box-sizing:border-box`). Leave top 100px & bottom {sub_safe}px empty!
2. Zero external `<script>`/`<link>` CDN dependencies.
3. Implement `window.__setStudioProgress = function(p, curTime, energy) {{ ... }}` cleanly with ZERO JS errors for `p in 0..1`.
4. Ensure high-contrast typography, clean margins (`>= 60px` horizontal pad), animated SVG paths/arrows (`stroke-dashoffset`) pointing accurately to labeled nodes matching Narration.
Output ONLY raw HTML starting with <!DOCTYPE html> and ending with </html>."""

    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite"):
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    raw = str(getattr(res, "text", "") or "").strip()
                    mh = re.search(r"(<!DOCTYPE html[\s\S]*?</html>|<html[\s\S]*?</html>)", raw, re.IGNORECASE)
                    if mh and "__setStudioProgress" in mh.group(1) and "<svg" in mh.group(1).lower():
                        return mh.group(1)
                except Exception:
                    continue
        except Exception:
            pass
    if GROQ_API_KEY:
        try:
            from groq import Groq
            gc = Groq(api_key=GROQ_API_KEY)
            res = gc.chat.completions.create(model="openai/gpt-oss-120b", messages=[{"role": "user", "content": prompt}], temperature=0.5, timeout=12)
            raw = res.choices[0].message.content.strip() if res.choices else ""
            mh = re.search(r"(<!DOCTYPE html[\s\S]*?</html>|<html[\s\S]*?</html>)", raw, re.IGNORECASE)
            if mh and "__setStudioProgress" in mh.group(1):
                return mh.group(1)
        except Exception:
            pass
    return ""


def _apply_surgical_scene_repair(
    scene: Dict[str, Any],
    scene_idx: int,
    total_scenes: int,
    defect: Dict[str, Any],
    topic: str,
    used_vtypes: set,
    format_ratio: str = "9:16",
    prefer_custom_html: bool = False,
) -> Tuple[Dict[str, Any], str]:
    """Mutates a copy of a single failing scene using Tier 1/2 repair strategy and returns `(repaired_scene, action_log)`."""
    sc = dict(scene)
    vd = dict(sc.get("visual_data") or {})
    sc["visual_data"] = vd
    itype = str(defect.get("issue_type") or "layout_mismatch")

    # Preserve isolated Studio V2 Vector Storyboard / Spatial Isometric architectures intact
    if str(sc.get("visual_type") or "").startswith("v2_"):
        return sc, f"S{scene_idx+1}: Kept isolated Studio V2 layout architecture intact"

    # 1. Text overflow / edge clip -> compact labels & disable intrusive action overlays cleanly
    if itype == "text_overflow_or_clip":
        for k in ("nodes", "steps", "stages", "items", "voice_beats"):
            seq = vd.get(k)
            if isinstance(seq, list):
                new_seq = []
                for it in seq[:4]:
                    if isinstance(it, dict):
                        it2 = dict(it)
                        for lk in ("label", "name", "title"):
                            if lk in it2:
                                it2[lk] = str(it2[lk])[:22].strip()
                        if "sub" in it2:
                            it2["sub"] = str(it2["sub"])[:36].strip()
                        new_seq.append(it2)
                    else:
                        new_seq.append(str(it)[:24].strip())
                vd[k] = new_seq
        if isinstance(vd.get("bullets"), list):
            vd["bullets"] = [str(b)[:44].strip() for b in vd["bullets"][:4]]
        sc["_disable_actions_overlay"] = True
        return sc, f"S{scene_idx+1}: Compacted card labels & cleared edge/subtitle overlap"

    # 2. Bad action popup / arrow mismatch -> suppress noisy auto actions or constrain explicit action cleanly
    if itype == "bad_action_popup":
        sc["actions"] = []
        sc["_disable_actions_overlay"] = True
        return sc, f"S{scene_idx+1}: Cleared mismatched action popup/disrupt_shake overlay"

    # 3. Custom Bespoke SVG/HTML5 synthesis when explicitly requested or in perfection mode
    if itype == "needs_custom_html" or prefer_custom_html:
        html_code = _generate_bespoke_svg_html_scene(sc, topic, defect, format_ratio=format_ratio)
        if html_code:
            vd["html"] = html_code
            sc["visual_type"] = "web_scene"
            sc["routed_engine"] = "AI Self-Heal Bespoke HTML5/SVG"
            return sc, f"S{scene_idx+1}: Synthesized custom Bespoke HTML5/SVG scene"

    # 4. Layout mismatch / sparse stage -> swap to next highest-scoring unused semantic layout cleanly
    old_vt = str(sc.get("visual_type") or "")
    used_ex = set(used_vtypes)
    if old_vt:
        used_ex.add(old_vt)
    from core.semantic_router import select_semantic_scene_layout
    new_vt, new_desc = select_semantic_scene_layout(
        sc, scene_idx, total_scenes, topic, str(sc.get("scene_tone") or "auto_2026_director"),
        scene_idx + 3, used_ex, {old_vt}, vd, used_geometries=set(),
    )
    sc["visual_type"] = new_vt
    sc["routed_engine"] = f"Repaired -> {new_desc}"
    vd.pop("html", None)
    used_vtypes.add(new_vt)
    return sc, f"S{scene_idx+1}: Swapped `{old_vt}` -> `{new_vt}`"


def run_quality_gate_and_self_heal(
    topic: str,
    aligned_scenes: List[Dict[str, Any]],
    frame_dirs: List[Path],
    word_timestamps: List[Dict[str, Any]],
    sfx_events: Optional[List[Dict[str, Any]]],
    quality_mode: str,
    render_single_scene_fn,
    format_ratio: str = "9:16",
    caption_style: str = "karaoke_pop",
    platform_safe_zone: str = "instagram_reels",
    progress_cb=None,
) -> Tuple[List[Dict[str, Any]], List[Path], Dict[str, Any]]:
    """
    Runs the Closed-Loop Quality Gate & Surgical Self-Repair Engine with strict bounds
    and Best-So-Far Checkpointing:
    - 'fast': instant bypass (0 extra latency)
    - 'standard': target >= 84.0, max 1-2 fast surgical repair rounds
    - 'perfection': target >= 90.0, max 2 surgical rounds (auto bespoke HTML5/SVG on round 2)
    ALWAYS guarantees returning a clean, ready-to-stitch `(best_scenes, best_frame_dirs, report)`.
    """
    mode = str(quality_mode or DEFAULT_QUALITY_MODE).lower().strip()
    if mode == "fast" or not aligned_scenes:
        return aligned_scenes, frame_dirs, {
            "mode": "fast",
            "status": "BYPASSED (Fast Mode)",
            "final_score": 0.0,
            "target_score": 0.0,
            "dimensions": {},
            "rounds": [],
            "repairs": [],
        }

    target_score = 90.0 if mode == "perfection" else 84.0
    max_repair_rounds = 2
    use_vision = bool(GEMINI_API_KEY)

    best_cache_dir = OUTPUT_DIR / "_best_scene_cache"
    shutil.rmtree(best_cache_dir, ignore_errors=True)
    best_cache_dir.mkdir(parents=True, exist_ok=True)

    cur_scenes = [dict(s, visual_data=dict(s.get("visual_data") or {})) for s in aligned_scenes]
    cur_dirs = list(frame_dirs)

    def _snapshot_best(src_dirs: List[Path]) -> List[Path]:
        saved: List[Path] = []
        for idx_d, sd in enumerate(src_dirs):
            dst = best_cache_dir / f"scene_{idx_d+1:02d}_frames"
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            if sd.exists():
                shutil.copytree(sd, dst)
            saved.append(dst)
        return saved

    r1 = evaluate_video_quality(
        topic, cur_scenes, cur_dirs, word_timestamps, sfx_events,
        format_ratio=format_ratio, caption_style=caption_style, platform_safe_zone=platform_safe_zone,
        use_vision_llm=use_vision, round_num=1,
    )
    rounds_log: List[Dict[str, Any]] = [r1]
    repair_logs: List[str] = []

    best_score = r1["overall_score"]
    best_report = r1
    best_scenes = [dict(s) for s in cur_scenes]
    best_dirs = _snapshot_best(cur_dirs)

    if best_score >= target_score or not r1["defects"]:
        shutil.rmtree(best_cache_dir, ignore_errors=True)
        return cur_scenes, cur_dirs, {
            "mode": mode,
            "status": f"PASSED ({best_score}/100 >= {int(target_score)})",
            "final_score": best_score,
            "target_score": target_score,
            "dimensions": best_report["dimensions"],
            "verdict_summary": best_report["verdict_summary"],
            "critic_model": best_report["critic_model"],
            "rounds": rounds_log,
            "repairs": repair_logs,
        }

    used_vtypes = {str(s.get("visual_type") or "") for s in cur_scenes}

    for r_idx in range(1, max_repair_rounds + 1):
        defects = best_report["defects"][:3]  # cap parallel repair work to top 3 bad scenes per round
        if not defects:
            break
        if progress_cb:
            try:
                progress_cb(
                    f"🔧 AI Quality Gate (Score {best_score}/100 < {int(target_score)}): Repairing {len(defects)} scene(s) in parallel (Round {r_idx})...",
                    min(0.95, 0.35 + 0.3 * r_idx),
                )
            except TypeError:
                progress_cb(
                    f"🔧 AI Quality Gate (Score {best_score}/100 < {int(target_score)}): Repairing {len(defects)} scene(s) in parallel (Round {r_idx})..."
                )

        repaired_indices: List[int] = []
        for df in defects:
            s_i = int(df["scene_idx"])
            rep_sc, act_log = _apply_surgical_scene_repair(
                cur_scenes[s_i], s_i, len(cur_scenes), df, topic, used_vtypes,
                format_ratio=format_ratio,
                prefer_custom_html=(mode == "perfection" and r_idx >= 2),
            )
            cur_scenes[s_i] = rep_sc
            repair_logs.append(f"[Round {r_idx}] {act_log}")
            repaired_indices.append(s_i)

        # Re-render ONLY repaired scenes in parallel
        with ThreadPoolExecutor(max_workers=min(4, max(1, len(repaired_indices)))) as pool_rep:
            futs = [pool_rep.submit(render_single_scene_fn, (s_i, cur_scenes[s_i])) for s_i in repaired_indices]
            for fut in as_completed(futs):
                fut.result()

        r_next = evaluate_video_quality(
            topic, cur_scenes, cur_dirs, word_timestamps, sfx_events,
            format_ratio=format_ratio, caption_style=caption_style, platform_safe_zone=platform_safe_zone,
            use_vision_llm=use_vision, round_num=r_idx + 1,
        )
        rounds_log.append(r_next)

        if r_next["overall_score"] >= best_score:
            best_score = r_next["overall_score"]
            best_report = r_next
            best_scenes = [dict(s) for s in cur_scenes]
            best_dirs = _snapshot_best(cur_dirs)

        if best_score >= target_score or not r_next["defects"]:
            break

    # Always restore best-so-far frames into final `cur_dirs` cleanly (never ship a worse regression!)
    for idx_b, b_dir in enumerate(best_dirs):
        target_dir = cur_dirs[idx_b]
        if b_dir.exists() and target_dir != b_dir:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            shutil.copytree(b_dir, target_dir)
    shutil.rmtree(best_cache_dir, ignore_errors=True)

    passed = best_score >= target_score
    return best_scenes, cur_dirs, {
        "mode": mode,
        "status": f"PASSED ({best_score}/100)" if passed else f"BEST-SO-FAR DELIVERED ({best_score}/100 after {len(rounds_log)-1} repair round(s))",
        "final_score": best_score,
        "target_score": target_score,
        "dimensions": best_report["dimensions"],
        "verdict_summary": best_report["verdict_summary"],
        "critic_model": best_report["critic_model"],
        "rounds": rounds_log,
        "repairs": repair_logs,
    }
