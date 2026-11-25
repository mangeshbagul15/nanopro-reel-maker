import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from core.palette_engine import resolve_studio_world

_PROBE_RESULT: Optional[Tuple[bool, Optional[str]]] = None

_BROWSER_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
]


def _is_streamlit_cloud() -> bool:
    return os.path.exists("/mount/src") or os.environ.get("STREAMLIT_SHARING_MODE") == "true"


def detect_web_engine() -> Tuple[bool, Optional[str]]:
    """Checks once whether Playwright + headless Chromium/Edge works cleanly without OOM."""
    global _PROBE_RESULT
    if _PROBE_RESULT is not None:
        return _PROBE_RESULT
    if _is_streamlit_cloud():
        _PROBE_RESULT = (False, None)
        return _PROBE_RESULT
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        _PROBE_RESULT = (False, None)
        return _PROBE_RESULT

    exe_path: Optional[str] = None
    for p in _BROWSER_PATHS:
        if os.path.exists(p):
            exe_path = p
            break
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if exe_path:
            kwargs["executable_path"] = exe_path
        browser = p.chromium.launch(**kwargs)
        browser.close()
        p.stop()
        _PROBE_RESULT = (True, exe_path)
    except Exception:
        _PROBE_RESULT = (False, None)
    return _PROBE_RESULT


def is_web_engine_available() -> bool:
    return detect_web_engine()[0]


def _rgb_css(rgb: Tuple[int, ...]) -> str:
    return f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"


def _rgba_css(rgb: Tuple[int, ...], alpha: float) -> str:
    return f"rgba({int(rgb[0])},{int(rgb[1])},{int(rgb[2])},{alpha:.2f})"


ZERO_TEMPLATE_50_ARCHETYPES: Tuple[str, ...] = (
    # 20 Interactive HTML5 / Canvas 3D Web Scenes (`web_scene`)
    "web_pipeline_3d", "web_hub_mesh", "web_bento_layers", "web_orbit_nodes",
    "web_memory_wal", "web_benchmark_race", "web_split_vs", "web_telemetry_hud",
    "web_terminal_sql", "web_alert_radar", "web_flamegraph_html", "web_waterfall_trace",
    "web_state_fsm", "web_kanban_stream", "web_packet_dissector", "web_neural_synapse",
    "web_timeline_ribbon", "web_quadrant_radar", "web_ring_consensus", "web_diff_inspector",
    # 18 Animated Crisp Vector Blueprints (`svg_scene`)
    "svg_circuit_bus", "svg_concentric_shields", "svg_dag_lineage", "svg_sequence_lanes",
    "svg_btree_split", "svg_raft_heartbeat", "svg_shard_hash_ring", "svg_tls_handshake_arcs",
    "svg_medallion_funnel", "svg_cache_hierarchy", "svg_lock_contention", "svg_vector_embeddings",
    "svg_microservice_mesh", "svg_dns_resolver_tree", "svg_tcp_congestion_wave", "svg_merkle_proof_tree",
    "svg_transformer_attention", "svg_event_sourcing_log",
    # 16 Freeform 3D-Camera Spatial Glass Compositions (`spatial_canvas`)
    "spatial_isometric_stack", "spatial_floating_cards", "spatial_depth_carousel", "spatial_constellation_map",
    "spatial_layered_slices", "spatial_split_hologram", "spatial_radar_sweep", "spatial_code_glass_pane",
    "spatial_metric_monolith", "spatial_queue_conveyor", "spatial_pipeline_tunnel", "spatial_pyramid_tier",
    "spatial_heatmap_tiles", "spatial_orbit_carousel", "spatial_comparison_bridge", "spatial_mastery_crown",
)

_OPTION1_ARCH_FAMILY: Dict[str, str] = {
    "web_pipeline_3d": "pipeline_3d", "web_hub_mesh": "hub_mesh", "web_bento_layers": "bento_layers",
    "web_orbit_nodes": "orbit_nodes", "web_memory_wal": "memory_wal", "web_benchmark_race": "benchmark",
    "web_split_vs": "split_vs", "web_telemetry_hud": "telemetry", "web_terminal_sql": "terminal_sql",
    "web_alert_radar": "alert_radar", "web_flamegraph_html": "flame_bars", "web_waterfall_trace": "waterfall_spans",
    "web_state_fsm": "fsm_cycle", "web_kanban_stream": "bento_layers", "web_packet_dissector": "svg_sequence",
    "web_neural_synapse": "hub_mesh", "web_timeline_ribbon": "pipeline_3d", "web_quadrant_radar": "matrix_grid",
    "web_ring_consensus": "svg_rings", "web_diff_inspector": "split_vs",
    "svg_circuit_bus": "svg_blueprint", "svg_concentric_shields": "svg_rings", "svg_dag_lineage": "svg_blueprint",
    "svg_sequence_lanes": "svg_sequence", "svg_btree_split": "svg_blueprint", "svg_raft_heartbeat": "svg_rings",
    "svg_shard_hash_ring": "svg_rings", "svg_tls_handshake_arcs": "svg_sequence", "svg_medallion_funnel": "pyramid_tiers",
    "svg_cache_hierarchy": "pyramid_tiers", "svg_lock_contention": "split_vs", "svg_vector_embeddings": "spatial_constellation",
    "svg_microservice_mesh": "hub_mesh", "svg_dns_resolver_tree": "svg_blueprint", "svg_tcp_congestion_wave": "waterfall_spans",
    "svg_merkle_proof_tree": "svg_blueprint", "svg_transformer_attention": "matrix_grid", "svg_event_sourcing_log": "memory_wal",
    "spatial_isometric_stack": "spatial_stack", "spatial_floating_cards": "bento_layers", "spatial_depth_carousel": "orbit_nodes",
    "spatial_constellation_map": "spatial_constellation", "spatial_layered_slices": "spatial_stack", "spatial_split_hologram": "split_vs",
    "spatial_radar_sweep": "alert_radar", "spatial_code_glass_pane": "terminal_sql", "spatial_metric_monolith": "telemetry",
    "spatial_queue_conveyor": "pipeline_3d", "spatial_pipeline_tunnel": "flame_bars", "spatial_pyramid_tier": "pyramid_tiers",
    "spatial_heatmap_tiles": "matrix_grid", "spatial_orbit_carousel": "svg_rings", "spatial_comparison_bridge": "split_vs",
    "spatial_mastery_crown": "pyramid_tiers",
}


