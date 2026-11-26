"""
Voice-Synchronized 12-Verb Action Choreography Engine + Dynamic Virtual Camera.

Triggers live, physical, word-locked visual actions directly over ANY rendered
Studio layout using Groq Whisper word timestamps and `StudioStage.anchor_cards`
coordinates:
  1. travel_token        (API Key, File, Parquet, TCP Packet, TXN A->B flight)
  2. wire_handshake      (Live 0%->100% network cable + bidirectional packets)
  3. construct_assemble  (Warehouse grid snap / Data Lake bucket drop)
  4. spotlight_sequence  (Popup tool stack strip lighting up word-by-word)
  5. disrupt_shake       (Red error alert strip + camera vibration screen-shake)
  6. filter_gate         (WAF / Rate-limit pass vs blocked bounce)
  7. fanout_split        (1->N or N->1 traffic split / shard merge)
  8. inspect_zoom        (Microscope ring + live offset/metric callout)
  9. state_flip          (Old state -> Verified state atomic flip pill)
 10. buffer_fill_drain   (Live queue / lag meter fill-drain gauge)
 11. cipher_scramble     (Plaintext -> Encrypted ciphertext hash morph)
 12. slot_reorder        (Partition / sorting element swap arc)
"""

import math
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from core.svg_engine import fetch_iconify_svg

_ACTION_FONT_CACHE: Dict[Tuple[int, bool, bool], ImageFont.FreeTypeFont] = {}


def _afont(sz: int, bold: bool = True, mono: bool = False) -> ImageFont.FreeTypeFont:
    key = (int(sz), bool(bold), bool(mono))
    if key in _ACTION_FONT_CACHE:
        return _ACTION_FONT_CACHE[key]
    paths = (
        ("C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf") if mono
        else ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    )
    for p in paths:
        try:
            f = ImageFont.truetype(p, int(sz))
            _ACTION_FONT_CACHE[key] = f
            return f
        except Exception:
            continue
    f = ImageFont.load_default()
    _ACTION_FONT_CACHE[key] = f
    return f


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def _rgb_hex(col: Tuple[int, ...]) -> str:
    return f"#{int(col[0]):02X}{int(col[1]):02X}{int(col[2]):02X}"


@lru_cache(maxsize=64)
def _get_action_sprite(query: str, tint_hex: str, size_px: int = 38) -> Optional[Image.Image]:
    """Fetches a crisp cached SVG icon sprite from Iconify when available (never fails)."""
    try:
        return fetch_iconify_svg(query, size_px=size_px, tint_hex=tint_hex)
    except Exception:
        return None


def get_story_beat_motion(role: Any, narration: Any) -> str:
    """Chooses a non-uniform entrance motion physics profile based on scene role & narration."""
    r = str(role or "").lower().strip()
    n = str(narration or "").lower()
    if r == "hook" or re.search(r"\b(trap|mistake|shock|percent|90%|freeze|why)\b", n):
        return "pop_bounce"
    if r in ("tradeoff", "comparison") or re.search(r"\b(vs|versus|trade-?off|compare|jabki)\b", n):
        return "split_collide"
    if re.search(r"\b(error|crash|fail|lock|timeout|deadlock|502|oom|alert)\b", n):
        return "disrupt_shake"
    if re.search(r"\b(warehouse|lake|layer|tier|stack|medallion|schema|build|docker)\b", n):
        return "stack_snap"
    return "flow_slide"


def _find_word_window(
    keywords: Tuple[str, ...],
    scene_words: Optional[List[Dict[str, Any]]],
    sc_start: float,
    duration: float,
    raw_narr: str,
    fallback_p: float = 0.5,
) -> Tuple[float, float]:
    """Locates exact normalized `[start_p, end_p]` window from Whisper word_timestamps or narration."""
    dur = max(0.5, float(duration))
    if scene_words:
        for w in scene_words:
            wt = re.sub(r"[^a-z0-9]", "", str(w.get("word", "")).lower())
            if any(wt == kw or (len(kw) >= 4 and kw in wt) for kw in keywords):
                ws = float(w.get("start", sc_start))
                p0 = _clamp01((ws - sc_start) / dur)
                return max(0.02, p0 - 0.03), min(0.98, p0 + 0.24)
    low = raw_narr.lower()
    for kw in keywords:
        idx = low.find(kw)
        if idx >= 0:
            p0 = _clamp01(idx / max(1, len(low)))
            return max(0.04, p0 - 0.02), min(0.96, p0 + 0.22)
    return _clamp01(fallback_p - 0.12), _clamp01(fallback_p + 0.14)


