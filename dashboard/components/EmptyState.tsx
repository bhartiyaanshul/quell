import { Inbox } from "lucide-react";

export function EmptyState({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-bg-raised/40 px-8 py-16 text-center">
      <Inbox size={28} className="mb-3 text-fg-dim" strokeWidth={1.5} />
      <div className="text-base font-semibold text-fg">{title}</div>
      <p className="mt-1 max-w-md text-sm text-fg-muted">{body}</p>
    </div>
  );
}
