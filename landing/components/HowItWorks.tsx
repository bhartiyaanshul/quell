"use client";

import { useEffect, useRef, useState } from "react";
import { Activity, Bot, FileCheck2, Siren } from "lucide-react";

import { SectionHeader } from "@/components/SectionHeader";
import { PIPELINE_STEPS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICONS = [Activity, Siren, Bot, FileCheck2] as const;

/**
 * Pipeline overview. Each step occupies one viewport-tall block; the active
 * step is whichever block is closest to the centre of the viewport, tracked
 * with a single IntersectionObserver.
 *
 * The previous version used a 400vh sticky stage with a GSAP `scrub: true`
 * ScrollTrigger that mutated 4 DOM nodes' inline transform/opacity on every
 * scroll frame. That was the single biggest source of jank on lower-end
 * machines — replaced with this much cheaper layout.
 */
export function HowItWorks() {
  const [active, setActive] = useState(0);
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const nodes = stepRefs.current.filter(Boolean) as HTMLDivElement[];
    if (nodes.length === 0) return;

    // Track which step is most-visible. Threshold list lets us pick the
    // node with the highest intersection ratio without polling on scroll.
    const ratios = new Map<Element, number>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) ratios.set(e.target, e.intersectionRatio);
        let best = 0;
        let bestRatio = 0;
        nodes.forEach((node, i) => {
          const r = ratios.get(node) ?? 0;
          if (r > bestRatio) {
            bestRatio = r;
            best = i;
          }
        });
        setActive(best);
      },
      {
        // Centre-biased: only count the middle band of the viewport.
        rootMargin: "-40% 0px -40% 0px",
        threshold: [0, 0.25, 0.5, 0.75, 1],
      }
    );
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, []);

  return (
    <section
      id="how-it-works"
      className="relative bg-bg-base py-24 sm:py-28"
    >
      <div className="mx-auto w-full max-w-6xl px-6">
        <SectionHeader
          eyebrow="How it works"
          title={
            <>
              One watch loop.{" "}
              <span className="text-gradient">Four deliberate stages.</span>
            </>
          }
          body="From raw log line to draft report — and a Slack / Discord / Telegram ping — is usually under 30 seconds."
        />

        <div className="relative mt-14 grid grid-cols-1 gap-10 lg:grid-cols-[1fr_auto] lg:gap-16">
          {/* Steps — one block per stage. */}
          <div className="space-y-16 sm:space-y-20">
            {PIPELINE_STEPS.map((step, i) => {
              const Icon = ICONS[i];
              const isActive = i === active;
              return (
                <div
                  key={step.title}
                  ref={(el) => {
                    stepRefs.current[i] = el;
                  }}
                  className={cn(
                    "grid grid-cols-1 items-center gap-8 transition-opacity duration-300 sm:grid-cols-[120px_1fr]",
                    isActive ? "opacity-100" : "opacity-60"
                  )}
                >
                  <div className="relative mx-auto h-28 w-28 sm:mx-0">
                    <div className="absolute inset-0 rounded-3xl border border-border bg-bg-raised/70" />
                    <div
                      className={cn(
                        "absolute inset-0 rounded-3xl bg-accent/15 blur-2xl transition-opacity duration-300",
                        isActive ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="relative flex h-full w-full items-center justify-center rounded-3xl border border-accent/40 bg-accent/8 text-accent">
                      <Icon size={42} strokeWidth={1.5} />
                    </div>
                    <div className="absolute -right-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-bg-base text-xs font-semibold text-fg">
                      0{i + 1}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-dim">
                      {step.tag}
                    </div>
                    <h3 className="mt-2 text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
                      {step.title}
                    </h3>
                    <p className="mt-4 max-w-xl text-base leading-relaxed text-fg-muted">
                      {step.body}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Sticky step rail — much cheaper than the old pinned 400vh stage. */}
          <div className="sticky top-32 hidden h-fit flex-col items-start gap-3 lg:flex">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.title} className="flex items-center gap-3">
                <span
                  className={cn(
                    "relative flex h-6 w-6 items-center justify-center rounded-full border transition-colors duration-300",
                    i === active
                      ? "border-accent text-accent"
                      : "border-border text-fg-dim"
                  )}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full transition",
                      i === active ? "bg-accent" : "bg-fg-dim/60"
                    )}
                  />
                </span>
                <span
                  className={cn(
                    "text-xs font-medium transition",
                    i === active ? "text-fg" : "text-fg-dim"
                  )}
                >
                  {step.title}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
