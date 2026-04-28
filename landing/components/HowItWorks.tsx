"use client";

import { useRef, useState } from "react";
import { Activity, Bot, FileCheck2, Siren } from "lucide-react";

import { SectionHeader } from "@/components/SectionHeader";
import { TextScramble } from "@/components/TextScramble";
import { useGsap, gsap, ScrollTrigger } from "@/lib/gsap";
import { PIPELINE_STEPS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICONS = [Activity, Siren, Bot, FileCheck2] as const;

/**
 * Scroll-driven 4-slide pipeline. Outer section is 400vh; the inner
 * stage is sticky and crossfades between PIPELINE_STEPS slides as
 * scroll progress goes 0 → 1.
 */
export function HowItWorks() {
  const sectionRef = useRef<HTMLElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const slidesRef = useRef<(HTMLDivElement | null)[]>([]);
  const dotsRef = useRef<(HTMLSpanElement | null)[]>([]);
  const [active, setActive] = useState(0);

  useGsap(
    () => {
      const section = sectionRef.current;
      const slides = slidesRef.current.filter(Boolean) as HTMLDivElement[];
      if (!section || slides.length === 0) return;

      // Initial state — only first slide visible.
      slides.forEach((s, i) => {
        s.style.opacity = i === 0 ? "1" : "0";
        s.style.transform = `translate3d(0, ${i === 0 ? 0 : 24}px, 0)`;
        s.style.transition = "opacity 350ms ease, transform 350ms ease";
        s.style.willChange = "opacity, transform";
      });

      const trigger = ScrollTrigger.create({
        trigger: section,
        start: "top top",
        end: "bottom bottom",
        scrub: true,
        onUpdate: (self) => {
          const idx = Math.min(
            slides.length - 1,
            Math.floor(self.progress * slides.length)
          );
          setActive(idx);
          slides.forEach((s, i) => {
            const isActive = i === idx;
            s.style.opacity = isActive ? "1" : "0";
            s.style.transform = `translate3d(0, ${
              isActive ? 0 : i < idx ? -24 : 24
            }px, 0)`;
            s.style.pointerEvents = isActive ? "auto" : "none";
          });
        },
      });

      return () => {
        trigger.kill();
      };
    },
    sectionRef,
    []
  );

  return (
    <section
      ref={sectionRef}
      id="how-it-works"
      className="relative bg-bg-base"
      style={{ height: `${PIPELINE_STEPS.length * 100}vh` }}
    >
      <div
        ref={stageRef}
        className="sticky top-0 flex h-screen w-full items-center"
      >
        <div className="relative mx-auto w-full max-w-6xl px-6">
          <SectionHeader
            eyebrow="How it works"
            title={
              <>
                One watch loop.{" "}
                <span className="text-gradient">Four deliberate stages.</span>
              </>
            }
            body="Scroll to step through. From raw log line to draft report — and a Slack / Discord / Telegram ping — is usually under 30 seconds."
          />

          <div className="relative mt-14 grid grid-cols-1 items-center gap-10 lg:grid-cols-[1fr_auto] lg:gap-16">
            {/* Slide stage */}
            <div className="relative h-[360px] sm:h-[320px]">
              {PIPELINE_STEPS.map((step, i) => {
                const Icon = ICONS[i];
                return (
                  <div
                    key={step.title}
                    ref={(el) => {
                      slidesRef.current[i] = el;
                    }}
                    className="absolute inset-0"
                  >
                    <div className="grid h-full grid-cols-1 items-center gap-8 sm:grid-cols-[120px_1fr]">
                      {/* Big icon */}
                      <div className="relative mx-auto h-28 w-28 sm:mx-0">
                        <div className="absolute inset-0 rounded-3xl border border-border bg-bg-raised/70 backdrop-blur" />
                        <div className="absolute inset-0 rounded-3xl bg-accent/15 blur-2xl" />
                        <div className="relative flex h-full w-full items-center justify-center rounded-3xl border border-accent/40 bg-accent/8 text-accent">
                          <Icon size={42} strokeWidth={1.5} />
                        </div>
                        <div className="absolute -right-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-bg-base text-xs font-semibold text-fg">
                          0{i + 1}
                        </div>
                      </div>
                      {/* Copy */}
                      <div>
                        <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-dim">
                          {step.tag}
                        </div>
                        <h3 className="mt-2 text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
                          <TextScramble
                            text={step.title}
                            trigger="inView"
                            duration={1100}
                          />
                        </h3>
                        <p className="mt-4 max-w-xl text-base leading-relaxed text-fg-muted">
                          {step.body}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Vertical step dots */}
            <div className="flex flex-row items-center justify-center gap-3 lg:flex-col">
              {PIPELINE_STEPS.map((step, i) => (
                <div key={step.title} className="group flex items-center gap-3">
                  <span
                    ref={(el) => {
                      dotsRef.current[i] = el;
                    }}
                    className={cn(
                      "relative flex h-6 w-6 items-center justify-center rounded-full border transition-colors duration-300",
                      i === active
                        ? "border-accent text-accent"
                        : "border-border text-fg-dim"
                    )}
                  >
                    {i === active && (
                      <span className="absolute inset-0 animate-spin-slow rounded-full border border-dashed border-accent/60" />
                    )}
                    <span
                      className={cn(
                        "h-1.5 w-1.5 rounded-full transition",
                        i === active ? "bg-accent" : "bg-fg-dim/60"
                      )}
                    />
                  </span>
                  <span
                    className={cn(
                      "hidden text-xs font-medium transition lg:inline",
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
      </div>
    </section>
  );
}
