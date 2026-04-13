/**
 * Rule: .env files committed to git
 *
 * Detects .env, .env.local, .env.production, etc. committed to git history.
 * This is one of the most common vibe-coding mistakes — secrets shipped to prod.
 *
 * Real-world example: A Lovable app leaked 1.5M API keys because .env was committed.
 * https://www.theregister.com/2025/04/08/ai_vibe_coding_security/
 */
import type { FileInfo, Finding, GitInfo } from '../../types.js';
import { findFilesInHistory } from '../../utils/git.js';

const ENV_PATTERNS = ['.env', '.env.local', '.env.production', '.env.staging', '.env.development'];

/** Detects .env files committed to git history or present in the working tree. */
export function envInGitRule(files: FileInfo[], gitInfo: GitInfo): Finding[] {
  const findings: Finding[] = [];

  // Check working tree for .env files
  for (const file of files) {
    const fileName = file.relativePath.split('/').pop() ?? '';
    if (ENV_PATTERNS.some((p) => fileName === p || fileName.startsWith('.env.'))) {
      findings.push({
        title: `.env file in project: ${file.relativePath}`,
        severity: 'CRITICAL',
        source: 'custom',
        ruleId: 'frisk/env-in-git',
        filePath: file.relativePath,
        line: 1,
        codeSnippet: file.content.split('\n').slice(0, 5).join('\n'),
        description:
          'An .env file containing secrets was found in the project directory. If this is committed to git, anyone with repo access can read your API keys, database passwords, and other credentials.',
        fix: 'Add .env* to your .gitignore file. Remove the .env file from git history using `git rm --cached .env`. Rotate all secrets that were exposed.',
        docsUrl: 'https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/',
      });
    }
  }

  // Check git history if available
  if (gitInfo.isGitRepo && gitInfo.gitRoot) {
    for (const pattern of ENV_PATTERNS) {
      const historicalFiles = findFilesInHistory(gitInfo.gitRoot, `*${pattern}*`);
      for (const histFile of historicalFiles) {
        const alreadyFound = findings.some((f) => f.filePath === histFile);
        if (!alreadyFound) {
          findings.push({
            title: `.env file found in git history: ${histFile}`,
            severity: 'CRITICAL',
            source: 'custom',
            ruleId: 'frisk/env-in-git-history',
            filePath: histFile,
            line: 1,
            codeSnippet:
              '[found in git history — file may have been deleted but secrets are still recoverable]',
            description:
              'An .env file was previously committed to this repository. Even though it may have been deleted, the secrets are still recoverable from git history by anyone who clones the repo.',
            fix: 'Rotate ALL secrets that were in this file. Use `git filter-branch` or BFG Repo-Cleaner to purge the file from history. Add .env* to .gitignore.',
            docsUrl:
              'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository',
          });
        }
      }
    }
  }

  return findings;
}
