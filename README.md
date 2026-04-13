# Frisk

> Frisk your vibe-coded app before someone else does.

[![npm version](https://img.shields.io/npm/v/friskit)](https://www.npmjs.com/package/friskit)
[![MIT License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![Node.js](https://img.shields.io/badge/node-%3E%3D20-green)](https://nodejs.org)

A zero-config CLI security scanner for apps built with Cursor, Lovable, Bolt, v0, Replit, and other AI coding tools. Combines Semgrep, gitleaks, and 13 hand-written AST-powered rules into a single command that produces a beautiful HTML report.

**One command. Sixty seconds. A report card with severity-ranked findings and a plain-English fix for each one.**

```bash
npx friskit ./my-app
```

---

## Why

A recent scan of 198 vibe-coded apps found **196 had vulnerabilities**. A Lovable showcase app had its auth logic backwards and exposed 18,000+ users. Another vibe-coded app leaked 1.5 million API keys.

AI writes code fast. It doesn't write code safe. If you shipped something with an AI coding tool, you need this.

## Install

```bash
# Run directly (no install)
npx friskit ./my-app

# Or install globally
npm install -g friskit
friskit ./my-app
```

Requires **Node.js 20+**.

## Usage

```bash
# Scan a directory
friskit ./my-app

# Custom output path
friskit ./my-app --output report.html

# JSON output (for CI pipelines)
friskit ./my-app --format json

# Fail CI if HIGH or above findings exist
friskit ./my-app --fail-on high

# Combine flags
friskit ./my-app --format json --output results.json --fail-on critical
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output <path>` | Report file path | `friskit-report.html` |
| `-f, --format <fmt>` | Output format: `html` or `json` | `html` |
| `--fail-on <sev>` | Exit code 1 if findings at this severity or above (`critical`, `high`, `medium`, `low`) | - |
| `-V, --version` | Print version | - |
| `-h, --help` | Show help | - |

## What It Detects

### Static Analysis (via Semgrep)

SQL injection, XSS, hardcoded secrets, weak crypto, insecure deserialization, path traversal, and hundreds more from Semgrep's open-source ruleset.

### Secret Scanning (via gitleaks)

API keys buried in git history -- AWS, Stripe, OpenAI, Anthropic, GitHub, Supabase, and 100+ other providers.

### Vibe-Code Specific Rules (custom AST engine)

These are the checks that catch what generic tools miss -- patterns that AI coding assistants produce over and over:

| Rule | Severity | What it catches |
|------|----------|----------------|
| `.env` files in project/git | CRITICAL | `.env` files committed or present in project directory |
| Supabase without RLS | CRITICAL | Supabase anon key used but no Row Level Security in SQL schema |
| Plaintext passwords | CRITICAL | Password storage without bcrypt/argon2, or using MD5/SHA1 for passwords |
| `NEXT_PUBLIC_*` secrets | CRITICAL | API keys, secrets, or tokens in `NEXT_PUBLIC_` environment variables |
| AI endpoints without rate limits | HIGH | OpenAI/Anthropic/AI SDK route handlers with no rate limiting |
| Unprotected admin routes | HIGH | Admin API routes with no auth middleware or session checks |
| CORS wildcard + credentials | HIGH | `origin: "*"` combined with `credentials: true` |
| Weak/hardcoded JWT secrets | HIGH | JWT secrets under 32 characters or hardcoded in source |
| `eval()` / `Function()` | HIGH | Direct eval or Function constructor calls |
| Open redirects | HIGH | `res.redirect()` with user-controlled URLs |
| NoSQL injection | HIGH | MongoDB queries with unsanitized user input |
| Unsafe `dangerouslySetInnerHTML` | MEDIUM | Raw HTML rendering without DOMPurify or similar sanitizer |
| Insecure cookies | MEDIUM | Cookies missing `httpOnly`, `secure`, or `sameSite` flags |

## How It Works

1. **Walk** -- Recursively scans the target directory, respecting `.gitignore`, skipping binaries and `node_modules`
2. **Parse** -- Builds TypeScript ASTs for JS/TS/JSX/TSX files using the TypeScript Compiler API (cached across rules)
3. **Scan** -- Runs three scanner layers in sequence:
   - **Semgrep** (if installed) -- static analysis with `--config auto`
   - **gitleaks** (if installed) -- secret detection across git history
   - **Custom rules** -- 13 AST-powered checks purpose-built for vibe-coded patterns
4. **Score** -- Calculates a 0-100 security score: `100 - (25 x CRITICAL + 10 x HIGH + 3 x MEDIUM + 1 x LOW)`
5. **Report** -- Generates a self-contained HTML report with dark/light theme, severity filtering, expandable findings with code snippets and fix recommendations

## The HTML Report

The report is a single `.html` file with everything inlined -- no external dependencies. Features:

- Dark/light theme toggle (saved to localStorage)
- Security score with color-coded rating
- Severity breakdown with counts
- Filter findings by severity
- Each finding expands to show: description, code snippet, fix recommendation, and documentation link
- Responsive layout for mobile/desktop
- Double-click "Findings" header to expand/collapse all

## CI Integration

### GitHub Actions

```yaml
- name: Security scan
  run: npx friskit . --format json --fail-on high
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Scan complete, no findings above threshold (or no `--fail-on` set) |
| `1` | Findings at or above `--fail-on` severity detected |

## External Tools (Optional)

Frisk works standalone with its custom rules engine. For full coverage, install:

### Semgrep

```bash
# macOS / Linux
pip install semgrep

# Docs: https://semgrep.dev/docs/getting-started/
```

### gitleaks

```bash
# macOS
brew install gitleaks

# Windows
choco install gitleaks
# or
scoop install gitleaks

# Docs: https://github.com/gitleaks/gitleaks#installing
```

## Development

```bash
git clone https://github.com/Bhartiyaanshul/vibeaudit.git
cd vibeaudit
npm install
npm run build
npm test

# Run against the fixture app
node dist/cli.js fixtures/vulnerable-app
```

## Contributing

Contributions welcome! To add a new detection rule:

1. Create a new file in `src/scanners/custom/`
2. Export a function matching `(files: FileInfo[], gitInfo?: GitInfo) => Finding[]`
3. Register it in `src/scanners/custom/index.ts`
4. Add a test in `tests/rules/`
5. Add a fixture in `fixtures/vulnerable-app/`

## License

[MIT](./LICENSE) -- built by [Anshul Bhartiya](https://anshulbuilds.xyz)

[Website](https://frisk.anshulbuilds.xyz) | [GitHub](https://github.com/Bhartiyaanshul/vibeaudit) | [Twitter](https://x.com/Bhartiyaanshul)
