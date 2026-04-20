"""Deliberately buggy checkout module used as the subject of e2e tests.

The ``process_order`` function dereferences ``order.user.id`` without
handling the case where ``order.user`` is ``None`` — a classic
unhandled-null bug the agent should surface.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    id: str


@dataclass
class Order:
    id: str
    user: User | None = None


def process_order(order: Order) -> str:
    # BUG: no None-check on order.user before accessing .id
    return f"order={order.id} user={order.user.id}"  # type: ignore[union-attr]
