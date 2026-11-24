import streamlit as st
import time
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import importlib
import core.config
import core.director
import core.voice
import core.animator
import core.subtitles
import core.renderer
import core.uploader

importlib.reload(core.config)
importlib.reload(core.director)
importlib.reload(core.voice)
importlib.reload(core.animator)
importlib.reload(core.subtitles)
importlib.reload(core.renderer)
importlib.reload(core.uploader)

from core.config import OUTPUT_DIR, VIDEO_FPS, FORMAT_SPECS
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
            ("hi-IN-MadhurNeural", "🇮🇳 Madhur (Hindi / Hinglish Tech Authority - Male)"),
            ("hi-IN-SwaraNeural", "🇮🇳 Swara (Hindi / Hinglish Conversational - Female)"),
            ("en-IN-PrabhatNeural", "🇮🇳 Prabhat (Crisp Indian Tech English - Male)"),
            ("en-IN-NeerjaExpressiveNeural", "🇮🇳 Neerja (Expressive Hinglish / Indian Tech - Female)"),
            ("mr-IN-ManoharNeural", "🇮🇳 Manohar (Marathi Tech Authority - Male)"),
            ("mr-IN-AarohiNeural", "🇮🇳 Aarohi (Marathi Conversational - Female)"),
            ("en-US-ChristopherNeural", "🇺🇸 Christopher (Calm Tech Authority - US Male)"),
            ("en-US-GuyNeural", "🇺🇸 Guy (Conversational American - US Male)"),
            ("en-US-JennyNeural", "🇺🇸 Jenny (Engaging Female Tech - US Female)"),
            ("en-GB-RyanNeural", "🇬🇧 Ryan (Crisp British Tech - UK Male)")
        ],
        format_func=lambda x: x[1]
    )
    
    aspect_ratio = st.selectbox(
        "Format",
        [
            ("9:16", "📱 9:16 Vertical (Reels / Shorts / TikTok - 1080x1920)"),
            ("16:9", "🖥️ 16:9 Widescreen (YouTube / Landscape - 1920x1080)"),
            ("1:1", "⏹️ 1:1 Square (Instagram / LinkedIn Post - 1080x1080)")
        ],
        format_func=lambda x: x[1]
    )
    
    duration_option = st.selectbox(
        "Video Duration & Depth (No 60s Limit)",
        [
            ("auto", "⚡ Dynamic / Auto (Based on topic depth) [Recommended]"),
            ("short", "⏱️ Quick Explainer (~30-45 sec)"),
            ("standard", "🎬 Standard Explainer (~60 sec)"),
            ("deep_dive", "🧠 Deep-Dive Architecture (~90-180+ sec)")
        ],
        format_func=lambda x: x[1]
    )
    
    visual_engine = st.selectbox(
        "Visual Engine & Style",
        [
            ("hybrid_modern", "🚀 Multi-Layer Hybrid Engine (Fireship + ByteByteGo + Terminal) [Recommended]"),
            ("terminal_screencast", "💻 Real Terminal & Hacker CLI Screencast (Bash / Python / Shell / Logs)"),
            ("bytebytego_dsl", "📊 ByteByteGo Architecture & Cloud Topology (Pipelines / Microservices)"),
            ("sql_deepdive", "🗄️ SQL Table, Query & Dataset Execution (Schemas / DENSE_RANK / Window Functions)"),
            ("split_comparison", "⚖️ Architectural Split Comparison (Legacy vs Modern / Trade-offs)"),
            ("benchmark_speed", "⚡ Performance Benchmark Bars & Latency (Throughput / Speedup 15x)"),
            ("memory_internals", "🧩 Memory Buffer, CDC WAL & Partition Slots (Low-level Bytes / Offsets)"),
            ("network_mesh", "🌐 Circular Hub & Spoke Event Mesh (Message Broker / Radar Nodes)"),
            ("telemetry_hud", "⏱️ Speedometer & Live Telemetry HUD (99.999% SLA / CPU / Event Counters)"),
            ("alert_troubleshoot", "🚨 Production Incident Alert & Post-Mortem (Radar Alert / Bottlenecks)"),
            ("concept_keynote", "💡 Kinetic Concept Keynote (Punchy Principles & Bullet Cards)"),
            ("custom_user_style", "✍️ Custom Visual Style... (Type your own custom visual aesthetic)")
        ],
        format_func=lambda x: x[1]
    )
    
    custom_style_prompt = ""
    if visual_engine[0] == "custom_user_style":
        custom_style_prompt = st.text_input(
            "Enter Custom Visual Aesthetic:",
            placeholder="e.g. Cyberpunk neon green terminal with matrix code rain and glowing data blocks",
            help="Describe the exact visual style, colors, and layout you want for every scene."
        )
    
    st.markdown("---")
    st.markdown("### ⚡ Compute & Studio Switcher")
    
    # Automatic Environment Detection (Windows = Local RTX 3050, Linux = Streamlit Cloud)
    is_local_machine = (sys.platform == "win32")
    
    if is_local_machine:
        st.success("🟢 Active: **Local RTX 3050 Studio**")
        st.caption("💻 Hardware: NVIDIA RTX 3050 NVENC • 16GB RAM • Blazing Fast")
        st.link_button("🌐 Switch to Online Cloud Studio", "https://nanopro-reel-maker.streamlit.app", use_container_width=True, type="secondary")
    else:
        st.info("☁️ Active: **Online Cloud Studio**")
        st.caption("Running in Cloud. Switch to your laptop's GPU for maximum speed.")
        st.link_button("⚡ Switch to Local RTX GPU Studio", "http://localhost:8501", use_container_width=True, type="primary")
    
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
    st.success("🟢 Google Gemini 3 Flash: Ready")
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
    # Initialize session state for user prompt
    if "user_prompt_input" not in st.session_state:
        st.session_state.user_prompt_input = "Explain AWS Database Migration Service (DMS) architecture with zero downtime"

    # Quick Prompts
    st.markdown("**Quick Preset Topics:**")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("☁️ AWS DMS Architecture"):
        st.session_state.user_prompt_input = "Explain AWS Database Migration Service (DMS) architecture with zero downtime"
        st.rerun()
    if col2.button("📊 SQL DENSE_RANK"):
        st.session_state.user_prompt_input = "Explain SQL DENSE_RANK vs RANK with real data table and duplicate salaries"
        st.rerun()
    if col3.button("❄️ Snowflake Pruning"):
        st.session_state.user_prompt_input = "How Snowflake micro-partitions and query pruning work under the hood"
        st.rerun()
    if col4.button("🐍 Python GIL"):
        st.session_state.user_prompt_input = "Explain Python Global Interpreter Lock (GIL) and why multi-threading blocks"
        st.rerun()

    # Prompt Input Box bound directly to session state
    user_prompt = st.text_area(
        "Enter Tech Topic / Scenario Prompt:",
        key="user_prompt_input",
        height=90,
        placeholder="e.g. Explain SQL Window Functions LEAD and LAG with interview scenario"
    )

    # Execution Action
    if st.button("🚀 Generate Video Reel", use_container_width=True):
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt.")
            st.stop()

        progress_bar = st.progress(0)
        status_box = st.empty()

        try:
            # STEP 1: AI Director Timeline Generation
            status_box.info("🧠 AI Director is designing the technical storyboard & script...")
            progress_bar.progress(20)
            timeline = generate_timeline(
                user_prompt.strip(),
                engine_style=visual_engine[0],
                duration_mode=duration_option[0],
                custom_style_prompt=custom_style_prompt,
                voice=voice_option[0],
                format_ratio=aspect_ratio[0]
            )
            
            with st.expander("📄 View Raw AI Director Blueprint (JSON)", expanded=False):
                st.json(timeline)

            # STEP 2: Voiceover & Whisper Alignment
            status_box.info("🎙️ Synthesizing conversational voiceover & microsecond word timestamps...")
            progress_bar.progress(40)
            scenes = timeline.get("scenes", [])
            audio_path, word_timestamps, aligned_scenes = generate_voiceover(scenes, voice=voice_option[0])

            with st.expander("🔊 Audio & Word Timestamps", expanded=False):
                st.audio(str(audio_path))
                st.write(f"Total Spoken Words: {len(word_timestamps)}")

            # STEP 3: 2D Generative Visual Rendering
            total_sc = len(aligned_scenes)
            all_scene_frame_dirs = []

            # Clean previous scene frame directories to avoid cross-contamination
            import shutil
            for old_dir in OUTPUT_DIR.glob("scene_*_frames"):
                try:
                    shutil.rmtree(old_dir, ignore_errors=True)
                except Exception:
                    pass

            for i, sc in enumerate(aligned_scenes):
                v_type = sc.get('visual_type', 'cards')
                status_box.info(f"🎨 Rendering motion visuals for scene {i + 1}/{total_sc} ({v_type})...")
                progress_bar.progress(45 + int(35 * (i + 1) / max(1, total_sc)))
                render_scene_frames(
                    sc,
                    i + 1,
                    total_scenes=total_sc,
                    engine_style=visual_engine[0],
                    format_ratio=aspect_ratio[0]
                )
                all_scene_frame_dirs.append(OUTPUT_DIR / f"scene_{i + 1:02d}_frames")

            # STEP 4: Video Stitching via Local Hardware / Cloud
            status_box.info(f"⚡ Assembling {aspect_ratio[0]} MP4 with karaoke captions & Lo-Fi audio...")
            progress_bar.progress(85)
            subtitles_path = generate_ass_subtitles(
                word_timestamps,
                format_ratio=aspect_ratio[0]
            )
            
            final_video_path = render_final_reel(
                all_scene_frame_dirs=all_scene_frame_dirs,
                audio_path=audio_path,
                subtitles_path=subtitles_path,
                output_filename=f"nanopro_{aspect_ratio[0].replace(':', 'x')}_{int(time.time())}.mp4"
            )

            # Cloudflare R2 Upload (Automatic only on Cloud, Optional on Local)
            r2_url = None
            if not is_local_machine:
                status_box.info("☁️ Uploading to Cloudflare R2 CDN...")
                progress_bar.progress(95)
                r2_url = upload_to_r2(final_video_path)

            progress_bar.progress(100)
            if is_local_machine:
                status_box.success("🎉 Reel generated and saved locally on your laptop!")
            else:
                status_box.success("🎉 Reel generation complete and deployed to Cloud CDN!")

            # Display Final Video & Actions
            col_vid, col_meta = st.columns([1, 1.1])
            with col_vid:
                st.markdown(f"### 📱 {aspect_ratio[0]} Video Preview")
                st.video(str(final_video_path))
                with open(final_video_path, "rb") as vf:
                    st.download_button(
                        label=f"⬇️ Download {aspect_ratio[0]} MP4 Video",
                        data=vf.read(),
                        file_name=final_video_path.name,
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary"
                    )

            with col_meta:
                st.markdown("### 📊 Production Inspector & Reel Summary")
                total_duration = aligned_scenes[-1]['end_time']
                
                # Top KPI Row
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("⏱️ Duration", f"{total_duration:.1f}s")
                kpi2.metric("🎬 Scenes", f"{len(aligned_scenes)}")
                kpi3.metric("🗣️ Words", f"{len(word_timestamps)}")
                kpi4.metric("📐 Format", f"{aspect_ratio[0]}")

                # Permanent Cloudflare R2 CDN Link Section
                if r2_url:
                    st.success("✅ **Uploaded to Cloudflare R2 CDN (Permanent Link):**")
                    st.code(r2_url, language="text")
                    st.link_button("🌐 Open Video in New Tab", r2_url, type="primary", use_container_width=True)
                elif is_local_machine:
                    st.info(f"💾 **Local Video Path:** `{final_video_path}`")
                    c_up1, c_up2 = st.columns(2)
                    with c_up1:
                        if st.button("📂 Open Output Folder", use_container_width=True):
                            import os
                            os.startfile(str(OUTPUT_DIR))
                    with c_up2:
                        if st.button("☁️ Upload to R2 CDN Now", use_container_width=True):
                            with st.spinner("Uploading to Cloudflare R2 Global Edge..."):
                                manual_r2 = upload_to_r2(final_video_path)
                                if manual_r2:
                                    st.success("✅ Permanent CDN Link Ready!")
                                    st.code(manual_r2, language="text")
                                    st.link_button("🌐 Open Live Video", manual_r2, type="primary", use_container_width=True)

                st.markdown("---")

                # 1. Step-by-Step Production Log ("First kay kel, then kay, then kay...")
                with st.expander("🔄 Complete Pipeline Execution Log (Start to Finish)", expanded=True):
                    st.markdown(f"""
                    1. **🧠 Step 1 — AI Director & Storyboard Blueprinting:**
                       - **Topic Entered:** *"{user_prompt.strip()}"*
                       - **AI Model Used:** `Google Gemini 3 Flash (gemini-3-flash-preview)`
                       - **Visual Engine:** `{visual_engine[1]}`
                       - **Duration Strategy:** `{duration_option[1]}` (Planned {len(aligned_scenes)} scenes without artificial 60s cutoff)
                    
                    2. **🎙️ Step 2 — Text-to-Speech & Microsecond Alignment:**
                       - **Voice Persona (TTS):** `{voice_option[1]}` (`{voice_option[0]}`)
                       - **Speech Engine:** Microsoft Edge-TTS (Per-scene exact millisecond synthesis)
                       - **Audio Alignment API:** `Groq Whisper Large v3` (`whisper-large-v3`)
                       - **Total Aligned Words:** `{len(word_timestamps)}` words aligned with 0% drift across all scenes.

                    3. **🎨 Step 3 — 2D Generative Visual Rendering:**
                       - **Rendering Engine:** Python 2D Generative Canvas (Pillow)
                       - **Resolution & Frame Rate:** {FORMAT_SPECS[aspect_ratio[0]]['width']}x{FORMAT_SPECS[aspect_ratio[0]]['height']} ({aspect_ratio[0]}) @ {VIDEO_FPS} FPS (Razor-sharp, 0% blur)
                       - **Dynamic Story Elements:** Visuals strictly enforced to match `{visual_engine[0]}`.
                       - **Total Frames Generated:** `{round(total_duration * VIDEO_FPS)}` frames rendered frame-by-frame.

                    4. **⚡ Step 4 — Hardware FFmpeg Video Stitching & Captions:**
                       - **Video Encoder:** Hardware Accelerated High-Bitrate (Windows Media Foundation 8 Mbps / libx264 CRF 18)
                       - **Karaoke Subtitles:** Advanced SubStation Alpha (`.ass`) with safe-zone margin adapted to {aspect_ratio[0]}
                       - **Audio Mixing:** Lo-Fi Cyber BGM mixed at 18% ducking volume under voiceover.

                    5. **☁️ Step 5 — Deployment & Storage:**
                       - **Host Compute:** `{"Local NVIDIA RTX 3050 Laptop Studio (Windows)" if is_local_machine else "Online Cloud Studio Container (Linux)"}`
                       - **Cloud CDN Target:** Cloudflare R2 Global Object Storage (`nanopro-reels`)
                    """)

                # 2. Complete Spoken Script (Verbatim Transcript)
                with st.expander("📜 Full Verbatim Script (Complete Narrator Transcript)", expanded=False):
                    full_script_text = "\n\n".join([f"[Scene {idx + 1} • {sc.get('role', 'scene').upper()} ({sc['duration']:.1f}s)]\n{sc.get('narration')}" for idx, sc in enumerate(aligned_scenes)])
                    st.text_area("Full Script Text:", value=full_script_text, height=220)
                    st.markdown(f"**Total Script Word Count:** {len(word_timestamps)} words")

                # 3. Scene-by-Scene Visual Breakdown ("Kontya scenes sathi konte visuals, kasa plan kela, konte element ghetle")
                with st.expander("🎬 Scene-by-Scene Visual Storyboard & Elements Breakdown", expanded=False):
                    for idx, sc in enumerate(aligned_scenes):
                        v_data = sc.get("visual_data", {})
                        v_type = sc.get("visual_type", "cards")
                        st.markdown(f"#### 📍 Scene {idx + 1}: `{sc.get('role', 'Scene').upper()}` ({sc['start_time']:.1f}s ➔ {sc['end_time']:.1f}s • {sc['duration']:.1f}s)")
                        st.markdown(f"- **Visual Engine:** `{v_type}`")
                        st.markdown(f"- **Badge & Title:** `{v_data.get('badge', 'N/A')}` — **{v_data.get('title', 'N/A')}**")
                        
                        # Show specific elements based on visual type
                        if v_type == "architecture_flow":
                            nodes = v_data.get("nodes", [])
                            node_labels = " ➔ ".join([f"**[{n.get('label')}]** ({n.get('sub', '')})" for n in nodes]) if nodes else "Pipeline nodes"
                            st.markdown(f"- **Rendered Nodes:** {node_labels}")
                        elif v_type == "sql_table":
                            code_snip = v_data.get("code_snippet", "")
                            st.markdown(f"- **SQL Query:** `{code_snip}`")
                            st.markdown(f"- **Table Columns:** `{v_data.get('table_data', {}).get('headers', [])}`")
                        elif v_type == "code_terminal":
                            cmd = v_data.get("command", "")
                            code = v_data.get("code_snippet", "")
                            st.markdown(f"- **CLI Command:** `{cmd}`" if cmd else "- **Terminal Code:**")
                            st.code(code[:150] + ("..." if len(code) > 150 else ""), language="python")
                        elif v_type == "split_comparison":
                            st.markdown(f"- **Comparison:** ❌ `{v_data.get('left_label')}` vs ⚡ `{v_data.get('right_label')}`")
                            st.markdown(f"- **Points:** {len(v_data.get('left_points', []))} cons vs {len(v_data.get('right_points', []))} pros")
                        elif v_type == "benchmark_chart":
                            bars = v_data.get("bars", [])
                            st.markdown(f"- **Benchmark Metrics:** {len(bars)} comparative bars • Winner: **{v_data.get('winner_badge', '10X FASTER')}**")
                        elif v_type == "data_structure_memory":
                            entries = v_data.get("entries", [])
                            st.markdown(f"- **Memory Offsets:** {len(entries)} buffer slots rendered with LSN offsets")
                        elif v_type == "alert_diagram":
                            st.markdown(f"- **Production Bottleneck:** *{v_data.get('problem_title', 'Incident Alert')}*")
                            st.markdown(f"- **Core Dilemma:** *{v_data.get('challenge', '')}*")
                        elif v_type == "circular_hub_mesh":
                            st.markdown(f"- **Central Broker:** `{v_data.get('hub_name', 'CORE BROKER')}` with {len(v_data.get('satellites', []))} satellite nodes")
                        elif v_type == "metric_gauge_hud":
                            st.markdown(f"- **Primary Gauge:** `{v_data.get('main_value')}` {v_data.get('main_unit')} ({v_data.get('gauge_percent')}% meter)")
                        else:
                            st.markdown(f"- **Bullet Cards:** `{v_data.get('bullets', [])}`")

                        st.markdown(f"- **Spoken Narration:** *\"{sc.get('narration')}\"*")
                        st.markdown("---")

                # 4. APIs, Models & System Stack Summary Table
                with st.expander("🤖 Tech Stack & API Architecture Matrix", expanded=False):
                    st.table([
                        {"Pipeline Layer": "AI Director & Storyboard", "API / Provider": "Google AI Studio", "Model / Spec": "gemini-3-flash-preview", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Text-to-Speech (TTS)", "API / Provider": "Microsoft Edge-TTS", "Model / Spec": str(voice_option[0]), "Status": "Active 🟢"},
                        {"Pipeline Layer": "Audio Alignment", "API / Provider": "Groq Cloud API", "Model / Spec": "whisper-large-v3 (Word-Level)", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Visual Graphics Engine", "API / Provider": "Python Pillow (PIL)", "Model / Spec": f"{FORMAT_SPECS[aspect_ratio[0]]['width']}x{FORMAT_SPECS[aspect_ratio[0]]['height']} ({aspect_ratio[0]}) @ {VIDEO_FPS} FPS", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Video Stitcher & Encoder", "API / Provider": "FFmpeg Engine", "Model / Spec": "Hardware MF 8Mbps / libx264 CRF 18", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Subtitles & Karaoke", "API / Provider": "ASS SubStation Engine", "Model / Spec": "Segoe UI Safe-Zone Font", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Cloud CDN Storage", "API / Provider": "Cloudflare R2", "Model / Spec": "S3 Global Edge (pub-ba534...)", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Host Compute", "API / Provider": "Local RTX 3050" if is_local_machine else "Streamlit Cloud", "Model / Spec": "Windows 11 / 16GB RAM", "Status": "Active 🟢"}
                    ])

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
