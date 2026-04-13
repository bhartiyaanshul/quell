/**
 * Rule: Open redirect vulnerabilities
 *
 * Redirecting to a URL taken directly from user input (query params, body)
 * enables phishing attacks — attacker sends a link like:
 * yourapp.com/redirect?url=evil.com and the user trusts it because
 * the domain starts with yourapp.com.
 *
 * https://cwe.mitre.org/data/definitions/601.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { findCalls, getSnippet, isParseable, parseFile, ts } from '../../utils/ast.js';

/** Checks if a node references user-controlled input. */
function isUserInput(node: ts.Expression, sourceFile: ts.SourceFile): boolean {
  const text = node.getText(sourceFile);
  return (
    text.includes('req.query') ||
    text.includes('req.body') ||
    text.includes('req.params') ||
    text.includes('searchParams') ||
    text.includes('query.') ||
    text.includes('params.') ||
    text.includes('request.url') ||
    text.includes('request.nextUrl')
  );
}

/** Detects open redirect patterns. */
export function openRedirectRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    if (!file.content.includes('redirect')) continue;

    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const calls = findCalls(sourceFile);

    for (const call of calls) {
      if (call.name !== 'redirect') continue;

      // Check if the redirect URL comes from user input
      for (const arg of call.arguments) {
        // Skip string literals — static URLs like '/dashboard' are safe
        if (ts.isStringLiteral(arg)) continue;

        if (isUserInput(arg, sourceFile)) {
          findings.push({
            title: 'Open redirect: user-controlled redirect URL',
            severity: 'HIGH',
            source: 'custom',
            ruleId: 'frisk/open-redirect',
            filePath: file.relativePath,
            line: call.line,
            codeSnippet: getSnippet(sourceFile, call.line),
            description:
              'The redirect destination comes from user input (query parameter, request body, etc.). An attacker can craft a URL like yourapp.com/redirect?url=evil.com to phish users — they trust the link because it starts with your domain.',
            fix: 'Validate the redirect URL against an allowlist of safe destinations. At minimum, ensure the URL is a relative path (starts with /) and doesn\'t contain "//". Best practice: use a lookup table of allowed redirect targets.',
            docsUrl: 'https://cwe.mitre.org/data/definitions/601.html',
          });
          break;
        }

        // Check for variable that might hold user input
        if (ts.isIdentifier(arg)) {
          const varName = arg.text;
          // Search backwards for where this variable is assigned from user input
          const lines = file.content.split('\n');
          const assignPattern = new RegExp(
            `(?:const|let|var)\\s+(?:\\{[^}]*${varName}[^}]*\\}|${varName})\\s*=`,
          );
          for (let i = 0; i < Math.min(call.line, lines.length); i++) {
            const line = lines[i] ?? '';
            if (assignPattern.test(line) && /req\.(query|body|params)|searchParams/.test(line)) {
              findings.push({
                title: 'Open redirect via user-controlled variable',
                severity: 'HIGH',
                source: 'custom',
                ruleId: 'frisk/open-redirect-variable',
                filePath: file.relativePath,
                line: call.line,
                codeSnippet: getSnippet(sourceFile, call.line, 3),
                description: `The variable "${varName}" is derived from user input and used as a redirect target. This enables phishing via open redirect.`,
                fix: 'Validate the redirect URL against an allowlist. Never pass user input directly to res.redirect().',
                docsUrl: 'https://cwe.mitre.org/data/definitions/601.html',
              });
              break;
            }
          }
        }
      }
    }
  }

  return findings;
}
