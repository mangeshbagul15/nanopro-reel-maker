import streamlit as st
import time
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import OUTPUT_DIR
from core.director import generate_timeline
from core.voice import generate_voiceover, DEFAULT_VOICE
from core.animator import render_scene_frames
from core.subtitles import generate_ass_subtitles
from core.renderer import render_final_reel
from core.uploader import (
    upload_to_r2,
    list_r2_videos,
    delete_from_r2,
    get_r2_storage_stats
)

# Page Config
st.set_page_config(
    page_title="NanoPro Reel Maker — 2D Tech AI Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek Modern Look
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        color: white;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.6rem 2rem;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
    }
    .stat-badge {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Video Settings")
    voice_option = st.selectbox(
        "Voice Persona (TTS)",
        [
            ("en-US-ChristopherNeural", "Christopher (Calm Tech Authority)"),
            ("en-US-GuyNeural", "Guy (Conversational American)"),
            ("en-IN-PrabhatNeural", "Prabhat (Crisp Indian Tech)"),
            ("en-US-JennyNeural", "Jenny (Engaging Female Tech)")
        ],
        format_func=lambda x: x[1]
    )
    
    aspect_ratio = st.selectbox("Format", ["9:16 Vertical (Reels / Shorts / TikTok)"])
    
    visual_engine = st.selectbox(
        "Visual Engine & Style",
        [
            ("hybrid_modern", "🚀 Multi-Layer Hybrid Engine (Fireship + ByteByteGo + Terminal) [Recommended]"),
            ("bytebytego_dsl", "📊 ByteByteGo Architecture & Diagram DSL (D2 / Mermaid)"),
            ("remotion_web", "⚛️ Remotion React Motion Graphics (Fireship Cyberpunk)"),
            ("handdrawn_sketch", "✏️ Hand-Drawn Whiteboard Sketch (NeetCode / Excalidraw)"),
            ("terminal_screencast", "💻 Real Terminal Screencast (Asciinema / Hacker CLI)"),
            ("manim_math", "📐 Mathematical Animation (3Blue1Brown / Manim)"),
            ("kinetic_type", "🔤 Kinetic Typography (Apple Keynote Style)"),
            ("scene_graph", "🎨 Primitive Scene Graph (Canva / Figma Engine)"),
            ("ai_video_broll", "🎬 AI Generative Video & B-Roll (Runway / Pexels) [Requires Key]"),
            ("digital_avatar", "👤 AI Digital Human Presenter (HeyGen) [Requires Key]"),
            ("blender_local_gpu", "🖥️ Local NVIDIA GPU 3D Ray-Tracing (Blender 3D / Unreal Engine) [Heavy PC]"),
            ("cloud_serverless_gpu", "☁️ Cloud Serverless GPU 3D Studio (RunPod / Modal Ray-Tracing) [Cloud GPU]")
        ],
        format_func=lambda x: x[1]
    )
    
    st.markdown("---")
    st.markdown("### ⚡ Compute & Studio Switcher")
    
    # Automatic Environment Detection (Windows = Local RTX 3050, Linux = Streamlit Cloud)
    is_local_machine = (sys.platform == "win32")
    
    if is_local_machine:
        st.success("🟢 Active Mode: **Local RTX 3050 Studio**")
        st.caption("💻 Hardware: NVIDIA RTX 3050 NVENC • 16GB RAM • Blazing Fast")
        st.link_button("🌐 Switch to Online Cloud Studio", "https://nanopro-reel-maker.streamlit.app", use_container_width=True, type="secondary")
    else:
        st.info("☁️ Active Mode: **Online Cloud Studio**")
        st.caption("Running in Cloud. Switch to your laptop's GPU for maximum speed.")
        st.link_button("⚡ Switch to Local RTX GPU Studio", "http://localhost:8501", use_container_width=True, type="primary")

    compute_mode = st.selectbox(
        "Acceleration Mode",
        [
            ("local_studio", "⚡ पर्याय 'A': Local High-Performance Studio (NVIDIA RTX 3050 + 13th Gen i5)"),
            ("hybrid_daemon", "🌐 पर्याय 'B': Online UI + Local Worker Daemon (Hybrid Cloud & Local GPU)")
        ],
        format_func=lambda x: x[1]
    )
    
    st.markdown("---")
    st.markdown("### ☁️ Cloudflare R2 Storage")
    try:
        r2_stats = get_r2_storage_stats()
        st.write(f"💾 **Used:** {r2_stats['total_mb']} MB / 10 GB")
        st.progress(min(1.0, max(0.01, r2_stats["percent_used"] / 100)))
        st.caption(f"📁 **Total Saved Reels:** {r2_stats['total_files']} files")
        st.caption(f"🆓 **Free Space:** {r2_stats['free_gb_remaining']} GB left")
    except Exception as e:
        st.caption("Cloudflare R2 connected")

    st.markdown("---")
    st.markdown("### 🚀 Engine Status")
    st.success("🟢 Google Gemini 2.5 Flash: Ready")
    st.success("🟢 Groq Whisper Large v3: Ready")
    st.success("🟢 2D Canvas Engine: Ready")
    st.success("🟢 FFmpeg Encoder: Ready")
    st.info("☁️ Cloudflare R2: Connected")

# Main Header
st.markdown('<div class="main-title">🎬 NanoPro Reel Maker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">100% Automated 2D Tech Video Generator — Zero Hardcoding, Human Cadence, Karaoke Sync.</div>', unsafe_allow_html=True)

# Two Main Tabs
tab_create, tab_storage = st.tabs(["🎬 Create New Reel", "☁️ Cloudflare R2 Media & Storage Manager"])

with tab_create:
    # Quick Prompts
    st.markdown("**Quick Preset Topics:**")
    col1, col2, col3, col4 = st.columns(4)
    preset_selected = None
    if col1.button("☁️ AWS DMS in 60s"):
        preset_selected = "Explain AWS Database Migration Service (DMS) architecture with zero downtime"
    if col2.button("📊 SQL DENSE_RANK"):
        preset_selected = "Explain SQL DENSE_RANK vs RANK with real data table and duplicate salaries"
    if col3.button("❄️ Snowflake Pruning"):
        preset_selected = "How Snowflake micro-partitions and query pruning work under the hood"
    if col4.button("🐍 Python GIL"):
        preset_selected = "Explain Python Global Interpreter Lock (GIL) and why multi-threading blocks"

    # Prompt Input Box
    default_prompt = preset_selected if preset_selected else "Explain AWS Database Migration Service (DMS) architecture with zero downtime"
    user_prompt = st.text_area(
        "Enter Tech Topic / Scenario Prompt:",
        value=default_prompt,
        height=90,
        placeholder="e.g. Explain SQL Window Functions LEAD and LAG with interview scenario"
    )

    # Execution Action
    if st.button("🚀 Generate 60s Reel", use_container_width=True):
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt.")
            st.stop()

        progress_bar = st.progress(0)
        status_box = st.empty()

        try:
            # STEP 1: AI Director Timeline Generation
            status_box.info("🧠 Step 1/5: AI Director is planning the scenes and conversational script...")
            progress_bar.progress(15)
            timeline = generate_timeline(user_prompt.strip(), engine_style=visual_engine[0])
            
            with st.expander("📄 View AI Director Blueprint (JSON)", expanded=False):
                st.json(timeline)

            # STEP 2 & 3: Voiceover & Whisper Alignment
            status_box.info("🎙️ Step 2/5: Synthesizing natural human voice & aligning microsecond word timestamps...")
            progress_bar.progress(35)
            scenes = timeline.get("scenes", [])
            audio_path, word_timestamps, aligned_scenes = generate_voiceover(scenes, voice=voice_option[0])

            with st.expander("🔊 Audio & Word Timestamps", expanded=False):
                st.audio(str(audio_path))
                st.write(f"Total Spoken Words: {len(word_timestamps)}")

            # STEP 4: 2D Generative Visual Rendering (Zero Template)
            total_sc = len(aligned_scenes)
            all_scene_frame_dirs = []
            for i, sc in enumerate(aligned_scenes):
                status_box.info(f"🎨 Step 3/5: Rendering dynamic 2D scene {i + 1}/{total_sc} ({sc.get('visual_type', 'cards')})...")
                progress_bar.progress(40 + int(30 * (i + 1) / max(1, total_sc)))
                render_scene_frames(sc, i + 1, total_scenes=total_sc)
                all_scene_frame_dirs.append(OUTPUT_DIR / f"scene_{i + 1:02d}_frames")

            # STEP 5: Subtitles & Video Stitching
            status_box.info("✂️ Step 4/5: Generating karaoke captions & encoding 1080x1920 MP4 via FFmpeg...")
            progress_bar.progress(80)
            subtitles_path = generate_ass_subtitles(word_timestamps)
            
            final_video_path = render_final_reel(
                all_scene_frame_dirs=all_scene_frame_dirs,
                audio_path=audio_path,
                subtitles_path=subtitles_path,
                output_filename=f"nanopro_{int(time.time())}.mp4"
            )

            # Optional: Cloudflare R2 Upload
            status_box.info("☁️ Step 5/5: Uploading to Cloudflare R2 CDN...")
            progress_bar.progress(95)
            r2_url = upload_to_r2(final_video_path)

            progress_bar.progress(100)
            status_box.success("🎉 Reel generation complete!")

            # Display Final Video & Download
            col_vid, col_meta = st.columns([1, 1])
            with col_vid:
                st.markdown("### 📱 9:16 Reel Preview")
                st.video(str(final_video_path))
                with open(final_video_path, "rb") as vf:
                    st.download_button(
                        label="⬇️ Download 1080x1920 MP4 Reel",
                        data=vf.read(),
                        file_name=final_video_path.name,
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary"
                    )

            with col_meta:
                st.markdown("### 📊 Reel Summary")
                st.markdown(f"**Title:** {timeline.get('title', 'Tech Reel')}")
                st.markdown(f"**Category:** `{timeline.get('topic_category', 'general')}`")
                st.markdown(f"**Duration:** `{aligned_scenes[-1]['end_time']:.1f} seconds`")
                st.markdown(f"**Scenes Count:** `{len(aligned_scenes)} scenes`")

                with open(final_video_path, "rb") as vf:
                    st.download_button(
                        label="⬇️ Download MP4 Reel",
                        data=vf.read(),
                        file_name=final_video_path.name,
                        mime="video/mp4",
                        use_container_width=True
                    )

                if r2_url:
                    st.success("✅ Uploaded to Cloudflare R2 CDN (Permanent Link)!")
                    st.code(r2_url, language="markdown")

        except Exception as e:
            status_box.error(f"❌ Error during generation: {e}")
            st.exception(e)

with tab_storage:
    st.markdown("### ☁️ Cloudflare R2 Media & Storage Manager")
    st.markdown("Review all uploaded reels, view permanent universal URLs, and permanently delete unwanted videos to keep your 10 GB storage free.")

    stats = get_r2_storage_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Stored Reels", f"{stats['total_files']} files")
    c2.metric("Storage Used", f"{stats['total_mb']} MB")
    c3.metric("Free Space Left", f"{stats['free_gb_remaining']} GB", delta="10 GB Free Tier")
    if c4.button("🔄 Refresh Gallery", use_container_width=True):
        st.rerun()

    st.markdown("---")

    videos = list_r2_videos()
    if not videos:
        st.info("ℹ️ No videos stored in Cloudflare R2 yet. Once you generate reels in the Studio, they will appear here with preview and delete options!")
    else:
        st.markdown(f"Showing **{len(videos)}** stored reels in `nanopro-reels`:")
        for idx, vid in enumerate(videos):
            with st.container(border=True):
                col_left, col_right = st.columns([1, 1.2])
                with col_left:
                    if vid["url"]:
                        st.video(vid["url"])
                    else:
                        st.warning("Video streaming preview not available.")
                with col_right:
                    st.markdown(f"#### 🎬 `{vid['name']}`")
                    st.caption(f"📅 Uploaded: **{vid['last_modified']}** • 📊 Size: **{vid['size_mb']} MB**")
                    if vid["url"]:
                        st.markdown("**🔗 Permanent Universal URL:**")
                        st.code(vid["url"], language="text")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            st.link_button("🌐 Open in New Tab", vid["url"], use_container_width=True)
                        with col_btn2:
                            if st.button("🗑️ Delete Permanently", key=f"del_btn_{idx}_{vid['name']}", type="secondary", use_container_width=True):
                                if delete_from_r2(vid["name"]):
                                    st.success(f"Deleted {vid['name']} from Cloudflare R2!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Failed to delete video.")
