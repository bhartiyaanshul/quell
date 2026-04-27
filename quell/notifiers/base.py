"""Abstract interface for Quell notifier channels.

Every notifier is a class that implements :class:`Notifier`.  The
:func:`create_notifier` factory instantiates the right concrete
subclass from a validated :data:`~quell.config.schema.NotifierConfig`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from quell.config.schema import (
    DiscordNotifierConfig,
    NotifierConfig,
    SlackNotifierConfig,
    TelegramNotifierConfig,
)
from quell.memory.models import Incident
from quell.utils.errors import NotifierError


class Notifier(ABC):
    """Abstract base class for Quell notification channels.

    Subclasses must implement :meth:`notify`, which receives the
    :class:`~quell.memory.models.Incident` that just finished
    investigation and fans it out to the channel.
    """

    @abstractmethod
    async def notify(self, incident: Incident) -> None:
        """Send a notification for *incident*.

        Must not raise on transient failures — wrap them in
        :class:`NotifierError` only when the channel config itself is
        invalid (e.g. missing webhook URL).  Network blips should be
        logged and swallowed so one flaky channel does not block the
        others.
        """


def create_notifier(config: NotifierConfig) -> Notifier:
    """Instantiate the correct :class:`Notifier` subclass for *config*.

    Raises:
        NotifierError: If the config type has no registered implementation.
    """
    if isinstance(config, SlackNotifierConfig):
        from quell.notifiers.slack import SlackNotifier  # noqa: PLC0415

        return SlackNotifier(config)
    if isinstance(config, DiscordNotifierConfig):
        from quell.notifiers.discord import DiscordNotifier  # noqa: PLC0415

        return DiscordNotifier(config)
    if isinstance(config, TelegramNotifierConfig):
        from quell.notifiers.telegram import TelegramNotifier  # noqa: PLC0415

        return TelegramNotifier(config)
    raise NotifierError(  # pragma: no cover
        f"Unknown notifier config type: {type(config).__name__!r}"
    )


__all__ = ["Notifier", "create_notifier"]
