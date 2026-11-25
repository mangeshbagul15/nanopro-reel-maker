import math
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw

from core.mesh_shader_engine import draw_procedural_3d_mesh
from core.shapes_3d import draw_3d_shape, draw_vector_glyph

# =========================================================================
# 12 DYNAMIC CAMERA & SCENE TRANSITION FX
# =========================================================================
ALL_TRANSITIONS: Tuple[str, ...] = (
    "crossfade",
    "slide_up",
    "slide_down",
    "slide_left",
    "slide_right",
    "zoom_push",
    "zoom_pull",
    "wipe_reveal",
    "iris_circle",
    "curtain_split",
    "parallax_pan",
    "glitch_snap",
)


def apply_scene_transition(
    stage_img: Image.Image,
    bg_img: Image.Image,
    transition: str,
    linear_p: float,
) -> Image.Image:
    """
    Applies one of 12 studio transitions over enter/exit envelope cleanly at 30fps
    onto bg_img without blocking fast PIL/NumPy frame timing.
    """
    tr = str(transition or "crossfade").lower().strip()
    if tr not in ALL_TRANSITIONS:
        tr = "crossfade"
    w, h = stage_img.size
    out = bg_img.convert("RGBA") if bg_img is not None else Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Enter phase: 0.0 -> 0.14, Exit phase: 0.90 -> 1.0
    if linear_p < 0.14:
        t = max(0.0, min(1.0, linear_p / 0.14))
        e = 1.0 - (1.0 - t) ** 3
        entering = True
    elif linear_p > 0.90:
        t = max(0.0, min(1.0, (1.0 - linear_p) / 0.10))
        e = 1.0 - (1.0 - t) ** 2
        entering = False
    else:
        out.alpha_composite(stage_img)
        return out

    if tr == "crossfade":
        layer = stage_img.copy()
        layer.putalpha(layer.split()[3].point(lambda p: int(p * (0.25 + 0.75 * e))))
        out.alpha_composite(layer)
    elif tr in ("slide_up", "slide_down", "slide_left", "slide_right", "parallax_pan"):
        dx, dy = 0, 0
        dist = int((1.0 - e) * (160 if entering else 120))
        if tr == "slide_up":
            dy = dist if entering else -dist
        elif tr == "slide_down":
            dy = -dist if entering else dist
        elif tr in ("slide_left", "parallax_pan"):
            dx = dist if entering else -dist
        elif tr == "slide_right":
            dx = -dist if entering else dist
        layer = stage_img.copy()
        layer.putalpha(layer.split()[3].point(lambda p: int(p * (0.25 + 0.75 * e))))
        out.alpha_composite(layer, (dx, dy))
    elif tr in ("zoom_push", "zoom_pull"):
        sc = (0.86 + 0.14 * e) if tr == "zoom_push" else (1.14 - 0.14 * e)
        nw, nh = max(64, int(w * sc)), max(64, int(h * sc))
        resized = stage_img.resize((nw, nh), Image.Resampling.BILINEAR)
        resized.putalpha(resized.split()[3].point(lambda p: int(p * (0.25 + 0.75 * e))))
        if nw <= w and nh <= h:
            out.alpha_composite(resized, ((w - nw) // 2, (h - nh) // 2))
        else:
            cx0, cy0 = (nw - w) // 2, (nh - h) // 2
            out.alpha_composite(resized.crop((cx0, cy0, cx0 + w, cy0 + h)))
    elif tr == "wipe_reveal":
        cut = max(1, int(w * (0.15 + 0.85 * e)))
        cropped = stage_img.crop((0, 0, cut, h))
        out.alpha_composite(cropped, (0, 0))
    elif tr == "iris_circle":
        mask = Image.new("L", (w, h), 0)
        rad = max(20, int(math.hypot(w, h) * 0.55 * (0.15 + 0.85 * e)))
        ImageDraw.Draw(mask).ellipse((w // 2 - rad, h // 2 - rad, w // 2 + rad, h // 2 + rad), fill=255)
        layer = stage_img.copy()
        layer.putalpha(ImageChops.darker(layer.split()[3], mask))
        out.alpha_composite(layer)
    elif tr == "curtain_split":
        half_w = max(1, int((w // 2) * (0.18 + 0.82 * e)))
        left_c = stage_img.crop((w // 2 - half_w, 0, w // 2 + half_w, h))
        out.alpha_composite(left_c, (w // 2 - half_w, 0))
    else:  # glitch_snap
        jitter = int(math.sin(linear_p * 180.0) * (1.0 - e) * 28)
        layer = stage_img.copy()
        layer.putalpha(layer.split()[3].point(lambda p: int(p * (0.35 + 0.65 * e))))
        out.alpha_composite(layer, (jitter, 0))
    return out


# =========================================================================
# 14 KINETIC TYPOGRAPHY & TEXT MOTION FX
# =========================================================================
ALL_TEXT_FX: Tuple[str, ...] = (
    "clean_fade",
    "word_pop",
    "highlighter_brush",
    "typewriter_cursor",
    "gradient_shimmer",
    "strike_vs_new",
    "neon_underline",
    "split_counter",
    "glitch_text",
    "pill_tag_drop",
    "scale_bounce",
    "letter_track",
    "quote_serif_glow",
    "slide_reveal",
)


def draw_kinetic_text(
    stage: Any,
    text: str,
    xy: Tuple[int, int],
    max_w: int,
    font: Any,
    accent: Tuple[int, int, int],
    progress: float,
    fx: str = "clean_fade",
    world: Optional[Dict[str, Any]] = None,
    _with_alpha_fn: Any = None,
    _draw_wrapped_fn: Any = None,
) -> None:
    """Applies any of 14 expressive headline / callout text motion effects cleanly."""
    w = world or stage.world
    mode = str(fx or "clean_fade").lower().strip()
    x, y = xy
    txt = str(text or "").strip()
    if not txt:
        return

    a = stage.t_alpha
    wa = _with_alpha_fn
    if mode == "typewriter_cursor":
        k = max(1, int(len(txt) * min(1.0, progress / 0.65)))
        shown = txt[:k] + ("_" if (progress < 0.85 and int(progress * 16) % 2 == 0) else "")
        _draw_wrapped_fn(stage.draw, (x, y), shown, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode == "highlighter_brush":
        sw = min(max_w, int(stage.draw.textlength(txt[:28], font=font) * min(1.0, progress / 0.35)) + 16)
        stage.draw.rounded_rectangle((x - 6, y + 6, x + sw, y + 54), radius=10, fill=wa((*accent[:3], 64), a))
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode == "neon_underline":
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
        uw = min(max_w, int(stage.draw.textlength(txt[:30], font=font) * min(1.0, progress / 0.45)))
        stage.add_glow_line([(x, y + 58), (x + uw, y + 58)], accent, width=10, alpha=160)
        stage.draw.line((x, y + 58, x + uw, y + 58), fill=wa(accent, a), width=4)
    elif mode == "gradient_shimmer":
        pulse = 0.5 + 0.5 * math.sin(progress * math.pi * 4.0)
        c1, c2 = accent, w["purple"]
        mix = (int(c1[0] * pulse + c2[0] * (1 - pulse)), int(c1[1] * pulse + c2[1] * (1 - pulse)), int(c1[2] * pulse + c2[2] * (1 - pulse)))
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(mix, a), max_w, line_gap=8, max_lines=2)
    elif mode == "glitch_text":
        off = 4 if (progress < 0.35 and int(progress * 30) % 3 == 0) else 0
        if off:
            _draw_wrapped_fn(stage.draw, (x - off, y), txt, font, wa(w["rose"], a * 0.7), max_w, line_gap=8, max_lines=2)
            _draw_wrapped_fn(stage.draw, (x + off, y), txt, font, wa(w["cyan"], a * 0.7), max_w, line_gap=8, max_lines=2)
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode in ("slide_reveal", "pill_tag_drop"):
        dy = int((1.0 - min(1.0, progress / 0.25)) * (-26 if mode == "pill_tag_drop" else 28))
        _draw_wrapped_fn(stage.draw, (x, y + dy), txt, font, wa(w["text"], a * min(1.0, progress / 0.20 + 0.2)), max_w, line_gap=8, max_lines=2)
    elif mode in ("word_pop", "scale_bounce"):
        words = txt.split()
        show_cnt = max(1, int(len(words) * min(1.0, progress / 0.45 + 0.2)))
        dy = -abs(int(math.sin(progress * math.pi * 6.0) * 6)) if progress < 0.35 else 0
        _draw_wrapped_fn(stage.draw, (x, y + dy), " ".join(words[:show_cnt]), font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode == "strike_vs_new":
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
        sw = min(max_w // 2, int(stage.draw.textlength(txt.split()[0], font=font))) if progress > 0.2 else 0
        if sw > 12:
            stage.draw.line((x, y + 26, x + sw, y + 26), fill=wa(w["rose"], a), width=4)
    elif mode == "quote_serif_glow":
        stage.add_glow_orb(x + 120, y + 26, 70, accent, alpha=int(75 * a))
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    else:
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)


# =========================================================================
# +32 ADDITIONAL SPECIALIZED STUDIO LAYOUTS (Total -> 65 Named Layouts)
# =========================================================================
EXTRA_32_LAYOUTS: Tuple[str, ...] = (
    # AI / ML & True 3D Mesh (7)
    "neural_net_layers", "attention_heatmap", "embedding_cluster", "rag_pipeline_3d",
    "agent_loop_3d", "token_prob_bars", "mesh_3d_stage",
    # Charts & Analytics (8)
    "line_area_chart", "donut_3d", "radar_spider", "sankey_flow",
    "candlestick_pro", "heatmap_matrix", "scatter_plot", "confusion_matrix",
    # UI / Mockups / Social (9)
    "mobile_app_mockup", "browser_window", "chat_thread_ai", "notification_stack",
    "kanban_board", "pricing_tiers", "quote_spotlight", "split_screen_50_50", "countdown_hero",
    # Science / Math / Strategy (8)
    "mindmap_radial", "timeline_gantt", "equation_proof", "before_after_slider",
    "pros_cons_scale", "atom_orbit_3d", "dna_helix_3d", "orbit_ecosystem",
)

_ACCENT_CYCLE = ("cyan", "purple", "emerald", "amber", "rose")
SX0, SY0, SX1, SY1 = 64, 358, 1016, 1426
SW, SH = SX1 - SX0, SY1 - SY0


def render_pro_layout(
    stage: Any,
    layout: str,
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> bool:
    """
    Renders all +32 specialized AI/ML, True-3D Mesh, Chart, Mockup & Science layouts.
    Returns True if handled.
    """
    l = str(layout or "").lower().strip()
    if l not in EXTRA_32_LAYOUTS:
        return False

    _get_font = helpers["_get_font"]
    _draw_wrapped = helpers["_draw_wrapped_text"]
    _with_alpha = helpers["_with_alpha"]
    _spring_gate = helpers["_spring_gate"]
    _ease = helpers["_ease_out_cubic"]
    _anim_num = helpers["_animate_counter_text"]
    _res_col = helpers["resolve_world_color"]
    _bezier = helpers["_draw_bezier_comet"]
    _draw_vis = helpers["_draw_node_visual"]
    d = data or {}
    g0 = _ease(min(1.0, progress / 0.20))

    # --- 1. TRUE NUMPY 3D MESH STAGE & SCIENCE 3D MODELS ---
    if l in ("mesh_3d_stage", "atom_orbit_3d", "dna_helix_3d"):
        mesh_kind = d.get("mesh") or d.get("shape") or ("atom_orbit" if l == "atom_orbit_3d" else ("dna_helix" if l == "dna_helix_3d" else "torus_3d"))
        stage.draw_glass_card((80, SY0 + 20, 1000, SY0 + 690), radius=30, accent_col=world["cyan"], alpha_mul=g0, active=True, layered=True)
        draw_procedural_3d_mesh(stage, 540, SY0 + 350, 265, str(mesh_kind), _res_col(world, d.get("color"), "cyan"), progress=progress, active=True, alpha_mul=g0, secondary_color=world["purple"])
        cap = str(d.get("caption") or d.get("formula") or mesh_kind.replace("_", " ").title())
        stage.draw_pill(540, SY0 + 640, cap[:30], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(23, bold=True), alpha_mul=g0)
        pts = list(d.get("points") or d.get("items") or d.get("notes") or [])[:3]
        for i, pt in enumerate(pts):
            gt = _ease(_spring_gate(progress, i + 1, len(pts) + 1, 0.24))
            y = SY0 + 720 + i * 112
            col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((80, y, 1000, y + 94), radius=20, accent_col=col, alpha_mul=gt)
            _draw_wrapped(stage.draw, (112, y + 26), str(pt.get("title") if isinstance(pt, dict) else pt), _get_font(25, bold=True), _with_alpha(world["text"], gt), 850, max_lines=2)
        return True

    # --- 2. NEURAL NET & AGENT / RAG / MINDMAP / ORBIT PIPELINES ---
    if l == "neural_net_layers":
        layers = list(d.get("layers") or [4, 6, 5, 3])[:5]
        names = list(d.get("layer_names") or [f"Layer {i+1}" for i in range(len(layers))])
        n_l = len(layers)
        stage.draw_glass_card((74, SY0 + 18, 1006, SY1 - 30), radius=26, accent_col=world["purple"], alpha_mul=g0)
        lx_xs = [int(165 + i * (750 / max(1, n_l - 1))) for i in range(n_l)]
        pts_per_layer: List[List[Tuple[int, int]]] = []
        for i, cnt in enumerate(layers):
            c_cnt = min(6, max(2, int(cnt)))
            ys = [int(860 - (c_cnt - 1) * 58 + k * 116) for k in range(c_cnt)]
            pts_per_layer.append([(lx_xs[i], y) for y in ys])
        for i in range(n_l - 1):
            gt = _ease(_spring_gate(progress, i, n_l, 0.24))
            if gt <= 0.03:
                continue
            c_line = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            for p0 in pts_per_layer[i]:
                for p1 in pts_per_layer[i + 1]:
                    stage.draw.line((p0[0], p0[1], p1[0], p1[1]), fill=_with_alpha((*c_line[:3], 85), gt), width=2)
        for i, layer_pts in enumerate(pts_per_layer):
            gt = _ease(_spring_gate(progress, i, n_l, 0.24))
            nc = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_pill(lx_xs[i], SY0 + 70, str(names[i] if i < len(names) else f"L{i+1}")[:12], world["card_alt"], nc, border_col=nc, font=_get_font(20, bold=True), alpha_mul=gt)
            for px, py in layer_pts:
                stage.draw.ellipse((px - 18, py - 18, px + 18, py + 18), fill=_with_alpha(nc, gt), outline=_with_alpha(world["glass_rim"], gt), width=2)
        return True

    if l in ("rag_pipeline_3d", "agent_loop_3d", "mindmap_radial", "orbit_ecosystem"):
        hub = str(d.get("center") or d.get("hub_name") or l.replace("_", " ").title()).strip()
        items = list(d.get("nodes") or d.get("steps") or d.get("branches") or d.get("satellites") or ["Plan", "Tool", "Observe", "Refine"])[:6]
        cx, cy, rad = 540, 880, 325
        for rr in (180, 295, 390):
            stage.draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=_with_alpha((*world["cyan"][:3], 42), g0), width=2)
        n = len(items)
        for i, it in enumerate(items):
            if isinstance(it, str):
                it = {"name": it}
            gt = _ease(_spring_gate(progress, i, n, 0.24))
            if gt <= 0.03:
                continue
            ang = -math.pi / 2.0 + i * (2.0 * math.pi / n) + (progress * 0.28 if l == "orbit_ecosystem" else 0.0)
            px, py = int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))
            col = _res_col(world, it.get("color"), _ACCENT_CYCLE[(i + 1) % len(_ACCENT_CYCLE)])
            _bezier(stage, (cx, cy), (px, py), col, reveal=gt, progress=progress, phase=i * 0.2, label=str(it.get("edge", "")), curve_bend=24, world=world)
            stage.draw_glass_card((px - 135, py - 46, px + 135, py + 48), radius=20, accent_col=col, alpha_mul=gt, active=(int(progress * n) == i))
            _draw_vis(stage, px, py - 74, 34, 16, 22, col, gt, shape=it.get("shape", "hexagon"), icon=it.get("icon", ""), label=it.get("name", ""), progress=progress)
            _draw_wrapped(stage.draw, (px - 122, py - 24), str(it.get("name") or it.get("title") or ""), _get_font(22, bold=True), _with_alpha(world["text"], gt), 244, align="center", max_lines=2)
        draw_procedural_3d_mesh(stage, cx, cy - 18, 68, "geodesic_sphere" if l != "agent_loop_3d" else "atom_orbit", world["cyan"], progress=progress, active=True, alpha_mul=g0)
        stage.draw_pill(cx, cy + 56, hub[:20], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g0)
        return True

    # --- 3. MATRIX / HEATMAPS / SCATTER / CHARTS ---
    if l in ("attention_heatmap", "heatmap_matrix", "confusion_matrix"):
        vals = d.get("matrix") or d.get("grid") or [[0.9, 0.2, 0.1, 0.05], [0.15, 0.85, 0.3, 0.1], [0.1, 0.25, 0.88, 0.2], [0.05, 0.1, 0.2, 0.92]]
        xlabels = list(d.get("x_labels") or d.get("labels") or [f"K{i+1}" for i in range(len(vals[0]))])
        ylabels = list(d.get("y_labels") or d.get("labels") or [f"Q{i+1}" for i in range(len(vals))])
        stage.draw_glass_card((74, SY0 + 20, 1006, SY1 - 40), radius=26, accent_col=world["cyan"], alpha_mul=g0)
        rows_n = min(6, len(vals))
        cols_n = min(6, len(vals[0]) if vals else 4)
        cell_w = min(145, 730 // max(1, cols_n))
        cell_h = min(145, 730 // max(1, rows_n))
        ox = 220
        oy = SY0 + 145
        for c_i in range(cols_n):
            stage.draw.text((ox + c_i * cell_w + 20, oy - 48), str(xlabels[c_i] if c_i < len(xlabels) else f"C{c_i}")[:8], font=_get_font(21, bold=True), fill=_with_alpha(world["cyan"], g0))
        for r_i in range(rows_n):
            stage.draw.text((106, oy + r_i * cell_h + cell_h // 2 - 14), str(ylabels[r_i] if r_i < len(ylabels) else f"R{r_i}")[:8], font=_get_font(21, bold=True), fill=_with_alpha(world["purple"], g0))
            for c_i in range(cols_n):
                gt = _ease(_spring_gate(progress, r_i * cols_n + c_i, rows_n * cols_n, 0.18))
                v = float(vals[r_i][c_i]) if c_i < len(vals[r_i]) else 0.2
                v_n = max(0.05, min(1.0, v / 100.0 if v > 1.0 else v))
                base_col = world["emerald"] if v_n >= 0.7 else (world["cyan"] if v_n >= 0.35 else world["card_layer"])
                bx0, by0 = ox + c_i * cell_w + 6, oy + r_i * cell_h + 6
                stage.draw.rounded_rectangle((bx0, by0, bx0 + cell_w - 12, by0 + cell_h - 12), radius=14, fill=_with_alpha((*base_col[:3], int(80 + 165 * v_n)), gt), outline=_with_alpha(world["border"], gt), width=1)
                stage.draw.text((bx0 + 18, by0 + cell_h // 2 - 20), f"{v:.2f}" if isinstance(v, float) and v <= 1.0 else str(v), font=_get_font(22, bold=True, mono=True), fill=_with_alpha(world["text"], gt))
        return True

    if l in ("line_area_chart", "candlestick_pro", "token_prob_bars", "scatter_plot", "embedding_cluster"):
        stage.draw_glass_card((74, SY0 + 20, 1006, SY1 - 40), radius=26, accent_col=world["cyan"], alpha_mul=g0, active=True)
        ax0, ay0, ax1, ay1 = 150, SY0 + 120, 955, SY1 - 150
        stage.draw.line((ax0, ay1, ax1, ay1), fill=_with_alpha(world["border"], g0), width=3)
        stage.draw.line((ax0, ay0, ax0, ay1), fill=_with_alpha(world["border"], g0), width=3)

        if l in ("scatter_plot", "embedding_cluster"):
            clusters = list(d.get("clusters") or d.get("points") or [
                {"label": "Cluster A", "x": 0.28, "y": 0.32}, {"label": "Cluster B", "x": 0.72, "y": 0.28}, {"label": "Cluster C", "x": 0.52, "y": 0.74}
            ])[:12]
            for i, cl in enumerate(clusters):
                gt = _ease(_spring_gate(progress, i, len(clusters), 0.20))
                if isinstance(cl, str):
                    cl = {"label": cl, "x": (i + 1) * 0.2, "y": 0.5}
                px = int(ax0 + float(cl.get("x", 0.2 + (i % 4) * 0.2)) * (ax1 - ax0))
                py = int(ay0 + float(cl.get("y", 0.25 + (i // 4) * 0.25)) * (ay1 - ay0))
                col = _res_col(world, cl.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                stage.add_glow_orb(px, py, 36, col, alpha=int(120 * gt))
                stage.draw.ellipse((px - 16, py - 16, px + 16, py + 16), fill=_with_alpha(col, gt), outline=_with_alpha(world["glass_rim"], gt), width=2)
                if cl.get("label"):
                    stage.draw_pill(px, py - 34, str(cl["label"])[:16], world["card_alt"], world["text"], border_col=col, font=_get_font(18, bold=True), alpha_mul=gt)
        elif l == "token_prob_bars":
            toks = list(d.get("tokens") or d.get("items") or [{"token": "quantum", "prob": 0.78}, {"token": "neural", "prob": 0.14}, {"token": "vector", "prob": 0.05}, {"token": "other", "prob": 0.03}])[:6]
            rh = min(130, (ay1 - ay0) // max(1, len(toks)))
            for i, tk in enumerate(toks):
                if isinstance(tk, str):
                    tk = {"token": tk, "prob": 0.5}
                gt = _ease(_spring_gate(progress, i, len(toks), 0.22))
                pr = max(0.04, min(1.0, float(tk.get("prob", 0.5))))
                col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                y = ay0 + 20 + i * rh
                stage.draw.text((ax0 + 16, y), str(tk.get("token") or "")[:16], font=_get_font(24, bold=True, mono=True), fill=_with_alpha(world["text"], gt))
                bw = max(24, int(520 * pr * gt))
                stage.draw.rounded_rectangle((ax0 + 230, y + 4, ax0 + 230 + bw, y + 40), radius=10, fill=_with_alpha(col, gt))
                stage.draw.text((ax0 + 245 + bw, y + 6), f"{pr*100:.1f}%", font=_get_font(22, bold=True), fill=_with_alpha(col, gt))
        else:
            series = list(d.get("values") or d.get("points") or [22, 34, 29, 51, 68, 62, 89, 96])[:12]
            nums = [float(x.get("y") if isinstance(x, dict) else x) for x in series]
            mn, mx = min(nums + [0]), max(nums + [1.0])
            coords = []
            for i, val in enumerate(nums):
                px = int(ax0 + (i / max(1, len(nums) - 1)) * (ax1 - ax0))
                py = int(ay1 - ((val - mn) / max(1e-4, mx - mn)) * (ay1 - ay0))
                coords.append((px, py))
            show_n = max(2, int(len(coords) * min(1.0, progress / 0.72)))
            pts = coords[:show_n]
            if l == "candlestick_pro":
                cw = max(20, (ax1 - ax0) // (len(coords) * 2))
                for i, (px, py) in enumerate(pts):
                    up = (i == 0) or (nums[i] >= nums[i - 1])
                    cc = world["emerald"] if up else world["rose"]
                    stage.draw.line((px, max(ay0, py - 46), px, min(ay1, py + 46)), fill=_with_alpha(cc, g0), width=4)
                    stage.draw.rounded_rectangle((px - cw // 2, py - 24, px + cw // 2, py + 24), radius=6, fill=_with_alpha(cc, g0))
            else:
                if len(pts) >= 2:
                    poly = [(pts[0][0], ay1)] + pts + [(pts[-1][0], ay1)]
                    stage.draw.polygon(poly, fill=_with_alpha((*world["cyan"][:3], 42), g0))
                    stage.add_glow_line(pts, world["cyan"], width=12, alpha=140)
                    stage.draw.line(pts, fill=_with_alpha(world["cyan"], g0), width=5)
                for px, py in pts:
                    stage.draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=_with_alpha(world["emerald"], g0), outline=_with_alpha((255, 255, 255, 230), g0), width=2)
        return True

    if l == "donut_3d":
        slices = list(d.get("slices") or d.get("items") or [{"label": "Compute", "value": 45}, {"label": "Storage", "value": 30}, {"label": "Network", "value": 25}])[:5]
        tot = sum(max(1.0, float(s.get("value", 20))) for s in slices)
        cx, cy, rad = 540, 680, 220
        cur_ang = -90.0
        for i, sl in enumerate(slices):
            gt = _ease(_spring_gate(progress, i, len(slices), 0.25))
            v = float(sl.get("value", 20))
            ang = (v / tot) * 360.0 * gt
            col = _res_col(world, sl.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            if ang > 1.0:
                stage.draw.pieslice((cx - rad, cy - rad, cx + rad, cy + rad), start=cur_ang, end=cur_ang + ang, fill=_with_alpha(col, gt), outline=_with_alpha(world["bg_top"], gt), width=4)
            cur_ang += ang
            ly = 980 + i * 74
            stage.draw_glass_card((110, ly, 970, ly + 60), radius=16, accent_col=col, alpha_mul=gt)
            stage.draw.ellipse((136, ly + 18, 160, ly + 42), fill=_with_alpha(col, gt))
            stage.draw.text((182, ly + 15), str(sl.get("label") or "")[:30], font=_get_font(23, bold=True), fill=_with_alpha(world["text"], gt))
            stage.draw.text((830, ly + 15), f"{int(round(v/tot*100))}%", font=_get_font(23, bold=True), fill=_with_alpha(col, gt))
        stage.draw.ellipse((cx - 110, cy - 110, cx + 110, cy + 110), fill=_with_alpha(world["bg_top"], g0), outline=_with_alpha(world["border"], g0), width=3)
        _draw_wrapped(stage.draw, (cx - 90, cy - 22), str(d.get("center") or "TOTAL"), _get_font(26, bold=True), _with_alpha(world["text"], g0), 180, align="center", max_lines=2)
        return True

    if l == "radar_spider":
        axes = list(d.get("axes") or d.get("metrics") or [{"label": "Speed", "value": 92}, {"label": "Scale", "value": 85}, {"label": "Cost", "value": 78}, {"label": "Safety", "value": 90}, {"label": "DX", "value": 88}])[:6]
        cx, cy, rad = 540, 860, 290
        n = len(axes)
        for ring in (0.33, 0.66, 1.0):
            poly = [(cx + int(rad * ring * math.cos(-math.pi / 2 + i * 2 * math.pi / n)), cy + int(rad * ring * math.sin(-math.pi / 2 + i * 2 * math.pi / n))) for i in range(n)]
            stage.draw.polygon(poly, outline=_with_alpha((*world["border"][:3], 120), g0))
        v_poly = []
        for i, ax in enumerate(axes):
            if isinstance(ax, str):
                ax = {"label": ax, "value": 75}
            val = max(10.0, min(100.0, float(ax.get("value", 75)))) * min(1.0, progress / 0.45)
            ang = -math.pi / 2 + i * 2 * math.pi / n
            vx, vy = int(cx + rad * (val / 100.0) * math.cos(ang)), int(cy + rad * (val / 100.0) * math.sin(ang))
            v_poly.append((vx, vy))
            lx, ly = int(cx + (rad + 58) * math.cos(ang)), int(cy + (rad + 58) * math.sin(ang))
            stage.draw_pill(lx, ly, str(ax.get("label") or "")[:12], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(19, bold=True), alpha_mul=g0)
        if len(v_poly) >= 3:
            stage.draw.polygon(v_poly, fill=_with_alpha((*world["cyan"][:3], 92), g0), outline=_with_alpha(world["cyan"], g0), width=4)
        return True

    if l == "sankey_flow":
        flows = list(d.get("flows") or [{"from": "Direct", "to": "Signup", "weight": 0.55}, {"from": "Organic", "to": "Signup", "weight": 0.45}, {"from": "Signup", "to": "Paid", "weight": 0.62}])[:5]
        for i, fl in enumerate(flows):
            gt = _ease(_spring_gate(progress, i, len(flows), 0.24))
            y0 = SY0 + 60 + i * 165
            col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((80, y0, 340, y0 + 110), radius=18, accent_col=col, alpha_mul=gt)
            _draw_wrapped(stage.draw, (96, y0 + 36), str(fl.get("from", "Source")), _get_font(23, bold=True), _with_alpha(world["text"], gt), 228, align="center", max_lines=2)
            stage.draw_glass_card((740, y0, 1000, y0 + 110), radius=18, accent_col=world["emerald"], alpha_mul=gt)
            _draw_wrapped(stage.draw, (756, y0 + 36), str(fl.get("to", "Target")), _get_font(23, bold=True), _with_alpha(world["text"], gt), 228, align="center", max_lines=2)
            _bezier(stage, (345, y0 + 55), (735, y0 + 55), col, reveal=gt, progress=progress, label=str(fl.get("label") or f"{int(float(fl.get('weight', 0.5))*100)}%"), world=world)
        return True

    # --- 4. UI / SOCIAL / PRODUCT MOCKUPS ---
    if l == "mobile_app_mockup":
        stage.draw_glass_card((245, SY0 + 16, 835, SY1 - 16), radius=54, accent_col=world["cyan"], alpha_mul=g0, active=True, layered=True)
        stage.draw.rounded_rectangle((465, SY0 + 34, 615, SY0 + 58), radius=12, fill=_with_alpha(world["card_layer"], g0))
        app_items = list(d.get("screens") or d.get("items") or [{"title": "Live Inference", "sub": "42 tokens/sec"}, {"title": "Cache Hit", "sub": "0.3ms Redis"}, {"title": "Status: Healthy", "sub": "99.99% Uptime"}])[:4]
        for i, it in enumerate(app_items):
            if isinstance(it, str):
                it = {"title": it}
            gt = _ease(_spring_gate(progress, i, len(app_items), 0.22))
            y = SY0 + 100 + i * 210
            col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((285, y, 795, y + 172), radius=24, accent_col=col, alpha_mul=gt)
            _draw_wrapped(stage.draw, (315, y + 34), str(it.get("title") or ""), _get_font(27, bold=True), _with_alpha(world["text"], gt), 450, max_lines=2)
            if it.get("sub"):
                _draw_wrapped(stage.draw, (315, y + 96), str(it["sub"]), _get_font(21), _with_alpha(col, gt), 450, max_lines=2)
        return True

    if l == "browser_window":
        stage.draw_glass_card((74, SY0 + 20, 1006, SY1 - 24), radius=26, accent_col=world["purple"], alpha_mul=g0, active=True)
        for k, cc in enumerate(((244, 63, 94), (245, 158, 11), (16, 185, 129))):
            stage.draw.ellipse((104 + k * 28, SY0 + 48, 120 + k * 28, SY0 + 64), fill=_with_alpha(cc, g0))
        stage.draw_pill(560, SY0 + 56, str(d.get("url") or "https://app.studio.dev")[:36], world["card_layer"], world["muted"], border_col=world["border"], font=_get_font(20, mono=True), alpha_mul=g0, pad_x=60, pad_y=6)
        _draw_wrapped(stage.draw, (120, SY0 + 165), str(d.get("headline") or d.get("title") or "Interactive Web App"), _get_font(44, bold=True), _with_alpha(world["text"], g0), 840, align="center", max_lines=2)
        _draw_wrapped(stage.draw, (140, SY0 + 305), str(d.get("body") or d.get("sub") or ""), _get_font(27), _with_alpha(world["muted"], g0), 800, align="center", max_lines=4)
        if d.get("cta"):
            stage.draw_pill(540, SY0 + 560, str(d["cta"])[:24], world["cyan"], (255, 255, 255), font=_get_font(26, bold=True), alpha_mul=g0, pad_x=36, pad_y=16)
        return True

    if l == "chat_thread_ai":
        msgs = list(d.get("messages") or [{"role": "user", "text": "Why did latency spike?"}, {"role": "ai", "text": "Connection pool exhausted at 480 concurrent reads."}, {"role": "user", "text": "Fix it fast!"}, {"role": "ai", "text": "Enabled PgBouncer transaction pooling -> dropped P99 from 900ms to 12ms."}])[:5]
        y = SY0 + 30
        for i, m in enumerate(msgs):
            if isinstance(m, str):
                m = {"role": "ai" if i % 2 else "user", "text": m}
            gt = _ease(_spring_gate(progress, i, len(msgs), 0.22))
            if gt <= 0.03:
                continue
            is_user = str(m.get("role", "")).lower() in ("user", "human", "right")
            bx0, bx1 = (240, 990) if is_user else (86, 840)
            col = world["cyan"] if is_user else world["emerald"]
            stage.draw_glass_card((bx0, y, bx1, y + 165), radius=24, accent_col=col, alpha_mul=gt, active=(i == len(msgs) - 1))
            stage.draw_pill(bx0 + 82, y + 32, "YOU" if is_user else "AI STUDIO", (*col[:3], 42), col, border_col=col, font=_get_font(17, bold=True), alpha_mul=gt)
            _draw_wrapped(stage.draw, (bx0 + 26, y + 66), str(m.get("text") or ""), _get_font(23), _with_alpha(world["text"], gt), (bx1 - bx0) - 52, max_lines=3)
            y += 188
        return True

    if l in ("notification_stack", "kanban_board", "pricing_tiers", "timeline_gantt", "pros_cons_scale"):
        items = list(d.get("columns") or d.get("tiers") or d.get("tasks") or d.get("items") or [{"title": "Tier 1", "sub": "Baseline"}, {"title": "Tier 2", "sub": "Optimized"}, {"title": "Tier 3", "sub": "Scale"}])[:4]
        n = len(items)
        if l in ("kanban_board", "pricing_tiers"):
            cw = (SW - (n - 1) * 20) // max(1, n)
            for i, it in enumerate(items):
                if isinstance(it, str):
                    it = {"title": it}
                gt = _ease(_spring_gate(progress, i, n, 0.22))
                x0 = SX0 + i * (cw + 20)
                col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                stage.draw_glass_card((x0, SY0 + 40, x0 + cw, SY1 - 60), radius=22, accent_col=col, alpha_mul=gt, active=(i == n - 1))
                _draw_wrapped(stage.draw, (x0 + 16, SY0 + 70), str(it.get("title") or it.get("name") or ""), _get_font(25, bold=True), _with_alpha(col, gt), cw - 32, align="center", max_lines=2)
                sub_list = it.get("cards") or it.get("features") or ([it.get("sub")] if it.get("sub") else [])
                for j, c_txt in enumerate(list(sub_list)[:4]):
                    cy = SY0 + 160 + j * 145
                    stage.draw_glass_card((x0 + 16, cy, x0 + cw - 16, cy + 120), radius=16, accent_col=col, alpha_mul=gt)
                    _draw_wrapped(stage.draw, (x0 + 28, cy + 28), str(c_txt), _get_font(21), _with_alpha(world["text"], gt), cw - 56, align="center", max_lines=3)
        else:
            rh = min(175, (SH - 60) // max(1, n))
            for i, it in enumerate(items):
                if isinstance(it, str):
                    it = {"title": it}
                gt = _ease(_spring_gate(progress, i, n, 0.22))
                y = SY0 + 40 + i * rh
                col = _res_col(world, it.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                stage.draw_glass_card((80, y, 1000, y + rh - 18), radius=22, accent_col=col, alpha_mul=gt, active=(int(progress * n) == i))
                draw_vector_glyph(stage, 136, y + (rh - 18) // 2, str(it.get("icon") or "bell"), 22, col, gt)
                _draw_wrapped(stage.draw, (186, y + 26), str(it.get("title") or it.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], gt), 780, max_lines=1)
                if it.get("sub") or it.get("range"):
                    _draw_wrapped(stage.draw, (186, y + 68), str(it.get("sub") or it.get("range")), _get_font(21), _with_alpha(world["muted"], gt), 780, max_lines=2)
        return True

    # --- 5. QUOTE / SPLIT SCREEN / EQUATION / BEFORE-AFTER / COUNTDOWN ---
    if l in ("quote_spotlight", "equation_proof", "countdown_hero"):
        stage.draw_glass_card((80, SY0 + 95, 1000, SY1 - 125), radius=34, accent_col=world["amber"], alpha_mul=g0, active=True, layered=True)
        big = _anim_num(d.get("value") or d.get("formula") or d.get("quote") or "O(log N)", progress) if l == "countdown_hero" else str(d.get("formula") or d.get("quote") or d.get("statement") or "E = mc^2")
        _draw_wrapped(stage.draw, (124, SY0 + 250), big, _get_font(62 if len(big) < 18 else 40, bold=True, mono=(l == "equation_proof")), _with_alpha(world["amber"] if l == "countdown_hero" else world["text"], g0), 832, align="center", max_lines=4)
        sub = str(d.get("author") or d.get("explanation") or d.get("sub") or "").strip()
        if sub:
            stage.draw_pill(540, SY1 - 210, sub[:34], world["card_alt"], world["cyan"], border_col=world["cyan"], font=_get_font(24, bold=True), alpha_mul=g0)
        return True

    if l in ("split_screen_50_50", "before_after_slider"):
        sep_x = int(540 + (math.sin(progress * math.pi * 2.0) * 140 if l == "before_after_slider" else 0))
        stage.draw_glass_card((72, SY0 + 30, sep_x - 10, SY1 - 30), radius=24, accent_col=world["rose"], alpha_mul=g0)
        _draw_wrapped(stage.draw, (96, SY0 + 90), str(d.get("left_label") or "BEFORE"), _get_font(30, bold=True), _with_alpha(world["rose"], g0), max(120, sep_x - 130), align="center", max_lines=2)
        _draw_wrapped(stage.draw, (96, SY0 + 200), str(d.get("left_text") or "\n".join(d.get("left_points", []))), _get_font(23), _with_alpha(world["text"], g0), max(120, sep_x - 130), max_lines=8)
        stage.draw_glass_card((sep_x + 10, SY0 + 30, 1008, SY1 - 30), radius=24, accent_col=world["emerald"], alpha_mul=g0, active=True)
        _draw_wrapped(stage.draw, (sep_x + 30, SY0 + 90), str(d.get("right_label") or "AFTER"), _get_font(30, bold=True), _with_alpha(world["emerald"], g0), max(120, 960 - sep_x), align="center", max_lines=2)
        _draw_wrapped(stage.draw, (sep_x + 30, SY0 + 200), str(d.get("right_text") or "\n".join(d.get("right_points", []))), _get_font(23), _with_alpha(world["text"], g0), max(120, 960 - sep_x), max_lines=8)
        stage.draw.line((sep_x, SY0 + 20, sep_x, SY1 - 20), fill=_with_alpha(world["amber"], g0), width=5)
        return True

    return True
