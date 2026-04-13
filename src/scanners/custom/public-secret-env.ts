/**
 * Rule: API keys exposed via NEXT_PUBLIC_* environment variables
 *
 * NEXT_PUBLIC_ vars are bundled into the client JavaScript. Putting secret keys
 * (Stripe secret keys, OpenAI keys, etc.) in NEXT_PUBLIC_ vars exposes them to
 * every visitor of the site.
 *
 * Real-world example: Multiple Lovable/v0 apps ship NEXT_PUBLIC_OPENAI_API_KEY
 * which allows anyone to use the developer's OpenAI credits.
 */
import type { FileInfo, Finding } from '../../types.js';

/** Patterns that indicate a secret key exposed via NEXT_PUBLIC_. */
const DANGEROUS_PATTERNS = [
  { pattern: /NEXT_PUBLIC_OPENAI_API_KEY/g, name: 'OpenAI API Key' },
  { pattern: /NEXT_PUBLIC_ANTHROPIC_API_KEY/g, name: 'Anthropic API Key' },
  { pattern: /NEXT_PUBLIC_STRIPE_SECRET_KEY/g, name: 'Stripe Secret Key' },
  { pattern: /NEXT_PUBLIC_STRIPE_API_KEY/g, name: 'Stripe API Key' },
  { pattern: /NEXT_PUBLIC_AWS_SECRET/g, name: 'AWS Secret' },
  { pattern: /NEXT_PUBLIC_DATABASE_URL/g, name: 'Database URL' },
  { pattern: /NEXT_PUBLIC_SUPABASE_SERVICE_ROLE/g, name: 'Supabase Service Role Key' },
  { pattern: /NEXT_PUBLIC_GITHUB_TOKEN/g, name: 'GitHub Token' },
  { pattern: /NEXT_PUBLIC_.*_SECRET/g, name: 'Secret Key' },
  { pattern: /NEXT_PUBLIC_.*_PRIVATE/g, name: 'Private Key' },
];

/** Detects secret API keys exposed via NEXT_PUBLIC_* environment variables. */
export function publicSecretEnvRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  const relevantFiles = files.filter(
    (f) =>
      f.relativePath.endsWith('.env') ||
      f.relativePath.endsWith('.env.local') ||
      f.relativePath.endsWith('.env.production') ||
      f.relativePath.endsWith('.env.development') ||
      f.relativePath.endsWith('.env.staging') ||
      f.relativePath.includes('next.config') ||
      f.relativePath.endsWith('.ts') ||
      f.relativePath.endsWith('.tsx') ||
      f.relativePath.endsWith('.js') ||
      f.relativePath.endsWith('.jsx'),
  );

  for (const file of relevantFiles) {
    const lines = file.content.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (!line) continue;

      for (const { pattern, name } of DANGEROUS_PATTERNS) {
        pattern.lastIndex = 0;
        const match = pattern.exec(line);
        if (match) {
          findings.push({
            title: `${name} exposed via NEXT_PUBLIC_* variable`,
            severity: 'CRITICAL',
            source: 'custom',
            ruleId: 'frisk/public-secret-env',
            filePath: file.relativePath,
            line: i + 1,
            codeSnippet: line.trim(),
            description: `The variable "${match[0]}" is prefixed with NEXT_PUBLIC_, which means it will be bundled into the client-side JavaScript. Anyone visiting your site can extract this value from the browser's dev tools.`,
            fix: 'Remove the NEXT_PUBLIC_ prefix. Move this to a server-only env var. Access it only in API routes or getServerSideProps, never in client components.',
            docsUrl:
              'https://nextjs.org/docs/app/building-your-application/configuring/environment-variables',
          });
          break;
        }
      }
    }
  }

  return findings;
}
