import { getStore } from "@netlify/blobs";

const USD_TO_INR = 85.0;

const SYSTEM_USERS = {
  admin: {
    password: "admin123",
    role: "admin",
    full_name: "Cloud Operations Admin",
    permissions: ["all", "scan", "seed", "remediate", "approve", "view_audit"],
  },
  approver: {
    password: "approver123",
    role: "approver",
    full_name: "Governance & Security Approver",
    permissions: ["approve", "reject", "view_findings", "test_sandbox"],
  },
};

function createInitialState() {
  const nowIso = new Date().toISOString();

  const resources = [
    {
      resource_id: "i-08a4f2c91b7e001",
      name: "aws-batch-worker-idle-01",
      provider: "aws",
      resource_type: "compute_instance",
      region: "us-east-1",
      environment_tag: "dev",
      state: "running",
      monthly_cost: 135.0,
      average_cpu: 1.8,
      average_memory: 14.2,
      extra_metadata: { vcpus: 4, memory_gb: 16, network_in_gb: 12.4, network_out_gb: 8.1, data_transfer_gb: 20.5 },
    },
    {
      resource_id: "vol-09c3a7d1e4f8202",
      name: "aws-orphan-analytics-vol",
      provider: "aws",
      resource_type: "block_storage",
      region: "us-east-1",
      environment_tag: "staging",
      state: "available",
      monthly_cost: 120.0,
      average_cpu: null,
      average_memory: null,
      extra_metadata: { size_gb: 1200, storage_used_gb: 310 },
    },
    {
      resource_id: "i-0f4b129c88a7703",
      name: "aws-prod-checkout-node-02",
      provider: "aws",
      resource_type: "compute_instance",
      region: "us-east-1",
      environment_tag: "production",
      state: "running",
      monthly_cost: 280.0,
      average_cpu: 7.4,
      average_memory: 38.5,
      extra_metadata: { vcpus: 8, memory_gb: 32, network_in_gb: 88.2, network_out_gb: 142.6, data_transfer_gb: 230.8 },
    },
    {
      resource_id: "eipalloc-0a1b2c3d4e5f",
      name: "aws-unassociated-elastic-ip",
      provider: "aws",
      resource_type: "ip_address",
      region: "us-east-1",
      environment_tag: "dev",
      state: "unassociated",
      monthly_cost: 15.0,
      average_cpu: null,
      average_memory: null,
      extra_metadata: {},
    },
    {
      resource_id: "vm-az-batch-indexer-stg",
      name: "azure-staging-indexer-vm",
      provider: "azure",
      resource_type: "compute_instance",
      region: "eastus",
      environment_tag: "staging",
      state: "running",
      monthly_cost: 165.0,
      average_cpu: 3.1,
      average_memory: 22.0,
      extra_metadata: { vcpus: 4, memory_gb: 16, network_in_gb: 18.0, network_out_gb: 11.5, data_transfer_gb: 29.5 },
    },
    {
      resource_id: "disk-az-unattached-04",
      name: "azure-legacy-snapshot-disk",
      provider: "azure",
      resource_type: "block_storage",
      region: "eastus",
      environment_tag: "dev",
      state: "unattached",
      monthly_cost: 95.0,
      average_cpu: null,
      average_memory: null,
      extra_metadata: { size_gb: 1024, storage_used_gb: 180 },
    },
    {
      resource_id: "vm-az-prod-ledger-01",
      name: "azure-prod-ledger-replica",
      provider: "azure",
      resource_type: "compute_instance",
      region: "eastus",
      environment_tag: "production",
      state: "running",
      monthly_cost: 290.0,
      average_cpu: 5.2,
      average_memory: 29.0,
      extra_metadata: { vcpus: 8, memory_gb: 32, network_in_gb: 54.0, network_out_gb: 91.2, data_transfer_gb: 145.2 },
    },
    {
      resource_id: "gcp-vm-ml-sandbox-01",
      name: "gcp-dev-notebook-runner",
      provider: "gcp",
      resource_type: "compute_instance",
      region: "us-central1",
      environment_tag: "dev",
      state: "running",
      monthly_cost: 145.0,
      average_cpu: 1.4,
      average_memory: 11.8,
      extra_metadata: { vcpus: 4, memory_gb: 16, network_in_gb: 9.2, network_out_gb: 6.4, data_transfer_gb: 15.6 },
    },
    {
      resource_id: "disk-gcp-orphan-09",
      name: "gcp-orphan-pd-ssd",
      provider: "gcp",
      resource_type: "block_storage",
      region: "us-central1",
      environment_tag: "staging",
      state: "unattached",
      monthly_cost: 110.0,
      average_cpu: null,
      average_memory: null,
      extra_metadata: { size_gb: 800, storage_used_gb: 215 },
    },
    {
      resource_id: "gcp-prod-api-gateway-03",
      name: "gcp-prod-edge-worker",
      provider: "gcp",
      resource_type: "compute_instance",
      region: "us-central1",
      environment_tag: "production",
      state: "running",
      monthly_cost: 320.0,
      average_cpu: 42.5,
      average_memory: 64.0,
      extra_metadata: { vcpus: 16, memory_gb: 64, network_in_gb: 310.0, network_out_gb: 490.0, data_transfer_gb: 800.0 },
    },
  ];

  const findings = [
    {
      id: 1,
      resource_id: "i-0f4b129c88a7703",
      provider: "aws",
      resource_type: "compute_instance",
      category: "compute",
      rule_id: "IDLE_COMPUTE_7D",
      reason: "7-day average CPU is 7.4% behind production load balancer",
      details: "Production workload behind Application Load Balancer with sustained low utilization",
      risk_level: "HIGH",
      risk_score: 85.0,
      estimated_monthly_saving: 280.0,
      recommended_action: "stop_instance",
      suggested_action: "stop_instance",
      status: "open",
      resource: { environment_tag: "production", average_cpu: 7.4 },
    },
    {
      id: 2,
      resource_id: "vm-az-prod-ledger-01",
      provider: "azure",
      resource_type: "compute_instance",
      category: "compute",
      rule_id: "IDLE_COMPUTE_7D",
      reason: "7-day average CPU is 5.2% on production database replica",
      details: "Production resource with active mount dependencies",
      risk_level: "HIGH",
      risk_score: 80.0,
      estimated_monthly_saving: 290.0,
      recommended_action: "stop_instance",
      suggested_action: "stop_instance",
      status: "open",
      resource: { environment_tag: "production", average_cpu: 5.2 },
    },
    {
      id: 3,
      resource_id: "vol-09c3a7d1e4f8202",
      provider: "aws",
      resource_type: "block_storage",
      category: "storage",
      rule_id: "UNATTACHED_VOLUME_14D",
      reason: "1,200 GB EBS volume unattached for 19 days",
      details: "Staging volume pending snapshot backup before deletion",
      risk_level: "MEDIUM",
      risk_score: 52.0,
      estimated_monthly_saving: 120.0,
      recommended_action: "delete_volume",
      suggested_action: "delete_volume",
      status: "open",
      resource: { environment_tag: "staging", average_cpu: 0.0 },
    },
    {
      id: 4,
      resource_id: "vm-az-batch-indexer-stg",
      provider: "azure",
      resource_type: "compute_instance",
      category: "compute",
      rule_id: "IDLE_COMPUTE_7D",
      reason: "Staging VM averaging 3.1% CPU over 7 days",
      details: "Staging compute instance with attached persistent disk",
      risk_level: "MEDIUM",
      risk_score: 55.0,
      estimated_monthly_saving: 165.0,
      recommended_action: "stop_instance",
      suggested_action: "stop_instance",
      status: "open",
      resource: { environment_tag: "staging", average_cpu: 3.1 },
    },
    {
      id: 5,
      resource_id: "disk-gcp-orphan-09",
      provider: "gcp",
      resource_type: "block_storage",
      category: "storage",
      rule_id: "UNATTACHED_DISK_14D",
      reason: "800 GB Persistent SSD unattached in us-central1",
      details: "Orphaned disk in staging project",
      risk_level: "MEDIUM",
      risk_score: 48.0,
      estimated_monthly_saving: 110.0,
      recommended_action: "delete_volume",
      suggested_action: "delete_volume",
      status: "open",
      resource: { environment_tag: "staging", average_cpu: 0.0 },
    },
    {
      id: 6,
      resource_id: "i-08a4f2c91b7e001",
      provider: "aws",
      resource_type: "compute_instance",
      category: "compute",
      rule_id: "DEV_IDLE_INSTANCE",
      reason: "Dev worker node at 1.8% CPU (Deep Idle)",
      details: "Standalone dev compute instance eligible for off-hours schedule",
      risk_level: "LOW",
      risk_score: 15.0,
      estimated_monthly_saving: 135.0,
      recommended_action: "stop_instance",
      suggested_action: "stop_instance",
      status: "open",
      resource: { environment_tag: "dev", average_cpu: 1.8 },
    },
    {
      id: 7,
      resource_id: "eipalloc-0a1b2c3d4e5f",
      provider: "aws",
      resource_type: "ip_address",
      category: "network",
      rule_id: "UNASSOCIATED_PUBLIC_IP",
      reason: "Static Elastic IP unassociated for 28 days",
      details: "Standalone dev network allocation",
      risk_level: "LOW",
      risk_score: 10.0,
      estimated_monthly_saving: 15.0,
      recommended_action: "release_ip",
      suggested_action: "release_ip",
      status: "open",
      resource: { environment_tag: "dev", average_cpu: 0.0 },
    },
    {
      id: 8,
      resource_id: "disk-az-unattached-04",
      provider: "azure",
      resource_type: "block_storage",
      category: "storage",
      rule_id: "UNATTACHED_DISK_14D",
      reason: "1,024 GB Dev Managed Disk unattached",
      details: "Standalone dev disk with zero mount dependencies",
      risk_level: "LOW",
      risk_score: 25.0,
      estimated_monthly_saving: 95.0,
      recommended_action: "delete_volume",
      suggested_action: "delete_volume",
      status: "open",
      resource: { environment_tag: "dev", average_cpu: 0.0 },
    },
    {
      id: 9,
      resource_id: "gcp-vm-ml-sandbox-01",
      provider: "gcp",
      resource_type: "compute_instance",
      category: "compute",
      rule_id: "DEV_IDLE_INSTANCE",
      reason: "GCP dev notebook VM at 1.4% CPU (Deep Idle)",
      details: "Standalone dev sandbox instance",
      risk_level: "LOW",
      risk_score: 15.0,
      estimated_monthly_saving: 145.0,
      recommended_action: "stop_instance",
      suggested_action: "stop_instance",
      status: "open",
      resource: { environment_tag: "dev", average_cpu: 1.4 },
    },
  ];

  const approvals = [
    { id: 1, finding_id: 1, status: "pending", created_at: nowIso, approver: null, decision_notes: null },
    { id: 2, finding_id: 2, status: "pending", created_at: nowIso, approver: null, decision_notes: null },
    { id: 3, finding_id: 3, status: "pending", created_at: nowIso, approver: null, decision_notes: null },
    { id: 4, finding_id: 4, status: "pending", created_at: nowIso, approver: null, decision_notes: null },
    { id: 5, finding_id: 5, status: "pending", created_at: nowIso, approver: null, decision_notes: null },
  ];

  const remediations = [];

  const focusRecords = [
    {
      ProviderName: "AWS",
      RegionId: "us-east-1",
      ResourceId: "i-08a4f2c91b7e001",
      ResourceType: "compute_instance",
      ChargeCategory: "Usage",
      ChargeSubcategory: "Compute Engine",
      BilledCost: 135.0,
      is_synthetic_leak: true,
      ground_truth_leak_type: "idle_compute",
      Telemetry: { avg_cpu_pct: 1.8, iops: 12, network_egress_gb: 8.1 },
      Tags: { Environment: "dev" },
    },
    {
      ProviderName: "AWS",
      RegionId: "us-east-1",
      ResourceId: "vol-09c3a7d1e4f8202",
      ResourceType: "block_storage",
      ChargeCategory: "Usage",
      ChargeSubcategory: "EBS GP3 Storage",
      BilledCost: 120.0,
      is_synthetic_leak: true,
      ground_truth_leak_type: "unattached_volume",
      Telemetry: { iops: 0 },
      Tags: { Environment: "staging" },
    },
    {
      ProviderName: "AWS",
      RegionId: "us-east-1",
      ResourceId: "i-0f4b129c88a7703",
      ResourceType: "compute_instance",
      ChargeCategory: "Usage",
      ChargeSubcategory: "EC2 m5.2xlarge",
      BilledCost: 280.0,
      is_synthetic_leak: false,
      ground_truth_leak_type: null,
      Telemetry: { avg_cpu_pct: 7.4, iops: 45, network_egress_gb: 142.6 },
      Tags: { Environment: "production" },
    },
    {
      ProviderName: "Azure",
      RegionId: "eastus",
      ResourceId: "vm-az-batch-indexer-stg",
      ResourceType: "compute_instance",
      ChargeCategory: "Usage",
      ChargeSubcategory: "Standard_D4s_v3",
      BilledCost: 165.0,
      is_synthetic_leak: true,
      ground_truth_leak_type: "idle_vm",
      Telemetry: { avg_cpu_pct: 3.1, iops: 18, network_egress_gb: 11.5 },
      Tags: { Environment: "staging" },
    },
    {
      ProviderName: "Azure",
      RegionId: "eastus",
      ResourceId: "disk-az-unattached-04",
      ResourceType: "block_storage",
      ChargeCategory: "Usage",
      ChargeSubcategory: "Managed Premium SSD",
      BilledCost: 95.0,
      is_synthetic_leak: true,
      ground_truth_leak_type: "unattached_disk",
      Telemetry: { iops: 0 },
      Tags: { Environment: "dev" },
    },
    {
      ProviderName: "Google Cloud",
      RegionId: "us-central1",
      ResourceId: "gcp-vm-ml-sandbox-01",
      ResourceType: "compute_instance",
      ChargeCategory: "Usage",
      ChargeSubcategory: "n2-standard-4",
      BilledCost: 145.0,
      is_synthetic_leak: true,
      ground_truth_leak_type: "idle_compute",
      Telemetry: { avg_cpu_pct: 1.4, iops: 9, network_egress_gb: 6.4 },
      Tags: { Environment: "dev" },
    },
    {
      ProviderName: "Google Cloud",
      RegionId: "us-central1",
      ResourceId: "gcp-prod-api-gateway-03",
      ResourceType: "compute_instance",
      ChargeCategory: "Usage",
      ChargeSubcategory: "c2-standard-16",
      BilledCost: 320.0,
      is_synthetic_leak: false,
      ground_truth_leak_type: null,
      Telemetry: { avg_cpu_pct: 42.5, iops: 410, network_egress_gb: 490.0 },
      Tags: { Environment: "production" },
    },
  ];

  const auditLogs = [
    {
      timestamp: nowIso,
      event_type: "MULTI_CLOUD_SCAN_COMPLETED",
      actor: "scheduler_pipeline",
      provider: "aws",
      resource_id: "aws-prod-01239",
      event_metadata: { findings_detected: 4, focus_compliant: true },
    },
    {
      timestamp: nowIso,
      event_type: "RISK_CLASSIFICATION_ROUTED",
      actor: "risk_classifier_v1",
      provider: "azure",
      resource_id: "vm-az-prod-ledger-01",
      event_metadata: { risk_score: 80.0, tier: "HIGH", routed_to: "approval_queue" },
    },
  ];

  const savingsHistory = [];
  const today = new Date();
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    savingsHistory.push({
      date: d.toISOString().slice(0, 10),
      realized: Math.round((13 - i) * 3800 + 4500),
      potential: 114750,
    });
  }

  return {
    resources,
    findings,
    approvals,
    remediations,
    focusRecords,
    auditLogs,
    savingsHistory,
    nextActionId: 1,
    nextFindingId: 10,
    nextApprovalId: 6,
  };
}

