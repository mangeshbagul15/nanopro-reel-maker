"""
Domain-Specialist Dynamic Animated Engines & 2026+ Visual Suite (30 Engines).

Covers all 17+ IT engineering domains (Python Stack/Heap, DSA Dry-Run, Event Loop,
SQL Live JOINs, Data Notebooks, Racing Charts, Snowflake Partition Pruning,
AWS/Azure Cloud Infra Builder, Neural Backprop, Sliding Convolution, 3B1B Vector Space,
AI Thinking & Multi-Agent Swarm, Bank IT Core Ledger + HSM + DR Failover,
32-bit Protocol Bitfields, World Globe Packet Arcs, Security Replay,
Excalidraw Sketch, 2026 AI IDE, Synced Diagram+Code, SRE 3-Panel Console,
macOS Terminal Cast, DB Cutover, DevTools, Live Race, CPU Clock, Apple Bento,
Media NLE Tracks, Scrollytelling).
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple

STAGE_X0, STAGE_Y0, STAGE_X1, STAGE_Y1 = 64, 328, 1016, 1406
STAGE_W = STAGE_X1 - STAGE_X0
STAGE_H = STAGE_Y1 - STAGE_Y0

DOMAIN_SPECIALIST_LAYOUTS: Tuple[str, ...] = (
    # #20 Python & Algorithms
    "python_stack_heap_live",
    "algorithm_dry_run_debugger",
    "event_loop_visualizer",
    # #21 SQL Live Joins
    "sql_live_join_venn_rows",
    # #22 Data Analyst, BI & Data Science
    "notebook_interactive_cell",
    "racing_timeseries_chart",
    # #23 Snowflake & Pipelines
    "snowflake_micro_partition_pruner",
    # #24 AWS & Azure Cloud Infrastructure
    "cloud_infra_zone_builder",
    # #25 AI, ML, Deep Learning & Agents
    "neural_forward_backprop_flow",
    "sliding_window_convolution_grid",
    "vector_space_3b1b",
    "ai_thinking_tool_trace",
    "multi_agent_swimlane_trace",
    # #26 Bank IT Infrastructure & Projects
    "banking_ledger_settlement_rails",
    "dr_active_active_failover",
    # #27 Networking & Security
    "bitfield_protocol_grid",
    "geo_world_packet_arcs",
    "security_attack_defense_replay",
    # #28 Modern 2026 Dev / IDE / SRE
    "excalidraw_sketch_board",
    "ide_split_workbench",
    "dual_sync_diagram_plus_code",
    "live_sre_observability_console",
    "mac_terminal_stream_cast",
    "db_live_cutover_migration",
    # #29 Specialized CS Extras
    "browser_devtools_studio",
    "live_benchmark_race_track",
    "cpu_pipeline_clock_cycle",
    "bento_apple_keynote",
    "media_streaming_tracks_nle",
    "vertical_scrollytelling_track",
)

DOMAIN_SPECIALIST_DESCRIPTIONS: Dict[str, str] = {
    "python_stack_heap_live": "python stack frame heap object pointer refcount gil gc memory visualizer",
    "algorithm_dry_run_debugger": "algorithm dsa code step cursor variable watch table pointers trace",
    "event_loop_visualizer": "python asyncio javascript event loop call stack microtask queue async",
    "sql_live_join_venn_rows": "sql inner left right full join table row match merge venn database",
    "notebook_interactive_cell": "jupyter notebook pandas numpy duckdb dataframe analytics python cell chart",
    "racing_timeseries_chart": "data visualization racing bar time series evolution cohort trend bi",
    "snowflake_micro_partition_pruner": "snowflake micro partition pruning virtual warehouse clustering olap bi",
    "cloud_infra_zone_builder": "aws azure cloud vpc vnet availability zone subnet aks eks s3 adls infra",
    "neural_forward_backprop_flow": "pytorch deep learning neural network forward pass loss backprop weights",
    "sliding_window_convolution_grid": "cnn convolution matrix sliding window kernel filter computer vision ml",
    "vector_space_3b1b": "embedding vector cosine similarity dot product 3blue1brown math projection",
    "ai_thinking_tool_trace": "ai reasoning thinking tool call llm agent prompt response verification",
    "multi_agent_swimlane_trace": "multi agent swarm coordinator researcher coder verifier parallel timeline",
    "banking_ledger_settlement_rails": "bank banking core cbs hsm pin vault fraud aml double entry ledger upi swift",
    "dr_active_active_failover": "bank disaster recovery dr active active primary dc failover rpo rto vault",
    "bitfield_protocol_grid": "networking tcp ipv6 quic jwt packet header 32bit frame bitfield bytes",
    "geo_world_packet_arcs": "global multi region world map cdn dns anycast bgp submarine packet arcs",
    "security_attack_defense_replay": "security waf mtls firewall ddos sqli attack shield token defense",
    "excalidraw_sketch_board": "excalidraw hand drawn whiteboard sketch architecture bytebytego diagram",
    "ide_split_workbench": "vscode cursor ide file tree code diff editor terminal tests software development",
    "dual_sync_diagram_plus_code": "synced architecture diagram live code execution line highlight flow",
    "live_sre_observability_console": "grafana datadog sre observability p99 spike otel trace waterfall pod logs",
    "mac_terminal_stream_cast": "macos terminal zsh cli kubectl docker curl streaming json output",
    "db_live_cutover_migration": "zero downtime database schema migration shadow table dual write cutover",
    "browser_devtools_studio": "chrome devtools dom elements network waterfall paint fps web performance",
    "live_benchmark_race_track": "benchmark race slow sync blocking vs fast async throughput latency",
    "cpu_pipeline_clock_cycle": "cpu instruction pipeline clock cycle fetch decode execute hazard hardware",
    "bento_apple_keynote": "bento grid apple keynote product feature metric kpi dashboard showcase",
    "media_streaming_tracks_nle": "ffmpeg hls webrtc video audio subtitle streaming chunk tracks timeline",
    "vertical_scrollytelling_track": "scrollytelling vertical chapter timeline camera parallax architecture journey",
}

_CYCLE = ("cyan", "purple", "emerald", "amber", "rose")


def _c01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _items_list(data: Dict[str, Any], fallbacks: List[Tuple[str, str]], limit: int = 5) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for k in ("nodes", "items", "steps", "stages", "bullets", "spans"):
        seq = data.get(k)
        if isinstance(seq, list) and seq:
            for idx, it in enumerate(seq[:limit]):
                if isinstance(it, dict):
                    nm = str(it.get("label") or it.get("name") or it.get("title") or "").strip()
                    sb = str(it.get("sub") or it.get("desc") or it.get("role") or "").strip()
                    if nm:
                        out.append({"name": nm, "sub": sb})
                elif isinstance(it, str) and it.strip():
                    out.append({"name": it.strip(), "sub": ""})
            if out:
                break
    for nm, sb in fallbacks:
        if len(out) >= limit:
            break
        if not any(nm.lower() == x["name"].lower() for x in out):
            out.append({"name": nm, "sub": sb})
    return out[:limit]


def _draw_top_panel(stage, box, col, alpha: float, title: str, helpers: Dict[str, Any], mono: bool = False) -> None:
    stage.draw_glass_card(box, radius=22, accent_col=col, alpha_mul=alpha, elev=10)
    if title:
        f = helpers["_get_font"](20, bold=True, mono=mono)
        stage.draw.text((box[0] + 24, box[1] + 20), title[:48], font=f, fill=helpers["_with_alpha"](col, alpha))


# -------------------------------------------------------------------------
# #20 PYTHON & ALGORITHMS
# -------------------------------------------------------------------------
def _render_python_stack_heap(stage, d, progress, world, h):
    gf, gw, wa, sg = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"], h["_spring_gate"]
    stacks = [("frame: main()", "rows = load()"), ("var: users_ref", "ptr -> 0x7F04"), ("var: cache_ref", "ptr -> 0x7F04"), ("GIL / GC Lock", "refcount == 2 -> 1")]
    heaps = [("0x7F04 list[int]", "refs: 2 | [10, 20, 30]"), ("0x8A12 dict", "refs: 1 | {'k': 'v'}"), ("GC Sweep", "ref == 0 -> freed!")]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, 510, STAGE_Y1 - 60), world["cyan"], 1.0, "CALL STACK (REFERENCES)", h, mono=True)
    _draw_top_panel(stage, (550, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 60), world["emerald"], 1.0, "HEAP OBJECTS (PyObject)", h, mono=True)
    for i, (sn, ss) in enumerate(stacks):
        g = h["_ease_out_cubic"](sg(progress, i, 4, 0.24))
        if g <= 0.02:
            continue
        y0 = STAGE_Y0 + 82 + i * 240
        act = (int(_c01(progress) * 4) == i)
        stage.draw_glass_card((STAGE_X0 + 20, y0, 488, y0 + 190), radius=18, accent_col=world["cyan"], alpha_mul=g, active=act, label=sn)
        gw(stage.draw, (STAGE_X0 + 38, y0 + 30), sn, gf(23, bold=True, mono=True), wa(world["text"], g), 410)
        gw(stage.draw, (STAGE_X0 + 38, y0 + 96), ss, gf(21, mono=True), wa(world["cyan"], g), 410)
    for j, (hn, hs) in enumerate(heaps):
        g = h["_ease_out_cubic"](sg(progress, j + 1, 4, 0.24))
        if g <= 0.02:
            continue
        y0 = STAGE_Y0 + 115 + j * 310
        col = world["rose"] if j == 2 else world["emerald"]
        stage.draw_glass_card((572, y0, STAGE_X1 - 22, y0 + 230), radius=18, accent_col=col, alpha_mul=g, active=(j == 0), label=hn)
        gw(stage.draw, (592, y0 + 36), hn, gf(23, bold=True, mono=True), wa(world["text"], g), 380)
        gw(stage.draw, (592, y0 + 108), hs, gf(21, mono=True), wa(col, g), 380)
    g_lnk = _c01((progress - 0.22) / 0.35)
    if g_lnk > 0.05:
        h["_draw_bezier_comet"](stage, (492, STAGE_Y0 + 410), (568, STAGE_Y0 + 230), world["amber"], reveal=g_lnk, progress=progress, label="ptr", world=world)
        h["_draw_bezier_comet"](stage, (492, STAGE_Y0 + 650), (568, STAGE_Y0 + 260), world["cyan"], reveal=g_lnk, progress=progress, phase=0.3, world=world)


def _render_algo_dry_run(stage, d, progress, world, h):
    gf, wa, sg = h["_get_font"], h["_with_alpha"], h["_spring_gate"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 520), world["cyan"], 1.0, "STEP-BY-STEP CODE EXECUTION", h, mono=True)
    code_lines = str(d.get("code_snippet") or "left, right = 0, len(arr) - 1\nwhile left <= right:\n  mid = (left + right) // 2\n  if arr[mid] == target: return mid\n  left = mid + 1").splitlines()[:5]
    active_ln = min(len(code_lines) - 1, int(_c01(progress) * len(code_lines)))
    for i, ln in enumerate(code_lines):
        cy = STAGE_Y0 + 78 + i * 78
        is_act = (i == active_ln)
        if is_act:
            stage.draw.rounded_rectangle((STAGE_X0 + 22, cy - 8, STAGE_X1 - 22, cy + 50), radius=12, fill=wa((*world["amber"][:3], 50), 1.0), outline=world["amber"], width=2)
        pref = "-> " if is_act else "   "
        stage.draw.text((STAGE_X0 + 36, cy + 4), f"{pref}{ln[:46]}", font=gf(23, bold=is_act, mono=True), fill=world["amber"] if is_act else world["text"])

    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 550, STAGE_X1, STAGE_Y1 - 40), world["emerald"], 1.0, "LIVE VARIABLE WATCH & ARRAY POINTERS", h, mono=True)
    arr = [4, 11, 18, 27, 39, 52]
    step_states = [(0, 5, 2), (3, 5, 4), (3, 3, 3)]
    st_idx = min(len(step_states) - 1, int(_c01(progress) * len(step_states)))
    lv, rv, mv = step_states[st_idx]
    cw = 132
    for idx, val in enumerate(arr):
        cx = STAGE_X0 + 48 + idx * (cw + 12)
        cy = STAGE_Y0 + 670
        col = world["emerald"] if idx == mv else (world["cyan"] if lv <= idx <= rv else world["border"])
        stage.draw_glass_card((cx, cy, cx + cw, cy + 128), radius=16, accent_col=col, active=(idx == mv), label=str(val))
        stage.draw.text((cx + 42, cy + 42), str(val), font=gf(34, bold=True, mono=True), fill=world["text"])
        tags = [t for t, ptr in (("L", lv), ("M", mv), ("R", rv)) if ptr == idx]
        if tags:
            stage.draw_pill(cx + cw // 2, cy - 28, "/".join(tags), (*col[:3], 48), col, border_col=col, font=gf(19, bold=True, mono=True))
    vars_txt = f"STEP {st_idx + 1}/3   •   left={lv}   mid={mv}   right={rv}   arr[mid]={arr[mv]}"
    stage.draw_pill(540, STAGE_Y0 + 960, vars_txt, (*world["emerald"][:3], 36), world["emerald"], border_col=world["emerald"], font=gf(24, bold=True, mono=True))


def _render_event_loop(stage, d, progress, world, h):
    gf, gw, wa, sg = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"], h["_spring_gate"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, 515, STAGE_Y0 + 520), world["cyan"], 1.0, "CALL STACK", h, mono=True)
    _draw_top_panel(stage, (565, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 520), world["purple"], 1.0, "ASYNC I/O POOL", h, mono=True)
    for i, nm in enumerate(["handle_req()", "await fetch_db()", "parse_json()"]):
        g = h["_ease_out_cubic"](sg(progress, i, 4, 0.24))
        if g > 0.03:
            y0 = STAGE_Y0 + 92 + (2 - i) * 124
            stage.draw_glass_card((STAGE_X0 + 24, y0, 490, y0 + 96), radius=14, accent_col=world["cyan"], alpha_mul=g, active=(i == 2), label=nm)
            stage.draw.text((STAGE_X0 + 44, y0 + 28), nm, font=gf(23, bold=True, mono=True), fill=wa(world["text"], g))
    for i, nm in enumerate(["OS epoll Socket #4", "Timer (15ms)"]):
        g = h["_ease_out_cubic"](sg(progress, i + 1, 4, 0.24))
        if g > 0.03:
            y0 = STAGE_Y0 + 110 + i * 165
            stage.draw_glass_card((588, y0, STAGE_X1 - 24, y0 + 125), radius=16, accent_col=world["purple"], alpha_mul=g, label=nm)
            stage.draw.text((612, y0 + 42), nm, font=gf(23, bold=True, mono=True), fill=wa(world["text"], g))

    # Spinning Event Loop Hub in Center
    cx, cy, rad = 540, STAGE_Y0 + 675, 118
    stage.draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=world["amber"], width=6)
    ang = progress * math.pi * 4.0
    dx, dy = int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))
    stage.draw.ellipse((dx - 16, dy - 16, dx + 16, dy + 16), fill=world["emerald"], outline=world["text"], width=3)
    stage.draw.text((cx - 72, cy - 18), "EVENT LOOP", font=gf(22, bold=True, mono=True), fill=world["amber"])

    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 830, STAGE_X1, STAGE_Y1 - 40), world["emerald"], 1.0, "MICROTASK & READY QUEUE", h, mono=True)
    for k, qnm in enumerate(["resolve(rows)", "Promise.then()", "emit_metrics()"]):
        g = h["_ease_out_cubic"](sg(progress, k + 1, 4, 0.24))
        if g > 0.03:
            qx = STAGE_X0 + 26 + k * 298
            stage.draw_glass_card((qx, STAGE_Y0 + 910, qx + 280, STAGE_Y1 - 76), radius=16, accent_col=world["emerald"], alpha_mul=g, active=(k == 0), label=qnm)
            gw(stage.draw, (qx + 16, STAGE_Y0 + 985), qnm, gf(21, bold=True, mono=True), wa(world["text"], g), 248, align="center")


# -------------------------------------------------------------------------
# #21 SQL LIVE JOIN
# -------------------------------------------------------------------------
def _render_sql_live_join(stage, d, progress, world, h):
    gf, wa, sg = h["_get_font"], h["_with_alpha"], h["_spring_gate"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, 515, STAGE_Y0 + 500), world["cyan"], 1.0, "LEFT: users (id, name)", h, mono=True)
    _draw_top_panel(stage, (565, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 500), world["purple"], 1.0, "RIGHT: orders (uid, total)", h, mono=True)
    left_r = [("id=1", "Ananya", True), ("id=2", "Rohan", True), ("id=3", "Kabir", False)]
    right_r = [("uid=1", "₹4,200", True), ("uid=2", "₹1,850", True), ("uid=9", "₹990", False)]
    for i, (k, v, m) in enumerate(left_r):
        y0 = STAGE_Y0 + 88 + i * 124
        col = world["emerald"] if (m and progress > 0.35) else world["cyan"]
        stage.draw_glass_card((STAGE_X0 + 22, y0, 492, y0 + 100), radius=14, accent_col=col, active=(m and progress > 0.35), label=f"{k} {v}")
        stage.draw.text((STAGE_X0 + 44, y0 + 32), f"{k}  |  {v}", font=gf(24, bold=True, mono=True), fill=world["text"])
    for i, (k, v, m) in enumerate(right_r):
        y0 = STAGE_Y0 + 88 + i * 124
        col = world["emerald"] if (m and progress > 0.35) else world["purple"]
        stage.draw_glass_card((588, y0, STAGE_X1 - 22, y0 + 100), radius=14, accent_col=col, active=(m and progress > 0.35), label=f"{k} {v}")
        stage.draw.text((610, y0 + 32), f"{k}  |  {v}", font=gf(24, bold=True, mono=True), fill=world["text"])

    g_match = _c01((progress - 0.25) / 0.35)
    if g_match > 0.05:
        h["_draw_bezier_comet"](stage, (496, STAGE_Y0 + 138), (584, STAGE_Y0 + 138), world["emerald"], reveal=g_match, progress=progress, label="JOIN", world=world)
        h["_draw_bezier_comet"](stage, (496, STAGE_Y0 + 262), (584, STAGE_Y0 + 262), world["emerald"], reveal=g_match, progress=progress, phase=0.25, world=world)

    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 545, STAGE_X1, STAGE_Y1 - 40), world["emerald"], 1.0, "JOIN OUTPUT (MATCHED ROWS MERGED)", h, mono=True)
    q_txt = str(d.get("query") or d.get("code_snippet") or "SELECT u.id, u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.uid;")
    stage.draw.text((STAGE_X0 + 28, STAGE_Y0 + 615), q_txt[:70], font=gf(19, bold=True, mono=True), fill=world["amber"])
    out_rows = [("1", "Ananya", "₹4,200", "MATCH ✅"), ("2", "Rohan", "₹1,850", "MATCH ✅")]
    for i, (oid, onm, tot, stg) in enumerate(out_rows):
        g = h["_ease_out_cubic"](sg(progress, i + 1, 3, 0.28))
        if g > 0.03:
            ry = STAGE_Y0 + 700 + i * 165
            stage.draw_glass_card((STAGE_X0 + 28, ry, STAGE_X1 - 28, ry + 130), radius=16, accent_col=world["emerald"], alpha_mul=g, active=True, label=onm)
            stage.draw.text((STAGE_X0 + 56, ry + 42), f"{oid}   •   {onm}   •   {tot}   —   {stg}", font=gf(27, bold=True, mono=True), fill=wa(world["text"], g))


# -------------------------------------------------------------------------
# #22 DATA NOTEBOOK & RACING TIME SERIES
# -------------------------------------------------------------------------
def _render_notebook_cell(stage, d, progress, world, h):
    gf, wa, sg = h["_get_font"], h["_with_alpha"], h["_spring_gate"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 340), world["cyan"], 1.0, "In [1]: pandas / duckdb live query", h, mono=True)
    q = str(d.get("query") or d.get("code_snippet") or "df.groupby('tier').agg(p50_ms=('latency', 'median'))")[:110]
    h["_draw_wrapped_text"](stage.draw, (STAGE_X0 + 28, STAGE_Y0 + 88), q, gf(25, bold=True, mono=True), world["text"], STAGE_W - 56)

    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 375, STAGE_X1, STAGE_Y1 - 40), world["emerald"], 1.0, "Out [1]: Vectorized Dataframe & Gain", h, mono=True)
    rows = [("Bronze Raw", "124K rows", 0.90, "rose"), ("Silver Clean", "18.4K rows", 0.36, "amber"), ("Gold Lakehouse", "640 rows", 0.14, "emerald")]
    for i, (nm, cnt, ratio, ck) in enumerate(rows):
        g = h["_ease_out_cubic"](sg(progress, i, 3, 0.25))
        if g <= 0.02:
            continue
        ry = STAGE_Y0 + 460 + i * 168
        col = world[ck]
        stage.draw_glass_card((STAGE_X0 + 26, ry, STAGE_X1 - 26, ry + 136), radius=16, accent_col=col, alpha_mul=g, active=(i == 2), label=nm)
        stage.draw.text((STAGE_X0 + 50, ry + 26), f"{nm}   ({cnt})", font=gf(26, bold=True), fill=wa(world["text"], g))
        bw = max(36, int(740 * ratio * g))
        stage.draw.rounded_rectangle((STAGE_X0 + 50, ry + 78, STAGE_X0 + 50 + bw, ry + 108), radius=10, fill=wa(col, g))
    gf_v = h["_footer_gate"](progress)
    if gf_v > 0.03:
        stage.draw_pill(540, STAGE_Y1 - 105, "Vectorized Parquet scan reduced I/O by 96%", (*world["emerald"][:3], 40), world["emerald"], border_col=world["emerald"], font=gf(23, bold=True), alpha_mul=gf_v)


def _render_racing_chart(stage, d, progress, world, h):
    gf, wa = h["_get_font"], h["_with_alpha"]
    items = _items_list(d, [("DuckDB Vector", "14ms"), ("Spark Photon", "48ms"), ("Snowflake WH", "72ms"), ("Legacy Hive", "840ms")], 4)
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, f"TIME-SERIES BENCHMARK • STEP {1 + int(_c01(progress) * 4)}/5", h, mono=True)
    for i, it in enumerate(items):
        col = world[_CYCLE[i % len(_CYCLE)]]
        ry = STAGE_Y0 + 110 + i * 240
        stage.draw_glass_card((STAGE_X0 + 28, ry, STAGE_X1 - 28, ry + 195), radius=18, accent_col=col, active=(i == 0), label=it["name"])
        stage.draw.text((STAGE_X0 + 52, ry + 26), f"#{i + 1}  {it['name'][:26]}", font=gf(28, bold=True), fill=world["text"])
        frac = max(0.18, (0.95 - i * 0.21) * _c01(0.25 + progress * 0.75))
        bw = int((STAGE_W - 140) * frac)
        stage.draw.rounded_rectangle((STAGE_X0 + 52, ry + 96, STAGE_X0 + 52 + bw, ry + 148), radius=14, fill=col)
        stage.draw.text((STAGE_X0 + 68, ry + 105), it.get("sub") or f"{int(frac * 100)}x", font=gf(23, bold=True, mono=True), fill=(15, 23, 42))


# -------------------------------------------------------------------------
# #23 SNOWFLAKE MICRO-PARTITION PRUNER
# -------------------------------------------------------------------------
def _render_snowflake_pruner(stage, d, progress, world, h):
    gf, wa = h["_get_font"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 780), world["cyan"], 1.0, "MICRO-PARTITION STORAGE (24 FILES • 16MB EACH)", h, mono=True)
    active_ids = {2, 3, 8, 9}
    pruned = (progress > 0.35)
    cw, ch = 132, 128
    for idx in range(24):
        r, c = divmod(idx, 6)
        px = STAGE_X0 + 36 + c * (cw + 16)
        py = STAGE_Y0 + 92 + r * (ch + 16)
        is_hit = idx in active_ids
        col = world["emerald"] if (pruned and is_hit) else (world["border"] if pruned else world["cyan"])
        alpha = 1.0 if (not pruned or is_hit) else 0.24
        stage.draw_glass_card((px, py, px + cw, py + ch), radius=14, accent_col=col, alpha_mul=alpha, active=(pruned and is_hit))
        stage.draw.text((px + 34, py + 44), f"P{idx + 1:02d}", font=gf(25, bold=True, mono=True), fill=wa(world["text"], alpha))
    st_lbl = "PRUNED: 20 SKIPPED  |  SCANNED: 4 PARTITIONS ✅" if pruned else "SCANNING FULL CLUSTER METADATA..."
    stage.draw_pill(540, STAGE_Y0 + 735, st_lbl, (*world["emerald"][:3], 42), world["emerald"] if pruned else world["cyan"], border_col=world["emerald"] if pruned else world["cyan"], font=gf(21, bold=True, mono=True))

    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 810, STAGE_X1, STAGE_Y1 - 40), world["amber"], 1.0, "VIRTUAL WAREHOUSE AUTO-SCALE (XS -> M -> XL)", h, mono=True)
    tiers = [("XS (1 node)", False), ("M (4 nodes)", progress > 0.5), ("XL (16 nodes)", progress > 0.8)]
    for i, (tnm, on) in enumerate(tiers):
        tx = STAGE_X0 + 30 + i * 304
        col = world["emerald"] if on else world["amber"]
        stage.draw_glass_card((tx, STAGE_Y0 + 890, tx + 282, STAGE_Y1 - 80), radius=18, accent_col=col, active=on, label=tnm)
        stage.draw.text((tx + 28, STAGE_Y0 + 975), tnm, font=gf(24, bold=True, mono=True), fill=world["text"])
        stage.draw.text((tx + 28, STAGE_Y0 + 1030), "ACTIVE" if on else "SUSPENDED", font=gf(20, bold=True, mono=True), fill=col)


# -------------------------------------------------------------------------
# #24 AWS / AZURE CLOUD INFRA BUILDER
# -------------------------------------------------------------------------
def _render_cloud_infra_builder(stage, d, progress, world, h):
    gf, gw, wa, sg = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"], h["_spring_gate"]
    ctx = f"{d.get('title', '')}".lower()
    is_az = "azure" in ctx or "aks" in ctx or "synapse" in ctx or "adls" in ctx
    reg_lbl = "AZURE REGION (CENTRAL INDIA) • VNET 10.2.0.0/16" if is_az else "AWS REGION (AP-SOUTH-1) • VPC 10.0.0.0/16"
    layers = [
        ("EDGE INGRESS", "Front Door / WAF + DDoS" if is_az else "CloudFront + ALB Ingress", "cyan"),
        ("COMPUTE AZ-1 & AZ-2", "AKS Pod Mesh + AutoScale" if is_az else "EKS Worker Pods + Lambda", "purple"),
        ("PRIVATE DATA PLANE", "ADLS Gen2 + Synapse SQL" if is_az else "S3 Lakehouse + Redshift", "emerald"),
    ]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, reg_lbl, h, mono=True)
    for i, (tit, sub, ck) in enumerate(layers):
        g = h["_ease_out_cubic"](sg(progress, i, 3, 0.26))
        if g <= 0.02:
            continue
        col = world[ck]
        y0 = STAGE_Y0 + 94 + i * 335
        stage.draw_glass_card((STAGE_X0 + 28, y0, STAGE_X1 - 28, y0 + 275), radius=22, accent_col=col, alpha_mul=g, active=(int(_c01(progress) * 3) == i), label=tit)
        stage.draw_pill(STAGE_X0 + 170, y0 + 46, tit, (*col[:3], 42), col, border_col=col, font=gf(19, bold=True, mono=True), alpha_mul=g)
        gw(stage.draw, (STAGE_X0 + 46, y0 + 108), sub, gf(30, bold=True), wa(world["text"], g), STAGE_W - 92)
        gw(stage.draw, (STAGE_X0 + 46, y0 + 176), "Private Endpoint + KeyVault KMS + Multi-AZ Sync" if is_az else "PrivateLink + KMS + Multi-AZ Replication", gf(21), wa(world["muted"], g), STAGE_W - 92)
        if i < 2:
            h["_draw_bezier_comet"](stage, (540, y0 + 278), (540, y0 + 332), col, reveal=g, progress=progress, world=world)


# -------------------------------------------------------------------------
# #25 AI / ML / DEEP LEARNING & MULTI-AGENT SWARM
# -------------------------------------------------------------------------
def _render_neural_backprop(stage, d, progress, world, h):
    gf, wa = h["_get_font"], h["_with_alpha"]
    is_back = progress >= 0.52
    mode_lbl = "BACKPROPAGATION: GRADIENT WEIGHT UPDATE <-" if is_back else "FORWARD PASS: TENSOR ACTIVATION ->"
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["amber"] if is_back else world["cyan"], 1.0, mode_lbl, h, mono=True)
    cols_x = [STAGE_X0 + 120, 405, 675, STAGE_X1 - 120]
    counts = [3, 4, 4, 2]
    centers: List[List[Tuple[int, int]]] = []
    for li, (cx, nc) in enumerate(zip(cols_x, counts)):
        pts = [(cx, STAGE_Y0 + 240 + k * (680 // max(1, nc))) for k in range(nc)]
        centers.append(pts)
    for li in range(len(centers) - 1):
        for p0 in centers[li]:
            for p1 in centers[li + 1]:
                col = world["amber"] if is_back else world["cyan"]
                stage.draw.line((p0[0], p0[1], p1[0], p1[1]), fill=wa(col, 0.45), width=3)
    for li, pts in enumerate(centers):
        for px, py in pts:
            col = world["amber"] if is_back else world["emerald"]
            stage.draw.ellipse((px - 28, py - 28, px + 28, py + 28), fill=world["card_bg"], outline=col, width=4)
    loss_lbl = f"LOSS: {max(0.04, 1.42 - progress * 1.35):.2f}  |  grad_norm=0.018"
    stage.draw_pill(540, STAGE_Y1 - 110, loss_lbl, (*world["amber"][:3], 42), world["amber"] if is_back else world["emerald"], border_col=world["amber"], font=gf(23, bold=True, mono=True))


def _render_sliding_conv(stage, d, progress, world, h):
    gf, wa = h["_get_font"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 650), world["cyan"], 1.0, "INPUT TENSOR (5x5) + MOVING 3x3 KERNEL", h, mono=True)
    step = min(8, int(_c01(progress) * 9))
    kr, kc = divmod(step, 3)
    cs = 84
    for r in range(5):
        for c in range(5):
            in_win = (kr <= r < kr + 3 and kc <= c < kc + 3)
            x0 = 330 + c * (cs + 6)
            y0 = STAGE_Y0 + 110 + r * (cs + 6)
            col = world["amber"] if in_win else world["border"]
            stage.draw_glass_card((x0, y0, x0 + cs, y0 + cs), radius=10, accent_col=col, active=in_win)
            stage.draw.text((x0 + 26, y0 + 24), str((r * 3 + c * 2) % 9 + 1), font=gf(24, bold=True, mono=True), fill=world["text"])
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 690, STAGE_X1, STAGE_Y1 - 40), world["emerald"], 1.0, "CONVOLVED FEATURE MAP (3x3 OUTPUT)", h, mono=True)
    for idx in range(9):
        rr, cc = divmod(idx, 3)
        ox = 380 + cc * 108
        oy = STAGE_Y0 + 785 + rr * 108
        done = idx <= step
        stage.draw_glass_card((ox, oy, ox + 96, oy + 96), radius=12, accent_col=world["emerald"] if done else world["border"], alpha_mul=1.0 if done else 0.25, active=(idx == step))
        if done:
            stage.draw.text((ox + 26, oy + 28), str(12 + idx * 5), font=gf(25, bold=True, mono=True), fill=world["emerald"])


def _render_vector_space_3b1b(stage, d, progress, world, h):
    gf, wa = h["_get_font"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["purple"], 1.0, "EMBEDDING VECTOR SPACE (COSINE SIMILARITY)", h, mono=True)
    ox, oy = 250, STAGE_Y0 + 820
    stage.draw.line((ox - 90, oy, 940, oy), fill=world["border"], width=3)
    stage.draw.line((ox, STAGE_Y0 + 120, ox, oy + 120), fill=world["border"], width=3)
    ang_b = 0.28 + 0.55 * (1.0 - _c01(progress))
    va = (ox + 560, oy - 160)
    vb = (int(ox + 480 * math.cos(ang_b)), int(oy - 480 * math.sin(ang_b)))
    stage.draw.line((ox, oy, va[0], va[1]), fill=world["cyan"], width=7)
    stage.draw.line((ox, oy, vb[0], vb[1]), fill=world["emerald"], width=7)
    stage.draw.line((vb[0], vb[1], vb[0], oy), fill=wa(world["amber"], 0.75), width=3)
    stage.draw_pill(va[0] - 40, va[1] - 32, "vec_query", (*world["cyan"][:3], 42), world["cyan"], border_col=world["cyan"], font=gf(20, bold=True, mono=True))
    stage.draw_pill(vb[0], vb[1] - 32, "vec_doc", (*world["emerald"][:3], 42), world["emerald"], border_col=world["emerald"], font=gf(20, bold=True, mono=True))
    sim = 0.72 + 0.24 * _c01(progress)
    stage.draw_pill(540, STAGE_Y1 - 110, f"cos(theta) = {sim:.3f}  |  Dot Product Aligned ✅", (*world["emerald"][:3], 44), world["emerald"], border_col=world["emerald"], font=gf(23, bold=True, mono=True))


def _render_ai_thinking_trace(stage, d, progress, world, h):
    gf, gw, wa, sg = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"], h["_spring_gate"]
    steps = _items_list(d, [("THOUGHT FOR 1.8s", "Inspecting query plan & metadata"), ("TOOL CALL • mcp.exec()", "Pruned 42,000 files down to 18 blocks"), ("VERIFIED OUTPUT", "P99 latency cut from 920ms -> 14ms")], 3)
    cols = (world["purple"], world["cyan"], world["emerald"])
    for i, stp in enumerate(steps):
        g = h["_ease_out_cubic"](sg(progress, i, 3, 0.28))
        if g <= 0.02:
            continue
        y0 = STAGE_Y0 + 30 + i * 375
        stage.draw_glass_card((STAGE_X0, y0, STAGE_X1, y0 + 335), radius=24, accent_col=cols[i], alpha_mul=g, active=(i == 1), label=stp["name"])
        stage.draw_pill(STAGE_X0 + 190, y0 + 52, stp["name"][:22], (*cols[i][:3], 44), cols[i], border_col=cols[i], font=gf(19, bold=True, mono=True), alpha_mul=g)
        gw(stage.draw, (STAGE_X0 + 36, y0 + 115), stp.get("sub") or stp["name"], gf(28, bold=True), wa(world["text"], g), STAGE_W - 72)


def _render_multi_agent_swimlane(stage, d, progress, world, h):
    gf, wa, sg = h["_get_font"], h["_with_alpha"], h["_spring_gate"]
    lanes = [("Coordinator", 0.0, 0.24, "Plan & Shard", "cyan"), ("Researcher", 0.24, 0.44, "Docs + Schema", "purple"), ("Coder Agent", 0.24, 0.50, "Patch + Tests", "emerald"), ("Verifier", 0.74, 0.26, "Suite Pass ✅", "amber")]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, "PARALLEL SWARM TIMELINE (0ms -> 800ms)", h, mono=True)
    for i, (nm, st_f, dur_f, task, ck) in enumerate(lanes):
        g = h["_ease_out_cubic"](sg(progress, i, 4, 0.25))
        if g <= 0.02:
            continue
        col = world[ck]
        ly = STAGE_Y0 + 100 + i * 245
        stage.draw.text((STAGE_X0 + 30, ly), nm, font=gf(27, bold=True), fill=wa(world["text"], g))
        x0 = STAGE_X0 + 36 + int(840 * st_f)
        x1 = x0 + max(160, int(840 * dur_f * g))
        stage.draw_glass_card((x0, ly + 48, x1, ly + 132), radius=16, accent_col=col, alpha_mul=g, active=(i in (1, 2)), label=task)
        stage.draw.text((x0 + 18, ly + 74), task, font=gf(22, bold=True), fill=wa(world["text"], g))


# -------------------------------------------------------------------------
# #26 BANK IT INFRASTRUCTURE (CORE BANKING + DR FAILOVER)
# -------------------------------------------------------------------------
def _render_banking_rails(stage, d, progress, world, h):
    gf, gw, wa, sg = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"], h["_spring_gate"]
    rails = [
        ("01 • mTLS + HSM PIN VAULT", "Hardware Encryption & Tokenization", "cyan"),
        ("02 • REAL-TIME AML / FRAUD", "Risk Score <15ms Inline Decision", "amber"),
        ("03 • ATOMIC DOUBLE-ENTRY CBS", "SERIALIZABLE Debit + Credit Lock", "emerald"),
        ("04 • NPCI / ISO 20022 / SWIFT", "Idempotent Clearing & Immutable Log", "purple"),
    ]
    for i, (tit, sub, ck) in enumerate(rails):
        g = h["_ease_out_cubic"](sg(progress, i, 4, 0.24))
        if g <= 0.02:
            continue
        col = world[ck]
        y0 = STAGE_Y0 + 20 + i * 256
        stage.draw_glass_card((STAGE_X0, y0, STAGE_X1, y0 + 208), radius=20, accent_col=col, alpha_mul=g, active=(int(_c01(progress) * 4) == i), label=tit)
        gw(stage.draw, (STAGE_X0 + 32, y0 + 34), tit, gf(28, bold=True, mono=True), wa(col, g), STAGE_W - 64)
        gw(stage.draw, (STAGE_X0 + 32, y0 + 98), sub, gf(25, bold=True), wa(world["text"], g), STAGE_W - 64)
        if i < 3:
            h["_draw_bezier_comet"](stage, (540, y0 + 212), (540, y0 + 252), col, reveal=g, progress=progress, world=world)


def _render_dr_failover(stage, d, progress, world, h):
    gf, gw, wa = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"]
    failed = progress >= 0.42
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 24, STAGE_X1, STAGE_Y0 + 440), world["rose"] if failed else world["cyan"], 1.0, "PRIMARY DC (MUMBAI) — " + ("OUTAGE DETECTED ❌" if failed else "ACTIVE"), h, mono=True)
    gw(stage.draw, (STAGE_X0 + 34, STAGE_Y0 + 140), "Core Banking Nodes + SAN Vault Mirror" if not failed else "Power/Link Fault Triggered Automated Fencing!", gf(30, bold=True), world["rose"] if failed else world["text"], STAGE_W - 68)
    g_sw = _c01((progress - 0.35) / 0.30)
    if g_sw > 0.04:
        h["_draw_bezier_comet"](stage, (540, STAGE_Y0 + 446), (540, STAGE_Y0 + 625), world["emerald"], reveal=g_sw, progress=progress, label="DNS + WAL CUTOVER", world=world)
    dr_on = progress >= 0.58
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 630, STAGE_X1, STAGE_Y1 - 60), world["emerald"] if dr_on else world["amber"], 1.0, "DR VAULT DC (HYDERABAD) — " + ("PROMOTED ACTIVE ✅" if dr_on else "HOT STANDBY"), h, mono=True)
    gw(stage.draw, (STAGE_X0 + 34, STAGE_Y0 + 750), "Zero Data Loss (RPO = 0)  |  Switchover Time (RTO < 18s)", gf(30, bold=True), world["emerald"] if dr_on else world["muted"], STAGE_W - 68)
    stage.draw_pill(540, STAGE_Y0 + 960, "CONTINUOUS AUDIT INTEGRITY VERIFIED", (*world["emerald"][:3], 42), world["emerald"], border_col=world["emerald"], font=gf(22, bold=True, mono=True))


# -------------------------------------------------------------------------
# #27 NETWORKING & SECURITY
# -------------------------------------------------------------------------
def _render_bitfield_grid(stage, d, progress, world, h):
    gf, sg, wa = h["_get_font"], h["_spring_gate"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, "32-BIT PROTOCOL HEADER FRAME (0..31 BITS)", h, mono=True)
    fields = [
        ("SRC PORT (16 bits)", 0.5, "cyan", 0), ("DST PORT (16 bits)", 0.5, "purple", 0),
        ("SEQUENCE NUMBER (32 bits)", 1.0, "emerald", 1),
        ("ACK NUMBER (32 bits)", 1.0, "amber", 2),
        ("LEN+FLAGS (16b)", 0.5, "rose", 3), ("WINDOW SIZE (16b)", 0.5, "cyan", 3),
    ]
    cur_x = STAGE_X0 + 28
    for i, (lbl, frac, ck, row) in enumerate(fields):
        g = h["_ease_out_cubic"](sg(progress, i, len(fields), 0.22))
        if g <= 0.02:
            continue
        if i in (0, 2, 3, 4):
            cur_x = STAGE_X0 + 28
        w = int((STAGE_W - 68) * frac)
        y0 = STAGE_Y0 + 100 + row * 240
        col = world[ck]
        stage.draw_glass_card((cur_x, y0, cur_x + w - 8, y0 + 200), radius=16, accent_col=col, alpha_mul=g, active=(int(_c01(progress) * 6) == i), label=lbl)
        stage.draw.text((cur_x + 22, y0 + 78), lbl, font=gf(24, bold=True, mono=True), fill=wa(world["text"], g))
        cur_x += w


def _render_geo_world_arcs(stage, d, progress, world, h):
    gf = h["_get_font"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, "GLOBAL EDGE ANYCAST & PACKET ARCS", h, mono=True)
    for poly in ([(140, 560), (290, 520), (330, 680), (260, 820), (320, 1080), (220, 1220), (160, 820)],
                 [(460, 520), (620, 490), (640, 680), (600, 960), (520, 1140), (450, 820)],
                 [(650, 500), (920, 530), (950, 780), (830, 960), (680, 760)]):
        stage.draw.polygon(poly, fill=(*world["card_layer"][:3], 180), outline=(*world["cyan"][:3], 120))
    hubs = [("US-EAST", 250, 660, "cyan"), ("FRANKFURT", 540, 600, "purple"), ("MUMBAI", 740, 810, "emerald"), ("SINGAPORE", 865, 920, "amber")]
    for a, b, lat in [(0, 1, "68ms"), (1, 2, "104ms"), (2, 3, "42ms")]:
        x0, y0, ck = hubs[a][1], hubs[a][2], hubs[a][3]
        x1, y1 = hubs[b][1], hubs[b][2]
        pts = [(x0 + (x1 - x0) * (s / 20.0), y0 + (y1 - y0) * (s / 20.0) - math.sin((s / 20.0) * math.pi) * 90) for s in range(21)]
        stage.draw.line(pts, fill=world[ck], width=5)
        pk = pts[min(20, int((progress * 20) % 21))]
        stage.draw.ellipse((pk[0] - 11, pk[1] - 11, pk[0] + 11, pk[1] + 11), fill=world["text"], outline=world[ck], width=3)
        stage.draw_pill(int(pts[10][0]), int(pts[10][1] - 32), lat, world["card_bg"], world[ck], border_col=world[ck], font=gf(18, bold=True))
    for nm, hx, hy, ck in hubs:
        stage.draw_glass_card((hx - 75, hy + 20, hx + 75, hy + 68), radius=16, accent_col=world[ck], active=True, label=nm)
        stage.draw.text((hx - 54, hy + 32), nm, font=gf(17, bold=True, mono=True), fill=world["text"])


def _render_security_replay(stage, d, progress, world, h):
    gf, gw, wa = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["rose"], 1.0, "ZERO-TRUST WAF / mTLS SHIELD SIMULATION", h, mono=True)
    stage.draw_glass_card((430, STAGE_Y0 + 150, 650, STAGE_Y1 - 160), radius=30, accent_col=world["cyan"], active=True, label="WAF + mTLS SHIELD")
    gw(stage.draw, (445, STAGE_Y0 + 520), "WAF + mTLS SHIELD", gf(26, bold=True), world["cyan"], 190, align="center")
    # Attacks bounce left, Verified tokens reach right
    for i, atk in enumerate(["SQLi Flood ❌", "Bot Spike ❌"]):
        ay = STAGE_Y0 + 230 + i * 210
        ax = int(STAGE_X0 + 36 + _c01(progress * 1.6) * 240)
        stage.draw_pill(ax, ay, atk, (*world["rose"][:3], 52), world["rose"], border_col=world["rose"], font=gf(20, bold=True, mono=True))
    vx = int(STAGE_X0 + 40 + _c01(progress) * 730)
    stage.draw_pill(vx, STAGE_Y0 + 780, "JWT + mTLS OK ✅", (*world["emerald"][:3], 52), world["emerald"], border_col=world["emerald"], font=gf(21, bold=True, mono=True))
    stage.draw_glass_card((740, STAGE_Y0 + 680, STAGE_X1 - 36, STAGE_Y0 + 880), radius=20, accent_col=world["emerald"], active=(progress > 0.65), label="ORIGIN API")
    stage.draw.text((768, STAGE_Y0 + 764), "PROTECTED API", font=gf(22, bold=True), fill=world["emerald"])


# -------------------------------------------------------------------------
# #28 MODERN 2026 DEV / IDE / SRE UIs
# -------------------------------------------------------------------------
def _render_excalidraw_sketch(stage, d, progress, world, h):
    gf, sg, wa = h["_get_font"], h["_spring_gate"], h["_with_alpha"]
    items = _items_list(d, [("Client App", "JWT Request"), ("API Gateway", "Route + Auth"), ("Redis Cache", "0.4ms Hit"), ("Core Storage", "ACID Write")], 4)
    rng = random.Random(42)
    coords = [(100, STAGE_Y0 + 120, 460, STAGE_Y0 + 340), (600, STAGE_Y0 + 120, 970, STAGE_Y0 + 340), (120, STAGE_Y0 + 520, 490, STAGE_Y0 + 760), (590, STAGE_Y0 + 520, 960, STAGE_Y0 + 760)]
    for i, it in enumerate(items[:4]):
        g = h["_ease_out_cubic"](sg(progress, i, 4, 0.25))
        if g <= 0.03:
            continue
        x0, y0, x1, y1 = coords[i]
        col = world[_CYCLE[i % len(_CYCLE)]]
        stage.draw.rounded_rectangle((x0, y0, x1, y1), radius=14, fill=wa(world["card_bg"], g))
        pts = [(x0 + rng.uniform(-3, 3), y0 + rng.uniform(-3, 3)), (x1 + rng.uniform(-3, 3), y0 + rng.uniform(-3, 3)), (x1 + rng.uniform(-3, 3), y1 + rng.uniform(-3, 3)), (x0 + rng.uniform(-3, 3), y1 + rng.uniform(-3, 3)), (x0 + rng.uniform(-3, 3), y0 + rng.uniform(-3, 3))]
        stage.draw.line(pts, fill=wa(col, g), width=4)
        h["_draw_wrapped_text"](stage.draw, (x0 + 22, y0 + 50), it["name"][:24], gf(27, bold=True), wa(world["text"], g), x1 - x0 - 44, align="center")
        h["_draw_wrapped_text"](stage.draw, (x0 + 22, y0 + 125), it.get("sub", "")[:34], gf(20), wa(col, g), x1 - x0 - 44, align="center")
    stage.draw_pill(540, STAGE_Y1 - 120, "Whiteboard Sketch • Architecture Breakdown", (*world["amber"][:3], 42), world["amber"], border_col=world["amber"], font=gf(22, bold=True))


def _render_ide_workbench(stage, d, progress, world, h):
    gf, sg, wa = h["_get_font"], h["_spring_gate"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, "    nanopro — worker_pool.py (2026 AI IDE)", h, mono=True)
    for k, cc in enumerate([(239, 68, 68), (245, 158, 11), (16, 185, 129)]):
        stage.draw.ellipse((STAGE_X0 + 22 + k * 24, STAGE_Y0 + 38, STAGE_X0 + 38 + k * 24, STAGE_Y0 + 54), fill=cc)
    stage.draw.line((STAGE_X0 + 235, STAGE_Y0 + 76, STAGE_X0 + 235, STAGE_Y0 + 740), fill=world["border"], width=2)
    for idx, fn in enumerate(["core/", "  director.py", "> worker.py", "  router.py"]):
        stage.draw.text((STAGE_X0 + 26, STAGE_Y0 + 115 + idx * 54), fn, font=gf(20, bold=(">" in fn), mono=True), fill=world["cyan"] if ">" in fn else world["muted"])
    code = str(d.get("code_snippet") or "- with global_lock:\n-   flush_sync(rows)\n+ shard = hash(key) % 8\n+ await wal[shard].append(rows)").splitlines()[:5]
    for i, ln in enumerate(code):
        g = h["_ease_out_cubic"](sg(progress, i, len(code), 0.22))
        if g > 0.03:
            col = world["rose"] if ln.startswith("-") else (world["emerald"] if ln.startswith("+") else world["text"])
            stage.draw.text((STAGE_X0 + 260, STAGE_Y0 + 125 + i * 76), ln[:38], font=gf(22, bold=True, mono=True), fill=wa(col, g))
    stage.draw.line((STAGE_X0, STAGE_Y0 + 740, STAGE_X1, STAGE_Y0 + 740), fill=world["border"], width=2)
    stage.draw.text((STAGE_X0 + 28, STAGE_Y0 + 785), "$ pytest -q -> [PASS] 1.8ms P99 • EXIT 0 ✅", font=gf(25, bold=True, mono=True), fill=world["emerald"])


def _render_dual_sync_diagram_code(stage, d, progress, world, h):
    gf, gw, wa = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"]
    items = _items_list(d, [("Client REQ", "Ingress"), ("Token Bucket", "Rate Gate"), ("API Cluster", "Upstream")], 3)
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 460), world["cyan"], 1.0, "ARCHITECTURE TOPOLOGY (LIVE ACTIVE NODE)", h, mono=True)
    act_i = min(len(items) - 1, int(_c01(progress) * len(items)))
    for i, it in enumerate(items[:3]):
        col = world[_CYCLE[i % len(_CYCLE)]]
        nx = STAGE_X0 + 24 + i * 308
        is_act = (i == act_i)
        stage.draw_glass_card((nx, STAGE_Y0 + 100, nx + 276, STAGE_Y0 + 360), radius=18, accent_col=col, active=is_act, label=it["name"])
        gw(stage.draw, (nx + 18, STAGE_Y0 + 190), it["name"][:22], gf(25, bold=True), world["text"], 240, align="center")
    ax = STAGE_X0 + 24 + act_i * 308 + 138
    stage.draw.line((ax, STAGE_Y0 + 365, ax, STAGE_Y0 + 545), fill=world["amber"], width=5)
    stage.draw_pill(ax, STAGE_Y0 + 495, "LIVE LINE", world["card_bg"], world["amber"], border_col=world["amber"], font=gf(18, bold=True))

    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 550, STAGE_X1, STAGE_Y1 - 40), world["amber"], 1.0, "EXECUTING CODE (SYNCED LINE BY LINE)", h, mono=True)
    code_lines = str(d.get("code_snippet") or "01 req = parse_ingress()\n02 tokens = await redis.eval_lua(key)\n03 return await cluster.forward(req)").splitlines()[:4]
    for i, ln in enumerate(code_lines):
        cy = STAGE_Y0 + 640 + i * 115
        is_act = (i == act_i % max(1, len(code_lines)))
        if is_act:
            stage.draw.rounded_rectangle((STAGE_X0 + 24, cy - 10, STAGE_X1 - 24, cy + 62), radius=12, fill=wa((*world["amber"][:3], 52), 1.0), outline=world["amber"], width=2)
        stage.draw.text((STAGE_X0 + 40, cy + 8), ln[:46], font=gf(24, bold=is_act, mono=True), fill=world["amber"] if is_act else world["text"])


def _render_sre_console(stage, d, progress, world, h):
    gf = h["_get_font"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 380), world["rose"], 1.0, "P99 LATENCY SPIKE — ALERT FIRING", h, mono=True)
    pts = [(110, STAGE_Y0 + 310), (260, STAGE_Y0 + 295), (420, STAGE_Y0 + 280), (540, STAGE_Y0 + 110), (690, STAGE_Y0 + 135), (890, STAGE_Y0 + 260)]
    stage.draw.line(pts, fill=world["rose"], width=6)
    stage.draw_pill(540, STAGE_Y0 + 100, "420ms SPIKE", world["card_bg"], world["rose"], border_col=world["rose"], font=gf(18, bold=True))
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 410, STAGE_X1, STAGE_Y0 + 760), world["amber"], 1.0, "OTEL DISTRIBUTED TRACE SPAN", h, mono=True)
    for i, (nm, s, wd, ck) in enumerate([("gateway.ingress", 0.0, 0.18, "cyan"), ("auth.jwt_verify", 0.18, 0.16, "emerald"), ("db.row_lock_wait", 0.34, 0.56, "rose")]):
        sy = STAGE_Y0 + 495 + i * 76
        stage.draw.text((STAGE_X0 + 26, sy), nm, font=gf(21, bold=True), fill=world["text"])
        stage.draw.rounded_rectangle((430 + int(480 * s), sy + 2, 430 + int(480 * (s + wd * _c01(0.3 + progress * 0.7))), sy + 34), radius=10, fill=world[ck])
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 790, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, "LIVE POD LOGS", h, mono=True)
    for i, (lg, ck) in enumerate([("ERROR 502 upstream lock timeout", "rose"), ("WARN  pool_connections=100/100", "amber"), ("INFO  circuit_breaker=OPEN shedding", "emerald")]):
        stage.draw.text((STAGE_X0 + 28, STAGE_Y0 + 875 + i * 76), lg, font=gf(22, bold=True, mono=True), fill=world[ck])


def _render_mac_terminal(stage, d, progress, world, h):
    gf, sg, wa = h["_get_font"], h["_spring_gate"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 24, STAGE_X1, STAGE_Y1 - 60), world["emerald"], 1.0, "    zsh — production-cluster", h, mono=True)
    for k, cc in enumerate([(239, 68, 68), (245, 158, 11), (16, 185, 129)]):
        stage.draw.ellipse((STAGE_X0 + 22 + k * 26, STAGE_Y0 + 46, STAGE_X0 + 40 + k * 26, STAGE_Y0 + 64), fill=cc)
    cmd = str(d.get("command") or "kubectl rollout status deploy/gateway")
    lines = [(f"$ {cmd[:46]}", "cyan"), ("{", "text"), ('  "status": "HEALTHY",', "emerald"), ('  "p99_latency_ms": 1.8,', "amber"), ('  "zero_downtime": true', "emerald"), ("}", "text")]
    for i, (ln, ck) in enumerate(lines):
        g = h["_ease_out_cubic"](sg(progress, i, len(lines), 0.20))
        if g > 0.03:
            col = world["text"] if ck == "text" else world[ck]
            stage.draw.text((STAGE_X0 + 36, STAGE_Y0 + 135 + i * 110), ln, font=gf(27, bold=(i == 0), mono=True), fill=wa(col, g))
    if progress > 0.72:
        stage.draw_pill(300, STAGE_Y1 - 140, "EXIT 0 • VERIFIED ✅", world["card_bg"], world["emerald"], border_col=world["emerald"], font=gf(22, bold=True, mono=True))


def _render_db_cutover(stage, d, progress, world, h):
    gf, gw = h["_get_font"], h["_draw_wrapped_text"]
    cut = progress >= 0.62
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 24, 515, STAGE_Y0 + 600), world["amber"], 1.0, "LEGACY PRIMARY TABLE", h, mono=True)
    _draw_top_panel(stage, (565, STAGE_Y0 + 24, STAGE_X1, STAGE_Y0 + 600), world["emerald"], 1.0, "NEW SHADOW TABLE (DUAL-WRITE)", h, mono=True)
    gw(stage.draw, (STAGE_X0 + 30, STAGE_Y0 + 180), "v1 Schema\n120M Rows", gf(30, bold=True), world["text"], 380)
    gw(stage.draw, (595, STAGE_Y0 + 180), "v2 Indexed Schema\n100% Shadow Parity", gf(30, bold=True), world["emerald"], 380)
    h["_draw_bezier_comet"](stage, (518, STAGE_Y0 + 310), (562, STAGE_Y0 + 310), world["cyan"], reveal=_c01(progress * 1.4), progress=progress, label="SYNC", world=world)
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 660, STAGE_X1, STAGE_Y1 - 80), world["emerald"] if cut else world["cyan"], 1.0, "ATOMIC DNS / ROUTER CUTOVER SWITCH", h, mono=True)
    stage.draw_pill(540, STAGE_Y0 + 910, "TRAFFIC CUTOVER -> V2 SHADOW ACTIVE ✅" if cut else "DUAL-WRITE VERIFYING PARITY...", world["card_bg"], world["emerald"] if cut else world["amber"], border_col=world["emerald"] if cut else world["amber"], font=gf(24, bold=True, mono=True))


# -------------------------------------------------------------------------
# #29 SPECIALIZED CS EXTRAS (DEVTOOLS, RACE, CPU CLOCK, BENTO, MEDIA, SCROLL)
# -------------------------------------------------------------------------
def _render_browser_devtools(stage, d, progress, world, h):
    gf, sg, wa = h["_get_font"], h["_spring_gate"], h["_with_alpha"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y0 + 480), world["cyan"], 1.0, "DEVTOOLS • ELEMENTS & DOM TREE", h, mono=True)
    for i, ln in enumerate(["<html>", "  <body>", "    <main class='hydrated'>", "      <ChartCanvas />  <!-- 60fps -->"]):
        stage.draw.text((STAGE_X0 + 32, STAGE_Y0 + 100 + i * 76), ln, font=gf(24, bold=(i == 3), mono=True), fill=world["emerald"] if i == 3 else world["text"])
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 520, STAGE_X1, STAGE_Y1 - 40), world["purple"], 1.0, "NETWORK WATERFALL & PAINT TIMELINE", h, mono=True)
    for i, (nm, s, wd, ck) in enumerate([("GET /index.html", 0.0, 0.14, "cyan"), ("GET /bundle.js", 0.14, 0.28, "amber"), ("GET /api/metrics", 0.42, 0.22, "emerald"), ("FIRST CONTENTFUL PAINT", 0.64, 0.30, "purple")]):
        g = h["_ease_out_cubic"](sg(progress, i, 4, 0.24))
        if g > 0.03:
            wy = STAGE_Y0 + 610 + i * 115
            stage.draw.text((STAGE_X0 + 28, wy), nm, font=gf(21, bold=True, mono=True), fill=wa(world["text"], g))
            stage.draw.rounded_rectangle((460 + int(450 * s), wy + 4, 460 + int(450 * (s + wd * g)), wy + 34), radius=8, fill=wa(world[ck], g))


def _render_benchmark_race(stage, d, progress, world, h):
    gf = h["_get_font"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 24, STAGE_X1, STAGE_Y0 + 520), world["rose"], 1.0, "LANE 1: BLOCKING SYNC (4,200 ms ❌)", h, mono=True)
    sx = STAGE_X0 + 30 + int((STAGE_W - 230) * min(0.32, progress * 0.35))
    stage.draw_pill(sx + 80, STAGE_Y0 + 270, "BLOCKED...", (*world["rose"][:3], 52), world["rose"], border_col=world["rose"], font=gf(23, bold=True, mono=True))
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 570, STAGE_X1, STAGE_Y1 - 60), world["emerald"], 1.0, "LANE 2: LOCK-FREE ASYNC (14 ms ✅ • 300x)", h, mono=True)
    fx = STAGE_X0 + 30 + int((STAGE_W - 230) * _c01(progress * 1.15))
    stage.draw_pill(fx + 80, STAGE_Y0 + 820, "FINISHED ✅", (*world["emerald"][:3], 52), world["emerald"], border_col=world["emerald"], font=gf(23, bold=True, mono=True))


def _render_cpu_pipeline(stage, d, progress, world, h):
    gf = h["_get_font"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["cyan"], 1.0, "CPU CLOCK CYCLES (IF -> ID -> EX -> MEM -> WB)", h, mono=True)
    stages = ["IF", "ID", "EX", "MEM", "WB"]
    cols = ("cyan", "purple", "amber", "emerald", "cyan")
    cur_t = int(_c01(progress) * 4)
    for r in range(4):
        ry = STAGE_Y0 + 130 + r * 220
        stage.draw.text((STAGE_X0 + 26, ry + 34), f"Inst {r + 1}", font=gf(23, bold=True, mono=True), fill=world["text"])
        for t in range(5):
            st_i = t - r
            cx = STAGE_X0 + 165 + t * 148
            if 0 <= st_i < len(stages) and t <= cur_t + r:
                col = world[cols[st_i]]
                stage.draw_glass_card((cx, ry, cx + 132, ry + 118), radius=14, accent_col=col, active=(t == cur_t + 1), label=stages[st_i])
                stage.draw.text((cx + 42, ry + 38), stages[st_i], font=gf(28, bold=True, mono=True), fill=world["text"])


def _render_bento_keynote(stage, d, progress, world, h):
    gf, gw, wa, sg = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"], h["_spring_gate"]
    items = _items_list(d, [("99.999%", "Production Uptime SLA"), ("14 ms", "P99 Tail Latency"), ("Zero Lock", "Atomic Non-Blocking"), ("10x Cost Cut", "Auto-Scale Tiering"), ("ACID Safe", "Verified Checkpoints")], 5)
    boxes = [
        (STAGE_X0, STAGE_Y0 + 20, STAGE_X1, STAGE_Y0 + 400),
        (STAGE_X0, STAGE_Y0 + 425, 525, STAGE_Y0 + 780),
        (550, STAGE_Y0 + 425, STAGE_X1, STAGE_Y0 + 780),
        (STAGE_X0, STAGE_Y0 + 805, 525, STAGE_Y1 - 40),
        (550, STAGE_Y0 + 805, STAGE_X1, STAGE_Y1 - 40),
    ]
    for i, it in enumerate(items[:5]):
        g = h["_ease_out_cubic"](sg(progress, i, 5, 0.22))
        if g <= 0.02:
            continue
        bx = boxes[i]
        col = world[_CYCLE[i % len(_CYCLE)]]
        stage.draw_glass_card(bx, radius=24, accent_col=col, alpha_mul=g, active=(i == 0), label=it["name"])
        gw(stage.draw, (bx[0] + 28, bx[1] + 55), it["name"][:22], gf(48 if i == 0 else 32, bold=True), wa(col, g), bx[2] - bx[0] - 56, align="center")
        gw(stage.draw, (bx[0] + 28, bx[1] + (180 if i == 0 else 145)), it.get("sub", "")[:46], gf(25 if i == 0 else 21, bold=True), wa(world["text"], g), bx[2] - bx[0] - 56, align="center")


def _render_media_tracks_nle(stage, d, progress, world, h):
    gf = h["_get_font"]
    _draw_top_panel(stage, (STAGE_X0, STAGE_Y0 + 16, STAGE_X1, STAGE_Y1 - 40), world["purple"], 1.0, "STREAMING TIMELINE (VIDEO • AUDIO • SUBS • HLS)", h, mono=True)
    tracks = [("VIDEO H.264", "cyan"), ("AUDIO AAC", "emerald"), ("HLS SEGMENTS", "amber"), ("CAPTIONS ASS", "purple")]
    for i, (nm, ck) in enumerate(tracks):
        ty = STAGE_Y0 + 120 + i * 240
        stage.draw.text((STAGE_X0 + 28, ty), nm, font=gf(22, bold=True, mono=True), fill=world[ck])
        for seg in range(3):
            sx = STAGE_X0 + 28 + seg * 296
            stage.draw_glass_card((sx, ty + 48, sx + 278, ty + 150), radius=14, accent_col=world[ck], label=f"Seg {seg + 1}")
            stage.draw.text((sx + 20, ty + 84), f"Chunk #{seg + 1}", font=gf(21, bold=True, mono=True), fill=world["text"])
    ph_x = STAGE_X0 + 28 + int(860 * _c01(progress))
    stage.draw.line((ph_x, STAGE_Y0 + 95, ph_x, STAGE_Y1 - 65), fill=world["rose"], width=5)


def _render_scrollytelling_track(stage, d, progress, world, h):
    gf, gw, wa = h["_get_font"], h["_draw_wrapped_text"], h["_with_alpha"]
    items = _items_list(d, [("INGEST EDGE", "Request parsed"), ("QUEUE BUFFER", "Partition routed"), ("CORE EXECUTION", "Atomic commit + ACID snapshot"), ("VERIFIED SERVE", "Sub-second response")], 4)
    stage.draw.line((STAGE_X0 + 78, STAGE_Y0 + 30, STAGE_X0 + 78, STAGE_Y1 - 40), fill=world["cyan"], width=5)
    act_i = min(len(items) - 1, int(_c01(progress) * len(items)))
    cur_y = STAGE_Y0 + 28
    for i, it in enumerate(items):
        is_act = (i == act_i)
        box_h = 340 if is_act else 185
        col = world["amber"] if is_act else world["cyan"]
        stage.draw.ellipse((STAGE_X0 + 56, cur_y + box_h // 2 - 22, STAGE_X0 + 100, cur_y + box_h // 2 + 22), fill=world["card_bg"], outline=col, width=4)
        x0 = STAGE_X0 + 130 if is_act else STAGE_X0 + 155
        stage.draw_glass_card((x0, cur_y, STAGE_X1 if is_act else STAGE_X1 - 36, cur_y + box_h), radius=22, accent_col=col, active=is_act, layered=is_act, label=it["name"])
        gw(stage.draw, (x0 + 28, cur_y + (70 if is_act else 34)), it["name"], gf(32 if is_act else 23, bold=True), world["text"], STAGE_X1 - x0 - 60)
        if it.get("sub"):
            gw(stage.draw, (x0 + 28, cur_y + (150 if is_act else 92)), it["sub"], gf(24 if is_act else 19), world["muted"] if not is_act else world["cyan"], STAGE_X1 - x0 - 60)
        cur_y += box_h + 24


_SPECIALIST_DISPATCH = {
    "python_stack_heap_live": _render_python_stack_heap,
    "algorithm_dry_run_debugger": _render_algo_dry_run,
    "event_loop_visualizer": _render_event_loop,
    "sql_live_join_venn_rows": _render_sql_live_join,
    "notebook_interactive_cell": _render_notebook_cell,
    "racing_timeseries_chart": _render_racing_chart,
    "snowflake_micro_partition_pruner": _render_snowflake_pruner,
    "cloud_infra_zone_builder": _render_cloud_infra_builder,
    "neural_forward_backprop_flow": _render_neural_backprop,
    "sliding_window_convolution_grid": _render_sliding_conv,
    "vector_space_3b1b": _render_vector_space_3b1b,
    "ai_thinking_tool_trace": _render_ai_thinking_trace,
    "multi_agent_swimlane_trace": _render_multi_agent_swimlane,
    "banking_ledger_settlement_rails": _render_banking_rails,
    "dr_active_active_failover": _render_dr_failover,
    "bitfield_protocol_grid": _render_bitfield_grid,
    "geo_world_packet_arcs": _render_geo_world_arcs,
    "security_attack_defense_replay": _render_security_replay,
    "excalidraw_sketch_board": _render_excalidraw_sketch,
    "ide_split_workbench": _render_ide_workbench,
    "dual_sync_diagram_plus_code": _render_dual_sync_diagram_code,
    "live_sre_observability_console": _render_sre_console,
    "mac_terminal_stream_cast": _render_mac_terminal,
    "db_live_cutover_migration": _render_db_cutover,
    "browser_devtools_studio": _render_browser_devtools,
    "live_benchmark_race_track": _render_benchmark_race,
    "cpu_pipeline_clock_cycle": _render_cpu_pipeline,
    "bento_apple_keynote": _render_bento_keynote,
    "media_streaming_tracks_nle": _render_media_tracks_nle,
    "vertical_scrollytelling_track": _render_scrollytelling_track,
}


def render_domain_specialist_layout(
    stage,
    layout: str,
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> bool:
    """Dispatches any of the 30 domain-specialist & 2026 UI layouts cleanly. Returns True if rendered."""
    fn = _SPECIALIST_DISPATCH.get(str(layout or "").lower().strip())
    if fn is None:
        return False
    fn(stage, data, progress, world, helpers)
    return True
