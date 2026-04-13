/**
 * Rule: Plain-text password storage
 *
 * Detects password fields being stored in a database without hashing.
 * Looks for insert/save/create patterns near password assignments that
 * don't involve bcrypt, argon2, scrypt, or other hashing functions.
 *
 * Real-world example: The Lovable showcase app stored passwords in plaintext,
 * exposing 18K+ user credentials.
 * https://cwe.mitre.org/data/definitions/256.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { findCalls, getSnippet, isParseable, parseFile } from '../../utils/ast.js';

/** Known password hashing functions/libraries. */
const HASH_FUNCTIONS = new Set([
  'bcrypt',
  'argon2',
  'scrypt',
  'hash',
  'hashPassword',
  'hashSync',
  'genSalt',
  'genSaltSync',
  'pbkdf2',
  'createHash',
]);

/** Detects plain-text password storage patterns. */
export function plaintextPasswordsRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const content = file.content;

    // Check if file has any hashing imports/calls
    const hasHashingContext = HASH_FUNCTIONS.values().some((fn) => content.includes(fn));

    const calls = findCalls(sourceFile);

    for (const call of calls) {
      // Look for database save/insert/create patterns
      const isDbWrite =
        call.name === 'insertOne' ||
        call.name === 'insertMany' ||
        call.name === 'create' ||
        call.name === 'save' ||
        call.name === 'insert' ||
        call.name === 'query' ||
        call.name === 'execute';

      if (!isDbWrite) continue;

      // Check if any argument contains "password" and there's no hashing nearby
      const argText = call.arguments.map((a) => a.getText(sourceFile)).join(' ');
      if (!argText.toLowerCase().includes('password')) continue;

      // Check surrounding context (10 lines above and below) for hashing
      const lines = content.split('\n');
      const startLine = Math.max(0, call.line - 11);
      const endLine = Math.min(lines.length, call.line + 10);
      const context = lines.slice(startLine, endLine).join('\n');

      const hasHashing = HASH_FUNCTIONS.values().some((fn) => context.includes(fn));

      // Also check for MD5/SHA1 which are NOT safe for passwords
      const hasWeakHash =
        context.includes('createHash') &&
        (context.includes("'md5'") ||
          context.includes('"md5"') ||
          context.includes("'sha1'") ||
          context.includes('"sha1"'));

      if (!hasHashing || hasWeakHash) {
        if (hasWeakHash) {
          findings.push({
            title: 'Password hashed with weak algorithm (MD5/SHA1)',
            severity: 'CRITICAL',
            source: 'custom',
            ruleId: 'frisk/weak-password-hash',
            filePath: file.relativePath,
            line: call.line,
            codeSnippet: getSnippet(sourceFile, call.line, 3),
            description:
              'Passwords are being hashed with MD5 or SHA1, which are cryptographically broken. These can be cracked in seconds using rainbow tables or GPU-accelerated attacks.',
            fix: 'Use bcrypt, argon2, or scrypt for password hashing: `const hash = await bcrypt.hash(password, 12)`. These are specifically designed for password storage with built-in salting.',
            docsUrl:
              'https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html',
          });
        } else if (!hasHashingContext) {
          findings.push({
            title: 'Password stored without hashing',
            severity: 'CRITICAL',
            source: 'custom',
            ruleId: 'frisk/plaintext-password',
            filePath: file.relativePath,
            line: call.line,
            codeSnippet: getSnippet(sourceFile, call.line, 3),
            description:
              'A password field is being saved to the database without any hashing. If the database is breached, all user passwords will be immediately visible in plain text.',
            fix: 'Hash passwords before storing them: `const hash = await bcrypt.hash(password, 12)`. Install bcrypt: `npm install bcrypt`. Never store plain-text passwords.',
            docsUrl:
              'https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html',
          });
        }
      }
    }
  }

  return findings;
}
