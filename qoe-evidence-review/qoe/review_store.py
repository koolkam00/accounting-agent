"""Reviewer decisions: an append-only log and the rules that turn it into final amounts.

The log is JSONL, one ``ReviewDecision`` per line, at
``<workpaper_dir>/review_log.jsonl``. It is never rewritten: the latest line for
an adj id wins, earlier lines stay as the audit trail.

Final-amount semantics (SPEC section 7):

- reviewed, not REQUEST_INFO -> the reviewer's amounts (every period label, missing -> 0.00)
- reviewed REQUEST_INFO      -> {} (pending, excluded from diligence adjusted EBITDA)
- unreviewed                 -> the tool's proposal ({} when the tool said REQUEST_INFO)

Diligence-identified items (``source == "diligence"``, SPEC §5.7) follow exactly
the same rules: they carry a zero claim, so an unreviewed item carries the
tool's proposal and a reviewed one carries the reviewer's amounts.

``apply_reviews`` rebuilds the bridge with ``qoe.bridge.build_bridge`` from
management's schedule as presented: the ``schedule`` argument when the caller
has the deal package, else ``Workpaper.schedule`` when the run stored it, else
the parts of the schedule the bridge uses reconstructed from the workpaper
itself (see ``schedule_from_workpaper``). That keeps the review path free of
file I/O on the deal package and works for a workpaper whose deal directory
has moved.

Questions for management have their own append-only log,
``<workpaper_dir>/question_log.jsonl`` (``QuestionLogEntry``: a status/response
update, or a question the reviewer raised). A question update is not a
decision: it never re-signs, re-dates or creates a ``ReviewDecision``, so a
management answer can be logged on an unreviewed adjustment without marking it
reviewed. ``apply_reviews(..., question_log=...)`` replays it together with the
``question_updates`` older decision lines carry, in time order.

Appends can be conditional (``expected_token``): the log is re-read under the
file lock and the write is refused with ``ConflictError`` when the latest
decision for the adjustment is not the one the reviewer's form was built from,
so a stale page cannot silently overwrite a colleague's newer decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from qoe.money import D, ZERO, fmt, period_map, q2
from qoe.schemas import (
    TOOL_ERROR_CORRECTIONS,
    AdjustmentAssessment,
    AdjustmentClaim,
    BridgeRow,
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
QUESTION_LOG_NAME = "question_log.jsonl"
TIMING_LOG_NAME = "timing.jsonl"

# Token of "no decision / no question update yet" for conditional appends.
NO_ENTRY_TOKEN = "none"
# Largest amount a reviewer may enter; anything bigger is a typo, not an EBITDA adjustment.
MAX_AMOUNT = Decimal("1e15")

STATUS_UNREVIEWED = "Unreviewed"
STATUS_AGREED = "Agreed"
STATUS_OVERRIDDEN = "Overridden"


# ---------------------------------------------------------------------------
# JSONL primitives
# ---------------------------------------------------------------------------


def _append_jsonl(
    path: Path,
    record: Mapping[str, Any] | Callable[[bytes], Mapping[str, Any]],
    check: Optional[Callable[[bytes], None]] = None,
) -> Mapping[str, Any]:
    """Append one JSON line under an exclusive lock.

    ``check`` sees the file's current bytes (read under the same lock) and may
    raise to refuse the write. ``record`` may be a callable of those bytes, for
    records whose content depends on what is already logged (a new question id).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+b") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            if check is not None or callable(record):
                fh.seek(0)
                existing = fh.read()
                if check is not None:
                    check(existing)
                if callable(record):
                    record = record(existing)
            line = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
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
    return record


def _split_lines(data: bytes) -> list[tuple[int, bytes]]:
    """(1-based line number, raw bytes) for every non-blank line of ``data``."""
    return [(i, chunk) for i, chunk in enumerate(data.split(b"\n"), 1) if chunk.strip()]


def _read_jsonl_lines(path: Path) -> list[tuple[int, bytes]]:
    """(1-based line number, raw bytes) for every non-blank line."""
    if not path.exists():
        return []
    return _split_lines(path.read_bytes())


def _parse_decisions(data: bytes) -> tuple[list[ReviewDecision], list[int]]:
    out: list[ReviewDecision] = []
    skipped: list[int] = []
    for lineno, raw in _split_lines(data):
        try:
            out.append(ReviewDecision.model_validate_json(raw))
        except ValueError:  # pydantic ValidationError and UnicodeDecodeError are ValueErrors
            skipped.append(lineno)
    return out, skipped


