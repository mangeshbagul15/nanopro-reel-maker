"""
Canonical 2026 Viral Tech Creator Tone, Narrative Cadence & Audio-Visual Sync Registry.

Single source of truth shared across Director, Semantic Router, Voice Synthesis
(Hook-to-Climax Clause Curves), Action Choreography, Virtual Camera, Micro-SFX Mixer,
Palette Engine, Visual Renderers, and Subtitles.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_TONE_KEY = "auto_2026_director"
DEFAULT_CONCRETE_TONE = "whiteboard_analogy"
DUAL_TONE_KEY = "dual_creator_debate"
DUAL_TONE_KEYS = (DUAL_TONE_KEY, "dual_dialogue_curious", "indian_boy_dual_chai")


def is_dual_tone(tone: Optional[str]) -> bool:
    return str(tone or "").strip().lower() in DUAL_TONE_KEYS


def split_text_to_dual_dialogue(text: str, scene_idx: int = 0) -> List[Dict[str, str]]:
    """
    Splits plain scene narration into alternating `female` (curious builder) and `male`
    (mentor/architect) dialogue turns so `dual:` voices ALWAYS alternate between 2 speakers
    even when upstream scene generation or custom scripts omit explicit `dialogue` arrays.
    """
    raw = str(text or "").strip()
    if not raw:
        return []

    # 1. Respect explicit speaker tags if present (e.g. "Female: ... Male: ..." or "Q: ... A: ...")
    tagged = re.findall(
        r"(?:^|\n)\s*(female|male|she|he|questioner|solver|mentor|dost|host|q|a)\s*:\s*([^\n]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if len(tagged) >= 2:
        turns: List[Dict[str, str]] = []
        for spk_raw, seg in tagged:
            s_low = spk_raw.strip().lower()
            spk = "female" if s_low in ("female", "she", "questioner", "q", "curious") else "male"
            clean_seg = seg.strip()
            if clean_seg:
                turns.append({"speaker": spk, "text": clean_seg})
        if turns:
            return turns

    clean = re.sub(
        r"^\s*(?:female|male|she|he|questioner|solver|mentor|dost|host)\s*:\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()
    if not clean:
        return []

    # 2. Split on sentence boundaries cleanly (Latin ., !, ? and Devanagari purna viram ।)
    parts = [p.strip() for p in re.split(r"(?<=[.!?।])\s+", clean) if p and p.strip()]
    if len(parts) == 1 and len(clean) >= 34:
        # Try mid-line conversational delimiters (`? `, `—`, `;`, newlines)
        sub_parts = [p.strip() for p in re.split(r"(?<=\?)\s+|\s*(?:—|--|;|\n)\s*", clean) if p and p.strip()]
        if len(sub_parts) >= 2:
            parts = sub_parts

    if len(parts) >= 2:
        # Merge ultra-tiny trailing punctuation fragments into previous chunk
        merged: List[str] = []
        for p in parts:
            if merged and len(p.split()) < 2 and len(p) < 10:
                merged[-1] = f"{merged[-1]} {p}".strip()
            else:
                merged.append(p)
        if len(merged) >= 2:
            turns = []
            for t_idx, seg in enumerate(merged):
                if "?" in seg and not (turns and turns[-1]["speaker"] == "female"):
                    spk = "female"
                elif t_idx == 0:
                    spk = "female"
                else:
                    spk = "male" if turns[-1]["speaker"] == "female" else "female"
                turns.append({"speaker": spk, "text": seg})
            return turns

    # 3. Single short sentence: alternate voice across consecutive scenes
    return [{"speaker": "female" if (scene_idx % 2 == 0) else "male", "text": clean}]


def ensure_dual_dialogue_for_scene(
    sc: Dict[str, Any],
    title: str,
    idx: int,
    total_scenes: int,
    voice: str = "",
    tone: str = "",
) -> None:
    """
    Normalizes `sc['dialogue']` into >=2 alternating `female` + `male` conversational turns
    whenever dual dialogue mode is requested via tone OR a `dual:` voice persona.
    """
    is_dual_req = (
        is_dual_tone(tone)
        or is_dual_tone(sc.get("scene_tone"))
        or str(voice or "").startswith("dual:")
        or (isinstance(sc.get("dialogue"), list) and len(sc.get("dialogue") or []) >= 1)
    )
    if not is_dual_req:
        return

    if is_dual_tone(tone):
        sc["scene_tone"] = DUAL_TONE_KEY if tone != "dual_dialogue_curious" else "dual_dialogue_curious"

    raw_dlg = sc.get("dialogue")
    clean_dlg: List[Dict[str, str]] = []
    if isinstance(raw_dlg, list):
        for item in raw_dlg:
            if not isinstance(item, dict):
                continue
            spk_raw = str(item.get("speaker") or "male").strip().lower()
            spk = "female" if spk_raw in ("female", "f", "she", "questioner", "curious", "girl", "student") else "male"
            txt = re.sub(
                r"^\s*(?:female|male|she|he|questioner|solver|mentor|dost|host)\s*:\s*",
                "",
                str(item.get("text") or "").strip(),
                flags=re.IGNORECASE,
            )
            if txt:
                clean_dlg.append({"speaker": spk, "text": txt})

    if len(clean_dlg) < 2:
        narr_clean = re.sub(
            r"^\s*(?:female|male|she|he|questioner|solver|mentor)\s*:\s*",
            "",
            str(sc.get("narration") or "").strip(),
            flags=re.IGNORECASE,
        )
        split_turns = split_text_to_dual_dialogue(narr_clean, scene_idx=idx)
        has_both = (
            len(split_turns) >= 2
            and any(t["speaker"] == "female" for t in split_turns)
            and any(t["speaker"] == "male" for t in split_turns)
        )
        if has_both:
            clean_dlg = split_turns
        else:
            v_low = str(voice or "").lower()
            short_t = " ".join(str(title or "this system").strip().split()[:6])
            role_s = str(sc.get("role") or "").lower()
            if "mr-in" in v_low or "marathi" in short_t.lower():
                if role_s == "hook" or idx == 0:
                    q_txt = f"{short_t} मधील मूळ problem नक्की काय आहे आणि हे scale वर कसं वागतं?"
                    a_txt = narr_clean or f"{short_t} चं architecture आणि flow step-by-step समजून घेऊया."
                elif role_s == "cta" or idx >= max(1, total_scenes - 1):
                    q_txt = f"{short_t} साठी production मध्ये कोणता pattern निवडावा?"
                    a_txt = narr_clean or "Throughput, consistency आणि cost नुसार योग्य pattern ठरवला जातो."
                else:
                    q_txt = f"या stage मध्ये {short_t} नक्की कसं काम करतं?"
                    a_txt = narr_clean or f"{short_t} मधील ही layer latency कमी करून data safe ठेवते."
            elif ("en-" in v_low and "|hi" not in v_low and "|hinglish" not in v_low) or (not any(k in v_low for k in ("hi-in", "mr-in", "|hi", "|hinglish"))):
                if role_s == "hook" or idx == 0:
                    q_txt = f"Wait — what actually breaks in {short_t} when traffic spikes?"
                    a_txt = narr_clean or f"Let's trace the exact production flow behind {short_t} step by step."
                elif role_s == "cta" or idx >= max(1, total_scenes - 1):
                    q_txt = f"So which architecture should we ship in production for {short_t}?"
                    a_txt = narr_clean or "Choose based on throughput, latency SLOs, and operational simplicity."
                else:
                    q_txt = f"How do the core components interact at this stage of {short_t}?"
                    a_txt = narr_clean or f"This execution layer preserves consistency while keeping tail latency low."
            else:
                if role_s == "hook" or idx == 0:
                    q_txt = f"{short_t} ka core problem kya hai aur yeh scale par kaise behave karta hai?"
                    a_txt = narr_clean or f"{short_t} mein exact architecture aur data flow step-by-step dekhte hain."
                elif role_s == "cta" or idx >= max(1, total_scenes - 1):
                    q_txt = f"{short_t} mein production architecture finalize karte waqt kaunsa pattern choose karna chahiye?"
                    a_txt = narr_clean or "Workload ke throughput, ACID guarantees aur cost trade-offs ke basis par pattern decide hota hai."
                else:
                    q_txt = f"{short_t} ke internal pipeline mein key components kaise interact karte hain?"
                    a_txt = narr_clean or f"{short_t} ki execution layer state consistency aur latency maintain karti hai."
            clean_dlg = [
                {"speaker": "female", "text": q_txt},
                {"speaker": "male", "text": a_txt},
            ]

    sc["dialogue"] = clean_dlg
    sc["narration"] = " ".join(d["text"] for d in clean_dlg).strip()


TONE_PROFILES: Dict[str, Dict[str, Any]] = {
    "auto_2026_director": {
        "label": "⚡ Dynamic 2026 AI Auto-Mix (2s Hook -> War Story -> Code -> Verdict) [Recommended]",
        "directive": (
            "DYNAMIC 2026 VIRAL TECH DIRECTOR (PER-SCENE TONE & PATTERN-INTERRUPT CHOREOGRAPHY):\n"
            "Shift narrative emotion, vocal cadence, and visual archetype cleanly per scene role:\n"
            "- Scene 1 (`hook`): Use `myth_buster_contrarian` OR `war_story_postmortem` with a sharp 2-second scroll-stopper opening (myth shatter, outage timestamp, or scale surprise).\n"
            "- Problem / Crash beat: Use `war_story_postmortem` (crisis metrics + `disrupt_shake`).\n"
            "- Concept / Mechanism: Use `whiteboard_analogy` (intuitive everyday analogy + clean architecture flow) OR `live_debug_pair` (exact line-by-line bug/SQL/code).\n"
            "- Trade-off / Evaluation: Use `cage_match_vs` (rapid criteria rounds + concrete winner metrics).\n"
            "- Scale Case Study / Closing Verdict: Use `bigtech_reverse_engineer` or `release_radar_tldr`.\n"
            "Set `scene_tone` on EVERY scene explicitly from these 2026 profiles!"
        ),
        "elevenlabs": {"stability": 0.42, "similarity_boost": 0.84, "style": 0.44, "use_speaker_boost": True},
        "edge_base": {"rate": "+5%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+8%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "-1Hz"},
        "pause_sec": "0.24",
        "atempo": "1.03",
        "subtitle_tag": r"\c&H002BF6FF&\fscx112\fscy112",
        "subtitle_name": "electric_2026_pop",
        "preferred_world": "obsidian_studio",
        "accent_key": "cyan",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.94,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "excalidraw_sketch_board", "ide_split_workbench", "bento_apple_keynote"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.09,
    },
    "war_story_postmortem": {
        "label": "🚨 3AM Production War Story (Outage Thriller, Root-Cause & Green Recovery)",
        "directive": (
            "SCRIPT TONE (2026 3AM PRODUCTION WAR STORY / POST-MORTEM THRILLER):\n"
            "Start immediately with a cold-open incident moment (e.g. 'Friday 11:45 PM... one missing timeout took 40TB offline'), "
            "escalate through cascading production failures (`502`, connection exhaustion, retry storms), isolate the exact root cause, "
            "and resolve with the verified architectural fix. Keep every word gripping and factual — zero cheesy filler."
        ),
        "elevenlabs": {"stability": 0.34, "similarity_boost": 0.84, "style": 0.48, "use_speaker_boost": True},
        "edge_base": {"rate": "+1%", "pitch": "-2Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "-2%", "pitch": "-3Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "+1Hz"},
        "pause_sec": "0.30",
        "atempo": "1.00",
        "subtitle_tag": r"\c&H005E3FF4&\fscx112\fscy112",
        "subtitle_name": "crimson_incident",
        "preferred_world": "crimson_studio",
        "accent_key": "rose",
        "animator_theme": "crimson_alert",
        "reveal_power": 1.04,
        "motion_profile": "disrupt_shake",
        "preferred_layouts": ("live_sre_observability_console", "alert_diagram", "dr_active_active_failover", "perf_waterfall_db_lock", "incident_thundering_herd"),
        "default_sfx": "alert_ping",
        "camera_zoom_bias": 1.11,
    },
    "myth_buster_contrarian": {
        "label": "💥 Contrarian Myth-Buster (2s Pattern Interrupt, Strikethrough & Real Benchmarks)",
        "directive": (
            "SCRIPT TONE (2026 CONTRARIAN MYTH-BUSTER — PATTERN INTERRUPT):\n"
            "Open Scene 1 in the very first 2 seconds by calling out a widespread engineering mistake ('90% teams still blindly do X — here is why it explodes at scale'), "
            "compare Myth vs Reality using concrete benchmarks (`p99`, cost, QPS, memory), and deliver a razor-sharp rule of thumb. "
            "Punchy, direct, slightly provocative truth backed by hard numbers."
        ),
        "elevenlabs": {"stability": 0.40, "similarity_boost": 0.82, "style": 0.42, "use_speaker_boost": True},
        "edge_base": {"rate": "+7%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+10%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+6%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+4%", "pitch": "-1Hz"},
        "pause_sec": "0.20",
        "atempo": "1.05",
        "subtitle_tag": r"\c&H0024BFFF&\fscx114\fscy114",
        "subtitle_name": "amber_myth_snap",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "gold_purple",
        "reveal_power": 0.90,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "benchmark_3d", "p99_tail_cdf_curve", "split_comparison", "live_benchmark_race_track"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.10,
    },
    "live_debug_pair": {
        "label": "🧪 Live Code & Debug Pair-Programmer (Dry Wit, Line-by-Line Bug Catch & Fix)",
        "directive": (
            "SCRIPT TONE (2026 LIVE CODE / DEBUG PAIR-PROGRAMMER — DRY WIT, ZERO SCREAMING):\n"
            "Sound like a calm, razor-sharp senior developer looking at an IDE screen with dry understated wit ('Look closely at line 4... yep, that innocent loop just triggered 1,000 SQL roundtrips'). "
            "Pinpoint the exact code/query flaw, show the 3-line fix or EXPLAIN bottleneck, and state the measured gain cleanly."
        ),
        "elevenlabs": {"stability": 0.58, "similarity_boost": 0.85, "style": 0.24, "use_speaker_boost": True},
        "edge_base": {"rate": "+3%", "pitch": "-1Hz"},
        "hook_curve": {"rate": "+5%", "pitch": "+0Hz"},
        "mid_curve": {"rate": "+2%", "pitch": "-1Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "pause_sec": "0.26",
        "atempo": "1.02",
        "subtitle_tag": r"\c&H0099D334&\fscx108\fscy108",
        "subtitle_name": "emerald_ide_clean",
        "preferred_world": "navy_studio",
        "accent_key": "emerald",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.96,
        "motion_profile": "flow_slide",
        "preferred_layouts": ("ide_split_workbench", "code_diff_split", "code_terminal", "browser_devtools_studio", "python_stack_heap_live"),
        "default_sfx": "key_tick",
        "camera_zoom_bias": 1.07,
    },
    "whiteboard_analogy": {
        "label": "✏️ 10-Sec Whiteboard Analogy (Everyday Intuition -> Sketch Flow & Internals)",
        "directive": (
            "SCRIPT TONE (2026 WHITEBOARD ANALOGY & INTUITION BUILDER):\n"
            "Unlock difficult distributed systems or database internals using a crisp 10-second real-world mental model first "
            "(e.g. restaurant order tickets, highway toll lanes, library index cards), then immediately map every piece of the analogy "
            "to real engineering layers (`WAL`, `Consumer Group`, `Micro-Partition`, `Consistent Hash`) with warm clarity."
        ),
        "elevenlabs": {"stability": 0.42, "similarity_boost": 0.84, "style": 0.40, "use_speaker_boost": True},
        "edge_base": {"rate": "+3%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+2%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "+0Hz"},
        "pause_sec": "0.28",
        "atempo": "1.02",
        "subtitle_tag": r"\c&H0099D334&\fscx110\fscy110",
        "subtitle_name": "whiteboard_mint",
        "preferred_world": "studio_white",
        "accent_key": "emerald",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.97,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("excalidraw_sketch_board", "iso_architecture", "sql_live_join_venn_rows", "snowflake_micro_partition_pruner", "medallion_lakehouse"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.08,
    },
    "cage_match_vs": {
        "label": "⚔️ Rapid-Fire Cage Match (`A vs B` in 45s — Scored Criteria & Verdict)",
        "directive": (
            "SCRIPT TONE (2026 RAPID-FIRE A vs B CAGE MATCH):\n"
            "Pit the two technologies/patterns head-to-head across 4 concrete battle rounds (Latency, Cost/Ops, Failure Mode, Scale Fit). "
            "Keep transitions rapid and score each round decisively ('Round 1 goes to X because...', 'In heavy writes, Y wins cleanly'). "
            "Close with an unmistakable decision matrix."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.80, "style": 0.36, "use_speaker_boost": True},
        "edge_base": {"rate": "+8%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+10%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+7%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+4%", "pitch": "-1Hz"},
        "pause_sec": "0.18",
        "atempo": "1.06",
        "subtitle_tag": r"\c&H002BF6FF&\fscx114\fscy114",
        "subtitle_name": "arena_yellow_snap",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.89,
        "motion_profile": "split_collide",
        "preferred_layouts": ("split_comparison", "iso_comparison", "compare_sync_vs_async", "sql_live_join_venn_rows", "benchmark_3d"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.07,
    },
    "release_radar_tldr": {
        "label": "📰 2026 Release & Paper Radar (What Dropped, Why It Matters & Upgrade Verdict)",
        "directive": (
            "SCRIPT TONE (2026 TECH RELEASE / PAPER RADAR TL;DR):\n"
            "Deliver fast, signal-dense engineering news synthesis structured cleanly in 3 beats: "
            "1) What just changed architecturally (no marketing fluff), 2) Real performance/cost delta in production, "
            "3) Concrete verdict — who upgrades today vs who waits."
        ),
        "elevenlabs": {"stability": 0.46, "similarity_boost": 0.82, "style": 0.32, "use_speaker_boost": True},
        "edge_base": {"rate": "+6%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+9%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+5%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "pause_sec": "0.20",
        "atempo": "1.05",
        "subtitle_tag": r"\c&H00F8BD38&\fscx110\fscy110",
        "subtitle_name": "radar_cyan_crisp",
        "preferred_world": "sapphire_3d",
        "accent_key": "cyan",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.92,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("bento_apple_keynote", "multi_agent_swimlane_trace", "neural_forward_backprop_flow", "ai_thinking_tool_trace", "notebook_interactive_cell"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.08,
    },
    "bigtech_reverse_engineer": {
        "label": "🕵️‍♂️ Big-Tech Reverse Engineer (How Hyperscalers Hit 500M+ Scale Under 1s)",
        "directive": (
            "SCRIPT TONE (2026 BIG-TECH REVERSE ENGINEER — ARCHITECTURAL CASE STUDY):\n"
            "Open with an astonishing verified scale constraint (millions of TPS, multi-region compliance, sub-10ms P99), "
            "then trace the exact physical hop-by-hop blueprint (edge POP -> async partition -> in-memory compute -> ledger/storage). "
            "Sound like a Principal Systems Architect dissecting real production internals."
        ),
        "elevenlabs": {"stability": 0.64, "similarity_boost": 0.86, "style": 0.18, "use_speaker_boost": True},
        "edge_base": {"rate": "+2%", "pitch": "-2Hz"},
        "hook_curve": {"rate": "+5%", "pitch": "+0Hz"},
        "mid_curve": {"rate": "+2%", "pitch": "-2Hz"},
        "verdict_curve": {"rate": "+1%", "pitch": "-2Hz"},
        "pause_sec": "0.26",
        "atempo": "1.01",
        "subtitle_tag": r"\c&H00F8BD38&\fscx106\fscy106",
        "subtitle_name": "principal_arch_cyan",
        "preferred_world": "navy_studio",
        "accent_key": "cyan",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.98,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("banking_ledger_settlement_rails", "cloud_infra_zone_builder", "geo_world_packet_arcs", "topo_kafka_isr_quorum_dlq", "architecture_flow"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.08,
    },
    "dual_creator_debate": {
        "label": "🎙️ Dual Voice Tech Debate (Builder Tough Question • Architect Counter-Proof)",
        "directive": (
            "DUAL VOICE 2026 BUILDER vs ARCHITECT DEBATE (ZERO FILLER):\n"
            "Two sharp practitioners debate the exact architecture live:\n"
            "- FEMALE (`\"speaker\": \"female\"`): Challenges production assumptions directly (tail latency, lock contention, cost spikes, edge failures).\n"
            "- MALE (`\"speaker\": \"male\"`): Counters with concrete mechanisms, storage layouts, and verified trade-offs.\n"
            "RULES: Populate `\"dialogue\"` (2-4 crisp turns `female` <-> `male`) AND concatenate cleanly into `\"narration\"`. Zero canned catchphrases."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.84, "style": 0.42, "use_speaker_boost": True},
        "edge_base": {"rate": "+4%", "pitch": "+0Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "-1Hz"},
        "pause_sec": "0.24",
        "atempo": "1.03",
        "subtitle_tag": r"\c&H00F8BD38&\fscx110\fscy110",
        "subtitle_name": "dual_debate_cyan",
        "preferred_world": "sapphire_3d",
        "accent_key": "cyan",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.96,
        "motion_profile": "split_collide",
        "preferred_layouts": ("chat_thread_ai", "mobile_app_mockup", "excalidraw_sketch_board", "iso_comparison", "hero_hook"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.08,
    },
    "indian_boy_heartfelt": {
        "label": "🇮🇳👦 Dil Se Indian Boy (Cute, Sweet, Smart & Chapal • Calm Mastery + Classic Finisher)",
        "directive": (
            "SCRIPT TONE (INDIAN HEARTFELT SMART BOY — CUTE, SWEET, CHARMING, CHAPAL & CLASSIC FINISHER):\n"
            "Write in authentic spoken **Indian Hindi / Hinglish** (the natural sweet cadence of a young, charming Indian creator — e.g. 'अरे एक सेकंड रुको...', 'सोचो ज़रा...', 'सीधी सी बात है यार...', 'दिल खुश हो जाएगा देखकर!').\n"
            "VIBE & PERSONALITY: Cute, sweet, slightly playful/romantic warmth, fresh village-meets-city confidence, calm deep tech knowledge, smart & nimble (*chapal*), ZERO extra filler words.\n"
            "PACING & PAUSES: Start with a smiling curious hook, insert crisp `...` breath pauses before revealing the core mechanism so visuals are 100% easy to absorb, keep sentences punchy (10-14 words), and end the final scene with ONE unforgettable, heart-touching classic finisher line (`मन में घर कर जाने वाला closer`)."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.85, "style": 0.44, "use_speaker_boost": True},
        "edge_base": {"rate": "+4%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+3%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+1%", "pitch": "+0Hz"},
        "pause_sec": "0.28",
        "tail_hold_sec": 0.44,
        "use_pause_cadence": True,
        "visual_pace_lead": 1.15,
        "atempo": "1.01",
        "subtitle_tag": r"\c&H002BF6FF&\fscx112\fscy112",
        "subtitle_name": "indian_boy_warm_cyan",
        "preferred_world": "sapphire_3d",
        "accent_key": "cyan",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.94,
        "motion_profile": "flow_slide",
        "preferred_layouts": ("excalidraw_sketch_board", "architecture_flow", "ide_split_workbench", "bento_apple_keynote"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.07,
    },
    "indian_boy_village_fresh": {
        "label": "🌾🇮🇳 Gaon Se Tech Tak (Desi Village Boy Freshness, Sweet Smile & Classic Intuition)",
        "directive": (
            "SCRIPT TONE (FRESH INDIAN VILLAGE TECH BOY — SWEET INNOCENCE + SHARP GENIUS):\n"
            "Speak in warm, fresh Indian Hindi/Hinglish rooted in relatable everyday desi analogies (chai tapri, gaon ka post-office, train ticket line, paani ki tanki) mapped accurately to real system internals.\n"
            "VIBE: Happy, grounded, lovable, crisp `...` breath pauses between intuition and technical proof, ZERO unnecessary words, ending on a classic smiling closer that stays in the viewer's heart."
        ),
        "elevenlabs": {"stability": 0.46, "similarity_boost": 0.85, "style": 0.42, "use_speaker_boost": True},
        "edge_base": {"rate": "+3%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+5%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+2%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+0%", "pitch": "+0Hz"},
        "pause_sec": "0.30",
        "tail_hold_sec": 0.46,
        "use_pause_cadence": True,
        "visual_pace_lead": 1.16,
        "atempo": "1.00",
        "subtitle_tag": r"\c&H0099D334&\fscx110\fscy110",
        "subtitle_name": "indian_village_mint",
        "preferred_world": "obsidian_studio",
        "accent_key": "emerald",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.95,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("excalidraw_sketch_board", "iso_architecture", "medallion_lakehouse"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.06,
    },
    "indian_boy_city_charm": {
        "label": "🏙️🇮🇳 Modern City Boy (Smart Chapal Hinglish, Fast Hook & Sweet Classic Closer)",
        "directive": (
            "SCRIPT TONE (MODERN INDIAN CITY TECH BOY — SMART, CHAPAL, ATTRACTIVE & CRISP):\n"
            "Fast-minded modern Indian city boy vibe — lively Hinglish, cute magnetic wit, zero rambling ('सीधा point पे आते हैं...', 'बस 10 सेकंड में तस्वीर साफ!'), crisp `...` pauses on key numbers/architecture steps, ending with a razor-sharp classic finisher line."
        ),
        "elevenlabs": {"stability": 0.42, "similarity_boost": 0.84, "style": 0.44, "use_speaker_boost": True},
        "edge_base": {"rate": "+6%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+8%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+5%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "+0Hz"},
        "pause_sec": "0.24",
        "tail_hold_sec": 0.38,
        "use_pause_cadence": True,
        "visual_pace_lead": 1.12,
        "atempo": "1.02",
        "subtitle_tag": r"\c&H0024BFFF&\fscx112\fscy112",
        "subtitle_name": "indian_city_amber",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "gold_purple",
        "reveal_power": 0.92,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "ide_split_workbench", "bento_apple_keynote", "split_comparison"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.08,
    },
    "indian_boy_calm_classic": {
        "label": "🎓🇮🇳 Calm Classic Tech Boy (Poised Indian Hindi, Crystal Visual Hold & Heartfelt Finisher)",
        "directive": (
            "SCRIPT TONE (CALM CLASSIC INDIAN TECH STORYTELLER — PURE PERFECTION):\n"
            "Calm, poetic clarity in natural spoken Indian Hindi/Hinglish. Zero rush, zero extra words, clean `...` pauses after every key insight so diagrams breathe on screen, concluding with a timeless, memorable finisher."
        ),
        "elevenlabs": {"stability": 0.56, "similarity_boost": 0.86, "style": 0.30, "use_speaker_boost": True},
        "edge_base": {"rate": "+2%", "pitch": "+0Hz"},
        "hook_curve": {"rate": "+4%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+2%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+0%", "pitch": "-1Hz"},
        "pause_sec": "0.32",
        "tail_hold_sec": 0.48,
        "use_pause_cadence": True,
        "visual_pace_lead": 1.18,
        "atempo": "1.00",
        "subtitle_tag": r"\c&H00F8BD38&\fscx108\fscy108",
        "subtitle_name": "indian_calm_cyan",
        "preferred_world": "navy_studio",
        "accent_key": "cyan",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.96,
        "motion_profile": "flow_slide",
        "preferred_layouts": ("architecture_flow", "excalidraw_sketch_board", "all_in_one_tech_canvas"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.06,
    },
    "indian_boy_dual_chai": {
        "label": "☕🇮🇳 Chai-Tapri Tech Jodi (Dual Voice: Sweet Curious Q + Smart Indian Boy Mentor A)",
        "directive": (
            "DUAL VOICE INDIAN CHAI-TAPRI DIALOGUE (CUTE CURIOUS FRIEND + SMART CALM INDIAN BOY MENTOR):\n"
            "- FEMALE (`\"speaker\": \"female\"`): Asks relatable, sharp curiosity questions with smiling Indian warmth.\n"
            "- MALE (`\"speaker\": \"male\"`): Cute, calm, smart & chapal Indian boy explains cleanly in Hinglish with crisp `...` pauses, zero extra words, and a classic memorable finisher.\n"
            "RULES: Populate `\"dialogue\"` (2-4 crisp turns `female` <-> `male`) AND concatenate cleanly into `\"narration\"`."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.84, "style": 0.42, "use_speaker_boost": True},
        "edge_base": {"rate": "+4%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+1%", "pitch": "+0Hz"},
        "pause_sec": "0.26",
        "tail_hold_sec": 0.42,
        "use_pause_cadence": True,
        "visual_pace_lead": 1.15,
        "atempo": "1.01",
        "subtitle_tag": r"\c&H00F8BD38&\fscx110\fscy110",
        "subtitle_name": "indian_dual_chai",
        "preferred_world": "sapphire_3d",
        "accent_key": "cyan",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.95,
        "motion_profile": "flow_slide",
        "preferred_layouts": ("chat_thread_ai", "excalidraw_sketch_board", "mobile_app_mockup", "iso_comparison"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.07,
    },
    # ------------------------------------------------------------------
    # Classic Legacy Studio Tones (Restored Alongside 2026 Profiles)
    # ------------------------------------------------------------------
    "dual_dialogue_curious": {
        "label": "🗣️ Dual Voice Hinglish Dialogue (Focused Technical Questions • Direct Architecture Answers)",
        "directive": (
            "Two speakers discuss the exact technical topic directly with zero scripted catchphrases, zero filler pleasantries, and zero emotional fluff:\n"
            "- FEMALE (`\"speaker\": \"female\"`): Raises sharp, topic-specific architectural or engineering questions (e.g., comparing storage models, failure modes, throughput bottlenecks).\n"
            "- MALE (`\"speaker\": \"male\"`): Gives clear, accurate, step-by-step technical explanations, concrete internals, and trade-offs directly answering her question.\n"
            "RULES: Include `\"dialogue\"` (2-4 alternating turns `female` -> `male`) and set `\"narration\"` to their clean concatenation. Keep every word strictly focused on technical substance."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.84, "style": 0.42, "use_speaker_boost": True},
        "edge_base": {"rate": "+3%", "pitch": "+0Hz"},
        "hook_curve": {"rate": "+5%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "-1Hz"},
        "pause_sec": "0.22",
        "atempo": "1.02",
        "subtitle_tag": r"\c&H00F8BD38&\fscx110\fscy110",
        "subtitle_name": "classic_dual_cyan",
        "preferred_world": "sapphire_3d",
        "accent_key": "cyan",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.96,
        "motion_profile": "split_collide",
        "preferred_layouts": ("chat_thread_ai", "mobile_app_mockup", "excalidraw_sketch_board", "iso_comparison"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.07,
    },
    "peaceful_human_guide": {
        "label": "🧘 Calm Technical Guide (Steady Hinglish Pace, Clear Problem Breakdown & Tight Visual Sync)",
        "directive": (
            "CALM, CLEAR TECHNICAL EXPLAINER (PURE CONTENT, ZERO FLUFF): "
            "Deliver calm, crystal-clear technical explanations in clean Hinglish with crisp English engineering nouns. "
            "Focus 100% on the topic's actual architecture, mechanics, and trade-offs — NEVER insert filler catchphrases."
        ),
        "elevenlabs": {"stability": 0.56, "similarity_boost": 0.84, "style": 0.24, "use_speaker_boost": True},
        "edge_base": {"rate": "+3%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+4%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "+0Hz"},
        "pause_sec": "0.26",
        "atempo": "1.01",
        "subtitle_tag": r"\c&H0099D334&\fscx108\fscy108",
        "subtitle_name": "classic_calm_mint",
        "preferred_world": "navy_studio",
        "accent_key": "emerald",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.97,
        "motion_profile": "flow_slide",
        "preferred_layouts": ("architecture_flow", "excalidraw_sketch_board", "iso_architecture"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.06,
    },
    "trusted_dost_guide": {
        "label": "🤝 Clear Dost & Architect Guide (Direct Hinglish Explanation, Focused Q&A & Clean Visual Sync)",
        "directive": (
            "FRIENDLY TECHNICAL EXPLAINER (PURE CONTENT, ZERO FLUFF): "
            "Warm, approachable Hinglish peer voice explaining the topic's real internals, architecture flow, and trade-offs directly."
        ),
        "elevenlabs": {"stability": 0.48, "similarity_boost": 0.82, "style": 0.34, "use_speaker_boost": True},
        "edge_base": {"rate": "+4%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "pause_sec": "0.24",
        "atempo": "1.02",
        "subtitle_tag": r"\c&H00F8BD38&\fscx110\fscy110",
        "subtitle_name": "classic_dost_cyan",
        "preferred_world": "sapphire_3d",
        "accent_key": "cyan",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.95,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "architecture_flow", "split_comparison"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.07,
    },
    "purposeful_hinglish_mentor": {
        "label": "🎯 Purposeful Hinglish Mentor (Crystal-Clear Male Mentor, Production Depth, Edge Cases & Visual Sync)",
        "directive": (
            "PURPOSEFUL HINGLISH MENTOR (CLEAR MECHANICS + EDGE CASES, ZERO FLUFF): "
            "Warm, authoritative Hinglish technical mentor explaining step-by-step system mechanics, real trade-offs, and production edge cases directly from Scene 1."
        ),
        "elevenlabs": {"stability": 0.52, "similarity_boost": 0.84, "style": 0.30, "use_speaker_boost": True},
        "edge_base": {"rate": "+5%", "pitch": "-1Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+0Hz"},
        "mid_curve": {"rate": "+5%", "pitch": "-1Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "-1Hz"},
        "pause_sec": "0.24",
        "atempo": "1.03",
        "subtitle_tag": r"\c&H0024BFFF&\fscx110\fscy110",
        "subtitle_name": "classic_mentor_amber",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.95,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("architecture_flow", "all_in_one_tech_canvas", "bento_apple_keynote"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.08,
    },
    "senior_hinglish_mentor": {
        "label": "🧑‍💻 Senior Hinglish Mentor (Experienced Architect Voice, System Trade-offs & Progressive Visuals)",
        "directive": (
            "SENIOR HINGLISH MENTOR & ARCHITECTURAL BREAKDOWN (PURE CONTENT): "
            "Crisp senior-engineer Hinglish explanation covering real problem statement, internal architecture stages, engineering trade-offs, and practical production takeaway."
        ),
        "elevenlabs": {"stability": 0.56, "similarity_boost": 0.85, "style": 0.24, "use_speaker_boost": True},
        "edge_base": {"rate": "+5%", "pitch": "+0Hz"},
        "hook_curve": {"rate": "+6%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "-1Hz"},
        "pause_sec": "0.24",
        "atempo": "1.03",
        "subtitle_tag": r"\c&H00F8BD38&\fscx110\fscy110",
        "subtitle_name": "classic_senior_cyan",
        "preferred_world": "navy_studio",
        "accent_key": "cyan",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.96,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("cloud_infra_zone_builder", "architecture_flow", "split_comparison"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.08,
    },
    "youth_friend_turbo": {
        "label": "🚀 Energetic Tech Explainer (Crisp Natural Voice, Fast Concept Breakdown & Synced Visuals)",
        "directive": (
            "LIVELY TECHNICAL EXPLAINER (CLEAR & COMPLETE, ZERO FILLER): "
            "Natural, upbeat Hinglish pacing with complete 12-16 word technical sentences covering concrete architecture details and trade-offs cleanly synced with visuals."
        ),
        "elevenlabs": {"stability": 0.42, "similarity_boost": 0.82, "style": 0.40, "use_speaker_boost": True},
        "edge_base": {"rate": "+6%", "pitch": "+2Hz"},
        "hook_curve": {"rate": "+8%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+6%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "pause_sec": "0.20",
        "atempo": "1.04",
        "subtitle_tag": r"\c&H002BF6FF&\fscx112\fscy112",
        "subtitle_name": "classic_turbo_pop",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.91,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "benchmark_3d", "bento_apple_keynote"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.09,
    },
    "mentor_storyteller": {
        "label": "🌟 Structured Tech Educator (Simple Words, Natural Pauses & Step-by-Step Clarity) [Ultra Pro]",
        "directive": (
            "INTUITIVE TECHNICAL STORYTELLER (PURE CONCEPT CLARITY): "
            "Explain complex systems in plain language with relatable real-world engineering intuition and step-by-step architectural clarity."
        ),
        "elevenlabs": {"stability": 0.36, "similarity_boost": 0.82, "style": 0.46, "use_speaker_boost": True},
        "edge_base": {"rate": "+3%", "pitch": "+2Hz"},
        "hook_curve": {"rate": "+5%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+3%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "+0Hz"},
        "pause_sec": "0.26",
        "atempo": "1.02",
        "subtitle_tag": r"\c&H0099D334&\fscx110\fscy110",
        "subtitle_name": "classic_storyteller_mint",
        "preferred_world": "studio_white",
        "accent_key": "emerald",
        "animator_theme": "emerald_matrix",
        "reveal_power": 0.97,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("excalidraw_sketch_board", "iso_architecture", "medallion_lakehouse"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.07,
    },
    "auto_dynamic": {
        "label": "⚡ Dynamic / Auto Classic (AI Adapts Voice Pace & Visual Cadence Per Technical Scene)",
        "directive": (
            "DYNAMIC PER-SCENE TONE & VOICE CHOREOGRAPHY: "
            "Dynamically shift emotional tone & pacing across the video storyboard: "
            "Hook/Intro -> energetic (`fireship_octane` or `interview_prep`), Problem/Mistake -> suspenseful (`dramatic_performance`), "
            "Architecture/Mechanism -> authoritative (`staff_engineer`), Closing Summary/CTA -> warm (`conversational_casual`)."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.83, "style": 0.36, "use_speaker_boost": True},
        "edge_base": {"rate": "+4%", "pitch": "+0Hz"},
        "hook_curve": {"rate": "+7%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+2%", "pitch": "-1Hz"},
        "pause_sec": "0.24",
        "atempo": "1.03",
        "subtitle_tag": r"\c&H002BF6FF&\fscx112\fscy112",
        "subtitle_name": "classic_auto_pop",
        "preferred_world": "obsidian_studio",
        "accent_key": "cyan",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.94,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "architecture_flow", "split_comparison"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.08,
    },
    "fireship_octane": {
        "label": "🔥 High-Tempo Code Breakdown (Rapid Technical Pacing & High-Contrast Visuals)",
        "directive": (
            "SCRIPT TONE & VISUAL SYNC MANDATE: Write in high-octane Fireship style. "
            "Punchy sentences, witty comparisons, rapid pacing, zero corporate throat-clearing. "
            "Prefer fast kinetic visuals (`kinetic_statement`, `split_comparison`, `code_terminal`, `hero_hook`)."
        ),
        "elevenlabs": {"stability": 0.44, "similarity_boost": 0.78, "style": 0.25, "use_speaker_boost": True},
        "edge_base": {"rate": "+7%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+9%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+7%", "pitch": "+1Hz"},
        "verdict_curve": {"rate": "+5%", "pitch": "+0Hz"},
        "pause_sec": "0.18",
        "atempo": "1.05",
        "subtitle_tag": r"\c&H0024BFFF&\fscx114\fscy114",
        "subtitle_name": "classic_fireship_snap",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "gold_purple",
        "reveal_power": 0.89,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("code_terminal", "split_comparison", "benchmark_3d"),
        "default_sfx": "key_tick",
        "camera_zoom_bias": 1.10,
    },
    "dramatic_performance": {
        "label": "🎭 Deep Focus Production Breakdown (Measured Pacing, Incident Context & Deliberate Pauses)",
        "directive": (
            "SCRIPT TONE & VISUAL SYNC MANDATE: Emotionally rich, theatrical, dramatic performance. "
            "Build tension and suspense around the production problem, incident context, and root-cause reveal."
        ),
        "elevenlabs": {"stability": 0.34, "similarity_boost": 0.82, "style": 0.42, "use_speaker_boost": True},
        "edge_base": {"rate": "-2%", "pitch": "-3Hz"},
        "hook_curve": {"rate": "+1%", "pitch": "-1Hz"},
        "mid_curve": {"rate": "-2%", "pitch": "-3Hz"},
        "verdict_curve": {"rate": "+1%", "pitch": "-2Hz"},
        "pause_sec": "0.28",
        "atempo": "0.99",
        "subtitle_tag": r"\c&H005E3FF4&\fscx112\fscy112",
        "subtitle_name": "classic_dramatic_crimson",
        "preferred_world": "crimson_studio",
        "accent_key": "rose",
        "animator_theme": "crimson_alert",
        "reveal_power": 1.04,
        "motion_profile": "disrupt_shake",
        "preferred_layouts": ("alert_diagram", "live_sre_observability_console", "dr_active_active_failover"),
        "default_sfx": "alert_ping",
        "camera_zoom_bias": 1.11,
    },
    "staff_engineer": {
        "label": "🧠 Senior Staff Engineer Authority (Calm Deep Voice & Architectural Blueprint)",
        "directive": (
            "SCRIPT TONE & VISUAL SYNC MANDATE: Senior Staff Engineer / ByteByteGo masterclass style. "
            "Calm, deeply authoritative, mature technical confidence focusing on real-world trade-offs and internals."
        ),
        "elevenlabs": {"stability": 0.68, "similarity_boost": 0.85, "style": 0.10, "use_speaker_boost": True},
        "edge_base": {"rate": "+2%", "pitch": "-2Hz"},
        "hook_curve": {"rate": "+4%", "pitch": "-1Hz"},
        "mid_curve": {"rate": "+2%", "pitch": "-2Hz"},
        "verdict_curve": {"rate": "+1%", "pitch": "-2Hz"},
        "pause_sec": "0.26",
        "atempo": "1.01",
        "subtitle_tag": r"\c&H00F8BD38&\fscx106\fscy106",
        "subtitle_name": "classic_staff_cyan",
        "preferred_world": "navy_studio",
        "accent_key": "cyan",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.98,
        "motion_profile": "stack_snap",
        "preferred_layouts": ("architecture_flow", "all_in_one_tech_canvas", "data_structure_memory"),
        "default_sfx": "whoosh",
        "camera_zoom_bias": 1.07,
    },
    "conversational_casual": {
        "label": "☕ Conversational Tech Walkthrough (Natural Direct Cadence & Clear System Flow)",
        "directive": (
            "SCRIPT TONE & VISUAL SYNC MANDATE: Conversational, warm, and friendly, like explaining architecture cleanly over coffee. "
            "Natural direct phrasing without stiff jargon or hype."
        ),
        "elevenlabs": {"stability": 0.52, "similarity_boost": 0.78, "style": 0.16, "use_speaker_boost": True},
        "edge_base": {"rate": "+4%", "pitch": "+0Hz"},
        "hook_curve": {"rate": "+5%", "pitch": "+1Hz"},
        "mid_curve": {"rate": "+4%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "+0Hz"},
        "pause_sec": "0.24",
        "atempo": "1.02",
        "subtitle_tag": r"\c&H0099D334&\fscx108\fscy108",
        "subtitle_name": "classic_casual_mint",
        "preferred_world": "sapphire_3d",
        "accent_key": "emerald",
        "animator_theme": "cyber_cyan",
        "reveal_power": 0.96,
        "motion_profile": "flow_slide",
        "preferred_layouts": ("architecture_flow", "bento_apple_keynote", "excalidraw_sketch_board"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.06,
    },
    "interview_prep": {
        "label": "⚡ System Design Interview Prep (Core Bottlenecks, Architecture Choices & Trade-offs)",
        "directive": (
            "SCRIPT TONE & VISUAL SYNC MANDATE: High-signal System Design Interview Prep. "
            "Present the exact interviewer constraint, common naive pitfall, scaling bottlenecks, concrete architecture choice, and trade-offs."
        ),
        "elevenlabs": {"stability": 0.56, "similarity_boost": 0.82, "style": 0.20, "use_speaker_boost": True},
        "edge_base": {"rate": "+5%", "pitch": "+1Hz"},
        "hook_curve": {"rate": "+7%", "pitch": "+2Hz"},
        "mid_curve": {"rate": "+5%", "pitch": "+0Hz"},
        "verdict_curve": {"rate": "+3%", "pitch": "-1Hz"},
        "pause_sec": "0.22",
        "atempo": "1.03",
        "subtitle_tag": r"\c&H0024BFFF&\fscx112\fscy112",
        "subtitle_name": "classic_interview_amber",
        "preferred_world": "obsidian_studio",
        "accent_key": "amber",
        "animator_theme": "indigo_cyan",
        "reveal_power": 0.93,
        "motion_profile": "pop_bounce",
        "preferred_layouts": ("hero_hook", "split_comparison", "architecture_flow"),
        "default_sfx": "pop_snap",
        "camera_zoom_bias": 1.09,
    },
}


UI_TONE_OPTIONS: List[Tuple[str, str]] = [
    (k, v["label"]) for k, v in TONE_PROFILES.items()
]

INDIAN_BOY_STYLE_OPTIONS: List[Tuple[str, str]] = [
    ("follow_tone", "🎬 Auto (Follow Above Script Tone Setting)"),
    ("indian_boy_heartfelt", "👦💖 Cute, Sweet & Smart Chapal Boy (Indian Hindi + Pauses + Manat Ghar Finisher)"),
    ("indian_boy_village_fresh", "🌾😊 Village Boy Freshness (Desi Analogy, Happy Warmth & Calm Clarity)"),
    ("indian_boy_city_charm", "🏙️⚡ Modern City Boy Charm (Fast Curious Hook, Romantic-Sweet Wit & Crisp Sync)"),
    ("indian_boy_calm_classic", "🎓✨ Calm Classic Perfection Boy (Zero Extra Words, Extra Visual Hold & Poetic Closer)"),
    ("indian_boy_dual_chai", "☕🗣️ Chai-Tapri Dual Jodi (Female Curious Q + Smart Indian Boy Mentor A)"),
]


def compute_synced_visual_progress(
    lin_p: float,
    cur_t: float,
    words: Optional[List[Dict[str, Any]]],
    tone: Optional[str] = None,
) -> float:
    """
    Computes word-synced visual reveal progress with comfortable eye-read dwell time:
    - Anchors animations to spoken `word_timestamps` (`word_p`) for tight audio-visual sync.
    - Applies `visual_pace_lead` from the tone profile so diagrams complete cleanly slightly before
      scene cut, preventing rapid visual flashes the viewer cannot read.
    """
    prof = get_tone_profile(tone)
    lead = float(prof.get("visual_pace_lead", 1.0))
    hold_cutoff = 0.84 if lead >= 1.10 else 0.93
    if lin_p >= hold_cutoff:
        return 1.0
    if words:
        spoken = sum(1 for wd in words if float(wd.get("start", 0.0)) <= cur_t)
        word_p = spoken / max(1, len(words))
        base_p = 0.72 * word_p + 0.28 * lin_p
    else:
        base_p = lin_p
    return min(1.0, max(0.0, base_p * lead))


def resolve_effective_tone(
    tone: Optional[str],
    scene_tone: Optional[str] = None,
    role: Optional[str] = None,
    idx: int = 0,
) -> str:
    """Resolves a requested/scene tone strictly into one concrete 2026 tone profile key."""
    req = str(tone or "").strip().lower()
    st = str(scene_tone or "").strip().lower()
    if req in (DEFAULT_TONE_KEY, "auto_dynamic") or not req:
        if st in TONE_PROFILES and st not in (DEFAULT_TONE_KEY, "auto_dynamic"):
            return st
        r = str(role or "").lower().strip()
        if r == "hook":
            return "myth_buster_contrarian"
        if r in ("problem", "incident", "alert"):
            return "war_story_postmortem"
        if r in ("architecture", "system", "pipeline", "analogy"):
            return "whiteboard_analogy"
        if r in ("tradeoff", "comparison", "compare"):
            return "cage_match_vs"
        if r in ("code", "query", "sql", "debug"):
            return "live_debug_pair"
        if r in ("cta", "summary", "takeaway"):
            return "bigtech_reverse_engineer"
        cycle = ("whiteboard_analogy", "live_debug_pair", "cage_match_vs", "bigtech_reverse_engineer", "release_radar_tldr")
        return cycle[idx % len(cycle)]
    if req in TONE_PROFILES:
        return req
    if st in TONE_PROFILES and st not in (DEFAULT_TONE_KEY, "auto_dynamic"):
        return st
    return DEFAULT_CONCRETE_TONE


def get_tone_profile(tone: Optional[str], scene_tone: Optional[str] = None, role: Optional[str] = None, idx: int = 0) -> Dict[str, Any]:
    key = resolve_effective_tone(tone, scene_tone=scene_tone, role=role, idx=idx)
    return dict(TONE_PROFILES.get(key, TONE_PROFILES[DEFAULT_CONCRETE_TONE]), key=key)


def get_tone_directive(tone: Optional[str]) -> str:
    t = str(tone or DEFAULT_TONE_KEY).strip().lower()
    prof = TONE_PROFILES.get(t) or TONE_PROFILES[DEFAULT_TONE_KEY]
    return str(prof["directive"])


def get_clause_prosody(
    tone: Optional[str],
    beat_idx: int,
    total_beats: int,
    beat_txt: str = "",
) -> Tuple[str, str]:
    """
    Hook-to-Climax Speed Curve across clauses inside a single scene:
    - Beat 0 (Hook/Opening) gets energetic punch burst (`hook_curve`)
    - Middle beats (Mechanism/Data) get crystal clarity (`mid_curve`)
    - Closing/Verdict/Alert clauses adjust pitch/speed dynamically (`verdict_curve` or tension dip)
    """
    prof = get_tone_profile(tone)
    txt = str(beat_txt or "").strip().lower()
    if any(kw in txt for kw in ("crash", "timeout", "deadlock", "outage", "fail", "error", "502", "429", "blocked")):
        return "-2%", "-3Hz"
    if total_beats <= 1:
        c = prof["edge_base"]
        return str(c["rate"]), str(c["pitch"])
    if beat_idx == 0:
        c = prof["hook_curve"]
        return str(c["rate"]), str(c["pitch"])
    if beat_idx >= total_beats - 1 or txt.endswith("!") or any(kw in txt for kw in ("winner", "verdict", "result", "always", "never", "rule")):
        c = prof["verdict_curve"]
        return str(c["rate"]), str(c["pitch"])
    if txt.endswith("?"):
        hr = prof["hook_curve"]
        return str(prof["mid_curve"]["rate"]), str(hr["pitch"])
    c = prof["mid_curve"]
    return str(c["rate"]), str(c["pitch"])


def collect_sfx_timeline(
    aligned_scenes: List[Dict[str, Any]],
    word_timestamps: Optional[List[Dict[str, Any]]] = None,
    tone: str = DEFAULT_TONE_KEY,
) -> List[Dict[str, Any]]:
    """
    Builds clean, volume-calibrated Micro-SFX timeline events synced to:
    1) 2-Second Hook Pattern Interrupt (`pop_snap` near t=0.06s)
    2) Scene boundaries (`whoosh` / tone transition cue)
    3) Spoken Action Verbs (`alert_ping` on disrupt_shake, `success_chime` on state_flip,
       `key_tick` on live_debug_pair/code scenes, `pop_snap` on filter_gate/travel_token)
    Capped safely to <= 12 events so FFmpeg audio mix stays lightweight and musical.
    """
    from core.action_engine import extract_spoken_actions

    events: List[Dict[str, Any]] = []
    if not aligned_scenes:
        return events

    def _add(t_sec: float, sfx_name: str, gain: float) -> None:
        ts = max(0.02, round(float(t_sec), 3))
        if any(abs(e["time"] - ts) < 0.65 and e["sfx"] == sfx_name for e in events):
            return
        events.append({"time": ts, "sfx": sfx_name, "gain": round(float(gain), 3)})

    # 1. Pattern Interrupt Opening Punch (first 0.08s)
    _add(0.06, "pop_snap", 0.22)

    all_words = word_timestamps or []
    for idx, sc in enumerate(aligned_scenes):
        st = float(sc.get("start_time", 0.0))
        dur = max(1.0, float(sc.get("duration", 4.0)))
        eff_t = resolve_effective_tone(tone, scene_tone=sc.get("scene_tone"), role=sc.get("role"), idx=idx)
        prof = TONE_PROFILES.get(eff_t, TONE_PROFILES[DEFAULT_CONCRETE_TONE])

        if idx > 0:
            _add(st + 0.02, prof.get("default_sfx", "whoosh") if idx == 1 else "whoosh", 0.19)

        sc_words = [
            w for w in all_words
            if st - 0.1 <= float(w.get("start", 0.0)) <= st + dur + 0.1
        ]
        acts = extract_spoken_actions(sc, dur, sc_words)
        for act in acts[:2]:
            verb = str(act.get("verb") or "")
            p0 = float(act.get("start_p", 0.35))
            act_t = st + p0 * dur
            if verb == "disrupt_shake":
                _add(act_t, "alert_ping", 0.24)
            elif verb == "state_flip":
                _add(act_t + dur * 0.12, "success_chime", 0.20)
            elif eff_t == "live_debug_pair" or str(sc.get("visual_type") or "") in ("code_terminal", "ide_split_workbench", "code_diff_split", "mac_terminal_stream_cast", "dual_sync_diagram_plus_code"):
                _add(act_t, "key_tick", 0.18)
            elif verb in ("filter_gate", "travel_token", "slot_reorder"):
                _add(act_t, "pop_snap", 0.16)

    # Sort chronologically and scale clean upper cap smoothly for multi-scene deep dives
    events.sort(key=lambda e: e["time"])
    max_sfx = min(24, max(12, len(aligned_scenes) * 2))
    return events[:max_sfx]
