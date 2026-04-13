/**
 * Rule: Supabase keys without Row Level Security
 *
 * If NEXT_PUBLIC_SUPABASE_ANON_KEY is found and no SQL files contain
 * "enable row level security", anyone with the anon key can read/write
 * all data in the database directly.
 *
 * Real-world example: Lovable showcase app exposed 18K+ users because
 * RLS was not enabled on any table.
 * https://cwe.mitre.org/data/definitions/284.html
 */
import type { FileInfo, Finding } from '../../types.js';

/** Detects Supabase usage without RLS enabled. */
export function supabaseNoRlsRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  // Check if the project uses Supabase
  const hasSupabaseKey = files.some(
    (f) =>
      f.content.includes('NEXT_PUBLIC_SUPABASE_ANON_KEY') ||
      f.content.includes('SUPABASE_ANON_KEY') ||
      f.content.includes('@supabase/supabase-js') ||
      (f.content.includes('createClient') && f.content.includes('supabase')),
  );

  if (!hasSupabaseKey) return findings;

  // Check SQL files for RLS
  const sqlFiles = files.filter(
    (f) => f.relativePath.endsWith('.sql') || f.relativePath.includes('migration'),
  );

  const hasRLS = sqlFiles.some(
    (f) =>
      f.content.toLowerCase().includes('enable row level security') ||
      f.content.toLowerCase().includes('row_level_security') ||
      f.content.toLowerCase().includes('create policy'),
  );

  if (!hasRLS && sqlFiles.length > 0) {
    // Find the specific SQL files with table definitions
    for (const sqlFile of sqlFiles) {
      if (
        sqlFile.content.toLowerCase().includes('create table') &&
        !sqlFile.content.toLowerCase().includes('enable row level security')
      ) {
        // Extract table names
        const tableMatches = sqlFile.content.matchAll(
          /create\s+table\s+(?:if\s+not\s+exists\s+)?(\w+)/gi,
        );
        const tables = [...tableMatches].map((m) => m[1]).filter(Boolean);

        findings.push({
          title: `Supabase tables without Row Level Security: ${tables.join(', ')}`,
          severity: 'CRITICAL',
          source: 'custom',
          ruleId: 'frisk/supabase-no-rls',
          filePath: sqlFile.relativePath,
          line: 1,
          codeSnippet: sqlFile.content.split('\n').slice(0, 10).join('\n'),
          description: `This project uses Supabase with a public anon key, but the SQL schema has no Row Level Security (RLS) policies. Without RLS, the anon key grants full read/write access to tables: ${tables.join(', ')}. Anyone can query your database directly from their browser.`,
          fix: 'Enable RLS on every table: `ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;`. Then add policies: `CREATE POLICY "users can read own data" ON table_name FOR SELECT USING (auth.uid() = user_id);`. See Supabase docs for policy examples.',
          docsUrl: 'https://supabase.com/docs/guides/auth/row-level-security',
        });
      }
    }

    // Also flag if there are no SQL files but Supabase is used
    if (sqlFiles.length === 0) {
      const supabaseFile = files.find(
        (f) =>
          f.content.includes('NEXT_PUBLIC_SUPABASE_ANON_KEY') ||
          f.content.includes('@supabase/supabase-js'),
      );
      if (supabaseFile) {
        findings.push({
          title: 'Supabase used without any SQL migration files',
          severity: 'HIGH',
          source: 'custom',
          ruleId: 'frisk/supabase-no-migrations',
          filePath: supabaseFile.relativePath,
          line: 1,
          codeSnippet: supabaseFile.content.split('\n').slice(0, 5).join('\n'),
          description:
            'This project uses Supabase but has no SQL migration files. This likely means tables were created via the Supabase dashboard without RLS policies. Verify that RLS is enabled on all tables in your Supabase dashboard.',
          fix: 'Go to your Supabase dashboard → Table Editor → select each table → Enable RLS. Also create migration files for reproducibility: `supabase db diff --schema public`.',
          docsUrl: 'https://supabase.com/docs/guides/auth/row-level-security',
        });
      }
    }
  }

  return findings;
}
