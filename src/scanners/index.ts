import { calculateScore } from '../score.js';
import type { FileInfo, Finding, GitInfo, ScanResult } from '../types.js';
import { runCustomRules } from './custom/index.js';
import { runGitleaks } from './gitleaks.js';
import { runSemgrep } from './semgrep.js';

interface ScanOptions {
  targetPath: string;
  files: FileInfo[];
  gitInfo: GitInfo;
  semgrepAvailable: boolean;
  gitleaksAvailable: boolean;
}

interface ScannerProgress {
  onScannerStart: (name: string) => void;
  onScannerDone: (name: string, count: number) => void;
}

/** Runs all available scanners and returns aggregated results. */
export function runAllScanners(options: ScanOptions, progress: ScannerProgress): ScanResult {
  const startTime = Date.now();
  const allFindings: Finding[] = [];

  // Run Semgrep if available
  if (options.semgrepAvailable) {
    progress.onScannerStart('Semgrep');
    const semgrepFindings = runSemgrep(options.targetPath);
    allFindings.push(...semgrepFindings);
    progress.onScannerDone('Semgrep', semgrepFindings.length);
  }

  // Run gitleaks if available and target is a git repo
  if (options.gitleaksAvailable && options.gitInfo.isGitRepo) {
    progress.onScannerStart('gitleaks');
    const gitleaksFindings = runGitleaks(options.targetPath);
    allFindings.push(...gitleaksFindings);
    progress.onScannerDone('gitleaks', gitleaksFindings.length);
  }

  // Run custom rules engine (always available — no external tools needed)
  progress.onScannerStart('Custom Rules (13 checks)');
  const customFindings = runCustomRules(options.files, options.gitInfo);
  allFindings.push(...customFindings);
  progress.onScannerDone('Custom Rules', customFindings.length);

  // Deduplicate findings by file+line+ruleId
  const deduplicated = deduplicateFindings(allFindings);

  // Sort by severity (CRITICAL first)
  const sorted = sortFindings(deduplicated);

  const durationMs = Date.now() - startTime;

  return {
    targetPath: options.targetPath,
    findings: sorted,
    filesScanned: options.files.length,
    durationMs,
    timestamp: new Date().toISOString(),
    score: calculateScore(sorted),
  };
}

/** Removes duplicate findings based on file path, line, and rule ID. */
function deduplicateFindings(findings: Finding[]): Finding[] {
  const seen = new Set<string>();
  const unique: Finding[] = [];

  for (const finding of findings) {
    const key = `${finding.filePath}:${finding.line}:${finding.ruleId}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(finding);
    }
  }

  return unique;
}

const SEVERITY_RANK: Record<string, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  INFO: 4,
};

/** Sorts findings by severity (most severe first), then by file path. */
function sortFindings(findings: Finding[]): Finding[] {
  return [...findings].sort((a, b) => {
    const severityDiff = (SEVERITY_RANK[a.severity] ?? 4) - (SEVERITY_RANK[b.severity] ?? 4);
    if (severityDiff !== 0) return severityDiff;
    return a.filePath.localeCompare(b.filePath);
  });
}
