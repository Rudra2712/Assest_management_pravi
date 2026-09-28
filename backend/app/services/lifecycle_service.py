from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import LifecycleStatus as S
from app.models.lifecycle import LifecycleEvent
from app.models.user import User
from app.utils.audit import record_audit

ALLOWED_TRANSITIONS: dict[S, set[S]] = {
    S.PLANNED: {S.SANCTIONED},
    S.SANCTIONED: {S.UNDER_CONSTRUCTION},
    S.UNDER_CONSTRUCTION: {S.COMMISSIONED},
    S.COMMISSIONED: {S.OPERATIONAL},
    S.OPERATIONAL: {S.INSPECTION_REQUIRED, S.MAINTENANCE_REQUIRED, S.RENOVATION_UPGRADATION, S.RETIRED},
    S.INSPECTION_REQUIRED: {S.OPERATIONAL, S.MAINTENANCE_REQUIRED},
    S.MAINTENANCE_REQUIRED: {S.UNDER_MAINTENANCE},
    S.UNDER_MAINTENANCE: {S.OPERATIONAL},
    S.RENOVATION_UPGRADATION: {S.OPERATIONAL},
    S.RETIRED: {S.DECOMMISSIONED},
    S.DECOMMISSIONED: set(),
}


class InvalidLifecycleTransition(Exception):
    def __init__(self, current: S, requested: S):
        allowed = sorted(s.value for s in ALLOWED_TRANSITIONS.get(current, set()))
        super().__init__(
            f"Cannot transition asset from {current.value} to {requested.value}. "
            f"Allowed next states: {allowed or 'none (terminal state)'}"
        )


def transition_asset(db: Session, asset: Asset, new_status: S, user: User, reason: str | None) -> LifecycleEvent:
    current = asset.lifecycle_status
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidLifecycleTransition(current, new_status)

    event = LifecycleEvent(
        asset_id=asset.id,
        old_status=current,
        new_status=new_status,
        changed_by=user.id,
        reason=reason,
    )
    db.add(event)

    old_status_value = current.value
    asset.lifecycle_status = new_status
    asset.updated_by = user.id

    record_audit(
        db,
        actor_id=user.id,
        action="LIFECYCLE_TRANSITION",
        entity_type="asset",
        entity_id=asset.id,
        old_value={"lifecycle_status": old_status_value},
        new_value={"lifecycle_status": new_status.value, "reason": reason},
    )
    return event
