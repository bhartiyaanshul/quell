"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

import { SectionHeader } from "@/components/SectionHeader";

/**
 * Animated SVG architecture diagram.
 *
 * We draw four node boxes on a grid and an SVG path between them,
 * then animate ``pathLength`` from 0 → 1 so the data flow visually
 * "streams" between the subsystems when the section scrolls into view.
 */
export function Architecture() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-120px" });

  return (
    <section
      id="architecture"
      className="relative mx-auto max-w-6xl px-6 py-28 sm:py-32"
    >
      <SectionHeader
        eyebrow="Under the hood"
        title={
          <>
            Eleven subsystems,{" "}
            <span className="text-gradient-cool">one clean contract.</span>
          </>
        }
        body="Monitors emit RawEvents. Detector fingerprints. Commander investigates via tools in a Docker sandbox, persists every run, fans the result to Slack / Discord / Telegram, and surfaces it in a local dashboard."
      />

      <div ref={ref} className="relative mt-14 overflow-hidden rounded-2xl border border-border bg-bg-raised/40 p-6 backdrop-blur md:p-10">
        {/* Background grid */}
        <svg
          className="pointer-events-none absolute inset-0 h-full w-full opacity-20"
          aria-hidden="true"
        >
          <defs>
            <pattern id="arch-grid" width="28" height="28" patternUnits="userSpaceOnUse">
              <path
                d="M28 0L0 0 0 28"
                fill="none"
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#arch-grid)" />
        </svg>

        <div className="relative grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-6">
          <Node title="Monitors" subtitle="local-file, http, vercel, sentry" />
          <Node title="Detector" subtitle="signature + baseline" />
          <Node title="Agents" subtitle="commander + subagents" accent />
          <Node title="Sandbox" subtitle="FastAPI tool server" />
        </div>

        {/* Arrow animation — visible md+ only */}
        <div className="relative mt-10 hidden h-12 md:block">
          <svg viewBox="0 0 1000 48" className="h-full w-full">
            <motion.path
              d="M 80 24 L 920 24"
              stroke="url(#arch-flow)"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
              strokeDasharray="6 8"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={inView ? { pathLength: 1, opacity: 1 } : {}}
              transition={{ duration: 1.8, ease: [0.22, 1, 0.36, 1] }}
            />
            <defs>
              <linearGradient id="arch-flow" x1="0%" x2="100%">
                <stop offset="0%" stopColor="#fb923c" stopOpacity="0.35" />
                <stop offset="50%" stopColor="#fb923c" />
                <stop offset="100%" stopColor="#a78bfa" />
              </linearGradient>
            </defs>
          </svg>

          {/* Pulse traveling along the line */}
          <motion.div
            aria-hidden
            initial={{ x: 80, opacity: 0 }}
            animate={
              inView
                ? { x: 920, opacity: [0, 1, 1, 0] }
                : {}
            }
            transition={{
              duration: 2.4,
              delay: 1.5,
              repeat: Infinity,
              repeatDelay: 1.8,
              ease: "linear",
            }}
            className="absolute top-1/2 -mt-[5px] h-[10px] w-[10px] rounded-full bg-accent shadow-[0_0_14px_rgba(251,146,60,0.9)]"
          />
        </div>

        {/* Middle row */}
        <div className="relative mt-10 grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-6">
          <Node title="Tools" subtitle="code/git/monitoring/reporting" />
          <Node title="Skills" subtitle="19 bundled runbooks" />
          <Node title="Memory" subtitle="AgentRun · Event · Finding" />
          <Node title="CLI" subtitle="init · watch · dashboard · replay" />
        </div>

        {/* Bottom row — v0.2 surfaces */}
        <div className="relative mt-6 grid grid-cols-2 gap-4 md:grid-cols-3 md:gap-6">
          <Node title="Notifiers" subtitle="Slack · Discord · Telegram" />
          <Node title="Dashboard" subtitle="Next.js + FastAPI" />
          <Node title="Cost + budgets" subtitle="per-model rate card" />
        </div>
      </div>
    </section>
  );
}

function Node({
  title,
  subtitle,
  accent,
}: {
  title: string;
  subtitle: string;
  accent?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94, y: 12 }}
      whileInView={{ opacity: 1, scale: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className={`relative rounded-xl border p-4 backdrop-blur ${
        accent
          ? "border-accent/40 bg-accent/[0.06] shadow-[0_12px_40px_-20px_rgba(251,146,60,0.45)]"
          : "border-border bg-bg-base/60"
      }`}
    >
      <div className="text-sm font-semibold tracking-tight text-fg">{title}</div>
      <div className="mt-1 font-mono text-[11px] leading-relaxed text-fg-dim">
        {subtitle}
      </div>
      {accent && (
        <motion.div
          aria-hidden
          animate={{ opacity: [0.45, 1, 0.45] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          className="absolute right-3 top-3 h-2 w-2 rounded-full bg-accent shadow-[0_0_10px_rgba(251,146,60,0.9)]"
        />
      )}
    </motion.div>
  );
}
