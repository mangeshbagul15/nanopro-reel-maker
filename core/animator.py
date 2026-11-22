import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, OUTPUT_DIR, FONTS_DIR

# Design System Colors (Modern Cyber-Tech Dark Mode)
BG_COLOR = (13, 17, 23)          # Deep Github Dark
CARD_BG = (22, 27, 34, 220)       # Glassmorphism Slate
CARD_BORDER = (48, 54, 61, 255)   # Subtle Border
ACCENT_BLUE = (56, 189, 248)      # Cyan / Cloud
ACCENT_GREEN = (52, 211, 153)     # Emerald / Target
ACCENT_AMBER = (251, 191, 36)     # Amber / Engine
ACCENT_RED = (248, 113, 113)      # Alert Red
ACCENT_PURPLE = (168, 85, 247)    # Modern Violet
TEXT_PRIMARY = (240, 246, 252)    # Crisp White
TEXT_MUTED = (139, 148, 158)      # Slate Gray

def get_font(size: int = 40, bold: bool = False) -> ImageFont.ImageFont:
    """Returns a clean Truetype font or default PIL font."""
    font_names = ["Arial.ttf", "arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
    if bold:
        font_names = ["arialbd.ttf", "Arial_Bold.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"] + font_names
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def render_scene_frames(scene: Dict[str, Any], scene_idx: int) -> List[Path]:
    """
    Renders high-quality 2D frames for a single scene across its duration.
    Returns list of saved frame image paths.
    """
    duration = max(2.0, float(scene.get("duration", 5.0)))
    total_frames = int(duration * VIDEO_FPS)
    
    scene_frames_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    scene_frames_dir.mkdir(parents=True, exist_ok=True)
    
    visual_type = scene.get("visual_type", "concept_cards")
    visual_data = scene.get("visual_data", {})
    
    frame_paths = []
    
    # Pre-render background base to optimize performance
    base_canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
    _draw_background_grid(base_canvas)
    
    for f in range(total_frames):
        progress = f / max(1, total_frames - 1)  # 0.0 to 1.0
        frame = base_canvas.copy()
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # Render Topic Header Badge
        _draw_header(draw, visual_data.get("badge", "TECH INSIGHT"), visual_data.get("title", ""))
        
        # Dispatch to 2D scene renderer
        if visual_type == "architecture_flow":
            _render_architecture_flow(draw, visual_data, progress)
        elif visual_type == "sql_table":
            _render_sql_table(draw, visual_data, progress)
        elif visual_type == "code_terminal":
            _render_code_terminal(draw, visual_data, progress)
        else:
            _render_concept_cards(draw, visual_data, progress)
            
        frame_file = scene_frames_dir / f"frame_{f:04d}.png"
        frame.convert("RGB").save(frame_file)
        frame_paths.append(frame_file)
        
    return frame_paths

def _draw_background_grid(img: Image.Image) -> None:
    """Draws subtle modern dot-grid / cyber pattern."""
    draw = ImageDraw.Draw(img, "RGBA")
    dot_color = (30, 41, 59, 120)
    spacing = 80
    for x in range(40, VIDEO_WIDTH, spacing):
        for y in range(40, VIDEO_HEIGHT, spacing):
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=dot_color)

