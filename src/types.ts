/** Severity levels for security findings, ordered from most to least critical. */
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

/** The source scanner that produced a finding. */
export type FindingSource = 'semgrep' | 'gitleaks' | 'custom';

/** A single security finding from any scanner. */
export interface Finding {
  /** Short, descriptive title of the vulnerability */
  title: string;
  /** Severity level */
  severity: Severity;
  /** Which scanner found this */
  source: FindingSource;
  /** Name of the specific rule that triggered */
  ruleId: string;
  /** Absolute or relative path to the affected file */
  filePath: string;
  /** Line number where the issue was found (1-based) */
  line: number;
  /** End line number for multi-line findings */
  endLine?: number;
  /** Column number (1-based) */
  column?: number;
  /** The offending code snippet */
  codeSnippet: string;
  /** Plain-English explanation of why this is a problem */
  description: string;
  /** Plain-English fix recommendation */
  fix: string;
  /** Link to relevant documentation or CWE */
  docsUrl?: string;
}

/** Information about a file in the scanned project. */
export interface FileInfo {
  /** Absolute path to the file */
  absolutePath: string;
  /** Path relative to the scan target */
  relativePath: string;
  /** File content (lazy-loaded) */
  content: string;
}

/** Git-related information for the scanned project. */
export interface GitInfo {
  /** Whether the target is a git repository */
  isGitRepo: boolean;
  /** Root path of the git repository */
  gitRoot?: string;
}

/** Aggregated results from all scanners. */
export interface ScanResult {
  /** Path that was scanned */
  targetPath: string;
  /** All findings from all scanners */
  findings: Finding[];
  /** Total number of files scanned */
  filesScanned: number;
  /** Scan duration in milliseconds */
  durationMs: number;
  /** ISO timestamp when scan started */
  timestamp: string;
  /** Security score (0-100) */
  score: number;
}

/** Output format for the report. */
export type OutputFormat = 'html' | 'json';

/** CLI options parsed from command-line arguments. */
export interface CliOptions {
  /** Path to write the report file */
  output?: string;
  /** Output format */
  format: OutputFormat;
  /** Minimum severity to trigger a non-zero exit code */
  failOn?: Severity;
}

/** Severity weights for score calculation. */
export const SEVERITY_WEIGHTS: Record<Severity, number> = {
  CRITICAL: 25,
  HIGH: 10,
  MEDIUM: 3,
  LOW: 1,
  INFO: 0,
};

/** Ordered severity levels from most to least severe. */
export const SEVERITY_ORDER: readonly Severity[] = [
  'CRITICAL',
  'HIGH',
  'MEDIUM',
  'LOW',
  'INFO',
] as const;
