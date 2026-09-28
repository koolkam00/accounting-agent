"""Synthetic QoE deal-package generator.

``generate_deal(spec, out_root)`` turns a YAML deal spec into a deal package in
the SPEC §3 layout under ``<out_root>/<deal_id>/``. Output is deterministic:
the same spec always yields byte-identical files.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml

from qoe.money import ZERO, D, fmt, q2
from qoe.periods import labels_for_month, month_range, months_in
from qoe.schemas import DealMeta, EbitdaClass, GroundTruth, PeriodDef

from .accounts import AccountInfo, build_accounts
from .documents import FOOTER, render_document
from .gl_writers import write_chart_of_accounts, write_gl
from .ledger import GenerationError, Ledger, build_ledger, ebitda_components, pl_by_month, resolve_keys
from .spec import DealSpec, load_spec
from .truth import TruthEffects, build_ground_truth
from .workbooks import write_monthly_pl, write_schedule

__all__ = ["GenerationError", "GenerationResult", "DealSpec", "generate_deal", "load_spec"]

PL_REL = "financials/monthly_pl.xlsx"
SCHEDULE_REL = "adjustments/management_adjusted_ebitda.xlsx"
GENERATED = ("deal.yaml", "ground_truth.json", "README.txt", "gl", "financials", "adjustments", "documents")


@dataclass
class GenerationResult:
    deal_dir: Path
    spec: DealSpec
    accounts: dict[str, AccountInfo]
    ledger: Ledger
    key_rows: dict[str, int]  # planted/background key -> GL source row
    gl_path: str
    documents: dict[str, str]  # document id -> relpath
    truth: GroundTruth
    effects: dict[str, TruthEffects]
    gl_ebitda: dict[str, dict[str, Decimal]]
    mgmt: dict[str, dict[str, Decimal]]  # what the schedule printed
    revenue: dict[str, Decimal]  # net revenue per period label (credit shown positive)


def _clean(deal_dir: Path) -> None:
    # Only remove what the generator writes, never the whole directory.
    for name in GENERATED:
        path = deal_dir / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def _deal_yaml(spec: DealSpec, gl_rel: str, coa_rel: str, overrides_rel: str | None) -> str:
    q = json.dumps  # JSON strings are valid YAML double-quoted scalars
    lines = [
        f"deal_id: {spec.deal_id}",
        f"target_name: {q(spec.company.name)}",
        f"industry: {q(spec.company.industry)}",
        "synthetic: true",
        f"currency: {spec.currency}",
        "periods:",
        *[f"  - {{label: {q(p.label)}, start: {q(p.start)}, end: {q(p.end)}}}" for p in spec.periods],
        f"data_start: {q(spec.data_start)}",
        f"data_end: {q(spec.data_end)}",
        f"gl_format: {spec.deal_yaml_gl_format}",
        "files:",
        f"  gl: {gl_rel}",
        f"  chart_of_accounts: {coa_rel}",
        *([f"  account_mapping_overrides: {overrides_rel}"] if overrides_rel else []),
        f"  monthly_pl: {PL_REL}",
        f"  adjustments: {SCHEDULE_REL}",
        "  documents_dir: documents",
        f"tolerance: {q(spec.tolerance)}",
    ]
    return "\n".join(lines) + "\n"


def _readme(spec: DealSpec, gl_rel: str, n_rows: int, n_docs: int) -> str:
    return f"""SYNTHETIC DEAL PACKAGE - NOT REAL DATA
{FOOTER}

Target: {spec.company.name} (fictional)
Industry: {spec.company.industry}
Split: {spec.split}

Every company, person, amount, and document in this package is synthetic. It was
generated deterministically from data/specs/{spec.deal_id}.yaml by
scripts/qoe_generate_deals.py for testing the QoE Evidence Review tool. Any
resemblance to real businesses or people is coincidental.

Contents
  deal.yaml                                     deal metadata (periods, file map)
  {gl_rel:<46}general ledger export ({spec.gl_format}, {n_rows} rows, P&L accounts only)
  gl/chart_of_accounts.csv                      chart of accounts
  {PL_REL:<46}management's monthly P&L
  {SCHEDULE_REL:<46}management's adjusted EBITDA schedule
  documents/                                    data-room documents ({n_docs} files)
  ground_truth.json                             answer key: evaluation only; the review pipeline must never read it

{spec.readme_extra.strip()}

Regenerate:
  uv run python scripts/qoe_generate_deals.py --spec data/specs/{spec.deal_id}.yaml --out data/{spec.split}
