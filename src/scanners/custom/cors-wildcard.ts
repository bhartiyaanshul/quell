/**
 * Rule: CORS wildcard (*) combined with credentials
 *
 * Setting Access-Control-Allow-Origin to * while also allowing credentials
 * is a dangerous misconfiguration. Browsers will block it, but some
 * vibe-coded backends set the origin dynamically to bypass this — which
 * enables cross-site request forgery from any domain.
 *
 * https://cwe.mitre.org/data/definitions/942.html
 */
import type { FileInfo, Finding } from '../../types.js';
import {
  findCalls,
  findStringLiterals,
  getSnippet,
  isParseable,
  parseFile,
} from '../../utils/ast.js';

/** Detects CORS wildcard with credentials misconfiguration. */
export function corsWildcardRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const content = file.content;
    const hasWildcardOrigin =
      content.includes("Access-Control-Allow-Origin', '*'") ||
      content.includes('Access-Control-Allow-Origin", "*"') ||
      content.includes("origin: '*'") ||
      content.includes('origin: "*"') ||
      content.includes("origin: '*'") ||
      content.includes('origin: true');

    const hasCredentials =
      content.includes("Access-Control-Allow-Credentials', 'true'") ||
      content.includes('Access-Control-Allow-Credentials", "true"') ||
      content.includes('credentials: true');

    if (hasWildcardOrigin && hasCredentials) {
      // Find the specific line
      const lines = content.split('\n');
      let originLine = 1;
      for (let i = 0; i < lines.length; i++) {
        if (lines[i]?.includes('Allow-Origin') || lines[i]?.includes('origin')) {
          if (lines[i]?.includes('*') || lines[i]?.includes('true')) {
            originLine = i + 1;
            break;
          }
        }
      }

      findings.push({
        title: 'CORS wildcard with credentials enabled',
        severity: 'HIGH',
        source: 'custom',
        ruleId: 'frisk/cors-wildcard-credentials',
        filePath: file.relativePath,
        line: originLine,
        codeSnippet: getSnippet(sourceFile, originLine, 3),
        description:
          'CORS is configured to allow all origins (*) while also allowing credentials. This combination lets any website make authenticated requests to your API, enabling CSRF attacks and data theft.',
        fix: 'Set Access-Control-Allow-Origin to your specific frontend domain instead of *. Example: `cors({ origin: "https://yourdomain.com", credentials: true })`.',
        docsUrl: 'https://cwe.mitre.org/data/definitions/942.html',
      });
    }

    // Also check for the cors() middleware pattern
    const calls = findCalls(sourceFile);
    for (const call of calls) {
      if (call.name === 'cors' && call.arguments.length > 0) {
        const argText = call.arguments[0]?.getText(sourceFile) ?? '';
        if (argText.includes("origin: '*'") || argText.includes('origin: "*"')) {
          if (argText.includes('credentials: true')) {
            findings.push({
              title: 'CORS middleware: wildcard origin with credentials',
              severity: 'HIGH',
              source: 'custom',
              ruleId: 'frisk/cors-middleware-wildcard',
              filePath: file.relativePath,
              line: call.line,
              codeSnippet: getSnippet(sourceFile, call.line, 3),
              description:
                'The cors() middleware is configured with origin: "*" and credentials: true. Any website can make authenticated requests to your API.',
              fix: 'Replace the wildcard origin with your actual frontend URL: `cors({ origin: "https://yourdomain.com", credentials: true })`.',
              docsUrl: 'https://cwe.mitre.org/data/definitions/942.html',
            });
          }
        }
      }
    }
  }

  return findings;
}
