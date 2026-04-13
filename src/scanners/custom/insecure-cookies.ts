/**
 * Rule: Insecure cookie settings
 *
 * Cookies missing httpOnly, secure, or sameSite flags are vulnerable to:
 * - XSS theft (no httpOnly → JS can read the cookie)
 * - Network sniffing (no secure → sent over plain HTTP)
 * - CSRF (no sameSite → sent with cross-origin requests)
 *
 * https://cwe.mitre.org/data/definitions/614.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { findCalls, getSnippet, isParseable, parseFile, ts } from '../../utils/ast.js';

/** Detects cookies set without httpOnly, secure, or sameSite flags. */
export function insecureCookiesRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    if (!file.content.includes('cookie')) continue;

    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const calls = findCalls(sourceFile);

    for (const call of calls) {
      // res.cookie() pattern (Express)
      if (call.name !== 'cookie') continue;
      if (call.arguments.length < 2) continue;

      // Get the options argument (3rd arg in res.cookie(name, value, options))
      const optionsArg = call.arguments[2];
      if (!optionsArg) {
        findings.push({
          title: 'Cookie set without security options',
          severity: 'MEDIUM',
          source: 'custom',
          ruleId: 'frisk/insecure-cookie-no-options',
          filePath: file.relativePath,
          line: call.line,
          codeSnippet: getSnippet(sourceFile, call.line),
          description:
            'A cookie is being set without any security options. By default, cookies are not httpOnly (readable by XSS), not secure (sent over HTTP), and have no CSRF protection.',
          fix: 'Add security options: `res.cookie("name", value, { httpOnly: true, secure: true, sameSite: "strict" })`.',
          docsUrl: 'https://cwe.mitre.org/data/definitions/614.html',
        });
        continue;
      }

      const optionsText = optionsArg.getText(sourceFile);

      const issues: string[] = [];
      if (optionsText.includes('httpOnly: false')) {
        issues.push('httpOnly is false — cookie is readable by JavaScript (XSS risk)');
      } else if (!optionsText.includes('httpOnly')) {
        issues.push('httpOnly is not set — cookie defaults to being readable by JavaScript');
      }

      if (optionsText.includes('secure: false')) {
        issues.push('secure is false — cookie will be sent over plain HTTP');
      } else if (!optionsText.includes('secure')) {
        issues.push('secure is not set — cookie may be sent over plain HTTP');
      }

      if (!optionsText.includes('sameSite')) {
        issues.push('sameSite is not set — cookie has no CSRF protection');
      }

      if (issues.length > 0) {
        findings.push({
          title: `Insecure cookie: ${issues.length} issue${issues.length > 1 ? 's' : ''}`,
          severity: 'MEDIUM',
          source: 'custom',
          ruleId: 'frisk/insecure-cookie',
          filePath: file.relativePath,
          line: call.line,
          codeSnippet: getSnippet(sourceFile, call.line, 3),
          description: `${issues.join('. ')}.`,
          fix: 'Set all security flags: `{ httpOnly: true, secure: true, sameSite: "strict" }`. Use "lax" for sameSite if the cookie needs to work with external OAuth redirects.',
          docsUrl: 'https://cwe.mitre.org/data/definitions/614.html',
        });
      }
    }
  }

  return findings;
}
