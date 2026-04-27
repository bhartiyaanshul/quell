"use client";

import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import {
  Bell,
  BookOpen,
  Brain,
  GitPullRequest,
  LayoutDashboard,
  Lock,
  Network,
  ShieldCheck,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { SectionHeader } from "@/components/SectionHeader";
import { FEATURES } from "@/lib/constants";

const ICON_MAP: Record<string, LucideIcon> = {
  "git-pull-request": GitPullRequest,
  "shield-check": ShieldCheck,
  brain: Brain,
  network: Network,
  "book-open": BookOpen,
  lock: Lock,
  bell: Bell,
  "layout-dashboard": LayoutDashboard,
  wallet: Wallet,
};

export function Features() {
  return (
    <section id="features" className="relative mx-auto max-w-6xl px-6 py-24 sm:py-28">
      <SectionHeader
        eyebrow="Built for real on-call"
        title={
          <>
            The boring,{" "}
            <span className="text-gradient-cool">critical</span> details.
          </>
        }
        body="Draft-PR-only, sandboxed by default, model-agnostic. Opinionated where it matters, flexible where it doesn't."
      />

      <div className="mt-16 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <FeatureCard key={f.title} feature={f} index={i} />
        ))}
      </div>
    </section>
  );
}

function FeatureCard({
  feature,
  index,
}: {
  feature: (typeof FEATURES)[number];
  index: number;
}) {
  const Icon = ICON_MAP[feature.icon] ?? ShieldCheck;

  // Mouse-follow radial highlight — the "alive" card effect.
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const highlight = useMotionTemplate`radial-gradient(220px circle at ${mx}px ${my}px, rgba(251,146,60,0.16), transparent 70%)`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{
        duration: 0.55,
        delay: index * 0.06,
        ease: [0.22, 1, 0.36, 1],
      }}
      onMouseMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        mx.set(e.clientX - r.left);
        my.set(e.clientY - r.top);
      }}
      className="group relative overflow-hidden rounded-2xl border border-border bg-bg-raised/40 p-6 backdrop-blur transition hover:border-border-bright hover:bg-bg-raised/70"
    >
      {/* Mouse-follow highlight */}
      <motion.div
        aria-hidden
        style={{ background: highlight }}
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
      />

      <div className="relative">
        <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl border border-border bg-bg-base text-accent transition group-hover:border-accent/50">
          <Icon size={20} strokeWidth={1.75} />
        </div>
        <h3 className="text-lg font-semibold tracking-tight text-fg">
          {feature.title}
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-fg-muted">
          {feature.body}
        </p>
      </div>
    </motion.div>
  );
}