def _token(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def decision_token(decision: Optional[ReviewDecision]) -> str:
    """Identifies the decision a review form was built from (``NO_ENTRY_TOKEN`` for none)."""
    return NO_ENTRY_TOKEN if decision is None else _token(decision.model_dump(mode="json"))


class ConflictError(RuntimeError):
    """A conditional append found a newer entry than the one the caller's page showed."""

    def __init__(self, message: str, current: Any = None) -> None:
        super().__init__(message)
        self.current = current


# ---------------------------------------------------------------------------
# Question log
# ---------------------------------------------------------------------------


class QuestionLogEntry(BaseModel):
    """One line of ``question_log.jsonl``.

    ``kind="update"``: a status and/or response change to an existing question
    (``response=None`` leaves the response as it was, ``""`` clears it).
    ``kind="new"``: a question the reviewer raised for management, OPEN.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["update", "new"]
    q_id: str
    adj_id: str
    reviewer: str
    timestamp: str
    status: Optional[QuestionStatus] = None
    response: Optional[str] = None
    text: str = ""
    priority: str = "medium"


def _parse_question_entries(data: bytes) -> tuple[list[QuestionLogEntry], list[int]]:
    out: list[QuestionLogEntry] = []
    skipped: list[int] = []
    for lineno, raw in _split_lines(data):
        try:
            out.append(QuestionLogEntry.model_validate_json(raw))
        except ValueError:
            skipped.append(lineno)
    return out, skipped


def question_token(entries: Iterable[QuestionLogEntry], q_id: str) -> str:
    """Identifies the latest logged change to ``q_id`` (``NO_ENTRY_TOKEN`` for none)."""
    last = None
    for e in entries:
        if e.q_id == q_id:
            last = e
    return NO_ENTRY_TOKEN if last is None else _token(last.model_dump(mode="json"))


_REVIEWER_QID = re.compile(r"-R(\d+)$")


def next_reviewer_question_id(adj_id: str, existing_ids: Iterable[str]) -> str:
    """``Q-<adj_id>-R<n>``: reviewer-raised questions are numbered apart from the tool's
    ``Q-<adj_id>-<n>`` so a re-run that adds tool questions cannot collide with them."""
    prefix = f"Q-{adj_id}-R"
    used = [int(m.group(1)) for q in existing_ids if q.startswith(prefix) and (m := _REVIEWER_QID.search(q))]
    return f"{prefix}{max(used, default=0) + 1}"


# ---------------------------------------------------------------------------
# Review log
# ---------------------------------------------------------------------------


class ReviewStore:
    """Append-only JSONL logs of reviewer decisions and of question updates."""

    def __init__(self, path: Path, question_path: Optional[Path] = None) -> None:
        self.path = Path(path)
        self.question_path = Path(question_path) if question_path is not None else self.path.with_name(QUESTION_LOG_NAME)
        # Line numbers that failed to parse on the last read (a torn trailing write,
        # or a hand-edited line). They are skipped, never repaired or removed.
        self.skipped_lines: list[int] = []
        self.skipped_question_lines: list[int] = []

    @classmethod
    def for_workpaper_dir(cls, workpaper_dir: Path) -> "ReviewStore":
        return cls(Path(workpaper_dir) / REVIEW_LOG_NAME)

    def append(self, decision: ReviewDecision, expected_token: Optional[str] = None) -> None:
        """Append a decision. With ``expected_token`` (see ``decision_token``) the write
        is refused with ``ConflictError`` unless the latest logged decision for the
        adjustment is still the one the caller's form was built from."""
        check = None
        if expected_token is not None:

            def check(existing: bytes) -> None:
                current = latest_by_adj(_parse_decisions(existing)[0]).get(decision.adj_id)
                if decision_token(current) != expected_token:
                    raise ConflictError(_decision_conflict_message(decision.adj_id, current), current)

        _append_jsonl(self.path, decision.model_dump(mode="json"), check)

    def all(self) -> list[ReviewDecision]:
        """Every decision in log order."""
        data = self.path.read_bytes() if self.path.exists() else b""
        out, self.skipped_lines = _parse_decisions(data)
        return out

    def latest(self) -> dict[str, ReviewDecision]:
        return latest_by_adj(self.all())

    def history(self, adj_id: str) -> list[ReviewDecision]:
        return [d for d in self.all() if d.adj_id == adj_id]

    # -- questions ---------------------------------------------------------

    def questions(self) -> list[QuestionLogEntry]:
        """Every question-log entry in log order."""
        data = self.question_path.read_bytes() if self.question_path.exists() else b""
        out, self.skipped_question_lines = _parse_question_entries(data)
        return out

    def append_question(self, entry: QuestionLogEntry, expected_token: Optional[str] = None) -> None:
        """Append a question update. With ``expected_token`` (see ``question_token``) the
        write is refused with ``ConflictError`` if the question changed since the caller read it."""
        if entry.kind != "update":
            raise ValueError("use add_question() to raise a new question")
        check = None
        if expected_token is not None:

            def check(existing: bytes) -> None:
                entries = _parse_question_entries(existing)[0]
                if question_token(entries, entry.q_id) != expected_token:
                    last = [e for e in entries if e.q_id == entry.q_id][-1]
                    raise ConflictError(
                        f"{entry.q_id} was updated by {last.reviewer or 'another reviewer'} at {last.timestamp} "
                        "after this page loaded. Review the current status, then record again.",
                        last,
                    )

        _append_jsonl(self.question_path, entry.model_dump(mode="json"), check)

    def add_question(
        self,
        *,
        adj_id: str,
        text: str,
        reviewer: str,
        priority: str = "medium",
        existing_ids: Iterable[str] = (),
        timestamp: Optional[str] = None,
    ) -> QuestionLogEntry:
        """Log a question the reviewer raised for management. The id (``Q-<adj>-R<n>``) is
        allotted under the log lock, so two reviewers adding questions at once get distinct ids."""
        problems = question_entry_problems(reviewer=reviewer, text=text)
        if problems:
            raise DecisionError(problems)
        known = list(existing_ids)
        built: dict[str, QuestionLogEntry] = {}

        def record(existing: bytes) -> Mapping[str, Any]:
            logged = [e.q_id for e in _parse_question_entries(existing)[0] if e.adj_id == adj_id]
            entry = QuestionLogEntry(
                kind="new",
                q_id=next_reviewer_question_id(adj_id, [*known, *logged]),
                adj_id=adj_id,
                reviewer=reviewer.strip(),
                timestamp=timestamp or utc_now_iso(),
                status=QuestionStatus.OPEN,
                text=" ".join(text.split()),
                priority=priority if priority in ("high", "medium", "low") else "medium",
            )
            built["entry"] = entry
            return entry.model_dump(mode="json")

        _append_jsonl(self.question_path, record)
        return built["entry"]


def _decision_conflict_message(adj_id: str, current: Optional[ReviewDecision]) -> str:
    if current is None:
        return f"The decision this form was built from for {adj_id} is no longer the latest. Reload and review again."
    return (
        f"{adj_id} was decided by {current.reviewer or 'another reviewer'} at {current.timestamp} "
        f"({current.treatment.value}) after this form was opened. Review that decision first; "
        "your draft is kept."
    )


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


DILIGENCE_SOURCE = "diligence"


def is_diligence_item(a: AdjustmentAssessment) -> bool:
    """Identified by the tool (SPEC §5.7), not an adjustment on management's schedule."""
    return a.source == DILIGENCE_SOURCE


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

    Only management items are on the schedule; diligence-identified items were
    never claimed by management and reach the bridge through the assessments.
    Claimed amounts come from the existing ``mgmt:<adj_id>`` bridge rows (what the
    bridge was originally built from) and fall back to ``assessment.claimed``.
    Descriptions, GL accounts and support refs come from the assessment.
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
    for i, a in enumerate((a for a in wp.assessments if not is_diligence_item(a)), 1):
        mgmt_row = rows.get(f"mgmt:{a.adj_id}")
        amounts = mgmt_row.amounts if mgmt_row is not None else a.claimed
        claims.append(
            AdjustmentClaim(
                adj_id=a.adj_id,
                title=a.title,
                category=a.category,
                description=a.description,
                gl_accounts=list(a.gl_accounts),
                support_refs=list(a.support_refs),
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
    question_log: Optional[Iterable[QuestionLogEntry]] = None,
) -> Workpaper:
    """A new workpaper with ``reviews`` recorded, question updates applied, and the
    bridge rebuilt on final amounts. The input workpaper is not modified.

    ``reviews`` is the full log in order (the Review Log sheet shows every line);
    the latest decision per adj id sets the final amount, for management and
    diligence-identified items alike. Pass the deal package's ``schedule`` when
    available; otherwise ``wp.schedule`` is used, and failing that the schedule
    is reconstructed from ``wp``. ``question_log`` (``ReviewStore.questions()``)
    adds the question updates and reviewer-raised questions logged apart from
    decisions.
    """
    from qoe.bridge import build_bridge  # lazy: the bridge is owned by the engine module

    decisions = list(reviews.values()) if isinstance(reviews, Mapping) else list(reviews)
    out = wp.model_copy(deep=True)
    out.reviews = decisions
    apply_question_updates(out.assessments, decisions, question_log or ())
    finals = final_amounts(out, latest_by_adj(decisions))
    sched = schedule_for(wp, schedule)
    out.bridge = build_bridge(out.deal, out.reconciliation, sched, out.assessments, final_amounts=finals)
    return out


def schedule_for(wp: Workpaper, schedule: Optional[ManagementSchedule] = None) -> ManagementSchedule:
    """The schedule to rebuild the bridge from: explicit, stored on the workpaper, or reconstructed."""
    if schedule is not None:
        return schedule
    if wp.schedule is not None:
        return wp.schedule
    return schedule_from_workpaper(wp)


def check_bridge_identity(wp: Workpaper) -> dict[str, str]:
    """period label -> (diligence adjusted EBITDA - (GL EBITDA + final amounts)).

    Final amounts cover management items and diligence-identified items (SPEC
    §5.6 identity). Uses the latest decisions in ``wp.reviews``; pending items
    are excluded. See
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


def bridge_row_adj_id(row: BridgeRow) -> Optional[str]:
    """The adjustment a bridge row belongs to: its adj_id, else the id in a "mgmt:" / "dil:" key."""
    if row.adj_id:
        return row.adj_id
    head, sep, tail = row.key.partition(":")
    return tail if sep and head in ("mgmt", "dil") else None


def is_item_row(row: BridgeRow, item_ids: Iterable[str]) -> bool:
    """A bridge row of a diligence-identified item (``item_ids`` = their adj ids)."""
    return row.kind == "diligence_adjustment" and bridge_row_adj_id(row) in set(item_ids)


def bridge_display_rows(rows: Iterable[BridgeRow], item_ids: Iterable[str]) -> list[BridgeRow]:
    """Bridge rows in the order the workpaper and the app show them.

    Diligence-identified items form their own block after the diligence
    revisions to management's items: within each run of rows between subtotals
    their rows move (stably) to the end, so every subtotal still sums the same
    rows. An all-zero "as claimed" row for an item management never claimed
    (an older bridge may carry one) is dropped.
    """
    ids = set(item_ids)
    out: list[BridgeRow] = []
    run: list[BridgeRow] = []

    def flush() -> None:
        out.extend(r for r in run if not is_item_row(r, ids))
        out.extend(r for r in run if is_item_row(r, ids))
        run.clear()

    for r in rows:
        if r.kind == "mgmt_adjustment" and bridge_row_adj_id(r) in ids and all(D(v) == 0 for v in r.amounts.values()):
            continue
        if r.kind == "subtotal":
            flush()
            out.append(r)
        else:
            run.append(r)
    flush()
    return out


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


def _parse_time(ts: str) -> datetime:
    try:
        t = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)
    return t if t.tzinfo is not None else t.replace(tzinfo=timezone.utc)


def merge_logs(
    decisions: Sequence[ReviewDecision], entries: Sequence[QuestionLogEntry]
) -> list[ReviewDecision | QuestionLogEntry]:
    """Decisions and question-log entries in one time line. Each log keeps its own
    order (log order, not timestamps, decides within a log); the two are merged by
    timestamp, a decision first on a tie."""
    out: list[ReviewDecision | QuestionLogEntry] = []
    i = j = 0
    while i < len(decisions) and j < len(entries):
        if _parse_time(entries[j].timestamp) < _parse_time(decisions[i].timestamp):
            out.append(entries[j])
            j += 1
        else:
            out.append(decisions[i])
            i += 1
    out.extend(decisions[i:])
    out.extend(entries[j:])
    return out


def reviewer_question(entry: QuestionLogEntry) -> OpenQuestion:
    return OpenQuestion(
        q_id=entry.q_id,
        adj_id=entry.adj_id,
        text=entry.text,
        priority=entry.priority,
        basis=f"Raised by reviewer {entry.reviewer}".strip(),
        status=QuestionStatus.OPEN,
    )


def apply_question_updates(
    assessments: list[AdjustmentAssessment],
    decisions: Iterable[ReviewDecision],
    question_log: Iterable[QuestionLogEntry] = (),
) -> list[str]:
    """Replay question updates onto ``assessments`` (mutated in place): the
    ``question_updates`` carried by decision lines and the question log, merged in
    time order (``merge_logs``). Updates are cumulative: a later line that does not
    mention a question leaves its earlier update in force. A reviewer-raised
    question is added to its adjustment once. Returns unknown q_ids."""
    by_qid: dict[str, OpenQuestion] = {}
    by_adj = {a.adj_id: a for a in assessments}
    for a in assessments:
        for q in a.open_questions:
            by_qid[q.q_id] = q
    unknown: list[str] = []

    def note_unknown(q_id: str) -> None:
        if q_id not in unknown:
            unknown.append(q_id)

    for item in merge_logs(list(decisions), list(question_log)):
        if isinstance(item, ReviewDecision):
            changes = [(q_id, *parse_question_update(v)) for q_id, v in item.question_updates.items()]
        elif item.kind == "new":
            a = by_adj.get(item.adj_id)
            if a is None:
                note_unknown(item.q_id)
            elif item.q_id not in by_qid:
                q = reviewer_question(item)
                a.open_questions.append(q)
                by_qid[q.q_id] = q
            continue
        else:
            changes = [(item.q_id, item.status, item.response)]
        for q_id, status, response in changes:
            q = by_qid.get(q_id)
            if q is None:
                note_unknown(q_id)
                continue
            if status is not None:
                q.status = status
            if response is not None:
                q.response = response
    return unknown


def questions_after(
    questions: Iterable[OpenQuestion],
    updates: Optional[Mapping[str, str]] = None,
    new_texts: Iterable[str] = (),
) -> list[OpenQuestion]:
    """The questions as they would stand after a form's edits: ``updates`` in the
    ``question_updates`` encoding, plus a new OPEN question for every non-blank text."""
    out = [q.model_copy() for q in questions]
    for q in out:
        value = (updates or {}).get(q.q_id)
        if value is None:
            continue
        status, response = parse_question_update(value)
        if status is not None:
            q.status = status
        if response is not None:
            q.response = response
    for i, text in enumerate(t for t in new_texts if t.strip()):
        out.append(OpenQuestion(q_id=f"(new {i + 1})", text=text.strip()))
    return out


def question_entry_problems(*, reviewer: str, text: Optional[str] = None) -> list[str]:
    """Errors that block logging a question update (``text=None``) or a new question."""
    errors = []
    if not reviewer.strip():
        errors.append("Enter the reviewer's name.")
    if text is not None and not text.strip():
        errors.append("Enter the question for management.")
    return errors


def make_question_update(
    question: OpenQuestion,
    *,
    adj_id: str,
    status: QuestionStatus,
    response: str,
    reviewer: str,
    timestamp: Optional[str] = None,
) -> Optional[QuestionLogEntry]:
    """A question-log update for a changed status and/or response, or None when nothing
    changed. Raises DecisionError when the reviewer is not named: an update is signed by
    whoever makes it, never by the reviewer of an earlier decision."""
    problems = question_entry_problems(reviewer=reviewer)
    if problems:
        raise DecisionError(problems)
    new_response = response.strip()
    response_changed = new_response != question.response.strip()
    if status == question.status and not response_changed:
        return None
    return QuestionLogEntry(
        kind="update",
        q_id=question.q_id,
        adj_id=question.adj_id or adj_id,
        reviewer=reviewer.strip(),
        timestamp=timestamp or utc_now_iso(),
        status=status,
        response=new_response if response_changed else None,
    )


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
    """True when the decision is an override of the tool's proposal.

    ACCEPT carrying exactly the tool's REVISE amounts agrees with the tool: that is
    what Accept means on a diligence-identified item (it carries the tool's
    proposal, see ``resolve_amounts``). On a management item Accept carries the
    claim, which differs from a REVISE proposal, so it stays an override.
    """
    if treatment == Treatment.ACCEPT and tool_treatment == Treatment.REVISE:
        return _differs(amounts, tool_amounts, tolerance)
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


def accept_carries_proposal(assessment: AdjustmentAssessment) -> bool:
    """Accept on a diligence-identified item accepts the tool's adjustment: management
    claimed nothing, so accepting "the claim" would silently remove the item."""
    return is_diligence_item(assessment)


def resolve_amounts(
    assessment: AdjustmentAssessment,
    treatment: Treatment,
    amounts: Mapping[str, object],
    labels: list[str],
) -> dict[str, str]:
    """The amounts a treatment carries: ACCEPT is management's claim as presented (for a
    diligence-identified item, the tool's proposed amount), REJECT is zero,
    REQUEST_INFO is pending ({}), REVISE is what the reviewer entered."""
    if treatment == Treatment.REQUEST_INFO:
        return {}
    if treatment == Treatment.REJECT:
        return period_map({}, labels)
    if treatment == Treatment.ACCEPT:
        if accept_carries_proposal(assessment):
            return period_map(assessment.proposed, labels)
        return period_map(assessment.claimed, labels)
    return period_map(amounts, labels)


def amount_problem(value: object) -> Optional[str]:
    """Why a reviewer-entered amount cannot be used, or None. NaN, Infinity and
    values too large to carry to the cent are rejected rather than crashing later."""
    try:
        d = D(value)
    except (TypeError, ValueError, ArithmeticError):
        return "not a number"
    if not d.is_finite():
        return "not a number"
    try:
        q2(d)
    except ArithmeticError:
        return "out of range"
    if abs(d) >= MAX_AMOUNT:
        return "out of range"
    return None


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
    questions: Optional[Iterable[OpenQuestion]] = None,
    previous: Optional[ReviewDecision] = None,
) -> tuple[list[str], list[str]]:
    """(errors, warnings) for a proposed decision. Errors block recording.

    ``questions`` are the adjustment's questions as they will stand once the form's
    question edits are logged (``questions_after``; default: as they are now): a
    REQUEST_INFO decision needs at least one of them OPEN, so a pending item always
    carries a request to management. ``previous`` is the decision being replaced: a
    different decision cannot reuse its rationale word for word.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if not reviewer.strip():
        errors.append("Enter the reviewer's name.")
    if treatment == Treatment.REVISE:
        bad: dict[str, list[str]] = {}
        for label in labels:
            problem = amount_problem(amounts.get(label))
            if problem is not None:
                bad.setdefault(problem, []).append(label)
        if bad:
            for problem, which in bad.items():
                errors.append(f"Amount is {problem} for: {', '.join(which)}.")
            return errors, warnings
    if treatment == Treatment.ACCEPT and accept_carries_proposal(assessment) and not assessment.proposed:
        errors.append("The tool proposed no amount for this diligence item, so Accept has nothing to carry; use Revise.")
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
    if (
        previous is not None
        and rationale.strip()
        and " ".join(rationale.split()) == " ".join(previous.rationale.split())
        and (previous.treatment != treatment or _differs(final, previous.amounts, tolerance))
    ):
        errors.append(
            f"This rationale was written for the previous decision ({previous.treatment.value} by "
            f"{previous.reviewer or 'another reviewer'}); explain this decision."
        )
    if treatment == Treatment.REQUEST_INFO:
        current = list(assessment.open_questions if questions is None else questions)
        if not any(q.status == QuestionStatus.OPEN for q in current):
            errors.append(
                "Request info leaves the item pending: add a question for management "
                "(or reopen one) so the request says what is needed."
            )
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
    questions: Optional[Iterable[OpenQuestion]] = None,
    previous: Optional[ReviewDecision] = None,
) -> ReviewDecision:
    """Validate and build a decision; raises DecisionError listing every problem.

    ``question_updates`` are stored on the decision line (older logs did this; the
    app now logs question changes in the question log). ``questions`` and
    ``previous``: see ``decision_problems``; when ``questions`` is omitted, the
    stored ``question_updates`` are taken into account.
    """
    if questions is None and question_updates:
        questions = questions_after(assessment.open_questions, question_updates)
    errors, _ = decision_problems(
        assessment,
        treatment=treatment,
        amounts=amounts,
        rationale=rationale,
        reviewer=reviewer,
        correction_type=correction_type,
        labels=labels,
        tolerance=tolerance,
        questions=questions,
        previous=previous,
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
