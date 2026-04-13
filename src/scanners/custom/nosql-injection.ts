/**
 * Rule: NoSQL injection via unsanitized user input in MongoDB queries
 *
 * If user input (req.body, req.query) is passed directly to MongoDB
 * query methods without validation, an attacker can inject query
 * operators like { "$gt": "" } to bypass authentication or extract data.
 *
 * https://cwe.mitre.org/data/definitions/943.html
 */
import type { FileInfo, Finding } from '../../types.js';
import { findCalls, getSnippet, isParseable, parseFile, ts } from '../../utils/ast.js';

const MONGO_QUERY_METHODS = new Set([
  'findOne',
  'find',
  'findOneAndUpdate',
  'findOneAndDelete',
  'findOneAndReplace',
  'updateOne',
  'updateMany',
  'deleteOne',
  'deleteMany',
  'countDocuments',
  'aggregate',
]);

/** Checks if a node references user input. */
function referencesUserInput(node: ts.Expression, sourceFile: ts.SourceFile): boolean {
  const text = node.getText(sourceFile);
  return (
    text.includes('req.body') ||
    text.includes('req.query') ||
    text.includes('req.params') ||
    text.includes('request.body') ||
    text.includes('request.query')
  );
}

/** Checks if a variable was destructured from user input. */
function isDestructuredFromInput(varName: string, content: string, maxLine: number): boolean {
  const lines = content.split('\n').slice(0, maxLine);
  for (const line of lines) {
    if (
      line.includes(varName) &&
      (line.includes('req.body') || line.includes('req.query') || line.includes('req.params'))
    ) {
      return true;
    }
  }
  return false;
}

/** Detects NoSQL injection patterns in MongoDB queries. */
export function nosqlInjectionRule(files: FileInfo[]): Finding[] {
  const findings: Finding[] = [];

  for (const file of files) {
    if (!isParseable(file.relativePath)) continue;
    if (
      !file.content.includes('findOne') &&
      !file.content.includes('find(') &&
      !file.content.includes('collection')
    ) {
      continue;
    }

    const sourceFile = parseFile(file);
    if (!sourceFile) continue;

    const calls = findCalls(sourceFile);

    for (const call of calls) {
      if (!MONGO_QUERY_METHODS.has(call.name)) continue;
      if (call.arguments.length === 0) continue;

      const queryArg = call.arguments[0];
      if (!queryArg) continue;

      // Direct user input: findOne(req.body)
      if (referencesUserInput(queryArg, sourceFile)) {
        findings.push({
          title: `NoSQL injection: user input passed to ${call.name}()`,
          severity: 'HIGH',
          source: 'custom',
          ruleId: 'frisk/nosql-injection-direct',
          filePath: file.relativePath,
          line: call.line,
          codeSnippet: getSnippet(sourceFile, call.line, 3),
          description: `User input is passed directly to MongoDB's ${call.name}(). An attacker can send query operators like {"$gt": ""} to bypass filters, or {"$regex": ".*"} to extract data.`,
          fix: 'Validate and sanitize all user input before using it in queries. Use a schema validator like zod or joi. For string fields, explicitly cast: `{ username: String(req.body.username) }`.',
          docsUrl: 'https://cwe.mitre.org/data/definitions/943.html',
        });
        continue;
      }

      // Object literal with destructured user input variables
      if (ts.isObjectLiteralExpression(queryArg)) {
        for (const prop of queryArg.properties) {
          if (!ts.isPropertyAssignment(prop)) continue;

          const value = prop.initializer;
          if (ts.isIdentifier(value)) {
            const varName = value.text;
            if (
              isDestructuredFromInput(varName, file.content, call.line) &&
              (varName.toLowerCase().includes('password') ||
                varName.toLowerCase().includes('username') ||
                varName.toLowerCase().includes('email') ||
                varName.toLowerCase().includes('filter') ||
                varName.toLowerCase().includes('query'))
            ) {
              findings.push({
                title: `NoSQL injection risk: "${varName}" from user input in ${call.name}()`,
                severity: 'HIGH',
                source: 'custom',
                ruleId: 'frisk/nosql-injection-variable',
                filePath: file.relativePath,
                line: call.line,
                codeSnippet: getSnippet(sourceFile, call.line, 3),
                description: `The variable "${varName}" comes from user input and is used directly in a MongoDB query. If an attacker sends an object like {"$gt": ""} instead of a string, they can manipulate the query logic.`,
                fix: `Cast the value to a string before querying: \`{ ${varName}: String(req.body.${varName}) }\`. Better yet, validate with zod: \`z.string().parse(req.body.${varName})\`.`,
                docsUrl: 'https://cwe.mitre.org/data/definitions/943.html',
              });
            }
          }
        }
      }

      // JSON.parse(req.query.filter) passed to a query
      const argText = queryArg.getText(sourceFile);
      if (argText.includes('JSON.parse') && /req\.(query|body|params)/.test(argText)) {
        findings.push({
          title: `NoSQL injection: JSON.parse of user input in ${call.name}()`,
          severity: 'HIGH',
          source: 'custom',
          ruleId: 'frisk/nosql-injection-json-parse',
          filePath: file.relativePath,
          line: call.line,
          codeSnippet: getSnippet(sourceFile, call.line, 3),
          description:
            'User-supplied JSON is parsed and passed directly as a MongoDB query filter. An attacker has full control over the query structure and can inject any MongoDB operator.',
          fix: 'Never allow users to control the full query structure. Define an allowlist of filterable fields and build the query server-side.',
          docsUrl: 'https://cwe.mitre.org/data/definitions/943.html',
        });
      }
    }
  }

  return findings;
}
