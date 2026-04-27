"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusPill } from "@/components/StatusPill";
import type { Incident } from "@/lib/api";
import { fmtCost, fmtDateTime } from "@/lib/utils";

export function IncidentTable({ incidents }: { incidents: Incident[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-bg-raised/40">
      <table className="min-w-full divide-y divide-border text-sm">
        <thead className="bg-bg-subtle/50 text-left text-[11px] uppercase tracking-wider text-fg-dim">
          <tr>
            <th className="px-4 py-3">Incident</th>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Occurrences</th>
            <th className="px-4 py-3">Cost</th>
            <th className="px-4 py-3">Last seen</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {incidents.map((i, idx) => (
            <motion.tr
              key={i.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.015 }}
              className="transition hover:bg-bg-raised"
            >
              <td className="px-4 py-3">
                <Link
                  href={`/incident?id=${encodeURIComponent(i.id)}`}
                  className="group block"
                >
                  <div className="font-mono text-[13px] text-fg group-hover:text-accent">
                    {i.id}
                  </div>
                  <div className="mt-0.5 max-w-sm truncate text-xs text-fg-muted">
                    {i.root_cause || i.signature}
                  </div>
                </Link>
              </td>
              <td className="px-4 py-3"><SeverityBadge value={i.severity} /></td>
              <td className="px-4 py-3"><StatusPill value={i.status} /></td>
              <td className="px-4 py-3 font-mono text-fg-muted">
                {i.occurrence_count}
              </td>
              <td className="px-4 py-3 font-mono text-fg-muted">
                {fmtCost(i.cost_usd)}
              </td>
              <td className="px-4 py-3 text-fg-muted">
                {fmtDateTime(i.last_seen)}
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
