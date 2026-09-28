"""Score a QoE workpaper against a deal's answer key (SPEC §9).

This is the only module that reads ``ground_truth.json``. The pipeline never
does, so nothing here can leak answers into a review run.

What is scored is the tool's *first-pass proposal* (``assessment.treatment``
and ``assessment.proposed``), never a reviewer's override: reviewer decisions
recorded on a workpaper are ignored by ``score``.

Scoring rules (the ones a reader could reasonably interpret differently):

- **Two populations.** Management items (``source != "diligence"``) are scored
  against ``GroundTruth.adjustments``: every per-adjustment metric below
  (treatment, amount, false accept, GL and document links, flags, case type)
  covers management items only. Diligence-identified items
  (``source == "diligence"``, SPEC §5.7) are scored separately against
  ``GroundTruth.diligence_items`` by ``diligence_item_accuracy``. Both
  populations enter the diligence adjusted EBITDA check.
- **GL rows.** A tool ``GLLink.entry_id`` maps to a GL source row through the
  ``GL-R<row>`` convention (SPEC §3.3). Ids that do not follow it cannot be
  compared with the answer key and are ignored.
- **Supporting link.** A link counts as *supporting* when
  ``supports_claim is True`` **and** its entry id is not listed in the
  ``entry_ids`` of any *removing* flag on the same adjustment. Removing flags
  are the §5.4 challenges whose effect is to take entries out of the
  proposal: ALREADY_EXCLUDED_FROM_EBITDA, OVERLAP_WITH_OTHER_ADJUSTMENT,
  CONTRADICTORY_EVIDENCE, CONTINUING_OBLIGATION, RECURRING_PATTERN.
  OUT_OF_PERIOD, OFFSETTING_RECOVERY and PERIOD_MISMATCH change amounts but
  leave the claimed entries supporting. GL link precision / recall compare
  the supporting rows with ``supporting_gl_rows``.
- **Surfaced recall.** A row is *surfaced* when it appears anywhere in the
  adjustment's evidence: any GL link (supporting or not), any flag's
  ``entry_ids``, or any recurrence observation. It is measured against
  ``supporting_gl_rows ∪ related_gl_rows``.
- **Supporting documents.** The key's ``supporting_docs`` are the documents
  that support the amount diligence carries. The tool's counterpart
  (``tool_supporting_docs``) depends on what the tool carries:

  * a non-zero amount (ACCEPT / REVISE): documents whose ``DocLink.entry_ids``
    include a supporting entry; plus agreements that stand for the event as a
    whole (``relation == "agreement"`` with no entry ids, e.g. a settlement
    agreement) unless a removing flag cites them; plus documents cited by an
    amount-effect flag (OFFSETTING_RECOVERY, OUT_OF_PERIOD) whose effect the
    carried amount includes;
  * zero in every period (REJECT): the evidence the zero rests on, i.e.
    documents linked to entries a removing flag took out, and documents a
    removing flag cites;
  * pending (REQUEST_INFO): documents linked to the claimed entries still
    standing, stand-alone agreements, and documents cited by the flags that
    drive the request (draft or unsigned support, missing benchmark, pro
    forma not realized, missing GL or document support).

  Documents that argue against part of a carried amount (for example the
  expense reports that show a trip was business travel) are therefore *not*
  supporting; the key lists those as ``related_docs``. Document precision /
  recall compare ``tool_supporting_docs`` with ``supporting_docs``.
- **Surfaced documents.** A document is *surfaced* when any ``DocLink`` or any
  flag's ``doc_ids`` on the adjustment names it. ``doc_surfaced_recall`` is
  measured against ``supporting_docs ∪ related_docs``.
- **Empty sets.** For one adjustment, precision (recall) is undefined when the
  tool proposed (the key expects) nothing; if both sets are empty the tool was
  right to link nothing and both are 1.0. Deal and overall figures are
  micro-averaged from the underlying counts.
- **False accept.** Tool ACCEPT while the key says anything else. The rate's
  denominator is the number of adjustments the key does *not* accept, i.e.
  "of the items that needed challenge, how many did the tool wave through".
- **Amount accuracy.** Only over adjustments where neither the key nor the
  tool says REQUEST_INFO. Every period label of the deal is compared (a
  missing amount is 0) with a tolerance of 1.00.
- **Flag recall.** An expected flag counts only when raised on the same
  adjustment. Extra flags are listed, not penalized: the key names the flags
  that *must* be raised, not the only acceptable ones.
- **Diligence items.** Each expected diligence item is matched one-to-one to a
  tool item with ``source == "diligence"``, greedily by the number of shared
  supporting GL rows (ties: key order, then tool order). An expected item
  with no supporting-row overlap may still match on any shared GL row (the
  tool reversed the other posting of a duplicate pair); the match basis is
  reported. A matched item is correct when every period of the tool's
  proposal is within 1.00 of the key (REQUEST_INFO carries nothing, so it is
  compared as zero). Unmatched items on either side are reported, and a tool
  item the key does not expect counts against accuracy: the denominator is
  expected items plus unmatched tool items.
- **Data quality.** A planted issue is detected when an issue with the same
  code exists and every locator both sides carry agrees (month, account, and
  GL rows vs the issue's entry ids), with at least one locator compared when
  the key specifies any.
- **EBITDA error.** The tool's diligence adjusted EBITDA is recomputed from
  the SPEC §5.6 identity: GL EBITDA per the workpaper's reconciliation plus
  every non-REQUEST_INFO *tool proposal*, management and diligence-identified
  items alike. The bridge row is reported beside it as a cross-check, because
  a bridge rebuilt after review would include reviewer decisions.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Iterable, Optional

from qoe.money import D, dsum, fmt
from qoe.schemas import (
    TOOL_ERROR_CORRECTIONS,
    AdjustmentAssessment,
    CorrectionType,
    DataQualityIssue,
    ExpectedAdjustment,
    ExpectedDataQuality,
    FlagCode,
    GroundTruth,
    ReviewDecision,
    Treatment,
    Workpaper,
)

GROUND_TRUTH_FILE = "ground_truth.json"
AMOUNT_TOLERANCE = Decimal("1.00")

REMOVING_FLAGS = frozenset(
    {
        FlagCode.ALREADY_EXCLUDED_FROM_EBITDA,
        FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,
        FlagCode.CONTRADICTORY_EVIDENCE,
        FlagCode.CONTINUING_OBLIGATION,
        FlagCode.RECURRING_PATTERN,
    }
)

# SPEC §9 "missed_contradictions": the challenges that decide whether an
# add-back survives at all, so missing one is a substantive miss.
CHALLENGE_FLAGS = frozenset(
    {
        FlagCode.CONTRADICTORY_EVIDENCE,
        FlagCode.RECURRING_PATTERN,
        FlagCode.CONTINUING_OBLIGATION,
        FlagCode.OFFSETTING_RECOVERY,
        FlagCode.OVERLAP_WITH_OTHER_ADJUSTMENT,
        FlagCode.ALREADY_EXCLUDED_FROM_EBITDA,
    }
)

# Flags whose amount effect is part of what the tool carries (their documents support that amount).
AMOUNT_EFFECT_FLAGS = frozenset({FlagCode.OFFSETTING_RECOVERY, FlagCode.OUT_OF_PERIOD})

# Flags that send an item to REQUEST_INFO (SPEC §5.5 steps 1-4): the request rests on their documents.
REQUEST_INFO_FLAGS = frozenset(
    {
        FlagCode.PRO_FORMA_NOT_REALIZED,
        FlagCode.UNSIGNED_OR_DRAFT_SUPPORT,
        FlagCode.NORMALIZATION_BENCHMARK_MISSING,
        FlagCode.NO_GL_SUPPORT,
        FlagCode.NO_DOCUMENT_SUPPORT,
    }
)

DILIGENCE_SOURCE = "diligence"  # AdjustmentAssessment.source of a diligence-identified item (SPEC §5.7)

VERDICTS = ("NOT_ASSESSED", "FALSE_ACCEPT", "WRONG_TREATMENT", "WRONG_AMOUNT", "MISSED_FLAG", "PASS")
DILIGENCE_VERDICTS = ("CORRECT", "WRONG_AMOUNT", "MISSED", "EXTRA")

RATIO_KEYS = (
    "treatment_accuracy",
    "amount_accuracy",
    "false_accept_rate",
    "gl_link_precision",
    "gl_link_recall",
    "gl_surfaced_recall",
    "doc_link_precision",
    "doc_link_recall",
    "doc_surfaced_recall",
    "flag_recall",
    "missed_contradictions",
    "data_quality_recall",
    "diligence_item_accuracy",
)

DISCLAIMER = (
    "These are automated scores of the tool's first-pass proposals, compared with answer keys "
    "written for SYNTHETIC deal packages. They are not practitioner-timed results, they say "
    "nothing about time saved, and they ignore any reviewer overrides. Each answer key records "
    "one careful senior's judgment; items marked medium or high ambiguity could reasonably be "
    "carried differently."
)

_ENTRY_ROW = re.compile(r"^GL-R(\d+)$")
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_ground_truth(deal_dir: Path) -> GroundTruth:
    """Read ``<deal_dir>/ground_truth.json``. The only reader of that file."""
    path = Path(deal_dir) / GROUND_TRUTH_FILE
    if not path.is_file():
        raise FileNotFoundError(f"no answer key at {path}")
    return GroundTruth.model_validate_json(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def entry_row(entry_id: str) -> Optional[int]:
    """GL source row for a ``GL-R<row>`` entry id, else None."""
    m = _ENTRY_ROW.match(entry_id.strip())
    return int(m.group(1)) if m else None


def _rows(entry_ids: Iterable[str]) -> set[int]:
    out: set[int] = set()
    for eid in entry_ids:
        row = entry_row(eid)
        if row is not None:
            out.add(row)
    return out


def _ratio(num: int, den: int) -> dict[str, Any]:
    return {"num": num, "den": den, "rate": round(num / den, 4) if den else None}


def _sum_ratios(ratios: Iterable[dict[str, Any]]) -> dict[str, Any]:
    num = den = 0
    for r in ratios:
        num += r["num"]
        den += r["den"]
    return _ratio(num, den)


def _pr(tool: set, expected: set) -> dict[str, Any]:
    tp, fp, fn = len(tool & expected), len(tool - expected), len(expected - tool)
    if not tool and not expected:
        precision: Optional[float] = 1.0
        recall: Optional[float] = 1.0
    else:
        precision = round(tp / (tp + fp), 4) if tp + fp else None
        recall = round(tp / (tp + fn), 4) if tp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}


def removed_entry_ids(a: AdjustmentAssessment) -> set[str]:
    """Entry ids a removing challenge took out of this adjustment's proposal."""
    out: set[str] = set()
    for f in a.flags:
        if f.code in REMOVING_FLAGS:
            out.update(f.entry_ids)
    return out


