import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

ALL_BACKDROPS: Tuple[str, ...] = (
    "subtle_grid",
    "aurora_mesh",
    "pcb_circuits",
    "topo_contours",
    "hex_honeycomb",
    "dot_matrix",
    "starfield_cosmos",
    "bokeh_cinema",
    "concentric_radar",
    "isometric_cubes_subtle",
    "duotone_beam",
    "paper_editorial",
    "glass_caustics",
    "plasma_wave",
    "voronoi_cells",
    "orbital_arcs",
    "prism_rays",
    "code_stream_subtle",
)

ALL_3D_MESHES: Tuple[str, ...] = (
    "torus_3d",
    "dna_helix",
    "atom_orbit",
    "geodesic_sphere",
    "neural_lattice",
    "terrain_wave_3d",
    "bar_landscape_3d",
    "cube_cluster_3d",
    "vortex_spiral_3d",
    "mobius_ring",
    "icosahedron_3d",
    "octahedron_3d",
)


def _with_alpha(col: Tuple[int, ...], alpha_mul: float) -> Tuple[int, int, int, int]:
    a_m = max(0.0, min(1.0, float(alpha_mul)))
    base_a = col[3] if len(col) >= 4 else 255
    return (int(col[0]), int(col[1]), int(col[2]), max(0, min(255, int(base_a * a_m))))


