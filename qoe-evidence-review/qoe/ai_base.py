"""The boundary between AI interpretation and deterministic code.

AI implementations (qoe/ai.py) read documents and management's narrative.
They may propose facts, links, contradictions, and question wording. They
never compute amounts and never choose a treatment: the engine does the
arithmetic and the reviewer makes the call.

Every quote an implementation returns must be verified with
``verify_quote`` before it reaches a workpaper; unverifiable quotes are
dropped and counted, never repaired.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from qoe.schemas import (
    AdjustmentClaim,
    DocFacts,
    EvidenceQuote,
    Flag,
    GLEntry,
    SourceDocument,
    StrictModel,
)
from pydantic import Field


class AdjustmentIntent(StrictModel):
    """What management's narrative claims, parsed into searchable terms."""

    adj_id: str
    counterparties: list[str] = Field(default_factory=list)  # vendor / person names mentioned
    keywords: list[str] = Field(default_factory=list)  # distinctive terms: "litigation", "severance", "relocation"
    reference_numbers: list[str] = Field(default_factory=list)  # matter / invoice / claim numbers mentioned
    event_type: str = "other"  # litigation | severance | recruiting | transaction | relocation | casualty | owner_expense | owner_comp | it_project | inventory | bad_debt | refinancing | out_of_period | pro_forma_savings | other
    asserts_nonrecurring: bool = False
    asserts_personal: bool = False  # owner / personal expense claim
    is_pro_forma: bool = False  # savings or events not yet reflected in the GL
    is_normalization: bool = False  # actual cost vs a market / normalized level
    normalized_amount: Optional[str] = None  # annual target level named in the narrative, if any
    event_months: list[str] = Field(default_factory=list)  # months the narrative dates the event to
    notes: str = ""


class Contradiction(StrictModel):
    """A document statement that conflicts with management's explanation."""

    doc_id: str
    statement: str  # plain-language summary of the conflict
    quote: EvidenceQuote
    conflicts_with: str  # which part of management's claim it contradicts
    entry_ids: list[str] = Field(default_factory=list)  # GL entries the conflict applies to, if specific


class EntryClassification(StrictModel):
    """Per-entry judgment for claims where only part of the activity qualifies
    (e.g. personal vs business travel). Proposed by AI, applied by code."""

    entry_id: str
    qualifies: bool
    reason: str
    doc_ids: list[str] = Field(default_factory=list)


@runtime_checkable
class EvidenceAI(Protocol):
    name: str  # "rules" or "llm:<model>"

    def extract_facts(self, doc: SourceDocument) -> DocFacts:
        """Classify a document and extract dated, quoted facts."""
        ...

    def parse_intent(self, adj: AdjustmentClaim) -> AdjustmentIntent:
        """Turn management's adjustment narrative into search terms and assertions."""
        ...

    def find_contradictions(
        self,
        adj: AdjustmentClaim,
        intent: AdjustmentIntent,
        facts: list[DocFacts],
        entries: list[GLEntry],
    ) -> list[Contradiction]:
        """Statements in linked documents that conflict with management's explanation."""
        ...

    def classify_entries(
        self,
        adj: AdjustmentClaim,
        intent: AdjustmentIntent,
        entries: list[GLEntry],
        facts: list[DocFacts],
    ) -> list[EntryClassification]:
        """For each linked entry, does it qualify under management's stated basis?"""
        ...

    def draft_questions(
        self,
        adj: AdjustmentClaim,
        flags: list[Flag],
        facts: list[DocFacts],
    ) -> list[str]:
        """Plain-English questions for management, one per unresolved issue."""
        ...


# A quote this short proves nothing: "a" or "$5" is a substring of almost any page.
MIN_QUOTE_CHARS = 8


def verify_quote(quote: EvidenceQuote, docs_by_id: dict[str, SourceDocument]) -> bool:
    """True only if the quote is a verbatim, non-trivial substring of the cited page."""
    doc = docs_by_id.get(quote.doc_id)
    if doc is None or len(quote.quote.strip()) < MIN_QUOTE_CHARS:
        return False
    for page in doc.pages:
        if page.page == quote.page:
            return quote.quote in page.text
    return False