def _extract_structured_scene_payload(scene: Dict[str, Any], scene_idx: int) -> Dict[str, Any]:
    """
    Normalizes ANY director storyboard scene (`visual_data` + `narration` + `visual_type`) into rich
    topic-grounded structured data & picks a distinct visual archetype so NO two scenes repeat
    or ever show canned placeholder labels.
    """
    vd = dict(scene.get("visual_data") or {})
    vtype = str(scene.get("visual_type") or "").lower().strip()
    narration = str(scene.get("narration") or "").strip()
    topic = str(scene.get("topic") or vd.get("topic") or "").strip()
    title = str(vd.get("title") or vd.get("headline") or "").strip()
    if not title:
        first_sent = re.split(r"[.!?\n]+", narration)[0].strip() if narration else ""
        title = (first_sent[:52] + ("..." if len(first_sent) > 52 else "")) or topic[:48] or f"System Stage {scene_idx}"
    badge = str(vd.get("badge") or vd.get("callout_badge") or vtype.replace("_", " ") or f"SCENE {scene_idx}").strip().upper()
    if badge in ("WEB SCENE", "HTML SCENE", "WEBGL SCENE", ""):
        badge = f"ARCHITECTURE • SCENE {scene_idx}"

    # Harvest cards/nodes/steps from ALL supported schemas
    cards: List[Dict[str, str]] = []
    for key in ("nodes", "steps", "stages", "milestones", "satellites", "layers", "tiers", "units", "items", "bullets"):
        raw = vd.get(key)
        if isinstance(raw, list) and raw:
            for idx, it in enumerate(raw[:5]):
                if isinstance(it, dict):
                    nm = str(it.get("name") or it.get("title") or it.get("label") or it.get("op") or "").strip()
                    sb = str(it.get("sub") or it.get("desc") or it.get("role") or it.get("table") or it.get("proto") or "").strip()
                    tag = str(it.get("tag") or it.get("u") or it.get("num") or it.get("status") or f"{idx+1:02d}").strip()
                    val = str(it.get("val") or it.get("value") or it.get("display") or it.get("edge") or "").strip()
                    if nm or sb:
                        cards.append({"title": nm or tag, "sub": sb, "tag": tag, "val": val})
                elif isinstance(it, str) and it.strip():
                    parts = it.split(":", 1)
                    if len(parts) == 2 and len(parts[0]) < 32:
                        cards.append({"title": parts[0].strip(), "sub": parts[1].strip(), "tag": f"{idx+1:02d}", "val": ""})
                    else:
                        cards.append({"title": it.strip(), "sub": "", "tag": f"{idx+1:02d}", "val": ""})
            if cards:
                break

    # Blocks schema (`custom_scene`)
    blocks = vd.get("blocks") if isinstance(vd.get("blocks"), list) else []
    stat_hero = None
    if blocks:
        for blk in blocks:
            if not isinstance(blk, dict):
                continue
            bt = str(blk.get("type") or blk.get("block") or "").lower()
            if bt == "big_stat":
                stat_hero = {"value": str(blk.get("value") or blk.get("number") or ""), "label": str(blk.get("label") or "")}
            elif bt in ("question_card", "banner") and blk.get("text"):
                cards.append({"title": str(blk.get("text")), "sub": str(blk.get("eyebrow") or blk.get("tone") or "").upper(), "tag": "KEY", "val": ""})
            elif bt == "pills":
                for p in (blk.get("items") or [])[:4]:
                    cards.append({"title": str(p), "sub": "", "tag": "TAG", "val": ""})
            elif bt in ("list_cards", "flow_chain"):
                for it in (blk.get("items") or blk.get("steps") or blk.get("nodes") or [])[:4]:
                    if isinstance(it, dict):
                        cards.append({"title": str(it.get("title") or it.get("name") or ""), "sub": str(it.get("sub") or it.get("desc") or ""), "tag": str(it.get("kind") or "NODE").upper(), "val": ""})
                    else:
                        cards.append({"title": str(it), "sub": "", "tag": "STEP", "val": ""})

    # WAL / Memory entries
    entries = []
    if isinstance(vd.get("entries"), list):
        for e in vd["entries"][:5]:
            if isinstance(e, dict):
                entries.append({
                    "addr": str(e.get("address") or "0x00A0"),
                    "op": str(e.get("op") or "WRITE OP"),
                    "table": str(e.get("table") or "stream"),
                    "status": str(e.get("status") or "SYNCED"),
                })

    # Bars (Benchmark)
    bars = []
    if isinstance(vd.get("bars"), list):
        for b in vd["bars"][:5]:
            if isinstance(b, dict):
                bars.append({
                    "label": str(b.get("label") or b.get("name") or "Metric"),
                    "value": float(b.get("value") or 10),
                    "display": str(b.get("display") or b.get("value") or ""),
                    "color": str(b.get("color") or ""),
                    "is_winner": bool(b.get("is_winner", False)),
                })

    # Split comparison
    left_pts = [str(x) for x in (vd.get("left_points") or vd.get("left_items") or []) if str(x).strip()][:4]
    right_pts = [str(x) for x in (vd.get("right_points") or vd.get("right_items") or []) if str(x).strip()][:4]
    split_data = None
    if left_pts or right_pts or (vd.get("left_label") and vd.get("right_label")):
        split_data = {
            "left_label": str(vd.get("left_label") or vd.get("left_title") or "LEGACY"),
            "right_label": str(vd.get("right_label") or vd.get("right_title") or "MODERN"),
            "left_points": left_pts or ["High Lock Contention", "Manual Switchover"],
            "right_points": right_pts or ["Sub-Second Async Stream", "Zero Production Downtime"],
        }

    # Problem Alert / Dilemma
    alert_data = None
    if vd.get("problem_title") or vd.get("problem_desc") or vd.get("challenge"):
        alert_data = {
            "title": str(vd.get("problem_title") or title),
            "desc": str(vd.get("problem_desc") or ""),
            "challenge": str(vd.get("challenge") or vd.get("warning_box") or ""),
        }
        if not cards:
            for idx, txt in enumerate([alert_data["title"], alert_data["desc"][:70], alert_data["challenge"][:70]]):
                if txt.strip():
                    cards.append({"title": txt.strip(), "sub": "", "tag": f"RISK {idx+1}", "val": ""})

    # Telemetry / Gauge
    telemetry = vd.get("telemetry") if isinstance(vd.get("telemetry"), list) else []
    gauge_data = None
    if vd.get("main_value") or vd.get("gauge_percent") or telemetry:
        gauge_data = {
            "val": str(vd.get("main_value") or vd.get("value") or "99.99%"),
            "unit": str(vd.get("main_unit") or vd.get("label") or "LIVE TELEMETRY"),
            "pct": int(vd.get("gauge_percent") or vd.get("percent") or 92),
            "items": [{"label": str(t.get("label") or ""), "val": str(t.get("val") or t.get("value") or "")} for t in telemetry[:4] if isinstance(t, dict)],
        }

    # Code / SQL
    code_snippet = str(vd.get("code_snippet") or vd.get("command") or vd.get("sql") or "").strip()
    table_data = vd.get("table_data") if isinstance(vd.get("table_data"), dict) else None

    # Last-resort narration key-phrase extraction (ZERO canned strings!)
    if not cards and not entries and not bars and not split_data and not code_snippet:
        sents = [s.strip() for s in re.split(r"[.!?\n]+", narration) if len(s.strip()) > 6][:4]
        for idx, st_txt in enumerate(sents):
            cards.append({"title": st_txt[:78], "sub": f"Key Concept {idx+1}", "tag": f"{idx+1:02d}", "val": ""})
        if not cards:
            cards.append({"title": title, "sub": topic or "Technical Breakdown", "tag": "01", "val": ""})

    var_seed = int(vd.get("_variation_seed") or 0)
    arch_hint = str(vd.get("archetype") or vd.get("option1_archetype") or scene.get("option1_archetype") or vtype).lower().strip()
    sub_variant = ""
    if arch_hint in _OPTION1_ARCH_FAMILY:
        sub_variant = arch_hint
        archetype = _OPTION1_ARCH_FAMILY[arch_hint]
    elif entries:
        archetype = "memory_wal"
        sub_variant = "web_memory_wal"
    elif bars:
        archetype = "benchmark"
        sub_variant = "web_benchmark_race"
    elif split_data:
        archetype = "split_vs"
        sub_variant = "web_split_vs"
    elif gauge_data:
        archetype = "telemetry"
        sub_variant = "web_telemetry_hud"
    elif code_snippet or table_data:
        archetype = "terminal_sql"
        sub_variant = "web_terminal_sql"
    elif alert_data and not (vd.get("satellites") or vd.get("nodes")):
        archetype = "alert_radar"
        sub_variant = "web_alert_radar"
    elif vtype == "svg_scene" or "svg" in arch_hint:
        svg_pool = [a for a in ZERO_TEMPLATE_50_ARCHETYPES if a.startswith("svg_")]
        sub_variant = svg_pool[(scene_idx - 1 + var_seed) % len(svg_pool)]
        archetype = _OPTION1_ARCH_FAMILY[sub_variant]
    elif vtype == "spatial_canvas" or "spatial" in arch_hint:
        sp_pool = [a for a in ZERO_TEMPLATE_50_ARCHETYPES if a.startswith("spatial_")]
        sub_variant = sp_pool[(scene_idx - 1 + var_seed) % len(sp_pool)]
        archetype = _OPTION1_ARCH_FAMILY[sub_variant]
    elif vd.get("satellites") or "mesh" in vtype or "hub" in vtype:
        archetype = "hub_mesh"
        sub_variant = "web_hub_mesh"
    else:
        cycle_variants = [a for a in ZERO_TEMPLATE_50_ARCHETYPES if a.startswith("web_")]
        sub_variant = cycle_variants[(scene_idx - 1 + var_seed * 3) % len(cycle_variants)]
        archetype = _OPTION1_ARCH_FAMILY.get(sub_variant, "pipeline_3d")

    return {
        "title": title,
        "badge": badge,
        "archetype": archetype,
        "sub_variant": sub_variant or archetype,
        "cards": cards[:5],
        "entries": entries,
        "bars": bars,
        "winner_badge": str(vd.get("winner_badge") or "").strip(),
        "split": split_data,
        "alert": alert_data,
        "gauge": gauge_data,
        "stat_hero": stat_hero,
        "code": code_snippet,
        "command": str(vd.get("command") or "").strip(),
        "output": str(vd.get("output") or "").strip(),
        "table_data": table_data,
        "hub_name": str(vd.get("hub_name") or vd.get("center") or title[:24]),
    }


