import uuid
from types import SimpleNamespace

import pytest

from app.models.enums import LifecycleStatus
from app.services.lifecycle_service import ALLOWED_TRANSITIONS, InvalidLifecycleTransition, transition_asset


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def make_asset(status: LifecycleStatus):
    return SimpleNamespace(id=uuid.uuid4(), lifecycle_status=status, updated_by=None)


def make_user():
    return SimpleNamespace(id=uuid.uuid4())


def test_valid_transition_updates_status_and_logs_event():
    db = FakeSession()
    asset = make_asset(LifecycleStatus.PLANNED)
    user = make_user()

    event = transition_asset(db, asset, LifecycleStatus.SANCTIONED, user, "Sanction order issued")

    assert asset.lifecycle_status == LifecycleStatus.SANCTIONED
    assert event.old_status == LifecycleStatus.PLANNED
    assert event.new_status == LifecycleStatus.SANCTIONED
    assert event in db.added


def test_invalid_transition_is_rejected_and_status_unchanged():
    db = FakeSession()
    asset = make_asset(LifecycleStatus.PLANNED)
    user = make_user()

    with pytest.raises(InvalidLifecycleTransition):
        transition_asset(db, asset, LifecycleStatus.OPERATIONAL, user, None)

    assert asset.lifecycle_status == LifecycleStatus.PLANNED


def test_decommissioned_is_terminal():
    assert ALLOWED_TRANSITIONS[LifecycleStatus.DECOMMISSIONED] == set()


def test_every_non_terminal_status_has_at_least_one_allowed_transition():
    for status, allowed in ALLOWED_TRANSITIONS.items():
        if status is LifecycleStatus.DECOMMISSIONED:
            continue
        assert allowed, f"{status} should allow at least one transition"
