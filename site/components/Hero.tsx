"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import Terminal from "./Terminal";

const stagger = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.12 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

export default function Hero() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText("npx friskit ./my-app");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative min-h-screen pt-28 pb-20 overflow-hidden">
      {/* Background — subtle dot pattern + green radial wash */}
      <div className="absolute inset-0 bg-dot-pattern opacity-40" />
      <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[900px] h-[600px] rounded-full bg-violet-100/40 blur-[160px] pointer-events-none" />

      <div className="relative max-w-6xl mx-auto px-6">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="text-center max-w-4xl mx-auto"
        >
          {/* Badge */}
          <motion.div variants={fadeUp}>
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-200 bg-violet-50 text-violet-700 text-sm font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-500 opacity-50" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500" />
              </span>
              Open Source Security Scanner
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={fadeUp}
            className="mt-8 text-4xl sm:text-5xl md:text-7xl font-extrabold leading-[1.08] tracking-tight"
          >
            Your vibe-coded app has{" "}
            <span className="gradient-text">security holes</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="mt-3 text-2xl sm:text-3xl md:text-5xl font-bold text-va-faint tracking-tight"
          >
            Find them in 60 seconds.
          </motion.p>

          {/* Subtitle */}
          <motion.p
            variants={fadeUp}
            className="mt-6 text-base md:text-lg text-va-muted max-w-2xl mx-auto leading-relaxed"
          >
            One command. A report card with severity-ranked findings and a
            plain-English fix for each one. Works with any JS/TS project.
          </motion.p>

          {/* CTA row */}
          <motion.div
            variants={fadeUp}
            className="mt-8 flex flex-wrap items-center justify-center gap-3"
          >
            <button
              onClick={handleCopy}
              className="group flex items-center gap-3 px-5 py-3 rounded-xl bg-white border border-va-border hover:border-violet-300 hover:shadow-lg hover:shadow-violet-100/50 transition-all duration-300 font-mono text-sm"
            >
              <span className="text-violet-600">$</span>
              <span className="text-va-text/70 group-hover:text-va-text transition-colors">
                npx friskit ./my-app
              </span>
              {copied ? (
                <svg className="w-4 h-4 text-violet-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-slate-300 group-hover:text-slate-400 transition-colors shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              )}
            </button>

            <a
              href="https://github.com/Bhartiyaanshul/frisk"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-va-text text-white text-sm font-medium hover:bg-va-text/90 transition-colors duration-200"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              Star on GitHub
            </a>
          </motion.div>
        </motion.div>

        {/* Terminal */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9, ease: "easeOut" }}
          className="mt-16 max-w-4xl mx-auto"
        >
          <Terminal />
        </motion.div>
      </div>
    </section>
  );
}
