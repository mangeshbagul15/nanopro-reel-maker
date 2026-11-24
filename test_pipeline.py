import time
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.director import generate_timeline
from core.voice import generate_voiceover
from core.animator import render_scene_frames
from core.subtitles import generate_ass_subtitles
from core.renderer import render_final_reel
from core.config import OUTPUT_DIR

def run_smoke_test():
    print("=== STARTING SMOKE TEST FOR NANOPRO REEL MAKER ===")
    
    # 1. Test Director with Hindi/Hinglish Voice Persona, sql_deepdive Engine, and 9:16 Format
    topic = "SQL DENSE_RANK vs RANK with duplicate salaries"
    voice = "hi-IN-MadhurNeural"
    engine_style = "sql_deepdive"
    duration_mode = "short"
    format_ratio = "9:16"
    print(f"\n[1/5] Calling Director for topic: '{topic}' (Engine: {engine_style}, Voice: {voice}, Format: {format_ratio})...")
    timeline = generate_timeline(
        topic=topic,
        engine_style=engine_style,
        duration_mode=duration_mode,
        voice=voice,
        format_ratio=format_ratio
    )
    print(f"Title: {timeline.get('title')}")
    print(f"Meta Director: {timeline.get('meta_director')}")
    scenes = timeline.get("scenes", [])
    print(f"Generated {len(scenes)} scenes.")
    assert len(scenes) > 0, "No scenes generated!"

    # 2. Test Voice & Whisper with Hindi/Hinglish TTS
    print(f"\n[2/5] Synthesizing Voice ({voice}) & Extracting Whisper Timestamps...")
    audio_path, word_timestamps, aligned_scenes = generate_voiceover(scenes, voice=voice)
    print(f"Audio Path: {audio_path} (exists: {audio_path.exists()})")
    print(f"Total Spoken Words Extracted: {len(word_timestamps)}")
    assert len(word_timestamps) > 0, "No word timestamps returned!"

    # 3. Test 2D Animator (30 FPS, Sharp Quality)
    print(f"\n[3/5] Rendering 2D Dynamic Visual Frames (Format: {format_ratio})...")
    all_scene_frame_dirs = []
    for i, sc in enumerate(aligned_scenes):
        print(f"  Rendering Scene {i+1}: {sc.get('visual_type')} ({sc.get('duration')}s)...")
        render_scene_frames(
            sc,
            i + 1,
            total_scenes=len(aligned_scenes),
            engine_style=engine_style,
            format_ratio=format_ratio
        )
        all_scene_frame_dirs.append(OUTPUT_DIR / f"scene_{i+1:02d}_frames")

    # 4. Test Subtitles with format_ratio
    print(f"\n[4/5] Generating Karaoke Subtitles ({format_ratio})...")
    subs_path = generate_ass_subtitles(word_timestamps, format_ratio=format_ratio)
    print(f"Subtitles: {subs_path} (exists: {subs_path.exists()})")

    # 5. Test FFmpeg Video Assembly at 8Mbps
    print(f"\n[5/5] Assembling {format_ratio} MP4 via FFmpeg High-Bitrate...")
    final_video = render_final_reel(
        all_scene_frame_dirs=all_scene_frame_dirs,
        audio_path=audio_path,
        subtitles_path=subs_path,
        output_filename="smoke_test_reel.mp4"
    )
    print(f"\n✅ SUCCESS! Final Video Created: {final_video}")
    print(f"File size: {final_video.stat().st_size / (1024*1024):.2f} MB")
    print("=== SMOKE TEST PASSED ===")

if __name__ == "__main__":
    run_smoke_test()