def supporting_entry_ids(a: AdjustmentAssessment) -> set[str]:
    """Claimed links that survived every removing challenge (see module docstring)."""
    removed = removed_entry_ids(a)
    return {link.entry_id for link in a.gl_links if link.supports_claim and link.entry_id not in removed}


def surfaced_entry_ids(a: AdjustmentAssessment) -> set[str]:
    """Every entry the adjustment's evidence shows a reviewer."""
    out = {link.entry_id for link in a.gl_links}
    for f in a.flags:
        out.update(f.entry_ids)
    for obs in a.recurrence:
        out.update(obs.entry_ids)
    return out


def is_diligence_item(a: AdjustmentAssessment) -> bool:
    """A diligence-identified item (SPEC §5.7), not an adjustment on management's schedule."""
    return a.source == DILIGENCE_SOURCE


def _carries_nonzero(a: AdjustmentAssessment) -> bool:
    return any(D(v) != 0 for v in a.proposed.values())


def _docs_linked_to(a: AdjustmentAssessment, entry_ids: set[str]) -> set[str]:
    return {dl.doc_id for dl in a.doc_links if entry_ids.intersection(dl.entry_ids)}


def _flag_docs(a: AdjustmentAssessment, codes: frozenset[FlagCode]) -> set[str]:
    return {d for f in a.flags if f.code in codes for d in f.doc_ids}


def tool_supporting_docs(a: AdjustmentAssessment) -> set[str]:
    """Documents the tool relies on for the amount it carries (see module docstring).

    Carried non-zero: documents on supporting entries, stand-alone agreements no
    removing flag cites, and documents behind a recovery or period effect.
    Carried zero: the documents that took the claim out. Pending: the documents
    the request for information rests on.
    """
    against = _flag_docs(a, REMOVING_FLAGS)
    standalone = {
        dl.doc_id for dl in a.doc_links if dl.relation == "agreement" and not dl.entry_ids and dl.doc_id not in against
    }
    if a.treatment == Treatment.REQUEST_INFO or not a.proposed:
        return _docs_linked_to(a, supporting_entry_ids(a)) | standalone | _flag_docs(a, REQUEST_INFO_FLAGS)
    if not _carries_nonzero(a):
        return _docs_linked_to(a, removed_entry_ids(a)) | against
    return _docs_linked_to(a, supporting_entry_ids(a)) | standalone | _flag_docs(a, AMOUNT_EFFECT_FLAGS)


