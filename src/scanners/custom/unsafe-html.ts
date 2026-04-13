/**
 * Rule: dangerouslySetInnerHTML with unsanitized input
 *
 * React's dangerouslySetInnerHTML bypasses XSS protection. If the input
 * comes from user data (props, API responses, URL params), it enables
 * stored or reflected XSS attacks.
 *
 * https://cwe.mitre.org/data/definitions/79.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { getLine, getSnippet, isParseable, parseFile, ts, walkAST } from '../../utils/ast.js';

/** Known sanitizer function names. */
const SANITIZERS = new Set([
  'sanitize',
  'sanitizeHtml',
  'DOMPurify',
  'purify',
  'xss',
  'escape',
  'escapeHtml',
  'marked',
]);

/** Checks if an expression involves a known sanitizer. */
function isSanitized(node: ts.Node, sourceFile: ts.SourceFile): boolean {
  const text = node.getText(sourceFile);
  for (const sanitizer of SANITIZERS) {
    if (text.includes(sanitizer)) return true;
  }
  return false;
}

/** Detects dangerouslySetInnerHTML usage with potentially unsanitized input. */
export function unsafeHtmlRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    if (!file.content.includes('dangerouslySetInnerHTML')) continue;

    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    walkAST(sourceFile, (node) => {
      if (!ts.isJsxAttribute(node)) return;
      if (node.name.getText(sourceFile) !== 'dangerouslySetInnerHTML') return;

      const line = getLine(sourceFile, node);

      // Check if the value is sanitized
      const initializer = node.initializer;
      if (initializer && isSanitized(initializer, sourceFile)) return;

      // Check the __html property value
      let htmlValue = '';
      if (initializer && ts.isJsxExpression(initializer) && initializer.expression) {
        htmlValue = initializer.expression.getText(sourceFile);
      }

      // Skip static strings (they're safe)
      if (htmlValue.startsWith("'") || htmlValue.startsWith('"') || htmlValue.startsWith('`')) {
        const hasInterpolation = htmlValue.includes('${');
        if (!hasInterpolation) return;
      }

      findings.push({
        title: 'dangerouslySetInnerHTML with unsanitized input',
        severity: 'MEDIUM',
        source: 'custom',
        ruleId: 'frisk/unsafe-html',
        filePath: file.relativePath,
        line,
        codeSnippet: getSnippet(sourceFile, line),
        description:
          'dangerouslySetInnerHTML renders raw HTML without escaping. If the content comes from user input, API responses, or URL parameters, an attacker can inject malicious scripts (XSS).',
        fix: 'Sanitize the HTML before rendering using DOMPurify: `dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}`. Better yet, avoid dangerouslySetInnerHTML entirely and use a markdown renderer.',
        docsUrl: 'https://cwe.mitre.org/data/definitions/79.html',
      });
    });
  }

  return findings;
}
