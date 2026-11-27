"""
Studio V4 — Blueprint Whiteboard Studio Renderer (ByteByteGo / Excalidraw Style).
Renders crisp, ultra-readable hand-drawn marker diagrams on a dark blueprint grid via Playwright Chromium:
  - Aspect-ratio calibrated viewBox (960x1320 for 9:16 portrait -> large sharp nodes & text!)
  - Engineering dark blueprint grid (minor 28px + major 140px grid lines)
  - Double-pass Excalidraw-style marker strokes with exact boundary-clipped curved arrows
  - Traveling glowing packet markers along edges + opaque high-contrast sticky callout cards
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS
from core.tone_engine import compute_synced_visual_progress, get_tone_profile

_ACCENT_HEX = {
    "cyan": "#38BDF8",
    "emerald": "#34D399",
    "amber": "#FBBF24",
    "rose": "#F43F5E",
    "purple": "#C084FC",
    "blue": "#60A5FA",
    "white": "#F8FAFC",
}


def _tone_whiteboard_style(tone: str, role: str, scene_tone: Optional[str]) -> Dict[str, Any]:
    prof = get_tone_profile(tone, scene_tone=scene_tone, role=role)
    t_key = prof.get("key", "whiteboard_analogy")
    accent = prof.get("accent_key", "cyan")
    if t_key in ("fireship_octane", "youth_friend_turbo", "cage_match_vs"):
        return {"draw_speed": 1.35, "wobble": 2.4, "tone_accent": accent}
    if t_key in ("war_story_postmortem", "dramatic_performance"):
        return {"draw_speed": 1.05, "wobble": 3.0, "tone_accent": "rose"}
    return {"draw_speed": 1.15, "wobble": 2.5, "tone_accent": accent}


def _build_whiteboard_html(
    scene: Dict[str, Any],
    width: int,
    height: int,
    tone: str = "auto_2026_director",
) -> str:
    vd = dict(scene.get("visual_data") or {})
    wb_style = _tone_whiteboard_style(tone, str(scene.get("role") or ""), scene.get("scene_tone"))
    accent_key = str(vd.get("accent_color") or wb_style["tone_accent"] or "cyan")
    accent_hex = _ACCENT_HEX.get(accent_key, "#38BDF8")

    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = (
        f'<span class="at">@</span>{html.escape(raw_wm[1:])}'
        if raw_wm.startswith("@")
        else html.escape(raw_wm)
    )
    hud_pill = html.escape(str(vd.get("hud_pill") or f"BLUEPRINT · {str(scene.get('role') or 'SKETCH').upper()}"))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))

    nodes = list(vd.get("diagram_nodes") or [])[:7]
    edges = list(vd.get("diagram_edges") or [])[:8]
    stickies = list(vd.get("sticky_notes") or [])[:2]
    footer_note = html.escape(str(vd.get("footer_pill") or ""))

    is_wide = width > height
    sc = min(width, height) / 1080.0
    pad_x = int((40 if not is_wide else 88) * sc)
    hl_px = int((56 if not is_wide else 42) * sc)

    # Calibrate virtual SVG coordinate space to stage proportions so shapes & text fill tall reels
    vb_w, vb_h = (1320, 680) if is_wide else ((1000, 900) if width == height else (960, 1280))

    wb_state = {
        "vb_w": vb_w,
        "vb_h": vb_h,
        "has_sticky": len(stickies) > 0,
        "nodes": nodes,
        "edges": edges,
        "stickies": stickies,
        "wobble": wb_style["wobble"],
        "draw_speed": wb_style["draw_speed"],
    }

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: radial-gradient(circle at 50% 18%, #10254A 0%, #081226 56%, #040914 100%);
    color: #F8FAFC;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }}
  .bp-grid {{
    position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(56,189,248,0.09) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,189,248,0.09) 1px, transparent 1px),
      linear-gradient(rgba(56,189,248,0.20) 1.5px, transparent 1.5px),
      linear-gradient(90deg, rgba(56,189,248,0.20) 1.5px, transparent 1.5px);
    background-size: 28px 28px, 28px 28px, 140px 140px, 140px 140px;
  }}
  .root {{
    position: relative; width: 100%; height: 100%; z-index: 2;
    display: flex; flex-direction: column;
    padding: {int(34*sc)}px {pad_x}px {int(42*sc)}px;
    gap: {int(14*sc)}px;
  }}
  .top-row {{ display: flex; align-items: center; justify-content: space-between; }}
  .wm-pill {{
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.92); border: 1.8px solid rgba(148,163,184,0.36);
    font-size: {int(23*sc)}px; font-weight: 800; color: #FFFFFF;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .hud-pill {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(9,20,42,0.92); border: 2px dashed {accent_hex};
    color: {accent_hex}; font-size: {int(20*sc)}px; font-weight: 900; letter-spacing: 2px;
  }}
  .headline {{
    text-align: center; line-height: 1.14; color: #FFFFFF;
    font-size: {hl_px}px; font-weight: 900; margin: {int(2*sc)}px 0;
    text-shadow: 0 6px 24px rgba(0,0,0,0.65);
  }}
  .headline .acc {{
    color: {accent_hex}; display: inline-block; position: relative;
    padding-bottom: {int(5*sc)}px;
    border-bottom: 4px dashed {accent_hex};
  }}

  /* Whiteboard Sketch Stage */
  .board-stage {{
    flex: 1; position: relative; border-radius: {int(24*sc)}px;
    border: 2.2px dashed rgba(56,189,248,0.42);
    background: rgba(6, 14, 32, 0.58);
    box-shadow: inset 0 0 60px rgba(8,20,48,0.75), 0 22px 60px rgba(0,0,0,0.55);
    overflow: hidden;
  }}
  .bp-corner {{
    position: absolute; font-family: "Cascadia Code", monospace;
    font-size: {int(16*sc)}px; color: rgba(125,211,252,0.55); letter-spacing: 1.5px; font-weight: 700;
  }}
  svg#wbSvg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}

  /* Aligned Bottom Sticky Callout Dock (never collides with diagram nodes) */
  #stickyLayer {{
    position: absolute; left: {int(24*sc)}px; right: {int(24*sc)}px; bottom: {int(22*sc)}px;
    z-index: 8; display: flex; align-items: stretch; justify-content: center; gap: {int(16*sc)}px;
    pointer-events: none;
  }}
  .sticky-note {{
    flex: 1; max-width: {int(720*sc)}px; min-width: {int(240*sc)}px;
    padding: {int(16*sc)}px {int(24*sc)}px; border-radius: 16px;
    background: rgba(11, 20, 40, 0.96); border: 2.5px solid #FACC15;
    box-shadow: 0 16px 38px rgba(0,0,0,0.72), 0 0 22px rgba(250,204,21,0.16);
    text-align: center;
  }}
  .sticky-tape {{
    width: {int(64*sc)}px; height: {int(10*sc)}px; border-radius: 5px;
    margin: -{int(22*sc)}px auto {int(10*sc)}px;
  }}
  .sticky-title {{
    font-size: {int(19*sc)}px; font-weight: 900; letter-spacing: 1.4px; margin-bottom: 5px;
  }}
  .sticky-txt {{
    font-size: {int(25*sc)}px; font-weight: 800; color: #FFFFFF; line-height: 1.32;
  }}

  .footer-pill {{
    align-self: center;
    padding: {int(12*sc)}px {int(32*sc)}px; border-radius: 14px;
    background: rgba(15,23,42,0.95); border: 2.2px dashed {accent_hex};
    color: #FFFFFF; font-size: {int(24*sc)}px; font-weight: 900; text-align: center;
    box-shadow: 0 0 26px {accent_hex}2E;
  }}
</style>
</head>
<body>
  <div class="bp-grid"></div>
  <div class="root">
    <div class="top-row">
      <div class="wm-pill">{wm_html}</div>
      <div class="hud-pill">✏️ {hud_pill}</div>
    </div>
    <div class="headline">{h_white} <span class="acc">{h_accent}</span></div>

    <div class="board-stage" id="boardStage">
      <div class="bp-corner" style="top:14px;left:18px">GRID 28px // REV-4</div>
      <svg id="wbSvg" viewBox="0 0 {vb_w} {vb_h}" preserveAspectRatio="xMidYMid meet"></svg>
      <div id="stickyLayer"></div>
    </div>

    {f'<div class="footer-pill" id="footerPill">{footer_note}</div>' if footer_note else ''}
  </div>

  <script>
    const STATE = {json.dumps(wb_state, ensure_ascii=False)};
    const VBW = STATE.vb_w || 920;
    const VBH = STATE.vb_h || 1260;
    const PAL = {{
      cyan: '#38BDF8', emerald: '#34D399', amber: '#FBBF24',
      rose: '#F43F5E', purple: '#C084FC', blue: '#60A5FA', white: '#F8FAFC'
    }};
    const svg = document.getElementById('wbSvg');
    const stickyLayer = document.getElementById('stickyLayer');
    const NS = 'http://www.w3.org/2000/svg';

    function mapX(x) {{ return (Number(x || 500) / 1000.0) * VBW; }}
    function mapY(y) {{ return (Number(y || 500) / 1000.0) * VBH; }}
    function mapW(w) {{ return Math.max(220, (Number(w || 240) / 1000.0) * VBW * 1.08); }}
    function mapH(h) {{ return Math.max(118, (Number(h || 120) / 1000.0) * VBH * 0.92); }}

    function prng(seed) {{
      let s = (seed * 9301 + 49297) % 233280;
      return () => {{ s = (s * 9301 + 49297) % 233280; return (s / 233280) - 0.5; }};
    }}

    function sketchLinePath(x1, y1, x2, y2, seed, wob) {{
      const r = prng(seed);
      const mx = (x1 + x2) / 2 + r() * wob * 2.6;
      const my = (y1 + y2) / 2 + r() * wob * 2.6;
      return `M ${{x1.toFixed(1)}} ${{y1.toFixed(1)}} Q ${{mx.toFixed(1)}} ${{my.toFixed(1)}} ${{x2.toFixed(1)}} ${{y2.toFixed(1)}}`;
    }}

    function sketchRectPaths(x, y, w, h, seed, wob) {{
      const r = prng(seed);
      const j = () => r() * wob * 2.0;
      const d1 = [
        sketchLinePath(x + j(), y + j(), x + w + j(), y + j(), seed + 1, wob),
        sketchLinePath(x + w + j(), y + j(), x + w + j(), y + h + j(), seed + 2, wob),
        sketchLinePath(x + w + j(), y + h + j(), x + j(), y + h + j(), seed + 3, wob),
        sketchLinePath(x + j(), y + h + j(), x + j(), y + j(), seed + 4, wob),
      ].join(' ');
      const d2 = [
        sketchLinePath(x + 2 + j(), y - 1 + j(), x + w - 1 + j(), y + 2 + j(), seed + 11, wob * 0.75),
        sketchLinePath(x + w + 1 + j(), y + 2 + j(), x + w - 2 + j(), y + h + j(), seed + 12, wob * 0.75),
        sketchLinePath(x + w + j(), y + h + 2 + j(), x + 2 + j(), y + h - 1 + j(), seed + 13, wob * 0.75),
        sketchLinePath(x - 1 + j(), y + h + j(), x + 1 + j(), y + 1 + j(), seed + 14, wob * 0.75),
      ].join(' ');
      return [d1, d2];
    }}

    // Exact boundary intersection from node center (cx, cy) toward (tx, ty)
    function boundaryPoint(node, tx, ty, pad = 10) {{
      const dx = tx - node.cx;
      const dy = ty - node.cy;
      if (Math.abs(dx) < 1e-4 && Math.abs(dy) < 1e-4) return [node.cx, node.cy];
      const hw = node.w * 0.5 + pad;
      const hh = node.h * 0.5 + pad;
      let t;
      if (String(node.data.kind || '').toLowerCase() === 'diamond') {{
        t = 1.0 / (Math.abs(dx) / hw + Math.abs(dy) / hh);
      }} else {{
        const tx_b = Math.abs(dx) > 1e-4 ? hw / Math.abs(dx) : 1e9;
        const ty_b = Math.abs(dy) > 1e-4 ? hh / Math.abs(dy) : 1e9;
        t = Math.min(tx_b, ty_b);
      }}
      return [node.cx + dx * t, node.cy + dy * t];
    }}

    function makeEl(tag, attrs) {{
      const el = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, String(v)));
      return el;
    }}

    const animatedPaths = [];
    const revealGroups = [];
    const edgePackets = [];
    const labelGroups = [];

    // Canvas text measurer so every SVG box & edge pill auto-fits wrapped text with zero overflow
    const _mCanvas = document.createElement('canvas');
    const _mCtx = _mCanvas.getContext('2d');
    function measureTextPx(txt, fontSpec) {{
      _mCtx.font = fontSpec;
      return _mCtx.measureText(String(txt || '')).width;
    }}
    function wrapTextLines(rawText, maxLineW, fontSpec, maxLines = 2) {{
      const words = String(rawText || '').trim().split(/\s+/).filter(Boolean);
      if (!words.length) return [''];
      const lines = [];
      let cur = words[0];
      for (let i = 1; i < words.length; i++) {{
        const cand = cur + ' ' + words[i];
        if (measureTextPx(cand, fontSpec) <= maxLineW) {{
          cur = cand;
        }} else {{
          lines.push(cur);
          cur = words[i];
          if (lines.length >= maxLines - 1) {{
            const rest = [cur, ...words.slice(i + 1)].join(' ');
            // Fit remaining text cleanly inside maxLineW if needed
            let trimmed = rest;
            while (trimmed.length > 6 && measureTextPx(trimmed, fontSpec) > maxLineW) {{
              trimmed = trimmed.slice(0, -4) + '...';
            }}
            lines.push(trimmed);
            return lines.slice(0, maxLines);
          }}
        }}
      }}
      lines.push(cur);
      return lines.slice(0, maxLines);
    }}

    // 1. Build measured, wrapped node geometry (zero text overflow outside boxes/cylinders/diamonds)
    const rawNodes = STATE.nodes || [];
    const isPortrait = VBW < VBH;
    const stickyReserve = STATE.has_sticky ? (isPortrait ? 235 : 150) : 54;
    const usableTop = 64;
    const usableBot = VBH - stickyReserve;
    const maxNodeTextW = isPortrait ? 310 : 250;
    const nodeEntries = rawNodes.map((n, idx) => {{
      const kind = String(n.kind || 'box').toLowerCase();
      const lblFont = '900 28px "Nirmala UI", "Segoe UI", sans-serif';
      const subFont = '800 20px "Cascadia Code", monospace';
      const lblLines = wrapTextLines(n.label || 'Node', maxNodeTextW, lblFont, 2);
      const subLines = n.sublabel ? wrapTextLines(n.sublabel, maxNodeTextW, subFont, 2) : [];
      const lblMaxW = Math.max(...lblLines.map(l => measureTextPx(l, lblFont)), 90);
      const subMaxW = subLines.length ? Math.max(...subLines.map(l => measureTextPx(l, subFont)), 60) : 0;
      const contentW = Math.max(lblMaxW, subMaxW);
      const contentH = lblLines.length * 34 + (subLines.length ? 10 + subLines.length * 26 : 0);

      let boxW = Math.max(245, Math.min(isPortrait ? 430 : 340, contentW + 64));
      let boxH = Math.max(118, contentH + (kind === 'cylinder' ? 76 : 50));
      if (kind === 'diamond') {{
        // Diamond inner safe zone requires wider/taller vertices so text stays cleanly inside diagonals
        boxW = Math.max(boxW + 76, contentW * 1.48 + 68);
        boxH = Math.max(boxH + 46, contentH * 1.55 + 56);
      }}
      return {{
        cx: mapX(n.x),
        cy: mapY(n.y),
        w: Math.round(boxW),
        h: Math.round(boxH),
        lblLines,
        subLines,
        data: n,
        dp: Number(n.dp !== undefined ? n.dp : 0.05 + idx * 0.10),
      }};
    }});

    // 2. Smart Portrait Re-flow & AABB Collision Solver (keeps generous space for arrows & edge pills)
    if (isPortrait && nodeEntries.length >= 2 && nodeEntries.length <= 4) {{
      const ys = nodeEntries.map(nd => nd.cy);
      const ySpan = Math.max(...ys) - Math.min(...ys);
      // If nodes are bunched horizontally in a narrow horizontal band, spread cleanly across portrait height
      if (ySpan < 190) {{
        const usableH = usableBot - usableTop;
        nodeEntries.forEach((nd, i) => {{
          const frac = (i + 0.5) / nodeEntries.length;
          nd.cy = usableTop + frac * usableH;
          if (nodeEntries.length === 2) {{
            nd.cx = VBW * (i === 0 ? 0.36 : 0.64);
          }} else {{
            nd.cx = VBW * (i % 2 === 0 ? 0.32 : 0.68);
          }}
        }});
      }}
    }}

    for (let iter = 0; iter < 24; iter++) {{
      for (let i = 0; i < nodeEntries.length; i++) {{
        for (let j = i + 1; j < nodeEntries.length; j++) {{
          const a = nodeEntries[i], b = nodeEntries[j];
          const minDx = (a.w + b.w) * 0.5 + 96;
          const minDy = (a.h + b.h) * 0.5 + 108;
          const dx = b.cx - a.cx;
          const dy = b.cy - a.cy;
          if (Math.abs(dx) < minDx && Math.abs(dy) < minDy) {{
            const penX = minDx - Math.abs(dx);
            const penY = minDy - Math.abs(dy);
            if (penY <= penX || isPortrait) {{
              const s = (dy >= 0 ? 1 : -1) || 1;
              a.cy -= s * penY * 0.45;
              b.cy += s * penY * 0.45;
            }} else {{
              const s = (dx >= 0 ? 1 : -1) || 1;
              a.cx -= s * penX * 0.45;
              b.cx += s * penX * 0.45;
            }}
          }}
        }}
      }}
      nodeEntries.forEach(nd => {{
        const padX = nd.w * 0.5 + 34;
        const padY = nd.h * 0.5 + 24;
        nd.cx = Math.max(padX, Math.min(VBW - padX, nd.cx));
        nd.cy = Math.max(usableTop + padY, Math.min(usableBot - padY, nd.cy));
      }});
    }}

    const nodeMap = {{}};
    nodeEntries.forEach((nd, idx) => {{
      nodeMap[String(nd.data.id || idx)] = nd;
    }});

    // 3. Hand-drawn boundary-clipped curved edges + measured edge pills (never collide with boxes)
    (STATE.edges || []).forEach((e, idx) => {{
      const a = nodeMap[String(e.from)], b = nodeMap[String(e.to)];
      if (!a || !b) return;
      const col = PAL[e.color] || '#38BDF8';
      const dp = Number(e.dp !== undefined ? e.dp : 0.16 + idx * 0.10);
      const [x1, y1] = boundaryPoint(a, b.cx, b.cy, 8);
      const [x2, y2] = boundaryPoint(b, a.cx, a.cy, 12);
      const dx = x2 - x1, dy = y2 - y1;
      const dist = Math.hypot(dx, dy) || 1;
      const ux = dx / dist, uy = dy / dist;
      const bend = dist < 160 ? 58 : (dist > 220 ? 32 : 40);
      const mx = (x1 + x2) * 0.5 - uy * bend;
      const my = (y1 + y2) * 0.5 + ux * bend;
      const d = `M ${{x1.toFixed(1)}} ${{y1.toFixed(1)}} Q ${{mx.toFixed(1)}} ${{my.toFixed(1)}} ${{x2.toFixed(1)}} ${{y2.toFixed(1)}}`;

      const pEl = makeEl('path', {{
        d, fill: 'none', stroke: col, 'stroke-width': 5.0, 'stroke-linecap': 'round'
      }});
      if (e.dashed) pEl.setAttribute('stroke-dasharray', '14 10');
      svg.appendChild(pEl);
      const len = pEl.getTotalLength ? pEl.getTotalLength() : 260;
      if (!e.dashed) {{
        pEl.style.strokeDasharray = String(len);
        pEl.style.strokeDashoffset = String(len);
        animatedPaths.push({{ el: pEl, len, dp }});
      }} else {{
        pEl.style.opacity = '0';
        revealGroups.push({{ el: pEl, dp }});
      }}

      const ang = Math.atan2(y2 - my, x2 - mx);
      const ah = 20;
      const ax1 = x2 - ah * Math.cos(ang - 0.45), ay1 = y2 - ah * Math.sin(ang - 0.45);
      const ax2 = x2 - ah * Math.cos(ang + 0.45), ay2 = y2 - ah * Math.sin(ang + 0.45);
      const head = makeEl('path', {{
        d: `M ${{ax1.toFixed(1)}} ${{ay1.toFixed(1)}} L ${{x2.toFixed(1)}} ${{y2.toFixed(1)}} L ${{ax2.toFixed(1)}} ${{ay2.toFixed(1)}}`,
        fill: 'none', stroke: col, 'stroke-width': 4.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
      }});
      svg.appendChild(head);
      revealGroups.push({{ el: head, dp: dp + 0.06 }});

      const pkt = makeEl('circle', {{ r: 7, fill: col, stroke: '#FFFFFF', 'stroke-width': 2, opacity: 0 }});
      svg.appendChild(pkt);
      edgePackets.push({{ el: pkt, x1, y1, mx, my, x2, y2, dp: dp + 0.06 }});

      if (e.label) {{
        const tg = makeEl('g', {{ opacity: 0 }});
        let lblTxt = String(e.label).trim();
        const eFont = '900 20px "Cascadia Code", monospace';
        while (lblTxt.length > 8 && measureTextPx(lblTxt, eFont) > 220) {{
          lblTxt = lblTxt.slice(0, -4) + '...';
        }}
        const tw = Math.max(104, measureTextPx(lblTxt, eFont) + 34);
        let lx = 0.25 * x1 + 0.5 * mx + 0.25 * x2;
        let ly = 0.25 * y1 + 0.5 * my + 0.25 * y2;
        lx = Math.max(tw * 0.5 + 16, Math.min(VBW - tw * 0.5 - 16, lx));
        ly = Math.max(usableTop + 24, Math.min(usableBot - 24, ly));
        tg.appendChild(makeEl('rect', {{
          x: lx - tw / 2, y: ly - 20, width: tw, height: 40, rx: 12,
          fill: '#071124', stroke: col, 'stroke-width': 2.4
        }}));
        const txt = makeEl('text', {{
          x: lx, y: ly + 7, 'text-anchor': 'middle', fill: '#FFFFFF',
          'font-size': 20, 'font-weight': '900', 'font-family': 'Cascadia Code, monospace'
        }});
        txt.textContent = lblTxt;
        tg.appendChild(txt);
        labelGroups.push({{ el: tg, dp: dp + 0.04 }});
      }}
    }});

    // 4. Hand-drawn high-contrast diagram nodes with wrapped multi-line labels inside exact bounds
    Object.values(nodeMap).forEach((nd, idx) => {{
      const n = nd.data;
      const col = PAL[n.color] || '#38BDF8';
      const kind = String(n.kind || 'box').toLowerCase();
      const x = nd.cx - nd.w * 0.5, y = nd.cy - nd.h * 0.5, w = nd.w, h = nd.h;
      const g = makeEl('g', {{ opacity: 0 }});

      if (kind === 'cylinder') {{
        g.appendChild(makeEl('path', {{
          d: `M ${{x}} ${{y + 22}} v ${{h - 44}} c 0 24 ${{w}} 24 ${{w}} 0 v -${{h - 44}} z`,
          fill: '#0C1A36', stroke: col, 'stroke-width': 4.4
        }}));
        g.appendChild(makeEl('path', {{
          d: `M ${{x}} ${{y + 22}} v ${{h - 44}} c 0 24 ${{w}} 24 ${{w}} 0 v -${{h - 44}} z`,
          fill: col + '24', stroke: 'none'
        }}));
        g.appendChild(makeEl('ellipse', {{
          cx: nd.cx, cy: y + 22, rx: w * 0.5, ry: 22,
          fill: '#112447', stroke: col, 'stroke-width': 4.4
        }}));
        g.appendChild(makeEl('path', {{
          d: `M ${{x}} ${{y + 36}} c 0 16 ${{w}} 16 ${{w}} 0`,
          fill: 'none', stroke: col + '66', 'stroke-width': 2.0, 'stroke-dasharray': '8 6'
        }}));
      }} else if (kind === 'diamond') {{
        const pts = `${{nd.cx}},${{nd.cy - h * 0.5}} ${{nd.cx + w * 0.5}},${{nd.cy}} ${{nd.cx}},${{nd.cy + h * 0.5}} ${{nd.cx - w * 0.5}},${{nd.cy}}`;
        g.appendChild(makeEl('polygon', {{
          points: pts, fill: '#0C1A36', stroke: col, 'stroke-width': 4.5, 'stroke-linejoin': 'round'
        }}));
        g.appendChild(makeEl('polygon', {{
          points: pts, fill: col + '26', stroke: 'none'
        }}));
      }} else {{
        g.appendChild(makeEl('rect', {{
          x, y, width: w, height: h, rx: kind === 'queue' ? 32 : 18,
          fill: '#0C1A36'
        }}));
        g.appendChild(makeEl('rect', {{
          x, y, width: w, height: h, rx: kind === 'queue' ? 32 : 18,
          fill: col + '24'
        }}));
        const [d1, d2] = sketchRectPaths(x, y, w, h, (idx + 1) * 37, STATE.wobble || 2.4);
        g.appendChild(makeEl('path', {{ d: d1, fill: 'none', stroke: col, 'stroke-width': 4.5, 'stroke-linecap': 'round' }}));
        g.appendChild(makeEl('path', {{ d: d2, fill: 'none', stroke: col + 'AA', 'stroke-width': 2.3, 'stroke-linecap': 'round' }}));
      }}

      const lblCount = nd.lblLines.length;
      const subCount = nd.subLines.length;
      const totalBlockH = lblCount * 34 + (subCount ? 8 + subCount * 26 : 0);
      const yOffset = kind === 'cylinder' ? 18 : 0;
      let curY = nd.cy + yOffset - totalBlockH * 0.5 + 24;

      nd.lblLines.forEach(line => {{
        const lbl = makeEl('text', {{
          x: nd.cx, y: curY, 'text-anchor': 'middle',
          fill: '#FFFFFF', 'font-size': 28, 'font-weight': '900',
          'font-family': 'Nirmala UI, Segoe UI, sans-serif'
        }});
        lbl.textContent = line;
        g.appendChild(lbl);
        curY += 34;
      }});

      if (subCount) {{
        curY += 4;
        nd.subLines.forEach(line => {{
          const sub = makeEl('text', {{
            x: nd.cx, y: curY, 'text-anchor': 'middle',
            fill: col, 'font-size': 20, 'font-weight': '800', 'font-family': 'Cascadia Code, monospace'
          }});
          sub.textContent = line;
          g.appendChild(sub);
          curY += 26;
        }});
      }}

      svg.appendChild(g);
      revealGroups.push({{ el: g, dp: nd.dp }});
    }});

    // Append edge label pills on top of nodes so labels are never occluded
    labelGroups.forEach(lg => {{
      svg.appendChild(lg.el);
      revealGroups.push(lg);
    }});

    // 5. Aligned High-Contrast Sticky Callout Bubbles inside bottom dock
    const stickyEls = [];
    (STATE.stickies || []).forEach((st, idx) => {{
      const col = PAL[st.color] || '#FBBF24';
      const rot = (STATE.stickies || []).length === 1 ? 0 : (idx % 2 === 0 ? -0.8 : 0.8);
      const dp = Number(st.dp !== undefined ? st.dp : 0.24 + idx * 0.16);
      const card = document.createElement('div');
      card.className = 'sticky-note';
      card.style.borderColor = col;
      card.style.boxShadow = `0 16px 38px rgba(0,0,0,0.72), 0 0 22px ${{col}}2E`;
      card.style.transform = `rotate(${{rot}}deg) scale(0.94)`;
      card.innerHTML = `<div class="sticky-tape" style="background:${{col}}CC"></div>` +
        `<div class="sticky-title" style="color:${{col}}">${{String(st.title || 'NOTE').replace(/</g,'&lt;')}}</div>` +
        `<div class="sticky-txt">${{String(st.text || '').replace(/</g,'&lt;')}}</div>`;
      stickyLayer.appendChild(card);
      stickyEls.push({{ el: card, dp, rot }});
    }});

    window.__setStudioProgress = function(wp, lp) {{
      const p = Math.max(0, Math.min(1, Number(wp) || 0));
      const t = Math.max(0, Math.min(1, Number(lp !== undefined ? lp : p) || 0));
      const spd = Number(STATE.draw_speed || 1.15);

      revealGroups.forEach(item => {{
        const f = Math.max(0, Math.min(1, (p - item.dp + 0.08) / 0.12));
        item.el.setAttribute('opacity', f.toFixed(3));
        item.el.style.opacity = f.toFixed(3);
      }});

      animatedPaths.forEach(ap => {{
        const local = Math.max(0, Math.min(1, ((t - ap.dp + 0.06) * spd) / 0.22));
        ap.el.style.strokeDashoffset = (ap.len * (1 - local)).toFixed(1);
      }});

      edgePackets.forEach(pk => {{
        if (t < pk.dp) {{ pk.el.setAttribute('opacity', '0'); return; }}
        const u = ((t - pk.dp) * 1.9) % 1.0;
        const imu = 1 - u;
        const bx = imu * imu * pk.x1 + 2 * imu * u * pk.mx + u * u * pk.x2;
        const by = imu * imu * pk.y1 + 2 * imu * u * pk.my + u * u * pk.y2;
        pk.el.setAttribute('cx', bx.toFixed(1));
        pk.el.setAttribute('cy', by.toFixed(1));
        pk.el.setAttribute('opacity', '0.95');
      }});

      stickyEls.forEach(s => {{
        const f = Math.max(0, Math.min(1, (p - s.dp + 0.08) / 0.12));
        s.el.style.opacity = f.toFixed(3);
        s.el.style.transform = `rotate(${{s.rot}}deg) scale(${{(0.92 + 0.08 * f).toFixed(3)}}) translateY(${{(10 * (1 - f)).toFixed(1)}}px)`;
      }});

      const fp = document.getElementById('footerPill');
      if (fp) {{
        const ff = Math.max(0, Math.min(1, (p - 0.58) / 0.14));
        fp.style.opacity = ff.toFixed(3);
      }}
    }};
    window.__setStudioProgress(1.0, 1.0);
  </script>
</body>
</html>"""


