import math
from typing import Any, Dict, List, Tuple

from core.shapes_3d import draw_vector_glyph

IT_SDLC_35_LAYOUTS: Tuple[str, ...] = (
    # 22 Networking, Edge Protocols & IT Infrastructure Topologies
    "osi_7_layers", "tcp_ip_handshake", "dns_resolution_flow", "vpc_subnet_topology",
    "cdn_edge_routing", "vpn_tunnel_mesh", "firewall_dmz_zones", "vlan_switch_ports",
    "bgp_routing_table", "zero_trust_mesh",
    "quic_http3_0rtt", "mtls_handshake_1rtt", "nat_traversal_stun_turn", "anycast_global_routing",
    "mpls_label_switching", "ipsec_ikev2_tunnel", "grpc_http2_multiplex", "ws_frame_duplex_flow",
    "arp_ndp_discovery", "ebpf_xdp_packet_drop", "service_mesh_envoy_proxy", "wireshark_packet_dissect",
    # 22 Data Engineering, Lakehouse & Streaming Pipelines
    "etl_elt_pipeline", "medallion_lakehouse", "lambda_kappa_arch", "kafka_streaming_topology",
    "star_snowflake_schema", "cdc_debezium_flow", "data_warehouse_cluster", "data_quality_lineage",
    "spark_dag_stages", "feature_store_ml",
    "iceberg_snapshot_tables", "delta_lake_time_travel", "flink_watermarks_window", "dbt_dag_lineage",
    "airflow_task_sensors", "trino_federated_query", "clickhouse_mergetree_parts", "parquet_columnar_rowgroup",
    "duckdb_vectorized_scan", "schema_registry_avro", "reverse_etl_sync", "data_contract_sla_gate",
    # 22 Software Development Lifecycle (SDLC), GitOps, CI/CD & Quality
    "sdlc_cycle_wheel", "cicd_pipeline_stages", "agile_sprint_board", "gitflow_release_lanes",
    "test_pyramid_qa", "blue_green_canary", "microservices_mesh", "event_driven_cqrs",
    "observability_pillars", "devsecops_shield_gate",
    "trunk_based_flags", "gitops_argocd_reconcile", "sbom_supply_chain_scan", "sast_dast_security_gate",
    "chaos_monkey_fault_inj", "contract_testing_pact", "mutation_testing_score", "dora_metrics_four_keys",
    "postmortem_blameless_loop", "incident_sev1_war_room", "release_train_cadence", "mono_vs_polyrepo_deps",
    # 20 Cloud Platform, Kubernetes, SRE & Observability
    "tech_stack_layers", "hardware_rack_diagram", "cloud_services_map", "language_ecosystem",
    "client_server_cluster",
    "k8s_pod_scheduling", "helm_kustomize_overlay", "terraform_state_lock", "finops_spot_autoscaling",
    "prometheus_scrape_tsdb", "opentelemetry_span_context", "loki_log_aggregation", "pagerduty_oncall_escalation",
    "geo_dns_active_active", "dr_rpo_rto_failover", "iam_least_privilege_rbac", "kms_envelope_encryption",
    "cdn_cache_invalidation", "api_gateway_rate_limit", "firecracker_microvm_boot",
    # 19 Systems Hardware, Firmware & Embedded Compute
    "cpu_cache_coherency_mesi", "nvme_submission_queues", "pcie_dma_ring_buffer", "fpga_lut_pipeline",
    "arm_big_little_cores", "bios_uefi_secure_boot", "usb4_thunderbolt_lanes", "ddr5_channel_timing",
    "tpu_systolic_array", "nic_rss_multi_queue", "san_iscsi_storage_fabric", "ecc_memory_scrubbing",
    "pdu_ups_power_redundancy", "edge_iot_mqtt_broker", "wasm_wasi_sandbox", "virtualization_kvm_qemu",
    "sr_iov_vf_passthrough", "numa_node_pinning", "bmc_ipmi_out_of_band",
    # +10 Network & Zero-Trust Security Protocols (32 total)
    "bgp_blackhole_filter", "dnssec_trust_chain", "wireguard_cryptokey", "ipv6_slaac_autoconf",
    "sdwan_smart_path", "haproxy_tls_sni", "waf_owasp_ruleset", "dhcp_dora_leases",
    "ntp_stratum_clock", "ssh_ca_bastion_cert",
    # +10 Data Lakehouse & Streaming Compute (32 total)
    "hudi_mor_cow_storage", "polars_lazy_optimizer", "ray_distributed_actors", "presto_disk_spilling",
    "bi_semantic_metrics", "debezium_chunk_snap", "pulsar_bookkeeper_tier", "ch_materialized_view",
    "dq_great_expectations", "openmetadata_lineage",
    # +10 SDLC, GitOps & Quality Automation (32 total)
    "ephemeral_pr_env", "renovate_dep_bot", "sonarqube_code_gate", "e2e_test_sharding",
    "otel_baggage_context", "kayenta_canary_eval", "rds_blue_green_cut", "helm_atomic_rollback",
    "crossplane_xrds_crd", "vault_dynamic_leases",
    # +10 Cloud Managed Services & SRE (30 total)
    "aws_privatelink_svc", "spanner_truetime_gps", "cosmos_five_consist", "cf_durable_objects",
    "s3_oac_cloudfront", "eks_pod_identity_iam", "alb_drain_deregister", "s3_presigned_upload",
    "sqs_fifo_msggroup", "redis_cluster_16k",
    # +10 Kernel, CPU & Storage Internals (29 total -> 155 total)
    "l1_set_associative", "tlb_shootdown_core", "io_uring_shared_ring", "linux_page_cache_wb",
    "cgroup_v2_psi_stall", "ext4_journal_modes", "zfs_arc_cow_pool", "usb4_pcie_tunneling",
    "avx_gather_scatter", "cpu_tage_predictor",
)

IT_SDLC_100_LAYOUTS: Tuple[str, ...] = IT_SDLC_35_LAYOUTS

