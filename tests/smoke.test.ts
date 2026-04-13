import { execSync } from 'node:child_process';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const CLI_PATH = resolve(import.meta.dirname, '..', 'dist', 'cli.js');

describe('frisk cli', () => {
  it('scans current directory and prints results', () => {
    const output = execSync(`node "${CLI_PATH}" .`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    expect(output).toContain('frisk');
    expect(output).toContain('v0.1.0');
    expect(output).toContain('Target:');
    expect(output).toContain('Security Score:');
  });

  it('shows version with --version flag', () => {
    const output = execSync(`node "${CLI_PATH}" --version`, { encoding: 'utf-8' });
    expect(output.trim()).toBe('0.1.0');
  });

  it('shows help with --help flag', () => {
    const output = execSync(`node "${CLI_PATH}" --help`, { encoding: 'utf-8' });
    expect(output).toContain('--output');
    expect(output).toContain('--format');
    expect(output).toContain('--fail-on');
  });
});
