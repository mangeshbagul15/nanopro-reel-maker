import subprocess
import shutil
import time
from pathlib import Path
from typing import List
from core.config import FFMPEG_EXE, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, OUTPUT_DIR

def render_final_reel(
    all_scene_frame_dirs: List[Path],
    audio_path: Path,
    subtitles_path: Path = None,
    output_filename: str = None
) -> Path:
    """
    Assembles all scene image frames, audio, and karaoke subtitles into a polished
    1080x1920 9:16 vertical MP4 video using high-speed FFmpeg hardware/software encoding.
    """
    timestamp = int(time.time())
    if not output_filename:
        output_filename = f"reel_{timestamp}.mp4"
    final_output_path = OUTPUT_DIR / output_filename

    # 1. Create FFmpeg concat demuxer file listing all frames
    concat_list_file = OUTPUT_DIR / f"concat_frames_{timestamp}.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for scene_dir in all_scene_frame_dirs:
            frames = sorted([p for p in scene_dir.iterdir() if p.name.startswith("frame_") and p.suffix.lower() in [".jpg", ".png", ".jpeg"]])
            for frame in frames:
                # FFmpeg requires forward slashes or escaped backslashes
                safe_path = str(frame.resolve()).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")
                f.write(f"duration {1.0 / VIDEO_FPS:.4f}\n")
        # Repeat last frame once for concat demuxer end boundary
        if frames:
            last_frame_path = str(frames[-1].resolve()).replace("\\", "/")
            f.write(f"file '{last_frame_path}'\n")

    # 2. Build FFmpeg command
    temp_video_no_subs = OUTPUT_DIR / f"temp_visuals_{timestamp}.mp4"
    
    # Pass 1: Stitches frames with audio
    cmd_pass1 = [
        str(FFMPEG_EXE),
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file.resolve()),
        "-i", str(audio_path.resolve()),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "faster",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(temp_video_no_subs.resolve())
    ]
    
    _run_ffmpeg(cmd_pass1)

    # Pass 2: Burn in ASS Subtitles if provided and supported
    if subtitles_path and subtitles_path.exists():
        safe_subs_path = str(subtitles_path.resolve()).replace("\\", "/").replace(":", "\\:")
        cmd_pass2 = [
            str(FFMPEG_EXE),
            "-y",
            "-i", str(temp_video_no_subs.resolve()),
            "-vf", f"subtitles='{safe_subs_path}'",
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "20",
            "-c:a", "copy",
            str(final_output_path.resolve())
        ]
        try:
            _run_ffmpeg(cmd_pass2)
            # Remove intermediate file
            if temp_video_no_subs.exists():
                temp_video_no_subs.unlink()
        except Exception as e:
            print(f"[Renderer] Subtitle filter warning, using clean video: {e}")
            if temp_video_no_subs.exists():
                shutil.move(str(temp_video_no_subs), str(final_output_path))
    else:
        if temp_video_no_subs.exists():
            shutil.move(str(temp_video_no_subs), str(final_output_path))

    # Cleanup temporary frame files and concat manifest
    if concat_list_file.exists():
        concat_list_file.unlink()
    for s_dir in all_scene_frame_dirs:
        if s_dir.exists():
            shutil.rmtree(s_dir, ignore_errors=True)

    return final_output_path

def _run_ffmpeg(cmd: List[str]) -> None:
    """Executes FFmpeg command and raises on error with informative output."""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        error_log = result.stderr[-500:] if result.stderr else "Unknown error"
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}:\n{error_log}")
