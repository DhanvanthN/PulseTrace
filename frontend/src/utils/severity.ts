export type SeverityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;

export function severityStyles(severity: SeverityLevel): {
  badge: string;
  dot: string;
  bar: string;
} {
  const key = severity.toUpperCase();
  switch (key) {
    case "CRITICAL":
      return {
        badge: "border-rose-500/35 bg-rose-500/10 text-rose-200",
        dot: "bg-rose-400",
        bar: "bg-rose-500/70",
      };
    case "HIGH":
      return {
        badge: "border-orange-500/35 bg-orange-500/10 text-orange-200",
        dot: "bg-orange-400",
        bar: "bg-orange-500/70",
      };
    case "MEDIUM":
      return {
        badge: "border-amber-500/30 bg-amber-500/10 text-amber-200",
        dot: "bg-amber-400",
        bar: "bg-amber-500/60",
      };
    case "LOW":
      return {
        badge: "border-slate-500/35 bg-slate-500/10 text-slate-300",
        dot: "bg-slate-400",
        bar: "bg-slate-500/60",
      };
    default:
      return {
        badge: "border-graphite-600 bg-graphite-800 text-slate-300",
        dot: "bg-slate-500",
        bar: "bg-graphite-600",
      };
  }
}

export const INCIDENT_STATUS_STYLES: Record<string, string> = {
  OPEN: "border-sky-500/30 bg-sky-500/10 text-sky-200",
  INVESTIGATING: "border-violet-500/30 bg-violet-500/10 text-violet-200",
  RESOLVED: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  IGNORED: "border-slate-600 bg-graphite-850 text-slate-400",
};

export const TIMELINE_EVENT_META: Record<
  string,
  { label: string; border: string; iconColor: string }
> = {
  ANOMALY_DETECTED: { label: "Anomaly", border: "border-amber-500/50", iconColor: "text-amber-400" },
  ERROR_SPIKE: { label: "Error spike", border: "border-rose-500/50", iconColor: "text-rose-400" },
  LOG_PATTERN_DETECTED: { label: "Log pattern", border: "border-cyan-500/45", iconColor: "text-cyan-400" },
  DEPLOYMENT: { label: "Deployment", border: "border-indigo-500/45", iconColor: "text-indigo-300" },
  INVESTIGATION_NOTE: { label: "Note", border: "border-slate-500/50", iconColor: "text-slate-400" },
  STATUS_CHANGED: { label: "Status", border: "border-emerald-500/45", iconColor: "text-emerald-400" },
  SERVICE_IMPACT: { label: "Service impact", border: "border-orange-500/45", iconColor: "text-orange-400" },
};