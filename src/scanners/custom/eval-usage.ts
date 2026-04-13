/**
 * Rule: Direct eval() or Function() constructor usage
 *
 * eval() and new Function() execute arbitrary strings as code, enabling
 * remote code execution if the input comes from user data.
 *
 * Real-world example: Vibe-coded "calculator" features that eval() user input.
 * https://cwe.mitre.org/data/definitions/95.html
 */
import type { FileInfo, Finding } from '../../types.js';
import {
  findCalls,
  getLine,
  getSnippet,
  isParseable,
  parseFile,
  ts,
  walkAST,
} from '../../utils/ast.js';

/** Detects eval() and Function() constructor usage. */
export function evalUsageRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    // Find eval() calls
    const calls = findCalls(sourceFile);
    for (const call of calls) {
      if (call.name === 'eval') {
        findings.push({
          title: 'Direct eval() call detected',
          severity: 'HIGH',
          source: 'custom',
          ruleId: 'frisk/eval-usage',
          filePath: file.relativePath,
          line: call.line,
          codeSnippet: getSnippet(sourceFile, call.line),
          description:
            'eval() executes arbitrary strings as JavaScript code. If any part of the evaluated string comes from user input, this enables Remote Code Execution (RCE).',
          fix: 'Remove eval(). Use JSON.parse() for data, or a safe expression parser like math.js for calculations. Never execute user-supplied strings as code.',
          docsUrl: 'https://cwe.mitre.org/data/definitions/95.html',
        });
      }
    }

    // Find new Function() constructor
    walkAST(sourceFile, (node) => {
      if (
        ts.isNewExpression(node) &&
        ts.isIdentifier(node.expression) &&
        node.expression.text === 'Function'
      ) {
        const line = getLine(sourceFile, node);
        findings.push({
          title: 'Function() constructor detected',
          severity: 'HIGH',
          source: 'custom',
          ruleId: 'frisk/function-constructor',
          filePath: file.relativePath,
          line,
          codeSnippet: getSnippet(sourceFile, line),
          description:
            'The Function() constructor is equivalent to eval() — it compiles and executes arbitrary strings as code. This enables RCE if any argument comes from user input.',
          fix: 'Replace new Function() with a safe alternative. If you need dynamic behavior, use a lookup table or strategy pattern instead of runtime code generation.',
          docsUrl: 'https://cwe.mitre.org/data/definitions/95.html',
        });
      }
    });
  }

  return findings;
}
