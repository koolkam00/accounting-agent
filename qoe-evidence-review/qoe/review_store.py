"""Reviewer decisions: an append-only log and the rules that turn it into final amounts.

The log is JSONL, one ``ReviewDecision`` per line, at
``<workpaper_dir>/review_log.jsonl``. It is never rewritten: the latest line for
an adj id wins, earlier lines stay as the audit trail.

Final-amount semantics (SPEC section 7):

- reviewed, not REQUEST_INFO -> the reviewer's amounts (every period label, missing -> 0.00)
- reviewed REQUEST_INFO      -> {} (pending, excluded from diligence adjusted EBITDA)
- unreviewed                 -> the tool's proposal ({} when the tool said REQUEST_INFO)

``apply_reviews`` rebuilds the bridge with ``qoe.bridge.build_bridge``. The
management schedule is not stored in a ``Workpaper``; callers that have the
deal package pass ``schedule=pkg.schedule``, otherwise the parts of the schedule
the bridge uses are reconstructed from the workpaper itself (see
``schedule_from_workpaper``). That keeps the review path free of file I/O on
the deal package and works for a workpaper whose deal directory has moved.
"""

from __future__ import annotations

import json
import os
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from qoe.money import D, ZERO, fmt, period_map
from qoe.schemas import (
    TOOL_ERROR_CORRECTIONS,
    AdjustmentAssessment,
    AdjustmentClaim,
    CorrectionType,
    ManagementSchedule,
    OpenQuestion,
    QuestionStatus,
    ReviewDecision,
    Treatment,
    Workpaper,
)

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None  # type: ignore[assignment]

REVIEW_LOG_NAME = "review_log.jsonl"
TIMING_LOG_NAME = "timing.jsonl"

STATUS_UNREVIEWED = "Unreviewed"
STATUS_AGREED = "Agreed"
STATUS_OVERRIDDEN = "Overridden"


# ---------------------------------------------------------------------------
# JSONL primitives
# ---------------------------------------------------------------------------