# =========================================================================
# 18+ PROCEDURAL BACKDROP & MATHEMATICAL SHADER ENGINE (Zero heavy jali!)
# =========================================================================
def render_procedural_backdrop(
    w: int,
    h: int,
    world: Dict[str, Any],
    style: str = "subtle_grid",
    progress: float = 0.0,
) -> Image.Image:
    """
    Renders 18+ edge-faded procedural shader & studio backdrops cleanly in vectorized NumPy
    with radial spotlights (ZERO distracting floor Tron mesh).
    """
    st = str(style or "subtle_grid").lower().strip()
    is_light = bool(world.get("is_light", False))
    y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]

    top = np.array(world["bg_top"], dtype=np.float32)[None, None, :]
    bot = np.array(world["bg_bot"], dtype=np.float32)[None, None, :]
    arr = top * (1.0 - y[..., None]) + bot * y[..., None]

    spot_a = np.array(world["spot_a"], dtype=np.float32)[None, None, :]
    spot_b = np.array(world["spot_b"], dtype=np.float32)[None, None, :]
    spot_c = np.array(world.get("spot_c", world["spot_a"]), dtype=np.float32)[None, None, :]
    grid_rgb = np.array(world["grid_col"], dtype=np.float32)[None, None, :]

    # Volumetric primary/secondary lighting
    d2_a = ((x - 0.48) * 1.15) ** 2 + ((y - 0.28) * 1.40) ** 2
    ia = np.exp(-d2_a * 4.4)[..., None]
    d2_b = ((x - 0.78) * 1.25) ** 2 + ((y - 0.72) * 1.35) ** 2
    ib = np.exp(-d2_b * 5.0)[..., None]
    vignette = np.exp(-(((x - 0.50) * 1.50) ** 2 + ((y - 0.48) * 1.32) ** 2))

    if is_light:
        arr = arr - 8.0 * ia + (spot_a - arr) * (ia * 0.08) + (spot_b - arr) * (ib * 0.05)
    else:
        arr = arr + spot_a * (ia * 0.14) + spot_b * (ib * 0.10)

    # Shader field variants computed directly on NumPy grid (quarter-res if trig-heavy for speed!)
    if st in ("aurora_mesh", "plasma_wave", "topo_contours", "glass_caustics", "voronoi_cells"):
        qw, qh = max(64, w // 4), max(64, h // 4)
        qy = np.linspace(0.0, 1.0, qh, dtype=np.float32)[:, None]
        qx = np.linspace(0.0, 1.0, qw, dtype=np.float32)[None, :]
        ph = progress * 2.4
        if st == "aurora_mesh":
            w1 = 0.5 + 0.5 * np.sin(qx * 5.5 + np.cos(qy * 4.2 + ph))
            w2 = 0.5 + 0.5 * np.cos(qy * 6.0 - np.sin(qx * 4.8 + ph * 0.7))
            field = np.stack([w1, w2], axis=-1)
            q_rgb = spot_a * field[..., :1] * 0.18 + spot_c * field[..., 1:] * 0.14
        elif st == "plasma_wave":
            val = np.sin(qx * 9.0 + ph) + np.sin(qy * 7.5 - ph * 1.1) + np.sin((qx + qy) * 6.5 + ph * 0.6)
            norm = (0.5 + 0.5 * np.sin(val * 1.1))[..., None]
            q_rgb = (spot_a * norm + spot_b * (1.0 - norm)) * (0.11 if is_light else 0.19)
        elif st == "topo_contours":
            elev = np.sin(qx * 7.0 + 0.4 * np.cos(qy * 5.0)) * np.cos(qy * 6.0 + ph * 0.35)
            band = np.exp(-((np.sin(elev * 11.0)) ** 2) * 36.0)[..., None]
            q_rgb = spot_a * band * (0.14 if is_light else 0.22)
        elif st == "glass_caustics":
            c1 = np.abs(np.sin(qx * 9.0 + np.sin(qy * 7.0 + ph)))
            c2 = np.abs(np.cos(qy * 8.0 - np.cos(qx * 7.0 - ph * 0.8)))
            rib = np.exp(-np.minimum(c1, c2) * 9.0)[..., None]
            q_rgb = (spot_a * 0.6 + spot_b * 0.4) * rib * 0.20
        else:  # voronoi_cells
            pts = [(0.2, 0.25), (0.8, 0.3), (0.5, 0.55), (0.25, 0.8), (0.78, 0.78), (0.5, 0.15)]
            d_min = np.full((qh, qw), 99.0, dtype=np.float32)
            d_sec = np.full((qh, qw), 99.0, dtype=np.float32)
            for px, py in pts:
                dist = np.hypot(qx - px, (qy - py) * (qh / max(1, qw)))
                d_sec = np.minimum(d_sec, np.maximum(d_min, dist))
                d_min = np.minimum(d_min, dist)
            edge = np.exp(-np.abs(d_sec - d_min) * 42.0)[..., None]
            q_rgb = spot_a * edge * (0.14 if is_light else 0.20)

        q_img = Image.fromarray(np.clip(q_rgb, 0, 255).astype(np.uint8), mode="RGB").resize((w, h), Image.Resampling.BILINEAR)
        q_arr = np.array(q_img, dtype=np.float32) * vignette[..., None]
        if is_light:
            arr = arr - q_arr * 0.32
        else:
            arr = arr + q_arr * 0.90

    elif st == "duotone_beam":
        diag = np.exp(-(((x - y * 0.72 - 0.15) * 4.5) ** 2))[..., None]
        arr = arr + spot_a * (diag * (0.09 if is_light else 0.18))
    elif st == "prism_rays":
        for k_ang in (-0.35, 0.25, 0.85):
            ray = np.exp(-(((x - 0.5) * math.cos(k_ang) + (y - 0.35) * math.sin(k_ang)) * 6.5) ** 2)[..., None]
            arr = arr + spot_b * (ray * (0.05 if is_light else 0.10))

    if st in ("subtle_grid", "paper_editorial"):
        step = 84 if st == "subtle_grid" else 112
        gx = (np.arange(w)[None, :] % step == 0)
        gy = (np.arange(h)[:, None] % step == 0)
        g_alpha = ((gx | gy).astype(np.float32) * vignette * (0.045 if not is_light else 0.08))[..., None]
        arr = arr * (1.0 - g_alpha) + grid_rgb * g_alpha

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")

    # Vector overlay backdrops drawn subtly inside radial vignette
    if st in ("pcb_circuits", "hex_honeycomb", "dot_matrix", "starfield_cosmos", "bokeh_cinema", "concentric_radar", "isometric_cubes_subtle", "orbital_arcs", "code_stream_subtle"):
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov, "RGBA")
        ac = world["spot_a"]
        sc = world["spot_b"]
        a_base = 34 if not is_light else 46
        if st == "dot_matrix":
            for py_i in range(80, h - 80, 56):
                for px_i in range(60, w - 60, 56):
                    fx = ((px_i / w) - 0.5) * 1.5
                    fy = ((py_i / h) - 0.5) * 1.3
                    fall = math.exp(-(fx * fx + fy * fy))
                    if fall > 0.22:
                        d.ellipse((px_i - 2, py_i - 2, px_i + 2, py_i + 2), fill=(*ac, int(a_base * fall)))
        elif st == "pcb_circuits":
            for i in range(14):
                x0 = int((i * 173 + 60) % w)
                y0 = int((i * 239 + 120) % (h - 300))
                xm = x0 + (90 if i % 2 == 0 else -90)
                ym = y0 + 130
                col_t = ac if i % 2 == 0 else sc
                d.line([(x0, y0), (xm, y0), (xm, ym)], fill=(*col_t, int(a_base * 0.9)), width=2)
                d.ellipse((xm - 4, ym - 4, xm + 4, ym + 4), outline=(*col_t, int(a_base * 1.2)), width=2)
        elif st == "hex_honeycomb":
            r = 46
            dy = int(r * 1.5)
            dx = int(r * math.sqrt(3))
            for row, cy in enumerate(range(120, h - 120, dy)):
                off = dx // 2 if row % 2 else 0
                for cx in range(90 + off, w - 60, dx):
                    fall = math.exp(-(((cx / w) - 0.5) * 1.6) ** 2 - (((cy / h) - 0.5) * 1.4) ** 2)
                    if fall > 0.28:
                        pts = [(cx + int(r * 0.88 * math.cos(math.radians(a + 30))), cy + int(r * 0.88 * math.sin(math.radians(a + 30)))) for a in range(0, 360, 60)]
                        d.polygon(pts, outline=(*ac, int(a_base * 0.65 * fall)))
        elif st == "starfield_cosmos":
            for i in range(65):
                sx = int((i * 313 + 71) % w)
                sy = int((i * 499 + 19) % h)
                sr = 1 if i % 3 else 2
                scol = (255, 255, 255) if not is_light else ac
                d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(*scol[:3], 35 + (i % 5) * 14))
        elif st == "bokeh_cinema":
            for i in range(9):
                bx = int((i * 263 + 120) % w)
                by = int((i * 389 + 160) % h)
                br = 42 + (i % 4) * 24
                d.ellipse((bx - br, by - br, bx + br, by + br), fill=(*(ac if i % 2 == 0 else sc), 18))
        elif st == "concentric_radar" or st == "orbital_arcs":
            cx, cy = w // 2, h // 2
            for rad in range(160, 820, 120):
                d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=(*ac, 26), width=2)
        elif st == "isometric_cubes_subtle":
            for i in range(10):
                cx = 110 + (i % 3) * 430
                cy = 240 + (i // 3) * 420
                pts = [(cx, cy - 36), (cx + 56, cy), (cx, cy + 36), (cx - 56, cy)]
                d.polygon(pts, outline=(*ac, 28), width=2)
        else:  # code_stream_subtle
            for i in range(16):
                col_x = 40 + i * 66
                for k in range(8):
                    cy = 140 + ((k * 180 + i * 75) % (h - 280))
                    d.rectangle((col_x, cy, col_x + 4, cy + 16), fill=(*ac, 22))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    return img


# =========================================================================
# TRUE 3D PERSPECTIVE CAMERA & Z-SORTED TRIANGLE MESH RENDERER (Pure NumPy)
# =========================================================================
def _rotate_3d(pts: np.ndarray, yaw: float, pitch: float, roll: float = 0.0) -> np.ndarray:
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], dtype=np.float32)
    rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]], dtype=np.float32)
    return pts @ (ry @ rx @ rz).T