"""


def generate_deal(spec: DealSpec | Path | str, out_root: Path | str) -> GenerationResult:
    if not isinstance(spec, DealSpec):
        spec = load_spec(spec)
    deal_dir = Path(out_root) / spec.deal_id
    _clean(deal_dir)
    deal_dir.mkdir(parents=True, exist_ok=True)

    accounts = build_accounts(spec.accounts)
    ledger = build_ledger(spec, accounts)
    gl_txns = ledger.gl_txns()
    gl_rel, key_rows = write_gl(deal_dir, spec, accounts, gl_txns)
    coa_rel, overrides_rel = write_chart_of_accounts(deal_dir, spec, accounts)

    months = month_range(spec.data_start, spec.data_end)
    periods = [PeriodDef(label=p.label, start=p.start, end=p.end) for p in spec.periods]
    labels = [p.label for p in periods]
    pl_amounts = pl_by_month(ledger, accounts, include_topside=True)
    write_monthly_pl(deal_dir / PL_REL, spec, accounts, pl_amounts, months)

    gl_amounts = pl_by_month(ledger, accounts, include_topside=False, gl_only=True)
    gl_comp = {p.label: ebitda_components(gl_amounts, accounts, months_in(p)) for p in periods}
    basis = pl_amounts if spec.schedule.basis == "pl" else gl_amounts
    mgmt_comp = {p.label: ebitda_components(basis, accounts, months_in(p)) for p in periods}

    gl_keys = sorted(key_rows, key=lambda k: key_rows[k])
    by_key = ledger.by_key()
    claims: dict[str, dict[str, Decimal]] = {}
    for adj in spec.schedule.adjustments:
        claims[adj.ref] = {l: q2(D(adj.amounts[l])) for l in labels}
        if adj.claim_keys:
            traced = {l: ZERO for l in labels}
            for k in resolve_keys(adj.claim_keys, gl_keys, f"schedule {adj.ref} claim_keys"):
                for l in labels_for_month(by_key[k].month, periods):
                    traced[l] += by_key[k].amount
            for l in adj.claim_periods or labels:
                if abs(traced[l] - claims[adj.ref][l]) > Decimal("0.005"):
                    raise GenerationError(f"schedule {adj.ref}: claimed {l} {claims[adj.ref][l]} but claim_keys total {traced[l]}")
    mgmt = write_schedule(deal_dir / SCHEDULE_REL, spec, mgmt_comp, claims)

    all_keys = [t.key for t in ledger.txns]
    documents: dict[str, str] = {}
    for doc in spec.documents:
        rendered = render_document(spec, doc, by_key)
        rel = "/".join(x for x in ("documents", doc.folder, doc.filename) if x)
        path = deal_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(rendered.data)
        documents[doc.id] = rel
        supported = resolve_keys(doc.supports, all_keys, f"document {doc.id} supports") if doc.supports else []
        if rendered.stated_total is not None and supported and doc.check_total:
            booked = sum((abs(by_key[k].amount) for k in supported), ZERO)
            if booked != rendered.stated_total:
                raise GenerationError(f"document {doc.id}: invoice total {rendered.stated_total} != supported GL rows {booked}")

    truth, effects = build_ground_truth(
        spec,
        ledger,
        key_rows,
        {d.id: d.filename for d in spec.documents},
        {l: gl_comp[l]["ebitda"] for l in labels},
        mgmt["reported_ebitda"],
        accounts,
    )
    (deal_dir / "ground_truth.json").write_text(truth.model_dump_json(indent=2) + "\n", encoding="utf-8")

    deal_text = _deal_yaml(spec, gl_rel, coa_rel, overrides_rel)
    DealMeta.model_validate(yaml.safe_load(deal_text))
    (deal_dir / "deal.yaml").write_text(deal_text, encoding="utf-8")
    (deal_dir / "README.txt").write_text(_readme(spec, gl_rel, len(gl_txns), len(documents)), encoding="utf-8")

    revenue = {}
    for p in periods:
        wanted = set(months_in(p))
        revenue[p.label] = -sum(
            (t.amount for t in gl_txns if t.month in wanted and accounts[t.account].ebitda_class == EbitdaClass.REVENUE), ZERO
        )
    return GenerationResult(
        deal_dir=deal_dir,
        spec=spec,
        accounts=accounts,
        ledger=ledger,
        key_rows=key_rows,
        gl_path=gl_rel,
        documents=documents,
        truth=truth,
        effects=effects,
        gl_ebitda=gl_comp,
        mgmt=mgmt,
        revenue=revenue,
    )


def summarize(result: GenerationResult) -> str:
    labels = [p.label for p in result.spec.periods]
    lines = [
        f"{result.spec.deal_id}: {len(result.ledger.gl_txns())} GL rows, {len(result.documents)} documents -> {result.deal_dir}",
    ]
    for l in labels:
        lines.append(
            f"  {l:<12} revenue {fmt(result.revenue[l]):>15}  GL EBITDA {result.truth.gl_ebitda[l]:>13}  "
            f"mgmt reported {fmt(result.mgmt['reported_ebitda'][l]):>13}  mgmt adjusted {fmt(result.mgmt['adjusted_ebitda'][l]):>13}  "
            f"diligence {result.truth.diligence_adjusted_ebitda[l]:>13}"
        )
    return "\n".join(lines)
