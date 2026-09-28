"""Tests for qoe.trace: linking, grouping, subset fit, document association, tie-out."""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Iterable, Optional


from qoe.ai_base import AdjustmentIntent
from qoe.money import fmt
from qoe.schemas import (
    Account,
    AdjustmentCategory,
    AdjustmentClaim,
    AmountFact,
    DealFiles,
    DealMeta,
    DealPackage,
    DocFacts,
    DocumentPage,
    EbitdaClass,
    EvidenceQuote,
    FlagCode,
    GLEntry,
    ManagementPL,
    ManagementSchedule,
    PeriodDef,
    Severity,
    SourceDocument,
)
from qoe.trace import (
    LINK_THRESHOLD,
    STRONG_LINK,
    build_index,
    find_subset,
    fit_claim,
    money,
    name_tokens,
    names_match,
    ref_tokens,
    support_ref_matches,
    theme_tokens,
    trace_adjustment,
)

# ---------------------------------------------------------------------------
# In-memory fixture kit
# ---------------------------------------------------------------------------

PERIODS = [
    PeriodDef(label="FY2024", start="2024-01", end="2024-12"),
    PeriodDef(label="FY2025", start="2025-01", end="2025-12"),
    PeriodDef(label="TTM Jun-26", start="2025-07", end="2026-06"),
]
LABELS = [p.label for p in PERIODS]
ACCOUNTS = {
    n: Account(number=n, name=name, source_type=typ, ebitda_class=cls)
    for n, name, typ, cls in [
        ("4000", "Service Revenue", "Income", EbitdaClass.REVENUE),
        ("6300", "Software & IT", "Expense", EbitdaClass.OPEX),
        ("6400", "Legal Fees", "Expense", EbitdaClass.OPEX),
        ("6450", "Recruiting", "Expense", EbitdaClass.OPEX),
        ("8000", "Other Income", "Other Income", EbitdaClass.OTHER_INCOME),
        ("1000", "Operating Cash", "Bank", EbitdaClass.BALANCE_SHEET),
    ]
}


class GL:
    def __init__(self) -> None:
        self.rows: list[GLEntry] = []

    def add(self, date: str, account: str, amount: object, cp: str = "", memo: str = "", num: str = "") -> str:
        row = len(self.rows) + 6
        self.rows.append(
            GLEntry(
                entry_id=f"GL-R{row}",
                date=date,
                period=date[:7],
                account=account,
                account_name=ACCOUNTS[account].name,
                txn_type="Bill",
                doc_number=num,
                counterparty=cp,
                memo=memo,
                amount=fmt(amount),
                source_file="gl/general_ledger.csv",
                source_row=row,
            )
        )
        return f"GL-R{row}"

    def monthly(self, start: str, end: str, account: str, amount: object, cp: str, memo: str) -> list[str]:
        from qoe.periods import month_range

        return [self.add(f"{m}-15", account, amount, cp, f"{memo} - {m}") for m in month_range(start, end)]


def doc(doc_id: str, text: str) -> SourceDocument:
    return SourceDocument(
        doc_id=doc_id, relpath=f"documents/{doc_id}", media_type="txt", sha256="0" * 64, pages=[DocumentPage(page=1, text=text)]
    )


def claim(adj_id: str, title: str, amounts: Iterable[object], accounts: Iterable[str] = (), refs: Iterable[str] = (),
          category: AdjustmentCategory = AdjustmentCategory.NON_RECURRING) -> AdjustmentClaim:
    return AdjustmentClaim(
        adj_id=adj_id,
        title=title,
        category=category,
        gl_accounts=list(accounts),
        support_refs=list(refs),
        amounts={lbl: fmt(a) for lbl, a in zip(LABELS, amounts)},
        source_row=10,
    )


