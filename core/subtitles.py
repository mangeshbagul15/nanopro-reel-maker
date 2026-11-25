from pathlib import Path
from typing import List, Dict, Any
from core.config import OUTPUT_DIR

def generate_ass_subtitles(
    word_timestamps: List[Dict[str, Any]],
    output_path: Path = None,
    format_ratio: str = "9:16"
) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file with viral
    TikTok / Instagram Reels style:
    - Safe-zone positioning adapted to aspect ratio (9:16, 16:9, 1:1) so text never touches bottom UI or middle cards
    - Fontsize dynamically scaled with clean margins so words never go out of frame
    - Intelligent 1-2 word chunking for long technical words
    - Active spoken word highlighted in bright glowing cyan/yellow with contrast outline
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
        f"Style: ReelHighlight,Segoe UI,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,5,2,2,80,80,{margin_v},1",
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

    for chunk in chunks:
        if not chunk:
            continue

        # For each word in the chunk, generate a micro-event highlighting that word
        for w_idx, current_word in enumerate(chunk):
            w_start = current_word["start"]
            w_end = current_word["end"]

            line_parts = []
            for j, w in enumerate(chunk):
                # Strip unsupported emojis/glyphs that render as tofu boxes (▯) in libass
                clean_w = w["word"].upper().strip()
                clean_w = clean_w.replace("—", "-").replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')
                clean_w = "".join(ch for ch in clean_w if 32 <= ord(ch) <= 126)
                if not clean_w:
                    continue
                if j == w_idx:
                    # Highlight color (Glowing Neon Cyan: &H002BF6FF&) with 106% gentle pop
                    line_parts.append(r"{\c&H002BF6FF&\fscx106\fscy106}" + clean_w + r"{\r}")
                else:
                    line_parts.append(r"{\c&H00FFFFFF&}" + clean_w)

            if not line_parts:
                continue
            dialogue_text = " ".join(line_parts)
            ass_content.append(
                f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},ReelHighlight,,0,0,0,,{dialogue_text}"
            )

    output_path.write_text("\n".join(ass_content), encoding="utf-8")
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
