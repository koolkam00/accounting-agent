import json

from sqlalchemy import select

from app.audit import AuditLog
from app.database import AuditEventRow, init_db


def test_audit_log_in_memory_path():
    audit = AuditLog()
    audit.emit("started", {"z": 1, "a": 2}, case_id="case-1", workflow_run_id=3)
    assert audit.events == [
        {
            "event_type": "started",
            "case_id": "case-1",
            "workflow_run_id": 3,
            "detail": {"z": 1, "a": 2},
        }
    ]


def test_audit_log_persists_sorted_json(tmp_path):
    sf = init_db(f"sqlite:///{tmp_path / 'audit.db'}")
    audit = AuditLog(session_factory=sf)
    audit.emit("validated", {"z": 1, "a": 2}, case_id="case-2")

    with sf() as session:
        rows = session.scalars(select(AuditEventRow)).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.event_type == "validated"
        assert row.case_id == "case-2"
        assert row.workflow_run_id is None
        assert row.detail_json == '{"a": 2, "z": 1}'
        assert json.loads(row.detail_json) == {"a": 2, "z": 1}
