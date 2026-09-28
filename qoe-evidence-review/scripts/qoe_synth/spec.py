"""Deal spec models: the YAML authoring contract for synthetic QoE deal packages.

A deal spec (data/specs/<deal_id>.yaml) fully describes one synthetic deal:
company profile, chart of accounts, background activity, planted transactions,
planted data-quality issues, data-room documents, management's adjusted EBITDA
schedule, and the answer key. See scripts/qoe_synth/SPEC_FORMAT.md.

Every model forbids unknown keys so a typo in the YAML fails loudly instead of
silently generating the wrong deal.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

GL_FORMATS = ("qbo_gl_csv", "netsuite_csv", "xero_xlsx")
Number = Union[str, int, float]


class SpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _as_str(value: Any) -> Any:
    # YAML turns 6400 into an int and 2025-02-12 into a date; account numbers,
    # dates and months are all handled as text downstream.
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return value


class Company(SpecModel):
    name: str
    industry: str = ""
    short_name: str = ""


class PeriodSpec(SpecModel):
    label: str
    start: str
    end: str


class AccountSpec(SpecModel):
    number: str
    name: str
    type: str  # as the source system labels it ("Income", "Expense", "DIRECTCOSTS", ...)
    detail_type: str = ""
    description: str = ""
    ebitda_class: Optional[str] = None  # forces an account_mapping_overrides.csv row
    override_basis: str = ""
    natural: Optional[Literal["debit", "credit"]] = None  # normal balance, if the type is ambiguous

    _num = field_validator("number", mode="before")(_as_str)


class Party(SpecModel):
    """A letterhead / address block reused across documents."""

    name: str
    address: list[str] = Field(default_factory=list)
    phone: str = ""
    email: str = ""
    web: str = ""
    tagline: str = ""


class Counterparty(SpecModel):
    name: str
    weight: int = 1
    amount: Optional[Number] = None  # fixed mode: per-row amount for this counterparty
    start: Optional[str] = None  # YYYY-MM first active month
    end: Optional[str] = None  # YYYY-MM last active month
    memo: Union[str, list[str], None] = None  # overrides the stream memo for this counterparty
    num: Optional[str] = None  # document-number format, e.g. "GCS-{seq}"
    seq_start: int = 1
    seq_step: tuple[int, int] = (1, 1)  # vendors number other customers' invoices in between


class NumSpec(SpecModel):
    format: str = "{seq}"
    sequence: Optional[str] = None  # shared sequence id from DealSpec.sequences
    start: int = 1
    step: tuple[int, int] = (1, 1)


class Schedule(SpecModel):
    """When a background stream posts within each month."""

    days: Optional[list[int]] = None  # fixed days of month; -1 = last day
    count: Optional[tuple[int, int]] = None  # random business days, inclusive range
    weekdays: Optional[list[int]] = None  # every date whose weekday (Mon=0) is listed
    months: Optional[list[int]] = None  # calendar-month filter, e.g. [3, 6, 9, 12]
    adjust: Literal["none", "prior", "next"] = "none"  # move weekend dates to a business day

    @model_validator(mode="after")
    def _one_rule(self) -> "Schedule":
        rules = [r for r in (self.days, self.count, self.weekdays) if r is not None]
        if len(rules) != 1:
            raise ValueError("schedule needs exactly one of days, count, weekdays")
        return self


class AmountSpec(SpecModel):
    fixed: Optional[Number] = None  # per-row amount (fixed mode)
    by_year: Optional[dict[int, Number]] = None  # per-row amount by calendar year (fixed mode)
    escalate_pct: Optional[Number] = None  # compounding annual increase for fixed amounts
    escalate_month: int = 1
    monthly: Optional[Number] = None  # monthly total at data_start (allocate mode)
    seasonality: Optional[list[Number]] = None  # 12 factors Jan..Dec, normalized to mean 1
    growth: Number = 0  # annual growth rate, compounded monthly from data_start
    noise: Number = 0  # uniform +/- fraction applied to each month's total
    spread: Number = "0.5"  # +/- dispersion of row weights within a month
    round: Number = "0.01"  # rounding increment for the monthly total

    @field_validator("seasonality")
    @classmethod
    def _twelve(cls, v: Optional[list[Number]]) -> Optional[list[Number]]:
        if v is not None and len(v) != 12:
            raise ValueError("seasonality needs 12 monthly factors")
        return v


class Stream(SpecModel):
    """Recurring background activity in one account."""

    id: str
    account: str
    txn_type: str
    mode: Literal["fixed", "allocate"] = "allocate"
    direction: Optional[Literal["debit", "credit"]] = None  # default: the account's normal side
    split: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    schedule: Schedule
    amount: AmountSpec
    counterparties: list[Counterparty] = Field(default_factory=list)
    memo: Union[str, list[str]] = ""
    num: Optional[NumSpec] = None
    choices: dict[str, list[str]] = Field(default_factory=dict)
    # A list value picks one entry per row (NetSuite dimension noise); a string applies to every row.
    dimensions: dict[str, Union[str, list[str]]] = Field(default_factory=dict)

    _acct = field_validator("account", mode="before")(_as_str)

    @field_validator("counterparties", mode="before")
    @classmethod
    def _cp(cls, v: Any) -> Any:
        return [{"name": c} if isinstance(c, str) else c for c in (v or [])]

    @model_validator(mode="after")
    def _amount_fits_mode(self) -> "Stream":
        a = self.amount
        if self.mode == "allocate" and a.monthly is None:
            raise ValueError(f"stream {self.id}: allocate mode needs amount.monthly")
        if self.mode == "fixed" and a.fixed is None and a.by_year is None:
            if not self.counterparties or any(c.amount is None for c in self.counterparties):
                raise ValueError(f"stream {self.id}: fixed mode needs amount.fixed, amount.by_year or counterparty amounts")
        return self


class Repeat(SpecModel):
    start: str
    end: str
    days: list[int] = Field(default_factory=lambda: [1])
    months: Optional[list[int]] = None
    adjust: Literal["none", "prior", "next"] = "none"


class Planted(SpecModel):
    """An explicit GL row (or a series of them) with a stable key."""

    key: str
    account: str
    amount: Number  # debit-positive: expenses +, income / credits -
    date: Optional[str] = None  # YYYY-MM-DD
    repeat: Optional[Repeat] = None
    txn_type: str = "bill"
    counterparty: str = ""
    num: str = ""
    num_sequence: Optional[str] = None  # draw the number from a shared sequence (num is then the format)
    memo: str = ""
    split: Optional[str] = None
    dimensions: dict[str, str] = Field(default_factory=dict)

    _acct = field_validator("account", "date", mode="before")(_as_str)

    @model_validator(mode="after")
    def _date_or_repeat(self) -> "Planted":
        if (self.date is None) == (self.repeat is None):
            raise ValueError(f"planted {self.key}: give exactly one of date or repeat")
        return self


class Duplicate(SpecModel):
    key: str  # key of the duplicate row
    of: str  # key of the row that is posted twice
    days_later: int = 0
    note: str = ""


class Topside(SpecModel):
    month: str
    account: str
    amount: Number  # debit-positive amount in management's P&L that is not in the GL
    note: str = ""

    _acct = field_validator("account", mode="before")(_as_str)


class MissingMonth(SpecModel):
    month: str
    keep_accounts: list[str] = Field(default_factory=list)  # accounts still exported that month
    note: str = ""


class DataQualitySpec(SpecModel):
    duplicates: list[Duplicate] = Field(default_factory=list)
    topside: list[Topside] = Field(default_factory=list)
    missing_gl_months: list[MissingMonth] = Field(default_factory=list)
    # Replaces the default explanation on the MGMT_EBITDA_DIFFERS_FROM_GL answer-key entry.
    mgmt_ebitda_note: str = ""


class DocumentSpec(SpecModel):
    id: str
    filename: str
    folder: str = ""
    template: Literal["invoice", "letter", "agreement", "memo", "form", "email"]
    title: str = ""  # PDF metadata title; defaults to the filename stem
    supports: list[str] = Field(default_factory=list)  # planted keys (glob patterns allowed)
    key_phrases: list[str] = Field(default_factory=list)  # must survive extraction verbatim
    draft: bool = False
    check_total: bool = True  # invoice total must equal the supported rows
    fields: dict[str, Any] = Field(default_factory=dict)


class PLSection(SpecModel):
    role: Literal["income", "cogs", "expenses", "other_income", "other_expenses"]
    name: str
    types: list[str]
    total_label: str = ""


def _default_sections() -> list[PLSection]:
    return [
        PLSection(role="income", name="Income", types=["Income", "Revenue", "Sales"]),
        PLSection(role="cogs", name="Cost of Goods Sold", types=["Cost of Goods Sold", "COGS", "DIRECTCOSTS", "Direct Costs"]),
        PLSection(role="expenses", name="Expenses", types=["Expense", "Expenses", "OVERHEADS", "Overhead", "DEPRECIATN", "Depreciation"]),
        PLSection(role="other_income", name="Other Income", types=["Other Income", "OTHERINCOME"]),
        PLSection(role="other_expenses", name="Other Expenses", types=["Other Expense", "Other Expenses"]),
    ]


class MonthlyPLSpec(SpecModel):
    sheet_name: str = "Profit and Loss"
    title: str = "Profit and Loss by Month"
    month_format: Literal["mon_yyyy", "month_yyyy", "iso", "date"] = "mon_yyyy"
    basis_line: str = ""  # optional extra title row, e.g. "Accrual Basis"
    sections: list[PLSection] = Field(default_factory=_default_sections)
    gross_profit_label: str = "Gross Profit"
    net_operating_income_label: str = "Net Operating Income"
    net_other_income_label: str = "Net Other Income"
    net_income_label: str = "Net Income"
    total_column: bool = True


class ScheduleAdjustment(SpecModel):
    ref: str
    title: str
    category: str
    description: str = ""
    accounts: str = ""
    support: str = ""
    amounts: dict[str, Number]
    claim_keys: list[str] = Field(default_factory=list)  # pass-through claims: verify vs these rows
    claim_periods: list[str] = Field(default_factory=list)  # periods claim_keys must tie in (default: all)

    _accts = field_validator("accounts", mode="before")(_as_str)


class ScheduleLabels(SpecModel):
    net_income: str = "Net income"
    interest: str = "Interest expense"
    taxes: str = "Income tax expense"
    depreciation_amortization: str = "Depreciation and amortization"
    reported_ebitda: str = "Reported EBITDA"
    total_adjustments: str = "Total management adjustments"
    adjusted_ebitda: str = "Management adjusted EBITDA"


class ScheduleColumns(SpecModel):
    ref: str = "Ref"
    title: str = "Adjustment"
    category: str = "Category"
    description: str = "Description"
    accounts: str = "GL Account(s)"
    support: str = "Support Ref"


class ScheduleSpec(SpecModel):
    sheet_name: str = "Adjusted EBITDA"
    title_rows: list[str] = Field(default_factory=list)
    columns: ScheduleColumns = Field(default_factory=ScheduleColumns)
    labels: ScheduleLabels = Field(default_factory=ScheduleLabels)
    basis: Literal["pl", "gl"] = "pl"  # management builds reported EBITDA from its P&L
    adjustments: list[ScheduleAdjustment]
    # Planted MGMT_SCHEDULE_ARITHMETIC: refs left out of the printed total row (a SUM range that
    # stops short of the last rows). Adjusted EBITDA is then built from the wrong total, as in Excel.
    total_excludes: list[str] = Field(default_factory=list)
    arithmetic_note: str = ""


class PeriodMove(SpecModel):
    keys: list[str]
    service_start: str  # YYYY-MM
    service_end: str


class NormalizedLevel(SpecModel):
    """A normalization's benchmark level: amount[p] = supporting rows in p - monthly x months of p in [start, end]."""

    monthly: Number
    start: Optional[str] = None  # YYYY-MM; default data_start
    end: Optional[str] = None  # YYYY-MM; default data_end


