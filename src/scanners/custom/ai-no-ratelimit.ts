/**
 * Rule: AI SDK endpoints without rate limiting
 *
 * AI API calls cost money. Without rate limiting, anyone can hit your
 * endpoint in a loop and burn through your API credits. This is the #1
 * way vibe-coded AI apps get drained.
 *
 * Checks for files that import an AI SDK and export a route handler
 * but don't import any rate limiting middleware.
 *
 * https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/
 */
import type { FileInfo, Finding } from '../../types.js';
import { findImports, getSnippet, isParseable, parseFile } from '../../utils/ast.js';

const AI_SDKS = [
  'openai',
  '@anthropic-ai/sdk',
  'anthropic',
  '@google/generative-ai',
  '@google-cloud/aiplatform',
  'cohere-ai',
  'replicate',
  '@mistralai/mistralai',
  'ai',
  '@ai-sdk/openai',
  '@ai-sdk/anthropic',
  '@ai-sdk/google',
];

const RATE_LIMITERS = [
  'express-rate-limit',
  '@upstash/ratelimit',
  'next-rate-limit',
  'rate-limiter-flexible',
  'limiter',
  'bottleneck',
  'p-throttle',
  'ratelimit',
];

/** Checks if a file path looks like a route handler. */
function isRouteFile(path: string): boolean {
  return (
    path.includes('/api/') ||
    path.includes('/routes/') ||
    path.includes('/pages/api/') ||
    path.includes('/app/') ||
    path.includes('route.') ||
    path.includes('server.')
  );
}

/** Detects AI SDK usage in route files without rate limiting. */
export function aiNoRatelimitRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  // First, check if ANY file in the project imports a rate limiter
  const projectHasRateLimiter = files.some((f) => {
    if (!isParseable(f.relativePath)) return false;
    return RATE_LIMITERS.some((rl) => f.content.includes(rl));
  });

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    if (!isRouteFile(file.relativePath)) continue;

    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const imports = findImports(sourceFile);
    const aiImport = imports.find((imp) =>
      AI_SDKS.some((sdk) => imp.moduleSpecifier === sdk || imp.moduleSpecifier.startsWith(sdk)),
    );

    if (!aiImport) continue;

    // Check if THIS file imports a rate limiter
    const fileHasRateLimiter = imports.some((imp) =>
      RATE_LIMITERS.some((rl) => imp.moduleSpecifier === rl || imp.moduleSpecifier.startsWith(rl)),
    );

    // Also check for inline rate limiting patterns
    const hasInlineRateLimit =
      file.content.includes('rateLimit') ||
      file.content.includes('rateLimiter') ||
      file.content.includes('throttle');

    if (!fileHasRateLimiter && !hasInlineRateLimit && !projectHasRateLimiter) {
      findings.push({
        title: `AI endpoint without rate limiting: ${file.relativePath}`,
        severity: 'HIGH',
        source: 'custom',
        ruleId: 'frisk/ai-no-ratelimit',
        filePath: file.relativePath,
        line: aiImport.line,
        codeSnippet: getSnippet(sourceFile, aiImport.line, 3),
        description: `This route handler imports "${aiImport.moduleSpecifier}" but has no rate limiting. Anyone can call this endpoint repeatedly and drain your AI API credits. An attacker could rack up thousands of dollars in charges.`,
        fix: 'Add rate limiting middleware. For Next.js: use @upstash/ratelimit. For Express: use express-rate-limit. Example: limit to 10 requests per minute per IP.',
        docsUrl:
          'https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/',
      });
    }
  }

  return findings;
}
