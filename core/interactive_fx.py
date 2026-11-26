"""
Interactive Effects & True Spoken-Word Storyboard Engine for NanoPro Studio.
- Aligns every scene component strictly to real spoken words (`scene_words` / `cue_phrase`).
- Renders rich micro-interactions: Bezier Cursor Glide, Click Ripple, Spotlight Focus,
  Focus Dimming, Marker Underline Swipe, Key-Term Pop, Contextual Thought/Warning/Pro-Tip/
  Status/Quiz/Split-Delta/Emoji Bubbles, and Drag-and-Drop Connector pulses.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


_FONT_CACHE: Dict[Tuple[int, bool], Any] = {}


def _fx_font(size: int, bold: bool = True) -> Any:
    key = (int(size), bool(bold))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = (
        [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    f = None
    for cp in candidates:
        if Path(cp).exists():
            try:
                f = ImageFont.truetype(cp, size)
                break
            except Exception:
                pass
    if f is None:
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else float(v))


def _ease_out_cubic(t: float) -> float:
    t = _clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def _ease_out_back(t: float) -> float:
    t = _clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _rgba(col: Tuple[int, ...], alpha: float) -> Tuple[int, int, int, int]:
    a = int(max(0, min(255, round(255.0 * _clamp01(alpha)))))
    return (int(col[0]), int(col[1]), int(col[2]), a)


# Mindset & rhetorical cue classifiers for contextual interactive bubbles
_CALM_CUES = {"relax", "chill", "easy", "calm", "sorted", "clear", "simple", "safe"}
_WARN_CUES = {"wait", "twist", "catch", "trap", "fail", "freeze", "lock", "crash", "slow", "bottleneck", "danger", "oom"}
_QUIZ_CUES = {"samjha", "think", "guess", "why", "how", "kya", "kyun", "socho", "right"}
_TIP_CUES = {"step", "chunk", "piece", "basics", "core", "breakdown", "layers", "flow", "secret", "hack", "shortcut"}
_DONE_CUES = {"boom", "done", "sorted", "verified", "fast", "zero", "shift", "magic"}


def detect_spoken_fx_cue(words_window: str) -> Tuple[str, str]:
    """Classifies what interactive bubble type fits the currently spoken phrase."""
    low = re.sub(r"[^a-z0-9\s%x-]", " ", str(words_window or "").lower())
    toks = set(low.split())
    if re.search(r"\b\d+\s*(x|%|ms|k|m)\b", low) or "farak" in toks or "vs" in toks:
        m = re.search(r"\b(\d+\s*(?:x|%|ms|k|m))\b", low)
        return "delta", (f"DELTA {m.group(1).upper()}" if m else "DELTA SHIFT")
    if toks & _WARN_CUES:
        for w in ("Twist", "Catch", "Wait", "Bottleneck", "Trap"):
            if w.lower() in toks:
                return "warn", f"! {w.upper()}"
        return "warn", "! WATCH OUT"
    if toks & _QUIZ_CUES:
        for w in ("Samjha?", "Think...", "Why?", "How?", "Guess?"):
            base = w.rstrip("?.").lower()
            if base in toks:
                return ("thought" if base in ("think", "socho", "guess") else "quiz"), w
        return "quiz", "? QUICK CHECK"
    if toks & _DONE_CUES:
        return "status", "SORTED"
    if toks & _TIP_CUES:
        return "tip", "PRO TIP"
    if toks & _CALM_CUES:
        return "calm", "EASY FLOW"
    return "none", ""


def _token_fuzzy_match(kw: str, wt: str) -> bool:
    """Matches Whisper Hinglish/technical phonetic variants cleanly (e.g. 'cache'/'caching', 'latency'/'latancy')."""
    if kw == wt or (len(kw) >= 4 and (kw in wt or wt in kw)):
        return True
    if len(kw) >= 5 and len(wt) >= 5 and kw[:4] == wt[:4]:
        return True
    return False


def _extract_component_keywords(scene: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Extracts ordered (label, keyword_tokens) pairs for progressive storyboard matching."""
    vd = scene.get("visual_data") or {}
    raw_items: List[Any] = []
    for k in ("nodes", "steps", "stages", "milestones", "voice_beats", "sub_points", "items", "bullets", "satellites", "bars", "entries"):
        val = vd.get(k)
        if isinstance(val, list) and val:
            raw_items = val[:6]
            break
    if not raw_items and vd.get("comp1_label"):
        raw_items = [
            {"label": vd.get(f"comp{i}_label", ""), "cue": vd.get(f"comp{i}_sub", "")}
            for i in range(1, 6) if vd.get(f"comp{i}_label")
        ]
    if not raw_items and (vd.get("left_points") or vd.get("right_points")):
        lp = vd.get("left_points") or []
        rp = vd.get("right_points") or []
        raw_items = [{"label": x} for x in (list(lp[:2]) + list(rp[:3]))]

    out: List[Tuple[str, str]] = []
    for idx, it in enumerate(raw_items):
        if isinstance(it, dict):
            lbl = str(it.get("label") or it.get("name") or it.get("title") or it.get("op") or f"Stage {idx+1}").strip()
            cue = str(it.get("cue_phrase") or it.get("keyword") or f"{lbl} {it.get('sub') or it.get('desc') or ''}").strip()
        else:
            lbl = str(it).strip()
            cue = lbl
        out.append((lbl[:32], cue.lower()))
    return out


