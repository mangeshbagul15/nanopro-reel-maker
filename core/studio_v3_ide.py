"""
Studio V3 — Live IDE & SQL/Python Simulator Renderer.
Renders a high-contrast, mobile-first VS Code / DataGrip dark IDE canvas via Playwright Chromium:
  - Large, razor-sharp syntax-highlighted Python / SQL code + active line focus + +/- diff marks
  - Unobstructed Line-anchored Callout Card (zero overlap with code lines)
  - Smooth mouse cursor glide + bright dual-ring click ripple (Line Click -> Run Button Click)
  - Expanded Live Output Drawer (SQL Result Table OR Live Profiler / Traceback / Execution Status)
"""

from __future__ import annotations

import html
import json
import re
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
}

_PY_KEYWORDS = {
    "def", "class", "return", "import", "from", "as", "if", "elif", "else",
    "for", "while", "in", "not", "and", "or", "with", "try", "except",
    "finally", "async", "await", "yield", "lambda", "pass", "break",
    "continue", "raise", "True", "False", "None", "is", "assert",
}

_SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
    "OUTER", "ON", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "INSERT",
    "INTO", "VALUES", "UPDATE", "SET", "DELETE", "CREATE", "TABLE",
    "INDEX", "CONCURRENTLY", "EXPLAIN", "ANALYZE", "OVER", "PARTITION",
    "DENSE_RANK", "ROW_NUMBER", "RANK", "AS", "AND", "OR", "NOT", "IN",
    "WITH", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN", "CASE",
    "WHEN", "THEN", "ELSE", "END", "DESC", "ASC", "INTERVAL", "NOW",
}


def _highlight_code_line(line: str, lang: str = "python") -> str:
    """Produces high-contrast syntax-highlighted HTML spans for Python or SQL lines."""
    raw = str(line or "")
    if not raw.strip():
        return "&nbsp;"

    low_lang = str(lang or "python").lower()
    comment_part = ""
    code_part = raw
    if low_lang == "sql":
        m_com = re.search(r"(--.*)$", raw)
        if m_com and raw[:m_com.start()].count("'") % 2 == 0:
            code_part = raw[:m_com.start()]
            comment_part = m_com.group(1)
    else:
        m_com = re.search(r"(#.*)$", raw)
        if m_com and raw[:m_com.start()].count("'") % 2 == 0 and raw[:m_com.start()].count('"') % 2 == 0:
            code_part = raw[:m_com.start()]
            comment_part = m_com.group(1)

    token_re = re.compile(
        r"('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b)"
    )
    out: List[str] = []
    pos = 0
    for m in token_re.finditer(code_part):
        if m.start() > pos:
            out.append(html.escape(code_part[pos:m.start()]))
        tok = m.group(0)
        esc = html.escape(tok)
        if tok.startswith(("'", '"')):
            out.append(f'<span class="tok-str">{esc}</span>')
        elif re.fullmatch(r"\d+(?:\.\d+)?", tok):
            out.append(f'<span class="tok-num">{esc}</span>')
        elif (low_lang == "sql" and tok.upper() in _SQL_KEYWORDS) or (low_lang != "sql" and tok in _PY_KEYWORDS):
            out.append(f'<span class="tok-kw">{esc}</span>')
        elif m.end() < len(code_part) and code_part[m.end():m.end() + 1] == "(":
            out.append(f'<span class="tok-fn">{esc}</span>')
        else:
            out.append(f'<span class="tok-id">{esc}</span>')
        pos = m.end()
    if pos < len(code_part):
        out.append(html.escape(code_part[pos:]))
    if comment_part:
        out.append(f'<span class="tok-com">{html.escape(comment_part)}</span>')
    return "".join(out)


def _tone_ide_motion(tone: str, role: str, scene_tone: Optional[str]) -> Dict[str, Any]:
    prof = get_tone_profile(tone, scene_tone=scene_tone, role=role)
    t_key = prof.get("key", "live_debug_pair")
    accent = prof.get("accent_key", "cyan")
    if t_key in ("fireship_octane", "youth_friend_turbo", "cage_match_vs", "myth_buster_contrarian"):
        return {"ripple_dur": 0.32, "tone_accent": accent}
    if t_key in ("war_story_postmortem", "dramatic_performance"):
        return {"ripple_dur": 0.40, "tone_accent": "rose"}
    return {"ripple_dur": 0.36, "tone_accent": accent}