def _project_3d(pts: np.ndarray, cx: int, cy: int, scale: float, cam_dist: float = 4.2) -> np.ndarray:
    z = cam_dist - pts[:, 2]
    z = np.maximum(0.4, z)
    factor = (scale * cam_dist) / (z * cam_dist)
    px = cx + pts[:, 0] * scale / (z / cam_dist)
    py = cy + pts[:, 1] * scale / (z / cam_dist)
    return np.stack([px, py, z], axis=1)


def _render_shaded_mesh(
    stage: Any,
    verts: np.ndarray,
    faces: List[Tuple[int, ...]],
    cx: int,
    cy: int,
    scale: float,
    color: Tuple[int, int, int],
    yaw: float,
    pitch: float,
    alpha_mul: float = 1.0,
) -> None:
    rot = _rotate_3d(verts, yaw, pitch, 0.18)
    proj = _project_3d(rot, cx, cy, scale)
    light_dir = np.array([0.45, -0.68, 0.58], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)

    sorted_faces = []
    for f in faces:
        z_avg = float(np.mean(rot[list(f), 2]))
        sorted_faces.append((z_avg, f))
    sorted_faces.sort(key=lambda t: t[0])

    eff = max(0.0, min(1.0, float(alpha_mul) * getattr(stage, "t_alpha", 1.0)))
    r, g, b = color[:3]
    wire = _with_alpha((min(255, r + 90), min(255, g + 90), min(255, b + 90), 210), eff)

    for _, f in sorted_faces:
        v0, v1, v2 = rot[f[0]], rot[f[1]], rot[f[2]]
        normal = np.cross(v1 - v0, v2 - v0)
        nlen = float(np.linalg.norm(normal))
        if nlen < 1e-6:
            continue
        normal /= nlen
        diff = max(0.18, min(1.0, 0.34 + 0.66 * float(np.dot(normal, light_dir))))
        fcol = (int(r * diff + 28 * diff), int(g * diff + 28 * diff), int(b * diff + 34 * diff), int(238 * eff))
        poly = [(float(proj[idx, 0]), float(proj[idx, 1])) for idx in f]
        stage.draw.polygon(poly, fill=fcol, outline=wire)