let memoryFallbackState = null;

async function loadState() {
  try {
    const store = getStore("cloudoptima-state");
    const saved = await store.get("demo_state_v1", { type: "json" });
    if (saved && saved.findings) {
      return saved;
    }
    const fresh = createInitialState();
    await store.setJSON("demo_state_v1", fresh);
    return fresh;
  } catch {
    if (!memoryFallbackState) {
      memoryFallbackState = createInitialState();
    }
    return memoryFallbackState;
  }
}

async function saveState(state) {
  memoryFallbackState = state;
  try {
    const store = getStore("cloudoptima-state");
    await store.setJSON("demo_state_v1", state);
  } catch {
    // Fallback to in-memory cache when running outside Netlify Blobs runtime
  }
}

function computeSavingsSummary(state) {
  const openFindings = state.findings.filter((f) => f.status === "open" || f.status === "pending_approval");
  const remediatedFindings = state.findings.filter((f) => f.status === "remediated");

  const totalPotentialInr = openFindings.reduce((sum, f) => sum + (f.estimated_monthly_saving || 0) * USD_TO_INR, 0);
  const totalRealizedInr = remediatedFindings.reduce((sum, f) => sum + (f.estimated_monthly_saving || 0) * USD_TO_INR, 0);

  const byProvider = { aws: 0, azure: 0, gcp: 0 };
  const byCategory = {};
  const byRisk = { LOW: 0, MEDIUM: 0, HIGH: 0 };

  for (const f of openFindings) {
    const p = (f.provider || "aws").toLowerCase();
    byProvider[p] = Math.round(((byProvider[p] || 0) + (f.estimated_monthly_saving || 0) * USD_TO_INR) * 100) / 100;
    const c = f.category || "compute";
    byCategory[c] = Math.round(((byCategory[c] || 0) + (f.estimated_monthly_saving || 0) * USD_TO_INR) * 100) / 100;
    const r = (f.risk_level || "LOW").toUpperCase();
    byRisk[r] = (byRisk[r] || 0) + 1;
  }

  return {
    total_potential_monthly_savings: Math.round(totalPotentialInr * 100) / 100,
    total_realized_savings: Math.round(totalRealizedInr * 100) / 100,
    open_findings_count: openFindings.length,
    remediated_count: remediatedFindings.length,
    by_provider: byProvider,
    by_category: byCategory,
    by_risk_level: byRisk,
  };
}

