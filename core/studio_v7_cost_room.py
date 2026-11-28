"""
Studio V7 — Agent Cost & Latency Control Room Renderer.

A finance/observability "control room" engine for the topic:
"AI Agent Cost & Latency — Token Bloat Aur Extra LLM Calls Kaise Kam Karein?"

Signature components (9:16 vertical, full-motion, deterministic):
  - Live Cost Meter   : per-request $ gauge (Naive vs Optimized)
  - Token Stack       : stacked breakdown (history / system / tool schema / few-shot / task)
  - Call Ledger       : tabular per-call cost+latency ledger (monospace, tabular-nums)
  - Burn Curve        : cumulative spend sparkline
  - Anti-Pattern Scan : red-flag scanner over wasteful patterns
  - Optimization Levers: caching / summarization / routing+early-exit
  - Latency Waterfall : TTFT -> tool -> model -> retry -> network
  - Savings Badge     : -72% cost, -64% latency, 90% cache hit

Driven by `window.__setStudioProgress(linP, wordP)` (voice-synced, arg_order="lp_wp").
10-scene arc: cost_hook -> token_bloat_anatomy -> call_bloat_ledger -> anti_pattern_scan ->
cost_compare -> fix_caching -> fix_summarize -> fix_route_earlyexit -> latency_waterfall -> verdict_savings.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS
from core.tone_engine import get_tone_profile

_ACCENT_HEX = {
    "cyan": "#38BDF8",
    "slate": "#64748B",
    "blue": "#60A5FA",
    "emerald": "#10B981",
    "violet": "#A855F7",
    "purple": "#A855F7",
    "amber": "#F59E0B",
    "rose": "#EF4444",
}

_VALID_MODES = {
    "cost_hook",
    "token_bloat_anatomy",
    "call_bloat_ledger",
    "anti_pattern_scan",
    "cost_compare",
    "fix_caching",
    "fix_summarize",
    "fix_route_earlyexit",
    "latency_waterfall",
    "verdict_savings",
    "cta",
}


def _tone_cost_motion(tone: str, role: str, scene_tone: Optional[str]) -> Dict[str, float]:
    """Maps Script Tone to meter sweep + scanner speed (voice-sync feel)."""
    prof = get_tone_profile(tone, scene_tone=scene_tone, role=role)
    t_key = prof.get("key", "whiteboard_analogy")
    if t_key in ("fireship_octane", "youth_friend_turbo", "cage_match_vs", "myth_buster_contrarian"):
        return {"sweep": 1.18, "scan": 1.30, "pulse": 1.25}
    if t_key in ("war_story_postmortem", "dramatic_performance", "bigtech_reverse_engineer"):
        return {"sweep": 1.05, "scan": 1.08, "pulse": 1.05}
    return {"sweep": 1.0, "scan": 1.0, "pulse": 1.0}


_DEF_NAIVE = {
    "label": "NAIVE AGENT",
    "cost": 0.84,
    "cost_label": "$0.84",
    "latency": 8.2,
    "lat_label": "8.2s",
    "calls": 6,
    "tokens": "26.4k",
}
_DEF_OPT = {
    "label": "OPTIMIZED AGENT",
    "cost": 0.24,
    "cost_label": "$0.24",
    "latency": 2.9,
    "lat_label": "2.9s",
    "calls": 3,
    "tokens": "8.1k",
}

_DEF_TOKEN_STACK = [
    {"label": "Chat History", "tok": 3200, "color": "amber"},
    {"label": "System Prompt", "tok": 2200, "color": "violet"},
    {"label": "Tool Schemas", "tok": 1800, "color": "cyan"},
    {"label": "Few-Shot Examples", "tok": 1400, "color": "blue"},
    {"label": "Actual Task", "tok": 240, "color": "emerald"},
]

_DEF_LEDGER = [
    {"call": "#1", "model": "GPT-4o", "purpose": "Plan task", "tok": "3.1k", "cost": "$0.14", "lat": "1.1s"},
    {"call": "#2", "model": "GPT-4o", "purpose": "Pick tool", "tok": "2.8k", "cost": "$0.12", "lat": "1.4s"},
    {"call": "#3", "model": "GPT-4o", "purpose": "Run tool", "tok": "2.2k", "cost": "$0.10", "lat": "0.9s"},
    {"call": "#4", "model": "GPT-4o", "purpose": "Self-critique", "tok": "3.6k", "cost": "$0.16", "lat": "1.3s"},
    {"call": "#5", "model": "GPT-4o", "purpose": "Retry (no fix)", "tok": "4.1k", "cost": "$0.18", "lat": "1.6s"},
    {"call": "#6", "model": "GPT-4o", "purpose": "Re-format", "tok": "2.0k", "cost": "$0.09", "lat": "0.7s"},
]

_DEF_ANTI = [
    {"title": "Full history हर call", "detail": "Same 8k context हर LLM call में resend"},
    {"title": "Over-powered model", "detail": "छोटे काम के लिए भी GPT-4o"},
    {"title": "Blind retry loop", "detail": "Fail होने पर बिना reason retry"},
    {"title": "No early exit", "detail": "Answer मिलने पर भी agent चलता रहा"},
]

_DEF_WATERFALL = [
    {"label": "TTFT", "ms": 480, "color": "cyan"},
    {"label": "Tool Calls", "ms": 1620, "color": "amber"},
    {"label": "Model Runs", "ms": 3400, "color": "violet"},
    {"label": "Retries", "ms": 2100, "color": "rose"},
    {"label": "Network", "ms": 220, "color": "blue"},
]

_DEF_LEVER = {
    "fix_caching": {
        "title": "Prompt Caching",
        "saving": "-58% cost",
        "how": "Static prefix (system + tools) ko cache karo — har call pe sirf delta bhejo.",
        "from_label": "$0.14 / req", "from_v": 1.0,
        "to_label": "$0.06 / req", "to_v": 0.42,
        "color": "emerald",
    },
    "fix_summarize": {
        "title": "History Summarization",
        "saving": "-40% tokens",
        "how": "Purani chat ko 1 short summary me squash karo — history 3.2k → 0.9k tokens.",
        "from_label": "History 3.2k tok", "from_v": 1.0,
        "to_label": "Summary 0.9k tok", "to_v": 0.28,
        "color": "cyan",
    },
    "fix_route_earlyexit": {
        "title": "Model Routing + Early Exit",
        "saving": "-52% calls",
        "how": "Easy step → chhota model; answer milte hi loop band karo. Calls 6 → 3.",
        "from_label": "6 calls · GPT-4o", "from_v": 1.0,
        "to_label": "3 calls · mini", "to_v": 0.5,
        "color": "violet",
    },
}

_DEF_SAVINGS = {"cost": "-72%", "latency": "-64%", "cache": "90%"}


def _as_list_of_dicts(val: Any, default: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = [d for d in val if isinstance(d, dict)] if isinstance(val, list) else []
    return out if out else [dict(d) for d in default]


def _build_cost_room_html(
    scene: Dict[str, Any],
    prev_scene: Optional[Dict[str, Any]],
    width: int,
    height: int,
    tone: str = "auto_2026_director",
) -> str:
    vd = dict(scene.get("visual_data") or {})
    mode = str(vd.get("scene_mode") or "cost_hook").strip()
    if mode not in _VALID_MODES:
        mode = "cost_hook"

    accent_hex = _ACCENT_HEX.get(str(vd.get("accent_color") or "cyan"), "#38BDF8")
    motion = _tone_cost_motion(tone, str(scene.get("role") or ""), scene.get("scene_tone"))
    sc = min(width, height) / 1080.0
    is_wide = width > height

    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = (
        f'<span class="at">@</span>{html.escape(raw_wm[1:])}'
        if raw_wm.startswith("@")
        else html.escape(raw_wm)
    )

    def _merge_num(base: Dict[str, Any], val: Any) -> Dict[str, Any]:
        out = dict(base)
        if isinstance(val, dict):
            for k in out:
                if k in val and val[k] not in (None, ""):
                    out[k] = val[k]
        return out

    naive = _merge_num(_DEF_NAIVE, vd.get("naive"))
    opt = _merge_num(_DEF_OPT, vd.get("opt"))
    token_stack = _as_list_of_dicts(vd.get("token_stack"), _DEF_TOKEN_STACK)
    ledger = _as_list_of_dicts(vd.get("ledger"), _DEF_LEDGER)
    anti = _as_list_of_dicts(vd.get("anti_patterns"), _DEF_ANTI)
    waterfall = _as_list_of_dicts(vd.get("waterfall"), _DEF_WATERFALL)

    savings = dict(_DEF_SAVINGS)
    if isinstance(vd.get("savings"), dict):
        for k in savings:
            if vd["savings"].get(k):
                savings[k] = vd["savings"][k]

    lever = dict(_DEF_LEVER.get(mode, _DEF_LEVER["fix_caching"]))
    if isinstance(vd.get("lever"), dict):
        for k in lever:
            if vd["lever"].get(k) not in (None, ""):
                lever[k] = vd["lever"][k]

    cta = dict(vd.get("cta") or {})

    state_json = json.dumps({
        "mode": mode,
        "accent": accent_hex,
        "motion": motion,
        "naive": naive,
        "opt": opt,
        "token_stack": token_stack,
        "ledger": ledger,
        "anti": anti,
        "waterfall": waterfall,
        "lever": lever,
        "savings": savings,
    }, ensure_ascii=False)

    hud_pill = html.escape(str(vd.get("hud_pill") or scene.get("role", "COST ROOM").upper()))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))
    question = html.escape(str(vd.get("question") or ""))
    caption = html.escape(str(vd.get("caption") or scene.get("narration") or ""))

    option_a = html.escape(str(cta.get("option_a") or "✅ Optimized Agent"))
    option_b = html.escape(str(cta.get("option_b") or "❌ Naive Agent"))
    footer_note = html.escape(str(cta.get("footer_note") or "Save this before your next LLM bill!"))
    cta_label_a = html.escape(str(cta.get("label_a") or "BEFORE"))
    cta_label_b = html.escape(str(cta.get("label_b") or "AFTER"))

    tmpl = _TEMPLATE
    repl = {
        "%%W%%": str(width),
        "%%H%%": str(height),
        "%%SC%%": ("1.0" if not is_wide else f"{sc:.3f}"),
        "%%ACCENT%%": accent_hex,
        "%%WM%%": wm_html,
        "%%PILL%%": hud_pill,
        "%%HW%%": h_white,
        "%%HA%%": h_accent,
        "%%QUESTION%%": question,
        "%%CAPTION%%": caption,
        "%%OPT_A%%": option_a,
        "%%OPT_B%%": option_b,
        "%%CTA_NOTE%%": footer_note,
        "%%CTA_LA%%": cta_label_a,
        "%%CTA_LB%%": cta_label_b,
        "%%STATE%%": state_json,
    }
    for k, v in repl.items():
        tmpl = tmpl.replace(k, v)
    return tmpl


_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --sc: %%SC%%;
    --bg0: #070B14;
    --bg1: #0C1220;
    --ink: #E8EEF9;
    --muted: #8A9AB5;
    --emerald: #10B981;
    --danger: #EF4444;
    --accent: %%ACCENT%%;
  }
  html, body {
    width: %%W%%px; height: %%H%%px; overflow: hidden;
    background: radial-gradient(circle at 50% 6%, rgba(16,185,129,0.11) 0%, var(--bg1) 46%, var(--bg0) 100%);
    color: var(--ink);
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }
  .grid-bg {
    position: absolute; inset: 0; opacity: 0.10;
    background-image:
      linear-gradient(rgba(148,163,184,0.30) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148,163,184,0.30) 1px, transparent 1px);
    background-size: calc(48px * var(--sc)) calc(48px * var(--sc));
  }
  #stage { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 2; }

  .hud {
    position: absolute; top: 0; left: 0; width: 100%; z-index: 6;
    padding: calc(40px * var(--sc)) calc(54px * var(--sc)) calc(30px * var(--sc));
    display: flex; flex-direction: column; align-items: center; text-align: center;
    background: linear-gradient(180deg, rgba(5,8,20,0.96) 0%, rgba(7,12,28,0.82) 68%, rgba(7,12,28,0.0) 100%);
  }
  .hud-top { width: 100%; display: flex; align-items: center; justify-content: space-between; margin-bottom: calc(14px * var(--sc)); }
  .wm-pill {
    padding: calc(8px * var(--sc)) calc(20px * var(--sc)); border-radius: 999px;
    background: rgba(15,23,42,0.85); border: 1.5px solid rgba(148,163,184,0.30);
    font-size: calc(23px * var(--sc)); font-weight: 800; color: var(--ink);
  }
  .wm-pill .at { color: #FB923C; }
  .hud-pill {
    display: inline-flex; align-items: center; gap: calc(9px * var(--sc));
    padding: calc(7px * var(--sc)) calc(20px * var(--sc)); border-radius: 999px;
    background: rgba(9,17,40,0.72); border: 1.6px solid var(--accent);
    font-size: calc(20px * var(--sc)); font-weight: 900; letter-spacing: calc(2.4px * var(--sc)); color: var(--accent);
  }
  .hud-pill .dot { width: calc(10px * var(--sc)); height: calc(10px * var(--sc)); border-radius: 50%; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
  .headline {
    font-size: calc(54px * var(--sc)); font-weight: 900; line-height: 1.1;
    color: #FFFFFF; text-shadow: 0 6px 26px rgba(0,0,0,0.66); max-width: calc(950px * var(--sc));
  }
  .headline .acc { color: var(--accent); }
  .question {
    margin-top: calc(10px * var(--sc)); font-size: calc(27px * var(--sc)); font-weight: 700;
    color: #C7D5EA; max-width: calc(900px * var(--sc)); line-height: 1.3;
  }
  .kpis { display: flex; gap: calc(14px * var(--sc)); margin-top: calc(16px * var(--sc)); flex-wrap: wrap; justify-content: center; }
  .kpi {
    display: inline-flex; align-items: center; gap: calc(8px * var(--sc));
    padding: calc(8px * var(--sc)) calc(18px * var(--sc)); border-radius: calc(14px * var(--sc));
    background: rgba(11,18,38,0.92); border: 1.6px solid rgba(148,163,184,0.24);
    font-size: calc(22px * var(--sc)); font-weight: 800; color: var(--ink);
  }
  .kpi .k { color: var(--muted); font-weight: 700; }
  .kpi .v { font-family: "Cascadia Code", "Consolas", monospace; font-variant-numeric: tabular-nums; }
  .kpi.warn { border-color: var(--danger); }
  .kpi.ok { border-color: var(--emerald); }

  .safe-bottom {
    position: absolute; left: 0; bottom: 0; width: 100%; z-index: 6;
    padding: calc(28px * var(--sc)) calc(60px * var(--sc)) calc(44px * var(--sc));
    display: flex; flex-direction: column; align-items: center; gap: calc(16px * var(--sc));
    background: linear-gradient(0deg, rgba(5,8,20,0.96) 0%, rgba(7,12,28,0.80) 62%, rgba(7,12,28,0.0) 100%);
  }
  .caption-wrap { width: 100%; text-align: center; }
  .caption {
    font-size: calc(35px * var(--sc)); font-weight: 800; line-height: 1.34; color: #F1F6FF;
    text-shadow: 0 4px 18px rgba(0,0,0,0.72); min-height: calc(46px * var(--sc));
  }
  .cap-track { margin-top: calc(12px * var(--sc)); width: 100%; height: calc(6px * var(--sc)); border-radius: 999px; background: rgba(148,163,184,0.18); overflow: hidden; }
  .cap-bar { height: 100%; width: 0%; border-radius: 999px; background: linear-gradient(90deg, var(--emerald), var(--accent)); }
  .cta-row { display: none; gap: calc(20px * var(--sc)); width: 100%; justify-content: center; }
  .cta-row.on { display: flex; }
  .cta-btn {
    flex: 1; padding: calc(20px * var(--sc)) calc(24px * var(--sc)); border-radius: calc(18px * var(--sc));
    background: rgba(11,18,38,0.94); border: 2.2px solid rgba(148,163,184,0.36);
    display: flex; flex-direction: column; align-items: center; gap: calc(6px * var(--sc));
    font-size: calc(29px * var(--sc)); font-weight: 900; color: var(--ink);
  }
  .cta-btn .lab { font-size: calc(19px * var(--sc)); letter-spacing: calc(2px * var(--sc)); color: var(--muted); font-weight: 800; }
  .cta-btn.b { border-color: var(--danger); box-shadow: 0 0 30px rgba(239,68,68,0.26); }
  .cta-btn.a { border-color: var(--emerald); box-shadow: 0 0 30px rgba(16,185,129,0.30); }
  .cta-note { font-size: calc(24px * var(--sc)); font-weight: 800; color: #FACC15; }
</style>
</head>
<body>
  <div class="grid-bg"></div>
  <canvas id="stage" width="%%W%%" height="%%H%%"></canvas>

  <div class="hud">
    <div class="hud-top">
      <div class="wm-pill">%%WM%%</div>
      <div class="hud-pill"><span class="dot"></span>%%PILL%%</div>
    </div>
    <div class="headline">%%HW%% <span class="acc">%%HA%%</span></div>
    <div class="question">%%QUESTION%%</div>
    <div class="kpis">
      <div class="kpi warn" id="kCost"><span class="k">Cost</span><span class="v">$0.84</span></div>
      <div class="kpi warn" id="kLat"><span class="k">Latency</span><span class="v">8.2s</span></div>
      <div class="kpi warn" id="kCalls"><span class="k">Calls</span><span class="v">6</span></div>
    </div>
  </div>

  <div class="safe-bottom">
    <div class="cta-row" id="ctaRow">
      <div class="cta-btn b"><span class="lab">%%CTA_LB%%</span>%%OPT_B%%</div>
      <div class="cta-btn a"><span class="lab">%%CTA_LA%%</span>%%OPT_A%%</div>
    </div>
    <div class="caption-wrap">
      <div class="caption" id="captionText">%%CAPTION%%</div>
      <div class="cap-track"><div class="cap-bar" id="capBar"></div></div>
    </div>
  </div>

<script>
  const STATE = %%STATE%%;
  const W = %%W%%, H = %%H%%, SC = %%SC%%;
  const canvas = document.getElementById('stage');
  const ctx = canvas.getContext('2d');

  const COLORS = {
    cyan:    { fill: '#0B2A3A', stroke: '#38BDF8', glow: 'rgba(56,189,248,0.55)' },
    blue:    { fill: '#0B1E3A', stroke: '#60A5FA', glow: 'rgba(96,165,250,0.55)' },
    slate:   { fill: '#1B2230', stroke: '#64748B', glow: 'rgba(100,116,139,0.40)' },
    emerald: { fill: '#062A21', stroke: '#10B981', glow: 'rgba(16,185,129,0.55)' },
    violet:  { fill: '#1B1036', stroke: '#A855F7', glow: 'rgba(168,85,247,0.58)' },
    amber:   { fill: '#2A1F05', stroke: '#F59E0B', glow: 'rgba(245,158,11,0.55)' },
    rose:    { fill: '#2A0D13', stroke: '#EF4444', glow: 'rgba(239,68,68,0.60)' },
    danger:  { fill: '#2A0D13', stroke: '#EF4444', glow: 'rgba(239,68,68,0.60)' },
  };
  function C(k) { return COLORS[k] || COLORS.cyan; }
  function clamp01(v) { return Math.max(0, Math.min(1, Number(v) || 0)); }
  function smooth(t) { t = clamp01(t); return t * t * (3 - 2 * t); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeOut(t) { t = clamp01(t); return 1 - Math.pow(1 - t, 3); }

  const STG_TOP = 386, STG_BOT = 1554, L = 74, R = 1006, CW = R - L, CX = 540;

  function rr(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function card(x, y, w, h, stroke, fill, alpha) {
    ctx.save();
    if (alpha !== undefined) ctx.globalAlpha = alpha;
    ctx.fillStyle = fill || 'rgba(148,163,184,0.05)';
    ctx.strokeStyle = stroke || 'rgba(148,163,184,0.18)';
    ctx.lineWidth = 1.8 * SC;
    rr(x, y, w, h, 24 * SC);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function chip(cx, cy, text, stroke, fill, txt, fs) {
    ctx.save();
    ctx.font = '900 ' + Math.round((fs || 24) * SC) + 'px "Segoe UI", sans-serif';
    const tw = ctx.measureText(text).width + 44 * SC;
    const th = (fs || 24) * 1.9 * SC;
    ctx.fillStyle = fill;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2.2 * SC;
    ctx.shadowColor = stroke;
    ctx.shadowBlur = 22 * SC;
    rr(cx - tw / 2, cy - th / 2, tw, th, 14 * SC);
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.fillStyle = txt;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, cx, cy + 1 * SC);
    ctx.restore();
  }

  function hbar(x, y, w, h, frac, from, to, glow) {
    ctx.save();
    ctx.fillStyle = 'rgba(148,163,184,0.16)';
    rr(x, y, w, h, h / 2); ctx.fill();
    const fw = Math.max(h, w * clamp01(frac));
    const grad = ctx.createLinearGradient(x, 0, x + w, 0);
    grad.addColorStop(0, from);
    grad.addColorStop(1, to);
    ctx.fillStyle = grad;
    if (glow) { ctx.shadowColor = glow; ctx.shadowBlur = 18 * SC; }
    rr(x, y, fw, h, h / 2); ctx.fill();
    ctx.restore();
    return fw;
  }

  function arrow(x1, y1, x2, y2, col, wdt) {
    ctx.save();
    ctx.strokeStyle = col; ctx.fillStyle = col;
    ctx.lineWidth = (wdt || 3) * SC;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    const ang = Math.atan2(y2 - y1, x2 - x1), sz = 12 * SC;
    ctx.beginPath(); ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - sz * Math.cos(ang - 0.42), y2 - sz * Math.sin(ang - 0.42));
    ctx.lineTo(x2 - sz * Math.cos(ang + 0.42), y2 - sz * Math.sin(ang + 0.42));
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  function meterGauge(x, y, w, value, max, col) {
    const segs = 14, gap = 4 * SC, sw = (w - gap * (segs - 1)) / segs;
    const lit = Math.round(segs * clamp01(value / max));
    for (let i = 0; i < segs; i++) {
      const on = i < lit;
      ctx.save();
      ctx.fillStyle = on ? col : 'rgba(148,163,184,0.14)';
      if (on) { ctx.shadowColor = col; ctx.shadowBlur = 12 * SC; }
      rr(x + i * (sw + gap), y, sw, 26 * SC, 5 * SC);
      ctx.fill();
      ctx.restore();
    }
  }

  function money(cx, cy, text, col, size) {
    ctx.save();
    ctx.fillStyle = col;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '900 ' + Math.round(size * SC) + 'px "Cascadia Code", "Consolas", monospace';
    ctx.shadowColor = col; ctx.shadowBlur = 22 * SC;
    ctx.fillText(text, cx, cy);
    ctx.restore();
  }

  // ============ MODE: cost_hook ============
  function modeCostHook(lp, wp) {
    const top = STG_TOP + 16, cardH = 606, cardW = 408;
    const lx = CX - 52 - cardW, rx = CX + 52;
    drawAgentCard(lx, top, cardW, cardH, STATE.naive, 'danger', '❌', lp);
    drawAgentCard(rx, top, cardW, cardH, STATE.opt, 'emerald', '✅', lp);
    // VS badge
    const vp = 0.6 + 0.4 * Math.sin(lp * 10);
    ctx.save();
    ctx.globalAlpha = 0.9;
    ctx.fillStyle = 'rgba(9,15,32,0.95)';
    ctx.strokeStyle = STATE.accent; ctx.lineWidth = 3 * SC;
    ctx.shadowColor = STATE.accent; ctx.shadowBlur = 26 * SC * vp;
    ctx.beginPath(); ctx.arc(CX, top + 210, 60 * SC, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.restore();
    ctx.save();
    ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '900 ' + Math.round(34 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('VS', CX, top + 210);
    ctx.restore();
    // Burn curve
    drawBurnCurve(L, top + cardH + 46, CW, 300, lp);
  }

  function drawAgentCard(x, y, w, h, d, colKey, badge, lp) {
    const col = C(colKey).stroke;
    card(x, y, w, h, col, 'rgba(11,18,38,0.72)');
    ctx.save();
    ctx.textAlign = 'left'; ctx.fillStyle = col;
    ctx.font = '900 ' + Math.round(26 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText(badge + ' ' + String(d.label || ''), x + 34 * SC, y + 56 * SC);
    ctx.restore();
    money(x + w / 2, y + 168 * SC, String(d.cost_label || ''), col, 82);
    ctx.save();
    ctx.textAlign = 'center'; ctx.fillStyle = '#8A9AB5';
    ctx.font = '800 ' + Math.round(22 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('per request · ' + String(d.tokens || '') + ' tok', x + w / 2, y + 232 * SC);
    ctx.restore();
    meterGauge(x + 34 * SC, y + 262 * SC, w - 68 * SC, Number(d.cost) || 0, 0.9, col);
    // pills
    const pw = (w - 68 * SC - 16 * SC) / 2;
    drawMiniPill(x + 34 * SC, y + 344 * SC, pw, 'Latency', String(d.lat_label || ''), col);
    drawMiniPill(x + 34 * SC + pw + 16 * SC, y + 344 * SC, pw, 'Calls', String(d.calls || ''), col);
    drawMiniPill(x + 34 * SC, y + 430 * SC, w - 68 * SC, 'Tokens', String(d.tokens || ''), col);
  }

  function drawMiniPill(x, y, w, k, v, col) {
    ctx.save();
    ctx.fillStyle = 'rgba(7,12,24,0.85)';
    ctx.strokeStyle = 'rgba(148,163,184,0.22)';
    ctx.lineWidth = 1.6 * SC;
    rr(x, y, w, 66 * SC, 14 * SC); ctx.fill(); ctx.stroke();
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#8A9AB5';
    ctx.font = '700 ' + Math.round(19 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText(k, x + 18 * SC, y + 33 * SC);
    ctx.textAlign = 'right';
    ctx.fillStyle = col;
    ctx.font = '900 ' + Math.round(26 * SC) + 'px "Consolas", monospace';
    ctx.fillText(v, x + w - 18 * SC, y + 33 * SC);
    ctx.restore();
  }

  function drawBurnCurve(x, y, w, h, lp) {
    card(x, y, w, h, 'rgba(148,163,184,0.16)', 'rgba(11,18,38,0.6)');
    ctx.save();
    ctx.textAlign = 'left'; ctx.fillStyle = '#8A9AB5';
    ctx.font = '800 ' + Math.round(21 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('CUMULATIVE SPEND / REQUEST', x + 30 * SC, y + 40 * SC);
    ctx.restore();
    const px = x + 34 * SC, py = y + 66 * SC, pw = w - 68 * SC, ph = h - 96 * SC;
    // grid
    ctx.save(); ctx.strokeStyle = 'rgba(148,163,184,0.12)'; ctx.lineWidth = 1 * SC;
    for (let i = 1; i < 4; i++) { ctx.beginPath(); ctx.moveTo(px, py + ph * i / 4); ctx.lineTo(px + pw, py + ph * i / 4); ctx.stroke(); }
    ctx.restore();
    const draw = (maxV, calls, col, glow) => {
      ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = 4 * SC;
      ctx.shadowColor = glow; ctx.shadowBlur = 16 * SC;
      ctx.beginPath();
      for (let i = 0; i <= calls; i++) {
        const t = i / calls;
        const cxp = px + pw * t;
        const cyp = py + ph - ph * (t * t) * (maxV / 0.9) * clamp01((lp - 0.05) / 0.7);
        if (i === 0) ctx.moveTo(cxp, cyp); else ctx.lineTo(cxp, cyp);
      }
      ctx.stroke(); ctx.restore();
    };
    draw(Number(STATE.naive.cost) || 0.84, Number(STATE.naive.calls) || 6, '#EF4444', 'rgba(239,68,68,0.7)');
    draw(Number(STATE.opt.cost) || 0.24, Number(STATE.opt.calls) || 3, '#10B981', 'rgba(16,185,129,0.7)');
    ctx.save();
    ctx.font = '800 ' + Math.round(20 * SC) + 'px "Consolas", monospace';
    ctx.fillStyle = '#FCA5A5'; ctx.textAlign = 'right';
    ctx.fillText('Naive  ' + String(STATE.naive.cost_label || ''), px + pw, py + 22 * SC);
    ctx.fillStyle = '#6EE7B7';
    ctx.fillText('Optimized  ' + String(STATE.opt.cost_label || ''), px + pw, py + 50 * SC);
    ctx.restore();
  }

  // ============ MODE: token_bloat_anatomy ============
  function modeTokens(lp, wp) {
    const items = STATE.token_stack || [];
    const total = items.reduce((s, it) => s + (Number(it.tok) || 0), 0) || 1;
    const bx = 300, bw = 176, top = STG_TOP + 60, bot = STG_BOT - 40, bh = bot - top;
    const appear = clamp01((lp - 0.05) / 0.55) * items.length;
    chip(CX, top - 34 * SC, 'WHERE YOUR TOKENS GO', STATE.accent, 'rgba(9,17,40,0.85)', STATE.accent, 22);
    let cy = top;
    items.forEach((it, i) => {
      const seg = bh * (Number(it.tok) || 0) / total;
      const vis = clamp01(appear - i);
      if (vis <= 0) { cy += seg; return; }
      const c = C(it.color);
      ctx.save();
      ctx.globalAlpha = vis;
      ctx.fillStyle = c.fill; ctx.strokeStyle = c.stroke; ctx.lineWidth = 2 * SC;
      ctx.shadowColor = c.glow; ctx.shadowBlur = (Number(it.tok) || 0) > 2000 ? 18 * SC : 8 * SC;
      rr(bx, cy + 3 * SC, bw, Math.max(6 * SC, seg * (0.4 + 0.6 * vis) - 6 * SC), 10 * SC);
      ctx.fill(); ctx.stroke();
      ctx.restore();
      // connector + label
      const ly = cy + seg / 2;
      ctx.save();
      ctx.globalAlpha = vis;
      ctx.strokeStyle = c.stroke; ctx.lineWidth = 2 * SC;
      ctx.setLineDash([8 * SC, 6 * SC]);
      ctx.beginPath(); ctx.moveTo(bx + bw, ly); ctx.lineTo(bx + bw + 70 * SC, ly); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = c.stroke;
      ctx.beginPath(); ctx.arc(bx + bw + 70 * SC, ly, 6 * SC, 0, Math.PI * 2); ctx.fill();
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#F1F6FF';
      ctx.font = '800 ' + Math.round(27 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText(String(it.label || ''), bx + bw + 96 * SC, ly - 14 * SC);
      ctx.fillStyle = c.stroke;
      ctx.font = '900 ' + Math.round(25 * SC) + 'px "Consolas", monospace';
      ctx.fillText((it.tok || '') + ' tok', bx + bw + 96 * SC, ly + 20 * SC);
      ctx.restore();
      cy += seg;
    });
    // total
    ctx.save();
    ctx.textAlign = 'center';
    ctx.fillStyle = '#FCA5A5';
    ctx.font = '900 ' + Math.round(30 * SC) + 'px "Consolas", monospace';
    ctx.fillText('TOTAL ' + Math.round(total / 100) / 10 + 'k tok', bx + bw / 2, bot + 34 * SC);
    ctx.restore();
    if (lp > 0.62) chip(CX + 210 * SC, top + 60 * SC, '⚠ 90% waste', '#EF4444', 'rgba(42,13,19,0.94)', '#FCA5A5', 22);
  }

  // ============ MODE: call_bloat_ledger ============
  function modeLedger(lp, wp) {
    const rows = STATE.ledger || [];
    const cols = [
      { k: 'call', w: 0.10, a: 'left' },
      { k: 'model', w: 0.20, a: 'left' },
      { k: 'purpose', w: 0.31, a: 'left' },
      { k: 'tok', w: 0.13, a: 'right' },
      { k: 'cost', w: 0.13, a: 'right' },
      { k: 'lat', w: 0.13, a: 'right' },
    ];
    const tx = L, tw = CW, hy = STG_TOP + 40, rowH = 108;
    chip(CX, hy - 40 * SC, 'CALL LEDGER · PER REQUEST', STATE.accent, 'rgba(9,17,40,0.85)', STATE.accent, 22);
    // header
    ctx.save();
    ctx.fillStyle = 'rgba(148,163,184,0.10)';
    rr(tx, hy, tw, 62 * SC, 12 * SC); ctx.fill();
    ctx.textBaseline = 'middle';
    let cx0 = tx + 22 * SC;
    cols.forEach((c) => {
      ctx.textAlign = c.a;
      ctx.fillStyle = '#8A9AB5';
      ctx.font = '800 ' + Math.round(21 * SC) + 'px "Segoe UI", sans-serif';
      const lx = c.a === 'right' ? cx0 + tw * c.w - 22 * SC - 20 * SC : cx0;
      ctx.fillText(c.k.toUpperCase(), lx, hy + 31 * SC);
      cx0 += tw * c.w;
    });
    ctx.restore();
    const appear = clamp01((lp - 0.05) / 0.6) * rows.length;
    let ry = hy + 78 * SC;
    rows.forEach((r, i) => {
      const vis = clamp01(appear - i);
      if (vis <= 0) return;
      ctx.save();
      ctx.globalAlpha = vis;
      ctx.fillStyle = i % 2 ? 'rgba(148,163,184,0.05)' : 'rgba(148,163,184,0.02)';
      rr(tx, ry, tw, rowH - 12 * SC, 12 * SC); ctx.fill();
      ctx.strokeStyle = 'rgba(148,163,184,0.10)'; ctx.lineWidth = 1 * SC;
      rr(tx, ry, tw, rowH - 12 * SC, 12 * SC); ctx.stroke();
      ctx.textBaseline = 'middle';
      let cxx = tx + 22 * SC;
      cols.forEach((c) => {
        let v = String(r[c.k] !== undefined ? r[c.k] : '');
        ctx.textAlign = c.a;
        if (c.k === 'cost') { ctx.fillStyle = '#FCA5A5'; ctx.font = '900 ' + Math.round(25 * SC) + 'px "Consolas", monospace'; }
        else if (c.k === 'tok' || c.k === 'lat') { ctx.fillStyle = '#CBD5E1'; ctx.font = '800 ' + Math.round(24 * SC) + 'px "Consolas", monospace'; }
        else { ctx.fillStyle = '#E8EEF9'; ctx.font = '800 ' + Math.round(24 * SC) + 'px "Segoe UI", sans-serif'; }
        const lx = c.a === 'right' ? cxx + tw * c.w - 22 * SC - 20 * SC : cxx;
        ctx.fillText(v, lx, ry + (rowH - 12 * SC) / 2);
        cxx += tw * c.w;
      });
      ctx.restore();
      ry += rowH;
    });
    if (lp > 0.66) {
      const tot = (Number(STATE.naive.cost) || 0.84);
      chip(CX + 250 * SC, ry + 4 * SC, '❌ Total $' + tot.toFixed(2), '#EF4444', 'rgba(42,13,19,0.94)', '#FCA5A5', 24);
    }
  }

  // ============ MODE: anti_pattern_scan ============
  function modeAntiPatterns(lp, wp) {
    const items = STATE.anti || [];
    const x = L + 30 * SC, w = CW - 60 * SC, top = STG_TOP + 40, ch = 214, gap = 30;
    chip(CX, top - 34 * SC, 'ANTI-PATTERN SCAN', '#EF4444', 'rgba(42,13,19,0.86)', '#FCA5A5', 22);
    // scanning line
    const scanY = top + (ch * items.length + gap * (items.length - 1)) * clamp01((lp - 0.04) / 0.72);
    let cy = top;
    items.forEach((it, i) => {
      const on = lp > (0.08 + 0.14 * i);
      card(x, cy, w, ch, on ? '#EF4444' : 'rgba(148,163,184,0.18)', on ? 'rgba(42,13,19,0.55)' : 'rgba(11,18,38,0.5)');
      ctx.save();
      ctx.textAlign = 'left';
      ctx.fillStyle = on ? '#EF4444' : '#8A9AB5';
      ctx.font = '900 ' + Math.round(30 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText('⚑', x + 30 * SC, cy + 62 * SC);
      ctx.fillStyle = '#F1F6FF';
      ctx.font = '900 ' + Math.round(30 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText(String(it.title || ''), x + 96 * SC, cy + 60 * SC);
      ctx.fillStyle = '#A9B8CE';
      ctx.font = '700 ' + Math.round(25 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText(String(it.detail || ''), x + 96 * SC, cy + 118 * SC);
      ctx.restore();
      if (on) {
        ctx.save();
        ctx.strokeStyle = '#EF4444'; ctx.lineWidth = 3 * SC;
        ctx.strokeRect(x + 10 * SC, cy + 10 * SC, w - 20 * SC, ch - 20 * SC);
        ctx.restore();
      }
      cy += ch + gap;
    });
    ctx.save();
    ctx.strokeStyle = '#EF4444'; ctx.lineWidth = 3 * SC;
    ctx.shadowColor = '#EF4444'; ctx.shadowBlur = 20 * SC;
    ctx.beginPath(); ctx.moveTo(x - 20 * SC, scanY); ctx.lineTo(x + w + 20 * SC, scanY); ctx.stroke();
    ctx.restore();
  }

  // ============ MODE: cost_compare ============
  function modeCompare(lp, wp) {
    const metrics = [
      { k: 'cost', label: 'COST / REQ', nv: STATE.naive.cost_label, ov: STATE.opt.cost_label, nm: Number(STATE.naive.cost), om: Number(STATE.opt.cost) },
      { k: 'lat', label: 'LATENCY', nv: STATE.naive.lat_label, ov: STATE.opt.lat_label, nm: Number(STATE.naive.latency), om: Number(STATE.opt.latency) },
      { k: 'call', label: 'LLM CALLS', nv: String(STATE.naive.calls), ov: String(STATE.opt.calls), nm: Number(STATE.naive.calls), om: Number(STATE.opt.calls) },
    ];
    const top = STG_TOP + 30, blockH = 330;
    chip(CX, top - 24 * SC, 'NAIVE vs OPTIMIZED', STATE.accent, 'rgba(9,17,40,0.85)', STATE.accent, 22);
    metrics.forEach((m, i) => {
      const y = top + i * blockH;
      const maxV = Math.max(m.nm, m.om) || 1;
      const bw = CW - 120 * SC, bx = L + 60 * SC;
      ctx.save();
      ctx.textAlign = 'left'; ctx.fillStyle = '#E8EEF9';
      ctx.font = '900 ' + Math.round(26 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText(m.label, bx, y + 34 * SC);
      ctx.restore();
      const t = smooth((lp - 0.06 - i * 0.08) / 0.4);
      const nw = bw * clamp01(m.nm / maxV) * t;
      const ow = bw * clamp01(m.om / maxV) * t;
      hbar(bx, y + 60 * SC, bw, 52 * SC, clamp01(nw / bw), '#7F1D1D', '#EF4444', 'rgba(239,68,68,0.5)');
      hbar(bx, y + 140 * SC, bw, 52 * SC, clamp01(ow / bw), '#065F46', '#10B981', 'rgba(16,185,129,0.5)');
      ctx.save();
      ctx.textBaseline = 'middle'; ctx.font = '900 ' + Math.round(26 * SC) + 'px "Consolas", monospace';
      ctx.fillStyle = '#FCA5A5'; ctx.textAlign = 'left';
      ctx.fillText('Naive ' + m.nv, bx + 12 * SC, y + 86 * SC);
      ctx.fillStyle = '#6EE7B7';
      ctx.fillText('Opt ' + m.ov, bx + 12 * SC, y + 166 * SC);
      ctx.restore();
      if (t > 0.6) {
        const pct = Math.round((1 - (m.om / m.nm)) * 100);
        chip(bx + bw + 4 * SC, y + 100 * SC, '−' + pct + '%', '#10B981', 'rgba(6,42,33,0.95)', '#6EE7B7', 24);
      }
    });
  }

  // ============ MODE: fix_* (lever) ============
  function modeLever(lp, wp) {
    const lv = STATE.lever || {};
    const col = C(lv.color || 'emerald').stroke;
    const lx = L, lw = 372, top = STG_TOP + 40, lh = 560;
    card(lx, top, lw, lh, col, 'rgba(11,18,38,0.7)');
    ctx.save();
    ctx.textAlign = 'center';
    ctx.fillStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 22 * SC;
    ctx.font = '900 ' + Math.round(74 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('🔧', lx + lw / 2, top + 150 * SC);
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 ' + Math.round(30 * SC) + 'px "Segoe UI", sans-serif';
    wrapCenter(String(lv.title || ''), lx + lw / 2, top + 236 * SC, lw - 40 * SC, 38 * SC);
    ctx.restore();
    chip(lx + lw / 2, top + lh - 96 * SC, String(lv.saving || ''), col, 'rgba(6,42,33,0.9)', '#FFFFFF', 34);

    // right: before -> after
    const rx = lx + lw + 48 * SC, rw = R - rx, ry = top;
    card(rx, ry, rw, lh, 'rgba(148,163,184,0.18)', 'rgba(11,18,38,0.55)');
    ctx.save();
    ctx.textAlign = 'left'; ctx.fillStyle = '#8A9AB5';
    ctx.font = '800 ' + Math.round(23 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('BEFORE', rx + 34 * SC, ry + 50 * SC);
    ctx.fillText('AFTER', rx + 34 * SC, ry + 300 * SC);
    ctx.restore();
    const bw = rw - 68 * SC, bx = rx + 34 * SC;
    const t = smooth((lp - 0.08) / 0.5);
    hbar(bx, ry + 70 * SC, bw, 62 * SC, clamp01((Number(lv.from_v) || 1) * t), '#7F1D1D', '#EF4444', 'rgba(239,68,68,0.5)');
    hbar(bx, ry + 320 * SC, bw, 62 * SC, clamp01((Number(lv.to_v) || 0.4) * t), '#065F46', '#10B981', 'rgba(16,185,129,0.5)');
    ctx.save();
    ctx.textBaseline = 'middle'; ctx.font = '900 ' + Math.round(26 * SC) + 'px "Consolas", monospace';
    ctx.fillStyle = '#FCA5A5'; ctx.textAlign = 'left';
    ctx.fillText(String(lv.from_label || ''), bx + 16 * SC, ry + 150 * SC);
    ctx.fillStyle = '#6EE7B7';
    ctx.fillText(String(lv.to_label || ''), bx + 16 * SC, ry + 400 * SC);
    ctx.restore();
    arrow(rx + rw / 2, ry + 176 * SC, rx + rw / 2, ry + 288 * SC, col, 4);

    // bottom how-it-works
    const hy = top + lh + 40 * SC, hh = STG_BOT - hy;
    card(L, hy, CW, hh, 'rgba(148,163,184,0.18)', 'rgba(11,18,38,0.55)');
    ctx.save();
    ctx.fillStyle = col; ctx.textAlign = 'left';
    ctx.font = '900 ' + Math.round(24 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('HOW IT WORKS', L + 34 * SC, hy + 48 * SC);
    ctx.fillStyle = '#E8EEF9';
    ctx.font = '700 ' + Math.round(27 * SC) + 'px "Segoe UI", sans-serif';
    wrapLeft(String(lv.how || ''), L + 34 * SC, hy + 104 * SC, CW - 68 * SC, 40 * SC);
    ctx.restore();
  }

  // ============ MODE: latency_waterfall ============
  function modeWaterfall(lp, wp) {
    const items = STATE.waterfall || [];
    const total = items.reduce((s, it) => s + (Number(it.ms) || 0), 0) || 1;
    const maxMs = total;
    const top = STG_TOP + 50, rowH = 158, x = L + 40 * SC, bw = CW - 200 * SC;
    chip(CX, top - 34 * SC, 'LATENCY WATERFALL', STATE.accent, 'rgba(9,17,40,0.85)', STATE.accent, 22);
    let off = 0;
    const reveal = clamp01((lp - 0.05) / 0.6) * items.length;
    items.forEach((it, i) => {
      const y = top + 30 * SC + i * rowH;
      const w = bw * (Number(it.ms) || 0) / maxMs;
      const xo = x + (off / maxMs) * bw;
      const vis = clamp01(reveal - i);
      const c = C(it.color);
      ctx.save();
      ctx.globalAlpha = 0.25 + 0.75 * vis;
      ctx.fillStyle = c.fill; ctx.strokeStyle = c.stroke; ctx.lineWidth = 2.4 * SC;
      rr(xo + 2 * SC, y, Math.max(80 * SC, w * (0.35 + 0.65 * vis)) - 4 * SC, 62 * SC, 12 * SC);
      ctx.fill(); ctx.stroke();
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#E8EEF9';
      ctx.font = '800 ' + Math.round(25 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText(String(it.label || ''), x, y + 31 * SC);
      ctx.fillStyle = c.stroke;
      ctx.font = '900 ' + Math.round(24 * SC) + 'px "Consolas", monospace';
      ctx.fillText((Number(it.ms) || 0) + 'ms', xo + Math.max(80 * SC, w) + 14 * SC, y + 31 * SC);
      ctx.restore();
      off += Number(it.ms) || 0;
    });
    if (lp > 0.7) {
      chip(CX, top + 30 * SC + items.length * rowH + 6 * SC, '⏱ TOTAL ' + (total / 1000).toFixed(1) + 's', '#EF4444', 'rgba(42,13,19,0.94)', '#FCA5A5', 26);
    }
  }

  // ============ MODE: verdict_savings ============
  function modeVerdict(lp, wp) {
    const top = STG_TOP + 40;
    const lw = 400, lx = CX - 40 - lw, rx = CX + 40, ch = 320;
    card(lx, top, lw, ch, '#EF4444', 'rgba(42,13,19,0.45)');
    card(rx, top, lw, ch, '#10B981', 'rgba(6,42,33,0.45)');
    money(lx + lw / 2, top + 120 * SC, String(STATE.naive.cost_label || ''), '#EF4444', 78);
    money(rx + lw / 2, top + 120 * SC, String(STATE.opt.cost_label || ''), '#10B981', 78);
    ctx.save();
    ctx.textAlign = 'center';
    ctx.fillStyle = '#8A9AB5';
    ctx.font = '800 ' + Math.round(24 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText('❌ Naive / req', lx + lw / 2, top + 56 * SC);
    ctx.fillText('✅ Optimized / req', rx + lw / 2, top + 56 * SC);
    ctx.fillStyle = '#C7D5EA';
    ctx.font = '800 ' + Math.round(23 * SC) + 'px "Consolas", monospace';
    ctx.fillText(String(STATE.naive.lat_label || '') + ' · ' + String(STATE.naive.calls || '') + ' calls', lx + lw / 2, top + 210 * SC);
    ctx.fillText(String(STATE.opt.lat_label || '') + ' · ' + String(STATE.opt.calls || '') + ' calls', rx + lw / 2, top + 210 * SC);
    ctx.restore();
    // center arrow
    const t = smooth((lp - 0.1) / 0.4);
    arrow(CX - 24 * SC, top + 120 * SC, CX + 24 * SC, top + 120 * SC, '#FACC15', 5);
    ctx.save();
    ctx.globalAlpha = t;
    chip(CX, top + ch + 60 * SC, '💸 ' + String(STATE.savings.cost || '-72%') + ' COST', '#10B981', 'rgba(6,42,33,0.95)', '#6EE7B7', 34);
    ctx.restore();
    const badges = [
      { t: '💰 ' + String(STATE.savings.cost || '') + ' cost', c: 'emerald' },
      { t: '⚡ ' + String(STATE.savings.latency || '') + ' latency', c: 'cyan' },
      { t: '⚡ ' + String(STATE.savings.cache || '') + ' cache hit', c: 'violet' },
    ];
    const by = top + ch + 130 * SC;
    const bwd = (CW - 40 * SC) / 3;
    badges.forEach((b, i) => {
      const bx = L + i * (bwd + 20 * SC);
      const c = C(b.c);
      card(bx, by, bwd, 150 * SC, c.stroke, 'rgba(11,18,38,0.7)');
      ctx.save();
      ctx.fillStyle = c.stroke; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.font = '900 ' + Math.round(26 * SC) + 'px "Segoe UI", sans-serif';
      drawWrappedChip(b.t, bx + bwd / 2, by + 75 * SC, bwd - 30 * SC);
      ctx.restore();
    });
  }

  function drawWrappedChip(text, cx, cy, maxw) {
    const words = String(text).split(' ');
    const lines = [];
    let cur = '';
    ctx.font = '900 ' + Math.round(26 * SC) + 'px "Segoe UI", sans-serif';
    words.forEach((w) => {
      const test = cur ? cur + ' ' + w : w;
      if (ctx.measureText(test).width > maxw && cur) { lines.push(cur); cur = w; } else { cur = test; }
    });
    if (cur) lines.push(cur);
    const lh = 34 * SC;
    const y0 = cy - (lines.length - 1) * lh / 2;
    lines.forEach((l, i) => ctx.fillText(l, cx, y0 + i * lh));
  }

  function wrapCenter(text, cx, y, maxw, lh) {
    const words = String(text).split(' ');
    const lines = [];
    let cur = '';
    words.forEach((w) => {
      const test = cur ? cur + ' ' + w : w;
      if (ctx.measureText(test).width > maxw && cur) { lines.push(cur); cur = w; } else { cur = test; }
    });
    if (cur) lines.push(cur);
    lines.forEach((l, i) => ctx.fillText(l, cx, y + i * lh));
  }

  function wrapLeft(text, x, y, maxw, lh) {
    const words = String(text).split(' ');
    const lines = [];
    let cur = '';
    words.forEach((w) => {
      const test = cur ? cur + ' ' + w : w;
      if (ctx.measureText(test).width > maxw && cur) { lines.push(cur); cur = w; } else { cur = test; }
    });
    if (cur) lines.push(cur);
    lines.forEach((l, i) => ctx.fillText(l, x, y + i * lh));
  }

  function computeCam(lp) {
    let zoom = 1.0, dy = 0;
    const f = smooth((lp - 0.02) / 0.2);
    zoom = 1.0 + 0.05 * f;
    dy = -8 * SC * f;
    if (STATE.mode === 'verdict_savings' || STATE.mode === 'cta') {
      const b = smooth((lp - 0.72) / 0.2);
      zoom = lerp(zoom, 1.06, b);
      dy = lerp(dy, 10 * SC, b);
    }
    return { zoom, dy };
  }

  function updateKpis(lp) {
    const t = smooth((lp - 0.05) / 0.5);
    const nCost = Number(STATE.naive.cost) || 0.84;
    const oCost = Number(STATE.opt.cost) || 0.24;
    const revolve = (STATE.mode === 'verdict_savings' || STATE.mode === 'cost_compare' || (STATE.mode === 'fix_caching') || STATE.mode === 'fix_summarize' || STATE.mode === 'fix_route_earlyexit');
    const showOpt = revolve && lp > 0.6;
    const kCost = document.getElementById('kCost');
    const kLat = document.getElementById('kLat');
    const kCalls = document.getElementById('kCalls');
    if (showOpt) {
      kCost.className = 'kpi ok'; kCost.querySelector('.v').textContent = String(STATE.opt.cost_label || '');
      kLat.className = 'kpi ok'; kLat.querySelector('.v').textContent = String(STATE.opt.lat_label || '');
      kCalls.className = 'kpi ok'; kCalls.querySelector('.v').textContent = String(STATE.opt.calls || '');
    } else {
      kCost.className = 'kpi warn'; kCost.querySelector('.v').textContent = String(STATE.naive.cost_label || '');
      kLat.className = 'kpi warn'; kLat.querySelector('.v').textContent = String(STATE.naive.lat_label || '');
      kCalls.className = 'kpi warn'; kCalls.querySelector('.v').textContent = String(STATE.naive.calls || '');
    }
  }

  let progressLP = 0, progressWP = 0;

  function draw() {
    const lp = progressLP, wp = progressWP;
    ctx.clearRect(0, 0, W, H);
    const cam = computeCam(lp);
    ctx.save();
    ctx.translate(W / 2, H / 2);
    ctx.scale(cam.zoom, cam.zoom);
    ctx.translate(-W / 2, -H / 2 + cam.dy);

    const m = STATE.mode;
    if (m === 'cost_hook') modeCostHook(lp, wp);
    else if (m === 'token_bloat_anatomy') modeTokens(lp, wp);
    else if (m === 'call_bloat_ledger') modeLedger(lp, wp);
    else if (m === 'anti_pattern_scan') modeAntiPatterns(lp, wp);
    else if (m === 'cost_compare') modeCompare(lp, wp);
    else if (m === 'latency_waterfall') modeWaterfall(lp, wp);
    else if (m === 'verdict_savings' || m === 'cta') modeVerdict(lp, wp);
    else modeLever(lp, wp);

    ctx.restore();
    updateKpis(lp);
  }

  window.__setStudioProgress = function (lp, wp) {
    progressLP = clamp01(lp);
    progressWP = clamp01(wp !== undefined ? wp : lp);
    const cap = document.getElementById('captionText');
    const cf = clamp01((progressWP - 0.05) / 0.30);
    cap.style.opacity = (0.15 + 0.85 * cf).toFixed(3);
    document.getElementById('capBar').style.width = (progressWP * 100).toFixed(1) + '%';
    const ctaRow = document.getElementById('ctaRow');
    if (STATE.mode === 'cta' || STATE.mode === 'verdict_savings') {
      ctaRow.classList.add('on');
      ctaRow.style.opacity = clamp01((progressWP - 0.32) / 0.25).toFixed(3);
      cap.style.display = 'none';
    } else {
      ctaRow.classList.remove('on');
    }
    draw();
  };
  window.__setStudioProgress(0.0, 0.0);
</script>
</body>
</html>"""


