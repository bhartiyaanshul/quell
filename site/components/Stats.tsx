"use client";

import { motion } from "framer-motion";

const STATS = [
  {
    value: "196/198",
    label: "Apps Had Vulnerabilities",
    description: "Recent audit of vibe-coded apps found nearly all had security issues",
  },
  {
    value: "18,000+",
    label: "Users Exposed",
    description: "A single Lovable app had its auth logic backwards",
  },
  {
    value: "1.5M",
    label: "API Keys Leaked",
    description: "From vibe-coded repositories pushed to GitHub",
  },
];

export default function Stats() {
  return (
    <section className="py-24 px-6 bg-va-bg-alt">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            The Problem
          </h2>
          <p className="mt-4 text-va-muted max-w-xl mx-auto">
            AI writes code fast. It doesn&apos;t write code safe. These numbers
            are from real vibe-coded apps.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {STATS.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.12 }}
              className="text-center p-8 rounded-2xl bg-white border border-va-border hover:border-violet-200 hover:shadow-lg hover:shadow-violet-50 transition-all duration-400"
            >
              <div className="text-4xl md:text-5xl font-extrabold gradient-text tracking-tight">
                {stat.value}
              </div>
              <div className="mt-3 text-base font-semibold text-va-text">
                {stat.label}
              </div>
              <div className="mt-1 text-sm text-va-muted leading-relaxed">
                {stat.description}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