def package(gl: GL, adjustments: list[AdjustmentClaim], docs: Iterable[SourceDocument] = ()) -> DealPackage:
    meta = DealMeta(
        deal_id="unit_deal",
        target_name="Unit Test Co (SYNTHETIC)",
        periods=PERIODS,
        data_start="2024-01",
        data_end="2026-06",
        files=DealFiles(gl="gl.csv", chart_of_accounts="coa.csv", monthly_pl="pl.xlsx", adjustments="adj.xlsx"),
    )
    return DealPackage(
        deal_dir="(memory)",
        meta=meta,
        accounts=ACCOUNTS,
        gl=gl.rows,
        pl=ManagementPL(source_file="pl.xlsx", months=[], lines=[]),
        schedule=ManagementSchedule(source_file="adj.xlsx", period_labels=LABELS, adjustments=adjustments),
        documents=list(docs),
    )


def intent(adj_id: str, **kw) -> AdjustmentIntent:
    return AdjustmentIntent(adj_id=adj_id, **kw)


def quote(doc_id: str, text: str) -> EvidenceQuote:
    return EvidenceQuote(doc_id=doc_id, page=1, quote=text)


def trace_one(pkg: DealPackage, it: AdjustmentIntent, facts: Optional[list[DocFacts]] = None):
    index = build_index(pkg, facts or [])
    return trace_adjustment(index, pkg.schedule.adjustments[0], it)


def flags(t, code: FlagCode):
    return [f for f in t.flags if f.code == code]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def test_name_matching_ignores_legal_suffixes_and_generic_words():
    assert names_match(name_tokens("Marlow & Finch"), name_tokens("Marlow & Finch LLP"))
    assert names_match(name_tokens("Pinecrest Search Partners"), name_tokens("Pinecrest Search"))
    # Sharing only a generic word is not a match.
    assert not names_match(name_tokens("Coastal Systems"), name_tokens("Nimbus Cloud Systems Group"))
    assert not names_match(name_tokens(""), name_tokens("Anything"))


def test_reference_tokens_and_memo_theme():
    refs = ref_tokens("Insurance proceeds - flood claim AM-2291-X, Mar 2025, $12,000.00")
    assert "AM2291X" in refs
    assert "2025" not in refs  # years are not references
    theme = theme_tokens("ERP managed services - Jan 2025 (inv 4471)", name_tokens("Nimbus"))
    assert theme == ("erp", "managed", "services")


def test_money_display_uses_deals_convention():
    assert money(Decimal("84500")) == "84,500"
    assert money("-42000") == "(42,000)"
    assert money("1234.5") == "1,234.50"


def test_support_ref_matches_data_room_index_not_neighbours():
    d1 = doc("3.1.2 Pinecrest invoice PS-102.txt", "x")
    d2 = doc("3.10 Other matter.txt", "x")
    assert support_ref_matches("DR 3.1", d1)
    assert not support_ref_matches("DR 3.1", d2)
    assert support_ref_matches("Pinecrest invoice", d1)


# ---------------------------------------------------------------------------
# Subset search
# ---------------------------------------------------------------------------


def test_find_subset_prefers_fewest_entries_and_exact_sums():
    values = [5_000_00, 2_500_00, 2_500_00, 7_500_00, 1_000_00]
    pick = find_subset(values, 7_500_00)
    assert pick == [3]  # one entry beats 5,000 + 2,500
    # Exact to the cent beats a closer-count approximate match within tolerance.
    assert find_subset([10_000_00, 4_999_50, 5_001_00], 10_000_50, tolerance=100) == [1, 2]
    assert find_subset([300_00, 700_00], 555_00) is None


def test_find_subset_group_weights_prefer_fewer_underlying_entries():
    # Group A (1 entry, 6,000) + group C (1 entry, 4,000) vs group B (12 entries, 10,000).
    pick = find_subset([6_000_00, 10_000_00, 4_000_00], 10_000_00, weights=[1, 12, 1])
    assert pick == [0, 2]


