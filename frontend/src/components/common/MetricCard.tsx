import type { LucideIcon } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardBody } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

interface MetricCardProps {
  label: string;
  icon: LucideIcon;
  value?: string | number | null;
  hint?: string;
  loading?: boolean;
}

export function MetricCard({ label, icon: Icon, value, hint, loading }: MetricCardProps) {
  const display =
    loading ? "…" : value === null || value === undefined || value === "" ? "—" : String(value);

  return (
    <Card className="transition-colors hover:border-graphite-600">
      <CardBody className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">{label}</span>
          <Icon className="h-4 w-4 text-slate-600" aria-hidden />
        </div>
        <p
          className={cn(
            "text-2xl font-semibold tracking-tight tabular-nums",
            display === "—" ? "text-slate-500" : "text-slate-100"
          )}
        >
          {display}
        </p>
        {hint ? (
          <p className="text-[10px] leading-snug text-slate-500">{hint}</p>
        ) : display === "—" ? (
          <Badge variant="muted">No data</Badge>
        ) : null}
      </CardBody>
    </Card>
  );
}