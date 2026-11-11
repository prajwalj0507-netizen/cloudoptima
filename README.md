# CloudOptima: Multi-Cloud Waste Detection & Risk-Governed Remediation Pipeline

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Multi-Cloud](https://img.shields.io/badge/Clouds-AWS%20%7C%20Azure%20%7C%20GCP-orange.svg)](#)
[![Safety](https://img.shields.io/badge/Safety-Pre--Action%20Snapshots%20%26%20Rollback-blue.svg)](#)

**CloudOptima** is an automated multi-cloud cost optimization platform that continuously monitors AWS, Azure, and GCP accounts. It detects cloud waste using heuristic rule engines and Machine Learning (Isolation Forest), evaluates operational and financial risk using a multi-factor **Risk Classifier (Core Contribution)**, and safely executes remediations with pre-action snapshots, dry-run simulation, state verification, and automated rollback.

---

## Architecture: The 7 Pipeline Layers

Data flows down from connected cloud accounts, through detection and risk decisions, to execution and verification:

```
+-------------------------------------------------------------------------+
|                  1. Dashboard & Backend API (FastAPI)                   |
|      (React SPA + Integrated HTML Dashboard + Swagger API Docs)        |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                  2. Collection Layer (Connectors)                       |
|   (Adapter Pattern: AWS boto3, Azure SDK, GCP SDK, Demo Simulator)      |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                         3. Normalizer Layer                             |
| (Universal Schema: Provider, Resource ID, Type, CPU/Mem, Cost, State)   |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                         4. Detection Layer                              |
|   - Rule Engine: Idle VMs (<10% CPU), Unattached Volumes, Off-Hours Dev |
|   - ML Anomaly Detector: Isolation Forest for sudden cost spikes        |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|              5. Risk Classifier (Core Contribution)                     |
|  (Environment Tag + Dependency/Topology + Action Impact + Confidence)   |
|            |                                             |              |
|   [Score < 35: LOW RISK]                      [Score >= 35: MED / HIGH] |
|            |                                             |              |
|    Auto-Remediation Queue                     Human Approval Queue      |
+------------+---------------------------------------------+--------------+
             |                                             |
+------------v---------------------------------------------v--------------+
|                   6. Executor, Verifier & Rollback                      |
|   - Dry-Run Simulation Mode                                             |
|   - Safety Pre-Action Snapshots (EBS / Azure Disk / GCP PD)             |
|   - State Verification against Cloud Provider API                       |
|   - Automated Rollback / Snapshot Restoration on Failure                |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                     7. Database (PostgreSQL / SQLite)                   |
|   - accounts, resources, findings, remediation_actions, approvals,     |
|     savings_history, audit_log                                          |
+-------------------------------------------------------------------------+
```

---

## Key Features & Layers Breakdown

### Layer 1: Dashboard and Backend API
- **FastAPI Backend**: Clean modular architecture with REST endpoints for accounts, findings, approvals, remediations, savings analytics, and audit logs.
- **Dual Presentation**:
  - **Embedded Dashboard**: Served directly from FastAPI at `http://localhost:8000/` with interactive Chart.js visualizations, live risk simulator, and one-click demo controls.
  - **React SPA**: Modern React + Tailwind CSS client in `frontend/`.
- **Scan Scheduler**: Embedded background scheduler (`APScheduler`) triggering periodic multi-cloud scans every few hours.

### Layer 2: Collection Layer (Adapter Pattern)
- Unified abstract interface (`CloudConnectorBase`):
  - `AWSConnector` using `boto3` (EC2, EBS, RDS, CloudWatch, Cost Explorer).
  - `AzureConnector` using Azure SDK (Compute, Monitor, Cost Management).
  - `GCPConnector` using Google Cloud SDK (Compute, Monitoring, Billing).
  - `MockMultiCloudConnector`: High-fidelity synthetic cloud provider simulating multi-cloud fleets, metrics, snapshots, and spend spikes for zero-cost demonstrations.
- **Read-only by default**: Operates under least-privilege IAM policies.

### Layer 3: Normalizer
Standardizes disparate vendor-specific outputs into a unified `NormalizedResource` model:
- `provider` (aws, azure, gcp)
- `resource_id`, `name`, `resource_type` (compute_instance, block_storage, ip_address)
- `region`, `environment_tag` (production, staging, dev, sandbox)
- `average_cpu` (7-day CloudWatch/Monitor average), `average_memory`
- `monthly_cost` ($ USD)
- `state` (running, stopped, unattached, unassociated)

### Layer 4: Detection Layer
- **Rule Engine**:
  1. *Unattached Storage Volumes*: Disks in available/unattached state with no mounted host.
  2. *Unused Elastic IPs*: Public IPs unassociated with active network interfaces.
  3. *Idle Instances*: Compute instances averaging `< 10% CPU` over 7 consecutive days.
  4. *Off-Hours Non-Production*: Dev/Staging instances running 24/7 without shutoff schedules (~65% monthly savings).
- **ML Anomaly Detector (`IsolationForest`)**:
  - Analyzes 30-day cost time-series to detect sudden cost spikes and multi-variate resource anomalies that fixed thresholds miss.
- Every finding outputs a **plain-language reason** and **estimated monthly savings**.

### Layer 5: Risk Classifier (Core Contribution)
Evaluates operational blast radius and business risk before any action is executed:

$$\text{Risk Score} = \min(100, \, \text{Env Impact} + \text{Topology} + \text{Action Impact} + \text{Confidence})$$

- **Environment Tag** (Weight: 40%): Production/Critical (+45 pts) vs Staging (+20 pts) vs Dev (+5 pts).
- **Topology Dependencies** (Weight: 30%): Behind Load Balancer (+35 pts) vs Active Mounts (+25 pts) vs Standalone (0 pts).
- **Action Impact** (Weight: 20%): Delete Volume (+20 pts) vs Stop Instance (+15 pts) vs IP Release (+5 pts).
- **Detection Confidence** (Weight: 10%): High confidence (-5 pts) vs Boundary metric (+10 pts).

**Routing Decision**:
- `LOW RISK (Score < 35)`: Eligible for automated remediation without manual intervention.
- `MEDIUM RISK (35 - 69)`: Routed to **Human Approval Queue**.
- `HIGH RISK (>= 70)`: Routed to **Approval Queue with Critical Warning** and mandatory pre-action snapshot.

### Layer 6: Executor, Verifier & Rollback
- **Dry-Run Mode**: Simulates API execution and logs predicted state changes.
- **Pre-Action Safety Snapshot**: Creates an immutable snapshot before any deletion or state change.
- **Verifier Engine**: Queries cloud provider API post-execution to confirm resource reached expected state.
- **Automated Rollback Engine**: If verification fails or user requests rollback, automatically restores volume from snapshot or restarts instance.
- **State Machine**: `pending` &rarr; `approved` &rarr; `executing` &rarr; `executed` &rarr; `verified` (or `rolled_back` / `failed`).

### Layer 7: Database (PostgreSQL / SQLite)
- Tables: `accounts`, `resources`, `findings`, `remediation_actions`, `approvals`, `savings_history`, `audit_log`.

---

## Design Principles to Highlight to Your Guide

1. **Read-Only by Default**: Connectors query read-only telemetry and require explicit privileges for execution.
2. **Nothing Risky Runs Without Human Approval**: Production systems and load-balanced resources are strictly routed to the approval queue.
3. **Defense-in-Depth Safety**: Every destructive action takes an immutable pre-action snapshot first, with verified rollback capability.
4. **Idempotent Operations**: All execution commands are idempotent and safe to re-run.
5. **Auditable Governance**: Every detection, decision, approval, and execution step is recorded in an immutable audit table.

---

## Quickstart & Local Execution

### Option 1: Turnkey Single-Command Run (Zero Configuration)

CloudOptima defaults to SQLite and Demo Mode out of the box:

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Run the platform
python run.py
```

Open your browser:
- **Interactive Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Docker Compose (Full Production Stack)

```bash
docker compose up --build
```
This launches PostgreSQL 16, Redis 7, FastAPI backend, and React frontend.

---

## Running the Automated Test Suite

Run pytest across all 7 layers:

```bash
cd backend
pytest tests/ -v
```

Verified test coverage includes:
- Multi-cloud connectors (AWS, Azure, GCP, Mock)
- Normalizer schema transformation
- Rule engine (4 waste scenarios)
- Isolation Forest ML cost spike anomaly detector
- Multi-factor Risk Classifier routing
- Executor snapshotting, verifier, and rollback restoration
- End-to-end API pipeline

---

## Live Presentation Guide for Your Project Guide

When presenting CloudOptima to your guide or evaluation committee, follow this recommended walkthrough:

1. **Show the Dashboard Overview (`/`)**: Point out the KPI cards: Total Potential Monthly Waste, Confirmed Realized Savings, and Open Findings by Risk Level.
2. **Explain the Normalizer (Layer 3)**: Explain that AWS, Azure, and GCP name things differently, but CloudOptima normalizes all compute, storage, and networking into a single unified format.
3. **Show Waste Detection (Layer 4)**:
   - Heuristic rules catching unattached EBS/Managed disks, unused Elastic IPs, and idle instances (<10% CPU).
   - **Isolation Forest ML**: Show the cost spike anomaly detected by scikit-learn without static threshold rules.
4. **Demonstrate Your Core Contribution - Risk Classifier (Layer 5)**:
   - Navigate to the **Risk Classifier Sandbox** tab in the dashboard.
   - Show how moving the environment from *Development* to *Production* increases the risk score from 20 to 65+, automatically shifting the routing decision from *Auto-Remediate* to *Human Approval Queue*.
   - Toggle the *Load Balancer* attachment switch to demonstrate blast radius awareness.
5. **Demonstrate Safety & Rollback (Layer 6)**:
   - Go to the **Approval Queue** tab.
   - Click **Approve & Execute (with Snapshot)** on a pending item.
   - Switch to the **Remediation History** tab: show the generated `snapshot_id`, the transition to `verified`, and the increase in realized savings!
   - Click **Restore / Rollback** to prove that the resource can be restored from the pre-action snapshot in real time.
6. **Show Audit Trail (Layer 7)**: Show that every single action, decision, and snapshot is immutably logged with timestamps and actor identities.
