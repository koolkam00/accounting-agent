"""Audit event helpers."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session, sessionmaker

from app.database import AuditEventRow


class AuditLog:
    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None) -> None:
        self._sf = session_factory
        self.events: list[dict[str, Any]] = []

    def emit(
        self,
        event_type: str,
        detail: Optional[dict[str, Any]] = None,
        *,
        case_id: Optional[str] = None,
        workflow_run_id: Optional[int] = None,
    ) -> None:
        payload = detail or {}
        record = {
            "event_type": event_type,
            "case_id": case_id,
            "workflow_run_id": workflow_run_id,
            "detail": payload,
        }
        self.events.append(record)
        if self._sf is not None:
            with self._sf() as session:
                session.add(
                    AuditEventRow(
                        workflow_run_id=workflow_run_id,
                        case_id=case_id,
                        event_type=event_type,
                        detail_json=json.dumps(payload, sort_keys=True),
                    )
                )
                session.commit()
