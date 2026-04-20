# Contributing to Quell

Thanks for your interest in improving Quell!  This guide covers the
basics.  If anything here conflicts with `CLAUDE.md` (the hard project
rules), `CLAUDE.md` wins.

## Setting up a dev environment

```bash
git clone https://github.com/bhartiyaanshul/quell
cd quell
poetry install
poetry run pytest -q
```

Quell targets **Python 3.12+**.

## The stop-gate — run these before pushing

```bash
poetry run ruff format quell/ tests/ --check
poetry run ruff check quell/ tests/
poetry run mypy quell/
poetry run pytest tests/ --tb=short -q
```

All four commands must pass.  CI runs the same checks; broken trunk
reverts on sight.

## Code conventions

- Strict typing.  No `# type: ignore` without an inline comment
  explaining why.
- All errors subclass `QuellError` from `quell.utils.errors`.
- All LLM calls go through LiteLLM (`quell.llm.llm.LLM`).  Direct use of
  `openai` or `anthropic` SDKs is forbidden.
- All tool output crosses module boundaries as `ToolResult` — no raw
  dicts.
- 300-line cap per file.  If a module wants to grow past that, split it
  along single-responsibility lines.
- Docstrings are not optional on public APIs.

## Adding a tool

1. Create a file in `quell/tools/<category>/<name>.py`.
2. Decorate an async function with `@register_tool(...)`.
3. Add the tool's module path and name to
   `quell/tools/builtins.py` so the bootstrap picks it up.
4. Write a matching test in `tests/unit/test_builtin_tools.py`.

## Adding a skill

1. Create `quell/skills/<category>/<slug>.md` with YAML frontmatter and
   a Markdown body.
2. Run `pytest tests/unit/test_skills.py::test_bundled_skills_parse` to
   confirm it parses.
3. The skill is picked up automatically by `list_skills()`.

## Commit style

One logical change per commit.  Prefix the subject line with the phase
or subsystem, e.g. `detector: dedupe high-severity repeats`.
