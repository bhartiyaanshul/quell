import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function fmtDuration(fromIso: string, toIso: string | null | undefined): string {
  if (!toIso) return "in progress";
  const ms = new Date(toIso).getTime() - new Date(fromIso).getTime();
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

export function fmtCost(usd: number | null | undefined): string {
  if (usd == null) return "—";
  if (usd === 0) return "$0.00";
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(3)}`;
}

export const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-crit border-crit/40 bg-crit/10",
  high: "text-accent border-accent/40 bg-accent/10",
  medium: "text-warn border-warn/40 bg-warn/10",
  low: "text-cool border-cool/40 bg-cool/10",
  info: "text-fg-muted border-border bg-bg-raised",
};

export const STATUS_COLOR: Record<string, string> = {
  detected: "text-warn",
  investigating: "text-accent",
  resolved: "text-ok",
  abandoned: "text-fg-dim",
};
