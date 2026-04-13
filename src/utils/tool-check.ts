import { execSync } from 'node:child_process';
import pc from 'picocolors';

interface ToolStatus {
  installed: boolean;
  version?: string;
}

/** Checks whether a CLI tool is available on the system PATH. */
function checkTool(command: string, versionFlag = '--version'): ToolStatus {
  try {
    const output = execSync(`${command} ${versionFlag}`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10_000,
    }).trim();

    const versionMatch = output.match(/(\d+\.\d+[\w.-]*)/);
    return { installed: true, version: versionMatch?.[1] ?? 'unknown' };
  } catch {
    return { installed: false };
  }
}

/** Returns platform-specific install instructions for semgrep. */
function semgrepInstallHint(): string {
  const platform = process.platform;
  const lines = [pc.bold('Install semgrep:')];

  if (platform === 'darwin') {
    lines.push(`  ${pc.cyan('brew install semgrep')}`);
  } else if (platform === 'linux') {
    lines.push(`  ${pc.cyan('pip install semgrep')}`);
    lines.push(`  ${pc.dim('or')} ${pc.cyan('brew install semgrep')}`);
  } else if (platform === 'win32') {
    lines.push(`  ${pc.cyan('pip install semgrep')}`);
    lines.push(`  ${pc.dim('(requires Python 3.8+)')}`);
  }

  lines.push(`  ${pc.dim('https://semgrep.dev/docs/getting-started/')}`);
  return lines.join('\n');
}

/** Returns platform-specific install instructions for gitleaks. */
function gitleaksInstallHint(): string {
  const platform = process.platform;
  const lines = [pc.bold('Install gitleaks:')];

  if (platform === 'darwin') {
    lines.push(`  ${pc.cyan('brew install gitleaks')}`);
  } else if (platform === 'linux') {
    lines.push(`  ${pc.cyan('brew install gitleaks')}`);
    lines.push(
      `  ${pc.dim('or download from')} ${pc.cyan('https://github.com/gitleaks/gitleaks/releases')}`,
    );
  } else if (platform === 'win32') {
    lines.push(`  ${pc.cyan('choco install gitleaks')}`);
    lines.push(`  ${pc.dim('or')} ${pc.cyan('scoop install gitleaks')}`);
    lines.push(
      `  ${pc.dim('or download from')} ${pc.cyan('https://github.com/gitleaks/gitleaks/releases')}`,
    );
  }

  lines.push(`  ${pc.dim('https://github.com/gitleaks/gitleaks#installing')}`);
  return lines.join('\n');
}

export interface ToolCheckResult {
  semgrep: ToolStatus;
  gitleaks: ToolStatus;
}

/** Detects whether semgrep and gitleaks are installed and prints status. */
export function checkExternalTools(silent = false): ToolCheckResult {
  const semgrep = checkTool('semgrep');
  const gitleaks = checkTool('gitleaks');

  if (!silent) {
    if (semgrep.installed) {
      console.log(`  ${pc.green('✓')} semgrep ${pc.dim(`v${semgrep.version}`)}`);
    } else {
      console.log(`  ${pc.yellow('○')} semgrep ${pc.dim('not found — skipping static analysis')}`);
      console.log('');
      console.log(semgrepInstallHint());
      console.log('');
    }

    if (gitleaks.installed) {
      console.log(`  ${pc.green('✓')} gitleaks ${pc.dim(`v${gitleaks.version}`)}`);
    } else {
      console.log(`  ${pc.yellow('○')} gitleaks ${pc.dim('not found — skipping secret scanning')}`);
      console.log('');
      console.log(gitleaksInstallHint());
      console.log('');
    }
  }

  return { semgrep, gitleaks };
}
