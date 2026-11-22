import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  footer?: ReactNode;
  className?: string;
  "data-testid"?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  footer,
  className,
  "data-testid": testId,
}: EmptyStateProps) {
  return (
    <div
      data-testid={testId}
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-graphite-700 bg-graphite-850/40 px-6 py-10 text-center",
        className
      )}
    >
      <div className="mb-3 rounded-md border border-graphite-700 bg-graphite-900 p-2.5">
        <Icon className="h-5 w-5 text-slate-500" aria-hidden />
      </div>
      <h4 className="text-sm font-medium text-slate-200">{title}</h4>
      <p className="mt-1 max-w-md text-xs leading-relaxed text-slate-500">
        {description}
      </p>
      {footer ? <div className="mt-4">{footer}</div> : null}
    </div>
  );
}