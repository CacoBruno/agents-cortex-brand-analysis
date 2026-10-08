from __future__ import annotations


class DomainError(ValueError):
    """Invalid user input or business-rule violation. Safe to show to API clients."""


class UpstreamError(RuntimeError):
    """An external dependency (Cortex, OpenAI, S3, a news site) failed."""


class ConfigurationError(RuntimeError):
    """Required credential, setting or optional extra is missing."""


class NewsEnrichmentError(UpstreamError):
    """Enrichment of a single news URL failed.

    Messages are written by us and are safe to return in API responses.
    """
