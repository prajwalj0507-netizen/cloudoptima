import os
import pytest
from app.datasets import FocusDatasetLoader, AzureTraceLoader, FinOpsBenchmarkEvaluator

def test_7_layer_web_pages_exist():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static")
    for layer_num in range(1, 8):
        f = os.path.join(static_dir, f"layer{layer_num}.html")
        assert os.path.exists(f), f"Layer {layer_num} file missing: {f}"
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
            assert f"Layer {layer_num}" in content

def test_focus_dataset_loader():
    summary = FocusDatasetLoader.get_summary_stats()
    assert summary["specification"] == "FOCUS 1.0 (FinOps Open Cost and Usage Specification)"
    assert summary["total_line_items"] > 0
    assert summary["exchange_rate"] == 85.0
    assert summary["synthetic_leaks_injected"] > 0

    records = FocusDatasetLoader.get_focus_records()
    assert len(records) > 0
    providers = set(r["ProviderName"] for r in records)
    assert "AWS" in providers
    assert "Azure" in providers
    assert "Google Cloud" in providers

def test_azure_traces():
    traces = AzureTraceLoader.get_vm_traces("vm-batch-indexer-stg", hours=24)
    assert len(traces) == 288 # 24 hours * 12 readings/hour (5-min intervals)
    assert "avg_cpu" in traces[0]
    assert "p95_cpu" in traces[0]

    fleet = AzureTraceLoader.get_fleet_trace_summary()
    assert len(fleet["vms"]) >= 3
    assert any(v["is_classified_idle"] for v in fleet["vms"])

def test_benchmark_metrics():
    benchmark = FinOpsBenchmarkEvaluator.evaluate_benchmark()
    summary = benchmark["summary"]
    assert summary["precision_pct"] >= 90.0
    assert summary["recall_pct"] >= 90.0
    assert summary["f1_score_pct"] >= 90.0
    assert len(benchmark["workload_evaluations"]) > 0
