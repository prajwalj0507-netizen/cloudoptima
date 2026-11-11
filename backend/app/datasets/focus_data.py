"""
FOCUS (FinOps Open Cost and Usage Specification) Dataset Generator & Loader
Implements the official FOCUS 1.0 schema for multi-cloud billing:
- ProviderName: AWS, Azure, Google Cloud
- ChargePeriodStart, ChargePeriodEnd
- BilledCost, EffectiveCost, BillingCurrency
- ChargeCategory, ChargeSubcategory
- ResourceId, ResourceName, ResourceType, RegionId, SubAccountId
- Tags (Environment, Owner, Application)
- Synthetic Leak Injection & Ground Truth Labels for Precision/Recall benchmark
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

class FocusDatasetLoader:
    """
    Loads and serves multi-cloud billing records compliant with FOCUS 1.0 specification.
    Includes ground-truth synthetic leakage labels for empirical FinOps validation.
    """

    @classmethod
    def get_focus_records(cls) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        start_str = yesterday.strftime("%Y-%m-%dT00:00:00Z")
        end_str = now.strftime("%Y-%m-%dT00:00:00Z")

        records = [
            # -------------------------------------------------------------
            # AWS (Amazon Web Services) FOCUS 1.0 Records
            # -------------------------------------------------------------
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "AWS",
                "SubAccountId": "aws-prod-01239",
                "SubAccountName": "AWS Production & Analytics",
                "RegionId": "ap-south-1",
                "RegionName": "Asia Pacific (Mumbai)",
                "ResourceId": "i-0a8174fbcd738",
                "ResourceName": "analytics-batch-worker-dev",
                "ResourceType": "compute_instance",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 248.00,
                "EffectiveCost": 248.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "dev", "Team": "DataEng", "Workload": "ETL"},
                "Telemetry": {
                    "vcpus": 4,
                    "memory_gb": 16.0,
                    "average_cpu": 3.4, # Idle < 10%
                    "average_memory": 12.0,
                    "network_out_gb": 147.0,
                    "schedule_tag": None
                },
                # Synthetic Benchmark Ground Truth
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "idle_instance",
                "ground_truth_remediation": "stop_instance"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "AWS",
                "SubAccountId": "aws-prod-01239",
                "SubAccountName": "AWS Production & Analytics",
                "RegionId": "ap-south-1",
                "RegionName": "Asia Pacific (Mumbai)",
                "ResourceId": "i-091fb72ca410b",
                "ResourceName": "prod-auth-api-gateway",
                "ResourceType": "compute_instance",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 280.00,
                "EffectiveCost": 280.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "production", "Team": "SecOps", "App": "Auth"},
                "Telemetry": {
                    "vcpus": 8,
                    "memory_gb": 32.0,
                    "average_cpu": 6.8, # Low CPU, but prod + behind load balancer
                    "average_memory": 45.0,
                    "network_out_gb": 825.5,
                    "is_behind_load_balancer": True
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "idle_instance",
                "ground_truth_remediation": "stop_instance"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "AWS",
                "SubAccountId": "aws-prod-01239",
                "SubAccountName": "AWS Production & Analytics",
                "RegionId": "ap-south-1",
                "RegionName": "Asia Pacific (Mumbai)",
                "ResourceId": "vol-0941bc4e27f10",
                "ResourceName": "ebs-dev-scratch-volume",
                "ResourceType": "block_storage",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 50.00,
                "EffectiveCost": 50.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 500.0,
                "UsageUnit": "GB-Month",
                "PricingQuantity": 1.0,
                "PricingUnit": "GB-Month",
                "Tags": {"Environment": "dev", "Project": "Scratch"},
                "Telemetry": {
                    "size_gb": 500,
                    "storage_used_gb": 45,
                    "storage_utilization_pct": 9.0,
                    "is_attached": False, # Unattached volume leak
                    "iops": 0
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "unattached_volume",
                "ground_truth_remediation": "delete_volume"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "AWS",
                "SubAccountId": "aws-prod-01239",
                "SubAccountName": "AWS Production & Analytics",
                "RegionId": "ap-south-1",
                "RegionName": "Asia Pacific (Mumbai)",
                "ResourceId": "vol-0182a4d9ef332",
                "ResourceName": "prod-mysql-primary-ebs",
                "ResourceType": "block_storage",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 120.00,
                "EffectiveCost": 120.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 1000.0,
                "UsageUnit": "GB-Month",
                "PricingQuantity": 1.0,
                "PricingUnit": "GB-Month",
                "Tags": {"Environment": "production", "Role": "Database"},
                "Telemetry": {
                    "size_gb": 1000,
                    "storage_used_gb": 850,
                    "storage_utilization_pct": 85.0,
                    "is_attached": True,
                    "iops": 3200
                },
                "is_synthetic_leak": False,
                "ground_truth_leak_type": None,
                "ground_truth_remediation": None
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "AWS",
                "SubAccountId": "aws-prod-01239",
                "SubAccountName": "AWS Production & Analytics",
                "RegionId": "ap-south-1",
                "RegionName": "Asia Pacific (Mumbai)",
                "ResourceId": "eipalloc-01783abf32",
                "ResourceName": "elastic-ip-unassociated-dev",
                "ResourceType": "ip_address",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 4.50,
                "EffectiveCost": 4.50,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "dev"},
                "Telemetry": {
                    "ip_address": "13.235.42.19",
                    "is_associated": False, # Idle IP reservation penalty
                    "data_transfer_gb": 0.0
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "unused_ip",
                "ground_truth_remediation": "release_ip"
            },

            # -------------------------------------------------------------
            # Azure (Microsoft Azure) FOCUS 1.0 Records
            # -------------------------------------------------------------
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "Azure",
                "SubAccountId": "azure-sub-corp-981",
                "SubAccountName": "Azure Enterprise Staging",
                "RegionId": "centralindia",
                "RegionName": "Central India (Pune)",
                "ResourceId": "vm-batch-indexer-stg",
                "ResourceName": "vm-batch-indexer-stg",
                "ResourceType": "compute_instance",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 145.00,
                "EffectiveCost": 145.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "staging", "Tier": "Middle"},
                "Telemetry": {
                    "vcpus": 4,
                    "memory_gb": 16.0,
                    "average_cpu": 7.2, # Idle < 10% on staging
                    "average_memory": 18.5,
                    "network_out_gb": 112.0,
                    "schedule_tag": None
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "idle_instance",
                "ground_truth_remediation": "stop_instance"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "Azure",
                "SubAccountId": "azure-sub-corp-981",
                "SubAccountName": "Azure Enterprise Staging",
                "RegionId": "centralindia",
                "RegionName": "Central India (Pune)",
                "ResourceId": "disk-data-stage-backup",
                "ResourceName": "disk-data-stage-backup",
                "ResourceType": "block_storage",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 138.00,
                "EffectiveCost": 138.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 1024.0,
                "UsageUnit": "GB-Month",
                "PricingQuantity": 1.0,
                "PricingUnit": "GB-Month",
                "Tags": {"Environment": "staging", "Owner": "DBA"},
                "Telemetry": {
                    "size_gb": 1024,
                    "storage_used_gb": 420,
                    "storage_utilization_pct": 41.0,
                    "is_attached": False, # Unattached managed disk
                    "iops": 0
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "unattached_volume",
                "ground_truth_remediation": "delete_volume"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "Azure",
                "SubAccountId": "azure-sub-corp-981",
                "SubAccountName": "Azure Enterprise Staging",
                "RegionId": "centralindia",
                "RegionName": "Central India (Pune)",
                "ResourceId": "pip-gateway-idle-01",
                "ResourceName": "pip-gateway-idle-01",
                "ResourceType": "ip_address",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 4.50,
                "EffectiveCost": 4.50,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "staging"},
                "Telemetry": {
                    "ip_address": "20.198.54.112",
                    "is_associated": False,
                    "data_transfer_gb": 0.0
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "unused_ip",
                "ground_truth_remediation": "release_ip"
            },

            # -------------------------------------------------------------
            # GCP (Google Cloud Platform) FOCUS 1.0 Records
            # -------------------------------------------------------------
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "Google Cloud",
                "SubAccountId": "gcp-proj-eng-441",
                "SubAccountName": "GCP Engineering & Data",
                "RegionId": "asia-south1",
                "RegionName": "Mumbai",
                "ResourceId": "gcp-vm-dev-microservices",
                "ResourceName": "gcp-vm-dev-microservices",
                "ResourceType": "compute_instance",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 98.00,
                "EffectiveCost": 98.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "dev", "Team": "Frontend"},
                "Telemetry": {
                    "vcpus": 2,
                    "memory_gb": 8.0,
                    "average_cpu": 14.5,
                    "average_memory": 38.0,
                    "network_out_gb": 89.0,
                    "schedule_tag": None # Dev VM active 24/7 without schedule
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "off_hours_dev",
                "ground_truth_remediation": "schedule_stop"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "Google Cloud",
                "SubAccountId": "gcp-proj-eng-441",
                "SubAccountName": "GCP Engineering & Data",
                "RegionId": "asia-south1",
                "RegionName": "Mumbai",
                "ResourceId": "disk-gcp-ml-scratch",
                "ResourceName": "disk-gcp-ml-scratch",
                "ResourceType": "block_storage",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 42.00,
                "EffectiveCost": 42.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 400.0,
                "UsageUnit": "GB-Month",
                "PricingQuantity": 1.0,
                "PricingUnit": "GB-Month",
                "Tags": {"Environment": "dev", "App": "ModelTrainer"},
                "Telemetry": {
                    "size_gb": 400,
                    "storage_used_gb": 12,
                    "storage_utilization_pct": 3.0,
                    "is_attached": False,
                    "iops": 0
                },
                "is_synthetic_leak": True,
                "ground_truth_leak_type": "unattached_volume",
                "ground_truth_remediation": "delete_volume"
            },
            {
                "ChargePeriodStart": start_str,
                "ChargePeriodEnd": end_str,
                "ProviderName": "Google Cloud",
                "SubAccountId": "gcp-proj-eng-441",
                "SubAccountName": "GCP Engineering & Data",
                "RegionId": "asia-south1",
                "RegionName": "Mumbai",
                "ResourceId": "gcp-k8s-prod-node-01",
                "ResourceName": "gcp-k8s-prod-node-01",
                "ResourceType": "compute_instance",
                "ChargeCategory": "Usage",
                "ChargeSubcategory": "On-Demand",
                "BilledCost": 320.00,
                "EffectiveCost": 320.00,
                "BillingCurrency": "USD",
                "UsageQuantity": 720.0,
                "UsageUnit": "Hours",
                "PricingQuantity": 1.0,
                "PricingUnit": "Hour",
                "Tags": {"Environment": "production", "Role": "Kubernetes"},
                "Telemetry": {
                    "vcpus": 8,
                    "memory_gb": 32.0,
                    "average_cpu": 68.2, # Healthy active node
                    "average_memory": 72.0,
                    "network_out_gb": 1420.0
                },
                "is_synthetic_leak": False,
                "ground_truth_leak_type": None,
                "ground_truth_remediation": None
            }
        ]
        return records

    @classmethod
    def get_summary_stats(cls) -> Dict[str, Any]:
        records = cls.get_focus_records()
        total_billed_usd = sum(r["BilledCost"] for r in records)
        leaks_count = sum(1 for r in records if r.get("is_synthetic_leak"))
        clean_count = len(records) - leaks_count
        providers = set(r["ProviderName"] for r in records)

        return {
            "specification": "FOCUS 1.0 (FinOps Open Cost and Usage Specification)",
            "total_line_items": len(records),
            "providers": list(providers),
            "total_billed_usd": total_billed_usd,
            "total_billed_inr": total_billed_usd * 85.0,
            "synthetic_leaks_injected": leaks_count,
            "normal_workloads": clean_count,
            "currency": "INR (₹)",
            "exchange_rate": 85.0
        }
