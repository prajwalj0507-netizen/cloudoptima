const API_BASE = '/api';

export async function fetchSavingsSummary() {
  const res = await fetch(`${API_BASE}/savings/summary`);
  return res.json();
}

export async function fetchSavingsHistory() {
  const res = await fetch(`${API_BASE}/savings/history`);
  return res.json();
}

export async function fetchFindings(provider = '', riskLevel = '') {
  let url = `${API_BASE}/findings?`;
  if (provider) url += `provider=${provider}&`;
  if (riskLevel) url += `risk_level=${riskLevel}&`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchApprovals() {
  const res = await fetch(`${API_BASE}/approvals?status=pending`);
  return res.json();
}

export async function submitApprovalDecision(approvalId, action, dryRun = false) {
  const res = await fetch(`${API_BASE}/approvals/${approvalId}/decision?dry_run=${dryRun}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, decision_notes: `Processed in React dashboard` })
  });
  return res.json();
}

export async function fetchRemediations() {
  const res = await fetch(`${API_BASE}/remediation`);
  return res.json();
}

export async function triggerDirectRemediation(findingId, dryRun = false) {
  const res = await fetch(`${API_BASE}/remediation/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ finding_id: findingId, dry_run: dryRun })
  });
  return res.json();
}

export async function triggerRollback(remediationId) {
  const res = await fetch(`${API_BASE}/remediation/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ remediation_id: remediationId, reason: "Operator rollback via React Dashboard" })
  });
  return res.json();
}

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/audit?limit=30`);
  return res.json();
}

export async function seedDemoData() {
  const res = await fetch(`${API_BASE}/demo/seed`, { method: 'POST' });
  return res.json();
}

export async function triggerScanAll() {
  const res = await fetch(`${API_BASE}/accounts/scan-all`, { method: 'POST' });
  return res.json();
}

export async function fetchResources(provider = '', resourceType = '', search = '') {
  let url = `${API_BASE}/resources?`;
  if (provider) url += `provider=${provider}&`;
  if (resourceType) url += `resource_type=${resourceType}&`;
  if (search) url += `search=${encodeURIComponent(search)}&`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchResourceTelemetry() {
  const res = await fetch(`${API_BASE}/resources/telemetry/summary`);
  return res.json();
}

