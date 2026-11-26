"""
Studio V2 — Spatial Isometric World Renderer (@thetechypenguin Style).
Renders ONE persistent 2.5D Isometric Architecture World on HTML5 Canvas + Glassy Top HUD Card,
with smooth cubic-bezier camera flyovers (`prev_focus` -> `cur_focus`), glowing dashed IAC/Prod zones,
animated 3D isometric servers/cylinders/gateways/data-packets, and hook/split/poll frames.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS

_ACCENT_HEX = {
    "cyan": "#38BDF8",
    "emerald": "#34D399",
    "amber": "#FBBF24",
    "rose": "#F43F5E",
    "purple": "#A855F7",
    "blue": "#3B82F6",
}


def _compute_camera_center(world_spec: Dict[str, Any], focus_ids: List[str]) -> Dict[str, float]:
    nodes = list(world_spec.get("nodes") or [])
    by_id = {str(n.get("id")): n for n in nodes if n.get("id")}
    chosen = [by_id[fid] for fid in (focus_ids or []) if fid in by_id]
    if not chosen:
        chosen = nodes[:3] if nodes else [{"x": 550, "y": 550}]
    xs = [float(n.get("x", 550)) for n in chosen]
    ys = [float(n.get("y", 550)) for n in chosen]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    span = max(240.0, max(xs) - min(xs) + max(ys) - min(ys))
    zoom = max(0.76, min(1.38, 620.0 / span))
    return {"cx": cx, "cy": cy, "zoom": round(zoom, 3)}


def _build_isometric_html(
    scene: Dict[str, Any],
    prev_scene: Optional[Dict[str, Any]],
    width: int,
    height: int,
) -> str:
    vd = dict(scene.get("visual_data") or {})
    prev_vd = dict((prev_scene or {}).get("visual_data") or {})
    world_spec = dict(vd.get("world_spec") or {})
    scene_mode = str(vd.get("scene_mode") or "world_cam")
    watermark = str(vd.get("watermark") or vd.get("header_brand") or "@nanopro").strip()
    if not watermark.startswith("@"):
        watermark = "@" + watermark
    wm_rest = html.escape(watermark[1:])

    hud_pill = html.escape(str(vd.get("hud_pill") or scene.get("role", "SYSTEM").upper()))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))
    accent_hex = _ACCENT_HEX.get(str(vd.get("accent_color") or "cyan"), "#38BDF8")

    # Camera keyframes for continuous smooth flyover between adjacent world scenes
    cur_cam = _compute_camera_center(world_spec, list(vd.get("focus_node_ids") or []))
    if prev_vd.get("scene_mode") == "world_cam":
        prev_cam = _compute_camera_center(world_spec, list(prev_vd.get("focus_node_ids") or []))
    else:
        prev_cam = cur_cam

    is_wide = width > height
    sc = min(width, height) / 1080.0

    # Top overlay variations for hook_chat / split_compare / world_cam / cta_poll
    hud_block = ""
    if scene_mode == "hook_chat":
        chan = html.escape(str(vd.get("chat_channel") or "meet · system-interview"))
        q_snd = html.escape(str(vd.get("question_sender") or "INTERVIEWER"))
        q_txt = html.escape(str(vd.get("question_text") or ""))
        bad_ans = html.escape(str(vd.get("bad_answer") or ""))
        stamp = html.escape(str(vd.get("stamp") or "REJECTED ✗"))
        hud_block = f"""
        <div class="hook-overlay">
          <div class="meet-card reveal" data-p="0.04">
            <div class="meet-bar"><span class="dots">•••</span><span>{chan}</span></div>
            <div class="meet-msg">
              <div class="m-av">👩‍💼</div>
              <div>
                <div class="m-who">{q_snd}</div>
                <div class="m-bub">{q_txt}</div>
              </div>
            </div>
            <div class="meet-ans reveal" data-p="0.34">
              <div class="m-ans-lbl">YOU</div>
              <div class="m-bub ans">{bad_ans}</div>
            </div>
            <div class="rej-stamp reveal" data-p="{float(vd.get('stamp_delay_p', 0.62)):.2f}">{stamp}</div>
          </div>
        </div>"""
    elif scene_mode == "split_compare":
        lc = dict(vd.get("left_card") or {"title": "BLUE", "sub": "Live v1.0", "color": "blue"})
        rc = dict(vd.get("right_card") or {"title": "GREEN", "sub": "New v2.0", "color": "emerald"})
        lcol = _ACCENT_HEX.get(str(lc.get("color") or "blue"), "#3B82F6")
        rcol = _ACCENT_HEX.get(str(rc.get("color") or "emerald"), "#34D399")
        hud_block = f"""
        <div class="split-overlay">
          <div class="glow-pillar reveal" data-p="0.10" style="background:linear-gradient(160deg,{lcol}CC,{lcol}55);box-shadow:0 0 60px {lcol}55">
            <div class="gp-title">{html.escape(str(lc.get('title') or ''))}</div>
            <div class="gp-sub">{html.escape(str(lc.get('sub') or ''))}</div>
          </div>
          <div class="glow-pillar reveal" data-p="0.32" style="background:linear-gradient(160deg,{rcol}CC,{rcol}55);box-shadow:0 0 60px {rcol}55">
            <div class="gp-title">{html.escape(str(rc.get('title') or ''))}</div>
            <div class="gp-sub">{html.escape(str(rc.get('sub') or ''))}</div>
          </div>
        </div>"""
    elif scene_mode == "cta_poll":
        oa = html.escape(str(vd.get("option_a") or "🔵 Option A"))
        ob = html.escape(str(vd.get("option_b") or "🌙 Option B"))
        fn = html.escape(str(vd.get("footer_note") or ""))
        hud_block = f"""
        <div class="poll-overlay">
          <div class="poll-row reveal" data-p="0.22">
            <div class="poll-btn primary">{oa}</div>
            <div class="poll-btn">{ob}</div>
          </div>
          {f'<div class="poll-note reveal" data-p="0.48">{fn}</div>' if fn else ''}
        </div>"""
    else:
        eyebrow = html.escape(str(vd.get("card_eyebrow") or hud_pill))
        ctitle = html.escape(str(vd.get("card_title") or ""))
        bullets = [html.escape(str(b)) for b in (vd.get("card_bullets") or [])[:2]]
        b_html = " &nbsp;·&nbsp; ".join(bullets)
        hud_block = f"""
        <div class="hud-card reveal" data-p="0.06" style="border-top:4px solid {accent_hex};box-shadow:0 18px 46px rgba(0,0,0,0.55),0 -8px 34px {accent_hex}2E">
          <div class="hud-eye" style="color:{accent_hex}">{eyebrow}</div>
          <div class="hud-title">{ctitle}</div>
          {f'<div class="hud-bul">{b_html}</div>' if b_html else ''}
        </div>"""

    scene_state_json = json.dumps({
        "world": world_spec,
        "scene_mode": scene_mode,
        "prev_cam": prev_cam,
        "cur_cam": cur_cam,
        "active_edges": list(vd.get("active_edge_ids") or []),
        "node_overrides": dict(vd.get("node_overrides") or {}),
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: radial-gradient(circle at 50% 10%, {accent_hex}26 0%, #0A1022 46%, #050814 100%);
    color: #F8FAFC;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }}
  canvas#iso {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
  .wm-pill {{
    position: absolute; top: {int(38*sc)}px; left: {int(42*sc)}px; z-index: 10;
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.85); border: 1.5px solid rgba(148,163,184,0.28);
    font-size: {int(24*sc)}px; font-weight: 800; color: #F8FAFC;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .top-zone {{
    position: relative; z-index: 8; width: 100%;
    padding: {int(115*sc if not is_wide else 80*sc)}px {int(52*sc)}px 0;
    display: flex; flex-direction: column; align-items: center; text-align: center;
  }}
  .hud-pill {{
    display: inline-flex; align-items: center; gap: 8px; padding: {int(6*sc)}px {int(16*sc)}px; border-radius: 999px;
    background: rgba(9,17,40,0.72); border: 1px solid {accent_hex}55;
    font-size: {int(19*sc)}px; font-weight: 800; letter-spacing: 3px; color: {accent_hex}; margin-bottom: {int(12*sc)}px;
  }}
  .hud-pill .dot {{ width: 9px; height: 9px; border-radius: 50%; background: {accent_hex}; opacity: 0.7; }}
  .headline {{
    font-size: {int(64*sc if not is_wide else 50*sc)}px; font-weight: 900; line-height: 1.12; margin-bottom: {int(22*sc)}px;
    text-shadow: 0 6px 26px rgba(0,0,0,0.65);
  }}
  .headline .acc {{ color: {accent_hex}; }}
  .hud-card {{
    width: min(100%, {int(920*sc)}px); text-align: left;
    background: rgba(11, 18, 38, 0.92); backdrop-filter: blur(12px);
    border-radius: {int(22*sc)}px; border: 1px solid rgba(148,163,184,0.2);
    padding: {int(24*sc)}px {int(30*sc)}px;
  }}
  .hud-eye {{ font-size: {int(18*sc)}px; font-weight: 800; letter-spacing: 2.5px; margin-bottom: 6px; }}
  .hud-title {{ font-size: {int(36*sc)}px; font-weight: 800; color: #F8FAFC; line-height: 1.2; }}
  .hud-bul {{ margin-top: 10px; font-size: {int(24*sc)}px; color: #94A3B8; font-weight: 600; }}

  /* Hook Chat Overlay */
  .hook-overlay {{ width: min(100%, {int(880*sc)}px); margin-top: {int(34*sc)}px; }}
  .meet-card {{
    background: rgba(15,23,42,0.94); border: 1.8px solid rgba(148,163,184,0.28);
    border-radius: 26px; padding: {int(26*sc)}px; text-align: left; position: relative;
    box-shadow: 0 28px 80px rgba(0,0,0,0.65);
  }}
  .meet-bar {{ display: flex; gap: 14px; color: #94A3B8; font-size: {int(20*sc)}px; margin-bottom: {int(22*sc)}px; border-bottom: 1px solid rgba(148,163,184,0.16); padding-bottom: 12px; }}
  .meet-msg {{ display: flex; gap: 16px; align-items: flex-start; }}
  .m-av {{ width: {int(52*sc)}px; height: {int(52*sc)}px; border-radius: 50%; background: #1E293B; display: flex; align-items: center; justify-content: center; font-size: {int(26*sc)}px; }}
  .m-who {{ font-size: {int(18*sc)}px; color: #94A3B8; font-weight: 800; letter-spacing: 2px; margin-bottom: 6px; }}
  .m-bub {{ background: rgba(30,41,59,0.75); border: 1.5px solid rgba(148,163,184,0.25); border-radius: 16px; padding: {int(18*sc)}px {int(22*sc)}px; font-size: {int(27*sc)}px; line-height: 1.38; }}
  .meet-ans {{ margin-top: {int(26*sc)}px; display: flex; flex-direction: column; align-items: flex-end; }}
  .m-ans-lbl {{ font-size: {int(17*sc)}px; color: #FACC15; font-weight: 800; margin-bottom: 6px; }}
  .m-bub.ans {{ border-color: #F43F5E88; background: rgba(45,18,28,0.82); max-width: 86%; }}
  .rej-stamp {{
    margin: {int(26*sc)}px auto 0; width: fit-content; transform: rotate(-6deg);
    border: 4.5px solid #F43F5E; border-radius: 14px; padding: {int(10*sc)}px {int(30*sc)}px;
    color: #F43F5E; font-size: {int(36*sc)}px; font-weight: 900; letter-spacing: 3px;
    background: rgba(244,63,94,0.12); box-shadow: 0 0 36px rgba(244,63,94,0.35);
  }}

  /* Split Compare */
  .split-overlay {{
    display: grid; grid-template-columns: 1fr 1fr; gap: {int(24*sc)}px;
    width: min(100%, {int(840*sc)}px); margin-top: {int(50*sc)}px;
  }}
  .glow-pillar {{
    height: {int(460*sc if not is_wide else 300*sc)}px; border-radius: 26px; padding: {int(28*sc)}px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
    border: 2px solid rgba(255,255,255,0.25);
  }}
  .gp-title {{ font-size: {int(46*sc)}px; font-weight: 900; color: #FFFFFF; letter-spacing: 2px; }}
  .gp-sub {{ font-size: {int(24*sc)}px; color: rgba(255,255,255,0.88); font-weight: 600; }}

  /* Poll CTA */
  .poll-overlay {{ margin-top: {int(44*sc)}px; display: flex; flex-direction: column; align-items: center; gap: 22px; width: 100%; }}
  .poll-row {{ display: flex; gap: 18px; justify-content: center; flex-wrap: wrap; }}
  .poll-btn {{
    padding: {int(18*sc)}px {int(34*sc)}px; border-radius: 16px;
    background: rgba(15,23,42,0.92); border: 2px solid rgba(148,163,184,0.4);
    font-size: {int(28*sc)}px; font-weight: 800; color: #E2E8F0;
  }}
  .poll-btn.primary {{ border-color: #38BDF8; background: rgba(14,45,78,0.92); color: #FFFFFF; box-shadow: 0 0 28px rgba(56,189,248,0.35); }}
  .poll-note {{ font-size: {int(24*sc)}px; color: #FACC15; font-weight: 700; }}

  .reveal {{ opacity: 0; transform: translateY(14px); }}
  .reveal.on {{ opacity: 1; transform: translateY(0); }}
</style>
</head>
<body>
  <canvas id="iso" width="{width}" height="{height}"></canvas>
  <div class="wm-pill"><span class="at">@</span>{wm_rest}</div>
  <div class="top-zone">
    <div class="hud-pill"><span class="dot"></span>{hud_pill}</div>
    <div class="headline">{h_white} <span class="acc">{h_accent}</span></div>
    {hud_block}
  </div>

  <script>
    const STATE = {scene_state_json};
    const canvas = document.getElementById('iso');
    const ctx = canvas.getContext('2d');
    const W = {width}, H = {height};
    const COLORS = {{
      blue:    {{ top: '#60A5FA', left: '#2563EB', right: '#1D4ED8', glow: 'rgba(59,130,246,0.45)', stroke: '#60A5FA' }},
      emerald: {{ top: '#4ADE80', left: '#16A34A', right: '#15803D', glow: 'rgba(52,211,153,0.45)', stroke: '#34D399' }},
      amber:   {{ top: '#FCD34D', left: '#D97706', right: '#B45309', glow: 'rgba(251,191,36,0.45)', stroke: '#FBBF24' }},
      purple:  {{ top: '#C084FC', left: '#7E22CE', right: '#6B21A8', glow: 'rgba(168,85,247,0.45)', stroke: '#A855F7' }},
      rose:    {{ top: '#FB7185', left: '#E11D48', right: '#BE123C', glow: 'rgba(244,63,94,0.45)', stroke: '#F43F5E' }},
      cyan:    {{ top: '#67E8F9', left: '#0891B2', right: '#0E7490', glow: 'rgba(34,211,238,0.45)', stroke: '#22D3EE' }},
    }};

    function easeInOut(t) {{
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }}

    function isoProject(wx, wy, wz, camX, camY, zoom) {{
      const dx = (wx - camX) * zoom;
      const dy = (wy - camY) * zoom;
      const sx = W * 0.5 + (dx - dy) * 0.86;
      const sy = H * 0.64 + (dx + dy) * 0.44 - wz * zoom;
      return [sx, sy];
    }}

    function drawIsoPrism(wx, wy, sxLen, syLen, hz, col, camX, camY, zoom, zBase = 0) {{
      const hw = sxLen * 0.5, hh = syLen * 0.5;
      const p00 = isoProject(wx - hw, wy - hh, zBase, camX, camY, zoom);
      const p10 = isoProject(wx + hw, wy - hh, zBase, camX, camY, zoom);
      const p11 = isoProject(wx + hw, wy + hh, zBase, camX, camY, zoom);
      const p01 = isoProject(wx - hw, wy + hh, zBase, camX, camY, zoom);
      const t00 = isoProject(wx - hw, wy - hh, zBase + hz, camX, camY, zoom);
      const t10 = isoProject(wx + hw, wy - hh, zBase + hz, camX, camY, zoom);
      const t11 = isoProject(wx + hw, wy + hh, zBase + hz, camX, camY, zoom);
      const t01 = isoProject(wx - hw, wy + hh, zBase + hz, camX, camY, zoom);

      ctx.save();
      ctx.shadowColor = col.glow;
      ctx.shadowBlur = 18 * zoom;
      // Right face
      ctx.beginPath(); ctx.moveTo(t10[0],t10[1]); ctx.lineTo(t11[0],t11[1]); ctx.lineTo(p11[0],p11[1]); ctx.lineTo(p10[0],p10[1]); ctx.closePath();
      ctx.fillStyle = col.right; ctx.fill();
      // Left face
      ctx.beginPath(); ctx.moveTo(t01[0],t01[1]); ctx.lineTo(t11[0],t11[1]); ctx.lineTo(p11[0],p11[1]); ctx.lineTo(p01[0],p01[1]); ctx.closePath();
      ctx.fillStyle = col.left; ctx.fill();
      // Top face
      ctx.beginPath(); ctx.moveTo(t00[0],t00[1]); ctx.lineTo(t10[0],t10[1]); ctx.lineTo(t11[0],t11[1]); ctx.lineTo(t01[0],t01[1]); ctx.closePath();
      ctx.fillStyle = col.top; ctx.fill();
      ctx.restore();
    }}

    function drawIsoCylinder(wx, wy, rad, hz, col, camX, camY, zoom, label, sub) {{
      const [bx, by] = isoProject(wx, wy, 0, camX, camY, zoom);
      const [tx, ty] = isoProject(wx, wy, hz, camX, camY, zoom);
      const rx = rad * zoom * 0.92, ry = rad * zoom * 0.46;
      ctx.save();
      ctx.shadowColor = col.glow; ctx.shadowBlur = 22 * zoom;
      ctx.fillStyle = col.left;
      ctx.beginPath();
      ctx.ellipse(bx, by, rx, ry, 0, 0, Math.PI);
      ctx.lineTo(tx - rx, ty);
      ctx.ellipse(tx, ty, rx, ry, 0, Math.PI, 0, true);
      ctx.closePath();
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(tx, ty, rx, ry, 0, 0, Math.PI * 2);
      ctx.fillStyle = col.top; ctx.fill();
      ctx.restore();
      ctx.fillStyle = '#091128';
      ctx.font = `900 ${{Math.max(12, Math.round(18*zoom))}}px "Segoe UI", sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText(label, tx, ty + 6 * zoom);
      if (sub) {{
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.font = `700 ${{Math.max(10, Math.round(13*zoom))}}px "Segoe UI", sans-serif`;
        ctx.fillText(sub, tx, (ty + by) * 0.5 + 8 * zoom);
      }}
    }}

    function drawBadge(sx, sy, text, bg, fg, zoom) {{
      ctx.save();
      ctx.font = `800 ${{Math.max(11, Math.round(15*zoom))}}px "Segoe UI", sans-serif`;
      const tw = ctx.measureText(text).width + 22 * zoom;
      const th = 28 * zoom;
      ctx.fillStyle = bg;
      ctx.beginPath();
      ctx.roundRect(sx - tw / 2, sy - th / 2, tw, th, 9 * zoom);
      ctx.fill();
      ctx.fillStyle = fg;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, sx, sy);
      ctx.restore();
    }}

    function drawWorld(prog) {{
      ctx.clearRect(0, 0, W, H);
      if (STATE.scene_mode === 'hook_chat' || STATE.scene_mode === 'split_compare') return;

      const camT = easeInOut(Math.min(1, prog / 0.34));
      const c0 = STATE.prev_cam, c1 = STATE.cur_cam;
      const camX = c0.cx + (c1.cx - c0.cx) * camT;
      const camY = c0.cy + (c1.cy - c0.cy) * camT;
      const zoom = c0.zoom + (c1.zoom - c0.zoom) * camT;

      if (STATE.scene_mode === 'cta_poll') {{ ctx.save(); ctx.globalAlpha = 0.25; }}

      // 1. Isometric floor diamond grid
      ctx.save();
      ctx.strokeStyle = 'rgba(148,163,184,0.08)';
      ctx.lineWidth = 1.2;
      for (let g = 0; g <= 1200; g += 75) {{
        const a1 = isoProject(g, 0, 0, camX, camY, zoom), b1 = isoProject(g, 1200, 0, camX, camY, zoom);
        ctx.beginPath(); ctx.moveTo(a1[0], a1[1]); ctx.lineTo(b1[0], b1[1]); ctx.stroke();
        const a2 = isoProject(0, g, 0, camX, camY, zoom), b2 = isoProject(1200, g, 0, camX, camY, zoom);
        ctx.beginPath(); ctx.moveTo(a2[0], a2[1]); ctx.lineTo(b2[0], b2[1]); ctx.stroke();
      }}
      ctx.restore();

      const world = STATE.world || {{}};
      const nodes = world.nodes || [];
      const edges = world.edges || [];
      const zones = world.zones || [];
      const ovs = STATE.node_overrides || {{}};
      const byId = Object.fromEntries(nodes.map(n => [n.id, n]));

      // 2. Dashed Isometric Zones
      zones.forEach(z => {{
        const col = COLORS[z.color || 'cyan'] || COLORS.cyan;
        const p00 = isoProject(z.x, z.y, 0, camX, camY, zoom);
        const p10 = isoProject(z.x + z.w, z.y, 0, camX, camY, zoom);
        const p11 = isoProject(z.x + z.w, z.y + z.h, 0, camX, camY, zoom);
        const p01 = isoProject(z.x, z.y + z.h, 0, camX, camY, zoom);
        ctx.save();
        ctx.setLineDash([8 * zoom, 6 * zoom]);
        ctx.strokeStyle = col.stroke; ctx.lineWidth = 2 * zoom;
        ctx.fillStyle = col.glow.replace('0.45', '0.07');
        ctx.beginPath(); ctx.moveTo(p00[0],p00[1]); ctx.lineTo(p10[0],p10[1]); ctx.lineTo(p11[0],p11[1]); ctx.lineTo(p01[0],p01[1]); ctx.closePath();
        ctx.fill(); ctx.stroke();
        ctx.fillStyle = col.top;
        ctx.font = `800 ${{Math.round(14*zoom)}}px "Segoe UI", sans-serif`;
        ctx.fillText(z.label || '', (p01[0]+p11[0])*0.5 - 40*zoom, (p01[1]+p11[1])*0.5 + 18*zoom);
        ctx.restore();
      }});

      // 3. Edges & Travelling Data Packets
      const activeSet = new Set(STATE.active_edges || []);
      edges.forEach(e => {{
        const nf = byId[e.from], nt = byId[e.to];
        if (!nf || !nt) return;
        const ovF = ovs[nf.id] || {{}}, ovT = ovs[nt.id] || {{}};
        if (ovF.visible === false || ovT.visible === false) return;
        const col = COLORS[e.color || 'cyan'] || COLORS.cyan;
        const a = isoProject(nf.x, nf.y, 12, camX, camY, zoom);
        const b = isoProject(nt.x, nt.y, 12, camX, camY, zoom);
        const isAct = activeSet.has(e.id);
        ctx.save();
        if (!isAct) ctx.setLineDash([7 * zoom, 7 * zoom]);
        ctx.strokeStyle = isAct ? col.top : 'rgba(148,163,184,0.35)';
        ctx.lineWidth = (isAct ? 4.5 : 2.2) * zoom;
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
        if (isAct) {{
          for (let k = 0; k < 3; k++) {{
            const ph = (prog * 2.4 + k * 0.33) % 1;
            const px = a[0] + (b[0] - a[0]) * ph, py = a[1] + (b[1] - a[1]) * ph;
            ctx.fillStyle = '#FFFFFF';
            ctx.shadowColor = col.top; ctx.shadowBlur = 14 * zoom;
            ctx.beginPath(); ctx.arc(px, py, 6.5 * zoom, 0, Math.PI * 2); ctx.fill();
          }}
        }}
        ctx.restore();
      }});

      // 4. Depth-sort nodes back-to-front by (x + y) so 2.5D overlap is ALWAYS physically accurate
      const sortedNodes = [...nodes].sort((a, b) => (a.x + a.y) - (b.x + b.y));
      sortedNodes.forEach(n => {{
        const ov = ovs[n.id] || {{}};
        if (ov.visible === false) return;
        const col = COLORS[n.color || 'blue'] || COLORS.blue;
        const kind = n.kind || 'server_cluster';

        if (kind === 'factory_cube') {{
          drawIsoPrism(n.x, n.y, 118, 92, 62, col, camX, camY, zoom);
          drawIsoPrism(n.x - 24, n.y - 16, 26, 26, 102, col, camX, camY, zoom);
          const [lx, ly] = isoProject(n.x, n.y, 82, camX, camY, zoom);
          drawBadge(lx, ly - 18 * zoom, `${{n.label || 'CI/CD'}}`, '#0F172AEE', col.top, zoom);
        }} else if (kind === 'balancer_bar') {{
          drawIsoPrism(n.x, n.y, 230, 56, 42, col, camX, camY, zoom);
          const [lx, ly] = isoProject(n.x, n.y, 58, camX, camY, zoom);
          drawBadge(lx, ly - 10 * zoom, n.label || 'LOAD BALANCER', '#1E1B4BEE', '#E9D5FF', zoom);
        }} else if (kind === 'cylinder_store') {{
          drawIsoCylinder(n.x, n.y, 68, 72, col, camX, camY, zoom, n.label || 'STORE', n.sublabel || '');
          if (ov.badge) {{
            const [bx, by] = isoProject(n.x, n.y, 102, camX, camY, zoom);
            drawBadge(bx, by, ov.badge, '#064E3BEE', '#6EE7B7', zoom);
          }}
        }} else if (kind === 'test_gate') {{
          drawIsoPrism(n.x - 42, n.y, 18, 22, 92, col, camX, camY, zoom, 0);
          drawIsoPrism(n.x + 42, n.y, 18, 22, 92, col, camX, camY, zoom, 0);
          drawIsoPrism(n.x, n.y, 108, 24, 24, col, camX, camY, zoom, 82);
          const [gx, gy] = isoProject(n.x, n.y, 132, camX, camY, zoom);
          drawBadge(gx, gy, `✓ ${{ov.badge || n.sublabel || 'APPROVED'}}`, '#14532DEE', '#4ADE80', zoom);
        }} else {{ // server_cluster (3 staggered 3D racks)
          const offsets = [[-65, -24], [0, 0], [65, 24]];
          offsets.forEach(([ox, oy], idx) => {{
            drawIsoPrism(n.x + ox, n.y + oy, 48, 48, 86, col, camX, camY, zoom);
            if (ov.checks && prog > 0.25 + idx * 0.14) {{
              const [cxp, cyp] = isoProject(n.x + ox, n.y + oy, 108, camX, camY, zoom);
              drawBadge(cxp, cyp, '✓', '#16A34A', '#FFFFFF', zoom * 0.9);
            }}
          }});
          const [tx, ty] = isoProject(n.x, n.y, 132, camX, camY, zoom);
          if (ov.bug) {{
            drawBadge(tx, ty, '🐞 BUG DETECTED!', '#7F1D1DEE', '#FCA5A5', zoom);
          }} else if (ov.badge) {{
            const isLive = String(ov.badge).includes('LIVE');
            drawBadge(tx, ty, ov.badge, isLive ? '#1D4ED8EE' : '#1E293BEE', isLive ? '#FFFFFF' : '#94A3B8', zoom);
          }} else {{
            drawBadge(tx, ty, n.label || 'CLUSTER', '#0F172AEE', col.top, zoom);
          }}
        }}
      }});

      if (STATE.scene_mode === 'cta_poll') ctx.restore();
    }}

    window.__setStudioProgress = function(p) {{
      const prog = Math.max(0, Math.min(1, Number(p) || 0));
      document.querySelectorAll('.reveal').forEach(el => {{
        const dp = parseFloat(el.dataset.p || '0');
        if (prog >= dp) el.classList.add('on');
        else el.classList.remove('on');
      }});
      drawWorld(prog);
    }};
    window.__setStudioProgress(1.0);
  </script>
</body>
</html>"""


