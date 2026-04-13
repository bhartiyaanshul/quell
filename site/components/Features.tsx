"use client";

import { motion } from "framer-motion";

const EXTERNAL_TOOLS = [
  {
    name: "Semgrep",
    label: "Static Analysis",
    accent: "violet",
    desc: "SQL injection, XSS, hardcoded secrets, weak crypto, insecure deserialization, path traversal, and hundreds more from the open-source ruleset.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    name: "gitleaks",
    label: "Secret Scanning",
    accent: "cyan",
    desc: "API keys buried in git history \u2014 AWS, Stripe, OpenAI, Anthropic, GitHub, Supabase, and 100+ other providers.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
  },
];

const CUSTOM_RULES = [
  { severity: "CRITICAL", name: ".env files in project / git history" },
  { severity: "CRITICAL", name: "Supabase tables without RLS" },
  { severity: "CRITICAL", name: "Secrets in NEXT_PUBLIC_* env vars" },
  { severity: "CRITICAL", name: "Plaintext password storage" },
  { severity: "HIGH", name: "AI endpoints without rate limiting" },
  { severity: "HIGH", name: "Unprotected admin routes" },
  { severity: "HIGH", name: "CORS wildcard with credentials" },
  { severity: "HIGH", name: "Weak / hardcoded JWT secrets" },
  { severity: "HIGH", name: "eval() and Function() calls" },
  { severity: "HIGH", name: "Open redirect vulnerabilities" },
  { severity: "HIGH", name: "NoSQL injection patterns" },
  { severity: "MEDIUM", name: "dangerouslySetInnerHTML without sanitizer" },
  { severity: "MEDIUM", name: "Insecure cookie configuration" },
];

const SEV_STYLE: Record<string, string> = {
  CRITICAL: "bg-red-50 text-red-600 border-red-200",
  HIGH: "bg-orange-50 text-orange-600 border-orange-200",
  MEDIUM: "bg-amber-50 text-amber-700 border-amber-200",
};

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function Features() {
  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-14"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            What It Catches
          </h2>
          <p className="mt-4 text-va-muted max-w-2xl mx-auto">
            13 hand-written AST-powered rules purpose-built for patterns AI
            coding assistants produce, plus Semgrep static analysis and gitleaks
            secret scanning.
          </p>
        </motion.div>

        {/* External tools */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {EXTERNAL_TOOLS.map((tool, i) => (
            <motion.div
              key={tool.name}
              initial={{ opacity: 0, x: i === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5 }}
              className="p-6 rounded-xl bg-white border border-va-border hover:shadow-md transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    tool.accent === "violet"
                      ? "bg-violet-50 text-violet-600"
                      : "bg-cyan-50 text-cyan-600"
                  }`}
                >
                  {tool.icon}
                </div>
                <div>
                  <h3 className="font-semibold">{tool.name}</h3>
                  <p className="text-xs text-va-faint">{tool.label}</p>
                </div>
              </div>
              <p className="text-sm text-va-muted leading-relaxed">
                {tool.desc}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Custom rules */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
        >
          {CUSTOM_RULES.map((rule) => (
            <motion.div
              key={rule.name}
              variants={item}
              className="flex items-start gap-3 p-4 rounded-xl bg-white border border-va-border hover:border-slate-300 hover:shadow-sm transition-all duration-200"
            >
              <span
                className={`shrink-0 mt-0.5 px-1.5 py-px rounded text-[10px] font-bold border leading-tight ${SEV_STYLE[rule.severity]}`}
              >
                {rule.severity}
              </span>
              <span className="text-sm text-va-text/80">{rule.name}</span>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