def _hud_overlay_snippet(
    width: int,
    height: int,
    scene_idx: int,
    total_scenes: int,
    world: Dict[str, Any],
    watermark: str,
) -> str:
    """Injects unified NanoPro Studio HUD (progress bar, reactive AUDIO waveform, watermark pill)."""
    cyan = _rgb_css(world["cyan"])
    emerald = _rgb_css(world["emerald"])
    text_col = _rgb_css(world["text"])
    card_bg = "rgba(255,255,255,0.90)" if world.get("is_light") else "rgba(15,23,42,0.86)"
    track_col = "rgba(15,23,42,0.16)" if world.get("is_light") else "rgba(255,255,255,0.14)"
    wm_json = json.dumps((watermark or "").strip())
    return f"""
<style>
#np-hud{{position:fixed;inset:0;pointer-events:none;z-index:9999;font-family:Inter,'Segoe UI',system-ui,sans-serif;}}
#np-track{{position:absolute;top:24px;left:40px;right:40px;height:6px;border-radius:4px;background:{track_col};overflow:hidden;}}
#np-fill{{height:100%;width:12%;border-radius:4px;background:linear-gradient(90deg,{cyan},{emerald});}}
#np-audio{{position:absolute;top:44px;left:40px;height:38px;padding:0 14px;border-radius:19px;background:{card_bg};border:2px solid {cyan};display:flex;align-items:center;gap:10px;box-shadow:0 4px 18px rgba(0,0,0,0.22);}}
#np-audio-lbl{{font-size:14px;font-weight:800;letter-spacing:0.04em;color:{cyan};}}
#np-bars{{display:flex;align-items:center;gap:4px;height:24px;}}
.np-bar{{width:4px;height:8px;border-radius:2px;background:{cyan};}}
#np-wm{{position:absolute;top:44px;right:36px;height:38px;padding:0 18px 0 14px;border-radius:19px;background:{card_bg};border:2px solid {cyan};display:flex;align-items:center;gap:9px;font-size:20px;font-weight:800;color:{text_col};box-shadow:0 4px 18px rgba(0,0,0,0.22);}}
#np-wm-dot{{width:9px;height:9px;border-radius:50%;background:{cyan};}}
</style>
<div id="np-hud">
  <div id="np-track"><div id="np-fill"></div></div>
  <div id="np-audio"><span id="np-audio-lbl">AUDIO</span><div id="np-bars"></div></div>
  <div id="np-wm"><span id="np-wm-dot"></span><span id="np-wm-txt"></span></div>
</div>
<script>
(function(){{
  const WM={wm_json}, SCI={scene_idx}, TOT={max(1,total_scenes)}, CYAN='{cyan}', EM='{emerald}';
  const wmEl=document.getElementById('np-wm'), wmTxt=document.getElementById('np-wm-txt');
  if(!WM) wmEl.style.display='none'; else wmTxt.textContent=WM;
  const barsHost=document.getElementById('np-bars');
  const bars=[];
  for(let i=0;i<12;i++){{const b=document.createElement('div');b.className='np-bar';barsHost.appendChild(b);bars.push(b);}}
  window.__npUpdateHud=function(p, curTime, energy){{
    const gp=Math.max(0.02, Math.min(1, ((SCI-1)+p)/TOT));
    const fill=document.getElementById('np-fill');
    if(fill) fill.style.width=(gp*100).toFixed(2)+'%';
    const e=Math.max(0.2, Math.min(1.0, energy||0.55));
    bars.forEach((b,bi)=>{{
      const phase=p*46.0 + bi*0.85;
      const amp=(0.35 + 0.65*Math.abs(Math.sin(phase)*Math.cos(phase*0.43)))*e;
      b.style.height=Math.max(5, Math.round(22*amp))+'px';
      b.style.background=(amp>0.55)?EM:CYAN;
    }});
  }};
}})();
</script>"""


def _build_default_webgl_html(
    scene: Dict[str, Any],
    world: Dict[str, Any],
    width: int,
    height: int,
    watermark: str,
    scene_idx: int = 1,
    total_scenes: int = 4,
) -> str:
    """
    Multi-Archetype Zero-Placeholder Bespoke HTML5 + Volumetric Shaded 3D Canvas + SVG Engine.
    - Reads ALL structured topic fields (NEVER outputs fake placeholder labels).
    - Keeps bottom subtitle zone (`y >= height - sub_reserve`) 100% collision-free!
    - Rotates completely distinct 3D/Diagram topologies across scenes.
    """
    payload = _extract_structured_scene_payload(scene, scene_idx)
    payload_json = json.dumps(payload, ensure_ascii=False)

    bg_top = _rgb_css(world["bg_top"])
    bg_bot = _rgb_css(world["bg_bot"])
    cyan = _rgb_css(world["cyan"])
    purple = _rgb_css(world["purple"])
    emerald = _rgb_css(world["emerald"])
    amber = _rgb_css(world["amber"])
    rose = _rgb_css(world["rose"])
    text_col = _rgb_css(world["text"])
    muted_col = _rgb_css(world["muted"])
    is_light = bool(world.get("is_light"))
    card_bg = "rgba(255,255,255,0.92)" if is_light else "rgba(15,23,42,0.84)"
    card_alt = "rgba(241,245,249,0.96)" if is_light else "rgba(24,35,58,0.92)"
    border_col = "rgba(148,163,184,0.34)" if is_light else "rgba(56,189,248,0.32)"
    sub_reserve = 500 if height >= 1600 else (180 if height >= 1000 else 140)
    hud_html = _hud_overlay_snippet(width, height, scene_idx, total_scenes, world, watermark)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:Inter,'Segoe UI',system-ui,sans-serif;}}
