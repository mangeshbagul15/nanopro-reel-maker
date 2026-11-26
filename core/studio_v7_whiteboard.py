"""
Studio V7 — Blueprint Whiteboard Studio Renderer (ByteByteGo / Excalidraw Style).
Renders crisp hand-drawn marker diagrams on a dark engineering blueprint grid via Playwright Chromium:
  - Engineering dark blueprint grid background (minor + major lines + crosshairs)
  - Hand-drawn sketchy marker SVG primitives (double-pass wobble strokes + soft marker wash)
  - Progressive draw-on arrows (`stroke-dashoffset`) + traveling marker data dots
  - Tilted sticky callout bubbles / post-it annotations anchored cleanly around nodes
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
        return {"draw_speed": 1.35, "wobble": 2.1, "tone_accent": accent}
    if t_key in ("war_story_postmortem", "dramatic_performance"):
        return {"draw_speed": 1.0, "wobble": 2.8, "tone_accent": "rose"}
    return {"draw_speed": 1.1, "wobble": 2.3, "tone_accent": accent}


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
    stickies = list(vd.get("sticky_notes") or [])[:4]
    zones = list(vd.get("blueprint_zones") or [])[:3]
    footer_note = html.escape(str(vd.get("footer_pill") or ""))

    is_wide = width > height
    sc = min(width, height) / 1080.0
    pad_x = int((44 if not is_wide else 90) * sc)
    hl_px = int((56 if not is_wide else 42) * sc)

    wb_state = {
        "nodes": nodes,
        "edges": edges,
        "stickies": stickies,
        "zones": zones,
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
    background: radial-gradient(circle at 50% 20%, #102446 0%, #081226 56%, #040914 100%);
    color: #F8FAFC;
    font-family: "Segoe Print", "Comic Sans MS", "Nirmala UI", "Segoe UI", system-ui, sans-serif;
  }}
  .bp-grid {{
    position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(56,189,248,0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,189,248,0.08) 1px, transparent 1px),
      linear-gradient(rgba(56,189,248,0.18) 1.4px, transparent 1.4px),
      linear-gradient(90deg, rgba(56,189,248,0.18) 1.4px, transparent 1.4px);
    background-size: 28px 28px, 28px 28px, 140px 140px, 140px 140px;
  }}
  .root {{
    position: relative; width: 100%; height: 100%; z-index: 2;
    display: flex; flex-direction: column;
    padding: {int(36*sc)}px {pad_x}px {int(46*sc)}px;
    gap: {int(14*sc)}px;
  }}
  .top-row {{ display: flex; align-items: center; justify-content: space-between; font-family: "Nirmala UI", "Segoe UI", system-ui, sans-serif; }}
  .wm-pill {{
    padding: {int(7*sc)}px {int(18*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.86); border: 1.5px solid rgba(148,163,184,0.32);
    font-size: {int(22*sc)}px; font-weight: 800; color: #F8FAFC;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .hud-pill {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: {int(7*sc)}px {int(18*sc)}px; border-radius: 999px;
    background: rgba(9,20,42,0.85); border: 1.6px dashed {accent_hex}AA;
    color: {accent_hex}; font-size: {int(19*sc)}px; font-weight: 800; letter-spacing: 2px;
  }}
  .headline {{
    text-align: center; line-height: 1.15;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
    font-size: {hl_px}px; font-weight: 900; margin: {int(4*sc)}px 0;
  }}
  .headline .acc {{
    color: {accent_hex}; display: inline-block; position: relative;
    padding-bottom: {int(6*sc)}px;
    border-bottom: 4px dashed {accent_hex}AA;
  }}

  /* Whiteboard Sketch Stage */
  .board-stage {{
    flex: 1; position: relative; border-radius: {int(24*sc)}px;
    border: 2px dashed rgba(56,189,248,0.34);
    background: rgba(6, 15, 34, 0.56);
    box-shadow: inset 0 0 60px rgba(8,20,48,0.72), 0 22px 60px rgba(0,0,0,0.55);
    overflow: hidden;
  }}
  .bp-corner {{
    position: absolute; font-family: "Cascadia Code", monospace;
    font-size: {int(15*sc)}px; color: rgba(56,189,248,0.45); letter-spacing: 1.5px;
  }}
  svg#wbSvg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}

  /* Sticky Callout Bubbles */
  .sticky-note {{
    position: absolute; z-index: 8; max-width: {int(285*sc)}px;
    padding: {int(14*sc)}px {int(18*sc)}px; border-radius: 14px;
    background: rgba(254, 240, 138, 0.14); border: 2.2px solid #FACC15;
    box-shadow: 0 12px 28px rgba(0,0,0,0.48);
    backdrop-filter: blur(6px);
  }}
  .sticky-tape {{
    width: {int(54*sc)}px; height: {int(11*sc)}px; border-radius: 4px;
    background: rgba(250,204,21,0.55); margin: -{int(20*sc)}px auto {int(6*sc)}px;
  }}
  .sticky-title {{
    font-family: "Nirmala UI", "Segoe UI", system-ui, sans-serif;
    font-size: {int(17*sc)}px; font-weight: 900; letter-spacing: 1px; margin-bottom: 4px;
  }}
  .sticky-txt {{
    font-size: {int(21*sc)}px; font-weight: 700; color: #F8FAFC; line-height: 1.28;
  }}

  .footer-pill {{
    align-self: center; font-family: "Nirmala UI", "Segoe UI", system-ui, sans-serif;
    padding: {int(10*sc)}px {int(28*sc)}px; border-radius: 14px;
    background: rgba(56,189,248,0.12); border: 2px dashed {accent_hex};
    color: #F8FAFC; font-size: {int(22*sc)}px; font-weight: 800; text-align: center;
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
      <div class="bp-corner" style="top:12px;left:16px">GRID 28px // REV-7</div>
      <div class="bp-corner" style="bottom:12px;right:16px">BLUEPRINT STUDIO V7</div>
      <svg id="wbSvg" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet"></svg>
      <div id="stickyLayer"></div>
    </div>

    {f'<div class="footer-pill" id="footerPill">{footer_note}</div>' if footer_note else ''}
  </div>

  <script>
    const STATE = {json.dumps(wb_state, ensure_ascii=False)};
    const PAL = {{
      cyan: '#38BDF8', emerald: '#34D399', amber: '#FBBF24',
      rose: '#F43F5E', purple: '#C084FC', blue: '#60A5FA', white: '#F8FAFC'
    }};
    const svg = document.getElementById('wbSvg');
    const stickyLayer = document.getElementById('stickyLayer');
    const NS = 'http://www.w3.org/2000/svg';

    function prng(seed) {{
      let s = (seed * 9301 + 49297) % 233280;
      return () => {{ s = (s * 9301 + 49297) % 233280; return (s / 233280) - 0.5; }};
    }}

    function sketchLinePath(x1, y1, x2, y2, seed, wob) {{
      const r = prng(seed);
      const mx = (x1 + x2) / 2 + r() * wob * 3;
      const my = (y1 + y2) / 2 + r() * wob * 3;
      return `M ${{x1.toFixed(1)}} ${{y1.toFixed(1)}} Q ${{mx.toFixed(1)}} ${{my.toFixed(1)}} ${{x2.toFixed(1)}} ${{y2.toFixed(1)}}`;
    }}

    function sketchRectPaths(x, y, w, h, seed, wob) {{
      const r = prng(seed);
      const j = () => r() * wob * 2.2;
      const d1 = [
        sketchLinePath(x + j(), y + j(), x + w + j(), y + j(), seed + 1, wob),
        sketchLinePath(x + w + j(), y + j(), x + w + j(), y + h + j(), seed + 2, wob),
        sketchLinePath(x + w + j(), y + h + j(), x + j(), y + h + j(), seed + 3, wob),
        sketchLinePath(x + j(), y + h + j(), x + j(), y + j(), seed + 4, wob),
      ].join(' ');
      const d2 = [
        sketchLinePath(x + 2 + j(), y - 1 + j(), x + w - 1 + j(), y + 2 + j(), seed + 11, wob * 0.8),
        sketchLinePath(x + w + 1 + j(), y + 2 + j(), x + w - 2 + j(), y + h + j(), seed + 12, wob * 0.8),
        sketchLinePath(x + w + j(), y + h + 2 + j(), x + 2 + j(), y + h - 1 + j(), seed + 13, wob * 0.8),
        sketchLinePath(x - 1 + j(), y + h + j(), x + 1 + j(), y + 1 + j(), seed + 14, wob * 0.8),
      ].join(' ');
      return [d1, d2];
    }}

    function makeEl(tag, attrs) {{
      const el = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, String(v)));
      return el;
    }}

    const animatedPaths = [];
    const revealGroups = [];

    // 1. Zones (hand-drawn dashed bounding areas)
    (STATE.zones || []).forEach((z, idx) => {{
      const col = PAL[z.color] || '#38BDF8';
      const x = Number(z.x || 80), y = Number(z.y || 80), w = Number(z.w || 380), h = Number(z.h || 260);
      const dp = Number(z.dp !== undefined ? z.dp : 0.04 + idx * 0.12);
      const g = makeEl('g', {{ opacity: 0 }});
      const rect = makeEl('rect', {{
        x, y, width: w, height: h, rx: 18,
        fill: col + '10', stroke: col, 'stroke-width': 2.5, 'stroke-dasharray': '12 9'
      }});
      const lbl = makeEl('text', {{
        x: x + 16, y: y + 28, fill: col, 'font-size': 20, 'font-weight': '900',
        'font-family': 'Cascadia Code, monospace'
      }});
      lbl.textContent = String(z.label || 'ZONE').toUpperCase();
      g.appendChild(rect);
      g.appendChild(lbl);
      svg.appendChild(g);
      revealGroups.push({{ el: g, dp }});
    }});

    // 2. Build node lookup + draw hand-drawn edges
    const nodeMap = {{}};
    (STATE.nodes || []).forEach((n, idx) => {{
      nodeMap[String(n.id || idx)] = {{
        cx: Number(n.x || 500),
        cy: Number(n.y || 500),
        w: Number(n.w || 235),
        h: Number(n.h || 112),
        data: n,
        dp: Number(n.dp !== undefined ? n.dp : 0.06 + idx * 0.11),
      }};
    }});

    (STATE.edges || []).forEach((e, idx) => {{
      const a = nodeMap[String(e.from)], b = nodeMap[String(e.to)];
      if (!a || !b) return;
      const col = PAL[e.color] || '#38BDF8';
      const dp = Number(e.dp !== undefined ? e.dp : 0.22 + idx * 0.10);
      const dx = b.cx - a.cx, dy = b.cy - a.cy;
      const dist = Math.hypot(dx, dy) || 1;
      const ux = dx / dist, uy = dy / dist;
      const x1 = a.cx + ux * (a.w * 0.48);
      const y1 = a.cy + uy * (a.h * 0.48);
      const x2 = b.cx - ux * (b.w * 0.52);
      const y2 = b.cy - uy * (b.h * 0.52);
      const mx = (x1 + x2) * 0.5 - uy * 28;
      const my = (y1 + y2) * 0.5 + ux * 28;
      const d = `M ${{x1.toFixed(1)}} ${{y1.toFixed(1)}} Q ${{mx.toFixed(1)}} ${{my.toFixed(1)}} ${{x2.toFixed(1)}} ${{y2.toFixed(1)}}`;

      const pEl = makeEl('path', {{
        d, fill: 'none', stroke: col, 'stroke-width': 4.5, 'stroke-linecap': 'round'
      }});
      if (e.dashed) pEl.setAttribute('stroke-dasharray', '12 9');
      svg.appendChild(pEl);
      const len = pEl.getTotalLength ? pEl.getTotalLength() : 240;
      if (!e.dashed) {{
        pEl.style.strokeDasharray = String(len);
        pEl.style.strokeDashoffset = String(len);
        animatedPaths.push({{ el: pEl, len, dp }});
      }} else {{
        pEl.style.opacity = '0';
        revealGroups.push({{ el: pEl, dp }});
      }}

      // Sketchy Arrowhead
      const ang = Math.atan2(y2 - my, x2 - mx);
      const ah = 18;
      const ax1 = x2 - ah * Math.cos(ang - 0.45), ay1 = y2 - ah * Math.sin(ang - 0.45);
      const ax2 = x2 - ah * Math.cos(ang + 0.45), ay2 = y2 - ah * Math.sin(ang + 0.45);
      const head = makeEl('path', {{
        d: `M ${{ax1.toFixed(1)}} ${{ay1.toFixed(1)}} L ${{x2.toFixed(1)}} ${{y2.toFixed(1)}} L ${{ax2.toFixed(1)}} ${{ay2.toFixed(1)}}`,
        fill: 'none', stroke: col, 'stroke-width': 4.2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
      }});
      svg.appendChild(head);
      revealGroups.push({{ el: head, dp: dp + 0.08 }});

      if (e.label) {{
        const tg = makeEl('g', {{ opacity: 0 }});
        const tw = Math.max(96, String(e.label).length * 12 + 24);
        const pill = makeEl('rect', {{
          x: mx - tw / 2, y: my - 18, width: tw, height: 34, rx: 10,
          fill: '#0A152C', stroke: col, 'stroke-width': 2
        }});
        const txt = makeEl('text', {{
          x: mx, y: my + 5, 'text-anchor': 'middle', fill: col,
          'font-size': 18, 'font-weight': '800', 'font-family': 'Cascadia Code, monospace'
        }});
        txt.textContent = String(e.label);
        tg.appendChild(pill);
        tg.appendChild(txt);
        svg.appendChild(tg);
        revealGroups.push({{ el: tg, dp: dp + 0.06 }});
      }}
    }});

    // 3. Draw hand-drawn whiteboard nodes
    Object.values(nodeMap).forEach((nd, idx) => {{
      const n = nd.data;
      const col = PAL[n.color] || '#38BDF8';
      const kind = String(n.kind || 'box').toLowerCase();
      const x = nd.cx - nd.w * 0.5, y = nd.cy - nd.h * 0.5, w = nd.w, h = nd.h;
      const g = makeEl('g', {{ opacity: 0 }});

      // Marker wash background
      if (kind === 'cylinder') {{
        const body = makeEl('path', {{
          d: `M ${{x}} ${{y + 18}} v ${{h - 36}} c 0 22 ${{w}} 22 ${{w}} 0 v -${{h - 36}} z`,
          fill: col + '1F', stroke: col, 'stroke-width': 3.8
        }});
        const top = makeEl('ellipse', {{
          cx: nd.cx, cy: y + 18, rx: w * 0.5, ry: 18,
          fill: '#0D1B35', stroke: col, 'stroke-width': 3.8
        }});
        const ring = makeEl('path', {{
          d: `M ${{x}} ${{y + 42}} c 0 18 ${{w}} 18 ${{w}} 0`,
          fill: 'none', stroke: col + '88', 'stroke-width': 2.2, 'stroke-dasharray': '7 6'
        }});
        g.appendChild(body);
        g.appendChild(top);
        g.appendChild(ring);
      }} else if (kind === 'diamond') {{
        const pts = `${{nd.cx}},${{y}} ${{x + w}},${{nd.cy}} ${{nd.cx}},${{y + h}} ${{x}},${{nd.cy}}`;
        g.appendChild(makeEl('polygon', {{
          points: pts, fill: col + '1F', stroke: col, 'stroke-width': 3.8, 'stroke-linejoin': 'round'
        }}));
      }} else {{
        g.appendChild(makeEl('rect', {{
          x, y, width: w, height: h, rx: kind === 'queue' ? 28 : 16,
          fill: col + '1A'
        }}));
        const [d1, d2] = sketchRectPaths(x, y, w, h, (idx + 1) * 37, STATE.wobble || 2.2);
        const p1 = makeEl('path', {{ d: d1, fill: 'none', stroke: col, 'stroke-width': 3.8, 'stroke-linecap': 'round' }});
        const p2 = makeEl('path', {{ d: d2, fill: 'none', stroke: col + '99', 'stroke-width': 2.1, 'stroke-linecap': 'round' }});
        g.appendChild(p1);
        g.appendChild(p2);
      }}

      const lbl = makeEl('text', {{
        x: nd.cx, y: nd.cy - (n.sublabel ? 4 : -7), 'text-anchor': 'middle',
        fill: '#F8FAFC', 'font-size': 25, 'font-weight': '900'
      }});
      lbl.textContent = String(n.label || 'Node');
      g.appendChild(lbl);

      if (n.sublabel) {{
        const sub = makeEl('text', {{
          x: nd.cx, y: nd.cy + 26, 'text-anchor': 'middle',
          fill: col, 'font-size': 18, 'font-weight': '800', 'font-family': 'Cascadia Code, monospace'
        }});
        sub.textContent = String(n.sublabel);
        g.appendChild(sub);
      }}

      svg.appendChild(g);
      revealGroups.push({{ el: g, dp: nd.dp }});
    }});

    // 4. Sticky Callout Bubbles
    const stickyEls = [];
    (STATE.stickies || []).forEach((st, idx) => {{
      const col = PAL[st.color] || '#FBBF24';
      const xp = Math.max(4, Math.min(72, Number(st.x_pct !== undefined ? st.x_pct : (idx % 2 === 0 ? 6 : 64))));
      const yp = Math.max(4, Math.min(78, Number(st.y_pct !== undefined ? st.y_pct : (10 + idx * 36))));
      const rot = idx % 2 === 0 ? -2.2 : 2.0;
      const dp = Number(st.dp !== undefined ? st.dp : 0.28 + idx * 0.20);
      const card = document.createElement('div');
      card.className = 'sticky-note';
      card.style.left = xp + '%';
      card.style.top = yp + '%';
      card.style.borderColor = col;
      card.style.background = col + '22';
      card.style.transform = `rotate(${{rot}}deg) scale(0.92)`;
      card.innerHTML = `<div class="sticky-tape" style="background:${{col}}99"></div>` +
        `<div class="sticky-title" style="color:${{col}}">${{String(st.title || 'NOTE').replace(/</g,'&lt;')}}</div>` +
        `<div class="sticky-txt">${{String(st.text || '').replace(/</g,'&lt;')}}</div>`;
      stickyLayer.appendChild(card);
      stickyEls.push({{ el: card, dp, rot }});
    }});

    window.__setStudioProgress = function(wp, lp) {{
      const p = Math.max(0, Math.min(1, Number(wp) || 0));
      const t = Math.max(0, Math.min(1, Number(lp !== undefined ? lp : p) || 0));
      const spd = Number(STATE.draw_speed || 1.1);

      revealGroups.forEach(item => {{
        const f = Math.max(0, Math.min(1, (p - item.dp + 0.06) / 0.12));
        item.el.setAttribute('opacity', f.toFixed(3));
        item.el.style.opacity = f.toFixed(3);
      }});

      animatedPaths.forEach(ap => {{
        const local = Math.max(0, Math.min(1, ((t - ap.dp + 0.05) * spd) / 0.22));
        ap.el.style.strokeDashoffset = (ap.len * (1 - local)).toFixed(1);
      }});

      stickyEls.forEach(s => {{
        const f = Math.max(0, Math.min(1, (p - s.dp + 0.06) / 0.12));
        s.el.style.opacity = f.toFixed(3);
        s.el.style.transform = `rotate(${{s.rot}}deg) scale(${{(0.88 + 0.12 * f).toFixed(3)}}) translateY(${{(12 * (1 - f)).toFixed(1)}}px)`;
      }});

      const fp = document.getElementById('footerPill');
      if (fp) {{
        const ff = Math.max(0, Math.min(1, (p - 0.70) / 0.15));
        fp.style.opacity = ff.toFixed(3);
      }}
    }};
    window.__setStudioProgress(1.0, 1.0);
  </script>
</body>
</html>"""


def render_v7_whiteboard_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
) -> Path:
    """Renders all FPS frames for a Studio V7 Blueprint Whiteboard Studio scene."""
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
            if words:
                spoken = sum(1 for wd in words if float(wd.get("start", 0.0)) <= cur_t)
                word_p = spoken / max(1, len(words))
                word_blend = min(1.0, 0.72 * word_p + 0.28 * lin_p)
            else:
                word_blend = lin_p
            if lin_p >= 0.94:
                word_blend = 1.0
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
