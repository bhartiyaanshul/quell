"use client";

import { motion } from "framer-motion";

const STEPS = [
  {
    num: "01",
    title: "Walk",
    desc: "Recursively scans the target directory, respecting .gitignore, skipping binaries and node_modules.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
    ),
  },
  {
    num: "02",
    title: "Parse",
    desc: "Builds TypeScript ASTs for JS/TS/JSX/TSX files using the TypeScript Compiler API with cross-rule caching.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
  },
  {
    num: "03",
    title: "Scan",
    desc: "Runs Semgrep, gitleaks, and 13 custom AST-powered rules. Deduplicates and sorts findings by severity.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
  {
    num: "04",
    title: "Report",
    desc: "Generates a self-contained HTML report with severity filtering, code snippets, and fix recommendations.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-6 bg-va-bg-alt">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            How It Works
          </h2>
          <p className="mt-4 text-va-muted">
            Four steps. Zero configuration. Results in under 60 seconds.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {STEPS.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="relative p-6 rounded-2xl bg-white border border-va-border hover:border-violet-200 hover:shadow-md transition-all duration-300"
            >
              {i < STEPS.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-2.5 w-5 h-px bg-slate-200" />
              )}

              <span className="text-violet-500/40 text-xs font-mono font-bold">
                {step.num}
              </span>
              <div className="mt-3 w-11 h-11 rounded-xl bg-violet-50 flex items-center justify-center text-violet-600">
                {step.icon}
              </div>
              <h3 className="mt-4 text-lg font-bold">{step.title}</h3>
              <p className="mt-2 text-sm text-va-muted leading-relaxed">
                {step.desc}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Score formula */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-12 p-5 rounded-xl bg-white border border-va-border text-center"
        >
          <p className="text-xs text-va-faint uppercase tracking-wider mb-2">
            Security Score Formula
          </p>
          <code className="text-base md:text-lg font-mono text-violet-700 font-semibold">
            100 &minus; (25&times;CRITICAL + 10&times;HIGH + 3&times;MEDIUM +
            1&times;LOW)
          </code>
        </motion.div>
      </div>
    </section>
  );
}
