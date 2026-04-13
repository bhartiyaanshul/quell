import { describe, expect, it } from 'vitest';
import { corsWildcardRule } from '../../src/scanners/custom/cors-wildcard.js';
import { mockFile } from './helpers.js';

describe('cors-wildcard rule', () => {
  it('detects CORS * with credentials via headers', () => {
    const file = mockFile(
      'src/server.js',
      `
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  next();
});`,
    );
    const findings = corsWildcardRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('HIGH');
  });

  it('ignores wildcard origin without credentials', () => {
    const file = mockFile('src/server.js', `res.setHeader('Access-Control-Allow-Origin', '*');`);
    const findings = corsWildcardRule([file]);
    expect(findings.length).toBe(0);
  });

  it('ignores specific origin with credentials', () => {
    const file = mockFile(
      'src/server.js',
      `
res.setHeader('Access-Control-Allow-Origin', 'https://myapp.com');
res.setHeader('Access-Control-Allow-Credentials', 'true');`,
    );
    const findings = corsWildcardRule([file]);
    expect(findings.length).toBe(0);
  });
});
