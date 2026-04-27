"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorCard } from "@/components/ErrorCard";
import { IncidentTable } from "@/components/IncidentTable";
import { api, type Incident } from "@/lib/api";

const FILTERS = [
  { value: undefined, label: "All" },
  { value: "detected", label: "Detected" },
  { value: "investigating", label: "Investigating" },
  { value: "resolved", label: "Resolved" },
] as const;

export default function HomePage() {
  const [incidents, setIncidents] = useState<Incident[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    setIncidents(null);
    setError(null);
    api
      .listIncidents(filter)
      .then((d) => setIncidents(d.incidents))
      .catch((e) => setError(e.message));
  }, [filter]);

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="flex flex-wrap items-start justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Incidents</h1>
          <p className="mt-1 text-sm text-fg-muted">
            Every investigation Quell has recorded on this machine.
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-full border border-border bg-bg-raised/60 p-1">
          {FILTERS.map((f) => {
            const active = filter === f.value;
            return (
              <button
                key={f.label}
                onClick={() => setFilter(f.value)}
                className={`rounded-full px-3 py-1 text-xs transition ${
                  active
                    ? "bg-accent text-bg-base"
                    : "text-fg-muted hover:text-fg"
                }`}
              >
                {f.label}
              </button>
            );
          })}
        </div>
      </motion.div>

      {error ? (
        <ErrorCard
          title="Could not load incidents"
          body={`Is ${location.host} reachable? ${error}`}
        />
      ) : incidents === null ? (
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-bg-raised/30" />
      ) : incidents.length === 0 ? (
        <EmptyState
          title="No incidents yet"
          body="Run `quell watch` against a project with real log output — or use the bundled fixture — to see an investigation appear here."
        />
      ) : (
        <IncidentTable incidents={incidents} />
      )}
    </div>
  );
}
