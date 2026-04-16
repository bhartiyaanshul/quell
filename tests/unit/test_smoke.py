"""Smoke tests — verify the package imports and basic machinery works."""


def test_version_importable() -> None:
    """Quell package is importable and reports the correct version."""
    import quell

    assert quell.__version__ == "0.1.0"


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
        assert issubclass(
            subclass, QuellError
        ), f"{subclass.__name__} must subclass QuellError"


def test_logger_setup_does_not_raise() -> None:
    """Logger setup completes without raising."""
    from quell.utils.logger import setup_logger

    setup_logger(level="WARNING")  # suppress output during tests
