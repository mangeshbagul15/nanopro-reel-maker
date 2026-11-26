import math
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw

from core.mesh_shader_engine import draw_procedural_3d_mesh
from core.shapes_3d import draw_3d_shape, draw_vector_glyph

# =========================================================================
# 12 DYNAMIC CAMERA & SCENE TRANSITION FX
# =========================================================================
ALL_TRANSITIONS: Tuple[str, ...] = (
    "crossfade",
    "slide_up",
    "slide_down",
    "slide_left",
    "slide_right",
    "zoom_push",
    "zoom_pull",
    "wipe_reveal",
    "iris_circle",
    "curtain_split",
    "parallax_pan",
    "glitch_snap",
)


def apply_scene_transition(
    stage_img: Image.Image,
    bg_img: Image.Image,
    transition: str,
    linear_p: float,
) -> Image.Image:
    """
    Applies one of 12 studio transitions over enter/exit envelope cleanly at 30fps
    onto bg_img without blocking fast PIL/NumPy frame timing.
    """
    tr = str(transition or "crossfade").lower().strip()
    if tr not in ALL_TRANSITIONS:
        tr = "crossfade"
    w, h = stage_img.size
    out = bg_img.convert("RGBA") if bg_img is not None else Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Enter phase: 0.0 -> 0.14, Exit phase: 0.90 -> 1.0
    if linear_p < 0.14:
        t = max(0.0, min(1.0, linear_p / 0.14))
        e = 1.0 - (1.0 - t) ** 3
        entering = True
    elif linear_p > 0.90:
        t = max(0.0, min(1.0, (1.0 - linear_p) / 0.10))
        e = 1.0 - (1.0 - t) ** 2
        entering = False
    else:
        out.alpha_composite(stage_img)
        return out

    if tr == "crossfade":
        layer = stage_img.copy()
        layer.putalpha(layer.split()[3].point(lambda p: int(p * (0.25 + 0.75 * e))))
        out.alpha_composite(layer)
    elif tr in ("slide_up", "slide_down", "slide_left", "slide_right", "parallax_pan"):
        dx, dy = 0, 0
        dist = int((1.0 - e) * (160 if entering else 120))
        if tr == "slide_up":
            dy = dist if entering else -dist
        elif tr == "slide_down":
            dy = -dist if entering else dist
        elif tr in ("slide_left", "parallax_pan"):
            dx = dist if entering else -dist
        elif tr == "slide_right":
            dx = -dist if entering else dist
        layer = stage_img.copy()
        layer.putalpha(layer.split()[3].point(lambda p: int(p * (0.25 + 0.75 * e))))
        out.alpha_composite(layer, (dx, dy))
    elif tr in ("zoom_push", "zoom_pull"):
        sc = (0.86 + 0.14 * e) if tr == "zoom_push" else (1.14 - 0.14 * e)
        nw, nh = max(64, int(w * sc)), max(64, int(h * sc))
        resized = stage_img.resize((nw, nh), Image.Resampling.BILINEAR)
        resized.putalpha(resized.split()[3].point(lambda p: int(p * (0.25 + 0.75 * e))))
        if nw <= w and nh <= h:
            out.alpha_composite(resized, ((w - nw) // 2, (h - nh) // 2))
        else:
            cx0, cy0 = (nw - w) // 2, (nh - h) // 2
            out.alpha_composite(resized.crop((cx0, cy0, cx0 + w, cy0 + h)))
    elif tr == "wipe_reveal":
        cut = max(1, int(w * (0.15 + 0.85 * e)))
        cropped = stage_img.crop((0, 0, cut, h))
        out.alpha_composite(cropped, (0, 0))
    elif tr == "iris_circle":
        mask = Image.new("L", (w, h), 0)
        rad = max(20, int(math.hypot(w, h) * 0.55 * (0.15 + 0.85 * e)))
        ImageDraw.Draw(mask).ellipse((w // 2 - rad, h // 2 - rad, w // 2 + rad, h // 2 + rad), fill=255)
        layer = stage_img.copy()
        layer.putalpha(ImageChops.darker(layer.split()[3], mask))
        out.alpha_composite(layer)
    elif tr == "curtain_split":
        half_w = max(1, int((w // 2) * (0.18 + 0.82 * e)))
        left_c = stage_img.crop((w // 2 - half_w, 0, w // 2 + half_w, h))
        out.alpha_composite(left_c, (w // 2 - half_w, 0))
    else:  # glitch_snap
        jitter = int(math.sin(linear_p * 180.0) * (1.0 - e) * 28)
        layer = stage_img.copy()
        layer.putalpha(layer.split()[3].point(lambda p: int(p * (0.35 + 0.65 * e))))
        out.alpha_composite(layer, (jitter, 0))
    return out


# =========================================================================
# 14 KINETIC TYPOGRAPHY & TEXT MOTION FX
# =========================================================================
ALL_TEXT_FX: Tuple[str, ...] = (
    "clean_fade",
    "word_pop",
    "highlighter_brush",
    "typewriter_cursor",
    "gradient_shimmer",
    "strike_vs_new",
    "neon_underline",
    "split_counter",
    "glitch_text",
    "pill_tag_drop",
    "scale_bounce",
    "letter_track",
    "quote_serif_glow",
    "slide_reveal",
)


def draw_kinetic_text(
    stage: Any,
    text: str,
    xy: Tuple[int, int],
    max_w: int,
    font: Any,
    accent: Tuple[int, int, int],
    progress: float,
    fx: str = "clean_fade",
    world: Optional[Dict[str, Any]] = None,
    _with_alpha_fn: Any = None,
    _draw_wrapped_fn: Any = None,
) -> None:
    """Applies any of 14 expressive headline / callout text motion effects cleanly."""
    w = world or stage.world
    mode = str(fx or "clean_fade").lower().strip()
    x, y = xy
    txt = str(text or "").strip()
    if not txt:
        return

    a = stage.t_alpha
    wa = _with_alpha_fn
    if mode == "typewriter_cursor":
        k = max(1, int(len(txt) * min(1.0, progress / 0.65)))
        shown = txt[:k] + ("_" if (progress < 0.85 and int(progress * 16) % 2 == 0) else "")
        _draw_wrapped_fn(stage.draw, (x, y), shown, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode == "highlighter_brush":
        sw = min(max_w, int(stage.draw.textlength(txt[:28], font=font) * min(1.0, progress / 0.35)) + 16)
        stage.draw.rounded_rectangle((x - 6, y + 6, x + sw, y + 54), radius=10, fill=wa((*accent[:3], 64), a))
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode == "neon_underline":
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
        uw = min(max_w, int(stage.draw.textlength(txt[:30], font=font) * min(1.0, progress / 0.45)))
        stage.add_glow_line([(x, y + 58), (x + uw, y + 58)], accent, width=10, alpha=160)
        stage.draw.line((x, y + 58, x + uw, y + 58), fill=wa(accent, a), width=4)
    elif mode == "gradient_shimmer":
        pulse = 0.5 + 0.5 * math.sin(progress * math.pi * 4.0)
        c1, c2 = accent, w["purple"]
        mix = (int(c1[0] * pulse + c2[0] * (1 - pulse)), int(c1[1] * pulse + c2[1] * (1 - pulse)), int(c1[2] * pulse + c2[2] * (1 - pulse)))
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(mix, a), max_w, line_gap=8, max_lines=2)
    elif mode == "glitch_text":
        off = 4 if (progress < 0.35 and int(progress * 30) % 3 == 0) else 0
        if off:
            _draw_wrapped_fn(stage.draw, (x - off, y), txt, font, wa(w["rose"], a * 0.7), max_w, line_gap=8, max_lines=2)
            _draw_wrapped_fn(stage.draw, (x + off, y), txt, font, wa(w["cyan"], a * 0.7), max_w, line_gap=8, max_lines=2)
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode in ("slide_reveal", "pill_tag_drop"):
        dy = int((1.0 - min(1.0, progress / 0.25)) * (-26 if mode == "pill_tag_drop" else 28))
        _draw_wrapped_fn(stage.draw, (x, y + dy), txt, font, wa(w["text"], a * min(1.0, progress / 0.20 + 0.2)), max_w, line_gap=8, max_lines=2)
    elif mode in ("word_pop", "scale_bounce"):
        words = txt.split()
        show_cnt = max(1, int(len(words) * min(1.0, progress / 0.45 + 0.2)))
        dy = -abs(int(math.sin(progress * math.pi * 6.0) * 6)) if progress < 0.35 else 0
        _draw_wrapped_fn(stage.draw, (x, y + dy), " ".join(words[:show_cnt]), font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    elif mode == "strike_vs_new":
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
        sw = min(max_w // 2, int(stage.draw.textlength(txt.split()[0], font=font))) if progress > 0.2 else 0
        if sw > 12:
            stage.draw.line((x, y + 26, x + sw, y + 26), fill=wa(w["rose"], a), width=4)
    elif mode == "quote_serif_glow":
        stage.add_glow_orb(x + 120, y + 26, 70, accent, alpha=int(75 * a))
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)
    else:
        _draw_wrapped_fn(stage.draw, (x, y), txt, font, wa(w["text"], a), max_w, line_gap=8, max_lines=2)


# =========================================================================
# +104 SPECIALIZED STUDIO PRO LAYOUTS (AI/ML, Charts, UI Mockups, Science)
# =========================================================================
_PRO_EXTRA_PRESETS: Dict[str, Tuple[str, str, Tuple[str, ...]]] = {
    # --- AI / LLM / Agents / MLOps (+19 -> 26 total in AI pillar) ---
    "transformer_self_attn": ("attention_heatmap", "Self-Attention Q·K^T Matrix", ("Query", "Key", "Value", "Softmax")),
    "kv_cache_sliding": ("timeline_gantt", "KV Cache Sliding Window", ("System Prompt", "Context Window", "Evicted Tokens", "Active Decode")),
    "lora_adapter_merge": ("sankey_flow", "LoRA Low-Rank Adapter Merge", ("Frozen W0|Merged W|95%", "Rank A*B|Merged W|100%")),
    "moe_routing_chart": ("rag_pipeline_3d", "Mixture-of-Experts Top-2 Router", ("Gate Router", "Expert Math", "Expert Code", "Expert SQL", "Combine")),
    "mcp_tool_bridge": ("agent_loop_3d", "Model Context Protocol (MCP) Bridge", ("LLM Host", "MCP Client", "Schema Discovery", "Tool Execution")),
    "eval_rubric_matrix": ("confusion_matrix", "LLM Eval Groundedness Matrix", ("Faithful", "Relevant", "Concise", "Cited")),
    "prompt_injection_guard": ("split_screen_50_50", "Prompt Firewall Defense", ("Untrusted Input\nRaw SQL / Override", "Sanitized Guard\nPolicy Verified ✓")),
    "speculative_tokens_chart": ("line_area_chart", "Speculative Draft vs Target Tokens/s", ("Draft k=4", "Verify 1 Pass", "Accept 3.2x", "Target Match")),
    "rlhf_ppo_loop": ("agent_loop_3d", "RLHF / DPO Alignment Loop", ("Policy LM", "Reward Model", "KL Penalty", "Human Prefs")),
    "diffusion_denoise_steps": ("line_area_chart", "Latent Diffusion Denoising Schedule", ("t=1000 Noise", "UNet Cross-Attn", "CFG Scale", "Clean Latent")),
    "quantization_int4": ("before_after_slider", "FP16 vs INT4 AWQ Footprint", ("FP16 Weights\n14 GB VRAM • 1x", "INT4 Quantized\n3.8 GB VRAM • 2.7x Faster")),
    "graph_rag_hops": ("mindmap_radial", "2-Hop Knowledge Graph RAG", ("Entity Hub", "Edge Weight", "Community Summary", "Vector Fuse")),
    "vllm_paged_attn": ("kanban_board", "vLLM PagedAttention KV Blocks", ("Logical KV", "Block Table", "Physical VRAM")),
    "supervisor_agent_orbit": ("orbit_ecosystem", "Multi-Agent Supervisor Swarm", ("Planner", "Researcher", "Coder", "Verifier")),
    "voice_pipeline_vad": ("rag_pipeline_3d", "Realtime Voice AI Pipeline (<300ms)", ("Mic PCM", "Silero VAD", "Streaming ASR", "TTS Prosody")),
    "semantic_cache_clusters": ("embedding_cluster", "Semantic Cosine Similarity Cache", ("Hit >0.94", "Miss <0.78", "Vector LSH", "LRU Evict")),
    "reranker_cross_encoder": ("token_prob_bars", "Bi-Encoder -> Cross-Encoder Rerank", ("Doc #14 Exact", "Doc #03 Semantic", "Doc #09 Keyword", "Doc #22 Tail")),
    "embedding_hnsw_layers": ("neural_net_layers", "HNSW Hierarchical Navigable Layers", ("Entry Layer 2", "Skip Layer 1", "Dense Layer 0", "Top-K")),
    "fine_tune_loss_curve": ("line_area_chart", "Training vs Validation Loss Decay", ("Epoch 1", "Warmup Peak", "Cosine Decay", "Converged")),

    # --- Charts, Quant & Observability (+18 -> 26 total in Analytics pillar) ---
    "cohort_retention_grid": ("heatmap_matrix", "Weekly User Cohort Retention %", ("Week 1", "Week 2", "Week 3", "Week 4")),
    "pareto_frontier_plot": ("scatter_plot", "Latency vs Cost Pareto Frontier", ("Optimal Frontier", "Over-Provisioned", "High Latency")),
    "box_whisker_latency": ("candlestick_pro", "P50 / P95 / P99 Tail Spread", ("Min", "P50", "P95", "P99")),
    "violin_distribution": ("line_area_chart", "Bimodal Cache Hit vs Miss Distribution", ("L1 Hit 0.2ms", "L2 Hit 3ms", "DB Fallback 48ms")),
    "waterfall_bridge_chart": ("candlestick_pro", "Latency Budget Bridge Breakdown", ("DNS 8ms", "TLS 14ms", "DB 42ms", "Render 12ms")),
    "treemap_storage_alloc": ("kanban_board", "Storage Partition Allocation", ("Hot NVMe 52%", "Warm S3 31%", "Cold Glacier 17%")),
    "sunburst_cost_breakdown": ("donut_3d", "Cloud Spend Cost Attribution", ("Compute", "Storage", "Egress")),
    "chord_service_deps": ("orbit_ecosystem", "Cross-Service Call Density", ("API GW", "Auth", "Orders", "Ledger")),
    "slo_burn_rate_gauge": ("donut_3d", "99.95% Error Budget Burn Rate", ("Healthy 82%", "Alert Burn 12%", "Remaining 6%")),
    "anomaly_zscore_bands": ("line_area_chart", "Z-Score Drift & Spike Detection", ("Mean", "+2 Sigma", "Anomaly Z>3.5", "Recovered")),
    "funnel_conversion_drop": ("sankey_flow", "Checkout Drop-Off Funnel", ("Landing|Cart|68%", "Cart|Checkout|54%", "Checkout|Paid|84%")),
    "bullet_kpi_targets": ("token_prob_bars", "Quarterly SLA Attainment vs Target", ("Uptime SLA", "P99 Target", "Error Cap", "MTTR Goal")),
    "histogram_p99_tail": ("token_prob_bars", "Request Latency Bucket Histogram", ("<10ms Fast", "10-50ms OK", "50-200ms Slow", ">200ms Tail")),
    "correlation_matrix_pro": ("heatmap_matrix", "Metric Pearson Correlation Grid", ("CPU", "GC Pause", "IOPS", "P99")),
    "cumulative_throughput_area": ("line_area_chart", "Cumulative RPS Throughput Ramp", ("Baseline 5K", "Autoscale 25K", "Peak 80K")),
    "sparkline_kpi_board": ("radar_spider", "Multi-Signal Service Health Radar", ("CPU", "Mem", "Disk", "Net", "Err")),
    "latency_heatmap_hour": ("heatmap_matrix", "24h Traffic Surge Heatmap", ("00:00", "06:00", "12:00", "18:00")),
    "resource_quota_meter": ("donut_3d", "Namespace CPU & Memory Quota", ("Reserved", "Burstable", "Headroom")),

    # --- UI / Product / Developer Experience (+17 -> 26 total in UI pillar) ---
    "ide_split_debugger": ("split_screen_50_50", "Breakpoint Watch & Callstack", ("Call Stack\nmain() -> parse()\nLine 42 Break", "Watch Inspector\ntokens = 1024\nerr = nil ✓")),
    "pr_review_thread": ("chat_thread_ai", "Automated PR Review Inline Thread", ("Bot: Potential N+1 query detected", "Dev: Switched to batched JOIN", "Bot: Latency -82% Approved ✓")),
    "billing_usage_meter": ("pricing_tiers", "Metered API Tier Consumption", ("Free Dev", "Pro Scale", "Enterprise SLA")),
    "feature_flag_toggle_ui": ("mobile_app_mockup", "Progressive Rollout Feature Flags", ("1% Canary ON", "10% Region US", "100% GA Ready")),
    "api_playground_console": ("browser_window", "Interactive REST / GraphQL Console", ("POST /v2/stream • 200 OK • 18ms",)),
    "webhook_inspector_card": ("notification_stack", "Signed Webhook Delivery Trace", ("HMAC SHA-256 Verified", "Retry #1 Backoff 2s", "200 ACK Confirmed")),
    "onboarding_stepper_ui": ("timeline_gantt", "Developer 3-Min Onboarding Flow", ("API Key Created", "SDK Installed", "First Request 200 OK")),
    "command_palette_modal": ("browser_window", "Cmd+K Global Action Palette", ("Jump to Traces • Logs • Deploy • Secrets",)),
    "diff_patch_card": ("before_after_slider", "Production Config Patch Diff", ("max_conn = 50\ntimeout = 30s", "max_conn = 400\ntimeout = 2s + retry ✓")),
    "auth_oauth_consent": ("mobile_app_mockup", "OAuth 2.1 PKCE Consent Flow", ("Scope: read:metrics", "PKCE S256 Verified", "Token Issued")),
    "role_permission_matrix": ("confusion_matrix", "RBAC Least-Privilege Matrix", ("Admin", "DevOps", "Viewer", "CI Bot")),
    "search_autocomplete_ui": ("token_prob_bars", "Typeahead Instant Prefix Ranking", ("pg_stat_statements", "pgbouncer_pool", "postgres_wal", "pgvector_hnsw")),
    "toast_alert_banner": ("notification_stack", "Zero-Downtime Cutover Alerts", ("Shadow Traffic Verified", "DNS Weight Shifted 100%", "Zero Dropped Requests")),
    "changelog_release_notes": ("timeline_gantt", "Semantic Release Changelog v4.2", ("v4.0 Engine", "v4.1 Streaming", "v4.2 Zero-Lock")),
    "profile_badge_showcase": ("radar_spider", "System Maturity Capability Profile", ("Speed", "Reliability", "Security", "Cost", "Observability")),
    "table_pagination_pro": ("before_after_slider", "OFFSET vs Keyset Cursor Pagination", ("OFFSET 100000\nScans 100K Rows (640ms)", "WHERE id > last_id\nB-Tree Seek (0.4ms)")),
    "mobile_push_alert": ("mobile_app_mockup", "On-Call Mobile Pager Alert", ("P1 Cache Stampede", "Auto-Mitigated", "SLO Green 99.99%")),

    # --- Science / Systems Strategy / Quantum / Hardware (+18 -> 26 total in Science pillar) ---
    "fourier_wave_decompose": ("line_area_chart", "FFT Signal Frequency Decomposition", ("Fundamental f0", "Harmonic 3f0", "Noise Filter", "Clean Signal")),
    "gradient_descent_valley": ("mesh_3d_stage", "AdamW Loss Landscape Convergence", ("Non-Convex Saddle -> Global Minima",)),
    "bayesian_prior_posterior": ("split_screen_50_50", "Bayesian Prior -> Posterior Update", ("Prior Belief\nP(H) = 0.25", "Observed Evidence\nPosterior = 0.89 ✓")),
    "markov_transition_graph": ("agent_loop_3d", "Markov Chain State Transition P(ij)", ("Idle", "Active", "Retry", "Settled")),
    "pid_feedback_controller": ("rag_pipeline_3d", "Closed-Loop PID Auto-Scaler", ("Setpoint", "Proportional", "Integral", "Derivative")),
    "simd_lane_kanban": ("kanban_board", "AVX-512 8-Lane SIMD Vectorization", ("Lane 0-1", "Lane 2-3", "Lane 4-7")),
    "gpu_warp_scheduler": ("neural_net_layers", "GPU SM 32-Thread Warp Scheduler", ("Warp Issue", "Tensor Core", "Shared Mem", "Register File")),
    "quantum_bloch_circuit": ("atom_orbit_3d", "Qubit Hadamard + CNOT Entanglement", ("Superposition |+⟩ State",)),
    "crispr_gene_edit": ("dna_helix_3d", "CRISPR Cas9 Guide RNA Target Cut", ("PAM Site Recognition & Repair",)),
    "protein_folding_energy": ("embedding_cluster", "AlphaFold Free-Energy Folding Funnel", ("Unfolded Coil", "Molten Globule", "Native State")),
    "neural_synapse_spike": ("neural_net_layers", "Leaky Integrate-and-Fire SNN", ("Dendrite", "Threshold", "Axon Spike", "Synapse")),
    "entropy_info_gain": ("equation_proof", "Shannon Entropy H(X) = -Σ p log p", ("Information Gain Maximization",)),
    "game_theory_payoff": ("confusion_matrix", "Nash Equilibrium Strategy Matrix", ("Cooperate", "Defect", "Retry", "Backoff")),
    "pareto_80_20_rule": ("donut_3d", "Pareto 80/20 Bottleneck Distribution", ("Critical 20%", "Secondary 30%", "Long Tail 50%")),
    "big_o_complexity_curves": ("line_area_chart", "O(1) vs O(log N) vs O(N^2) Growth", ("O(1) Hash", "O(log N) B-Tree", "O(N) Scan", "O(N^2) Cliff")),
    "cap_pacelc_matrix": ("pros_cons_scale", "PACELC Partition & Latency Choice", ("PA/EL: Dynamo/Cassandra", "PC/EC: Spanner/Cockroach")),
    "amortized_cost_analysis": ("countdown_hero", "O(1) Amortized Dynamic Resize", ("Doubling Strategy Token Credit",)),
    "flywheel_compounding_loop": ("orbit_ecosystem", "Compounding Systems Flywheel", ("Better Latency", "Higher Trust", "More Scale", "Lower Cost")),

    # --- +13 AI / LLM / Reasoning (Total 39 in AI Pillar) ---
    "cot_reasoning_tree": ("rag_pipeline_3d", "Chain-of-Thought Search Tree", ("Root Query", "Branch Plan A", "Verify Branch B", "Prune Low Score")),
    "parallel_tool_calls": ("agent_loop_3d", "Parallel Function Calling Fan-Out", ("Planner", "SQL Tool", "Search API", "Merge Obs")),
    "cosine_sim_heatmap": ("attention_heatmap", "Embedding Cosine Similarity Grid", ("Doc 1", "Doc 2", "Doc 3", "Query")),
    "hybrid_rrf_rerank": ("sankey_flow", "Reciprocal Rank Fusion (BM25 + Dense)", ("BM25 Sparse|RRF Fusion|50%", "Dense Vector|RRF Fusion|50%", "RRF Fusion|Top-K Context|96%")),
    "prompt_prefix_compress": ("before_after_slider", "Prompt Token Pruning Compression", ("Raw 4,800 Tokens\n$0.14 / Call", "Compressed 1,200 Tokens\n4x Faster Prefill ✓")),
    "vlm_patch_encoder": ("neural_net_layers", "Vision Transformer Image Patch Grid", ("16x16 Patches", "Linear Proj", "Cross-Attn", "Text Tokens")),
    "audio_mel_bands": ("heatmap_matrix", "Log-Mel Spectrogram Speech Bands", ("40Hz", "400Hz", "2kHz", "8kHz")),
    "reward_hacking_shield": ("split_screen_50_50", "RLHF Reward Hacking Mitigation", ("Unconstrained Policy\nVerbosity Exploits", "KL-Penalty Guard\nConcise Accuracy ✓")),
    "synthetic_distill_pipe": ("rag_pipeline_3d", "Teacher -> Student Model Distillation", ("70B Teacher", "Verified Trace", "Filter Quality", "7B Student")),
    "lora_rank_sweeps": ("line_area_chart", "LoRA Rank r=4..64 Accuracy vs VRAM", ("r=4", "r=8", "r=16", "r=32", "r=64")),
    "episodic_agent_store": ("timeline_gantt", "Long-Horizon Agent Episodic Memory", ("Working Scratch", "Session Redis", "Episodic Qdrant", "Long-Term SQL")),
    "prefix_kv_reuse": ("kanban_board", "System Prompt KV Prefix Reuse", ("Shared Sys KV", "Tenant Doc KV", "Per-User Tail")),
    "cascade_model_router": ("sankey_flow", "Small-to-Large LLM Model Router", ("Easy 75%|8B Fast|$0.0002", "Hard 25%|Frontier Pro|99% Acc")),

    # --- +13 Graphs, Analytics & Observability (Total 39 in Analytics Pillar) ---
    "multi_series_area": ("line_area_chart", "Read vs Write Throughput Ramp", ("Baseline", "Shard x2", "Cache Hit", "Peak 95K")),
    "stacked_traffic_area": ("line_area_chart", "API Traffic by Edge vs Origin", ("Edge Cached", "Origin API", "Background", "Total RPS")),
    "p99_tail_cdf_curve": ("line_area_chart", "Cumulative Latency Distribution (CDF)", ("P50 4ms", "P90 12ms", "P99 38ms", "P99.9 110ms")),
    "scatter_trend_fit": ("scatter_plot", "Memory vs Latency Regression Fit", ("Small Pool", "Optimal Knee", "Swap Cliff")),
    "latency_knee_point": ("line_area_chart", "Load Saturation Little's Law Knee", ("20% Util", "50% Util", "78% Knee", "95% Spike")),
    "error_budget_burn": ("donut_3d", "30-Day SLO Error Budget Status", ("Healthy 78%", "Canary Burn 14%", "Buffer 8%")),
    "memory_slab_treemap": ("kanban_board", "Heap & PageCache Memory Partition", ("Buffer Pool 62%", "WAL Cache 18%", "Temp Sort 20%")),
    "queue_sawtooth_chart": ("candlestick_pro", "GC Allocation & Pause Sawtooth", ("Alloc Ramp", "Young GC", "Survivors", "Steady")),
    "cache_miss_heatmap": ("heatmap_matrix", "Key Prefix Hot-Shard Miss Matrix", ("Shard 0", "Shard 1", "Shard 2", "Shard 3")),
    "cohort_ltv_curve": ("line_area_chart", "Net Dollar Retention Expansion Cohort", ("M1 100%", "M3 108%", "M6 118%", "M12 134%")),
    "ab_ci_error_bars": ("candlestick_pro", "Experiment 95% Confidence Intervals", ("Control", "Variant A", "Variant B", "Winner")),
    "core_cpu_util_bars": ("token_prob_bars", "Per-Core Saturation Skew Check", ("Core 0 IRQ Hot", "Core 1 Worker", "Core 2 Worker", "Core 3 Idle")),
    "egress_bandwidth_area": ("donut_3d", "Cross-AZ vs CDN Network Egress", ("CDN Edge", "Cross-AZ Sync", "DB Replication")),

    # --- +12 UI / Developer UX Mockups (Total 38 in UI Pillar) ---
    "cli_progress_board": ("terminal_studio" if False else "notification_stack", "Live CI Runner Deployment Progress", ("Build Docker SHA256 ✓", "Integration Tests 142/142 ✓", "Canary 25% Health Green ✓")),
    "openapi_schema_docs": ("browser_window", "OpenAPI 3.1 Interactive Spec Portal", ("GET /v2/tenants/{id}/usage • Typed SDK Ready",)),
    "git_blame_gutter_ui": ("split_screen_50_50", "IDE Inline Commit Blame & PR Link", ("Legacy Line 112\nPR #402 by @ops", "Refactored Line 112\nPR #988 • -65% Alloc ✓")),
    "flame_modal_viewer": ("token_prob_bars", "Continuous eBPF Profile Hotspots", ("serde_json::from_str", "sha256_compress", "tls_handshake", "pg_bind_exec")),
    "explain_plan_viewer": ("kanban_board", "Query Plan Operator Cost Breakdown", ("Hash Join 12%", "Index Only 4%", "Bitmap Heap 84%")),
    "secret_rotation_ui": ("timeline_gantt", "Automated Zero-Downtime Key Rotation", ("Dual Key Issue", "Grace Overlap 24h", "Revoke Legacy Key")),
    "audit_event_feed_ui": ("chat_thread_ai", "Immutable Compliance Audit Stream", ("Admin: Updated RBAC Role Policy", "System: Signed Hash #9941A", "Verifier: Chain Validated ✓")),
    "status_outage_banner": ("mobile_app_mockup", "Real-Time Status Incident Updates", ("US-East Investigating", "Failover Complete", "All Systems Operational")),
    "saml_sso_handshake_ui": ("browser_window", "Enterprise SAML 2.0 / OIDC SSO Login", ("Verified Assertion • JIT SCIM Group Synced",)),
    "k8s_pod_lens_ui": ("mobile_app_mockup", "Kubernetes Pod Live Resource Metrics", ("CPU 240m / 500m", "RAM 412Mi / 1Gi", "Restarts: 0 Ready")),
    "tf_plan_diff_card": ("diff_patch_card" if False else "before_after_slider", "Terraform IaC State Plan Diff", ("~ aws_rds_cluster\nstorage_iops = 3000", "+ aws_rds_cluster\nstorage_iops = 12000 ✓")),
    "docker_image_layers_ui": ("kanban_board", "Multi-Stage Image Size Reduction", ("Ubuntu Fat (920MB)", "Node Slim (240MB)", "Distroless (28MB)")),

    # --- +12 Science, Math & Distributed Systems (Total 38 in Science Pillar) ---
    "amdahl_parallel_law": ("line_area_chart", "Amdahl's Law Serial Bottleneck Cap", ("1 Core", "4 Cores", "16 Cores", "64 Cores Cap")),
    "little_law_concurrency": ("equation_proof", "Little's Law: L = λ · W", ("Avg In-Flight = Arrival Rate × Latency",)),
    "usl_scalability_curve": ("line_area_chart", "Universal Scalability Law (USL) Retrograde", ("Linear", "Contention", "Coherency Peak", "Retrograde Drop")),
    "bloom_fpr_curve": ("line_area_chart", "Bloom Filter False Positive Rate vs Bits", ("4 bits", "8 bits", "10 bits (1%)", "16 bits (0.04%)")),
    "hyperloglog_registers": ("token_prob_bars", "HyperLogLog 16KB Billion Unique Count", ("Bucket 0x1A Leading0", "Bucket 0x4F Leading0", "Harmonic Mean Est", "0.8% Std Error")),
    "hash_ring_vnodes": ("orbit_ecosystem", "Virtual Nodes Smooth Consistent Ring", ("VNode N1-A", "VNode N2-B", "VNode N3-A", "VNode N1-C")),
    "vector_clock_events": ("agent_loop_3d", "Lamport & Vector Clocks Causal Order", ("Node A [2,1,0]", "Node B [2,2,0]", "Node C [2,2,1]", "Concurrent Detect")),
    "crdt_gcounter_merge": ("split_screen_50_50", "State-Based CRDT Max-Vector Merge", ("Replica 1 Counter\n[A:5, B:2]", "Replica 2 Counter\n[A:3, B:9] -> [5,9] ✓")),
    "paxos_prepare_phase": ("chat_thread_ai", "Single-Decree Paxos Two-Phase Quorum", ("Proposer: Prepare(n=42)", "Acceptor Quorum: Promise + MaxVal", "Proposer: Accept(n=42, v)", "Quorum: Chosen ✓")),
    "raft_append_entries": ("rag_pipeline_3d", "Raft Leader Term & Log Replication", ("Leader Term 7", "AppendEntries RPC", "Majority fsync", "Commit Index++")),
    "canary_score_judge": ("radar_spider", "Automated Canary Mann-Whitney Judge", ("CPU", "P99", "5xx", "GC", "Mem")),
    "backpressure_flow_rate": ("sankey_flow", "Reactive Streams Request(N) Credit", ("Fast Producer|Bounded Buffer|Throttle N", "Consumer Drain|Refill Credit|Zero OOM")),
}

EXTRA_32_LAYOUTS: Tuple[str, ...] = (
    # AI / ML & True 3D Mesh (39)
    "neural_net_layers", "attention_heatmap", "embedding_cluster", "rag_pipeline_3d",
    "agent_loop_3d", "token_prob_bars", "mesh_3d_stage",
    "transformer_self_attn", "kv_cache_sliding", "lora_adapter_merge", "moe_routing_chart",
    "mcp_tool_bridge", "eval_rubric_matrix", "prompt_injection_guard", "speculative_tokens_chart",
    "rlhf_ppo_loop", "diffusion_denoise_steps", "quantization_int4", "graph_rag_hops",
    "vllm_paged_attn", "supervisor_agent_orbit", "voice_pipeline_vad", "semantic_cache_clusters",
    "reranker_cross_encoder", "embedding_hnsw_layers", "fine_tune_loss_curve",
    "cot_reasoning_tree", "parallel_tool_calls", "cosine_sim_heatmap", "hybrid_rrf_rerank",
    "prompt_prefix_compress", "vlm_patch_encoder", "audio_mel_bands", "reward_hacking_shield",
    "synthetic_distill_pipe", "lora_rank_sweeps", "episodic_agent_store", "prefix_kv_reuse",
    "cascade_model_router",
    # Charts & Analytics (39)
    "line_area_chart", "donut_3d", "radar_spider", "sankey_flow",
    "candlestick_pro", "heatmap_matrix", "scatter_plot", "confusion_matrix",
    "cohort_retention_grid", "pareto_frontier_plot", "box_whisker_latency", "violin_distribution",
    "waterfall_bridge_chart", "treemap_storage_alloc", "sunburst_cost_breakdown", "chord_service_deps",
    "slo_burn_rate_gauge", "anomaly_zscore_bands", "funnel_conversion_drop", "bullet_kpi_targets",
    "histogram_p99_tail", "correlation_matrix_pro", "cumulative_throughput_area", "sparkline_kpi_board",
    "latency_heatmap_hour", "resource_quota_meter",
    "multi_series_area", "stacked_traffic_area", "p99_tail_cdf_curve", "scatter_trend_fit",
    "latency_knee_point", "error_budget_burn", "memory_slab_treemap", "queue_sawtooth_chart",
    "cache_miss_heatmap", "cohort_ltv_curve", "ab_ci_error_bars", "core_cpu_util_bars",
    "egress_bandwidth_area",
    # UI / Mockups / Social (38)
    "mobile_app_mockup", "browser_window", "chat_thread_ai", "notification_stack",
    "kanban_board", "pricing_tiers", "quote_spotlight", "split_screen_50_50", "countdown_hero",
    "ide_split_debugger", "pr_review_thread", "billing_usage_meter", "feature_flag_toggle_ui",
    "api_playground_console", "webhook_inspector_card", "onboarding_stepper_ui", "command_palette_modal",
    "diff_patch_card", "auth_oauth_consent", "role_permission_matrix", "search_autocomplete_ui",
    "toast_alert_banner", "changelog_release_notes", "profile_badge_showcase", "table_pagination_pro",
    "mobile_push_alert",
    "cli_progress_board", "openapi_schema_docs", "git_blame_gutter_ui", "flame_modal_viewer",
    "explain_plan_viewer", "secret_rotation_ui", "audit_event_feed_ui", "status_outage_banner",
    "saml_sso_handshake_ui", "k8s_pod_lens_ui", "tf_plan_diff_card", "docker_image_layers_ui",
    # Science / Math / Strategy (38)
    "mindmap_radial", "timeline_gantt", "equation_proof", "before_after_slider",
    "pros_cons_scale", "atom_orbit_3d", "dna_helix_3d", "orbit_ecosystem",
    "fourier_wave_decompose", "gradient_descent_valley", "bayesian_prior_posterior", "markov_transition_graph",
    "pid_feedback_controller", "simd_lane_kanban", "gpu_warp_scheduler", "quantum_bloch_circuit",
    "crispr_gene_edit", "protein_folding_energy", "neural_synapse_spike", "entropy_info_gain",
    "game_theory_payoff", "pareto_80_20_rule", "big_o_complexity_curves", "cap_pacelc_matrix",
    "amortized_cost_analysis", "flywheel_compounding_loop",
    "amdahl_parallel_law", "little_law_concurrency", "usl_scalability_curve", "bloom_fpr_curve",
    "hyperloglog_registers", "hash_ring_vnodes", "vector_clock_events", "crdt_gcounter_merge",
    "paxos_prepare_phase", "raft_append_entries", "canary_score_judge", "backpressure_flow_rate",
)

EXTRA_PRO_100_LAYOUTS: Tuple[str, ...] = EXTRA_32_LAYOUTS

_ACCENT_CYCLE = ("cyan", "purple", "emerald", "amber", "rose")
SX0, SY0, SX1, SY1 = 64, 328, 1016, 1406
SW, SH = SX1 - SX0, SY1 - SY0


def render_pro_layout(
    stage: Any,
    layout: str,
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> bool:
    """
    Renders all +104 specialized AI/ML, True-3D Mesh, Chart, Mockup & Science layouts.
    Returns True if handled.
    """
    l_orig = str(layout or "").lower().strip()
    if l_orig not in EXTRA_32_LAYOUTS:
        return False

    d = dict(data or {})
    l = l_orig
    if l_orig in _PRO_EXTRA_PRESETS:
        base_mode, sub_title, items_t = _PRO_EXTRA_PRESETS[l_orig]
        l = base_mode
        d.setdefault("caption", sub_title)
        d.setdefault("center", sub_title[:24])
        if base_mode in ("rag_pipeline_3d", "agent_loop_3d", "mindmap_radial", "orbit_ecosystem") and not (d.get("nodes") or d.get("steps") or d.get("branches") or d.get("satellites")):
            d["nodes"] = list(items_t)
        elif base_mode in ("kanban_board", "pricing_tiers", "notification_stack", "timeline_gantt", "pros_cons_scale") and not (d.get("columns") or d.get("tiers") or d.get("tasks") or d.get("items")):
            d["items"] = [{"title": s, "sub": sub_title} for s in items_t]
        elif base_mode == "mobile_app_mockup" and not (d.get("screens") or d.get("items")):
            d["screens"] = [{"title": s, "sub": sub_title} for s in items_t]
        elif base_mode == "browser_window" and not d.get("body"):
            d["url"] = f"https://studio.dev/{l_orig.replace('_', '-')}"
            d["headline"] = sub_title
            d["body"] = " • ".join(items_t)
            d["cta"] = "Inspect Live"
        elif base_mode == "chat_thread_ai" and not d.get("messages"):
            d["messages"] = [{"role": "ai" if i % 2 else "user", "text": s} for i, s in enumerate(items_t)]
        elif base_mode in ("split_screen_50_50", "before_after_slider") and not d.get("left_text") and len(items_t) >= 2:
            d.setdefault("left_label", "BASELINE")
            d.setdefault("left_text", items_t[0])
            d.setdefault("right_label", "OPTIMIZED")
            d.setdefault("right_text", items_t[1])
        elif base_mode in ("equation_proof", "countdown_hero") and not (d.get("formula") or d.get("value")):
            d["formula"] = sub_title
            d["value"] = sub_title[:16]
            d["sub"] = items_t[0] if items_t else l_orig.replace("_", " ").title()
        elif base_mode in ("attention_heatmap", "heatmap_matrix", "confusion_matrix") and not d.get("labels"):
            d["labels"] = list(items_t)
        elif base_mode == "token_prob_bars" and not (d.get("tokens") or d.get("items")):
            d["tokens"] = [{"token": s, "prob": round(max(0.12, 0.88 - i * 0.2), 2)} for i, s in enumerate(items_t)]
        elif base_mode == "sankey_flow" and not d.get("flows"):
            flows = []
            for s in items_t:
                parts = [p.strip() for p in s.split("|")]
                if len(parts) >= 2:
                    flows.append({"from": parts[0], "to": parts[1], "label": parts[2] if len(parts) > 2 else "Flow"})
            if flows:
                d["flows"] = flows
        elif base_mode == "donut_3d" and not (d.get("slices") or d.get("items")):
            d["slices"] = [{"label": s, "value": max(15, 50 - i * 12)} for i, s in enumerate(items_t)]
        elif base_mode == "radar_spider" and not (d.get("axes") or d.get("metrics")):
            d["axes"] = [{"label": s, "value": 92 - i * 4} for i, s in enumerate(items_t)]
        elif base_mode == "neural_net_layers" and not d.get("layer_names"):
            d["layer_names"] = list(items_t)
        elif base_mode in ("embedding_cluster", "scatter_plot") and not (d.get("clusters") or d.get("points")):
            d["clusters"] = [{"label": s, "x": 0.22 + (i % 3) * 0.28, "y": 0.28 + (i // 3) * 0.42} for i, s in enumerate(items_t)]
        elif base_mode in ("mesh_3d_stage", "atom_orbit_3d", "dna_helix_3d") and not (d.get("points") or d.get("items")):
            d["points"] = list(items_t) + [sub_title]
        elif base_mode in ("line_area_chart", "candlestick_pro") and not d.get("values"):
            # deterministic rising curve distinct per preset hash
            h = sum(ord(ch) for ch in l_orig) % 19
            d["values"] = [18 + h, 31 + h // 2, 27 + h, 52, 66 + h // 3, 74, 88, 96]

    _get_font = helpers["_get_font"]
    _draw_wrapped = helpers["_draw_wrapped_text"]
    _with_alpha = helpers["_with_alpha"]
    _spring_gate = helpers["_spring_gate"]
    _ease = helpers["_ease_out_cubic"]
    _sub_gate = helpers.get("_sub_gate") or (lambda g, p="box": _ease(g))
    _footer_gate = helpers.get("_footer_gate") or (lambda p: _ease(max(0.0, min(1.0, (p - 0.72) / 0.22))))
    _anim_num = helpers["_animate_counter_text"]
    _res_col = helpers["resolve_world_color"]
    _bezier = helpers["_draw_bezier_comet"]
    _draw_vis = helpers["_draw_node_visual"]
    g0 = _ease(min(1.0, progress / 0.16))
    gf = _footer_gate(progress)

    # --- 1. TRUE NUMPY 3D MESH STAGE & SCIENCE 3D MODELS ---
    if l in ("mesh_3d_stage", "atom_orbit_3d", "dna_helix_3d"):
        mesh_kind = d.get("mesh") or d.get("shape") or ("atom_orbit" if l == "atom_orbit_3d" else ("dna_helix" if l == "dna_helix_3d" else "torus_3d"))
        stage.draw_glass_card((80, SY0 + 20, 1000, SY0 + 670), radius=30, accent_col=world["cyan"], alpha_mul=g0, active=True, layered=True)
        draw_procedural_3d_mesh(stage, 540, SY0 + 340, 260, str(mesh_kind), _res_col(world, d.get("color"), "cyan"), progress=progress, active=True, alpha_mul=g0, secondary_color=world["purple"])
        cap = str(d.get("caption") or d.get("formula") or mesh_kind.replace("_", " ").title())
        stage.draw_pill(540, SY0 + 625, cap[:30], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(23, bold=True), alpha_mul=_sub_gate(_spring_gate(progress, 0, 4, 0.22), "badge"))
        pts = list(d.get("points") or d.get("items") or d.get("notes") or [])[:4]
        for i, pt in enumerate(pts):
            gt = _spring_gate(progress, i + 1, len(pts) + 1, 0.22)
            if gt <= 0.02:
                continue
            g_b, g_t = _sub_gate(gt, "box"), _sub_gate(gt, "title")
            y = SY0 + 695 + i * 96
            col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((80, y, 1000, y + 82), radius=20, accent_col=col, alpha_mul=g_b, active=(int(progress * len(pts)) == i))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (112, y + 20), str(pt.get("title") if isinstance(pt, dict) else pt), _get_font(24, bold=True), _with_alpha(world["text"], g_t), 850, max_lines=2)
        return True

    # --- 2. NEURAL NET & AGENT / RAG / MINDMAP / ORBIT PIPELINES ---
    if l == "neural_net_layers":
        layers = list(d.get("layers") or [4, 6, 5, 3])[:5]
        names = list(d.get("layer_names") or [f"Layer {i+1}" for i in range(len(layers))])
        n_l = len(layers)
        stage.draw_glass_card((74, SY0 + 18, 1006, SY1 - 92), radius=26, accent_col=world["purple"], alpha_mul=g0)
        lx_xs = [int(165 + i * (750 / max(1, n_l - 1))) for i in range(n_l)]
        pts_per_layer: List[List[Tuple[int, int]]] = []
        for i, cnt in enumerate(layers):
            c_cnt = min(6, max(2, int(cnt)))
            ys = [int(840 - (c_cnt - 1) * 56 + k * 112) for k in range(c_cnt)]
            pts_per_layer.append([(lx_xs[i], y) for y in ys])
        for i in range(n_l - 1):
            gt = _spring_gate(progress, i, n_l, 0.22)
            g_lnk = _sub_gate(gt, "link")
            if g_lnk <= 0.02:
                continue
            c_line = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            for p0 in pts_per_layer[i]:
                for p1 in pts_per_layer[i + 1]:
                    ex = int(p0[0] + (p1[0] - p0[0]) * g_lnk)
                    ey = int(p0[1] + (p1[1] - p0[1]) * g_lnk)
                    stage.draw.line((p0[0], p0[1], ex, ey), fill=_with_alpha((*c_line[:3], 95), g_lnk), width=2)
        for i, layer_pts in enumerate(pts_per_layer):
            gt = _spring_gate(progress, i, n_l, 0.22)
            if gt <= 0.02:
                continue
            g_b, g_t = _sub_gate(gt, "box"), _sub_gate(gt, "title")
            nc = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            if g_t > 0.02:
                stage.draw_pill(lx_xs[i], SY0 + 70, str(names[i] if i < len(names) else f"L{i+1}")[:12], world["card_alt"], nc, border_col=nc, font=_get_font(20, bold=True), alpha_mul=g_t)
            for px, py in layer_pts:
                stage.draw.ellipse((px - 18, py - 18, px + 18, py + 18), fill=_with_alpha(nc, g_b), outline=_with_alpha(world["glass_rim"], g_b), width=2)
        ft_txt = str(d.get("footer") or d.get("summary") or " -> ".join(str(x)[:14] for x in names[:4]))
        if gf > 0.03 and ft_txt:
            stage.draw_glass_card((80, SY1 - 78, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), ft_txt[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return True

    if l in ("rag_pipeline_3d", "agent_loop_3d", "mindmap_radial", "orbit_ecosystem"):
        hub = str(d.get("center") or d.get("hub_name") or l.replace("_", " ").title()).strip()
        items = list(d.get("nodes") or d.get("steps") or d.get("branches") or d.get("satellites") or ["Plan", "Tool", "Observe", "Refine"])[:6]
        cx, cy, rad = 540, 845, 315
        for rr in (180, 290, 385):
            stage.draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=_with_alpha((*world["cyan"][:3], 42), g0), width=2)
        draw_procedural_3d_mesh(stage, cx, cy - 18, 68, "geodesic_sphere" if l != "agent_loop_3d" else "atom_orbit", world["cyan"], progress=progress, active=True, alpha_mul=g0)
        stage.draw_pill(cx, cy + 56, hub[:20], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g0)
        n = len(items)
        for i, it in enumerate(items):
            if isinstance(it, str):
                it = {"name": it}
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_ico, g_t, g_lnk = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "link")
            ang = -math.pi / 2.0 + i * (2.0 * math.pi / n) + (progress * 0.28 if l == "orbit_ecosystem" else 0.0)
            px, py = int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))
            col = _res_col(world, it.get("color"), _ACCENT_CYCLE[(i + 1) % len(_ACCENT_CYCLE)])
            _bezier(stage, (cx, cy), (px, py), col, reveal=max(g_b, g_lnk), progress=progress, phase=i * 0.2, label=str(it.get("edge", "")), curve_bend=24, world=world)
            stage.draw_glass_card((px - 135, py - 46, px + 135, py + 48), radius=20, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_ico > 0.02:
                _draw_vis(stage, px, py - 74, 34, 16, 22, col, g_ico, shape=it.get("shape", "hexagon"), icon=it.get("icon", ""), label=it.get("name", ""), progress=progress)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (px - 122, py - 24), str(it.get("name") or it.get("title") or ""), _get_font(22, bold=True), _with_alpha(world["text"], g_t), 244, align="center", max_lines=2)
        ft_txt = str(d.get("footer") or d.get("summary") or f"{hub} • {len(items)} Connected Stages")
        if gf > 0.03 and ft_txt:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), ft_txt[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return True

    # --- 3. MATRIX / HEATMAPS / SCATTER / CHARTS ---
    if l in ("attention_heatmap", "heatmap_matrix", "confusion_matrix"):
        vals = d.get("matrix") or d.get("grid") or [[0.9, 0.2, 0.1, 0.05], [0.15, 0.85, 0.3, 0.1], [0.1, 0.25, 0.88, 0.2], [0.05, 0.1, 0.2, 0.92]]
        xlabels = list(d.get("x_labels") or d.get("labels") or [f"K{i+1}" for i in range(len(vals[0]))])
        ylabels = list(d.get("y_labels") or d.get("labels") or [f"Q{i+1}" for i in range(len(vals))])
        stage.draw_glass_card((74, SY0 + 20, 1006, SY1 - 40), radius=26, accent_col=world["cyan"], alpha_mul=g0)
        rows_n = min(6, len(vals))
        cols_n = min(6, len(vals[0]) if vals else 4)
        cell_w = min(145, 730 // max(1, cols_n))
        cell_h = min(145, 730 // max(1, rows_n))
        ox = 220
        oy = SY0 + 145
        for c_i in range(cols_n):
            stage.draw.text((ox + c_i * cell_w + 20, oy - 48), str(xlabels[c_i] if c_i < len(xlabels) else f"C{c_i}")[:8], font=_get_font(21, bold=True), fill=_with_alpha(world["cyan"], g0))
        for r_i in range(rows_n):
            stage.draw.text((106, oy + r_i * cell_h + cell_h // 2 - 14), str(ylabels[r_i] if r_i < len(ylabels) else f"R{r_i}")[:8], font=_get_font(21, bold=True), fill=_with_alpha(world["purple"], g0))
            for c_i in range(cols_n):
                gt = _ease(_spring_gate(progress, r_i * cols_n + c_i, rows_n * cols_n, 0.18))
                v = float(vals[r_i][c_i]) if c_i < len(vals[r_i]) else 0.2
                v_n = max(0.05, min(1.0, v / 100.0 if v > 1.0 else v))
                base_col = world["emerald"] if v_n >= 0.7 else (world["cyan"] if v_n >= 0.35 else world["card_layer"])
                bx0, by0 = ox + c_i * cell_w + 6, oy + r_i * cell_h + 6
                stage.draw.rounded_rectangle((bx0, by0, bx0 + cell_w - 12, by0 + cell_h - 12), radius=14, fill=_with_alpha((*base_col[:3], int(80 + 165 * v_n)), gt), outline=_with_alpha(world["border"], gt), width=1)
                stage.draw.text((bx0 + 18, by0 + cell_h // 2 - 20), f"{v:.2f}" if isinstance(v, float) and v <= 1.0 else str(v), font=_get_font(22, bold=True, mono=True), fill=_with_alpha(world["text"], gt))
        return True

    if l in ("line_area_chart", "candlestick_pro", "token_prob_bars", "scatter_plot", "embedding_cluster"):
        stage.draw_glass_card((74, SY0 + 20, 1006, SY1 - 40), radius=26, accent_col=world["cyan"], alpha_mul=g0, active=True)
        ax0, ay0, ax1, ay1 = 150, SY0 + 120, 955, SY1 - 150
        stage.draw.line((ax0, ay1, ax1, ay1), fill=_with_alpha(world["border"], g0), width=3)
        stage.draw.line((ax0, ay0, ax0, ay1), fill=_with_alpha(world["border"], g0), width=3)

        if l in ("scatter_plot", "embedding_cluster"):
            clusters = list(d.get("clusters") or d.get("points") or [
                {"label": "Cluster A", "x": 0.28, "y": 0.32}, {"label": "Cluster B", "x": 0.72, "y": 0.28}, {"label": "Cluster C", "x": 0.52, "y": 0.74}
            ])[:12]
            for i, cl in enumerate(clusters):
                gt = _ease(_spring_gate(progress, i, len(clusters), 0.20))
                if isinstance(cl, str):
                    cl = {"label": cl, "x": (i + 1) * 0.2, "y": 0.5}
                px = int(ax0 + float(cl.get("x", 0.2 + (i % 4) * 0.2)) * (ax1 - ax0))
                py = int(ay0 + float(cl.get("y", 0.25 + (i // 4) * 0.25)) * (ay1 - ay0))
                col = _res_col(world, cl.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                stage.add_glow_orb(px, py, 36, col, alpha=int(120 * gt))
                stage.draw.ellipse((px - 16, py - 16, px + 16, py + 16), fill=_with_alpha(col, gt), outline=_with_alpha(world["glass_rim"], gt), width=2)
                if cl.get("label"):
                    stage.draw_pill(px, py - 34, str(cl["label"])[:16], world["card_alt"], world["text"], border_col=col, font=_get_font(18, bold=True), alpha_mul=gt)
        elif l == "token_prob_bars":
            toks = list(d.get("tokens") or d.get("items") or [{"token": "quantum", "prob": 0.78}, {"token": "neural", "prob": 0.14}, {"token": "vector", "prob": 0.05}, {"token": "other", "prob": 0.03}])[:6]
            rh = min(130, (ay1 - ay0) // max(1, len(toks)))
            for i, tk in enumerate(toks):
                if isinstance(tk, str):
                    tk = {"token": tk, "prob": 0.5}
                gt = _ease(_spring_gate(progress, i, len(toks), 0.22))
                pr = max(0.04, min(1.0, float(tk.get("prob", 0.5))))
                col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                y = ay0 + 20 + i * rh
                stage.draw.text((ax0 + 16, y), str(tk.get("token") or "")[:16], font=_get_font(24, bold=True, mono=True), fill=_with_alpha(world["text"], gt))
                bw = max(24, int(520 * pr * gt))
                stage.draw.rounded_rectangle((ax0 + 230, y + 4, ax0 + 230 + bw, y + 40), radius=10, fill=_with_alpha(col, gt))
                stage.draw.text((ax0 + 245 + bw, y + 6), f"{pr*100:.1f}%", font=_get_font(22, bold=True), fill=_with_alpha(col, gt))
        else:
            series = list(d.get("values") or d.get("points") or [22, 34, 29, 51, 68, 62, 89, 96])[:12]
            nums = [float(x.get("y") if isinstance(x, dict) else x) for x in series]
            mn, mx = min(nums + [0.0]), max(nums + [1.0])
            # Dashed horizontal gridlines & clean Y-axis tick values for readable charts
            for frac in (0.25, 0.5, 0.75, 1.0):
                gy = int(ay1 - frac * (ay1 - ay0))
                tick_val = mn + frac * (mx - mn)
                for gx in range(ax0, ax1, 20):
                    stage.draw.line((gx, gy, min(ax1, gx + 10), gy), fill=_with_alpha((*world["border"][:3], 95), g0), width=1)
                stage.draw.text((88, gy - 12), f"{int(round(tick_val))}", font=_get_font(17, mono=True), fill=_with_alpha(world["muted"], g0))
            coords = []
            for i, val in enumerate(nums):
                px = int(ax0 + (i / max(1, len(nums) - 1)) * (ax1 - ax0))
                py = int(ay1 - ((val - mn) / max(1e-4, mx - mn)) * (ay1 - ay0))
                coords.append((px, py))
            show_n = max(2, int(len(coords) * min(1.0, progress / 0.72)))
            pts = coords[:show_n]
            if l == "candlestick_pro":
                cw = max(22, (ax1 - ax0) // (len(coords) * 2))
                for i, (px, py) in enumerate(pts):
                    up = (i == 0) or (nums[i] >= nums[i - 1])
                    cc = world["emerald"] if up else world["rose"]
                    stage.draw.line((px, max(ay0, py - 48), px, min(ay1, py + 48)), fill=_with_alpha(cc, g0), width=4)
                    stage.draw.rounded_rectangle((px - cw // 2, py - 24, px + cw // 2, py + 24), radius=6, fill=_with_alpha(cc, g0), outline=_with_alpha(world["text"], g0 * 0.45), width=1)
            else:
                if len(pts) >= 2:
                    poly = [(pts[0][0], ay1)] + pts + [(pts[-1][0], ay1)]
                    stage.draw.polygon(poly, fill=_with_alpha((*world["cyan"][:3], 48), g0))
                    stage.add_glow_line(pts, world["cyan"], width=12, alpha=145)
                    stage.draw.line(pts, fill=_with_alpha(world["cyan"], g0), width=6)
                for idx_pt, (px, py) in enumerate(pts):
                    stage.draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=_with_alpha(world["emerald"], g0), outline=_with_alpha(world["text"], g0), width=2)
                    if idx_pt == len(pts) - 1:
                        stage.add_glow_orb(px, py, 24, world["emerald"], alpha=int(150 * g0))
                        stage.draw_pill(min(890, max(210, px)), max(ay0 + 24, py - 38), f"Peak: {nums[idx_pt]:.0f}", world["card_alt"], world["emerald"], border_col=world["emerald"], font=_get_font(18, bold=True), alpha_mul=g0)
        if d.get("caption"):
            stage.draw_pill(540, SY1 - 88, str(d["caption"])[:40], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(20, bold=True), alpha_mul=g0)
        return True

    if l == "donut_3d":
        slices = list(d.get("slices") or d.get("items") or [{"label": "Compute", "value": 45}, {"label": "Storage", "value": 30}, {"label": "Network", "value": 25}])[:5]
        tot = sum(max(1.0, float(s.get("value", 20))) for s in slices)
        cx, cy, rad = 540, 660, 215
        cur_ang = -90.0
        for i, sl in enumerate(slices):
            gt_raw = _spring_gate(progress, i, len(slices), 0.24)
            if gt_raw <= 0.02:
                continue
            g_b, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            v = float(sl.get("value", 20))
            ang = (v / tot) * 360.0 * g_b
            col = _res_col(world, sl.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            if ang > 1.0:
                stage.draw.pieslice((cx - rad, cy - rad, cx + rad, cy + rad), start=cur_ang, end=cur_ang + ang, fill=_with_alpha(col, g_b), outline=_with_alpha(world["bg_top"], g_b), width=4)
            cur_ang += (v / tot) * 360.0
            ly = 940 + i * 74
            stage.draw_glass_card((110, ly, 970, ly + 60), radius=16, accent_col=col, alpha_mul=g_b, active=(int(progress * len(slices)) == i))
            stage.draw.ellipse((136, ly + 18, 160, ly + 42), fill=_with_alpha(col, g_b))
            if g_t > 0.02:
                stage.draw.text((182, ly + 15), str(sl.get("label") or "")[:30], font=_get_font(23, bold=True), fill=_with_alpha(world["text"], g_t))
            if g_s > 0.02:
                stage.draw.text((830, ly + 15), f"{int(round(v/tot*100))}%", font=_get_font(23, bold=True), fill=_with_alpha(col, g_s))
        stage.draw.ellipse((cx - 108, cy - 108, cx + 108, cy + 108), fill=_with_alpha(world["bg_top"], g0), outline=_with_alpha(world["border"], g0), width=3)
        _draw_wrapped(stage.draw, (cx - 90, cy - 22), str(d.get("center") or "TOTAL"), _get_font(26, bold=True), _with_alpha(world["text"], g0), 180, align="center", max_lines=2)
        return True

    if l == "radar_spider":
        axes = list(d.get("axes") or d.get("metrics") or [{"label": "Speed", "value": 92}, {"label": "Scale", "value": 85}, {"label": "Cost", "value": 78}, {"label": "Safety", "value": 90}, {"label": "DX", "value": 88}])[:6]
        cx, cy, rad = 540, 845, 285
        n = len(axes)
        for ring in (0.33, 0.66, 1.0):
            poly = [(cx + int(rad * ring * math.cos(-math.pi / 2 + i * 2 * math.pi / n)), cy + int(rad * ring * math.sin(-math.pi / 2 + i * 2 * math.pi / n))) for i in range(n)]
            stage.draw.polygon(poly, outline=_with_alpha((*world["border"][:3], 120), g0))
        v_poly = []
        for i, ax in enumerate(axes):
            if isinstance(ax, str):
                ax = {"label": ax, "value": 75}
            gt_raw = _spring_gate(progress, i, n, 0.22)
            g_b, g_t = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title")
            val = max(10.0, min(100.0, float(ax.get("value", 75)))) * max(0.15, g_b)
            ang = -math.pi / 2 + i * 2 * math.pi / n
            vx, vy = int(cx + rad * (val / 100.0) * math.cos(ang)), int(cy + rad * (val / 100.0) * math.sin(ang))
            v_poly.append((vx, vy))
            if g_t > 0.02:
                lx, ly = int(cx + (rad + 58) * math.cos(ang)), int(cy + (rad + 58) * math.sin(ang))
                stage.draw_pill(lx, ly, str(ax.get("label") or "")[:12], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(19, bold=True), alpha_mul=g_t)
        if len(v_poly) >= 3:
            gp = _ease(min(1.0, max(0.2, progress * 1.15)))
            stage.draw.polygon(v_poly, fill=_with_alpha((*world["cyan"][:3], 92), gp), outline=_with_alpha(world["cyan"], gp), width=4)
        return True

    if l == "sankey_flow":
        flows = list(d.get("flows") or [{"from": "Direct", "to": "Signup", "weight": 0.55}, {"from": "Organic", "to": "Signup", "weight": 0.45}, {"from": "Signup", "to": "Paid", "weight": 0.62}])[:5]
        for i, fl in enumerate(flows):
            gt_raw = _spring_gate(progress, i, len(flows), 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_t, g_lnk = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "link")
            y0 = SY0 + 50 + i * 162
            col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((80, y0, 340, y0 + 106), radius=18, accent_col=col, alpha_mul=g_b)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (96, y0 + 34), str(fl.get("from", "Source")), _get_font(23, bold=True), _with_alpha(world["text"], g_t), 228, align="center", max_lines=2)
            if g_lnk > 0.02:
                _bezier(stage, (345, y0 + 53), (735, y0 + 53), col, reveal=g_lnk, progress=progress, label=str(fl.get("label") or f"{int(float(fl.get('weight', 0.5))*100)}%"), world=world)
                stage.draw_glass_card((740, y0, 1000, y0 + 106), radius=18, accent_col=world["emerald"], alpha_mul=g_lnk)
                _draw_wrapped(stage.draw, (756, y0 + 34), str(fl.get("to", "Target")), _get_font(23, bold=True), _with_alpha(world["text"], g_lnk), 228, align="center", max_lines=2)
        return True

    # --- 4. UI / SOCIAL / PRODUCT MOCKUPS ---
    if l == "mobile_app_mockup":
        stage.draw_glass_card((245, SY0 + 16, 835, SY1 - 16), radius=54, accent_col=world["cyan"], alpha_mul=g0, active=True, layered=True)
        stage.draw.rounded_rectangle((465, SY0 + 34, 615, SY0 + 58), radius=12, fill=_with_alpha(world["card_layer"], g0))
        app_items = list(d.get("screens") or d.get("items") or [{"title": "Live Inference", "sub": "42 tokens/sec"}, {"title": "Cache Hit", "sub": "0.3ms Redis"}, {"title": "Status: Healthy", "sub": "99.99% Uptime"}])[:4]
        for i, it in enumerate(app_items):
            if isinstance(it, str):
                it = {"title": it}
            gt = _ease(_spring_gate(progress, i, len(app_items), 0.22))
            y = SY0 + 100 + i * 210
            col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
            stage.draw_glass_card((285, y, 795, y + 172), radius=24, accent_col=col, alpha_mul=gt)
            _draw_wrapped(stage.draw, (315, y + 34), str(it.get("title") or ""), _get_font(27, bold=True), _with_alpha(world["text"], gt), 450, max_lines=2)
            if it.get("sub"):
                _draw_wrapped(stage.draw, (315, y + 96), str(it["sub"]), _get_font(21), _with_alpha(col, gt), 450, max_lines=2)
        return True

    if l == "browser_window":
        stage.draw_glass_card((74, SY0 + 20, 1006, SY1 - 24), radius=26, accent_col=world["purple"], alpha_mul=g0, active=True)
        for k, cc in enumerate(((244, 63, 94), (245, 158, 11), (16, 185, 129))):
            stage.draw.ellipse((104 + k * 28, SY0 + 48, 120 + k * 28, SY0 + 64), fill=_with_alpha(cc, g0))
        stage.draw_pill(560, SY0 + 56, str(d.get("url") or "https://app.studio.dev")[:36], world["card_layer"], world["muted"], border_col=world["border"], font=_get_font(20, mono=True), alpha_mul=g0, pad_x=60, pad_y=6)
        _draw_wrapped(stage.draw, (120, SY0 + 165), str(d.get("headline") or d.get("title") or "Interactive Web App"), _get_font(44, bold=True), _with_alpha(world["text"], g0), 840, align="center", max_lines=2)
        _draw_wrapped(stage.draw, (140, SY0 + 305), str(d.get("body") or d.get("sub") or ""), _get_font(27), _with_alpha(world["muted"], g0), 800, align="center", max_lines=4)
        if d.get("cta"):
            stage.draw_pill(540, SY0 + 560, str(d["cta"])[:24], world["cyan"], (255, 255, 255), font=_get_font(26, bold=True), alpha_mul=g0, pad_x=36, pad_y=16)
        return True

    if l == "chat_thread_ai":
        msgs = list(d.get("messages") or [{"role": "user", "text": "Why did latency spike?"}, {"role": "ai", "text": "Connection pool exhausted at 480 concurrent reads."}, {"role": "user", "text": "Fix it fast!"}, {"role": "ai", "text": "Enabled PgBouncer transaction pooling -> dropped P99 from 900ms to 12ms."}])[:5]
        y = SY0 + 30
        for i, m in enumerate(msgs):
            if isinstance(m, str):
                m = {"role": "ai" if i % 2 else "user", "text": m}
            gt_raw = _spring_gate(progress, i, len(msgs), 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title")
            is_user = str(m.get("role", "")).lower() in ("user", "human", "right")
            bx0, bx1 = (240, 990) if is_user else (86, 840)
            col = world["cyan"] if is_user else world["emerald"]
            stage.draw_glass_card((bx0, y, bx1, y + 165), radius=24, accent_col=col, alpha_mul=g_b, active=(int(progress * len(msgs)) == i))
            if g_bdg > 0.02:
                stage.draw_pill(bx0 + 82, y + 32, "YOU" if is_user else "AI STUDIO", (*col[:3], 42), col, border_col=col, font=_get_font(17, bold=True), alpha_mul=g_bdg)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (bx0 + 26, y + 66), str(m.get("text") or ""), _get_font(23), _with_alpha(world["text"], g_t), (bx1 - bx0) - 52, max_lines=3)
            y += 188
        return True

    if l in ("notification_stack", "kanban_board", "pricing_tiers", "timeline_gantt", "pros_cons_scale"):
        items = list(d.get("columns") or d.get("tiers") or d.get("tasks") or d.get("items") or [{"title": "Tier 1", "sub": "Baseline"}, {"title": "Tier 2", "sub": "Optimized"}, {"title": "Tier 3", "sub": "Scale"}])[:4]
        n = len(items)
        if l in ("kanban_board", "pricing_tiers"):
            cw = (SW - (n - 1) * 20) // max(1, n)
            for i, it in enumerate(items):
                if isinstance(it, str):
                    it = {"title": it}
                gt_raw = _spring_gate(progress, i, n, 0.22)
                if gt_raw <= 0.02:
                    continue
                g_b, g_t = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title")
                x0 = SX0 + i * (cw + 20)
                col = _res_col(world, _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                stage.draw_glass_card((x0, SY0 + 40, x0 + cw, SY1 - 60), radius=22, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
                if g_t > 0.02:
                    _draw_wrapped(stage.draw, (x0 + 16, SY0 + 70), str(it.get("title") or it.get("name") or ""), _get_font(25, bold=True), _with_alpha(col, g_t), cw - 32, align="center", max_lines=2)
                sub_list = it.get("cards") or it.get("features") or ([it.get("sub")] if it.get("sub") else [])
                for j, c_txt in enumerate(list(sub_list)[:4]):
                    cj_g = _sub_gate(_spring_gate(progress, i + j * 0.25, n + 1, 0.20), "sub")
                    if cj_g <= 0.02:
                        continue
                    cy = SY0 + 160 + j * 145
                    stage.draw_glass_card((x0 + 16, cy, x0 + cw - 16, cy + 120), radius=16, accent_col=col, alpha_mul=cj_g)
                    _draw_wrapped(stage.draw, (x0 + 28, cy + 28), str(c_txt), _get_font(21), _with_alpha(world["text"], cj_g), cw - 56, align="center", max_lines=3)
        else:
            rh = min(175, (SH - 60) // max(1, n))
            for i, it in enumerate(items):
                if isinstance(it, str):
                    it = {"title": it}
                gt_raw = _spring_gate(progress, i, n, 0.22)
                if gt_raw <= 0.02:
                    continue
                g_b, g_ico, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
                y = SY0 + 40 + i * rh
                col = _res_col(world, it.get("color"), _ACCENT_CYCLE[i % len(_ACCENT_CYCLE)])
                stage.draw_glass_card((80, y, 1000, y + rh - 18), radius=22, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
                if g_ico > 0.02:
                    draw_vector_glyph(stage, 136, y + (rh - 18) // 2, str(it.get("icon") or "bell"), 22, col, g_ico)
                if g_t > 0.02:
                    _draw_wrapped(stage.draw, (186, y + 26), str(it.get("title") or it.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], g_t), 780, max_lines=1)
                if (it.get("sub") or it.get("range")) and g_s > 0.02:
                    _draw_wrapped(stage.draw, (186, y + 68), str(it.get("sub") or it.get("range")), _get_font(21), _with_alpha(world["muted"], g_s), 780, max_lines=2)
        return True

    # --- 5. QUOTE / SPLIT SCREEN / EQUATION / BEFORE-AFTER / COUNTDOWN ---
    if l in ("quote_spotlight", "equation_proof", "countdown_hero"):
        stage.draw_glass_card((80, SY0 + 95, 1000, SY1 - 125), radius=34, accent_col=world["amber"], alpha_mul=g0, active=True, layered=True)
        big = _anim_num(d.get("value") or d.get("formula") or d.get("quote") or "O(log N)", progress) if l == "countdown_hero" else str(d.get("formula") or d.get("quote") or d.get("statement") or "E = mc^2")
        _draw_wrapped(stage.draw, (124, SY0 + 250), big, _get_font(62 if len(big) < 18 else 40, bold=True, mono=(l == "equation_proof")), _with_alpha(world["amber"] if l == "countdown_hero" else world["text"], g0), 832, align="center", max_lines=4)
        sub = str(d.get("author") or d.get("explanation") or d.get("sub") or "").strip()
        if sub:
            stage.draw_pill(540, SY1 - 210, sub[:34], world["card_alt"], world["cyan"], border_col=world["cyan"], font=_get_font(24, bold=True), alpha_mul=g0)
        return True

    if l in ("split_screen_50_50", "before_after_slider"):
        sep_x = int(540 + (math.sin(progress * math.pi * 2.0) * 140 if l == "before_after_slider" else 0))
        stage.draw_glass_card((72, SY0 + 30, sep_x - 10, SY1 - 30), radius=24, accent_col=world["rose"], alpha_mul=g0)
        _draw_wrapped(stage.draw, (96, SY0 + 90), str(d.get("left_label") or "BEFORE"), _get_font(30, bold=True), _with_alpha(world["rose"], g0), max(120, sep_x - 130), align="center", max_lines=2)
        _draw_wrapped(stage.draw, (96, SY0 + 200), str(d.get("left_text") or "\n".join(d.get("left_points", []))), _get_font(23), _with_alpha(world["text"], g0), max(120, sep_x - 130), max_lines=8)
        stage.draw_glass_card((sep_x + 10, SY0 + 30, 1008, SY1 - 30), radius=24, accent_col=world["emerald"], alpha_mul=g0, active=True)
        _draw_wrapped(stage.draw, (sep_x + 30, SY0 + 90), str(d.get("right_label") or "AFTER"), _get_font(30, bold=True), _with_alpha(world["emerald"], g0), max(120, 960 - sep_x), align="center", max_lines=2)
        _draw_wrapped(stage.draw, (sep_x + 30, SY0 + 200), str(d.get("right_text") or "\n".join(d.get("right_points", []))), _get_font(23), _with_alpha(world["text"], g0), max(120, 960 - sep_x), max_lines=8)
        stage.draw.line((sep_x, SY0 + 20, sep_x, SY1 - 20), fill=_with_alpha(world["amber"], g0), width=5)
        return True

    return True