_AUTO_VERB_PATTERNS: List[Tuple[str, Tuple[str, ...], str, str, str]] = [
    # (verb, spoken_keywords, default_label, icon_query, accent_key)
    ("disrupt_shake", ("error", "crash", "fail", "timeout", "deadlock", "lock", "502", "503", "oom", "bottleneck", "stall"), "TIMEOUT / LOCK", "alert", "rose"),
    ("travel_token", ("apikey", "key", "token", "jwt", "auth", "call", "request", "endpoint"), "API KEY", "key", "amber"),
    ("travel_token", ("parquet", "file", "csv", "json", "transfer", "upload", "ingest", "replicate", "copy"), "DATA FILE", "file", "cyan"),
    ("travel_token", ("packet", "syn", "ack", "tcp", "udp", "frame", "payload", "stream"), "PACKET", "network", "emerald"),
    ("wire_handshake", ("connect", "handshake", "network", "link", "bridge", "relation", "join", "sync"), "LIVE LINK", "link", "cyan"),
    ("construct_assemble", ("warehouse", "lakehouse", "datalake", "lake", "medallion", "schema", "bucket", "bronze", "silver", "gold"), "BUILD STACK", "database", "emerald"),
    ("filter_gate", ("ratelimit", "waf", "firewall", "filter", "drop", "429", "guardrail", "block"), "RATE GATE", "shield", "rose"),
    ("fanout_split", ("shard", "fanout", "partition", "broadcast", "loadbalance", "shuffle"), "FANOUT", "router", "purple"),
    ("state_flip", ("cutover", "atomic", "failover", "promote", "switch", "lockfree", "healthy"), "SWITCH [OK]", "check", "emerald"),
    ("buffer_fill_drain", ("lag", "buffer", "queue", "drain", "flush", "evict", "backpressure"), "QUEUE DRAIN", "queue", "amber"),
    ("cipher_scramble", ("encrypt", "hash", "cipher", "tls", "mtls", "aes", "hsm"), "ENCRYPT", "lock", "purple"),
    ("inspect_zoom", ("explain", "index", "offset", "lsn", "debug", "trace", "p99", "metric"), "INSPECT", "search", "cyan"),
    ("slot_reorder", ("sort", "reorder", "rebalance", "swap", "merge"), "REORDER", "layers", "amber"),
]

_KNOWN_TOOL_BADGES: Tuple[str, ...] = (
    "Kafka", "Spark", "Flink", "Snowflake", "Iceberg", "Delta", "Parquet", "DuckDB", "Postgres",
    "MySQL", "Redis", "Debezium", "Airflow", "dbt", "Kubernetes", "Docker", "Envoy", "gRPC",
    "PyTorch", "LangGraph", "MCP", "eBPF", "WebRTC", "HSM", "SWIFT", "UPI", "AWS", "Azure", "S3", "AKS", "EKS",
)


