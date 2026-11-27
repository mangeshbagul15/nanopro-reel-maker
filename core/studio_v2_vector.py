"""
Studio V2 — Clean Vector Storyboard Renderer (GyanaHut Tech Style).
Renders crisp 100% vector SVG + HTML5 step-by-step animated scenes via Playwright Chromium
synced tightly to spoken Whisper word progress, with zero visual noise or overlapping clutter.
"""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS
from core.tone_engine import compute_synced_visual_progress

_ACCENT_HEX = {
    "cyan": "#22D3EE",
    "amber": "#FACC15",
    "emerald": "#34D399",
    "rose": "#F43F5E",
    "purple": "#A855F7",
    "blue": "#3B82F6",
}

_SVG_ICONS: Dict[str, str] = {
    "robot": '<rect x="6" y="8" width="20" height="15" rx="4" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="16" y1="3" x2="16" y2="8" stroke="currentColor" stroke-width="2.2"/><circle cx="16" cy="2.5" r="2" fill="#FACC15"/><circle cx="12" cy="14" r="2" fill="currentColor"/><circle cx="20" cy="14" r="2" fill="currentColor"/><line x1="12" y1="19" x2="20" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="13" x2="6" y2="13" stroke="currentColor" stroke-width="2"/><line x1="26" y1="13" x2="29" y2="13" stroke="currentColor" stroke-width="2"/>',
    "app": '<rect x="5" y="5" width="22" height="22" rx="5" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="5" y1="11" x2="27" y2="11" stroke="currentColor" stroke-width="2"/><circle cx="9" cy="8" r="1.2" fill="currentColor"/><circle cx="13" cy="8" r="1.2" fill="currentColor"/><path d="M11 19l3-3 3 3 4-4" stroke="currentColor" stroke-width="2.1" fill="none" stroke-linecap="round"/>',
    "server": '<rect x="5" y="5" width="22" height="9" rx="2.5" stroke="currentColor" stroke-width="2.1" fill="none"/><rect x="5" y="18" width="22" height="9" rx="2.5" stroke="currentColor" stroke-width="2.1" fill="none"/><circle cx="9.5" cy="9.5" r="1.4" fill="currentColor"/><circle cx="9.5" cy="22.5" r="1.4" fill="currentColor"/><line x1="14" y1="9.5" x2="23" y2="9.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="14" y1="22.5" x2="23" y2="22.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "file": '<path d="M8 4h10l6 6v18a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" stroke="currentColor" stroke-width="2.2" fill="none"/><path d="M18 4v6h6" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="10" y1="16" x2="20" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="10" y1="21" x2="18" y2="21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "db": '<ellipse cx="16" cy="8" rx="9.5" ry="3.8" stroke="currentColor" stroke-width="2.2" fill="none"/><path d="M6.5 8v16c0 2.1 4.2 3.8 9.5 3.8s9.5-1.7 9.5-3.8V8" stroke="currentColor" stroke-width="2.2" fill="none"/><path d="M6.5 16c0 2.1 4.2 3.8 9.5 3.8s9.5-1.7 9.5-3.8" stroke="currentColor" stroke-width="2.1" fill="none"/>',
    "git": '<circle cx="10" cy="8" r="3" stroke="currentColor" stroke-width="2.2" fill="none"/><circle cx="22" cy="14" r="3" stroke="currentColor" stroke-width="2.2" fill="none"/><circle cx="10" cy="24" r="3" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="10" y1="11" x2="10" y2="21" stroke="currentColor" stroke-width="2.2"/><path d="M10 21c0-5 12-2 12-4" stroke="currentColor" stroke-width="2.2" fill="none"/>',
    "plug": '<path d="M12 6v6M20 6v6M8 12h16v3a7 7 0 0 1-16 0v-3zM16 22v6" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
    "monitor": '<rect x="4" y="5" width="24" height="16" rx="2.5" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="16" y1="21" x2="16" y2="27" stroke="currentColor" stroke-width="2.2"/><line x1="10" y1="27" x2="22" y2="27" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
    "keyboard": '<rect x="3" y="9" width="26" height="14" rx="3" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="7" y1="14" x2="10" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="14" y1="14" x2="18" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="22" y1="14" x2="25" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="9" y1="19" x2="23" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "usb": '<rect x="11" y="4" width="10" height="7" rx="1" stroke="currentColor" stroke-width="2" fill="none"/><rect x="8" y="11" width="16" height="16" rx="3.5" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="14" y1="7.5" x2="18" y2="7.5" stroke="currentColor" stroke-width="2"/>',
    "phone": '<rect x="9" y="3" width="14" height="26" rx="3" stroke="currentColor" stroke-width="2.2" fill="none"/><line x1="14" y1="25" x2="18" y2="25" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "code": '<path d="M11 10l-6 6 6 6M21 10l6 6-6 6M18 8l-4 16" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "cloud": '<path d="M9 24h14a5 5 0 0 0 .8-9.94A7 7 0 0 0 10.2 12.2 4.8 4.8 0 0 0 9 24z" stroke="currentColor" stroke-width="2.2" fill="none"/>',
    "api": '<circle cx="16" cy="16" r="10" stroke="currentColor" stroke-width="2.1" fill="none"/><path d="M12 16h8M16 12v8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
    "shield": '<path d="M16 4l10 4v7c0 6.5-4.3 11.2-10 13-5.7-1.8-10-6.5-10-13V8l10-4z" stroke="currentColor" stroke-width="2.2" fill="none"/>',
    "brain": '<circle cx="16" cy="16" r="10" stroke="currentColor" stroke-width="2.2" fill="none"/><circle cx="12.5" cy="13.5" r="1.5" fill="currentColor"/><circle cx="19.5" cy="13.5" r="1.5" fill="currentColor"/><path d="M11.5 19.5c2 2 7 2 9 0" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>',
    "cpu": '<rect x="8" y="8" width="16" height="16" rx="2.5" stroke="currentColor" stroke-width="2.2" fill="none"/><rect x="12" y="12" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M12 4v4M20 4v4M12 24v4M20 24v4M4 12h4M4 20h4M24 12h4M24 20h4" stroke="currentColor" stroke-width="2"/>',
    "globe": '<circle cx="16" cy="16" r="11" stroke="currentColor" stroke-width="2.1" fill="none"/><ellipse cx="16" cy="16" rx="5" ry="11" stroke="currentColor" stroke-width="1.8" fill="none"/><line x1="5" y1="16" x2="27" y2="16" stroke="currentColor" stroke-width="1.8"/>',
}


