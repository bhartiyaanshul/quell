import { describe, expect, it } from 'vitest';
import { plaintextPasswordsRule } from '../../src/scanners/custom/plaintext-passwords.js';
import { mockFile } from './helpers.js';

describe('plaintext-passwords rule', () => {
  it('detects password in insertOne without hashing', () => {
    const file = mockFile(
      'src/auth.js',
      `const { email, password } = req.body;
await db.collection('users').insertOne({ email, password });`,
    );
    const findings = plaintextPasswordsRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('CRITICAL');
  });

  it('detects MD5 hashed passwords', () => {
    const file = mockFile(
      'src/auth.js',
      `const crypto = require('crypto');
const hash = crypto.createHash('md5').update(password).digest('hex');
await db.collection('users').insertOne({ email, password: hash });`,
    );
    const findings = plaintextPasswordsRule([file]);
    expect(findings.some((f) => f.ruleId === 'frisk/weak-password-hash')).toBe(true);
  });

  it('ignores password with bcrypt hashing', () => {
    const file = mockFile(
      'src/auth.js',
      `const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
await db.collection('users').insertOne({ email, password: hash });`,
    );
    const findings = plaintextPasswordsRule([file]);
    expect(findings.length).toBe(0);
  });
});
