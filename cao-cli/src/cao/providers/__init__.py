"""Agent provider adapters.

Each provider wraps a CLI tool (claude, codex, etc.) or an API
into a common interface for running agent turns.
"""

from cao.providers.base import BaseProvider, ProviderConfig, ProviderResponse
from cao.providers.mock import MockProvider

__all__ = ["BaseProvider", "ProviderConfig", "ProviderResponse", "MockProvider", "get_provider"]


def get_provider(provider_name: str) -> type[BaseProvider]:
    """Return the provider class for the given provider name."""
    registry: dict[str, type[BaseProvider]] = {
        "mock": MockProvider,
        "claude_code": _try_import_claude_code(),
    }
    provider_cls = registry.get(provider_name)
    if provider_cls is None:
        raise ValueError(
            f"Unknown provider: {provider_name!r}. "
            f"Available: {list(registry.keys())}"
        )
    return provider_cls


def _try_import_claude_code() -> type[BaseProvider]:
    try:
        from cao.providers.claude_code import ClaudeCodeProvider
        return ClaudeCodeProvider
    except ImportError:
        return MockProvider
