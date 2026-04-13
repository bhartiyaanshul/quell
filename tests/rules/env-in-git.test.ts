import { describe, expect, it } from 'vitest';
import { envInGitRule } from '../../src/scanners/custom/env-in-git.js';
import { mockFile, mockNoGit } from './helpers.js';

describe('env-in-git rule', () => {
  it('detects .env files in the project', () => {
    const file = mockFile('.env', 'API_KEY=secret123');
    const findings = envInGitRule([file], mockNoGit());
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('CRITICAL');
  });

  it('detects .env.local files', () => {
    const file = mockFile('.env.local', 'DB_PASSWORD=test');
    const findings = envInGitRule([file], mockNoGit());
    expect(findings.length).toBe(1);
  });

  it('detects .env.production files', () => {
    const file = mockFile('.env.production', 'SECRET=prod');
    const findings = envInGitRule([file], mockNoGit());
    expect(findings.length).toBe(1);
  });

  it('ignores non-env files', () => {
    const file = mockFile('src/config.ts', 'export const API_URL = "https://api.com";');
    const findings = envInGitRule([file], mockNoGit());
    expect(findings.length).toBe(0);
  });
});