def test_find_subset_is_bounded_to_the_strongest_items():
    values = [1_000_00] * 30 + [123_45]
    start = time.perf_counter()
    # The only item that hits the target is the 31st and the weakest link: outside the bound.
    assert find_subset(values, 123_45, scores=[100] * 30 + [1]) is None
    # The same item with the strongest link is inside the bound and found.
    assert find_subset(values, 123_45, scores=[100] * 30 + [200]) == [30]
    # Ties break toward the earliest items, so repeated runs pick the same entries.
    assert find_subset(values[:30], 5_000_00) == [0, 1, 2, 3, 4]
    assert time.perf_counter() - start < 5


def test_fit_claim_prefers_fits_that_keep_groups_whole():
    # A: one 6,000 entry; B: two 5,000 entries; C: one 4,000 entry. 10,000 = A + C (whole) or B (whole)
    # or A + half of... none; the earliest-first rule would otherwise take A + 4,000 of B if it could.
    values = [6_000_00, 5_000_00, 4_000_00, 5_000_00]
    groups = ["A", "B", "C", "B"]
    fit = fit_claim(values, 10_000_00, 0, groups, [False] * 4)
    assert fit is not None and fit.split_groups == 0
    # Two whole-group fits remain (A + C, and B); the earliest entries decide and the tie is counted.
    assert fit.indices == [0, 2] and fit.ties == 2


def test_fit_claim_prefers_whole_groups_then_cited_entries_then_the_earliest():
    # Group G has four 2,500 entries; X is a single 5,000 entry that management's support cites.
    values = [2_500_00, 2_500_00, 2_500_00, 2_500_00, 5_000_00]
    groups = ["G", "G", "G", "G", "X"]
    # 5,000: X alone (whole, cited) beats any two G entries (splits G).
    assert fit_claim(values, 5_000_00, 0, groups, [False] * 4 + [True]).indices == [4]
    # 7,500: every fit splits G once; the cited X decides over three uncited G entries.
    fit = fit_claim(values, 7_500_00, 0, groups, [False] * 4 + [True])
    assert fit.indices == [0, 4] and fit.cited == 1 and fit.split_groups == 1 and fit.ties == 4
    # Nothing cited: the earliest entries win among the equally ranked fits.
    fit = fit_claim(values, 7_500_00, 0, groups, [False] * 5)
    assert fit.indices == [0, 1, 2]
    # Exact beats approximate; no fit within tolerance is None.
    assert fit_claim(values, 7_500_50, 100, groups, [False] * 5).diff == 50
    assert fit_claim(values, 1_000_00, 0, groups, [False] * 5) is None


def test_fit_claim_counts_residual_ties_and_stays_bounded():
    # Twelve equal monthly entries, a claim of six: C(12,6) = 924 equal fits; the earliest six are taken.
    fit = fit_claim([8_000_00] * 12, 48_000_00, 0, ["G"] * 12, [True] * 12)
    assert fit.indices == list(range(6)) and fit.ties == 924 and not fit.bounded
    start = time.perf_counter()
    values = [1_000_00 + i for i in range(40)]
    fit = fit_claim(values, values[3] + values[38], 0, [f"g{i}" for i in range(40)], [False] * 40, scores=[1.0] * 40)
    assert fit is not None and fit.bounded
    assert time.perf_counter() - start < 5


def test_find_subset_handles_mixed_signs():
    # A credit memo inside the claimed set nets against the invoices.
    assert find_subset([10_000_00, -2_000_00, 3_000_00], 8_000_00) == [0, 1]


# ---------------------------------------------------------------------------
# Linking and grouping
# ---------------------------------------------------------------------------


