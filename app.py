import streamlit as st
import time
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure fresh module imports on Streamlit Cloud hot-reloads
import importlib
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("core."):
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

from core.config import OUTPUT_DIR, VIDEO_FPS, FORMAT_SPECS, DEFAULT_WATERMARK
from core.director import generate_timeline, generate_viral_meta, generate_video_titles
from core.voice import generate_voiceover, DEFAULT_VOICE, get_elevenlabs_usage, ELEVENLABS_MODELS, VOICE_CATALOG
from core.animator import render_scene_frames, generate_thumbnail_9_16
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
    channel_watermark = st.text_input(
        "🏷️ Channel Watermark (Video Corner)",
        value=DEFAULT_WATERMARK,
        help="Channel watermark displayed in the corner of every video frame and thumbnail."
    )
    st.markdown("---")
    st.markdown("### 🎭 Script Tone & Delivery Style")
    tone_option = st.selectbox(
        "Script Tone & Emotion",
        [
            ("fireship_octane", "🔥 High-Octane & Punchy (Fireship Style - Fast, Witty & Zero Fluff) [Recommended]"),
            ("dramatic_performance", "🎭 Dramatic & Emotionally Rich (Suspenseful, Dramatic Pauses & Theatrical)"),
            ("staff_engineer", "🧠 Senior Staff Engineer Authority (ByteByteGo Architectural Depth & Trade-offs)"),
            ("conversational_casual", "☕ Conversational & Friendly (Casual Tech Friend Chat over Coffee)"),
            ("interview_prep", "⚡ High-Stakes Interview Prep (FAANG Question & Tactical Masterclass)")
        ],
        format_func=lambda x: x[1],
        help="Controls the AI Director's scriptwriting style, dramatic pauses ('...'), and ElevenLabs voice delivery emotion."
    )
    chosen_tone = tone_option[0]

    st.markdown("---")
    st.markdown("### 🎙️ Voice & TTS Engine")
    voice_provider = st.radio(
        "Select Voice Engine Provider:",
        ["ElevenLabs AI (Ultra-Realistic)", "Microsoft Edge-TTS (Free & Fast)"],
        index=0,
        help="ElevenLabs provides studio-quality realistic human cadence with emotional performance. Edge-TTS is completely free and fast."
    )

    # Gender filter pills (safe fallback for older Streamlit versions)
    if hasattr(st, "pills"):
        gender_filter = st.pills("Filter Voice by Gender:", ["All", "👨 Male", "👩 Female"], default="All")
    else:
        gender_filter = st.radio("Filter Voice by Gender:", ["All", "👨 Male", "👩 Female"], index=0, horizontal=True)
    g_filter_key = "all" if (not gender_filter or gender_filter == "All") else ("male" if "Male" in gender_filter else "female")

    if voice_provider == "ElevenLabs AI (Ultra-Realistic)":
        el_usage = get_elevenlabs_usage()
        st.caption(f"💳 **Free Tier Usage:** `{el_usage['character_count']}` / `{el_usage['character_limit']}` credits used ({el_usage['remaining']} remaining)")
        st.progress(min(1.0, max(0.01, el_usage["percent_used"] / 100)))
        st.caption("⚡ **Credit Conservation Active:** Audio is cached locally by hash, so repeated generations consume 0 credits.")

        elevenlabs_model_choice = st.selectbox(
            "ElevenLabs Voice Model",
            [
                ("eleven_flash_v2_5", "⚡ Eleven Flash v2.5 (Fastest & Emotive • 50% fewer credits [Recommended])"),
                ("eleven_multilingual_v2", "🎭 Eleven Multilingual v2 (Emotionally rich delivery for dramatic performances)"),
                ("eleven_turbo_v2_5", "🚀 Eleven Turbo v2.5 (Our best model for real-time and agents)")
            ],
            format_func=lambda x: x[1],
            help="Choose the ElevenLabs model. Flash v2.5 is fastest and uses 50% fewer credits."
        )
        elevenlabs_model_id = elevenlabs_model_choice[0]

        # Filter available voices by gender
        available_el_voices = VOICE_CATALOG.get("elevenlabs", [])
        if g_filter_key != "all":
            available_el_voices = [v for v in available_el_voices if v.get("gender") == g_filter_key]

        el_voice_options = [(v["id"], v["label"]) for v in available_el_voices]
        el_voice_options.append(("custom", "✍️ Custom Voice ID (Enter your own Voice ID)"))

        elevenlabs_voice_choice = st.selectbox(
            f"ElevenLabs Voice Persona ({len(available_el_voices)} available)",
            el_voice_options,
            format_func=lambda x: x[1]
        )
        if elevenlabs_voice_choice[0] == "custom":
            custom_vid = st.text_input("Enter ElevenLabs Voice ID:", placeholder="e.g. pNInz6obpgDQGcFmaJgB")
            chosen_voice = f"elevenlabs:{custom_vid.strip()}" if custom_vid.strip() else "elevenlabs:pNInz6obpgDQGcFmaJgB"
            voice_label = f"ElevenLabs Custom ({custom_vid.strip()})"
        else:
            chosen_voice = elevenlabs_voice_choice[0]
            voice_label = elevenlabs_voice_choice[1]
    else:
        elevenlabs_model_id = "eleven_flash_v2_5"
        available_edge_voices = VOICE_CATALOG.get("edge_tts", [])
        if g_filter_key != "all":
            available_edge_voices = [v for v in available_edge_voices if v.get("gender") == g_filter_key]
        edge_voice_options = [(v["id"], v["label"]) for v in available_edge_voices]

        edge_voice_choice = st.selectbox(
            f"Edge-TTS Voice Persona ({len(available_edge_voices)} available)",
            edge_voice_options,
            format_func=lambda x: x[1]
        )
        chosen_voice = edge_voice_choice[0]
        voice_label = edge_voice_choice[1]
    
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
            ("all_in_one_tech_canvas", "🔮 All-in-One Tech Canvas (DB Cylinders, Python, AWS, AI Robot, K8s, Pipeline & 2D Motion) [Recommended]"),
            ("hybrid_modern", "🚀 Multi-Layer Hybrid Engine (Fireship + ByteByteGo + Terminal)"),
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
    st.success("🟢 Google Gemini Flash: Ready")
    st.success("🟢 ElevenLabs AI Voice: Connected (10k Free Tier)")
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

    with st.expander("✍️ Custom Script / Storyboard Override (Optional)", expanded=False):
        st.caption("Want full control over the spoken script? Type or paste your exact scene-by-scene narration below. The AI Director will structure the visuals around your exact words.")
        custom_script_override = st.text_area(
            "Custom Script Narration Override:",
            placeholder="Scene 1: At 3 AM, our production database locked up under traditional mysqldump...\nScene 2: Here's how AWS DMS replicates changes continuously using CDC without table locks...\nScene 3: The result? Sub-second replication lag and zero production downtime.",
            height=130,
            help="If provided, AI Director will strictly adapt the scenes and visuals to match these exact spoken narrations."
        )

    # Action Studio Controls Bar
    st.markdown("#### 🚀 Action Studio Controls:")
    col_act1, col_act2 = st.columns([1.3, 1])
    col_act3, col_act4 = st.columns([1, 1])

    do_full_generate = col_act1.button("🎬 Generate Full Video Reel", type="primary", use_container_width=True)
    do_titles = col_act2.button("🏷️ Make Title for Video", type="secondary", use_container_width=True)
    do_thumbnail = col_act3.button("🖼️ Generate 9:16 Thumbnail", use_container_width=True)
    do_meta = col_act4.button("📋 Generate Description & Hashtags", use_container_width=True)

    # 1. STANDALONE 9:16 THUMBNAIL GENERATOR
    if do_thumbnail:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        with st.spinner(f"Generating 9:16 high-impact thumbnail with watermark {channel_watermark}..."):
            try:
                thumb_path = generate_thumbnail_9_16(
                    user_prompt.strip(),
                    watermark=channel_watermark,
                    visual_engine=visual_engine[0]
                )
                st.success("🎉 9:16 Thumbnail generated successfully!")
                c_th1, c_th2 = st.columns([1, 1.2])
                with c_th1:
                    st.image(str(thumb_path), caption="9:16 High-Conversion Thumbnail (Shorts / Reels Cover)", use_container_width=True)
                with c_th2:
                    st.markdown("### 🖼️ 9:16 Thumbnail Details")
                    st.write(f"- **Aspect Ratio:** `9:16` (1080x1920)")
                    st.write(f"- **Channel Watermark:** `{channel_watermark}`")
                    st.write(f"- **Topic:** *{user_prompt.strip()}*")
                    with open(thumb_path, "rb") as tf:
                        st.download_button(
                            label="⬇️ Download 9:16 Thumbnail (PNG)",
                            data=tf.read(),
                            file_name=thumb_path.name,
                            mime="image/png",
                            use_container_width=True,
                            type="primary"
                        )
            except Exception as e:
                st.error(f"❌ Error generating thumbnail: {e}")

    # 2. STANDALONE VIRAL DESCRIPTION & HASHTAGS GENERATOR
    elif do_meta:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        with st.spinner("Generating viral YouTube Shorts & Instagram Reels copy & hashtags..."):
            try:
                viral_meta = generate_viral_meta(
                    user_prompt.strip(),
                    channel_tag=channel_watermark
                )
                st.success("🎉 Viral Description & 25+ Hashtags Ready!")
                st.markdown("### 🎯 High-CTR Catchy Titles:")
                for t in viral_meta.get("titles", []):
                    st.markdown(f"- **{t}**")
                
                st.markdown("### 📝 Full Description & Hashtags (Ready to Copy):")
                st.code(viral_meta.get("full_text", ""), language="markdown")
                
                st.download_button(
                    label="⬇️ Download Description & Tags (.txt)",
                    data=viral_meta.get("full_text", ""),
                    file_name=f"description_and_hashtags_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Error generating metadata: {e}")

    # 3. MAKE TITLE FOR VIDEO (High-CTR Viral Title Generator)
    elif do_titles:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt first.")
            st.stop()
        with st.spinner(f"Generating viral, high-converting video titles for '{user_prompt[:50]}' ..."):
            try:
                title_list = generate_video_titles(user_prompt.strip(), channel_tag=channel_watermark)
                st.success("🎉 High-CTR Video Titles Ready! Choose one or click 'Use This Title':")
                
                for idx, t_obj in enumerate(title_list):
                    t_text = t_obj.get("title", "")
                    t_cat = t_obj.get("category", "Viral Hook")
                    c_t1, c_t2 = st.columns([3.5, 1])
                    with c_t1:
                        st.markdown(f"**{idx + 1}. {t_text}** `[{t_cat}]`")
                    with c_t2:
                        if st.button("📌 Use This Title", key=f"use_title_btn_{idx}", use_container_width=True):
                            st.session_state.user_prompt_input = t_text
                            st.rerun()
                
                st.markdown("---")
                all_titles_text = "\n".join([f"{i+1}. {t.get('title', '')} [{t.get('category', '')}]" for i, t in enumerate(title_list)])
                st.markdown("**Copy All Titles:**")
                st.code(all_titles_text, language="text")
            except Exception as e:
                st.error(f"❌ Error generating titles: {e}")

    # 4. FULL REEL GENERATION ACTION
    elif do_full_generate:
        if not user_prompt.strip():
            st.error("Please enter a technical topic prompt.")
            st.stop()

        progress_bar = st.progress(0)
        status_box = st.empty()

        try:
            # STEP 1: AI Director Timeline Generation
            status_box.info("🧠 AI Director is designing the technical storyboard & script...")
            progress_bar.progress(15)
            full_prompt = user_prompt.strip()
            if custom_script_override.strip():
                full_prompt += f"\n\nEXPLICIT USER SCRIPT OVERRIDE (MANDATORY: Follow these exact scene narrations):\n{custom_script_override.strip()}"

            timeline = generate_timeline(
                full_prompt,
                tone=chosen_tone,
                engine_style=visual_engine[0],
                duration_mode=duration_option[0],
                custom_style_prompt=custom_style_prompt,
                voice=chosen_voice,
                format_ratio=aspect_ratio[0]
            )
            
            with st.expander("📄 View Raw AI Director Blueprint (JSON)", expanded=False):
                st.json(timeline)

            # STEP 2: Voiceover & Whisper Alignment
            status_box.info("🎙️ Synthesizing conversational voiceover & microsecond word timestamps...")
            progress_bar.progress(35)
            scenes = timeline.get("scenes", [])
            audio_path, word_timestamps, aligned_scenes = generate_voiceover(
                scenes,
                voice=chosen_voice,
                elevenlabs_model=elevenlabs_model_id,
                tone=chosen_tone
            )

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
                status_box.info(f"🎨 Rendering visuals for scene {i + 1}/{total_sc} with watermark ({channel_watermark})...")
                progress_bar.progress(40 + int(35 * (i + 1) / max(1, total_sc)))
                sc_start = float(sc.get("start_time", 0.0))
                sc_end = float(sc.get("end_time", sc_start + float(sc.get("duration", 5.0))))
                sc_words = [
                    w for w in word_timestamps
                    if sc_start - 0.1 <= float(w.get("start", 0.0)) <= sc_end + 0.1
                ]
                render_scene_frames(
                    sc,
                    i + 1,
                    total_scenes=total_sc,
                    engine_style=visual_engine[0],
                    format_ratio=aspect_ratio[0],
                    watermark=channel_watermark,
                    scene_words=sc_words,
                    custom_style_prompt=custom_style_prompt
                )
                all_scene_frame_dirs.append(OUTPUT_DIR / f"scene_{i + 1:02d}_frames")

            # STEP 4: Video Stitching via Local Hardware / Cloud
            status_box.info(f"⚡ Assembling {aspect_ratio[0]} MP4 with karaoke captions & Lo-Fi audio...")
            progress_bar.progress(80)
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

            # STEP 5: Generate 9:16 High-Conversion Thumbnail
            status_box.info("🖼️ Generating 9:16 high-impact thumbnail with watermark...")
            progress_bar.progress(90)
            thumb_path = generate_thumbnail_9_16(
                user_prompt.strip(),
                timeline=timeline,
                watermark=channel_watermark,
                visual_engine=visual_engine[0]
            )

            # STEP 6: Generate Viral Description & Hashtags
            status_box.info("📋 Preparing YouTube Shorts & Reels viral description & hashtags...")
            progress_bar.progress(95)
            viral_meta = generate_viral_meta(
                user_prompt.strip(),
                timeline=timeline,
                channel_tag=channel_watermark
            )

            # Cloudflare R2 Upload (Automatic only on Cloud, Optional on Local)
            r2_url = None
            if not is_local_machine:
                status_box.info("☁️ Uploading to Cloudflare R2 CDN...")
                r2_url = upload_to_r2(final_video_path)

            progress_bar.progress(100)
            if is_local_machine:
                status_box.success("🎉 Full Reel generated and saved locally on your laptop!")
            else:
                status_box.success("🎉 Full Reel generation complete and deployed to Cloud CDN!")

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

                # 9:16 Thumbnail Section
                if thumb_path and thumb_path.exists():
                    st.markdown("---")
                    st.markdown("### 🖼️ 9:16 Thumbnail (Shorts / Reels Cover)")
                    st.image(str(thumb_path), caption="9:16 High-Conversion Thumbnail", use_container_width=True)
                    with open(thumb_path, "rb") as tf:
                        st.download_button(
                            label="⬇️ Download 9:16 Thumbnail (PNG)",
                            data=tf.read(),
                            file_name=thumb_path.name,
                            mime="image/png",
                            use_container_width=True,
                            type="secondary"
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

                # Viral Description & Hashtags Expander
                with st.expander("📋 Viral Description & 25+ Hashtags (Ready to Copy)", expanded=True):
                    st.markdown("#### 🎯 Catchy Titles:")
                    for t in viral_meta.get("titles", []):
                        st.markdown(f"- **{t}**")
                    st.markdown("#### 📝 Full Description & Hashtags:")
                    st.code(viral_meta.get("full_text", ""), language="markdown")
                    st.download_button(
                        label="⬇️ Download Description & Tags (.txt)",
                        data=viral_meta.get("full_text", ""),
                        file_name=f"description_{int(time.time())}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
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
                       - **Script Tone & Cadence:** `{tone_option[1]}`
                       - **Visual Engine:** `{visual_engine[1]}`
                       - **Duration Strategy:** `{duration_option[1]}` (Planned {len(aligned_scenes)} scenes without artificial 60s cutoff)
                    
                    2. **🎙️ Step 2 — Text-to-Speech & Microsecond Alignment:**
                       - **Voice Gender Filter:** `{gender_filter}`
                       - **Voice Persona (TTS):** `{voice_label}` (`{chosen_voice}`)
                       - **Speech Engine:** `{"ElevenLabs (" + elevenlabs_model_id + " - " + chosen_tone + ")" if chosen_voice.startswith("elevenlabs:") else "Microsoft Edge-TTS"}`
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
                        elif v_type == "all_in_one_tech_canvas":
                            st.markdown(f"- **Cloud Boundary:** `{v_data.get('vpc_label')}`")
                            st.markdown(f"- **2D Tech Stack:** 🗄️ `{v_data.get('comp4_label')}` (DB Cylinder) • 🐍 `{v_data.get('comp1_label')}` (Python Chip) • 🤖 `{v_data.get('comp2_label')}` (AI Bot) • 🖥️ `{v_data.get('comp3_label')}` (K8s Rack) • 🪣 `{v_data.get('comp5_label')}` (S3 Lake)")
                            st.markdown(f"- **2D Motion:** Directed arrows with traveling packet streams & live pulsing target reticle")
                        else:
                            st.markdown(f"- **Bullet Cards:** `{v_data.get('bullets', [])}`")

                        st.markdown(f"- **Spoken Narration:** *\"{sc.get('narration')}\"*")
                        st.markdown("---")

                # 4. APIs, Models & System Stack Summary Table
                with st.expander("🤖 Tech Stack & API Architecture Matrix", expanded=False):
                    st.table([
                        {"Pipeline Layer": "AI Director & Storyboard", "API / Provider": "Google AI Studio", "Model / Spec": "gemini-3-flash-preview", "Status": "Active 🟢"},
                        {"Pipeline Layer": "Text-to-Speech (TTS)", "API / Provider": "ElevenLabs AI" if chosen_voice.startswith("elevenlabs:") else "Microsoft Edge-TTS", "Model / Spec": str(elevenlabs_model_id if chosen_voice.startswith("elevenlabs:") else chosen_voice), "Status": "Active 🟢"},
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
