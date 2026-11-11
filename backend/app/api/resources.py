from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.models import Resource
from app.schemas import ResourceOut
from app.config import settings

router = APIRouter(prefix="/resources", tags=["Resource Inventory & Data Usage Telemetry"])

@router.get("", response_model=List[ResourceOut])
def list_resources(
    provider: Optional[str] = None,
    resource_type: Optional[str] = None,
    environment: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Returns inventory of normalized multi-cloud resources across AWS, Azure, and GCP
    with hardware specifications and data usage metrics.
    """
    query = db.query(Resource)

    if provider:
        query = query.filter(Resource.provider == provider.lower())
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type.lower())
    if environment:
        query = query.filter(Resource.environment_tag == environment.lower())
    if state:
        query = query.filter(Resource.state == state.lower())
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (Resource.name.ilike(s)) |
            (Resource.resource_id.ilike(s)) |
            (Resource.region.ilike(s))
        )

    return query.order_by(Resource.monthly_cost.desc()).offset(skip).limit(limit).all()


@router.get("/telemetry")
@router.get("/telemetry/")
@router.get("/telemetry/summary")
def get_resource_telemetry_summary(db: Session = Depends(get_db)):
    """
    Calculates aggregated telemetry for compute capacity, storage usage,
    and network data transfer bandwidth across all active cloud accounts.
    """
    resources = db.query(Resource).all()

    total_resources = len(resources)
    compute_count = 0
    storage_count = 0
    ip_count = 0

    total_vcpus = 0
    total_memory_gb = 0.0
    total_storage_prov_gb = 0.0
    total_storage_used_gb = 0.0
    total_network_in_gb = 0.0
    total_network_out_gb = 0.0
    total_data_transfer_gb = 0.0

    cpu_samples = []
    mem_samples = []
    total_monthly_cost = 0.0

    by_provider: Dict[str, Dict[str, Any]] = {
        "aws": {"count": 0, "storage_gb": 0.0, "data_transfer_gb": 0.0, "monthly_cost": 0.0},
        "azure": {"count": 0, "storage_gb": 0.0, "data_transfer_gb": 0.0, "monthly_cost": 0.0},
        "gcp": {"count": 0, "storage_gb": 0.0, "data_transfer_gb": 0.0, "monthly_cost": 0.0}
    }

    for r in resources:
        total_monthly_cost += (r.monthly_cost or 0.0)
        prov = (r.provider or "").lower()
        if prov in by_provider:
            by_provider[prov]["count"] += 1
            by_provider[prov]["monthly_cost"] += (r.monthly_cost or 0.0)

        meta = r.extra_metadata or {}

        if r.resource_type == "compute_instance":
            compute_count += 1
            vcpus = meta.get("vcpus", 4)
            ram = meta.get("memory_gb", 16.0)
            net_in = meta.get("network_in_gb", 0.0)
            net_out = meta.get("network_out_gb", 0.0)
            dt = meta.get("data_transfer_gb", net_in + net_out)

            total_vcpus += int(vcpus)
            total_memory_gb += float(ram)
            total_network_in_gb += float(net_in)
            total_network_out_gb += float(net_out)
            total_data_transfer_gb += float(dt)

            if prov in by_provider:
                by_provider[prov]["data_transfer_gb"] += float(dt)

            if r.state == "running":
                if r.average_cpu is not None:
                    cpu_samples.append(r.average_cpu)
                if r.average_memory is not None:
                    mem_samples.append(r.average_memory)

        elif r.resource_type == "block_storage":
            storage_count += 1
            size_gb = float(meta.get("size_gb", 0.0))
            used_gb = float(meta.get("storage_used_gb", 0.0))

            total_storage_prov_gb += size_gb
            total_storage_used_gb += used_gb

            if prov in by_provider:
                by_provider[prov]["storage_gb"] += size_gb

        elif r.resource_type == "ip_address":
            ip_count += 1
            dt = float(meta.get("data_transferred_gb", 0.0))
            total_data_transfer_gb += dt
            if prov in by_provider:
                by_provider[prov]["data_transfer_gb"] += dt

    avg_cpu = round(sum(cpu_samples) / len(cpu_samples), 1) if cpu_samples else 0.0
    avg_mem = round(sum(mem_samples) / len(mem_samples), 1) if mem_samples else 0.0
    storage_util = round((total_storage_used_gb / total_storage_prov_gb * 100.0), 1) if total_storage_prov_gb > 0 else 0.0

    # Format provider breakdowns
    for p in by_provider:
        by_provider[p]["storage_gb"] = round(by_provider[p]["storage_gb"], 1)
        by_provider[p]["data_transfer_gb"] = round(by_provider[p]["data_transfer_gb"], 1)
        by_provider[p]["monthly_cost"] = round(by_provider[p]["monthly_cost"], 2)

    return {
        "total_resources": total_resources,
        "compute_instances_count": compute_count,
        "storage_volumes_count": storage_count,
        "ip_addresses_count": ip_count,
        "total_vcpus": total_vcpus,
        "total_memory_gb": round(total_memory_gb, 1),
        "total_ram_gb": round(total_memory_gb, 1),
        "total_storage_provisioned_gb": round(total_storage_prov_gb, 1),
        "total_storage_used_gb": round(total_storage_used_gb, 1),
        "storage_utilization_pct": storage_util,
        "total_network_in_gb": round(total_network_in_gb, 1),
        "total_network_ingress_gb": round(total_network_in_gb, 1),
        "total_network_out_gb": round(total_network_out_gb, 1),
        "total_network_egress_gb": round(total_network_out_gb, 1),
        "total_data_transfer_gb": round(total_data_transfer_gb, 1),
        "avg_cpu_pct": avg_cpu,
        "fleet_avg_cpu": avg_cpu,
        "avg_memory_pct": avg_mem,
        "fleet_avg_memory": avg_mem,
        "total_monthly_cost": round(total_monthly_cost, 2),
        "currency": settings.CURRENCY,
        "currency_symbol": settings.CURRENCY_SYMBOL,
        "by_provider": by_provider
    }
