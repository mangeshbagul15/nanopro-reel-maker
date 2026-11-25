import math
import re
from typing import Any, Dict, List, Tuple

_ACCENT = ("cyan", "purple", "emerald", "amber", "rose")
SX0, SY0, SX1, SY1 = 64, 358, 1016, 1426
SW, SH = SX1 - SX0, SY1 - SY0

# =========================================================================
# 220 DOMAIN-SPECIFIC TECH, CS, SYSTEM DESIGN & ARCHITECTURE PRESETS
# 11 Engineering Domains x 20 Distinct Layouts = 220 Unique Named Layouts
# Archetypes: 'flow', 'tiers', 'ring', 'split', 'hub', 'grid', 'seq', 'slots', 'code_flow', 'triangle', 'table'
# =========================================================================
_RAW_DOMAIN_SPECS: List[Tuple[str, str, str, Tuple[str, ...]]] = [
    # 1. ALGORITHMS & DATA STRUCTURES (20)
    ("binary_search_trace", "slots", "O(log N) Halving Window", ("low=0..7", "mid=3 Check", "Discard Left", "Found Target")),
    ("two_pointers_window", "slots", "Two Pointers Convergence", ("Left Pointer L=0", "Window Sum Check", "Right Pointer R=N-1", "O(N) Solution")),
    ("sliding_window_buffer", "flow", "Fixed / Dynamic Sliding Window", ("Expand Right", "Update State", "Shrink Left", "Max Answer")),
    ("quicksort_partition", "tree", "Pivot Partition Divide", ("Choose Pivot", "Left < Pivot", "Right >= Pivot", "In-Place Swap")),
    ("mergesort_divide", "tree", "Stable Divide & Merge", ("Split Half", "Sort Subarrays", "Two-Pointer Merge", "O(N log N)")),
    ("heap_priority_tree", "tree", "Binary Min/Max Heap", ("Root Min/Max", "Heapify Down", "Parent <= Child", "O(log N) Pop")),
    ("trie_prefix_tree", "tree", "Prefix Character Trie", ("Root ''", "Branch 'a'->'p'", "Terminal Flag", "O(L) Autocomplete")),
    ("bloom_filter_bits", "slots", "Probabilistic Membership", ("Item -> k Hashes", "Bit Array Set 1", "0 = Definite No", "1 = Maybe Yes")),
    ("skip_list_lanes", "tiers", "Multi-Level Skip Express Lanes", ("Level 3 Express", "Level 2 Jump", "Level 1 Fast", "Level 0 All Keys")),
    ("lru_cache_eviction", "dual", "HashMap O(1) + Doubly Linked List", ("HashMap Lookup -> O(1) Ptr", "Move Head MRU <-> Evict Tail LRU")),
    ("union_find_dsu", "hub", "Disjoint Set Path Compression", ("Root Representative", "Union By Rank", "Path Compression", "O(alpha(N)) Find")),
    ("dijkstra_shortest_path", "flow", "Greedy Priority Queue Relaxation", ("Init dist=0", "Pop Min Heap", "Relax Neighbors", "Shortest Path Tree")),
    ("bfs_dfs_traversal", "dual", "Level Queue vs Recursive Stack", ("BFS Queue (Shortest Hop)", "DFS Stack (Backtracking & Paths)")),
    ("topological_sort_dag", "flow", "Kahn In-Degree DAG Ordering", ("Compute In-Degrees", "Queue Zero In-Degree", "Decrement Edges", "Valid Build Order")),
    ("segment_tree_ranges", "tree", "Range Query & Lazy Propagation", ("Full [0..N-1] Sum", "Left [0..N/2]", "Right [N/2+1..N-1]", "O(log N) Update")),
    ("monotonic_stack", "slots", "Next Greater Element Stack", ("Push Candidate", "Pop Smaller Elements", "Record Next Greater", "O(N) Linear Pass")),
    ("kadane_dp_table", "slots", "Max Subarray Running DP", ("Current Element", "max(x, cur+x)", "Update Global Best", "O(N) / O(1) Space")),
    ("knapsack_dp_grid", "table", "2D State Transition Matrix", ("Item|Cap 1|Cap 2|Cap 3", "Wt 1|$10|$15|$20", "Wt 2|$10|$25|$35", "Best|$10|$25|$40")),
    ("consistent_hashing_ring", "ring", "Virtual Node Hash Ring", ("Hash Key 0..2^32", "Node A vNodes", "Node B vNodes", "Clockwise Lookup")),
    ("merkle_tree_proof", "tree", "Cryptographic Hash Verification", ("Top Merkle Root", "Left Sub-Hash", "Right Sub-Hash", "Leaf Block Hashes")),

    # 2. DATABASE INTERNALS & STORAGE ENGINES (20)
    ("b_plus_tree_pages", "tree", "4KB Slotted Disk B+Tree", ("Root Index Page", "Internal Keys", "Sorted Leaf Pages", "Doubly-Linked Range Scan")),
    ("lsm_tree_compaction", "flow", "Append MemTable -> SSTable Levels", ("Write WAL + MemTable", "Flush Immutable L0", "Leveled Compaction", "Bloom + SSTable")),
    ("write_ahead_log_wal", "flow", "Sequential Crash-Safe Redo Log", ("Append WAL Frame", "fsync Sequential Disk", "Update Dirty Page", "Async Checkpoint")),
    ("mvcc_snapshot_versions", "tiers", "Multi-Version Row Tuple Visibility", ("Tx 104 Snapshot (Read)", "Row v3 (xmin=105 Hidden)", "Row v2 (xmin=101 Visible)", "Zero Read Locks")),
    ("two_phase_commit_2pc", "seq", "Coordinator Prepare & Commit Protocol", ("Coord->P1:PREPARE", "Coord->P2:PREPARE", "P1->Coord:VOTE YES", "Coord->All:COMMIT")),
    ("saga_orchestration", "flow", "Compensating Distributed Transactions", ("Reserve Inventory", "Charge Payment", "Failure -> Refund", "Eventual Consistency")),
    ("sharding_hash_range", "hub", "Horizontal Partition Routing", ("Shard Router", "Shard 01 (A-G)", "Shard 02 (H-P)", "Shard 03 (Q-Z)")),
    ("read_replica_lag", "dual", "Primary Write vs Async Follower", ("Primary RW (WAL Stream)", "Replica RO (Replication Lag ms)")),
    ("multi_master_crdt", "hub", "Conflict-Free Replicated Data Types", ("G-Counter Merge", "LWW Element Set", "No Central Lock", "Strong Eventual Sync")),
    ("columnar_parquet_blocks", "slots", "Row Group Column Encoding", ("Header Metadata", "Col A RLE Compressed", "Col B Dict Encoded", "Footer Min/Max Stats")),
    ("index_seek_vs_scan", "dual", "B-Tree Seek vs Full Table Scan", ("Index Seek O(log N) ms", "Seq Full Scan O(N) Pages")),
    ("buffer_pool_lru", "slots", "Clock-Sweep Shared Memory Frames", ("Pin Page in RAM", "Dirty Bit Flag", "Clock Evict Unpinned", "99% Hit Ratio")),
    ("bloom_sstable_lookup", "flow", "Negative Lookup Skip Fastpath", ("Query Key ID", "Check In-RAM Bloom", "Miss -> Skip Disk!", "Hit -> Binary Search")),
    ("deadlock_wait_graph", "ring", "Cyclic Lock Wait Detection", ("Tx A Waits Row 2", "Row 2 Held by Tx B", "Tx B Waits Row 1", "Kill Youngest Tx")),
    ("isolation_levels_matrix", "table", "ANSI SQL Anomaly Prevention", ("Level|Dirty|NonRep|Phantom", "Read Comm|No|Yes|Yes", "Repeatable|No|No|Mostly", "Serial|No|No|No")),
    ("time_series_chunks", "tiers", "Hypertable Time-Partitioned Chunks", ("Today Hot Chunk (RAM)", "Last Week Compressed", "Last Quarter Glacier", "Time Pruning Skip")),
    ("geospatial_quadtree", "tree", "2D Spatial Bounding Subdivision", ("World BBox", "NE/NW Quadrants", "City Tiles", "R-Tree Proximity")),
    ("full_text_inverted_idx", "dual", "Tokenize Stemming -> Posting Lists", ("Doc Text -> Stem Tokens", "Term -> [Doc1, Doc4, Doc9]")),
    ("hnsw_vector_graph", "tiers", "Hierarchical Navigable Small World", ("Layer 2 Coarse Hops", "Layer 1 Medium Links", "Layer 0 Dense K-NN", "Cosine ANN Search")),
    ("ivf_pq_quantization", "flow", "Compressed Billion-Scale Vectors", ("Split Centroids IVF", "Sub-Vector PQ Codes", "90% RAM Reduction", "Fast Asymmetric Dist")),

    # 3. DISTRIBUTED SYSTEMS & RESILIENCE (20)
    ("raft_leader_election", "ring", "Split-Vote Term & Quorum Majority", ("Follower Timeout", "Candidate ReqVote", "Majority Ack >= N/2+1", "Leader Heartbeat")),
    ("paxos_quorum_rounds", "seq", "Prepare/Promise & Accept/Accepted", ("Proposer->All:Prepare N", "Acceptor->Prop:Promise", "Prop->All:Accept(N,V)", "Learner:Chosen V")),
    ("cap_theorem_triangle", "triangle", "Partition Forces C or A Choice", ("Consistency (Linearizable)", "Availability (Every Req)", "Partition Tolerance (Network)")),
    ("pacelc_tradeoff", "dual", "Partition (A vs C) Else (L vs C)", ("On Partition: Avail vs Consist", "Normal Mode: Latency vs Consist")),
    ("circuit_breaker_states", "ring", "Fail-Fast Fault Isolation FSM", ("CLOSED (Normal Flow)", "Error Threshold -> OPEN", "Timeout -> HALF-OPEN", "Probe OK -> CLOSED")),
    ("rate_limiter_token_bucket", "flow", "Burst-Tolerant Token Bucket", ("Refill R Tokens/s", "Capacity Cap Max", "Req Consumes 1 Token", "Empty -> HTTP 429")),
    ("sliding_window_limiter", "slots", "Redis ZSET Exact Timestamp Log", ("Remove Expired Entries", "Count Current Window", "Under Limit -> Allow", "Over -> Reject 429")),
    ("leaky_bucket_shaper", "flow", "Constant-Rate Traffic Smoothing", ("Bursty Ingress Traffic", "FIFO Queue Buffer", "Fixed Leak Rate Output", "Drops Overflow")),
    ("retry_exponential_backoff", "slots", "Jittered Retry Delay Progression", ("Attempt 1: 100ms", "Attempt 2: 200ms+Jitter", "Attempt 3: 400ms+Jitter", "Max Cap -> Circuit Open")),
    ("dead_letter_queue_dlq", "flow", "Poison Message Quarantine", ("Primary Consumer", "Retry x3 Failed", "Route to DLQ Topic", "Alert & Replay Tool")),
    ("idempotency_key_store", "flow", "Exactly-Once Payment Execution", ("Client UUID Key", "Check Redis Lock", "Duplicate -> Cached Resp", "New -> Execute Once")),
    ("outbox_pattern_cdc", "flow", "Atomic DB + Event Publishing", ("Single ACID Tx", "Write Orders + Outbox", "Debezium Relay Reads", "Guaranteed Kafka Pub")),
    ("gossip_protocol_cluster", "hub", "Decentralized Peer State Sync", ("Node Seed Gossip", "Random Peer Exchange", "O(log N) Convergence", "Zero Single Point")),
    ("vector_clock_causality", "seq", "Logical Happens-Before Versioning", ("Node A: [1,0,0]", "Node B: [1,1,0]", "Concurrent Conflict!", "Client Merge LWW")),
    ("distributed_lock_redlock", "ring", "Multi-Node Fencing Token Lock", ("Acquire N/2+1 Masters", "TTL Lease Timer", "Monotonic Fencing ID", "Safe Storage Write")),
    ("leaderless_quorum_rw", "hub", "Dynamo W + R > N Consistency", ("Coordinator Node", "Write W Replicas", "Read R Replicas", "Read Repair Stale")),
    ("backpressure_reactive", "flow", "Consumer-Driven Pull Demand", ("Fast Producer", "Bounded Buffer Queue", "Slow Consumer Signal", "Pull Demand N Items")),
    ("bulkhead_isolation", "tiers", "Tenant / Pool Failure Containment", ("Pool A (Checkout 20 Threads)", "Pool B (Search Isolated)", "Search Slow != Checkout Down")),
    ("service_discovery_dns", "flow", "Dynamic Ephemeral Instance Registry", ("Pod Boot Register", "Health Probe Check", "Update Registry Map", "Client Route Lookup")),
    ("heartbeat_failover", "seq", "Keepalive Lease Expiry Switchover", ("Primary->Standby:HB 1s", "Primary Crashes!", "Standby Missed 3 HBs", "Promote New Primary")),

    # 4. OS, KERNEL, COMPILERS & HARDWARE (20)
    ("virtual_memory_paging", "flow", "MMU TLB Virtual -> Physical Frame", ("Virtual Addr 0x7FF", "TLB Fast Cache Hit", "Page Table Walk", "Physical RAM Frame")),
    ("cpu_pipeline_fetch_exec", "slots", "5-Stage Instruction Pipelining", ("1. Fetch (IF)", "2. Decode (ID)", "3. Execute (EX)", "4. Mem/Writeback")),
    ("l1_l2_l3_cache_tiers", "tiers", "Hardware Memory Latency Pyramid", ("Registers (0.3ns)", "L1/L2 Cache (1-4ns)", "Shared L3 (15ns)", "DRAM Main Memory (100ns)")),
    ("syscall_kernel_trap", "seq", "User Ring 3 -> Kernel Ring 0 Transition", ("App:read() Syscall", "CPU:Trap Ring 3->0", "Kernel:VFS Disk Read", "Kernel->App:Return Buf")),
    ("process_thread_context", "dual", "Isolated Process vs Shared Thread Heap", ("Process: Separate Virtual RAM", "Threads: Shared Heap, Fast Switch")),
    ("epoll_event_loop", "ring", "Non-Blocking I/O Multiplexing", ("Register FDs epoll_ctl", "Kernel Wait epoll_wait", "Dispatch Ready Events", "10k+ C10K Connections")),
    ("mutex_semaphore_locks", "dual", "Exclusive Binary Mutex vs Counting Semaphore", ("Mutex: 1 Owner Lock/Unlock", "Semaphore: N Concurrent Permits")),
    ("copy_on_write_fork", "flow", "Zero-Copy Page Sharing Until Write", ("fork() Shares Read Pages", "Page Marked Read-Only", "Write Triggers Fault", "Allocate Private Copy")),
    ("garbage_collector_generations", "tiers", "Generational Mark-Sweep & Compact", ("Eden Young Gen (Minor GC)", "Survivor S0/S1", "Tenured Old Gen", "Major Compact Sweep")),
    ("jit_tier_compilation", "flow", "Bytecode -> Hot Profiled Machine Code", ("Cold Interpreter", "Execution Counter++", "Hot Loop Detected", "JIT Native x86/ARM64")),
    ("llvm_ir_optimizer", "flow", "Frontend -> Target-Independent SSA IR", ("C++/Rust AST", "Lower to LLVM IR", "Opt Passes (-O3)", "Codegen x86/WASM")),
    ("ast_lexer_parser", "flow", "Source Text -> Token Stream -> AST", ("Source String", "Lexer Tokens", "Recursive Parser", "Executable AST Tree")),
    ("cuda_gpu_warp_grid", "tiers", "SIMT Streaming Multiprocessor Hierarchy", ("Grid of Thread Blocks", "Shared SRAM Block", "32-Thread SIMD Warp", "Tensor Core FP16 Matrix")),
    ("simd_vector_lanes", "slots", "AVX-512 Single Instruction Multiple Data", ("Lane 0..3 Float32", "Lane 4..7 Float32", "Parallel ALU Add", "4x-16x Vector Speed")),
    ("dma_zero_copy_io", "dual", "Standard Kernel Copy vs sendfile() DMA", ("Legacy: 4 Copies + 4Ctx Switch", "DMA Zero-Copy: NIC <- PageCache")),
    ("nvme_submission_queue", "flow", "64K Lockless PCIe Submission Rings", ("Core Submission Queue", "Doorbell Register Write", "NVMe Controller DMA", "Completion Interrupt")),
    ("numa_memory_nodes", "dual", "Socket-Local vs Cross-QPI Interconnect", ("CPU0 <-> Local RAM (Fast)", "CPU0 -> Socket1 RAM (Penalty)")),
    ("interrupt_irq_handler", "flow", "Hardware Top-Half vs Deferred Bottom-Half", ("NIC Packet IRQ Pin", "Top-Half Ack Fast", "SoftIRQ ksoftirqd", "Network Stack NAPI")),
    ("docker_cgroups_namespaces", "tiers", "Linux Container Isolation Primitives", ("Namespaces: PID/Net/Mnt View", "cgroups v2: CPU/RAM Quotas", "OverlayFS Copy Layers", "Zero Hypervisor Overhead")),
    ("ebpf_kernel_hooks", "flow", "Sandboxed In-Kernel Verifier Bytecode", ("Write eBPF C Program", "Kernel Verifier Safety", "JIT Attach Tracepoint", "Zero Overhead Metrics")),

    # 5. SECURITY, CRYPTOGRAPHY & IDENTITY (20)
    ("oauth2_pkce_flow", "seq", "Public Client Code Verifier + Challenge", ("App->Auth:Challenge SHA256", "User->Auth:Consent Login", "Auth->App:Auth Code", "App->Auth:Code+Verifier->JWT")),
    ("oidc_id_token_flow", "flow", "Authentication Identity Layer on OAuth2", ("OIDC Scope openid", "Verify Signed ID Token", "Read Claims (sub/email)", "Call UserInfo Endpoint")),
    ("jwt_header_payload_sig", "slots", "Base64URL Stateless Token Anatomy", ("Header (Alg: RS256)", "Payload (sub, exp, role)", "HMAC/RSA Signature", "Tamper Proof Stateless")),
    ("tls_13_handshake", "seq", "1-RTT Encrypted Forward-Secret Setup", ("Client->Srv:ClientHello+KeyShare", "Srv->Client:Hello+Cert+Finished", "Client->Srv:Encrypted App Data", "Forward Secrecy ECDHE")),
    ("mtls_mutual_cert", "dual", "Two-Way X.509 Identity Verification", ("Server Proves Cert to Client", "Client Proves Cert to Server")),
    ("diffie_hellman_key_ex", "flow", "Public Exchange -> Shared Secret", ("Public Base g, Mod p", "Private Keys a & b", "Swap g^a & g^b", "Identical Shared g^ab")),
    ("rsa_asymmetric_keys", "dual", "Public Key Encrypt vs Private Decrypt", ("Public Key: Encrypt / Verify Sig", "Private Key: Decrypt / Sign")),
    ("aes_gcm_cipher", "flow", "Authenticated Encryption (Confidential + Tag)", ("Nonce IV + Key", "CTR Stream Encrypt", "GMAC Auth Tag", "Detect Bit Tampering")),
    ("hmac_signature_verify", "flow", "Timing-Safe Webhook Integrity Check", ("Payload + Timestamp", "HMAC-SHA256(Secret)", "Compare Constant-Time", "Reject Replay >5min")),
    ("merkle_zkp_proof", "flow", "Verify Fact Without Revealing Secret", ("Prover Private Witness", "Commit + Challenge", "Verify Polynomial Eq", "Zero Knowledge Leak")),
    ("passkey_webauthn_fido2", "seq", "Phishing-Resistant Biometric Public Key", ("Browser->User:FaceID Prompt", "Device Signs Origin+Challenge", "Server Verifies Stored PubKey", "No Password Stored!")),
    ("rbac_abac_policy", "dual", "Role Hierarchy vs Context Attributes", ("RBAC: role == 'admin'", "ABAC: dept=='fin' AND time<18h")),
    ("secrets_vault_rotation", "flow", "Dynamic Short-Lived DB Credentials", ("App Requests Vault", "Mint Temp User (TTL 1h)", "Auto-Revoke On Expiry", "Zero Static Passwords")),
    ("kms_envelope_encrypt", "flow", "DEK Encrypts Data + KEK Wraps DEK", ("Generate Local DEK", "Encrypt 10GB File Fast", "KMS Encrypts Tiny DEK", "Store Cipher + WrappedKey")),
    ("xss_csp_defense", "tiers", "Defense-in-Depth Browser Script Lock", ("Strict Output Escaping", "HttpOnly SameSite Cookies", "Content-Security-Policy Nonce", "Block Inline Eval()")),
    ("sql_injection_prepared", "dual", "Unsafe String Concat vs Parameterized AST", ("Concat: ' OR 1=1 -- Pwned", "Prepared: Bind ? Param Data Only")),
    ("csrf_samesite_token", "flow", "Cross-Origin Request Forgery Prevention", ("SameSite=Lax Cookie", "Custom Anti-CSRF Header", "Origin Header Match", "Block Forged Forms")),
    ("ddos_anycast_scrubbing", "flow", "Edge Volumetric L3/L4/L7 Mitigation", ("Global Anycast PoPs", "BGP Sinkhole Floods", "WAF JS Challenge", "Clean Origin Traffic")),
    ("sbom_supply_chain", "flow", "Signed Provenance SLSA Artifacts", ("Pin SHA256 Deps", "Generate CycloneDX SBOM", "Cosign Keyless Sign", "Verify At K8s Admit")),
    ("siem_soc_triage", "flow", "Ingest Logs -> Correlate -> Auto-Contain", ("EDR + Firewall + CloudTrail", "Sigma Rule Correlation", "Anomaly Risk Score", "Auto Isolate Compromised Pod")),

    # 6. WEB, PROTOCOLS, REALTIME & API ENGINEERING (20)
    ("http1_vs_http2_vs_http3", "tiers", "Evolution of Web Transport Multiplexing", ("HTTP/1.1: Serial + HOL Block", "HTTP/2: Binary Stream Mux (TCP)", "HTTP/3: QUIC UDP 0-RTT Streams")),
    ("quic_zero_rtt_flow", "flow", "Combined Transport + TLS Over UDP", ("UDP Socket Open", "1-RTT Initial Handshake", "0-RTT Session Resume", "Connection Migration WiFi->5G")),
    ("cors_preflight_options", "seq", "Cross-Origin Browser Security Handshake", ("Browser->API:OPTIONS Preflight", "API->Browser:Allow-Origin+Methods", "Browser->API:Actual POST Req")),
    ("websocket_duplex_frames", "seq", "Persistent Bidirectional Frame Socket", ("Client->Srv:HTTP 101 Upgrade", "Full-Duplex Binary Frames", "Low-Overhead Heartbeat Ping")),
    ("sse_server_events", "flow", "Lightweight HTTP One-Way AI Token Stream", ("GET Accept: text/event-stream", "Keep-Alive Connection", "data: token chunks\\n\\n", "Auto-Reconnect Built-In")),
    ("webrtc_ice_stun_turn", "seq", "Peer-to-Peer NAT Traversal Media Setup", ("PeerA->STUN:Find Public IP", "Signal SDP via WebSocket", "Direct UDP / TURN Relay Fallback")),
    ("graphql_federation_subgraphs", "hub", "Unified Supergraph Across Microservices", ("Apollo Router Gateway", "Users Subgraph", "Orders Subgraph", "Inventory Subgraph")),
    ("grpc_protobuf_mux", "dual", "Verbose JSON/HTTP1.1 vs Binary Protobuf/HTTP2", ("REST: Text JSON Keys Repeated", "gRPC: Compact Field Tags + Stream")),
    ("rest_hateoas_resources", "flow", "Stateless Resource URIs & Hypermedia Links", ("GET /orders/42", "Status 200 JSON + _links", "Action URL: /orders/42/pay", "Cacheable ETag Header")),
    ("webhook_hmac_retries", "flow", "Reliable Outbound Event Delivery", ("Enqueue Event Job", "Sign X-Signature Header", "POST Endpoint 5s Timeout", "Exponential Retry 24h")),
    ("ssr_vs_csr_vs_rsc", "tiers", "Modern Web Rendering Spectrum", ("CSR: Empty HTML -> JS Fetch", "SSR: Server HTML -> Hydrate", "RSC: Zero-Bundle Server Stream")),
    ("islands_architecture", "slots", "Static Zero-JS HTML + Interactive Islands", ("Static Header/Article", "Interactive Cart Island", "Interactive Search Island", "Tiny JS Hydration")),
    ("edge_worker_middleware", "flow", "Zero-Cold-Start V8 Isolate Logic", ("User Nearest Edge PoP", "Auth + A/B Rewrite (<1ms)", "Regional Geo Routing", "Serve Cached Shell")),
    ("service_worker_cache", "flow", "Offline Browser Intercept Proxy", ("Fetch Event Intercept", "Stale-While-Revalidate", "Serve Instant Cache", "Background Network Refresh")),
    ("browser_critical_render", "flow", "HTML Bytes -> Pixels Painted at 60fps", ("Parse HTML -> DOM", "Parse CSS -> CSSOM", "Layout Geometry", "Paint & GPU Composite")),
    ("dom_shadow_vdom_diff", "flow", "Minimal Batched Real DOM Mutations", ("State Change Trigger", "Render Virtual Tree", "Reconcile O(N) Diff", "Commit Exact DOM Patch")),
    ("stripe_payment_intent", "seq", "Two-Step Idempotent Card Capture", ("Client->API:Create Intent", "Client->Stripe:Confirm 3DS", "Stripe->API:Webhook Paid!", "API:Fulfill Order Safely")),
    ("idempotent_checkout_ledger", "flow", "Double-Entry Immutable Balance Safety", ("Lock Account Row", "Debit User Ledger -100", "Credit Merchant +100", "Sum Always Equals Zero")),
    ("long_polling_vs_stream", "dual", "Repeated Hold Requests vs Continuous Stream", ("Long Poll: Re-open After Data", "Stream: Single Open Socket")),
    ("oauth_refresh_rotation", "flow", "Detect Token Theft via Refresh Families", ("Short Access Token 15m", "One-Time Refresh Token", "Reuse Detected -> Revoke All", "Re-Auth Protection")),

    # 7. AI AGENTS, LLMS & MLOPS (20)
    ("transformer_multihead_attn", "flow", "Scaled Dot-Product Parallel Attention", ("Linear Q, K, V Proj", "MatMul Q*K^T / sqrt(d)", "Softmax Attention Weights", "Concat Heads -> MLP")),
    ("lora_qlora_adapters", "dual", "Frozen Base Weights vs Low-Rank A*B Matrices", ("Base W Frozen (16/4-bit)", "Train Tiny Rank r Adapters (<1%)")),
    ("dpo_rlhf_alignment", "flow", "Human Preference Optimization Pipeline", ("SFT Instruction Model", "Chosen vs Rejected Pairs", "DPO Direct Log-Prob Loss", "Aligned Safe Policy")),
    ("moe_router_experts", "hub", "Sparse Mixture-of-Experts Top-2 Gating", ("Router Gating Network", "Expert 1 (Code)", "Expert 2 (Math)", "Expert 3 (Reasoning)")),
    ("kv_cache_paged_attn", "slots", "Non-Contiguous GPU VRAM KV Blocks", ("Logical KV Sequence", "Block Table Mapping", "Paged Physical VRAM", "Zero Memory Fragmentation")),
    ("speculative_decoding", "flow", "Tiny Draft Model + Parallel Target Verify", ("Fast Draft 5 Tokens", "Large Model 1 Forward Pass", "Accept Matching Prefix", "2.5x Faster Decode!")),
    ("flash_attention_tiling", "dual", "Slow HBM N^2 Reads vs Fast On-Chip SRAM Tiles", ("Standard: Materialize NxN HBM", "FlashAttn: Fused SRAM Tiling")),
    ("multi_agent_supervisor", "hub", "Orchestrator Delegating Specialist Agents", ("Supervisor Planner", "Researcher Agent", "Coder Agent", "Reviewer QA Agent")),
    ("mcp_tool_protocol", "seq", "Standard Model Context Host-Client-Server", ("LLM->Host:Need DB Schema", "Host->MCP:call_tool(query)", "MCP->Host:Typed JSON Rows", "Host->LLM:Grounded Answer")),
    ("react_thought_action_obs", "ring", "Iterative Agent Reasoning Loop", ("Thought: Plan Next Step", "Action: Invoke Tool API", "Observation: Parse Output", "Reflect -> Final Answer")),
    ("graph_rag_knowledge", "hub", "Entity Graph Traversal + Vector Retrieval", ("Query Entities", "Community Summary", "2-Hop Neo4j Subgraph", "Synthesized Context")),
    ("hybrid_bm25_vector_rrf", "flow", "Lexical Keyword + Semantic Dense Fusion", ("BM25 Exact Match", "HNSW Vector Similarity", "Reciprocal Rank Fusion", "Cross-Encoder Rerank")),
    ("semantic_cache_hit", "flow", "Skip LLM Calls for Similar Prompts", ("Embed User Query", "Cosine Sim > 0.94", "Return Cached JSON (15ms)", "Save 70% GPU Cost")),
    ("guardrails_input_output", "tiers", "Dual-Stage Prompt & PII Safety Filter", ("Input: Prompt Injection Scan", "Core LLM Reasoning", "Output: PII Redact + Schema", "Safe Validated JSON")),
    ("llm_eval_judge_rubric", "flow", "Automated CI Regression Testing for Prompts", ("Golden Test Suite", "LLM Run Outputs", "Judge Model Scoring", "Track Faithfulness %")),
    ("fine_tuning_dataset_prep", "flow", "High-Signal Curation Beats Raw Volume", ("Collect Raw Traces", "Deduplicate MinHash", "Filter Toxicity/Length", "Format JSONL ChatML")),
    ("vllm_continuous_batch", "slots", "Iteration-Level Dynamic Request Scheduling", ("Req A finishes early", "Slot immediately reused!", "Req C joins mid-batch", "10x GPU Utilization")),
    ("quantization_fp16_int4", "tiers", "Bit-Width Compression Memory Footprint", ("FP32 (4 Bytes/Param)", "BF16/FP16 (2 Bytes)", "INT8/FP8 (1 Byte)", "AWQ/GGUF INT4 (0.5 Byte)")),
    ("multimodal_vision_patch", "flow", "ViT Image Patches -> Shared Token Space", ("Split Image 16x16 Patches", "Linear Vision Encoder", "Project To LLM Dim", "Unified Attention Reasoning")),
    ("synthetic_data_flywheel", "ring", "Self-Improving Model + Verifier Data Loop", ("Seed Real Prompts", "Generate Candidate Solns", "Unit Test / Verifier Filter", "Train Stronger Next Gen")),

    # 8. CLOUD, KUBERNETES & DEVSECOPS INTERNALS (20)
    ("k8s_control_plane", "hub", "Declarative Cluster Reconciliation Brain", ("kube-apiserver", "etcd Key-Value State", "kube-scheduler", "controller-manager")),
    ("k8s_pod_lifecycle", "flow", "Pending -> Init -> Running -> Terminating", ("Scheduler Node Assign", "Pull Container Image", "Startup/Readiness Probe", "SIGTERM Graceful Drain")),
    ("k8s_hpa_vpa_autoscale", "dual", "Horizontal Pod Count vs Vertical CPU/RAM", ("HPA: Scale Replicas 2 -> 50", "VPA: Resize Container Limits")),
    ("k8s_ingress_service_mesh", "flow", "External HTTPS -> Envoy Sidecar mTLS", ("Cloud Load Balancer", "Gateway / Ingress API", "Service ClusterIP", "Pod Sidecar Envoy mTLS")),
    ("helm_chart_release", "flow", "Versioned Templated Kubernetes Manifests", ("values.yaml Env Overrides", "Go Template Render", "Helm Diff Verification", "Atomic Release + Rollback")),
    ("terraform_plan_apply_state", "flow", "Immutable IaC Drift-Free Provisioning", ("HCL Config Files", "Lock Remote S3 State", "Preview Exact Plan", "Apply Cloud APIs")),
    ("docker_overlayfs_layers", "tiers", "Union Filesystem Read-Only Base + RW Top", ("Container RW Upper Layer", "App Code Layer (5MB)", "Dependencies Layer (120MB)", "Base OS Image Cached RO")),
    ("containerd_runc_shim", "flow", "CRI High-Level Runtime -> OCI Container", ("Kubelet gRPC CRI Call", "containerd Pulls Layers", "containerd-shim Spawns", "runc Linux Process")),
    ("prometheus_pull_scrape", "flow", "Time-Series /metrics Scraping & PromQL", ("Pod Exposes /metrics", "Prometheus Scrape 15s", "Local TSDB Blocks", "Alertmanager PagerDuty")),
    ("otel_collector_pipeline", "flow", "Vendor-Neutral Trace/Metric/Log Router", ("App OTLP SDK Export", "Batch & Tail-Sample", "Redact PII Attributes", "Fan-out Grafana/Datadog")),
    ("chaos_engineering_blast", "flow", "Proactive Controlled Production Faults", ("Define Steady State", "Inject Pod Kill / Latency", "Verify Auto-Recovery", "Patch Weak Links Early")),
    ("disaster_recovery_rto_rpo", "dual", "Recovery Time (Downtime) vs Recovery Point (Loss)", ("RPO: Max Acceptable Data Loss", "RTO: Max Time Back Online")),
    ("multi_region_active_active", "hub", "Zero-Regional-Outage Geo Distribution", ("GeoDNS Anycast", "US-East Active Cluster", "EU-West Active Cluster", "CRDT Async DB Sync")),
    ("finops_spot_rightsizing", "flow", "Cut Cloud Compute Bills by 50%+", ("Identify Idle CPU", "Karpenter Auto-Binpack", "Mixed Spot + Reserved", "S3 Lifecycle Tiering")),
    ("serverless_cold_start", "slots", "Provisioned MicroVM Warm vs Cold Boot", ("Download Code Bundle", "Boot Firecracker MicroVM", "Init Runtime Modules", "Warm Reuse <2ms Invoke")),
    ("iam_sts_assume_role", "seq", "Short-Lived Cloud Federation Credentials", ("Pod OIDC Token", "Call AWS STS AssumeRole", "Return Temp Keys (1h)", "Access S3 Least Priv")),
    ("gitops_reconcile_loop", "ring", "ArgoCD Desired Git vs Live Cluster Sync", ("Watch Git Repo Commit", "Compare Live K8s Diff", "OutOfSync Detected!", "Auto-Heal & Reconcile")),
    ("canary_analysis_kayenta", "flow", "Automated Statistical Metric Rollout Gate", ("Route 5% Canary Traffic", "Compare Baseline P99/5xx", "Pass Mann-Whitney Test", "Promote 100% Safely")),
    ("blue_green_dns_cutover", "dual", "Instant Zero-Warmup Environment Flip", ("Blue (Live 100%) Tested Standby", "Green Ready -> Instant LB Switch")),
    ("vault_dynamic_creds", "flow", "On-Demand Ephemeral Database Passwords", ("Service Auth JWT", "Vault Generates User", "App Connects to RDS", "Lease Expires Auto-Drop")),

    # 9. DATA PLATFORMS, ANALYTICS & STREAMING (20)
    ("iceberg_snapshot_manifest", "tree", "Atomic Table Snapshots & Time Travel", ("Metadata Pointer", "Manifest List Snap", "Parquet Data Files", "Time-Travel Query AS OF")),
    ("delta_lake_acid_log", "flow", "ACID Transactions on S3 Object Storage", ("00001.json Commit Log", "Optimistic Concurrency", "Add/Remove Parquet Refs", "Vacuum Old Snapshots")),
    ("parquet_rowgroup_cols", "slots", "Columnar Analytics Predicate Pushdown", ("Row Group 128MB", "Column Chunk Pages", "ZSTD Compression 6x", "Skip Irrelevant Blocks")),
    ("duckdb_vectorized_exec", "flow", "In-Process SIMD OLAP Vector Engine", ("Read Parquet Zero Copy", "2048-Row Vector Chunks", "SIMD Hash Join", "10x Faster Pandas")),
    ("flink_watermarks_windows", "flow", "Out-of-Order Stateful Stream Processing", ("Event Time Stamp", "Watermark Progress", "Allowed Lateness", "Checkpointed RocksDB")),
    ("kafka_consumer_rebalance", "flow", "Cooperative Sticky Partition Assignment", ("New Worker Joins Group", "Incremental Revoke Only", "Zero Stop-The-World", "Continue Lag-Free")),
    ("kafka_isr_replication", "hub", "Broker In-Sync Replicas acks=all Safety", ("Leader Partition P0", "Follower F1 In-Sync", "Follower F2 In-Sync", "Commit High Watermark")),
    ("clickhouse_mergetree", "tiers", "Sparse Primary Key Background Merge", ("Write Unsorted Parts", "Primary Granule Index", "Async Merge Compression", "Billion Rows <50ms")),
    ("trino_coordinator_workers", "hub", "Federated SQL Across Any Data Source", ("Trino Coordinator", "Worker Swarm (Memory)", "S3 Iceberg Connector", "Postgres + Kafka Join")),
    ("dbt_dag_lineage_tests", "flow", "Software-Engineered SQL Transformation", ("Staging Sources", "Intermediate Joins", "Schema & Not-Null Tests", "Auto Lineage Docs")),
    ("airflow_scheduler_exec", "flow", "DAG Parsing -> Queued Celery/K8s Pods", ("Scheduler Parse Python", "Push Ready Task IDs", "Worker Executes Operator", "Metadata DB State")),
    ("data_contract_protobuf", "flow", "Producer-Consumer Typed Schema SLA", ("Schema Definition PR", "CI Compatibility Check", "Reject Breaking Change", "Zero Pipeline Break")),
    ("slowly_changing_dim_scd2", "table", "Historical Attribute Tracking Row Versions", ("User|Tier|ValidFrom|Curr", "u1|Free|Jan 01|False", "u1|Pro|Mar 15|True", "Audit Time Accuracy")),
    ("reverse_etl_activation", "flow", "Sync Warehouse Insights Back to SaaS", ("Gold Churn Score SQL", "Incremental Diff Fetch", "Batch Upsert API", "Update CRM / Ads")),
    ("metric_semantic_layer", "tiers", "Single Source of Truth KPI Definitions", ("Central YAML Metrics", "Auto-Generated SQL Joins", "Looker / Tableau BI", "No Metric Drift!")),
    ("pivot_cube_olap", "hub", "Multi-Dimensional Slice & Dice Rollups", ("Measure: Revenue $", "Dim 1: Region", "Dim 2: Quarter", "Dim 3: Product SKU")),
    ("churn_cohort_retention", "table", "Monthly Customer Retention Matrix", ("Cohort|M0|M1|M2|M3", "Jan|100%|72%|65%|61%", "Feb|100%|78%|71%|-", "Mar|100%|81%|-|-")),
    ("ab_test_bayesian_lift", "dual", "Control Group vs Variant Treatment Lift", ("Control A: 3.2% Conv", "Variant B: 4.1% (+28% Lift!)")),
    ("attribution_multi_touch", "flow", "Channel Credit Across Conversion Path", ("Ad Impression (20%)", "Blog Search (30%)", "Webinar Demo (25%)", "Direct Signup (25%)")),
    ("time_series_forecast_ci", "slots", "Trend + Seasonality + Confidence Band", ("Historical Actuals", "Trend Component", "Weekly Seasonality", "Upper/Lower 95% CI")),

    # 10. MOBILE, DESIGN SYSTEMS & FRONTEND UI/UX (20)
    ("ios_swiftui_mvvm", "flow", "Declarative View Observing State Model", ("User Tap Action", "ViewModel Async Task", "Combine @Published", "Diffed SwiftUI Body")),
    ("android_compose_state", "flow", "Unidirectional State Hoisting Architecture", ("Event Up Lambda", "ViewModel StateFlow", "State Down Recompose", "Skip Unchanged Nodes")),
    ("offline_first_sync", "dual", "Optimistic Local SQLite + Background Sync", ("Local DB Instant Write 1ms", "Conflict CRDT Sync Online")),
    ("push_apns_fcm_flow", "flow", "Reliable Cross-Platform Mobile Notifications", ("Backend Trigger Event", "Token Device Lookup", "APNs / FCM Gateway", "Wake App Notification")),
    ("design_token_3tier", "tiers", "Primitive -> Semantic -> Component Tokens", ("Primitive: blue-500 #3B82F6", "Semantic: --color-primary", "Component: --btn-bg-hover")),
    ("a11y_wcag_audit", "tiers", "Accessible Semantic Web Standards", ("Contrast Ratio >= 4.5:1", "Keyboard Focus Order", "Semantic ARIA Landmarks", "Screen Reader Tested")),
    ("cwv_lcp_cls_inp", "slots", "Google Core Web Vitals Speed Targets", ("LCP Load < 2.5s", "INP Input < 200ms", "CLS Shift < 0.1", "SEO Boost Green")),
    ("state_redux_zustand", "ring", "Predictable Flux State Store Cycle", ("Dispatch Action", "Pure Reducer / Store", "Select Slice Hooks", "Minimal Re-Render")),
    ("virtual_list_windowing", "slots", "Render 15 Visible Rows Out of 100,000", ("Buffer Top Overscan", "Visible Viewport Rows", "Recycle DOM Nodes", "60fps Smooth Scroll")),
    ("optimistic_ui_rollback", "flow", "Zero-Latency Perceived UX Safety Net", ("User Clicks Like", "Update UI Immediately", "API Request Async", "Fail -> Revert + Toast")),
    ("responsive_breakpoints", "tiers", "Fluid Mobile-First CSS Grid Layout", ("Mobile < 640px (1 Col)", "Tablet >= 768px (2 Col)", "Desktop >= 1280px (4 Col)")),
    ("dark_light_theming", "dual", "Dynamic CSS Custom Property Tokens", ("Dark Mode Obsidian Surface", "Light Mode Editorial Paper")),
    ("microfrontend_module_fed", "hub", "Independent Frontend Teams Ship Together", ("Host App Shell", "Checkout Remote MF", "Search Remote MF", "Account Remote MF")),
    ("biometric_auth_flow", "flow", "Secure Enclave Hardware Key Unlock", ("Biometric Face/Touch Scan", "Unlock Keychain EC Key", "Sign Server Nonce", "Seamless Login")),
    ("deep_link_universal", "flow", "Universal Links Routing Web -> App Screen", ("Tap https://app.io/item/9", "OS Checks assetlinks.json", "Launch Exact App View", "Fallback Web If Uninstalled")),
    ("media_hls_abr_stream", "flow", "Adaptive Bitrate Chunk Streaming", ("Measure Bandwidth Mbps", "Manifest m3u8 Index", "Switch 1080p <-> 480p", "Zero Buffering Stall")),
    ("webgl_render_pipeline", "flow", "Vertex Shader -> Raster -> Fragment Pixels", ("3D Mesh Buffers", "Vertex Matrix Transform", "Triangle Rasterization", "Fragment Lighting PBR")),
    ("canvas_hit_testing", "flow", "QuadTree Spatial Pointer Interactivity", ("Pointer Move (x,y)", "Transform Matrix Inv", "QuadTree Region Check", "Exact Shape Hover")),
    ("lottie_vector_timeline", "flow", "After Effects JSON -> Native 60fps Curves", ("Export Vector Paths", "Zero Pixelation Any DPI", "Bind Scrub Progress", "50KB vs 5MB MP4")),
    ("pwa_manifest_sync", "flow", "Installable Web App + Background Sync", ("Manifest App Icons", "Service Worker Cache", "Background Queue Retry", "Native-Like Experience")),

    # 11. ARCHITECTURE PATTERNS, DDD & PRODUCT STRATEGY (20)
    ("hexagonal_ports_adapters", "hub", "Pure Domain Core Isolated from Infra", ("Domain Business Logic", "HTTP REST Adapter", "Postgres Repo Adapter", "Kafka Event Adapter")),
    ("clean_architecture_rings", "tiers", "Inward Dependency Rule Concentric Rings", ("Entities (Pure Core)", "Use Cases (App Rules)", "Interface Adapters", "Frameworks / DB / UI")),
    ("ddd_bounded_contexts", "hub", "Domain Language Isolation & Context Map", ("Shared Kernel", "Billing Context", "Shipping Context", "Catalog Context")),
    ("monolith_modular_vs_micro", "dual", "Start Modular Monolith vs Premature Microservices", ("Modular Monolith: Single Deploy", "Microservices: Network Cost + Scale")),
    ("strangler_fig_migration", "flow", "Incremental Zero-Downtime Legacy Rewrite", ("Edge Router Intercept", "Route New Paths -> v2", "Legacy Keeps Running", "Retire Old Monolith")),
    ("anti_corruption_layer", "flow", "Translate Messy Legacy Data Into Clean Domain", ("Legacy SOAP/XML", "ACL Translator Adapter", "Validate & Normalize", "Clean Modern Domain")),
    ("backend_for_frontend_bff", "hub", "Tailored API Aggregator Per Client Surface", ("Core Services Pool", "Mobile BFF (Compact)", "Web BFF (Rich Data)", "Public Partner API")),
    ("sidecar_ambassador_proxy", "dual", "Cross-Cutting Proxy Alongside App Container", ("App Container: Pure Business", "Sidecar Container: mTLS+Logs")),
    ("choreography_vs_orchestration", "dual", "Event-Driven Peer Reactors vs Central Conductor", ("Choreography: Loose Coupling", "Orchestration: Clear Workflow")),
    ("event_sourcing_snapshots", "flow", "Reconstruct State From Immutable Events", ("Append Domain Events", "Periodic Checkpoint Snap", "Replay Delta Since Snap", "Full Audit Trail")),
    ("tenancy_silo_bridge_pool", "tiers", "Multi-Tenant Data Isolation Models", ("Silo: Dedicated DB/Tenant", "Bridge: Shared DB, Row Schema", "Pool: Shared Table + TenantID")),
    ("gdpr_data_residency", "hub", "Regional Data Sovereignty & Right to Erasure", ("Global Control Router", "EU Vault (Frankfurt)", "US Vault (Virginia)", "Crypto-Shredding Delete")),
    ("north_star_metric_tree", "tree", "Decompose Product Outcome Into Levers", ("Weekly Active Teams", "Activation Rate %", "Retention Wk-4 %", "Referral Viral K-Factor")),
    ("rice_prioritization_matrix", "table", "Quantitative Roadmap Scoring Framework", ("Feature|Reach|Impact|Effort|Score", "AI Search|5k|3x|2w|750", "CSV Exp|1k|1x|1w|100", "Dark UI|4k|2x|1w|800")),
    ("user_journey_funnel", "tiers", "End-to-End Activation & Drop-Off Stages", ("Discovery & Ad (100%)", "Sign Up Flow (38%)", "Aha! First Value (24%)", "Paid Upgrade (7.5%)")),
    ("aarrr_pirate_metrics", "flow", "Startup Growth Engine Funnel Loops", ("Acquisition Traffic", "Activation First Win", "Retention Cohort", "Revenue & Referral")),
    ("okr_alignment_cascade", "tree", "Company Objective -> Team Key Results", ("Objective: #1 Speed", "KR1: P99 < 25ms", "KR2: Uptime 99.99%", "KR3: Cost -30%")),
    ("incident_sev_escalation", "tiers", "Paged On-Call Triage & SLA Tiers", ("SEV-1 Critical (<5m Page)", "SEV-2 Degraded (<15m)", "SEV-3 Minor Ticket", "Blameless Postmortem")),
    ("postmortem_5_whys", "flow", "Root Cause Systemic Fix Instead of Blame", ("Why 1: API Timed Out", "Why 2: DB CPU 100%", "Why 3: Missing Index", "Fix: Add CI Explain Check")),
    ("rfc_adr_decision_log", "flow", "Asynchronous Architecture Decision Records", ("Context & Constraints", "Evaluated Trade-Offs", "Chosen Decision + Owner", "Consequences & Review")),
]