class TruthAdjustment(SpecModel):
    adj_id: str
    case_type: str
    treatment: Literal["ACCEPT", "REVISE", "REJECT", "REQUEST_INFO"]
    amounts: dict[str, Number] = Field(default_factory=dict)
    supporting: list[str] = Field(default_factory=list)  # planted keys / globs
    related: list[str] = Field(default_factory=list)
    recoveries: list[str] = Field(default_factory=list)  # rows whose EBITDA effect is part of the amount
    period_moves: list[PeriodMove] = Field(default_factory=list)
    normalized_level: Optional[NormalizedLevel] = None  # normalizations: subtract the benchmark level
    # Keep P&L activity that a planted missing GL month dropped from the export (EBITDA accounts only):
    # amount[p] -= the debit-positive total of those ledger rows in p.
    restore_missing_months: list[str] = Field(default_factory=list)
    verify_amounts: bool = True
    # Periods whose amount must tie to the rows (default: all). A run-rate pro forma presented in TTM only has
    # its supporting rows in other periods too, where the carried amount is 0 by presentation, not by the GL.
    verify_periods: list[str] = Field(default_factory=list)
    supporting_docs: list[str] = Field(default_factory=list)  # document ids
    related_docs: list[str] = Field(default_factory=list)  # document ids surfaced as context / evidence against
    expected_flags: list[str] = Field(default_factory=list)
    question_topics: list[str] = Field(default_factory=list)
    rationale: str
    ambiguity: Literal["low", "medium", "high"] = "low"
    reviewer_note: str = ""


