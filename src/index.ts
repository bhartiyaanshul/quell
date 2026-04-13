/**
 * Frisk — programmatic API
 *
 * Use this module to run Frisk scans from your own code.
 * Full scanning API will be exposed in a future phase.
 */

export type {
  CliOptions,
  FileInfo,
  Finding,
  FindingSource,
  GitInfo,
  OutputFormat,
  ScanResult,
  Severity,
} from './types.js';

export { SEVERITY_ORDER, SEVERITY_WEIGHTS } from './types.js';
