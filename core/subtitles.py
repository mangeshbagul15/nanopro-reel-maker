from pathlib import Path
from typing import List, Dict, Any
from core.config import OUTPUT_DIR

def generate_ass_subtitles(word_timestamps: List[Dict[str, Any]], output_path: Path = None) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file with viral
    TikTok / Instagram Reels style:
    - Bold uppercase typography
    - Active spoken word highlighted in bright glowing yellow (#00E6FF / #00FFFF or #00FFFF)
    - High contrast black outline and shadow
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "subtitles.ass"

    # ASS Header & Styles
    ass_content = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: ReelHighlight,Arial,76,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,2,60,60,340,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    # Group words into fast-paced punchy 2-3 word chunks (Viral Shorts retention)
    CHUNK_SIZE = 2
    for i in range(0, len(word_timestamps), CHUNK_SIZE):
        chunk = word_timestamps[i:i + CHUNK_SIZE]
        if not chunk:
            continue

        chunk_start = chunk[0]["start"]
        chunk_end = chunk[-1]["end"]

        # For each word in the chunk, generate a micro-event highlighting that word
        for w_idx, current_word in enumerate(chunk):
            w_start = current_word["start"]
            w_end = current_word["end"]

            # Construct the line: words before, active highlighted word, words after
            line_parts = []
            for j, w in enumerate(chunk):
                raw_word = w["word"].upper().strip()
                if j == w_idx:
                    # Highlight color (Yellow: &H002BF6FF& or Cyan &H00FFE600&)
                    line_parts.append(r"{\c&H002BF6FF&\fscx110\fscy110}" + raw_word + r"{\r}")
                else:
                    line_parts.append(r"{\c&H00FFFFFF&}" + raw_word)

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
