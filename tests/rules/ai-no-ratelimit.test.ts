import { describe, expect, it } from 'vitest';
import { aiNoRatelimitRule } from '../../src/scanners/custom/ai-no-ratelimit.js';
import { mockFile } from './helpers.js';

describe('ai-no-ratelimit rule', () => {
  it('detects AI SDK in route without rate limiting', () => {
    const file = mockFile(
      'src/pages/api/chat.js',
      `import OpenAI from 'openai';\nexport default function handler(req, res) {}`,
    );
    const findings = aiNoRatelimitRule([file]);
    expect(findings.length).toBe(1);
    expect(findings[0]?.severity).toBe('HIGH');
  });

  it('ignores route with rate limiter import', () => {
    const file = mockFile(
      'src/pages/api/chat.js',
      `import OpenAI from 'openai';\nimport rateLimit from 'express-rate-limit';\nexport default function handler(req, res) {}`,
    );
    const findings = aiNoRatelimitRule([file]);
    expect(findings.length).toBe(0);
  });

  it('ignores non-route files with AI SDK', () => {
    const file = mockFile(
      'src/lib/ai.js',
      `import OpenAI from 'openai';\nexport const client = new OpenAI();`,
    );
    const findings = aiNoRatelimitRule([file]);
    expect(findings.length).toBe(0);
  });
});
