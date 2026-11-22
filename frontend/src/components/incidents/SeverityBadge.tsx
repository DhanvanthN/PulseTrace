import { cn } from "@/lib/cn";
import { severityStyles } from "@/utils/severity";

export function SeverityBadge({
  severity,
  className,
}: {
  severity: string;
  className?: string;
}) {
  const styles = severityStyles(severity);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        styles.badge,
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", styles.dot)} aria-hidden />
      {severity}
    </span>
  );
}