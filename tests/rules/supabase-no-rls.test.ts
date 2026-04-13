import { describe, expect, it } from 'vitest';
import { supabaseNoRlsRule } from '../../src/scanners/custom/supabase-no-rls.js';
import { mockFile } from './helpers.js';

describe('supabase-no-rls rule', () => {
  it('detects tables without RLS when Supabase is used', () => {
    const envFile = mockFile('.env.local', 'NEXT_PUBLIC_SUPABASE_ANON_KEY=abc');
    const sqlFile = mockFile('sql/schema.sql', 'CREATE TABLE users (id UUID PRIMARY KEY);');
    const findings = supabaseNoRlsRule([envFile, sqlFile]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('CRITICAL');
  });

  it('ignores when RLS is enabled', () => {
    const envFile = mockFile('.env.local', 'NEXT_PUBLIC_SUPABASE_ANON_KEY=abc');
    const sqlFile = mockFile(
      'sql/schema.sql',
      'CREATE TABLE users (id UUID);\nALTER TABLE users ENABLE ROW LEVEL SECURITY;',
    );
    const findings = supabaseNoRlsRule([envFile, sqlFile]);
    expect(findings.length).toBe(0);
  });

  it('ignores when Supabase is not used', () => {
    const sqlFile = mockFile('sql/schema.sql', 'CREATE TABLE users (id UUID);');
    const findings = supabaseNoRlsRule([sqlFile]);
    expect(findings.length).toBe(0);
  });
});
