import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class MLAnomalyDetector:
    """
    Machine Learning Anomaly Detector using Isolation Forest.
    Detects what static threshold rules miss:
    - Sudden cost spikes
    - Abnormal spend surges across billing time-series
    - Multi-dimensional utilization shifts
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )

    def detect_cost_spikes(
        self,
        cost_history: List[Dict[str, Any]],
        provider: str,
        account_id: str
    ) -> List[Dict[str, Any]]:
        """
        Analyzes 30-day daily cost time series using Isolation Forest.
        Flags cost anomalies where spend abruptly deviates from baseline.
        """
        findings = []
        if len(cost_history) < 7:
            logger.info("Insufficient cost history data for ML anomaly detection (need at least 7 days).")
            return findings

        # Extract costs
        costs = np.array([point.get("cost", 0.0) for point in cost_history]).reshape(-1, 1)
        
        try:
            # Fit Isolation Forest on the cost distribution
            self.model.fit(costs)
            predictions = self.model.predict(costs) # -1 for anomaly, 1 for normal
            scores = self.model.decision_function(costs) # lower score = more anomalous

            # Baseline calculation (median of normal points)
            normal_costs = costs[predictions == 1]
            baseline_cost = float(np.median(normal_costs)) if len(normal_costs) > 0 else float(np.median(costs))

            # Look for recent anomalies (in the most recent 5 days)
            recent_window = min(5, len(cost_history))
            for i in range(len(cost_history) - recent_window, len(cost_history)):
                if predictions[i] == -1 and costs[i][0] > baseline_cost * 1.5:
                    point = cost_history[i]
                    date_str = point.get("date")
                    actual_cost = float(costs[i][0])
                    surge_diff = actual_cost - baseline_cost
                    pct_increase = round((surge_diff / max(baseline_cost, 0.01)) * 100, 1)
                    
                    # Estimate monthly waste if this unmitigated spike continues
                    est_monthly_waste = round(surge_diff * 30, 2)

                    findings.append({
                        "resource_id": f"spend-anomaly-{provider}-{date_str}",
                        "provider": provider,
                        "detector_type": "ml_anomaly",
                        "category": "cost_spike",
                        "reason": (
                            f"Isolation Forest ML detected an abnormal cost spike of ₹{actual_cost:.2f}/day on {date_str} "
                            f"(+{pct_increase}% vs ₹{baseline_cost:.2f}/day baseline, anomaly score {scores[i]:.2f})."
                        ),
                        "recommended_action": "investigate_cost_spike",
                        "estimated_monthly_saving": est_monthly_waste,
                        "raw_resource": {
                            "resource_id": f"spend-anomaly-{provider}-{date_str}",
                            "provider": provider,
                            "resource_type": "cost_anomaly",
                            "environment_tag": "production",
                            "monthly_cost": est_monthly_waste,
                            "average_cpu": 0.0,
                            "average_memory": 0.0,
                            "state": "active",
                            "extra_metadata": {
                                "date": date_str,
                                "baseline_cost": baseline_cost,
                                "anomaly_score": float(scores[i]),
                                "surge_diff": surge_diff
                            }
                        }
                    })
        except Exception as e:
            logger.error(f"Error during ML cost spike detection: {e}")

        return findings

    def detect_multivariate_resource_anomalies(
        self,
        resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Multivariate anomaly detection across CPU, Memory, and Cost feature vector.
        Flags high-cost low-utilization outliers.
        """
        findings = []
        compute_resources = [r for r in resources if r.get("resource_type") == "compute_instance"]
        if len(compute_resources) < 4:
            return findings

        # Feature matrix: [CPU, Memory, Monthly Cost]
        features = []
        for r in compute_resources:
            features.append([
                float(r.get("average_cpu", 0.0)),
                float(r.get("average_memory", 0.0)),
                float(r.get("monthly_cost", 0.0))
            ])
        X = np.array(features)

        try:
            iso = IsolationForest(contamination=0.15, random_state=self.random_state)
            preds = iso.fit_predict(X)
            scores = iso.decision_function(X)

            for i, pred in enumerate(preds):
                r = compute_resources[i]
                cpu = X[i][0]
                cost = X[i][2]
                # If anomalous with high cost and low/moderate cpu
                if pred == -1 and cost > 100.0 and cpu < 25.0:
                    est_savings = round(cost * 0.70, 2)
                    findings.append({
                        "resource_id": r.get("resource_id"),
                        "provider": r.get("provider"),
                        "detector_type": "ml_anomaly",
                        "category": "multivariate_waste",
                        "reason": (
                            f"Isolation Forest identified '{r.get('name')}' as an operational outlier: "
                            f"incurring high spend (₹{cost:.2f}/mo) with disproportionately low activity "
                            f"(CPU: {cpu:.1f}%, anomaly score {scores[i]:.2f})."
                        ),
                        "recommended_action": "stop_instance",
                        "estimated_monthly_saving": est_savings,
                        "raw_resource": r
                    })
        except Exception as e:
            logger.error(f"Multivariate ML anomaly error: {e}")

        return findings
