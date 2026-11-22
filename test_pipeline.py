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
    
    # 1. Test Director
    topic = "AWS DMS in 30 seconds"
    print(f"\n[1/5] Calling Director for topic: '{topic}'...")
    timeline = generate_timeline(topic)
    print(f"Title: {timeline.get('title')}")
    print(f"Category: {timeline.get('topic_category')}")
    scenes = timeline.get("scenes", [])
    print(f"Generated {len(scenes)} scenes.")
    assert len(scenes) > 0, "No scenes generated!"

    # 2. Test Voice & Whisper
    print("\n[2/5] Synthesizing Voice & Extracting Whisper Timestamps...")
    audio_path, word_timestamps, aligned_scenes = generate_voiceover(scenes)
    print(f"Audio Path: {audio_path} (exists: {audio_path.exists()})")
    print(f"Total Words Extracted: {len(word_timestamps)}")
    assert len(word_timestamps) > 0, "No word timestamps returned!"

    # 3. Test 2D Animator
    print("\n[3/5] Rendering 2D Dynamic Visual Frames...")
    all_scene_frame_dirs = []
    # For fast smoke test, let's render frames for each scene
    for i, sc in enumerate(aligned_scenes):
        print(f"  Rendering Scene {i+1}: {sc.get('visual_type')} ({sc.get('duration')}s)...")
        render_scene_frames(sc, i + 1)
        all_scene_frame_dirs.append(OUTPUT_DIR / f"scene_{i+1:02d}_frames")

    # 4. Test Subtitles
    print("\n[4/5] Generating Karaoke Subtitles...")
    subs_path = generate_ass_subtitles(word_timestamps)
    print(f"Subtitles: {subs_path} (exists: {subs_path.exists()})")

    # 5. Test FFmpeg Video Assembly
    print("\n[5/5] Assembling 1080x1920 MP4 via FFmpeg...")
    final_video = render_final_reel(
        all_scene_frame_dirs=all_scene_frame_dirs,
        audio_path=audio_path,
        subtitles_path=subs_path,
        output_filename="smoke_test_reel.mp4"
    )
    print(f"\n SUCCESS! Final Video Created: {final_video}")
    print(f"File size: {final_video.stat().st_size / (1024*1024):.2f} MB")
    print("=== SMOKE TEST PASSED ===")

if __name__ == "__main__":
    run_smoke_test()
