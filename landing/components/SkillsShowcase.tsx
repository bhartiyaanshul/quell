"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Boxes,
  CreditCard,
  Database,
  HardDrive,
  Lock,
  Zap,
  type LucideIcon,
} from "lucide-react";

import { SectionHeader } from "@/components/SectionHeader";
import { SKILLS_SHOWCASE } from "@/lib/constants";
import { cn } from "@/lib/utils";

type Skill = (typeof SKILLS_SHOWCASE)[number];
type Frame = "terminal" | "analysis" | "diff";
const FRAME_ORDER: readonly Frame[] = ["terminal", "analysis", "diff"];

const ICONS: Record<string, LucideIcon> = {
  database: Database,
  "credit-card": CreditCard,
  "hard-drive": HardDrive,
  lock: Lock,
  boxes: Boxes,
  zap: Zap,
};

/** Tailwind-safe accent map. Keys must match `accent` values in constants. */
const ACCENT: Record<
  string,
  {
    text: string;
    bg: string;
    border: string;
    glow: string;
    chipBg: string;
    chipText: string;
    diff: string;
  }
> = {
  sky: {
    text: "text-sky-300",
    bg: "bg-sky-400/10",
    border: "border-sky-400/30",
    glow: "from-sky-400/25",
    chipBg: "bg-sky-400/15",
    chipText: "text-sky-200",
    diff: "bg-sky-400",
  },
  violet: {
    text: "text-violet-300",
    bg: "bg-violet-400/10",
    border: "border-violet-400/30",
    glow: "from-violet-400/25",
    chipBg: "bg-violet-400/15",
    chipText: "text-violet-200",
    diff: "bg-violet-400",
  },
  rose: {
    text: "text-rose-300",
    bg: "bg-rose-400/10",
    border: "border-rose-400/30",
    glow: "from-rose-400/25",
    chipBg: "bg-rose-400/15",
    chipText: "text-rose-200",
    diff: "bg-rose-400",
  },
  emerald: {
    text: "text-emerald-300",
    bg: "bg-emerald-400/10",
    border: "border-emerald-400/30",
    glow: "from-emerald-400/25",
    chipBg: "bg-emerald-400/15",
    chipText: "text-emerald-200",
    diff: "bg-emerald-400",
  },
  amber: {
    text: "text-amber-300",
    bg: "bg-amber-400/10",
    border: "border-amber-400/30",
    glow: "from-amber-400/25",
    chipBg: "bg-amber-400/15",
    chipText: "text-amber-200",
    diff: "bg-amber-400",
  },
  lime: {
    text: "text-lime-300",
    bg: "bg-lime-400/10",
    border: "border-lime-400/30",
    glow: "from-lime-400/25",
    chipBg: "bg-lime-400/15",
    chipText: "text-lime-200",
    diff: "bg-lime-400",
  },
};

export function SkillsShowcase() {
  return (
    <section id="skills" className="relative bg-bg-base py-32 md:py-44">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-border-bright/40 to-transparent"
      />

      <div className="mx-auto max-w-6xl px-6">
        <SectionHeader
          eyebrow="Skills"
          title={
            <>
              Built-in runbooks. Auto-injected when{" "}
              <span className="text-gradient">triggers match.</span>
            </>
          }
          body="Each skill is a markdown + YAML runbook. The detector matches an incident's signature against trigger globs; matched skills are appended to the agent's system prompt for that investigation."
        />

        <div className="mt-16 grid grid-cols-1 gap-7 md:grid-cols-2">
          {SKILLS_SHOWCASE.map((skill, i) => (
            <SkillCard key={skill.id} skill={skill} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function SkillCard({ skill, index }: { skill: Skill; index: number }) {
  const [active, setActive] = useState<Frame>("terminal");
  const [hovered, setHovered] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!hovered) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
      setActive("terminal");
      return;
    }
    intervalRef.current = setInterval(() => {
      setActive((prev) => {
        const i = FRAME_ORDER.indexOf(prev);
        return FRAME_ORDER[(i + 1) % FRAME_ORDER.length];
      });
    }, 1500);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [hovered]);

  const accent = ACCENT[skill.accent] ?? ACCENT.sky;
  const Icon = ICONS[skill.icon] ?? Database;

  return (
    <motion.article
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.55, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group relative overflow-hidden rounded-2xl border border-border bg-bg-raised/60 transition-colors duration-500 hover:border-border-bright"
    >
      {/* Preview area — three frames, only the active one shown. Each card
          has its own accent colour so adjacent cards don't visually blur
          together the way the old image-based mocks did. */}
      <div className="relative aspect-[3/2] w-full overflow-hidden bg-[#0d0d14]">
        {/* Per-skill glow — discrete child so Tailwind picks up the class. */}
        <div
          aria-hidden
          className={cn(
            "pointer-events-none absolute inset-0 bg-gradient-to-br to-transparent opacity-60",
            accent.glow
          )}
        />
        {/* Top accent stripe — instant per-skill identity. */}
        <div
          aria-hidden
          className={cn("absolute inset-x-0 top-0 h-[3px]", accent.diff)}
        />

        {/* Skill icon + label chip — top-left, distinct per skill. */}
        <div className="absolute left-4 top-4 z-10 flex items-center gap-2">
          <span
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg border",
              accent.border,
              accent.bg,
              accent.text
            )}
          >
            <Icon size={16} strokeWidth={1.75} />
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider",
              accent.chipBg,
              accent.chipText
            )}
          >
            {active === "terminal"
              ? "TTY"
              : active === "analysis"
              ? "AGENT"
              : "DIFF"}
          </span>
        </div>

        {/* Frame */}
        <div className="absolute inset-0 flex items-center px-4 pb-12 pt-14 sm:px-6">
          {active === "terminal" && (
            <TerminalFrame skill={skill} accent={accent} />
          )}
          {active === "analysis" && (
            <AnalysisFrame skill={skill} accent={accent} />
          )}
          {active === "diff" && <DiffFrame skill={skill} accent={accent} />}
        </div>

        {/* Slide indicator */}
        <div className="absolute bottom-3 left-4 flex gap-1.5">
          {FRAME_ORDER.map((f) => (
            <span
              key={f}
              className={cn(
                "h-1 w-6 rounded-full transition-colors duration-300",
                f === active ? accent.diff : "bg-fg/15"
              )}
            />
          ))}
        </div>

        <span
          aria-hidden
          className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-bg-base/70 text-fg opacity-0 backdrop-blur transition-all duration-500 group-hover:opacity-100"
        >
          <ArrowUpRight size={16} />
        </span>
      </div>

      <div className="p-5">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-base font-semibold text-fg">
            {skill.title}
          </h3>
          <span className="text-xs text-fg-dim">{skill.year}</span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-fg-muted">
          {skill.description}
        </p>
        <div className="mt-4 flex flex-wrap gap-1.5">
          {skill.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-border bg-bg-base/60 px-2.5 py-0.5 text-[11px] font-medium text-fg-dim"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </motion.article>
  );
}

