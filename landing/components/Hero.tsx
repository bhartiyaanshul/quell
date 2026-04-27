"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Github, Sparkles } from "lucide-react";

import { AnimatedGrid } from "@/components/AnimatedGrid";
import { TerminalDemo } from "@/components/TerminalDemo";
import { REPO_URL } from "@/lib/constants";

const HEADLINE = ["Your", "production's", "autonomous", "on-call."];
const SUBLINE =
  "Quell watches your logs, investigates incidents in a Docker sandbox, and produces a root-cause report with a proposed fix — while you sleep.";

export function Hero() {
  const reduce = useReducedMotion();

  const container = {
    hidden: {},
    show: {
      transition: {
        staggerChildren: reduce ? 0 : 0.12,
        delayChildren: 0.15,
      },
    },
  };

  const word = {
    hidden: { y: 42, opacity: 0, filter: "blur(8px)" },
    show: {
      y: 0,
      opacity: 1,
      filter: "blur(0px)",
      transition: { duration: 0.75, ease: [0.22, 1, 0.36, 1] },
    },
  };

  const fade = {
    hidden: { opacity: 0, y: 16 },
    show: (delay: number) => ({
      opacity: 1,
      y: 0,
      transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1], delay },
    }),
  };

  return (
    <section
      id="top"
      className="relative isolate min-h-[820px] pt-[140px] sm:min-h-[900px] md:pt-[170px]"
    >
      <AnimatedGrid />

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-14 px-6 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:gap-20">
        {/* Left — copy */}
        <div>
          {/* Announcement pill */}
          <motion.a
            href={`${REPO_URL}/blob/main/CHANGELOG.md`}
            target="_blank"
            rel="noopener noreferrer"
            variants={fade}
            initial="hidden"
            animate="show"
            custom={0}
            className="group mb-8 inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/60 px-3.5 py-1.5 text-xs font-medium text-fg-muted backdrop-blur transition hover:border-accent/50 hover:text-fg"
          >
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-accent/15">
              <Sparkles size={10} className="text-accent" />
            </span>
            <span>v0.2.0 — dashboard, notifiers, cost budgets</span>
            <ArrowRight
              size={12}
              className="transition group-hover:translate-x-0.5"
            />
          </motion.a>

          {/* Headline — word-by-word reveal */}
          <motion.h1
            variants={container}
            initial="hidden"
            animate="show"
            className="max-w-[640px] text-5xl font-semibold leading-[1.04] tracking-tight text-fg sm:text-6xl md:text-7xl"
          >
            {HEADLINE.map((w, i) => (
              <span key={i} className="inline-block overflow-hidden pr-[0.22em]">
                <motion.span
                  variants={word}
                  className={
                    w === "autonomous" || w === "on-call."
                      ? "inline-block text-gradient"
                      : "inline-block"
                  }
                >
                  {w}
                </motion.span>
              </span>
            ))}
          </motion.h1>

          <motion.p
            variants={fade}
            initial="hidden"
            animate="show"
            custom={0.55}
            className="mt-7 max-w-[580px] text-base leading-relaxed text-fg-muted sm:text-lg"
          >
            {SUBLINE}
          </motion.p>

          {/* CTAs */}
          <motion.div
            variants={fade}
            initial="hidden"
            animate="show"
            custom={0.75}
            className="mt-9 flex flex-wrap items-center gap-3"
          >
            <a
              href="#install"
              className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-accent px-5 py-3 text-sm font-semibold text-bg-base shadow-[0_10px_30px_-10px_rgba(251,146,60,0.6)] transition hover:shadow-[0_15px_40px_-10px_rgba(251,146,60,0.75)]"
            >
              <span className="relative z-10">Install Quell</span>
              <ArrowRight
                size={16}
                className="relative z-10 transition group-hover:translate-x-0.5"
              />
              {/* Shine */}
              <span
                aria-hidden
                className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/35 to-transparent transition-transform duration-700 group-hover:translate-x-full"
              />
            </a>

            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/60 px-5 py-3 text-sm font-semibold text-fg backdrop-blur transition hover:border-border-bright hover:bg-bg-raised"
            >
              <Github size={16} />
              <span>View on GitHub</span>
            </a>
          </motion.div>

          {/* Socials row */}
          <motion.div
            variants={fade}
            initial="hidden"
            animate="show"
            custom={0.95}
            className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-fg-dim"
          >
            <Bullet label="302 tests passing" />
            <Bullet label="Python 3.12+" />
            <Bullet label="Apache 2.0" />
            <Bullet label="Sandboxed by default" />
          </motion.div>
        </div>

        {/* Right — live terminal */}
        <div className="relative">
          <TerminalDemo />
        </div>
      </div>

      {/* Bottom fade into next section */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-bg-base"
      />
    </section>
  );
}

function Bullet({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-1.5 w-1.5 rounded-full bg-accent/70 shadow-[0_0_8px_rgba(251,146,60,0.8)]" />
      <span>{label}</span>
    </span>
  );
}
