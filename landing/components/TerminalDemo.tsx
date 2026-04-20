"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

import { TERMINAL_LINES } from "@/lib/constants";

/**
 * Live terminal demo in the hero.
 *
 * The first line is typed character-by-character; subsequent lines
 * appear one-by-one with a 750 ms stagger.  The whole sequence loops
 * with a pause at the end so the terminal feels like a persistent
 * process, not a one-shot animation.
 */
export function TerminalDemo() {
  const [typedCmd, setTypedCmd] = useState("");
  const [visibleLines, setVisibleLines] = useState(1);
  const [cycle, setCycle] = useState(0);

  const FIRST = TERMINAL_LINES[0];
  const TOTAL = TERMINAL_LINES.length;

  // Type the first command char-by-char.
  useEffect(() => {
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
  }, [cycle, FIRST.cmd]);

  // After the command is typed, reveal output lines with a stagger.
  useEffect(() => {
    if (typedCmd.length < (FIRST.cmd ?? "").length) return;
    if (visibleLines >= TOTAL) {
      // Hold the final state, then loop.
      const id = setTimeout(() => setCycle((c) => c + 1), 4200);
      return () => clearTimeout(id);
    }
    const id = setTimeout(() => setVisibleLines((n) => n + 1), 620);
    return () => clearTimeout(id);
  }, [typedCmd, visibleLines, FIRST.cmd, TOTAL]);

  return (
    <motion.div
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

        {/* Body */}
        <div className="h-[320px] overflow-hidden px-5 py-4 font-mono text-[13px] leading-relaxed">
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
