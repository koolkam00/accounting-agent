"""Domain exceptions.

Failures that a human must see are raised, never swallowed. Data-quality
problems on a single invoice stay in the exception-code channel (they route the
document to HUMAN_REVIEW); infrastructure and contract failures raise.
"""

from __future__ import annotations


class AccountingAgentError(Exception):
    """Base class for all errors raised by this package."""


class PdfExtractionError(AccountingAgentError):
    """The PDF could not be parsed at all (not the same as image-only/OCR)."""


class LLMExtractionError(AccountingAgentError):
    """The model response was missing, truncated, non-JSON, or off-schema."""


class PolicyConfigError(AccountingAgentError):
    """config/policy.yaml is missing, unreadable, or does not match PolicyConfig."""


class ERPPersistenceError(AccountingAgentError):
    """An ERP read/write failed or returned corrupt persisted state."""


class AuditPersistenceError(AccountingAgentError):
    """An audit event could not be persisted — the trail is incomplete."""
