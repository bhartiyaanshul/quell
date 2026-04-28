"use client";

import { motion } from "framer-motion";
import { ArrowRight, Github } from "lucide-react";

import { REPO_URL } from "@/lib/constants";

export function CTA() {
  return (
    <section className="relative mx-auto max-w-5xl bg-bg-base px-6 py-28">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative overflow-hidden rounded-3xl border border-border bg-bg-raised/60 px-6 py-16 text-center backdrop-blur sm:px-10 sm:py-20"
      >
        {/* Radial glow behind the CTA */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10"
        >
          <div className="absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/20 blur-3xl" />
          <div className="absolute left-1/3 top-1/3 h-[380px] w-[380px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cool/20 blur-3xl" />
        </div>

        <motion.div
          aria-hidden
          animate={{ rotate: 360 }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
          className="pointer-events-none absolute -right-40 -top-40 h-[500px] w-[500px] rounded-full border border-accent/10"
        />

        <h2 className="text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-fg sm:text-5xl">
          Ship fewer 3am pings.{" "}
          <span className="text-gradient">Sleep through more nights.</span>
        </h2>
        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-fg-muted sm:text-lg">
          Quell is Apache-2.0, built on LiteLLM, and designed so your code
          never leaves your machine.  Install in under a minute.
        </p>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
          <a
            href="#install"
            className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-accent px-6 py-3.5 text-sm font-semibold text-bg-base shadow-[0_15px_40px_-15px_rgba(251,146,60,0.7)] transition hover:shadow-[0_18px_50px_-15px_rgba(251,146,60,0.85)]"
          >
            <span className="relative z-10">Get started</span>
            <ArrowRight
              size={16}
              className="relative z-10 transition group-hover:translate-x-0.5"
            />
            <span
              aria-hidden
              className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/35 to-transparent transition-transform duration-700 group-hover:translate-x-full"
            />
          </a>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/60 px-6 py-3.5 text-sm font-semibold text-fg backdrop-blur transition hover:border-border-bright"
          >
            <Github size={16} />
            Star on GitHub
          </a>
        </div>
      </motion.div>
    </section>
  );
}
