import { execSync } from 'node:child_process';
import type { GitInfo } from '../types.js';

/** Checks if a directory is inside a git repository. */
export function getGitInfo(targetPath: string): GitInfo {
  try {
    const gitRoot = execSync('git rev-parse --show-toplevel', {
      cwd: targetPath,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();

    return { isGitRepo: true, gitRoot };
  } catch {
    return { isGitRepo: false };
  }
}

/** Searches git history for files matching a pattern (e.g., ".env"). */
export function findFilesInHistory(targetPath: string, pattern: string): string[] {
  try {
    const output = execSync(
      `git log --all --diff-filter=A --name-only --pretty=format: -- "${pattern}"`,
      {
        cwd: targetPath,
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 30_000,
      },
    );

    return output
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
  } catch {
    return [];
  }
}

/** Checks if a specific file has ever been committed to the repository. */
export function wasFileEverCommitted(targetPath: string, filePath: string): boolean {
  try {
    const output = execSync(`git log --all --oneline -- "${filePath}"`, {
      cwd: targetPath,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10_000,
    });

    return output.trim().length > 0;
  } catch {
    return false;
  }
}

/** Gets the content of a file at a specific commit. */
export function getFileAtCommit(
  targetPath: string,
  commitHash: string,
  filePath: string,
): string | undefined {
  try {
    return execSync(`git show ${commitHash}:${filePath}`, {
      cwd: targetPath,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10_000,
    });
  } catch {
    return undefined;
  }
}

/** Lists all commits where a file was added or modified. */
export function getFileCommits(targetPath: string, filePath: string): string[] {
  try {
    const output = execSync(`git log --all --pretty=format:%H -- "${filePath}"`, {
      cwd: targetPath,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10_000,
    });

    return output
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
  } catch {
    return [];
  }
}