DOMAIN_PRESETS_220: Dict[str, Tuple[str, str, Tuple[str, ...]]] = {
    name: (arch, sub, items) for name, arch, sub, items in _RAW_DOMAIN_SPECS
}
DOMAIN_220_LAYOUTS: Tuple[str, ...] = tuple(DOMAIN_PRESETS_220.keys())


# =========================================================================
# UNIVERSAL COMPOSABLE DIAGRAM GRAMMAR COMPILER (`compose_diagram_grammar`)
# =========================================================================
def _parse_grammar_items(spec_str: str, data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parses parameterized layout grammars like:
      - 'grid:3x3' / 'flow:5' / 'ring:6' / 'stack:5' / 'tree:3' / 'slots:6' / 'compare:2'
    or explicit `data["grammar"] = {"kind": "grid", "cols": 3, "rows": 2, ...}`.
    Creates unlimited layout topologies dynamically without hardcoding!
    """
    g = data.get("grammar") if isinstance(data.get("grammar"), dict) else {}
    raw = str(g.get("expr") or spec_str or "").lower().strip()
    kind = str(g.get("kind") or raw.split(":", 1)[0] or "flow").strip()
    param = raw.split(":", 1)[1] if ":" in raw else ""

    items = list(data.get("items") or data.get("nodes") or data.get("steps") or g.get("items") or [])
    norm: List[Dict[str, Any]] = []
    for it in items:
        norm.append({"name": it} if isinstance(it, str) else dict(it))

    if not norm:
        cnt = 4
        if "x" in param:
            parts = param.split("x")
            try:
                cnt = max(2, min(12, int(parts[0]) * int(parts[1])))
            except ValueError:
                cnt = 6
        elif param.isdigit():
            cnt = max(2, min(10, int(param)))
        norm = [{"name": f"Node {i+1}", "sub": f"{kind.upper()} Component"} for i in range(cnt)]

    return f"{kind}:{param}" if param else kind, norm


def _render_archetype(
    stage: Any,
    arch: str,
    title_sub: str,
    raw_items: Tuple[str, ...],
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> None:
    _get_font = helpers["_get_font"]
    _draw_wrapped = helpers["_draw_wrapped_text"]
    _with_alpha = helpers["_with_alpha"]
    _spring_gate = helpers["_spring_gate"]
    _ease = helpers["_ease_out_cubic"]
    _res_col = helpers["resolve_world_color"]
    _bezier = helpers["_draw_bezier_comet"]
    _draw_vis = helpers["_draw_node_visual"]

    user_items = list(data.get("items") or data.get("nodes") or data.get("steps") or data.get("stages") or [])
    items = user_items if user_items else [{"name": s} for s in raw_items]
    norm: List[Dict[str, Any]] = [{"name": x} if isinstance(x, str) else dict(x) for x in items]
    g0 = _ease(min(1.0, progress / 0.18))

    # Optional architectural subtitle strip at top of stage
    y_off = 0
    if title_sub:
        stage.draw_pill(540, SY0 + 18, title_sub[:44], (*world["cyan"][:3], 34), world["cyan"], border_col=world["border"], font=_get_font(19, bold=True), alpha_mul=g0)
        y_off = 44

    # 1. FLOW / CODE_FLOW -> Zigzag vertical stages with clear non-overlapping central Bezier pills
    if arch in ("flow", "code_flow"):
        n = min(5, len(norm))
        rh = min(215, (SH - y_off - 24) // max(1, n))
        prev_pt = None
        for i, it in enumerate(norm[:5]):
            gt = _ease(_spring_gate(progress, i, n, 0.22))
            if gt <= 0.03:
                continue
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            cy = SY0 + y_off + 72 + i * rh
            is_left = (i % 2 == 0)
            scx = 180 if is_left else 900
            cx0, cx1 = (278, 996) if is_left else (84, 802)
            active = (int(progress * n) == i)
            if prev_pt is not None:
                _bezier(stage, prev_pt, (460 if is_left else 620, cy - 52), col, reveal=gt, progress=progress, phase=i * 0.2, world=world)
            stage.draw_glass_card((cx0, cy - 48, cx1, cy + 50), radius=19, accent_col=col, alpha_mul=gt, active=active)
            _draw_vis(stage, scx, cy - 14, 42, 18, 28, col, gt, shape=it.get("shape", ""), icon=it.get("icon", ""), label=str(it.get("name", "")), active=active, progress=progress)
            stage.draw.line((scx + (50 if is_left else -50), cy, cx0 if is_left else cx1, cy), fill=_with_alpha(col, gt), width=3)
            _draw_wrapped(stage.draw, (cx0 + 22, cy - 30), str(it.get("name") or it.get("title") or ""), _get_font(24, bold=True), _with_alpha(world["text"], gt), cx1 - cx0 - 44, max_lines=2)
            if it.get("sub"):
                _draw_wrapped(stage.draw, (cx0 + 22, cy + 10), str(it["sub"]), _get_font(19), _with_alpha(world["muted"], gt), cx1 - cx0 - 44, max_lines=1)
            prev_pt = (460 if is_left else 620, cy + 52)
        return

    # 2. TIERS -> Horizontal architectural stack / memory layers
    if arch == "tiers":
        n = min(6, len(norm))
        rh = min(185, (SH - y_off - 24) // max(1, n))
        for i, it in enumerate(norm[:6]):
            gt = _ease(_spring_gate(progress, i, n, 0.20))
            if gt <= 0.03:
                continue
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            y = SY0 + y_off + 18 + i * rh
            h = rh - 14
            stage.draw_glass_card((80, y, 1000, y + h), radius=18, accent_col=col, alpha_mul=gt, active=(int(progress * n) == i))
            _draw_vis(stage, 146, y + h // 2 - 12, 32, 14, 22, col, gt, shape=it.get("shape", "layers_wafer"), icon=it.get("icon", ""), label=str(it.get("name", "")), active=(int(progress * n) == i), progress=progress)
            stage.draw_pill(242, y + h // 2, f"0{i+1}", (*col[:3], 42), col, border_col=col, font=_get_font(19, bold=True), alpha_mul=gt)
            _draw_wrapped(stage.draw, (296, y + max(12, h // 2 - 22)), str(it.get("name") or ""), _get_font(24, bold=True), _with_alpha(world["text"], gt), 680, max_lines=2)
        return

    # 3. RING -> Circular Raft / Circuit Breaker / Event Loop / Consistent Hash Ring
    if arch == "ring":
        cx, cy, rad = 540, SY0 + y_off + (SH - y_off) // 2, 325
        stage.draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=_with_alpha((*world["cyan"][:3], 72), g0), width=4)
        n = min(6, len(norm))
        pts = [(int(cx + rad * math.cos(-math.pi / 2 + i * 2 * math.pi / n)), int(cy + rad * math.sin(-math.pi / 2 + i * 2 * math.pi / n))) for i in range(n)]
        for i in range(n):
            gt = _ease(_spring_gate(progress, i, n, 0.22))
            _bezier(stage, pts[i], pts[(i + 1) % n], _res_col(world, _ACCENT[i % len(_ACCENT)]), reveal=gt, progress=progress, curve_bend=22, world=world)
        for i, it in enumerate(norm[:n]):
            gt = _ease(_spring_gate(progress, i, n, 0.22))
            if gt <= 0.03:
                continue
            px, py = pts[i]
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((px - 135, py - 42, px + 135, py + 44), radius=18, accent_col=col, alpha_mul=gt, active=(int(progress * n) == i))
            _draw_wrapped(stage.draw, (px - 122, py - 24), str(it.get("name") or ""), _get_font(20, bold=True), _with_alpha(world["text"], gt), 244, align="center", max_lines=2)
        return

    # 4. HUB -> Hub & Satellites Topology
    if arch == "hub":
        cx, cy = 540, SY0 + y_off + (SH - y_off) // 2
        hub_item = norm[0] if norm else {"name": "Core"}
        sats = norm[1:5] if len(norm) > 1 else [{"name": "Node 1"}, {"name": "Node 2"}, {"name": "Node 3"}]
        pos = [(265, SY0 + y_off + 170), (815, SY0 + y_off + 170), (265, SY1 - 140), (815, SY1 - 140)]
        for i, sat in enumerate(sats):
            gt = _ease(_spring_gate(progress, i + 1, len(sats) + 1, 0.22))
            if gt <= 0.03:
                continue
            sx, sy = pos[i % len(pos)]
            col = _res_col(world, sat.get("color"), _ACCENT[(i + 1) % len(_ACCENT)])
            _bezier(stage, (cx, cy), (sx, sy), col, reveal=gt, progress=progress, curve_bend=20, world=world)
            stage.draw_glass_card((sx - 165, sy - 54, sx + 165, sy + 56), radius=20, accent_col=col, alpha_mul=gt)
            _draw_vis(stage, sx, sy - 78, 36, 16, 22, col, gt, shape=sat.get("shape", ""), icon=sat.get("icon", ""), label=str(sat.get("name", "")), progress=progress)
            _draw_wrapped(stage.draw, (sx - 150, sy - 26), str(sat.get("name") or ""), _get_font(22, bold=True), _with_alpha(world["text"], gt), 300, align="center", max_lines=2)
        _draw_vis(stage, cx, cy - 26, 56, 24, 38, world["cyan"], g0, shape=hub_item.get("shape", "geodesic_sphere"), icon=hub_item.get("icon", ""), label=str(hub_item.get("name", "")), active=True, progress=progress)
        stage.draw_pill(cx, cy + 56, str(hub_item.get("name") or "")[:24], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g0)
        return

    # 5. DUAL -> Split Comparison / Trade-Off Cards
    if arch == "dual":
        pts_d = norm[:2] if len(norm) >= 2 else [norm[0], {"name": "Optimized Approach"}]
        for idx, it in enumerate(pts_d):
            gt = _ease(_spring_gate(progress, idx, 2, 0.24))
            col = world["rose"] if idx == 0 else world["emerald"]
            x0, x1 = (72, 520) if idx == 0 else (560, 1008)
            stage.draw_glass_card((x0, SY0 + y_off + 30, x1, SY1 - 50), radius=24, accent_col=col, alpha_mul=gt, active=(idx == 1), layered=(idx == 1))
            _draw_vis(stage, (x0 + x1) // 2, SY0 + y_off + 140, 56, 24, 36, col, gt, shape=it.get("shape", "hexagon" if idx else "box"), icon=it.get("icon", ""), label=str(it.get("name", "")), active=(idx == 1), progress=progress)
            _draw_wrapped(stage.draw, (x0 + 26, SY0 + y_off + 270), str(it.get("name") or ""), _get_font(28, bold=True), _with_alpha(world["text"], gt), x1 - x0 - 52, align="center", max_lines=5)
        stage.draw_pill(540, SY0 + y_off + 460, "VS", world["card_alt"], world["amber"], border_col=world["amber"], font=_get_font(26, bold=True), alpha_mul=g0)
        return

    # 6. SLOTS -> Horizontal Array / Memory / Cache / Bit / Vector Lanes
    if arch == "slots":
        n = min(6, len(norm))
        cw = (SW - (n - 1) * 14) // max(1, n)
        slot_y = SY0 + y_off + 140
        for i, it in enumerate(norm[:n]):
            gt = _ease(_spring_gate(progress, i, n, 0.20))
            if gt <= 0.03:
                continue
            x0 = SX0 + i * (cw + 14)
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((x0, slot_y, x0 + cw, slot_y + 290), radius=18, accent_col=col, alpha_mul=gt, active=(int(progress * n) == i))
            stage.draw_pill(x0 + cw // 2, slot_y + 38, f"[{i}]", (*col[:3], 42), col, border_col=col, font=_get_font(19, bold=True, mono=True), alpha_mul=gt)
            _draw_wrapped(stage.draw, (x0 + 12, slot_y + 92), str(it.get("name") or ""), _get_font(21 if n <= 4 else 18, bold=True), _with_alpha(world["text"], gt), cw - 24, align="center", max_lines=4)
        # Detail callout strip below memory array
        active_i = min(n - 1, int(progress * n))
        ac_col = _res_col(world, _ACCENT[active_i % len(_ACCENT)])
        stage.draw_glass_card((80, slot_y + 340, 1000, slot_y + 520), radius=22, accent_col=ac_col, alpha_mul=g0, active=True)
        _draw_wrapped(stage.draw, (112, slot_y + 390), f"Active Step [{active_i}]: {norm[active_i].get('name', '')}", _get_font(29, bold=True), _with_alpha(world["text"], g0), 856, align="center", max_lines=2)
        return

    # 7. TREE -> Root -> Children Hierarchy
    if arch == "tree":
        root_n = norm[0]
        children = norm[1:4] if len(norm) > 1 else [{"name": "Left Subtree"}, {"name": "Right Subtree"}]
        stage.draw_glass_card((310, SY0 + y_off + 20, 770, SY0 + y_off + 135), radius=22, accent_col=world["cyan"], alpha_mul=g0, active=True)
        _draw_wrapped(stage.draw, (330, SY0 + y_off + 54), str(root_n.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], g0), 420, align="center", max_lines=2)
        cn = len(children)
        cw = (SW - (cn - 1) * 24) // cn
        for i, ch in enumerate(children):
            gt = _ease(_spring_gate(progress, i + 1, cn + 1, 0.22))
            if gt <= 0.03:
                continue
            bx0 = SX0 + i * (cw + 24)
            col = _res_col(world, ch.get("color"), _ACCENT[(i + 1) % len(_ACCENT)])
            _bezier(stage, (540, SY0 + y_off + 136), (bx0 + cw // 2, SY0 + y_off + 310), col, reveal=gt, progress=progress, world=world)
            stage.draw_glass_card((bx0, SY0 + y_off + 312, bx0 + cw, SY0 + y_off + 530), radius=20, accent_col=col, alpha_mul=gt, active=(int(progress * cn) == i))
            _draw_vis(stage, bx0 + cw // 2, SY0 + y_off + 382, 40, 18, 26, col, gt, shape=ch.get("shape", "hexagon"), progress=progress)
            _draw_wrapped(stage.draw, (bx0 + 16, SY0 + y_off + 448), str(ch.get("name") or ""), _get_font(22, bold=True), _with_alpha(world["text"], gt), cw - 32, align="center", max_lines=2)
        return

    # 8. TRIANGLE -> Three-Corner Tradeoff (CAP Theorem)
    if arch == "triangle":
        pts = [(540, SY0 + y_off + 120), (225, SY1 - 150), (855, SY1 - 150)]
        for i in range(3):
            _bezier(stage, pts[i], pts[(i + 1) % 3], _res_col(world, _ACCENT[i % 3]), reveal=g0, progress=progress, world=world)
        for i, (px, py) in enumerate(pts):
            gt = _ease(_spring_gate(progress, i, 3, 0.25))
            col = _res_col(world, _ACCENT[i % 3])
            lbl = str(norm[i % len(norm)].get("name") or "")
            stage.draw_glass_card((px - 175, py - 65, px + 175, py + 65), radius=22, accent_col=col, alpha_mul=gt, active=(int(progress * 3) == i))
            _draw_wrapped(stage.draw, (px - 155, py - 24), lbl, _get_font(23, bold=True), _with_alpha(world["text"], gt), 310, align="center", max_lines=2)
        return

    # 9. SEQ -> Vertical Actor Lifelines Sequence Messages
    if arch == "seq":
        actors = ["Client/Proposer", "Coordinator/Gateway", "Cluster/Vault"]
        xs = [210, 540, 870]
        for i, act in enumerate(actors):
            ac = _res_col(world, _ACCENT[i])
            stage.draw_glass_card((xs[i] - 115, SY0 + y_off + 14, xs[i] + 115, SY0 + y_off + 92), radius=16, accent_col=ac, alpha_mul=g0, active=True)
            _draw_wrapped(stage.draw, (xs[i] - 105, SY0 + y_off + 36), act, _get_font(20, bold=True), _with_alpha(world["text"], g0), 210, align="center", max_lines=1)
            for ly in range(SY0 + y_off + 104, SY1 - 24, 24):
                stage.draw.line((xs[i], ly, xs[i], min(SY1 - 24, ly + 12)), fill=_with_alpha((*ac[:3], 125), g0), width=3)
        for i, it in enumerate(norm[:5]):
            gt = _ease(_spring_gate(progress, i, len(norm), 0.22))
            if gt <= 0.03:
                continue
            y = SY0 + y_off + 175 + i * 160
            _bezier(stage, (xs[i % 2], y), (xs[1 + ((i + 1) % 2)], y), _res_col(world, _ACCENT[i % len(_ACCENT)]), reveal=gt, progress=progress, label=str(it.get("name") or "")[:24], world=world)
        return

    # 10. TABLE -> Matrix / Isolation Levels / Cohort Matrix / Knapsack DP
    n_rows = min(5, len(norm))
    stage.draw_glass_card((76, SY0 + y_off + 20, 1004, SY0 + y_off + 80 + n_rows * 125), radius=24, accent_col=world["emerald"], alpha_mul=g0)
    for r_i, it in enumerate(norm[:n_rows]):
        gt = _ease(_spring_gate(progress, r_i, n_rows, 0.20))
        parts = str(it.get("name") or "").split("|")
        y = SY0 + y_off + 55 + r_i * 125
        cw = 880 // max(1, len(parts))
        if r_i == 0:
            stage.draw.rounded_rectangle((96, y - 8, 984, y + 60), radius=12, fill=_with_alpha((*world["emerald"][:3], 42), gt))
        for c_i, p_txt in enumerate(parts):
            stage.draw.text((112 + c_i * cw, y + 12), p_txt.strip()[:14], font=_get_font(21, bold=(r_i == 0), mono=True), fill=_with_alpha(world["emerald"] if r_i == 0 else world["text"], gt))


def render_domain_220_or_grammar(
    stage: Any,
    layout: str,
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> bool:
    l = str(layout or "").lower().strip()
    if l in DOMAIN_PRESETS_220:
        arch, sub, items = DOMAIN_PRESETS_220[l]
        _render_archetype(stage, arch, sub, items, data or {}, progress, world, helpers)
        return True

    # Handle universal Composable Diagram Grammar expressions (grid:3x2, flow:5, ring:6, tree:3, slots:5, tiers:4)
    if l.startswith(("grammar:", "grid:", "flow:", "ring:", "tree:", "slots:", "tiers:", "dual:")) or (data and data.get("grammar")):
        g_spec, g_items = _parse_grammar_items(l, data or {})
        kind = g_spec.split(":", 1)[0]
        arch = {"grid": "slots", "stack": "tiers"}.get(kind, kind)
        if arch not in ("flow", "tiers", "ring", "hub", "dual", "slots", "tree", "triangle", "seq", "table"):
            arch = "flow"
        _render_archetype(stage, arch, str((data or {}).get("subtitle") or g_spec.upper()), (), {"items": g_items}, progress, world, helpers)
        return True

    return False
