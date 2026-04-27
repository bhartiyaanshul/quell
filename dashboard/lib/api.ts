// Typed fetch wrapper for the FastAPI backend.
//
// During ``next dev``, a rewrite in next.config.mjs proxies /api/* to
// localhost:7777.  In the production bundle Next.js is mounted under
// the same FastAPI process, so the relative path just works.

export type Incident = {
  id: string;
  signature: string;
  severity: string;
  status: string;
  first_seen: string;
  last_seen: string;
  occurrence_count: number;
  root_cause: string | null;
  fix_pr_url: string | null;
  cost_usd: number;
};

export type Run = {
  id: string;
  name: string;
  parent_agent_id: string | null;
  skills: string[];
  status: string;
  started_at: string;
  finished_at: string | null;
  final_result: Record<string, unknown>;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
  iterations: number | null;
};

export type Finding = {
  id: string;
  category: string;
  description: string;
  file_path: string | null;
  line_number: number | null;
  confidence: number;
  created_at: string;
  agent_run_id: string;
};

export type EventRow = {
  id: string;
  event_type: "llm_call" | "tool_call" | "error" | "info" | string;
  timestamp: string;
  payload: Record<string, unknown>;
};

export type ReplayRun = Run & { events: EventRow[] };

export type Stats = {
  total: number;
  by_status: { detected: number; investigating: number; resolved: number };
  mttr_seconds: number | null;
  top_signatures: { signature: string; count: number }[];
};

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listIncidents: (status?: string) =>
    get<{ incidents: Incident[]; count: number }>(
      "/incidents" + (status ? `?status=${encodeURIComponent(status)}` : ""),
    ),
  getIncident: (id: string) =>
    get<{ incident: Incident; runs: Run[]; findings: Finding[] }>(
      `/incidents/${encodeURIComponent(id)}`,
    ),
  getReplay: (id: string) =>
    get<{ incident_id: string; runs: ReplayRun[]; totals: { runs: number; events: number; cost_usd: number } }>(
      `/incidents/${encodeURIComponent(id)}/replay`,
    ),
  stats: () => get<Stats>("/stats"),
};
