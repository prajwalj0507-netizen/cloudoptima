import React, { useState, useEffect } from 'react';
import { 
  CloudLightning, Database, Scan, DollarSign, ShieldCheck, 
  Search, UserCheck, ShieldAlert, Sliders, History, FileText, CheckCircle,
  LogOut, Shield, User, Lock, ArrowRight
} from 'lucide-react';
import * as api from './services/api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('cloudoptima_react_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [loginRole, setLoginRole] = useState('admin');
  const [loginUsername, setLoginUsername] = useState('admin');
  const [loginPassword, setLoginPassword] = useState('admin123');
  const [loginError, setLoginError] = useState('');

  const [activeTab, setActiveTab] = useState('findings');
  const [summary, setSummary] = useState(null);
  const [findings, setFindings] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [remediations, setRemediations] = useState([]);
  const [audits, setAudits] = useState([]);
  const [resources, setResources] = useState([]);
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(false);

  // Filters
  const [filterProv, setFilterProv] = useState('');
  const [filterRisk, setFilterRisk] = useState('');

  // Sandbox State
  const [simEnv, setSimEnv] = useState('dev');
  const [simTopo, setSimTopo] = useState('none');
  const [simAction, setSimAction] = useState('delete_volume');
  const [simCpu, setSimCpu] = useState(3.5);

  const loadAll = async () => {
    try {
      const [sumData, findData, appData, remData, audData, resData, telData] = await Promise.all([
        api.fetchSavingsSummary(),
        api.fetchFindings(filterProv, filterRisk),
        api.fetchApprovals(),
        api.fetchRemediations(),
        api.fetchAuditLogs(),
        api.fetchResources(),
        api.fetchResourceTelemetry()
      ]);
      setSummary(sumData);
      setFindings(findData);
      setApprovals(appData);
      setRemediations(remData);
      setAudits(audData);
      setResources(resData || []);
      setTelemetry(telData || null);
    } catch (err) {
      console.error("Error loading data:", err);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadAll();
      if (currentUser.role === 'approver') {
        setActiveTab('approvals');
      } else {
        setActiveTab('findings');
      }
    }
  }, [currentUser, filterProv, filterRisk]);

  const handleRoleTabClick = (role) => {
    setLoginRole(role);
    if (role === 'admin') {
      setLoginUsername('admin');
      setLoginPassword('admin123');
    } else {
      setLoginUsername('approver');
      setLoginPassword('approver123');
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: loginUsername, password: loginPassword })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Invalid login");
      }
      const data = await res.json();
      const userObj = { ...data.user, token: data.access_token };
      setCurrentUser(userObj);
      localStorage.setItem('cloudoptima_react_user', JSON.stringify(userObj));
    } catch (err) {
      setLoginError(err.message);
    }
  };

  const handleQuickLogin = (u, p) => {
    setLoginUsername(u);
    setLoginPassword(p);
    fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    })
      .then(res => res.json())
      .then(data => {
        if (data.user) {
          const userObj = { ...data.user, token: data.access_token };
          setCurrentUser(userObj);
          localStorage.setItem('cloudoptima_react_user', JSON.stringify(userObj));
        }
      })
      .catch(err => setLoginError("Login failed: " + err));
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('cloudoptima_react_user');
  };

  const handleSeed = async () => {
    setLoading(true);
    try {
      await api.seedDemoData();
      alert("Demo data successfully seeded across AWS, Azure, and GCP accounts!");
      await loadAll();
    } catch (e) {
      alert("Seed error: " + e);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setLoading(true);
    try {
      const res = await api.triggerScanAll();
      alert(`Full scan completed across ${res.scanned_accounts} accounts.`);
      await loadAll();
    } catch (e) {
      alert("Scan error: " + e);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (id, actionStr, dryRun = false) => {
    try {
      const res = await api.submitApprovalDecision(id, actionStr, dryRun);
      alert(res.message);
      await loadAll();
    } catch (e) {
      alert("Approval error: " + e);
    }
  };

  const handleDirectRemediate = async (findingId, dryRun = false) => {
    if (!confirm(`Execute ${dryRun ? 'Dry-Run Simulation' : 'Safe Remediation (with Snapshot)'}?`)) return;
    try {
      const res = await api.triggerDirectRemediation(findingId, dryRun);
      alert(`Status: ${res.status}. Snapshot ID: ${res.snapshot_id || 'N/A'}`);
      await loadAll();
    } catch (e) {
      alert("Remediation error: " + e);
    }
  };

  const handleRollback = async (remId) => {
    if (!confirm(`Initiate rollback for Action #${remId} from safety snapshot?`)) return;
    try {
      const res = await api.triggerRollback(remId);
      alert(res.message);
      await loadAll();
    } catch (e) {
      alert("Rollback error: " + e);
    }
  };

  // Sandbox Live Scoring
  const computeSandboxScore = () => {
    let score = 0;
    if (simEnv === 'production') score += 45;
    else if (simEnv === 'staging') score += 20;
    else if (simEnv === 'unknown') score += 25;
    else score += 5;

    if (simTopo === 'lb') score += 35;
    else if (simTopo === 'mount') score += 25;

    if (simAction === 'delete_volume') score += 20;
    else if (simAction === 'stop_instance') score += 15;
    else score += 5;

    if (simCpu > 8.0) score += 10;

    return Math.min(100, Math.max(0, score));
  };

  const simScore = computeSandboxScore();

  // -------------------------------------------------------------
  // Render Login View if not logged in
  // -------------------------------------------------------------
  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F19] px-4">
        <div className="glass-card max-w-md w-full rounded-3xl p-8 border border-gray-800 shadow-2xl relative overflow-hidden">
          <div className="text-center mb-6">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-3">
              <CloudLightning className="text-white w-8 h-8" />
            </div>
            <h2 className="text-2xl font-extrabold text-white">CloudOptima</h2>
            <p className="text-xs text-gray-400 mt-1">Multi-Cloud Waste Detection & Risk Governance</p>
          </div>

          <div className="flex rounded-xl bg-gray-900 p-1 mb-5 border border-gray-800 text-xs font-semibold">
            <button
              type="button"
              onClick={() => handleRoleTabClick('admin')}
              className={`flex-1 py-2 rounded-lg flex items-center justify-center space-x-1.5 transition ${
                loginRole === 'admin' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Admin Portal</span>
            </button>
            <button
              type="button"
              onClick={() => handleRoleTabClick('approver')}
              className={`flex-1 py-2 rounded-lg flex items-center justify-center space-x-1.5 transition ${
                loginRole === 'approver' ? 'bg-amber-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Approver Portal</span>
            </button>
          </div>

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Username</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <User className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  required
                  className="w-full bg-gray-900 border border-gray-800 rounded-xl pl-9 pr-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                  className="w-full bg-gray-900 border border-gray-800 rounded-xl pl-9 pr-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {loginError && <div className="text-xs text-rose-400 text-center">{loginError}</div>}

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold hover:from-indigo-500 transition shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-1.5"
            >
              <span>Sign In to CloudOptima</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-gray-800/80 space-y-2">
            <p className="text-[11px] text-gray-400 text-center font-medium">Quick Demo Sign-In (1-Click for Presentation):</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin', 'admin123')}
                className="p-2.5 rounded-xl bg-indigo-950/60 hover:bg-indigo-900/60 text-indigo-300 border border-indigo-800/40 font-medium transition text-left flex items-center space-x-2"
              >
                <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                <div>
                  <div className="font-bold">Admin Demo</div>
                  <div className="text-[10px] text-gray-400">Full Cloud Control</div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('approver', 'approver123')}
                className="p-2.5 rounded-xl bg-amber-950/60 hover:bg-amber-900/60 text-amber-300 border border-amber-800/40 font-medium transition text-left flex items-center space-x-2"
              >
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <div>
                  <div className="font-bold">Approver Demo</div>
                  <div className="text-[10px] text-gray-400">Risk Approval Portal</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isAdmin = currentUser.role === 'admin';

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F19] text-gray-100">
      {/* Header */}
      <header className="glass-card sticky top-0 z-50 px-6 py-4 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <CloudLightning className="text-white w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-300">CloudOptima</span>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase ${
                isAdmin ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              }`}>
                {isAdmin ? 'Admin Portal' : 'Approver Portal'}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">INR (₹)</span>
            </div>
            <p className="text-xs text-gray-400">Multi-Cloud Waste Detection & Risk Governance Pipeline</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {isAdmin && (
            <>
              <button onClick={handleSeed} disabled={loading} className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 flex items-center space-x-1.5 transition">
                <Database className="w-4 h-4" />
                <span>Seed Demo Data</span>
              </button>
              <button onClick={handleScan} disabled={loading} className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 shadow-md shadow-indigo-500/25 flex items-center space-x-1.5 transition">
                <Scan className="w-4 h-4" />
                <span>Run Full Scan</span>
              </button>
            </>
          )}

          <div className="h-6 w-px bg-gray-800"></div>

          <div className="flex items-center space-x-3 pl-2">
            <div className="text-right text-xs">
              <div className="font-medium text-gray-200">{currentUser.full_name || currentUser.username}</div>
              <div className="text-indigo-400 font-semibold uppercase text-[10px]">{currentUser.role}</div>
            </div>
            <button onClick={handleLogout} title="Sign Out" className="p-2 rounded-lg bg-gray-800 hover:bg-rose-950/60 text-gray-400 hover:text-rose-300 border border-gray-700 transition">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {/* Welcome Role Banner */}
        <div className={`p-4 rounded-2xl border text-xs flex items-center justify-between ${
          isAdmin ? 'bg-indigo-950/40 border-indigo-800/40' : 'bg-amber-950/40 border-amber-800/40'
        }`}>
          <div className="flex items-center space-x-3">
            {isAdmin ? <Shield className="w-5 h-5 text-indigo-400" /> : <UserCheck className="w-5 h-5 text-amber-400" />}
            <div>
              <span className={`font-bold text-sm block ${isAdmin ? 'text-indigo-200' : 'text-amber-200'}`}>
                {isAdmin ? 'Admin Control Center' : 'Human-in-the-Loop Governance Portal'}
              </span>
              <span className="text-gray-300">
                {isAdmin ? 'Full administrative privileges: automated scans, inventory, and remediation.' :
                 'Approver view: review high/medium risk actions, verify topology dependencies, and approve with snapshots.'}
              </span>
            </div>
          </div>
        </div>

        {/* KPI Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-card rounded-2xl p-5">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Potential Monthly Waste</p>
                <h3 className="text-3xl font-extrabold text-white mt-1">
                  ₹{summary ? summary.total_potential_monthly_savings.toFixed(2) : '0.00'}
                </h3>
              </div>
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-lg">
                ₹
              </div>
            </div>
            <p className="text-xs text-amber-400 mt-3">Identified Waste across accounts</p>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Realized Savings</p>
                <h3 className="text-3xl font-extrabold text-emerald-400 mt-1">
                  ₹{summary ? summary.total_realized_savings.toFixed(2) : '0.00'}
                </h3>
              </div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-lg">
                ₹
              </div>
            </div>
            <p className="text-xs text-emerald-400 mt-3">Verified post-remediation</p>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Active Findings</p>
                <h3 className="text-3xl font-extrabold text-white mt-1">
                  {summary ? summary.open_findings_count : 0}
                </h3>
              </div>
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex space-x-2 text-xs">
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">{summary?.by_risk_level?.LOW || 0} Low</span>
              <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300">{summary?.by_risk_level?.MEDIUM || 0} Med</span>
              <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300">{summary?.by_risk_level?.HIGH || 0} High</span>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Pending Approvals</p>
                <h3 className="text-3xl font-extrabold text-indigo-400 mt-1">
                  {approvals.length}
                </h3>
              </div>
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                <UserCheck className="w-5 h-5" />
              </div>
            </div>
            <p className="text-xs text-indigo-400 mt-3">Awaiting Lead Approval</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-800 flex space-x-8 text-sm font-medium">
          <button onClick={() => setActiveTab('approvals')} className={`py-3 flex items-center space-x-2 ${activeTab === 'approvals' ? 'border-b-2 border-indigo-500 text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}>
            <ShieldAlert className="w-4 h-4" />
            <span>Approval Queue ({approvals.length})</span>
          </button>
          <button onClick={() => setActiveTab('resources')} className={`py-3 flex items-center space-x-2 ${activeTab === 'resources' ? 'border-b-2 border-emerald-500 text-emerald-400' : 'text-gray-400 hover:text-gray-200'}`}>
            <Database className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 font-semibold">Resources & Data Usage</span>
          </button>
          <button onClick={() => setActiveTab('findings')} className={`py-3 flex items-center space-x-2 ${activeTab === 'findings' ? 'border-b-2 border-indigo-500 text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}>
            <Search className="w-4 h-4" />
            <span>Waste Findings</span>
          </button>
          {isAdmin && (
            <button onClick={() => setActiveTab('remediations')} className={`py-3 flex items-center space-x-2 ${activeTab === 'remediations' ? 'border-b-2 border-indigo-500 text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}>
              <History className="w-4 h-4" />
              <span>Remediation & Rollback</span>
            </button>
          )}
          <button onClick={() => setActiveTab('simulator')} className={`py-3 flex items-center space-x-2 ${activeTab === 'simulator' ? 'border-b-2 border-cyan-500 text-cyan-400' : 'text-gray-400 hover:text-gray-200'}`}>
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span className="text-cyan-400 font-semibold">Risk Classifier Sandbox</span>
          </button>
          {isAdmin && (
            <button onClick={() => setActiveTab('audit')} className={`py-3 flex items-center space-x-2 ${activeTab === 'audit' ? 'border-b-2 border-indigo-500 text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}>
              <FileText className="w-4 h-4" />
              <span>Audit Trail</span>
            </button>
          )}
        </div>

        {/* Tab: Findings */}
        {activeTab === 'findings' && (
          <div className="space-y-4">
            <div className="flex gap-4">
              <select value={filterProv} onChange={e => setFilterProv(e.target.value)} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-200">
                <option value="">All Cloud Providers</option>
                <option value="aws">AWS</option>
                <option value="azure">Azure</option>
                <option value="gcp">GCP</option>
              </select>
              <select value={filterRisk} onChange={e => setFilterRisk(e.target.value)} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-200">
                <option value="">All Risk Levels</option>
                <option value="LOW">Low (Auto-Remediate)</option>
                <option value="MEDIUM">Medium (Approval)</option>
                <option value="HIGH">High (Critical)</option>
              </select>
            </div>

            <div className="glass-card rounded-2xl overflow-hidden border border-gray-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-900/80 text-xs uppercase text-gray-400 border-b border-gray-800">
                  <tr>
                    <th className="px-6 py-4">Resource & Provider</th>
                    <th className="px-6 py-4">Detection Reason</th>
                    <th className="px-6 py-4">Risk Level</th>
                    <th className="px-6 py-4">Monthly Saving</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {findings.map(f => (
                    <tr key={f.id} className="hover:bg-gray-800/40">
                      <td className="px-6 py-4">
                        <span className="font-mono text-xs font-bold text-indigo-300 block">{f.resource_id}</span>
                        <span className="text-[10px] uppercase font-bold text-gray-400">{f.provider}</span>
                      </td>
                      <td className="px-6 py-4 max-w-md text-xs text-gray-300">
                        {f.reason}
                        <div className="text-[10px] text-gray-500 font-mono mt-1">Action: {f.recommended_action}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                          f.risk_level === 'LOW' ? 'bg-emerald-500/20 text-emerald-400' :
                          f.risk_level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {f.risk_level} ({f.risk_score})
                        </span>
                      </td>
                      <td className="px-6 py-4 font-semibold text-emerald-400 text-sm">
                        +₹{f.estimated_monthly_saving.toFixed(2)}/mo
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        {f.status === 'remediated' ? (
                          <span className="text-xs text-emerald-400 font-medium">Remediated</span>
                        ) : (
                          isAdmin ? (
                            <>
                              <button onClick={() => handleDirectRemediate(f.id, true)} className="px-2.5 py-1 text-xs rounded bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700">Dry Run</button>
                              <button onClick={() => handleDirectRemediate(f.id, false)} className="px-2.5 py-1 text-xs rounded bg-indigo-600 text-white hover:bg-indigo-500 font-medium">Remediate</button>
                            </>
                          ) : (
                            <span className="text-xs text-amber-400 font-medium">Requires Approval</span>
                          )
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab: Approvals */}
        {activeTab === 'approvals' && (
          <div className="space-y-4">
            {approvals.length === 0 ? (
              <div className="glass-card rounded-2xl p-8 text-center text-gray-500">
                <CheckCircle className="w-8 h-8 mx-auto text-emerald-400 mb-2" />
                <p>No actions waiting in human approval queue.</p>
              </div>
            ) : (
              approvals.map(app => (
                <div key={app.id} className="glass-card rounded-2xl p-6 border-l-4 border-l-amber-500 space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm font-mono text-gray-200">{app.finding?.resource_id}</span>
                        <span className="text-xs uppercase px-2 py-0.5 rounded bg-gray-800 text-indigo-400 font-semibold">{app.finding?.provider}</span>
                      </div>
                      <p className="text-xs text-gray-300 mt-2">{app.finding?.reason}</p>
                      <p className="text-xs text-amber-400 mt-1 font-semibold">Action: {app.finding?.recommended_action} &bull; Savings: ₹{app.finding?.estimated_monthly_saving?.toFixed(2)}/mo</p>
                    </div>
                    <div className="flex space-x-2">
                      <button onClick={() => handleApproval(app.id, 'reject')} className="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 text-xs">Reject</button>
                      <button onClick={() => handleApproval(app.id, 'approve', true)} className="px-3 py-1.5 rounded-lg bg-indigo-950 text-indigo-300 border border-indigo-700 text-xs">Dry Run</button>
                      <button onClick={() => handleApproval(app.id, 'approve', false)} className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold">Approve (with Snapshot)</button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab: Remediations (Admin only) */}
        {isAdmin && activeTab === 'remediations' && (
          <div className="glass-card rounded-2xl overflow-hidden border border-gray-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-900/80 text-xs uppercase text-gray-400 border-b border-gray-800">
                <tr>
                  <th className="px-6 py-4">Action ID & Resource</th>
                  <th className="px-6 py-4">Action Type</th>
                  <th className="px-6 py-4">Snapshot ID</th>
                  <th className="px-6 py-4">State</th>
                  <th className="px-6 py-4 text-right">Rollback</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {remediations.map(r => (
                  <tr key={r.id} className="hover:bg-gray-800/40">
                    <td className="px-6 py-4 font-mono text-xs text-gray-200">
                      #{r.id} - {r.resource_id}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-indigo-300">{r.action_type}</td>
                    <td className="px-6 py-4 text-xs font-mono text-cyan-400">{r.snapshot_id || 'None'}</td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400">
                        {r.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {r.status === 'rolled_back' ? (
                        <span className="text-xs text-rose-400">Rolled Back</span>
                      ) : (
                        <button onClick={() => handleRollback(r.id)} className="px-2.5 py-1 text-xs rounded bg-rose-950/60 text-rose-300 hover:bg-rose-900 border border-rose-800/50">
                          Restore Snapshot
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        {/* Tab: Resources & Data Usage */}
        {activeTab === 'resources' && (
          <div className="space-y-6">
            {/* Telemetry Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="glass-card rounded-2xl p-5">
                <p className="text-xs font-medium text-gray-400 uppercase">Compute Fleet</p>
                <h3 className="text-2xl font-extrabold text-white mt-1">{telemetry?.total_vcpus || 0} vCPUs</h3>
                <p className="text-xs text-gray-400 mt-0.5">{telemetry?.total_memory_gb || 0} GB Total RAM</p>
                <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-indigo-400">
                  Fleet Avg: {telemetry?.avg_cpu_pct || 0}% CPU &bull; {telemetry?.avg_memory_pct || 0}% RAM
                </div>
              </div>

              <div className="glass-card rounded-2xl p-5">
                <p className="text-xs font-medium text-gray-400 uppercase">Storage Data Usage</p>
                <h3 className="text-2xl font-extrabold text-emerald-400 mt-1">{telemetry?.total_storage_used_gb || 0} GB Used</h3>
                <p className="text-xs text-gray-400 mt-0.5">of {telemetry?.total_storage_provisioned_gb || 0} GB Provisioned</p>
                <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-emerald-300">
                  Utilization: {telemetry?.storage_utilization_pct || 0}%
                </div>
              </div>

              <div className="glass-card rounded-2xl p-5">
                <p className="text-xs font-medium text-gray-400 uppercase">Network Data Egress</p>
                <h3 className="text-2xl font-extrabold text-cyan-400 mt-1">{telemetry?.total_network_out_gb || 0} GB Out</h3>
                <p className="text-xs text-gray-400 mt-0.5">{telemetry?.total_network_in_gb || 0} GB Inbound</p>
                <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-cyan-300">
                  Total Bandwidth: {telemetry?.total_data_transfer_gb || 0} GB
                </div>
              </div>

              <div className="glass-card rounded-2xl p-5">
                <p className="text-xs font-medium text-gray-400 uppercase">Total Cloud Assets</p>
                <h3 className="text-2xl font-extrabold text-amber-400 mt-1">{telemetry?.total_resources || 0} Assets</h3>
                <p className="text-xs text-amber-300 mt-0.5">₹{telemetry?.total_monthly_cost ? telemetry.total_monthly_cost.toFixed(2) : '0.00'} / mo</p>
                <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-gray-400 flex space-x-2">
                  <span className="text-amber-400">AWS: {telemetry?.by_provider?.aws?.count || 0}</span>
                  <span className="text-blue-400">Azure: {telemetry?.by_provider?.azure?.count || 0}</span>
                  <span className="text-rose-400">GCP: {telemetry?.by_provider?.gcp?.count || 0}</span>
                </div>
              </div>
            </div>

            {/* Resources Table */}
            <div className="glass-card rounded-2xl overflow-hidden border border-gray-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-900/80 text-xs uppercase text-gray-400 border-b border-gray-800">
                  <tr>
                    <th className="px-6 py-4">Resource & Provider</th>
                    <th className="px-6 py-4">Type & Environment</th>
                    <th className="px-6 py-4">State</th>
                    <th className="px-6 py-4">Compute Specs & Load</th>
                    <th className="px-6 py-4">Storage Usage</th>
                    <th className="px-6 py-4">Data Transfer</th>
                    <th className="px-6 py-4 text-right">Cost (INR)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800 text-xs">
                  {resources.map(r => (
                    <tr key={r.id} className="hover:bg-gray-800/40">
                      <td className="px-6 py-3">
                        <div className="font-semibold text-gray-200">{r.name || r.resource_id}</div>
                        <div className="text-[11px] text-gray-400 font-mono">{r.resource_id} &bull; {r.provider.toUpperCase()} &bull; {r.region}</div>
                      </td>
                      <td className="px-6 py-3">
                        <div className="text-gray-300">{r.resource_type}</div>
                        <span className="text-[10px] uppercase font-bold text-indigo-400">{r.environment_tag}</span>
                      </td>
                      <td className="px-6 py-3">
                        <span className="px-2 py-0.5 rounded text-[11px] bg-gray-800 text-gray-300">{r.state}</span>
                      </td>
                      <td className="px-6 py-3 font-mono">
                        {r.resource_type === 'compute_instance' ? (
                          <div>
                            <div>{r.extra_metadata?.vcpus || 4} vCPU &bull; {r.extra_metadata?.memory_gb || 16} GB</div>
                            <div className="text-emerald-400 font-bold">{r.average_cpu}% CPU &bull; {r.average_memory}% RAM</div>
                          </div>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-3 font-mono">
                        {r.resource_type === 'block_storage' ? (
                          <div>
                            <div>{r.extra_metadata?.storage_used_gb || 0} / {r.extra_metadata?.size_gb || 0} GB</div>
                            <div className="text-emerald-400">{r.extra_metadata?.storage_utilization_pct || 0}% used</div>
                          </div>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-3 font-mono">
                        {r.resource_type === 'compute_instance' ? (
                          <div>
                            <div className="text-cyan-400">&uarr; {r.extra_metadata?.network_out_gb || 0} GB Out</div>
                            <div className="text-gray-400">&darr; {r.extra_metadata?.network_in_gb || 0} GB In</div>
                          </div>
                        ) : r.resource_type === 'ip_address' ? (
                          <div className="text-cyan-400">{r.extra_metadata?.data_transferred_gb || 0} GB</div>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-3 text-right font-mono font-semibold text-gray-200">
                        ₹{r.monthly_cost.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab: Sandbox */}
        {activeTab === 'simulator' && (
          <div className="glass-card rounded-2xl p-6 border border-cyan-500/30">
            <h3 className="text-lg font-bold text-cyan-400 mb-2">Live Risk Classifier Sandbox</h3>
            <p className="text-xs text-gray-400 mb-6">Interact with the multi-factor risk model live to test decision boundaries.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Environment Tag</label>
                  <select value={simEnv} onChange={e => setSimEnv(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-gray-200">
                    <option value="production">Production (+45 pts)</option>
                    <option value="staging">Staging (+20 pts)</option>
                    <option value="dev">Development (+5 pts)</option>
                    <option value="unknown">Unknown (+25 pts)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Topology & Dependencies</label>
                  <select value={simTopo} onChange={e => setSimTopo(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-gray-200">
                    <option value="none">Standalone (0 pts)</option>
                    <option value="lb">Behind Load Balancer (+35 pts)</option>
                    <option value="mount">Volume Mount Dependencies (+25 pts)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Remediation Action</label>
                  <select value={simAction} onChange={e => setSimAction(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-gray-200">
                    <option value="delete_volume">Delete Volume (+20 pts)</option>
                    <option value="stop_instance">Stop Instance (+15 pts)</option>
                    <option value="release_ip">Release IP (+5 pts)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">CPU Utilization: {simCpu}%</label>
                  <input type="range" min="1" max="15" step="0.5" value={simCpu} onChange={e => setSimCpu(parseFloat(e.target.value))} className="w-full accent-indigo-500" />
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-gray-900 border border-gray-800 flex flex-col justify-between">
                <div>
                  <div className="text-xs uppercase text-gray-400">Computed Risk Score</div>
                  <div className="flex items-baseline space-x-3 mt-1">
                    <span className="text-5xl font-black text-white">{simScore.toFixed(1)}</span>
                    <span className="text-gray-500">/ 100</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                      simScore < 35 ? 'bg-emerald-500/20 text-emerald-400' :
                      simScore < 70 ? 'bg-amber-500/20 text-amber-400' : 'bg-rose-500/20 text-rose-400'
                    }`}>
                      {simScore < 35 ? 'LOW RISK' : simScore < 70 ? 'MEDIUM RISK' : 'HIGH RISK'}
                    </span>
                  </div>
                  <div className="mt-4 p-3 rounded-lg bg-gray-800 text-xs text-gray-300">
                    {simScore < 35 ? 'Routing: Auto-remediation queue. Safe to execute without disruption.' :
                     simScore < 70 ? 'Routing: Human approval queue. DevOps review required.' :
                     'Routing: High Risk Critical Approval. Mandatory pre-action snapshot enforced.'}
                  </div>
                </div>
                <div className="text-xs text-gray-400 pt-4 border-t border-gray-800">
                  Thresholds: Low &lt; 35 &bull; Med 35-69 &bull; High &ge; 70
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab: Audit (Admin only) */}
        {isAdmin && activeTab === 'audit' && (
          <div className="glass-card rounded-2xl overflow-hidden border border-gray-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-900/80 text-xs uppercase text-gray-400 border-b border-gray-800">
                <tr>
                  <th className="px-6 py-4">Timestamp</th>
                  <th className="px-6 py-4">Event Type</th>
                  <th className="px-6 py-4">Actor</th>
                  <th className="px-6 py-4">Resource</th>
                  <th className="px-6 py-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800 text-xs font-mono">
                {audits.map(a => (
                  <tr key={a.id} className="hover:bg-gray-800/40">
                    <td className="px-6 py-3 text-gray-400">{new Date(a.timestamp).toLocaleTimeString()}</td>
                    <td className="px-6 py-3 text-indigo-300">{a.event_type}</td>
                    <td className="px-6 py-3 text-gray-300">{a.actor}</td>
                    <td className="px-6 py-3 text-gray-400">{a.resource_id || '-'}</td>
                    <td className="px-6 py-3 text-gray-400 truncate max-w-xs">{JSON.stringify(a.details)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
