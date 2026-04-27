"""SQLAlchemy 2.0 ORM models for Quell's incident memory.

All models use the modern ``Mapped[]`` annotation style and
``mapped_column()`` factory. The schema is created via
``Base.metadata.create_all()`` — no Alembic in v0.1.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all Quell models."""


class Incident(Base):
    """A production incident detected by Quell."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    signature: Mapped[str] = mapped_column(sa.String, index=True)
    severity: Mapped[str] = mapped_column(sa.String)  # low / medium / high / critical
    status: Mapped[str] = mapped_column(
        sa.String
    )  # detected / investigating / resolved / abandoned
    first_seen: Mapped[datetime] = mapped_column(sa.DateTime)
    last_seen: Mapped[datetime] = mapped_column(sa.DateTime)
    occurrence_count: Mapped[int] = mapped_column(sa.Integer, default=1)
    root_cause: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    fix_pr_url: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    postmortem: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    agent_graph_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)

    # v0.2 — running LLM cost across every investigation run for this
    # incident.  Summed when each ``agent_loop`` finishes.
    cost_usd: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)

    agent_runs: Mapped[list[AgentRun]] = relationship(
        "AgentRun", back_populates="incident", cascade="all, delete-orphan"
    )
    findings: Mapped[list[Finding]] = relationship(
        "Finding", back_populates="incident", cascade="all, delete-orphan"
    )


class AgentRun(Base):
    """A single agent execution associated with an incident."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    incident_id: Mapped[str] = mapped_column(sa.String, sa.ForeignKey("incidents.id"))
    parent_agent_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    name: Mapped[str] = mapped_column(sa.String)
    skills: Mapped[list[str]] = mapped_column(sa.JSON)
    status: Mapped[str] = mapped_column(sa.String)  # running / completed / failed
    started_at: Mapped[datetime] = mapped_column(sa.DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime, nullable=True)
    final_result: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON, nullable=True)

    incident: Mapped[Incident] = relationship("Incident", back_populates="agent_runs")
    events: Mapped[list[Event]] = relationship(
        "Event", back_populates="agent_run", cascade="all, delete-orphan"
    )


class Event(Base):
    """A structured event emitted by an agent during an investigation."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    agent_run_id: Mapped[str] = mapped_column(sa.String, sa.ForeignKey("agent_runs.id"))
    event_type: Mapped[str] = mapped_column(
        sa.String
    )  # llm_call / tool_call / error / info
    timestamp: Mapped[datetime] = mapped_column(sa.DateTime, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(sa.JSON)

    agent_run: Mapped[AgentRun] = relationship("AgentRun", back_populates="events")


class Finding(Base):
    """A discrete piece of evidence discovered during an investigation."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    incident_id: Mapped[str] = mapped_column(sa.String, sa.ForeignKey("incidents.id"))
    agent_run_id: Mapped[str] = mapped_column(sa.String, sa.ForeignKey("agent_runs.id"))
    category: Mapped[str] = mapped_column(sa.String)  # null_reference / db_error / etc.
    description: Mapped[str] = mapped_column(sa.Text)
    file_path: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    line_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(sa.Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime)

    incident: Mapped[Incident] = relationship("Incident", back_populates="findings")


__all__ = ["Base", "Incident", "AgentRun", "Event", "Finding"]