def render_v7_cost_room_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    prev_scene: Optional[Dict[str, Any]] = None,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
    fps: int = VIDEO_FPS,
    res_scale: float = 1.0,
    frame_ext: str = "jpg",
) -> Path:
    """Renders continuous Agent Cost & Latency Control Room frames + HUD for a Studio V7 scene."""
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    w, h = spec["width"], spec["height"]
    duration = max(1.2, float(scene.get("duration", 4.5)))
    total_frames = max(18, int(round(duration * max(15, int(fps or VIDEO_FPS)))))
    out_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.*"):
        try:
            old.unlink()
        except Exception:
            pass

    html_doc = _build_cost_room_html(scene, prev_scene, w, h, tone=tone)
    from core.web_generative_engine import capture_studio_playwright_frames
    if capture_studio_playwright_frames(
        html_doc, out_dir, w, h, duration, scene, scene_words,
        tone=tone, fps=fps, res_scale=res_scale, frame_ext=frame_ext, arg_order="lp_wp",
    ):
        return out_dir

    # Graceful headless Pillow fallback
    from PIL import Image, ImageDraw
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (7, 11, 20))
    draw = ImageDraw.Draw(img)
    draw.text((70, 130), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(232, 238, 249))
    draw.rectangle([60, 300, w - 60, 700], outline=(239, 68, 68), width=3)
    draw.text((80, 330), "Naive Agent: $0.84 / req  8.2s  6 calls", fill=(252, 165, 165))
    draw.rectangle([60, 730, w - 60, 1130], outline=(16, 185, 129), width=3)
    draw.text((80, 760), "Optimized: $0.24 / req  2.9s  3 calls", fill=(110, 231, 183))
    draw.text((80, 1180), "Cache 90% · Summarize history · Route model · Early exit", fill=(167, 139, 250))
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir
