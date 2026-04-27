"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  ScrollText,
  Wrench,
} from "lucide-react";

import type { EventRow, ReplayRun } from "@/lib/api";
import { fmtCost, fmtDateTime, fmtDuration } from "@/lib/utils";

const EVENT_ICON: Record<string, typeof AlertTriangle> = {
  llm_call: Cpu,
  tool_call: Wrench,
  error: AlertTriangle,
  info: ScrollText,
};

const EVENT_COLOR: Record<string, string> = {
  llm_call: "text-cool-hi",
  tool_call: "text-accent",
  error: "text-crit",
  info: "text-fg-muted",
};

function summariseEvent(e: EventRow): string {
  const p = e.payload;
  if (e.event_type === "llm_call") {
    const model = (p.model as string) ?? "model";
    const inTok = (p.input_tokens as number) ?? 0;
    const outTok = (p.output_tokens as number) ?? 0;
    const lat = (p.latency_ms as number) ?? 0;
    return `${model} — ${inTok.toLocaleString()} in / ${outTok.toLocaleString()} out (${lat} ms)`;
  }
  if (e.event_type === "tool_call") {
    const name = (p.tool_name as string) ?? "?";
    const ok = p.ok as boolean;
    const lat = (p.latency_ms as number) ?? 0;
    return `${name} — ${ok ? "ok" : "error"} (${lat} ms)`;
  }
  if (e.event_type === "error") {
    const msg = (p.message as string) ?? (p.exc_type as string) ?? "error";
    return msg;
  }
  return JSON.stringify(p).slice(0, 120);
}

export function ReplayTimeline({ runs }: { runs: ReplayRun[] }) {
  if (runs.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-bg-raised/30 px-8 py-12 text-center text-sm text-fg-muted">
        This incident has no recorded events yet.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {runs.map((run, idx) => (
        <motion.section
          key={run.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.05 }}
          className="overflow-hidden rounded-2xl border border-border bg-bg-raised/40"
        >
          <header className="flex flex-wrap items-baseline justify-between gap-3 border-b border-border bg-bg-subtle/50 px-5 py-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-fg">{run.name}</span>
              <span className="text-xs text-fg-dim">·</span>
              <span className="font-mono text-xs text-fg-muted">{run.id}</span>
            </div>
            <div className="flex items-center gap-4 font-mono text-xs text-fg-muted">
              <span className="flex items-center gap-1">
                {run.status === "completed" ? (
                  <CheckCircle2 size={13} className="text-ok" />
                ) : run.status === "failed" ? (
                  <AlertTriangle size={13} className="text-crit" />
                ) : null}
                {run.status}
              </span>
              <span>{fmtDuration(run.started_at, run.finished_at)}</span>
              <span>{fmtCost(run.cost_usd)}</span>
            </div>
          </header>

          <ol className="relative space-y-1 px-5 py-4">
            {/* Vertical timeline rail */}
            <span className="pointer-events-none absolute left-[29px] top-4 bottom-4 w-px bg-border" />
            {run.events.map((e) => {
              const Icon = EVENT_ICON[e.event_type] ?? ScrollText;
              const colour = EVENT_COLOR[e.event_type] ?? "text-fg-muted";
              return (
                <li key={e.id} className="relative flex items-start gap-3 py-1.5">
                  <span
                    className={`relative z-10 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border border-border bg-bg-base ${colour}`}
                  >
                    <Icon size={12} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-2 font-mono text-[11px] text-fg-dim">
                      <span>{fmtDateTime(e.timestamp)}</span>
                      <span className="uppercase tracking-wide">
                        {e.event_type}
                      </span>
                    </div>
                    <div className="mt-0.5 break-words text-sm text-fg">
                      {summariseEvent(e)}
                    </div>
                  </div>
                </li>
              );
            })}
            {run.events.length === 0 && (
              <li className="py-3 text-center text-xs text-fg-dim">
                No events recorded for this run.
              </li>
            )}
          </ol>
        </motion.section>
      ))}
    </div>
  );
}
