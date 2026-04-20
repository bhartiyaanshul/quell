"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Activity, Bot, FileCheck2, Siren } from "lucide-react";

import { SectionHeader } from "@/components/SectionHeader";
import { PIPELINE_STEPS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICONS = [Activity, Siren, Bot, FileCheck2] as const;

/**
 * Animated four-step pipeline.
 *
 * The connecting line between steps draws in when the section comes
 * into view (scaleX from 0 → 1 along its own x-axis).  Each step then
 * slides + fades in with a stagger.  Numbered rings pulse to reinforce
 * the "alive" feel.
 */
export function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-120px" });

  return (
    <section
      id="how-it-works"
      className="relative mx-auto max-w-6xl px-6 py-28 sm:py-32"
    >
      <SectionHeader
        eyebrow="How it works"
        title={
          <>
            One watch loop.{" "}
            <span className="text-gradient">Four deliberate stages.</span>
          </>
        }
        body="From raw log line to draft report is usually under 30 seconds. Quell never auto-merges — a human always reviews the proposed fix."
      />

      <div ref={ref} className="relative mt-20">
        {/* Connector line (desktop) */}
        <motion.div
          aria-hidden
          initial={{ scaleX: 0 }}
          animate={inView ? { scaleX: 1 } : {}}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
          style={{ transformOrigin: "0% 50%" }}
          className="absolute left-[8%] right-[8%] top-[52px] hidden h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent md:block"
        />

        <div className="grid grid-cols-1 gap-8 md:grid-cols-4 md:gap-6">
          {PIPELINE_STEPS.map((step, i) => {
            const Icon = ICONS[i];
            return (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 40 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{
                  duration: 0.7,
                  delay: 0.25 + i * 0.14,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="relative"
              >
                {/* Numbered ring */}
                <div className="relative z-10 mx-auto flex h-[104px] w-[104px] items-center justify-center">
                  <div
                    className={cn(
                      "absolute inset-0 rounded-full border border-border bg-bg-raised/70 backdrop-blur",
                    )}
                  />
                  {/* Pulsing glow */}
                  <motion.div
                    aria-hidden
                    animate={
                      inView
                        ? {
                            scale: [1, 1.08, 1],
                            opacity: [0.4, 0.8, 0.4],
                          }
                        : {}
                    }
                    transition={{
                      duration: 3.2,
                      repeat: Infinity,
                      delay: i * 0.55,
                      ease: "easeInOut",
                    }}
                    className="absolute inset-0 rounded-full bg-accent/20 blur-xl"
                  />
                  <div className="relative flex h-14 w-14 items-center justify-center rounded-full border border-accent/40 bg-accent/10 text-accent">
                    <Icon size={22} strokeWidth={1.75} />
                  </div>
                  <div className="absolute -right-1 -top-1 flex h-7 w-7 items-center justify-center rounded-full border border-border bg-bg-base text-xs font-semibold text-fg-muted">
                    {i + 1}
                  </div>
                </div>

                {/* Card */}
                <div className="mt-5 rounded-2xl border border-border bg-bg-raised/50 p-5 text-center backdrop-blur md:text-left">
                  <h3 className="text-lg font-semibold tracking-tight text-fg">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-fg-muted">
                    {step.body}
                  </p>
                  <div className="mt-4 inline-block rounded-full border border-border bg-bg-base px-2.5 py-1 font-mono text-[11px] text-fg-dim">
                    {step.tag}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
