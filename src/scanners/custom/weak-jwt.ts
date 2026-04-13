/**
 * Rule: JWT secrets shorter than 32 characters or hardcoded
 *
 * A short or hardcoded JWT secret can be brute-forced or extracted from
 * source code, allowing an attacker to forge authentication tokens.
 *
 * Real-world example: Vibe-coded apps often use 'secret' or 'mysecret' as JWT keys.
 * https://cwe.mitre.org/data/definitions/326.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { findCalls, getSnippet, isParseable, parseFile, ts } from '../../utils/ast.js';

/** Detects weak or hardcoded JWT secrets. */
export function weakJwtRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const calls = findCalls(sourceFile);

    for (const call of calls) {
      // Look for jwt.sign() and jwt.verify() calls
      if (call.name !== 'sign' && call.name !== 'verify') continue;
      if (!call.fullExpression.includes('jwt')) continue;

      // The secret is typically the 2nd argument for sign, 2nd for verify
      const secretArg = call.arguments[1];
      if (!secretArg) continue;

      // Check for hardcoded string literal secrets
      if (ts.isStringLiteral(secretArg) || ts.isNoSubstitutionTemplateLiteral(secretArg)) {
        const secretValue = secretArg.text;

        if (secretValue.length < 32) {
          findings.push({
            title: `JWT secret is only ${secretValue.length} characters (minimum 32)`,
            severity: 'HIGH',
            source: 'custom',
            ruleId: 'frisk/weak-jwt-secret',
            filePath: file.relativePath,
            line: call.line,
            codeSnippet: getSnippet(sourceFile, call.line),
            description: `The JWT signing secret "${secretValue.length <= 8 ? secretValue : `${secretValue.slice(0, 4)}...`}" is ${secretValue.length} characters long. Secrets shorter than 32 characters can be brute-forced. This secret is also hardcoded in source code, making it visible to anyone with repo access.`,
            fix: 'Use a cryptographically random secret of at least 32 characters. Store it in an environment variable: `jwt.sign(payload, process.env.JWT_SECRET)`. Generate one with: `openssl rand -base64 32`.',
            docsUrl: 'https://cwe.mitre.org/data/definitions/326.html',
          });
        } else {
          findings.push({
            title: 'Hardcoded JWT secret in source code',
            severity: 'HIGH',
            source: 'custom',
            ruleId: 'frisk/hardcoded-jwt-secret',
            filePath: file.relativePath,
            line: call.line,
            codeSnippet: getSnippet(sourceFile, call.line),
            description:
              'The JWT signing secret is hardcoded in source code. Anyone with access to the repository can see it and forge authentication tokens.',
            fix: 'Move the JWT secret to an environment variable: `jwt.sign(payload, process.env.JWT_SECRET)`. Never commit secrets to source code.',
            docsUrl: 'https://cwe.mitre.org/data/definitions/798.html',
          });
        }
      }

      // Check for variable references to short constants
      if (ts.isIdentifier(secretArg)) {
        // Look for the variable declaration to check its value
        const varName = secretArg.text;
        const lines = file.content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i] ?? '';
          const constMatch = line.match(
            new RegExp(`(?:const|let|var)\\s+${varName}\\s*=\\s*['"\`]([^'"\`]*)['"\`]`),
          );
          if (constMatch?.[1] !== undefined && constMatch[1].length < 32) {
            findings.push({
              title: `JWT secret variable "${varName}" is only ${constMatch[1].length} characters`,
              severity: 'HIGH',
              source: 'custom',
              ruleId: 'frisk/weak-jwt-variable',
              filePath: file.relativePath,
              line: call.line,
              codeSnippet: getSnippet(sourceFile, call.line),
              description: `The variable "${varName}" used as a JWT secret contains a ${constMatch[1].length}-character value hardcoded in the source. This is both too short and exposed in code.`,
              fix: 'Use process.env.JWT_SECRET with a randomly generated value of at least 32 characters.',
              docsUrl: 'https://cwe.mitre.org/data/definitions/326.html',
            });
            break;
          }
        }
      }
    }
  }

  return findings;
}
