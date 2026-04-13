import { existsSync, statSync } from 'node:fs';
import { resolve } from 'node:path';
import Table from 'cli-table3';
import { Command } from 'commander';
import ora from 'ora';
import pc from 'picocolors';
import { writeHtmlReport } from './report/html.js';
import { writeJsonReport } from './report/json.js';
import { runAllScanners } from './scanners/index.js';
import { countBySeverity } from './score.js';
import type { OutputFormat, Severity } from './types.js';
import { SEVERITY_ORDER } from './types.js';
import { getGitInfo } from './utils/git.js';
import { checkExternalTools } from './utils/tool-check.js';
import { walkDirectory } from './utils/walk.js';

const VERSION = '0.1.0';

const VALID_FORMATS = new Set<string>(['html', 'json']);
const VALID_SEVERITIES = new Set<string>(['critical', 'high', 'medium', 'low']);

const SEVERITY_COLORS: Record<Severity, (s: string) => string> = {
  CRITICAL: (s) => pc.bgRed(pc.white(pc.bold(` ${s} `))),
  HIGH: (s) => pc.red(s),
  MEDIUM: (s) => pc.yellow(s),
  LOW: (s) => pc.blue(s),
  INFO: (s) => pc.dim(s),
};

function printBanner(): void {
  console.log('');
  console.log(pc.bold(pc.cyan('  ⟁ frisk')) + pc.dim(` v${VERSION}`));
  console.log(pc.dim('  Frisk your vibe-coded app'));
  console.log(pc.dim('  before someone else does.'));
  console.log('');
}

function colorSeverity(severity: Severity): string {
  return SEVERITY_COLORS[severity](severity);
}

function scoreColor(score: number): (s: string) => string {
  if (score > 80) return pc.green;
  if (score > 50) return pc.yellow;
  return pc.red;
}

const program = new Command();

program
  .name('friskit')
  .description('Frisk your vibe-coded app before someone else does.')
  .version(VERSION)
  .argument('[target]', 'path to the project to scan', '.')
  .option('-o, --output <path>', 'write report to a custom file path')
  .option('-f, --format <format>', 'output format: html or json', 'html')
  .option(
    '--fail-on <severity>',
    'exit 1 if findings at or above this severity (critical, high, medium, low)',
  )
  .action((target: string, options: { output?: string; format: string; failOn?: string }) => {
    printBanner();

    // Validate format
    if (!VALID_FORMATS.has(options.format)) {
      console.error(pc.red(`  Error: invalid format "${options.format}". Use "html" or "json".`));
      process.exit(1);
    }

    // Validate fail-on
    if (options.failOn && !VALID_SEVERITIES.has(options.failOn.toLowerCase())) {
      console.error(
        pc.red(
          `  Error: invalid severity "${options.failOn}". Use "critical", "high", "medium", or "low".`,
        ),
      );
      process.exit(1);
    }

    // Resolve and validate target path
    const targetPath = resolve(target);

    if (!existsSync(targetPath)) {
      console.error(pc.red(`  Error: path does not exist: ${targetPath}`));
      process.exit(1);
    }

    const targetStat = statSync(targetPath);
    if (!targetStat.isDirectory()) {
      console.error(pc.red(`  Error: path is not a directory: ${targetPath}`));
      process.exit(1);
    }

    console.log(`  ${pc.bold('Target:')} ${pc.white(targetPath)}`);
    console.log('');

    // Check git status
    const gitInfo = getGitInfo(targetPath);
    if (gitInfo.isGitRepo) {
      console.log(`  ${pc.green('✓')} git repository detected`);
    } else {
      console.log(
        `  ${pc.yellow('○')} not a git repository ${pc.dim('— git history scans will be skipped')}`,
      );
    }

    // Check external tools
    const tools = checkExternalTools();
    console.log('');

    // Walk directory
    const walkSpinner = ora({ text: 'Scanning files...', indent: 2 }).start();
    const files = walkDirectory(targetPath);
    walkSpinner.succeed(`Found ${pc.bold(pc.white(String(files.length)))} scannable files`);
    console.log('');

    // Run scanners
    const result = runAllScanners(
      {
        targetPath,
        files,
        gitInfo,
        semgrepAvailable: tools.semgrep.installed,
        gitleaksAvailable: tools.gitleaks.installed,
      },
      {
        onScannerStart: (name) => {
          ora({ text: `Running ${name}...`, indent: 2 }).start();
        },
        onScannerDone: (name, count) => {
          const spinner = ora({ indent: 2 });
          if (count > 0) {
            spinner.warn(`${name}: ${pc.bold(String(count))} finding${count > 1 ? 's' : ''}`);
          } else {
            spinner.succeed(`${name}: ${pc.dim('clean')}`);
          }
        },
      },
    );

    console.log('');

    // Print score
    const colorFn = scoreColor(result.score);
    console.log(
      `  ${pc.bold('Security Score:')} ${colorFn(pc.bold(String(result.score)))}${pc.dim('/100')}`,
    );
    console.log('');

    // Print severity summary
    const counts = countBySeverity(result.findings);
    const summaryParts: string[] = [];
    for (const sev of SEVERITY_ORDER) {
      if (counts[sev] > 0) {
        summaryParts.push(`${colorSeverity(sev)} ${counts[sev]}`);
      }
    }
    if (summaryParts.length > 0) {
      console.log(`  ${summaryParts.join(pc.dim('  ·  '))}`);
    } else {
      console.log(`  ${pc.green('No issues found!')}`);
    }
    console.log('');

    // Print findings table
    if (result.findings.length > 0) {
      const table = new Table({
        head: [pc.dim('Sev'), pc.dim('Finding'), pc.dim('Location')],
        colWidths: [12, 50, 40],
        wordWrap: true,
        style: { head: [], border: ['dim'] },
      });

      for (const finding of result.findings.slice(0, 30)) {
        const location = `${finding.filePath}:${finding.line}`;
        table.push([
          colorSeverity(finding.severity),
          `${finding.title}\n${pc.dim(finding.description.slice(0, 100))}`,
          pc.dim(location.length > 38 ? `...${location.slice(-35)}` : location),
        ]);
      }

      console.log(table.toString());

      if (result.findings.length > 30) {
        console.log(
          pc.dim(`\n  ... and ${result.findings.length - 30} more findings. See the full report.`),
        );
      }
      console.log('');
    }

    // Print scan duration
    const duration =
      result.durationMs < 1000
        ? `${result.durationMs}ms`
        : `${(result.durationMs / 1000).toFixed(1)}s`;
    console.log(pc.dim(`  Scanned ${result.filesScanned} files in ${duration}`));
    console.log('');

    // Write report
    const format = options.format as OutputFormat;
    const failOn = options.failOn?.toUpperCase() as Severity | undefined;
    const outputPath = options.output ?? `friskit-report.${format}`;

    if (format === 'html') {
      const reportPath = writeHtmlReport(result, outputPath);
      console.log(`  ${pc.green('✓')} Report written to ${pc.bold(pc.white(reportPath))}`);
    } else {
      const reportPath = writeJsonReport(result, outputPath);
      console.log(`  ${pc.green('✓')} JSON report written to ${pc.bold(pc.white(reportPath))}`);
    }
    console.log('');

    // Exit code based on --fail-on
    if (failOn) {
      const failIndex = SEVERITY_ORDER.indexOf(failOn);
      const hasFailure = result.findings.some(
        (f) => SEVERITY_ORDER.indexOf(f.severity) <= failIndex,
      );
      if (hasFailure) {
        console.log(pc.red(`  ✗ Findings at ${failOn} or above detected. Exiting with code 1.`));
        process.exit(1);
      }
    }
  });

program.parse();
