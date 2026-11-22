import { cn } from "@/lib/cn";
import { INCIDENT_STATUS_STYLES } from "@/utils/severity";

export function StatusBadge({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const style = INCIDENT_STATUS_STYLES[status] ?? INCIDENT_STATUS_STYLES.OPEN;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        style,
        className
      )}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}