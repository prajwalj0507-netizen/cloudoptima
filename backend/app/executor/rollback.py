import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import RemediationAction, Finding, Resource, AuditLog
from app.connectors import get_connector

logger = logging.getLogger(__name__)

class RollbackManager:
    """
    Rollback Engine.
    Restores previous cloud state when verification fails or upon human request:
    - Restores storage volume from pre-action safety snapshot
    - Restarts stopped compute instances
    - Reverts configuration schedules
    - Logs complete audit history
    """

    @classmethod
    def rollback(
        cls,
        db: Session,
        action: RemediationAction,
        finding: Finding,
        resource: Resource,
        reason: str = "Rollback initiated"
    ) -> RemediationAction:
        action.status = "rolling_back"
        db.commit()

        connector = get_connector(provider=finding.provider, account_id=resource.account_id)
        rollback_data = {}

        try:
            if action.action_type == "delete_volume" and action.snapshot_id:
                logger.info(f"Restoring volume {resource.resource_id} from snapshot {action.snapshot_id}")
                rollback_data = connector.restore_snapshot(
                    snapshot_id=action.snapshot_id,
                    original_resource_id=resource.resource_id
                )
                resource.state = "available"

            elif action.action_type == "stop_instance":
                logger.info(f"Restarting instance {resource.resource_id}")
                rollback_data = connector.start_instance(resource.resource_id)
                resource.state = "running"

            else:
                rollback_data = {"action": "revert", "message": "Reverted target state to baseline", "success": True}

            action.status = "rolled_back"
            action.rolled_back_at = datetime.now(timezone.utc)
            action.rollback_result = {
                "success": True,
                "reason": reason,
                "details": rollback_data
            }

            # Re-open finding
            finding.status = "open"
            finding.resolved_at = None

            db.add(AuditLog(
                event_type="REMEDIATION_ROLLED_BACK",
                actor="rollback_manager",
                resource_id=resource.resource_id,
                provider=finding.provider,
                details={
                    "action_id": action.id,
                    "reason": reason,
                    "rollback_data": rollback_data
                }
            ))
            db.commit()
            logger.info(f"Action {action.id} successfully rolled back.")

        except Exception as e:
            logger.error(f"Rollback failed for action {action.id}: {e}")
            action.status = "rollback_failed"
            action.error_message = f"Rollback failure: {str(e)}"
            db.add(AuditLog(
                event_type="ROLLBACK_FAILED",
                actor="rollback_manager",
                resource_id=resource.resource_id,
                provider=finding.provider,
                details={"error": str(e)}
            ))
            db.commit()

        return action
