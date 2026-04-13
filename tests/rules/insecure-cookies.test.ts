import { describe, expect, it } from 'vitest';
import { insecureCookiesRule } from '../../src/scanners/custom/insecure-cookies.js';
import { mockFile } from './helpers.js';

describe('insecure-cookies rule', () => {
  it('detects cookie with httpOnly: false', () => {
    const file = mockFile(
      'src/server.js',
      `res.cookie('session', token, { httpOnly: false, secure: false });`,
    );
    const findings = insecureCookiesRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('MEDIUM');
  });

  it('detects cookie with no options', () => {
    const file = mockFile('src/server.js', `res.cookie('session', token);`);
    const findings = insecureCookiesRule([file]);
    expect(findings.length).toBe(1);
  });

  it('ignores secure cookie', () => {
    const file = mockFile(
      'src/server.js',
      `res.cookie('session', token, { httpOnly: true, secure: true, sameSite: 'strict' });`,
    );
    const findings = insecureCookiesRule([file]);
    expect(findings.length).toBe(0);
  });
});
