import { describe, expect, it } from 'vitest';
import { nosqlInjectionRule } from '../../src/scanners/custom/nosql-injection.js';
import { mockFile } from './helpers.js';

describe('nosql-injection rule', () => {
  it('detects direct req.body in findOne', () => {
    const file = mockFile(
      'src/api.js',
      `const user = await db.collection('users').findOne(req.body);`,
    );
    const findings = nosqlInjectionRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('HIGH');
  });

  it('detects JSON.parse of user input in find', () => {
    const file = mockFile(
      'src/api.js',
      `const results = await db.collection('items').find(JSON.parse(req.query.filter)).toArray();`,
    );
    const findings = nosqlInjectionRule([file]);
    expect(findings.length).toBe(1);
  });

  it('detects destructured user input in query', () => {
    const file = mockFile(
      'src/api.js',
      `const { username, password } = req.body;
const user = await db.collection('users').findOne({ username: username, password: password });`,
    );
    const findings = nosqlInjectionRule([file]);
    expect(findings.length).toBeGreaterThanOrEqual(1);
  });

  it('ignores queries without user input', () => {
    const file = mockFile(
      'src/api.js',
      `const user = await db.collection('users').findOne({ _id: internalId });`,
    );
    const findings = nosqlInjectionRule([file]);
    expect(findings.length).toBe(0);
  });
});
