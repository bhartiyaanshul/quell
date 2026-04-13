import { execSync } from 'node:child_process';
import type { Finding, Severity } from '../types.js';

/** Shape of a single result from Semgrep's JSON output. */
interface SemgrepResult {
  check_id?: string;
  path?: string;
  start?: { line?: number; col?: number };
  end?: { line?: number };
  extra?: {
    message?: string;
    severity?: string;
    metadata?: {
      cwe?: string[] | string;
      references?: string[];
      fix?: string;
    };
    lines?: string;
    fix?: string;
  };
}

/** Maps Semgrep severity strings to our severity levels. */
function mapSeverity(semgrepSeverity: string | undefined): Severity {
  switch (semgrepSeverity?.toUpperCase()) {
    case 'ERROR':
      return 'HIGH';
    case 'WARNING':
      return 'MEDIUM';
    case 'INFO':
      return 'LOW';
    default:
      return 'MEDIUM';
  }
}

/** Extracts a human-readable title from a Semgrep rule ID. */
function ruleIdToTitle(ruleId: string): string {
  const parts = ruleId.split('.');
  const lastPart = parts[parts.length - 1] ?? ruleId;
  return lastPart.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Builds a docs URL from CWE or rule metadata. */
function buildDocsUrl(result: SemgrepResult): string | undefined {
  const cwe = result.extra?.metadata?.cwe;
  if (cwe) {
    const firstCwe = Array.isArray(cwe) ? cwe[0] : cwe;
    if (firstCwe) {
      const cweId = firstCwe.match(/CWE-(\d+)/)?.[1];
      if (cweId) {
        return `https://cwe.mitre.org/data/definitions/${cweId}.html`;
      }
    }
  }

  const refs = result.extra?.metadata?.references;
  if (refs && refs.length > 0) {
    return refs[0];
  }

  return undefined;
}

/** Runs Semgrep on the target and returns parsed findings. */
export function runSemgrep(targetPath: string): Finding[] {
  try {
    const output = execSync(`semgrep scan --config auto --json --quiet "${targetPath}"`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 120_000,
      maxBuffer: 10 * 1024 * 1024,
    });

    const parsed: unknown = JSON.parse(output);
    if (!parsed || typeof parsed !== 'object' || !('results' in parsed)) {
      return [];
    }

    const data = parsed as { results: unknown[] };
    if (!Array.isArray(data.results)) {
      return [];
    }

    return data.results
      .map((r: unknown): Finding | undefined => {
        const result = r as SemgrepResult;
        if (!result.path || !result.check_id) return undefined;

        return {
          title: ruleIdToTitle(result.check_id),
          severity: mapSeverity(result.extra?.severity),
          source: 'semgrep',
          ruleId: result.check_id,
          filePath: result.path,
          line: result.start?.line ?? 1,
          endLine: result.end?.line,
          column: result.start?.col,
          codeSnippet: result.extra?.lines ?? '',
          description: result.extra?.message ?? 'Security issue detected by Semgrep.',
          fix:
            result.extra?.fix ??
            result.extra?.metadata?.fix ??
            'Review this code for security issues.',
          docsUrl: buildDocsUrl(result),
        };
      })
      .filter((f): f is Finding => f !== undefined);
  } catch (error: unknown) {
    // Semgrep exits with code 1 when it finds results — parse stderr/stdout
    if (error && typeof error === 'object' && 'stdout' in error) {
      const stdout = (error as { stdout: string }).stdout;
      if (stdout && typeof stdout === 'string') {
        try {
          const parsed: unknown = JSON.parse(stdout);
          if (parsed && typeof parsed === 'object' && 'results' in parsed) {
            const data = parsed as { results: unknown[] };
            if (Array.isArray(data.results)) {
              return data.results
                .map((r: unknown): Finding | undefined => {
                  const result = r as SemgrepResult;
                  if (!result.path || !result.check_id) return undefined;

                  return {
                    title: ruleIdToTitle(result.check_id),
                    severity: mapSeverity(result.extra?.severity),
                    source: 'semgrep',
                    ruleId: result.check_id,
                    filePath: result.path,
                    line: result.start?.line ?? 1,
                    endLine: result.end?.line,
                    column: result.start?.col,
                    codeSnippet: result.extra?.lines ?? '',
                    description: result.extra?.message ?? 'Security issue detected by Semgrep.',
                    fix:
                      result.extra?.fix ??
                      result.extra?.metadata?.fix ??
                      'Review this code for security issues.',
                    docsUrl: buildDocsUrl(result),
                  };
                })
                .filter((f): f is Finding => f !== undefined);
            }
          }
        } catch {
          // JSON parse failed on stdout — return empty
        }
      }
    }
    return [];
  }
}
