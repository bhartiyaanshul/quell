import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { ScanResult } from '../types.js';
import { buildHtmlReport } from './template-layout.js';

/** Generates the HTML report and writes it to disk. Returns the absolute path. */
export function writeHtmlReport(result: ScanResult, outputPath: string): string {
  const html = buildHtmlReport(result);
  const absPath = resolve(outputPath);
  writeFileSync(absPath, html, 'utf-8');
  return absPath;
}