def extract_spoken_actions(
    scene: Dict[str, Any],
    duration: float,
    scene_words: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Extracts time-aligned Action Events from explicit AI `scene["actions"]` AND/OR
    spoken narration/Whisper word timestamps cleanly (zero domain hardcoding).
    """
    dur = max(1.0, float(duration))
    sc_start = float(scene.get("start_time", 0.0))
    raw_narr = str(scene.get("narration") or "")
    v_data = scene.get("visual_data") or {}
    ctx = f"{raw_narr} {v_data.get('title', '')}".lower()

    events: List[Dict[str, Any]] = []
    explicit = scene.get("actions")
    if isinstance(explicit, list):
        for ei, act in enumerate(explicit[:5]):
            if not isinstance(act, dict):
                continue
            verb = str(act.get("verb") or act.get("type") or "travel_token").lower().strip()
            kw = re.sub(r"[^a-z0-9]", "", str(act.get("word") or "").lower())
            p0, p1 = _find_word_window((kw,) if kw else ("__none__",), scene_words, sc_start, dur, raw_narr, (ei + 0.5) / max(1, len(explicit)))
            events.append({
                "verb": verb,
                "label": str(act.get("label") or act.get("word") or verb).upper()[:22],
                "icon": str(act.get("icon") or "bolt"),
                "from_idx": int(act.get("from_idx", act.get("from", 0))),
                "to_idx": int(act.get("to_idx", act.get("to", 1))),
                "items": list(act.get("items") or act.get("tools") or []),
                "color_key": str(act.get("color_key") or ("rose" if verb == "disrupt_shake" else "cyan")),
                "start_p": round(p0, 4),
                "end_p": round(p1, 4),
            })

    # Auto-detect spoken physical activities if AI didn't supply explicit actions
    if not events:
        used_verbs = set()
        for idx_p, (verb, kws, def_lbl, ico, ckey) in enumerate(_AUTO_VERB_PATTERNS):
            # Look for actual literal spoken hit
            matched_kw = None
            for kw in kws:
                if re.search(rf"\b{re.escape(kw)}", ctx):
                    matched_kw = kw
                    break
            if not matched_kw:
                continue
            sig_key = f"{verb}:{def_lbl}"
            if sig_key in used_verbs:
                continue
            used_verbs.add(sig_key)
            p0, p1 = _find_word_window(kws, scene_words, sc_start, dur, raw_narr, 0.25 + 0.2 * len(events))
            lbl = def_lbl
            if matched_kw in ("parquet", "csv", "json"):
                lbl = f".{matched_kw.upper()}"
            elif matched_kw in ("jwt", "apikey", "502", "503", "429", "deadlock", "timeout"):
                lbl = matched_kw.upper()
            events.append({
                "verb": verb,
                "label": lbl,
                "icon": ico,
                "from_idx": max(0, len(events) % 2),
                "to_idx": max(1, (len(events) % 2) + 1),
                "items": [],
                "color_key": ckey,
                "start_p": round(p0, 4),
                "end_p": round(p1, 4),
            })
            if len(events) >= 3:
                break

    # Tool-Stack Spotlight Sequence when >=2 real tools/technologies are mentioned together
    mentioned_tools = [t for t in _KNOWN_TOOL_BADGES if re.search(rf"\b{re.escape(t.lower())}\b", ctx)]
    if len(mentioned_tools) >= 2 and not any(e["verb"] == "spotlight_sequence" for e in events):
        p0, _ = _find_word_window((mentioned_tools[0].lower(),), scene_words, sc_start, dur, raw_narr, 0.35)
        events.append({
            "verb": "spotlight_sequence",
            "label": "STACK TOOLS",
            "icon": "layers",
            "from_idx": 0,
            "to_idx": 1,
            "items": mentioned_tools[:4],
            "color_key": "cyan",
            "start_p": round(max(0.08, p0), 4),
            "end_p": round(min(0.92, p0 + 0.42), 4),
        })

    return events


def eval_active_actions(events: List[Dict[str, Any]], linear_p: float) -> List[Dict[str, Any]]:
    """Returns actions active at normalized scene progress `linear_p` with local progress `t` in [0,1]."""
    active: List[Dict[str, Any]] = []
    lp = _clamp01(linear_p)
    for ev in events or ():
        s = float(ev.get("start_p", 0.0))
        e = max(s + 0.05, float(ev.get("end_p", 1.0)))
        if s <= lp <= e:
            t = _clamp01((lp - s) / (e - s))
            out = dict(ev)
            out["t"] = t
            active.append(out)
    return active


def compute_camera_transform(
    anchor_cards: List[Dict[str, Any]],
    active_actions: List[Dict[str, Any]],
    linear_p: float,
    canvas_w: int,
    canvas_h: int,
) -> Dict[str, Any]:
    """
    Computes Dynamic Virtual Camera zoom/pan (`cam_zoom`, `cam_cx`, `cam_cy`) following
    the currently active component, plus micro screen-shake `(dx, dy)` during `disrupt_shake`.
    """
    cam_zoom = 1.0
    cam_cx = canvas_w * 0.5
    cam_cy = canvas_h * 0.5

    # Track currently speaking/active anchor card gently inside [0.10..0.86], zoom out for finale
    act_card = None
    for c in anchor_cards or ():
        if c.get("active"):
            act_card = c
    if act_card is not None and 0.10 <= linear_p <= 0.88:
        env = math.sin(_clamp01((linear_p - 0.10) / 0.78) * math.pi)
        cam_zoom = 1.0 + 0.085 * env
        # Gentle pan bias (40% toward active card center so stage stays framed)
        cam_cx = canvas_w * 0.5 + (float(act_card["cx"]) - canvas_w * 0.5) * 0.42 * env
        cam_cy = canvas_h * 0.5 + (float(act_card["cy"]) - canvas_h * 0.5) * 0.36 * env

    dx, dy = 0, 0
    shake_lbl = ""
    for ev in active_actions:
        if ev.get("verb") == "disrupt_shake":
            t = float(ev.get("t", 0.5))
            damp = math.sin(t * math.pi)
            dx = int(round(math.sin(t * 58.0) * 11.0 * damp))
            dy = int(round(math.cos(t * 47.0) * 7.0 * damp))
            shake_lbl = str(ev.get("label") or "SYSTEM ERROR")
            break

    return {
        "zoom": cam_zoom,
        "cx": cam_cx,
        "cy": cam_cy,
        "dx": dx,
        "dy": dy,
        "shake_lbl": shake_lbl,
    }


def apply_camera_to_stage(stage_rgba: Image.Image, cam: Dict[str, Any]) -> Image.Image:
    """
    Applies smooth virtual zoom/pan ONLY to the diagram stage region (y >= 310) so the
    top badge/title/AUDIO chrome stays crisp and never collides, plus error shake (dx, dy).
    """
    z = float(cam.get("zoom", 1.0))
    dx, dy = int(cam.get("dx", 0)), int(cam.get("dy", 0))
    if z <= 1.002 and dx == 0 and dy == 0:
        return stage_rgba
    w, h = stage_rgba.size
    header_y = min(312, int(h * 0.18))
    out = stage_rgba.copy()
    if z > 1.002 and h > header_y + 120:
        body = stage_rgba.crop((0, header_y, w, h))
        bw, bh = body.size
        cw, ch = max(100, int(bw / z)), max(100, int(bh / z))
        cx = max(cw // 2, min(bw - cw // 2, int(cam.get("cx", bw // 2))))
        cy_raw = int(cam.get("cy", header_y + bh // 2)) - header_y
        cy = max(ch // 2, min(bh - ch // 2, cy_raw))
        zoomed = body.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)).resize((bw, bh), Image.Resampling.BILINEAR)
        out.paste((0, 0, 0, 0), (0, header_y, w, h))
        out.paste(zoomed, (0, header_y))
    if dx != 0 or dy != 0:
        shaken = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shaken.paste(out, (dx, dy))
        out = shaken
    return out


def _anchor_pair(anchor_cards: List[Dict[str, Any]], f_idx: int, t_idx: int, w: int, h: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    if len(anchor_cards) >= 2:
        a = anchor_cards[f_idx % len(anchor_cards)]
        b = anchor_cards[t_idx % len(anchor_cards)]
        if a is b:
            b = anchor_cards[(t_idx + 1) % len(anchor_cards)]
        return (int(a["cx"]), int(a["cy"])), (int(b["cx"]), int(b["cy"]))
    if len(anchor_cards) == 1:
        a = anchor_cards[0]
        return (max(120, int(a["cx"]) - 240), int(a["cy"])), (int(a["cx"]), int(a["cy"]))
    return (int(w * 0.24), int(h * 0.42)), (int(w * 0.76), int(h * 0.56))


def _draw_pill_badge(draw: ImageDraw.ImageDraw, cx: int, cy: int, text: str, bg: Tuple[int, ...], fg: Tuple[int, ...], border: Tuple[int, ...], icon_img: Optional[Image.Image] = None) -> None:
    f = _afont(20, bold=True, mono=True)
    tw = draw.textlength(text, font=f)
    pad_l = 44 if icon_img is not None else 18
    pw = int(tw + pad_l + 18)
    ph = 42
    box = (cx - pw // 2, cy - ph // 2, cx + pw // 2, cy + ph // 2)
    draw.rounded_rectangle(box, radius=21, fill=bg, outline=border, width=2)
    if icon_img is not None:
        # Icon pasted directly on caller overlay image if provided
        pass
    draw.text((box[0] + pad_l - 4, cy - 11), text, font=f, fill=fg)


def render_action_overlay(
    stage_img: Image.Image,
    world: Dict[str, Any],
    anchor_cards: List[Dict[str, Any]],
    active_actions: List[Dict[str, Any]],
    linear_p: float,
) -> Image.Image:
    """
    Renders live, word-locked animated actions across all 12 composable physics verbs
    cleanly on top of any active scene without distracting GUI mouse pointers.
    """
    if not active_actions:
        return stage_img
    w, h = stage_img.size
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov, "RGBA")

    for ev in active_actions[:3]:
        verb = str(ev.get("verb") or "travel_token")
        t = _clamp01(float(ev.get("t", 0.5)))
        ck = str(ev.get("color_key") or "cyan")
        col = tuple(world.get(ck, world["cyan"])[:3])
        lbl = str(ev.get("label") or "")
        p0, p1 = _anchor_pair(anchor_cards, int(ev.get("from_idx", 0)), int(ev.get("to_idx", 1)), w, h)
        fade = math.sin(t * math.pi)
        alp = max(60, min(255, int(255 * min(1.0, fade * 1.6))))

        if verb in ("travel_token", "fanout_split"):
            ctrl = ((p0[0] + p1[0]) * 0.5, min(p0[1], p1[1]) - 110.0)
            # Dashed live trajectory
            pts = [
                ((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * ctrl[0] + s ** 2 * p1[0],
                 (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * ctrl[1] + s ** 2 * p1[1])
                for s in [k / 16.0 for k in range(17)]
            ]
            dr.line(pts, fill=(*col, int(alp * 0.48)), width=4)
            u = 1.0 - t
            bx = int(u * u * p0[0] + 2 * u * t * ctrl[0] + t * t * p1[0])
            by = int(u * u * p0[1] + 2 * u * t * ctrl[1] + t * t * p1[1])
            spr = _get_action_sprite(str(ev.get("icon") or "bolt"), _rgb_hex(col), size_px=26)
            _draw_pill_badge(dr, bx, by, lbl[:16], (13, 20, 36, 240), (*col, alp), (*col, alp), icon_img=spr)
            if spr is not None:
                tw = dr.textlength(lbl[:16], font=_afont(20, bold=True, mono=True))
                pw = int(tw + 62)
                ov.alpha_composite(spr.convert("RGBA"), (bx - pw // 2 + 10, by - 13))
            if t >= 0.82:
                dr.ellipse((p1[0] - 32, p1[1] - 32, p1[0] + 32, p1[1] + 32), outline=(*world["emerald"][:3], alp), width=4)

        elif verb == "wire_handshake":
            cur_x = int(p0[0] + (p1[0] - p0[0]) * min(1.0, t * 1.4))
            cur_y = int(p0[1] + (p1[1] - p0[1]) * min(1.0, t * 1.4))
            dr.line((p0[0], p0[1], cur_x, cur_y), fill=(*col, alp), width=5)
            dr.ellipse((cur_x - 9, cur_y - 9, cur_x + 9, cur_y + 9), fill=(255, 255, 255, alp), outline=(*col, alp), width=3)
            if t > 0.45:
                _draw_pill_badge(dr, (p0[0] + p1[0]) // 2, (p0[1] + p1[1]) // 2 - 26, lbl[:16], (13, 20, 36, 238), (*col, alp), (*col, alp))

        elif verb == "construct_assemble":
            zx, zy = p1
            is_lake = "LAKE" in lbl or "DROP" in lbl or "RAW" in lbl
            items = list(ev.get("items") or (["JSON", "CSV", ".parquet"] if is_lake else ["FACT", "DIM_1", "DIM_2"]))[:3]
            for bi, b_txt in enumerate(items):
                local_t = _clamp01((t - bi * 0.14) / 0.55)
                off_y = int((1.0 - local_t) * -120) if is_lake else int((1.0 - local_t) * 60)
                bx = zx - 110 + bi * 110
                by = zy - 44 + off_y
                if local_t > 0.05:
                    _draw_pill_badge(dr, bx, by, str(b_txt)[:10], (15, 23, 42, 240), (*col, alp), (*col, alp))

        elif verb == "spotlight_sequence":
            tools = list(ev.get("items") or [])[:4]
            if tools:
                act_ti = min(len(tools) - 1, int(t * len(tools)))
                bw = 195
                start_x = (w - (len(tools) * bw + (len(tools) - 1) * 16)) // 2
                y_strip = h - 540
                for ti, tname in enumerate(tools):
                    tx = start_x + ti * (bw + 16) + bw // 2
                    is_cur = (ti == act_ti)
                    tcol = world["emerald"] if is_cur else world["muted"]
                    _draw_pill_badge(
                        dr, tx, y_strip - (8 if is_cur else 0), str(tname)[:14],
                        (18, 28, 48, 245 if is_cur else 185), (*tcol[:3], 255 if is_cur else 190),
                        (*world["emerald"][:3], 255) if is_cur else (*world["border"][:3], 150),
                    )

        elif verb == "disrupt_shake":
            pulse = 120 + int(120 * abs(math.sin(t * 20.0)))
            dr.rounded_rectangle((12, 12, w - 12, h - 12), radius=24, outline=(244, 63, 94, pulse), width=8)
            _draw_pill_badge(dr, w // 2, 275, f"! {lbl[:20]}", (127, 29, 29, 245), (254, 226, 226, 255), (244, 63, 94, 255))

        elif verb == "filter_gate":
            gx, gy = (p0[0] + p1[0]) // 2, (p0[1] + p1[1]) // 2
            dr.line((gx, gy - 85, gx, gy + 85), fill=(*world["cyan"][:3], alp), width=6)
            bx = int(p0[0] + (gx - 28 - p0[0]) * min(1.0, t * 1.3))
            _draw_pill_badge(dr, bx, gy - 26, "DROP [X]", (127, 29, 29, 240), (254, 202, 202, alp), (244, 63, 94, alp))
            px = int(p0[0] + (p1[0] - p0[0]) * t)
            _draw_pill_badge(dr, px, gy + 32, "PASS [OK]", (6, 78, 59, 240), (167, 243, 208, alp), (16, 185, 129, alp))

        elif verb == "inspect_zoom":
            rad = int(52 + 12 * math.sin(t * math.pi * 4.0))
            dr.ellipse((p0[0] - rad, p0[1] - rad, p0[0] + rad, p0[1] + rad), outline=(*col, alp), width=4)
            _draw_pill_badge(dr, p0[0], p0[1] - rad - 26, f"INSPECT: {lbl[:12]}", (15, 23, 42, 240), (*col, alp), (*col, alp))

        elif verb == "state_flip":
            _draw_pill_badge(dr, p1[0], p1[1] - 45, lbl[:18] if t > 0.45 else "UPDATING...", (6, 78, 59, 242), (*world["emerald"][:3], alp), (*world["emerald"][:3], alp))

        elif verb == "buffer_fill_drain":
            bw = 320
            x0 = w // 2 - bw // 2
            y0 = h - 540
            fill_ratio = max(0.08, 1.0 - t * 0.86)
            dr.rounded_rectangle((x0, y0, x0 + bw, y0 + 28), radius=14, fill=(15, 23, 42, 230), outline=(*col, alp), width=2)
            dr.rounded_rectangle((x0 + 4, y0 + 4, x0 + 4 + int((bw - 8) * fill_ratio), y0 + 24), radius=10, fill=(*col, alp))
            dr.text((x0, y0 - 26), f"{lbl[:16]}: {int(fill_ratio * 100)}%", font=_afont(19, bold=True, mono=True), fill=(*col, alp))

        elif verb == "cipher_scramble":
            ciph = "".join(chr(65 + ((ord(ch) + int(t * 17) + k) % 26)) for k, ch in enumerate("PAYLOAD"))
            txt = ciph if t < 0.7 else f"ENC:{ciph[:5]}"
            _draw_pill_badge(dr, (p0[0] + p1[0]) // 2, (p0[1] + p1[1]) // 2, f"{txt}", (30, 27, 75, 240), (*world["purple"][:3], alp), (*world["purple"][:3], alp))

        elif verb == "slot_reorder":
            ux = int(p0[0] + (p1[0] - p0[0]) * t)
            uy = int(p0[1] + (p1[1] - p0[1]) * t - math.sin(t * math.pi) * 65)
            _draw_pill_badge(dr, ux, uy, "<-> SWAP", (15, 23, 42, 240), (*col, alp), (*col, alp))

    return Image.alpha_composite(stage_img.convert("RGBA"), ov)
