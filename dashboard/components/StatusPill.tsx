import { STATUS_COLOR, cn } from "@/lib/utils";

export function StatusPill({ value }: { value: string }) {
  const key = (value || "detected").toLowerCase();
  return (
    <span className={cn("inline-flex items-center gap-1.5 font-mono text-[11px]", STATUS_COLOR[key] ?? "text-fg-dim")}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {key}
    </span>
  );
}
