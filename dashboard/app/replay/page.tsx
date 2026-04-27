"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { ErrorCard } from "@/components/ErrorCard";
import { ReplayTimeline } from "@/components/ReplayTimeline";
import { api, type ReplayRun } from "@/lib/api";

type ReplayData = {
  incident_id: string;
  runs: ReplayRun[];
  totals: { runs: number; events: number; cost_usd: number };
};

function ReplayInner() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id") ?? "";
  const [data, setData] = useState<ReplayData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getReplay(id).then(setData).catch((e) => setError(e.message));
  }, [id]);

  if (!id) {
    return (
      <ErrorCard
        title="Missing incident id"
        body="Visit this page from the incident detail, or pass ?id=inc_xxx in the URL."
      />
    );
  }
  if (error) return <ErrorCard title="Could not load replay" body={error} />;
  if (!data)
    return (
      <div className="h-40 animate-pulse rounded-2xl border border-border bg-bg-raised/30" />
    );

  return (
    <div className="space-y-6">
      <div className="text-xs text-fg-muted">
        <Link href="/" className="hover:text-fg">
          Incidents
        </Link>
        <ChevronRight size={12} className="mx-1 inline" />
        <Link
          href={`/incident?id=${encodeURIComponent(id)}`}
          className="hover:text-fg"
        >
          <span className="font-mono">{id}</span>
        </Link>
        <ChevronRight size={12} className="mx-1 inline" />
        <span>Replay</span>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Replay</h1>
          <p className="mt-1 text-sm text-fg-muted">
            Full event timeline as Quell recorded it. No new LLM calls, no cost.
          </p>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs text-fg-muted">
          <span>{data.totals.runs} runs</span>
          <span>{data.totals.events} events</span>
          <span>${data.totals.cost_usd.toFixed(4)}</span>
        </div>
      </div>

      <ReplayTimeline runs={data.runs} />
    </div>
  );
}

export default function ReplayPage() {
  return (
    <Suspense
      fallback={
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-bg-raised/30" />
      }
    >
      <ReplayInner />
    </Suspense>
  );
}
