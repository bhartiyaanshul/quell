import type { Finding, Severity } from './types.js';
import { SEVERITY_WEIGHTS } from './types.js';

/** Calculates a security score from 0-100 based on findings. */
export function calculateScore(findings: Finding[]): number {
  let deductions = 0;

  for (const finding of findings) {
    deductions += SEVERITY_WEIGHTS[finding.severity];
  }

  return Math.max(0, 100 - deductions);
}

/** Returns a count of findings grouped by severity. */
export function countBySeverity(findings: Finding[]): Record<Severity, number> {
  return {
    CRITICAL: findings.filter((f) => f.severity === 'CRITICAL').length,
    HIGH: findings.filter((f) => f.severity === 'HIGH').length,
    MEDIUM: findings.filter((f) => f.severity === 'MEDIUM').length,
    LOW: findings.filter((f) => f.severity === 'LOW').length,
    INFO: findings.filter((f) => f.severity === 'INFO').length,
  };
}
