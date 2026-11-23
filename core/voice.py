import asyncio
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import edge_tts
from groq import Groq
from core.config import GROQ_API_KEY, OUTPUT_DIR

# Recommended natural voices for tech reels
DEFAULT_VOICE = "en-US-ChristopherNeural"  # Authoritative, calm, clear tech narrator
# Alternative options:
# "en-US-GuyNeural" - Conversational American
# "en-IN-PrabhatNeural" - Crisp Indian English tech accent
# "en-US-JennyNeural" - Engaging Female tech narrator

async def _synthesize_edge_tts(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> None:
    """Uses Edge-TTS to synthesize human-like voice with natural pacing."""
    # Pre-clean pauses & technical punctuation for natural narration
    cleaned_text = text.replace("...", ", ")
    cleaned_text = cleaned_text.replace("`", "").replace("*", "")
    # Replace technical underscores with spaces (e.g. DENSE_RANK -> DENSE RANK)
    cleaned_text = re.sub(r'(?<=\w)_(?=\w)', ' ', cleaned_text)
    communicate = edge_tts.Communicate(cleaned_text, voice, rate="+8%", pitch="+0Hz")
    await communicate.save(str(output_path))

def generate_voiceover(scenes: List[Dict[str, Any]], voice: str = DEFAULT_VOICE) -> Tuple[Path, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Synthesizes the entire reel narration into a single audio file and computes
    microsecond word-level timestamps via Groq Whisper.
    
    Returns:
        (audio_file_path, word_timestamps, scenes_with_timestamps)
    """
    combined_script = []
    scene_markers = []
    current_char_count = 0

    for idx, sc in enumerate(scenes):
        narration = sc.get("narration", "").strip()
        combined_script.append(narration)
        start_char = current_char_count
        end_char = start_char + len(narration)
        scene_markers.append({
            "scene_id": sc.get("scene_id", idx + 1),
            "start_char": start_char,
            "end_char": end_char,
            "narration": narration
        })
        current_char_count = end_char + 1  # accounting for space

    full_narration_text = " ".join(combined_script)
    audio_path = OUTPUT_DIR / "reel_voiceover.mp3"
    
    # 1. Generate Voice Audio via edge-tts
    asyncio.run(_synthesize_edge_tts(full_narration_text, audio_path, voice=voice))
    
    # 2. Extract Word Timestamps via Groq Whisper
    word_timestamps = _extract_word_timestamps(audio_path)
    
    # 3. Align scenes to exact audio timestamps
    scenes_with_timestamps = _align_scenes_with_audio(scenes, word_timestamps)
    
    return audio_path, word_timestamps, scenes_with_timestamps

def _extract_word_timestamps(audio_path: Path) -> List[Dict[str, Any]]:
    """Calls Groq Whisper Large v3 to get exact word-level start & end timestamps."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required for word timestamp alignment.")
    
    client = Groq(api_key=GROQ_API_KEY)
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path.name, file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    
    words = []
    # Groq returns words in transcription.words
    if hasattr(transcription, "words") and transcription.words:
        for w in transcription.words:
            # handle dict or object
            if isinstance(w, dict):
                words.append({"word": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])})
            else:
                words.append({"word": getattr(w, "word", "").strip(), "start": float(getattr(w, "start", 0)), "end": float(getattr(w, "end", 0))})
    return words

def _align_scenes_with_audio(scenes: List[Dict[str, Any]], word_timestamps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Splits word timestamps across scenes to give each scene its exact start and end seconds."""
    if not word_timestamps:
        # Fallback approximation if no words
        cur = 0.0
        out = []
        for s in scenes:
            dur = max(6.0, len(s.get("narration", "").split()) * 0.4)
            s_copy = dict(s)
            s_copy["start_time"] = cur
            s_copy["end_time"] = cur + dur
            s_copy["duration"] = dur
            out.append(s_copy)
            cur += dur
        return out

    total_words = len(word_timestamps)
    total_audio_duration = word_timestamps[-1]["end"]
    
    # Calculate word count proportion per scene
    scene_word_counts = [len(s.get("narration", "").split()) for s in scenes]
    sum_words = sum(scene_word_counts) or 1
    
    out_scenes = []
    current_word_idx = 0
    for i, s in enumerate(scenes):
        w_count = scene_word_counts[i]
        target_end_idx = min(total_words, current_word_idx + w_count)
        
        # Determine start time
        if current_word_idx < total_words:
            s_start = word_timestamps[current_word_idx]["start"]
        else:
            s_start = total_audio_duration
            
        # Determine end time
        if i == len(scenes) - 1:
            s_end = total_audio_duration
        else:
            if target_end_idx - 1 < total_words:
                s_end = word_timestamps[target_end_idx - 1]["end"]
            else:
                s_end = total_audio_duration
                
        s_copy = dict(s)
        s_copy["start_time"] = round(s_start, 2)
        s_copy["end_time"] = round(s_end, 2)
        s_copy["duration"] = round(s_end - s_start, 2)
        out_scenes.append(s_copy)
        current_word_idx = target_end_idx

    return out_scenes
