import { AlertTriangle } from "lucide-react";

export function ErrorCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-crit/40 bg-crit/5 p-5">
      <AlertTriangle size={18} className="mt-0.5 text-crit" />
      <div>
        <div className="font-semibold text-fg">{title}</div>
        <p className="mt-1 text-sm text-fg-muted">{body}</p>
      </div>
    </div>
  );
}
