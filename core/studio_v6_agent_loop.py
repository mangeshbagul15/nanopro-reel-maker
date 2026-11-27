"""
Studio V6 — LLM vs Autonomous Agent Loop Renderer ("Cognitive Loop" Engine).

A strict cognitive/execution-loop engine (NO infrastructure nodes) that contrasts:
  - LEFT LANE  "Simple LLM"        : linear single-pass pipeline Prompt -> LLM -> Answer (dead-end).
  - RIGHT LANE "Autonomous Agent"  : cyclic state loop Goal -> Reason/Plan -> Tool Call -> Observe ->
                                     Final Output, with a curved feedback arc Observe -> Reason/Plan.
  - Visible Failure -> Diagnosis -> Self-Correction beat (Loop #1 red spark -> Reflection pulse ->
    Loop #2 recovery glow).
  - Live context/memory meter + tabular monospace step/loop counters (no jitter).
  - 9:16 dark Snowflake-inspired glassmorphism + deterministic camera choreography driven by
    `window.__setStudioProgress(linP, wordP)` (fully voice-synced via `compute_synced_visual_progress`).
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

_VALID_MODES = {"split_intro", "llm_only", "agent_loop", "verdict", "cta"}


def _default_left_lane(vd: Dict[str, Any]) -> Dict[str, Any]:
    lane = dict(vd.get("left_lane") or {})
    lane.setdefault("title", "Simple LLM")
    lane.setdefault("sub", "Linear Pipeline")
    nodes = lane.get("nodes")
    if not isinstance(nodes, list) or len(nodes) < 2:
        nodes = [
            {"label": "Prompt", "color": "cyan"},
            {"label": "LLM", "color": "cyan"},
            {"label": "Answer", "color": "slate"},
        ]
    lane["nodes"] = nodes[:3]
    lane.setdefault("counter", "Calls: 1 · Memory: None · Loop: 0/0")
    return lane


def _default_right_lane(vd: Dict[str, Any]) -> Dict[str, Any]:
    lane = dict(vd.get("right_lane") or {})
    lane.setdefault("title", "Autonomous Agent")
    lane.setdefault("sub", "Cyclic State Loop")
    nodes = lane.get("nodes")
    if not isinstance(nodes, list) or len(nodes) < 3:
        nodes = [
            {"label": "Goal", "color": "emerald"},
            {"label": "Reason / Plan", "color": "violet"},
            {"label": "Tool Call", "color": "amber"},
            {"label": "Observe", "color": "cyan"},
            {"label": "Final Output", "color": "emerald"},
        ]
    lane["nodes"] = nodes[:5]
    lane.setdefault("tool", "Search")
    lane.setdefault("fail_reason", "429 Rate Limit")
    lane.setdefault("reflect_text", "Missing filter → Adjusting query")
    lane.setdefault("recovery_note", "Retrying with fallback")
    lane.setdefault("memory_label", "Memory: 2 items · +140 tok")
    lane.setdefault("max_calls", 3)
    return lane


def _tone_loop_motion(tone: str, role: str, scene_tone: Optional[str]) -> Dict[str, float]:
    """Maps Script Tone to packet glide speed + camera push intensity (voice-sync feel)."""
    prof = get_tone_profile(tone, scene_tone=scene_tone, role=role)
    t_key = prof.get("key", "whiteboard_analogy")
    if t_key in ("fireship_octane", "youth_friend_turbo", "cage_match_vs", "myth_buster_contrarian"):
        return {"glide": 0.92, "push": 1.12, "pulse": 1.25}
    if t_key in ("war_story_postmortem", "dramatic_performance", "bigtech_reverse_engineer"):
        return {"glide": 1.08, "push": 1.18, "pulse": 1.05}
    return {"glide": 1.0, "push": 1.10, "pulse": 1.0}


def _build_agent_loop_html(
    scene: Dict[str, Any],
    prev_scene: Optional[Dict[str, Any]],
    width: int,
    height: int,
    tone: str = "auto_2026_director",
) -> str:
    vd = dict(scene.get("visual_data") or {})
    mode = str(vd.get("scene_mode") or "agent_loop").strip()
    if mode not in _VALID_MODES:
        mode = "agent_loop"

    left = _default_left_lane(vd)
    right = _default_right_lane(vd)
    motion = _tone_loop_motion(tone, str(scene.get("role") or ""), scene.get("scene_tone"))

    accent_hex = _ACCENT_HEX.get(str(vd.get("accent_color") or "cyan"), "#38BDF8")
    sc = min(width, height) / 1080.0
    is_wide = width > height

    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = (
        f'<span class="at">@</span>{html.escape(raw_wm[1:])}'
        if raw_wm.startswith("@")
        else html.escape(raw_wm)
    )
    hud_pill = html.escape(str(vd.get("hud_pill") or scene.get("role", "AGENT LOOP").upper()))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))
    question = html.escape(str(vd.get("question") or ""))
    caption = html.escape(str(vd.get("caption") or scene.get("narration") or ""))

    cta = dict(vd.get("cta") or {})
    option_a = html.escape(str(cta.get("option_a") or "🔄 Autonomous Agent"))
    option_b = html.escape(str(cta.get("option_b") or "➡️ Simple LLM"))
    footer_note = html.escape(str(cta.get("footer_note") or "Save this for your next system design!"))
    cta_label_a = html.escape(str(cta.get("label_a") or "STEP #1"))
    cta_label_b = html.escape(str(cta.get("label_b") or "STEP #2"))

    state_json = json.dumps({
        "mode": mode,
        "left": left,
        "right": right,
        "accent": accent_hex,
        "motion": motion,
    }, ensure_ascii=False)

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
    --bg1: #0D1322;
    --ink: #E8EEF9;
    --muted: #8A9AB5;
    --cyan: #38BDF8;
    --slate: #64748B;
    --emerald: #10B981;
    --violet: #A855F7;
    --amber: #F59E0B;
    --danger: #EF4444;
    --accent: %%ACCENT%%;
  }
  html, body {
    width: %%W%%px; height: %%H%%px; overflow: hidden;
    background: radial-gradient(circle at 50% 8%, rgba(56,189,248,0.10) 0%, var(--bg1) 44%, var(--bg0) 100%);
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
  #stage { position: absolute; inset: 0; width: 100%%; height: 100%%; z-index: 2; }

  /* ---------- Top HUD (12-16%% safe zone) ---------- */
  .hud {
    position: absolute; top: 0; left: 0; width: 100%%; z-index: 6;
    padding: calc(40px * var(--sc)) calc(54px * var(--sc)) calc(30px * var(--sc));
    display: flex; flex-direction: column; align-items: center; text-align: center;
    background: linear-gradient(180deg, rgba(5,8,20,0.96) 0%, rgba(7,12,28,0.82) 68%, rgba(7,12,28,0.0) 100%%);
  }
  .hud-top { width: 100%%; display: flex; align-items: center; justify-content: space-between; margin-bottom: calc(14px * var(--sc)); }
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
    font-size: calc(20px * var(--sc)); font-weight: 900; letter-spacing: calc(2.6px * var(--sc)); color: var(--accent);
  }
  .hud-pill .dot { width: calc(10px * var(--sc)); height: calc(10px * var(--sc)); border-radius: 50%%; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
  .headline {
    font-size: calc(56px * var(--sc)); font-weight: 900; line-height: 1.1;
    color: #FFFFFF; text-shadow: 0 6px 26px rgba(0,0,0,0.66); max-width: calc(940px * var(--sc));
  }
  .headline .acc { color: var(--accent); }
  .question {
    margin-top: calc(12px * var(--sc)); font-size: calc(28px * var(--sc)); font-weight: 700;
    color: #C7D5EA; max-width: calc(900px * var(--sc)); line-height: 1.3;
  }
  .telemetry { display: flex; gap: calc(14px * var(--sc)); margin-top: calc(18px * var(--sc)); flex-wrap: wrap; justify-content: center; }
  .t-pill {
    display: inline-flex; align-items: center; gap: calc(8px * var(--sc));
    padding: calc(8px * var(--sc)) calc(18px * var(--sc)); border-radius: calc(14px * var(--sc));
    background: rgba(11,18,38,0.92); border: 1.6px solid rgba(148,163,184,0.24);
    font-size: calc(23px * var(--sc)); font-weight: 800; color: var(--ink);
  }
  .t-pill .k { color: var(--muted); font-weight: 700; }
  .t-pill .v { font-family: "Cascadia Code", "Consolas", monospace; font-variant-numeric: tabular-nums; }
  .t-pill.ok { border-color: var(--emerald); }
  .t-pill.warn { border-color: var(--amber); }
  .t-pill.err { border-color: var(--danger); }

  /* ---------- Bottom safe zone (captions / CTA) ---------- */
  .safe-bottom {
    position: absolute; left: 0; bottom: 0; width: 100%%; z-index: 6;
    padding: calc(30px * var(--sc)) calc(60px * var(--sc)) calc(46px * var(--sc));
    display: flex; flex-direction: column; align-items: center; gap: calc(18px * var(--sc));
    background: linear-gradient(0deg, rgba(5,8,20,0.96) 0%, rgba(7,12,28,0.80) 62%, rgba(7,12,28,0.0) 100%%);
  }
  .caption-wrap { width: 100%%; text-align: center; }
  .caption {
    font-size: calc(36px * var(--sc)); font-weight: 800; line-height: 1.34; color: #F1F6FF;
    text-shadow: 0 4px 18px rgba(0,0,0,0.72); min-height: calc(46px * var(--sc));
  }
  .cap-track { margin-top: calc(14px * var(--sc)); width: 100%%; height: calc(6px * var(--sc)); border-radius: 999px; background: rgba(148,163,184,0.18); overflow: hidden; }
  .cap-bar { height: 100%%; width: 0%%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--emerald)); }
  .cta-row { display: none; gap: calc(20px * var(--sc)); width: 100%%; justify-content: center; }
  .cta-row.on { display: flex; }
  .cta-btn {
    flex: 1; padding: calc(20px * var(--sc)) calc(24px * var(--sc)); border-radius: calc(18px * var(--sc));
    background: rgba(11,18,38,0.94); border: 2.2px solid rgba(148,163,184,0.36);
    display: flex; flex-direction: column; align-items: center; gap: calc(6px * var(--sc));
    font-size: calc(30px * var(--sc)); font-weight: 900; color: var(--ink);
  }
  .cta-btn .lab { font-size: calc(19px * var(--sc)); letter-spacing: calc(2px * var(--sc)); color: var(--muted); font-weight: 800; }
  .cta-btn.a { border-color: var(--violet); box-shadow: 0 0 30px rgba(168,85,247,0.30); }
  .cta-btn.b { border-color: var(--cyan); box-shadow: 0 0 30px rgba(56,189,248,0.24); }
  .cta-note { font-size: calc(25px * var(--sc)); font-weight: 800; color: #FACC15; }
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
    <div class="telemetry">
      <div class="t-pill" id="tCalls"><span class="k">Calls</span><span class="v">1</span></div>
      <div class="t-pill" id="tLoop"><span class="k">Loop</span><span class="v">0 / 0</span></div>
      <div class="t-pill" id="tMem"><span class="k">Memory</span><span class="v">None</span></div>
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
  };
  function C(k) { return COLORS[k] || COLORS.cyan; }
  function clamp01(v) { return Math.max(0, Math.min(1, Number(v) || 0)); }
  function smooth(t) { t = clamp01(t); return t * t * (3 - 2 * t); }
  function lerp(a, b, t) { return a + (b - a) * t; }

  const LX = 290, RX = 790, NW = 330, NHALF = NW / 2, NH = 78;
  const LY0 = 478, LYSTEP = 182, RY0 = 478, RYSTEP = 176;
  const LANE_HALF = 232, LANE_TOP = 344, LANE_BOT = 1278;

  function nodesOf(side) {
    const lane = (side === 'left') ? STATE.left : STATE.right;
    const arr = lane.nodes || [];
    const cx = (side === 'left') ? LX : RX;
    const y0 = (side === 'left') ? LY0 : RY0;
    const step = (side === 'left') ? LYSTEP : RYSTEP;
    return arr.map((n, i) => ({
      x: cx, y: y0 + i * step,
      label: String(n.label || ''),
      color: n.color || (side === 'left' ? 'cyan' : 'emerald'),
    }));
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawArrow(a, b, col, alpha, width) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = col;
    ctx.lineWidth = width * SC;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
    const ang = Math.atan2(b.y - a.y, b.x - a.x);
    const sz = 11 * SC;
    ctx.beginPath();
    ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - sz * Math.cos(ang - 0.42), b.y - sz * Math.sin(ang - 0.42));
    ctx.lineTo(b.x - sz * Math.cos(ang + 0.42), b.y - sz * Math.sin(ang + 0.42));
    ctx.closePath();
    ctx.fillStyle = col;
    ctx.fill();
    ctx.restore();
  }

  function drawNode(n, isActive, pulse, badge) {
    const s = 1 + (isActive ? 0.04 * pulse : 0);
    const w = NW * s, h = NH * s;
    const x = n.x - w / 2, y = n.y - h / 2;
    const col = C(n.color);
    ctx.save();
    ctx.fillStyle = col.fill;
    ctx.strokeStyle = col.stroke;
    ctx.lineWidth = (isActive ? 3.4 : 2.0) * SC;
    ctx.shadowColor = isActive ? col.glow : 'rgba(0,0,0,0.0)';
    ctx.shadowBlur = isActive ? 26 * SC : 0;
    roundRect(x, y, w, h, 16 * SC);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#F4F8FF';
    ctx.font = '800 ' + Math.round(27 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText(n.label, n.x, n.y + (badge ? -8 * SC : 0));
    if (badge) {
      ctx.fillStyle = '#CBD5E1';
      ctx.font = '700 ' + Math.round(18 * SC) + 'px "Segoe UI", sans-serif';
      ctx.fillText(badge, n.x, n.y + 22 * SC);
    }
    ctx.restore();
  }

  function drawChip(cx, cy, text, stroke, fill, textColor) {
    ctx.save();
    ctx.font = '800 ' + Math.round(23 * SC) + 'px "Segoe UI", sans-serif';
    const tw = ctx.measureText(text).width + 40 * SC;
    const th = 50 * SC;
    ctx.fillStyle = fill;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2.4 * SC;
    ctx.shadowColor = stroke;
    ctx.shadowBlur = 24 * SC;
    roundRect(cx - tw / 2, cy - th / 2, tw, th, 14 * SC);
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, cx, cy + 1 * SC);
    ctx.restore();
  }

  function drawLaneCard(side, alpha) {
    const cx = (side === 'left') ? LX : RX;
    ctx.save();
    ctx.globalAlpha = alpha;
    const x = cx - LANE_HALF, y = LANE_TOP, w = LANE_HALF * 2, h = LANE_BOT - LANE_TOP;
    ctx.fillStyle = 'rgba(148,163,184,0.045)';
    ctx.strokeStyle = 'rgba(148,163,184,0.16)';
    ctx.lineWidth = 1.6 * SC;
    roundRect(x, y, w, h, 26 * SC);
    ctx.fill();
    ctx.stroke();

    const lane = (side === 'left') ? STATE.left : STATE.right;
    ctx.textAlign = 'center';
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 ' + Math.round(30 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText(String(lane.title || ''), cx, y + 46 * SC);
    ctx.fillStyle = '#8A9AB5';
    ctx.font = '700 ' + Math.round(20 * SC) + 'px "Segoe UI", sans-serif';
    ctx.fillText(String(lane.sub || ''), cx, y + 76 * SC);

    // Memory meter (right lane only)
    if (side === 'right') {
      const memT = clamp01((progressLP - 0.30) / 0.55);
      const bw = LANE_HALF * 1.5, bx = cx - bw / 2, by = y + 96 * SC, bh = 13 * SC;
      ctx.fillStyle = 'rgba(148,163,184,0.20)';
      roundRect(bx, by, bw, bh, bh / 2); ctx.fill();
      const grad = ctx.createLinearGradient(bx, 0, bx + bw, 0);
      grad.addColorStop(0, '#F59E0B');
      grad.addColorStop(1, '#10B981');
      ctx.fillStyle = grad;
      roundRect(bx, by, Math.max(bh, bw * memT), bh, bh / 2); ctx.fill();
      ctx.fillStyle = '#E5B96B';
      ctx.textAlign = 'left';
      ctx.font = '800 ' + Math.round(19 * SC) + 'px "Consolas", monospace';
      ctx.fillText(String(lane.memory_label || ''), bx, y + 130 * SC);
    } else {
      ctx.textAlign = 'left';
      ctx.fillStyle = '#7C8AA3';
      ctx.font = '800 ' + Math.round(19 * SC) + 'px "Consolas", monospace';
      ctx.fillText(String(lane.counter || ''), cx - LANE_HALF * 0.75, y + 112 * SC);
    }
    ctx.restore();
  }

  // ---- Left lane single-pass packet (dead-end) ----
  function drawLeftPacket(lp) {
    const nd = nodesOf('left');
    if (nd.length < 3) return;
    const p = clamp01((lp - 0.18) / 0.44);
    const segA = { a: nd[0], b: nd[1] }, segB = { a: nd[1], b: nd[2] };
    let pt, segIdx;
    if (p <= 0.5) { const t = p / 0.5; pt = { x: lerp(segA.a.x, segA.b.x, t), y: lerp(segA.a.y, segA.b.y, t) }; segIdx = 0; }
    else { const t = (p - 0.5) / 0.5; pt = { x: lerp(segB.a.x, segB.b.x, t), y: lerp(segB.a.y, segB.b.y, t) }; segIdx = 1; }

    ctx.save();
    ctx.fillStyle = 'rgba(56,189,248,0.95)';
    ctx.shadowColor = 'rgba(56,189,248,0.9)';
    ctx.shadowBlur = 22 * SC;
    ctx.beginPath(); ctx.arc(pt.x, pt.y, 11 * SC, 0, Math.PI * 2); ctx.fill();
    ctx.restore();

    // Live counters on the flown node
    const actIdx = (p < 0.25) ? 0 : (p < 0.75 ? 1 : 2);
    nd.forEach((n, i) => {
      drawNode(n, i === actIdx, 0.6 + 0.4 * Math.sin(lp * 12), null);
    });
    if (segIdx === 0) drawArrow({ x: nd[0].x, y: nd[0].y + NHALF * 0.7 }, { x: nd[1].x, y: nd[1].y - NHALF * 0.7 }, '#38BDF8', 0.55, 3);
    drawArrow({ x: nd[1].x, y: nd[1].y + NHALF * 0.7 }, { x: nd[2].x, y: nd[2].y - NHALF * 0.7 }, '#38BDF8', 0.55, 3);

    if (p >= 0.985) {
      drawChip(nd[2].x, nd[2].y + 92 * SC, '✕ No retry · ends here', '#EF4444', 'rgba(42,13,19,0.94)', '#FDA4AF');
    }
  }

  // ---- Right lane cyclic loop with failure -> reflection -> recovery ----
  function sampleArc(a, b) {
    const p0 = [a.x + NHALF, a.y], p3 = [b.x + NHALF, b.y];
    const c1 = [a.x + NHALF + 108 * SC, a.y];
    const c2 = [b.x + NHALF + 108 * SC, b.y];
    const out = [];
    for (let i = 0; i <= 8; i++) {
      const t = i / 8, mt = 1 - t;
      const x = mt * mt * mt * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t * t * t * p3[0];
      const y = mt * mt * mt * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t * t * t * p3[1];
      out.push({ x, y });
    }
    return out;
  }
  function arcControl(a, b) {
    return { c1: [a.x + NHALF + 108 * SC, a.y], c2: [b.x + NHALF + 108 * SC, b.y] };
  }

  function buildRightSegs() {
    const nd = nodesOf('right');
    const segs = [];
    segs.push({ a: { x: nd[0].x, y: nd[0].y + NHALF * 0.7 }, b: { x: nd[1].x, y: nd[1].y - NHALF * 0.7 }, w: 1, kind: 'f' });
    segs.push({ a: { x: nd[1].x, y: nd[1].y + NHALF * 0.7 }, b: { x: nd[2].x, y: nd[2].y - NHALF * 0.7 }, w: 1, kind: 'f' });
    segs.push({ a: { x: nd[2].x, y: nd[2].y + NHALF * 0.7 }, b: { x: nd[3].x, y: nd[3].y - NHALF * 0.7 }, w: 1, kind: 'tool1' });
    const arc = sampleArc(nd[3], nd[1]);
    for (let i = 0; i < arc.length - 1; i++) segs.push({ a: arc[i], b: arc[i + 1], w: 0.16, kind: 'reflect' });
    segs.push({ a: { x: nd[1].x, y: nd[1].y + NHALF * 0.7 }, b: { x: nd[2].x, y: nd[2].y - NHALF * 0.7 }, w: 1, kind: 'f' });
    segs.push({ a: { x: nd[2].x, y: nd[2].y + NHALF * 0.7 }, b: { x: nd[3].x, y: nd[3].y - NHALF * 0.7 }, w: 1, kind: 'f' });
    segs.push({ a: { x: nd[3].x, y: nd[3].y + NHALF * 0.7 }, b: { x: nd[4].x, y: nd[4].y - NHALF * 0.7 }, w: 1, kind: 'final' });
    return segs;
  }

  function drawRightLoop(lp, wp) {
    const nd = nodesOf('right');
    if (nd.length < 5) return;
    const segs = buildRightSegs();
    const total = segs.reduce((s, g) => s + g.w, 0);
    const prog = clamp01((lp - 0.10) / 0.74);
    let d = prog * total, cur = segs[segs.length - 1], localT = 1;
    for (const g of segs) {
      if (d <= g.w || g === segs[segs.length - 1]) { localT = clamp01(d / g.w); cur = g; break; }
      d -= g.w;
    }
    const pt = { x: lerp(cur.a.x, cur.b.x, localT), y: lerp(cur.a.y, cur.b.y, localT) };
    const kind = cur.kind;

    // Feedback arc (dashed) always faintly visible
    const ac = arcControl(nd[3], nd[1]);
    ctx.save();
    ctx.setLineDash([12 * SC, 9 * SC]);
    ctx.lineDashOffset = -(lp * 260 * SC) % (21 * SC);
    const reflecting = (kind === 'reflect');
    ctx.strokeStyle = reflecting ? '#A855F7' : 'rgba(148,163,184,0.34)';
    ctx.lineWidth = (reflecting ? 4.4 : 2.4) * SC;
    if (reflecting) { ctx.shadowColor = 'rgba(168,85,247,0.7)'; ctx.shadowBlur = 22 * SC; }
    ctx.beginPath();
    ctx.moveTo(nd[3].x + NHALF, nd[3].y);
    ctx.bezierCurveTo(ac.c1[0], ac.c1[1], ac.c2[0], ac.c2[1], nd[1].x + NHALF, nd[1].y);
    ctx.stroke();
    ctx.restore();

    // Forward arrows (dim baseline)
    drawArrow({ x: nd[0].x, y: nd[0].y + NHALF * 0.7 }, { x: nd[1].x, y: nd[1].y - NHALF * 0.7 }, 'rgba(16,185,129,0.65)', 0.7, 3);
    drawArrow({ x: nd[1].x, y: nd[1].y + NHALF * 0.7 }, { x: nd[2].x, y: nd[2].y - NHALF * 0.7 }, 'rgba(168,85,247,0.65)', 0.7, 3);
    drawArrow({ x: nd[2].x, y: nd[2].y + NHALF * 0.7 }, { x: nd[3].x, y: nd[3].y - NHALF * 0.7 }, 'rgba(245,158,11,0.65)', 0.7, 3);
    drawArrow({ x: nd[3].x, y: nd[3].y + NHALF * 0.7 }, { x: nd[4].x, y: nd[4].y - NHALF * 0.7 }, 'rgba(16,185,129,0.65)', 0.7, 3);

    // Active node highlight
    let actIdx = 0;
    if (kind === 'reflect') actIdx = 1;
    else if (kind === 'final' || (kind === 'f' && prog > 0.72)) actIdx = 4;
    else if (kind === 'tool1') actIdx = 2;
    else if (prog > 0.18 && prog < 0.34) actIdx = 1;
    const pu = 0.6 + 0.4 * Math.sin(lp * 14);
    nd.forEach((n, i) => {
      let badge = null;
      if (i === 2 && (kind === 'tool1' || kind === 'f')) badge = String(STATE.right.tool || 'Tool');
      drawNode(n, i === actIdx, pu, badge);
    });

    // Tool pill pulse
    if (kind === 'tool1') {
      drawChip(nd[2].x + 200 * SC, nd[2].y, String(STATE.right.tool || 'Tool'), '#F59E0B', 'rgba(42,31,5,0.94)', '#FCD34D');
    }

    // Failure spark (Loop #1)
    if (kind === 'tool1' && localT > 0.35) {
      ctx.save();
      ctx.globalAlpha = 0.9;
      ctx.strokeStyle = '#EF4444'; ctx.lineWidth = 4 * SC;
      ctx.shadowColor = 'rgba(239,68,68,0.9)'; ctx.shadowBlur = 26 * SC;
      ctx.beginPath(); ctx.arc(nd[3].x, nd[3].y, 62 * SC, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
      drawChip(nd[3].x, nd[3].y + 96 * SC, '⚠ ' + String(STATE.right.fail_reason || 'Error'), '#EF4444', 'rgba(42,13,19,0.94)', '#FCA5A5');
    }

    // Reflection pulse
    if (reflecting) {
      drawChip(nd[1].x + NHALF + 150 * SC, (nd[1].y + nd[3].y) / 2, '↺ ' + String(STATE.right.reflect_text || 'Reflecting...'), '#A855F7', 'rgba(27,16,54,0.96)', '#D8B4FE');
    }

    // Recovery glow (Loop #2 verified)
    if (kind === 'final' && localT > 0.5) {
      drawChip(nd[4].x + NHALF + 118 * SC, nd[4].y, '✓ Verified', '#10B981', 'rgba(6,42,33,0.95)', '#6EE7B7');
      ctx.save();
      ctx.strokeStyle = '#10B981'; ctx.lineWidth = 4 * SC;
      ctx.shadowColor = 'rgba(16,185,129,0.9)'; ctx.shadowBlur = 26 * SC;
      ctx.beginPath(); ctx.arc(nd[4].x, nd[4].y, 60 * SC, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
    }

    // Moving packet + trail
    ctx.save();
    ctx.fillStyle = '#FFFFFF';
    ctx.shadowColor = kind === 'reflect' ? 'rgba(168,85,247,0.95)' : (kind === 'tool1' ? 'rgba(245,158,11,0.95)' : 'rgba(16,185,129,0.95)');
    ctx.shadowBlur = 26 * SC;
    ctx.beginPath(); ctx.arc(pt.x, pt.y, 12 * SC, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = 0.4;
    ctx.beginPath(); ctx.arc(pt.x, pt.y, 20 * SC, 0, Math.PI * 2); ctx.fill();
    ctx.restore();

    return { kind, prog, localT };
  }

  function computeCam(lp) {
    const mode = STATE.mode;
    let fx = W / 2, fy = 830, zoom = 1.0, leftA = 1, rightA = 1;
    if (mode === 'llm_only') {
      const f = smooth((lp - 0.06) / 0.16);
      fx = lerp(W / 2, LX, f);
      zoom = 1.0 + 0.10 * f;
      rightA = 1 - 0.55 * f;
    } else if (mode === 'agent_loop') {
      const f = smooth((lp - 0.16) / 0.18);
      const back = smooth((lp - 0.90) / 0.10);
      const f2 = f * (1 - back);
      fx = lerp(W / 2, RX, f2);
      zoom = 1.0 + 0.10 * f2;
      leftA = 1 - 0.58 * f2;
      rightA = 1;
    } else {
      const f = smooth((lp - 0.02) / 0.12);
      zoom = 1.0 + 0.04 * f;
    }
    return { fx, fy, zoom, leftA, rightA };
  }

  function updateHUD(lp, res) {
    const tCalls = document.getElementById('tCalls');
    const tLoop = document.getElementById('tLoop');
    const tMem = document.getElementById('tMem');
    let calls = '1', loop = '0 / 0', mem = 'None', cls = 't-pill';
    if (STATE.mode === 'agent_loop' && res) {
      const k = res.kind;
      if (k === 'tool1') { calls = '1'; loop = '#1'; mem = 'Reading…'; cls = 't-pill warn'; }
      else if (k === 'reflect') { calls = '2'; loop = '#1 retry'; mem = '2 items'; cls = 't-pill warn'; }
      else if (k === 'final' || (k === 'f' && res.prog > 0.72)) { calls = '3'; loop = '#2'; mem = 'Active'; cls = 't-pill ok'; }
      else { calls = '1'; loop = '#1'; mem = 'Reading…'; cls = 't-pill warn'; }
    }
    tCalls.className = cls; tCalls.querySelector('.v').textContent = calls;
    tLoop.className = cls; tLoop.querySelector('.v').textContent = loop;
    tMem.className = cls; tMem.querySelector('.v').textContent = mem;
  }

  let progressLP = 0, progressWP = 0;

  function draw() {
    const lp = progressLP, wp = progressWP;
    ctx.clearRect(0, 0, W, H);
    const cam = computeCam(lp);

    ctx.save();
    ctx.translate(W / 2, cam.fy);
    ctx.scale(cam.zoom, cam.zoom);
    ctx.translate(-cam.fx, -cam.fy);

    drawLaneCard('left', cam.leftA);
    drawLaneCard('right', cam.rightA);

    let res = null;
    const mode = STATE.mode;
    if (mode === 'llm_only' || mode === 'split_intro' || mode === 'verdict') {
      drawLeftPacket(lp);
    }
    if (mode === 'agent_loop' || mode === 'verdict') {
      res = drawRightLoop(lp, wp);
    }
    if (mode === 'split_intro') {
      res = drawRightLoop(Math.min(0.34, lp), wp);
    }
    ctx.restore();

    updateHUD(lp, res);
  }

  window.__setStudioProgress = function (lp, wp) {
    progressLP = clamp01(lp);
    progressWP = clamp01(wp !== undefined ? wp : lp);
    const cap = document.getElementById('captionText');
    const cf = clamp01((progressWP - 0.05) / 0.30);
    cap.style.opacity = (0.15 + 0.85 * cf).toFixed(3);
    document.getElementById('capBar').style.width = (progressWP * 100).toFixed(1) + '%';
    const ctaRow = document.getElementById('ctaRow');
    if (STATE.mode === 'cta') {
      ctaRow.classList.add('on');
      ctaRow.style.opacity = clamp01((progressWP - 0.28) / 0.25).toFixed(3);
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


def render_v6_agent_loop_scene_frames(
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
    """Renders continuous LLM-vs-Agent cognitive-loop frames + HUD for a Studio V6 scene."""
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

    html_doc = _build_agent_loop_html(scene, prev_scene, w, h, tone=tone)
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
    draw.rectangle([60, 300, w - 60, 500], outline=(56, 189, 248), width=3)
    draw.text((80, 330), "Simple LLM (linear)  vs  Autonomous Agent (loop)", fill=(56, 189, 248))
    draw.rectangle([60, 540, w - 60, 1240], outline=(168, 85, 247), width=3)
    draw.text((80, 580), "Goal -> Reason -> Tool -> Observe -> Reflect -> Final", fill=(216, 180, 254))
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir
