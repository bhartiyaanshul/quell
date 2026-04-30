"""Preview script — run this to see the v0.3.0 CLI visual language.

    python examples/preview_visuals.py

Renders every primitive from quell.interface.visuals plus a sample
``quell incident list`` and ``quell incident show`` mock so the look
can be locked in before Phase 3 builds real commands using it.

Per ``docs/cli-design.md``: this is the design contract — if the
output below feels right, every later command will match.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Run-from-repo support: when invoked as `python examples/preview_visuals.py`
# without quell installed, the parent directory holds the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows cmd.exe defaults to cp1252 which can't encode ✓ / ▸ / ─.
# Reconfigure stdout for UTF-8 so the preview renders the same on
# every platform. Modern terminals (Windows Terminal, iTerm, gnome-
# terminal) already speak UTF-8 — this is a safety net for old shells.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from quell.interface.format import (  # noqa: E402
    format_cost_usd,
    relative_time,
    truncate_id,
)
from quell.interface.output import Output  # noqa: E402
from quell.interface.visuals import (  # noqa: E402
    badge,
    diff,
    divider,
    empty_state,
    markdown,
    next_step,
    step_indicator,
    welcome_panel,
)


def main() -> None:
    out = Output()

    # 1. Welcome panel — first-run experience
    welcome_panel(
        out,
        title="Quell",
        body=(
            "an on-call engineer that never sleeps.\n\nSetup takes about 90 seconds."
        ),
    )

    # 2. Step indicators — multi-step flows
    out.header("Step indicators")
    step_indicator(out, 1, 5, "Project type: Python (Poetry)")
    step_indicator(out, 2, 5, "Log source: Local file")
    step_indicator(out, 3, 5, "Notifications: Slack")
    step_indicator(out, 4, 5, "LLM provider: Anthropic")
    step_indicator(out, 5, 5, "GitHub token (optional)")

    # 3. Status messages — ambient feedback
    out.header("Status messages")
    out.success("Config written to .quell/config.toml")
    out.warn("API key not yet configured")
    out.error(
        "Docker daemon not reachable",
        fix="Start Docker Desktop or `sudo systemctl start docker`",
    )

    # 4. Dividers
    out.header("Dividers")
    divider(out, label="Section heading")
    out.line("  body content here")
    divider(out)
    out.line("  (full-width rule)")

    # 5. Badges — used inline for status columns
    out.header("Badges (inline)")
    out.styled(f"  Incident: {badge('resolved', status='success')}  high  2h ago")
    out.styled(f"  Incident: {badge('detected', status='warning')}  medium  4h ago")
    out.styled(f"  Incident: {badge('investigating', status='info')}  low  6h ago")
    out.styled(f"  Incident: {badge('failed', status='error')}  critical  yesterday")

    # 6. Sample table — `quell incident list`
    out.header("`quell incident list` mock")
    out.line("")
    out.line(f"  {'ID':<14}  {'STATUS':<24}  {'SEV':<8}  {'COST':<8}  LAST SEEN")
    rows = [
        ("inc_a1b2c3d4", "resolved", "success", "high", 0.012, "2h ago"),
        ("inc_e5f6g7h8", "detected", "warning", "medium", 0.0034, "4h ago"),
        ("inc_i9j0k1l2", "investigating", "info", "low", 0.045, "6h ago"),
        ("inc_m3n4o5p6", "failed", "error", "critical", 0.21, "yesterday"),
    ]
    for inc_id, label, status, sev, cost, when in rows:
        out.styled(
            f"  {truncate_id(inc_id, max_length=14):<14}  "
            f"{badge(label, status=status):<32}  "  # padding accounts for markup
            f"{sev:<8}  "
            f"{format_cost_usd(cost):<8}  "
            f"{when}"
        )
    out.line("")
    out.info("  Showing 4 of 47.")

    # 7. Sample incident detail — `quell incident show`
    out.header("`quell incident show` mock")
    out.line("")
    out.key_value(
        [
            ("ID", "inc_a1b2c3d4"),
            ("Status", badge("resolved", status="success")),
            ("Severity", "high"),
            ("First seen", "2026-04-30 09:14:02"),
            ("Last seen", relative_time(datetime.now(UTC) - timedelta(hours=2))),
            ("Occurrences", "17"),
            ("Cost", format_cost_usd(0.012)),
        ]
    )
    out.line("")
    divider(out, label="root cause")
    markdown(
        out,
        "**Null dereference in `processOrder`** — `order.user` was assumed to "
        "be non-null but a recent migration introduced rows where it can be "
        "`NULL`. The handler crashes on the first such row in each request "
        "batch, surfacing as a `TypeError` to the caller.",
    )
    out.line("")
    divider(out, label="proposed fix")
    diff(
        out,
        "src/checkout.ts",
        [
            ("context", "function processOrder(order: Order) {"),
            ("rm", "  const userId = order.user.id;"),
            ("add", "  if (!order.user) return null;  // skip orphan rows"),
            ("add", "  const userId = order.user.id;"),
            ("context", "  return calculateTotal(userId);"),
        ],
    )
    out.line("")

    # 8. Empty states
    out.header("Empty states")
    empty_state(out, "(no incidents recorded yet)")
    out.line("")
    empty_state(
        out,
        "(no incidents recorded yet)",
        hint="Try `quell watch` to start monitoring",
    )

    # 9. Next-step hints
    out.header("Next-step hints")
    next_step(out, "Run quell doctor to verify your setup")
    next_step(out, "Verify your setup", command="quell doctor")
    next_step(out, "Watch for incidents", command="quell watch")

    out.line("")
    divider(out)
    out.line("")
    out.info(
        "  End of preview. Run `python examples/preview_visuals.py` "
        "to see this anytime."
    )


if __name__ == "__main__":
    main()