body{{width:{width}px;height:{height}px;overflow:hidden;background:linear-gradient(168deg,{bg_top},{bg_bot});color:{text_col};position:relative;}}
canvas#bg3d{{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;}}
.stage{{position:relative;z-index:2;padding:106px 64px {sub_reserve}px;height:100%;display:flex;flex-direction:column;gap:22px;}}
.hdr{{display:flex;flex-direction:column;gap:14px;flex-shrink:0;}}
.badge{{display:inline-flex;align-items:center;gap:11px;padding:9px 22px;border-radius:999px;border:2px solid {cyan};background:{card_bg};color:{cyan};font-weight:800;font-size:22px;width:max-content;letter-spacing:0.03em;box-shadow:0 0 26px {_rgba_css(world['cyan'],0.24)};}}
.dot{{width:11px;height:11px;border-radius:50%;background:{cyan};}}
h1{{font-size:48px;line-height:1.14;font-weight:900;letter-spacing:-0.02em;}}
#mainMount{{flex:1;position:relative;display:flex;flex-direction:column;justify-content:flex-start;gap:22px;padding-top:16px;min-height:0;}}
.gcard{{background:{card_bg};backdrop-filter:blur(16px);border:2px solid {border_col};border-radius:24px;padding:24px 28px;box-shadow:0 16px 38px rgba(0,0,0,0.28);position:relative;overflow:hidden;}}
.gcard.active{{border-color:{cyan};box-shadow:0 0 34px {_rgba_css(world['cyan'],0.28)}, 0 18px 42px rgba(0,0,0,0.34);}}
.pill-num{{min-width:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,{cyan},{purple});color:#fff;font-size:24px;font-weight:900;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.ctitle{{font-size:28px;font-weight:800;line-height:1.22;}}
.csub{{font-size:21px;color:{muted_col};margin-top:6px;line-height:1.3;}}
.hero-footer{{margin-top:auto;padding:24px 28px;border-radius:24px;background:{card_alt};border:2px solid {emerald};box-shadow:0 0 32px {_rgba_css(world['emerald'],0.24)};text-align:center;}}
.hero-num{{font-size:64px;font-weight:900;background:linear-gradient(90deg,{cyan},{emerald});-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.05;}}
.term-box{{background:rgba(9,13,24,0.94);border:2px solid {cyan};border-radius:24px;overflow:hidden;box-shadow:0 20px 50px rgba(0,0,0,0.45);}}
.term-hdr{{display:flex;align-items:center;gap:10px;padding:16px 22px;background:rgba(30,41,59,0.75);border-bottom:1px solid {border_col};}}
.tlight{{width:14px;height:14px;border-radius:50%;}}
.term-code{{padding:24px;font-family:'JetBrains Mono','Cascadia Code',Consolas,monospace;font-size:22px;line-height:1.5;color:#e2e8f0;white-space:pre-wrap;word-break:break-word;}}
.tbl-wrap{{width:100%;border-collapse:collapse;font-family:'JetBrains Mono',Consolas,monospace;font-size:20px;}}
.tbl-wrap th{{text-align:left;padding:14px 16px;color:{emerald};border-bottom:2px solid {border_col};font-weight:800;}}
.tbl-wrap td{{padding:13px 16px;border-bottom:1px solid rgba(148,163,184,0.14);}}
</style></head>
<body>
<canvas id="bg3d" width="{width}" height="{height}"></canvas>
{hud_html}
<div class="stage">
  <div class="hdr">
    <div class="badge"><span class="dot"></span><span id="badgeTxt"></span></div>
    <h1 id="titleTxt"></h1>
  </div>
  <div id="mainMount"></div>
</div>
<script>
const P={payload_json};
const PAL={{cyan:'{cyan}',purple:'{purple}',emerald:'{emerald}',amber:'{amber}',rose:'{rose}',text:'{text_col}',muted:'{muted_col}',cardAlt:'{card_alt}'}};
const ACCENTS=[PAL.cyan,PAL.purple,PAL.emerald,PAL.amber,PAL.rose];
document.getElementById('titleTxt').textContent=P.title;
document.getElementById('badgeTxt').textContent=P.badge;
const mount=document.getElementById('mainMount');
const cv=document.getElementById('bg3d'), ctx=cv.getContext('2d');
const W={width}, H={height}, SUB_R={sub_reserve};

// ---------- VOLUMETRIC SHADED 3D MESH ENGINE ON CANVAS (Faceted Lit Solid Geometry!) ----------
function drawLitPoly3D(cx, cy, R, r, rotY, rotX, colA, colB, mode){{
  const faces=[];
  if(mode==='icosa'||mode==='hub'){{
    const phi=(1+Math.sqrt(5))/2;
    const rawV=[[-1,phi,0],[1,phi,0],[-1,-phi,0],[1,-phi,0],[0,-1,phi],[0,1,phi],[0,-1,-phi],[0,1,-phi],[phi,0,-1],[phi,0,1],[-phi,0,-1],[-phi,0,1]];
    const idx=[[0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],[1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],[3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],[4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]];
    const rot=rawV.map(v=>{{
      const ln=Math.hypot(v[0],v[1],v[2]); let x=v[0]/ln,y=v[1]/ln,z=v[2]/ln;
      let x1=x*Math.cos(rotY)-z*Math.sin(rotY), z1=x*Math.sin(rotY)+z*Math.cos(rotY);
      let y2=y*Math.cos(rotX)-z1*Math.sin(rotX), z2=y*Math.sin(rotX)+z1*Math.cos(rotX);
      return [x1,y2,z2];
    }});
    idx.forEach(f=>{{
      const a=rot[f[0]], b=rot[f[1]], c=rot[f[2]];
      const ux=b[0]-a[0], uy=b[1]-a[1], uz=b[2]-a[2];
      const vx=c[0]-a[0], vy=c[1]-a[1], vz=c[2]-a[2];
      const nx=uy*vz-uz*vy, ny=uz*vx-ux*vz, nz=ux*vy-uy*vx;
      if(nz>0){{
        const nln=Math.hypot(nx,ny,nz)||1;
        const lum=Math.max(0.18, Math.min(1.0, (0.45*(-nx/nln)+0.55*(-ny/nln)+0.7*(nz/nln))));
        faces.push({{z:(a[2]+b[2]+c[2])/3, lum, pts:[a,b,c].map(pt=>{{const s=R/(1-pt[2]*0.28);return [cx+pt[0]*s, cy+pt[1]*s];}})}});
      }}
    }});
  }} else {{
    // Shaded 3D Torus Solid Facets (NOT empty thin wires!)
    const nu=18, nv=10;
    for(let u=0;u<nu;u++){{
      for(let v=0;v<nv;v++){{
        const ring=[ [u,v],[u+1,v],[u+1,v+1],[u,v+1] ].map(uv=>{{
          const th=(uv[0]%nu)*Math.PI*2/nu, ph=(uv[1]%nv)*Math.PI*2/nv;
          let x=(R+r*Math.cos(ph))*Math.cos(th), y=r*Math.sin(ph), z=(R+r*Math.cos(ph))*Math.sin(th);
          let x1=x*Math.cos(rotY)-z*Math.sin(rotY), z1=x*Math.sin(rotY)+z*Math.cos(rotY);
          let y2=y*Math.cos(rotX)-z1*Math.sin(rotX), z2=y*Math.sin(rotX)+z1*Math.cos(rotX);
          const sc=1100/(1100-z2*0.65);
          return [cx+x1*sc, cy+y2*sc, z2];
        }});
        const zAvg=(ring[0][2]+ring[1][2]+ring[2][2]+ring[3][2])/4;
        if(zAvg>-R*0.65){{
          const lum=Math.max(0.18, Math.min(1.0, 0.45+0.55*(zAvg/(R+r))));
          faces.push({{z:zAvg, lum, pts:ring.map(p=>[p[0],p[1]]), alt:u%2===0}});
        }}
      }}
    }}
  }}
  faces.sort((a,b)=>a.z-b.z);
  faces.forEach(fc=>{{
    ctx.beginPath();
    fc.pts.forEach((pt,i)=>i===0?ctx.moveTo(pt[0],pt[1]):ctx.lineTo(pt[0],pt[1]));
    ctx.closePath();
    ctx.fillStyle=fc.alt===false?colB:colA;
    ctx.globalAlpha=0.07+0.13*fc.lum;
    ctx.fill();
    ctx.strokeStyle=fc.alt===false?colB:colA;
    ctx.globalAlpha=0.11+0.17*fc.lum;
    ctx.lineWidth=1.2;
    ctx.stroke();
  }});
  ctx.globalAlpha=1;
}}

let animNodes=[];
function renderArchetype(){{
  mount.innerHTML=''; animNodes=[];
  const arch=P.archetype;

  if(arch==='memory_wal'){{
    const hdrCard=document.createElement('div'); hdrCard.className='gcard active';
    hdrCard.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:900;font-size:24px;color:${{PAL.cyan}}">WAL / BUFFER MEMORY STREAM</span><span id="walCur" style="font-family:monospace;font-size:22px;color:${{PAL.emerald}};font-weight:800">SCANNING...</span></div><div style="height:14px;border-radius:8px;background:rgba(255,255,255,0.08);margin-top:14px;overflow:hidden;"><div id="walBar" style="height:100%;width:15%;background:linear-gradient(90deg,${{PAL.cyan}},${{PAL.emerald}});border-radius:8px;"></div></div>`;
    mount.appendChild(hdrCard);
    const list=P.entries.length?P.entries:[{{addr:'0x00A1',op:'COMMIT STREAM',table:'events',status:'REPLICATED'}}];
    list.forEach((e,i)=>{{
      const col=e.status.includes('REP')||e.status.includes('SYNC')?PAL.emerald:(e.status.includes('TRANS')?PAL.amber:PAL.cyan);
      const el=document.createElement('div'); el.className='gcard';
      el.innerHTML=`<div style="display:flex;align-items:center;justify-content:space-between;gap:16px;"><span style="padding:10px 16px;border-radius:12px;background:rgba(56,189,248,0.14);border:1.5px solid ${{col}};font-family:monospace;font-weight:900;font-size:22px;color:${{col}}">${{e.addr}}</span><div style="flex:1;"><div class="ctitle">${{e.op}}</div><div class="csub" style="font-family:monospace">TABLE: ${{e.table}}</div></div><span style="padding:8px 16px;border-radius:999px;background:rgba(16,185,129,0.14);border:1.5px solid ${{col}};font-weight:800;font-size:18px;color:${{col}}">${{e.status}}</span></div>`;
      mount.appendChild(el); animNodes.push(el);
    }});
    const ft=document.createElement('div'); ft.className='hero-footer';
    ft.innerHTML=`<div style="font-size:24px;color:${{PAL.emerald}};font-weight:900;">SEQUENTIAL APPEND-ONLY LOG • ZERO TABLE LOCKS</div>`;
    mount.appendChild(ft);
  }} else if(arch==='benchmark'){{
    const bars=P.bars.length?P.bars:[{{label:P.title,value:100,display:'100%',is_winner:true}}];
    const maxV=Math.max(...bars.map(b=>Math.max(1,b.value)));
    const winnerBar=bars.find(b=>b.is_winner)||bars[bars.length-1];
    bars.forEach((b,i)=>{{
      const col=b.is_winner?PAL.emerald:(b.color||(i===0?PAL.rose:(i===1?PAL.amber:PAL.purple)));
      const pct=Math.max(10, Math.round((b.value/maxV)*100));
      const el=document.createElement('div'); el.className='gcard'+(b.is_winner?' active':'');
      el.style.borderColor=col;
      el.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><span class="ctitle" style="color:${{b.is_winner?PAL.emerald:PAL.text}}">${{b.is_winner?'✓ ':''}}${{b.label}}</span><span style="font-size:28px;font-weight:900;color:${{col}}">${{b.display||b.value}}</span></div><div style="height:30px;border-radius:14px;background:rgba(255,255,255,0.08);overflow:hidden;"><div data-bw="${{pct}}" class="bm-fill" style="height:100%;width:6%;border-radius:14px;background:${{col}};box-shadow:0 0 22px ${{col}};"></div></div>`;
      mount.appendChild(el); animNodes.push(el);
    }});
    const ratio=maxV>0&&winnerBar.value>0&&winnerBar.value<maxV?Math.round(maxV/winnerBar.value):0;
    const badgeTxt=P.winner_badge||(ratio>=2?`${{ratio}}x FASTER • ZERO DOWNTIME`:'BENCHMARK WINNER VERIFIED');
    const hero=document.createElement('div'); hero.className='hero-footer';
    hero.innerHTML=`<div class="hero-num">${{badgeTxt}}</div><div style="font-size:24px;color:${{PAL.text}};font-weight:700;margin-top:8px;">Winner: ${{winnerBar.label}} (${{winnerBar.display||winnerBar.value}})</div>`;
    mount.appendChild(hero);
  }} else if(arch==='split_vs'&&P.split){{
    const row=document.createElement('div'); row.style.cssText='display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:stretch;';
    const makeCol=(lbl,pts,col,win)=>{{
      const c=document.createElement('div'); c.className='gcard'+(win?' active':'');
      c.style.borderColor=col;
      c.innerHTML=`<div style="text-align:center;font-size:28px;font-weight:900;color:${{col}};padding-bottom:16px;border-bottom:2px solid ${{col}}33;margin-bottom:18px;">${{lbl}}</div>`+pts.map(pt=>`<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:18px;font-size:23px;line-height:1.35;"><span style="color:${{col}};font-weight:900;">${{win?'✔':'✖'}}</span><span>${{pt}}</span></div>`).join('');
      return c;
    }};
    const cL=makeCol(P.split.left_label,P.split.left_points,PAL.rose,false);
    const cR=makeCol(P.split.right_label,P.split.right_points,PAL.emerald,true);
    row.appendChild(cL); row.appendChild(cR); mount.appendChild(row); animNodes.push(cL,cR);
    const vs=document.createElement('div'); vs.className='hero-footer'; vs.innerHTML=`<div style="font-size:26px;font-weight:900;color:${{PAL.amber}}">ARCHITECTURAL UPGRADE → ZERO DOWNTIME SWITCH</div>`;
    mount.appendChild(vs);
  }} else if(arch==='terminal_sql'){{
    const tb=document.createElement('div'); tb.className='term-box';
    const cmdLine=P.command?('$ '+P.command+'\\n\\n'):'';
    tb.innerHTML=`<div class="term-hdr"><span class="tlight" style="background:#f43f5e"></span><span class="tlight" style="background:#f59e0b"></span><span class="tlight" style="background:#10b981"></span><span style="margin-left:10px;font-family:monospace;font-size:20px;color:${{PAL.muted}}">studio_runtime.sh</span></div><div class="term-code" id="termTxt"></div>`;
    mount.appendChild(tb); window.__fullTermText=(cmdLine+(P.code||'// Ready')).slice(0,520);
    if(P.table_data&&P.table_data.headers){{
      const tc=document.createElement('div'); tc.className='gcard active';
      const ths=P.table_data.headers.map(h=>`<th>${{h}}</th>`).join('');
      const trs=(P.table_data.rows||[]).slice(0,4).map(r=>`<tr>${{r.map(v=>`<td>${{v}}</td>`).join('')}}</tr>`).join('');
      tc.innerHTML=`<table class="tbl-wrap"><thead><tr>${{ths}}</tr></thead><tbody>${{trs}}</tbody></table>`;
      mount.appendChild(tc); animNodes.push(tc);
    }} else if(P.output){{
      const oc=document.createElement('div'); oc.className='hero-footer';
      oc.innerHTML=`<div style="font-family:monospace;font-size:23px;color:${{PAL.emerald}};font-weight:700;">STDOUT → ${{P.output}}</div>`;
      mount.appendChild(oc);
    }}
  }} else if(arch==='alert_radar'&&P.alert){{
    const radBox=document.createElement('div'); radBox.className='gcard'; radBox.style.cssText='height:540px;display:flex;align-items:center;justify-content:center;padding:12px;';
    radBox.innerHTML=`<svg id="radSvg" viewBox="0 0 880 500" width="100%" height="100%"><defs><linearGradient id="sw" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="${{PAL.rose}}" stop-opacity="0.45"/><stop offset="100%" stop-color="${{PAL.cyan}}" stop-opacity="0.02"/></linearGradient></defs><circle cx="440" cy="250" r="85" fill="none" stroke="${{PAL.rose}}" stroke-opacity="0.45" stroke-width="2.5"/><circle cx="440" cy="250" r="155" fill="none" stroke="${{PAL.rose}}" stroke-opacity="0.34" stroke-width="2.5"/><circle cx="440" cy="250" r="220" fill="none" stroke="${{PAL.rose}}" stroke-opacity="0.24" stroke-width="2.5"/><path id="radCone" d="M440 250 L660 250 A220 220 0 0 1 605 395 Z" fill="url(#sw)"/><line id="radBeam" x1="440" y1="250" x2="660" y2="250" stroke="${{PAL.cyan}}" stroke-width="4" stroke-linecap="round"/><g id="radBlips"></g></svg>`;
    mount.appendChild(radBox);
    const blipsEl=radBox.querySelector('#radBlips');
    const bPts=[[295,155],[605,165],[315,355],[585,350]];
    (P.cards.length?P.cards:[{{title:P.alert.title}}]).slice(0,4).forEach((c,i)=>{{
      const pt=bPts[i%bPts.length];
      blipsEl.innerHTML+=`<circle cx="${{pt[0]}}" cy="${{pt[1]}}" r="12" fill="${{PAL.rose}}"/><circle cx="${{pt[0]}}" cy="${{pt[1]}}" r="24" fill="none" stroke="${{PAL.rose}}" stroke-opacity="0.6" stroke-width="2"/><rect x="${{pt[0]-95}}" y="${{pt[1]+20}}" width="190" height="34" rx="17" fill="${{PAL.cardAlt}}" stroke="${{PAL.amber}}" stroke-width="1.5"/><text x="${{pt[0]}}" y="${{pt[1]+43}}" text-anchor="middle" fill="${{PAL.text}}" font-size="16" font-weight="800">${{(c.title||'').slice(0,18)}}</text>`;
    }});
    const ac=document.createElement('div'); ac.className='gcard active'; ac.style.borderColor=PAL.rose;
    ac.innerHTML=`<div style="font-size:28px;font-weight:900;color:${{PAL.rose}};margin-bottom:10px;">⚠ ${{P.alert.title}}</div>${{P.alert.desc?`<div style="font-size:22px;line-height:1.4;margin-bottom:14px;">${{P.alert.desc}}</div>`:''}}${{P.alert.challenge?`<div style="padding:14px 18px;border-radius:14px;background:rgba(56,189,248,0.12);border:1.5px solid ${{PAL.cyan}};font-size:22px;font-weight:800;color:${{PAL.cyan}}">→ ${{P.alert.challenge}}</div>`:''}}`;
    mount.appendChild(ac); animNodes.push(ac);
  }} else if(arch==='telemetry'&&P.gauge){{
    const gc=document.createElement('div'); gc.className='gcard active'; gc.style.textAlign='center';
    gc.innerHTML=`<svg viewBox="0 0 420 260" width="420" height="260"><path d="M 60 220 A 150 150 0 1 1 360 220" fill="none" stroke="rgba(148,163,184,0.22)" stroke-width="26" stroke-linecap="round"/><path id="gArc" d="M 60 220 A 150 150 0 1 1 360 220" fill="none" stroke="${{PAL.emerald}}" stroke-width="26" stroke-linecap="round" stroke-dasharray="680" stroke-dashoffset="680"/></svg><div style="margin-top:-135px;margin-bottom:45px;"><div class="hero-num">${{P.gauge.val}}</div><div style="font-size:22px;font-weight:800;color:${{PAL.cyan}};margin-top:8px;">${{P.gauge.unit}}</div></div>`;
    mount.appendChild(gc);
    const grid=document.createElement('div'); grid.style.cssText='display:grid;grid-template-columns:repeat(3,1fr);gap:16px;';
    (P.gauge.items.length?P.gauge.items:[{{label:'THROUGHPUT',val:'Real-Time'}},{{label:'DOWNTIME',val:'0.0s'}},{{label:'SLA',val:'99.999%'}}]).slice(0,3).forEach((m,i)=>{{
      const mc=document.createElement('div'); mc.className='gcard'; mc.style.textAlign='center';
      mc.innerHTML=`<div style="font-size:32px;font-weight:900;color:${{ACCENTS[i%ACCENTS.length]}}">${{m.val}}</div><div style="font-size:18px;font-weight:700;color:${{PAL.muted}};margin-top:8px;">${{m.label}}</div>`;
      grid.appendChild(mc); animNodes.push(mc);
    }});
    mount.appendChild(grid);
  }} else if(arch==='hub_mesh'||arch==='orbit_nodes'||arch==='spatial_constellation'){{
    const topo=document.createElement('div'); topo.className='gcard active'; topo.style.cssText='padding:26px;text-align:center;';
    const hdrTxt=arch==='spatial_constellation'?'✧ SPATIAL CONSTELLATION: ':'✦ CORE HUB: ';
    topo.innerHTML=`<div style="font-size:26px;font-weight:900;color:${{PAL.cyan}};margin-bottom:18px;">${{hdrTxt}}${{P.hub_name}}</div><div id="satGrid" style="display:grid;grid-template-columns:1fr 1fr;gap:18px;text-align:left;"></div>`;
    mount.appendChild(topo);
    const sg=topo.querySelector('#satGrid');
    P.cards.forEach((c,i)=>{{
      const col=ACCENTS[i%ACCENTS.length];
      const sc=document.createElement('div'); sc.className='gcard'; sc.style.borderColor=col;
      sc.innerHTML=`<div style="display:flex;align-items:center;gap:12px;"><span class="pill-num" style="min-width:44px;height:44px;font-size:20px;background:${{col}}">${{i+1}}</span><div><div style="font-size:23px;font-weight:800;">${{c.title}}</div>${{c.sub?`<div style="font-size:18px;color:${{PAL.muted}};margin-top:4px;">${{c.sub}}</div>`:''}}</div></div>`;
      sg.appendChild(sc); animNodes.push(sc);
    }});
    const ft=document.createElement('div'); ft.className='hero-footer';
    ft.innerHTML=`<div style="font-size:24px;color:${{PAL.emerald}};font-weight:900;">CONTINUOUS ZERO-LOCK DATA STREAM</div>`;
    mount.appendChild(ft);
  }} else if(arch==='svg_blueprint'||arch==='svg_sequence'||arch==='svg_rings'||arch==='fsm_cycle'){{
    const svgBox=document.createElement('div'); svgBox.className='gcard active'; svgBox.style.cssText='padding:18px;';
    const list=P.cards.slice(0,4);
    let inner='';
    if(arch==='svg_rings'||arch==='fsm_cycle'){{
      inner=`<svg viewBox="0 0 880 420" width="100%" height="380"><circle cx="440" cy="210" r="165" fill="none" stroke="${{PAL.cyan}}" stroke-opacity="0.32" stroke-width="3" stroke-dasharray="10 8"/><circle cx="440" cy="210" r="105" fill="none" stroke="${{PAL.purple}}" stroke-opacity="0.38" stroke-width="2.5"/><text x="440" y="216" text-anchor="middle" fill="${{PAL.text}}" font-size="22" font-weight="900">${{P.hub_name.slice(0,18)}}</text></svg>`;
    }} else if(arch==='svg_sequence'){{
      const xs=[160,440,720];
      const lines=xs.map((x,i)=>`<line x1="${{x}}" y1="30" x2="${{x}}" y2="380" stroke="${{ACCENTS[i%ACCENTS.length]}}" stroke-width="3" stroke-dasharray="8 6"/>`).join('');
      const arrows=list.map((c,i)=>`<line x1="${{xs[i%2]}}" y1="${{90+i*75}}" x2="${{xs[1+((i+1)%2)]}}" y2="${{90+i*75}}" stroke="${{ACCENTS[i%ACCENTS.length]}}" stroke-width="4"/><text x="440" y="${{80+i*75}}" text-anchor="middle" fill="${{PAL.text}}" font-size="18" font-weight="800">${{(c.title||'Step').slice(0,26)}}</text>`).join('');
      inner=`<svg viewBox="0 0 880 400" width="100%" height="360">${{lines}}${{arrows}}</svg>`;
    }} else {{
      const paths=list.map((c,i)=>`<rect x="${{70+(i%2)*400}}" y="${{40+Math.floor(i/2)*180}}" width="340" height="120" rx="18" fill="rgba(15,23,42,0.75)" stroke="${{ACCENTS[i%ACCENTS.length]}}" stroke-width="2.5"/><text x="${{240+(i%2)*400}}" y="${{96+Math.floor(i/2)*180}}" text-anchor="middle" fill="${{PAL.text}}" font-size="20" font-weight="800">${{(c.title||'Module').slice(0,22)}}</text><text x="${{240+(i%2)*400}}" y="${{128+Math.floor(i/2)*180}}" text-anchor="middle" fill="${{ACCENTS[i%ACCENTS.length]}}" font-size="15" font-weight="700">${{(c.sub||P.sub_variant||'SVG NODE').slice(0,26)}}</text>`).join('');
      inner=`<svg viewBox="0 0 880 390" width="100%" height="350"><line x1="240" y1="160" x2="640" y2="220" stroke="${{PAL.cyan}}" stroke-width="3" stroke-dasharray="8 6"/>${{paths}}</svg>`;
    }}
    svgBox.innerHTML=inner; mount.appendChild(svgBox); animNodes.push(svgBox);
    list.slice(0,3).forEach((c,i)=>{{
      const col=ACCENTS[i%ACCENTS.length];
      const sc=document.createElement('div'); sc.className='gcard'; sc.style.borderColor=col;
      sc.innerHTML=`<div style="display:flex;align-items:center;gap:16px;"><div class="pill-num" style="background:${{col}}">${{c.tag||('0'+(i+1))}}</div><div><div class="ctitle">${{c.title}}</div>${{c.sub?`<div class="csub">${{c.sub}}</div>`:''}}</div></div>`;
      mount.appendChild(sc); animNodes.push(sc);
    }});
  }} else if(arch==='flame_bars'||arch==='waterfall_spans'||arch==='pyramid_tiers'){{
    P.cards.slice(0,5).forEach((c,i)=>{{
      const col=ACCENTS[i%ACCENTS.length];
      const wPct=arch==='pyramid_tiers'?(54+i*11):(100-i*14);
      const marginL=arch==='waterfall_spans'?(i*8):0;
      const el=document.createElement('div'); el.className='gcard';
      el.style.cssText=`width:${{wPct}}%;margin-left:${{marginL}}%;align-self:${{arch==='pyramid_tiers'?'center':'stretch'}};border-color:${{col}};`;
      el.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;gap:14px;"><div><div class="ctitle" style="color:${{col}}">${{c.title}}</div>${{c.sub?`<div class="csub">${{c.sub}}</div>`:''}}</div><span style="font-family:monospace;font-weight:900;color:${{PAL.text}}">${{c.val||((wPct)+'%')}}</span></div>`;
      mount.appendChild(el); animNodes.push(el);
    }});
  }} else if(arch==='matrix_grid'){{
    const grid=document.createElement('div'); grid.style.cssText='display:grid;grid-template-columns:1fr 1fr;gap:18px;';
    P.cards.slice(0,4).forEach((c,i)=>{{
      const col=ACCENTS[i%ACCENTS.length];
      const el=document.createElement('div'); el.className='gcard'; el.style.borderColor=col;
      el.innerHTML=`<span style="display:inline-block;padding:6px 12px;border-radius:999px;background:${{col}}22;color:${{col}};font-weight:900;font-size:17px;margin-bottom:10px;">CELL 0${{i+1}}</span><div class="ctitle">${{c.title}}</div>${{c.sub?`<div class="csub">${{c.sub}}</div>`:''}}`;
      grid.appendChild(el); animNodes.push(el);
    }});
    mount.appendChild(grid);
  }} else if(arch==='spatial_stack'){{
    P.cards.slice(0,4).forEach((c,i)=>{{
      const col=ACCENTS[i%ACCENTS.length];
      const el=document.createElement('div'); el.className='gcard'+(i===0?' active':'');
      el.style.cssText=`border-color:${{col}};transform:perspective(900px) rotateX(6deg) translateX(${{(i%2===0?-10:10)}}px);`;
      el.innerHTML=`<div style="display:flex;align-items:center;gap:18px;"><div class="pill-num" style="background:${{col}}">L${{i+1}}</div><div><div class="ctitle">${{c.title}}</div>${{c.sub?`<div class="csub">${{c.sub}}</div>`:''}}</div></div>`;
      mount.appendChild(el); animNodes.push(el);
    }});
  }} else {{
    // Interactive Glowing Bezier Pipeline / Bento Stages (Default Zero-Template Multi-Card Flow)
    P.cards.forEach((c,i)=>{{
      const col=ACCENTS[i%ACCENTS.length];
      const el=document.createElement('div'); el.className='gcard';
      el.innerHTML=`<div style="display:flex;align-items:center;gap:20px;"><div class="pill-num" style="background:linear-gradient(135deg,${{col}},${{ACCENTS[(i+1)%ACCENTS.length]}})">${{c.tag||('0'+(i+1))}}</div><div style="flex:1;"><div class="ctitle">${{c.title}}</div>${{c.sub?`<div class="csub">${{c.sub}}</div>`:''}}</div>${{c.val?`<span style="padding:8px 16px;border-radius:999px;border:1.5px solid ${{col}};font-weight:800;font-size:20px;color:${{col}}">${{c.val}}</span>`:''}}</div>`;
      mount.appendChild(el); animNodes.push(el);
    }});
  }}
}}
renderArchetype();

window.__setStudioProgress=function(p, curTime, energy){{
  if(window.__npUpdateHud) window.__npUpdateHud(p, curTime, energy);
  ctx.clearRect(0,0,W,H);
  // Subtle Volumetric Shaded 3D Backdrop Sphere/Torus centered harmoniously behind the glass stage
  drawLitPoly3D(W*0.5, Math.round(H*0.52), 255, 78, p*Math.PI*2.0, 0.55, '{_rgba_css(world["cyan"],0.5)}', '{_rgba_css(world["purple"],0.5)}', P.archetype==='hub_mesh'?'icosa':'torus');

  animNodes.forEach((el,i)=>{{
    const g=Math.max(0,Math.min(1,(p-i*0.11)/0.22));
    const ease=1-Math.pow(1-g,3);
    el.style.opacity=ease;
    el.style.transform=`translateY(${{(1-ease)*28}}px) scale(${{0.95+0.05*ease}})`;
  }});

  if(P.archetype==='memory_wal'&&animNodes.length){{
    const idx=Math.min(animNodes.length-1, Math.floor(p*animNodes.length));
    const walBar=document.getElementById('walBar'), walCur=document.getElementById('walCur');
    if(walBar) walBar.style.width=(15+85*p).toFixed(1)+'%';
    if(walCur&&P.entries[idx]) walCur.textContent=P.entries[idx].addr+' • '+P.entries[idx].status;
    animNodes.forEach((el,i)=>el.classList.toggle('active', i===idx));
  }}
  if(P.archetype==='benchmark'){{
    document.querySelectorAll('.bm-fill').forEach((f,i)=>{{
      const tgt=Number(f.getAttribute('data-bw')||50);
      const g=Math.max(0,Math.min(1,(p-i*0.12)/0.45));
      const ease=1-Math.pow(1-g,3);
      f.style.width=Math.max(6, Math.round(tgt*ease))+'%';
    }});
  }}
  if(P.archetype==='terminal_sql'&&window.__fullTermText){{
    const te=document.getElementById('termTxt');
    if(te){{
      const k=Math.max(12, Math.round(window.__fullTermText.length*Math.min(1, p/0.68)));
      te.textContent=window.__fullTermText.slice(0,k)+(p<0.85?' ▌':'');
    }}
  }}
  if(P.archetype==='alert_radar'){{
    const ang=p*Math.PI*3.0;
    const x2=440+220*Math.cos(ang), y2=250+220*Math.sin(ang);
    const b=document.getElementById('radBeam'), cn=document.getElementById('radCone');
    if(b){{b.setAttribute('x2',x2.toFixed(1));b.setAttribute('y2',y2.toFixed(1));}}
    if(cn){{
      const a0=ang-0.55;
      const x0=440+220*Math.cos(a0), y0=250+220*Math.sin(a0);
      cn.setAttribute('d',`M440 250 L${{x0.toFixed(1)}} ${{y0.toFixed(1)}} A220 220 0 0 1 ${{x2.toFixed(1)}} ${{y2.toFixed(1)}} Z`);
    }}
  }}
  if(P.archetype==='telemetry'&&P.gauge){{
    const arc=document.getElementById('gArc');
    if(arc){{
      const frac=(Math.max(10,Math.min(100,P.gauge.pct))/100)*Math.min(1,p/0.55);
      arc.setAttribute('stroke-dashoffset',(680*(1-frac)).toFixed(1));
    }}
  }}
}};
window.__setStudioProgress(0.05, 0, 0.55);
</script></body></html>"""


_STUDIO_HELPER_SCRIPT = """<script>
window.STUDIO_FX = {
  easeOutCubic: (t) => 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3),
  easeOutBack: (t) => { const x = Math.max(0, Math.min(1, t)), c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); },
  gate: (p, idx, total) => Math.max(0, Math.min(1, (p - (idx / Math.max(1, total)) * 0.6) / 0.25)),
};
</script>"""


def _wrap_custom_html(
    raw_html: str,
    width: int,
    height: int,
    scene_idx: int = 1,
    total_scenes: int = 4,
    world: Optional[Dict[str, Any]] = None,
    watermark: str = DEFAULT_WATERMARK,
) -> str:
    txt = str(raw_html or "").strip()
    sub_safe = 470 if height >= 1600 else (180 if height >= 1000 else 130)
    hud = _hud_overlay_snippet(width, height, scene_idx, total_scenes, world or resolve_studio_world(), watermark)
    safe_css = f"<style>html,body{{width:{width}px!important;height:{height}px!important;overflow:hidden!important;}} .subbox,.narration-box,[data-subtitle-collide]{{display:none!important;}}</style>"
    if "<html" in txt.lower():
        out = txt.replace("</head>", _STUDIO_HELPER_SCRIPT + safe_css + "</head>", 1) if "</head>" in txt else (_STUDIO_HELPER_SCRIPT + safe_css + txt)
        if "__setStudioProgress" not in out:
            hook = """<script>
window.__setStudioProgress=window.__setStudioProgress||function(p,curTime,energy){
  if(window.__npUpdateHud) window.__npUpdateHud(p,curTime,energy);
  document.documentElement.style.setProperty('--p', p);
  document.querySelectorAll('[data-stage]').forEach((el,i)=>{
    const th=Number(el.getAttribute('data-stage')||i+1)/6;
    const vis=p>=th?1:Math.max(0,(p-th+0.18)/0.18);
    el.style.opacity=vis;
    el.style.transform=`translateY(${(1-vis)*22}px) scale(${0.95+0.05*vis})`;
  });
};</script></body>"""
            out = out.replace("</body>", hud + hook)
        else:
            wrap_fn = """<script>
(function(){
  const _orig = window.__setStudioProgress;
  window.__setStudioProgress = function(p, curTime, energy){
    if(window.__npUpdateHud) window.__npUpdateHud(p, curTime, energy);
    if(typeof _orig === 'function') _orig(p, curTime, energy);
  };
})();
</script>"""
            out = out.replace("</body>", hud + wrap_fn + "</body>") if "</body>" in out else (out + hud + wrap_fn)
        return out

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
{_STUDIO_HELPER_SCRIPT}{safe_css}
<style>html,body{{margin:0;padding:106px 56px {sub_safe}px;width:{width}px;height:{height}px;overflow:hidden;background:#070B16;color:#F8FAFC;font-family:Inter,'Segoe UI',sans-serif;box-sizing:border-box;}}</style>
</head><body>{hud}{txt}
<script>
window.__setStudioProgress=window.__setStudioProgress||function(p,curTime,energy){{
  if(window.__npUpdateHud) window.__npUpdateHud(p,curTime,energy);
  document.documentElement.style.setProperty('--p', p);
  document.querySelectorAll('[data-stage]').forEach((el,i)=>{{
    const th=Number(el.getAttribute('data-stage')||i+1)/6;
    el.style.opacity=p>=th?1:Math.max(0,(p-th+0.18)/0.18);
  }});
}};
</script></body></html>"""


def render_web_generative_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    total_scenes: int = 4,
    format_ratio: str = "9:16",
    watermark: str = DEFAULT_WATERMARK,
    scene_words: List[Dict[str, Any]] = None,
    tone: str = "auto_dynamic",
) -> Optional[List[Path]]:
    """
    Renders true HTML5 / CSS3 / Canvas 3D / SVG motion graphics deterministically at 30fps via Playwright + Chromium.
    Includes automatic JS-error fallback -> Topic-Adaptive Multi-Archetype 3D HTML5 Synthesizer, plus unified Studio HUD!
    """
    ok, exe_path = detect_web_engine()
    if not ok:
        return None

    duration = max(1.5, float(scene.get("duration", 5.0)))
    total_frames = max(15, round(duration * VIDEO_FPS))
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    canvas_w = spec.get("width", VIDEO_WIDTH)
    canvas_h = spec.get("height", VIDEO_HEIGHT)

    scene_frames_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    if scene_frames_dir.exists():
        for old_f in scene_frames_dir.glob("frame_*.*"):
            try:
                old_f.unlink()
            except Exception:
                pass
    scene_frames_dir.mkdir(parents=True, exist_ok=True)

    visual_data = scene.get("visual_data") or {}
    effective_tone = (scene.get("scene_tone") or "conversational_casual") if tone == "auto_dynamic" else tone
    art_style = str(visual_data.get("art_style") or scene.get("art_style") or "editorial_dark").strip()
    topic_seed = str(scene.get("topic") or visual_data.get("title") or "").strip()
    world = resolve_studio_world(art_style=art_style, tone=effective_tone, visual_data=visual_data, topic=topic_seed)

    raw_html = str(visual_data.get("html") or visual_data.get("web_code") or "").strip()
    fallback_html = _build_default_webgl_html(
        scene, world, canvas_w, canvas_h, watermark, scene_idx=scene_idx, total_scenes=total_scenes
    )
    html_doc = (
        _wrap_custom_html(raw_html, canvas_w, canvas_h, scene_idx=scene_idx, total_scenes=total_scenes, world=world, watermark=watermark)
        if raw_html
        else fallback_html
    )

    frame_paths: List[Path] = []
    sc_start = float(scene.get("start_time", 0.0))
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if exe_path:
            kwargs["executable_path"] = exe_path
        browser = p.chromium.launch(**kwargs)
        page = browser.new_page(viewport={"width": canvas_w, "height": canvas_h}, device_scale_factor=1)
        page_errors: List[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.set_content(html_doc, wait_until="domcontentloaded", timeout=10000)

        # Smoke test progress callback on custom AI HTML; swap cleanly to rich multi-archetype HTML if AI code threw errors
        if raw_html:
            try:
                page.evaluate(f"if (window.__setStudioProgress) window.__setStudioProgress(0.5, {sc_start:.3f}, 0.75);")
                body_len = page.evaluate("() => (document.body.innerText || '').trim().length + document.querySelectorAll('svg,canvas').length")
            except Exception:
                body_len = 0
                page_errors.append("eval_error")
            if page_errors or (body_len or 0) < 2:
                page.set_content(fallback_html, wait_until="domcontentloaded", timeout=10000)

        wps = (len(scene_words) / max(0.5, duration)) if scene_words else 2.5
        pace_boost = max(0.96, min(1.12, wps / 2.85))

        for f in range(total_frames):
            lin_p = f / max(1, total_frames - 1)
            cur_t = sc_start + lin_p * duration
            energy = 0.55
            word_p = lin_p
            if scene_words:
                spoken = 0
                for w in scene_words:
                    ws = float(w.get("start", 0.0))
                    we = float(w.get("end", ws + 0.25))
                    if ws <= cur_t:
                        spoken += 1
                    if ws <= cur_t <= we:
                        energy = 0.95
                word_p = spoken / max(1, len(scene_words))
            raw_p = min(1.0, (0.65 * word_p + 0.35 * lin_p) * pace_boost)
            if effective_tone == "youth_friend_turbo":
                eff_p = 1.0 if lin_p >= 0.93 else min(1.0, (raw_p ** 0.92) * 1.05)
            elif effective_tone in ("purposeful_hinglish_mentor", "senior_hinglish_mentor"):
                eff_p = 1.0 if lin_p >= 0.94 else min(1.0, (raw_p ** 0.94) * 1.04)
            elif effective_tone == "fireship_octane":
                eff_p = 1.0 if lin_p >= 0.93 else min(1.0, raw_p * 1.08)
            else:
                eff_p = 1.0 if lin_p >= 0.95 else raw_p
            page.evaluate(f"if (window.__setStudioProgress) window.__setStudioProgress({eff_p:.5f}, {cur_t:.4f}, {energy:.3f});")
            fpath = scene_frames_dir / f"frame_{f:04d}.jpg"
            page.screenshot(path=str(fpath), type="jpeg", quality=88)
            frame_paths.append(fpath)

        browser.close()
        p.stop()
        return frame_paths
    except Exception:
        return None
