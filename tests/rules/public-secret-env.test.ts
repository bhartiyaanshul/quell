import { describe, expect, it } from 'vitest';
import { publicSecretEnvRule } from '../../src/scanners/custom/public-secret-env.js';
import { mockFile } from './helpers.js';

describe('public-secret-env rule', () => {
  it('detects NEXT_PUBLIC_OPENAI_API_KEY', () => {
    const file = mockFile('.env.local', 'NEXT_PUBLIC_OPENAI_API_KEY=sk-proj-abc123');
    const findings = publicSecretEnvRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('CRITICAL');
  });

  it('detects NEXT_PUBLIC_STRIPE_SECRET_KEY', () => {
    const file = mockFile('.env', 'NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_abc');
    const findings = publicSecretEnvRule([file]);
    expect(findings.length).toBe(1);
  });

  it('detects secrets in next.config.js', () => {
    const file = mockFile(
      'next.config.js',
      'module.exports = { env: { NEXT_PUBLIC_OPENAI_API_KEY: process.env.KEY } };',
    );
    const findings = publicSecretEnvRule([file]);
    expect(findings.length).toBe(1);
  });

  it('ignores safe NEXT_PUBLIC_ variables', () => {
    const file = mockFile('.env', 'NEXT_PUBLIC_APP_URL=https://myapp.com');
    const findings = publicSecretEnvRule([file]);
    expect(findings.length).toBe(0);
  });

  it('ignores server-only env vars', () => {
    const file = mockFile('.env', 'OPENAI_API_KEY=sk-proj-abc123');
    const findings = publicSecretEnvRule([file]);
    expect(findings.length).toBe(0);
  });
});
