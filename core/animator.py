import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, OUTPUT_DIR, FONTS_DIR

# Premium Cyber-Tech Color Palette
COLOR_BG_TOP = (10, 14, 26)
COLOR_BG_MID = (17, 24, 39)
COLOR_BG_BOT = (8, 12, 22)

CARD_BG = (17, 24, 39, 235)
CARD_BORDER = (51, 65, 85, 200)

NEON_CYAN = (56, 189, 248)       # #38BDF8
NEON_PURPLE = (168, 85, 247)     # #A855F7
NEON_EMERALD = (52, 211, 153)    # #34D399
NEON_AMBER = (251, 191, 36)      # #FBBF24
NEON_ROSE = (244, 63, 94)        # #F43F5E

TEXT_PRIMARY = (248, 250, 252)   # Crisp White
TEXT_MUTED = (148, 163, 184)     # Modern Slate Muted

def get_font(size: int = 40, bold: bool = False) -> ImageFont.ImageFont:
    """Returns a clean Truetype font or default PIL font."""
    font_names = ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    if bold:
        font_names = ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] + font_names
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def render_scene_frames(scene: Dict[str, Any], scene_idx: int, total_scenes: int = 4) -> List[Path]:
    """
    Renders high-quality 2D frames for a single scene across its duration.
    Uses ultra-fast JPEG encoding and modern cyber-tech design system.
    """
    duration = max(2.0, float(scene.get("duration", 5.0)))
    total_frames = int(duration * VIDEO_FPS)
    
    scene_frames_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    scene_frames_dir.mkdir(parents=True, exist_ok=True)
    
    visual_type = scene.get("visual_type", "concept_cards")
    visual_data = scene.get("visual_data", {})
    
    frame_paths = []
    
    # Pre-render base background
    base_canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT))
    _draw_background_gradient(base_canvas)
    
    for f in range(total_frames):
        progress = f / max(1, total_frames - 1)  # 0.0 to 1.0
        frame = base_canvas.copy()
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 1. Instagram / Shorts Top Story Progress Bars
        _draw_story_progress_bar(draw, total_scenes, scene_idx, progress)
        
        # 2. Ambient Pulse Glow in center
        _draw_ambient_glow(draw, progress)
        
        # 3. Topic Pill Badge & Scene Title
        _draw_header(draw, visual_data.get("badge", "TECH DEEP-DIVE"), visual_data.get("title", ""))
        
        # 4. Dispatch to dynamic 2D visual scene renderer
        if visual_type == "architecture_flow":
            _render_architecture_flow(draw, visual_data, progress)
        elif visual_type == "alert_diagram":
            _render_alert_diagram(draw, visual_data, progress)
        elif visual_type == "sql_table":
            _render_sql_table(draw, visual_data, progress)
        elif visual_type == "code_terminal":
            _render_code_terminal(draw, visual_data, progress)
        else:
            _render_concept_cards(draw, visual_data, progress)
            
        frame_file = scene_frames_dir / f"frame_{f:04d}.jpg"
        frame.convert("RGB").save(frame_file, "JPEG", quality=88, optimize=False)
        frame_paths.append(frame_file)
        
    return frame_paths

def _draw_background_gradient(img: Image.Image) -> None:
    """Draws rich deep tech gradient with perspective cyber grid."""
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    step = 8
    for y in range(0, h, step):
        ratio = y / h
        if ratio < 0.5:
            r = int(COLOR_BG_TOP[0] + (COLOR_BG_MID[0] - COLOR_BG_TOP[0]) * (ratio * 2))
            g = int(COLOR_BG_TOP[1] + (COLOR_BG_MID[1] - COLOR_BG_TOP[1]) * (ratio * 2))
            b = int(COLOR_BG_TOP[2] + (COLOR_BG_MID[2] - COLOR_BG_TOP[2]) * (ratio * 2))
        else:
            r = int(COLOR_BG_MID[0] + (COLOR_BG_BOT[0] - COLOR_BG_MID[0]) * ((ratio - 0.5) * 2))
            g = int(COLOR_BG_MID[1] + (COLOR_BG_BOT[1] - COLOR_BG_MID[1]) * ((ratio - 0.5) * 2))
            b = int(COLOR_BG_MID[2] + (COLOR_BG_BOT[2] - COLOR_BG_MID[2]) * ((ratio - 0.5) * 2))
        draw.rectangle((0, y, w, y + step), fill=(r, g, b, 255))
        
    # Subtle Dot Matrix Pattern
    dot_color = (255, 255, 255, 14)
    spacing = 80
    for x in range(40, w, spacing):
        for y in range(40, h, spacing):
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=dot_color)