class TruthSpec(SpecModel):
    authored_by: str
    notes: str = ""
    adjustments: list[TruthAdjustment]
    diligence_items: list[TruthAdjustment] = Field(default_factory=list)  # not on management's schedule


class DealSpec(SpecModel):
    deal_id: str
    split: Literal["dev", "holdout"]
    seed: int
    package_date: str  # YYYY-MM-DD; fixed timestamp for xlsx metadata

    _date = field_validator("package_date", mode="before")(_as_str)
    company: Company
    periods: list[PeriodSpec]
    data_start: str
    data_end: str
    gl_format: Literal["qbo_gl_csv", "netsuite_csv", "xero_xlsx"]
    deal_yaml_gl_format: str = "auto"  # what deal.yaml declares; "auto" exercises format detection
    currency: str = "USD"
    tolerance: str = "1.00"
    readme_extra: str = ""
    txn_types: dict[str, dict[str, str]] = Field(default_factory=dict)  # generic -> {format: label}
    split_defaults: dict[str, str] = Field(default_factory=dict)  # generic txn type -> QBO Split
    default_dimensions: dict[str, str] = Field(default_factory=dict)
    netsuite_internal_id_start: int = 100001
    sequences: dict[str, int] = Field(default_factory=dict)
    parties: dict[str, Party] = Field(default_factory=dict)
    accounts: list[AccountSpec]
    background: list[Stream] = Field(default_factory=list)
    planted: list[Planted] = Field(default_factory=list)
    data_quality: DataQualitySpec = Field(default_factory=DataQualitySpec)
    documents: list[DocumentSpec] = Field(default_factory=list)
    monthly_pl: MonthlyPLSpec = Field(default_factory=MonthlyPLSpec)
    schedule: ScheduleSpec
    ground_truth: TruthSpec

    @model_validator(mode="after")
    def _cross_checks(self) -> "DealSpec":
        numbers = [a.number for a in self.accounts]
        if len(numbers) != len(set(numbers)):
            raise ValueError("duplicate account numbers in accounts")
        ids = [s.id for s in self.background]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate background stream ids")
        doc_ids = [d.id for d in self.documents]
        if len(doc_ids) != len(set(doc_ids)):
            raise ValueError("duplicate document ids")
        names = [d.filename for d in self.documents]
        if len(names) != len(set(names)):
            raise ValueError("document filenames must be unique (doc_id is the basename)")
        labels = [p.label for p in self.periods]
        for adj in self.schedule.adjustments:
            missing = set(labels) - set(adj.amounts)
            if missing:
                raise ValueError(f"schedule {adj.ref}: missing amounts for {sorted(missing)}")
        refs = {a.ref for a in self.schedule.adjustments}
        truth_ids = {a.adj_id for a in self.ground_truth.adjustments}
        if refs != truth_ids:
            raise ValueError(f"ground_truth adj ids {sorted(truth_ids)} do not match schedule refs {sorted(refs)}")
        stray = set(self.schedule.total_excludes) - refs
        if stray:
            raise ValueError(f"schedule.total_excludes names unknown refs {sorted(stray)}")
        clash = refs & {t.adj_id for t in self.ground_truth.diligence_items}
        if clash:
            raise ValueError(f"diligence item ids clash with schedule refs: {sorted(clash)}")
        known_docs = set(doc_ids)
        for t in [*self.ground_truth.adjustments, *self.ground_truth.diligence_items]:
            unknown = [d for d in [*t.supporting_docs, *t.related_docs] if d not in known_docs]
            if unknown:
                raise ValueError(f"ground_truth {t.adj_id}: unknown document ids {unknown}")
        return self


def load_spec(path: Path | str) -> DealSpec:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return DealSpec.model_validate(data)
