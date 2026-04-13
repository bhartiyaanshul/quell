/** All CSS for the HTML report — dark/light themes, responsive layout. */
export function getStyles(): string {
  return `
    :root {
      --bg: #0a0a0f;
      --bg-card: #12121a;
      --bg-code: #1a1a2e;
      --bg-hover: #1e1e2f;
      --border: #2a2a3d;
      --text: #e4e4ef;
      --text-dim: #8888a0;
      --text-muted: #5c5c74;
      --accent: #7c5cff;
      --accent-dim: #5c3fd6;
      --critical: #ff4757;
      --critical-bg: rgba(255, 71, 87, 0.1);
      --high: #ff8c42;
      --high-bg: rgba(255, 140, 66, 0.1);
      --medium: #ffc53d;
      --medium-bg: rgba(255, 197, 61, 0.1);
      --low: #4da6ff;
      --low-bg: rgba(77, 166, 255, 0.1);
      --info: #6b7280;
      --info-bg: rgba(107, 114, 128, 0.1);
      --green: #36d399;
      --green-bg: rgba(54, 211, 153, 0.08);
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
      --radius: 12px;
      --radius-sm: 8px;
    }

    [data-theme="light"] {
      --bg: #f8f8fc;
      --bg-card: #ffffff;
      --bg-code: #f0f0f6;
      --bg-hover: #f0f0f6;
      --border: #e2e2ee;
      --text: #1a1a2e;
      --text-dim: #5c5c74;
      --text-muted: #8888a0;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    .container { max-width: 960px; margin: 0 auto; padding: 40px 24px; }

    /* Header */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 40px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border);
    }
    .logo {
      font-size: 20px;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.02em;
    }
    .logo span { color: var(--text-dim); font-weight: 400; }
    .theme-toggle {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 6px 14px;
      color: var(--text-dim);
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
    }
    .theme-toggle:hover { border-color: var(--accent); color: var(--text); }

    /* Score */
    .score-card {
      text-align: center;
      padding: 48px 24px;
      margin-bottom: 32px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
    }
    .score-label {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-muted);
      margin-bottom: 12px;
    }
    .score-value {
      font-size: 96px;
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.04em;
    }
    .score-max { font-size: 36px; color: var(--text-muted); font-weight: 400; }
    .score-green { color: var(--green); }
    .score-yellow { color: var(--medium); }
    .score-red { color: var(--critical); }

    /* Summary stats */
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 32px;
    }
    .stat {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 16px;
      text-align: center;
    }
    .stat-value { font-size: 28px; font-weight: 700; }
    .stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

    /* Meta info */
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      margin-bottom: 32px;
      font-size: 13px;
      color: var(--text-dim);
    }
    .meta-item strong { color: var(--text); }

    /* Severity badges */
    .badge {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 100px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-critical { background: var(--critical-bg); color: var(--critical); border: 1px solid var(--critical); }
    .badge-high { background: var(--high-bg); color: var(--high); border: 1px solid var(--high); }
    .badge-medium { background: var(--medium-bg); color: var(--medium); border: 1px solid var(--medium); }
    .badge-low { background: var(--low-bg); color: var(--low); border: 1px solid var(--low); }
    .badge-info { background: var(--info-bg); color: var(--info); border: 1px solid var(--info); }

    /* Findings */
    .findings-header {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }
    .finding {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 12px;
      overflow: hidden;
      transition: border-color 0.2s;
    }
    .finding:hover { border-color: var(--accent-dim); }
    .finding-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 20px;
      cursor: pointer;
      user-select: none;
    }
    .finding-title { font-weight: 600; font-size: 14px; flex: 1; }
    .finding-location {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
    }
    .finding-chevron {
      color: var(--text-muted);
      transition: transform 0.2s;
      font-size: 12px;
    }
    .finding.open .finding-chevron { transform: rotate(90deg); }
    .finding-body {
      display: none;
      padding: 0 20px 20px;
      border-top: 1px solid var(--border);
    }
    .finding.open .finding-body { display: block; padding-top: 16px; }

    .finding-desc { font-size: 14px; color: var(--text-dim); margin-bottom: 16px; line-height: 1.7; }

    .code-block {
      background: var(--bg-code);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 16px;
      margin-bottom: 16px;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 13px;
      line-height: 1.6;
      white-space: pre;
      color: var(--text-dim);
    }

    .fix-box {
      background: var(--green-bg);
      border: 1px solid rgba(54, 211, 153, 0.2);
      border-radius: var(--radius-sm);
      padding: 14px 16px;
      margin-bottom: 12px;
    }
    .fix-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--green);
      margin-bottom: 6px;
    }
    .fix-text { font-size: 13px; color: var(--text-dim); line-height: 1.6; }
    .fix-text code {
      background: var(--bg-code);
      padding: 1px 6px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 12px;
    }

    .docs-link {
      display: inline-block;
      font-size: 12px;
      color: var(--accent);
      text-decoration: none;
    }
    .docs-link:hover { text-decoration: underline; }

    /* Footer */
    .footer {
      margin-top: 48px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
    }
    .footer a { color: var(--accent); text-decoration: none; }
    .footer a:hover { text-decoration: underline; }

    /* Filter bar */
    .filter-bar {
      display: flex;
      gap: 8px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .filter-btn {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 100px;
      padding: 6px 14px;
      font-size: 12px;
      cursor: pointer;
      color: var(--text-dim);
      transition: all 0.2s;
    }
    .filter-btn:hover, .filter-btn.active {
      border-color: var(--accent);
      color: var(--text);
    }
    .filter-btn .count { margin-left: 4px; opacity: 0.6; }

    @media (max-width: 640px) {
      .container { padding: 24px 16px; }
      .score-value { font-size: 64px; }
      .summary { grid-template-columns: repeat(2, 1fr); }
      .finding-header { flex-wrap: wrap; }
      .finding-location { width: 100%; }
    }
  `;
}
