import asyncio
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import edge_tts
from groq import Groq
from core.config import GROQ_API_KEY, OUTPUT_DIR, FFMPEG_EXE

DEFAULT_VOICE = "en-US-ChristopherNeural"

def get_audio_duration(file_path: Path) -> float:
    """Extracts exact duration of an audio file using FFmpeg."""
    try:
        cmd = [str(FFMPEG_EXE), "-i", str(file_path.resolve())]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        print(f"[Voice] Error getting audio duration for {file_path}: {e}")
    return 0.0

async def _synthesize_scene_tts(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> None:
    """Uses Edge-TTS to synthesize speech for a single scene with natural pacing."""
    cleaned_text = text.replace("...", ", ")
    cleaned_text = cleaned_text.replace("`", "").replace("*", "")
    # Replace technical underscores with spaces (e.g. DENSE_RANK -> DENSE RANK)
    cleaned_text = re.sub(r'(?<=\w)_(?=\w)', ' ', cleaned_text)
    communicate = edge_tts.Communicate(cleaned_text, voice, rate="+7%", pitch="+0Hz")
    await communicate.save(str(output_path))

async def _synthesize_all_scenes_parallel(scene_texts: List[str], scene_paths: List[Path], voice: str) -> None:
    """Synthesizes all scene narration audios concurrently."""
    tasks = [
        _synthesize_scene_tts(text, path, voice=voice)
        for text, path in zip(scene_texts, scene_paths)
    ]
    await asyncio.gather(*tasks)

def generate_voiceover(
    scenes: List[Dict[str, Any]],
    voice: str = DEFAULT_VOICE
) -> Tuple[Path, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Synthesizes each scene's voiceover individually to guarantee 100% exact timing
    match between spoken narration and on-screen visuals.
    
    Returns:
        (audio_file_path, word_timestamps, scenes_with_exact_timestamps)
    """
    scene_audio_paths = []
    scene_texts = []
    
    for i, sc in enumerate(scenes):
        sc_text = sc.get("narration", "").strip()
        if not sc_text:
            sc_text = sc.get("visual_data", {}).get("title", f"Scene {i + 1}")
        scene_texts.append(sc_text)
        sc_path = OUTPUT_DIR / f"scene_{i + 1:02d}_voice.mp3"
        scene_audio_paths.append(sc_path)

    # 1. Synthesize all scene voiceovers in parallel
    asyncio.run(_synthesize_all_scenes_parallel(scene_texts, scene_audio_paths, voice=voice))

    # 2. Measure exact duration of each scene's audio
    scene_durations = [max(1.5, get_audio_duration(p)) for p in scene_audio_paths]

    # 3. Concatenate scene audios into full reel voiceover via FFmpeg
    final_audio_path = OUTPUT_DIR / "reel_voiceover.mp3"
    concat_cmd = [str(FFMPEG_EXE), "-y"]
    for p in scene_audio_paths:
        concat_cmd.extend(["-i", str(p.resolve())])
    filter_expr = "".join(f"[{i}:a]" for i in range(len(scene_audio_paths))) + f"concat=n={len(scene_audio_paths)}:v=0:a=1[a]"
    concat_cmd.extend(["-filter_complex", filter_expr, "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", str(final_audio_path.resolve())])
    
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    total_audio_duration = get_audio_duration(final_audio_path)
    if total_audio_duration <= 0:
        total_audio_duration = sum(scene_durations)

    # 4. Compute exact scene timestamps
    scenes_with_timestamps = []
    cur_time = 0.0
    for i, sc in enumerate(scenes):
        dur = scene_durations[i]
        s_start = cur_time
        s_end = cur_time + dur
        
        # Ensure the last scene aligns exactly with total audio
        if i == len(scenes) - 1:
            s_end = max(s_end, total_audio_duration)
            dur = s_end - s_start
            
        s_copy = dict(sc)
        s_copy["start_time"] = round(s_start, 3)
        s_copy["end_time"] = round(s_end, 3)
        s_copy["duration"] = round(dur, 3)
        scenes_with_timestamps.append(s_copy)
        cur_time = s_end

    # 5. Extract Word Timestamps via Groq Whisper for karaoke subtitles
    word_timestamps = []
    try:
        word_timestamps = _extract_word_timestamps(final_audio_path)
    except Exception as e:
        print(f"[Voice] Groq Whisper extraction error ({e}), generating robust fallback timestamps...")
        word_timestamps = _generate_fallback_word_timestamps(scenes_with_timestamps)

    # Cleanup individual scene MP3 files
    for p in scene_audio_paths:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    return final_audio_path, word_timestamps, scenes_with_timestamps

def _extract_word_timestamps(audio_path: Path) -> List[Dict[str, Any]]:
    """Calls Groq Whisper Large v3 to get microsecond word-level timestamps."""
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
    if hasattr(transcription, "words") and transcription.words:
        for w in transcription.words:
            if isinstance(w, dict):
                words.append({
                    "word": str(w.get("word", "")).strip(),
                    "start": round(float(w.get("start", 0)), 3),
                    "end": round(float(w.get("end", 0)), 3)
                })
            else:
                words.append({
                    "word": str(getattr(w, "word", "")).strip(),
                    "start": round(float(getattr(w, "start", 0)), 3),
                    "end": round(float(getattr(w, "end", 0)), 3)
                })
    return [w for w in words if w["word"]]

def _generate_fallback_word_timestamps(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fallback word timing generator that guarantees words match their exact scene
    boundaries if Groq API is temporarily unreachable.
    """
    all_words = []
    for sc in scenes:
        narration = sc.get("narration", "").strip()
        words = narration.split()
        if not words:
            continue
        sc_start = sc.get("start_time", 0.0)
        sc_dur = sc.get("duration", 5.0)
        time_per_word = sc_dur / max(1, len(words))
        
        for idx, w in enumerate(words):
            w_start = sc_start + (idx * time_per_word)
            w_end = w_start + (time_per_word * 0.95)
            all_words.append({
                "word": w.strip(),
                "start": round(w_start, 3),
                "end": round(w_end, 3)
            })
    return all_words
