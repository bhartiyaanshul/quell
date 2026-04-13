/**
 * Custom rules engine — runs all hand-written security rules.
 *
 * This is the differentiator: these rules catch vibe-coded app patterns
 * that Semgrep and gitleaks miss.
 */
import type { FileInfo, Finding, GitInfo } from '../../types.js';
import { clearAstCache } from '../../utils/ast.js';
import { aiNoRatelimitRule } from './ai-no-ratelimit.js';
import { corsWildcardRule } from './cors-wildcard.js';
import { envInGitRule } from './env-in-git.js';
import { evalUsageRule } from './eval-usage.js';
import { insecureCookiesRule } from './insecure-cookies.js';
import { nosqlInjectionRule } from './nosql-injection.js';
import { openRedirectRule } from './open-redirect.js';
import { plaintextPasswordsRule } from './plaintext-passwords.js';
import { publicSecretEnvRule } from './public-secret-env.js';
import { supabaseNoRlsRule } from './supabase-no-rls.js';
import { unprotectedAdminRule } from './unprotected-admin.js';
import { unsafeHtmlRule } from './unsafe-html.js';
import { weakJwtRule } from './weak-jwt.js';

interface RuleDef {
  name: string;
  run: (files: FileInfo[], gitInfo: GitInfo) => Finding[];
}

/** All custom rules, registered in order. */
const RULES: RuleDef[] = [
  { name: 'env-in-git', run: envInGitRule },
  { name: 'public-secret-env', run: (files) => publicSecretEnvRule(files) },
  { name: 'supabase-no-rls', run: (files) => supabaseNoRlsRule(files) },
  { name: 'plaintext-passwords', run: (files) => plaintextPasswordsRule(files) },
  { name: 'ai-no-ratelimit', run: (files) => aiNoRatelimitRule(files) },
  { name: 'unprotected-admin', run: (files) => unprotectedAdminRule(files) },
  { name: 'cors-wildcard', run: (files) => corsWildcardRule(files) },
  { name: 'unsafe-html', run: (files) => unsafeHtmlRule(files) },
  { name: 'weak-jwt', run: (files) => weakJwtRule(files) },
  { name: 'eval-usage', run: (files) => evalUsageRule(files) },
  { name: 'insecure-cookies', run: (files) => insecureCookiesRule(files) },
  { name: 'open-redirect', run: (files) => openRedirectRule(files) },
  { name: 'nosql-injection', run: (files) => nosqlInjectionRule(files) },
];

/** Runs all custom rules and returns aggregated findings. */
export function runCustomRules(files: FileInfo[], gitInfo: GitInfo): Finding[] {
  const allFindings: Finding[] = [];

  // Clear AST cache from any previous runs
  clearAstCache();

  for (const rule of RULES) {
    try {
      const findings = rule.run(files, gitInfo);
      allFindings.push(...findings);
    } catch {
      // Individual rule failures shouldn't crash the scan
    }
  }

  // Clear cache after run to free memory
  clearAstCache();

  return allFindings;
}

/** Returns the count of registered custom rules. */
export function getCustomRuleCount(): number {
  return RULES.length;
}
