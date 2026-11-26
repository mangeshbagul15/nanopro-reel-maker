import math
import re
from typing import Any, Dict, List, Tuple

_ACCENT = ("cyan", "purple", "emerald", "amber", "rose")
SX0, SY0, SX1, SY1 = 64, 328, 1016, 1406
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

    # 12. AI AGENTS, LLMS & RETRIEVAL INTERNALS (20)
    ("llm_tokenization_bpe", "flow", "Byte-Pair Encoding Subword Vocabulary", ("Raw UTF-8 String", "Frequent Pair Merge", "Subword Token IDs", "Embedding Matrix Lookup")),
    ("llm_prefill_vs_decode", "dual", "Compute-Bound Prefill vs Memory-Bound Decode", ("Prefill: Parallel Prompt Matrix", "Decode: Autoregressive KV Read")),
    ("llm_kv_cache_vram", "slots", "Autoregressive Key/Value Tensor Reuse", ("Sys K/V", "Turn 1", "Turn 2", "Turn 3", "New Tok", "Cached")),
    ("rag_chunk_overlap_pipe", "flow", "Semantic Chunking + Vector + BM25 Hybrid", ("PDF / Markdown Parse", "Overlap 512-Tok Chunks", "Dense + BM25 Hybrid", "Cross-Encoder Rerank")),
    ("agent_react_tool_loop", "ring", "Think -> Act Tool Call -> Observe State", ("Goal State", "Reasoning Plan", "Tool Sandbox Call", "Observe Output", "Verify Answer")),
    ("mcp_client_host_server", "hub", "Universal Tool Protocol Over JSON-RPC", ("MCP Host IDE/Agent", "Filesystem Server", "Database Server", "GitHub/API Server")),
    ("llm_guardrails_safety", "tiers", "Input & Output Policy Enforcement Layers", ("PII & Jailbreak Scan", "Prompt Budget Check", "Structured JSON Schema", "Citation Grounding")),
    ("moe_sparse_routing", "tree", "Activate Only Top-2 of 8 Experts Per Token", ("Router Gate Softmax", "Code Expert E2 (0.62)", "Math Expert E5 (0.31)", "Zero Unused Compute")),
    ("lora_adapter_serving", "tiers", "Shared Base Model + Hot-Swapped Rank Adapters", ("Frozen Base FP16 Model", "Adapter A (Support)", "Adapter B (SQL Gen)", "Adapter C (Security)")),
    ("speculative_draft_verify", "flow", "Small Draft Proposes 4 Tokens -> Verified Once", ("0.5B Draft Speculate", "4 Candidate Tokens", "70B Single Forward", "Accept Prefix 3x Fast")),
    ("eval_golden_dataset", "table", "Deterministic Offline Regression Scorecard", ("Suite|Metric|Baseline|v2 Model", "SQL Gen|Pass@1|72%|94%", "Safety|Refusal|91%|99%", "Latency|P95|1.9s|0.8s")),
    ("vector_index_ivf_pq", "flow", "Cluster Centroids + Product Quantization", ("Full 1536-d Vector", "Coarse IVF Centroids", "PQ 64-Byte Compress", "Sub-10ms 100M Search")),
    ("voice_realtime_duplex", "flow", "Full-Duplex VAD + Streaming ASR + TTS", ("Audio Frame 20ms", "VAD Speech Barge-In", "Streaming Token LLM", "Chunked Voice Output")),
    ("structured_json_grammar", "flow", "Finite-State Mask Guarantees Valid JSON", ("JSON Schema Spec", "Compile FSM Transitions", "Mask Invalid Logits", "100% Parseable Output")),
    ("multi_agent_handoff", "seq", "Triage -> Specialist -> Verifier Choreography", ("Triage Agent Dispatch", "Domain Specialist Work", "QA Critique Checks", "Final Signed Response")),
    ("dpo_alignment_pairs", "dual", "Direct Preference Without Reward Model", ("Chosen Response (+Reward)", "Rejected Response (-Penalty)")),
    ("hallucination_citation_chk", "tiers", "Post-Generation Claim Verification Gates", ("Extract Atomic Claims", "Match Retrieved Chunks", "Flag Unsupported Span")),
    ("context_rot_attention", "triangle", "Signal vs Cost vs Window Trade-off", ("128K Window Capacity", "Attention Dilution", "Focused RAG Precision")),
    ("semantic_llm_caching", "flow", "Skip Expensive LLM Inference on Similar Queries", ("Embed Incoming Prompt", "Cosine Distance < 0.06", "Return Cached JSON (2ms)", "Save 70% GPU Spend")),
    ("agent_memory_hierarchy", "tiers", "Working Context -> Episodic -> Long-Term Store", ("In-Prompt Scratchpad", "Redis Session Memory", "Vector Episodic Recall", "SQL Profile Facts")),

    # 13. FRONTEND, WEB RUNTIME & BROWSERS (20)
    ("browser_critical_path", "flow", "HTML -> DOM/CSSOM -> Layout -> Paint -> Composite", ("Parse HTML Bytes -> DOM", "Build CSSOM + Exec JS", "Render Tree & Layout", "GPU Layer Composite")),
    ("react_fiber_reconciler", "tree", "Interruptible Work Loop Prioritizes Input", ("Root Fiber Node", "High-Prio Click Update", "Idle Background Render", "Commit DOM Mutations")),
    ("hydration_vs_resumability", "dual", "Replay Event Listeners vs Zero-JS Serialized State", ("Hydration: Download + Re-exec", "Resumable: Lazy On Interaction")),
    ("service_worker_cache_strat", "tiers", "Offline-First Interceptor Routing Policies", ("Cache-First (Static Shell)", "Stale-While-Revalidate", "Network-First (Live API)")),
    ("virtual_dom_diffing", "dual", "O(N) Keyed Reconciliation vs Naive O(N^3)", ("Unkeyed List Shift (Slow)", "Keyed ID Diff (Minimal Patch)")),
    ("web_worker_offload", "seq", "Keep Main UI Thread 60fps During Heavy Parse", ("Main UI 16ms Frame", "postMessage Transferable", "Worker Heavy Compute", "Render Fresh Canvas")),
    ("core_web_vitals_lcp", "tiers", "LCP (<2.5s), INP (<200ms), CLS (<0.1)", ("Preload Hero LCP Image", "Yield Long Tasks -> INP", "Reserve Img Aspect -> CLS")),
    ("rsc_server_components", "dual", "Zero-Bundle DB Queries Streamed Over Wire", ("Client Component (Interactive)", "Server Component (Zero JS)")),
    ("css_layout_gpu_compositor", "tiers", "Avoid Reflow Triggers With Transform/Opacity", ("Layout/Reflow (Costly CPU)", "Paint/Rasterize Layer", "GPU Transform/Opacity (60fps)")),
    ("micro_frontends_federation", "hub", "Independent Team Deploys Composed in Shell", ("App Shell Router", "Checkout Remote", "Search Remote", "Account Remote")),
    ("view_transitions_morph", "flow", "Smooth Native SPA Cross-Document Morph", ("Snapshot Old DOM Rect", "Compute Layout Delta", "GPU Crossfade + Morph", "Commit New Route Cleanly")),
    ("shadow_dom_encapsulation", "tiers", "Scoped CSS & Isolated Component Tree", ("Document Light DOM", "Shadow Root Boundary", "Scoped Component Styles")),
    ("indexeddb_local_first", "flow", "Instant Offline Reads + Background Sync Queue", ("Write IndexedDB Locally", "Immediate Reactive UI", "CRDT Sync When Online", "Conflict-Free Merge")),
    ("http_cache_etag_304", "seq", "Conditional Revalidation Saves Payload Bandwidth", ("Client Sends If-None-Match", "Server Checks ETag Hash", "304 Not Modified (0B Body)", "Reuse Local Cache")),
    ("wasm_simd_browser", "flow", "Near-Native C++/Rust Execution Inside Browser", ("Compile Rust -> .wasm", "Stream Instantiate Module", "SharedArrayBuffer Memory", "10x Faster Media/CAD")),
    ("speculation_prerender", "seq", "Zero-ms Instant Navigation Via Prefetch Hints", ("Hover Link Predictive Intent", "Background Subframe Render", "Instant Pointer Swap", "Zero Spinner Wait")),
    ("accessibility_aria_tree", "tree", "Semantic Landmark & Keyboard Focus Order", ("Main Landmark Root", "Nav Tab Index Flow", "Live Region Announcements", "Screen Reader Parity")),
    ("vite_esm_hmr_graph", "flow", "Instant Unbundled Native ESM Hot Reload", ("Edit Single Module", "Invalidate Direct Importers", "WebSocket HMR Push", "Sub-50ms Browser Patch")),
    ("cookie_samesite_security", "tiers", "Layered Browser Session Defense Matrix", ("HttpOnly (Blocks XSS Read)", "Secure (TLS Transport Only)", "SameSite=Lax/Strict (CSRF)")),
    ("progressive_streaming_ssr", "flow", "Flush Above-the-Fold Shell Before Slow DB Calls", ("Send Head + Nav Shell First", "Stream Suspense Boundaries", "Parallel Data Fetch Completes", "Out-of-Order Swap In Place")),

    # 14. MOBILE SYSTEMS, IOS & ANDROID INTERNALS (20)
    ("android_zygote_fork_art", "flow", "Preloaded Shared Runtime Instant App Launch", ("System Boot Zygote Preload", "Fork Child App Process", "Copy-on-Write Classes", "ART AOT/JIT Exec")),
    ("ios_arc_retain_cycles", "dual", "Deterministic Memory Freeing vs Leak Cycle", ("Strong <-> Strong Cycle (Leak)", "Weak / Unowned Ref (Freed)")),
    ("mobile_offline_sync_engine", "flow", "Local SQLite First + Delta Sync Queue", ("UI Reads Local SQLite", "Mutations Logged Offline", "Network Reachable Wake", "Batched Idempotent Push")),
    ("battery_doze_coalescing", "tiers", "OS Power Scheduler Windows Protect Battery", ("Foreground High-Prio", "Expedited JobScheduler", "Doze Batched Sync Window")),
    ("push_apns_fcm_gateway", "hub", "Persistent Single OS Socket Multiplexer", ("App Backend Server", "APNs Apple Gateway", "FCM Google Gateway", "Device Single Radio Wake")),
    ("jetpack_compose_recompose", "flow", "Skip Unchanged Subtrees With Stable State", ("State Snapshot Changed", "Trace Reader Composable", "Re-Execute Minimal Scope", "Skip Unchanged Siblings")),
    ("swiftui_layout_negotiation", "seq", "Parent Proposes Size -> Child Chooses Frame", ("Parent Proposes Bounds", "Child Measures Content", "Child Returns Exact Size", "Parent Positions Child")),
    ("mobile_startup_cold_warm", "dual", "Process Init vs Resumed Activity Latency", ("Cold Start: IPC + Class Load", "Warm/Hot Start: Frame Draw")),
    ("deep_link_universal_router", "flow", "Verified Domain Association Opens Exact Screen", ("Click https://app.co/item/9", "OS Checks assetlinks.json", "Route Directly Into Screen", "Fallback Store If Missing")),
    ("biometric_keychain_enclave", "tiers", "Hardware-Backed Crypto Signing Isolation", ("App Biometric Prompt", "OS FaceID/Fingerprint Verify", "Secure Enclave Unlocks Key")),
    ("mobile_image_decode_lru", "slots", "Downsample & Recycle Bitmaps Off Main Thread", ("Disk Cache", "Mem LRU", "Pool Reuse", "Decode BG", "GPU Tex")),
    ("ble_gatt_iot_pairing", "flow", "Low-Energy Characteristic Read/Notify Link", ("Advertise Service UUID", "GATT Connect & MTU Negot", "Enable Characteristic Notify", "Real-Time Sensor Stream")),
    ("crash_symbolication_dsym", "flow", "Translate Stripped Stack Addresses Back to Code", ("Device Captures Crash Trace", "Upload Hex Offsets Only", "Match dSYM/ProGuard Map", "Exact File & Line Pinpoint")),
    ("over_the_air_rollout_gates", "tiers", "Staged Phased Release With Crash Stop-Button", ("1% Beta Dogfood Cohort", "10% Phased (Monitor ANR)", "50% Regional Expand", "100% Global Availability")),
    ("sqlite_wal_mobile_perf", "dual", "Readers Never Block Single Background Writer", ("Rollback Journal (Stalls UI)", "WAL Mode (Smooth 60fps UI)")),
    ("certificate_pinning_mobile", "flow", "Defeat Rogue CA Proxy With Public Key Hash", ("App Embeds SPKI Hash", "TLS Server Cert Arrives", "Compare SHA-256 Pin", "Abort If Proxy MITM Detected")),
    ("background_upload_session", "flow", "OS Completes Transfers Even After App Killed", ("Hand File to NSURLSession/WM", "OS Schedules WiFi/Charging", "Chunked Resume After Drop", "Silent Wake On Done")),
    ("react_native_jsi_fabric", "dual", "Zero JSON Bridge Serialization Overhead", ("Legacy JSON Async Bridge", "New JSI C++ Host Objects")),
    ("flutter_impeller_pipeline", "flow", "Pre-Compiled Shaders Eliminate First-Run Jank", ("Dart Widget -> RenderObject", "Impeller Display List", "Precompiled Metal/Vulkan", "Zero Shader Compilation Stutter")),
    ("mobile_frame_120hz_budget", "tiers", "8.3ms ProMotion Budget Per Render Frame", ("UI Event & Layout (2.5ms)", "GPU Command Encode (2.5ms)", "Display Raster & Swap (3.3ms)")),

    # 15. GAME ENGINE, GRAPHICS & WEBGPU (20)
    ("ecs_entity_component_sys", "slots", "Cache-Friendly Struct-of-Arrays Component Memory", ("Pos[]", "Vel[]", "HP[]", "Mesh[]", "System Loop")),
    ("pbr_metallic_roughness", "tiers", "Physically Based Rendering Material Channels", ("Albedo Base Color Map", "Normal Tangent Micro-Surface", "Metallic / Roughness PBR", "IBL Environment Irradiance")),
    ("deferred_vs_forward_plus", "dual", "G-Buffer Many Lights vs Clustered Tile Shading", ("Deferred: G-Buffer Bandwidth", "Forward+: Tiled Light Culling")),
    ("bvh_raytracing_accel", "tree", "Hierarchical Bounding Boxes Skip Empty Space", ("Scene Root AABB", "Left Wing BVH", "Right Wing BVH", "Triangle Hit Test")),
    ("fixed_timestep_physics", "flow", "Decouple Variable FPS From Deterministic Simulation", ("Accumulate Frame Delta dt", "Step Fixed 16.6ms Physics", "Interpolate Remaining Alpha", "Consistent Collision Anywhere")),
    ("rollback_netcode_ggpo", "seq", "Zero Input Lag With Instant Speculative Rollback", ("Predict Remote Input", "Simulate Local Frame", "Late Packet Arrives", "Rollback & Fast-Forward")),
    ("spatial_hash_grid_broadphase", "tiers", "Avoid O(N^2) Pairwise Collision Checks", ("Insert Objects in Cell ID", "Check Same + Neighbor Cells", "Narrowphase SAT/GJK Test")),
    ("shadow_map_cascades", "tiers", "High Detail Near Camera + Wide Coverage Far", ("Cascade 0: 0-15m Crisp", "Cascade 1: 15-60m Medium", "Cascade 2: 60-250m Wide")),
    ("webgpu_compute_indirect", "flow", "GPU Culls & Draws Scene Without CPU Stall", ("Compute Frustum Culling", "Write Indirect Draw Args", "Execute Render Pass", "Zero CPU Readback Latency")),
    ("skeletal_skinning_matrix", "flow", "Dual-Quaternion & Bone Hierarchy Transforms", ("Root Pelvis Bone", "Recursive Joint Matrices", "Vertex Weights Blend (4)", "Smooth Deformed Mesh")),
    ("bloom_hdr_tonemapping", "flow", "Wide Dynamic Range Lighting -> sRGB Display", ("HDR Linear Framebuffer", "Bright Threshold + Blur", "Additive Composite Glow", "ACES Filmic Tone Map")),
    ("occlusion_hi_z_culling", "flow", "Skip Drawing Geometry Hidden Behind Walls", ("Render Occluder Depth", "Generate Hi-Z Mip Pyramid", "Test Mesh Bounds On GPU", "Discard Hidden Drawcalls")),
    ("texture_streaming_mips", "tiers", "Load Only Visible Resolution Mipmap Pages", ("4K Detail Close Camera", "1K Mid-Distance LOD", "256px Distant Horizon")),
    ("procedural_perlin_biome", "flow", "Deterministic Seeded Infinite Worlds", ("Hash (x,y) Seed Octave", "FBM Height + Moisture", "Rule-Based Biome Mask", "Mesh + Foliage Instancing")),
    ("audio_spatial_hrtf", "hub", "3D Positional Acoustics Around Listener", ("Player Listener Head", "Occlusion Raycast", "Distance Attenuation", "HRTF Binaural Pan")),
    ("asset_bundle_compression", "dual", "LZ4 Fast Stream vs Zstd High Archive Ratio", ("LZ4: Fast GPU Direct Read", "Zstd: Smaller Patch Download")),
    ("frame_pacing_vsync_vrr", "tiers", "Eliminate Tearing & Micro-Stutter", ("Present Queue Double/Triple", "G-Sync / FreeSync VRR", "Zero Dropped Tear Frames")),
    ("double_buffer_swapchain", "seq", "Prevent Half-Drawn Tear Artifacts On Scanout", ("GPU Renders Back Buffer", "Wait Safe Scanout Boundary", "Atomic Pointer Swap", "Front Displayed Cleanly")),
    ("meshlet_nanite_clusters", "tiers", "Micro-Polygon Cluster Streaming Without Pop-In", ("Source Million-Tri Mesh", "128-Tri Cluster DAG", "Sub-Pixel Screen Error Cut")),
    ("particle_gpu_instancing", "flow", "1 Million Dynamic Particles In Single Draw Call", ("Flat SSBO Particle Array", "Compute Euler Force Update", "Sorted Quad Billboard Draw", "0.4ms Frame Overhead")),

    # 16. FINTECH, PAYMENTS & LEDGER ARCHITECTURE (20)
    ("double_entry_ledger", "dual", "Every Credit Matches An Equal Atomic Debit", ("Debit Source Account (-$50)", "Credit Dest Account (+$50)")),
    ("payment_idempotent_retry", "flow", "Network Retries Never Double-Charge Customers", ("Client Generates UUID Key", "Acquire Ledger Lock Row", "Replay Stored Response If Seen", "Exactly-Once Settlement")),
    ("card_auth_capture_clear", "seq", "Three-Stage Payment Lifecycle Across Networks", ("Auth Hold Funds Now", "Merchant Capture Batch", "Interchange Clearing", "T+1 Bank Settlement")),
    ("three_ds_fraud_scoring", "flow", "Sub-50ms Real-Time Risk Evaluation Pipeline", ("Extract Device + Velocity", "ML Fraud Score Inference", "Low Risk -> Frictionless", "High Risk -> 3DS Challenge")),
    ("pci_dss_token_vault", "tiers", "Isolate Raw Card PAN From Core App Databases", ("Client SDK Direct Capture", "HSM Isolated Token Vault", "App Stores Safe tok_abc123")),
    ("ledger_snapshot_balance", "flow", "Avoid Scanning Billion Rows Per Balance Check", ("Immutable Append Entries", "Daily Midnight Checkpoint", "Checkpoint + Delta Today", "O(1) Audited Balance")),
    ("iso8583_vs_iso20022", "dual", "Legacy Compact Bitmaps vs Rich XML Financial Standard", ("ISO 8583: Fast Compact Fields", "ISO 20022: Rich Structured XML")),
    ("escrow_split_payout", "hub", "Marketplace Multi-Party Split Settlement", ("Buyer Payment Escrow", "Merchant 85% Split", "Platform 10% Fee", "Tax Vault 5%")),
    ("fx_multi_currency_lock", "flow", "Lock Exchange Quote TTL Across Checkout Window", ("Quote EUR/USD 30s TTL", "Store Rate ID With Order", "Execute Atomic Dual Ledger", "Zero Slippage Surprise")),
    ("chargeback_dispute_fsm", "ring", "Evidence Submission State Machine Lifecycle", ("Transaction Settled", "Dispute Opened", "Evidence Submitted", "Arbitration Won/Lost")),
    ("kyc_aml_sanctions_pipe", "tiers", "Automated Identity & Compliance Screening", ("Document OCR + Liveness", "Sanctions PEP Watchlist", "Risk Tier Limit Assigned")),
    ("high_frequency_matching", "slots", "Price-Time Priority Limit Order Book Engine", ("Bids", "Asks", "RingBuf", "Match", "Publish")),
    ("reconciliation_t_plus_1", "flow", "Detect Orphan Ledger Records Automatically", ("Ingest Bank Statement", "Deterministic Hash Match", "Flag Penny Discrepancies", "Auto-Heal /Ops Alert")),
    ("saga_refund_compensate", "flow", "Reverse Partial Failures Across 4 Services", ("Void Reservation Step", "Release Loyalty Points", "Issue Card Refund Tx", "Emit Final Audit Event")),
    ("hot_wallet_cold_vault", "tiers", "Tiered Custody Thresholds Protect Treasury", ("Hot API Wallet (2% Liquidity)", "Warm Multi-Sig Policy Gate", "Air-Gapped Cold HSM (90%)")),
    ("instant_upi_rails_flow", "seq", "Sub-Second Account-to-Account Push Settlement", ("Payer VPA Init", "NPCI Switch Route", "Remitter Bank Debit", "Beneficiary Credit ACK")),
    ("rate_limit_fraud_vel", "flow", "Sliding Window Counters Block Card Testing", ("Count BIN + IP Velocity", "Redis Sorted-Set Window", "Trip 429 Challenge Gate", "Zero Credential Stuffing")),
    ("webhook_stripe_replay", "flow", "Ordered Delivery Even When Events Arrive Out-of-Order", ("Verify Webhook Signature", "Check Event Timestamp", "Fetch Latest Resource State", "Idempotent DB Upsert")),
    ("audit_log_merkle_seal", "flow", "Cryptographically Tamper-Evident Financial Logs", ("Hash Transaction Entry", "Chain Prev Digest Hash", "Anchor Daily Root Anchor", "Regulator Verifiable")),
    ("graceful_degrade_psp", "hub", "Auto-Failover Payment Processors On 5xx Spike", ("Smart PSP Router", "PSP Primary (Stripe)", "PSP Backup (Adyen)", "Health Circuit Breaker")),

    # 17. BLOCKCHAIN, CONSENSUS & CRYPTOGRAPHY INTERNALS (20)
    ("merkle_patricia_trie", "tree", "Compact Authenticated Key-Value State Proofs", ("State Root Hash", "Extension Branch", "Leaf Value Node", "Verify O(log N) Proof")),
    ("zk_snark_prover_verifier", "dual", "Prove Computation Truth Without Revealing Secrets", ("Prover: Private Witness -> 200B", "Verifier: Checks In <5ms")),
    ("optimistic_vs_zk_rollup", "dual", "Fraud Proof Challenge Window vs Validity Proof", ("Optimistic: 7d Challenge Delay", "ZK Rollup: Instant Math Finality")),
    ("bls_signature_aggregate", "flow", "Merge 10,000 Validator Sigs Into 1 Verification", ("Validators Sign Block", "Pairing Aggregate Combine", "Single 48B Signature", "1 Fast Pairing Check")),
    ("shamir_secret_sharing", "hub", "Recover Master Key From Any k-of-n Shares", ("Master Secret Split (3/5)", "Share 1 HSM", "Share 2 Legal", "Share 3 Cloud KMS")),
    ("diffie_hellman_ecdh", "seq", "Establish Shared Key Over Insecure Channel", ("Alice Sends Public G^a", "Bob Sends Public G^b", "Both Compute G^ab", "Zero Eve Knowledge")),
    ("aes_gcm_authenticated", "flow", "Confidentiality + Integrity Tag In Single Pass", ("Nonce + Key + Plaintext", "CTR Counter Encrypt", "GHASH Poly Tag", "Detect 1-Bit Tamper")),
    ("mempool_mev_ordering", "tiers", "Transaction Ordering Auctions & Block Building", ("Public User Mempool", "Searcher Bundle Bids", "Block Builder Optimal Sort", "Proposer Signed Block")),
    ("utxo_vs_account_model", "dual", "Parallel Unspent Coins vs Global Mutable Balances", ("UTXO: Parallel Coin Graph", "Account: Nonce Serial Balance")),
    ("threshold_mpc_signing", "ring", "Distributed Signing Without Assembling Full Key", ("Node 1 Share", "Node 2 Share", "Node 3 Share", "Joint ECDSA Sig")),
    ("slashing_pos_incentives", "dual", "Reward Honest Attestation vs Burn Equivocation", ("Online Finality: +Yield", "Double Sign: 100% Slashed")),
    ("ipfs_content_addressing", "flow", "Address Files By Cryptographic Hash Instead of URL", ("Chunk File 256KB Blocks", "Build DAG Merkle Links", "Derive CID Root Hash", "Fetch From Nearest Peer")),
    ("bloom_filter_light_client", "slots", "Verify Header Logs Without Full Chain Sync", ("Hdr", "Topic", "Addr", "Log", "Match")),
    ("envelope_kms_rotation", "tiers", "Rotate Root KEK Without Re-Encrypting Petabytes", ("Master HSM Root Key (KEK)", "Data Encryption Keys (DEK)", "Encrypted S3 Objects")),
    ("ed25519_vs_secp256k1", "dual", "Deterministic Fast Edwards Curves vs Legacy", ("Ed25519: Safe & Constant-Time", "secp256k1: Bitcoin/ETH Compat")),
    ("nonce_replay_protection", "flow", "Stop Duplicate Requests With Time & Sequence", ("Include Signed Nonce + Exp", "Check Redis Seen Window", "Reject Replay 409 Conflict", "One-Time Execution")),
    ("gossipsub_p2p_mesh", "hub", "Scalable Epidemic Message Propagation Mesh", ("Proposer Origin", "Mesh Peer Fanout", "Graft/Prune Sparse", "Cluster Convergence <1s")),
    ("verifiable_delay_vdf", "flow", "Sequential Unparallelizable Time-Lock Proof", ("Seed Challenge Value", "Run T Sequential Squarings", "Output + Fast Proof", "Fair Unbiasable Random")),
    ("post_quantum_kyber_mlkem", "dual", "Lattice Key Exchange Resists Shor Quantum Attack", ("RSA/ECDH: Vulnerable Quantum", "ML-KEM Lattice: Quantum-Safe")),
    ("cross_chain_bridge_proof", "seq", "Verify Source Chain State Light-Client On Dest", ("Lock Asset Chain A", "Wait Source Finality", "Verify Merkle State Proof", "Mint Wrapped Chain B")),

    # 18. ROBOTICS, REAL-TIME CONTROL & EDGE SYSTEMS (20)
    ("ros2_dds_pubsub", "hub", "Real-Time Decentralized Robotics Middleware", ("DDS Discovery Bus", "LiDAR PointCloud Node", "Planner Node", "Motor Actuator Node")),
    ("kalman_sensor_fusion", "flow", "Blend Noisy IMU + GPS + Wheel Odometry", ("Predict State From Motion", "Read Noisy Sensors", "Compute Kalman Gain K", "Optimal Pose Estimate")),
    ("slam_loop_closure", "ring", "Map Unknown Environment While Localizing Robot", ("Extract Visual Features", "Visual Odometry Track", "Recognize Visited Place", "Optimize Pose Graph")),
    ("pid_control_loop_1khz", "flow", "Minimize Error With P, I, D Gain Tuning", ("Target Setpoint - Actual", "Proportional + Integral + Deriv", "Clamp Actuator Torque", "Stable Zero-Overshoot")),
    ("can_bus_arbitration", "tiers", "Deterministic Hardware Priority On Automotive Bus", ("Brake / Airbag (ID 0x010)", "Powertrain ECU (ID 0x120)", "Infotainment (ID 0x580)")),
    ("rtos_priority_preempt", "tiers", "Hard Real-Time Deadlines Never Miss Microseconds", ("ISR Hardware Interrupt (1us)", "Control Task 1kHz (Highest)", "Telemetry Logging (Idle)")),
    ("edge_ota_ab_partition", "dual", "Power-Safe Firmware Updates On Remote IoT", ("Partition A: Active Stable", "Partition B: Flash & Verify")),
    ("lidar_occupancy_grid", "tiers", "Convert 3D Point Clouds Into Navigable Costmap", ("Raw 3D Laser Scan", "Ground Plane Filter", "Voxel Costmap + Inflation")),
    ("path_planning_astar_rrt", "flow", "Global Graph Search + Local Obstacle Avoidance", ("A* Global Grid Waypoints", "Check Dynamic Obstacles", "DWA Local Velocity Traj", "Smooth Curved Motion")),
    ("inverse_kinematics_arm", "seq", "Compute 6 Joint Angles From End-Effector Pose", ("Target 3D Grab Pose", "Jacobian Pseudo-Inverse", "Check Joint Limits", "Execute Smooth Trajectory")),
    ("sim2real_domain_rand", "flow", "Train Policies In Randomized Physics -> Real World", ("Randomize Friction/Mass", "Train PPO In 4096 Envs", "Zero-Shot Real Deploy", "Resilient Robot Grip")),
    ("watchdog_timer_failsafe", "flow", "Hardware Reset If Control Loop Freezes >10ms", ("Control Loop Feeds Timer", "Memory/Bus Hang Occurs", "Timer Hits Zero -> Trip", "Safe Brake Relay Engaged")),
    ("time_sensitive_net_tsn", "slots", "Bounded Microsecond Jitter Over Standard Ethernet", ("Sync", "Guard", "Ctrl", "Video", "BestEffort")),
    ("tinyml_mcu_quantized", "tiers", "Run Neural Nets On 256KB Cortex-M Chips", ("Prune & INT8 Quantize", "Static Arena (Zero Malloc)", "CMSIS-NN SIMD Kernels")),
    ("mqtt_qos_0_1_2", "tiers", "IoT Telemetry Delivery Guarantees Trade-Off", ("QoS 0: Fire & Forget", "QoS 1: At Least Once PUBACK", "QoS 2: Exactly Once 4-Way")),
    ("drone_vio_optical_flow", "hub", "GPS-Denied Stable Hover Using Camera + IMU", ("Flight Controller", "Downward Optical Cam", "High-Rate 1kHz IMU", "ESCs Motor Mixer")),
    ("digital_twin_telemetry", "seq", "Bidirectional Physical Asset & Cloud Mirror", ("Edge Sensors Stream", "Cloud Twin Physics Sync", "Predict Bearing Wear", "Push Preventive Command")),
    ("fpga_vision_pipeline", "flow", "Zero-CPU-Copy Streaming Pixel Convolutions", ("MIPI Camera Line Buffer", "BRAM Sliding Window", "Parallel DSP Filters", "PCIe DMA Ready Box")),
    ("autonomous_behavior_tree", "tree", "Modular Reactive Fallback Task Hierarchy", ("Root Mission Selector", "Battery Low -> Dock", "Obstacle -> Replan", "Continue Patrol")),
    ("v2x_edge_offload_mec", "flow", "Sub-10ms 5G Multi-Access Edge Inference", ("Car Perception Packet", "5G Tower Base Station", "Colocated MEC GPU", "Broadcast Hazard Alert")),
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
    if raw.startswith("grammar:"):
        raw = raw.split(":", 1)[1].strip()
    kind = str(g.get("kind") or raw.split(":", 1)[0] or "flow").strip()
    param = raw.split(":", 1)[1] if ":" in raw else ""

    items = list(data.get("items") or data.get("nodes") or data.get("steps") or g.get("items") or [])
    norm: List[Dict[str, Any]] = []
    for it in items:
        norm.append({"name": it} if isinstance(it, str) else dict(it))

    if not norm:
        cnt = 4
        m_grid = re.search(r"(\d+)\s*x\s*(\d+)", param)
        m_num = re.search(r"(\d+)", param)
        if m_grid:
            cnt = max(2, min(12, int(m_grid.group(1)) * int(m_grid.group(2))))
        elif m_num:
            cnt = max(2, min(10, int(m_num.group(1))))
        elif kind in ("dual", "split"):
            cnt = 2
        elif kind in ("triangle",):
            cnt = 3
        elif kind in ("quadrant", "matrix"):
            cnt = 4
        label_prefix = param.replace("_", " ").replace(":", " ").strip().title() if param else kind.upper()
        norm = [{"name": f"{label_prefix[:18]} #{i+1}", "sub": f"{kind.upper()} Stage"} for i in range(cnt)]

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
    _sub_gate = helpers.get("_sub_gate") or (lambda g, p="box": _ease(g))
    _footer_gate = helpers.get("_footer_gate") or (lambda p: _ease(max(0.0, min(1.0, (p - 0.72) / 0.22))))
    _res_col = helpers["resolve_world_color"]
    _bezier = helpers["_draw_bezier_comet"]
    _draw_vis = helpers["_draw_node_visual"]

    user_items = list(
        data.get("items") or data.get("nodes") or data.get("steps") or data.get("stages")
        or data.get("satellites") or data.get("bullets") or data.get("layers") or data.get("tiers") or []
    )
    if not user_items and isinstance(data.get("entries"), list):
        user_items = [{"name": e.get("op"), "sub": f"{e.get('address','')} • {e.get('table','')}"} for e in data["entries"] if isinstance(e, dict)]
    if not user_items and isinstance(data.get("bars"), list):
        user_items = [{"name": b.get("label"), "sub": str(b.get("display") or b.get("value") or "")} for b in data["bars"] if isinstance(b, dict)]
    items = user_items if user_items else [{"name": s} for s in raw_items]
    norm: List[Dict[str, Any]] = []
    for x in items:
        if isinstance(x, str):
            norm.append({"name": x})
        else:
            d_it = dict(x)
            if not d_it.get("sub") and d_it.get("desc"):
                d_it["sub"] = d_it["desc"]
            elif not d_it.get("sub") and d_it.get("role"):
                d_it["sub"] = d_it["role"]
            norm.append(d_it)
    g0 = _ease(min(1.0, progress / 0.16))
    gf = _footer_gate(progress)
    footer_note = str(data.get("footer") or data.get("summary") or "").strip()

    # Optional architectural subtitle strip at top of stage
    y_off = 0
    if title_sub:
        stage.draw_pill(540, SY0 + 18, title_sub[:44], (*world["cyan"][:3], 34), world["cyan"], border_col=world["border"], font=_get_font(19, bold=True), alpha_mul=g0)
        y_off = 44

    # 1. FLOW / CODE_FLOW -> Zigzag vertical stages with clear non-overlapping central Bezier pills
    if arch in ("flow", "code_flow"):
        n = min(5, len(norm))
        reserve_ft = 105 if (footer_note or n <= 3) else 24
        rh = min(215, (SH - y_off - reserve_ft) // max(1, n))
        prev_pt = None
        active_idx = min(max(0, n - 1), int(max(0.0, min(0.999, progress)) * max(1, n)))
        for i, it in enumerate(norm[:5]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_box = _sub_gate(gt_raw, "box")
            g_bdg = _sub_gate(gt_raw, "badge")
            g_tit = _sub_gate(gt_raw, "title")
            g_sub = _sub_gate(gt_raw, "sub")
            g_lnk = _sub_gate(gt_raw, "link")
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            cy = SY0 + y_off + 68 + i * rh
            is_left = (i % 2 == 0)
            scx = 180 if is_left else 900
            cx0, cx1 = (278, 996) if is_left else (84, 802)
            active = (active_idx == i and progress > 0.03)
            if prev_pt is not None:
                _bezier(stage, prev_pt, (460 if is_left else 620, cy - 50), col, reveal=g_box, progress=progress, phase=i * 0.2, label=str(it.get("edge") or it.get("via") or ""), world=world)
            stage.draw_glass_card((cx0, cy - 50, cx1, cy + 52), radius=19, accent_col=col, alpha_mul=g_box, active=active)
            if g_bdg > 0.02:
                _draw_vis(stage, scx, cy - 14, 42, 18, 28, col, g_bdg, shape=it.get("shape", ""), icon=it.get("icon", ""), label=str(it.get("name", "")), active=active, progress=progress)
                stage.draw.line((scx + (50 if is_left else -50), cy, cx0 if is_left else cx1, cy), fill=_with_alpha(col, g_bdg), width=3)
            if g_tit > 0.02:
                _draw_wrapped(stage.draw, (cx0 + 22, cy - 34), str(it.get("name") or it.get("title") or ""), _get_font(24, bold=True), _with_alpha(world["text"], g_tit), cx1 - cx0 - 44, max_lines=1 if it.get("sub") else 2)
            if it.get("sub") and g_sub > 0.02:
                _draw_wrapped(stage.draw, (cx0 + 22, cy + 6), str(it["sub"]), _get_font(19), _with_alpha(world["muted"], g_sub), cx1 - cx0 - 44, max_lines=2)
            prev_pt = (460 if is_left else 620, cy + 52) if g_lnk > 0.02 or i + 1 < n else None
        if gf > 0.03 and (footer_note or n <= 3):
            stage.draw_glass_card((80, SY1 - 92, 1000, SY1 - 20), radius=20, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 70), (footer_note or title_sub or "End-to-End Architecture Pipeline")[:60], _get_font(24, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 2. TIERS -> Horizontal architectural stack / memory layers
    if arch == "tiers":
        n = min(6, len(norm))
        reserve_ft = 96 if footer_note else 24
        rh = min(200, (SH - y_off - reserve_ft) // max(1, n))
        active_idx = min(max(0, n - 1), int(max(0.0, min(0.999, progress)) * max(1, n)))
        for i, it in enumerate(norm[:6]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_box = _sub_gate(gt_raw, "box")
            g_bdg = _sub_gate(gt_raw, "badge")
            g_tit = _sub_gate(gt_raw, "title")
            g_sub = _sub_gate(gt_raw, "sub")
            g_lnk = _sub_gate(gt_raw, "link")
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            y = SY0 + y_off + 18 + i * rh
            h = rh - 16
            is_act = (active_idx == i and progress > 0.03)
            stage.draw_glass_card((80, y, 1000, y + h), radius=18, accent_col=col, alpha_mul=g_box, active=is_act)
            if g_bdg > 0.02:
                _draw_vis(stage, 146, y + h // 2 - 12, 32, 14, 22, col, g_bdg, shape=it.get("shape", "layers_wafer"), icon=it.get("icon", ""), label=str(it.get("name", "")), active=is_act, progress=progress)
                stage.draw_pill(242, y + h // 2, f"0{i+1}", (*col[:3], 42), col, border_col=col, font=_get_font(19, bold=True), alpha_mul=g_bdg)
            sub_txt = str(it.get("sub") or "").strip()
            if g_tit > 0.02:
                _draw_wrapped(stage.draw, (296, y + (max(14, h // 2 - 38) if sub_txt else max(12, h // 2 - 22))), str(it.get("name") or ""), _get_font(24, bold=True), _with_alpha(world["text"], g_tit), 680, max_lines=1 if sub_txt else 2)
            if sub_txt and g_sub > 0.02:
                _draw_wrapped(stage.draw, (296, y + h // 2 + 8), sub_txt, _get_font(19), _with_alpha(world["muted"], g_sub), 680, max_lines=2)
            if i + 1 < n and g_lnk > 0.02:
                stage.draw.line((242, y + h, 242, y + rh), fill=_with_alpha(col, g_lnk), width=3)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 84, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 64), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 3. RING -> Circular Raft / Circuit Breaker / Event Loop / Consistent Hash Ring
    if arch == "ring":
        cx, cy, rad = 540, SY0 + y_off + (SH - y_off - 40) // 2, 315
        stage.draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=_with_alpha((*world["cyan"][:3], 72), g0), width=4)
        n = min(6, len(norm))
        pts = [(int(cx + rad * math.cos(-math.pi / 2 + i * 2 * math.pi / n)), int(cy + rad * math.sin(-math.pi / 2 + i * 2 * math.pi / n))) for i in range(n)]
        active_idx = min(max(0, n - 1), int(max(0.0, min(0.999, progress)) * max(1, n)))
        for i, it in enumerate(norm[:n]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_t, g_lnk = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "link")
            px, py = pts[i]
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            if g_lnk > 0.02:
                _bezier(stage, pts[i], pts[(i + 1) % n], col, reveal=g_lnk, progress=progress, curve_bend=22, label=str(it.get("edge") or ""), world=world)
            stage.draw_glass_card((px - 135, py - 42, px + 135, py + 44), radius=18, accent_col=col, alpha_mul=g_b, active=(active_idx == i and progress > 0.03))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (px - 122, py - 24), str(it.get("name") or ""), _get_font(20, bold=True), _with_alpha(world["text"], g_t), 244, align="center", max_lines=2)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 84, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 64), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 4. HUB -> Hub & Satellites Topology
    if arch == "hub":
        cx, cy = 540, SY0 + y_off + (SH - y_off - 40) // 2
        hub_item = norm[0] if norm else {"name": "Core"}
        sats = norm[1:5] if len(norm) > 1 else [{"name": "Node 1"}, {"name": "Node 2"}, {"name": "Node 3"}]
        pos = [(265, SY0 + y_off + 165), (815, SY0 + y_off + 165), (265, SY1 - 180), (815, SY1 - 180)]
        _draw_vis(stage, cx, cy - 26, 56, 24, 38, world["cyan"], g0, shape=hub_item.get("shape", "geodesic_sphere"), icon=hub_item.get("icon", ""), label=str(hub_item.get("name", "")), active=True, progress=progress)
        stage.draw_pill(cx, cy + 56, str(hub_item.get("name") or "")[:24], world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g0)
        for i, sat in enumerate(sats):
            gt_raw = _spring_gate(progress, i + 1, len(sats) + 1, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_ico, g_t, g_lnk = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "link")
            sx, sy = pos[i % len(pos)]
            col = _res_col(world, sat.get("color"), _ACCENT[(i + 1) % len(_ACCENT)])
            if g_b > 0.02:
                _bezier(stage, (cx, cy), (sx, sy), col, reveal=max(g_b, g_lnk), progress=progress, curve_bend=20, label=str(sat.get("edge") or ""), world=world)
            stage.draw_glass_card((sx - 165, sy - 54, sx + 165, sy + 56), radius=20, accent_col=col, alpha_mul=g_b, active=(int(progress * len(sats)) == i))
            if g_ico > 0.02:
                _draw_vis(stage, sx, sy - 78, 36, 16, 22, col, g_ico, shape=sat.get("shape", ""), icon=sat.get("icon", ""), label=str(sat.get("name", "")), progress=progress)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (sx - 150, sy - 26), str(sat.get("name") or ""), _get_font(22, bold=True), _with_alpha(world["text"], g_t), 300, align="center", max_lines=2)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 84, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 64), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 5. DUAL -> Split Comparison / Trade-Off Cards
    if arch == "dual":
        pts_d = norm[:2] if len(norm) >= 2 else [norm[0], {"name": "Optimized Approach"}]
        for idx, it in enumerate(pts_d):
            gt_raw = _spring_gate(progress, idx, 2, 0.28)
            if gt_raw <= 0.02:
                continue
            g_b, g_ico, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            col = world["rose"] if idx == 0 else world["emerald"]
            x0, x1 = (72, 520) if idx == 0 else (560, 1008)
            stage.draw_glass_card((x0, SY0 + y_off + 30, x1, SY1 - 105), radius=24, accent_col=col, alpha_mul=g_b, active=(idx == 1), layered=(idx == 1))
            if g_ico > 0.02:
                _draw_vis(stage, (x0 + x1) // 2, SY0 + y_off + 140, 56, 24, 36, col, g_ico, shape=it.get("shape", "hexagon" if idx else "box"), icon=it.get("icon", ""), label=str(it.get("name", "")), active=(idx == 1), progress=progress)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (x0 + 26, SY0 + y_off + 260), str(it.get("name") or ""), _get_font(28, bold=True), _with_alpha(world["text"], g_t), x1 - x0 - 52, align="center", max_lines=4)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (x0 + 26, SY0 + y_off + 470), str(it["sub"]), _get_font(21), _with_alpha(world["muted"], g_s), x1 - x0 - 52, align="center", max_lines=3)
        gv = _ease(max(0.0, min(1.0, (progress - 0.36) / 0.16)))
        if gv > 0.02:
            stage.draw_pill(540, SY0 + y_off + 440, "VS", world["card_alt"], world["amber"], border_col=world["amber"], font=_get_font(26, bold=True), alpha_mul=gv)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 84, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 64), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 6. SLOTS -> Horizontal Array / Memory / Cache / Bit / Vector Lanes
    if arch == "slots":
        n = min(6, len(norm))
        cw = (SW - (n - 1) * 14) // max(1, n)
        slot_y = SY0 + y_off + 120
        for i, it in enumerate(norm[:n]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title")
            x0 = SX0 + i * (cw + 14)
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((x0, slot_y, x0 + cw, slot_y + 290), radius=18, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_bdg > 0.02:
                stage.draw_pill(x0 + cw // 2, slot_y + 38, f"[{i}]", (*col[:3], 42), col, border_col=col, font=_get_font(19, bold=True, mono=True), alpha_mul=g_bdg)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (x0 + 12, slot_y + 92), str(it.get("name") or ""), _get_font(21 if n <= 4 else 18, bold=True), _with_alpha(world["text"], g_t), cw - 24, align="center", max_lines=4)
        # Detail callout strip + Insight Summary Footer below memory/array slots
        active_i = min(n - 1, int(max(0.0, min(0.999, progress)) * max(1, n)))
        ac_col = _res_col(world, _ACCENT[active_i % len(_ACCENT)])
        g_det = _ease(min(1.0, progress / 0.28))
        stage.draw_glass_card((80, slot_y + 330, 1000, slot_y + 520), radius=22, accent_col=ac_col, alpha_mul=g_det, active=True)
        act_sub = str(norm[active_i].get("sub") or title_sub or "Live State Execution").strip()
        _draw_wrapped(stage.draw, (112, slot_y + 372), f"Step [{active_i+1}/{n}]: {norm[active_i].get('name', '')}", _get_font(29, bold=True), _with_alpha(world["text"], g_det), 856, align="center", max_lines=2)
        _draw_wrapped(stage.draw, (112, slot_y + 448), act_sub, _get_font(21), _with_alpha(ac_col, g0), 856, align="center", max_lines=1)
        if slot_y + 545 < SY1 - 95:
            stage.draw_glass_card((80, slot_y + 545, 1000, SY1 - 24), radius=20, accent_col=world["cyan"], alpha_mul=g0)
            _draw_wrapped(stage.draw, (112, slot_y + 578), "Deterministic Production Mechanics", _get_font(23, bold=True), _with_alpha(world["muted"], g0), 856, align="center", max_lines=1)
        return

    # 7. TREE -> Root -> Children Hierarchy
    if arch == "tree":
        root_n = norm[0]
        children = norm[1:4] if len(norm) > 1 else [{"name": "Left Subtree"}, {"name": "Right Subtree"}]
        stage.draw_glass_card((300, SY0 + y_off + 20, 780, SY0 + y_off + 145), radius=22, accent_col=world["cyan"], alpha_mul=g0, active=True)
        _draw_wrapped(stage.draw, (320, SY0 + y_off + 54), str(root_n.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], g0), 440, align="center", max_lines=2)
        cn = len(children)
        cw = (SW - (cn - 1) * 24) // cn
        for i, ch in enumerate(children):
            gt_raw = _spring_gate(progress, i + 1, cn + 1, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_ico, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            bx0 = SX0 + i * (cw + 24)
            col = _res_col(world, ch.get("color"), _ACCENT[(i + 1) % len(_ACCENT)])
            _bezier(stage, (540, SY0 + y_off + 146), (bx0 + cw // 2, SY0 + y_off + 310), col, reveal=g_b, progress=progress, label=str(ch.get("edge") or ""), world=world)
            stage.draw_glass_card((bx0, SY0 + y_off + 312, bx0 + cw, SY0 + y_off + 585), radius=20, accent_col=col, alpha_mul=g_b, active=(int(progress * cn) == i))
            if g_ico > 0.02:
                _draw_vis(stage, bx0 + cw // 2, SY0 + y_off + 382, 42, 18, 28, col, g_ico, shape=ch.get("shape", "hexagon"), progress=progress)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (bx0 + 16, SY0 + y_off + 448), str(ch.get("name") or ""), _get_font(22, bold=True), _with_alpha(world["text"], g_t), cw - 32, align="center", max_lines=2)
            if ch.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (bx0 + 16, SY0 + y_off + 516), str(ch["sub"]), _get_font(18), _with_alpha(world["muted"], g_s), cw - 32, align="center", max_lines=2)
        if gf > 0.03:
            stage.draw_glass_card((80, SY1 - 220, 1000, SY1 - 24), radius=22, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 172), (footer_note or f"Hierarchy: {root_n.get('name', '')}")[:56], _get_font(26, bold=True), _with_alpha(world["text"], gf), 856, align="center", max_lines=2)
            _draw_wrapped(stage.draw, (112, SY1 - 96), title_sub or "Balanced Branch Decomposition", _get_font(21), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 8. TRIANGLE -> Three-Corner Tradeoff (CAP Theorem)
    if arch == "triangle":
        pts = [(540, SY0 + y_off + 120), (225, SY1 - 180), (855, SY1 - 180)]
        for i, (px, py) in enumerate(pts):
            gt_raw = _spring_gate(progress, i, 3, 0.25)
            if gt_raw <= 0.02:
                continue
            g_b, g_t, g_lnk = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "link")
            col = _res_col(world, _ACCENT[i % 3])
            if g_lnk > 0.02:
                _bezier(stage, pts[i], pts[(i + 1) % 3], col, reveal=g_lnk, progress=progress, world=world)
            lbl = str(norm[i % len(norm)].get("name") or "")
            stage.draw_glass_card((px - 175, py - 65, px + 175, py + 65), radius=22, accent_col=col, alpha_mul=g_b, active=(int(progress * 3) == i))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (px - 155, py - 24), lbl, _get_font(23, bold=True), _with_alpha(world["text"], g_t), 310, align="center", max_lines=2)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 84, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 64), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 9. SEQ -> Vertical Actor Lifelines Sequence Messages
    if arch == "seq":
        actors = ["Client/Proposer", "Coordinator/Gateway", "Cluster/Vault"]
        xs = [210, 540, 870]
        for i, act in enumerate(actors):
            ac = _res_col(world, _ACCENT[i])
            stage.draw_glass_card((xs[i] - 115, SY0 + y_off + 14, xs[i] + 115, SY0 + y_off + 92), radius=16, accent_col=ac, alpha_mul=g0, active=True)
            _draw_wrapped(stage.draw, (xs[i] - 105, SY0 + y_off + 36), act, _get_font(20, bold=True), _with_alpha(world["text"], g0), 210, align="center", max_lines=1)
            for ly in range(SY0 + y_off + 104, SY1 - 92, 24):
                stage.draw.line((xs[i], ly, xs[i], min(SY1 - 92, ly + 12)), fill=_with_alpha((*ac[:3], 125), g0), width=3)
        for i, it in enumerate(norm[:5]):
            gt_raw = _spring_gate(progress, i, len(norm), 0.22)
            if gt_raw <= 0.02:
                continue
            g_lnk = _sub_gate(gt_raw, "link")
            g_t = _sub_gate(gt_raw, "title")
            y = SY0 + y_off + 170 + i * 150
            col = _res_col(world, _ACCENT[i % len(_ACCENT)])
            _bezier(stage, (xs[i % 2], y), (xs[1 + ((i + 1) % 2)], y), col, reveal=max(_sub_gate(gt_raw, "box"), g_lnk), progress=progress, label=str(it.get("name") or "")[:24] if g_t > 0.02 else "", world=world)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 10. GRID -> True N x M Bento Matrix (2x2, 3x2, 2x3, 4x4)
    if arch == "grid":
        n = min(9, max(4, len(norm)))
        cols = 2 if n <= 4 else (3 if n <= 6 or n == 9 else 2)
        rows = max(2, math.ceil(n / cols))
        gw = (SW - (cols - 1) * 18) // cols
        gh = min(275, (SH - y_off - (110 if footer_note else 40) - (rows - 1) * 18) // rows)
        for i, it in enumerate(norm[:rows * cols]):
            gt_raw = _spring_gate(progress, i, min(n, rows * cols), 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            r_i, c_i = i // cols, i % cols
            x0 = SX0 + c_i * (gw + 18)
            y0 = SY0 + y_off + 24 + r_i * (gh + 18)
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((x0, y0, x0 + gw, y0 + gh), radius=18, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_bdg > 0.02:
                stage.draw_pill(x0 + 46, y0 + 28, f"{i+1:02d}", (*col[:3], 42), col, border_col=col, font=_get_font(17, bold=True, mono=True), alpha_mul=g_bdg)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (x0 + 18, y0 + 58), str(it.get("name") or ""), _get_font(22 if cols <= 2 else 19, bold=True), _with_alpha(world["text"], g_t), gw - 36, max_lines=2)
            if it.get("sub") and gh >= 170 and g_s > 0.02:
                _draw_wrapped(stage.draw, (x0 + 18, y0 + 122), str(it["sub"]), _get_font(17), _with_alpha(world["muted"], g_s), gw - 36, max_lines=2)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 11. SWIMLANE -> Horizontal role/lane bands with cross-lane signals
    if arch == "swimlane":
        lanes = norm[:4] if len(norm) >= 2 else norm + [{"name": "Processing Lane"}, {"name": "Storage Lane"}]
        n = len(lanes)
        lh = min(210, (SH - y_off - (110 if footer_note else 40)) // max(1, n))
        for i, it in enumerate(lanes):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t, g_s, g_lnk = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub"), _sub_gate(gt_raw, "link")
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            y0 = SY0 + y_off + 22 + i * lh
            h = lh - 18
            if g_bdg > 0.02:
                stage.draw_glass_card((76, y0, 260, y0 + h), radius=16, accent_col=col, alpha_mul=g_bdg, active=True)
                _draw_wrapped(stage.draw, (90, y0 + h // 2 - 22), f"LANE {i+1}", _get_font(21, bold=True, mono=True), _with_alpha(col, g_bdg), 156, align="center", max_lines=1)
            stage.draw_glass_card((276, y0, 1004, y0 + h), radius=16, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (300, y0 + 26), str(it.get("name") or ""), _get_font(24, bold=True), _with_alpha(world["text"], g_t), 680, max_lines=2)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (300, y0 + 82), str(it["sub"]), _get_font(19), _with_alpha(world["muted"], g_s), 680, max_lines=2)
            if i < n - 1 and g_lnk > 0.02:
                _bezier(stage, (640, y0 + h), (640, y0 + lh), col, reveal=g_lnk, progress=progress, label=str(it.get("edge") or ""), world=world)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 12. CHEVRON / PIPELINE RIBBON -> Staged chevron sequence + bottom detail panel
    if arch == "chevron":
        n = min(5, max(2, len(norm)))
        rh = min(160, (SH - y_off - 205) // n)
        for i, it in enumerate(norm[:n]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            y0 = SY0 + y_off + 20 + i * rh
            indent = 26 * (i % 2)
            stage.draw_glass_card((76 + indent, y0, 1004 - indent, y0 + rh - 16), radius=18, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_bdg > 0.02:
                stage.draw_pill(144 + indent, y0 + (rh - 16) // 2, f"STAGE {i+1}", (*col[:3], 42), col, border_col=col, font=_get_font(17, bold=True), alpha_mul=g_bdg)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (226 + indent, y0 + 18), str(it.get("name") or ""), _get_font(23, bold=True), _with_alpha(world["text"], g_t), 730 - indent * 2, max_lines=1 if it.get("sub") else 2)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (226 + indent, y0 + 54), str(it["sub"]), _get_font(18), _with_alpha(world["muted"], g_s), 730 - indent * 2, max_lines=1)
        act_i = min(n - 1, int(max(0.0, min(0.999, progress)) * n))
        g_ft = max(gf, _ease(min(1.0, progress / 0.28)))
        stage.draw_glass_card((76, SY1 - 165, 1004, SY1 - 24), radius=20, accent_col=world["emerald"], alpha_mul=g_ft, active=True)
        _draw_wrapped(stage.draw, (108, SY1 - 120), f"Active Stage: {norm[act_i].get('name', '')}", _get_font(25, bold=True), _with_alpha(world["emerald"], g_ft), 864, align="center", max_lines=1)
        return

    # 13. BENTO -> Asymmetric Hero + Metric Tiles Mosaic
    if arch == "bento":
        hero = norm[0] if norm else {"name": "Core System"}
        rest = norm[1:5] if len(norm) > 1 else [{"name": "Throughput"}, {"name": "Latency"}, {"name": "Safety"}]
        stage.draw_glass_card((76, SY0 + y_off + 20, 1004, SY0 + y_off + 290), radius=24, accent_col=world["cyan"], alpha_mul=g0, active=True, layered=True)
        _draw_vis(stage, 180, SY0 + y_off + 145, 56, 24, 36, world["cyan"], g0, shape="geodesic_sphere", active=True, progress=progress)
        _draw_wrapped(stage.draw, (268, SY0 + y_off + 86), str(hero.get("name") or ""), _get_font(30, bold=True), _with_alpha(world["text"], g0), 700, max_lines=2)
        if hero.get("sub"):
            _draw_wrapped(stage.draw, (268, SY0 + y_off + 180), str(hero["sub"]), _get_font(22), _with_alpha(world["cyan"], g0), 700, max_lines=2)
        gw = (SW - 18) // 2
        for i, it in enumerate(rest[:4]):
            gt_raw = _spring_gate(progress, i + 1, len(rest) + 1, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            c_i, r_i = i % 2, i // 2
            x0 = SX0 + c_i * (gw + 18)
            y0 = SY0 + y_off + 314 + r_i * 235
            col = _res_col(world, it.get("color"), _ACCENT[(i + 1) % len(_ACCENT)])
            stage.draw_glass_card((x0, y0, x0 + gw, y0 + 216), radius=20, accent_col=col, alpha_mul=g_b, active=(int(progress * 4) == i))
            if g_bdg > 0.02:
                stage.draw_pill(x0 + 62, y0 + 36, f"TILE {i+1}", (*col[:3], 42), col, border_col=col, font=_get_font(17, bold=True), alpha_mul=g_bdg)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (x0 + 22, y0 + 78), str(it.get("name") or ""), _get_font(23, bold=True), _with_alpha(world["text"], g_t), gw - 44, max_lines=2)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (x0 + 22, y0 + 146), str(it["sub"]), _get_font(18), _with_alpha(world["muted"], g_s), gw - 44, max_lines=2)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 14. TIMELINE_V -> Glowing Vertical Spine Milestones
    if arch == "timeline_v":
        n = min(5, len(norm))
        sx_spine = 178
        stage.draw.line((sx_spine, SY0 + y_off + 40, sx_spine, SY1 - 100), fill=_with_alpha((*world["cyan"][:3], 130), g0), width=5)
        rh = min(185, (SH - y_off - (110 if footer_note else 40)) // max(1, n))
        for i, it in enumerate(norm[:n]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            cy = SY0 + y_off + 80 + i * rh
            if g_bdg > 0.02:
                stage.draw.ellipse((sx_spine - 22, cy - 22, sx_spine + 22, cy + 22), fill=_with_alpha(col, g_bdg), outline=_with_alpha(world["glass_rim"], g_bdg), width=3)
                stage.draw.text((sx_spine - 10, cy - 13), f"{i+1}", font=_get_font(21, bold=True), fill=_with_alpha(world["bg_top"], g_bdg))
            stage.draw_glass_card((228, cy - 54, 1000, cy + 58), radius=18, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (254, cy - 36), str(it.get("name") or ""), _get_font(24, bold=True), _with_alpha(world["text"], g_t), 720, max_lines=1 if it.get("sub") else 2)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (254, cy + 8), str(it["sub"]), _get_font(19), _with_alpha(world["muted"], g_s), 720, max_lines=1)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 15. PYRAMID / FUNNEL -> Tapered Tiers Stacked Center-Aligned
    if arch in ("pyramid", "funnel"):
        n = min(5, max(3, len(norm)))
        rh = min(165, (SH - y_off - (110 if footer_note else 40)) // n)
        is_f = (arch == "funnel")
        for i, it in enumerate(norm[:n]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            frac = (1.0 - i * 0.14) if is_f else (0.36 + i * 0.16)
            bw = max(320, int(900 * min(1.0, frac)))
            bx0 = 540 - bw // 2
            y0 = SY0 + y_off + 24 + i * rh
            col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((bx0, y0, bx0 + bw, y0 + rh - 14), radius=18, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (bx0 + 20, y0 + (18 if it.get("sub") else (rh - 14) // 2 - 22)), str(it.get("name") or ""), _get_font(23, bold=True), _with_alpha(world["text"], g_t), bw - 40, align="center", max_lines=1 if it.get("sub") else 2)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (bx0 + 20, y0 + 58), str(it["sub"]), _get_font(18), _with_alpha(world["muted"], g_s), bw - 40, align="center", max_lines=1)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 16. QUADRANT -> 2x2 Matrix With X/Y Crosshair Axes
    if arch == "quadrant":
        cx, cy = 540, SY0 + y_off + (SH - y_off) // 2
        stage.draw.line((80, cy, 1000, cy), fill=_with_alpha(world["cyan"], g0), width=4)
        stage.draw.line((cx, SY0 + y_off + 20, cx, SY1 - 24), fill=_with_alpha(world["cyan"], g0), width=4)
        coords = [(96, SY0 + y_off + 46, cx - 18, cy - 18), (cx + 18, SY0 + y_off + 46, 984, cy - 18), (96, cy + 18, cx - 18, SY1 - 40), (cx + 18, cy + 18, 984, SY1 - 40)]
        for i, (x0, y0, x1, y1) in enumerate(coords):
            it = norm[i % len(norm)]
            gt_raw = _spring_gate(progress, i, 4, 0.24)
            if gt_raw <= 0.02:
                continue
            g_b, g_bdg, g_t, g_s = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "badge"), _sub_gate(gt_raw, "title"), _sub_gate(gt_raw, "sub")
            col = _res_col(world, _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((x0, y0, x1, y1), radius=20, accent_col=col, alpha_mul=g_b, active=(int(progress * 4) == i))
            if g_bdg > 0.02:
                stage.draw_pill(x0 + 60, y0 + 34, f"Q{i+1}", (*col[:3], 42), col, border_col=col, font=_get_font(18, bold=True), alpha_mul=g_bdg)
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (x0 + 20, y0 + 82), str(it.get("name") or ""), _get_font(23, bold=True), _with_alpha(world["text"], g_t), (x1 - x0) - 40, max_lines=3)
            if it.get("sub") and g_s > 0.02:
                _draw_wrapped(stage.draw, (x0 + 20, y0 + 182), str(it["sub"]), _get_font(18), _with_alpha(world["muted"], g_s), (x1 - x0) - 40, max_lines=2)
        return

    # 17. WATERFALL / LADDER -> Staggered Execution Spans or Stepped Escalation
    if arch in ("waterfall", "ladder"):
        n = min(6, max(3, len(norm)))
        rh = min(148, (SH - y_off - (110 if footer_note else 40)) // n)
        for i, it in enumerate(norm[:n]):
            gt_raw = _spring_gate(progress, i, n, 0.22)
            if gt_raw <= 0.02:
                continue
            g_b, g_t = _sub_gate(gt_raw, "box"), _sub_gate(gt_raw, "title")
            col = _res_col(world, _ACCENT[i % len(_ACCENT)])
            y0 = SY0 + y_off + 24 + i * rh
            if arch == "waterfall":
                x0 = 84 + i * 75
                bw = max(240, 460 - i * 32)
            else:
                x0 = 84 + (n - 1 - i) * 52
                bw = 920 - (x0 - 84) * 2
            stage.draw_glass_card((x0, y0, min(1004, x0 + bw), y0 + rh - 14), radius=16, accent_col=col, alpha_mul=g_b, active=(int(progress * n) == i))
            if g_t > 0.02:
                _draw_wrapped(stage.draw, (x0 + 20, y0 + (rh - 14) // 2 - 20), str(it.get("name") or ""), _get_font(22, bold=True), _with_alpha(world["text"], g_t), min(980, x0 + bw) - x0 - 40, max_lines=2)
        if gf > 0.03 and footer_note:
            stage.draw_glass_card((80, SY1 - 80, 1000, SY1 - 16), radius=18, accent_col=world["emerald"], alpha_mul=gf, active=True)
            _draw_wrapped(stage.draw, (112, SY1 - 60), footer_note[:60], _get_font(22, bold=True), _with_alpha(world["emerald"], gf), 856, align="center", max_lines=1)
        return

    # 18. TABLE -> Matrix / Isolation Levels / Cohort Matrix / Knapsack DP
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


GRAMMAR_50_PRESETS: Tuple[str, ...] = (
    # 2D Grid & Matrix Compositions (22)
    "grammar:grid:2x2", "grammar:grid:3x2", "grammar:grid:2x3", "grammar:grid:3x3",
    "grammar:grid:4x2", "grammar:grid:2x4", "grammar:grid:nodes_2x2", "grammar:grid:shards_3x2",
    "grammar:grid:layers_2x3", "grammar:grid:pillars_2x2", "grammar:grid:checks_3x2", "grammar:grid:rules_3x3",
    "grammar:matrix:2x2", "grammar:matrix:3x2", "grammar:matrix:2x3", "grammar:matrix:3x3",
    "grammar:matrix:risk_2x2", "grammar:matrix:iso_2x2", "grammar:matrix:auth_3x2", "grammar:matrix:perf_3x3",
    "grammar:matrix:sla_2x2", "grammar:matrix:rbac_3x2",
    # Bento & Asymmetric Mosaics (16)
    "grammar:bento:3", "grammar:bento:4", "grammar:bento:5", "grammar:bento:kpi_4",
    "grammar:bento:hero_5", "grammar:bento:slo_4", "grammar:bento:cache_5", "grammar:bento:rag_4",
    "grammar:bento:infra_5", "grammar:bento:sec_4", "grammar:quadrant:2x2", "grammar:quadrant:matrix",
    "grammar:quadrant:effort_impact", "grammar:quadrant:cap_risk", "grammar:quadrant:cost_latency", "grammar:quadrant:build_buy",
    # Sequential Flow, Code Flow & Chevron Pipelines (26)
    "grammar:flow:3", "grammar:flow:4", "grammar:flow:5", "grammar:flow:ingest_4",
    "grammar:flow:cdc_5", "grammar:flow:auth_4", "grammar:flow:rag_5", "grammar:flow:deploy_4",
    "grammar:flow:checkout_5", "grammar:flow:sync_3", "grammar:code_flow:3", "grammar:code_flow:4",
    "grammar:code_flow:5", "grammar:code_flow:async_4", "grammar:code_flow:sql_4", "grammar:code_flow:rust_5",
    "grammar:chevron:3", "grammar:chevron:4", "grammar:chevron:5", "grammar:chevron:etl_4",
    "grammar:chevron:ci_5", "grammar:chevron:release_4", "grammar:pipeline:3", "grammar:pipeline:4",
    "grammar:pipeline:5", "grammar:pipeline:stream_5",
    # Rings, Hubs, Orbits & Cycles (22)
    "grammar:ring:3", "grammar:ring:4", "grammar:ring:5", "grammar:ring:6",
    "grammar:ring:raft_5", "grammar:ring:hash_6", "grammar:ring:sdlc_6", "grammar:ring:react_4",
    "grammar:hub:3", "grammar:hub:4", "grammar:hub:5", "grammar:hub:gateway_5",
    "grammar:hub:mesh_4", "grammar:hub:broker_5", "grammar:orbit:3", "grammar:orbit:4",
    "grammar:orbit:5", "grammar:orbit:6", "grammar:cycle:3", "grammar:cycle:4",
    "grammar:cycle:5", "grammar:cycle:6",
    # Hierarchical Trees & Triangles (16)
    "grammar:tree:2", "grammar:tree:3", "grammar:tree:4", "grammar:tree:ast_3",
    "grammar:tree:btree_4", "grammar:tree:dom_3", "grammar:tree:merkle_4", "grammar:tree:org_3",
    "grammar:tree:behavior_4", "grammar:tree:index_3", "grammar:triangle:cap", "grammar:triangle:cia",
    "grammar:triangle:cost", "grammar:triangle:iron", "grammar:triangle:perf", "grammar:triangle:quorum",
    # Slots, Memory Arrays & Swimlanes (18)
    "grammar:slots:3", "grammar:slots:4", "grammar:slots:5", "grammar:slots:6",
    "grammar:slots:ringbuf_5", "grammar:slots:cache_6", "grammar:slots:ecs_5", "grammar:slots:wal_4",
    "grammar:slots:kv_6", "grammar:slots:tsn_5", "grammar:swimlane:2", "grammar:swimlane:3",
    "grammar:swimlane:4", "grammar:swimlane:async_3", "grammar:swimlane:svc_4", "grammar:swimlane:saga_4",
    "grammar:swimlane:payment_3", "grammar:swimlane:etl_4",
    # Tiers, Stacks, Pyramids, Funnels & Ladders (22)
    "grammar:tiers:3", "grammar:tiers:4", "grammar:tiers:5", "grammar:tiers:6",
    "grammar:tiers:osi_6", "grammar:tiers:mem_4", "grammar:tiers:sec_5", "grammar:stack:3",
    "grammar:stack:4", "grammar:stack:5", "grammar:pyramid:3", "grammar:pyramid:4",
    "grammar:pyramid:5", "grammar:pyramid:test_4", "grammar:funnel:3", "grammar:funnel:4",
    "grammar:funnel:5", "grammar:funnel:latency_4", "grammar:ladder:3", "grammar:ladder:4",
    "grammar:ladder:5", "grammar:ladder:growth_5",
    # Dual Compare, Sequences, Timelines, Waterfalls & Tables (14 -> 156 total!)
    "grammar:dual:vs", "grammar:dual:tradeoff", "grammar:dual:before_after", "grammar:split:60_40",
    "grammar:split:sync_async", "grammar:timeline_v:3", "grammar:timeline_v:4", "grammar:timeline_v:5",
    "grammar:waterfall:4", "grammar:waterfall:5", "grammar:waterfall:6", "grammar:seq:3",
    "grammar:seq:4", "grammar:seq:5", "grammar:table:3x3", "grammar:table:4x4",
)

GRAMMAR_150_PRESETS: Tuple[str, ...] = GRAMMAR_50_PRESETS


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

    # Handle universal Composable Diagram Grammar expressions (56+ named presets + dynamic grammar:<kind>:<param>)
    _GRAMMAR_PREFIXES = (
        "grammar:", "grid:", "flow:", "ring:", "tree:", "slots:", "tiers:", "dual:",
        "swimlane:", "chevron:", "bento:", "timeline_v:", "pyramid:", "funnel:",
        "quadrant:", "waterfall:", "ladder:", "hub:", "matrix:", "pipeline:", "orbit:",
        "cycle:", "table:", "seq:", "triangle:",
    )
    if l in GRAMMAR_50_PRESETS or l.startswith(_GRAMMAR_PREFIXES) or (data and data.get("grammar")):
        g_spec, g_items = _parse_grammar_items(l, data or {})
        kind = g_spec.split(":", 1)[0]
        arch = {
            "stack": "tiers",
            "matrix": "grid",
            "pipeline": "chevron",
            "orbit": "ring",
            "cycle": "ring",
            "split": "dual",
        }.get(kind, kind)
        valid_archs = (
            "flow", "code_flow", "tiers", "ring", "hub", "dual", "slots", "tree",
            "triangle", "seq", "table", "grid", "swimlane", "chevron", "bento",
            "timeline_v", "pyramid", "funnel", "quadrant", "waterfall", "ladder",
        )
        if arch not in valid_archs:
            arch = "flow"
        _render_archetype(stage, arch, str((data or {}).get("subtitle") or g_spec.upper()), (), {"items": g_items}, progress, world, helpers)
        return True

    return False
