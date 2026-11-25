import math
from typing import Any, Dict, List, Tuple

from core.shapes_3d import draw_vector_glyph

IT_SDLC_35_LAYOUTS: Tuple[str, ...] = (
    # 10 Networking & IT Infrastructure Topologies
    "osi_7_layers", "tcp_ip_handshake", "dns_resolution_flow", "vpc_subnet_topology",
    "cdn_edge_routing", "vpn_tunnel_mesh", "firewall_dmz_zones", "vlan_switch_ports",
    "bgp_routing_table", "zero_trust_mesh",
    # 10 Data Engineering & Lakehouse Pipelines
    "etl_elt_pipeline", "medallion_lakehouse", "lambda_kappa_arch", "kafka_streaming_topology",
    "star_snowflake_schema", "cdc_debezium_flow", "data_warehouse_cluster", "data_quality_lineage",
    "spark_dag_stages", "feature_store_ml",
    # 10 Software Development Lifecycle (SDLC), CI/CD & Software Engineering
    "sdlc_cycle_wheel", "cicd_pipeline_stages", "agile_sprint_board", "gitflow_release_lanes",
    "test_pyramid_qa", "blue_green_canary", "microservices_mesh", "event_driven_cqrs",
    "observability_pillars", "devsecops_shield_gate",
    # 5 IT Hardware, Stack, Cloud & Language Ecosystems
    "tech_stack_layers", "hardware_rack_diagram", "cloud_services_map", "language_ecosystem",
    "client_server_cluster",
)

_ACCENT = ("cyan", "purple", "emerald", "amber", "rose")
SX0, SY0, SX1, SY1 = 64, 358, 1016, 1426
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
    rh = min(232, (SH - 36) // n)
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
        stage.draw_glass_card((cb_x0, cy - 52, cb_x1, cy + 54), radius=20, accent_col=col, alpha_mul=gt, active=active)
        _draw_vis(stage, scx, cy - 16, 44, 20, 30, col, gt, shape=it.get("shape", default_shape), icon=it.get("icon", ""), label=it.get("name", ""), active=active, progress=progress, phase=i * 0.5)
        stage.draw.line((scx + (52 if is_left else -52), cy, cb_x0 if is_left else cb_x1, cy), fill=_with_alpha(col, gt), width=3)
        _draw_wrapped(stage.draw, (cb_x0 + 22, cy - 34), str(it.get("name") or it.get("title") or ""), _get_font(25, bold=True), _with_alpha(world["text"], gt), cb_x1 - cb_x0 - 44, max_lines=1)
        if it.get("sub"):
            _draw_wrapped(stage.draw, (cb_x0 + 22, cy + 6), str(it["sub"]), _get_font(20), _with_alpha(world["muted"], gt), cb_x1 - cb_x0 - 44, max_lines=2)
        prev_out = (460 if is_left else 620, cy + 56)
        prev_edge = str(it.get("edge", ""))


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
        cards = preset_cards.get(l, [{"name": l.replace("_", " ").title(), "sub": "Studio Architecture Module", "shape": "hexagon"}])
    _render_horizontal_pipeline(stage, cards, progress, world, helpers)
    return True