def _legal_deal():
    gl = GL()
    lit = [
        gl.add("2025-03-10", "6400", 12000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Unit Co - litigation", "MF-7710-03"),
        gl.add("2025-06-10", "6400", 14000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Unit Co - litigation", "MF-7710-06"),
        gl.add("2025-09-10", "6400", 8000, "Marlow & Finch LLP", "Matter 7710 Reyes v. Unit Co - litigation", "MF-7710-09"),
    ]
    retainer = gl.monthly("2024-01", "2026-06", "6400", 1000, "Marlow & Finch LLP", "Matter 3002 general corporate retainer")
    adhoc = gl.add("2025-08-20", "6400", 4000, "Marlow & Finch LLP", "Matter 3002 employment policy review", "MF-3002-AH")
    other_firm = gl.add("2025-05-05", "6400", 2500, "Beacon Law Group", "Trademark filing", "BL-1")
    cash = gl.add("2025-05-06", "1000", -2500, "Beacon Law Group", "litigation payment")
    return gl, lit, retainer, adhoc, other_firm, cash


def test_account_alone_does_not_link_but_counterparty_plus_account_does():
    gl, lit, retainer, adhoc, other_firm, cash = _legal_deal()
    pkg = package(gl, [claim("A-1", "Litigation fees", [0, 50000, 24000], ["6400"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Marlow & Finch"]))
    assert other_firm not in t.links  # account only (1.0 < threshold)
    assert cash not in t.links  # balance sheet entries are never linked
    link = t.links[lit[0]]
    assert link.score >= LINK_THRESHOLD
    assert any("Account 6400 Legal Fees" in r for r in link.reasons)
    assert any("Marlow & Finch LLP" in r and "named by management" in r for r in link.reasons)


def test_reference_alone_links_an_entry_outside_the_named_accounts():
    gl = GL()
    e = gl.add("2025-04-01", "6300", 900, "Records Vault", "Matter 7710 document hosting")
    pkg = package(gl, [claim("A-1", "Litigation fees", [0, 900, 0], ["6400"])])
    t = trace_one(pkg, intent("A-1", reference_numbers=["Matter 7710"]))
    assert e in t.links
    assert any("Memo cites Matter 7710" in r for r in t.links[e].reasons)


def test_groups_split_one_vendor_by_matter_reference():
    gl, lit, retainer, adhoc, *_ = _legal_deal()
    pkg = package(gl, [claim("A-1", "Litigation fees", [0, 50000, 24000], ["6400"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Marlow & Finch"], keywords=["litigation"]))
    assert t.group_of[lit[0]] == t.group_of[lit[2]]
    assert t.group_of[retainer[0]] == t.group_of[adhoc]  # ad hoc work under the same matter
    assert t.group_of[lit[0]] != t.group_of[retainer[0]]
    assert "Matter 7710" in t.group_of[lit[0]] and "Marlow & Finch LLP" in t.group_of[lit[0]]


# ---------------------------------------------------------------------------
# Claimed-set fit and tie-out
# ---------------------------------------------------------------------------


def test_linked_total_equal_to_claim_claims_everything_and_overlapping_periods_share_months():
    gl, lit, retainer, adhoc, *_ = _legal_deal()
    # FY2025: 34,000 litigation + 12,000 retainer + 4,000 ad hoc; TTM: 8,000 + 12,000 + 4,000.
    pkg = package(gl, [claim("A-1", "Litigation fees", [0, 50000, 24000], ["6400"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Marlow & Finch"]))
    assert t.traced("FY2025") == Decimal("50000") and t.traced("TTM Jun-26") == Decimal("24000")
    # Sep 2025 sits in both FY2025 and TTM Jun-26.
    assert lit[2] in t.claimed["FY2025"] and lit[2] in t.claimed["TTM Jun-26"]
    assert t.claimed.get("FY2024") is None  # no claim, nothing claimed
    links = {gl_link.entry_id: gl_link for gl_link in t.gl_links()}
    assert links[retainer[0]].supports_claim is False  # Jan 2024: context for recurrence
    assert "no claim in FY2024" in links[retainer[0]].reasons[-1]
    assert not t.flags


def test_excess_activity_is_fitted_by_whole_groups_first():
    gl, lit, retainer, adhoc, *_ = _legal_deal()
    pkg = package(gl, [claim("A-1", "Litigation fees", [0, 34000, 8000], ["6400"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Marlow & Finch"]))
    assert set(t.claimed["FY2025"]) == set(lit)
    assert t.claimed["TTM Jun-26"] == [lit[2]]
    excess = flags(t, FlagCode.EXCESS_GL_ACTIVITY)
    assert [f.period_label for f in excess] == ["FY2025", "TTM Jun-26"]
    assert all(f.severity == Severity.INFO for f in excess)
    assert "ties to the cent to 3 entries" in excess[0].message
    # The excess is unclaimed context activity, not an EBITDA effect: it is stated in the message
    # only, never as amount_impact / effects (review findings excel-flag-impact-column, ui-08).
    assert "the other 16,000 is context only" in excess[0].message
    assert all(f.amount_impact is None and f.effects == {} for f in excess)
    assert {x.entry_id for x in t.gl_links() if x.supports_claim} == set(lit)


def test_entry_level_fit_when_no_group_combination_ties():
    gl, lit, retainer, adhoc, *_ = _legal_deal()
    # 18,000 splits a group whichever way it is made, and nothing is cited: the earliest entries
    # win (SPEC §5.3), and the residual tie is recorded for the reviewer.
    pkg = package(gl, [claim("A-1", "Mixed", [0, 18000, 0], ["6400"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Marlow & Finch"]))
    fit = t.fits["FY2025"]
    assert fit.method == "entries" and fit.ties > 1
    assert set(t.claimed["FY2025"]) == {lit[0]} | set(retainer[12:18])  # Mar 12,000 + Jan-Jun 2025 retainers
    assert any(f"{fit.ties:,} fits rank equal" in f.message for f in flags(t, FlagCode.EXCESS_GL_ACTIVITY))
    assert any("Which entries make up" in j for j in t.judgments)


def test_a_reference_management_names_decides_between_equal_fits():
    gl, lit, retainer, adhoc, *_ = _legal_deal()
    pkg = package(gl, [claim("A-1", "Mixed", [0, 18000, 0], ["6400"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Marlow & Finch"], reference_numbers=["MF-7710-06"]))
    # The invoice management names is taken first; the other 4,000 then comes from the earliest retainers.
    assert set(t.claimed["FY2025"]) == {lit[1]} | set(retainer[12:16])
    assert t.fits["FY2025"].cited == 1



def test_ttm_fit_prefers_the_entries_claimed_in_the_overlapping_fiscal_year():
    gl = GL()
    subs = gl.monthly("2025-01", "2026-06", "6300", 3000, "Nimbus Cloud Systems", "ERP managed services")
    pkg = package(gl, [claim("A-1", "ERP implementation", [0, 36000, 18000], ["6300"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Nimbus Cloud Systems"]))
    assert t.claimed["FY2025"] == subs[:12]
    assert t.claimed["TTM Jun-26"] == subs[6:12]  # Jul-Dec 2025, already claimed in FY2025


def test_partial_support_flags_the_gap_in_ebitda_terms():
    gl, lit, *_ = _legal_deal()
    pkg = package(gl, [claim("A-1", "Litigation fees", [0, 40000, 0], ["6400"])])
    t = trace_one(pkg, intent("A-1", reference_numbers=["7710"]))
    (partial,) = flags(t, FlagCode.PARTIAL_GL_SUPPORT)
    assert partial.period_label == "FY2025" and partial.severity == Severity.WARNING
    assert partial.amount_impact == "-6000.00"  # linked 34,000 - claimed 40,000
    assert "6,000 of the claim is not found in the GL" in partial.message


def test_nothing_linked_raises_no_gl_support():
    gl, *_ = _legal_deal()
    pkg = package(gl, [claim("A-1", "Mystery item", [0, 5000, 0], ["6450"])])
    t = trace_one(pkg, intent("A-1", keywords=["mystery"]))
    (flag,) = flags(t, FlagCode.NO_GL_SUPPORT)
    assert flag.severity == Severity.CRITICAL
    assert "accounts 6450" in flag.message and "keywords mystery" in flag.message


def test_no_exact_subset_uses_strong_links_and_caps_the_proposal():
    gl = GL()
    a = gl.add("2025-02-01", "6450", 7000, "Pinecrest Search", "CFO search retainer", "PS-1")
    b = gl.add("2025-03-01", "6450", 7000, "Pinecrest Search", "CFO search milestone", "PS-2")
    c = gl.add("2025-04-01", "6450", 500, "Jobly", "CFO search job ad")
    pkg = package(gl, [claim("A-1", "CFO search", [0, 10000, 0], ["6450"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Pinecrest Search"], keywords=["search"]))
    assert c in t.links and t.links[c].score < STRONG_LINK <= t.links[a].score
    assert t.fits["FY2025"].method == "strong"
    assert set(t.claimed["FY2025"]) == {a, b}
    assert "FY2025" in t.capped
    assert any("no combination of linked entries ties" in f.message for f in flags(t, FlagCode.EXCESS_GL_ACTIVITY))
    assert t.judgments and "Which GL entries" in t.judgments[0]


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def test_documents_link_by_support_ref_and_doc_number_and_count_as_documented():
    gl = GL()
    inv = [
        gl.add("2025-04-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 1", "PS-101"),
        gl.add("2025-05-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 2", "PS-102"),
    ]
    undocumented = gl.add("2025-06-15", "6450", 10000, "Pinecrest Search Partners", "Executive search - installment 3", "PS-103")
    texts = {
        "3.1 Pinecrest engagement letter.txt": "Engagement letter. Fee of $30,000 payable in three installments.",
        "3.2 Pinecrest invoice PS-101.txt": "Invoice PS-101. Total due $10,000.00",
        "3.3 Pinecrest invoice PS-102.txt": "Invoice PS-102. Total due $10,000.00",
        "9.9 Unrelated memo.txt": "Nothing to see.",
    }
    docs = [doc(k, v) for k, v in texts.items()]
    facts = [
        DocFacts(
            doc_id="3.1 Pinecrest engagement letter.txt",
            doc_type="engagement_letter",
            counterparty="Pinecrest Search Partners",
            amounts=[AmountFact(label="total_fee", amount="30000", quote=quote("3.1 Pinecrest engagement letter.txt", "Fee of $30,000"))],
        ),
        DocFacts(doc_id="3.2 Pinecrest invoice PS-101.txt", doc_type="invoice", counterparty="Pinecrest Search Partners", reference_numbers=["PS-101"]),
        DocFacts(doc_id="3.3 Pinecrest invoice PS-102.txt", doc_type="invoice", counterparty="Pinecrest Search Partners", reference_numbers=["PS-102"]),
    ]
    pkg = package(gl, [claim("A-1", "Executive search", [0, 30000, 0], ["6450"], refs=["DR 3"])], docs)
    t = trace_one(pkg, intent("A-1", keywords=["search"]), facts)
    links = {d.doc_id: d for d in t.doc_link_models()}
    assert "9.9 Unrelated memo.txt" not in links
    assert links["3.2 Pinecrest invoice PS-101.txt"].relation == "invoice_for_entry"
    assert links["3.2 Pinecrest invoice PS-101.txt"].entry_ids == [inv[0]]
    # The engagement letter states the 30,000 total of the three installments.
    assert set(links["3.1 Pinecrest engagement letter.txt"].entry_ids) == set(inv + [undocumented])
    assert links["3.1 Pinecrest engagement letter.txt"].relation == "agreement"
    assert links["3.1 Pinecrest engagement letter.txt"].quotes[0].quote == "Fee of $30,000"
    assert t.documented("FY2025") == Decimal("30000")
    gl_links = {x.entry_id: x for x in t.gl_links()}
    assert "3.2 Pinecrest invoice PS-101.txt" in gl_links[inv[0]].doc_ids
    assert any("Doc # PS-101 appears in" in r for r in gl_links[inv[0]].reasons)


# ---------------------------------------------------------------------------
# Behaviours added for real-deal robustness
# ---------------------------------------------------------------------------


def test_keywords_match_stems_but_do_not_restate_the_party():
    from qoe.trace import keyword_hits

    tokens = frozenset("office payroll dispatch fte".split())
    assert keyword_hits(["dispatcher"], "office payroll dispatch fte", tokens) == ["dispatcher"]
    memo = frozenset("hollis crane litigation".split())
    assert keyword_hits(["hollis", "litigation"], "hollis crane litigation", memo, party=frozenset({"hollis", "crane"})) == ["litigation"]


def test_claim_matching_activity_booked_in_another_period_is_not_forced_onto_unrelated_entries():
    gl = GL()
    moves = [
        gl.add("2025-02-10", "6300", 12000, "Swift Movers", "Office relocation - moving", "SM-7"),
        gl.add("2025-03-22", "6300", 8000, "Keel Build-Out", "Office relocation - build-out", "KB-3"),
    ]
    rent = gl.monthly("2025-07", "2026-06", "6300", 9000, "Swift Movers", "Storage relocation fee")
    pkg = package(gl, [claim("A-1", "Relocation", [0, 20000, 20000], ["6300"])])
    t = trace_one(pkg, intent("A-1", counterparties=["Swift Movers", "Keel Build-Out"]))
    fit = t.fits["TTM Jun-26"]
    assert fit.method == "elsewhere" and t.claimed["TTM Jun-26"] == []
    assert fit.elsewhere == moves
    assert all(r in t.links and not t.links[r].context for r in rent)  # still linked, as context


def test_normalization_claims_only_the_named_accounts():
    gl = GL()
    comp = gl.monthly("2025-01", "2025-12", "6400", 25000, "J. Varga", "Officer payroll - J. Varga")
    dues = gl.monthly("2025-01", "2025-12", "6300", 500, "Harbor Point Yacht Club", "Club dues - J. Varga compensation")
    pkg = package(gl, [claim("A-1", "Owner comp", [0, 100000, 0], ["6400"], category=AdjustmentCategory.NORMALIZATION)])
    t = trace_one(pkg, intent("A-1", counterparties=["J. Varga"], keywords=["compensation"], is_normalization=True))
    assert all(d in t.links for d in dues)  # linked (party + keyword) but not actual cost of the named account
    assert t.claimed["FY2025"] == comp and t.traced("FY2025") == Decimal("300000")


def test_pro_forma_without_accounts_links_the_cost_base_on_keywords():
    gl = GL()
    staff = gl.monthly("2025-07", "2026-06", "6300", 5000, "", "Office payroll - Dispatch team")
    pkg = package(gl, [claim("A-1", "Dispatch savings", [0, 0, 60000], [], category=AdjustmentCategory.PRO_FORMA)])
    t = trace_one(pkg, intent("A-1", keywords=["dispatcher"], is_pro_forma=True))
    assert t.claimed["TTM Jun-26"] == staff
    # The same keywords do not link an adjustment that names accounts.
    pkg2 = package(gl, [claim("A-1", "Dispatch savings", [0, 0, 60000], ["6400"], category=AdjustmentCategory.PRO_FORMA)])
    assert not trace_one(pkg2, intent("A-1", keywords=["dispatcher"], is_pro_forma=True)).links


def test_correspondence_citing_a_claimed_invoice_number_is_linked_to_it():
    gl = GL()
    e = gl.add("2025-03-05", "6300", 8000, "Nimbus Cloud Systems", "ERP managed services", "NCS-2503")
    texts = {"6.2 Controller email.txt": "The March invoice (NCS-2503) came in at the usual amount; it is our subscription."}
    pkg = package(gl, [claim("A-1", "ERP", [0, 8000, 0], ["6300"])], [doc(k, v) for k, v in texts.items()])
    t = trace_one(pkg, intent("A-1", counterparties=["Nimbus Cloud Systems"]))
    (link,) = t.doc_link_models()
    assert link.doc_id == "6.2 Controller email.txt" and link.entry_ids == [e] and link.relation == "other"
    assert t.doc_links["6.2 Controller email.txt"].entry_basis[e] == "mention"
