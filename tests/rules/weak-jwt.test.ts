import { describe, expect, it } from 'vitest';
import { weakJwtRule } from '../../src/scanners/custom/weak-jwt.js';
import { mockFile } from './helpers.js';

describe('weak-jwt rule', () => {
  it('detects short hardcoded JWT secret', () => {
    const file = mockFile(
      'src/auth.js',
      `const jwt = require('jsonwebtoken');\njwt.sign(payload, 'short');`,
    );
    const findings = weakJwtRule([file]);
    expect(findings.length).toBeGreaterThanOrEqual(1);
    expect(findings.some((f) => f.ruleId === 'frisk/weak-jwt-secret')).toBe(true);
  });

  it('detects hardcoded JWT secret via variable', () => {
    const file = mockFile(
      'src/auth.js',
      `const jwt = require('jsonwebtoken');\nconst SECRET = 'abc';\njwt.sign(payload, SECRET);`,
    );
    const findings = weakJwtRule([file]);
    expect(findings.length).toBeGreaterThanOrEqual(1);
  });

  it('ignores jwt.sign with env var', () => {
    const file = mockFile(
      'src/auth.js',
      `const jwt = require('jsonwebtoken');\njwt.sign(payload, process.env.JWT_SECRET);`,
    );
    const findings = weakJwtRule([file]);
    expect(findings.length).toBe(0);
  });
});
