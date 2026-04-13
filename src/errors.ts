/** Base error class for all Frisk errors. */
export class FriskError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FriskError';
  }
}

/** Thrown when a required external tool (semgrep, gitleaks) is not installed. */
export class ToolNotFoundError extends FriskError {
  constructor(
    public readonly tool: string,
    public readonly installHint: string,
  ) {
    super(`${tool} is not installed. ${installHint}`);
    this.name = 'ToolNotFoundError';
  }
}

/** Thrown when a scan operation fails. */
export class ScanError extends FriskError {
  constructor(
    public readonly scanner: string,
    message: string,
    public readonly cause?: unknown,
  ) {
    super(`[${scanner}] ${message}`);
    this.name = 'ScanError';
  }
}

/** Thrown when the target path does not exist or is not a directory. */
export class InvalidTargetError extends FriskError {
  constructor(public readonly targetPath: string) {
    super(`Target path does not exist or is not a directory: ${targetPath}`);
    this.name = 'InvalidTargetError';
  }
}