def _draw_ambient_glow(draw: ImageDraw.Draw, progress: float) -> None:
    """Draws subtle animated radial neon aura behind main content."""
    cx = VIDEO_WIDTH // 2
    cy = int(VIDEO_HEIGHT * 0.42 + math.sin(progress * math.pi * 2) * 30)
    for rad in range(360, 60, -45):
        alpha = int(18 * (1.0 - (rad / 360)))
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(56, 189, 248, alpha))

def _draw_story_progress_bar(draw: ImageDraw.Draw, total_scenes: int, current_scene: int, progress: float) -> None:
    """Draws Instagram / Reels style segmented progress indicators at the very top."""
    padding = 50
    bar_y = 55
    bar_h = 7
    gap = 12
    total_w = VIDEO_WIDTH - (padding * 2)
    bar_w = (total_w - ((total_scenes - 1) * gap)) // total_scenes
    
    for i in range(total_scenes):
        bx = padding + i * (bar_w + gap)
        draw.rounded_rectangle((bx, bar_y, bx + bar_w, bar_y + bar_h), radius=4, fill=(255, 255, 255, 50))
        if i < current_scene - 1:
            draw.rounded_rectangle((bx, bar_y, bx + bar_w, bar_y + bar_h), radius=4, fill=NEON_CYAN)
        elif i == current_scene - 1:
            fill_w = max(4, int(bar_w * progress))
            draw.rounded_rectangle((bx, bar_y, bx + fill_w, bar_y + bar_h), radius=4, fill=NEON_CYAN)

def _draw_header(draw: ImageDraw.Draw, badge_text: str, title_text: str) -> None:
    """Draws top branded header badge with glowing border and bold scene title."""
    font_badge = get_font(28, bold=True)
    font_title = get_font(52, bold=True)
    
    badge_str = badge_text.upper()
    bbox = font_badge.getbbox(badge_str)
    bw = bbox[2] - bbox[0] + 50
    bh = 54
    bx = (VIDEO_WIDTH - bw) // 2
    by = 120
    
    # Outer glow & pill
    draw.rounded_rectangle((bx - 3, by - 3, bx + bw + 3, by + bh + 3), radius=28, fill=(56, 189, 248, 50))
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=27, fill=(15, 23, 42, 240), outline=NEON_CYAN, width=3)
    draw.text((bx + 25, by + 12), badge_str, fill=NEON_CYAN, font=font_badge)
    
    # Title
    if title_text:
        title_bbox = font_title.getbbox(title_text)
        tw = title_bbox[2] - title_bbox[0]
        tx = max(50, (VIDEO_WIDTH - tw) // 2)
        draw.text((tx, by + 80), title_text, fill=TEXT_PRIMARY, font=font_title)

def _draw_vector_check(draw: ImageDraw.Draw, cx: int, cy: int, radius: int = 34) -> None:
    """Draws crisp vector checkmark badge without font dependency."""
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(16, 185, 129, 60), outline=NEON_EMERALD, width=4)
    points = [
        (cx - radius * 0.45, cy),
        (cx - radius * 0.1, cy + radius * 0.35),
        (cx + radius * 0.5, cy - radius * 0.35)
    ]
    draw.line(points, fill=TEXT_PRIMARY, width=5)

def _draw_vector_warning(draw: ImageDraw.Draw, cx: int, cy: int, radius: int = 34) -> None:
    """Draws crisp vector warning triangle."""
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(244, 63, 94, 60), outline=NEON_ROSE, width=4)
    draw.line((cx, cy - 14, cx, cy + 5), fill=TEXT_PRIMARY, width=5)
    draw.ellipse((cx - 3, cy + 12, cx + 3, cy + 18), fill=TEXT_PRIMARY)

def _render_concept_cards(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders sleek 2D glassmorphic comparison cards with vector badges and metric HUD."""
    raw_bullets = data.get("bullets", [
        "Zero-Copy Memory Streaming",
        "OS PageCache Kernel Level Buffering",
        "Append-Only Sequential Storage"
    ])
    
    font_head = get_font(38, bold=True)
    font_sub = get_font(28)
    card_w = 940
    card_h = 180
    start_y = 440
    gap = 215
    cx = (VIDEO_WIDTH - card_w) // 2
    
    for i, bullet in enumerate(raw_bullets[:3]):
        cy = start_y + (i * gap)
        card_scale = min(1.0, max(0.0, (progress * 3.5) - (i * 0.35)))
        if card_scale <= 0:
            continue
            
        parts = bullet.split(":") if ":" in bullet else (bullet.split("—") if "—" in bullet else [bullet, ""])
        headline = parts[0].strip()
        subtext = parts[1].strip() if len(parts) > 1 else "High performance architecture principle"
        
        draw.rounded_rectangle((cx - 3, cy - 3, cx + card_w + 3, cy + card_h + 3), radius=26, fill=(56, 189, 248, 35 if i == 0 else 15))
        draw.rounded_rectangle(
            (cx, cy, cx + card_w, cy + card_h),
            radius=24,
            fill=CARD_BG,
            outline=NEON_CYAN if i == 0 else CARD_BORDER,
            width=3 if i == 0 else 2
        )
        
        _draw_vector_check(draw, cx + 70, cy + card_h // 2, radius=32)
        draw.text((cx + 140, cy + 38), headline, fill=TEXT_PRIMARY, font=font_head)
        draw.text((cx + 140, cy + 96), subtext, fill=TEXT_MUTED, font=font_sub)

    # High-Tech Live Metric HUD Card at bottom
    hud_w, hud_h = 940, 150
    hx = (VIDEO_WIDTH - hud_w) // 2
    hy = 1110
    draw.rounded_rectangle((hx - 2, hy - 2, hx + hud_w + 2, hy + hud_h + 2), radius=26, fill=(52, 211, 153, 30))
    draw.rounded_rectangle((hx, hy, hx + hud_w, hy + hud_h), radius=24, fill=(11, 18, 33, 245), outline=NEON_EMERALD, width=3)
    
    font_stat = get_font(50, bold=True)
    font_lbl = get_font(22, bold=True)
    
    metric_val = data.get("metric_value", "1,000,000+ msgs/s")
    metric_lbl = data.get("metric_label", "THROUGHPUT CAPACITY")
    
    draw.text((hx + 50, hy + 28), metric_lbl.upper(), fill=NEON_EMERALD, font=font_lbl)
    draw.text((hx + 50, hy + 65), metric_val, fill=TEXT_PRIMARY, font=font_stat)
    
    draw.text((hx + 640, hy + 28), "SYSTEM LATENCY", fill=NEON_CYAN, font=font_lbl)
    draw.text((hx + 640, hy + 65), "< 2.5 ms", fill=NEON_CYAN, font=font_stat)

def _render_alert_diagram(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders high-impact Hook/Problem scene with glowing radar warning."""
    center_x = VIDEO_WIDTH // 2
    center_y = 580
    pulse = (progress * 2.5) % 1.0
    for ring in range(3):
        r_prog = (pulse + (ring * 0.33)) % 1.0
        rad = int(80 + r_prog * 240)
        alpha = int(120 * (1.0 - r_prog))
        draw.ellipse((center_x - rad, center_y - rad, center_x + rad, center_y + rad), outline=(244, 63, 94, alpha), width=3)
        
    _draw_vector_warning(draw, center_x, center_y, radius=70)
    
    box_w, box_h = 920, 240
    bx = (VIDEO_WIDTH - box_w) // 2
    by = 780
    draw.rounded_rectangle((bx - 3, by - 3, bx + box_w + 3, by + box_h + 3), radius=26, fill=(244, 63, 94, 40))
    draw.rounded_rectangle((bx, by, bx + box_w, by + box_h), radius=24, fill=(24, 15, 23, 245), outline=NEON_ROSE, width=4)
    
    font_h = get_font(44, bold=True)
    font_s = get_font(30)
    
    p_title = data.get("problem_title", data.get("title", "High-Volume Production Bottleneck"))
    p_sub = data.get("problem_desc", data.get("subtitle", "Traditional message brokers hit I/O locks and JVM garbage collection crashes at scale."))
    
    draw.text((bx + 40, by + 40), p_title, fill=TEXT_PRIMARY, font=font_h)
    
    words = p_sub.split()
    line1 = " ".join(words[:7])
    line2 = " ".join(words[7:]) if len(words) > 7 else ""
    draw.text((bx + 40, by + 110), line1, fill=TEXT_MUTED, font=font_s)
    if line2:
        draw.text((bx + 40, by + 155), line2, fill=TEXT_MUTED, font=font_s)
        
    cx, cy, cw, ch = bx, 1080, box_w, 150
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=20, fill=CARD_BG, outline=NEON_AMBER, width=3)
    draw.text((cx + 40, cy + 30), "CRITICAL CHALLENGE", fill=NEON_AMBER, font=get_font(24, bold=True))
    draw.text((cx + 40, cy + 75), "How do you achieve 100% Zero Data Loss without speed drops?", fill=TEXT_PRIMARY, font=get_font(30, bold=True))