def _append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    line = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+b") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            prefix = b""
            if size:
                fh.seek(size - 1)
                if fh.read(1) != b"\n":
                    # A torn write left a partial last line. Terminate it rather than
                    # truncating, so history is never rewritten and this record parses.
                    prefix = b"\n"
            fh.write(prefix + line + b"\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _read_jsonl_lines(path: Path) -> list[tuple[int, bytes]]:
    """(1-based line number, raw bytes) for every non-blank line."""
    if not path.exists():
        return []
    out: list[tuple[int, bytes]] = []
    for i, chunk in enumerate(path.read_bytes().split(b"\n"), 1):
        if chunk.strip():
            out.append((i, chunk))
    return out


# ---------------------------------------------------------------------------
# Review log
# ---------------------------------------------------------------------------


class ReviewStore:
    """Append-only JSONL log of reviewer decisions."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        # Line numbers that failed to parse on the last read (a torn trailing write,
        # or a hand-edited line). They are skipped, never repaired or removed.
        self.skipped_lines: list[int] = []

    @classmethod
    def for_workpaper_dir(cls, workpaper_dir: Path) -> "ReviewStore":
        return cls(Path(workpaper_dir) / REVIEW_LOG_NAME)

    def append(self, decision: ReviewDecision) -> None:
        _append_jsonl(self.path, decision.model_dump(mode="json"))

    def all(self) -> list[ReviewDecision]:
        """Every decision in log order."""
        skipped: list[int] = []
        out: list[ReviewDecision] = []
        for lineno, raw in _read_jsonl_lines(self.path):
            try:
                out.append(ReviewDecision.model_validate_json(raw))
            except ValueError:  # pydantic ValidationError and UnicodeDecodeError are ValueErrors
                skipped.append(lineno)
        self.skipped_lines = skipped
        return out

    def latest(self) -> dict[str, ReviewDecision]:
        return latest_by_adj(self.all())

    def history(self, adj_id: str) -> list[ReviewDecision]:
        return [d for d in self.all() if d.adj_id == adj_id]


def latest_by_adj(decisions: Iterable[ReviewDecision]) -> dict[str, ReviewDecision]:
    """Latest decision per adj id. Log order decides, not timestamps, so clock skew
    between reviewers cannot resurrect an older decision."""
    out: dict[str, ReviewDecision] = {}
    for d in decisions:
        out[d.adj_id] = d
    return out


def _as_latest(reviews: Mapping[str, ReviewDecision] | Iterable[ReviewDecision]) -> dict[str, ReviewDecision]:
    if isinstance(reviews, Mapping):
        return dict(reviews)
    return latest_by_adj(reviews)


# ---------------------------------------------------------------------------
# Final amounts and bridge rebuild
# ---------------------------------------------------------------------------


def period_labels(wp: Workpaper) -> list[str]:
    return [p.label for p in wp.deal.periods]


def final_amounts(
    wp: Workpaper, reviews: Mapping[str, ReviewDecision] | Iterable[ReviewDecision]
) -> dict[str, dict[str, str]]:
    """adj_id -> period label -> final diligence amount; {} means pending (excluded)."""
    labels = period_labels(wp)
    latest = _as_latest(reviews)
    out: dict[str, dict[str, str]] = {}
    for a in wp.assessments:
        decision = latest.get(a.adj_id)
        if decision is not None:
            out[a.adj_id] = {} if decision.treatment == Treatment.REQUEST_INFO else period_map(decision.amounts, labels)
        elif a.treatment == Treatment.REQUEST_INFO:
            out[a.adj_id] = {}
        else:
            out[a.adj_id] = period_map(a.proposed, labels)
    return out


def schedule_from_workpaper(wp: Workpaper) -> ManagementSchedule:
    """Rebuild the parts of management's schedule the bridge needs from the workpaper.

    Claimed amounts come from the existing ``mgmt:<adj_id>`` bridge rows (what the
    bridge was originally built from) and fall back to ``assessment.claimed``.
    Reported EBITDA comes from the reconciliation. Management's own net income /
    interest / tax / D&A lines are not stored in a workpaper and are left empty;
    the bridge takes those components from the GL.
    """
    labels = period_labels(wp)
    rows = {r.key: r for r in wp.bridge.rows}

    def row_amounts(key: str) -> dict[str, str]:
        row = rows.get(key)
        return period_map(row.amounts, labels) if row is not None else {}

    claims: list[AdjustmentClaim] = []
    for i, a in enumerate(wp.assessments, 1):
        mgmt_row = rows.get(f"mgmt:{a.adj_id}")
        amounts = mgmt_row.amounts if mgmt_row is not None else a.claimed
        claims.append(
            AdjustmentClaim(
                adj_id=a.adj_id,
                title=a.title,
                category=a.category,
                amounts=period_map(amounts, labels),
                source_row=i,
            )
        )
    reported = wp.reconciliation.mgmt_reported_ebitda or row_amounts("mgmt_reported_ebitda")
    return ManagementSchedule(
        source_file="(reconstructed from workpaper)",
        period_labels=labels,
        reported_ebitda=period_map(reported, labels) if reported else {},
        adjustments=claims,
        total_adjustments=row_amounts("mgmt_total"),
        adjusted_ebitda=row_amounts("mgmt_adjusted_ebitda"),
    )


def apply_reviews(
    wp: Workpaper,
    reviews: Iterable[ReviewDecision],
    schedule: Optional[ManagementSchedule] = None,
) -> Workpaper:
    """A new workpaper with ``reviews`` recorded, question updates applied, and the
    bridge rebuilt on final amounts. The input workpaper is not modified.

    ``reviews`` is the full log in order (the Review Log sheet shows every line);
    the latest decision per adj id sets the final amount. Pass the deal package's
    ``schedule`` when available; otherwise it is reconstructed from ``wp``.
    """
    from qoe.bridge import build_bridge  # lazy: the bridge is owned by the engine module

    decisions = list(reviews.values()) if isinstance(reviews, Mapping) else list(reviews)
    out = wp.model_copy(deep=True)
    out.reviews = decisions
    apply_question_updates(out.assessments, decisions)
    finals = final_amounts(out, latest_by_adj(decisions))
    sched = schedule if schedule is not None else schedule_from_workpaper(wp)
    out.bridge = build_bridge(out.deal, out.reconciliation, sched, out.assessments, final_amounts=finals)
    return out


def check_bridge_identity(wp: Workpaper) -> dict[str, str]:
    """period label -> (diligence adjusted EBITDA - (GL EBITDA + final amounts)).

    Uses the latest decisions in ``wp.reviews``; pending items are excluded. See
    ``bridge_ties``. Raises ValueError when the bridge lacks the rows the identity
    needs.
    """
    rows = {r.key: r for r in wp.bridge.rows}
    missing = [k for k in ("gl_ebitda", "diligence_adjusted_ebitda") if k not in rows]
    if missing:
        raise ValueError(f"bridge is missing row(s): {', '.join(missing)}")
    finals = final_amounts(wp, latest_by_adj(wp.reviews))
    out: dict[str, str] = {}
    for label in period_labels(wp):
        expected = D(rows["gl_ebitda"].amounts.get(label)) + sum(
            (D(f.get(label)) for f in finals.values() if f), ZERO
        )
        out[label] = fmt(D(rows["diligence_adjusted_ebitda"].amounts.get(label)) - expected)
    return out


def bridge_ties(differences: Mapping[str, str], tolerance: object = "0.01") -> bool:
    return all(abs(D(v)) <= D(tolerance) for v in differences.values())


# ---------------------------------------------------------------------------
# Open-question updates
# ---------------------------------------------------------------------------

_STATUS_BY_NAME = {s.value: s for s in QuestionStatus}


def encode_question_update(status: QuestionStatus, response: str = "") -> str:
    """The ``ReviewDecision.question_updates`` value: "STATUS" or "STATUS: response"."""
    response = response.strip()
    return f"{status.value}: {response}" if response else status.value


def parse_question_update(value: str) -> tuple[Optional[QuestionStatus], Optional[str]]:
    """(status or None, response or None).

    "ANSWERED" sets status only; "ANSWERED: text" sets both; any other text is a
    response note that leaves the status unchanged.
    """
    text = value.strip()
    head, sep, rest = text.partition(":")
    status = _STATUS_BY_NAME.get(head.strip().upper())
    if status is not None:
        return status, (rest.strip() if sep else None)
    return None, (text or None)


def apply_question_updates(
    assessments: list[AdjustmentAssessment], decisions: Iterable[ReviewDecision]
) -> list[str]:
    """Replay every decision's question updates in log order onto ``assessments``
    (mutated in place). Updates are cumulative: a later decision that does not
    mention a question leaves its earlier update in force. Returns unknown q_ids."""
    by_qid: dict[str, OpenQuestion] = {}
    for a in assessments:
        for q in a.open_questions:
            by_qid[q.q_id] = q
    unknown: list[str] = []
    for d in decisions:
        for q_id, value in d.question_updates.items():
            q = by_qid.get(q_id)
            if q is None:
                if q_id not in unknown:
                    unknown.append(q_id)
                continue
            status, response = parse_question_update(value)
            if status is not None:
                q.status = status
            if response is not None:
                q.response = response
    return unknown


# ---------------------------------------------------------------------------
# Building and classifying decisions
# ---------------------------------------------------------------------------


def _differs(a: Mapping[str, str], b: Mapping[str, str], tolerance: object) -> bool:
    tol = D(tolerance)
    return any(abs(D(a.get(k)) - D(b.get(k))) > tol for k in set(a) | set(b))


def differs_from_tool(
    treatment: Treatment,
    amounts: Mapping[str, str],
    tool_treatment: Treatment,
    tool_amounts: Mapping[str, str],
    tolerance: object = "1.00",
) -> bool:
    if treatment != tool_treatment:
        return True
    if treatment == Treatment.REQUEST_INFO:
        return False
    return _differs(amounts, tool_amounts, tolerance)


def decision_is_override(decision: ReviewDecision, tolerance: object = "1.00") -> bool:
    return differs_from_tool(
        decision.treatment, decision.amounts, decision.tool_treatment, decision.tool_amounts, tolerance
    )


def decision_is_stale(
    assessment: AdjustmentAssessment, decision: ReviewDecision, tolerance: object = "1.00"
) -> bool:
    """True when the tool's current proposal differs from what the reviewer saw
    (the review was re-run after the decision was recorded)."""
    return differs_from_tool(
        assessment.treatment, assessment.proposed, decision.tool_treatment, decision.tool_amounts, tolerance
    )


def review_status(
    assessment: AdjustmentAssessment, decision: Optional[ReviewDecision], tolerance: object = "1.00"
) -> str:
    if decision is None:
        return STATUS_UNREVIEWED
    return STATUS_OVERRIDDEN if decision_is_override(decision, tolerance) else STATUS_AGREED


def resolve_amounts(
    assessment: AdjustmentAssessment,
    treatment: Treatment,
    amounts: Mapping[str, object],
    labels: list[str],
) -> dict[str, str]:
    """The amounts a treatment carries: ACCEPT is management's claim as presented,
    REJECT is zero, REQUEST_INFO is pending ({}), REVISE is what the reviewer entered."""
    if treatment == Treatment.REQUEST_INFO:
        return {}
    if treatment == Treatment.REJECT:
        return period_map({}, labels)
    if treatment == Treatment.ACCEPT:
        return period_map(assessment.claimed, labels)
    return period_map(amounts, labels)


def decision_problems(
    assessment: AdjustmentAssessment,
    *,
    treatment: Treatment,
    amounts: Mapping[str, object],
    rationale: str,
    reviewer: str,
    correction_type: CorrectionType,
    labels: list[str],
    tolerance: object = "1.00",
) -> tuple[list[str], list[str]]:
    """(errors, warnings) for a proposed decision. Errors block recording."""
    errors: list[str] = []
    warnings: list[str] = []
    if not reviewer.strip():
        errors.append("Enter the reviewer's name.")
    if treatment == Treatment.REVISE:
        bad = []
        for label in labels:
            try:
                D(amounts.get(label))
            except ValueError:
                bad.append(label)
        if bad:
            errors.append(f"Amount is not a number for: {', '.join(bad)}.")
            return errors, warnings
    final = resolve_amounts(assessment, treatment, amounts, labels)
    tool_amounts = period_map(assessment.proposed, labels) if assessment.proposed else {}
    override = differs_from_tool(treatment, final, assessment.treatment, tool_amounts, tolerance)
    if override and not rationale.strip():
        errors.append("A rationale is required when the decision differs from the tool's proposal.")
    if override and correction_type == CorrectionType.NONE:
        errors.append("Select a correction type: the decision differs from the tool's proposal.")
    if not override and correction_type != CorrectionType.NONE and not rationale.strip():
        errors.append("Explain the correction in the rationale.")
    if not override and correction_type in (CorrectionType.JUDGMENT_DIFFERENCE, CorrectionType.NEW_INFORMATION):
        warnings.append("The decision matches the tool's proposal; this correction type only applies to an override.")
    if treatment == Treatment.REVISE:
        if not _differs(final, period_map(assessment.claimed, labels), tolerance):
            warnings.append("Revised amounts equal management's claim; Accept is the consistent treatment.")
        elif all(D(v) == 0 for v in final.values()):
            warnings.append("Revised amounts are zero in every period; Reject is the consistent treatment.")
    return errors, warnings


class DecisionError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_decision(
    assessment: AdjustmentAssessment,
    *,
    treatment: Treatment,
    amounts: Mapping[str, object],
    rationale: str,
    reviewer: str,
    labels: list[str],
    correction_type: CorrectionType = CorrectionType.NONE,
    question_updates: Optional[Mapping[str, str]] = None,
    tolerance: object = "1.00",
    timestamp: Optional[str] = None,
) -> ReviewDecision:
    """Validate and build a decision; raises DecisionError listing every problem."""
    errors, _ = decision_problems(
        assessment,
        treatment=treatment,
        amounts=amounts,
        rationale=rationale,
        reviewer=reviewer,
        correction_type=correction_type,
        labels=labels,
        tolerance=tolerance,
    )
    if errors:
        raise DecisionError(errors)
    return ReviewDecision(
        adj_id=assessment.adj_id,
        reviewer=reviewer.strip(),
        timestamp=timestamp or utc_now_iso(),
        treatment=treatment,
        amounts=resolve_amounts(assessment, treatment, amounts, labels),
        rationale=rationale.strip(),
        tool_treatment=assessment.treatment,
        tool_amounts=period_map(assessment.proposed, labels) if assessment.proposed else {},
        correction_type=correction_type,
        question_updates=dict(question_updates or {}),
    )


def carry_forward_decision(
    previous: ReviewDecision,
    *,
    reviewer: str,
    question_updates: Mapping[str, str],
    timestamp: Optional[str] = None,
) -> ReviewDecision:
    """Re-record the latest decision unchanged, carrying only new question updates.

    Question status is recorded on a decision line (the contract has no separate
    question log), so a status change made after the decision re-affirms it.
    """
    return previous.model_copy(
        update={
            "reviewer": reviewer.strip() or previous.reviewer,
            "timestamp": timestamp or utc_now_iso(),
            "question_updates": dict(question_updates),
        },
        deep=True,
    )


# ---------------------------------------------------------------------------
# Feedback loop: corrections summary
# ---------------------------------------------------------------------------


def corrections_summary(
    decisions: Iterable[ReviewDecision], latest_only: bool = True, tolerance: object = "1.00"
) -> dict[str, Any]:
    """Count reviewer corrections by type, split tool errors from judgment.

    Tool-error types become regression cases; JUDGMENT_DIFFERENCE and
    NEW_INFORMATION do not count against the tool. With ``latest_only`` an
    adjustment re-reviewed several times counts once, as finally decided.
    """
    items = list(latest_by_adj(decisions).values()) if latest_only else list(decisions)
    by_type = {c.value: 0 for c in CorrectionType}
    tool_error_ids: list[str] = []
    unclassified: list[str] = []
    overridden = 0
    for d in items:
        by_type[d.correction_type.value] += 1
        override = decision_is_override(d, tolerance)
        overridden += int(override)
        if d.correction_type in TOOL_ERROR_CORRECTIONS and d.adj_id not in tool_error_ids:
            tool_error_ids.append(d.adj_id)
        if override and d.correction_type == CorrectionType.NONE and d.adj_id not in unclassified:
            unclassified.append(d.adj_id)
    tool_error = sum(by_type[c.value] for c in TOOL_ERROR_CORRECTIONS)
    return {
        "decisions": len(items),
        "agreed": len(items) - overridden,
        "overridden": overridden,
        "by_type": by_type,
        "tool_error": tool_error,
        "judgment": by_type[CorrectionType.JUDGMENT_DIFFERENCE.value],
        "new_information": by_type[CorrectionType.NEW_INFORMATION.value],
        "tool_error_adj_ids": tool_error_ids,
        "unclassified_overrides": unclassified,
    }


def tool_error_corrections(decisions: Iterable[ReviewDecision]) -> list[ReviewDecision]:
    """Latest decisions whose correction type blames the tool (regression-case input)."""
    return [d for d in latest_by_adj(decisions).values() if d.correction_type in TOOL_ERROR_CORRECTIONS]


# ---------------------------------------------------------------------------
# Time on task (benchmark support), stored beside the review log
# ---------------------------------------------------------------------------


def append_timing(
    path: Path,
    *,
    adj_id: str,
    opened_at: str,
    decided_at: str,
    seconds: int,
    reviewer: str = "",
    treatment: Optional[Treatment] = None,
    deal_id: str = "",
    run_id: str = "",
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "adj_id": adj_id,
        "opened_at": opened_at,
        "decided_at": decided_at,
        "seconds": int(seconds),
        "reviewer": reviewer,
        "treatment": treatment.value if treatment is not None else None,
        "deal_id": deal_id,
        "run_id": run_id,
    }
    _append_jsonl(Path(path), record)
    return record


def load_timing(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for _, raw in _read_jsonl_lines(Path(path)):
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        if isinstance(rec, dict) and "adj_id" in rec and isinstance(rec.get("seconds"), int):
            out.append(rec)
    return out


def timing_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Seconds per adjustment (summed across decisions) and overall totals."""
    per_adj: dict[str, dict[str, Any]] = {}
    for r in records:
        s = per_adj.setdefault(r["adj_id"], {"adj_id": r["adj_id"], "decisions": 0, "seconds": 0, "last_decided_at": ""})
        s["decisions"] += 1
        s["seconds"] += int(r["seconds"])
        s["last_decided_at"] = max(s["last_decided_at"], str(r.get("decided_at", "")))
    per = sorted(per_adj.values(), key=lambda s: _natural_key(s["adj_id"]))
    totals = [s["seconds"] for s in per]
    return {
        "adjustments": len(per),
        "decisions": sum(s["decisions"] for s in per),
        "total_seconds": sum(totals),
        "median_seconds_per_adjustment": int(statistics.median(totals)) if totals else 0,
        "per_adjustment": per,
    }


def _natural_key(text: str) -> list[Any]:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", text)]