function generateCpuTraces(hours = 24) {
  const points = Math.min(288, Math.max(24, hours * 12));
  const now = new Date();
  const traces = [];
  let sum = 0;
  let peak = 0;

  for (let i = points - 1; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 5 * 60 * 1000);
    const label = t.toISOString().substring(11, 16);
    const wave = Math.sin(i * 0.25) * 4.5 + Math.cos(i * 0.11) * 2.5;
    const avg = Math.max(3.2, Math.min(28.0, 14.5 + wave));
    const p95 = Math.min(48.0, avg + 4.8 + Math.abs(Math.sin(i * 0.4)) * 3.5);
    sum += avg;
    if (p95 > peak) peak = p95;
    traces.push({
      time_label: label,
      timestamp: t.toISOString(),
      avg_cpu: Math.round(avg * 10) / 10,
      p95_cpu: Math.round(p95 * 10) / 10,
    });
  }

  const meanCpu = Math.round((sum / traces.length) * 10) / 10;
  const liveCpu = traces[traces.length - 1].avg_cpu;

  return {
    vm_id: "netlify-cloud-host",
    live_cpu: liveCpu,
    mean_cpu: meanCpu,
    p95_cpu: Math.round(peak * 10) / 10,
    is_classified_idle: meanCpu < 10.0,
    system_info: {
      os_name: "Linux x86_64 (Netlify Serverless)",
      logical_cores: 4,
      total_ram_gb: 16.0,
      memory_load_pct: 34.2,
    },
    traces,
  };
}

