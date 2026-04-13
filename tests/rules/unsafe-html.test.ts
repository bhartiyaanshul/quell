import { describe, expect, it } from 'vitest';
import { unsafeHtmlRule } from '../../src/scanners/custom/unsafe-html.js';
import { mockFile } from './helpers.js';

describe('unsafe-html rule', () => {
  it('detects dangerouslySetInnerHTML with dynamic content', () => {
    const file = mockFile(
      'src/Comment.jsx',
      `export function Comment({ data }) {
  return <div dangerouslySetInnerHTML={{ __html: data.body }} />;
}`,
    );
    const findings = unsafeHtmlRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('MEDIUM');
  });

  it('ignores dangerouslySetInnerHTML with DOMPurify', () => {
    const file = mockFile(
      'src/Safe.jsx',
      `export function Safe({ data }) {
  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(data.body) }} />;
}`,
    );
    const findings = unsafeHtmlRule([file]);
    expect(findings.length).toBe(0);
  });

  it('ignores files without dangerouslySetInnerHTML', () => {
    const file = mockFile(
      'src/Normal.jsx',
      'export function Normal() { return <div>Hello</div>; }',
    );
    const findings = unsafeHtmlRule([file]);
    expect(findings.length).toBe(0);
  });
});
