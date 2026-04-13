import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import type { FileInfo } from '../types.js';

/** Default directories to always skip. */
const ALWAYS_SKIP_DIRS = new Set([
  'node_modules',
  '.git',
  'dist',
  'build',
  '.next',
  '.nuxt',
  '.svelte-kit',
  '.output',
  'coverage',
  '__pycache__',
  '.turbo',
  '.vercel',
  '.cache',
  'vendor',
]);

/** File extensions to skip (binary / irrelevant). */
const SKIP_EXTENSIONS = new Set([
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.ico',
  '.svg',
  '.webp',
  '.mp4',
  '.mp3',
  '.woff',
  '.woff2',
  '.ttf',
  '.eot',
  '.zip',
  '.tar',
  '.gz',
  '.pdf',
  '.exe',
  '.dll',
  '.so',
  '.dylib',
  '.lock',
  '.map',
]);

/** Max file size to read (1 MB). */
const MAX_FILE_SIZE = 1_048_576;

/** Parses a .gitignore file into an array of patterns. */
function parseGitignore(rootDir: string): string[] {
  try {
    const content = readFileSync(join(rootDir, '.gitignore'), 'utf-8');
    return content
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0 && !line.startsWith('#'));
  } catch {
    return [];
  }
}

/** Checks if a file/directory name matches a gitignore pattern (simplified). */
function matchesPattern(name: string, relativePath: string, pattern: string): boolean {
  const cleanPattern = pattern.replace(/\/$/, '');

  if (cleanPattern.includes('/')) {
    const patternPath = cleanPattern.startsWith('/') ? cleanPattern.slice(1) : cleanPattern;
    return relativePath.startsWith(patternPath) || relativePath.includes(`/${patternPath}`);
  }

  if (cleanPattern.startsWith('*.')) {
    const ext = cleanPattern.slice(1);
    return name.endsWith(ext);
  }

  if (cleanPattern.startsWith('**/')) {
    const rest = cleanPattern.slice(3);
    return name === rest || relativePath.includes(rest);
  }

  return name === cleanPattern;
}

/** Checks if a path should be ignored based on gitignore patterns. */
function isIgnored(name: string, relativePath: string, patterns: string[]): boolean {
  for (const pattern of patterns) {
    if (pattern.startsWith('!')) {
      if (matchesPattern(name, relativePath, pattern.slice(1))) {
        return false;
      }
    } else if (matchesPattern(name, relativePath, pattern)) {
      return true;
    }
  }
  return false;
}

/** Recursively walks a directory and returns scannable files. */
export function walkDirectory(rootDir: string): FileInfo[] {
  const gitignorePatterns = parseGitignore(rootDir);
  const files: FileInfo[] = [];

  function walk(dir: string): void {
    let entries: string[];
    try {
      entries = readdirSync(dir);
    } catch {
      return;
    }

    for (const entry of entries) {
      const fullPath = join(dir, entry);
      const relPath = relative(rootDir, fullPath).replace(/\\/g, '/');

      if (isIgnored(entry, relPath, gitignorePatterns)) {
        continue;
      }

      let stat: ReturnType<typeof statSync>;
      try {
        stat = statSync(fullPath);
      } catch {
        continue;
      }

      if (stat.isDirectory()) {
        if (ALWAYS_SKIP_DIRS.has(entry) || entry.startsWith('.')) {
          continue;
        }
        walk(fullPath);
      } else if (stat.isFile()) {
        const ext = entry.slice(entry.lastIndexOf('.'));
        if (SKIP_EXTENSIONS.has(ext)) {
          continue;
        }
        if (stat.size > MAX_FILE_SIZE) {
          continue;
        }

        try {
          const content = readFileSync(fullPath, 'utf-8');
          files.push({
            absolutePath: fullPath,
            relativePath: relPath,
            content,
          });
        } catch {
          // Skip files that can't be read (binary, permission issues)
        }
      }
    }
  }

  walk(rootDir);
  return files;
}