def render_v2_isometric_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    prev_scene: Optional[Dict[str, Any]] = None,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
) -> Path:
    """Renders continuous 2.5D Isometric World flyover frames + HUD for a Studio V2 scene."""
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    w, h = spec["width"], spec["height"]
    duration = max(1.2, float(scene.get("duration", 4.5)))
    total_frames = max(18, int(round(duration * VIDEO_FPS)))
    out_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.*"):
        try:
            old.unlink()
        except Exception:
            pass

    html_doc = _build_isometric_html(scene, prev_scene, w, h)
    from core.web_generative_engine import detect_web_engine
    pw_ok, exe_path = detect_web_engine()
    if pw_ok:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-vsync"]}
        if exe_path:
            kwargs["executable_path"] = exe_path
        browser = p.chromium.launch(**kwargs)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="domcontentloaded", timeout=12000)

        sc_start = float(scene.get("start_time", 0.0))
        words = list(scene_words or [])
        for f in range(total_frames):
            lin_p = f / max(1, total_frames - 1)
            cur_t = sc_start + lin_p * duration
            if words:
                spoken = sum(1 for wd in words if float(wd.get("start", 0.0)) <= cur_t)
                word_p = spoken / max(1, len(words))
                eff_p = min(1.0, 0.50 * word_p + 0.50 * lin_p)
            else:
                eff_p = lin_p
            page.evaluate("(p) => { if (window.__setStudioProgress) window.__setStudioProgress(p); }", round(eff_p, 4))
            page.screenshot(path=str(out_dir / f"frame_{f:04d}.jpg"), type="jpeg", quality=90)

        browser.close()
        p.stop()
        return out_dir

    # Graceful headless Pillow fallback
    from PIL import Image, ImageDraw
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (10, 16, 34))
    draw = ImageDraw.Draw(img)
    draw.text((80, 120), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(56, 189, 248))
    draw.rectangle([60, 260, w - 60, 460], fill=(15, 23, 42), outline=(56, 189, 248), width=3)
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir
