# Extending Quell

Two common extension points:

- **Skills** — Markdown runbooks that get injected into the agent's
  system prompt when their triggers match an incident.
- **Tools** — async Python functions the agent can call.

Skills do not require code; tools do.  Both ship in the main wheel by
being in the right directory under `quell/`.

---

## Writing a skill

A *skill* is a Markdown file under `quell/skills/<category>/<slug>.md`
with a YAML frontmatter block.

```markdown
---
name: stripe-webhook-timeout
category: incidents
description: Stripe webhook endpoints timing out or returning 500
applicable_when:
  - error_contains: "stripe-signature"
  - error_contains: "webhook timeout"
severity_hint: high
---

# Stripe webhook timeout runbook

## What it looks like
... (plain markdown from here on) ...
```

### Required frontmatter fields

| Field | Type | Example |
|-------|------|---------|
| `name` | `str` | Must match the filename stem. |
| `category` | `"incidents" \| "frameworks" \| "technologies"` | Must match the parent directory. |
| `description` | `str` | One-line human-readable summary. |
| `severity_hint` | `"low" \| "medium" \| "high"` | Helps the agent prioritise. |
| `applicable_when` | list of dicts | See [triggers](#applicable_when-triggers). |

### `applicable_when` triggers

A skill matches an incident if **any** of its `applicable_when` entries
matches (OR semantics across entries).  Within a single entry, **all**
keys must match (AND semantics).

| Trigger key | Matches against | Semantics |
|-------------|-----------------|-----------|
| `error_contains` | `context["error"]` | Case-insensitive substring. |
| `signature_contains` | `context["signature"]` | Case-insensitive substring. |
| `framework_is` | `context["framework"]` | Case-insensitive equality. |
| `tech_stack_includes` | `context["tech_stack"]` | Case-insensitive substring. |

Unknown trigger keys never match — a typo makes a skill silently
unreachable instead of accidentally universal.  A skill with an empty
`applicable_when` list is **never** auto-selected; it can only be
loaded explicitly by name.

### Writing the body

Anything below the second `---` is the body.  The loader preserves it
verbatim and it is injected into the agent's system prompt inside a
per-skill XML tag.  Aim for:

- 30–80 lines of markdown.
- A short "what it looks like" section.
- A "usual root causes" section.
- A concrete investigation checklist.

Examples live in [`quell/skills/`](../quell/skills/).

### Verifying

```bash
poetry run pytest tests/unit/test_skills.py::test_bundled_skills_parse -q
```

That test loads every `.md` under `quell/skills/` and fails the build
on any parse error.  The skill is now discoverable by `list_skills()`
and selectable by `select_applicable()`.

---

## Writing a tool

A *tool* is an `async def` that returns a `ToolResult` and is
registered via the `@register_tool` decorator.

```python
# quell/tools/code/count_lines.py
from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_WORKSPACE_ROOT = Path("/workspace")


@register_tool(
    name="count_lines",
    description="Return the number of lines in a workspace file.",
    parameters=[
        ToolParameterSpec(
            name="path", type="string", description="Workspace-relative path."
        ),
    ],
    execute_in_sandbox=True,
)
async def count_lines(path: str) -> ToolResult:
    target = (_WORKSPACE_ROOT / path).resolve()
    try:
        target.relative_to(_WORKSPACE_ROOT.resolve())
    except ValueError:
        return ToolResult.failure("count_lines", f"Path escapes workspace: {path}")
    if not target.is_file():
        return ToolResult.failure("count_lines", f"Not a file: {path}")

    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    return ToolResult.success(
        "count_lines",
        f"{len(lines)} lines",
        metadata={"path": path, "line_count": len(lines)},
    )
```

### `@register_tool` parameters

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | ✓ | Unique slug the LLM uses in `<function=name>` XML tags. |
| `description` | ✓ | One sentence; shown in the tool catalogue inside the system prompt. |
| `parameters` | | List of `ToolParameterSpec(name, type, description, required=True)`. |
| `execute_in_sandbox` | default `True` | When `True`, the host routes the call to the tool server inside Docker.  Set to `False` for pure-Python tools that don't touch the filesystem. |
| `needs_agent_state` | default `False` | When `True`, the executor injects `agent_state=…` so the tool can read/write the current `AgentState`. |

### Return contract

Always return `ToolResult`.  Never raise.  The executor wraps unhandled
exceptions in a `ToolResult.failure(...)` automatically, but returning
an explicit failure with a descriptive message is much more useful to
the agent.

### Register it for the watch loop

Add your tool's module path + registered name to
`quell/tools/builtins.py`:

```python
_BUILTIN_TOOL_NAMES: tuple[str, ...] = (
    ...,
    "count_lines",
)

_BUILTIN_MODULES: tuple[str, ...] = (
    ...,
    "quell.tools.code.count_lines",
)
```

`register_builtin_tools()` uses this list to (re)register everything
idempotently at startup and in tests.

### Test it

Follow the pattern in [`tests/unit/test_builtin_tools.py`](../tests/unit/test_builtin_tools.py):

```python
async def test_count_lines_returns_count(tmp_path: Path) -> None:
    (tmp_path / "hello.py").write_text("a\nb\nc\n", encoding="utf-8")
    inv = ToolInvocation(
        name="count_lines",
        parameters={"path": "hello.py"},
        raw_xml="",
    )
    with patch("quell.tools.code.count_lines._WORKSPACE_ROOT", tmp_path):
        result = await execute_tool(inv)
    assert result.ok is True
    assert result.metadata["line_count"] == 3
```

Then run:

```bash
poetry run pytest tests/unit/test_builtin_tools.py -q
poetry run ruff check quell/ tests/
poetry run mypy quell/
```

All three must pass before the change can merge.

---

## Writing a specialised agent

Rare, but possible.  Subclass `BaseAgent` (or `GenericSubagent`) and
override `_render_system_prompt()`.  Optionally override
`FINISH_TOOLS` to broaden the set of tool names that terminate the
loop, or `_build_initial_state()` to change the initial
`AgentState`.

See `quell/agents/incident_commander/commander.py` for the pattern —
it's 68 lines and covers the common case of loading a Jinja2 template
from `PackageLoader`.
