from pathlib import Path
from typing import List, Dict, Any
from core.config import OUTPUT_DIR

def generate_ass_subtitles(
    word_timestamps: List[Dict[str, Any]],
    output_path: Path = None,
    format_ratio: str = "9:16",
    tone: str = "auto_dynamic",
    aligned_scenes: List[Dict[str, Any]] = None,
    art_style: str = "editorial_dark"
) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file with viral
    TikTok / Instagram Reels style synchronized to aspect ratio, visual art_style AND script tone:
    - Dynamic highlight colors & kinetic pop matched to chosen/per-scene tone
    - High-contrast opaque pill backing when art_style == 'light_whiteboard'
    - Safe-zone positioning adapted to aspect ratio (9:16, 16:9, 1:1)
    - Devanagari (Hindi/Marathi) + English technical terms cleanly rendered
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "subtitles.ass"

    if format_ratio == "16:9":
        res_x, res_y = 1920, 1080
        font_size = 52
        margin_v = 110
    elif format_ratio == "1:1":
        res_x, res_y = 1080, 1080
        font_size = 54
        margin_v = 150
    else:  # 9:16
        res_x, res_y = 1080, 1920
        font_size = 62
        margin_v = 420

    # Light-mode canvas needs solid dark pill / heavier outline so white+yellow karaoke text pops cleanly
    is_light_canvas = (str(art_style).lower().strip() in ("light_whiteboard", "studio_white"))
    border_style = 3 if is_light_canvas else 1
    outline_px = 12 if is_light_canvas else 5
    back_col = "&HC80F172A" if is_light_canvas else "&H90000000"

    # ASS Header & Styles - strictly constrained to chosen aspect ratio safe frame
    ass_content = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {res_x}",
        f"PlayResY: {res_y}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: ReelHighlight,Nirmala UI,{font_size},&H00FFFFFF,&H0000FFFF,&H000F172A,{back_col},-1,0,0,0,100,100,1,0,{border_style},{outline_px},2,2,80,80,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    # Filter out standalone punctuation tokens (e.g. ",", ".", "!") before chunking
    filtered_words = []
    for w in word_timestamps:
        raw = w.get("word", "").strip()
        cleaned = "".join(ch for ch in raw if ch.isalnum())
        if cleaned:
            filtered_words.append(w)

    # Intelligent chunking: 1 word for long tech words (>= 8 chars), 2 words for short words
    i = 0
    chunks = []
    while i < len(filtered_words):
        current = filtered_words[i]
        curr_text = current.get("word", "").strip()
        
        # If long word, give it its own chunk to guarantee 0 overflow
        if len(curr_text) >= 8:
            chunks.append([current])
            i += 1
        elif i + 1 < len(filtered_words):
            next_w = filtered_words[i + 1]
            next_text = next_w.get("word", "").strip()
            # If combined length would be too wide, keep separate
            if len(curr_text) + len(next_text) > 13:
                chunks.append([current])
                i += 1
            else:
                chunks.append([current, next_w])
                i += 2
        else:
            chunks.append([current])
            i += 1

    # Highlight color (ASS BGR hex) & kinetic pop scale per tone
    tone_styles = {
        "senior_hinglish_mentor": (r"\c&H00F8BD38&\fscx110\fscy110", "mentor_cyan_emphasis"),
        "youth_friend_turbo": (r"\c&H002BF6FF&\fscx116\fscy116", "turbo_youth_pop"),
        "mentor_storyteller": (r"\c&H0099D334&\fscx112\fscy112", "mentor_emerald"),
        "fireship_octane": (r"\c&H002BF6FF&\fscx114\fscy114", "electric_yellow"),
        "dramatic_performance": (r"\c&H0024BFFF&\fscx108\fscy108", "amber_drama"),
        "staff_engineer": (r"\c&H00F8BD38&\fscx105\fscy105", "cyber_cyan"),
        "interview_prep": (r"\c&H0099D334&\fscx110\fscy110", "emerald_pop"),
        "conversational_casual": (r"\c&H002BF6FF&\fscx106\fscy106", "warm_yellow"),
    }

    def _tone_for_time(t_sec: float) -> str:
        if tone != "auto_dynamic":
            return tone
        if aligned_scenes:
            for sc in aligned_scenes:
                st_t = float(sc.get("start_time", 0.0))
                en_t = float(sc.get("end_time", 9999.0))
                if st_t <= t_sec <= en_t:
                    return sc.get("scene_tone", "conversational_casual")
        return "fireship_octane"

    for chunk in chunks:
        if not chunk:
            continue

        # For each word in the chunk, generate a micro-event highlighting that word
        for w_idx, current_word in enumerate(chunk):
            w_start = current_word["start"]
            w_end = current_word["end"]
            active_tone = _tone_for_time(w_start)
            hl_tag = tone_styles.get(active_tone, tone_styles["fireship_octane"])[0]

            line_parts = []
            for j, w in enumerate(chunk):
                # Strip unsupported emojis/glyphs while preserving ASCII + Devanagari (Hindi/Marathi)
                clean_w = w["word"].upper().strip()
                clean_w = clean_w.replace("—", "-").replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')
                clean_w = "".join(ch for ch in clean_w if (32 <= ord(ch) <= 126) or (0x0900 <= ord(ch) <= 0x097F))
                if not clean_w:
                    continue
                if j == w_idx:
                    line_parts.append("{" + hl_tag + "}" + clean_w + r"{\r}")
                else:
                    line_parts.append(r"{\c&H00FFFFFF&}" + clean_w)

            if not line_parts:
                continue
            dialogue_text = " ".join(line_parts)
            ass_content.append(
                f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},ReelHighlight,,0,0,0,,{dialogue_text}"
            )

    output_path.write_text("\n".join(ass_content), encoding="utf-8-sig")
    return output_path

def _format_ass_time(seconds: float) -> str:
    """Formats seconds to ASS time format: H:MM:SS.CC"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"
