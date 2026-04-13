import { countBySeverity } from '../score.js';
import type { Finding, ScanResult, Severity } from '../types.js';

/** Escapes HTML special characters. */
function esc(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/** Returns the CSS class for a score value. */
function scoreClass(score: number): string {
  if (score > 80) return 'score-green';
  if (score > 50) return 'score-yellow';
  return 'score-red';
}

/** Returns the CSS class for a severity badge. */
function badgeClass(severity: Severity): string {
  return `badge-${severity.toLowerCase()}`;
}

/** Generates the score card section. */
export function renderScoreCard(result: ScanResult): string {
  return `
    <div class="score-card">
      <div class="score-label">Security Score</div>
      <div class="score-value ${scoreClass(result.score)}">
        ${result.score}<span class="score-max">/100</span>
      </div>
    </div>`;
}

/** Generates the severity summary stats bar. */
export function renderSummaryStats(result: ScanResult): string {
  const counts = countBySeverity(result.findings);
  const duration =
    result.durationMs < 1000
      ? `${result.durationMs}ms`
      : `${(result.durationMs / 1000).toFixed(1)}s`;

  return `
    <div class="summary">
      <div class="stat">
        <div class="stat-value" style="color:var(--critical)">${counts.CRITICAL}</div>
        <div class="stat-label">Critical</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color:var(--high)">${counts.HIGH}</div>
        <div class="stat-label">High</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color:var(--medium)">${counts.MEDIUM}</div>
        <div class="stat-label">Medium</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color:var(--low)">${counts.LOW}</div>
        <div class="stat-label">Low</div>
      </div>
      <div class="stat">
        <div class="stat-value">${result.findings.length}</div>
        <div class="stat-label">Total</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color:var(--text-dim)">${duration}</div>
        <div class="stat-label">Scan Time</div>
      </div>
    </div>`;
}

/** Generates the scan metadata section. */
export function renderMeta(result: ScanResult): string {
  const date = new Date(result.timestamp);
  const formatted = date.toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  return `
    <div class="meta">
      <div class="meta-item"><strong>Target:</strong> ${esc(result.targetPath)}</div>
      <div class="meta-item"><strong>Files scanned:</strong> ${result.filesScanned}</div>
      <div class="meta-item"><strong>Date:</strong> ${formatted}</div>
    </div>`;
}

/** Generates the filter bar for severity filtering. */
export function renderFilterBar(result: ScanResult): string {
  const counts = countBySeverity(result.findings);
  const severities: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];

  const buttons = severities
    .filter((s) => counts[s] > 0)
    .map(
      (s) =>
        `<button class="filter-btn active" data-severity="${s}">${s}<span class="count">${counts[s]}</span></button>`,
    )
    .join('\n      ');

  return `
    <div class="filter-bar">
      <button class="filter-btn active" data-severity="ALL">All<span class="count">${result.findings.length}</span></button>
      ${buttons}
    </div>`;
}

/** Generates a single finding card. */
function renderFinding(finding: Finding, index: number): string {
  const open = index === 0 ? ' open' : '';
  return `
    <div class="finding${open}" data-severity="${finding.severity}">
      <div class="finding-header" onclick="this.parentElement.classList.toggle('open')">
        <span class="badge ${badgeClass(finding.severity)}">${finding.severity}</span>
        <span class="finding-title">${esc(finding.title)}</span>
        <span class="finding-location">${esc(finding.filePath)}:${finding.line}</span>
        <span class="finding-chevron">&#9654;</span>
      </div>
      <div class="finding-body">
        <div class="finding-desc">${esc(finding.description)}</div>
        ${finding.codeSnippet ? `<div class="code-block">${esc(finding.codeSnippet)}</div>` : ''}
        <div class="fix-box">
          <div class="fix-label">How to fix</div>
          <div class="fix-text">${escapeFix(finding.fix)}</div>
        </div>
        ${finding.docsUrl ? `<a class="docs-link" href="${esc(finding.docsUrl)}" target="_blank" rel="noopener">Learn more &rarr;</a>` : ''}
      </div>
    </div>`;
}

/** Escapes fix text but preserves backtick code blocks. */
function escapeFix(text: string): string {
  return esc(text).replace(/`([^`]+)`/g, '<code>$1</code>');
}

/** Generates all finding cards. */
export function renderFindings(result: ScanResult): string {
  if (result.findings.length === 0) {
    return `
      <div class="score-card" style="padding:32px">
        <div style="font-size:48px;margin-bottom:12px">&#10003;</div>
        <div style="font-size:18px;font-weight:600;color:var(--green)">No issues found</div>
        <div style="color:var(--text-dim);margin-top:8px">Your code looks clean. Nice work!</div>
      </div>`;
  }

  const cards = result.findings.map((f, i) => renderFinding(f, i)).join('');

  return `
    <div class="findings-header">Findings (${result.findings.length})</div>
    ${renderFilterBar(result)}
    ${cards}`;
}

/** Generates the footer. */
export function renderFooter(): string {
  return `
    <div class="footer">
      Generated by <a href="https://github.com/Bhartiyaanshul/vibeaudit">Frisk</a>
      &middot; Frisk your vibe-coded app before someone else does
    </div>`;
}
