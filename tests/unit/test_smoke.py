"""Smoke tests — verify the package imports and basic machinery works."""


def test_version_importable() -> None:
    """Quell package is importable and exposes a PEP 440 version string."""
    import re

    import quell

    # Don't hardcode the literal version — the value changes every
    # release and pinning it here creates a pointless test failure on
    # every bump.  Verify the shape instead.
    assert isinstance(quell.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+([-.a-z0-9]*)?", quell.__version__), (
        f"not a PEP 440 version: {quell.__version__!r}"
    )


def test_error_hierarchy() -> None:
    """All error subclasses inherit from QuellError."""
    from quell.utils.errors import (
        AgentError,
        ConfigError,
        LLMError,
        MonitorError,
        QuellError,
        SandboxError,
        ToolError,
    )

    subclasses = (
        ConfigError,
        MonitorError,
        AgentError,
        ToolError,
        SandboxError,
        LLMError,
    )
    for subclass in subclasses:
        assert issubclass(subclass, QuellError), (
            f"{subclass.__name__} must subclass QuellError"
        )


def test_logger_setup_does_not_raise() -> None:
    """Logger setup completes without raising."""
    from quell.utils.logger import setup_logger

    setup_logger(level="WARNING")  # suppress output during tests