def surfaced_doc_ids(a: AdjustmentAssessment) -> set[str]:
    """Every document the adjustment's evidence shows a reviewer: doc links and flag citations."""
    out = {dl.doc_id for dl in a.doc_links}
    for f in a.flags:
        out.update(f.doc_ids)
    return out


def _period_keys(labels: list[str], *maps: dict[str, str]) -> list[str]:
    keys = list(labels)
    for m in maps:
        keys.extend(k for k in m if k not in keys)
    return keys


def _unique(items: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


# ---------------------------------------------------------------------------
# Per-adjustment scoring
# ---------------------------------------------------------------------------


def _score_gl(exp: ExpectedAdjustment, a: Optional[AdjustmentAssessment]) -> dict[str, Any]:
    supporting = _rows(supporting_entry_ids(a)) if a is not None else set()
    expected_rows = set(exp.supporting_gl_rows)
    gl = _pr(supporting, expected_rows)
    gl["tool_rows"] = sorted(supporting)
    gl["expected_rows"] = sorted(expected_rows)
    gl["missing_rows"] = sorted(expected_rows - supporting)
    gl["extra_rows"] = sorted(supporting - expected_rows)
    surfaced = _rows(surfaced_entry_ids(a)) if a is not None else set()
    target = expected_rows | set(exp.related_gl_rows)
    gl["surfaced"] = _ratio(len(surfaced & target), len(target))
    gl["unsurfaced_rows"] = sorted(target - surfaced)
    return gl


def _score_docs(exp: ExpectedAdjustment, a: Optional[AdjustmentAssessment]) -> dict[str, Any]:
    tool_docs = tool_supporting_docs(a) if a is not None else set()
    expected_docs = set(exp.supporting_docs)
    docs = _pr(tool_docs, expected_docs)
    docs["tool"] = sorted(tool_docs)
    docs["expected"] = sorted(expected_docs)
    docs["missing"] = sorted(expected_docs - tool_docs)
    docs["extra"] = sorted(tool_docs - expected_docs)
    surfaced = surfaced_doc_ids(a) if a is not None else set()
    target = expected_docs | set(exp.related_docs)
    docs["surfaced"] = _ratio(len(surfaced & target), len(target))
    docs["unsurfaced"] = sorted(target - surfaced)
    return docs


def _score_adjustment(exp: ExpectedAdjustment, a: Optional[AdjustmentAssessment], labels: list[str]) -> dict[str, Any]:
    tool_t = a.treatment if a is not None else None
    expected_t = exp.treatment
    treatment_correct = tool_t == expected_t
    false_accept = tool_t == Treatment.ACCEPT and expected_t != Treatment.ACCEPT

    proposed = dict(a.proposed) if a is not None else {}
    claimed = dict(a.claimed) if a is not None else {}
    amount_scored = a is not None and expected_t != Treatment.REQUEST_INFO and tool_t != Treatment.REQUEST_INFO
    amount_diffs: dict[str, str] = {}
    amount_correct: Optional[bool] = None
    if amount_scored:
        for p in _period_keys(labels, exp.amounts):
            amount_diffs[p] = fmt(D(proposed.get(p)) - D(exp.amounts.get(p)))
        amount_correct = all(abs(D(v)) <= AMOUNT_TOLERANCE for v in amount_diffs.values())

    gl = _score_gl(exp, a)
    docs = _score_docs(exp, a)

    expected_flags = _unique(f.value for f in exp.expected_flags)
    raised = _unique(f.code.value for f in a.flags) if a is not None else []
    missing_flags = [f for f in expected_flags if f not in raised]
    missed_challenges = [f for f in missing_flags if FlagCode(f) in CHALLENGE_FLAGS]

    if a is None:
        verdict = "NOT_ASSESSED"
    elif false_accept:
        verdict = "FALSE_ACCEPT"
    elif not treatment_correct:
        verdict = "WRONG_TREATMENT"
    elif amount_correct is False:
        verdict = "WRONG_AMOUNT"
    elif missing_flags:
        verdict = "MISSED_FLAG"
    else:
        verdict = "PASS"

    return {
        "adj_id": exp.adj_id,
        "title": a.title if a is not None else "",
        "case_type": exp.case_type,
        "ambiguity": exp.ambiguity,
        "expected_treatment": expected_t.value,
        "tool_treatment": tool_t.value if tool_t is not None else None,
        "tool_confidence": a.confidence if a is not None else None,
        "treatment_correct": treatment_correct,
        "false_accept": false_accept,
        "claimed": claimed,
        "expected_amounts": dict(exp.amounts),
        "proposed_amounts": proposed,
        "amount_scored": amount_scored,
        "amount_correct": amount_correct,
        "amount_diffs": amount_diffs,
        "gl_links": gl,
        "doc_links": docs,
        "flags": {
            "expected": expected_flags,
            "raised": raised,
            "missing": missing_flags,
            "unexpected": [f for f in raised if f not in expected_flags],
        },
        "missed_challenge_flags": missed_challenges,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Diligence-identified items (SPEC §5.7)
# ---------------------------------------------------------------------------


def _greedy_pairs(scores: list[tuple[int, int, int]], taken_exp: set[int], taken_tool: set[int]) -> list[tuple[int, int]]:
    """One-to-one pairs from (overlap, exp index, tool index), largest overlap first."""
    out: list[tuple[int, int]] = []
    for _, i, j in sorted(scores, key=lambda t: (-t[0], t[1], t[2])):
        if i in taken_exp or j in taken_tool:
            continue
        taken_exp.add(i)
        taken_tool.add(j)
        out.append((i, j))
    return out


def match_diligence_items(
    expected: list[ExpectedAdjustment], tool: list[AdjustmentAssessment]
) -> list[tuple[int, int, str]]:
    """(expected index, tool index, basis) for every matched pair.

    First on shared supporting GL rows; then, for items still unmatched, on any
    shared GL row (key supporting + related vs every row the tool item links),
    which catches a duplicate whose other posting the tool chose to reverse.
    """
    taken_exp: set[int] = set()
    taken_tool: set[int] = set()
    tool_supporting = [_rows(supporting_entry_ids(a)) for a in tool]
    tool_linked = [_rows(surfaced_entry_ids(a)) for a in tool]
    first = [
        (len(set(exp.supporting_gl_rows) & tool_supporting[j]), i, j)
        for i, exp in enumerate(expected)
        for j in range(len(tool))
    ]
    pairs = [(i, j, "supporting_rows") for i, j in _greedy_pairs([t for t in first if t[0]], taken_exp, taken_tool)]
    second = [
        (len((set(exp.supporting_gl_rows) | set(exp.related_gl_rows)) & tool_linked[j]), i, j)
        for i, exp in enumerate(expected)
        if i not in taken_exp
        for j in range(len(tool))
        if j not in taken_tool
    ]
    pairs += [(i, j, "linked_rows") for i, j in _greedy_pairs([t for t in second if t[0]], taken_exp, taken_tool)]
    return sorted(pairs)


def _score_diligence_items(wp: Workpaper, gt: GroundTruth, labels: list[str]) -> dict[str, Any]:
    expected = list(gt.diligence_items)
    tool = [a for a in wp.assessments if is_diligence_item(a)]
    matched = {i: (j, basis) for i, j, basis in match_diligence_items(expected, tool)}
    used = {j for j, _ in matched.values()}
    items: list[dict[str, Any]] = []
    for i, exp in enumerate(expected):
        j, basis = matched.get(i, (None, None))
        a = tool[j] if j is not None else None
        diffs: dict[str, str] = {}
        correct = False
        if a is not None:
            proposed = a.proposed if a.treatment != Treatment.REQUEST_INFO else {}
            for p in _period_keys(labels, exp.amounts, proposed):
                diffs[p] = fmt(D(proposed.get(p)) - D(exp.amounts.get(p)))
            correct = all(abs(D(v)) <= AMOUNT_TOLERANCE for v in diffs.values())
        raised = _unique(f.code.value for f in a.flags) if a is not None else []
        expected_flags = _unique(f.value for f in exp.expected_flags)
        items.append(
            {
                "key_id": exp.adj_id,
                "tool_id": a.adj_id if a is not None else None,
                "title": a.title if a is not None else "",
                "match_basis": basis,
                "case_type": exp.case_type,
                "ambiguity": exp.ambiguity,
                "expected_treatment": exp.treatment.value,
                "tool_treatment": a.treatment.value if a is not None else None,
                "expected_amounts": dict(exp.amounts),
                "proposed_amounts": dict(a.proposed) if a is not None else {},
                "amount_diffs": diffs,
                "correct": correct,
                "gl_links": _score_gl(exp, a),
                "doc_links": _score_docs(exp, a),
                "flags": {
                    "expected": expected_flags,
                    "raised": raised,
                    "missing": [f for f in expected_flags if f not in raised],
                },
                "verdict": "MISSED" if a is None else ("CORRECT" if correct else "WRONG_AMOUNT"),
            }
        )
    for j, a in enumerate(tool):
        if j in used:
            continue
        items.append(
            {
                "key_id": None,
                "tool_id": a.adj_id,
                "title": a.title,
                "match_basis": None,
                "tool_treatment": a.treatment.value,
                "proposed_amounts": dict(a.proposed),
                "tool_rows": sorted(_rows(supporting_entry_ids(a))),
                "correct": False,
                "verdict": "EXTRA",
            }
        )
    out = _ratio(sum(1 for r in items if r["correct"]), len(items))
    out["expected"] = len(expected)
    out["tool"] = len(tool)
    out["matched"] = len(matched)
    out["missed"] = [r["key_id"] for r in items if r["verdict"] == "MISSED"]
    out["extra"] = [r["tool_id"] for r in items if r["verdict"] == "EXTRA"]
    out["items"] = items
    return out


# ---------------------------------------------------------------------------
# Data quality and EBITDA
# ---------------------------------------------------------------------------


def _dq_matches(exp: ExpectedDataQuality, issue: DataQualityIssue) -> bool:
    if issue.code != exp.code:
        return False
    specified = bool(exp.month or exp.account or exp.gl_rows)
    checks: list[bool] = []
    if exp.month and issue.month:
        checks.append(exp.month == issue.month)
    if exp.account and issue.account:
        checks.append(exp.account == issue.account)
    if exp.gl_rows and issue.entry_ids:
        checks.append(bool(set(exp.gl_rows) & _rows(issue.entry_ids)))
    if not specified:
        return True
    return bool(checks) and all(checks)


def _score_data_quality(wp: Workpaper, gt: GroundTruth) -> dict[str, Any]:
    items = []
    for exp in gt.data_quality:
        match = next((i for i in wp.reconciliation.issues if _dq_matches(exp, i)), None)
        items.append(
            {
                "code": exp.code.value,
                "month": exp.month,
                "account": exp.account,
                "note": exp.note,
                "detected": match is not None,
                "matched_message": match.message if match is not None else "",
            }
        )
    out = _ratio(sum(1 for i in items if i["detected"]), len(items))
    out["items"] = items
    return out


def _bridge_value(wp: Workpaper, key: str, label: str) -> Optional[str]:
    for row in wp.bridge.rows:
        if row.key == key:
            return row.amounts.get(label)
    return None


def _score_ebitda(wp: Workpaper, gt: GroundTruth, labels: list[str]) -> dict[str, Any]:
    by_period: dict[str, dict[str, Any]] = {}
    worst: Optional[Decimal] = None
    for label in labels:
        comps = wp.reconciliation.gl_ebitda.get(label)
        tool_gl = D(comps.ebitda) if comps is not None else None
        carried = [a for a in wp.assessments if a.treatment != Treatment.REQUEST_INFO]
        tool_mgmt = dsum(a.proposed.get(label) for a in carried if not is_diligence_item(a))
        tool_items = dsum(a.proposed.get(label) for a in carried if is_diligence_item(a))
        tool_dil = tool_gl + tool_mgmt + tool_items if tool_gl is not None else None
        exp_items = dsum(x.amounts.get(label) for x in gt.diligence_items if x.treatment != Treatment.REQUEST_INFO)
        exp_gl = gt.gl_ebitda.get(label)
        exp_dil = gt.diligence_adjusted_ebitda.get(label)
        abs_error = abs(tool_dil - D(exp_dil)) if tool_dil is not None and exp_dil is not None else None
        gl_diff = tool_gl - D(exp_gl) if tool_gl is not None and exp_gl is not None else None
        bridge = _bridge_value(wp, "diligence_adjusted_ebitda", label)
        if abs_error is not None and (worst is None or abs_error > worst):
            worst = abs_error
        by_period[label] = {
            "tool_gl_ebitda": fmt(tool_gl) if tool_gl is not None else None,
            "expected_gl_ebitda": fmt(exp_gl) if exp_gl is not None else None,
            "gl_ebitda_diff": fmt(gl_diff) if gl_diff is not None else None,
            "gl_ebitda_agrees": abs(gl_diff) <= AMOUNT_TOLERANCE if gl_diff is not None else None,
            "tool_management_adjustments": fmt(tool_mgmt),
            "tool_diligence_items": fmt(tool_items),
            "expected_diligence_items": fmt(exp_items),
            "tool_diligence_adjusted_ebitda": fmt(tool_dil) if tool_dil is not None else None,
            "expected_diligence_adjusted_ebitda": fmt(exp_dil) if exp_dil is not None else None,
            "abs_error": fmt(abs_error) if abs_error is not None else None,
            "within_tolerance": abs_error <= AMOUNT_TOLERANCE if abs_error is not None else None,
            "bridge_diligence_adjusted_ebitda": bridge,
            "bridge_matches_proposals": (
                abs(D(bridge) - tool_dil) <= AMOUNT_TOLERANCE if bridge is not None and tool_dil is not None else None
            ),
        }
    return {"by_period": by_period, "max_abs_error": fmt(worst) if worst is not None else None}


def _grouped_accuracy(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        groups[str(r.get(key) or "not_assessed")].append(r["treatment_correct"])
    return {k: _ratio(sum(v), len(v)) for k, v in sorted(groups.items())}


# ---------------------------------------------------------------------------
# Public scoring API
# ---------------------------------------------------------------------------


def score(wp: Workpaper, gt: GroundTruth) -> dict[str, Any]:
    """Every SPEC §9 metric for one deal, plus per-adjustment detail rows.

    Rate metrics are ``{"num", "den", "rate"}`` (rate is None when den is 0).
    Money is a 2-dp string.
    """
    if wp.deal.deal_id != gt.deal_id:
        raise ValueError(f"workpaper is for {wp.deal.deal_id!r} but the answer key is for {gt.deal_id!r}")
    labels = [p.label for p in wp.deal.periods]
    # Management-item metrics never see diligence-identified items (scored on their own below).
    management = [a for a in wp.assessments if not is_diligence_item(a)]
    by_id: dict[str, AdjustmentAssessment] = {}
    for a in management:
        by_id.setdefault(a.adj_id, a)
    rows = [_score_adjustment(exp, by_id.get(exp.adj_id), labels) for exp in gt.adjustments]
    expected_ids = {exp.adj_id for exp in gt.adjustments}

    scored_amounts = [r for r in rows if r["amount_scored"]]
    false_accept = _ratio(
        sum(1 for r in rows if r["false_accept"]),
        sum(1 for r in rows if r["expected_treatment"] != Treatment.ACCEPT.value),
    )
    false_accept["adj_ids"] = [r["adj_id"] for r in rows if r["false_accept"]]
    missed = [
        {"adj_id": r["adj_id"], "flag": f, "tool_treatment": r["tool_treatment"]}
        for r in rows
        for f in r["missed_challenge_flags"]
    ]
    expected_challenges = sum(1 for r in rows for f in r["flags"]["expected"] if FlagCode(f) in CHALLENGE_FLAGS)
    missed_ratio = _ratio(len(missed), expected_challenges)
    missed_ratio["items"] = missed

    def link_ratio(section: str, which: str) -> dict[str, Any]:
        tp = sum(r[section]["tp"] for r in rows)
        other = sum(r[section]["fp" if which == "precision" else "fn"] for r in rows)
        return _ratio(tp, tp + other)

    return {
        "deal_id": gt.deal_id,
        "split": gt.split,
        "run_id": wp.run_id,
        "tool_version": wp.tool_version,
        "ai_mode": wp.ai_mode,
        "period_labels": labels,
        "n_adjustments": len(rows),
        "treatment_accuracy": _ratio(sum(1 for r in rows if r["treatment_correct"]), len(rows)),
        "amount_accuracy": _ratio(sum(1 for r in scored_amounts if r["amount_correct"]), len(scored_amounts)),
        "false_accept_rate": false_accept,
        "gl_link_precision": link_ratio("gl_links", "precision"),
        "gl_link_recall": link_ratio("gl_links", "recall"),
        "gl_surfaced_recall": _sum_ratios(r["gl_links"]["surfaced"] for r in rows),
        "doc_link_precision": link_ratio("doc_links", "precision"),
        "doc_link_recall": link_ratio("doc_links", "recall"),
        "doc_surfaced_recall": _sum_ratios(r["doc_links"]["surfaced"] for r in rows),
        "flag_recall": _ratio(
            sum(len(r["flags"]["expected"]) - len(r["flags"]["missing"]) for r in rows),
            sum(len(r["flags"]["expected"]) for r in rows),
        ),
        "missed_contradictions": missed_ratio,
        "data_quality_recall": _score_data_quality(wp, gt),
        "n_diligence_items": len(gt.diligence_items),
        "diligence_item_accuracy": _score_diligence_items(wp, gt, labels),
        "ebitda_error": _score_ebitda(wp, gt, labels),
        "by_case_type": _grouped_accuracy(rows, "case_type"),
        "by_confidence": _grouped_accuracy(rows, "tool_confidence"),
        "by_ambiguity": _grouped_accuracy(rows, "ambiguity"),
        "verdicts": dict(sorted(Counter(r["verdict"] for r in rows).items())),
        "adjustments": rows,
        "unscored_tool_adjustments": sorted(a.adj_id for a in management if a.adj_id not in expected_ids),
    }


def aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool per-deal scores: counts are summed, so rates are micro-averages."""
    out: dict[str, Any] = {
        "deals": [s["deal_id"] for s in scores],
        "n_adjustments": sum(s["n_adjustments"] for s in scores),
        "n_diligence_items": sum(s.get("n_diligence_items", 0) for s in scores),
    }
    for key in RATIO_KEYS:
        out[key] = _sum_ratios(s[key] for s in scores if key in s)
    out["diligence_item_accuracy"]["items"] = [
        {"deal_id": s["deal_id"], **item}
        for s in scores
        for item in s.get("diligence_item_accuracy", {}).get("items", [])
        if item["verdict"] != "CORRECT"
    ]
    out["false_accept_rate"]["items"] = [
        {"deal_id": s["deal_id"], "adj_id": adj_id} for s in scores for adj_id in s["false_accept_rate"]["adj_ids"]
    ]
    out["missed_contradictions"]["items"] = [
        {"deal_id": s["deal_id"], **item} for s in scores for item in s["missed_contradictions"]["items"]
    ]
    out["data_quality_recall"]["missed"] = [
        {"deal_id": s["deal_id"], **item}
        for s in scores
        for item in s["data_quality_recall"]["items"]
        if not item["detected"]
    ]
    rows = [r for s in scores for r in s["adjustments"]]
    out["by_case_type"] = _grouped_accuracy(rows, "case_type")
    out["by_confidence"] = _grouped_accuracy(rows, "tool_confidence")
    out["by_ambiguity"] = _grouped_accuracy(rows, "ambiguity")
    out["verdicts"] = dict(sorted(Counter(r["verdict"] for r in rows).items()))
    worst: Optional[Decimal] = None
    by_deal: dict[str, dict[str, Optional[str]]] = {}
    for s in scores:
        by_deal[s["deal_id"]] = {p: v["abs_error"] for p, v in s["ebitda_error"]["by_period"].items()}
        m = s["ebitda_error"]["max_abs_error"]
        if m is not None and (worst is None or D(m) > worst):
            worst = D(m)
    out["ebitda_error"] = {"max_abs_error": fmt(worst) if worst is not None else None, "by_deal": by_deal}
    return out


def build_report(split: str, scores: list[dict[str, Any]], ai_mode: str) -> dict[str, Any]:
    """The eval_<split>.json payload: disclaimer, per-deal scores, overall pool."""
    versions = sorted({s["tool_version"] for s in scores})
    return {
        "split": split,
        "ai_mode": ai_mode,
        "tool_version": versions[0] if len(versions) == 1 else versions,
        "disclaimer": DISCLAIMER,
        "deals": scores,
        "overall": aggregate(scores),
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def _money(value: Optional[str]) -> str:
    if value is None:
        return "n/a"
    d = D(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if d == 0:
        return "0"
    return f"({abs(d):,})" if d < 0 else f"{d:,}"


def _amounts(m: dict[str, str], labels: list[str], assessed: bool = True) -> str:
    if not assessed:
        return "-"
    if not m:
        return "none (pending)"
    return " / ".join(_money(m.get(p, "0")) for p in labels)


def _pct(r: dict[str, Any]) -> str:
    if r["rate"] is None:
        return "n/a"
    return f"{r['rate'] * 100:.1f}%"


def _frac(r: dict[str, Any]) -> str:
    return f"{r['num']}/{r['den']}"


def _pr_text(section: dict[str, Any]) -> str:
    p = "n/a" if section["precision"] is None else f"{section['precision']:.2f}"
    r = "n/a" if section["recall"] is None else f"{section['recall']:.2f}"
    return f"{p} / {r}"


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    """Human-readable eval report. Leads with false accepts and misses."""
    overall = report["overall"]
    deals = report["deals"]
    lines: list[str] = []
    add = lines.append
    add(f"# QoE Evidence Review: automated evaluation ({report['split']})")
    add("")
    add(f"> **Read this first.** {report['disclaimer']}")
    add("")
    add(
        f"- Deals: {len(deals)} ({', '.join(overall['deals']) or 'none'}); management adjustments scored: "
        f"{overall['n_adjustments']}; diligence-identified items in the keys: {overall.get('n_diligence_items', 0)}"
    )
    add(f"- AI mode: `{report['ai_mode']}`; tool version: `{report['tool_version']}`")
    for s in deals:
        add(f"- {s['deal_id']}: amount columns read `{' / '.join(s['period_labels'])}` (USD)")
    add("")

    fa = overall["false_accept_rate"]
    add("## 1. False accepts")
    add("")
    add(
        "The tool proposed ACCEPT where the answer key says REVISE, REJECT or REQUEST_INFO. "
        "This is the costliest error: an unsupported add-back would reach the buyer's EBITDA "
        "if the reviewer relied on the proposal."
    )
    add("")
    add(f"**{fa['num']} false accept(s) out of {fa['den']} adjustments that needed challenge ({_pct(fa)}).**")
    add("")
    fa_rows = [(s, r) for s in deals for r in s["adjustments"] if r["false_accept"]]
    if fa_rows:
        add("| Deal | Ref | Case type | Answer key | Key amounts | Tool amounts | Missing flags |")
        add("| --- | --- | --- | --- | --- | --- | --- |")
        for s, r in fa_rows:
            labels = s["period_labels"]
            add(
                f"| {s['deal_id']} | {_cell(r['adj_id'])} | {r['case_type']} | {r['expected_treatment']} | "
                f"{_amounts(r['expected_amounts'], labels)} | {_amounts(r['proposed_amounts'], labels)} | "
                f"{', '.join(r['flags']['missing']) or '-'} |"
            )
    else:
        add("None.")
    add("")

    add("## 2. Misses")
    add("")
    mc = overall["missed_contradictions"]
    add(f"### Missed challenges ({mc['num']} of {mc['den']} expected)")
    add("")
    add(
        "Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, "
        "OVERLAP_WITH_OTHER_ADJUSTMENT or ALREADY_EXCLUDED_FROM_EBITDA flags that the tool did not raise "
        "on the right adjustment."
    )
    add("")
    if mc["items"]:
        add("| Deal | Ref | Missing flag | Tool treatment |")
        add("| --- | --- | --- | --- |")
        for item in mc["items"]:
            add(
                f"| {item['deal_id']} | {_cell(item['adj_id'])} | {item['flag']} | "
                f"{item['tool_treatment'] or 'not assessed'} |"
            )
    else:
        add("None.")
    add("")
    add("### Wrong treatment or wrong amount")
    add("")
    wrong = [
        (s, r)
        for s in deals
        for r in s["adjustments"]
        if r["verdict"] in ("NOT_ASSESSED", "WRONG_TREATMENT", "WRONG_AMOUNT")
    ]
    if wrong:
        add("| Deal | Ref | Case type | Answer key | Tool | Key amounts | Tool amounts | Verdict |")
        add("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for s, r in wrong:
            labels = s["period_labels"]
            add(
                f"| {s['deal_id']} | {_cell(r['adj_id'])} | {r['case_type']} | {r['expected_treatment']} | "
                f"{r['tool_treatment'] or 'not assessed'} | {_amounts(r['expected_amounts'], labels)} | "
                f"{_amounts(r['proposed_amounts'], labels, r['tool_treatment'] is not None)} | {r['verdict']} |"
            )
    else:
        add("None.")
    add("")
    dq_missed = overall["data_quality_recall"]["missed"]
    add(f"### Missed data-quality issues ({len(dq_missed)} of {overall['data_quality_recall']['den']} planted)")
    add("")
    if dq_missed:
        add("| Deal | Code | Month | Account | Note |")
        add("| --- | --- | --- | --- | --- |")
        for item in dq_missed:
            add(
                f"| {item['deal_id']} | {item['code']} | {item['month'] or '-'} | {item['account'] or '-'} | "
                f"{_cell(item['note'])} |"
            )
    else:
        add("None.")
    add("")
    di = overall.get("diligence_item_accuracy", _ratio(0, 0))
    add(f"### Diligence-identified items ({di['num']} of {di['den']} correct)")
    add("")
    add(
        "Adjustments the tool proposes beyond management's schedule (SPEC §5.7, e.g. reversing a duplicate "
        "posting), matched to the key by shared GL rows. Correct = every period within 1.00. A key item the "
        "tool did not identify is MISSED; a tool item the key does not expect is EXTRA and counts against accuracy."
    )
    add("")
    di_rows = [(s, r) for s in deals for r in s.get("diligence_item_accuracy", {}).get("items", [])]
    if di_rows:
        add("| Deal | Key item | Tool item | Matched on | Key amounts | Tool amounts | Missing flags | Verdict |")
        add("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for s, r in di_rows:
            labels = s["period_labels"]
            key_amounts = _amounts(r["expected_amounts"], labels) if r["key_id"] is not None else "-"
            tool_amounts = (
                _amounts(r["proposed_amounts"], labels) if r["tool_id"] is not None else "-"
            )
            missing = ", ".join(r.get("flags", {}).get("missing", [])) or "-"
            basis = (r["match_basis"] or "-").replace("_", " ")
            add(
                f"| {s['deal_id']} | {_cell(r['key_id'] or '-')} | {_cell(r['tool_id'] or '-')} | {basis} | "
                f"{key_amounts} | {tool_amounts} | {missing} | {r['verdict']} |"
            )
    else:
        add("None expected, and the tool proposed none.")
    add("")
    add("### Diligence adjusted EBITDA vs answer key")
    add("")
    add(
        "Tool figure = GL EBITDA + every tool proposal that is not REQUEST_INFO, management items and "
        "diligence-identified items alike (SPEC §5.6 identity), before any reviewer decision."
    )
    add("")
    add(
        "| Deal | Period | GL EBITDA (tool) | GL EBITDA (key) | Diligence items (tool) | (key) | "
        "Diligence adj. EBITDA (tool) | (key) | Abs. error |"
    )
    add("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in deals:
        for label, v in s["ebitda_error"]["by_period"].items():
            add(
                f"| {s['deal_id']} | {label} | {_money(v['tool_gl_ebitda'])} | {_money(v['expected_gl_ebitda'])} | "
                f"{_money(v.get('tool_diligence_items'))} | {_money(v.get('expected_diligence_items'))} | "
                f"{_money(v['tool_diligence_adjusted_ebitda'])} | {_money(v['expected_diligence_adjusted_ebitda'])} | "
                f"{_money(v['abs_error'])} |"
            )
    add("")

    add("## 3. Headline accuracy")
    add("")
    add("| Metric | Result | Count | What it measures |")
    add("| --- | --- | --- | --- |")
    headline = [
        ("False accept rate", "false_accept_rate", "tool ACCEPT where the key does not accept (lower is better)"),
        ("Treatment accuracy", "treatment_accuracy", "tool treatment equals the key"),
        ("Amount accuracy", "amount_accuracy", "every period within 1.00, where neither side is REQUEST_INFO"),
        ("Missed challenges", "missed_contradictions", "expected challenge flags not raised (lower is better)"),
        ("Flag recall", "flag_recall", "expected flags raised on the right adjustment"),
        ("GL link precision", "gl_link_precision", "supporting tool links that the key also supports"),
        ("GL link recall", "gl_link_recall", "key supporting rows the tool linked as supporting"),
        ("GL surfaced recall", "gl_surfaced_recall", "key supporting + related rows shown anywhere in the evidence"),
        ("Document precision", "doc_link_precision", "documents the tool relies on that the key lists as support"),
        ("Document recall", "doc_link_recall", "key support documents the tool relies on"),
        ("Document surfaced recall", "doc_surfaced_recall", "key supporting + related documents shown anywhere"),
        ("Data-quality recall", "data_quality_recall", "planted data issues detected"),
        ("Diligence item accuracy", "diligence_item_accuracy", "items beyond management's schedule, right amounts"),
    ]
    for name, key, what in headline:
        r = overall.get(key, _ratio(0, 0))
        add(f"| {name} | {_pct(r)} | {_frac(r)} | {what} |")
    add(
        f"| Max diligence EBITDA error | {_money(overall['ebitda_error']['max_abs_error'])} | - | "
        "largest absolute error across deals and periods |"
    )
    add("")

    add("## 4. Per-case results")
    add("")
    add(
        "| Deal | Ref | Case type | Ambiguity | Key | Tool | Conf. | Key amounts | Tool amounts | "
        "GL P / R | Doc P / R | Missing flags | Verdict |"
    )
    add("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in deals:
        labels = s["period_labels"]
        for r in s["adjustments"]:
            add(
                f"| {s['deal_id']} | {_cell(r['adj_id'])} | {r['case_type']} | {r['ambiguity']} | "
                f"{r['expected_treatment']} | {r['tool_treatment'] or 'not assessed'} | "
                f"{r['tool_confidence'] or '-'} | "
                f"{_amounts(r['expected_amounts'], labels)} | "
                f"{_amounts(r['proposed_amounts'], labels, r['tool_treatment'] is not None)} | "
                f"{_pr_text(r['gl_links'])} | {_pr_text(r['doc_links'])} | "
                f"{', '.join(r['flags']['missing']) or '-'} | {r['verdict']} |"
            )
    add("")

    add("## 5. Treatment accuracy by case type")
    add("")
    add("| Case type | Correct | Accuracy |")
    add("| --- | --- | --- |")
    for ct, r in overall["by_case_type"].items():
        add(f"| {ct} | {_frac(r)} | {_pct(r)} |")
    add("")
    add("### By the tool's own confidence")
    add("")
    add("| Tool confidence | Correct | Accuracy |")
    add("| --- | --- | --- |")
    for conf, r in overall["by_confidence"].items():
        add(f"| {conf} | {_frac(r)} | {_pct(r)} |")
    add("")

    add("## 6. How these numbers are computed")
    add("")
    add(
        "- A tool GL link is *supporting* when `supports_claim` is true and the entry is not listed on a "
        "removing flag (already excluded, overlap, contradiction, continuing obligation, recurring pattern) "
        "for the same adjustment. Links map to GL rows via `GL-R<row>`."
    )
    add(
        "- *Surfaced* rows are rows shown anywhere in the adjustment's evidence (links, flag entries, "
        "recurrence observations), measured against the key's supporting and related rows."
    )
    add(
        "- The documents the tool *relies on* depend on what it carries. A non-zero amount: documents linked to "
        "supporting entries, stand-alone agreements no removing flag cites, and documents behind a recovery or "
        "out-of-period effect. Zero (REJECT): the documents that took the claim out. Pending (REQUEST_INFO): the "
        "documents the request rests on. Documents that argue against part of a carried amount are not support; "
        "*surfaced* documents (any doc link or flag citation) are measured against supporting + related documents."
    )
    add(
        "- Management-item metrics exclude diligence-identified items. Those are matched to the key one-to-one by "
        "shared supporting GL rows (then any shared GL row) and scored on amounts only; both kinds of item enter "
        "the diligence adjusted EBITDA check."
    )
    add(
        "- Deal and overall rates pool the underlying counts (micro-average). The false accept rate's "
        "denominator is the number of adjustments the key does not accept."
    )
    add("- Extra flags are not penalized; the key lists the flags that must be raised, not the only acceptable ones.")
    add("- Amounts are USD, rounded to the dollar here; the JSON report carries cents.")
    add("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reviewer corrections -> regression cases (SPEC §7 feedback loop)
# ---------------------------------------------------------------------------


def _safe(text: str) -> str:
    return _UNSAFE.sub("_", text).strip("_") or "x"


def regression_case_id(deal_id: str, adj_id: str, n: int) -> str:
    return f"{_safe(deal_id)}__{_safe(adj_id)}__{n}"


def _tool_output(a: Optional[AdjustmentAssessment]) -> Optional[dict[str, Any]]:
    if a is None:
        return None
    return {
        "source": a.source,
        "treatment": a.treatment.value,
        "confidence": a.confidence,
        "claimed": dict(a.claimed),
        "traced_gl": dict(a.traced_gl),
        "proposed": dict(a.proposed),
        "flags": [
            {
                "code": f.code.value,
                "severity": f.severity.value,
                "gl_rows": sorted(_rows(f.entry_ids)),
                "message": f.message,
            }
            for f in a.flags
        ],
        "supporting_gl_rows": sorted(_rows(supporting_entry_ids(a))),
        "linked_gl_rows": sorted(_rows(link.entry_id for link in a.gl_links)),
        "doc_ids": sorted({dl.doc_id for dl in a.doc_links}),
        "rationale": a.rationale,
    }


def regression_cases(
    wp: Workpaper, decisions: list[ReviewDecision], deal_dir: Optional[str] = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Turn tool-error corrections into regression cases; summarize the rest.

    Every decision (not only the latest per adjustment) whose correction type
    is a tool error becomes one case, numbered per adjustment in log order.
    JUDGMENT_DIFFERENCE and NEW_INFORMATION are reviewer calls, not tool
    defects, so they are summarized but never become cases.
    """
    by_id = {a.adj_id: a for a in wp.assessments}
    counters: Counter[str] = Counter()
    cases: list[dict[str, Any]] = []
    judgment: list[dict[str, Any]] = []
    by_type: Counter[str] = Counter()
    for line_no, d in enumerate(decisions, start=1):
        by_type[d.correction_type.value] += 1
        if d.correction_type in TOOL_ERROR_CORRECTIONS:
            counters[d.adj_id] += 1
            n = counters[d.adj_id]
            a = by_id.get(d.adj_id)
            tool = _tool_output(a)
            changed = tool is not None and (
                tool["treatment"] != d.tool_treatment.value or tool["proposed"] != dict(d.tool_amounts)
            )
            cases.append(
                {
                    "schema": "qoe_regression_case/v1",
                    "case_id": regression_case_id(wp.deal.deal_id, d.adj_id, n),
                    "inputs": {
                        "deal_dir": deal_dir,
                        "deal_id": wp.deal.deal_id,
                        "adj_id": d.adj_id,
                        "run_id": wp.run_id,
                        "tool_version": wp.tool_version,
                        "ai_mode": wp.ai_mode,
                        "input_hashes": dict(wp.input_hashes),
                    },
                    "tool_output": tool,
                    "tool_output_seen_by_reviewer": {
                        "treatment": d.tool_treatment.value,
                        "amounts": dict(d.tool_amounts),
                    },
                    "tool_output_changed_since_review": changed,
                    "expected": {"treatment": d.treatment.value, "amounts": dict(d.amounts)},
                    "correction_type": d.correction_type.value,
                    "rationale": d.rationale,
                    "reviewer": d.reviewer,
                    "reviewed_at": d.timestamp,
                    "review_log_line": line_no,
                }
            )
        elif d.correction_type in (CorrectionType.JUDGMENT_DIFFERENCE, CorrectionType.NEW_INFORMATION):
            judgment.append(
                {
                    "adj_id": d.adj_id,
                    "correction_type": d.correction_type.value,
                    "tool_treatment": d.tool_treatment.value,
                    "reviewer_treatment": d.treatment.value,
                    "rationale": d.rationale,
                }
            )
    summary = {
        "deal_id": wp.deal.deal_id,
        "decisions": len(decisions),
        "by_correction_type": dict(sorted(by_type.items())),
        "regression_cases": [c["case_id"] for c in cases],
        "judgment_and_new_information": judgment,
    }
    return cases, summary


__all__ = [
    "AMOUNT_TOLERANCE",
    "CHALLENGE_FLAGS",
    "DISCLAIMER",
    "REMOVING_FLAGS",
    "aggregate",
    "build_report",
    "entry_row",
    "is_diligence_item",
    "load_ground_truth",
    "match_diligence_items",
    "regression_case_id",
    "regression_cases",
    "removed_entry_ids",
    "render_markdown",
    "score",
    "supporting_entry_ids",
    "surfaced_doc_ids",
    "surfaced_entry_ids",
    "tool_supporting_docs",
]
