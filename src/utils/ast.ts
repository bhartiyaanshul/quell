/**
 * Shared TypeScript AST parsing utilities for custom rules.
 *
 * Uses the TypeScript compiler API to parse JS/TS/JSX/TSX files and provides
 * helpers for common analysis patterns: finding imports, function calls,
 * string literals, property assignments, and general tree walking.
 */
import ts from 'typescript';
import type { FileInfo } from '../types.js';

/** Cached parsed source files to avoid re-parsing across rules. */
const sourceFileCache = new Map<string, ts.SourceFile>();

/** File extensions that can be parsed as TypeScript/JavaScript. */
const PARSEABLE_EXTENSIONS = new Set([
  '.ts',
  '.tsx',
  '.js',
  '.jsx',
  '.mjs',
  '.cjs',
  '.mts',
  '.cts',
]);

/** Checks if a file can be parsed by the TypeScript compiler. */
export function isParseable(filePath: string): boolean {
  const ext = filePath.slice(filePath.lastIndexOf('.'));
  return PARSEABLE_EXTENSIONS.has(ext);
}

/** Determines the script kind from a file extension. */
function getScriptKind(filePath: string): ts.ScriptKind {
  const ext = filePath.slice(filePath.lastIndexOf('.'));
  switch (ext) {
    case '.tsx':
      return ts.ScriptKind.TSX;
    case '.jsx':
      return ts.ScriptKind.JSX;
    case '.ts':
    case '.mts':
    case '.cts':
      return ts.ScriptKind.TS;
    default:
      return ts.ScriptKind.JS;
  }
}

/** Parses a file into a TypeScript AST SourceFile, with caching. */
export function parseFile(file: FileInfo): ts.SourceFile | undefined {
  if (!isParseable(file.relativePath)) return undefined;

  const cached = sourceFileCache.get(file.absolutePath);
  if (cached) return cached;

  try {
    const sourceFile = ts.createSourceFile(
      file.relativePath,
      file.content,
      ts.ScriptTarget.Latest,
      true,
      getScriptKind(file.relativePath),
    );
    sourceFileCache.set(file.absolutePath, sourceFile);
    return sourceFile;
  } catch {
    return undefined;
  }
}

/** Clears the AST cache (call between scan runs). */
export function clearAstCache(): void {
  sourceFileCache.clear();
}

/** Represents an import found in a source file. */
export interface ImportInfo {
  moduleSpecifier: string;
  defaultImport?: string;
  namedImports: string[];
  node: ts.Node;
  line: number;
}

/** Finds all import declarations in a source file. */
export function findImports(sourceFile: ts.SourceFile): ImportInfo[] {
  const imports: ImportInfo[] = [];

  ts.forEachChild(sourceFile, (node) => {
    // ES import
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      const info: ImportInfo = {
        moduleSpecifier: node.moduleSpecifier.text,
        namedImports: [],
        node,
        line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
      };

      const clause = node.importClause;
      if (clause) {
        if (clause.name) {
          info.defaultImport = clause.name.text;
        }
        if (clause.namedBindings && ts.isNamedImports(clause.namedBindings)) {
          info.namedImports = clause.namedBindings.elements.map((e) => e.name.text);
        }
      }

      imports.push(info);
    }

    // CommonJS require
    if (ts.isVariableStatement(node)) {
      for (const decl of node.declarationList.declarations) {
        if (
          decl.initializer &&
          ts.isCallExpression(decl.initializer) &&
          ts.isIdentifier(decl.initializer.expression) &&
          decl.initializer.expression.text === 'require' &&
          decl.initializer.arguments.length > 0
        ) {
          const arg = decl.initializer.arguments[0];
          if (arg && ts.isStringLiteral(arg)) {
            imports.push({
              moduleSpecifier: arg.text,
              defaultImport: ts.isIdentifier(decl.name) ? decl.name.text : undefined,
              namedImports: [],
              node,
              line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
            });
          }
        }
      }
    }
  });

  return imports;
}

/** Represents a function/method call found in a source file. */
export interface CallInfo {
  name: string;
  fullExpression: string;
  arguments: ts.NodeArray<ts.Expression>;
  node: ts.CallExpression;
  line: number;
}

/** Recursively finds all call expressions in a source file. */
export function findCalls(sourceFile: ts.SourceFile): CallInfo[] {
  const calls: CallInfo[] = [];

  function visit(node: ts.Node): void {
    if (ts.isCallExpression(node)) {
      const name = getCallName(node);
      if (name) {
        calls.push({
          name,
          fullExpression: node.expression.getText(sourceFile),
          arguments: node.arguments,
          node,
          line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        });
      }
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return calls;
}

/** Extracts the name from a call expression. */
function getCallName(node: ts.CallExpression): string | undefined {
  const expr = node.expression;
  if (ts.isIdentifier(expr)) return expr.text;
  if (ts.isPropertyAccessExpression(expr)) return expr.name.text;
  return undefined;
}

/** Finds all string literals in a source file. */
export function findStringLiterals(
  sourceFile: ts.SourceFile,
): Array<{ value: string; line: number; node: ts.Node }> {
  const literals: Array<{ value: string; line: number; node: ts.Node }> = [];

  function visit(node: ts.Node): void {
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
      literals.push({
        value: node.text,
        line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        node,
      });
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return literals;
}

/** Walks the entire AST calling the visitor for each node. */
export function walkAST(sourceFile: ts.SourceFile, visitor: (node: ts.Node) => void): void {
  function visit(node: ts.Node): void {
    visitor(node);
    ts.forEachChild(node, visit);
  }
  visit(sourceFile);
}

/** Gets the line number (1-based) for a node in a source file. */
export function getLine(sourceFile: ts.SourceFile, node: ts.Node): number {
  return sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1;
}

/** Gets the source text for a specific line number. */
export function getLineText(sourceFile: ts.SourceFile, line: number): string {
  const lines = sourceFile.text.split('\n');
  return lines[line - 1]?.trimEnd() ?? '';
}

/** Gets a code snippet around a line number. */
export function getSnippet(sourceFile: ts.SourceFile, line: number, context = 2): string {
  const lines = sourceFile.text.split('\n');
  const start = Math.max(0, line - 1 - context);
  const end = Math.min(lines.length, line + context);
  return lines
    .slice(start, end)
    .map((l) => l.trimEnd())
    .join('\n');
}

/** Re-export ts for rules that need deeper AST access. */
export { ts };