def _build_ide_html(
    scene: Dict[str, Any],
    width: int,
    height: int,
    tone: str = "auto_2026_director",
) -> str:
    vd = dict(scene.get("visual_data") or {})
    tone_cfg = _tone_ide_motion(tone, str(scene.get("role") or ""), scene.get("scene_tone"))
    accent_key = str(vd.get("accent_color") or tone_cfg["tone_accent"] or "cyan")
    accent_hex = _ACCENT_HEX.get(accent_key, "#38BDF8")

    raw_wm = str(vd.get("watermark") or DEFAULT_WATERMARK).strip() or DEFAULT_WATERMARK
    wm_html = (
        f'<span class="at">@</span>{html.escape(raw_wm[1:])}'
        if raw_wm.startswith("@")
        else html.escape(raw_wm)
    )
    hud_pill = html.escape(str(vd.get("hud_pill") or scene.get("role", "LIVE IDE").upper()))
    h_white = html.escape(str(vd.get("headline_white") or ""))
    h_accent = html.escape(str(vd.get("headline_accent") or ""))

    lang = str(vd.get("language") or "python").lower()
    if lang not in ("python", "sql", "bash"):
        lang = "python"
    file_name = html.escape(str(vd.get("file_name") or ("query.sql" if lang == "sql" else "main.py")))
    tab_secondary = html.escape(str(vd.get("tab_secondary") or ("schema.sql" if lang == "sql" else "tests.py")))

    code_lines = [str(x) for x in (vd.get("code_lines") or [])][:9]
    if not code_lines:
        code_lines = [
            "SELECT u.id, u.name, COUNT(*) AS total",
            "FROM users u",
            "INNER JOIN orders o ON o.user_id = u.id",
            "GROUP BY u.id, u.name;",
        ] if lang == "sql" else [
            "users = db.fetch_active_users()",
            "for user in users:",
            "    orders = db.fetch_orders(user.id)  # N+1!",
        ]

    raw_focus = list(vd.get("focus_lines") or [min(2, len(code_lines))])
    focus_lines = {int(x) for x in raw_focus if isinstance(x, (int, float)) or str(x).isdigit()}
    if not focus_lines:
        focus_lines = {min(2, len(code_lines))}

    line_status = str(vd.get("line_status") or ("error" if scene.get("role") in ("problem", "misconception", "edge_case") else "active")).lower()
    diff_marks = dict(vd.get("diff_marks") or {})

    primary_ln = sorted(focus_lines)[0]
    steps = list(vd.get("ide_steps") or [])
    if not steps:
        steps = [
            {"line": primary_ln, "p": 0.08, "click": True},
            {"target": "run_btn", "p": 0.34, "click": True},
        ]

    # Dynamic monospace size based on max line length so lines NEVER clip or look tiny
    max_chars = max((len(ln) for ln in code_lines), default=32)
    is_wide = width > height
    sc = min(width, height) / 1080.0
    if is_wide:
        code_font_px = int(max(18, min(24, int(920 / max(28, max_chars) * 1.4))) * sc)
    else:
        if max_chars <= 38:
            code_font_px = int(31 * sc)
        elif max_chars <= 48:
            code_font_px = int(27 * sc)
        else:
            code_font_px = int(24 * sc)

    code_rows_html: List[str] = []
    for idx_l, raw_line in enumerate(code_lines, start=1):
        is_foc = idx_l in focus_lines
        dm = str(diff_marks.get(str(idx_l)) or "")
        cls = ["code-line"]
        if is_foc:
            cls.append("focus-err" if line_status in ("error", "bug", "warn") else "focus-ok")
        if dm == "-":
            cls.append("diff-del")
        elif dm == "+":
            cls.append("diff-add")
        hl_html = _highlight_code_line(raw_line, lang=lang)
        badge_mark = f'<span class="diff-sym">{html.escape(dm)}</span>' if dm in ("+", "-") else ""
        focus_tag = ""
        if is_foc and idx_l == primary_ln:
            ft_lbl = "HOTSPOT" if line_status in ("error", "bug", "warn") else "FOCUS"
            ft_cls = "ft-err" if line_status in ("error", "bug", "warn") else "ft-ok"
            focus_tag = f'<span class="focus-pill {ft_cls}">{ft_lbl}</span>'
        code_rows_html.append(
            f'<div class="{" ".join(cls)}" id="line_{idx_l}" data-ln="{idx_l}">'
            f'<span class="ln-num">{idx_l:02d}</span>{badge_mark}<span class="ln-txt">{hl_html}</span>{focus_tag}'
            f'</div>'
        )

    # Context Callout Bubble (anchored cleanly below the code rows — zero overlap!)
    callout = dict(vd.get("callout") or {})
    c_title = html.escape(str(callout.get("title") or ("⚠️ BOTTLENECK" if line_status in ("error", "bug") else "💡 INSIGHT")))
    c_body = html.escape(str(callout.get("text") or "Highlighted execution hotspot"))
    c_tone = str(callout.get("color") or ("rose" if line_status in ("error", "bug") else "amber"))
    c_hex = _ACCENT_HEX.get(c_tone, "#FBBF24")
    c_line = int(callout.get("line") or primary_ln)
    c_dp = float(callout.get("delay_p", 0.14))

    # Live Output Drawer (SQL Table OR Terminal Output)
    drawer = dict(vd.get("output_drawer") or {})
    d_mode = str(drawer.get("mode") or ("sql_table" if lang == "sql" else "terminal")).lower()
    d_title = html.escape(str(drawer.get("title") or ("SQL RESULT SET" if d_mode == "sql_table" else "TERMINAL OUTPUT")))
    d_metric = html.escape(str(drawer.get("metric") or ("3 rows · 1.2ms" if d_mode == "sql_table" else "exit 0 · 8ms")))
    d_metric_tone = str(drawer.get("metric_color") or ("rose" if line_status in ("error", "bug") else "emerald"))
    d_metric_hex = _ACCENT_HEX.get(d_metric_tone, "#34D399")
    d_open_p = min(0.32, float(drawer.get("open_p", 0.28)))

    if d_mode == "sql_table":
        tbl = dict(drawer.get("table") or {})
        headers = [html.escape(str(h)) for h in (tbl.get("headers") or ["id", "status", "latency"])[:4]]
        rows = list(tbl.get("rows") or [["101", "SYNCED", "0.8ms"], ["102", "SYNCED", "1.1ms"], ["103", "CACHED", "0.3ms"]])[:4]
        th_html = "".join(f"<th>{h}</th>" for h in headers)
        tr_html_list = []
        for r_i, row in enumerate(rows):
            cells = "".join(f"<td>{html.escape(str(c))}</td>" for c in list(row)[:len(headers)])
            tr_html_list.append(
                f'<tr class="drawer-row" data-p="{min(0.76, d_open_p + 0.06 + r_i * 0.09):.2f}">{cells}</tr>'
            )
        drawer_body_html = f'<table class="sql-tbl"><thead><tr>{th_html}</tr></thead><tbody>{"".join(tr_html_list)}</tbody></table>'
    else:
        term_lines = list(drawer.get("lines") or [
            "$ python pipeline.py",
            "✓ Processed 10,000 rows in 14ms (batch JOIN)",
        ])[:5]
        t_rows = []
        for t_i, tl in enumerate(term_lines):
            txt_s = str(tl)
            low_t = txt_s.lower()
            l_cls = "term-err" if any(k in low_t for k in ("err", "fail", "timeout", "n+1", "1,001", "dropped", "✗")) else (
                "term-ok" if any(k in low_t for k in ("✓", "pass", "ok", "fast", "saved", "fixed", "1.2 ms", "8.1 ms")) else "term-norm"
            )
            t_rows.append(
                f'<div class="term-ln {l_cls} drawer-row" data-p="{min(0.76, d_open_p + 0.05 + t_i * 0.09):.2f}">{html.escape(txt_s)}</div>'
            )
        drawer_body_html = f'<div class="term-wrap">{"".join(t_rows)}</div>'

    footer_pill = html.escape(str(vd.get("footer_pill") or ""))

    pad_x = int((42 if not is_wide else 88) * sc)
    hl_px = int((58 if not is_wide else 42) * sc)

    state_json = json.dumps({
        "steps": steps,
        "callout_line": c_line,
        "callout_p": c_dp,
        "drawer_open_p": d_open_p,
        "ripple_dur": tone_cfg["ripple_dur"],
        "line_count": len(code_lines),
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {width}px; height: {height}px; overflow: hidden;
    background: radial-gradient(circle at 50% 10%, {accent_hex}24 0%, #091124 46%, #040711 100%);
    color: #F8FAFC;
    font-family: "Nirmala UI", "Segoe UI", "Noto Sans Devanagari", system-ui, sans-serif;
  }}
  .grid-bg {{
    position: absolute; inset: 0; opacity: 0.14;
    background-image:
      linear-gradient(rgba(148,163,184,0.22) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148,163,184,0.22) 1px, transparent 1px);
    background-size: 36px 36px;
  }}
  .root {{
    position: relative; width: 100%; height: 100%; z-index: 2;
    display: flex; flex-direction: column;
    padding: {int(34*sc)}px {pad_x}px {int(42*sc)}px;
    gap: {int(16*sc)}px;
  }}
  .top-row {{ display: flex; align-items: center; justify-content: space-between; }}
  .wm-pill {{
    display: inline-flex; align-items: center;
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    background: rgba(15,23,42,0.92); border: 1.8px solid rgba(148,163,184,0.36);
    font-size: {int(23*sc)}px; font-weight: 800; color: #FFFFFF;
  }}
  .wm-pill .at {{ color: #FB923C; }}
  .hud-pill {{
    display: inline-flex; align-items: center; gap: 9px;
    padding: {int(8*sc)}px {int(20*sc)}px; border-radius: 999px;
    border: 1.8px solid {accent_hex}; background: rgba(15,23,42,0.90);
    color: {accent_hex}; font-size: {int(20*sc)}px; font-weight: 900; letter-spacing: 2px;
  }}
  .hud-pill .dot {{ width: 10px; height: 10px; border-radius: 50%; background: {accent_hex}; box-shadow: 0 0 12px {accent_hex}; }}
  .headline {{
    text-align: center; line-height: 1.12;
    font-size: {hl_px}px; font-weight: 900; margin: {int(2*sc)}px 0 {int(4*sc)}px;
    color: #FFFFFF; text-shadow: 0 6px 24px rgba(0,0,0,0.65);
  }}
  .headline .acc {{ color: {accent_hex}; }}

  /* IDE Window Shell */
  .ide-shell {{
    flex: 1; display: flex; flex-direction: column; position: relative;
    background: #0B1324; border: 2px solid rgba(148,163,184,0.34);
    border-radius: {int(24*sc)}px; overflow: hidden;
    box-shadow: 0 28px 80px rgba(0,0,0,0.72), 0 0 46px {accent_hex}1E;
  }}
  .ide-titlebar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: {int(15*sc)}px {int(22*sc)}px; background: #131E36;
    border-bottom: 1.8px solid rgba(148,163,184,0.22);
  }}
  .win-dots {{ display: flex; gap: 9px; align-items: center; }}
  .wdot {{ width: {int(15*sc)}px; height: {int(15*sc)}px; border-radius: 50%; }}
  .ide-tabs {{ display: flex; gap: 10px; align-items: center; }}
  .ide-tab {{
    padding: {int(7*sc)}px {int(16*sc)}px; border-radius: 10px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: {int(20*sc)}px; font-weight: 700; color: #94A3B8; background: rgba(30,41,59,0.65);
  }}
  .ide-tab.active {{
    color: #FFFFFF; background: #1E293B; border: 1.8px solid {accent_hex};
  }}
  .run-btn {{
    padding: {int(8*sc)}px {int(22*sc)}px; border-radius: 11px;
    background: rgba(52,211,153,0.22); border: 2px solid #34D399;
    color: #6EE7B7; font-size: {int(21*sc)}px; font-weight: 900; letter-spacing: 0.6px;
  }}
  .run-btn.clicked {{
    background: #34D399; color: #022C22; box-shadow: 0 0 30px rgba(52,211,153,0.85);
  }}

  /* Code Editor Surface (auto height — no empty void!) */
  .editor-area {{
    padding: {int(24*sc)}px {int(18*sc)}px {int(20*sc)}px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: {code_font_px}px; line-height: 1.56;
    display: flex; flex-direction: column; gap: {int(8*sc)}px;
    background: linear-gradient(180deg, #0B1324 0%, #0D162B 100%);
  }}
  .code-line {{
    display: flex; align-items: center; gap: {int(12*sc)}px;
    padding: {int(9*sc)}px {int(14*sc)}px; border-radius: 12px;
    border-left: 5px solid transparent; white-space: pre-wrap; word-break: break-word;
  }}
  .code-line.focus-err {{
    background: rgba(244,63,94,0.20); border-left-color: #F43F5E;
    box-shadow: inset 0 0 0 1.5px rgba(244,63,94,0.45);
  }}
  .code-line.focus-ok {{
    background: rgba(56,189,248,0.18); border-left-color: {accent_hex};
    box-shadow: inset 0 0 0 1.5px {accent_hex}66;
  }}
  .code-line.diff-del {{ background: rgba(244,63,94,0.20); border-left-color: #F43F5E; }}
  .code-line.diff-add {{ background: rgba(52,211,153,0.18); border-left-color: #34D399; }}
  .ln-num {{
    min-width: {int(40*sc)}px; text-align: right; color: #64748B;
    font-size: {int(code_font_px * 0.85)}px; font-weight: 700; user-select: none; flex-shrink: 0;
  }}
  .diff-sym {{ font-weight: 900; width: 18px; color: #FACC15; flex-shrink: 0; }}
  .ln-txt {{ flex: 1; color: #F1F5F9; font-weight: 600; }}
  .focus-pill {{
    padding: 3px 10px; border-radius: 8px; font-size: {int(15*sc)}px; font-weight: 900;
    font-family: "Nirmala UI", "Segoe UI", sans-serif; letter-spacing: 1px; flex-shrink: 0;
  }}
  .ft-err {{ background: #F43F5E; color: #FFFFFF; }}
  .ft-ok {{ background: {accent_hex}; color: #061224; }}
  .tok-kw {{ color: #D8B4FE; font-weight: 800; }}
  .tok-fn {{ color: #67E8F9; font-weight: 800; }}
  .tok-str {{ color: #6EE7B7; }}
  .tok-num {{ color: #FDE047; font-weight: 700; }}
  .tok-com {{ color: #94A3B8; font-style: italic; }}
  .tok-id {{ color: #F8FAFC; }}

  /* Context Callout Card (cleanly sits between code and drawer) */
  .callout-wrap {{
    padding: 0 {int(22*sc)}px {int(20*sc)}px;
    background: #0D162B;
    border-bottom: 1.5px solid rgba(148,163,184,0.16);
  }}
  .callout-bubble {{
    background: rgba(15, 25, 48, 0.98); border: 2.5px solid {c_hex};
    border-radius: 16px; padding: {int(16*sc)}px {int(22*sc)}px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.48), 0 0 24px {c_hex}2E;
  }}
  .callout-title {{
    font-size: {int(20*sc)}px; font-weight: 900; color: {c_hex};
    letter-spacing: 1.4px; margin-bottom: 5px;
  }}
  .callout-body {{
    font-size: {int(27*sc)}px; font-weight: 800; color: #FFFFFF; line-height: 1.3;
  }}

  /* Expanded Live Output Drawer (fills bottom half cleanly) */
  .output-drawer {{
    flex: 1; display: flex; flex-direction: column; justify-content: flex-start;
    background: #060B16; border-top: 2.5px solid {d_metric_hex};
    padding: {int(22*sc)}px {int(24*sc)}px {int(24*sc)}px;
    gap: {int(16*sc)}px;
  }}
  .drawer-head {{
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: {int(12*sc)}px; border-bottom: 1px solid rgba(148,163,184,0.20);
  }}
  .drawer-title {{
    display: flex; align-items: center; gap: 10px;
    font-size: {int(21*sc)}px; font-weight: 900; letter-spacing: 1.8px; color: #CBD5E1;
  }}
  .drawer-dot {{ width: 11px; height: 11px; border-radius: 50%; background: {d_metric_hex}; box-shadow: 0 0 12px {d_metric_hex}; }}
  .drawer-badge {{
    padding: {int(6*sc)}px {int(18*sc)}px; border-radius: 999px;
    background: {d_metric_hex}28; border: 2px solid {d_metric_hex};
    color: #FFFFFF; font-size: {int(20*sc)}px; font-weight: 900;
  }}
  .sql-tbl {{
    width: 100%; border-collapse: collapse;
    font-family: "Cascadia Code", "Consolas", monospace; font-size: {int(24*sc)}px;
  }}
  .sql-tbl th {{
    text-align: left; padding: {int(12*sc)}px {int(14*sc)}px; color: #38BDF8; font-weight: 900;
    border-bottom: 2px solid rgba(56,189,248,0.45); background: rgba(15,23,42,0.92);
  }}
  .sql-tbl td {{
    padding: {int(12*sc)}px {int(14*sc)}px; color: #F8FAFC; font-weight: 700;
    border-bottom: 1px solid rgba(148,163,184,0.22);
  }}
  .sql-tbl tbody tr:nth-child(odd) {{ background: rgba(30,41,59,0.34); }}
  .term-wrap {{
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: {int(24*sc)}px; line-height: 1.55; display: flex; flex-direction: column; gap: {int(12*sc)}px;
  }}
  .term-ln {{
    padding: {int(10*sc)}px {int(16*sc)}px; border-radius: 10px;
    background: rgba(15,23,42,0.72); border-left: 4px solid rgba(148,163,184,0.35);
  }}
  .term-err {{ color: #FDA4AF; border-left-color: #F43F5E; background: rgba(244,63,94,0.12); font-weight: 800; }}
  .term-ok {{ color: #6EE7B7; border-left-color: #34D399; background: rgba(52,211,153,0.12); font-weight: 800; }}
  .term-norm {{ color: #F1F5F9; font-weight: 700; }}

  .footer-pill {{
    align-self: center; padding: {int(12*sc)}px {int(32*sc)}px; border-radius: 14px;
    background: rgba(250,204,21,0.14); border: 2.2px solid #FACC15;
    color: #FEF08A; font-size: {int(24*sc)}px; font-weight: 900; text-align: center;
  }}

  /* Mouse Pointer & Dual Click Ripple Overlay */
  .ripple-ring {{
    position: absolute; border-radius: 50%; pointer-events: none; z-index: 25;
    border: 4px solid {accent_hex}; background: {accent_hex}28;
    box-shadow: 0 0 26px {accent_hex};
    transform: translate(-50%, -50%); opacity: 0;
  }}
  .mouse-cursor {{
    position: absolute; width: {int(46*sc)}px; height: {int(46*sc)}px; z-index: 30;
    pointer-events: none; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.85));
  }}
</style>
</head>
<body>
  <div class="grid-bg"></div>
  <div class="root">
    <div class="top-row">
      <div class="wm-pill">{wm_html}</div>
      <div class="hud-pill"><span class="dot"></span>{hud_pill}</div>
    </div>
    <div class="headline">{h_white} <span class="acc">{h_accent}</span></div>

    <div class="ide-shell" id="ideShell">
      <div class="ide-titlebar">
        <div class="win-dots">
          <div class="wdot" style="background:#F43F5E"></div>
          <div class="wdot" style="background:#FBBF24"></div>
          <div class="wdot" style="background:#34D399"></div>
        </div>
        <div class="ide-tabs">
          <div class="ide-tab active">{file_name}</div>
          <div class="ide-tab">{tab_secondary}</div>
        </div>
        <div class="run-btn" id="runBtn">▶ Run</div>
      </div>

      <div class="editor-area" id="editorArea">
        {"".join(code_rows_html)}
      </div>

      <div class="callout-wrap">
        <div class="callout-bubble" id="calloutBubble">
          <div class="callout-title">↳ LINE {c_line:02d} · {c_title}</div>
          <div class="callout-body">{c_body}</div>
        </div>
      </div>

      <div class="output-drawer" id="outputDrawer">
        <div class="drawer-head">
          <div class="drawer-title"><span class="drawer-dot"></span>{d_title}</div>
          <div class="drawer-badge">{d_metric}</div>
        </div>
        {drawer_body_html}
      </div>
    </div>
    {f'<div class="footer-pill" id="footerPill">{footer_pill}</div>' if footer_pill else ''}
  </div>

  <div class="ripple-ring" id="ripple1"></div>
  <div class="ripple-ring" id="ripple2"></div>
  <svg class="mouse-cursor" id="mouseCursor" viewBox="0 0 28 28">
    <path d="M4 3 L22 14 L13 16 L17 24 L13.5 25.5 L9.5 17.5 L4 22 Z"
          fill="#FFFFFF" stroke="#0B1324" stroke-width="2.4" stroke-linejoin="round"/>
  </svg>

  <script>
    const STATE = {state_json};

    function getTargetXY(step) {{
      const shell = document.getElementById('ideShell').getBoundingClientRect();
      if (step.target === 'run_btn') {{
        const rb = document.getElementById('runBtn').getBoundingClientRect();
        return [rb.left + rb.width * 0.5, rb.top + rb.height * 0.55];
      }}
      const lnNum = Math.max(1, Math.min(STATE.line_count, Number(step.line || STATE.callout_line || 1)));
      const el = document.getElementById('line_' + lnNum);
      if (el) {{
        const r = el.getBoundingClientRect();
        return [r.left + Math.min(r.width * 0.52, 420), r.top + r.height * 0.55];
      }}
      return [shell.left + shell.width * 0.5, shell.top + shell.height * 0.35];
    }}

    window.__setStudioProgress = function(wp, lp) {{
      const p = Math.max(0, Math.min(1, Number(wp) || 0));
      const t = Math.max(0, Math.min(1, Number(lp !== undefined ? lp : p) || 0));

      const cb = document.getElementById('calloutBubble');
      const cf = Math.max(0, Math.min(1, (p - (STATE.callout_p || 0.12) + 0.08) / 0.12));
      cb.style.opacity = (0.35 + 0.65 * cf).toFixed(3);
      cb.style.transform = `translateY(${{(8 * (1 - cf)).toFixed(1)}}px) scale(${{(0.97 + 0.03 * cf).toFixed(3)}})`;

      const dr = document.getElementById('outputDrawer');
      const dOpen = Math.max(0, Math.min(1, (t - (STATE.drawer_open_p || 0.28) + 0.14) / 0.18));
      dr.style.opacity = (0.48 + 0.52 * dOpen).toFixed(3);
      dr.style.transform = `translateY(${{(16 * (1 - dOpen)).toFixed(1)}}px)`;

      document.querySelectorAll('.drawer-row').forEach(el => {{
        const dp = parseFloat(el.dataset.p || '0.35');
        const rf = Math.max(0, Math.min(1, (p - dp + 0.08) / 0.12));
        el.style.opacity = rf.toFixed(3);
        el.style.transform = `translateY(${{(6 * (1 - rf)).toFixed(1)}}px)`;
      }});

      const fp = document.getElementById('footerPill');
      if (fp) {{
        const ff = Math.max(0, Math.min(1, (p - 0.62) / 0.14));
        fp.style.opacity = ff.toFixed(3);
      }}

      const steps = STATE.steps || [];
      if (steps.length > 0) {{
        let activeIdx = 0;
        for (let i = 0; i < steps.length; i++) {{
          if (t >= Number(steps[i].p || 0)) activeIdx = i;
        }}
        const curStep = steps[activeIdx];
        const prevStep = activeIdx > 0 ? steps[activeIdx - 1] : curStep;
        const [x0, y0] = getTargetXY(prevStep);
        const [x1, y1] = getTargetXY(curStep);
        const sp = Number(curStep.p || 0);
        const glide = Math.max(0, Math.min(1, (t - sp + 0.10) / 0.14));
        const ease = glide < 0.5 ? 2 * glide * glide : 1 - Math.pow(-2 * glide + 2, 2) / 2;
        const cx = x0 + (x1 - x0) * ease;
        const cy = y0 + (y1 - y0) * ease;

        const cursorEl = document.getElementById('mouseCursor');
        cursorEl.style.left = cx.toFixed(1) + 'px';
        cursorEl.style.top = cy.toFixed(1) + 'px';

        const runBtn = document.getElementById('runBtn');
        if (curStep.target === 'run_btn' && t >= sp) {{
          runBtn.classList.add('clicked');
        }} else {{
          runBtn.classList.remove('clicked');
        }}

        const rDur = Number(STATE.ripple_dur || 0.36);
        const age = t - sp;
        const r1 = document.getElementById('ripple1');
        const r2 = document.getElementById('ripple2');
        if (curStep.click !== false && age >= 0 && age <= rDur) {{
          const rp = age / rDur;
          const sz1 = 22 + rp * 116;
          const sz2 = 12 + rp * 70;
          r1.style.left = x1.toFixed(1) + 'px';
          r1.style.top = y1.toFixed(1) + 'px';
          r1.style.width = sz1.toFixed(1) + 'px';
          r1.style.height = sz1.toFixed(1) + 'px';
          r1.style.opacity = (1 - rp).toFixed(3);

          r2.style.left = x1.toFixed(1) + 'px';
          r2.style.top = y1.toFixed(1) + 'px';
          r2.style.width = sz2.toFixed(1) + 'px';
          r2.style.height = sz2.toFixed(1) + 'px';
          r2.style.opacity = ((1 - rp) * 0.9).toFixed(3);
        }} else {{
          r1.style.opacity = '0';
          r2.style.opacity = '0';
        }}
      }}
    }};
    window.__setStudioProgress(1.0, 1.0);
  </script>
</body>
</html>"""


def render_v3_ide_scene_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    format_ratio: str = "9:16",
    scene_words: Optional[List[Dict[str, Any]]] = None,
    tone: str = "auto_2026_director",
    fps: int = VIDEO_FPS,
    res_scale: float = 1.0,
    frame_ext: str = "jpg",
) -> Path:
    """Renders all FPS frames for a Studio V3 Live IDE & SQL/Python Simulator scene."""
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

    html_doc = _build_ide_html(scene, w, h, tone=tone)
    from core.web_generative_engine import capture_studio_playwright_frames
    if capture_studio_playwright_frames(
        html_doc, out_dir, w, h, duration, scene, scene_words,
        tone=tone, fps=fps, res_scale=res_scale, frame_ext=frame_ext, arg_order="wp_lp",
    ):
        return out_dir

    # Graceful headless Pillow fallback
    from PIL import Image, ImageDraw
    vd = dict(scene.get("visual_data") or {})
    img = Image.new("RGB", (w, h), (11, 18, 32))
    draw = ImageDraw.Draw(img)
    draw.rectangle([48, 220, w - 48, h - 220], outline=(56, 189, 248), width=3)
    draw.text((76, 110), f"{vd.get('headline_white','')} {vd.get('headline_accent','')}", fill=(248, 250, 252))
    for i, ln in enumerate(list(vd.get("code_lines") or [])[:8]):
        draw.text((84, 280 + i * 44), f"{i+1:02d}  {str(ln)[:54]}", fill=(226, 232, 240))
    for f in range(total_frames):
        img.save(out_dir / f"frame_{f:04d}.jpg", quality=90)
    return out_dir
