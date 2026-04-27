"use client";

import { motion } from "framer-motion";
import { ChevronRight, ExternalLink, GitBranch } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { ErrorCard } from "@/components/ErrorCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusPill } from "@/components/StatusPill";
import {
  api,
  type Finding,
  type Incident,
  type Run,
} from "@/lib/api";
import { fmtCost, fmtDateTime, fmtDuration } from "@/lib/utils";

function IncidentDetail() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id") ?? "";
  const [data, setData] = useState<{
    incident: Incident;
    runs: Run[];
    findings: Finding[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getIncident(id).then(setData).catch((e) => setError(e.message));
  }, [id]);

  if (!id) {
    return (
      <ErrorCard
        title="Missing incident id"
        body="Visit this page from the incident table, or pass ?id=inc_xxx in the URL."
      />
    );
  }
  if (error) return <ErrorCard title="Could not load incident" body={error} />;
  if (!data)
    return (
      <div className="h-40 animate-pulse rounded-2xl border border-border bg-bg-raised/30" />
    );

  const { incident, runs, findings } = data;

  return (
    <div className="space-y-8">
      <div className="text-xs text-fg-muted">
        <Link href="/" className="hover:text-fg">
          Incidents
        </Link>
        <ChevronRight size={12} className="mx-1 inline" />
        <span className="font-mono text-fg">{incident.id}</span>
      </div>

      {/* Header card */}
      <motion.section
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="overflow-hidden rounded-2xl border border-border bg-bg-raised/50 p-6"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <SeverityBadge value={incident.severity} />
              <StatusPill value={incident.status} />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {incident.root_cause || "Investigation in progress"}
            </h1>
            <div className="font-mono text-xs text-fg-dim">
              {incident.signature}
            </div>
          </div>
          <div className="text-right text-xs text-fg-muted">
            <div>First seen {fmtDateTime(incident.first_seen)}</div>
            <div>Last seen {fmtDateTime(incident.last_seen)}</div>
            <div>Occurrences: {incident.occurrence_count}</div>
            <div>Cost: {fmtCost(incident.cost_usd)}</div>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          <Link
            href={`/replay?id=${encodeURIComponent(incident.id)}`}
            className="inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 text-sm font-medium text-bg-base transition hover:brightness-110"
          >
            View replay
            <ChevronRight size={14} />
          </Link>
          {incident.fix_pr_url && (
            <a
              href={incident.fix_pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-border bg-bg-base/60 px-4 py-2 text-sm text-fg-muted transition hover:text-fg"
            >
              <GitBranch size={14} />
              Draft PR
              <ExternalLink size={12} />
            </a>
          )}
        </div>
      </motion.section>

      {/* Runs */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Agent runs</h2>
        {runs.length === 0 ? (
          <p className="text-sm text-fg-muted">No runs recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {runs.map((r) => (
              <div
                key={r.id}
                className="rounded-2xl border border-border bg-bg-raised/40 p-4"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <div className="font-mono text-sm text-fg">{r.name}</div>
                    <div className="mt-1 font-mono text-[11px] text-fg-dim">
                      {r.id}
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs text-fg-muted">
                    <div>{r.status}</div>
                    <div>{fmtDuration(r.started_at, r.finished_at)}</div>
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-fg-muted md:grid-cols-4">
                  <div>
                    <div className="text-[10px] uppercase text-fg-dim">
                      Iterations
                    </div>
                    <div className="font-mono text-fg">
                      {r.iterations ?? "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-fg-dim">
                      Input tokens
                    </div>
                    <div className="font-mono text-fg">
                      {r.input_tokens?.toLocaleString() ?? "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-fg-dim">
                      Output tokens
                    </div>
                    <div className="font-mono text-fg">
                      {r.output_tokens?.toLocaleString() ?? "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-fg-dim">Cost</div>
                    <div className="font-mono text-fg">{fmtCost(r.cost_usd)}</div>
                  </div>
                </div>
                {r.skills.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {r.skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-border bg-bg-base px-2 py-0.5 font-mono text-[10px] text-fg-muted"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Findings */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Findings</h2>
        {findings.length === 0 ? (
          <p className="text-sm text-fg-muted">
            No structured findings were emitted. See the replay for the full
            event stream.
          </p>
        ) : (
          <div className="space-y-2">
            {findings.map((f) => (
              <div
                key={f.id}
                className="rounded-2xl border border-border bg-bg-raised/40 p-4"
              >
                <div className="flex items-baseline justify-between">
                  <span className="rounded-full border border-border bg-bg-base px-2 py-0.5 font-mono text-[10px] uppercase text-fg-muted">
                    {f.category}
                  </span>
                  <span className="font-mono text-[11px] text-fg-dim">
                    confidence {f.confidence.toFixed(2)}
                  </span>
                </div>
                <p className="mt-2 text-sm text-fg">{f.description}</p>
                {f.file_path && (
                  <div className="mt-2 font-mono text-xs text-fg-muted">
                    {f.file_path}
                    {f.line_number ? `:${f.line_number}` : ""}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function IncidentDetailPage() {
  // ``useSearchParams`` requires a Suspense boundary at build time.
  return (
    <Suspense
      fallback={
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-bg-raised/30" />
      }
    >
      <IncidentDetail />
    </Suspense>
  );
}