def _svg_icon(name: str, color_hex: str, size: int = 38) -> str:
    path = _SVG_ICONS.get(str(name or "code").lower(), _SVG_ICONS["code"])
    return f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" style="color:{color_hex};flex-shrink:0">{path}</svg>'


def _build_vector_html(scene: Dict[str, Any], width: int, height: int) -> str:
    vd = dict(scene.get("visual_data") or {})
    tag_pill = html.escape(str(vd.get("tag_pill") or scene.get("role", "TOPIC").upper()))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))
    accent_hex = _ACCENT_HEX.get(str(vd.get("accent_color") or "amber"), "#FACC15")
    widget_type = str(vd.get("widget_type") or "progressive_cards")
    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = (
        f'<span class="at">@</span>{html.escape(raw_wm[1:])}'
        if raw_wm.startswith("@")
        else html.escape(raw_wm)
    )

    is_wide = width > height
    scale_base = min(width, height) / 1080.0
    pad_x = int(58 * scale_base) if not is_wide else int(110 * scale_base)

    # Build Widget Markup + Animation Timeline Rules
    body_html = ""
    if widget_type == "chat_dialogue":
        msgs = list(vd.get("messages") or [])
        rows = []
        for idx, m in enumerate(msgs[:4]):
            snd = html.escape(str(m.get("sender") or "DEV")[:4].upper())
            txt = html.escape(str(m.get("text") or ""))
            col = _ACCENT_HEX.get(str(m.get("color") or ("cyan" if idx % 2 == 0 else "amber")), "#22D3EE")
            dp = float(m.get("delay_p", 0.08 + idx * 0.36))
            rows.append(f"""
            <div class="chat-row reveal" data-p="{dp:.2f}">
              <div class="avatar" style="background:{col};color:#091128">{snd}</div>
              <div class="bubble" style="border-color:{col}88">{txt}</div>
            </div>""")
        stamp = str(vd.get("stamp") or "").strip()
        stamp_html = f'<div class="stamp-red reveal" data-p="0.72">{html.escape(stamp)}</div>' if stamp else ""
        body_html = f'<div class="chat-wrap">{"".join(rows)}{stamp_html}</div>'

    elif widget_type == "meter_verdict":
        eyebrow = html.escape(str(vd.get("highlight_eyebrow") or "COPY-PASTE DEFINITION"))
        htext = html.escape(str(vd.get("highlight_text") or ""))
        dsend = html.escape(str(vd.get("dialogue_sender") or "HR")[:4].upper())
        dtext = html.escape(str(vd.get("dialogue_text") or ""))
        bars = list(vd.get("bars") or [])
        bar_rows = []
        for idx, b in enumerate(bars[:3]):
            lbl = html.escape(str(b.get("label") or ""))
            pct = max(3, min(100, int(b.get("pct", 50))))
            bcol = _ACCENT_HEX.get(str(b.get("color") or "emerald"), "#34D399")
            r_lbl = html.escape(str(b.get("right_label") or ""))
            dp = 0.25 + idx * 0.22
            bar_rows.append(f"""
            <div class="meter-row reveal" data-p="{dp:.2f}">
              <div class="meter-top"><span>{lbl}</span><span style="color:{bcol}">{r_lbl}</span></div>
              <div class="meter-track"><div class="meter-fill" data-target="{pct}" data-p="{dp:.2f}" style="background:{bcol};width:0%"></div></div>
            </div>""")
        stamp = html.escape(str(vd.get("stamp") or "रटा ✗"))
        body_html = f"""
        <div class="meter-wrap">
          <div class="dashed-box reveal" data-p="0.04">
            <div class="eyebrow">{eyebrow}</div>
            <div class="def-big">{htext}</div>
          </div>
          <div class="chat-row reveal" data-p="0.16">
            <div class="avatar" style="background:#FACC15;color:#091128">{dsend}</div>
            <div class="bubble" style="border-color:#FACC1588">{dtext}</div>
          </div>
          <div class="meters-block">{"".join(bar_rows)}</div>
          <div class="stamp-red reveal" data-p="0.68">{stamp}</div>
        </div>"""

    elif widget_type == "progressive_cards":
        h_icon = _svg_icon(str(vd.get("hero_icon") or "robot"), "#22D3EE", int(104 * scale_base))
        h_lbl = html.escape(str(vd.get("hero_label") or ""))
        cards = list(vd.get("cards") or [])
        c_rows = []
        pal_cycle = ["cyan", "amber", "emerald", "purple"]
        for idx, c in enumerate(cards[:4]):
            ic_col = _ACCENT_HEX[pal_cycle[idx % len(pal_cycle)]]
            ic_svg = _svg_icon(str(c.get("icon") or "file"), ic_col, int(36 * scale_base))
            ctext = html.escape(str(c.get("text") or ""))
            dp = 0.16 + idx * 0.20
            c_rows.append(f"""
            <div class="pcard reveal" data-p="{dp:.2f}" style="border-color:{ic_col}77">
              {ic_svg}<span>{ctext}</span>
            </div>""")
        fpill = str(vd.get("footer_pill") or "").strip()
        fp_html = f'<div class="footer-pill reveal" data-p="0.78">{html.escape(fpill)}</div>' if fpill else ""
        body_html = f"""
        <div class="pcards-wrap">
          <div class="hero-col reveal" data-p="0.02">
            {h_icon}
            <div class="hero-lbl">{h_lbl}</div>
          </div>
          <div class="pcards-list">{"".join(c_rows)}</div>
          {fp_html}
        </div>"""

    elif widget_type == "spaghetti_wires":
        ln = dict(vd.get("left_node") or {})
        rns = list(vd.get("right_nodes") or [])[:4]
        l_svg = _svg_icon(str(ln.get("icon") or "robot"), "#22D3EE", int(92 * scale_base))
        l_lbl = html.escape(str(ln.get("label") or "App"))
        n_cnt = max(1, len(rns))
        ys = [120, 290, 460] if n_cnt == 3 else ([170, 400] if n_cnt == 2 else [90, 220, 350, 480])
        paths_svg = []
        tags_html = []
        boxes_html = []
        for idx, rn in enumerate(rns):
            y_end = ys[idx]
            col = _ACCENT_HEX.get(str(rn.get("color") or "cyan"), "#22D3EE")
            ic = _svg_icon(str(rn.get("icon") or "file"), col, int(44 * scale_base))
            rlbl = html.escape(str(rn.get("label") or ""))
            wtag = html.escape(str(rn.get("wire_tag") or f"custom code {idx+1}"))
            dp = 0.12 + idx * 0.20
            paths_svg.append(
                f'<path class="svg-draw" data-p="{dp:.2f}" d="M 155 290 C 290 290, 360 {y_end}, 530 {y_end}" '
                f'stroke="#F43F5E" stroke-width="4.5" fill="none" stroke-linecap="round"/>'
            )
            tags_html.append(
                f'<div class="wire-pill reveal" data-p="{dp+0.08:.2f}" style="top:{int((290+y_end)/2 - 18)}px">{wtag}</div>'
            )
            boxes_html.append(
                f'<div class="rnode reveal" data-p="{dp:.2f}" style="top:{y_end - 44}px;border-color:{col}AA">{ic}<span>{rlbl}</span></div>'
            )
        body_html = f"""
        <div class="graph-stage">
          <svg class="graph-svg" viewBox="0 0 760 580">{"".join(paths_svg)}</svg>
          <div class="left-hero reveal" data-p="0.02">{l_svg}<div class="left-lbl">{l_lbl}</div></div>
          {"".join(tags_html)}
          {"".join(boxes_html)}
        </div>"""

    elif widget_type == "hub_radiate":
        ln = dict(vd.get("left_node") or {})
        rns = list(vd.get("right_nodes") or [])[:4]
        l_svg = _svg_icon(str(ln.get("icon") or "robot"), "#22D3EE", int(50 * scale_base))
        l_lbl = html.escape(str(ln.get("label") or "AI App"))
        h_lbl = html.escape(str(vd.get("hub_label") or "HUB")[:14])
        h_lbl_fs = 24 if len(h_lbl) > 7 else (28 if len(h_lbl) > 4 else 36)
        h_sub = html.escape(str(vd.get("hub_sub") or "standard protocol"))
        eq = html.escape(str(vd.get("equation_line") or ""))
        fpill = html.escape(str(vd.get("footer_pill") or ""))
        n_cnt = max(1, len(rns))
        ys = [85, 195, 305, 415] if n_cnt == 4 else ([105, 250, 395] if n_cnt == 3 else [160, 330])
        paths_svg = []
        boxes_html = []
        for idx, rn in enumerate(rns):
            y_end = ys[idx]
            col = _ACCENT_HEX.get(str(rn.get("color") or "cyan"), "#22D3EE")
            ic = _svg_icon(str(rn.get("icon") or "file"), col, int(34 * scale_base))
            rlbl = html.escape(str(rn.get("label") or ""))
            dp = 0.22 + idx * 0.14
            paths_svg.append(
                f'<path id="hp_{idx}" class="svg-draw" data-p="{dp:.2f}" d="M 425 250 L 545 {y_end}" '
                f'stroke="#22D3EE" stroke-width="4" fill="none" stroke-linecap="round"/>'
                f'<circle class="pkt-dot" data-x1="425" data-y1="250" data-x2="545" data-y2="{y_end}" data-p="{dp:.2f}" r="6" fill="#FACC15"/>'
            )
            boxes_html.append(
                f'<div class="hub-rnode reveal" data-p="{dp:.2f}" style="top:{y_end - 32}px;border-color:{col}AA">{ic}<span>{rlbl}</span></div>'
            )
        eq_html = f'<div class="eq-line reveal" data-p="0.72">{eq}</div>' if eq else ""
        fp_html = f'<div class="footer-pill reveal" data-p="0.80">{fpill}</div>' if fpill else ""
        body_html = f"""
        <div class="hub-wrap">
          <div class="hub-canvas">
            <svg class="graph-svg" viewBox="0 0 760 490">
              <line class="svg-draw" data-p="0.12" x1="175" y1="250" x2="295" y2="250" stroke="#22D3EE" stroke-width="4.5" stroke-dasharray="10 8"/>
              {"".join(paths_svg)}
            </svg>
            <div class="hub-left reveal" data-p="0.02">{l_svg}<span>{l_lbl}</span></div>
            <div class="hub-center reveal" data-p="0.06">
              <div class="hub-badge" style="font-size:{h_lbl_fs}px">{h_lbl}</div>
              <div class="hub-sub">{h_sub}</div>
            </div>
            {"".join(boxes_html)}
          </div>
          {eq_html}{fp_html}
        </div>"""

    elif widget_type == "analogy_tree":
        tn = dict(vd.get("top_node") or {})
        t_svg = _svg_icon(str(tn.get("icon") or "monitor"), "#94A3B8", int(36 * scale_base))
        t_lbl = html.escape(str(tn.get("label") or "Computer"))
        h_lbl = html.escape(str(vd.get("hub_label") or "USB")[:12])
        h_col = _ACCENT_HEX.get(str(vd.get("hub_color") or "cyan"), "#22D3EE")
        brs = list(vd.get("branches") or [])[:3]
        eq = html.escape(str(vd.get("equation_line") or ""))
        fpill = html.escape(str(vd.get("footer_pill") or ""))
        xs = [135, 380, 625] if len(brs) >= 3 else ([240, 520] if len(brs) == 2 else [380])
        paths_svg = []
        cards_html = []
        for idx, br in enumerate(brs):
            x_end = xs[idx]
            col = _ACCENT_HEX.get(str(br.get("color") or "cyan"), "#22D3EE")
            ic = _svg_icon(str(br.get("icon") or "keyboard"), col, int(44 * scale_base))
            blbl = html.escape(str(br.get("label") or ""))
            dp = 0.20 + idx * 0.19
            chk = '<div class="chk reveal" data-p="' + f"{min(0.92, dp+0.12):.2f}" + '">✓</div>' if br.get("check", True) else ""
            paths_svg.append(
                f'<path class="svg-draw" data-p="{dp:.2f}" d="M 380 218 C 380 295, {x_end} 275, {x_end} 355" '
                f'stroke="{h_col}" stroke-width="4.5" fill="none" stroke-linecap="round"/>'
            )
            cards_html.append(
                f'<div class="tree-col" style="left:{x_end - 98}px">'
                f'<div class="tree-card reveal" data-p="{dp:.2f}" style="border-color:{col}BB">{ic}<span>{blbl}</span></div>'
                f'{chk}</div>'
            )
        eq_html = f'<div class="eq-line reveal" data-p="0.76">{eq}</div>' if eq else ""
        fp_html = f'<div class="footer-pill reveal" data-p="0.84">{fpill}</div>' if fpill else ""
        body_html = f"""
        <div class="hub-wrap">
          <div class="tree-canvas">
            <svg class="graph-svg" viewBox="0 0 760 520">
              <line class="svg-draw" data-p="0.06" x1="380" y1="92" x2="380" y2="148" stroke="{h_col}" stroke-width="4.5"/>
              {"".join(paths_svg)}
            </svg>
            <div class="tree-top reveal" data-p="0.02">{t_svg}<span>{t_lbl}</span></div>
            <div class="tree-hub reveal" data-p="0.10" style="background:{h_col};box-shadow:0 0 36px {h_col}66">{h_lbl}</div>
            {"".join(cards_html)}
          </div>
          {eq_html}{fp_html}
        </div>"""

    elif widget_type == "split_verdict":
        lc = dict(vd.get("left_col") or {})
        rc = dict(vd.get("right_col") or {})
        eq = html.escape(str(vd.get("equation_line") or ""))
        fpill = html.escape(str(vd.get("footer_pill") or ""))
        body_html = f"""
        <div class="split-wrap">
          <div class="split-cols">
            <div class="scol left reveal" data-p="0.08">
              <div class="scol-title">{html.escape(str(lc.get("title") or ""))}</div>
              <div class="scol-body">{html.escape(str(lc.get("body") or ""))}</div>
              <div class="scol-mark" style="color:#F43F5E">✗</div>
            </div>
            <div class="scol right reveal" data-p="0.34">
              <div class="scol-title" style="color:#34D399">{html.escape(str(rc.get("title") or ""))}</div>
              <div class="scol-body">{html.escape(str(rc.get("body") or ""))}</div>
              <div class="scol-mark" style="color:#34D399">✓</div>
            </div>
          </div>
          {f'<div class="eq-big reveal" data-p="0.62">{eq}</div>' if eq else ''}
          {f'<div class="footer-pill reveal" data-p="0.76">{fpill}</div>' if fpill else ''}
        </div>"""

    else:  # follow_cta
        pills = list(vd.get("pills") or ["AI", "Coding", "System Design", "Practical"])[:4]
        ht = html.escape(str(vd.get("handle_title") or watermark))
        hs = html.escape(str(vd.get("handle_sub") or "Tech & Engineering"))
        btn = html.escape(str(vd.get("cta_button") or "+ Follow"))
        p_cols = ["#22D3EE", "#FACC15", "#34D399", "#A855F7"]
        p_html = "".join(
            f'<div class="tag-grid-item reveal" data-p="{0.05 + idx*0.10:.2f}" style="border-color:{p_cols[idx%4]}99">{html.escape(str(p))}</div>'
            for idx, p in enumerate(pills)
        )
        body_html = f"""
        <div class="cta-wrap">
          <div class="tag-grid">{p_html}</div>
          <div class="brand-box reveal" data-p="0.45">
            {_svg_icon("cpu", "#FACC15", int(54 * scale_base))}
            <div>
              <div class="brand-big">{ht}</div>
              <div class="brand-sub">{hs}</div>
            </div>
          </div>
          <div class="cta-btn reveal" data-p="0.68">{btn}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: radial-gradient(circle at 50% 18%, #102046 0%, #091128 58%, #050915 100%);
    color: #F8FAFC;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }}
  .dot-bg {{
    position: absolute; inset: 0; opacity: 0.18;
    background-image: radial-gradient(#64748B 1.2px, transparent 1.2px);
    background-size: 28px 28px;
  }}
  .root {{
    position: relative; width: 100%; height: 100%;
    display: flex; flex-direction: column;
    padding: {int(40*scale_base)}px {pad_x}px {int(52*scale_base)}px;
    gap: {int(20*scale_base)}px;
  }}
  .top-wm-row {{ display: flex; align-items: center; justify-content: flex-start; }}
  .wm-pill {{
    display: inline-flex; align-items: center;
    padding: {int(8*scale_base)}px {int(20*scale_base)}px; border-radius: 999px;
    background: rgba(15,23,42,0.88); border: 1.5px solid rgba(148,163,184,0.30);
    font-size: {int(24*scale_base)}px; font-weight: 800; color: #F8FAFC;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .pill-tag {{
    align-self: flex-start; display: inline-flex; align-items: center; gap: 10px;
    padding: {int(10*scale_base)}px {int(22*scale_base)}px; border-radius: 999px;
    border: 1.8px solid rgba(34,211,238,0.6); background: rgba(15,23,42,0.75);
    color: #22D3EE; font-size: {int(21*scale_base)}px; font-weight: 700; letter-spacing: 2px;
  }}
  .pill-dot {{ width: 11px; height: 11px; border-radius: 50%; background: #22D3EE; box-shadow: 0 0 10px #22D3EE; }}
  .headline {{
    text-align: center; line-height: 1.18; margin: {int(8*scale_base)}px 0 {int(6*scale_base)}px;
    font-size: {int(62*scale_base if not is_wide else 48*scale_base)}px; font-weight: 800;
  }}
  .headline .acc {{ display: block; color: {accent_hex}; }}
  .stage-card {{
    flex: 1; background: rgba(11, 18, 38, 0.88);
    border: 1.8px solid rgba(148,163,184,0.22); border-radius: {int(30*scale_base)}px;
    box-shadow: 0 24px 70px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.06);
    padding: {int(34*scale_base)}px {int(32*scale_base)}px;
    display: flex; flex-direction: column; justify-content: center; position: relative; overflow: hidden;
  }}
  .reveal {{ opacity: 0; transform: translateY(16px); transition: none; }}
  .reveal.on {{ opacity: 1; transform: translateY(0); }}

  /* Chat dialogue */
  .chat-wrap {{ display: flex; flex-direction: column; gap: {int(28*scale_base)}px; position: relative; }}
  .chat-row {{ display: flex; align-items: center; gap: {int(18*scale_base)}px; }}
  .avatar {{
    width: {int(64*scale_base)}px; height: {int(64*scale_base)}px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: {int(22*scale_base)}px; flex-shrink: 0;
  }}
  .bubble {{
    flex: 1; background: rgba(15,23,42,0.92); border: 2px solid rgba(34,211,238,0.5);
    border-radius: {int(18*scale_base)}px; padding: {int(22*scale_base)}px {int(26*scale_base)}px;
    font-size: {int(31*scale_base)}px; font-weight: 600; color: #F1F5F9; line-height: 1.35;
  }}
  .stamp-red {{
    align-self: flex-end; margin-top: {int(18*scale_base)}px; transform: rotate(-6deg);
    border: 4px solid #F43F5E; border-radius: 14px; color: #F43F5E;
    padding: {int(10*scale_base)}px {int(26*scale_base)}px; font-size: {int(34*scale_base)}px; font-weight: 900;
    background: rgba(244,63,94,0.10); box-shadow: 0 0 28px rgba(244,63,94,0.28);
  }}

  /* Meter Verdict */
  .meter-wrap {{ display: flex; flex-direction: column; gap: {int(26*scale_base)}px; }}
  .dashed-box {{
    border: 2px dashed rgba(148,163,184,0.45); border-radius: 18px; padding: {int(22*scale_base)}px; text-align: center;
    background: rgba(30,41,59,0.35);
  }}
  .eyebrow {{ font-size: {int(20*scale_base)}px; letter-spacing: 3px; color: #94A3B8; margin-bottom: 8px; font-weight: 700; }}
  .def-big {{ font-size: {int(34*scale_base)}px; font-weight: 800; color: #22D3EE; }}
  .meters-block {{ display: flex; flex-direction: column; gap: {int(22*scale_base)}px; margin-top: 8px; }}
  .meter-top {{ display: flex; justify-content: space-between; font-size: {int(27*scale_base)}px; font-weight: 700; margin-bottom: 10px; }}
  .meter-track {{ width: 100%; height: {int(22*scale_base)}px; background: rgba(51,65,85,0.65); border-radius: 999px; overflow: hidden; }}
  .meter-fill {{ height: 100%; border-radius: 999px; }}

  /* Progressive Cards */
  .pcards-wrap {{ display: flex; flex-direction: column; align-items: center; gap: {int(26*scale_base)}px; }}
  .hero-col {{ display: flex; flex-direction: column; align-items: center; gap: 10px; }}
  .hero-lbl {{ font-size: {int(25*scale_base)}px; color: #94A3B8; font-weight: 700; }}
  .pcards-list {{ width: 100%; display: flex; flex-direction: column; gap: {int(18*scale_base)}px; }}
  .pcard {{
    display: flex; align-items: center; gap: {int(20*scale_base)}px;
    background: rgba(15,23,42,0.92); border: 2px solid rgba(34,211,238,0.45); border-radius: 18px;
    padding: {int(22*scale_base)}px {int(26*scale_base)}px; font-size: {int(30*scale_base)}px; font-weight: 700;
  }}
  .footer-pill {{
    margin-top: {int(10*scale_base)}px; align-self: center;
    padding: {int(12*scale_base)}px {int(34*scale_base)}px; border-radius: 14px;
    border: 2px solid rgba(250,204,21,0.55); background: rgba(250,204,21,0.08);
    color: #FACC15; font-size: {int(26*scale_base)}px; font-weight: 800; text-align: center;
  }}

  /* Spaghetti & Hub & Analogy SVG Stage */
  .graph-stage {{ position: relative; width: 760px; height: 580px; margin: 0 auto; transform: scale({scale_base * (1.12 if not is_wide else 0.72):.3f}); transform-origin: center center; }}
  .graph-svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }}
  .left-hero {{ position: absolute; left: 22px; top: 215px; width: 130px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 8px; }}
  .left-lbl {{ font-size: 22px; font-weight: 700; color: #94A3B8; }}
  .wire-pill {{
    position: absolute; left: 280px; background: #191528; border: 1.5px solid #F43F5E; color: #FCA5A5;
    padding: 5px 14px; border-radius: 10px; font-size: 18px; font-weight: 700; white-space: nowrap;
  }}
  .rnode {{
    position: absolute; left: 530px; width: 210px; height: 88px; border-radius: 18px;
    background: rgba(15,23,42,0.95); border: 2.2px solid #22D3EE;
    display: flex; align-items: center; gap: 14px; padding: 0 18px; font-size: 22px; font-weight: 700;
  }}

  /* Hub Radiate */
  .hub-wrap {{ display: flex; flex-direction: column; align-items: center; gap: {int(16*scale_base)}px; width: 100%; }}
  .hub-canvas {{ position: relative; width: 760px; height: 490px; transform: scale({scale_base * (1.12 if not is_wide else 0.72):.3f}); transform-origin: top center; }}
  .hub-left {{
    position: absolute; left: 10px; top: 185px; width: 165px; height: 130px; border-radius: 20px;
    border: 2.2px solid rgba(34,211,238,0.65); background: rgba(15,23,42,0.95);
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; font-size: 23px; font-weight: 700;
  }}
  .hub-center {{ position: absolute; left: 280px; top: 192px; width: 162px; text-align: center; }}
  .hub-badge {{
    min-height: 106px; padding: 12px 14px; border-radius: 22px; background: #FACC15; color: #091128;
    font-size: 34px; font-weight: 900; line-height: 1.08; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 38px rgba(250,204,21,0.55); overflow-wrap: anywhere;
  }}
  .hub-sub {{ margin-top: 10px; color: #FACC15; font-size: 19px; font-weight: 700; }}
  .hub-rnode {{
    position: absolute; left: 545px; width: 205px; height: 64px; border-radius: 14px;
    background: rgba(15,23,42,0.95); border: 2px solid #22D3EE;
    display: flex; align-items: center; gap: 12px; padding: 0 16px; font-size: 22px; font-weight: 700;
  }}
  .eq-line {{ font-size: {int(27*scale_base)}px; font-weight: 700; color: #E2E8F0; text-align: center; }}

  /* Analogy Tree */
  .tree-canvas {{ position: relative; width: 760px; height: 520px; transform: scale({scale_base * (1.12 if not is_wide else 0.72):.3f}); transform-origin: top center; }}
  .tree-top {{
    position: absolute; left: 255px; top: 18px; width: 250px; height: 74px; border-radius: 16px;
    border: 2px solid rgba(148,163,184,0.55); background: rgba(15,23,42,0.95);
    display: flex; align-items: center; justify-content: center; gap: 12px; font-size: 26px; font-weight: 700;
  }}
  .tree-hub {{
    position: absolute; left: 250px; top: 146px; width: 260px; height: 74px; border-radius: 18px;
    color: #091128; font-size: 38px; font-weight: 900; display: flex; align-items: center; justify-content: center;
  }}
  .tree-col {{ position: absolute; top: 355px; width: 196px; display: flex; flex-direction: column; align-items: center; gap: 12px; }}
  .tree-card {{
    width: 196px; height: 128px; border-radius: 18px; background: rgba(15,23,42,0.95);
    border: 2.2px solid #22D3EE; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
    font-size: 22px; font-weight: 700;
  }}
  .chk {{ color: #34D399; font-size: 32px; font-weight: 900; }}

  /* Split Verdict */
  .split-wrap {{ display: flex; flex-direction: column; align-items: center; gap: {int(28*scale_base)}px; }}
  .split-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: {int(22*scale_base)}px; width: 100%; }}
  .scol {{
    border-radius: 22px; padding: {int(30*scale_base)}px {int(22*scale_base)}px; text-align: center;
    display: flex; flex-direction: column; justify-content: space-between; min-height: {int(380*scale_base)}px;
  }}
  .scol.left {{ background: rgba(244,63,94,0.08); border: 2px solid rgba(244,63,94,0.45); }}
  .scol.right {{ background: rgba(52,211,153,0.08); border: 2px solid rgba(52,211,153,0.55); }}
  .scol-title {{ font-size: {int(34*scale_base)}px; font-weight: 800; }}
  .scol-body {{ font-size: {int(27*scale_base)}px; color: #CBD5E1; line-height: 1.35; }}
  .scol-mark {{ font-size: {int(62*scale_base)}px; font-weight: 900; }}
  .eq-big {{ font-size: {int(42*scale_base)}px; font-weight: 900; color: #FACC15; }}

  /* Follow CTA */
  .cta-wrap {{ display: flex; flex-direction: column; align-items: center; gap: {int(26*scale_base)}px; width: 100%; }}
  .tag-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: {int(16*scale_base)}px; width: 100%; }}
  .tag-grid-item {{
    border: 2px solid #22D3EE; border-radius: 16px; padding: {int(20*scale_base)}px;
    text-align: center; font-size: {int(28*scale_base)}px; font-weight: 700; background: rgba(15,23,42,0.85);
  }}
  .brand-box {{
    width: 100%; display: flex; align-items: center; justify-content: center; gap: 20px;
    border: 2px solid rgba(148,163,184,0.3); border-radius: 22px; padding: {int(26*scale_base)}px;
    background: rgba(15,23,42,0.92);
  }}
  .brand-big {{ font-size: {int(34*scale_base)}px; font-weight: 900; color: #F8FAFC; }}
  .brand-sub {{ font-size: {int(23*scale_base)}px; color: #94A3B8; margin-top: 4px; }}
  .cta-btn {{
    width: 100%; padding: {int(22*scale_base)}px; border-radius: 18px;
    background: #FACC15; color: #091128; font-size: {int(32*scale_base)}px; font-weight: 900; text-align: center;
    box-shadow: 0 0 36px rgba(250,204,21,0.45);
  }}
  .corner-wm {{
    position: absolute; right: {int(38*scale_base)}px; bottom: {int(22*scale_base)}px;
    padding: 6px 14px; border-radius: 10px; background: rgba(15,23,42,0.9);
    border: 1px solid rgba(250,204,21,0.45); color: #FACC15; font-size: {int(18*scale_base)}px; font-weight: 800;
  }}
</style>
</head>
<body>
  <div class="dot-bg"></div>
  <div class="root">
    <div class="top-wm-row"><div class="wm-pill">{wm_html}</div></div>
    <div class="pill-tag"><span class="pill-dot"></span>{tag_pill}</div>
    <div class="headline">{h_white}<span class="acc">{h_accent}</span></div>
    <div class="stage-card">{body_html}</div>
  </div>

  <script>
    const draws = Array.from(document.querySelectorAll('.svg-draw'));
    draws.forEach(el => {{
      const len = (el.getTotalLength ? el.getTotalLength() : 400) || 400;
      el.dataset.len = String(len);
      el.style.strokeDasharray = String(len);
      el.style.strokeDashoffset = String(len);
    }});

    window.__setStudioProgress = function(p, linClock) {{
      const prog = Math.max(0, Math.min(1, Number(p) || 0));
      const lp = Math.max(0, Math.min(1, Number(linClock !== undefined ? linClock : prog) || 0));
      document.querySelectorAll('.reveal').forEach(el => {{
        const dp = parseFloat(el.dataset.p || '0');
        const fade = Math.max(0, Math.min(1, (prog - dp + 0.05) / 0.10));
        el.style.opacity = fade.toFixed(3);
        el.style.transform = `translateY(${{(12 * (1 - fade)).toFixed(1)}}px)`;
      }});
      document.querySelectorAll('.meter-fill').forEach(el => {{
        const dp = parseFloat(el.dataset.p || '0');
        const tgt = parseFloat(el.dataset.target || '50');
        const local = Math.max(0, Math.min(1, (lp - dp) / 0.28));
        el.style.width = (tgt * local).toFixed(1) + '%';
      }});
      draws.forEach(el => {{
        const dp = parseFloat(el.dataset.p || '0');
        const len = parseFloat(el.dataset.len || '400');
        const local = Math.max(0, Math.min(1, (lp - dp) / 0.22));
        el.style.strokeDashoffset = (len * (1 - local)).toFixed(1);
      }});
      document.querySelectorAll('.pkt-dot').forEach(dot => {{
        const dp = parseFloat(dot.dataset.p || '0');
        if (lp < dp) {{ dot.style.opacity = '0'; return; }}
        dot.style.opacity = '1';
        const x1 = parseFloat(dot.dataset.x1), y1 = parseFloat(dot.dataset.y1);
        const x2 = parseFloat(dot.dataset.x2), y2 = parseFloat(dot.dataset.y2);
        const phase = ((lp - dp) * 2.6) % 1;
        dot.setAttribute('cx', (x1 + (x2 - x1) * phase).toFixed(1));
        dot.setAttribute('cy', (y1 + (y2 - y1) * phase).toFixed(1));
      }});
    }};
    window.__setStudioProgress(1.0, 1.0);
  </script>
</body>
</html>"""


def render_v2_vector_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
) -> Path:
    """Renders all FPS frames for a Studio V2 Clean Vector Storyboard scene using Chromium."""
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

    html_doc = _build_vector_html(scene, w, h)
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
            eff_p = compute_synced_visual_progress(lin_p, cur_t, words, tone=tone)
            page.evaluate(
                "(args) => { if (window.__setStudioProgress) window.__setStudioProgress(args.wp, args.lp); }",
                {"wp": round(eff_p, 4), "lp": round(lin_p, 4)},
            )
            page.screenshot(path=str(out_dir / f"frame_{f:04d}.jpg"), type="jpeg", quality=90)

        browser.close()
        p.stop()
        return out_dir

    # Graceful headless Pillow fallback if browser unavailable
    from PIL import Image, ImageDraw, ImageFont
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (9, 17, 40))
    draw = ImageDraw.Draw(img)
    draw.rectangle([48, 280, w - 48, h - 180], outline=(56, 189, 248), width=3)
    draw.text((80, 120), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(248, 250, 252))
    base_jpg = out_dir / "frame_0000.jpg"
    img.save(base_jpg, quality=90)
    for f in range(1, total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir
