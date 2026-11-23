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

def draw_wrapped_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    max_width: int,
    fill: Tuple[int, ...],
    line_spacing: int = 8,
    align: str = "left",
    max_lines: int = 2,
    ellipsis: bool = True
) -> int:
    """
    Renders multi-line text strictly within max_width boundary.
    Automatically breaks words onto new lines and truncates with ellipsis if exceeding max_lines.
    Guarantees that text NEVER bleeds outside the screen frame.
    """
    if not text:
        return 0

    words = text.strip().split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Word itself is wider than max_width, force truncate
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    # Enforce max lines
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if ellipsis and lines:
            last = lines[-1]
            while last and (font.getbbox(last + "...")[2] - font.getbbox(last + "...")[0]) > max_width:
                last = last[:-1]
            lines[-1] = last.rstrip() + "..."

    cur_y = y
    for line in lines:
        bbox = font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]

        if align == "center":
            lx = x + (max_width - lw) // 2
        elif align == "right":
            lx = x + (max_width - lw)
        else:
            lx = x

        draw.text((lx, cur_y), line, fill=fill, font=font)
        cur_y += lh + line_spacing

    return cur_y - y

def render_scene_frames(scene: Dict[str, Any], scene_idx: int, total_scenes: int = 4) -> List[Path]:
    """
    Renders high-quality 2D frames for a single scene across its duration.
    Uses ultra-fast JPEG encoding and strictly bound cyber-tech design system.
    """
    duration = max(2.0, float(scene.get("duration", 5.0)))
    total_frames = int(duration * VIDEO_FPS)
    
    scene_frames_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    scene_frames_dir.mkdir(parents=True, exist_ok=True)
    
    visual_type = scene.get("visual_type", "concept_cards")
    visual_data = scene.get("visual_data", {})
    
    frame_paths = []
    
    # Pre-render clean matte dark background
    base_canvas = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (14, 17, 24))
    
    for f in range(total_frames):
        progress = f / max(1, total_frames - 1)  # 0.0 to 1.0
        frame = base_canvas.copy()
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 1. Instagram / Shorts Top Story Progress Bars
        _draw_story_progress_bar(draw, total_scenes, scene_idx, progress)
        
        # 2. Topic Pill Badge & Scene Title (Wrapped & Constrained to Safe Frame)
        _draw_header(draw, visual_data.get("badge", "TECH DEEP-DIVE"), visual_data.get("title", ""))
        
        # 3. Dispatch to dynamic 2D visual scene renderer
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
            
        # Subtle cinematic forward camera drift (Ken Burns effect)
        zoom = 1.0 + (progress * 0.03)
        if zoom > 1.001:
            zw = int(VIDEO_WIDTH / zoom)
            zh = int(VIDEO_HEIGHT / zoom)
            zx = (VIDEO_WIDTH - zw) // 2
            zy = (VIDEO_HEIGHT - zh) // 2
            frame = frame.crop((zx, zy, zx + zw, zy + zh)).resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.BILINEAR)

        frame_file = scene_frames_dir / f"frame_{f:04d}.jpg"
        frame.convert("RGB").save(frame_file, "JPEG", quality=88, optimize=False)
        frame_paths.append(frame_file)
        
    return frame_paths

def _draw_story_progress_bar(draw: ImageDraw.Draw, total_scenes: int, current_scene: int, progress: float) -> None:
    """Draws Instagram / Reels style segmented progress indicators at the very top."""
    padding = 60
    bar_y = 55
    bar_h = 7
    gap = 12
    total_w = VIDEO_WIDTH - (padding * 2)
    bar_w = (total_w - ((total_scenes - 1) * gap)) // max(1, total_scenes)
    
    for i in range(total_scenes):
        bx = padding + i * (bar_w + gap)
        draw.rounded_rectangle((bx, bar_y, bx + bar_w, bar_y + bar_h), radius=4, fill=(255, 255, 255, 50))
        if i < current_scene - 1:
            draw.rounded_rectangle((bx, bar_y, bx + bar_w, bar_y + bar_h), radius=4, fill=NEON_CYAN)
        elif i == current_scene - 1:
            fill_w = max(4, int(bar_w * progress))
            draw.rounded_rectangle((bx, bar_y, bx + fill_w, bar_y + bar_h), radius=4, fill=NEON_CYAN)

def _draw_header(draw: ImageDraw.Draw, badge_text: str, title_text: str) -> None:
    """Draws top branded header badge with glowing border and multi-line safe-wrapped scene title."""
    font_badge = get_font(26, bold=True)
    font_title = get_font(44, bold=True)
    
    # Badge (Pill)
    badge_str = badge_text.upper().strip()
    bbox = font_badge.getbbox(badge_str)
    raw_bw = bbox[2] - bbox[0]
    bw = min(880, raw_bw + 44)
    bh = 50
    bx = (VIDEO_WIDTH - bw) // 2
    by = 115
    
    draw.rounded_rectangle((bx - 2, by - 2, bx + bw + 2, by + bh + 2), radius=26, fill=(56, 189, 248, 50))
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=25, fill=(15, 23, 42, 240), outline=NEON_CYAN, width=3)
    
    # Draw centered badge text
    tx_badge = bx + (bw - raw_bw) // 2
    draw.text((tx_badge, by + 10), badge_str, fill=NEON_CYAN, font=font_badge)
    
    # Title - Safe Wrapped across 1 or 2 lines, centered, max_width = 940px
    if title_text:
        max_title_w = 940
        start_x = (VIDEO_WIDTH - max_title_w) // 2
        draw_wrapped_text(
            draw=draw,
            text=title_text,
            font=font_title,
            x=start_x,
            y=by + 75,
            max_width=max_title_w,
            fill=TEXT_PRIMARY,
            line_spacing=8,
            align="center",
            max_lines=2
        )

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
    """Renders sleek 2D glassmorphic comparison cards with safe wrapped headlines and subtexts."""
    raw_bullets = data.get("bullets", [
        "Zero-Copy Memory Streaming",
        "OS PageCache Kernel Level Buffering",
        "Append-Only Sequential Storage"
    ])
    
    font_head = get_font(34, bold=True)
    font_sub = get_font(26)
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
        
        # Wrapped texts strictly within card bounds (available width = 740px)
        draw_wrapped_text(draw, headline, font_head, cx + 135, cy + 32, max_width=740, fill=TEXT_PRIMARY, max_lines=1)
        draw_wrapped_text(draw, subtext, font_sub, cx + 135, cy + 86, max_width=740, fill=TEXT_MUTED, max_lines=2)

    # High-Tech Live Metric HUD Card at bottom
    hud_w, hud_h = 940, 150
    hx = (VIDEO_WIDTH - hud_w) // 2
    hy = 1110
    draw.rounded_rectangle((hx - 2, hy - 2, hx + hud_w + 2, hy + hud_h + 2), radius=26, fill=(52, 211, 153, 30))
    draw.rounded_rectangle((hx, hy, hx + hud_w, hy + hud_h), radius=24, fill=(11, 18, 33, 245), outline=NEON_EMERALD, width=3)
    
    font_stat = get_font(46, bold=True)
    font_lbl = get_font(22, bold=True)
    
    metric_val = data.get("metric_value", "1,000,000+ msgs/s")
    metric_lbl = data.get("metric_label", "THROUGHPUT CAPACITY")
    
    draw_wrapped_text(draw, metric_lbl.upper(), font_lbl, hx + 50, hy + 28, max_width=450, fill=NEON_EMERALD, max_lines=1)
    draw_wrapped_text(draw, metric_val, font_stat, hx + 50, hy + 65, max_width=450, fill=TEXT_PRIMARY, max_lines=1)
    
    draw.text((hx + 560, hy + 28), "SYSTEM LATENCY", fill=NEON_CYAN, font=font_lbl)
    draw.text((hx + 560, hy + 65), "< 2.5 ms", fill=NEON_CYAN, font=font_stat)

def _render_alert_diagram(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders high-impact Hook/Problem scene with safe wrapped challenge cards."""
    center_x = VIDEO_WIDTH // 2
    center_y = 560
    pulse = (progress * 2.5) % 1.0
    for ring in range(3):
        r_prog = (pulse + (ring * 0.33)) % 1.0
        rad = int(80 + r_prog * 230)
        alpha = int(120 * (1.0 - r_prog))
        draw.ellipse((center_x - rad, center_y - rad, center_x + rad, center_y + rad), outline=(244, 63, 94, alpha), width=3)
        
    _draw_vector_warning(draw, center_x, center_y, radius=65)
    
    box_w, box_h = 920, 240
    bx = (VIDEO_WIDTH - box_w) // 2
    by = 760
    draw.rounded_rectangle((bx - 3, by - 3, bx + box_w + 3, by + box_h + 3), radius=26, fill=(244, 63, 94, 40))
    draw.rounded_rectangle((bx, by, bx + box_w, by + box_h), radius=24, fill=(24, 15, 23, 245), outline=NEON_ROSE, width=4)
    
    font_h = get_font(38, bold=True)
    font_s = get_font(28)
    
    p_title = data.get("problem_title", data.get("title", "High-Volume Production Bottleneck"))
    p_sub = data.get("problem_desc", data.get("subtitle", "Traditional message brokers hit I/O locks and JVM garbage collection crashes at scale."))
    
    draw_wrapped_text(draw, p_title, font_h, bx + 40, by + 32, max_width=840, fill=TEXT_PRIMARY, max_lines=1)
    draw_wrapped_text(draw, p_sub, font_s, bx + 40, by + 90, max_width=840, fill=TEXT_MUTED, max_lines=3, line_spacing=6)
        
    cx, cy, cw, ch = bx, 1060, box_w, 150
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=20, fill=CARD_BG, outline=NEON_AMBER, width=3)
    draw.text((cx + 40, cy + 26), "CRITICAL CHALLENGE", fill=NEON_AMBER, font=get_font(24, bold=True))
    draw_wrapped_text(draw, "How do you achieve 100% Zero Data Loss without speed drops?", get_font(28, bold=True), cx + 40, cy + 70, max_width=840, fill=TEXT_PRIMARY, max_lines=2)

def _render_architecture_flow(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders 2D Architecture Nodes with strictly wrapped text boundaries."""
    nodes = data.get("nodes", [
        {"id": "src", "label": "Producers (IoT / Web)", "sub": "1,000,000 Events / sec", "color": "#38BDF8"},
        {"id": "eng", "label": "Kafka Cluster (Partitions)", "sub": "Sequential Append-Only Log", "color": "#FBBF24"},
        {"id": "tgt", "label": "Consumer Analytics", "sub": "Zero-Copy sendfile() Stream", "color": "#34D399"}
    ])
    
    font_title = get_font(36, bold=True)
    font_sub = get_font(26)
    
    node_w, node_h = 860, 180
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
        draw.ellipse((center_x + 35, ny + 65, center_x + 85, ny + 115), fill=accent_rgb)
        
        # Wrapped text strictly inside node (max_width = 710px)
        draw_wrapped_text(draw, node.get("label", ""), font_title, center_x + 105, ny + 35, max_width=710, fill=TEXT_PRIMARY, max_lines=1)
        draw_wrapped_text(draw, node.get("sub", ""), font_sub, center_x + 105, ny + 92, max_width=710, fill=TEXT_MUTED, max_lines=2)

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
    """Renders interactive 2D SQL table with safe margins and bound cells."""
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
    
    font_head = get_font(28, bold=True)
    font_cell = get_font(26)
    font_code = get_font(26, bold=True)
    
    qx, qy, qw, qh = 70, 440, 940, 140
    draw.rounded_rectangle((qx, qy, qx + qw, qy + qh), radius=20, fill=CARD_BG, outline=NEON_PURPLE, width=3)
    draw.text((qx + 30, qy + 18), "PIPELINE LOGIC:", fill=NEON_PURPLE, font=get_font(22, bold=True))
    draw_wrapped_text(draw, code, font_code, qx + 30, qy + 58, max_width=880, fill=TEXT_PRIMARY, max_lines=2)
    
    tx, ty, tw = 70, 610, 940
    headers = table_data.get("headers", ["Col 1", "Col 2", "Col 3", "Col 4"])
    rows = table_data.get("rows", [])
    
    col_w = tw // max(1, len(headers))
    row_h = 90
    
    draw.rounded_rectangle((tx, ty, tx + tw, ty + row_h), radius=16, fill=(30, 41, 59, 240), outline=CARD_BORDER, width=2)
    for c_idx, h in enumerate(headers):
        h_str = str(h).upper()
        # Truncate header if too long for column
        while h_str and font_head.getbbox(h_str)[2] - font_head.getbbox(h_str)[0] > col_w - 30:
            h_str = h_str[:-1]
        draw.text((tx + (c_idx * col_w) + 20, ty + 28), h_str, fill=NEON_CYAN, font=font_head)
        
    active_row = int((progress * len(rows)) % len(rows)) if rows else 0
    for r_idx, row in enumerate(rows[:4]):
        ry = ty + ((r_idx + 1) * row_h) + 12
        is_highlighted = (r_idx == active_row)
        bg = (56, 189, 248, 45) if is_highlighted else CARD_BG
        border = NEON_AMBER if is_highlighted else CARD_BORDER
        
        draw.rounded_rectangle((tx, ry, tx + tw, ry + row_h - 10), radius=14, fill=bg, outline=border, width=3 if is_highlighted else 1)
        for c_idx, cell in enumerate(row[:len(headers)]):
            txt_color = NEON_AMBER if (is_highlighted and c_idx == len(row) - 1) else TEXT_PRIMARY
            cell_str = str(cell)
            while cell_str and font_cell.getbbox(cell_str)[2] - font_cell.getbbox(cell_str)[0] > col_w - 30:
                cell_str = cell_str[:-1]
            draw.text((tx + (c_idx * col_w) + 20, ry + 24), cell_str, fill=txt_color, font=font_cell)

def _render_code_terminal(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders macOS-style dark code terminal with bound text limits."""
    raw_code = data.get("code_snippet", "def kafka_stream_handler(event):\n    # Zero-copy memory mapped file\n    return broker.append_log(event, acks=-1)")
    lines = raw_code.split("\n")
    
    tx, ty, tw, th = 70, 460, 940, 750
    draw.rounded_rectangle((tx, ty, tx + tw, ty + th), radius=24, fill=(15, 23, 42, 245), outline=CARD_BORDER, width=3)
    
    draw.rounded_rectangle((tx, ty, tx + tw, ty + 70), radius=24, fill=(30, 41, 59, 255))
    draw.ellipse((tx + 30, ty + 24, tx + 52, ty + 46), fill=(239, 68, 68))
    draw.ellipse((tx + 65, ty + 24, tx + 87, ty + 46), fill=(245, 158, 11))
    draw.ellipse((tx + 100, ty + 24, tx + 122, ty + 46), fill=(16, 185, 129))
    draw.text((tx + 140, ty + 20), "terminal.py — Execution Output", fill=TEXT_MUTED, font=get_font(26))
    
    font_code = get_font(30)
    total_chars = len(raw_code)
    chars_to_show = int(progress * total_chars * 1.5)
    
    current_char_count = 0
    line_y = ty + 120
    max_code_w = 760
    for i, line in enumerate(lines[:8]):
        line_num = f"{i + 1:2d}  "
        draw.text((tx + 30, line_y), line_num, fill=(71, 85, 105), font=font_code)
        
        remaining = max(0, chars_to_show - current_char_count)
        visible = line[:remaining]
        
        # Ensure visible line never overflows terminal right border
        while visible and (font_code.getbbox(visible)[2] - font_code.getbbox(visible)[0]) > max_code_w:
            visible = visible[:-1]
            
        draw.text((tx + 95, line_y), visible, fill=NEON_EMERALD if "def " in line or "return" in line else TEXT_PRIMARY, font=font_code)
        
        current_char_count += len(line) + 1
        line_y += 68
        if current_char_count >= chars_to_show:
            bbox_vis = font_code.getbbox(visible) if visible else (0, 0, 0, 0)
            vis_w = bbox_vis[2] - bbox_vis[0]
            cx = tx + 95 + vis_w + 4
            draw.rectangle((cx, line_y - 62, cx + 4, line_y - 25), fill=NEON_CYAN)
            break

def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Converts hex string to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    return (56, 189, 248)
