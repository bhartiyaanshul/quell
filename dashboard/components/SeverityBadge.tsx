import { SEVERITY_COLOR, cn } from "@/lib/utils";

export function SeverityBadge({ value }: { value: string }) {
  const key = (value || "info").toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        SEVERITY_COLOR[key] ?? SEVERITY_COLOR.info,
      )}
    >
      {key}
    </span>
  );
}
