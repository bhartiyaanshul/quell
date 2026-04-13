import { execSync } from 'node:child_process';
import type { Finding, Severity } from '../types.js';

/** Shape of a single result from gitleaks JSON output. */
interface GitleaksResult {
  Description?: string;
  RuleID?: string;
  File?: string;
  StartLine?: number;
  EndLine?: number;
  StartColumn?: number;
  Match?: string;
  Secret?: string;
  Commit?: string;
  Author?: string;
  Date?: string;
  Tags?: string[];
}

/** Maps common gitleaks rule IDs to severity levels. */
function mapSeverity(ruleId: string | undefined): Severity {
  if (!ruleId) return 'HIGH';

  const lower = ruleId.toLowerCase();

  // Critical: cloud provider keys, payment keys
  if (
    lower.includes('aws') ||
    lower.includes('stripe-secret') ||
    lower.includes('private-key') ||
    lower.includes('gcp')
  ) {
    return 'CRITICAL';
  }

  // High: API keys, tokens
  if (
    lower.includes('api-key') ||
    lower.includes('token') ||
    lower.includes('secret') ||
    lower.includes('password') ||
    lower.includes('openai') ||
    lower.includes('anthropic') ||
    lower.includes('supabase')
  ) {
    return 'HIGH';
  }

  return 'MEDIUM';
}

/** Generates a human-readable title from a gitleaks rule ID. */
function ruleIdToTitle(ruleId: string): string {
  return ruleId.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Masks a secret for display, showing only first/last 4 chars. */
function maskSecret(secret: string): string {
  if (secret.length <= 8) return '****';
  return `${secret.slice(0, 4)}...${secret.slice(-4)}`;
}

/** Generates a fix recommendation based on the leak type. */
function generateFix(ruleId: string): string {
  const lower = ruleId.toLowerCase();

  if (lower.includes('aws')) {
    return 'Rotate this AWS credential immediately via the AWS IAM console. Remove it from source code and use environment variables or AWS Secrets Manager.';
  }
  if (lower.includes('stripe')) {
    return 'Rotate this Stripe key in the Stripe Dashboard. Use environment variables to store API keys, never commit them to source.';
  }
  if (lower.includes('openai')) {
    return 'Rotate this OpenAI API key at platform.openai.com. Move it to an environment variable and add .env to .gitignore.';
  }
  if (lower.includes('anthropic')) {
    return 'Rotate this Anthropic API key at console.anthropic.com. Store it in an environment variable, not in source code.';
  }
  if (lower.includes('github')) {
    return 'Revoke this GitHub token at github.com/settings/tokens. Use environment variables or GitHub Actions secrets.';
  }
  if (lower.includes('supabase')) {
    return 'Rotate this Supabase key in your Supabase project settings. Use environment variables for all Supabase credentials.';
  }
  if (lower.includes('private-key')) {
    return 'Remove this private key from source control immediately. Generate a new key pair and store the private key securely outside the repo.';
  }

  return 'Remove this secret from source code and git history. Rotate the credential, then store it in environment variables or a secrets manager.';
}

/** Runs gitleaks on the target and returns parsed findings. */
export function runGitleaks(targetPath: string): Finding[] {
  try {
    // gitleaks exits 1 when leaks are found, so we catch and parse
    execSync(
      `gitleaks detect --source "${targetPath}" --report-format json --report-path - --no-banner`,
      {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 120_000,
        maxBuffer: 10 * 1024 * 1024,
      },
    );

    // Exit 0 = no leaks found
    return [];
  } catch (error: unknown) {
    if (!error || typeof error !== 'object') return [];

    // gitleaks exits 1 when leaks are found — results are on stdout
    const stdout = 'stdout' in error ? (error as { stdout: string }).stdout : '';
    if (!stdout || typeof stdout !== 'string') return [];

    try {
      const parsed: unknown = JSON.parse(stdout);
      if (!Array.isArray(parsed)) return [];

      return (parsed as GitleaksResult[])
        .map((result): Finding | undefined => {
          if (!result.File || !result.RuleID) return undefined;

          const secret = result.Secret ?? result.Match ?? '';
          const masked = maskSecret(secret);

          return {
            title: `Leaked Secret: ${ruleIdToTitle(result.RuleID)}`,
            severity: mapSeverity(result.RuleID),
            source: 'gitleaks',
            ruleId: result.RuleID,
            filePath: result.File,
            line: result.StartLine ?? 1,
            endLine: result.EndLine,
            column: result.StartColumn,
            codeSnippet: result.Match
              ? result.Match.replace(secret, masked)
              : `[secret: ${masked}]`,
            description: `${result.Description ?? 'Secret detected in source code'}. Found value: ${masked}${result.Commit ? ` (commit: ${result.Commit.slice(0, 8)})` : ''}`,
            fix: generateFix(result.RuleID),
            docsUrl: 'https://github.com/gitleaks/gitleaks#readme',
          };
        })
        .filter((f): f is Finding => f !== undefined);
    } catch {
      return [];
    }
  }
}
