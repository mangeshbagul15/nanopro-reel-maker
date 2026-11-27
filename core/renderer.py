import subprocess
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.config import FFMPEG_EXE, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, OUTPUT_DIR, SFX_DIR

_CACHED_ENCODER_MAP: Dict[str, List[str]] = {}

def _get_encoder_args(export_spec: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Dynamically tests and selects the best available hardware or software encoder
    calibrated to `export_spec` (High Profile NVENC / libx264 CRF / MediaFoundation).
    """
    spec = dict(export_spec or {})
    cq = str(spec.get("nvenc_cq") or "16")
    bv = str(spec.get("nvenc_bv") or "12M")
    crf = str(spec.get("x264_crf") or "16")
    cache_key = f"{cq}|{bv}|{crf}"
    if cache_key in _CACHED_ENCODER_MAP:
        return _CACHED_ENCODER_MAP[cache_key]

    bv_num = int("".join(ch for ch in bv if ch.isdigit()) or "12")
    max_bv = f"{max(10, int(bv_num * 1.4))}M"
    buf_bv = f"{max(16, int(bv_num * 2))}M"

    candidates = [
        # Candidate 1: NVIDIA NVENC High Profile (Prioritized on Local RTX 3050 GPU)
        (
            ["-c:v", "h264_nvenc", "-profile:v", "high", "-preset", "p5", "-cq", cq, "-b:v", bv, "-maxrate", max_bv, "-bufsize", buf_bv, "-pix_fmt", "yuv420p"],
            f"NVIDIA NVENC High Profile ({bv} / CQ {cq})"
        ),
        # Candidate 2: libx264 High Profile CPU (Razor-sharp text/gradients for Cloud & PNG/4K)
        (
            ["-c:v", "libx264", "-profile:v", "high", "-preset", "fast", "-crf", crf, "-pix_fmt", "yuv420p"],
            f"libx264 High Profile (CRF {crf})"
        ),
        # Candidate 3: Windows Media Foundation Hardware Acceleration
        (
            ["-c:v", "h264_mf", "-b:v", bv, "-pix_fmt", "yuv420p"],
            f"Windows Media Foundation Hardware ({bv})"
        ),
    ]

    for args, name in candidates:
        try:
            test_cmd = [
                str(FFMPEG_EXE), "-y",
                "-f", "lavfi", "-i", "color=c=black:s=128x128:d=0.1",
                *args,
                "-f", "null", "-"
            ]
            res = subprocess.run(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode == 0:
                print(f"[Renderer] Active Video Encoder: {name}")
                _CACHED_ENCODER_MAP[cache_key] = args
                return _CACHED_ENCODER_MAP[cache_key]
        except Exception:
            continue

    _CACHED_ENCODER_MAP[cache_key] = ["-c:v", "libx264", "-profile:v", "high", "-preset", "faster", "-crf", "18", "-pix_fmt", "yuv420p"]
    return _CACHED_ENCODER_MAP[cache_key]

BGM_TRACK_MAP = {
    "none": None,
    "lofi_cyber": "lofi_cyber_bgm.wav",
    "dark_cyber_suspense": "dark_cyber_suspense.wav",
    "upbeat_electro_pulse": "upbeat_electro_pulse.wav",
}


def render_final_reel(
    all_scene_frame_dirs: List[Path],
    audio_path: Path,
    subtitles_path: Path = None,
    output_filename: str = None,
    sfx_events: Optional[List[Dict[str, Any]]] = None,
    bgm_style: str = "lofi_cyber",
    bgm_volume: float = 0.18,
    fps: int = VIDEO_FPS,
    export_spec: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Assembles all scene image frames, audio, micro-SFX cues, selected BGM track/volume,
    and karaoke subtitles into a polished MP4 video using high-speed FFmpeg encoding.
    """
    eff_fps = max(15, int((export_spec or {}).get("fps") or fps or VIDEO_FPS))
    timestamp = int(time.time())
    if not output_filename:
        output_filename = f"reel_{timestamp}.mp4"
    final_output_path = OUTPUT_DIR / output_filename

    # 1. Create FFmpeg concat demuxer file listing all frames
    concat_list_file = OUTPUT_DIR / f"concat_frames_{timestamp}.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        frames = []
        for scene_dir in all_scene_frame_dirs:
            sc_frames = sorted([p for p in scene_dir.iterdir() if p.name.startswith("frame_") and p.suffix.lower() in [".jpg", ".png", ".jpeg"]])
            frames.extend(sc_frames)
            for frame in sc_frames:
                safe_path = str(frame.resolve()).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")
                f.write(f"duration {1.0 / eff_fps:.6f}\n")
        # Hold last frame to cleanly cover audio without premature cutoff
        if frames:
            last_frame_path = str(frames[-1].resolve()).replace("\\", "/")
            f.write(f"file '{last_frame_path}'\n")
            f.write("duration 1.0\n")
            f.write(f"file '{last_frame_path}'\n")

    bgm_file_name = BGM_TRACK_MAP.get(str(bgm_style or "lofi_cyber").lower().strip(), "lofi_cyber_bgm.wav")
    bgm_vol = max(0.0, min(0.38, float(bgm_volume)))
    bgm_path = (SFX_DIR / bgm_file_name) if bgm_file_name else None
    has_bgm = (bgm_path is not None) and bgm_path.exists() and bgm_vol >= 0.005
    has_subs = subtitles_path is not None and subtitles_path.exists()
    safe_subs_path = str(subtitles_path.resolve()).replace("\\", "/").replace(":", "\\:") if has_subs else ""

    encoder_args = _get_encoder_args(export_spec)

    # Build High-Speed Single-Pass FFmpeg Command
    inputs = [
        str(FFMPEG_EXE), "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file.resolve()),
        "-i", str(audio_path.resolve())
    ]
    if has_bgm:
        inputs.extend(["-stream_loop", "-1", "-i", str(bgm_path.resolve())])

    valid_sfx: List[Dict[str, Any]] = []
    if sfx_events:
        for ev in sfx_events[:12]:
            s_name = str(ev.get("sfx") or "").strip().lower()
            s_file = SFX_DIR / f"{s_name}.wav"
            if s_file.exists():
                valid_sfx.append({
                    "path": s_file,
                    "delay_ms": max(0, int(round(float(ev.get("time", 0.0)) * 1000.0))),
                    "gain": max(0.05, min(0.32, float(ev.get("gain", 0.18)))),
                })
                inputs.extend(["-i", str(s_file.resolve())])

    # Filter Complex Construction
    filter_parts = []
    if has_subs:
        filter_parts.append(f"[0:v]subtitles='{safe_subs_path}'[v_out]")
        video_map = "[v_out]"
    else:
        video_map = "0:v"

    mix_labels: List[str] = ["[speech]"]
    filter_parts.append("[1:a]volume=1.0[speech]")
    sfx_base_idx = 2
    if has_bgm:
        filter_parts.append(f"[2:a]volume={bgm_vol:.2f}[bgm]")
        mix_labels.append("[bgm]")
        sfx_base_idx = 3

    for si, sx in enumerate(valid_sfx):
        in_i = sfx_base_idx + si
        ms = sx["delay_ms"]
        gn = sx["gain"]
        lbl = f"[sx{si}]"
        filter_parts.append(f"[{in_i}:a]adelay={ms}|{ms},volume={gn:.2f}{lbl}")
        mix_labels.append(lbl)

    if len(mix_labels) > 1:
        # Speech is always first input so duration=first terminates cleanly at voiceover end
        filter_parts.append(f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2:normalize=0[a_out]")
        audio_map = "[a_out]"
    else:
        filter_parts.pop()
        audio_map = "1:a"

    cmd = list(inputs)
    if filter_parts:
        cmd.extend(["-filter_complex", ";".join(filter_parts)])
    cmd.extend(["-map", video_map, "-map", audio_map])
    cmd.extend(encoder_args)
    cmd.extend(["-r", str(eff_fps), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(final_output_path.resolve())])

    try:
        _run_ffmpeg(cmd)
    except Exception as e:
        print(f"[Renderer] Primary encode failed ({e}), falling back to two-pass / CPU...")
        # Fallback without subtitles if filter failed
        fallback_cmd = [
            str(FFMPEG_EXE), "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list_file.resolve()),
            "-i", str(audio_path.resolve()),
            "-c:v", "libx264", "-preset", "faster", "-crf", "22", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_output_path.resolve())
        ]
        _run_ffmpeg(fallback_cmd)

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
        error_log = result.stderr[-600:] if result.stderr else "Unknown error"
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}:\n{error_log}")
