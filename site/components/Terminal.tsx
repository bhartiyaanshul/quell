"use client";

import { useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const COMMAND = "npx frisk ./my-startup-app";

interface Line {
  text: string;
  className: string;
  delay: number;
}

const OUTPUT_LINES: Line[] = [
  { text: "", className: "", delay: 0 },
  { text: "  \u27C1 frisk v0.1.0", className: "text-cyan-400 font-bold", delay: 200 },
  { text: "  Catch the security bugs in your vibe-coded app", className: "text-slate-500", delay: 350 },
  { text: "  before someone else does.", className: "text-slate-500", delay: 450 },
  { text: "", className: "", delay: 550 },
  { text: "  Target: ./my-startup-app", className: "text-slate-300", delay: 700 },
  { text: "", className: "", delay: 800 },
  { text: "  \u2713 git repository detected", className: "text-emerald-400", delay: 950 },
  { text: "  \u2713 semgrep available", className: "text-emerald-400", delay: 1150 },
  { text: "  \u2713 gitleaks available", className: "text-emerald-400", delay: 1350 },
  { text: "", className: "", delay: 1500 },
  { text: "  \u2714 Found 142 scannable files", className: "text-emerald-400 font-semibold", delay: 1700 },
  { text: "", className: "", delay: 1850 },
  { text: "  \u26A0 Semgrep: 5 findings", className: "text-amber-400", delay: 2050 },
  { text: "  \u26A0 gitleaks: 3 findings", className: "text-amber-400", delay: 2250 },
  { text: "  \u26A0 Custom Rules: 14 findings", className: "text-amber-400", delay: 2450 },
  { text: "", className: "", delay: 2600 },
  { text: "  Security Score: 12/100", className: "text-red-400 font-bold text-base", delay: 2850 },
  { text: "", className: "", delay: 3000 },
  { text: "SEVERITY_LINE", className: "__severity__", delay: 3200 },
  { text: "", className: "", delay: 3400 },
  { text: "  \u2713 Report written to frisk-report.html", className: "text-emerald-400", delay: 3600 },
];

export default function Terminal() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  const [typedChars, setTypedChars] = useState(0);
  const [commandDone, setCommandDone] = useState(false);
  const [visibleLines, setVisibleLines] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setTypedChars(i);
      if (i >= COMMAND.length) {
        clearInterval(interval);
        setTimeout(() => setCommandDone(true), 400);
      }
    }, 35);
    return () => clearInterval(interval);
  }, [isInView]);

  useEffect(() => {
    if (!commandDone) return;
    const timeouts = OUTPUT_LINES.map((_, i) =>
      setTimeout(() => setVisibleLines(i + 1), OUTPUT_LINES[i]!.delay)
    );
    return () => timeouts.forEach(clearTimeout);
  }, [commandDone]);

  return (
    <div
      ref={ref}
      className="rounded-2xl border border-slate-800 bg-[#0f172a] overflow-hidden shadow-2xl shadow-slate-900/30"
    >
      {/* Chrome bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <span className="ml-3 text-[11px] text-slate-500 font-mono tracking-wide">
          Terminal &mdash; frisk
        </span>
      </div>

      {/* Body */}
      <div className="p-5 md:p-6 font-mono text-[13px] leading-relaxed min-h-[420px] select-text">
        <div className="flex">
          <span className="text-emerald-400 mr-2">$</span>
          <span className="text-slate-200">{COMMAND.slice(0, typedChars)}</span>
          {!commandDone && (
            <span className="cursor-blink text-emerald-400 ml-px">&#9608;</span>
          )}
        </div>

        {OUTPUT_LINES.slice(0, visibleLines).map((line, i) => {
          if (line.className === "__severity__") {
            return (
              <div key={i} className="flex flex-wrap items-center gap-1.5 ml-2 mt-px">
                <span className="px-1.5 py-px rounded bg-red-500/15 text-red-400 font-bold text-[11px] border border-red-500/20">
                  CRITICAL
                </span>
                <span className="text-slate-400 text-xs">4</span>
                <span className="text-slate-600 mx-0.5">&middot;</span>
                <span className="text-orange-400 font-semibold text-[11px]">HIGH</span>
                <span className="text-slate-400 text-xs">9</span>
                <span className="text-slate-600 mx-0.5">&middot;</span>
                <span className="text-amber-400 text-[11px]">MEDIUM</span>
                <span className="text-slate-400 text-xs">7</span>
                <span className="text-slate-600 mx-0.5">&middot;</span>
                <span className="text-blue-400 text-[11px]">LOW</span>
                <span className="text-slate-400 text-xs">2</span>
              </div>
            );
          }
          if (!line.text) return <div key={i} className="h-5" />;
          return (
            <div key={i} className={line.className}>
              {line.text}
            </div>
          );
        })}
      </div>
    </div>
  );
}
