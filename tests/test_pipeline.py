import json
import tempfile
from pathlib import Path

import pytest

from app.adapters.local_erp import LocalERPAdapter
from app.database import init_db, reset_db
from app.llm_client import MockLLMClient
from app.pipeline import Pipeline, run_case_dir
from app.schemas import WorkflowDecision

REPO = Path(__file__).resolve().parents[1]


def _init_with_fixtures(db_url: str):
    import subprocess
    import sys

    subprocess.check_call(
        [sys.executable, str(REPO / "scripts" / "initialize_database.py"), "--reset", "--database-url", db_url],
        cwd=str(REPO),
    )
    return init_db(db_url)


@pytest.fixture()
def erp_db(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    sf = _init_with_fixtures(db_url)
    return LocalERPAdapter(sf), db_url, sf


def test_pipeline_exact_match_ready(erp_db):
    erp, _, _ = erp_db
    case_dir = REPO / "tests" / "fixtures" / "development" / "case_001"
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
    expected = json.loads((case_dir / "expected.json").read_text())
    assert result.decision.value == expected["decision"]
    assert result.exception_codes == []
    assert result.proposed_journal is not None
    assert result.proposed_journal.balanced


def test_pipeline_price_over_review(erp_db):
    erp, _, _ = erp_db
    case_dir = REPO / "tests" / "fixtures" / "development" / "case_021"
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
    assert result.decision == WorkflowDecision.HUMAN_REVIEW
    assert "PRICE_VARIANCE" in result.exception_codes


def test_pipeline_duplicate(erp_db):
    erp, _, _ = erp_db
    case_dir = REPO / "tests" / "fixtures" / "holdout" / "case_031"
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
    assert result.decision == WorkflowDecision.HUMAN_REVIEW
    assert "DUPLICATE_INVOICE" in result.exception_codes


def test_idempotent_create_draft(erp_db):
    erp, db_url, sf = erp_db
    case_dir = REPO / "tests" / "fixtures" / "development" / "case_001"
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    r1 = run_case_dir(case_dir, erp=erp, llm=llm, mode="create_draft")
    assert r1.decision == WorkflowDecision.READY_FOR_DRAFT
    assert r1.draft_bill_id
    r2 = run_case_dir(case_dir, erp=erp, llm=llm, mode="create_draft")
    assert r2.idempotency_key == r1.idempotency_key
    assert r2.draft_bill_id == r1.draft_bill_id


def test_development_cases_decisions(erp_db):
    erp, _, _ = erp_db
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    root = REPO / "tests" / "fixtures" / "development"
    failures = []
    for case_dir in sorted(root.glob("case_*")):
        expected = json.loads((case_dir / "expected.json").read_text())
        result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
        if result.decision.value != expected["decision"]:
            failures.append((case_dir.name, expected["decision"], result.decision.value, result.exception_codes))
            continue
        exp_codes = set(expected.get("exception_codes") or [])
        got = set(result.exception_codes)
        if expected["decision"] == "READY_FOR_DRAFT":
            if got:
                failures.append((case_dir.name, "no codes", sorted(got), result.exception_codes))
        else:
            if not exp_codes.issubset(got):
                failures.append((case_dir.name, sorted(exp_codes), sorted(got), "codes"))
    assert failures == []


def test_holdout_cases_decisions(erp_db):
    erp, _, _ = erp_db
    llm = MockLLMClient(fixture_root=REPO / "tests" / "fixtures")
    root = REPO / "tests" / "fixtures" / "holdout"
    failures = []
    for case_dir in sorted(root.glob("case_*")):
        expected = json.loads((case_dir / "expected.json").read_text())
        result = run_case_dir(case_dir, erp=erp, llm=llm, mode="evaluate")
        if result.decision.value != expected["decision"]:
            failures.append((case_dir.name, expected["decision"], result.decision.value, result.exception_codes))
            continue
        exp_codes = set(expected.get("exception_codes") or [])
        got = set(result.exception_codes)
        if expected["decision"] == "READY_FOR_DRAFT":
            if got:
                failures.append((case_dir.name, "no codes", sorted(got), result.exception_codes))
        else:
            if not exp_codes.issubset(got):
                failures.append((case_dir.name, sorted(exp_codes), sorted(got), "codes"))
    assert failures == []
