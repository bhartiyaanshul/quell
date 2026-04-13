import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { countBySeverity } from '../score.js';
import type { ScanResult } from '../types.js';

/** Builds a machine-readable JSON report object. */
function buildJsonReport(result: ScanResult): object {
  const counts = countBySeverity(result.findings);

  return {
    version: '0.1.0',
    score: result.score,
    timestamp: result.timestamp,
    durationMs: result.durationMs,
    target: result.targetPath,
    filesScanned: result.filesScanned,
    summary: {
      total: result.findings.length,
      critical: counts.CRITICAL,
      high: counts.HIGH,
      medium: counts.MEDIUM,
      low: counts.LOW,
      info: counts.INFO,
    },
    findings: result.findings.map((f) => ({
      title: f.title,
      severity: f.severity,
      source: f.source,
      ruleId: f.ruleId,
      file: f.filePath,
      line: f.line,
      description: f.description,
      fix: f.fix,
      codeSnippet: f.codeSnippet ?? null,
      docsUrl: f.docsUrl ?? null,
    })),
  };
}

/** Generates the JSON report and writes it to disk. Returns the absolute path. */
export function writeJsonReport(result: ScanResult, outputPath: string): string {
  const report = buildJsonReport(result);
  const absPath = resolve(outputPath);
  writeFileSync(absPath, JSON.stringify(report, null, 2), 'utf-8');
  return absPath;
}

/** Returns the JSON report as a string (for stdout piping). */
export function formatJsonReport(result: ScanResult): string {
  return JSON.stringify(buildJsonReport(result), null, 2);
}
