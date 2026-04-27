"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

import { ErrorCard } from "@/components/ErrorCard";
import { api, type Stats } from "@/lib/api";

function formatMttr(seconds: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return <ErrorCard title="Could not load stats" body={error} />;
  }
  if (stats === null) {
    return <div className="h-40 animate-pulse rounded-2xl border border-border bg-bg-raised/30" />;
  }

  const cards = [
    { label: "Total incidents", value: stats.total, accent: "cool" },
    { label: "Detected", value: stats.by_status.detected, accent: "warn" },
    { label: "Investigating", value: stats.by_status.investigating, accent: "accent" },
    { label: "Resolved", value: stats.by_status.resolved, accent: "ok" },
    { label: "MTTR", value: formatMttr(stats.mttr_seconds), accent: "cool" },
  ] as const;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Stats</h1>
        <p className="mt-1 text-sm text-fg-muted">
          Aggregate counters across every incident this Quell install has seen.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {cards.map((c, i) => (
          <motion.div
            key={c.label}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-2xl border border-border bg-bg-raised/50 p-4"
          >
            <div className="text-[11px] uppercase tracking-wider text-fg-dim">
              {c.label}
            </div>
            <div className="mt-2 text-3xl font-semibold tracking-tight text-fg">
              {c.value}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-bg-raised/40 p-6">
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Top signatures</h2>
          <span className="text-xs text-fg-dim">
            {stats.top_signatures.length} tracked
          </span>
        </div>
        {stats.top_signatures.length === 0 ? (
          <p className="text-sm text-fg-muted">No recurring signatures yet.</p>
        ) : (
          <ol className="space-y-2">
            {stats.top_signatures.map((t) => (
              <li
                key={t.signature}
                className="flex items-center justify-between rounded-xl border border-border bg-bg-base/60 px-3 py-2 font-mono text-xs"
              >
                <span className="truncate text-fg-muted">{t.signature}</span>
                <span className="text-accent">×{t.count}</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