_IT_70_EXTRA_PRESETS: Dict[str, List[Dict[str, Any]]] = {
    # +12 Networking & Edge Protocols
    "quic_http3_0rtt": [{"name": "UDP + TLS 1.3 Combined", "sub": "Eliminates TCP 3-Way Stall", "shape": "router"}, {"name": "0-RTT Session Resumption", "sub": "Encrypted Data on First Flight", "shape": "vpn_tunnel"}, {"name": "Independent QUIC Streams", "sub": "Zero Head-of-Line Blocking", "shape": "network_switch"}],
    "mtls_handshake_1rtt": [{"name": "1. ClientHello + KeyShare", "sub": "ECDHE x25519 + Cipher Suites", "shape": "laptop"}, {"name": "2. ServerHello + Cert + Finished", "sub": "Single 1-RTT Handshake Done", "shape": "server_rack"}, {"name": "3. Encrypted App Stream", "sub": "AEAD AES-GCM Forward Secrecy", "shape": "lock"}],
    "nat_traversal_stun_turn": [{"name": "Peer Behind NAT Firewall", "sub": "Learns Public IP:Port via STUN", "shape": "firewall_wall"}, {"name": "ICE Candidate Pair Check", "sub": "Direct UDP Hole Punching", "shape": "router"}, {"name": "TURN Relay Fallback", "sub": "Symmetrical NAT Safe Path", "shape": "hub"}],
    "anycast_global_routing": [{"name": "Single Global Anycast IP", "sub": "203.0.113.10 Announced Worldwide", "shape": "cdn_edge"}, {"name": "BGP Nearest POP Routing", "sub": "AS-Path Routes to Nearest Edge", "shape": "router"}, {"name": "Local POP Failover <1s", "sub": "Withdraw Route On Outage", "shape": "server_rack"}],
    "mpls_label_switching": [{"name": "Ingress LER Push Label", "sub": "Classify IP -> Label #4091", "shape": "router"}, {"name": "Core LSR Fast Label Swap", "sub": "Hardware Lookup Without IP Parse", "shape": "network_switch"}, {"name": "Egress LER Pop Label", "sub": "Deliver Clean Packet to LAN", "shape": "server_rack"}],
    "ipsec_ikev2_tunnel": [{"name": "IKEv2 SA Mutual Auth", "sub": "Diffie-Hellman Keys Established", "shape": "lock"}, {"name": "ESP Encapsulating Security", "sub": "Encrypts Inner IP Packet", "shape": "vpn_tunnel"}, {"name": "Multi-Site Encrypted Mesh", "sub": "HQ <-> Branch Zero-Trust Link", "shape": "router"}],
    "grpc_http2_multiplex": [{"name": "Protobuf Binary Schema", "sub": "5x Smaller Than JSON Payloads", "shape": "code_cube"}, {"name": "Single TCP HTTP/2 Mux", "sub": "Concurrent Bidirectional Streams", "shape": "network_switch"}, {"name": "HPACK Header Compression", "sub": "Sub-ms Service-to-Service RPC", "shape": "server_rack"}],
    "ws_frame_duplex_flow": [{"name": "HTTP 101 Upgrade Request", "sub": "Switch TCP Socket To Persistent", "shape": "api_plug_3d"}, {"name": "2-Byte Lightweight Framing", "sub": "Full-Duplex Server Push Frames", "shape": "hub"}, {"name": "Heartbeat Ping / Pong", "sub": "Keep Idle Realtime Feed Alive", "shape": "radar_dish"}],
    "arp_ndp_discovery": [{"name": "Broadcast: Who Has 10.0.0.5?", "sub": "L2 Ethernet FF:FF:FF:FF Frame", "shape": "network_switch"}, {"name": "Unicast Reply: MAC aa:bb:cc", "sub": "Target Updates Neighbour Table", "shape": "server_rack"}, {"name": "ARP Cache Entry (TTL 60s)", "sub": "Direct L2 Frame Forwarding", "shape": "ethernet_port"}],
    "ebpf_xdp_packet_drop": [{"name": "NIC Driver RX Ring", "sub": "Packet Arrives Before sk_buff", "shape": "ethernet_port"}, {"name": "XDP eBPF JIT Filter", "sub": "40M Packets/s DDoS Match", "shape": "shield"}, {"name": "XDP_DROP / XDP_REDIRECT", "sub": "Bypass Kernel TCP/IP Stack", "shape": "fiber_cable"}],
    "service_mesh_envoy_proxy": [{"name": "Sidecar Envoy Proxy", "sub": "Auto mTLS + Retries + Timeouts", "shape": "network_switch", "icon": "envoy"}, {"name": "xDS Control Plane", "sub": "Dynamic Route & Endpoint Push", "shape": "k8s_pod_mesh"}, {"name": "Zero App Code Change", "sub": "App Calls Localhost Port", "shape": "server_rack"}],
    "wireshark_packet_dissect": [{"name": "Frame + Ethernet L2 Header", "sub": "Src/Dst MAC + VLAN 802.1Q", "shape": "ethernet_port"}, {"name": "IPv4/IPv6 + TCP Flags", "sub": "SYN/ACK/PSH Window Size", "shape": "firewall_wall"}, {"name": "TLS / HTTP Payload", "sub": "Filter tcp.analysis.retransmission", "shape": "terminal_box"}],
    # +12 Data Engineering, Lakehouse & Streaming
    "iceberg_snapshot_tables": [{"name": "Catalog Pointer -> v14", "sub": "Atomic Compare-And-Swap Commit", "shape": "data_lake"}, {"name": "Snapshot Manifest List", "sub": "Tracks Partition Bounds (min/max)", "shape": "schema_table"}, {"name": "Immutable Parquet Datafiles", "sub": "Time-Travel & Hidden Partitioning", "shape": "warehouse_3d"}],
    "delta_lake_time_travel": [{"name": "_delta_log JSON Commits", "sub": "Ordered ACID Transaction Log", "shape": "schema_table"}, {"name": "Snapshot Version Isolation", "sub": "Concurrent Writers With OCC", "shape": "data_lake"}, {"name": "SELECT VERSION AS OF 12", "sub": "Instant Rollback & Audit", "shape": "warehouse_3d"}],
    "flink_watermarks_window": [{"name": "Event-Time Timestamp Extract", "sub": "Handles Out-of-Order Mobile Logs", "shape": "kafka_broker", "icon": "flink"}, {"name": "Watermark W(t) Boundary", "sub": "Bounded Lateness Tolerance", "shape": "radar_dish"}, {"name": "Tumbling / Sliding Window", "sub": "Chandy-Lamport RocksDB Snap", "shape": "warehouse_3d"}],
    "dbt_dag_lineage": [{"name": "Staging Models (Clean Views)", "sub": "Rename, Cast & Deduplicate Raw", "shape": "schema_table", "icon": "dbt"}, {"name": "Intermediate Business Joins", "sub": "Incremental Merge Partitioning", "shape": "dag_pipeline"}, {"name": "Mart Models + Schema Tests", "sub": "unique, not_null, ref() DAG", "shape": "warehouse_3d"}],
    "airflow_task_sensors": [{"name": "S3 / API Deferrable Sensor", "sub": "Zero Worker Slot Blocking", "shape": "radar_dish", "icon": "airflow"}, {"name": "Dynamic Task Mapping .expand()", "sub": "Fan-Out Parallel Partition Tasks", "shape": "dag_nodes"}, {"name": "XCom & SLA Callback Alert", "sub": "Deterministic Backfill Support", "shape": "ci_runner"}],
    "trino_federated_query": [{"name": "Trino Coordinator Planner", "sub": "Cost-Based Distributed SQL DAG", "shape": "hub", "icon": "trino"}, {"name": "Parallel MPP Worker Fleet", "sub": "Join S3 Iceberg + Postgres", "shape": "server_rack"}, {"name": "Dynamic Partition Pruning", "sub": "Skip 95% Unrelated Splits", "shape": "data_lake"}],
    "clickhouse_mergetree_parts": [{"name": "Batch Insert -> Immutable Part", "sub": "Sorted By ORDER BY Primary Key", "shape": "warehouse_3d", "icon": "clickhouse"}, {"name": "Sparse Primary Index (Granules)", "sub": "1 Entry Per 8192 Rows In RAM", "shape": "chip"}, {"name": "Background Zstd Merge", "sub": "Sub-50ms Billion-Row OLAP", "shape": "data_lake"}],
    "parquet_columnar_rowgroup": [{"name": "Row Group Partition (128MB)", "sub": "Independent Parallel Split", "shape": "data_lake"}, {"name": "Columnar Dictionary + RLE", "sub": "80% Compression & Read Only Used Cols", "shape": "schema_table"}, {"name": "Page Footer Min/Max Stats", "sub": "Predicate Pushdown Skip", "shape": "ssd_nvme"}],
    "duckdb_vectorized_scan": [{"name": "Zero-Server In-Process Engine", "sub": "Runs Inside Python / Lambda / CLI", "shape": "laptop", "icon": "duckdb"}, {"name": "2048-Row Vectorized SIMD", "sub": "CPU L1/L2 Cache Friendly Push", "shape": "chip"}, {"name": "Direct Parquet / S3 HTTP Range", "sub": "GBs Analyzed In Milliseconds", "shape": "data_lake"}],
    "schema_registry_avro": [{"name": "Producer Checks Schema ID", "sub": "Prefers Compact 4-Byte ID Header", "shape": "api_plug_3d"}, {"name": "Compatibility Gate (BACKWARD)", "sub": "Blocks Breaking Column Deletes", "shape": "firewall_wall"}, {"name": "Safe Schema Evolution", "sub": "Zero Broken Downstream Consumers", "shape": "kafka_broker"}],
    "reverse_etl_sync": [{"name": "Single Source Warehouse Truth", "sub": "Gold Customer Churn Score", "shape": "warehouse_3d"}, {"name": "Incremental Diff Detector", "sub": "Compute Only Changed Records", "shape": "dag_pipeline"}, {"name": "Sync -> CRM / Ads / Slack", "sub": "Rate-Limited Batch Upserts", "shape": "api_plug_3d"}],
    "data_contract_sla_gate": [{"name": "Producer YAML Schema + SLA", "sub": "Owner, Freshness <15m, Types", "shape": "schema_table"}, {"name": "CI/CD Contract Diff Gate", "sub": "Block Breaking PR Before Merge", "shape": "pr_merge"}, {"name": "Quarantine Bad Records (DLQ)", "sub": "Keep Production Tables Clean", "shape": "firewall_wall"}],
    # +12 SDLC, GitOps, DevSecOps & Quality
    "trunk_based_flags": [{"name": "Short-Lived Branches (<1 Day)", "sub": "Small Frequent Merges -> main", "shape": "pr_merge"}, {"name": "Feature Flag Kill Switch", "sub": "Decouple Deploy From Release", "shape": "ci_runner"}, {"name": "Gradual Ring Rollout", "sub": "Internal -> 5% -> 100% Users", "shape": "release_tag_3d"}],
    "gitops_argocd_reconcile": [{"name": "Git Desired State Repo", "sub": "Signed Helm / Kustomize Commit", "shape": "git", "icon": "argocd"}, {"name": "Cluster Controller Drift Watch", "sub": "Detects Out-of-Band Edits", "shape": "radar_dish"}, {"name": "Auto-Reconcile Convergence", "sub": "Live State == Git SHA Always", "shape": "k8s_pod_mesh"}],
    "sbom_supply_chain_scan": [{"name": "CycloneDX / SPDX SBOM", "sub": "Full Transitive Dependency Tree", "shape": "schema_table"}, {"name": "Sigstore Cosign Provenance", "sub": "SLSA Level-3 Attestation", "shape": "lock"}, {"name": "CVE Policy Admission Gate", "sub": "Block Critical CVEs In Cluster", "shape": "firewall_wall"}],
    "sast_dast_security_gate": [{"name": "SAST Static AST Scan", "sub": "Catches SQLi / Secrets In PR", "shape": "terminal_box"}, {"name": "SCA + Container Trivy Scan", "sub": "OS Lib & npm/pip Audit", "shape": "container"}, {"name": "DAST Live Staging Probe", "sub": "Tests Auth & OWASP Headers", "shape": "shield"}],
    "chaos_monkey_fault_inj": [{"name": "Define Steady State SLA", "sub": "Error <0.1%, P99 <150ms", "shape": "gauge_dial"}, {"name": "Inject Packet Loss / Pod Kill", "sub": "Controlled Blast Radius Test", "shape": "firewall_wall"}, {"name": "Verify Auto-Heal Circuit", "sub": "Failover Triggers Under 5s", "shape": "server_rack"}],
    "contract_testing_pact": [{"name": "Consumer Publishes Pact JSON", "sub": "Exact API Expectations Recorded", "shape": "laptop"}, {"name": "Pact Broker Matrix", "sub": "Tracks Consumer x Provider SHAs", "shape": "hub"}, {"name": "Provider Verifies Without Env", "sub": "Catch Breaks Before Deploy", "shape": "ci_runner"}],
    "mutation_testing_score": [{"name": "Inject Bug Mutants (+ -> -, ==)", "sub": "Create 50 Code Variants", "shape": "code_cube"}, {"name": "Run Unit Test Suite", "sub": "Check If Tests Catch Mutant", "shape": "unit_test_cube"}, {"name": "Killed >85% Mutation Score", "sub": "Proves Real Assertion Strength", "shape": "release_tag_3d"}],
    "dora_metrics_four_keys": [{"name": "Deployment Frequency & Lead Time", "sub": "Multiple/Day • Commit-to-Prod <1h", "shape": "rocket"}, {"name": "Change Failure Rate (<5%)", "sub": "Small Batches Reduce Blast", "shape": "shield"}, {"name": "MTTR Recovery Time (<30m)", "sub": "Instant Feature Flag Revert", "shape": "gauge_dial"}],
    "postmortem_blameless_loop": [{"name": "Timeline & Detection Gap", "sub": "Factual Seconds-Level Log", "shape": "terminal_box"}, {"name": "Systemic Root Contributors", "sub": "Fix Guardrails Never People", "shape": "hub"}, {"name": "Tracked P0 Prevention Action", "sub": "CI Alert Or Auto-Limiter Added", "shape": "ci_runner"}],
    "incident_sev1_war_room": [{"name": "Incident Commander + Comms", "sub": "Single Coordinator Clears Noise", "shape": "headset"}, {"name": "Roll Back / Shed Load First", "sub": "Restore Users Before Deep Debug", "shape": "load_balancer"}, {"name": "Status Page + Root Fix", "sub": "Clear SLA Transparency", "shape": "server_rack"}],
    "release_train_cadence": [{"name": "Weekly Cut Off Branch", "sub": "Predictable Fixed Train Departure", "shape": "ci_runner"}, {"name": "Feature Ready -> Boards Train", "sub": "Incomplete Work Behind Flag", "shape": "release_tag_3d"}, {"name": "Zero Merge-Freeze Panic", "sub": "Calm Repeatable Shipping", "shape": "rocket"}],
    "mono_vs_polyrepo_deps": [{"name": "Monorepo Atomic Cross-Pkg PR", "sub": "Bazel / Nx Affected Graph Cache", "shape": "dag_pipeline"}, {"name": "Polyrepo Independent Releases", "sub": "Clear Ownership & SemVer Boundaries", "shape": "k8s_pod_mesh"}, {"name": "CI Remote Build Cache", "sub": "Rebuild Only Changed Targets", "shape": "server_rack"}],
    # +15 Cloud Platform, Kubernetes, SRE & Observability
    "k8s_pod_scheduling": [{"name": "API Server -> etcd Persist", "sub": "Validates Pod Spec + Admission", "shape": "k8s_pod_mesh", "icon": "kubernetes"}, {"name": "Scheduler Filter & Score Nodes", "sub": "CPU/RAM, Taints, Affinity Match", "shape": "server_rack"}, {"name": "Kubelet Pulls & Starts Cgroup", "sub": "Containerd + CNI Pod IP Ready", "shape": "container"}],
    "helm_kustomize_overlay": [{"name": "Base Clean K8s Manifests", "sub": "DRY Deployment + Service YAML", "shape": "schema_table", "icon": "helm"}, {"name": "Env Overlays (Dev / Stage / Prod)", "sub": "Patch Replicas, Limits & Secrets", "shape": "dag_nodes"}, {"name": "Deterministic Rendered Apply", "sub": "Auditable Diff Before Rollout", "shape": "k8s_pod_mesh"}],
    "terraform_state_lock": [{"name": "Acquire DynamoDB State Lock", "sub": "Prevents Concurrent Corrupt Edits", "shape": "lock", "icon": "terraform"}, {"name": "Plan DAG Diff vs Cloud API", "sub": "Exact Create / In-Place / Destroy", "shape": "dag_pipeline"}, {"name": "Atomic Apply + Remote S3 State", "sub": "Encrypted Versioned Infra Graph", "shape": "cloud"}],
    "finops_spot_autoscaling": [{"name": "Karpenter Bin-Packing Watch", "sub": "Right-Size Nodes Per Pending Pod", "shape": "k8s_pod_mesh"}, {"name": "Spot 70% Discount Pool + PDB", "sub": "Graceful 2-Min Drain On Notice", "shape": "server_rack"}, {"name": "On-Demand Core Fallback", "sub": "55% Cloud Bill Reduction Safely", "shape": "gauge_dial"}],
    "prometheus_scrape_tsdb": [{"name": "Pull /metrics Every 15s", "sub": "PromQL Counter & Histogram", "shape": "gauge_dial", "icon": "prometheus"}, {"name": "In-Memory 2h Head + WAL", "sub": "Xor Gorilla Float Compression", "shape": "ssd_nvme"}, {"name": "Alertmanager + Grafana Dash", "sub": "Multi-Window Burn Rate Alerts", "shape": "radar_dish", "icon": "grafana"}],
    "opentelemetry_span_context": [{"name": "Inject W3C traceparent Header", "sub": "TraceID Propagates Edge -> DB", "shape": "api_plug_3d"}, {"name": "OTel Collector Tail-Sample", "sub": "Keep 100% Errors + Slow Traces", "shape": "dag_pipeline"}, {"name": "Unified Metrics-Logs-Traces", "sub": "Jump Directly From Alert -> Line", "shape": "radar_dish"}],
    "loki_log_aggregation": [{"name": "Index Labels Only (App, Env)", "sub": "No Expensive Full-Text Inverted", "shape": "terminal_box"}, {"name": "Gzip Log Chunks -> S3 Object", "sub": "10x Cheaper Than Elastic Cluster", "shape": "data_lake"}, {"name": "LogQL Parallel Grep Stream", "sub": "Filter JSON At Query Time", "shape": "radar_dish"}],
    "pagerduty_oncall_escalation": [{"name": "Symptom-Based SLO Alert Fires", "sub": "Auto-Deduplicates Noise Storm", "shape": "radar_dish"}, {"name": "Primary -> 5m Backup Escalate", "sub": "Linked Runbook & One-Click Ack", "shape": "headset"}, {"name": "Blameless Action Follow-Up", "sub": "Auto-Create Jira Ticket", "shape": "server_rack"}],
    "geo_dns_active_active": [{"name": "Geo-DNS Latency Routing", "sub": "Route US-East / EU-West Locally", "shape": "cdn_edge"}, {"name": "Stateless Local Compute", "sub": "Zero Cross-Region Hop Per API", "shape": "k8s_pod_mesh"}, {"name": "CRDT / Global Spanner Sync", "sub": "Survives Full Region Blackout", "shape": "database_cluster"}],
    "dr_rpo_rto_failover": [{"name": "Continuous Async Snapshot", "sub": "RPO < 60 Seconds Max Data Loss", "shape": "database_cluster"}, {"name": "Warm Pilot-Light Standby", "sub": "Pre-Provisioned VPC & DB Read", "shape": "server_rack"}, {"name": "Automated DNS Failover", "sub": "RTO Recovery In <5 Minutes", "shape": "router"}],
    "iam_least_privilege_rbac": [{"name": "Short-Lived OIDC Workload ID", "sub": "Zero Static Long-Lived API Keys", "shape": "lock"}, {"name": "Scoped Resource + Action Policy", "sub": "Allow Only Bucket/prefix Read", "shape": "firewall_wall"}, {"name": "CloudTrail Audit + Access Analyzer", "sub": "Auto-Prune Unused Permissions", "shape": "shield"}],
    "kms_envelope_encryption": [{"name": "Generate Ephemeral Data Key", "sub": "Hardware HSM Root Never Leaves", "shape": "lock"}, {"name": "Encrypt File Locally With DEK", "sub": "Fast Multi-GB AES-GCM Stream", "shape": "ssd_nvme"}, {"name": "Store Wrapped Encrypted DEK", "sub": "Rotate Key Policy Centrally", "shape": "cloud"}],
    "cdn_cache_invalidation": [{"name": "Immutable Hash Assets (1y)", "sub": "app.a8f31.js Never Invalidated", "shape": "cdn_edge", "icon": "cloudflare"}, {"name": "Surrogate-Key Tag Purge", "sub": "Invalidate Product Group <150ms", "shape": "network_switch"}, {"name": "Stale-While-Revalidate Origin", "sub": "Origin Shield Prevents Stampede", "shape": "server_rack"}],
    "api_gateway_rate_limit": [{"name": "TLS Terminate + JWT Verify", "sub": "Drop Bad Auth At Edge", "shape": "firewall_wall"}, {"name": "Redis Token Bucket Limiter", "sub": "Per-Tenant RPS & Burst Quota", "shape": "gauge_dial"}, {"name": "Return 429 + Retry-After", "sub": "Protects Downstream Databases", "shape": "api_plug_3d"}],
    "firecracker_microvm_boot": [{"name": "Init Sandbox + Runtime Mount", "sub": "Firecracker MicroVM <125ms", "shape": "container", "icon": "aws_lambda"}, {"name": "SnapStart Memory Checkpoint", "sub": "Restore Pre-Warmed Heap Snapshot", "shape": "chip"}, {"name": "Warm Invocation Handler Reuse", "sub": "Keep DB Pools Outside Handler", "shape": "rocket"}],
    # +19 Systems Hardware, Firmware & Embedded Compute
    "cpu_cache_coherency_mesi": [{"name": "L1/L2 Cache Line (64 Bytes)", "sub": "Modified / Exclusive / Shared / Invalid", "shape": "chip"}, {"name": "False Sharing Pitfall", "sub": "Adjacent Vars Invalidate Cores", "shape": "blade_server"}, {"name": "Alignas(64) Cache Padding", "sub": "4x Parallel Thread Scaling", "shape": "gauge_dial"}],
    "nvme_submission_queues": [{"name": "Per-Core Lock-Free Queues", "sub": "Up to 64K Queues x 64K Cmds", "shape": "ssd_nvme"}, {"name": "PCIe DMA Zero-Copy Read", "sub": "Bypass Legacy SATA AHCI Bottleneck", "shape": "fiber_cable"}, {"name": "1M+ Random 4K IOPS", "sub": "Sub-100us NVMe Flash Latency", "shape": "server_rack"}],
    "pcie_dma_ring_buffer": [{"name": "Device -> Host RAM Ring Buffer", "sub": "Direct Memory Access Bypass CPU", "shape": "chip"}, {"name": "Scatter-Gather Descriptor", "sub": "Batched MSI-X Interrupts", "shape": "ethernet_port"}, {"name": "RDMA Zero-Copy Networking", "sub": "Microseconds Cluster Sync", "shape": "fiber_cable"}],
    "fpga_lut_pipeline": [{"name": "Deterministic Pipelined LUTs", "sub": "New Output Every 1 Clock Cycle", "shape": "chip"}, {"name": "BRAM Line Buffer Streaming", "sub": "Zero DRAM Stall Overhead", "shape": "ssd_nvme"}, {"name": "Custom Hardware Bitstream", "sub": "10x Lower Jitter Than CPU", "shape": "server_rack"}],
    "arm_big_little_cores": [{"name": "Efficiency Little Cores", "sub": "Background Sync @ Milliwatts", "shape": "chip"}, {"name": "Performance Big Out-of-Order", "sub": "Burst UI / Game Physics Speed", "shape": "gpu_rack"}, {"name": "EAS Energy-Aware Scheduler", "sub": "Doubles Mobile Battery Runtime", "shape": "ups_battery"}],
    "bios_uefi_secure_boot": [{"name": "Hardware ROM Root Trust", "sub": "Verify UEFI Platform Keys", "shape": "lock"}, {"name": "TPM PCR Hash Measurement", "sub": "Measure Bootloader -> Signed Kernel", "shape": "chip"}, {"name": "LUKS Disk Auto-Unlock", "sub": "Zero Tampered Rootkit Boot", "shape": "shield"}],
    "usb4_thunderbolt_lanes": [{"name": "Protocol Tunneling Mux", "sub": "USB3 + DisplayPort + PCIe Gen3", "shape": "fiber_cable"}, {"name": "40/80 Gbps Bi-Directional PAM3", "sub": "Single Type-C External GPU/NVMe", "shape": "laptop"}, {"name": "100W-240W USB-PD Negotiate", "sub": "Power + 4K Displays Together", "shape": "ups_battery"}],
    "ddr5_channel_timing": [{"name": "Dual Independent 32-Bit Sub-Ch", "sub": "Doubles Parallel Bank Access", "shape": "chip"}, {"name": "On-Die ECC Bit Repair", "sub": "High-Density Stability @ 6400MT/s", "shape": "blade_server"}, {"name": "PMIC On-DIMM Power Control", "sub": "Cleaner Voltage Signal Integrity", "shape": "rack_cabinet"}],
    "tpu_systolic_array": [{"name": "Weight-Stationary 128x128 Grid", "sub": "Load Matrix Weights Once", "shape": "gpu_rack"}, {"name": "Wavefront Activation Pulse", "sub": "Reuse Results Neighbor-to-Neighbor", "shape": "chip"}, {"name": "Extreme Matrix Ops / Watt", "sub": "Eliminate HBM Register Churn", "shape": "gauge_dial"}],
    "nic_rss_multi_queue": [{"name": "Receive Side Scaling Hash", "sub": "5-Tuple Hash -> Per-Core RX Ring", "shape": "ethernet_port"}, {"name": "Pin IRQ To NUMA Local Core", "sub": "Zero Cross-Socket Cache Bounce", "shape": "chip"}, {"name": "Line-Rate 100GbE Throughput", "sub": "Scales Linearly With CPU Cores", "shape": "network_switch"}],
    "san_iscsi_storage_fabric": [{"name": "Dedicated Storage VLAN / FC", "sub": "Multipath Active-Active Links", "shape": "network_switch"}, {"name": "Block LUNs Virtualized", "sub": "Shared Pool For Hypervisors", "shape": "rack_cabinet"}, {"name": "Live VM Storage vMotion", "sub": "Zero Downtime Array Upgrade", "shape": "server_rack"}],
    "ecc_memory_scrubbing": [{"name": "64 Data + 8 Parity SECDED", "sub": "Auto-Fix 1-Bit / Halt 2-Bit Error", "shape": "chip"}, {"name": "Background Hardware Scrub", "sub": "Clears Silent Cosmic Ray Flips", "shape": "blade_server"}, {"name": "Prevents Silent DB Corruption", "sub": "Mandatory For Production Servers", "shape": "database_cluster"}],
    "pdu_ups_power_redundancy": [{"name": "Dual A+B Power Feed Bus", "sub": "Independent Utility + Generator", "shape": "ups_battery"}, {"name": "Rack Dual-Cord PSU Load Share", "sub": "Survive Full PDU Maintenance", "shape": "rack_cabinet"}, {"name": "Online Double-Conversion UPS", "sub": "Zero-ms Transfer On Grid Drop", "shape": "server_rack"}],
    "edge_iot_mqtt_broker": [{"name": "50KB Persistent TLS Sockets", "sub": "Tiny 2-Byte MQTT Publish Header", "shape": "cell_tower"}, {"name": "Topic Wildcard Tree Matching", "sub": "factory/+/temp -> Alert Sink", "shape": "hub"}, {"name": "Retained LWT Offline Status", "sub": "Instant Disconnect Notification", "shape": "radar_dish"}],
    "wasm_wasi_sandbox": [{"name": "Deny-By-Default Capabilities", "sub": "No Filesystem/Net Unless Granted", "shape": "lock"}, {"name": "Sub-Millisecond Cold Instantiate", "sub": "20x Lighter Than Linux Container", "shape": "container"}, {"name": "Safe Untrusted Edge Plugins", "sub": "Runs C/Rust/Go Anywhere", "shape": "cdn_edge"}],
    "virtualization_kvm_qemu": [{"name": "Intel VT-x / AMD-V Guest Mode", "sub": "Hardware Ring Isolation + EPT", "shape": "chip"}, {"name": "VirtIO Paravirtualized Rings", "sub": "Near-Native Net & NVMe Speed", "shape": "ethernet_port"}, {"name": "Multi-Tenant Kernel Isolation", "sub": "Stronger Security Boundary", "shape": "server_rack"}],
    "sr_iov_vf_passthrough": [{"name": "1 Physical NIC -> 64 Virtual VFs", "sub": "PCIe Hardware Switch Split", "shape": "ethernet_port"}, {"name": "VM Bypasses Hypervisor VSwitch", "sub": "Direct Hardware DMA Queue", "shape": "fiber_cable"}, {"name": "Near-Wire Latency In Cloud VMs", "sub": "Zero Soft-Switch CPU Burn", "shape": "gauge_dial"}],
    "numa_node_pinning": [{"name": "Socket 0 Local RAM (70ns)", "sub": "vs Cross-QPI Remote RAM (140ns)", "shape": "chip"}, {"name": "numactl --cpunodebind=0", "sub": "Pin Redis/DB Memory Locally", "shape": "blade_server"}, {"name": "Eliminate NUMA Reclaim Stalls", "sub": "Consistent Tail Performance", "shape": "gauge_dial"}],
    "bmc_ipmi_out_of_band": [{"name": "Independent Management SoC", "sub": "Dedicated Ethernet Runs OS-Off", "shape": "ethernet_port"}, {"name": "Remote KVM Console & Power", "sub": "Fix Kernel Panic Across World", "shape": "blade_server"}, {"name": "Mount Virtual Recovery ISO", "sub": "Zero Physical Datacenter Visit", "shape": "rack_cabinet"}],
    # +10 Network & Zero-Trust Security Protocols
    "bgp_blackhole_filter": [{"name": "Volumetric DDoS Trigger", "sub": "Prefix /32 Exceeds 50Gbps", "shape": "firewall_wall"}, {"name": "BGP RTBH Community 666", "sub": "Upstream Scrubbing Edge Drop", "shape": "router"}, {"name": "Clean Origin Upstream", "sub": "Legitimate SLA Uninterrupted", "shape": "server_rack"}],
    "dnssec_trust_chain": [{"name": "Root DS Digest Trust Anchor", "sub": "Signed . -> .com KSK/ZSK", "shape": "dns_server"}, {"name": "RRSIG Record Signature", "sub": "Cryptographic Zone Integrity", "shape": "lock"}, {"name": "Defeat DNS Cache Poisoning", "sub": "Resolver Validates Full Chain", "shape": "shield"}],
    "wireguard_cryptokey": [{"name": "4K-Line Kernel eBPF Ready", "sub": "Noise Protocol ChaCha20 + Curve25519", "shape": "vpn_tunnel"}, {"name": "Cryptokey Routing Table", "sub": "AllowedIPs == PublicKey Binding", "shape": "router"}, {"name": "Silent Stealth Roaming", "sub": "Zero Handshake Bloat On Switch", "shape": "laptop"}],
    "ipv6_slaac_autoconf": [{"name": "Router Advertisement (RA)", "sub": "Broadcasts /64 Network Prefix", "shape": "router"}, {"name": "SLAAC EUI-64 / Privacy ID", "sub": "Host Self-Assigns Without DHCP", "shape": "ethernet_port"}, {"name": "DAD Duplicate Check", "sub": "Instant Neighbor Solicitation", "shape": "network_switch"}],
    "sdwan_smart_path": [{"name": "Measure MPLS + Broadband", "sub": "Continuous Loss / Jitter Probes", "shape": "radar_dish"}, {"name": "Application-Aware Steer", "sub": "Voice -> Low Jitter; Backup -> Bulk", "shape": "router"}, {"name": "Zero-Touch Branch Provision", "sub": "Central Policy Pushed In Secs", "shape": "cloud"}],
    "haproxy_tls_sni": [{"name": "Peek TLS ClientHello SNI", "sub": "Route Without Decrypting Keys", "shape": "load_balancer"}, {"name": "Zero-Copy Kernel Splice", "sub": "100Gbps TCP Passthrough", "shape": "network_switch"}, {"name": "Active Health Drain", "sub": "Instant Slow-Start Warmup", "shape": "server_rack"}],
    "waf_owasp_ruleset": [{"name": "Edge TLS Terminate + Parse", "sub": "Decode JSON / Form / URI", "shape": "cdn_edge"}, {"name": "OWASP CRS Anomaly Score", "sub": "Blocks SQLi, XSS, SSRF Probes", "shape": "firewall_wall"}, {"name": "Zero-Day Virtual Patching", "sub": "Mitigate CVE Before Code Fix", "shape": "shield"}],
    "dhcp_dora_leases": [{"name": "1. DISCOVER -> 2. OFFER", "sub": "Broadcast Finds Pool Lease IP", "shape": "ethernet_port"}, {"name": "3. REQUEST -> 4. ACK", "sub": "Binds IP + DNS + Gateway TTL", "shape": "network_switch"}, {"name": "50% T1 Lease Renewal", "sub": "Seamless Background Extension", "shape": "server_rack"}],
    "ntp_stratum_clock": [{"name": "Stratum 0 Atomic / GPS", "sub": "Nanosecond Reference Pulse", "shape": "radar_dish"}, {"name": "Stratum 1-2 Fleet Servers", "sub": "Chronyc Compensates Drift", "shape": "hub"}, {"name": "Distributed Lock Safety", "sub": "Avoid Skew Certificate Errors", "shape": "lock"}],
    "ssh_ca_bastion_cert": [{"name": "Ephemeral 15-Min Signed Cert", "sub": "Replaces Static ~/.ssh/authorized_keys", "shape": "lock"}, {"name": "SSO OIDC MFA Issued CA", "sub": "Scoped Principals + ForceCmd", "shape": "terminal_box"}, {"name": "Session Transcript Recorded", "sub": "Zero Orphaned Contractor Keys", "shape": "shield"}],
    # +10 Data Lakehouse & Streaming Compute
    "hudi_mor_cow_storage": [{"name": "Copy-on-Write (Read Opt)", "sub": "Rewrites Parquet For Instant BI", "shape": "warehouse_3d"}, {"name": "Merge-on-Read (Write Opt)", "sub": "Appends Fast Avro Delta Logs", "shape": "data_lake"}, {"name": "Async Compactor Service", "sub": "Minute-Fresh Upsert Lakehouse", "shape": "dag_pipeline"}],
    "polars_lazy_optimizer": [{"name": "LazyFrame Logical Plan", "sub": "Predicate + Projection Pushdown", "shape": "code_cube"}, {"name": "Apache Arrow Zero-Copy RAM", "sub": "Multi-Core Rust Rayon Threads", "shape": "chip"}, {"name": "10x Faster Than Pandas", "sub": "Handles Larger-Than-RAM Files", "shape": "gauge_dial"}],
    "ray_distributed_actors": [{"name": "Stateless Tasks + Stateful Actors", "sub": "Unified Python Compute Graph", "shape": "hub"}, {"name": "Plasma Shared Object Store", "sub": "Zero-Copy ZeroMQ Arrow Ref", "shape": "ssd_nvme"}, {"name": "Distributed GPU Train + Serve", "sub": "Scales Laptop To 1000 Nodes", "shape": "gpu_rack"}],
    "presto_disk_spilling": [{"name": "Memory Pool High Watermark", "sub": "Heavy Sort Exceeds Worker RAM", "shape": "gauge_dial"}, {"name": "Spill Intermediate Buffers", "sub": "Flush Partitioned Runs To NVMe", "shape": "ssd_nvme"}, {"name": "Complete Petabyte Joins", "sub": "Zero Query OOM Abort Errors", "shape": "warehouse_3d"}],
    "bi_semantic_metrics": [{"name": "Single Metric Definition YAML", "sub": "ARR, Churn, GMV Versioned Git", "shape": "schema_table"}, {"name": "Compiled Dynamic SQL", "sub": "Eliminates Conflicting Reports", "shape": "warehouse_3d"}, {"name": "Row-Level Security Enforced", "sub": "BI, Notebooks & API Synced", "shape": "shield"}],
    "debezium_chunk_snap": [{"name": "Signal Chunked Key Ranges", "sub": "Reads 1TB Table Lock-Free", "shape": "database_cluster"}, {"name": "Interleave Snapshot + WAL", "sub": "Buffer Window Deduplication", "shape": "kafka_broker"}, {"name": "Resumable Safe Restarts", "sub": "Zero DB CPU Spike In Prod", "shape": "server_rack"}],
    "pulsar_bookkeeper_tier": [{"name": "Stateless Broker Serving", "sub": "Instant Partition Ownership Swap", "shape": "hub"}, {"name": "Apache BookKeeper Journal", "sub": "Independent IO Ledgers Quorums", "shape": "ssd_nvme"}, {"name": "Auto-Offload Cold -> S3", "sub": "Infinite Topic Retention Low Cost", "shape": "data_lake"}],
    "ch_materialized_view": [{"name": "Insert Trigger On Raw Stream", "sub": "Computes Aggregates Incrementally", "shape": "kafka_broker"}, {"name": "SummingMergeTree Target", "sub": "Stores Tiny Rollup State Only", "shape": "warehouse_3d"}, {"name": "Sub-10ms Realtime Dashboards", "sub": "Avoids Full Billions Scan", "shape": "gauge_dial"}],
    "dq_great_expectations": [{"name": "Expectations Suite Contract", "sub": "Null %, Range, Regex & Volume", "shape": "unit_test_cube"}, {"name": "Pipeline Inline Validation", "sub": "Halt Downstream Load On Corrupt", "shape": "firewall_wall"}, {"name": "Auto-Generated Data Docs", "sub": "Lineage + Freshness SLA Score", "shape": "schema_table"}],
    "openmetadata_lineage": [{"name": "Extract SQL + Airflow DAGs", "sub": "Column-Level Impact Graph", "shape": "dag_pipeline"}, {"name": "PII Sensitivity Tagging", "sub": "Auto-Propagate SSN/Email Mask", "shape": "lock"}, {"name": "Prevent Downstream Breakage", "sub": "Instant Owner Slack Notify", "shape": "hub"}],
    # +10 SDLC, GitOps & Quality Automation
    "ephemeral_pr_env": [{"name": "Open GitHub PR #482", "sub": "Spins Isolated K8s Namespace", "shape": "pr_merge"}, {"name": "Seeded Masked Preview DB", "sub": "Live URL Posted In PR Comment", "shape": "browser_window" if False else "container"}, {"name": "Auto-Destroy On Merge", "sub": "Zero Shared Staging Conflicts", "shape": "ci_runner"}],
    "renovate_dep_bot": [{"name": "Scan Lockfiles Daily", "sub": "Group Minor/Patch Auto-PRs", "shape": "ci_runner"}, {"name": "CVE Security Priority", "sub": "Immediate Patch With Tests", "shape": "shield"}, {"name": "Confidence Badges + AutoMerge", "sub": "Prevents Supply-Chain Rot", "shape": "release_tag_3d"}],
    "sonarqube_code_gate": [{"name": "Cyclomatic & Cognitive Audit", "sub": "Flags Dead Code & Taint Flow", "shape": "code_cube"}, {"name": "PR Coverage Delta >80%", "sub": "Focuses On New Lines Added", "shape": "unit_test_cube"}, {"name": "Fail Quality Gate On Blockers", "sub": "Stops Security Hotspots Early", "shape": "firewall_wall"}],
    "e2e_test_sharding": [{"name": "Matrix 8 Parallel CI Runners", "sub": "Blob Shards Split Playwright", "shape": "ci_runner"}, {"name": "Auto Trace + Video On Retry", "sub": "Zero Blind Flake Debugging", "shape": "radar_dish"}, {"name": "45-Min Suite -> 4 Minutes", "sub": "Merged Single JUnit Report", "shape": "rocket"}],
    "otel_baggage_context": [{"name": "Cross-Process Key/Value Bag", "sub": "Carries tenant_id + canary Flag", "shape": "api_plug_3d"}, {"name": "Propagates Through Kafka/gRPC", "sub": "Auto Enriches Logs & Metrics", "shape": "kafka_broker"}, {"name": "Zero Signature Changes Needed", "sub": "Scoped Tenant Cost Tracking", "shape": "gauge_dial"}],
    "kayenta_canary_eval": [{"name": "Baseline vs Canary Populations", "sub": "Paired Time-Series Metrics", "shape": "gauge_dial"}, {"name": "Mann-Whitney U-Test Judge", "sub": "Scores Latency, 5xx & CPU", "shape": "radar_dish"}, {"name": "Objective 0-100 Gate Pass", "sub": "Automated Safe Rollout Engine", "shape": "rocket"}],
    "rds_blue_green_cut": [{"name": "Logical Replication Clone", "sub": "Upgrade Major PG Version Safely", "shape": "database_cluster"}, {"name": "Wait 0ms Replica Catch-Up", "sub": "Run Read Canary Validations", "shape": "radar_dish"}, {"name": "DNS + Read-Only Fence Switch", "sub": "<5s Cutover With Clean Backout", "shape": "router"}],
    "helm_atomic_rollback": [{"name": "helm upgrade --atomic --wait", "sub": "Monitors Pod Readiness Probes", "shape": "helm" if False else "k8s_pod_mesh"}, {"name": "Fails CrashLoop Within 120s", "sub": "Detects Broken Release Fast", "shape": "firewall_wall"}, {"name": "Instant Revision Restore", "sub": "Zero Broken Half-Deployed YAML", "shape": "release_tag_3d"}],
    "crossplane_xrds_crd": [{"name": "Kubernetes Control Plane Loop", "sub": "Manages RDS/S3 As K8s CRDs", "shape": "k8s_pod_mesh"}, {"name": "Continuous Drift Healing", "sub": "Fixes Console Click Overrides", "shape": "radar_dish"}, {"name": "Self-Service Dev Compositions", "sub": "Enforces Tag & Encryption Policy", "shape": "cloud"}],
    "vault_dynamic_leases": [{"name": "App Authenticates Via JWT", "sub": "Requests Temporary Postgres Role", "shape": "lock"}, {"name": "Vault Creates TTL 1h User", "sub": "Unique Per-Pod Credentials", "shape": "database_cluster"}, {"name": "Auto-Revoked On Lease End", "sub": "Leaked Creds Useless Quickly", "shape": "shield"}],
    # +10 Cloud Managed Services & SRE
    "aws_privatelink_svc": [{"name": "Consumer VPC ENI Endpoint", "sub": "Private 10.x.x.x IP Access Only", "shape": "vpc_subnet_topology" if False else "ethernet_port"}, {"name": "AWS Backbone Hyperplane", "sub": "Zero Public Internet Exposure", "shape": "fiber_cable"}, {"name": "Bypasses Overlapping CIDRs", "sub": "Zero NAT Gateway Egress Fee", "shape": "shield"}],
    "spanner_truetime_gps": [{"name": "Dual GPS + Atomic Clocks", "sub": "Bounds Global Skew Epsilon <7ms", "shape": "radar_dish"}, {"name": "Commit Wait Uncertainty Window", "sub": "External Consistency Globally", "shape": "database_cluster"}, {"name": "Paxos Shards Across Continents", "sub": "Serializable SQL At Any Scale", "shape": "cloud"}],
    "cosmos_five_consist": [{"name": "Strong & Bounded Staleness", "sub": "Financial & Inventory Guarantees", "shape": "lock"}, {"name": "Session Monotonic Prefix", "sub": "Read-Your-Writes Per User", "shape": "router"}, {"name": "Eventual Multi-Write Edge", "sub": "<10ms Global Read Replicas", "shape": "cdn_edge"}],
    "cf_durable_objects": [{"name": "Single-Threaded Edge Actor", "sub": "Unique ID Pinned Worldwide", "shape": "cdn_edge"}, {"name": "Colocated Transactional SQL", "sub": "Atomic Locking Inside Worker", "shape": "ssd_nvme"}, {"name": "WebSockets Hibernation Ready", "sub": "Live Multiplayer Rooms Globally", "shape": "hub"}],
    "s3_oac_cloudfront": [{"name": "Lock S3 Bucket Public=BLOCK", "sub": "Zero Direct S3 URL Bypass", "shape": "lock"}, {"name": "Origin Access Control SigV4", "sub": "Edge CDN Signs Origin Reads", "shape": "cdn_edge"}, {"name": "Fast Edge Cache + KMS Support", "sub": "Encrypted Private Media Assets", "shape": "data_lake"}],
    "eks_pod_identity_iam": [{"name": "Kubelet Agent Token Fetch", "sub": "Binds ServiceAccount -> IAM Role", "shape": "k8s_pod_mesh"}, {"name": "Sub-ms Pod Auth Metadata", "sub": "Scales Without OIDC Bottleneck", "shape": "lock"}, {"name": "Zero Static AccessKeys In Env", "sub": "Clean Multi-Cluster Rotation", "shape": "shield"}],
    "alb_drain_deregister": [{"name": "K8s PreStop Sleep 5s Hook", "sub": "Lets LB Remove IP From Pool", "shape": "load_balancer"}, {"name": "Finish In-Flight Responses", "sub": "Graceful Connection Draining", "shape": "server_rack"}, {"name": "SIGTERM Shutdown Zero 502s", "sub": "Seamless Zero-Error Rollouts", "shape": "rocket"}],
    "s3_presigned_upload": [{"name": "API Grants Signed PUT URL", "sub": "Short 60s TTL + Content Cap", "shape": "api_plug_3d"}, {"name": "Browser Uploads Direct -> S3", "sub": "Bypasses API Server Memory/Net", "shape": "data_lake"}, {"name": "Event Notification Triggers Job", "sub": "Scales Multi-GB Uploads Easily", "shape": "kafka_broker"}],
    "sqs_fifo_msggroup": [{"name": "MessageGroupId Hash Partition", "sub": "Strict FIFO Within Each Tenant", "shape": "kafka_broker"}, {"name": "ContentBasedDeduplication", "sub": "5-Min Window Drops Duplicates", "shape": "shield"}, {"name": "Parallel High-Throughput Mode", "sub": "Scales Across Thousands Groups", "shape": "server_rack"}],
    "redis_cluster_16k": [{"name": "16,384 CRC16 Hash Slots", "sub": "Distributed Across Master Nodes", "shape": "hub", "icon": "redis"}, {"name": "Hash Tags {order_123}:meta", "sub": "Co-Locate Keys On Same Slot", "shape": "ssd_nvme"}, {"name": "Sentinel/Gossip Auto Failover", "sub": "Replica Promoted Sub-Second", "shape": "server_rack"}],
    # +10 Kernel, CPU & Storage Internals
    "l1_set_associative": [{"name": "32KB 8-Way L1d Cache", "sub": "4-Cycle Ultra-Fast Core Hit", "shape": "chip"}, {"name": "Index Bits Map To Cache Sets", "sub": "Power-of-2 Stride Thrashing", "shape": "blade_server"}, {"name": "Hardware Prefetcher Pattern", "sub": "Contiguous Arrays 10x Faster", "shape": "gauge_dial"}],
    "tlb_shootdown_core": [{"name": "munmap() Changes Page Table", "sub": "Other Cores Hold Stale PTEs", "shape": "chip"}, {"name": "Kernel Sends Inter-Processor IPI", "sub": "Halts Sibling Cores To Flush", "shape": "blade_server"}, {"name": "Batch Free + HugePages (2MB)", "sub": "Cuts TLB Overhead By 95%", "shape": "ssd_nvme"}],
    "io_uring_shared_ring": [{"name": "Submission & Completion Rings", "sub": "Mmap Shared Between User/Kernel", "shape": "ethernet_port"}, {"name": "Zero Syscall Submit Batch", "sub": "SQPOLL Polling Eliminates Traps", "shape": "chip"}, {"name": "True Async NVMe & Socket I/O", "sub": "1M+ IOPS With Minimal CPU", "shape": "ssd_nvme"}],
    "linux_page_cache_wb": [{"name": "Buffered write() -> Dirty Page", "sub": "Instant Nanosecond RAM Copy", "shape": "chip"}, {"name": "Background kworker Flush", "sub": "Coalesces Sequential Disk I/O", "shape": "ssd_nvme"}, {"name": "fsync() Guarantees Power Safety", "sub": "Forces Controller Flash Flush", "shape": "database_cluster"}],
    "cgroup_v2_psi_stall": [{"name": "Pressure Stall Information", "sub": "Exact ms Lost Waiting CPU/IO/Mem", "shape": "gauge_dial"}, {"name": "Unified Single Hierarchy Tree", "sub": "Fair Page Cache Writeback Limit", "shape": "k8s_pod_mesh"}, {"name": "Early OOMD Proactive Evict", "sub": "Prevents Full Node Thrash Freeze", "shape": "server_rack"}],
    "ext4_journal_modes": [{"name": "JBD2 Write-Ahead Journal", "sub": "Records Metadata Intent Before Write", "shape": "ssd_nvme"}, {"name": "data=ordered Crash Consistency", "sub": "Writes File Blocks Before Commit", "shape": "database_cluster"}, {"name": "Fast Mount Recovery After Loss", "sub": "Replays Seconds Instead fsck", "shape": "shield"}],
    "zfs_arc_cow_pool": [{"name": "Copy-on-Write Merkle Checksum", "sub": "Self-Heals Silent Bit-Rot Mirror", "shape": "lock"}, {"name": "Adaptive Replacement Cache", "sub": "Tracks Recency + Frequency Lists", "shape": "chip"}, {"name": "Instant Zero-Cost Snapshots", "sub": "Clones Petabytes In Milliseconds", "shape": "data_lake"}],
    "usb4_pcie_tunneling": [{"name": "Protocol Router Caps Negotiate", "sub": "Encapsulates PCIe + DP Alt Mode", "shape": "fiber_cable"}, {"name": "Time-Division Bandwidth Share", "sub": "80Gbps Asymmetric Boost 120G", "shape": "ethernet_port"}, {"name": "Single Cable NVMe + Dual 6K", "sub": "Unified Hardware DMA Fabric", "shape": "laptop"}],
    "avx_gather_scatter": [{"name": "Vector Register ZMM0..31", "sub": "Loads Non-Contiguous Pointers", "shape": "chip"}, {"name": "Mask Predicate Registers K1..K7", "sub": "Zero Branch Divergence Lanes", "shape": "code_cube"}, {"name": "Parallel Sparse Matrix Ops", "sub": "Accelerates Analytics & Sim", "shape": "gauge_dial"}],
    "cpu_tage_predictor": [{"name": "Geometric History Tables", "sub": "Global Branch Patterns To 1000b", "shape": "chip"}, {"name": "Tagged Entry Confidence Count", "sub": ">99% Speculative Fetch Accuracy", "shape": "radar_dish"}, {"name": "Zero Pipeline Flush Penalty", "sub": "Eliminates 15-Cycle Mispredict", "shape": "gauge_dial"}],
}

