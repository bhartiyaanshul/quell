import { describe, expect, it } from 'vitest';
import { unprotectedAdminRule } from '../../src/scanners/custom/unprotected-admin.js';
import { mockFile } from './helpers.js';

describe('unprotected-admin rule', () => {
  it('detects admin route without auth', () => {
    const file = mockFile(
      'src/pages/api/admin/users.js',
      'export default function handler(req, res) { res.json([]); }',
    );
    const findings = unprotectedAdminRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('HIGH');
  });

  it('ignores admin route with auth import', () => {
    const file = mockFile(
      'src/pages/api/admin/users.js',
      `import { getServerSession } from 'next-auth';\nexport default function handler(req, res) { const session = getServerSession(); }`,
    );
    const findings = unprotectedAdminRule([file]);
    expect(findings.length).toBe(0);
  });

  it('ignores non-admin routes', () => {
    const file = mockFile(
      'src/pages/api/posts.js',
      'export default function handler(req, res) { res.json([]); }',
    );
    const findings = unprotectedAdminRule([file]);
    expect(findings.length).toBe(0);
  });
});
