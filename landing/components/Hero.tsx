"use client";

import { useRef } from "react";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Github, Sparkles } from "lucide-react";

import { AnimatedGrid } from "@/components/AnimatedGrid";
import { SplineScene as HeroOrb } from "@/components/SplineScene";
import { useGsap, gsap } from "@/lib/gsap";
import { REPO_URL } from "@/lib/constants";

// Hook: anthropomorphic — Quell as a teammate.
// Gradient lands on "never sleeps." for the warm payoff beat.
const HEADLINE = ["An", "on-call", "engineer", "that", "never", "sleeps."];
const GRADIENT_FROM = 4; // gradient applies to "never sleeps." (last 2 words)
const SUBLINE =
  "Quell watches your logs, investigates the incident in a Docker sandbox, and ships a root-cause report with a proposed fix to your inbox — before your phone buzzes.";

export function Hero() {
  const reduce = useReducedMotion();
  const sectionRef = useRef<HTMLElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  // Scroll-driven 3D tilt (desktop only, respects reduced motion).
  useGsap(
    () => {
      const stage = stageRef.current;
      if (!stage) return;
      const mq = window.matchMedia(
        "(min-width: 768px) and (prefers-reduced-motion: no-preference)"
      );
      if (!mq.matches) return;

      gsap.to(stage, {
        rotateX: 8,
        scale: 0.92,
        y: -60,
        ease: "power2.out",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: "+=100%",
          scrub: true,
        },
      });
    },
    sectionRef,
    []
  );

  // Word-by-word reveal — cinematic at hero scale (slide + blur).
  const container = {
    hidden: {},
    show: {
      transition: {
        staggerChildren: reduce ? 0 : 0.11,
        delayChildren: 0.18,
      },
    },
  };
  const word = {
    hidden: { y: 38, opacity: 0, filter: "blur(8px)" },
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
      ref={sectionRef}
      id="top"
      className="relative isolate flex flex-col overflow-hidden lg:min-h-[100svh]"
      style={{ transformStyle: "preserve-3d" }}
    >
      {/* Photo background */}
      <div className="absolute inset-0 -z-20">
        <Image
          src="/bg/hero.jpg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover opacity-55"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-bg-base/65 via-bg-base/55 to-bg-base" />
      </div>

      {/* Animated grid + ember particles */}
      <AnimatedGrid />

      {/* Noise grain */}
      <div className="noise-overlay-bright pointer-events-none absolute inset-0 -z-10" />

      <div
        ref={stageRef}
        className="relative mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 items-center gap-y-10 px-5 pb-16 pt-[96px] sm:gap-y-12 sm:px-6 sm:pb-20 sm:pt-[112px] lg:grid-cols-[1.08fr_1fr] lg:gap-x-12 lg:pb-12 xl:gap-x-16"
      >
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
            className="group mb-5 inline-flex max-w-full items-center gap-2 truncate rounded-full border border-border bg-bg-raised/60 px-3 py-1.5 text-[11px] font-medium text-fg-muted backdrop-blur transition hover:border-accent/50 hover:text-fg sm:mb-7 sm:px-3.5 sm:text-xs"
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

          {/* Headline — word-by-word slide + blur reveal */}
          <motion.h1
            variants={container}
            initial="hidden"
            animate="show"
            className="max-w-[640px] text-[clamp(2.25rem,5.4vw,4rem)] font-semibold leading-[1.04] tracking-tight text-fg"
          >
            {HEADLINE.map((w, i) => (
              <span key={i} className="inline-block overflow-hidden pr-[0.22em]">
                <motion.span
                  variants={word}
                  className={
                    i >= GRADIENT_FROM
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
            custom={0.7}
            className="mt-4 max-w-[540px] text-sm leading-relaxed text-fg-muted sm:mt-5 sm:text-base md:text-lg"
          >
            {SUBLINE}
          </motion.p>

          {/* CTAs */}
          <motion.div
            variants={fade}
            initial="hidden"
            animate="show"
            custom={0.9}
            className="mt-5 flex flex-wrap items-center gap-3 sm:mt-7"
          >
            <a
              href="#install"
              className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-accent px-4 py-2.5 text-sm font-semibold text-bg-base shadow-[0_10px_30px_-10px_rgba(251,146,60,0.6)] transition hover:shadow-[0_15px_40px_-10px_rgba(251,146,60,0.75)] sm:px-5 sm:py-3"
            >
              <span className="relative z-10">Install Quell</span>
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
              className="group inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/60 px-4 py-2.5 text-sm font-semibold text-fg backdrop-blur transition hover:border-border-bright hover:bg-bg-raised sm:px-5 sm:py-3"
            >
              <Github size={16} />
              <span>View on GitHub</span>
            </a>
          </motion.div>

          <motion.div
            variants={fade}
            initial="hidden"
            animate="show"
            custom={1.1}
            className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-fg-dim sm:mt-8 sm:gap-x-5 sm:text-xs"
          >
            <Bullet label="302 tests passing" />
            <Bullet label="Python 3.12+" />
            <Bullet label="Apache 2.0" />
            <Bullet label="Sandboxed by default" />
          </motion.div>
        </div>

        {/* Right — Three.js orb, desktop only */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.4, delay: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="relative hidden aspect-[1/1] w-full max-w-[460px] justify-self-end lg:block xl:max-w-[500px]"
        >
          {/* halo behind the orb */}
          <div
            aria-hidden
            className="absolute inset-[15%] -z-10 rounded-full bg-gradient-to-br from-accent/35 via-cool/20 to-transparent blur-3xl"
          />
          <HeroOrb parallax={0.05} />
        </motion.div>
      </div>

      {/* Bottom fade */}
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
