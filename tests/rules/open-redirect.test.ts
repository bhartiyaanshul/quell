import { describe, expect, it } from 'vitest';
import { openRedirectRule } from '../../src/scanners/custom/open-redirect.js';
import { mockFile } from './helpers.js';

describe('open-redirect rule', () => {
  it('detects redirect with req.query input', () => {
    const file = mockFile(
      'src/server.js',
      `app.get('/go', (req, res) => { res.redirect(req.query.url); });`,
    );
    const findings = openRedirectRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('HIGH');
  });

  it('detects redirect via destructured variable', () => {
    const file = mockFile(
      'src/server.js',
      `app.get('/go', (req, res) => {
  const { url } = req.query;
  res.redirect(url);
});`,
    );
    const findings = openRedirectRule([file]);
    expect(findings.length).toBe(1);
  });

  it('ignores redirect with static URL', () => {
    const file = mockFile(
      'src/server.js',
      `app.get('/home', (req, res) => { res.redirect('/dashboard'); });`,
    );
    const findings = openRedirectRule([file]);
    expect(findings.length).toBe(0);
  });
});