def compute_voice_stage_timeline(
    scene: Dict[str, Any],
    duration: float,
    scene_words: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Maps every visual component (`stage 0..n-1`) directly to the exact spoken word timestamp
    when its concept appears in `scene_words` (true voice-locked storyboard timing).
    """
    duration = max(1.0, float(duration or 5.0))
    sc_start = float(scene.get("start_time", 0.0))
    comps = _extract_component_keywords(scene)
    choreo = scene.get("choreography") if isinstance(scene.get("choreography"), dict) else {}
    trigs = list(choreo.get("triggers") or [])

    n = max(len(comps), len(trigs), 4)
    clean_words: List[Tuple[str, float, float, str]] = []
    if scene_words:
        for w in scene_words:
            raw = str(w.get("word", "")).strip()
            norm = re.sub(r"[^a-z0-9\u0900-\u097f]", "", raw.lower())
            if norm:
                ws = (float(w.get("start", sc_start)) - sc_start) / duration
                we = (float(w.get("end", ws * duration + sc_start + 0.2)) - sc_start) / duration
                clean_words.append((norm, _clamp01(ws), _clamp01(we), raw))

    cue_times: List[float] = []
    labels: List[str] = []
    cursor = 0
    prev_t = -0.05

    for idx in range(n):
        lbl = comps[idx][0] if idx < len(comps) else f"Stage {idx + 1}"
        labels.append(lbl)
        kw_pool: List[str] = []
        if idx < len(trigs) and isinstance(trigs[idx], dict):
            tk = re.sub(r"[^a-z0-9\u0900-\u097f\s]", " ", str(trigs[idx].get("keyword", "")).lower())
            kw_pool.extend([t for t in tk.split() if len(t) >= 3])
        if idx < len(comps):
            ck = re.sub(r"[^a-z0-9\u0900-\u097f\s]", " ", comps[idx][1])
            kw_pool.extend([t for t in ck.split() if len(t) >= 4])

        found_t: Optional[float] = None
        if clean_words and kw_pool:
            # Scan forward monotonically in spoken narration so later components never fire early
            search_limit = len(clean_words)
            for wi in range(cursor, search_limit):
                wt = clean_words[wi][0]
                if any(_token_fuzzy_match(kw, wt) for kw in kw_pool if len(kw) >= 3):
                    found_t = clean_words[wi][1]
                    cursor = min(len(clean_words) - 1, wi + 1)
                    break

        if found_t is None:
            if idx == 0:
                found_t = 0.02
            else:
                remaining = max(1, n - idx)
                span_left = max(0.08, 0.80 - max(0.02, prev_t))
                found_t = min(0.84, max(0.02, prev_t) + span_left / float(remaining + 0.4))
                if clean_words:
                    est_wi = min(len(clean_words) - 1, int((idx / max(1, n)) * len(clean_words) * 0.82))
                    word_t = clean_words[max(cursor, est_wi)][1]
                    found_t = 0.65 * word_t + 0.35 * found_t

        t_clamped = max(prev_t + 0.07, min(0.86, float(found_t)))
        if idx == 0:
            t_clamped = min(0.10, max(0.01, t_clamped))
        prev_t = t_clamped
        cue_times.append(round(t_clamped, 4))

    speaker_spans: List[Dict[str, Any]] = []
    raw_spans = scene.get("dialogue_spans")
    if isinstance(raw_spans, list) and raw_spans:
        for sp in raw_spans:
            if not isinstance(sp, dict):
                continue
            speaker_spans.append({
                "speaker": str(sp.get("speaker") or "male").lower(),
                "t0": _clamp01(float(sp.get("start", 0.0)) / duration),
                "t1": _clamp01(float(sp.get("end", duration)) / duration),
            })
    elif isinstance(scene.get("dialogue"), list) and scene.get("dialogue"):
        turns = [d for d in scene["dialogue"] if isinstance(d, dict) and str(d.get("text") or "").strip()]
        total_w = max(1, sum(max(1, len(str(d.get("text", "")).split())) for d in turns))
        cur_w = 0
        for d in turns:
            w_cnt = max(1, len(str(d.get("text", "")).split()))
            speaker_spans.append({
                "speaker": str(d.get("speaker") or "male").lower(),
                "t0": round(cur_w / float(total_w), 4),
                "t1": round((cur_w + w_cnt) / float(total_w), 4),
            })
            cur_w += w_cnt

    return {
        "n": n,
        "cue_times": cue_times,
        "labels": labels,
        "words": clean_words,
        "speaker_spans": speaker_spans,
    }


def eval_voice_gates(timeline_cues: Dict[str, Any], linear_p: float, total_stages: int = 0) -> Dict[str, Any]:
    """Evaluates per-stage progressive values `[0..1]` and active voice FX context at `linear_p`."""
    p = _clamp01(linear_p)
    cue_times = list(timeline_cues.get("cue_times") or [0.02, 0.24, 0.48, 0.70])
    labels = list(timeline_cues.get("labels") or [])
    n_cues = len(cue_times)
    n_target = max(1, total_stages or n_cues)

    gates: List[float] = []
    for i in range(n_target):
        if i < n_cues:
            t0 = cue_times[i]
            nxt = cue_times[i + 1] if i + 1 < n_cues else 0.96
        else:
            t0 = 0.02 + (i / float(n_target)) * 0.74
            nxt = 0.02 + ((i + 1) / float(n_target)) * 0.74
        rise_span = max(0.14, min(0.28, (nxt - t0) * 1.15))
        g = _clamp01((p - t0) / rise_span)
        if p >= 0.96:
            g = 1.0
        gates.append(round(g, 4))

    # Active stage is the latest component whose cue_time has already arrived
    active_idx = 0
    for i, ct in enumerate(cue_times):
        if p >= ct - 0.01:
            active_idx = i

    t_active = cue_times[min(active_idx, len(cue_times) - 1)] if cue_times else 0.0
    ripple_t = _clamp01((p - t_active) / 0.16)

    # Identify currently spoken word & short phrase window
    cur_word = ""
    phrase_win = ""
    words = timeline_cues.get("words") or []
    for wi, (wnorm, ws, we, wraw) in enumerate(words):
        if ws - 0.04 <= p <= we + 0.06:
            cur_word = wraw
            lo = max(0, wi - 2)
            hi = min(len(words), wi + 2)
            phrase_win = " ".join(words[k][3] for k in range(lo, hi))
            break
    if not cur_word and labels:
        cur_word = labels[min(active_idx, len(labels) - 1)]
        phrase_win = cur_word

    fx_type, fx_label = detect_spoken_fx_cue(phrase_win)
    active_speaker = ""
    for sp in (timeline_cues.get("speaker_spans") or []):
        if float(sp.get("t0", 0.0)) - 0.02 <= p <= float(sp.get("t1", 1.0)) + 0.02:
            active_speaker = str(sp.get("speaker") or "")
            break
    if not active_speaker and (timeline_cues.get("speaker_spans") or []):
        active_speaker = str(timeline_cues["speaker_spans"][-1].get("speaker") or "")

    return {
        "gates": gates,
        "cue_times": cue_times,
        "labels": labels,
        "active_idx": min(n_target - 1, active_idx),
        "ripple_t": ripple_t,
        "cur_word": cur_word,
        "phrase": phrase_win,
        "fx_type": fx_type,
        "fx_label": fx_label,
        "speaker": active_speaker,
        "linear_p": p,
    }


def _bezier_pt(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], t: float) -> Tuple[float, float]:
    u = 1.0 - t
    return (
        u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
    )


def render_interactive_fx_overlay(
    stage_img: Image.Image,
    world: Dict[str, Any],
    fx_state: Dict[str, Any],
    anchors: List[Tuple[int, int, str]],
    progress: float,
) -> Image.Image:
    """
    Composites voice-synced interactive micro-FX cleanly over the stage:
    - Expanding Click Ripple on newly spoken stage anchor
    - Bezier Cursor Glide traveling smoothly to current stage
    - Contextual Thought / Warning / Pro-Tip / Status / Mini-Quiz / Delta Bubble
    - Spoken Keyword Pop + Marker Underline Swipe at top-right HUD band
    """
    if not fx_state:
        return stage_img
    overlay = Image.new("RGBA", stage_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    cyan = world["cyan"]
    amber = world["amber"]
    emerald = world["emerald"]
    rose = world["rose"]
    purple = world["purple"]
    card_alt = world["card_alt"]
    text_col = world["text"]

    p = float(fx_state.get("linear_p", progress))
    active_idx = int(fx_state.get("active_idx", 0))
    ripple_t = float(fx_state.get("ripple_t", 1.0))
    cur_word = str(fx_state.get("cur_word") or "").strip()
    fx_type = str(fx_state.get("fx_type") or "none")
    fx_label = str(fx_state.get("fx_label") or "")

    # Deduplicate anchors by proximity so only distinct primary component cards get FX
    dedup: List[Tuple[int, int, str]] = []
    for ax, ay, albl in anchors:
        if ay < 360 or ay > 1540:
            continue
        if all(abs(ax - dx) > 90 or abs(ay - dy) > 85 for dx, dy, _ in dedup):
            dedup.append((ax, ay, albl))
    if not dedup:
        dedup = [(320, 620, "Stage 1"), (740, 820, "Stage 2"), (340, 1060, "Stage 3"), (740, 1280, "Stage 4")]

    n_a = len(dedup)
    tgt_idx = min(n_a - 1, active_idx % n_a)
    prev_idx = max(0, tgt_idx - 1)
    tx, ty, _ = dedup[tgt_idx]
    px, py, _ = dedup[prev_idx]

    # Glide cursor along quadratic Bezier path during first 45% of active beat
    glide_t = _ease_out_cubic(_clamp01(ripple_t / 0.42))
    ctrl_pt = ((px + tx) * 0.5 + (65 if tgt_idx % 2 == 0 else -65), min(py, ty) - 45)
    cx, cy = _bezier_pt((float(px), float(py)), ctrl_pt, (float(tx), float(ty)), glide_t)

    # 1. Click Ripple & Pulse Ring on active spoken component
    if 0.03 < ripple_t < 0.96:
        r1 = int(18 + 62 * _ease_out_cubic(ripple_t))
        r2 = int(10 + 40 * _ease_out_cubic(ripple_t))
        fade = (1.0 - ripple_t) * 0.85
        draw.ellipse((tx - r1, ty - r1, tx + r1, ty + r1), outline=_rgba(cyan, fade), width=3)
        draw.ellipse((tx - r2, ty - r2, tx + r2, ty + r2), outline=_rgba(emerald, fade * 0.8), width=2)

    # 2. Active Drag/Focus Glow Dot at anchor handle
    pulse = 0.5 + 0.5 * math.sin(p * math.pi * 8.0)
    draw.ellipse((tx - 9, ty - 9, tx + 9, ty + 9), fill=_rgba(cyan, 0.28 + 0.25 * pulse), outline=_rgba(cyan, 0.85), width=2)

    # 2b. Drag-and-Drop Dashed Connector Preview + Hover Preview Pill toward upcoming stage during cursor glide
    if n_a > tgt_idx + 1 and 0.04 < p < 0.88:
        nx, ny, _ = dedup[tgt_idx + 1]
        steps_d = 8
        for si in range(steps_d):
            if si % 2 == 0:
                f0, f1 = si / steps_d, (si + 0.7) / steps_d
                sx0, sy0 = int(cx + (nx - cx) * f0), int(cy + (ny - cy) * f0)
                sx1, sy1 = int(cx + (nx - cx) * f1), int(cy + (ny - cy) * f1)
                draw.line((sx0, sy0, sx1, sy1), fill=_rgba(purple, 0.42), width=2)
        draw.ellipse((nx - 7, ny - 7, nx + 7, ny + 7), outline=_rgba(purple, 0.65), width=2)
        nxt_lbl = (fx_state.get("labels") or [])[min(len(fx_state.get("labels") or []) - 1, tgt_idx + 1)] if fx_state.get("labels") else ""
        if nxt_lbl and ripple_t < 0.55:
            f_hp = _fx_font(16, bold=True)
            htxt = f"NEXT -> {nxt_lbl[:18]}"
            hbb = f_hp.getbbox(htxt)
            hw = (hbb[2] - hbb[0]) + 22
            hx = max(60, min(stage_img.width - hw - 60, int(cx + 18)))
            hy = max(390, int(cy + 34))
            draw.rounded_rectangle((hx, hy, hx + hw, hy + 28), radius=10, fill=_rgba(card_alt, 0.85), outline=_rgba(purple, 0.72), width=1)
            draw.text((hx + 10, hy + 5), htxt, font=f_hp, fill=_rgba(text_col, 0.90))

    # 3. Clean Bezier Vector Cursor Arrow at (cx, cy)
    if 0.02 < p < 0.96:
        c_pts = [
            (cx, cy),
            (cx + 22, cy + 12),
            (cx + 12, cy + 16),
            (cx + 18, cy + 28),
            (cx + 12, cy + 31),
            (cx + 6, cy + 19),
            (cx, cy + 26),
        ]
        draw.polygon(c_pts, fill=_rgba((255, 255, 255), 0.94), outline=_rgba(cyan, 0.95), width=2)

    # 4. Spoken Key-Term Pop + Marker Underline Swipe (Right of Scene Header, y=318..366)
    clean_kw = re.sub(r"[^A-Za-z0-9\-\+\.%]", "", cur_word)[:18]
    if clean_kw and 0.02 < p < 0.98:
        f_kw = _fx_font(20, bold=True)
        kw_txt = f"• {clean_kw.upper()}"
        kbb = f_kw.getbbox(kw_txt)
        kw_w = min(310, (kbb[2] - kbb[0]) + 34)
        kx1 = stage_img.width - 44
        kx0 = kx1 - kw_w
        ky0, ky1 = 316, 356
        draw.rounded_rectangle((kx0, ky0, kx1, ky1), radius=14, fill=_rgba(card_alt, 0.92), outline=_rgba(amber, 0.85), width=2)
        draw.text((kx0 + 14, ky0 + 8), kw_txt, font=f_kw, fill=_rgba(amber, 0.98))
        # Animated Marker Underline Swipe inside badge
        swipe_t = _ease_out_cubic(min(1.0, (p * 12.0) % 1.0 + 0.25))
        draw.line((kx0 + 14, ky1 - 5, int(kx0 + 14 + (kw_w - 28) * swipe_t), ky1 - 5), fill=_rgba(cyan, 0.95), width=3)

    # 4b. Dual Dialogue Live Speaker Pill (Top-Left HUD beside Spoken Keyword Pop, y=316..356)
    active_speaker = str(fx_state.get("speaker") or "").strip().lower()
    if active_speaker in ("female", "male") and 0.01 < p < 0.99:
        f_sp = _fx_font(19, bold=True)
        if active_speaker == "female":
            sp_txt = "SHE ASKS ?"
            sp_col = rose
        else:
            sp_txt = "MENTOR SOLVES"
            sp_col = emerald
        sbb = f_sp.getbbox(sp_txt)
        sp_w = (sbb[2] - sbb[0]) + 46
        sx0, sy0, sy1 = 68, 316, 356
        draw.rounded_rectangle((sx0, sy0, sx0 + sp_w, sy1), radius=14, fill=_rgba(card_alt, 0.92), outline=_rgba(sp_col, 0.88), width=2)
        draw.ellipse((sx0 + 14, sy0 + 14, sx0 + 26, sy0 + 26), fill=_rgba(sp_col, 0.96))
        draw.text((sx0 + 34, sy0 + 8), sp_txt, font=f_sp, fill=_rgba(sp_col, 0.98))

    # 5. Contextual Thought Cloud / Mini Quiz / Warning / Pro-Tip / Status+Sparkle Burst / Split Delta Bubble
    if fx_type != "none" and fx_label and 0.04 < p < 0.95:
        b_col = rose if fx_type == "warn" else (purple if fx_type in ("quiz", "thought") else (emerald if fx_type in ("status", "delta") else amber))
        f_bub = _fx_font(19, bold=True)
        bbb = f_bub.getbbox(fx_label)
        bw = (bbb[2] - bbb[0]) + 36
        bx = max(84, min(stage_img.width - bw - 84, int(tx - bw // 2)))
        by = max(368, int(ty - 114))
        pop_a = _ease_out_back(min(1.0, ripple_t * 2.2)) * 0.95
        if fx_type == "thought":
            # Cloud scalloped thought bubble with trailing circles
            draw.rounded_rectangle((bx, by, bx + bw, by + 38), radius=19, fill=_rgba(card_alt, pop_a), outline=_rgba(b_col, pop_a), width=2)
            draw.ellipse((bx + 6, by - 10, bx + 32, by + 16), fill=_rgba(card_alt, pop_a), outline=_rgba(b_col, pop_a), width=2)
            draw.ellipse((bx + bw - 34, by - 10, bx + bw - 8, by + 16), fill=_rgba(card_alt, pop_a), outline=_rgba(b_col, pop_a), width=2)
            draw.ellipse((int(tx) - 5, by + 40, int(tx) + 5, by + 50), fill=_rgba(b_col, pop_a))
            draw.ellipse((int(tx) - 3, by + 54, int(tx) + 3, by + 60), fill=_rgba(b_col, pop_a))
        else:
            draw.rounded_rectangle((bx, by, bx + bw, by + 38), radius=19, fill=_rgba(card_alt, pop_a), outline=_rgba(b_col, pop_a), width=2)
            tail_x = max(bx + 14, min(bx + bw - 14, int(tx)))
            draw.polygon([(tail_x - 6, by + 37), (tail_x + 6, by + 37), (tail_x, by + 46)], fill=_rgba(b_col, pop_a))
        draw.text((bx + 18, by + 8), fx_label, font=f_bub, fill=_rgba(b_col, pop_a))
        if fx_type == "status" and ripple_t < 0.72:
            # Radial Neon Vector Sparkle Burst (Emoji/Burst FX)
            for bi in range(8):
                ang = bi * (math.pi / 4.0)
                r_in = int(26 + 26 * ripple_t)
                r_out = int(38 + 38 * ripple_t)
                sc_col = emerald if bi % 2 == 0 else cyan
                draw.line(
                    (int(tx + r_in * math.cos(ang)), int(ty + r_in * math.sin(ang)),
                     int(tx + r_out * math.cos(ang)), int(ty + r_out * math.sin(ang))),
                    fill=_rgba(sc_col, (1.0 - ripple_t) * 0.9), width=3,
                )

    return Image.alpha_composite(stage_img.convert("RGBA"), overlay)