/* ─── Frame variants ───────────────────────────────────────────── */

type AccentTheme = (typeof ACCENT)[keyof typeof ACCENT];

function TerminalFrame({
  skill,
  accent,
}: {
  skill: Skill;
  accent: AccentTheme;
}) {
  const t = skill.frames.terminal;
  return (
    <div className="w-full font-mono text-[11px] leading-relaxed sm:text-[12px]">
      <div className="mb-1.5 flex items-center gap-1.5 text-fg-dim">
        <span className={accent.text}>$</span>
        <span className="truncate text-fg/80">{t.cmd}</span>
      </div>
      <div className="space-y-1">
        {t.lines.map((line, i) => (
          <div
            key={i}
            className={cn(
              "truncate",
              line.kind === "err"
                ? "text-rose-300"
                : line.kind === "warn"
                ? "text-amber-300"
                : line.kind === "info"
                ? accent.text
                : "text-fg-dim"
            )}
          >
            {line.text}
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalysisFrame({
  skill,
  accent,
}: {
  skill: Skill;
  accent: AccentTheme;
}) {
  const a = skill.frames.analysis;
  return (
    <div className="w-full">
      <div
        className={cn(
          "mb-3 inline-flex items-center gap-2 rounded-md border px-2 py-1 font-mono text-[10px] uppercase tracking-wider",
          accent.border,
          accent.bg,
          accent.text
        )}
      >
        <span
          className={cn("inline-block h-1.5 w-1.5 rounded-full", accent.diff)}
        />
        {a.title}
      </div>
      <ul className="space-y-1.5 font-mono text-[11px] leading-relaxed sm:text-[12px]">
        {a.bullets.map((b, i) => {
          const isConclusion = b.startsWith("→");
          return (
            <li
              key={i}
              className={cn(
                "flex gap-2",
                isConclusion ? accent.text : "text-fg/85"
              )}
            >
              {!isConclusion && (
                <span className="mt-1 inline-block h-1 w-1 shrink-0 rounded-full bg-fg-dim" />
              )}
              <span className="truncate">{b}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function DiffFrame({ skill, accent }: { skill: Skill; accent: AccentTheme }) {
  const d = skill.frames.diff;
  return (
    <div className="w-full">
      <div className="mb-2 flex items-center gap-2 font-mono text-[10px] text-fg-dim">
        <span className={cn("inline-block h-1.5 w-1.5 rounded-full", accent.diff)} />
        <span className="truncate">{d.file}</span>
      </div>
      <div className="space-y-0.5 font-mono text-[11px] leading-relaxed sm:text-[12px]">
        {d.lines.map((line, i) => {
          const isAdd = line.kind === "add";
          return (
            <div
              key={i}
              className={cn(
                "flex gap-2 truncate rounded-sm px-1",
                isAdd
                  ? "bg-emerald-400/10 text-emerald-200"
                  : "bg-rose-400/10 text-rose-200"
              )}
            >
              <span className="w-3 shrink-0 select-none opacity-70">
                {isAdd ? "+" : "−"}
              </span>
              <span className="truncate">{line.text}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
