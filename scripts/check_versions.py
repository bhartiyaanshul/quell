#!/usr/bin/env python3
"""Verify every version string in the repo agrees.

Quell ships through five channels (PyPI, npm, Homebrew, prebuilt
binaries, curl-pipe).  Each one keeps its own copy of the version,
and a release with mismatched versions is a long, painful bug — npm
will try to download a binary for a tag that doesn't exist, brew
will fail to find the sdist, etc.

This script reads every version string we care about and prints a
table.  Exits non-zero if they disagree.

Sources of truth:
  pyproject.toml         tool.poetry.version
  quell/version.py       __version__
  packaging/npm/package.json    version
  packaging/homebrew/quell.rb   url   (parsed for "quell-agent-X.Y.Z.tar.gz")

Usage:
  python scripts/check_versions.py            # just check
  python scripts/check_versions.py --bump X.Y.Z   # rewrite all four
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
VERSION_PY = REPO_ROOT / "quell" / "version.py"
NPM_PKG = REPO_ROOT / "packaging" / "npm" / "package.json"
HOMEBREW = REPO_ROOT / "packaging" / "homebrew" / "quell.rb"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([a-z0-9.-]+)?$")


def read_pyproject() -> str:
    data = tomllib.loads(PYPROJECT.read_text())
    return str(data["tool"]["poetry"]["version"])


def read_version_py() -> str:
    text = VERSION_PY.read_text()
    m = re.search(r'__version__\s*:\s*str\s*=\s*"([^"]+)"', text)
    if not m:
        raise RuntimeError(f"Could not parse __version__ from {VERSION_PY}")
    return m.group(1)


def read_npm() -> str:
    return str(json.loads(NPM_PKG.read_text())["version"])


def read_homebrew() -> str | None:
    """Returns None if the formula is still a template (placeholder url)."""
    text = HOMEBREW.read_text()
    m = re.search(r"quell-agent-(\d+\.\d+\.\d+[a-z0-9.-]*)\.tar\.gz", text)
    return m.group(1) if m else None


def write_pyproject(version: str) -> None:
    text = PYPROJECT.read_text()
    new = re.sub(
        r'(?m)^(version\s*=\s*)"[^"]+"',
        rf'\1"{version}"',
        text,
        count=1,
    )
    PYPROJECT.write_text(new)


def write_version_py(version: str) -> None:
    text = VERSION_PY.read_text()
    new = re.sub(
        r'(__version__\s*:\s*str\s*=\s*)"[^"]+"',
        rf'\1"{version}"',
        text,
        count=1,
    )
    VERSION_PY.write_text(new)


def write_npm(version: str) -> None:
    data = json.loads(NPM_PKG.read_text())
    data["version"] = version
    NPM_PKG.write_text(json.dumps(data, indent=2) + "\n")


def write_homebrew(version: str) -> None:
    text = HOMEBREW.read_text()
    new = re.sub(
        r"quell-agent-\d+\.\d+\.\d+[a-z0-9.-]*\.tar\.gz",
        f"quell-agent-{version}.tar.gz",
        text,
    )
    HOMEBREW.write_text(new)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bump",
        metavar="X.Y.Z",
        help="Rewrite every version string to this value.",
    )
    args = parser.parse_args()

    if args.bump:
        if not SEMVER_RE.match(args.bump):
            print(f"error: --bump value '{args.bump}' is not semver", file=sys.stderr)
            return 2
        write_pyproject(args.bump)
        write_version_py(args.bump)
        write_npm(args.bump)
        write_homebrew(args.bump)
        print(f"Bumped every version string to {args.bump}")
        return 0

    versions = {
        "pyproject.toml": read_pyproject(),
        "quell/version.py": read_version_py(),
        "packaging/npm/package.json": read_npm(),
        "packaging/homebrew/quell.rb": read_homebrew(),
    }

    width = max(len(k) for k in versions)
    for name, ver in versions.items():
        marker = "?" if ver is None else " "
        print(f"  {marker} {name:<{width}}  {ver or '(template — no version)'}")

    # Homebrew is allowed to lag (template state) until the first
    # PyPI release. Skip it from the consensus check unless populated.
    consensus = {v for v in versions.values() if v is not None}
    if len(consensus) == 1:
        print(f"\nAll versions agree: {consensus.pop()}")
        return 0

    print(
        "\nerror: version strings disagree — run "
        "`python scripts/check_versions.py --bump X.Y.Z` to fix.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
