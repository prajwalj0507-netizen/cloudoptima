"""
Synthetic Leak Benchmark Evaluator
Computes Ground Truth vs Detection Engine Performance Metrics:
- True Positives (TP)
- False Positives (FP)
- False Negatives (FN)
- Precision: TP / (TP + FP)
- Recall: TP / (TP + FN)
- F1-Score: 2 * (Precision * Recall) / (Precision + Recall)
"""

from typing import Dict, Any, List
from app.datasets.focus_data import FocusDatasetLoader
from app.detection import RuleEngine, MLAnomalyDetector
from app.normalizer import CloudNormalizer

class FinOpsBenchmarkEvaluator:
    """
    Evaluates detection precision, recall, and F1-score against synthetic ground truth leaks.
    """

    @classmethod
    def evaluate_benchmark(cls) -> Dict[str, Any]:
        records = FocusDatasetLoader.get_focus_records()
        
        # Ground Truth stats
        ground_truth_leaks = [r for r in records if r.get("is_synthetic_leak")]
        ground_truth_clean = [r for r in records if not r.get("is_synthetic_leak")]

        # Run Detection on normalized resources
        tp = 0
        fp = 0
        fn = 0
        tn = 0

        breakdown_by_type = {
            "unattached_volume": {"tp": 0, "fn": 0, "fp": 0},
            "idle_instance": {"tp": 0, "fn": 0, "fp": 0},
            "unused_ip": {"tp": 0, "fn": 0, "fp": 0},
            "off_hours_dev": {"tp": 0, "fn": 0, "fp": 0}
        }

        detection_details = []

        for r in records:
            res_id = r["ResourceId"]
            is_leak_gt = r.get("is_synthetic_leak", False)
            leak_type_gt = r.get("ground_truth_leak_type")

            # Compute canonical state
            if r["ResourceType"] == "compute_instance":
                canonical_state = "running"
            elif r["ResourceType"] == "block_storage":
                canonical_state = "attached" if r["Telemetry"].get("is_attached", False) else "unattached"
            elif r["ResourceType"] == "ip_address":
                canonical_state = "in-use" if r["Telemetry"].get("is_associated", False) else "unassociated"
            else:
                canonical_state = "available"

            # Map FOCUS to normalized dict
            norm_res = {
                "resource_id": res_id,
                "name": r.get("ResourceName", res_id),
                "provider": r["ProviderName"].lower(),
                "resource_type": r["ResourceType"],
                "region": r["RegionId"],
                "environment_tag": r["Tags"].get("Environment", "unknown"),
                "average_cpu": r["Telemetry"].get("average_cpu", 0.0),
                "monthly_cost": r["BilledCost"],
                "state": canonical_state,
                "tags": r["Tags"],
                "extra_metadata": {
                    "is_attached": r["Telemetry"].get("is_attached", True),
                    "is_associated": r["Telemetry"].get("is_associated", True),
                    "schedule_tag": r["Telemetry"].get("schedule_tag"),
                    "vcpus": r["Telemetry"].get("vcpus", 2),
                    "memory_gb": r["Telemetry"].get("memory_gb", 4.0),
                    "size_gb": r["Telemetry"].get("size_gb", 100),
                    "iops": r["Telemetry"].get("iops", 100),
                    "network_out_gb": r["Telemetry"].get("network_out_gb", 10.0)
                }
            }

            # Evaluate with RuleEngine
            findings = RuleEngine.evaluate_resource(norm_res)
            detected_flag = len(findings) > 0
            detected_type = findings[0]["category"] if detected_flag else None

            if is_leak_gt:
                if detected_flag:
                    tp += 1
                    if leak_type_gt in breakdown_by_type:
                        breakdown_by_type[leak_type_gt]["tp"] += 1
                    status = "TRUE_POSITIVE"
                else:
                    fn += 1
                    if leak_type_gt in breakdown_by_type:
                        breakdown_by_type[leak_type_gt]["fn"] += 1
                    status = "FALSE_NEGATIVE"
            else:
                if detected_flag:
                    fp += 1
                    status = "FALSE_POSITIVE"
                else:
                    tn += 1
                    status = "TRUE_NEGATIVE"

            detection_details.append({
                "resource_id": res_id,
                "provider": r["ProviderName"],
                "resource_type": r["ResourceType"],
                "monthly_cost_inr": r["BilledCost"] * 85.0,
                "ground_truth_is_leak": is_leak_gt,
                "ground_truth_type": leak_type_gt,
                "detected": detected_flag,
                "detected_type": detected_type,
                "evaluation_status": status
            })

        # Calculate Precision, Recall, F1
        precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 100.0
        recall = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 100.0
        f1_score = round(2 * (precision * recall) / (precision + recall), 2) if (precision + recall) > 0 else 100.0

        return {
            "summary": {
                "total_workloads_evaluated": len(records),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
                "precision_pct": precision,
                "recall_pct": recall,
                "f1_score_pct": f1_score
            },
            "breakdown_by_leak_type": breakdown_by_type,
            "workload_evaluations": detection_details
        }