export default async (req) => {
  const url = new URL(req.url);
  const path = url.pathname.replace(/\/+$/, "") || "/";
  const method = req.method.toUpperCase();

  if (path === "/health") {
    return Response.json({ status: "healthy", project: "CloudOptima", version: "1.0.0", runtime: "netlify-functions" });
  }

  // Auth login
  if (path === "/api/auth/login" && method === "POST") {
    const body = await req.json().catch(() => ({}));
    const username = (body.username || "").trim().toLowerCase();
    const userInfo = SYSTEM_USERS[username];
    if (!userInfo || userInfo.password !== body.password) {
      return Response.json(
        { detail: "Invalid credentials. Use 'admin'/'admin123' or 'approver'/'approver123'." },
        { status: 401 }
      );
    }
    return Response.json({
      access_token: `netlify-demo-jwt-${username}-${Date.now()}`,
      token_type: "bearer",
      user: {
        username,
        role: userInfo.role,
        full_name: userInfo.full_name,
        permissions: userInfo.permissions,
      },
    });
  }

  const state = await loadState();

  // Savings endpoints
  if (path === "/api/savings/summary" && method === "GET") {
    return Response.json(computeSavingsSummary(state));
  }

  if (path === "/api/savings/history" && method === "GET") {
    return Response.json(state.savingsHistory);
  }

  if (path === "/api/savings/clear-realized" && method === "POST") {
    state.remediations.forEach((r) => {
      r.status = "rolled_back";
    });
    state.findings.forEach((f) => {
      if (f.status === "remediated") f.status = "open";
    });
    state.savingsHistory.forEach((h) => {
      h.realized = 0;
    });
    state.auditLogs.unshift({
      timestamp: new Date().toISOString(),
      event_type: "REALIZED_SAVINGS_CLEARED",
      actor: "admin",
      provider: "aws",
      resource_id: "fleet-ledger",
      event_metadata: { realized_reset_to: 0 },
    });
    await saveState(state);
    return Response.json({ status: "success", message: "Realized savings ledger successfully cleared to ₹0.00." });
  }

  if (path === "/api/savings/reopen-all-waste" && method === "POST") {
    state.findings.forEach((f) => {
      f.status = "open";
    });
    state.approvals.forEach((a) => {
      a.status = "pending";
      a.decided_at = null;
    });
    state.auditLogs.unshift({
      timestamp: new Date().toISOString(),
      event_type: "WASTE_FINDINGS_REOPENED",
      actor: "admin",
      provider: "aws",
      resource_id: "all-findings",
      event_metadata: { count: state.findings.length },
    });
    await saveState(state);
    return Response.json({ status: "success", message: "All waste findings and approvals successfully re-opened." });
  }

  // FOCUS & Telemetry endpoints
  if (path === "/api/focus/records" && method === "GET") {
    return Response.json(state.focusRecords);
  }

  if (path === "/api/focus/inject-leaks" && method === "POST") {
    const ts = Date.now().toString().slice(-4);
    const newRecords = [
      {
        ProviderName: "AWS",
        RegionId: "us-east-1",
        ResourceId: `vol-leak-${ts}`,
        ResourceType: "block_storage",
        ChargeCategory: "Usage",
        ChargeSubcategory: "Unattached EBS GP3",
        BilledCost: 85.0,
        is_synthetic_leak: true,
        ground_truth_leak_type: "unattached_volume",
        Telemetry: { iops: 0 },
        Tags: { Environment: "staging" },
      },
      {
        ProviderName: "Azure",
        RegionId: "eastus",
        ResourceId: `vm-leak-${ts}`,
        ResourceType: "compute_instance",
        ChargeCategory: "Usage",
        ChargeSubcategory: "Idle Standard_B4ms",
        BilledCost: 110.0,
        is_synthetic_leak: true,
        ground_truth_leak_type: "idle_vm",
        Telemetry: { avg_cpu_pct: 1.2, iops: 5, network_egress_gb: 2.1 },
        Tags: { Environment: "dev" },
      },
      {
        ProviderName: "Google Cloud",
        RegionId: "us-central1",
        ResourceId: `gcp-leak-${ts}`,
        ResourceType: "compute_instance",
        ChargeCategory: "Usage",
        ChargeSubcategory: "Idle e2-standard-4",
        BilledCost: 98.0,
        is_synthetic_leak: true,
        ground_truth_leak_type: "idle_compute",
        Telemetry: { avg_cpu_pct: 1.5, iops: 7, network_egress_gb: 3.0 },
        Tags: { Environment: "dev" },
      },
    ];
    state.focusRecords.unshift(...newRecords);
    state.findings.push({
      id: state.nextFindingId++,
      resource_id: `vm-leak-${ts}`,
      provider: "azure",
      resource_type: "compute_instance",
      category: "compute",
      rule_id: "SYNTHETIC_TELEMETRY_LEAK",
      reason: "Injected synthetic idle VM (1.2% CPU)",
      details: "Telemetry leak verification target",
      risk_level: "LOW",
      risk_score: 15.0,
      estimated_monthly_saving: 110.0,
      recommended_action: "stop_instance",
      suggested_action: "stop_instance",
      status: "open",
      resource: { environment_tag: "dev", average_cpu: 1.2 },
    });
    state.auditLogs.unshift({
      timestamp: new Date().toISOString(),
      event_type: "TELEMETRY_LEAKS_INJECTED",
      actor: "admin",
      provider: "aws",
      resource_id: `vol-leak-${ts}`,
      event_metadata: { leaks_added: 3 },
    });
    await saveState(state);
    return Response.json({ status: "success", leaks_added: 3 });
  }

  if (path === "/api/focus/system-traces" && method === "GET") {
    const hours = parseInt(url.searchParams.get("hours") || "24", 10);
    return Response.json(generateCpuTraces(hours));
  }

  if (path === "/api/focus/live-cpu" && method === "GET") {
    const sample = Math.round((11.5 + Math.random() * 8.5) * 10) / 10;
    return Response.json({
      status: "success",
      live_cpu: sample,
      timestamp: new Date().toTimeString().slice(0, 8),
    });
  }

  // Resources endpoints
  if (path === "/api/resources" && method === "GET") {
    return Response.json(state.resources);
  }

  if ((path === "/api/resources/telemetry" || path === "/api/resources/telemetry/summary") && method === "GET") {
    const resources = state.resources;
    let totalVcpus = 0;
    let totalRam = 0;
    let totalStorageProv = 0;
    let totalStorageUsed = 0;
    let totalNetIn = 0;
    let totalNetOut = 0;
    const cpuSamples = [];
    const memSamples = [];

    for (const r of resources) {
      const m = r.extra_metadata || {};
      if (r.resource_type === "compute_instance") {
        totalVcpus += m.vcpus || 4;
        totalRam += m.memory_gb || 16;
        totalNetIn += m.network_in_gb || 0;
        totalNetOut += m.network_out_gb || 0;
        if (typeof r.average_cpu === "number") cpuSamples.push(r.average_cpu);
        if (typeof r.average_memory === "number") memSamples.push(r.average_memory);
      } else if (r.resource_type === "block_storage") {
        totalStorageProv += m.size_gb || 0;
        totalStorageUsed += m.storage_used_gb || 0;
      }
    }

    const avgCpu = cpuSamples.length ? cpuSamples.reduce((a, b) => a + b, 0) / cpuSamples.length : 0;
    const avgMem = memSamples.length ? memSamples.reduce((a, b) => a + b, 0) / memSamples.length : 0;
    const storagePct = totalStorageProv > 0 ? (totalStorageUsed / totalStorageProv) * 100 : 0;

    return Response.json({
      total_resources: resources.length,
      total_vcpus: totalVcpus,
      total_ram_gb: Math.round(totalRam * 10) / 10,
      total_memory_gb: Math.round(totalRam * 10) / 10,
      fleet_avg_cpu: Math.round(avgCpu * 10) / 10,
      fleet_avg_memory: Math.round(avgMem * 10) / 10,
      total_storage_used_gb: Math.round(totalStorageUsed * 10) / 10,
      total_storage_provisioned_gb: Math.round(totalStorageProv * 10) / 10,
      storage_utilization_pct: Math.round(storagePct * 10) / 10,
      total_network_out_gb: Math.round(totalNetOut * 10) / 10,
      total_network_in_gb: Math.round(totalNetIn * 10) / 10,
      total_data_transfer_gb: Math.round((totalNetIn + totalNetOut) * 10) / 10,
    });
  }

  // Findings endpoint
  if (path === "/api/findings" && method === "GET") {
    const prov = (url.searchParams.get("provider") || "").toLowerCase();
    const risk = (url.searchParams.get("risk_level") || "").toUpperCase();
    let list = [...state.findings];
    if (prov) list = list.filter((f) => f.provider.toLowerCase() === prov);
    if (risk) list = list.filter((f) => f.risk_level.toUpperCase() === risk);
    list.sort((a, b) => b.risk_score - a.risk_score);
    return Response.json(list);
  }

  // Remediation execute / trigger
  if ((path === "/api/remediation/execute" || path === "/api/remediation/trigger") && method === "POST") {
    const body = await req.json().catch(() => ({}));
    const finding = state.findings.find((f) => f.id == body.finding_id);
    if (!finding) {
      return Response.json({ detail: "Finding not found" }, { status: 404 });
    }
    const dryRun = Boolean(body.dry_run);
    const nowIso = new Date().toISOString();
    const snapshotId = `snap-${finding.provider}-${Math.floor(Date.now() / 1000)}`;
    const action = {
      id: state.nextActionId++,
      finding_id: finding.id,
      resource_id: finding.resource_id,
      action_type: finding.recommended_action,
      snapshot_id: snapshotId,
      status: "verified",
      dry_run: dryRun,
      triggered_by: "operator",
      created_at: nowIso,
      executed_at: nowIso,
    };

    if (!dryRun) {
      finding.status = "remediated";
      const approval = state.approvals.find((a) => a.finding_id === finding.id && a.status === "pending");
      if (approval) {
        approval.status = "approved";
        approval.decided_at = nowIso;
        approval.approver = "operator";
      }
      state.remediations.unshift(action);
      state.auditLogs.unshift({
        timestamp: nowIso,
        event_type: "REMEDIATION_EXECUTED",
        actor: "operator",
        provider: finding.provider,
        resource_id: finding.resource_id,
        event_metadata: { action_id: action.id, snapshot_id: snapshotId, action_type: action.action_type },
      });
      await saveState(state);
    }

    return Response.json(action);
  }

  // Remediation list
  if ((path === "/api/remediation" || path === "/api/remediations") && method === "GET") {
    return Response.json(state.remediations);
  }

  // Remediation rollback
  if (path === "/api/remediation/rollback" && method === "POST") {
    const body = await req.json().catch(() => ({}));
    const action = state.remediations.find((r) => r.id == body.remediation_id);
    if (!action) {
      return Response.json({ detail: "Remediation action not found" }, { status: 404 });
    }
    const nowIso = new Date().toISOString();
    action.status = "rolled_back";
    const finding = state.findings.find((f) => f.id === action.finding_id);
    if (finding) finding.status = "open";
    state.auditLogs.unshift({
      timestamp: nowIso,
      event_type: "REMEDIATION_ROLLED_BACK",
      actor: "operator",
      provider: finding ? finding.provider : "aws",
      resource_id: action.resource_id,
      event_metadata: { remediation_id: action.id, snapshot_restored: action.snapshot_id },
    });
    await saveState(state);
    return Response.json({ status: "success", message: `Rolled back #ACT-00${action.id} using snapshot ${action.snapshot_id}.` });
  }

  // Approvals list
  if (path === "/api/approvals" && method === "GET") {
    const statusFilter = (url.searchParams.get("status") || "").toLowerCase();
    let list = state.approvals.map((a) => ({
      ...a,
      finding: state.findings.find((f) => f.id === a.finding_id) || {},
    }));
    if (statusFilter) {
      list = list.filter((a) => (a.status || "").toLowerCase() === statusFilter);
    }
    return Response.json(list);
  }

  // Approvals decision
  const approvalMatch = path.match(/^\/api\/approvals\/(\d+)\/decision$/);
  if (approvalMatch && method === "POST") {
    const approvalId = parseInt(approvalMatch[1], 10);
    const approval = state.approvals.find((a) => a.id === approvalId);
    if (!approval) {
      return Response.json({ detail: "Approval request not found" }, { status: 404 });
    }
    const finding = state.findings.find((f) => f.id === approval.finding_id);
    const body = await req.json().catch(() => ({}));
    const decisionStr = (body.action || body.decision || "approve").toLowerCase();
    const nowIso = new Date().toISOString();

    approval.decided_at = nowIso;
    approval.decision_notes = body.decision_notes || "Decided via CloudOptima Dashboard";
    approval.approver = "lead_engineer";

    if (decisionStr.includes("approve")) {
      approval.status = "approved";
      const snapshotId = `snap-${finding ? finding.provider : "cloud"}-${Math.floor(Date.now() / 1000)}`;
      const action = {
        id: state.nextActionId++,
        finding_id: finding ? finding.id : approval.finding_id,
        resource_id: finding ? finding.resource_id : "resource",
        action_type: finding ? finding.recommended_action : "stop_instance",
        snapshot_id: snapshotId,
        status: "verified",
        dry_run: false,
        triggered_by: "human_approver",
        created_at: nowIso,
        executed_at: nowIso,
      };
      if (finding) finding.status = "remediated";
      state.remediations.unshift(action);
      state.auditLogs.unshift({
        timestamp: nowIso,
        event_type: "APPROVAL_GRANTED_AND_EXECUTED",
        actor: "lead_engineer",
        provider: finding ? finding.provider : "aws",
        resource_id: action.resource_id,
        event_metadata: { approval_id: approvalId, snapshot_id: snapshotId, action_id: action.id },
      });
      await saveState(state);
      return Response.json({
        status: "success",
        snapshot_id: snapshotId,
        remediation_status: "VERIFIED",
        remediation_id: action.id,
      });
    } else {
      approval.status = "rejected";
      if (finding) finding.status = "dismissed";
      state.auditLogs.unshift({
        timestamp: nowIso,
        event_type: "APPROVAL_REJECTED",
        actor: "lead_engineer",
        provider: finding ? finding.provider : "aws",
        resource_id: finding ? finding.resource_id : "",
        event_metadata: { approval_id: approvalId },
      });
      await saveState(state);
      return Response.json({ status: "rejected", message: "Approval request dismissed." });
    }
  }

  // Audit logs
  if (path === "/api/audit" && method === "GET") {
    const limit = parseInt(url.searchParams.get("limit") || "25", 10);
    return Response.json(state.auditLogs.slice(0, limit));
  }

  // Demo reset / seed / scan-all
  if ((path === "/api/demo/reset" || path === "/api/demo/seed" || path === "/api/accounts/scan-all") && method === "POST") {
    const fresh = createInitialState();
    fresh.auditLogs.unshift({
      timestamp: new Date().toISOString(),
      event_type: path.includes("scan") ? "MULTI_CLOUD_RESCAN" : "DEMO_ENVIRONMENT_RESET",
      actor: "admin",
      provider: "aws",
      resource_id: "all-accounts",
      event_metadata: { resources: fresh.resources.length, findings: fresh.findings.length },
    });
    await saveState(fresh);
    return Response.json({ status: "success", message: "Multi-cloud fleet refreshed cleanly." });
  }

  return Response.json({ detail: `Route ${method} ${path} not found` }, { status: 404 });
};

export const config = {
  path: ["/api/*", "/health"],
};