def _draw_header(draw: ImageDraw.Draw, badge_text: str, title_text: str) -> None:
    """Draws top branded header badge and dynamic title."""
    font_badge = get_font(32, bold=True)
    font_title = get_font(56, bold=True)
    
    # Pill Badge
    badge_str = badge_text.upper()
    bbox = font_badge.getbbox(badge_str)
    bw = bbox[2] - bbox[0] + 40
    bh = 54
    bx = (VIDEO_WIDTH - bw) // 2
    by = 180
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=27, fill=(30, 58, 138, 200), outline=ACCENT_BLUE, width=3)
    draw.text((bx + 20, by + 10), badge_str, fill=ACCENT_BLUE, font=font_badge)
    
    # Main Scene Title
    if title_text:
        title_bbox = font_title.getbbox(title_text)
        tw = title_bbox[2] - title_bbox[0]
        tx = max(60, (VIDEO_WIDTH - tw) // 2)
        draw.text((tx, by + 80), title_text, fill=TEXT_PRIMARY, font=font_title)

def _render_architecture_flow(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders 2D Architecture Nodes with animated data flow stream."""
    nodes = data.get("nodes", [
        {"id": "src", "label": "Source DB", "sub": "Oracle / Postgres", "color": "#EF4444"},
        {"id": "eng", "label": "DMS Replication", "sub": "CDC Engine", "color": "#F59E0B"},
        {"id": "tgt", "label": "Target Cloud", "sub": "AWS Aurora / S3", "color": "#10B981"}
    ])
    
    font_title = get_font(42, bold=True)
    font_sub = get_font(30)
    
    node_w, node_h = 760, 190
    center_x = (VIDEO_WIDTH - node_w) // 2
    start_y = 520
    gap = 260
    
    node_coords = []
    for i, node in enumerate(nodes[:3]):
        ny = start_y + (i * gap)
        node_coords.append((center_x + node_w // 2, ny + node_h // 2))
        
        # Animated entrance
        card_scale = min(1.0, progress * 3.0 - (i * 0.3))
        if card_scale <= 0:
            continue
            
        color_hex = node.get("color", "#38BDF8")
        outline_rgb = _hex_to_rgb(color_hex)
        
        # Glassmorphic Box
        draw.rounded_rectangle(
            (center_x, ny, center_x + node_w, ny + node_h),
            radius=24,
            fill=CARD_BG,
            outline=outline_rgb,
            width=4
        )
        
        # Color Indicator Light
        draw.ellipse((center_x + 40, ny + 75, center_x + 75, ny + 110), fill=outline_rgb)
        
        # Texts
        draw.text((center_x + 100, ny + 45), node.get("label", ""), fill=TEXT_PRIMARY, font=font_title)
        draw.text((center_x + 100, ny + 105), node.get("sub", ""), fill=TEXT_MUTED, font=font_sub)

    # Connecting Conduit Lines & Animated Moving Particles
    for i in range(len(node_coords) - 1):
        x1, y1 = node_coords[i]
        x2, y2 = node_coords[i + 1]
        
        # Draw background pipe
        draw.line((x1, y1 + node_h // 2, x2, y2 - node_h // 2), fill=CARD_BORDER, width=8)
        
        # Animated Data Particles flowing down
        particle_t = (progress * 4.0 + (i * 0.5)) % 1.0
        py = (y1 + node_h // 2) + particle_t * ((y2 - node_h // 2) - (y1 + node_h // 2))
        draw.ellipse((x1 - 10, py - 10, x1 + 10, py + 10), fill=ACCENT_BLUE)

def _render_sql_table(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders interactive 2D SQL table with animated row highlighting."""
    table_data = data.get("table_data", {
        "headers": ["id", "employee", "salary", "rank"],
        "rows": [
            ["101", "Alice", "$130,000", "1"],
            ["102", "Bob", "$130,000", "1"],
            ["103", "Charlie", "$95,000", "2"],
            ["104", "David", "$80,000", "3"]
        ]
    })
    code = data.get("code_snippet", "DENSE_RANK() OVER (ORDER BY salary DESC)")
    
    font_head = get_font(34, bold=True)
    font_cell = get_font(32)
    font_code = get_font(30, bold=True)
    
    # 1. SQL Query Display Box
    qx, qy, qw, qh = 80, 480, 920, 160
    draw.rounded_rectangle((qx, qy, qx + qw, qy + qh), radius=20, fill=CARD_BG, outline=ACCENT_PURPLE, width=3)
    draw.text((qx + 30, qy + 20), "SQL QUERY:", fill=ACCENT_PURPLE, font=get_font(24, bold=True))
    draw.text((qx + 30, qy + 65), code, fill=TEXT_PRIMARY, font=font_code)
    
    # 2. Table Container
    tx, ty, tw = 80, 690, 920
    headers = table_data.get("headers", ["Col 1", "Col 2", "Col 3", "Col 4"])
    rows = table_data.get("rows", [])
    
    col_w = tw // len(headers)
    row_h = 100
    
    # Table Header Row
    draw.rounded_rectangle((tx, ty, tx + tw, ty + row_h), radius=16, fill=(30, 41, 59, 240), outline=CARD_BORDER, width=2)
    for c_idx, h in enumerate(headers):
        draw.text((tx + (c_idx * col_w) + 25, ty + 30), str(h).upper(), fill=ACCENT_BLUE, font=font_head)
        
    # Table Data Rows
    active_row = int((progress * len(rows)) % len(rows))
    for r_idx, row in enumerate(rows):
        ry = ty + ((r_idx + 1) * row_h) + 15
        is_highlighted = (r_idx == active_row)
        bg = (56, 189, 248, 40) if is_highlighted else CARD_BG
        border = ACCENT_AMBER if is_highlighted else CARD_BORDER
        
        draw.rounded_rectangle((tx, ry, tx + tw, ry + row_h - 10), radius=14, fill=bg, outline=border, width=3 if is_highlighted else 1)
        
        for c_idx, cell in enumerate(row):
            txt_color = ACCENT_AMBER if (is_highlighted and c_idx == len(row) - 1) else TEXT_PRIMARY
            draw.text((tx + (c_idx * col_w) + 25, ry + 25), str(cell), fill=txt_color, font=font_cell)

def _render_code_terminal(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders macOS-style dark code terminal with dynamic typing effect."""
    raw_code = data.get("code_snippet", "def optimize_pipeline(df):\n    # Vectorized execution\n    return df.groupby('dept').sum()")
    lines = raw_code.split("\n")
    
    tx, ty, tw, th = 80, 500, 920, 800
    
    # Terminal Window Box
    draw.rounded_rectangle((tx, ty, tx + tw, ty + th), radius=24, fill=(15, 23, 42, 240), outline=CARD_BORDER, width=3)
    
    # Title Bar
    draw.rounded_rectangle((tx, ty, tx + tw, ty + 70), radius=24, fill=(30, 41, 59, 255))
    # 3 colored window dots
    draw.ellipse((tx + 30, ty + 24, tx + 52, ty + 46), fill=(239, 68, 68))
    draw.ellipse((tx + 65, ty + 24, tx + 87, ty + 46), fill=(245, 158, 11))
    draw.ellipse((tx + 100, ty + 24, tx + 122, ty + 46), fill=(16, 185, 129))
    draw.text((tx + 150, ty + 20), "main.py — Python Engine", fill=TEXT_MUTED, font=get_font(26))
    
    # Code Lines Typing Animation
    font_code = get_font(34)
    total_chars = len(raw_code)
    chars_to_show = int(progress * total_chars * 1.5)  # finishes typing halfway
    
    current_char_count = 0
    line_y = ty + 120
    for i, line in enumerate(lines):
        line_num = f"{i + 1:2d}  "
        draw.text((tx + 30, line_y), line_num, fill=(71, 85, 105), font=font_code)
        
        remaining_budget = max(0, chars_to_show - current_char_count)
        visible_text = line[:remaining_budget]
        
        draw.text((tx + 100, line_y), visible_text, fill=ACCENT_GREEN if "def " in line or "return" in line else TEXT_PRIMARY, font=font_code)
        
        current_char_count += len(line) + 1
        line_y += 75
        if current_char_count >= chars_to_show:
            # Draw blinking cursor
            cx = tx + 100 + len(visible_text) * 20
            draw.rectangle((cx, line_y - 70, cx + 4, line_y - 30), fill=ACCENT_BLUE)
            break

def _render_concept_cards(draw: ImageDraw.Draw, data: Dict[str, Any], progress: float) -> None:
    """Renders sleek 2D comparison bullet cards and key takeaways."""
    bullets = data.get("bullets", [
        "Zero Downtime Data Replication",
        "CDC (Change Data Capture) Engine",
        "Cross-Engine Cloud Compatibility"
    ])
    
    font_bullet = get_font(38, bold=True)
    card_w = 920
    card_h = 170
    start_y = 520
    gap = 220
    
    for i, bullet in enumerate(bullets[:4]):
        cy = start_y + (i * gap)
        cx = (VIDEO_WIDTH - card_w) // 2
        
        # Staggered card emergence
        card_progress = min(1.0, max(0.0, (progress * 3.5) - (i * 0.4)))
        if card_progress <= 0:
            continue
            
        draw.rounded_rectangle(
            (cx, cy, cx + card_w, cy + card_h),
            radius=20,
            fill=CARD_BG,
            outline=ACCENT_BLUE if i == 0 else CARD_BORDER,
            width=3 if i == 0 else 2
        )
        
        # Bullet Checkmark Badge
        draw.ellipse((cx + 35, cy + 50, cx + 105, cy + 120), fill=(16, 185, 129, 60), outline=ACCENT_GREEN, width=3)
        draw.text((cx + 56, cy + 56), "✓", fill=ACCENT_GREEN, font=get_font(42, bold=True))
        
        # Bullet Text
        draw.text((cx + 130, cy + 60), bullet, fill=TEXT_PRIMARY, font=font_bullet)

def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Converts hex string to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    return (56, 189, 248)
