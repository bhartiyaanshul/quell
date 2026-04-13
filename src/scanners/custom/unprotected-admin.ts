/**
 * Rule: Admin routes without authentication
 *
 * Files in /admin/ or /api/admin/ paths that don't import any auth
 * middleware. Vibe-coded apps often skip auth on admin pages because
 * "no one will guess the URL."
 *
 * https://cwe.mitre.org/data/definitions/306.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { findImports, getSnippet, isParseable, parseFile } from '../../utils/ast.js';

const AUTH_PATTERNS = [
  'auth',
  'authenticate',
  'requireAuth',
  'isAuthenticated',
  'isAdmin',
  'withAuth',
  'checkAuth',
  'verifyToken',
  'jwt',
  'jsonwebtoken',
  'passport',
  'next-auth',
  'clerk',
  '@clerk',
  'supabase',
  'firebase-admin',
  'getSession',
  'getServerSession',
  'getToken',
  'middleware',
  'protect',
  'guard',
];

/** Checks if a file path is an admin route. */
function isAdminRoute(path: string): boolean {
  const normalized = path.replace(/\\/g, '/').toLowerCase();
  return (
    normalized.includes('/admin/') ||
    normalized.includes('/api/admin') ||
    (normalized.includes('/dashboard/') && normalized.includes('api'))
  );
}

/** Detects admin routes without authentication checks. */
export function unprotectedAdminRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    if (!isAdminRoute(file.relativePath)) continue;

    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    // Check imports for auth-related modules
    const imports = findImports(sourceFile);
    const hasAuthImport = imports.some((imp) =>
      AUTH_PATTERNS.some(
        (pattern) =>
          imp.moduleSpecifier.toLowerCase().includes(pattern) ||
          (imp.defaultImport?.toLowerCase().includes(pattern) ?? false) ||
          imp.namedImports.some((n) => n.toLowerCase().includes(pattern)),
      ),
    );

    // Check content for auth-related function calls
    const content = file.content.toLowerCase();
    const hasAuthCheck = AUTH_PATTERNS.some(
      (pattern) =>
        content.includes(`${pattern}(`) ||
        content.includes(`${pattern} (`) ||
        content.includes(`.${pattern}`),
    );

    if (!hasAuthImport && !hasAuthCheck) {
      findings.push({
        title: `Unprotected admin route: ${file.relativePath}`,
        severity: 'HIGH',
        source: 'custom',
        ruleId: 'frisk/unprotected-admin',
        filePath: file.relativePath,
        line: 1,
        codeSnippet: getSnippet(sourceFile, 1, 5),
        description:
          'This admin route does not appear to import or check any authentication/authorization. Anyone who discovers the URL can access admin functionality including viewing user data and performing destructive actions.',
        fix: 'Add authentication middleware to all admin routes. For Next.js, use getServerSession() or Clerk/NextAuth middleware. For Express, add an isAdmin middleware before the route handler.',
        docsUrl: 'https://cwe.mitre.org/data/definitions/306.html',
      });
    }
  }

  return findings;
}
