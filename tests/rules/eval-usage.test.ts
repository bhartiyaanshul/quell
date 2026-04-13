import { describe, expect, it } from 'vitest';
import { evalUsageRule } from '../../src/scanners/custom/eval-usage.js';
import { mockFile } from './helpers.js';

describe('eval-usage rule', () => {
  it('detects eval() calls', () => {
    const file = mockFile('src/calc.js', 'const result = eval(userInput);');
    const findings = evalUsageRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.ruleId).toBe('frisk/eval-usage');
    expect(findings[0]?.severity).toBe('HIGH');
  });

  it('detects new Function() constructor', () => {
    const file = mockFile('src/transform.js', `const fn = new Function('data', code);`);
    const findings = evalUsageRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.ruleId).toBe('frisk/function-constructor');
  });

  it('ignores files without eval or Function', () => {
    const file = mockFile('src/safe.js', 'const x = JSON.parse(data);');
    const findings = evalUsageRule([file]);
    expect(findings.length).toBe(0);
  });

  it('ignores non-JS files', () => {
    const file = mockFile('README.md', 'You can use eval() for testing.');
    const findings = evalUsageRule([file]);
    expect(findings.length).toBe(0);
  });
});
