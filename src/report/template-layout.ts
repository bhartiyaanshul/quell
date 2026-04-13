import type { ScanResult } from '../types.js';
import {
  renderFindings,
  renderFooter,
  renderMeta,
  renderScoreCard,
  renderSummaryStats,
} from './template-sections.js';
import { getStyles } from './template-styles.js';

/** Generates the interactive JavaScript for the report. */
function getScript(): string {
  return `
    // Theme toggle
    const toggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    toggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      html.setAttribute('data-theme', next);
      toggle.textContent = next === 'light' ? '☾ Dark' : '☀ Light';
      localStorage.setItem('frisk-theme', next);
    });
    // Restore saved theme
    const saved = localStorage.getItem('frisk-theme');
    if (saved) {
      html.setAttribute('data-theme', saved);
      toggle.textContent = saved === 'light' ? '☾ Dark' : '☀ Light';
    }

    // Severity filter
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const severity = btn.dataset.severity;

        // Toggle active state
        if (severity === 'ALL') {
          document.querySelectorAll('.filter-btn').forEach(b => b.classList.add('active'));
        } else {
          const allBtn = document.querySelector('[data-severity="ALL"]');
          if (allBtn) allBtn.classList.remove('active');
          btn.classList.toggle('active');
        }

        // Get all active severities
        const active = new Set();
        document.querySelectorAll('.filter-btn.active').forEach(b => {
          if (b.dataset.severity !== 'ALL') active.add(b.dataset.severity);
        });

        // If none active, show all
        const showAll = active.size === 0 || document.querySelector('[data-severity="ALL"]')?.classList.contains('active');

        document.querySelectorAll('.finding').forEach(f => {
          f.style.display = (showAll || active.has(f.dataset.severity)) ? '' : 'none';
        });
      });
    });

    // Expand/collapse all on double-click header
    document.querySelector('.findings-header')?.addEventListener('dblclick', () => {
      const findings = document.querySelectorAll('.finding');
      const allOpen = Array.from(findings).every(f => f.classList.contains('open'));
      findings.forEach(f => {
        if (allOpen) f.classList.remove('open');
        else f.classList.add('open');
      });
    });
  `;
}

/** Builds the complete HTML report as a single self-contained file. */
export function buildHtmlReport(result: ScanResult): string {
  return `<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VibeAudit Report — Score: ${result.score}/100</title>
  <style>${getStyles()}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">⟁ frisk <span>v0.1.0</span></div>
      <button id="theme-toggle" class="theme-toggle">☀ Light</button>
    </div>

    ${renderScoreCard(result)}
    ${renderSummaryStats(result)}
    ${renderMeta(result)}
    ${renderFindings(result)}
    ${renderFooter()}
  </div>
  <script>${getScript()}</script>
</body>
</html>`;
}