def _render_architecture_flow(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders 2D Architecture Nodes with animated data flow stream and particle packets."""
    nodes = data.get("nodes", [
        {"id": "src", "label": "Producers (IoT / Web)", "sub": "1,000,000 Events / sec", "color": "#38BDF8"},
        {"id": "eng", "label": "Kafka Cluster (Partitions)", "sub": "Sequential Append-Only Log", "color": "#FBBF24"},
        {"id": "tgt", "label": "Consumer Analytics", "sub": "Zero-Copy sendfile() Stream", "color": "#34D399"}
    ])
    
    font_title = get_font(40, bold=True)
    font_sub = get_font(28)
    
    node_w, node_h = 820, 180
    center_x = (VIDEO_WIDTH - node_w) // 2
    start_y = 440
    gap = 250
    
    node_coords = []
    for i, node in enumerate(nodes[:3]):
        ny = start_y + (i * gap)
        node_coords.append((center_x + node_w // 2, ny + node_h // 2))
        
        color_hex = node.get("color", "#38BDF8")
        accent_rgb = _hex_to_rgb(color_hex)
        
        draw.rounded_rectangle((center_x - 3, ny - 3, center_x + node_w + 3, ny + node_h + 3), radius=26, fill=(*accent_rgb, 35))
        draw.rounded_rectangle((center_x, ny, center_x + node_w, ny + node_h), radius=24, fill=CARD_BG, outline=accent_rgb, width=3)
        draw.ellipse((center_x + 40, ny + 70, center_x + 80, ny + 110), fill=accent_rgb)
        
        draw.text((center_x + 110, ny + 40), node.get("label", ""), fill=TEXT_PRIMARY, font=font_title)
        draw.text((center_x + 110, ny + 98), node.get("sub", ""), fill=TEXT_MUTED, font=font_sub)

    for i in range(len(node_coords) - 1):
        x1, y1 = node_coords[i]
        x2, y2 = node_coords[i + 1]
        draw.line((x1, y1 + node_h // 2, x2, y2 - node_h // 2), fill=CARD_BORDER, width=6)
        
        for p_offset in [0.0, 0.33, 0.66]:
            particle_t = (progress * 3.0 + (i * 0.5) + p_offset) % 1.0
            py = (y1 + node_h // 2) + particle_t * ((y2 - node_h // 2) - (y1 + node_h // 2))
            draw.ellipse((x1 - 12, py - 12, x1 + 12, py + 12), fill=(56, 189, 248, 100))
            draw.ellipse((x1 - 7, py - 7, x1 + 7, py + 7), fill=NEON_CYAN)

def _render_sql_table(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders interactive 2D SQL table with animated row highlighting."""
    table_data = data.get("table_data", {
        "headers": ["partition", "offset", "payload", "status"],
        "rows": [
            ["P-0", "009142", "Order_Created", "ACK"],
            ["P-1", "009143", "Payment_Done", "ACK"],
            ["P-2", "009144", "Inventory_Sync", "ACK"],
            ["P-0", "009145", "Dispatch_Ready", "LIVE"]
        ]
    })
    code = data.get("code_snippet", "topic.produce(key=user_id, value=event, acks='all')")
    
    font_head = get_font(30, bold=True)
    font_cell = get_font(28)
    font_code = get_font(28, bold=True)
    
    qx, qy, qw, qh = 80, 440, 920, 150
    draw.rounded_rectangle((qx, qy, qx + qw, qy + qh), radius=20, fill=CARD_BG, outline=NEON_PURPLE, width=3)
    draw.text((qx + 30, qy + 20), "PIPELINE LOGIC:", fill=NEON_PURPLE, font=get_font(22, bold=True))
    draw.text((qx + 30, qy + 65), code, fill=TEXT_PRIMARY, font=font_code)
    
    tx, ty, tw = 80, 630, 920
    headers = table_data.get("headers", ["Col 1", "Col 2", "Col 3", "Col 4"])
    rows = table_data.get("rows", [])
    
    col_w = tw // len(headers)
    row_h = 95
    
    draw.rounded_rectangle((tx, ty, tx + tw, ty + row_h), radius=16, fill=(30, 41, 59, 240), outline=CARD_BORDER, width=2)
    for c_idx, h in enumerate(headers):
        draw.text((tx + (c_idx * col_w) + 25, ty + 28), str(h).upper(), fill=NEON_CYAN, font=font_head)
        
    active_row = int((progress * len(rows)) % len(rows)) if rows else 0
    for r_idx, row in enumerate(rows):
        ry = ty + ((r_idx + 1) * row_h) + 14
        is_highlighted = (r_idx == active_row)
        bg = (56, 189, 248, 45) if is_highlighted else CARD_BG
        border = NEON_AMBER if is_highlighted else CARD_BORDER
        
        draw.rounded_rectangle((tx, ry, tx + tw, ry + row_h - 10), radius=14, fill=bg, outline=border, width=3 if is_highlighted else 1)
        for c_idx, cell in enumerate(row):
            txt_color = NEON_AMBER if (is_highlighted and c_idx == len(row) - 1) else TEXT_PRIMARY
            draw.text((tx + (c_idx * col_w) + 25, ry + 25), str(cell), fill=txt_color, font=font_cell)

def _render_code_terminal(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders macOS-style dark code terminal with dynamic typing effect."""
    raw_code = data.get("code_snippet", "def kafka_stream_handler(event):\n    # Zero-copy memory mapped file\n    return broker.append_log(event, acks=-1)")
    lines = raw_code.split("\n")
    
    tx, ty, tw, th = 80, 460, 920, 750
    draw.rounded_rectangle((tx, ty, tx + tw, ty + th), radius=24, fill=(15, 23, 42, 245), outline=CARD_BORDER, width=3)
    
    draw.rounded_rectangle((tx, ty, tx + tw, ty + 70), radius=24, fill=(30, 41, 59, 255))
    draw.ellipse((tx + 30, ty + 24, tx + 52, ty + 46), fill=(239, 68, 68))
    draw.ellipse((tx + 65, ty + 24, tx + 87, ty + 46), fill=(245, 158, 11))
    draw.ellipse((tx + 100, ty + 24, tx + 122, ty + 46), fill=(16, 185, 129))
    draw.text((tx + 150, ty + 20), "producer.py — High-Throughput Stream", fill=TEXT_MUTED, font=get_font(26))
    
    font_code = get_font(32)
    total_chars = len(raw_code)
    chars_to_show = int(progress * total_chars * 1.5)
    
    current_char_count = 0
    line_y = ty + 120
    for i, line in enumerate(lines):
        line_num = f"{i + 1:2d}  "
        draw.text((tx + 30, line_y), line_num, fill=(71, 85, 105), font=font_code)
        
        remaining = max(0, chars_to_show - current_char_count)
        visible = line[:remaining]
        draw.text((tx + 100, line_y), visible, fill=NEON_EMERALD if "def " in line or "return" in line else TEXT_PRIMARY, font=font_code)
        
        current_char_count += len(line) + 1
        line_y += 70
        if current_char_count >= chars_to_show:
            cx = tx + 100 + len(visible) * 18
            draw.rectangle((cx, line_y - 65, cx + 4, line_y - 25), fill=NEON_CYAN)
            break

def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Converts hex string to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    return (56, 189, 248)