_ACCENT = ("cyan", "purple", "emerald", "amber", "rose")
SX0, SY0, SX1, SY1 = 64, 328, 1016, 1406
SW, SH = SX1 - SX0, SY1 - SY0


def _render_horizontal_pipeline(
    stage: Any,
    items: List[Dict[str, Any]],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
    default_shape: str = "box",
) -> None:
    """Shared crisp animated left-to-right or zigzag IT/Data/CI-CD stage pipeline."""
    _get_font = helpers["_get_font"]
    _draw_wrapped = helpers["_draw_wrapped_text"]
    _with_alpha = helpers["_with_alpha"]
    _spring_gate = helpers["_spring_gate"]
    _ease = helpers["_ease_out_cubic"]
    _res_col = helpers["resolve_world_color"]
    _bezier = helpers["_draw_bezier_comet"]
    _draw_vis = helpers["_draw_node_visual"]

    n = min(5, len(items))
    if n <= 0:
        return
    rh = min(232, (SH - (140 if n <= 4 else 36)) // n)
    prev_out = None
    prev_edge = ""
    for i, it in enumerate(items[:5]):
        if isinstance(it, str):
            it = {"name": it}
        gt = _ease(_spring_gate(progress, i, n, 0.22))
        if gt <= 0.03:
            continue
        col = _res_col(world, it.get("color"), _ACCENT[i % len(_ACCENT)])
        cy = SY0 + 78 + i * rh
        is_left = (i % 2 == 0)
        scx = 185 if is_left else 895
        cb_x0 = 285 if is_left else 84
        cb_x1 = 996 if is_left else 795
        active = (int(progress * n) == i)
        if prev_out is not None:
            in_x = 460 if is_left else 620
            _bezier(stage, prev_out, (in_x, cy - 58), col, reveal=gt, progress=progress, phase=i * 0.2, label=prev_edge, world=world)
        stage.draw_glass_card((cb_x0, cy - 54, cb_x1, cy + 56), radius=20, accent_col=col, alpha_mul=gt, active=active)
        _draw_vis(stage, scx, cy - 16, 44, 20, 30, col, gt, shape=it.get("shape", default_shape), icon=it.get("icon", ""), label=it.get("name", ""), active=active, progress=progress, phase=i * 0.5)
        stage.draw.line((scx + (52 if is_left else -52), cy, cb_x0 if is_left else cb_x1, cy), fill=_with_alpha(col, gt), width=3)
        sub_txt = str(it.get("sub") or it.get("desc") or "").strip()
        _draw_wrapped(stage.draw, (cb_x0 + 22, cy - 36), str(it.get("name") or it.get("title") or ""), _get_font(25, bold=True), _with_alpha(world["text"], gt), cb_x1 - cb_x0 - 44, max_lines=1 if sub_txt else 2)
        if sub_txt:
            _draw_wrapped(stage.draw, (cb_x0 + 22, cy + 6), sub_txt, _get_font(20), _with_alpha(world["muted"], gt), cb_x1 - cb_x0 - 44, max_lines=2)
        prev_out = (460 if is_left else 620, cy + 56)
        prev_edge = str(it.get("edge", ""))
    if n <= 4:
        g0 = _ease(min(1.0, progress / 0.25))
        stage.draw_glass_card((80, SY1 - 122, 1000, SY1 - 22), radius=20, accent_col=world["emerald"], alpha_mul=g0, active=True)
        _draw_wrapped(stage.draw, (112, SY1 - 88), "Continuous Real-Time Pipeline • Zero Production Locks", _get_font(24, bold=True), _with_alpha(world["emerald"], g0), 856, align="center", max_lines=1)


def _render_tiered_zones(
    stage: Any,
    zones: List[Dict[str, Any]],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> None:
    """Shared multi-zone container diagram for Subnets, DMZ, Medallion Lakehouse, Testing Pyramid & OSI Layers."""
    _get_font = helpers["_get_font"]
    _draw_wrapped = helpers["_draw_wrapped_text"]
    _with_alpha = helpers["_with_alpha"]
    _spring_gate = helpers["_spring_gate"]
    _ease = helpers["_ease_out_cubic"]
    _res_col = helpers["resolve_world_color"]
    _draw_vis = helpers["_draw_node_visual"]

    n = min(7, len(zones))
    if n <= 0:
        return
    rh = (SH - 40) // n
    for i, zn in enumerate(zones[:7]):
        if isinstance(zn, str):
            zn = {"name": zn}
        gt = _ease(_spring_gate(progress, i, n, 0.20))
        if gt <= 0.03:
            continue
        col = _res_col(world, zn.get("color"), _ACCENT[i % len(_ACCENT)])
        y = SY0 + 20 + i * rh
        h = rh - 14
        active = (int(progress * n) == i)
        stage.draw_glass_card((80, y, 1000, y + h), radius=18, accent_col=col, alpha_mul=gt, active=active)
        _draw_vis(stage, 142, y + h // 2 - 12, 30, 14, 20, col, gt, shape=zn.get("shape", "box"), icon=zn.get("icon", ""), label=zn.get("name", ""), active=active, progress=progress)
        stage.draw_pill(248, y + h // 2, str(zn.get("tag") or f"L{n - i}")[:10], (*col[:3], 42), col, border_col=col, font=_get_font(18, bold=True), alpha_mul=gt)
        _draw_wrapped(stage.draw, (318, y + max(10, h // 2 - 26)), str(zn.get("name") or zn.get("title") or ""), _get_font(24 if n <= 5 else 21, bold=True), _with_alpha(world["text"], gt), 430, max_lines=1)
        if zn.get("sub") or zn.get("proto"):
            _draw_wrapped(stage.draw, (755, y + max(12, h // 2 - 18)), str(zn.get("sub") or zn.get("proto")), _get_font(19, mono=True), _with_alpha(col, gt), 228, align="right", max_lines=2)


def render_it_sdlc_layout(
    stage: Any,
    layout: str,
    data: Dict[str, Any],
    progress: float,
    world: Dict[str, Any],
    helpers: Dict[str, Any],
) -> bool:
    """Renders all 35 dedicated Networking, Hardware, Data Engineering & SDLC Studio Layouts."""
    l = str(layout or "").lower().strip()
    if l not in IT_SDLC_35_LAYOUTS:
        return False

    _get_font = helpers["_get_font"]
    _draw_wrapped = helpers["_draw_wrapped_text"]
    _with_alpha = helpers["_with_alpha"]
    _spring_gate = helpers["_spring_gate"]
    _ease = helpers["_ease_out_cubic"]
    _res_col = helpers["resolve_world_color"]
    _bezier = helpers["_draw_bezier_comet"]
    _draw_vis = helpers["_draw_node_visual"]
    d = data or {}
    g0 = _ease(min(1.0, progress / 0.20))

    # --- A. TIERED ZONES / LAYERS (OSI 7, Firewall DMZ, VPC Subnets, Medallion, Tech Stack) ---
    if l == "osi_7_layers":
        default_osi = [
            {"tag": "L7", "name": "Application", "proto": "HTTP / DNS / gRPC", "shape": "cloud", "icon": "globe"},
            {"tag": "L6", "name": "Presentation", "proto": "TLS / JSON / UTF-8", "shape": "lock"},
            {"tag": "L5", "name": "Session", "proto": "RPC / Sockets", "shape": "bridge"},
            {"tag": "L4", "name": "Transport", "proto": "TCP / UDP Ports", "shape": "router"},
            {"tag": "L3", "name": "Network", "proto": "IP Packets / BGP", "shape": "network_switch"},
            {"tag": "L2", "name": "Data Link", "proto": "MAC Frames / VLAN", "shape": "hub"},
            {"tag": "L1", "name": "Physical", "proto": "Fiber / Cat6 Signal", "shape": "fiber_cable"},
        ]
        _render_tiered_zones(stage, list(d.get("layers") or default_osi), progress, world, helpers)
        return True

    if l == "medallion_lakehouse":
        med = list(d.get("tiers") or d.get("layers") or [
            {"tag": "BRONZE", "name": "Raw Ingestion Lake", "sub": "Kafka + Debezium JSON/Parquet", "shape": "data_lake", "icon": "kafka", "color": "amber"},
            {"tag": "SILVER", "name": "Validated & Conformed", "sub": "Spark / dbt Cleanse + Dedup", "shape": "spark_engine", "icon": "spark", "color": "cyan"},
            {"tag": "GOLD", "name": "Business Aggregates", "sub": "Star Schema BI & ML Features", "shape": "warehouse_3d", "icon": "dbt", "color": "emerald"},
        ])
        _render_tiered_zones(stage, med, progress, world, helpers)
        return True

    if l in ("firewall_dmz_zones", "vpc_subnet_topology", "tech_stack_layers", "zero_trust_mesh", "test_pyramid_qa"):
        defaults = {
            "firewall_dmz_zones": [
                {"tag": "WAN", "name": "Untrusted Internet", "sub": "DDoS / Bot Traffic", "shape": "globe", "color": "rose"},
                {"tag": "EDGE", "name": "Perimeter Firewall", "sub": "WAF + L7 Packet Filter", "shape": "firewall_wall", "color": "amber"},
                {"tag": "DMZ", "name": "Public DMZ Zone", "sub": "Reverse Proxy / Bastion", "shape": "router", "icon": "nginx", "color": "purple"},
                {"tag": "LAN", "name": "Trusted Private Subnet", "sub": "Core DB + Internal API", "shape": "server_rack", "icon": "postgres", "color": "emerald"},
            ],
            "vpc_subnet_topology": [
                {"tag": "IGW", "name": "Internet Gateway", "sub": "Elastic IP / DNS", "shape": "router", "icon": "aws", "color": "cyan"},
                {"tag": "PUBLIC", "name": "Public Subnet (ALB + NAT)", "sub": "10.0.1.0/24", "shape": "load_balancer", "color": "purple"},
                {"tag": "PRIVATE", "name": "Private App Subnet (EKS)", "sub": "10.0.2.0/24", "shape": "k8s_pod_mesh", "icon": "aws_eks", "color": "emerald"},
                {"tag": "DATA", "name": "Isolated DB Subnet (RDS)", "sub": "10.0.3.0/24 No Public IP", "shape": "database_cluster", "icon": "aws_rds", "color": "amber"},
            ],
            "tech_stack_layers": [
                {"tag": "UI", "name": "Client Tier", "sub": "React / Mobile / Desktop", "shape": "laptop", "icon": "react", "color": "cyan"},
                {"tag": "API", "name": "Gateway & Auth", "sub": "FastAPI / GraphQL / JWT", "shape": "load_balancer", "icon": "fastapi", "color": "purple"},
                {"tag": "CACHE", "name": "In-Memory Cache & Bus", "sub": "Redis + Kafka Streams", "shape": "kafka_broker", "icon": "redis", "color": "amber"},
                {"tag": "STORE", "name": "Database & Lakehouse", "sub": "PostgreSQL + S3 Parquet", "shape": "warehouse_3d", "icon": "postgres", "color": "emerald"},
            ],
            "zero_trust_mesh": [
                {"tag": "VERIFY", "name": "Device & Identity Posture", "sub": "SSO + MFA + Hardware Key", "shape": "laptop", "icon": "lock", "color": "cyan"},
                {"tag": "POLICY", "name": "Zero-Trust PDP Engine", "sub": "Least Privilege RBAC", "shape": "shield", "icon": "shield", "color": "purple"},
                {"tag": "MESH", "name": "mTLS Micro-Segmentation", "sub": "East-West Encrypted Tunnels", "shape": "network_switch", "color": "emerald"},
            ],
            "test_pyramid_qa": [
                {"tag": "10%", "name": "E2E Browser Tests", "sub": "Playwright / Cypress", "shape": "browser", "icon": "playwright", "color": "rose"},
                {"tag": "25%", "name": "Integration & API Tests", "sub": "Contract + DB Testcontainers", "shape": "api_plug_3d", "icon": "postman", "color": "amber"},
                {"tag": "65%", "name": "Fast Unit Tests", "sub": "Isolated Pure Functions (<10ms)", "shape": "unit_test_cube", "icon": "jest", "color": "emerald"},
            ],
        }
        _render_tiered_zones(stage, list(d.get("zones") or d.get("layers") or defaults[l]), progress, world, helpers)
        return True

    # --- B. MULTI-STAGE IT / DATA ENGINEERING / CI-CD PIPELINES ---
    if l in ("etl_elt_pipeline", "cicd_pipeline_stages", "cdc_debezium_flow", "dns_resolution_flow", "cdn_edge_routing", "vpn_tunnel_mesh", "data_quality_lineage", "devsecops_shield_gate", "event_driven_cqrs"):
        p_defaults = {
            "etl_elt_pipeline": [
                {"name": "OLTP & API Sources", "sub": "Postgres / SaaS Webhooks", "shape": "database_cluster", "icon": "postgres", "edge": "Extract"},
                {"name": "Cloud Object Staging", "sub": "Parquet on S3 / GCS", "shape": "data_lake", "icon": "aws_s3", "edge": "Load"},
                {"name": "dbt / Spark Transform", "sub": "SQL Models & Joins", "shape": "spark_engine", "icon": "dbt", "edge": "Transform"},
                {"name": "Cloud Data Warehouse", "sub": "BI & ML Ready Tables", "shape": "warehouse_3d", "icon": "snowflake", "edge": "Serve"},
            ],
            "cicd_pipeline_stages": [
                {"name": "Git Push & PR", "sub": "Feature Branch Trigger", "shape": "pr_merge", "icon": "git", "edge": "Webhook"},
                {"name": "Lint & Unit Tests", "sub": "Fast CI Matrix Check", "shape": "unit_test_cube", "icon": "sonarqube", "edge": "Pass"},
                {"name": "Docker Image Build", "sub": "Multi-stage + SBOM Sign", "shape": "container", "icon": "docker", "edge": "Push"},
                {"name": "ArgoCD K8s Rollout", "sub": "Zero-Downtime Sync", "shape": "k8s_pod_mesh", "icon": "argocd", "edge": "Deploy"},
            ],
            "cdc_debezium_flow": [
                {"name": "Postgres Write-Ahead Log", "sub": "Row-level WAL Events", "shape": "database_cluster", "icon": "postgres", "edge": "Stream WAL"},
                {"name": "Debezium CDC Connect", "sub": "Zero Polling Impact", "shape": "data_pipe", "edge": "Publish"},
                {"name": "Kafka Topic Partitions", "sub": "Ordered Event Ledger", "shape": "kafka_broker", "icon": "kafka", "edge": "Sink"},
                {"name": "ClickHouse Analytics", "sub": "Sub-second OLAP Query", "shape": "warehouse_3d", "icon": "clickhouse", "edge": "Query"},
            ],
            "dns_resolution_flow": [
                {"name": "Client Browser Cache", "sub": "Check Local hosts/TTL", "shape": "laptop", "icon": "laptop", "edge": "Query"},
                {"name": "Recursive ISP Resolver", "sub": "1.1.1.1 / 8.8.8.8", "shape": "dns_server", "icon": "cloudflare", "edge": "Root -> TLD"},
                {"name": "Authoritative Nameserver", "sub": "Returns A / AAAA IP", "shape": "server_rack", "edge": "34.120.x.x"},
            ],
            "cdn_edge_routing": [
                {"name": "Mobile & Desktop Users", "sub": "Global Anycast Entry", "shape": "mobile", "icon": "mobile", "edge": "HTTP/3"},
                {"name": "Edge PoP Cache (5ms)", "sub": "TLS Term + Asset Hit", "shape": "cdn_edge", "icon": "cloudflare", "edge": "Miss Only"},
                {"name": "Origin Shield Cluster", "sub": "Auto-Scaled Backends", "shape": "server_rack", "icon": "nginx", "edge": "Origin"},
            ],
            "vpn_tunnel_mesh": [
                {"name": "Remote Engineer Laptop", "sub": "WireGuard / IPSec Client", "shape": "laptop", "icon": "laptop", "edge": "Encrypt"},
                {"name": "Encrypted VPN Tunnel", "sub": "AES-256 Virtual Pipe", "shape": "vpn_tunnel", "icon": "vpn", "edge": "Auth"},
                {"name": "Corporate Edge Router", "sub": "Internal Private Subnets", "shape": "router", "icon": "router", "edge": "Access"},
            ],
            "data_quality_lineage": [
                {"name": "Raw Event Stream", "sub": "Schema Registry Gate", "shape": "data_pipe", "edge": "Validate"},
                {"name": "Freshness & Null Check", "sub": "dbt / Great Expectations", "shape": "unit_test_cube", "icon": "dbt", "edge": "Quarantine"},
                {"name": "PII Masking & Governance", "sub": "Column-Level Policy", "shape": "lock", "icon": "lock", "edge": "Certify"},
            ],
            "devsecops_shield_gate": [
                {"name": "SAST & Secrets Scan", "sub": "Pre-Commit & PR Block", "shape": "code_cube", "icon": "git", "edge": "Scan"},
                {"name": "SCA Container Audit", "sub": "CVE Vulnerability Gate", "shape": "shield_zero", "icon": "docker", "edge": "Sign"},
                {"name": "Runtime WAF & SIEM", "sub": "Live Anomaly Detection", "shape": "firewall_wall", "icon": "shield", "edge": "Protect"},
            ],
            "event_driven_cqrs": [
                {"name": "Command API (Writes)", "sub": "Validate Business Rules", "shape": "api_plug_3d", "edge": "Append"},
                {"name": "Immutable Event Store", "sub": "Kafka Event Log", "shape": "kafka_broker", "icon": "kafka", "edge": "Project"},
                {"name": "Read Materialized View", "sub": "Redis/Elastic Fast Read", "shape": "warehouse_3d", "icon": "redis", "edge": "Query"},
            ],
        }
        items = list(d.get("stages") or d.get("nodes") or d.get("steps") or p_defaults[l])
        _render_horizontal_pipeline(stage, items, progress, world, helpers)
        return True

    # --- C. CIRCULAR SDLC WHEEL / HARDWARE RACK / CLIENT-SERVER CLUSTER ---
    if l == "sdlc_cycle_wheel":
        phases = list(d.get("phases") or [
            {"name": "Plan", "shape": "kanban_card"}, {"name": "Design", "shape": "schema_table"},
            {"name": "Code", "shape": "code_cube", "icon": "vscode"}, {"name": "Build", "shape": "container", "icon": "docker"},
            {"name": "Test", "shape": "unit_test_cube"}, {"name": "Deploy", "shape": "rocket"},
            {"name": "Operate", "shape": "k8s_pod_mesh", "icon": "kubernetes"}, {"name": "Monitor", "shape": "gauge_dial", "icon": "grafana"},
        ])[:8]
        cx, cy, rad = 540, 885, 345
        stage.draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=_with_alpha((*world["cyan"][:3], 70), g0), width=5)
        draw_vector_glyph(stage, cx, cy, "sdlc_cycle", 56, world["cyan"], g0, with_badge=True)
        stage.draw_pill(cx, cy + 82, str(d.get("center") or "SDLC CYCLE"), world["card_alt"], world["text"], border_col=world["cyan"], font=_get_font(22, bold=True), alpha_mul=g0)
        n = len(phases)
        for i, ph in enumerate(phases):
            if isinstance(ph, str):
                ph = {"name": ph}
            gt = _ease(_spring_gate(progress, i, n, 0.22))
            if gt <= 0.03:
                continue
            ang = -math.pi / 2 + i * (2 * math.pi / n)
            px, py = int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))
            col = _res_col(world, ph.get("color"), _ACCENT[i % len(_ACCENT)])
            active = (int(progress * n) == i)
            _draw_vis(stage, px, py - 18, 34, 15, 22, col, gt, shape=ph.get("shape", "box"), icon=ph.get("icon", ""), active=active, progress=progress)
            stage.draw_pill(px, py + 44, f"{i+1}. {ph.get('name','')[:12]}", world["card_alt"], world["text"], border_col=col, font=_get_font(19, bold=True), alpha_mul=gt)
        return True

    if l == "hardware_rack_diagram":
        units = list(d.get("units") or [
            {"u": "U42", "name": "Perimeter Firewall", "sub": "Dual ISP Failover + IDS", "shape": "firewall_wall", "color": "rose"},
            {"u": "U38", "name": "Core L3 Switch (48-Port)", "sub": "100GbE SFP+ Trunk Fabric", "shape": "network_switch", "color": "cyan"},
            {"u": "U34", "name": "Edge WiFi Router & VPN", "sub": "WireGuard Site-to-Site", "shape": "router", "color": "purple"},
            {"u": "U24", "name": "Blade Compute Cluster", "sub": "8x EPYC Nodes + NVMe", "shape": "server_rack", "color": "emerald"},
            {"u": "U10", "name": "SAN Storage & UPS Power", "sub": "RAID-10 + Redundant PSU", "shape": "ups_battery", "color": "amber"},
        ])[:5]
        stage.draw_glass_card((120, SY0 + 20, 960, SY1 - 24), radius=24, accent_col=world["cyan"], alpha_mul=g0, layered=True)
        for i, un in enumerate(units):
            if isinstance(un, str):
                un = {"name": un, "u": f"U{i+1}"}
            gt = _ease(_spring_gate(progress, i, len(units), 0.22))
            if gt <= 0.03:
                continue
            y = SY0 + 50 + i * 195
            col = _res_col(world, un.get("color"), _ACCENT[i % len(_ACCENT)])
            stage.draw_glass_card((155, y, 925, y + 165), radius=18, accent_col=col, alpha_mul=gt, active=(int(progress * len(units)) == i))
            _draw_vis(stage, 265, y + 66, 56, 24, 34, col, gt, shape=un.get("shape", "server_rack"), active=(int(progress * len(units)) == i), progress=progress)
            stage.draw_pill(380, y + 48, str(un.get("u") or f"U{i+1}"), (*col[:3], 42), col, border_col=col, font=_get_font(19, bold=True, mono=True), alpha_mul=gt)
            _draw_wrapped(stage.draw, (445, y + 32), str(un.get("name") or ""), _get_font(26, bold=True), _with_alpha(world["text"], gt), 450, max_lines=1)
            if un.get("sub"):
                _draw_wrapped(stage.draw, (445, y + 82), str(un["sub"]), _get_font(21), _with_alpha(world["muted"], gt), 450, max_lines=2)
        return True

    if l == "client_server_cluster":
        # Top row: Laptop, Desktop, Mobile Clients -> Mid: Router + Switch/Hub -> Bot: Server Cluster + DB
        clients = list(d.get("clients") or [{"name": "Laptop", "shape": "laptop"}, {"name": "Desktop", "shape": "desktop"}, {"name": "Mobile", "shape": "mobile"}])[:3]
        net_nodes = list(d.get("network") or [{"name": "Router", "shape": "router"}, {"name": "Core Switch", "shape": "network_switch"}, {"name": "Network Hub", "shape": "hub"}])[:3]
        backends = list(d.get("servers") or [{"name": "App Cluster", "shape": "server_rack"}, {"name": "Primary DB", "shape": "database_cluster"}])[:2]

        for i, cl in enumerate(clients):
            cx = 220 + i * 320
            col = _res_col(world, _ACCENT[i % len(_ACCENT)])
            _draw_vis(stage, cx, SY0 + 95, 52, 22, 34, col, g0, shape=cl.get("shape", "laptop"), active=True, progress=progress)
            stage.draw_pill(cx, SY0 + 185, cl["name"][:14], world["card_alt"], world["text"], border_col=col, font=_get_font(20, bold=True), alpha_mul=g0)
            _bezier(stage, (cx, SY0 + 210), (220 + i * 320, SY0 + 380), col, reveal=g0, progress=progress, world=world)

        g1 = _ease(min(1.0, max(0.0, (progress - 0.18) / 0.25)))
        for i, nw in enumerate(net_nodes):
            cx = 220 + i * 320
            col = world["purple"] if i == 1 else world["cyan"]
            _draw_vis(stage, cx, SY0 + 445, 54, 24, 34, col, g1, shape=nw.get("shape", "router"), active=True, progress=progress)
            stage.draw_pill(cx, SY0 + 535, nw["name"][:16], world["card_alt"], world["text"], border_col=col, font=_get_font(20, bold=True), alpha_mul=g1)
            _bezier(stage, (cx, SY0 + 560), (350 if i < 2 else 730, SY0 + 730), col, reveal=g1, progress=progress, world=world)

        g2 = _ease(min(1.0, max(0.0, (progress - 0.36) / 0.28)))
        for i, bk in enumerate(backends):
            cx = 350 + i * 380
            col = world["emerald"] if i == 0 else world["amber"]
            stage.draw_glass_card((cx - 160, SY0 + 725, cx + 160, SY0 + 965), radius=24, accent_col=col, alpha_mul=g2, active=True)
            _draw_vis(stage, cx, SY0 + 815, 58, 26, 40, col, g2, shape=bk.get("shape", "server_rack"), active=True, progress=progress)
            stage.draw_pill(cx, SY0 + 925, bk["name"][:18], world["card_alt"], world["text"], border_col=col, font=_get_font(22, bold=True), alpha_mul=g2)
        return True

    # --- D. REMAINING SPECIALIZED TOPOLOGIES & GRIDS ---
    # (`tcp_ip_handshake`, `vlan_switch_ports`, `bgp_routing_table`, `lambda_kappa_arch`,
    #  `kafka_streaming_topology`, `star_snowflake_schema`, `data_warehouse_cluster`, `spark_dag_stages`,
    #  `feature_store_ml`, `agile_sprint_board`, `gitflow_release_lanes`, `blue_green_canary`,
    #  `microservices_mesh`, `observability_pillars`, `cloud_services_map`, `language_ecosystem`)
    cards = list(d.get("items") or d.get("services") or d.get("pillars") or d.get("lanes") or [])
    if not cards:
        preset_cards = {
            "tcp_ip_handshake": [{"name": "1. SYN (Seq=x)", "sub": "Client initiates connection", "shape": "laptop"}, {"name": "2. SYN-ACK (Ack=x+1)", "sub": "Server acknowledges + allocates socket", "shape": "server_rack"}, {"name": "3. ACK (Ack=y+1)", "sub": "Full-Duplex TCP Channel Established", "shape": "router"}],
            "vlan_switch_ports": [{"name": "VLAN 10: Engineering", "sub": "Ports 1-16 (Subnet 10.10.0.0/24)", "shape": "network_switch"}, {"name": "VLAN 20: Finance", "sub": "Ports 17-32 (Isolated PCI)", "shape": "lock"}, {"name": "VLAN 30: Corporate WiFi", "sub": "Ports 33-48 + 802.1Q Trunk", "shape": "hub"}],
            "bgp_routing_table": [{"name": "AS 64512 (Origin Edge)", "sub": "Announces Prefix 198.51.100.0/24", "shape": "router"}, {"name": "AS 3356 (Tier-1 Transit)", "sub": "Shortest AS-Path Selected", "shape": "hub"}, {"name": "AS 15169 (Cloud Target)", "sub": "BGP Session Established", "shape": "cloud"}],
            "lambda_kappa_arch": [{"name": "Batch Layer (S3 + Spark)", "sub": "Full Historical Accuracy", "shape": "data_lake", "icon": "spark"}, {"name": "Speed Layer (Kafka + Flink)", "sub": "Sub-Second Real-Time Views", "shape": "kafka_broker", "icon": "kafka"}, {"name": "Serving Query Layer", "sub": "Merged Batch + Real-time", "shape": "warehouse_3d"}],
            "kafka_streaming_topology": [{"name": "Producers (Services)", "sub": "Key-Hashed Events", "shape": "api_plug_3d"}, {"name": "Topic Partitions P0 / P1 / P2", "sub": "Append-Only Replication", "shape": "kafka_broker", "icon": "kafka"}, {"name": "Consumer Group Workers", "sub": "Parallel Offset Reads", "shape": "worker" if False else "gear"}],
            "star_snowflake_schema": [{"name": "FACT_ORDERS (Central)", "sub": "order_id, user_fk, date_fk, amount", "shape": "warehouse_3d"}, {"name": "DIM_USERS", "sub": "Segment, Plan, Region", "shape": "hexagon"}, {"name": "DIM_TIME & PRODUCTS", "sub": "SKU, Category, Fiscal Qtr", "shape": "schema_table"}],
            "data_warehouse_cluster": [{"name": "Virtual Compute (BI XS)", "sub": "Auto-Resumes in 1s", "shape": "chip"}, {"name": "ML Transform (XL Cluster)", "sub": "Isolated Heavy Joins", "shape": "gpu_rack"}, {"name": "Shared Columnar Storage", "sub": "Compressed Micro-Partitions", "shape": "data_lake", "icon": "snowflake"}],
            "spark_dag_stages": [{"name": "Spark Driver Plan", "sub": "Catalyst Logical -> Physical DAG", "shape": "dag_nodes", "icon": "spark"}, {"name": "Stage 1: Map & Filter", "sub": "Parallel Partition Reads", "shape": "container"}, {"name": "Stage 2: Shuffle & Reduce", "sub": "Write Partitioned Parquet", "shape": "data_lake"}],
            "feature_store_ml": [{"name": "Batch & Stream Pipelines", "sub": "Spark + Flink Feature Compute", "shape": "spark_engine"}, {"name": "Offline Training Store", "sub": "Historical Time-Travel Parquet", "shape": "data_lake"}, {"name": "Online Feature Store", "sub": "Redis <2ms Inference Lookup", "shape": "database_cluster", "icon": "redis"}],
            "agile_sprint_board": [{"name": "Backlog & Spec", "sub": "Prioritized User Stories", "shape": "kanban_card"}, {"name": "In Dev & Code Review", "sub": "PR Checks & Pair Review", "shape": "pr_merge"}, {"name": "QA Verified & Released", "sub": "Production Sprint Ship", "shape": "release_tag_3d"}],
            "gitflow_release_lanes": [{"name": "feature/* -> develop", "sub": "Continuous Integration Merge", "shape": "pr_merge", "icon": "git"}, {"name": "release/v2.4", "sub": "QA Stabilization & Hotfixes", "shape": "ci_runner"}, {"name": "main (Tagged Prod)", "sub": "Immutable Signed Artifact", "shape": "release_tag_3d"}],
            "blue_green_canary": [{"name": "Load Balancer Router", "sub": "Weighted Traffic Split", "shape": "load_balancer"}, {"name": "Blue Cluster (v1.9 - 90%)", "sub": "Proven Production Pool", "shape": "server_rack"}, {"name": "Canary / Green (v2.0 - 10%)", "sub": "Auto-Rollback Guard", "shape": "rocket"}],
            "microservices_mesh": [{"name": "Envoy Service Proxy", "sub": "mTLS + Circuit Breaking", "shape": "network_switch", "icon": "envoy"}, {"name": "Orders & Billing Pods", "sub": "Independent Scale & DB", "shape": "k8s_pod_mesh", "icon": "kubernetes"}, {"name": "Distributed Trace Span", "sub": "OpenTelemetry Correlation", "shape": "radar_dish"}],
            "observability_pillars": [{"name": "Metrics (Prometheus)", "sub": "Time-Series Counters & Alerts", "shape": "gauge_dial", "icon": "prometheus"}, {"name": "Logs (Structured JSON)", "sub": "Centralized Elastic/Loki", "shape": "terminal_box"}, {"name": "Traces (OpenTelemetry)", "sub": "End-to-End Request Spans", "shape": "radar_dish", "icon": "grafana"}],
            "cloud_services_map": [{"name": "Compute (EC2 / EKS / Lambda)", "sub": "Serverless & Containers", "shape": "gpu_rack", "icon": "aws_lambda"}, {"name": "Storage & DB (S3 / RDS / Dynamo)", "sub": "Durable Object & OLTP", "shape": "data_lake", "icon": "aws_s3"}, {"name": "Edge & IAM (CloudFront / IAM)", "sub": "Global CDN & Least Privilege", "shape": "cdn_edge", "icon": "aws_cloudfront"}],
            "language_ecosystem": [{"name": "Core Language Runtime", "sub": "Type System, GC / Ownership", "shape": "code_cube", "icon": "python"}, {"name": "Package & Build Tool", "sub": "uv / Cargo / npm / Gradle", "shape": "sdk_module"}, {"name": "Web, Data & Test Frameworks", "sub": "FastAPI, Polars, Pytest", "shape": "k8s_pod_mesh", "icon": "fastapi"}],
        }
        cards = preset_cards.get(l) or _IT_70_EXTRA_PRESETS.get(l) or [{"name": l.replace("_", " ").title(), "sub": "Studio Architecture Module", "shape": "hexagon"}]
    _tiered_subset = {
        "quic_http3_0rtt", "mtls_handshake_1rtt", "iceberg_snapshot_tables", "delta_lake_time_travel",
        "parquet_columnar_rowgroup", "sbom_supply_chain_scan", "sast_dast_security_gate",
        "k8s_pod_scheduling", "helm_kustomize_overlay", "iam_least_privilege_rbac",
        "kms_envelope_encryption", "cpu_cache_coherency_mesi", "bios_uefi_secure_boot",
        "ddr5_channel_timing", "ecc_memory_scrubbing", "wasm_wasi_sandbox",
    }
    if l in _tiered_subset and len(cards) >= 3:
        _render_tiered_zones(stage, cards, progress, world, helpers)
    else:
        _render_horizontal_pipeline(stage, cards, progress, world, helpers)
    return True