def render_v4_whiteboard_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
) -> Path:
    """Renders all FPS frames for a Studio V4 Blueprint Whiteboard Studio scene."""
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

    html_doc = _build_whiteboard_html(scene, w, h, tone=tone)
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
            word_blend = compute_synced_visual_progress(lin_p, cur_t, words, tone=tone)
            page.evaluate(
                "(args) => { if (window.__setStudioProgress) window.__setStudioProgress(args.wp, args.lp); }",
                {"wp": round(word_blend, 4), "lp": round(lin_p, 4)},
            )
            page.screenshot(path=str(out_dir / f"frame_{f:04d}.jpg"), type="jpeg", quality=90)

        browser.close()
        p.stop()
        return out_dir

    # Graceful headless Pillow fallback
    from PIL import Image, ImageDraw
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (8, 18, 38))
    draw = ImageDraw.Draw(img)
    draw.rectangle([48, 220, w - 48, h - 220], outline=(56, 189, 248), width=3)
    draw.text((76, 110), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(248, 250, 252))
    for i, nd in enumerate(list(vd.get("diagram_nodes") or [])[:6]):
        draw.text((90, 280 + i * 56), f"[{nd.get('label', 'Node')}] - {nd.get('sublabel', '')}", fill=(56, 189, 248))
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir
