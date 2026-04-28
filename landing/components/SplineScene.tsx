"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";

type Props = {
  className?: string;
  parallax?: number;
};

/**
 * Hero stage — three floating glass panels arranged in 3D, one per
 * stage of a Quell investigation: terminal log, agent thought, draft
 * PR diff. Mouse parallax tilts the whole rig; each panel has its own
 * slow drift. The content is real Quell output (not lorem) so the
 * scene communicates what the product actually does the moment a
 * visitor lands.
 *
 * Pure HTML + CSS 3D transforms — no Three.js for this one. Text is
 * crisp at every zoom level and the cards inherit the site's design
 * tokens.
 */
export function SplineScene({ className, parallax = 0.05 }: Props) {
  const stageRef = useRef<HTMLDivElement | null>(null);

  // Mouse parallax — tilts the stage on a perspective container.
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    let raf = 0;
    let targetX = 0;
    let targetY = 0;
    let curX = 0;
    let curY = 0;

    const onMove = (e: MouseEvent) => {
      const rect = stage.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      targetX = ((e.clientX - cx) / rect.width) * parallax * 16;
      targetY = ((e.clientY - cy) / rect.height) * parallax * 16;
    };

    const tick = () => {
      curX += (targetX - curX) * 0.06;
      curY += (targetY - curY) * 0.06;
      stage.style.transform = `rotateY(${(-curX).toFixed(
        3
      )}deg) rotateX(${curY.toFixed(3)}deg)`;
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("mousemove", onMove);
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
    };
  }, [parallax]);

  return (
    <div
      className={`relative h-full w-full ${className ?? ""}`}
      style={{ perspective: "1600px", perspectiveOrigin: "50% 50%" }}
    >
      <div
        ref={stageRef}
        className="relative h-full w-full"
        style={{
          transformStyle: "preserve-3d",
          willChange: "transform",
          transition: "transform 60ms linear",
        }}
      >
        {/* Behind-left — agent thought (peeks from top-left) */}
        <FloatingPanel
          className="left-0 top-0 w-[52%]"
          depth={-70}
          rotateY={14}
          rotateX={2}
          drift={{ y: [-6, 8, -6], duration: 11, delay: 0.6 }}
          tone="cool"
          enterDelay={0.55}
        >
          <PanelHeader title="agent ▸ analyse_deadlock_graph" tag="THINK" tone="cool" />
          <PanelBody>
            <ThoughtLine label="hypothesis">
              Two txns blocking each other.
            </ThoughtLine>
            <Mono dim className="mt-1.5">
              · txn 4218 → row id=$1
              <br />· txn 4219 → row id=$2
            </Mono>
            <Mono accent="green" className="mt-2.5">
              → sort ids before UPDATE
              <br />→ retry-with-backoff
            </Mono>
          </PanelBody>
        </FloatingPanel>

        {/* Behind-right — PR diff (peeks from bottom-right) */}
        <FloatingPanel
          className="right-0 bottom-0 w-[54%]"
          depth={-50}
          rotateY={-13}
          rotateX={-2}
          drift={{ y: [6, -8, 6], duration: 13, delay: 1.2 }}
          tone="green"
          enterDelay={0.85}
        >
          <PanelHeader title="PR ▸ draft #882" tag="FIX" tone="green" />
          <PanelBody>
            <Mono dim>orders_repo.py @@ -42,5 +42,7 @@</Mono>
            <DiffLine kind="-">  for oid in ids:</DiffLine>
            <DiffLine kind="+">  for oid in sorted(ids):</DiffLine>
            <DiffLine kind="+">    for attempt in range(3):</DiffLine>
            <DiffLine kind="+">      try: run(oid)</DiffLine>
            <DiffLine kind="+">      except DeadlockDetected:</DiffLine>
            <DiffLine kind="+">        backoff(attempt)</DiffLine>
          </PanelBody>
        </FloatingPanel>

        {/* Front — terminal (centerpiece, on top) */}
        <FloatingPanel
          className="left-1/2 top-1/2 w-[68%]"
          depth={90}
          rotateY={-3}
          rotateX={1}
          drift={{ y: [-4, 4, -4], duration: 9, delay: 0 }}
          tone="ember"
          highlight
          center
          enterDelay={0.25}
        >
          <PanelHeader title="~/my-app — quell watch" mac />
          <PanelBody dense>
            <Term prompt color="ember">quell watch</Term>
            <Term color="muted">10:02:45 INFO  monitor: tailing error.log</Term>
            <Term color="red">10:02:47 ERROR TypeError: read of null</Term>
            <Term color="muted">10:02:47 INFO  detector: signature 7a9e42f8</Term>
            <Term color="cool">10:02:47 INFO  commander: spawning agent</Term>
            <Term color="muted">10:02:49 INFO  tool: code_read checkout.ts:42</Term>
            <Term color="green">✓ inc_a1b2c3 resolved in 13s — PR #882</Term>
            <ThinkingDot />
          </PanelBody>
        </FloatingPanel>

        {/* Ambient connector — thin glowing line from terminal corner
            toward the agent panel; hints at the data flow between cards. */}
        <Connector />
      </div>
    </div>
  );
}

/* ─── Floating glass panel ─────────────────────────────────────────── */

function FloatingPanel({
  children,
  className,
  depth,
  rotateY,
  rotateX,
  drift,
  tone = "ember",
  highlight = false,
  center = false,
  enterDelay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  depth: number;
  rotateY: number;
  rotateX: number;
  drift: { y: number[]; duration: number; delay: number };
  tone?: "ember" | "cool" | "green";
  highlight?: boolean;
  /** Apply -50%/-50% offset so absolute left/top values position centre. */
  center?: boolean;
  enterDelay?: number;
}) {
  const ringByTone = {
    ember:
      "shadow-[0_30px_70px_-30px_rgba(251,146,60,0.45),0_0_0_1px_rgba(251,146,60,0.18)_inset]",
    cool:
      "shadow-[0_30px_70px_-30px_rgba(167,139,250,0.45),0_0_0_1px_rgba(167,139,250,0.18)_inset]",
    green:
      "shadow-[0_30px_70px_-30px_rgba(134,239,172,0.4),0_0_0_1px_rgba(134,239,172,0.15)_inset]",
  } as const;

  return (
    <div
      className={`absolute ${highlight ? "z-10" : ""} ${className ?? ""}`}
      style={{
        transform: `translate3d(${center ? "-50%" : "0"}, ${
          center ? "-50%" : "0"
        }, ${depth}px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
        transformStyle: "preserve-3d",
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1, y: drift.y }}
        transition={{
          opacity: { duration: 0.9, delay: enterDelay, ease: [0.22, 1, 0.36, 1] },
          scale: { duration: 0.9, delay: enterDelay, ease: [0.22, 1, 0.36, 1] },
          y: {
            duration: drift.duration,
            delay: drift.delay,
            ease: "easeInOut",
            repeat: Infinity,
          },
        }}
        className={`overflow-hidden rounded-2xl border border-border bg-bg-raised/55 backdrop-blur-2xl ${ringByTone[tone]}`}
      >
        {children}
      </motion.div>
    </div>
  );
}

/* ─── Header / body / content primitives ───────────────────────────── */

function PanelHeader({
  title,
  tag,
  tone = "ember",
  mac = false,
}: {
  title: string;
  tag?: string;
  tone?: "ember" | "cool" | "green";
  mac?: boolean;
}) {
  const tagColor =
    tone === "cool"
      ? "border-cool/40 bg-cool/10 text-cool"
      : tone === "green"
      ? "border-green-300/30 bg-green-300/10 text-green-300"
      : "border-accent/40 bg-accent/10 text-accent";
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/60 bg-bg-base/40 px-3.5 py-2.5">
      <div className="flex items-center gap-2.5">
        {mac && (
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-border-bright" />
            <span className="h-2.5 w-2.5 rounded-full bg-border-bright" />
            <span className="h-2.5 w-2.5 rounded-full bg-border-bright" />
          </div>
        )}
        <span className="truncate font-mono text-[10.5px] text-fg-dim">
          {title}
        </span>
      </div>
      {tag && (
        <span
          className={`shrink-0 rounded-full border px-1.5 py-0.5 font-mono text-[9px] tracking-wider ${tagColor}`}
        >
          {tag}
        </span>
      )}
    </div>
  );
}

function PanelBody({
  children,
  dense = false,
}: {
  children: React.ReactNode;
  dense?: boolean;
}) {
  return (
    <div
      className={`font-mono text-[11px] leading-relaxed text-fg ${
        dense ? "px-3.5 py-3" : "px-3.5 py-3.5"
      }`}
    >
      {children}
    </div>
  );
}

function Term({
  children,
  prompt = false,
  color = "fg",
}: {
  children: React.ReactNode;
  prompt?: boolean;
  color?: "fg" | "muted" | "ember" | "cool" | "green" | "red";
}) {
  const colorMap: Record<string, string> = {
    fg: "text-fg",
    muted: "text-fg-muted",
    ember: "text-accent",
    cool: "text-cool",
    green: "text-green-300",
    red: "text-red-300",
  };
  return (
    <div className={`whitespace-nowrap ${colorMap[color]}`}>
      {prompt && <span className="mr-1.5 text-accent">$</span>}
      {children}
    </div>
  );
}

function ThinkingDot() {
  return (
    <div className="mt-1.5 inline-flex h-3 items-center">
      <span className="relative inline-block h-2 w-2">
        <span className="absolute inset-0 animate-ping rounded-full bg-accent/40" />
        <span className="absolute inset-[3px] rounded-full bg-accent" />
      </span>
    </div>
  );
}

function ThoughtLine({
  children,
  label,
  className,
}: {
  children: React.ReactNode;
  label: string;
  className?: string;
}) {
  return (
    <div className={`flex gap-2 ${className ?? ""}`}>
      <span className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-cool">
        {label}
      </span>
      <span className="text-fg">{children}</span>
    </div>
  );
}

function Mono({
  children,
  dim = false,
  accent,
  className,
}: {
  children: React.ReactNode;
  dim?: boolean;
  accent?: "green" | "ember";
  className?: string;
}) {
  const color =
    accent === "green"
      ? "text-green-300"
      : accent === "ember"
      ? "text-accent"
      : dim
      ? "text-fg-dim"
      : "text-fg-muted";
  return (
    <pre
      className={`whitespace-pre-wrap font-mono text-[10.5px] leading-relaxed ${color} ${
        className ?? ""
      }`}
    >
      {children}
    </pre>
  );
}

function DiffLine({
  kind,
  children,
}: {
  kind: " " | "+" | "-" | "@";
  children: React.ReactNode;
}) {
  const fill =
    kind === "+"
      ? "bg-green-300/[0.08]"
      : kind === "-"
      ? "bg-red-300/[0.08]"
      : "";
  const sign =
    kind === "+"
      ? "text-green-300"
      : kind === "-"
      ? "text-red-300"
      : "text-fg-dim";
  return (
    <div className={`flex gap-2 ${fill}`}>
      <span className={`w-3 shrink-0 text-center ${sign}`}>{kind}</span>
      <span className="text-fg/90">{children}</span>
    </div>
  );
}

/* ─── Ambient connector line between cards (purely decorative) ─────── */

function Connector() {
  return (
    <svg
      aria-hidden
      className="pointer-events-none absolute inset-0 h-full w-full"
      style={{ transform: "translateZ(40px)" }}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="connector-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#fb923c" stopOpacity="0" />
          <stop offset="0.5" stopColor="#fb923c" stopOpacity="0.4" />
          <stop offset="1" stopColor="#a78bfa" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M 30 25 Q 50 50 70 80"
        stroke="url(#connector-grad)"
        strokeWidth="0.4"
        fill="none"
      />
    </svg>
  );
}
