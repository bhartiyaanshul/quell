"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import { TERMINAL_LINES } from "@/lib/constants";

/**
 * Live terminal demo in the hero.
 *
 * The first line is typed character-by-character; subsequent lines
 * appear one-by-one with a 750 ms stagger.  The whole sequence loops
 * with a pause at the end so the terminal feels like a persistent
 * process, not a one-shot animation.
 *
 * The animation pauses when the demo is offscreen so it doesn't burn
 * timers further down the page.
 */
export function TerminalDemo() {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [typedCmd, setTypedCmd] = useState("");
  const [visibleLines, setVisibleLines] = useState(1);
  const [cycle, setCycle] = useState(0);
  const [active, setActive] = useState(false);

  const FIRST = TERMINAL_LINES[0];
  const TOTAL = TERMINAL_LINES.length;

  // Pause the loop while offscreen.
  useEffect(() => {
    const node = wrapRef.current;
    if (!node) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) setActive(entry.isIntersecting);
      },
      { threshold: 0 }
    );
    io.observe(node);
    return () => io.disconnect();
  }, []);

  // Type the first command char-by-char.
  useEffect(() => {
    if (!active) return;
    setTypedCmd("");
    setVisibleLines(1);
    let i = 0;
    const target = FIRST.cmd ?? "";
    const id = setInterval(() => {
      i += 1;
      setTypedCmd(target.slice(0, i));
      if (i >= target.length) {
        clearInterval(id);
      }
    }, 75);
    return () => clearInterval(id);
  }, [cycle, FIRST.cmd, active]);

  // After the command is typed, reveal output lines with a stagger.
  useEffect(() => {
    if (!active) return;
    if (typedCmd.length < (FIRST.cmd ?? "").length) return;
    if (visibleLines >= TOTAL) {
      // Hold the final state, then loop.
      const id = setTimeout(() => setCycle((c) => c + 1), 4200);
      return () => clearTimeout(id);
    }
    const id = setTimeout(() => setVisibleLines((n) => n + 1), 620);
    return () => clearTimeout(id);
  }, [typedCmd, visibleLines, FIRST.cmd, TOTAL, active]);

  return (
    <motion.div
      ref={wrapRef}
      initial={{ opacity: 0, y: 30, rotate: -1 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ duration: 0.8, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative isolate"
    >
      {/* Outer glow */}
      <div
        aria-hidden
        className="absolute -inset-6 -z-10 rounded-[28px] bg-gradient-to-br from-accent/30 via-accent-glow/10 to-cool/25 blur-2xl"
      />

      <div className="overflow-hidden rounded-2xl border border-border bg-bg-raised/85 shadow-2xl backdrop-blur noise-overlay">
        {/* Title bar */}
        <div className="flex items-center gap-2 border-b border-border bg-bg-subtle/60 px-4 py-3">
          <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <span className="h-3 w-3 rounded-full bg-[#28c840]" />
          <span className="ml-3 font-mono text-xs text-fg-dim">
            ~/src/my-app — quell watch
          </span>
        </div>

        {/* Body — min-height keeps the terminal the right size even
             before output has filled in, but we don't force-clip so
             wrapped lines on narrow viewports stay readable. */}
        <div className="min-h-[360px] px-5 py-4 font-mono text-[13px] leading-relaxed sm:min-h-[400px]">
          {/* The typed command */}
          <div className="flex items-start gap-2">
            <span className="select-none text-accent">➜</span>
            <span className="select-none text-cool">
              {FIRST.prompt}
            </span>
            <span className="text-fg">
              {typedCmd}
              <motion.span
                aria-hidden
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="ml-0.5 inline-block h-[14px] w-[7px] translate-y-0.5 bg-accent"
              />
            </span>
          </div>

          {/* Output lines */}
          <div className="mt-2 space-y-1">
            <AnimatePresence initial={false}>
              {TERMINAL_LINES.slice(1, visibleLines).map((line, idx) => (
                <motion.div
                  key={`${cycle}-${idx}`}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.28 }}
                  className={logLineClass(line.output)}
                >
                  {line.output}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function logLineClass(text: string | null | undefined): string {
  if (!text) return "text-fg-muted";
  if (text.startsWith("\u2713")) return "text-emerald-400";
  if (text.includes("ERROR")) return "text-accent";
  if (text.includes("tool:")) return "text-cool-hi";
  if (text.includes("detector:")) return "text-amber-300";
  if (text.includes("commander:")) return "text-sky-300";
  return "text-fg-muted";
}
