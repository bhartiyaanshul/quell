import type { FileInfo, GitInfo } from '../../src/types.js';

let mockFileCounter = 0;

/** Creates a mock FileInfo from inline content. */
export function mockFile(relativePath: string, content: string): FileInfo {
  return {
    absolutePath: `/test/${mockFileCounter++}/${relativePath}`,
    relativePath,
    content,
  };
}

/** Creates a mock GitInfo for a git repo. */
export function mockGitRepo(): GitInfo {
  return { isGitRepo: true, gitRoot: '/test' };
}

/** Creates a mock GitInfo for a non-git directory. */
export function mockNoGit(): GitInfo {
  return { isGitRepo: false };
}
