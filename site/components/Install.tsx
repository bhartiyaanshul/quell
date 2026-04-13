"use client";

import { motion } from "framer-motion";
import { useState } from "react";

function CopyBtn({ text }: { text: string }) {
  const [ok, setOk] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setOk(true);
    setTimeout(() => setOk(false), 2000);
  };
  return (
    <button
      onClick={copy}
      className="text-slate-300 hover:text-slate-500 transition-colors"
      title="Copy"
    >
      {ok ? (
        <svg className="w-4 h-4 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

const COMMANDS = [
  { label: "Scan a directory", cmd: "npx frisk ./my-app" },
  { label: "Custom output", cmd: "npx frisk ./my-app -o report.html" },
  { label: "JSON for CI", cmd: "npx frisk ./my-app --format json" },
  { label: "Fail on HIGH+", cmd: "npx frisk ./my-app --fail-on high" },
];

const OPTIONS = [
  { flag: "-o, --output <path>", desc: "Report file path", def: "frisk-report.html" },
  { flag: "-f, --format <fmt>", desc: "Output format: html or json", def: "html" },
  { flag: "--fail-on <severity>", desc: "Exit 1 if findings at or above", def: "\u2014" },
  { flag: "-V, --version", desc: "Print version number", def: "\u2014" },
];

export default function Install() {
  return (
    <section id="install" className="py-24 px-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-14"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            Get Started
          </h2>
          <p className="mt-4 text-va-muted">
            No install needed. Just run it with npx.
          </p>
        </motion.div>

        {/* Commands */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="space-y-2.5 mb-12"
        >
          {COMMANDS.map((c) => (
            <div
              key={c.cmd}
              className="flex items-center justify-between px-5 py-3.5 rounded-xl bg-va-text font-mono text-sm group hover:bg-va-text/90 transition-colors duration-200"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-slate-500 text-xs hidden sm:block whitespace-nowrap">
                  {c.label}
                </span>
                <span className="text-violet-400 shrink-0">$</span>
                <span className="text-slate-300 truncate">{c.cmd}</span>
              </div>
              <CopyBtn text={c.cmd} />
            </div>
          ))}
        </motion.div>

        {/* Options table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="rounded-xl bg-white border border-va-border overflow-hidden mb-12"
        >
          <div className="px-5 py-3.5 border-b border-va-border bg-slate-50">
            <h3 className="text-sm font-semibold">CLI Options</h3>
          </div>
          <div className="divide-y divide-va-border">
            {OPTIONS.map((o) => (
              <div
                key={o.flag}
                className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-0 px-5 py-3"
              >
                <code className="text-violet-600 text-sm font-mono sm:w-[38%]">
                  {o.flag}
                </code>
                <span className="text-va-muted text-sm sm:w-[38%]">
                  {o.desc}
                </span>
                <span className="text-va-faint text-sm font-mono sm:w-[24%] sm:text-right">
                  {o.def}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CI snippet */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h3 className="text-base font-semibold mb-4 text-center text-va-muted">
            GitHub Actions
          </h3>
          <div className="rounded-xl bg-va-text overflow-hidden">
            <div className="px-5 py-2.5 border-b border-slate-700/50 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                ci.yml
              </span>
              <CopyBtn
                text={`- name: Security scan\n  run: npx frisk . --format json --fail-on high`}
              />
            </div>
            <pre className="px-5 py-5 font-mono text-sm text-slate-300 overflow-x-auto leading-relaxed">
              {`- name: Security scan
  run: npx frisk . --format json --fail-on high`}
            </pre>
          </div>
          <div className="mt-4 flex justify-center gap-8 text-xs text-va-faint">
            <span>
              Exit <code className="text-green-600">0</code> = clean
            </span>
            <span>
              Exit <code className="text-red-500">1</code> = findings above
              threshold
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