def draw_procedural_3d_mesh(
    stage: Any,
    cx: int,
    cy: int,
    size: int,
    kind: str,
    color: Tuple[int, int, int],
    progress: float = 0.5,
    active: bool = True,
    alpha_mul: float = 1.0,
    secondary_color: Optional[Tuple[int, int, int]] = None,
) -> None:
    """
    Pure NumPy True 3D Perspective Camera & Shaded Surface/Lattice Renderer:
    Renders real rotating 3D Torus, DNA Double-Helix, Atom Orbitals, Geodesic Sphere,
    Neural Lattice, 3D Wave Terrain, 3D Bar Landscape, Cube Cluster, Vortex, Mobius, Icosahedron, Octahedron.
    """
    eff = max(0.0, min(1.0, float(alpha_mul) * getattr(stage, "t_alpha", 1.0)))
    if eff <= 0.03:
        return
    k = str(kind or "torus_3d").lower().strip()
    yaw = progress * math.pi * (1.8 if active else 0.7) + 0.45
    pitch = 0.42 + math.sin(progress * math.pi * 2.0) * 0.14
    sec = secondary_color or stage.world.get("purple", (168, 85, 247))

    if active and hasattr(stage, "add_glow_orb"):
        stage.add_glow_orb(cx, cy, size * 0.95, color, alpha=int(88 * eff))

    if k in ("torus_3d", "mobius_ring"):
        u_cnt, v_cnt = 18, 10
        R, r_tube = 0.76, 0.28
        verts = []
        faces = []
        for ui in range(u_cnt):
            u = 2.0 * math.pi * ui / u_cnt
            for vi in range(v_cnt):
                v = 2.0 * math.pi * vi / v_cnt
                twist = 0.5 * u if k == "mobius_ring" else 0.0
                rad = R + r_tube * math.cos(v + twist)
                verts.append([rad * math.cos(u), r_tube * math.sin(v + twist), rad * math.sin(u)])
        v_arr = np.array(verts, dtype=np.float32)
        for ui in range(u_cnt):
            u_next = (ui + 1) % u_cnt
            for vi in range(v_cnt):
                v_next = (vi + 1) % v_cnt
                a = ui * v_cnt + vi
                b = u_next * v_cnt + vi
                c = u_next * v_cnt + v_next
                d_i = ui * v_cnt + v_next
                faces.append((a, b, c, d_i))
        _render_shaded_mesh(stage, v_arr, faces, cx, cy, size * 0.86, color, yaw, pitch + 0.35, alpha_mul)

    elif k == "icosahedron_3d":
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        v_arr = np.array([
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
        ], dtype=np.float32) / 1.75
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
        ]
        _render_shaded_mesh(stage, v_arr, faces, cx, cy, size * 0.95, color, yaw, pitch, alpha_mul)

    elif k == "octahedron_3d":
        v_arr = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], dtype=np.float32)
        faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        _render_shaded_mesh(stage, v_arr, faces, cx, cy, size * 0.92, color, yaw, pitch, alpha_mul)

    elif k == "dna_helix":
        pts = []
        n_bp = 14
        for i in range(n_bp):
            t = (i / (n_bp - 1)) * 2.0 - 1.0
            ang = t * math.pi * 2.2
            pts.append([0.55 * math.cos(ang), t * 0.95, 0.55 * math.sin(ang)])
            pts.append([-0.55 * math.cos(ang), t * 0.95, -0.55 * math.sin(ang)])
        v_arr = _rotate_3d(np.array(pts, dtype=np.float32), yaw, 0.25, 0.15)
        proj = _project_3d(v_arr, cx, cy, size * 0.92)
        for i in range(0, len(pts) - 2, 2):
            stage.draw.line([(proj[i, 0], proj[i, 1]), (proj[i + 2, 0], proj[i + 2, 1])], fill=_with_alpha((*color[:3], 220), eff), width=4)
            stage.draw.line([(proj[i + 1, 0], proj[i + 1, 1]), (proj[i + 3, 0], proj[i + 3, 1])], fill=_with_alpha((*sec[:3], 220), eff), width=4)
            stage.draw.line([(proj[i, 0], proj[i, 1]), (proj[i + 1, 0], proj[i + 1, 1])], fill=_with_alpha((226, 232, 240, 150), eff), width=2)
        for j in range(len(pts)):
            px, py = float(proj[j, 0]), float(proj[j, 1])
            nc = color if j % 2 == 0 else sec
            stage.draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=_with_alpha(nc, eff), outline=_with_alpha((255, 255, 255, 210), eff), width=1)

    elif k in ("atom_orbit", "geodesic_sphere"):
        stage.draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=_with_alpha(color, eff), outline=_with_alpha((255, 255, 255, 220), eff), width=2)
        for oi in range(3):
            ring = np.array([[math.cos(2 * math.pi * i / 36), 0.0, math.sin(2 * math.pi * i / 36)] for i in range(36)], dtype=np.float32)
            rot_r = _rotate_3d(ring, yaw + oi * 0.9, 0.55 + oi * 0.7, oi * 1.05)
            p_r = _project_3d(rot_r, cx, cy, size * 0.96)
            rc = color if oi == 0 else (sec if oi == 1 else stage.world.get("amber", (245, 158, 11)))
            stage.draw.line([(float(p_r[i, 0]), float(p_r[i, 1])) for i in range(len(p_r))] + [(float(p_r[0, 0]), float(p_r[0, 1]))], fill=_with_alpha((*rc[:3], 200), eff), width=3)
            e_idx = int((progress * 36 + oi * 12) % 36)
            ex, ey = float(p_r[e_idx, 0]), float(p_r[e_idx, 1])
            stage.draw.ellipse((ex - 7, ey - 7, ex + 7, ey + 7), fill=_with_alpha((255, 255, 255, 250), eff), outline=_with_alpha(rc, eff), width=2)

    elif k in ("neural_lattice", "cube_cluster_3d"):
        coords = np.array([[ix - 0.5, iy - 0.5, iz - 0.5] for ix in (0, 1) for iy in (0, 1) for iz in (0, 1)] + [[0, 0, 0]], dtype=np.float32) * 1.25
        rot = _rotate_3d(coords, yaw, pitch)
        proj = _project_3d(rot, cx, cy, size * 0.95)
        for i in range(8):
            for j in range(i + 1, 9):
                if np.linalg.norm(coords[i] - coords[j]) < 1.35:
                    stage.draw.line([(proj[i, 0], proj[i, 1]), (proj[j, 0], proj[j, 1])], fill=_with_alpha((*color[:3], 155), eff), width=2)
        for idx in range(len(coords)):
            px, py = float(proj[idx, 0]), float(proj[idx, 1])
            r_n = 11 if idx == 8 else 7
            stage.draw.ellipse((px - r_n, py - r_n, px + r_n, py + r_n), fill=_with_alpha(sec if idx == 8 else color, eff))

    elif k in ("terrain_wave_3d", "bar_landscape_3d", "vortex_spiral_3d"):
        grid_n = 7
        xs = np.linspace(-0.85, 0.85, grid_n, dtype=np.float32)
        pts = []
        for gi, gx in enumerate(xs):
            for gj, gz in enumerate(xs):
                gy = -0.35 * math.sin(gx * 3.5 + progress * 5.0) * math.cos(gz * 3.5) if k != "vortex_spiral_3d" else -0.45 * math.exp(-(gx * gx + gz * gz))
                pts.append([gx, gy, gz])
        rot = _rotate_3d(np.array(pts, dtype=np.float32), yaw * 0.5 + 0.55, 0.55)
        proj = _project_3d(rot, cx, cy, size * 0.92)
        for i in range(grid_n):
            for j in range(grid_n):
                idx = i * grid_n + j
                if i + 1 < grid_n:
                    nidx = (i + 1) * grid_n + j
                    stage.draw.line([(proj[idx, 0], proj[idx, 1]), (proj[nidx, 0], proj[nidx, 1])], fill=_with_alpha((*color[:3], 185), eff), width=2)
                if j + 1 < grid_n:
                    nidx = i * grid_n + (j + 1)
                    stage.draw.line([(proj[idx, 0], proj[idx, 1]), (proj[nidx, 0], proj[nidx, 1])], fill=_with_alpha((*sec[:3], 185), eff), width=2)
